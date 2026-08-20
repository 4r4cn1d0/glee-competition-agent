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

    p = buyer_plan(game, cfg)
    return {"decision": "yes" if p["buy"] else "no", "_plan": p}
