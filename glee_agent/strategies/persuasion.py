"""Persuasion — a seller who sees quality, a buyer who sees only the odds.

**Seller.** This is Bayesian persuasion. The seller recommends every high-quality
unit and lies on low-quality ones at rate q. A Bayesian buyer who trusts a
recommendation is buying at expected value

    E[value | recommend] = (p*v + (1-p)*q*u) / (p + (1-p)*q)

and keeps buying while that is at least the price, which caps the sustainable
lie rate at

    q* = p*(v - price) / ((1-p) * (price - u)).

Above q* the buyer stops believing and sales collapse; below it the seller is
leaving money on the table. Two corner cases matter: when the prior alone
justifies buying (p*v + (1-p)*u >= price) the buyer buys regardless, so
recommending everything already sells every round and is optimal; when v <= price
no recommendation can ever make a purchase rational.

**Buyer.** The prior is only the starting point — what matters is this seller's
observed truthfulness. Quality is revealed only on rounds the buyer bought, so
early purchases carry information value on top of their payoff.
"""

from __future__ import annotations

from .. import runtime_flags

from ..actions import _num
from ..text import reads_as_recommendation

# Weight of the prior in the buyer's honesty estimate, in pseudo-observations.
# Keeps a single unlucky round from swinging the posterior to an extreme.
_PRIOR_STRENGTH = 2.0


def _rounds(state: dict) -> tuple[int, int]:
    total = int(_num(state.get("total_rounds"), 1))
    current = int(_num(state.get("round"), 1))
    return current, max(total, current)


def optimal_lie_rate(p: float, v: float, u: float, price: float) -> float:
    """The largest rate of recommending low-quality units a Bayesian buyer tolerates."""
    if price <= u:                      # even a low unit is worth the price
        return 1.0
    if v <= price:                      # no belief makes buying rational
        return 0.0
    if p >= 1.0:
        return 1.0
    denominator = (1.0 - p) * (price - u)
    if denominator <= 0:
        return 1.0
    return min(max(p * (v - price) / denominator, 0.0), 1.0)


def _seller_history(state: dict, me: str) -> list[dict]:
    return [h for h in (state.get("history") or []) if isinstance(h, dict)]


