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

import math

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

    # DP v3 (models/pers_policy_dp_v3.json). Sits ABOVE the prior-justifies
    # shortcut on purpose: that shortcut is a theory result -- a Bayesian buyer
    # whose prior already clears the price buys whatever you say -- and at the
    # MARGIN of that condition the logged field does not obey it. The biggest
    # measured gain in the whole candidate is binary|mid|r2.0, a cell sitting
    # exactly on p*v == price, where the shortcut recommends everything and the
    # field punishes it.
    #
    # But the shortcut is right where it has room. Once the prior clears the
    # price by a comfortable margin the seller replay and the theory agree
    # against the fitted model: lying really is close to free, the DP's early
    # honesty is pure lost revenue, and every cell at ratio 3 or 4 came back
    # NEGATIVE. So the gate carries a margin guard.
    #
    # The qualitative rule -- defer to the shortcut where the prior clears the
    # price outright, plan where it is tight -- is theory-driven. The 0.25 level
    # was read off the seller replay across 30 cells, which is an in-sample
    # choice on a small grid and should be re-checked on new data, so it is a
    # tunable flag rather than a constant.
    if runtime_flags.enabled("GLEE_PERS_DP_V3"):
        margin = ((p * v + (1.0 - p) * u) / price - 1.0) if price else 0.0
        if margin <= runtime_flags.as_float("GLEE_PERS_DP_V3_MARGIN", 0.25):
            plan = _dp_v3_plan(state, p, v, price, round_no, total, buy_rate)
            if plan is not None:
                plan["prior_margin"] = round(margin, 4)
                return plan

    if p * v + (1.0 - p) * u >= price:
        # BACKLOADING ARM. The claim below -- "a buyer purchases every round
        # regardless" -- is refuted by a live transcript: at p=1/3, v/price=3
        # (where p*v == price exactly, so this branch fires) we pushed all 20
        # including 10 low units, the buyer bought in round ONE, got a low unit,
        # and never bought again. We earned 100 of a possible 1000.
        #
        # The error is that the branch is MYOPIC. It asks whether a sale beats
        # nothing this round and never prices the continuation: a lie told early
        # costs every remaining round, a lie told last costs nothing, because
        # there is no continuation left to protect. Codex's backward induction
        # against that buyer: all-push 0.2278, always-honest 0.4864,
        # honest-then-push-at-the-end 0.5144.
        #
        # This is a RANDOMISED ARM, not a decided policy. Backtests on our own
        # logs cannot settle it -- the data was generated by the policy under
        # test -- so assignment is per GAME by a hash of its id, exactly as
        # GLEE_NEGO_ZOPA_AB does, and scripts/live_percentile.py recovers the
        # arm with the same pure function. At 4,042 seller games a day an effect
        # of this size resolves in well under an hour.
        _bl = int(runtime_flags.as_float("GLEE_PERS_BACKLOAD_AB", 0.0))
        if _bl > 0:
            import hashlib as _h
            _gid = str(game.get("game_id") or "")
            if _gid and (int(_h.sha256(("backload|" + _gid).encode()).hexdigest(), 16) & 1):
                # Treatment: stay honest until the last `_bl` rounds, then push.
                _late = round_no > max(1, total - _bl)
                _rec = True if _late else is_high
                return {"recommend": _rec, "reason": "backload arm",
                        "round": round_no, "total_rounds": total,
                        "buy_rate": buy_rate, "knows_values": True,
                        "lie_rate": 1.0 if _late else 0.0,
                        "quality_is_high": is_high,
                        "backload_arm": True, "backload_late": _late}
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


def _recommendation_signal(entry: dict) -> bool | None:
    """The seller's recommendation signal, preserving parser abstention."""
    msg = entry.get("seller_message")
    if isinstance(msg, bool):
        return msg
    if isinstance(msg, str):
        return reads_as_recommendation(msg)
    recommended = entry.get("recommended")
    if isinstance(recommended, bool):
        return recommended
    return None


def _recommended(entry: dict) -> bool:
    """Legacy boolean reading of a seller move.

    Text mode is parsed by ``glee_agent.text``. A message carrying no usable
    signal counts as a recommendation, because a seller who says nothing useful
    is still offering the unit — but a message that declines the sale must be
    read as declining it, or the buyer's honesty estimate treats truthful
    sellers as liars.
    """
    verdict = _recommendation_signal(entry)
    if verdict is not None:
        return verdict
    if isinstance(entry.get("seller_message"), str):
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

# Independent of every existing persuasion salt.  The pure assignment helper is
# also imported by scripts/live_percentile.py, so the analysis cannot silently
# disagree with the action path about which games were treatment.
PERS_BUYER_SELECTIVITY_SALT = "pers_buyer_selectivity_v1|"
# The one-low stop is a separate, unmeasured hypothesis.  When its own flag is
# armed, this independent salt creates a nested 2x2 design: the selectivity
# candidate is split into strike/no-strike games while both corresponding main-
# arm controls remain behaviorally identical.  The historical fixed-stream
# proxy fell from +.01445 without the stop to +.01209 with it while removing
# 5,604 more purchases, so silently bundling it into the main arm would make its
# cost impossible to identify.
PERS_BUYER_SELECTIVITY_STRIKE_SALT = "pers_buyer_selectivity_strike_v1|"