def seller_plan(game: dict, cfg) -> dict:
    state = game["game_state"]
    price = _num(state.get("product_price"), 0.0)
    p = _num(state.get("p"), 0.5)
    quality = str(state.get("current_quality", "")).lower()
    is_high = quality == "high"
    round_no, total = _rounds(state)

    knows_values = state.get("v") is not None
    v = _num(state.get("v"), 0.0)
    u = _num(state.get("u"), 0.0)

    history = _seller_history(state, game["your_player"])
    bought = [h for h in history if h.get("bought")]
    buy_rate = len(bought) / len(history) if history else None

    if is_high:
        # Never pass up a genuine sale.
        return {"recommend": True, "reason": "high quality", "round": round_no,
                "total_rounds": total, "buy_rate": buy_rate, "knows_values": knows_values,
                "quality_is_high": True}

    if not knows_values:
        # Without v the lie rate is not computable. Read the buyer instead: keep
        # recommending while they are buying, turn honest once they stop, so the
        # next honest round rebuilds the record.
        recommend = buy_rate is None or buy_rate >= 0.5
        return {"recommend": recommend, "reason": "no valuations; tracking buyer",
                "round": round_no, "total_rounds": total, "buy_rate": buy_rate,
                "knows_values": False, "quality_is_high": False}

    if p * v + (1.0 - p) * u >= price:
        # The prior alone justifies buying, so a buyer purchases every round
        # regardless. Recommending everything already sells out the game.
        return {"recommend": True, "reason": "prior alone justifies purchase",
                "round": round_no, "total_rounds": total, "buy_rate": buy_rate,
                "knows_values": True, "lie_rate": 1.0, "quality_is_high": False}

    # Read live so the honesty setting can be changed without a restart -- a
    # restart of an unbounded agent costs every game it holds. Falls back to the
    # config value, so behaviour is unchanged unless arms.json says otherwise.
    shading = runtime_flags.as_float("GLEE_PERS_LIE_SHADING", cfg.pers_lie_shading)
    honest_rounds = int(runtime_flags.as_float("GLEE_PERS_HONEST_ROUNDS",
                                               cfg.pers_honest_rounds))
    # DP policy (models/pers_policy_dp_v1.json): exact backward-induction
    # recommendation for low-quality rounds, keyed on (mode, prior, v/price
    # ratio, round, lies-the-buyer-caught). Gated; falls through to the
    # shading heuristic when off, unkeyed, or the file is absent.
    if runtime_flags.enabled("GLEE_PERS_DP"):
        # v2 dispatch: when the opponent's NAME maps to a fitted buyer
        # archetype, plan against that archetype's own policy -- the pooled
        # policy plans against an average buyer the clustering shows is a
        # fiction (16/33 named buyers keep buying at ~0.92 after 2+ caught
        # lies; a skeptic cluster drops to ~0.57). Hidden opponents, unknown
        # names, and thin archetype cells all fall through to the pooled
        # cell, which is v1 verbatim.
        dp = _dp_policy_v2() if runtime_flags.enabled("GLEE_PERS_DP_ARCH") else None
        arch_used = False
        if dp is None:
            dp = _dp_policy()
        if dp is not None:
            pb_ = "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")
            rb_ = min((1.2, 1.25, 2.0, 3.0, 4.0),
                      key=lambda g_: abs(g_ - (v / price if price else 0)))
            cell = None
            opp_name = (game.get("opponent") or {}).get("name")
            if opp_name is not None:
                k_ = (dp.get("names") or {}).get(str(opp_name))
                if k_ is not None:
                    cell = (dp.get("cells") or {}).get(
                        f"a{k_}|{mode_of(state)}|{pb_}|r{rb_}")
                    arch_used = cell is not None
            if cell is None:
                cell = (dp.get("cells") or {}).get(f"{mode_of(state)}|{pb_}|r{rb_}")
            if cell:
                lies_caught = 0
                for _r in state.get("history") or []:
                    if (_r.get("bought") and str(_r.get("quality")).lower() == "low"
                            and _looks_positive(_r.get("seller_message"))):
                        lies_caught += 1
                lb_ = "0" if lies_caught == 0 else ("1" if lies_caught == 1 else "2+")
                idx = min(max(round_no - 1, 0), len(cell["policy"][lb_]) - 1)
                # high quality already returned above -- this hook only ever
                # decides the LOW-quality recommendation
                lie_now = bool(cell["policy"][lb_][idx])
                return {"recommend": lie_now,
                        "reason": "dp: exact policy on low quality",
                        "round": round_no, "total_rounds": total,
                        "buy_rate": buy_rate, "knows_values": True,
                        "lie_rate": 1.0 if lie_now else 0.0,
                        "quality_is_high": False, "dp": True,
                        "dp_arch": arch_used}

    q_star = optimal_lie_rate(p, v, u, price) * shading
    # Stay honest through the opening rounds: the buyer learns quality only on
    # rounds they buy, so an early clean record is what makes later ones sell.
    if round_no <= honest_rounds:
        return {"recommend": False, "reason": "building reputation", "round": round_no,
                "total_rounds": total, "buy_rate": buy_rate, "knows_values": True,
                "lie_rate": q_star, "quality_is_high": False}

    # Spread the lies deterministically rather than by coin flip: it keeps the
    # realised rate at q* instead of letting variance overshoot it.
    lows_so_far = sum(1 for h in history if str(h.get("quality", "")).lower() == "low")
    lies_so_far = sum(1 for h in history
                      if str(h.get("quality", "")).lower() == "low" and _recommended(h))
    # Lie only if doing so keeps the realised rate at or below q*. Testing the
    # rate *after* this round is what stops a tiny q* from still buying a first
    # free lie (zero lies is below every positive allowance).
    allowed = (lows_so_far + 1) * q_star
    return {"recommend": lies_so_far + 1 <= allowed, "reason": f"lie budget {q_star:.2f}",
            "round": round_no, "total_rounds": total, "buy_rate": buy_rate,
            "knows_values": True, "lie_rate": q_star, "lies_so_far": lies_so_far,
            "quality_is_high": False}


def _recommended(entry: dict) -> bool:
    """Whether the seller's move in a history entry was a recommendation to buy.

    Text mode is parsed by ``glee_agent.text``. A message carrying no usable
    signal counts as a recommendation, because a seller who says nothing useful
    is still offering the unit — but a message that declines the sale must be
    read as declining it, or the buyer's honesty estimate treats truthful
    sellers as liars.
    """
    msg = entry.get("seller_message")
    if isinstance(msg, bool):
        return msg
    if isinstance(msg, str):
        verdict = reads_as_recommendation(msg)
        if verdict is not None:
            return verdict
        return True
    return bool(entry.get("recommended", False))


# ---------------------------------------------------------------------------
# Buyer v2: a type posterior over the seller's lie rate, fed by the FULL
# recommendation stream -- not just the rounds we bought.
# ---------------------------------------------------------------------------
#
# The v1 buyer learns honesty only from purchases, which produced the two loss
# shapes that dominate our persuasion ledger: in cells where the prior alone
# does not justify buying it never buys, so it never learns, so it never buys
# (a guaranteed $0 against sellers whose recommendations are in fact
# informative), and its flat exploration bonus junk-buys in tight-margin cells
# where one bad unit erases five good ones. But the seller's recommendation
# stream is visible on EVERY round: an all-yes seller is identified as a
# spammer within a handful of rounds by frequency alone (P(yes|q) = p+(1-p)q),
# and a seller who sometimes declines has proven selectivity, which makes
# their yes worth something -- all without spending a single purchase.

_Q_GRID = (0.0, 0.125, 0.25, 0.5, 0.75, 1.0)
#: Chance a seller declines to recommend a HIGH unit; keeps likelihoods off 0.
_EPS = 0.02

_PRIOR_STATE = {"checked": 0.0, "mtime": None, "doc": None}


def _buyer_prior_doc():
    import os as _os, time as _time, json as _json
    path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__)))), "models", "pers_buyer_prior_v1.json")
    now = _time.monotonic()
    if now - _PRIOR_STATE["checked"] < 10.0:
        return _PRIOR_STATE["doc"]
    _PRIOR_STATE["checked"] = now
    try:
        mtime = _os.stat(path).st_mtime_ns
    except OSError:
        return _PRIOR_STATE["doc"]
    if mtime == _PRIOR_STATE["mtime"]:
        return _PRIOR_STATE["doc"]
    try:
        doc = _json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return _PRIOR_STATE["doc"]
    if isinstance(doc, dict) and doc.get("cells"):
        _PRIOR_STATE.update(mtime=mtime, doc=doc)
    return _PRIOR_STATE["doc"]


def _q_posterior(history: list, p: float, mode: str) -> list[float]:
    """Posterior over _Q_GRID given every observable round so far.

    Bought rounds contribute their (recommendation, quality) joint; unbought
    rounds contribute the recommendation's marginal frequency. The prior is the
    field-fitted mixture for this (mode, prior-bin) cell when the model file is
    present, uniform otherwise.
    """
    doc = _buyer_prior_doc()
    pb = "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")
    prior = None
    if doc:
        cell = (doc.get("cells") or {}).get(f"{mode}|{pb}")
        if cell and len(cell.get("prior") or []) == len(_Q_GRID):
            prior = [max(float(x), 1e-4) for x in cell["prior"]]
    if prior is None:
        prior = [1.0] * len(_Q_GRID)
    post = list(prior)
    for entry in history:
        if not isinstance(entry, dict):
            continue
        rec = _recommended(entry)
        quality = str(entry.get("quality", "")).lower()
        for i, q in enumerate(_Q_GRID):
            if entry.get("bought") and quality in ("high", "low"):
                if quality == "high":
                    like = p * ((1.0 - _EPS) if rec else _EPS)
                else:
                    like = (1.0 - p) * (q if rec else (1.0 - q))
            else:
                pr = p * (1.0 - _EPS) + (1.0 - p) * q
                like = pr if rec else (1.0 - pr)
            post[i] *= max(like, 1e-12)
    z = sum(post)
    return [x / z for x in post] if z > 0 else [1.0 / len(_Q_GRID)] * len(_Q_GRID)