#: Independent salt for the rank-buy arm. Must not collide with the selectivity
#: salts above or the two experiments would be correlated and neither readable.
PERS_RANK_BUY_SALT = "pers_rank_buy_v1|"


def rank_buy_assignment(game_id) -> bool | None:
    """Stable per-game rank-buy arm, without consulting live flags."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    return bool(int(_hashlib.sha256((PERS_RANK_BUY_SALT + gid).encode()).hexdigest(), 16) & 1)


def _rank_buy_arm(game: dict) -> bool:
    """Whether THIS game is assigned to buy through the p*r <= threshold cell.

    WHY THIS EXISTS. We gate purchases on money EV -- buy iff the posterior beats
    (price-u)/(v-u), which with u=0 is 1/r -- and at p*r <= 1 an always-recommend
    seller leaves the posterior at the prior exactly, so that gate refuses every
    purchase. THE COMPETITION DOES NOT SCORE MONEY, IT SCORES RANK. The
    rank-indifference threshold is

        q_rank = [F(S) - F(S+u-P)] / [F(S+v-P) - F(S+u-P)]

    for the cell payoff CDF F at accumulated payoff S, and it is not equal to
    (P-u)/(v-u). On fitted numbers for the text p=.5, r=1.2 cell -- F(-P)=.0284,
    F(0)=.4498, F(+.2P)=.8734 -- q_rank is 0.4987 against a money gate of 0.8333,
    so the gate is 33 probability points stricter than the objective, and on the
    prior alone rank says BUY where money says REFUSE.

    The logs agree in shape. Across 3,800 buyer games at p*r < 1 we score 0.4813
    and refuse outright in 2,882 of them (75.8%), for percentile 0.4651; games
    where we bought 75-99% scored 0.7329 and the 34 where we bought everything
    scored 0.8173. The mirror cell is the tell: as SELLER at p*r < 1 we score
    0.6505, our best cell anywhere, which is only possible because the buyers
    facing us there do buy. We are on the losing side of a trade we win from the
    other seat.

    That evidence is observational and our buyer is adaptive -- it buys more
    after a seller looks honest -- so the monotone table is confounded by reverse
    causation and cannot be trusted on its own. This arm exists to settle it the
    only way that removes the confound: randomise. Assignment is a hash of the
    game id, independent of every other persuasion salt, so both arms run inside
    one agent against the same opponent pool in the same hour.

    Deliberately one-directional: it may only turn a refusal INTO a purchase,
    never the reverse, so it cannot damage the cells we already win. It is scoped
    to p*r <= GLEE_PERS_RANK_BUY_AB and cannot fire at p*r > 1, where we already
    score 0.5521 and buy 84% of rounds.
    """
    thr = runtime_flags.as_float("GLEE_PERS_RANK_BUY_AB", 0.0)
    # Fail CLOSED on a malformed flag: NaN comparisons are all False, so an
    # unguarded value would slip past a bare `<= 0` check and arm the treatment.
    if not math.isfinite(thr) or thr <= 0.0:
        return False
    state = game.get("game_state") or {}
    if (state.get(f"{game.get('your_player')}_role") or "") != "buyer":
        return False
    p = _num(state.get("p"), 0.0)
    v = _num(state.get("v"), 0.0)
    price = _num(state.get("product_price"), 0.0)
    if not (p > 0.0 and v > 0.0 and price > 0.0):
        return False                      # blind cell: no p*r to test against
    if not (p * v / price) <= thr:
        return False
    return bool(rank_buy_assignment(game.get("game_id")))


#: Independent salt for the continuation-aware rank gate.
PERS_RANK_GATE_SALT = "pers_rank_gate_v1|"

#: One solved DP per (cell, horizon, m_hat bucket, q_hat bucket). The tables are
#: small (231 states at T=20) and the bucketing is what keeps this off the hot
#: path: measured 0.97 ms to solve, and a cache hit costs a dict lookup.
_RANK_DP_CACHE: dict = {}


def rank_gate_assignment(game_id) -> bool | None:
    """Stable per-game rank-gate arm, without consulting live flags."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    return bool(int(_hashlib.sha256((PERS_RANK_GATE_SALT + gid).encode()).hexdigest(), 16) & 1)


def _cell_samples(state: dict, seat: str):
    """The buyer payoff sample vector for this exact configuration, or None.

    Keyed identically to sim/percentile.py so the DP optimises the same ladder
    the competition scores us on. Any drift between the two makes the threshold
    an answer to the wrong question.
    """
    price = _num(state.get("product_price"), 0.0)
    p = state.get("p")
    v = _num(state.get("v"), 0.0)
    rounds = int(_num(state.get("total_rounds"), 20)) or 20
    if not price or p is None or not v:
        return None
    mode = state.get("seller_message_type") or "text"
    ratio = min((1.2, 1.25, 2.0, 3.0, 4.0), key=lambda g: abs(g - v / price))
    role = "seller" if seat == "player_1" else "buyer"
    key = "|".join(str(x) for x in
                   ("persuasion", mode, round(float(p), 2), ratio, role, rounds))
    try:
        from sim.percentile import _load
        return _load().get(key)
    except Exception:
        return None