def buyer_plan_v2(game: dict, cfg) -> dict:
    state = game["game_state"]
    price = _num(state.get("product_price"), 0.0)
    p = _num(state.get("p"), 0.5)
    v = _num(state.get("v"), 0.0)
    u = _num(state.get("u"), 0.0)
    round_no, total = _rounds(state)
    mode = mode_of(state)
    history = [h for h in (state.get("history") or []) if isinstance(h, dict)]

    recommended_now = _recommended({"seller_message": state.get("seller_message")})
    post = _q_posterior(history, p, mode)

    # The CURRENT message is itself evidence about q and must reweight the
    # mixture before P(high|message) is read off it -- a pure spammer almost
    # never says "no", so a "no" collapses the q=1 mass instead of letting
    # P(high|no,q=1)~1 ride into the average. The audit measured the unweighted
    # version buying on explicit declines 688 times across the logged games at
    # -0.65x price a piece.
    post_now = []
    for w, q in zip(post, _Q_GRID):
        pr_yes = p * (1.0 - _EPS) + (1.0 - p) * q
        post_now.append(w * (pr_yes if recommended_now else (1.0 - pr_yes)))
    z = sum(post_now)
    post_now = [x / z for x in post_now] if z > 1e-12 else list(post)

    # P(high | this seller's current message), mixed over the type posterior.
    p_high = 0.0
    for w, q in zip(post_now, _Q_GRID):
        if recommended_now:
            yes_hi = p * (1.0 - _EPS)
            p_high += w * yes_hi / (yes_hi + (1.0 - p) * q)
        else:
            no_hi = p * _EPS
            p_high += w * no_hi / max(no_hi + (1.0 - p) * (1.0 - q), 1e-9)
    expected = p_high * v + (1.0 - p_high) * u

    observed = sum(1 for h in history if h.get("bought")
                   and str(h.get("quality", "")).lower() in ("high", "low"))
    caught = sum(1 for h in history if h.get("bought")
                 and str(h.get("quality", "")).lower() == "low" and _recommended(h))

    # Tight cells: breakeven belief close to 1 means one junk unit erases many
    # good ones, so demand a posterior MARGIN, not just a positive edge -- and
    # optionally walk away outright once this seller is a proven liar here.
    breakeven = (price - u) / (v - u) if v > u else 1.0
    guard = runtime_flags.as_float("GLEE_PERS_BUYER_GUARD", 0.0)
    strike = int(runtime_flags.as_float("GLEE_PERS_BUYER_STRIKE", 0))
    tight = breakeven >= 0.75
    blocked = False
    if tight and strike > 0 and caught >= strike:
        blocked = True
    # In tight cells the stream posterior must close the gap between prior and
    # breakeven; when that gap is wide (lo/mid prior at ratio <=1.25) the
    # inference burden exceeds what noisy streams support -- the arena measured
    # every such cell NEGATIVE for an unrestricted v2 while sitting out earns
    # exactly 0. Buying there is allowed only when the prior starts near the
    # breakeven it must clear.
    tight_prior = runtime_flags.as_float("GLEE_PERS_BUYER_TIGHT_PRIOR", 0.0)
    if tight and p < tight_prior:
        blocked = True
    threshold = price + (guard * price if tight else 0.0)

    # Optional audit bonus: worth a small paid look while nothing has been
    # observed and rounds remain to collect on what it reveals. v2's stream
    # posterior makes this far less necessary than v1's -- it is a knob for the
    # arena to price, default off.
    audit = runtime_flags.as_float("GLEE_PERS_BUYER_AUDIT", 0.0)
    rounds_remaining = max(0, total - round_no)
    bonus = 0.0
    if audit > 0.0 and observed == 0 and rounds_remaining > 0 and not tight:
        bonus = audit * price * (rounds_remaining / max(total, 1))

    return {
        "price": price, "p": p, "v": v, "u": u,
        "recommended": recommended_now,
        "p_high": p_high, "expected_value": expected,
        "q_posterior": [round(x, 3) for x in post_now],
        "observed_rounds": observed, "caught_lies": caught,
        "breakeven": breakeven, "tight": tight, "blocked": blocked,
        "exploration_bonus": bonus,
        "round": round_no, "total_rounds": total,
        "buyer_v2": True,
        "buy": (not blocked) and (expected + bonus >= threshold),
    }


def buyer_plan(game: dict, cfg) -> dict:
    state = game["game_state"]
    price = _num(state.get("product_price"), 0.0)
    p = _num(state.get("p"), 0.5)
    v = _num(state.get("v"), 0.0)
    u = _num(state.get("u"), 0.0)
    round_no, total = _rounds(state)

    recommended_now = _recommended({"seller_message": state.get("seller_message")})

    # Quality is observed only on rounds we bought, so only those inform the
    # honesty estimate. Smooth toward the prior while the sample is tiny.
    hits = misses = 0
    for entry in state.get("history") or []:
        if not isinstance(entry, dict) or not entry.get("bought"):
            continue
        if _recommended(entry) != recommended_now:
            continue                       # compare like with like
        if str(entry.get("quality", "")).lower() == "high":
            hits += 1
        elif str(entry.get("quality", "")).lower() == "low":
            misses += 1

    observed = hits + misses
    prior_high = p if recommended_now else p / 2.0   # a non-recommendation is bearish
    p_high = ((hits + _PRIOR_STRENGTH * prior_high)
              / (observed + _PRIOR_STRENGTH))
    expected = p_high * v + (1.0 - p_high) * u

    # Information has value while rounds remain: a purchase is the only way to
    # learn this seller's honesty, and that knowledge pays off on every later
    # round. Worth a small deficit early, nothing at the end.
    rounds_remaining = max(0, total - round_no)
    exploration = 0.0
    if observed < 2 and rounds_remaining > 0:
        exploration = price * 0.10 * min(1.0, rounds_remaining / max(1, total))

    return {
        "price": price, "p": p, "v": v, "u": u,
        "recommended": recommended_now,
        "p_high": p_high, "expected_value": expected,
        "observed_rounds": observed, "hits": hits, "misses": misses,
        "exploration_bonus": exploration,
        "round": round_no, "total_rounds": total,
        "buy": expected + exploration >= price,
    }


def decide(game: dict, cfg) -> dict:
    action_type = game["valid_actions"]["type"]

    if action_type in ("seller_message", "seller_recommendation"):
        p = seller_plan(game, cfg)
        if action_type == "seller_recommendation":
            return {"decision": "yes" if p["recommend"] else "no", "_plan": p}
        # Text mode: the message *is* the recommendation. The LLM layer rewrites
        # this into something persuasive; the fallback still carries the signal.
        # Message style is a live experiment knob. The fitted buyer table shows a
        # 20pp conversion gap between a binary "yes" (71.5% buy at high prior)
        # and our text-mode positive template (51.2%) -- same intent, different
        # tokens, and the buyers are parsers. Styles reword the SAME honest
        # recommendation; the decision itself is unchanged. Binary-mode games in
        # the same block are untouched by this knob and serve as the concurrent
        # control for field drift.
        style = (runtime_flags.get("GLEE_PERS_MSG_STYLE") or "plain").strip().lower()
        if style == "affirm":
            message = ("Yes. Buy this one - great product, I recommend it."
                       if p["recommend"]
                       else "No. Skip this one - I do not recommend it.")
        elif style == "token":
            message = "yes" if p["recommend"] else "no"
        else:
            message = ("I recommend this one." if p["recommend"]
                       else "I would hold off on this one.")
        return {"message": message, "_plan": p}

    # Buyer v2 (type posterior over the seller's lie rate) is arena-gated:
    # candidates and the live agent run this same line, so an arena win IS a
    # statement about deployed behaviour.
    if runtime_flags.enabled("GLEE_PERS_BUYER_V2"):
        p = buyer_plan_v2(game, cfg)
    else:
        p = buyer_plan(game, cfg)
    return {"decision": "yes" if p["buy"] else "no", "_plan": p}

_DP_STATE = {"checked": 0.0, "mtime": None, "doc": None}
_DP2_STATE = {"checked": 0.0, "mtime": None, "doc": None}


def _dp_policy_v2():
    import os as _os, time as _time, json as _json
    path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__)))), "models", "pers_policy_dp_v2.json")
    now = _time.monotonic()
    if now - _DP2_STATE["checked"] < 10.0:
        return _DP2_STATE["doc"]
    _DP2_STATE["checked"] = now
    try:
        mtime = _os.stat(path).st_mtime_ns
    except OSError:
        return _DP2_STATE["doc"]
    if mtime == _DP2_STATE["mtime"]:
        return _DP2_STATE["doc"]
    try:
        doc = _json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return _DP2_STATE["doc"]
    if isinstance(doc, dict) and doc.get("cells"):
        _DP2_STATE.update(mtime=mtime, doc=doc)
    return _DP2_STATE["doc"]


def mode_of(state) -> str:
    return state.get("seller_message_type") or "text"


def _looks_positive(msg) -> bool:
    s = str(msg or "").strip().lower()
    return not ("hold off" in s or s in ("no", "false") or "not recommend" in s
                or "skip" in s)


def _dp_policy():
    import os as _os, time as _time, json as _json
    path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__)))), "models", "pers_policy_dp_v1.json")
    now = _time.monotonic()
    if now - _DP_STATE["checked"] < 10.0:
        return _DP_STATE["doc"]
    _DP_STATE["checked"] = now
    try:
        mtime = _os.stat(path).st_mtime_ns
    except OSError:
        return _DP_STATE["doc"]
    if mtime == _DP_STATE["mtime"]:
        return _DP_STATE["doc"]
    try:
        doc = _json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return _DP_STATE["doc"]
    if isinstance(doc, dict) and doc.get("cells"):
        _DP_STATE.update(mtime=mtime, doc=doc)
    return _DP_STATE["doc"]