def _midrank(samples, x: float) -> float:
    """F(x): the percentile this payoff would score in its own cell."""
    import bisect
    lo = bisect.bisect_left(samples, x - 1e-9)
    hi = bisect.bisect_right(samples, x + 1e-9)
    return (lo + hi) / 2.0 / len(samples)


def _rank_dp(samples, total: int, v: float, u: float, price: float,
             m_hat: float, q_hat: float):
    """Solve for V(t,a,b), the expected PERCENTILE from state (t, a, b).

    WHY A DP AND NOT THE ONE-SHOT FORMULA. The rank-indifference threshold

        q_rank = [F(S) - F(S+u-P)] / [F(S+v-P) - F(S+u-P)]

    is exact only in the LAST round, where there is no continuation to protect.
    Applied as a standing rule it is rank-negative in every p*r <= 1 cell --
    measured: buy-iff-recommended at q=0.50 scores 0.056 against 0.4498 for
    refusing, because the effective 20-round threshold is 0.80-0.85, i.e. right
    back at the money gate. The gap between money and rank is real in 16 of 30
    cells and worth +0.0585 buyer percentile, but ONLY in continuation-aware
    form, where the threshold runs 0.50 at the horizon up to 0.97 early on. A
    myopic rank gate is worse than the money gate it replaces; that error cost us
    a live arm today.

    a = units bought that proved high, b = bought and proved low. Quality is
    revealed only on rounds we bought, which is exactly why (a,b) is the state:
    everything we know about this seller is in it.
    """
    T = total
    terminal = {}
    for a in range(T + 1):
        for b in range(T + 1 - a):
            payoff = (a * (v - price) - b * (price - u)) / (price * T)
            terminal[(a, b)] = _midrank(samples, payoff)
    layers = [terminal]
    for _ in range(T):
        nxt, cur = layers[-1], {}
        for a in range(T + 1):
            for b in range(T + 1 - a):
                refuse = nxt.get((a, b), 0.0)
                take = (q_hat * nxt.get((a + 1, b), refuse)
                        + (1.0 - q_hat) * nxt.get((a, b + 1), refuse))
                # A recommendation arrives with probability m_hat; with the
                # remainder the seller declines and there is nothing to buy.
                cur[(a, b)] = m_hat * max(refuse, take) + (1.0 - m_hat) * refuse
        layers.append(cur)
    return layers


def _q_rank_threshold(samples, t: int, total: int, a: int, b: int,
                      v: float, u: float, price: float,
                      m_hat: float, q_hat: float):
    """The posterior P(high) at which buying and refusing are rank-indifferent."""
    key = (id(samples), total, round(m_hat / 0.05), round(q_hat / 0.05))
    layers = _RANK_DP_CACHE.get(key)
    if layers is None:
        layers = _rank_dp(samples, total, v, u, price, m_hat, q_hat)
        if len(_RANK_DP_CACHE) > 512:
            _RANK_DP_CACHE.clear()
        _RANK_DP_CACHE[key] = layers
    # layers[0] is t = T+1; the value function at t+1 is layers[total - t].
    idx = total - t
    if idx < 0 or idx >= len(layers):
        return None
    nxt = layers[idx]
    hold = nxt.get((a, b))
    win = nxt.get((a + 1, b))
    lose = nxt.get((a, b + 1))
    if hold is None or win is None or lose is None:
        return None
    denom = win - lose
    if denom <= 1e-12:
        return None                       # no rank separation: fall through
    return (hold - lose) / denom


def buyer_selectivity_assignment(game_id) -> bool | None:
    """Stable per-game selectivity arm, without consulting live flags."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    digest = _hashlib.sha256((PERS_BUYER_SELECTIVITY_SALT + gid).encode()).hexdigest()
    return bool(int(digest, 16) & 1)


def buyer_selectivity_strike_assignment(game_id) -> bool | None:
    """Stable independent strike bit, without consulting live flags."""
    gid = str(game_id or "")
    if not gid:
        return None
    import hashlib as _hashlib
    digest = _hashlib.sha256(
        (PERS_BUYER_SELECTIVITY_STRIKE_SALT + gid).encode()).hexdigest()
    return bool(int(digest, 16) & 1)


def _buyer_selectivity_arm(game_id) -> bool | None:
    """Treatment bit when the buyer-selectivity experiment is armed."""
    if not runtime_flags.enabled("GLEE_PERS_BUYER_SELECTIVITY_AB"):
        return None
    return buyer_selectivity_assignment(game_id)


def _buyer_selectivity_strike_arm(game_id) -> bool | None:
    """Independent strike bit only when its default-off experiment is armed."""
    if not runtime_flags.enabled("GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB"):
        return None
    return buyer_selectivity_strike_assignment(game_id)


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


def _q_posterior(history: list, p: float, mode: str,
                 preserve_abstentions: bool = False) -> list[float]:
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
        rec = (_recommendation_signal(entry) if preserve_abstentions
               else _recommended(entry))
        if rec is None:
            # Without a readable recommendation/decline, revealed quality has
            # its base-rate likelihood p and therefore cannot identify q.
            continue
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

    parse_tri = runtime_flags.enabled("GLEE_PERS_PARSE_TRI")
    current = {"seller_message": state.get("seller_message")}
    recommended_now = (_recommendation_signal(current) if parse_tri
                       else _recommended(current))
    post = _q_posterior(history, p, mode, preserve_abstentions=parse_tri)

    # TRI-STATE PARSER CORRECTION (flagged off by default). On Test 1's actual
    # buyer-v2 path, 38 of 2,640 messages were misread: all 38 were warnings
    # coerced into recommendations, with zero false negatives. We bought 15,
    # every one revealed low quality, for a realised loss of 4,040,700;
    # GLEE_PERS_PARSE_V2 fixes only 4 of the 38. At v=1.2 a bad buy costs five
    # times a missed good buy, so optimistic coercion has the wrong asymmetry.
    #
    # Under GLEE_PERS_PARSE_TRI, False remains readable negative evidence and
    # is also a final hard veto. None has no modeled likelihood ratio for either
    # quality or seller type: marginalising the unreadable semantic signal leaves
    # P(high) at the known base rate p and leaves the q posterior unchanged. The
    # normal buyer-v2 guards may still reject, but no bonus may buy an abstention
    # below the base-rate breakeven p >= (price-u)/(v-u), i.e. p >= 1/v when
    # price=1 and low quality is worth u=0.

    # The CURRENT message is itself evidence about q and must reweight the
    # mixture before P(high|message) is read off it -- a pure spammer almost
    # never says "no", so a "no" collapses the q=1 mass instead of letting
    # P(high|no,q=1)~1 ride into the average. The audit measured the unweighted
    # version buying on explicit declines 688 times across the logged games at
    # -0.65x price a piece.
    if recommended_now is None:
        post_now = list(post)
    else:
        post_now = []
        for w, q in zip(post, _Q_GRID):
            pr_yes = p * (1.0 - _EPS) + (1.0 - p) * q
            post_now.append(w * (pr_yes if recommended_now else (1.0 - pr_yes)))
        z = sum(post_now)
        post_now = [x / z for x in post_now] if z > 1e-12 else list(post)

    # P(high | this seller's current message), mixed over the type posterior.
    if recommended_now is None:
        p_high = p
    else:
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
                 and str(h.get("quality", "")).lower() == "low"
                 and ((_recommendation_signal(h) is True) if parse_tri
                      else _recommended(h)))

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
    if (audit > 0.0 and observed == 0 and rounds_remaining > 0 and not tight
            and recommended_now is not None):
        bonus = audit * price * (rounds_remaining / max(total, 1))

    buy = (not blocked) and (expected + bonus >= threshold)

    rank_gate_extra: dict = {}
    # CONTINUATION-AWARE RANK GATE (see _rank_dp). Scoped to `tight` cells only,
    # which is the entire safety argument: tight means breakeven >= 0.75, i.e.
    # r <= 1.333, and on the live (1.2, 1.25, 2, 3, 4) x (1/3, 0.5, 0.8) grid the
    # set {tight} and {p*r > 1} are DISJOINT. So this provably cannot reach the
    # buyer p*r>1 cell we already win at 0.5521, and being buyer-only it cannot
    # reach seller p*r<1 at 0.6505. Do not relax the `tight` guard.
    _rg = runtime_flags.as_float("GLEE_PERS_RANK_GATE_AB", 0.0)
    if (tight and math.isfinite(_rg) and _rg > 0.0
            and rank_gate_assignment(game.get("game_id"))):
        _samples = _cell_samples(state, game.get("your_player"))
        # The threshold is lowest at the horizon (0.50-0.54) exactly where the
        # measured P(high|recommended) collapses -- 0.88 -> 0.699 at margin <0.5.
        # Letting the DP-only branch fire there buys the seller's endgame dump,
        # so the last three rounds keep the money gate.
        _late = round_no > max(1, total - 3)
        if _samples and not _late and recommended_now is not None:
            _a = sum(1 for h in history if h.get("bought")
                     and str(h.get("quality", "")).lower() == "high")
            _b = sum(1 for h in history if h.get("bought")
                     and str(h.get("quality", "")).lower() == "low")
            _recs = sum(1 for h in history
                        if ((_recommendation_signal(h) is True) if parse_tri
                            else _recommended(h)))
            _declines = sum(1 for h in history
                            if ((_recommendation_signal(h) is False) if parse_tri
                                else not _recommended(h)))
            # Shrunk prefix recommendation rate: four pseudo-observations keep a
            # one-round prefix from asserting a rate of 0 or 1.
            _m = (_recs + 4.0) / ((round_no - 1) + 4.0)
            _m = min(max(_m, 1e-6), 1.0)
            _q = min(1.0, p / _m) if _m > 0 else 1.0
            _thr = _q_rank_threshold(_samples, round_no, total, _a, _b,
                                     v, u, price, _m, _q)
            if _thr is not None:
                # The second clause scopes the weaker rank bar to sellers who
                # have shown they will decline: it costs 0.0017 of the gain and
                # stops the rule from acting on a pure spammer, whose every
                # "yes" carries no information at all.
                _ok = p_high >= _thr and (p_high >= breakeven or _declines >= 1)
                rank_gate_extra = {"rank_gate_arm": True,
                                   "rank_gate_threshold": round(_thr, 4),
                                   "rank_gate_flipped": _ok != buy,
                                   "rank_gate_a": _a, "rank_gate_b": _b,
                                   "rank_gate_m": round(_m, 3)}
                buy = _ok

    # Posterior LOWER-CONFIDENCE-BOUND buying, aimed at exactly the cells the
    # tight-prior gate leaves open: tight (breakeven >= 0.75) hi-prior cells,
    # where the posterior MEAN still clears the price while a fat q-tail says
    # this seller may well be a spammer -- live those cells kept producing
    # -7-class games (3-5 junk buys in a row). Blanket GUARD/STRIKE knobs were
    # arena-tested and LOST to the plain gate; this instead demands that the
    # pessimistic alpha-quantile of P(high|message,q) -- not the mean -- pay
    # for the purchase, and ONLY in the open tight cells. Non-tight cells and
    # gate-blocked cells are untouched.
    lcb_alpha = runtime_flags.as_float("GLEE_PERS_BUYER_LCB", 0.0)
    lcb_extra = {}
    if (0.0 < lcb_alpha < 0.5 and tight and not blocked
            and recommended_now is not None):
        # Per-type P(high | message, q). Monotone in q (decreasing on a "yes",
        # increasing on a "no"), but sort anyway so the quantile is correct by
        # construction rather than by direction bookkeeping.
        vals = []
        for w, q in zip(post_now, _Q_GRID):
            if recommended_now:
                yes_hi = p * (1.0 - _EPS)
                vals.append((yes_hi / max(yes_hi + (1.0 - p) * q, 1e-9), w))
            else:
                no_hi = p * _EPS
                vals.append((no_hi / max(no_hi + (1.0 - p) * (1.0 - q), 1e-9), w))
        vals.sort(key=lambda t: t[0])
        acc = 0.0
        lcb_p_high = vals[-1][0]
        for val, w in vals:
            acc += w
            if acc >= lcb_alpha:
                lcb_p_high = val
                break
        lcb_buy = lcb_p_high * v + (1.0 - lcb_p_high) * u >= threshold
        lcb_extra["lcb_p_high"] = lcb_p_high
        if buy and not lcb_buy:
            lcb_extra["lcb_veto"] = True
        buy = lcb_buy

    # UNINFORMATIVE-SELLER VETO.
    #
    # A seller who never declines carries no information, so P(high | "yes")
    # collapses to the PRIOR. Buying is then profitable only if p >= 1/v, and at
    # p == 1/v it is exactly zero-EV -- there is nothing to learn, because even a
    # perfectly honest seller only returns us to breakeven.
    #
    # Replayed against a real transcript (p=0.8, v=1.25, so 1/v = 0.800 exactly,
    # seller said "yes" all 20 rounds and never once declined):
    #     bought all 20      -500   percentile 0.000   <- what we did, cell WORST
    #     buy r1 then stop   -100   percentile 0.056
    #     never buy at all      0   percentile 0.444   <- correct play
    # Passing every round is worth about +3,550 rating-equivalent in that single
    # game over what we actually did.
    #
    # The test is the seller's DECLINE RATE, not a count of their yeses. An
    # honest seller at prior p declines about (1-p) of the time, so seeing no
    # declines in k rounds has probability p**k -- evidence that accumulates
    # properly. Counting yeses does not: at p=0.8 an honest seller opens
    # "yes, yes" 64% of the time, so a two-yes trigger would abandon most honest
    # sellers in the cell where buying is most profitable.
    #
    # Only fires where the prior does NOT already clear breakeven. At v=2,3,4
    # (breakeven 0.50/0.33/0.25 against priors up to 0.8) buying blind is hugely
    # profitable and this must never touch it.
    _veto = runtime_flags.as_float("GLEE_PERS_UNINFORMED_VETO", 0.0)
    if _veto > 0.0 and buy and v > 0:
        _breakeven_p = price / v if v else 1.0
        _margin = p - _breakeven_p
        if _margin <= _veto:
            _their = [r for r in (state.get("history") or []) if isinstance(r, dict)]
            if parse_tri:
                _signals = [_recommendation_signal(r) for r in _their]
                _seen = [signal for signal in _signals if signal is not None]
                _declines = sum(1 for signal in _seen if signal is False)
            else:
                _seen = [r for r in _their if r.get("seller_message") is not None]
                _declines = sum(
                    1 for r in _seen
                    if reads_as_recommendation(str(r.get("seller_message"))) is False)
            if len(_seen) >= 3 and _declines == 0:
                buy = False
                lcb_extra["uninformed_veto"] = True
                lcb_extra["seller_declines"] = 0
                lcb_extra["prior_margin"] = round(_margin, 4)

    # BUYER SELECTIVITY ARM (default OFF, assigned per game).
    #
    # Live buyer games whose prior money value did not beat price numbered 5,181
    # at the measurement snapshot.  The supplied full-game split associated an
    # eventual no-decline record with percentile .4636 and an eventual decline
    # with .5167, but that split is post-treatment: the buyer cannot know at round
    # one whether a seller will decline later.  This arm tests the reachable rule
    # using only the history available now and never revives a purchase rejected
    # by the existing buyer.
    #
    # A decline is NOT trusted as a costly signal.  While this arm is waiting, a
    # seller's yes would be refused too, so a round-one no costs it no on-path
    # sale and can launder the q posterior.  The treatment therefore combines:
    #   1. no purchase before an explicit historical decline;
    #   2. current message must be an explicit recommendation;
    #   3. posterior-mean P(high|recommend) must STRICTLY clear money breakeven;
    # A separately randomised, default-off STRIKE_AB can add a fourth condition:
    # after the first bought low unit, no more purchases in this game.  Against
    # decline-on-high/recommend-on-low this caps direct loss at one product price,
    # but the oldest 5,181-game fixed-stream proxy fell from +.01445 without the
    # stop to +.01209 with it while removing 5,604 more purchases.  The independent
    # game hash therefore makes the insurance cost identifiable instead of
    # silently bundling it into this arm.  Seller adaptation still makes either
    # historical shadow non-causal.
    #
    # The estimator remains the field-fitted bimodal q-grid posterior above
    # (4,191 games in models/pers_buyer_prior_v1.json), not a Beta/Laplace fit:
    # the measured seller population has mass near both q=0 and q=1, which a
    # single Beta family erases.  No supplied measurement identifies a positive
    # probability margin, and the earlier blanket guard/LCB arms measured
    # negative, so the pre-registered first arm uses margin 0.0 plus strict `>`.
    # The 23 Aug rank audit does not justify replacing this money check with the
    # raw one-step CDF threshold: at empirical cell medians rank was looser in
    # 8/18 cells, stricter in 9/18, and tied in one; over all 27,493 historical
    # purchase states it was stricter 16,973 times versus money's 9,843.  Only 13
    # full-candidate vetoes were attributable to this check after earlier gates.
    # More fundamentally, F(S) is a terminal threshold while these are 20-round
    # decisions whose purchase changes both future payoff and revealed evidence.
    # The code therefore keeps the explicit money-safety condition; a randomized
    # final-percentile outcome, not a myopic F(S) substitution, would test it.
    # A later margin remains live-tunable but is read only inside treatment, so it
    # cannot contaminate the hash-control decision.
    selectivity_extra = {}
    prior_value = p * v + (1.0 - p) * u
    value_scale = max(1.0, abs(price), abs(prior_value))
    prior_not_profitable = prior_value <= price + 1e-9 * value_scale
    if v > u and price > u and prior_not_profitable:
        selectivity_arm = _buyer_selectivity_arm(game.get("game_id"))
        if selectivity_arm is not None:
            selectivity_extra["buyer_selectivity_arm"] = (
                "candidate" if selectivity_arm else "control")
            selectivity_extra["buyer_selectivity_prior_value"] = prior_value
            strike_arm = _buyer_selectivity_strike_arm(game.get("game_id"))
            selectivity_extra["buyer_selectivity_strike_arm"] = (
                "off" if strike_arm is None
                else ("strike" if strike_arm else "no-strike"))
            if selectivity_arm:
                selectivity_margin = runtime_flags.as_float(
                    "GLEE_PERS_BUYER_SELECTIVITY_MARGIN", 0.0)
                if not 0.0 <= selectivity_margin <= 1.0:
                    selectivity_margin = 0.0
                signals = [_recommendation_signal(entry) for entry in history]
                declines = sum(signal is False for signal in signals)
                caught_low = any(
                    entry.get("bought")
                    and str(entry.get("quality", "")).lower() == "low"
                    for entry in history
                )
                # Do not reuse ``recommended_now`` here.  With the legacy
                # parser stack an ambiguous string is intentionally coerced to
                # True for the control policy; this treatment's safety claim
                # requires an actually readable positive signal.
                selectivity_current = _recommendation_signal(current)
                # The treatment likewise keeps parser abstentions out of its
                # q likelihood even when the legacy control parser is live.
                # Otherwise unreadable historical copy would be silently
                # counted as a recommendation and the asserted estimator would
                # differ by fleet flag stack.
                selectivity_post = _q_posterior(
                    history, p, mode, preserve_abstentions=True)
                if selectivity_current is None:
                    selectivity_p_high = p
                else:
                    selectivity_post_now = []
                    for weight, q in zip(selectivity_post, _Q_GRID):
                        pr_yes = p * (1.0 - _EPS) + (1.0 - p) * q
                        likelihood = (pr_yes if selectivity_current
                                      else (1.0 - pr_yes))
                        selectivity_post_now.append(weight * likelihood)
                    selectivity_z = sum(selectivity_post_now)
                    if selectivity_z > 1e-12:
                        selectivity_post_now = [
                            weight / selectivity_z
                            for weight in selectivity_post_now
                        ]
                    else:
                        selectivity_post_now = list(selectivity_post)
                    selectivity_p_high = 0.0
                    for weight, q in zip(selectivity_post_now, _Q_GRID):
                        if selectivity_current:
                            numerator = p * (1.0 - _EPS)
                            denominator = numerator + (1.0 - p) * q
                        else:
                            numerator = p * _EPS
                            denominator = numerator + (1.0 - p) * (1.0 - q)
                        selectivity_p_high += (
                            weight * numerator / max(denominator, 1e-9))
                posterior_gap = selectivity_p_high - breakeven
                reason = None
                if strike_arm is True and caught_low:
                    reason = "bought_low_strike"
                elif declines == 0:
                    reason = "no_prior_decline"
                elif selectivity_current is not True:
                    reason = "current_not_explicit_yes"
                elif posterior_gap <= selectivity_margin:
                    reason = "posterior_not_strictly_profitable"

                selectivity_extra.update({
                    "buyer_selectivity_margin": selectivity_margin,
                    "buyer_selectivity_declines": declines,
                    "buyer_selectivity_caught_low": caught_low,
                    "buyer_selectivity_p_high": selectivity_p_high,
                    "buyer_selectivity_posterior_gap": posterior_gap,
                })
                if buy and reason is not None:
                    buy = False
                    selectivity_extra["buyer_selectivity_veto"] = reason
                    if runtime_flags.enabled("GLEE_TRACE_GATES"):
                        selectivity_extra["gates_fired"] = ["buyer_selectivity"]

    parser_extra = {}
    if parse_tri and recommended_now is False:
        # Apply last so no posterior, audit, or optional LCB path can revive an
        # explicit instruction not to buy.
        buy = False
        parser_extra["parser_decline_veto"] = True
    elif parse_tri and recommended_now is None:
        parser_extra["parser_abstained"] = True
        if expected < price:
            buy = False
            parser_extra["parser_prior_below_breakeven"] = True

    return {
        **lcb_extra,
        **selectivity_extra,
        **parser_extra,
        **rank_gate_extra,
        "price": price, "p": p, "v": v, "u": u,
        "recommended": recommended_now,
        "p_high": p_high, "expected_value": expected,
        "q_posterior": [round(x, 3) for x in post_now],
        "observed_rounds": observed, "caught_lies": caught,
        "breakeven": breakeven, "tight": tight, "blocked": blocked,
        "exploration_bonus": bonus,
        "round": round_no, "total_rounds": total,
        "buyer_v2": True,
        "buy": buy,
    }


def buyer_plan(game: dict, cfg) -> dict:
    state = game["game_state"]
    price = _num(state.get("product_price"), 0.0)
    p = _num(state.get("p"), 0.5)
    v = _num(state.get("v"), 0.0)
    u = _num(state.get("u"), 0.0)
    round_no, total = _rounds(state)

    parse_tri = runtime_flags.enabled("GLEE_PERS_PARSE_TRI")
    current = {"seller_message": state.get("seller_message")}
    recommended_now = (_recommendation_signal(current) if parse_tri
                       else _recommended(current))

    # Quality is observed only on rounds we bought, so only those inform the
    # honesty estimate. Smooth toward the prior while the sample is tiny.
    hits = misses = 0
    if recommended_now is not None:
        for entry in state.get("history") or []:
            if not isinstance(entry, dict) or not entry.get("bought"):
                continue
            historical = (_recommendation_signal(entry) if parse_tri
                          else _recommended(entry))
            if historical != recommended_now:
                continue                   # compare like with like
            if str(entry.get("quality", "")).lower() == "high":
                hits += 1
            elif str(entry.get("quality", "")).lower() == "low":
                misses += 1

    observed = hits + misses
    if recommended_now is None:
        prior_high = p
    else:
        prior_high = p if recommended_now else p / 2.0
    p_high = ((hits + _PRIOR_STRENGTH * prior_high)
              / (observed + _PRIOR_STRENGTH))
    expected = p_high * v + (1.0 - p_high) * u

    # Information has value while rounds remain: a purchase is the only way to
    # learn this seller's honesty, and that knowledge pays off on every later
    # round. Worth a small deficit early, nothing at the end.
    rounds_remaining = max(0, total - round_no)
    exploration = 0.0
    if observed < 2 and rounds_remaining > 0 and recommended_now is not None:
        exploration = price * 0.10 * min(1.0, rounds_remaining / max(1, total))

    buy = expected + exploration >= price
    parser_extra = {}
    if parse_tri and recommended_now is False:
        buy = False
        parser_extra["parser_decline_veto"] = True
    elif parse_tri and recommended_now is None:
        parser_extra["parser_abstained"] = True
        if expected < price:
            buy = False
            parser_extra["parser_prior_below_breakeven"] = True

    return {
        **parser_extra,
        "price": price, "p": p, "v": v, "u": u,
        "recommended": recommended_now,
        "p_high": p_high, "expected_value": expected,
        "observed_rounds": observed, "hits": hits, "misses": misses,
        "exploration_bonus": exploration,
        "round": round_no, "total_rounds": total,
        "buy": buy,
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
        # PRIOR-CONDITIONAL STYLE. Deploying `token` globally was my error and it
        # cost us live. The evidence I acted on -- "binary mode converts 89% at
        # p=0.8 against text mode's 61%" -- compares two different GAMES, not two
        # different messages. In binary mode "yes" IS the protocol, the only
        # thing a seller can say. Dropped into a text channel where prose is
        # expected it reads as low-effort and carries no evidence at all.
        #
        # Measured within TEXT MODE, on rounds where we pushed the sale, from
        # the live turn stream:
        #     p=0.33   token 49.6% +/-4.9   prose 41.7% +/-2.0   token WINS
        #     p=0.50   token 53.5% +/-5.3   prose 53.4% +/-1.9   a tie
        #     p=0.80   token 60.8% +/-5.2   prose 69.3% +/-1.5   token LOSES 8.5pp
        # And p=0.8 is our highest-volume seller cell (196 games in six hours).
        # The high prior is exactly where it hurts: the buyer is already inclined
        # to buy and only wants a reason, and "yes" gives them none.
        #
        # So the token is right where the buyer needs BREVITY and wrong where
        # they need EVIDENCE. Above this prior, fall back to prose.
        # seller_plan does not carry the prior, so read it from the state.
        _cut = runtime_flags.as_float("GLEE_PERS_TOKEN_MAX_P", 0.0)
        if style == "token" and _cut > 0.0:
            _prior = (game.get("game_state") or {}).get("p")
            if isinstance(_prior, (int, float)) and _prior > _cut + 1e-9:
                style = "plain"
                p["style_downgraded"] = True
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

    # RANK-BUY ARM (see _rank_buy_arm). One-directional by construction: it may
    # only convert a refusal into a purchase inside the p*r <= threshold cell it
    # is scoped to, so no cell we already win can be damaged by it, and a game
    # the buyer already wanted to buy is left exactly as the buyer decided.
    if not p.get("buy") and _rank_buy_arm(game):
        p["buy"] = True
        p["rank_buy_arm"] = True
        p.setdefault("gates_fired", []).append("rank_buy")

    return {"decision": "yes" if p["buy"] else "no", "_plan": p}

_DP_STATE = {"checked": 0.0, "mtime": None, "doc": None}
_DP2_STATE = {"checked": 0.0, "mtime": None, "doc": None}
_DP3_STATE = {"checked": 0.0, "mtime": None, "doc": None}


def _dp_policy_v3():
    return _cached_model("pers_policy_dp_v3.json", _DP3_STATE)


def _cached_model(filename, cache):
    """mtime-cached model read, checked at most once every 10s."""
    import os as _os, time as _time, json as _json
    path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__)))), "models", filename)
    now = _time.monotonic()
    if now - cache["checked"] < 10.0:
        return cache["doc"]
    cache["checked"] = now
    try:
        mtime = _os.stat(path).st_mtime_ns
    except OSError:
        return cache["doc"]
    if mtime == cache["mtime"]:
        return cache["doc"]
    try:
        doc = _json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return cache["doc"]
    if isinstance(doc, dict) and doc.get("cells"):
        cache.update(mtime=mtime, doc=doc)
    return cache["doc"]


def _dp_v3_plan(state, p, v, price, round_no, total, buy_rate):
    """The v3 decision for a LOW-quality round, or None to fall through.

    State is what the SELLER has done -- lies told, declines shown, rounds
    elapsed -- plus the sales banked so far, which the percentile objective
    needs because the value of one more sale depends on where the total already
    sits on the field CDF.  None of these is the v1 lies-CAUGHT counter, which
    only moved when the buyer bought and so measured the buyer rather than us.
    """
    dp = _dp_policy_v3()
    if not dp:
        return None
    pb_ = "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")
    rb_ = min((1.2, 1.25, 2.0, 3.0, 4.0),
              key=lambda g_: abs(g_ - (v / price if price else 0)))
    cell = (dp.get("cells") or {}).get(f"{mode_of(state)}|{pb_}|r{rb_}")
    if not cell:
        return None
    told = nos = sales = 0
    for _r in state.get("history") or []:
        if not isinstance(_r, dict):
            continue
        positive = _looks_positive(_r.get("seller_message"))
        if positive:
            if str(_r.get("quality")).lower() == "low":
                told += 1
        else:
            nos += 1
        if _r.get("bought"):
            sales += 1
    t = min(round_no - 1, int(dp.get("rounds", 20)) - 1)
    if t < 0:
        return None
    row = (cell.get("policy") or {}).get(f"{t}|{told}|{nos}")
    if not row:
        return None
    lie_now = row[min(sales, len(row) - 1)] == "1"
    return {"recommend": lie_now, "reason": "dp v3: percentile-optimal on low quality",
            "round": round_no, "total_rounds": total, "buy_rate": buy_rate,
            "knows_values": True, "lie_rate": 1.0 if lie_now else 0.0,
            "quality_is_high": False, "dp": True, "dp_v3": True,
            "dp_state": {"t": t, "told": told, "nos": nos, "sales": sales}}


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
