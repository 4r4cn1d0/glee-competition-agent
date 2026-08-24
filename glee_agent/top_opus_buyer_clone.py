"""Default-off, buyer-only reconstruction of the observed Opus policy.

This module is deliberately not wired into negotiation dispatch.  It is a
standalone prospective arm: a caller may use :func:`owns` and then accept the
result of :func:`action`, falling through to the current control policy when
``None`` is returned.  That fallback is part of the contract.  The 172-game
direct corpus identifies several submitted-price wires, but it does not
identify every late decision that produced them.

Evidence boundary
-----------------

* Point-identified wires: complete-information cap-10 first four buyer prices,
  hidden cap-10 first four buyer prices, and the first 43 hidden
  unknown-horizon buyer prices.  These constants reproduce the observed wire
  prices after the platform's cent rounding; they are not fitted curves.
* Inferred own-type mapping: hidden transcripts conceal the Opus buyer value.
  Agreement payoffs identify some types and the three scale-equivalent opening
  families identify the remaining mapping.  Applying a normalized family to
  our visible own type is therefore an explicit randomized hypothesis.
* Unidentified late branches: complete cap-10 fifth prices used three different
  seller-zone shares (.02, .10, .20); hidden cap-10 fifth prices switched to an
  .824B floor / .68666667-of-own-value rule; and hidden unknown-horizon paths
  reset after coefficient 43.  Opponent state did not identify those branch
  choices.  This module returns ``None`` there so control remains authoritative.

No bargaining symbol is imported and bargaining games are never eligible.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

from . import pricing, runtime_flags


FLAG = "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB"
CONFLICTING_FLAG = "GLEE_NEGO_TOP_BUYER_CLONE_AB"
SALT = "nego_top_opus_buyer_clone_v1|"
PLAN_SOURCE = "top_opus_buyer_clone"

# Both private values are visible in this cell, so these seller-zone shares are
# point identified.  In the B=1,000,000 trace they submit exactly 806000.00,
# 806058.53, 806936.44, and 810740.74 for seller=.8B, buyer=1.0B.
COMPLETE_CAP10_FIRST_FOUR = (
    0.03000000,
    0.03029265,
    0.03468220,
    0.05370370,
)

# Evidence-only: fifth complete/cap-10 wires landed on all three shares below.
# Their public states do not select among them, so _wire_target never reads this
# tuple.  Keeping the observations explicit prevents a later maintainer from
# mistaking the first four coefficients for an accidentally truncated curve.
COMPLETE_CAP10_UNIDENTIFIED_FIFTH_SHARES = (0.02, 0.10, 0.20)

# The prices are point identified; expressing the shared path as a fraction of
# *our* hidden buyer value uses the inferred private-type mapping described in
# the module docstring.  High-scale wires retain enough precision to reproduce
# every lower-scale, cent-rounded observation.
HIDDEN_CAP10_FIRST_FOUR = (
    0.676666666667,
    0.677075141667,
    0.683202258333,
    0.709753083333,
)

# Evidence-only fifth-wire coefficients, expressed as price / inferred own
# buyer value.  The 1.0 path used .824; the 1.2 and 1.5 paths used .68666667.
# The paths are observed, but the hidden state selecting them is not, so action
# falls through rather than reading this mapping.
HIDDEN_CAP10_UNIDENTIFIED_FIFTH_BY_TYPE = (
    (1.0, 0.824000000000),
    (1.2, 0.686666666667),
    (1.5, 0.686666666667),
)

# Exact first 43 hidden, unknown-horizon price coefficients, normalized by the
# inferred Opus buyer value.  The observed post-43 .824B reset and later
# .84416667-of-own-value branch are intentionally absent: their state selector
# is unidentified, so extrapolating them would no longer be an observed clone.
HIDDEN_UNKNOWN_COEFFICIENTS = (
    0.67666667,
    0.67666670,
    0.67666713,
    0.67666902,
    0.67667410,
    0.67668483,
    0.67670432,
    0.67673643,
    0.67678568,
    0.67685730,
    0.67695722,
    0.67709207,
    0.67726916,
    0.67749652,
    0.67778287,
    0.67813761,
    0.67857086,
    0.67909342,
    0.67971681,
    0.68045323,
    0.68131557,
    0.68231744,
    0.68347313,
    0.68479763,
    0.68630663,
    0.68801653,
    0.68994440,
    0.69210803,
    0.69452589,
    0.69721717,
    0.70020174,
    0.70350016,
    0.70713372,
    0.71112436,
    0.71549477,
    0.72026829,
    0.72546899,
    0.73112162,
    0.73725163,
    0.74388518,
    0.75104911,
    0.75877097,
    0.76707899,
)

# Evidence-only unknown-horizon tail: six wires used
# max(.824B, .68666667 * own_value), followed in the longest trajectory by
# .84416667 * own_value.  These are literal observations, not active policy;
# the reconstruction does not identify why the reset fired at that point.
HIDDEN_UNKNOWN_UNIDENTIFIED_HOLD_COUNT = 6
HIDDEN_UNKNOWN_UNIDENTIFIED_B_FLOOR = 0.824000000000
HIDDEN_UNKNOWN_UNIDENTIFIED_OWN_COEFFICIENT = 0.686666666667
HIDDEN_UNKNOWN_UNIDENTIFIED_FINAL_COEFFICIENT = 0.844166670000

HIDDEN_TRAJECTORY_TYPES = (1.0, 1.2, 1.5)
BUYER_MESSAGE_TEMPLATE = (
    "{price} is what this is worth to me. "
    "Above that the purchase stops making sense."
)


@dataclass(frozen=True)
class _Context:
    state: dict
    me: str
    other: str
    phase: str
    complete: bool
    horizon_known: bool
    max_rounds: int | None
    round_no: int
    messages_allowed: bool
    own_value: float
    other_value: float | None
    base: float
    own_mult: float
    own_price_count: int
    incoming: float | None


def _number(value) -> float | None:
    """Strict finite-number parser; booleans and numeric strings fail closed."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def _positive_int(value) -> int | None:
    parsed = _number(value)
    if parsed is None or parsed < 1.0 or not parsed.is_integer():
        return None
    return int(parsed)


def _multiplier(value: float, base: float) -> float | None:
    return next(
        (mult for mult in (0.8, 1.0, 1.2, 1.5)
         if abs(value / base - mult) <= 1e-6),
        None,
    )


def treatment_assignment(game_id) -> bool | None:
    """Return a stable candidate bit recoverable from a valid game id alone."""
    if not isinstance(game_id, str) or not game_id.strip():
        return None
    digest = hashlib.sha256((SALT + game_id).encode("utf-8")).digest()
    return bool(digest[-1] & 1)


def enabled() -> bool:
    """The new arm is inert, including while the older full clone is armed."""
    return (runtime_flags.enabled(FLAG)
            and not runtime_flags.enabled(CONFLICTING_FLAG))


def _history_price_count(state: dict, me: str, round_no: int) -> int | None:
    history = state.get("history")
    if not isinstance(history, list):
        return None

    # Some records echo a counter as the next round's offer.  Count a wire once
    # by (round, price), while preserving genuine repeated holds in later rounds.
    seen: set[tuple[int, float]] = set()
    for entry in history:
        if not isinstance(entry, dict):
            return None
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if offer is None or not isinstance(offer, dict):
                continue
            if offer.get("from_player") != me:
                continue
            price = _number(offer.get("price"))
            offer_round = _positive_int(offer.get("round", entry.get("round")))
            if (price is None or price < 0.0 or offer_round is None
                    or offer_round >= round_no):
                return None
            seen.add((offer_round, round(price, 8)))
    return len(seen)


def _context(game: dict) -> _Context | None:
    """Parse only a complete, internally consistent negotiation-buyer state."""
    if not isinstance(game, dict) or game.get("game_family") != "negotiation":
        return None
    if treatment_assignment(game.get("game_id")) is None:
        return None
    state = game.get("game_state")
    valid = game.get("valid_actions")
    if not isinstance(state, dict) or not isinstance(valid, dict):
        return None
    if state.get("game_family") != "negotiation":
        return None

    phase = valid.get("type")
    if phase not in ("offer", "decision"):
        return None
    me = state.get("current_player")
    if me not in ("player_1", "player_2") or game.get("your_player") != me:
        return None
    other = "player_2" if me == "player_1" else "player_1"
    if state.get(f"{me}_role") != "buyer" or state.get(f"{other}_role") != "seller":
        return None

    complete = state.get("complete_information")
    horizon_known = state.get("horizon_known")
    messages_allowed = state.get("messages_allowed")
    if (not isinstance(complete, bool) or not isinstance(horizon_known, bool)
            or not isinstance(messages_allowed, bool)):
        return None

    round_no = _positive_int(state.get("round"))
    if round_no is None:
        return None
    max_rounds = None
    if horizon_known:
        max_rounds = _positive_int(state.get("max_rounds"))
        if max_rounds is None or round_no > max_rounds:
            return None

    own_value = _number(state.get(f"{me}_value"))
    if own_value is None or own_value <= 0.0:
        return None
    base = pricing.infer_base(own_value)
    if base is None:
        return None
    own_mult = _multiplier(own_value, base)
    if own_mult is None:
        return None

    other_value = None
    if complete:
        other_value = _number(state.get(f"{other}_value"))
        if (other_value is None or other_value < 0.0
                or pricing.infer_base(other_value) != base):
            return None

    own_price_count = _history_price_count(state, me, round_no)
    if own_price_count is None:
        return None

    incoming = None
    if phase == "decision":
        offer = state.get("last_offer")
        if not isinstance(offer, dict) or offer.get("from_player") != other:
            return None
        incoming = _number(offer.get("price"))
        if incoming is None or incoming < 0.0:
            return None

    return _Context(
        state=state,
        me=me,
        other=other,
        phase=phase,
        complete=complete,
        horizon_known=horizon_known,
        max_rounds=max_rounds,
        round_no=round_no,
        messages_allowed=messages_allowed,
        own_value=own_value,
        other_value=other_value,
        base=base,
        own_mult=own_mult,
        own_price_count=own_price_count,
        incoming=incoming,
    )


def eligible(game: dict) -> bool:
    """Whether the state is a well-formed negotiation buyer turn."""
    try:
        return _context(game) is not None
    except Exception:
        return False


def owns(game: dict) -> bool:
    """Own only well-formed hash-treatment turns with no clone collision."""
    try:
        return (enabled() and treatment_assignment(game.get("game_id")) is True
                and _context(game) is not None)
    except Exception:
        return False


def _wire_target(ctx: _Context) -> tuple[float, str] | None:
    index = ctx.own_price_count

    if ctx.complete:
        if not (ctx.horizon_known and ctx.max_rounds == 10
                and index < len(COMPLETE_CAP10_FIRST_FOUR)):
            return None
        assert ctx.other_value is not None
        span = ctx.own_value - ctx.other_value
        if span <= 0.0:
            return None
        target = ctx.other_value + COMPLETE_CAP10_FIRST_FOUR[index] * span
        regime = "complete_cap10_first_four"
    else:
        # No .8B outgoing trajectory was observed: that inferred type walked in
        # the supported cap-10/unknown states.  Do not synthesize a fourth path.
        if ctx.own_mult not in HIDDEN_TRAJECTORY_TYPES:
            return None
        if ctx.horizon_known and ctx.max_rounds == 10:
            if index >= len(HIDDEN_CAP10_FIRST_FOUR):
                return None
            target = ctx.own_value * HIDDEN_CAP10_FIRST_FOUR[index]
            regime = "hidden_cap10_first_four"
        elif not ctx.horizon_known:
            if index >= len(HIDDEN_UNKNOWN_COEFFICIENTS):
                return None
            target = ctx.own_value * HIDDEN_UNKNOWN_COEFFICIENTS[index]
            regime = "hidden_unknown_observed_prefix"
        else:
            return None

    if not math.isfinite(target) or target < 0.0 or target >= ctx.own_value:
        return None
    return round(target, 2), regime


def _accept_is_identified(ctx: _Context) -> str | None:
    """Return the supporting transcript cell for monotone-better acceptances."""
    offered = ctx.incoming
    if offered is None or offered >= ctx.own_value:
        return None

    # One complete single-round agreement: buyer=1.2B, seller=1.0B accepted
    # 1.078B.  Lower prices are weakly better for the buyer.
    if (ctx.complete and ctx.horizon_known and ctx.max_rounds == 1
            and ctx.own_mult == 1.2 and ctx.other_value == ctx.base
            and offered <= 1.078 * ctx.base + 1e-9):
        return "complete_single_accept_1.078B"

    # Complete unknown-horizon transcripts repeatedly rejected the same offer
    # before accepting it late, so both round and outgoing-count gates matter.
    if (ctx.complete and not ctx.horizon_known
            and ctx.other_value == 0.8 * ctx.base):
        if (ctx.own_mult == 1.2 and ctx.round_no >= 67
                and ctx.own_price_count >= 33
                and offered <= 0.96 * ctx.base + 1e-9):
            return "complete_unknown_accept_1.2_at_67"
        if (ctx.own_mult == 1.5 and ctx.round_no >= 69
                and ctx.own_price_count >= 34
                and offered <= 1.08 * ctx.base + 1e-9):
            return "complete_unknown_accept_1.5_at_69"

    # Two hidden single-round agreements reveal buyer=1.0B from payoff and an
    # accepted .95B price.  Other hidden single-round types remain unidentified.
    if (not ctx.complete and ctx.horizon_known and ctx.max_rounds == 1
            and ctx.own_mult == 1.0
            and offered <= 0.95 * ctx.base + 1e-9):
        return "hidden_single_accept_0.95B"

    # Two hidden unknown-horizon games accepted .8B at round 63 after rejecting
    # that same price through round 61.  Earlier acceptance is not inferred.
    if (not ctx.complete and not ctx.horizon_known and ctx.own_mult == 1.0
            and ctx.round_no >= 63 and ctx.own_price_count >= 31
            and offered <= 0.8 * ctx.base + 1e-9):
        return "hidden_unknown_accept_0.8B_at_63"

    return None


def _walk_is_identified(ctx: _Context) -> str | None:
    """Copy only the immediate hidden .8B walk family reconstructed in logs."""
    offered = ctx.incoming
    if (ctx.complete or offered is None or ctx.own_mult != 0.8
            or ctx.round_no != 1 or ctx.own_price_count != 0
            or offered <= ctx.own_value):
        return None
    # The no-price hidden family walked immediately in both cap-10 and unknown
    # horizons.  Assigning that payoff-hidden family to .8B is inferred from the
    # three observed higher-type price families, not point-identified payoff.
    if (not ctx.horizon_known
            or (ctx.horizon_known and ctx.max_rounds == 10)):
        return "hidden_0.8_immediate_walk"
    return None


def _plan(ctx: _Context, evidence: str, target: float | None = None) -> dict:
    plan = {
        "source": PLAN_SOURCE,
        "evidence": evidence,
        "step": ctx.own_price_count,
        "own_mult": ctx.own_mult,
    }
    if target is not None:
        plan["target"] = target
    return plan


def _format_message_price(price: float) -> str:
    # This matches the direct Opus strings: cents at B=100, and rounded,
    # comma-grouped units at the two larger scales (e.g. 67.67 / 6,767 / 812,000).
    if abs(price) >= 1000.0:
        return f"{price:,.0f}"
    return f"{price:,.2f}".rstrip("0").rstrip(".")


def _with_message(move: dict, ctx: _Context, target: float) -> dict:
    if ctx.messages_allowed:
        move["message"] = BUYER_MESSAGE_TEMPLATE.format(
            price=_format_message_price(target))
    return move


def action(game: dict) -> dict | None:
    """Return one evidence-supported treatment move, else control fallback.

    ``None`` is intentional: it means the caller must execute its unchanged
    control policy.  In particular, no late hold, endpoint acceptance, or walk
    threshold is manufactured merely to make this function total.
    """
    if not owns(game):
        return None
    ctx = _context(game)
    if ctx is None:  # Defensive against a state mutation between the two reads.
        return None

    if ctx.phase == "decision":
        accept_evidence = _accept_is_identified(ctx)
        if accept_evidence is not None:
            return {"decision": "AcceptOffer",
                    "_plan": _plan(ctx, accept_evidence)}

        walk_evidence = _walk_is_identified(ctx)
        if walk_evidence is not None:
            return {"decision": "WalkAway",
                    "_plan": _plan(ctx, walk_evidence)}

    wire = _wire_target(ctx)
    if wire is None:
        return None
    target, regime = wire
    plan = _plan(ctx, regime, target)

    if ctx.phase == "offer":
        return _with_message({"product_price": target, "_plan": plan},
                             ctx, target)

    # Every copied rejection in these prefixes faced a seller price strictly
    # worse than the emitted buyer counter.  At equality or a better incoming
    # price, the corpus does not identify reject versus accept, so use control.
    if ctx.incoming is None or ctx.incoming <= target + 1e-9:
        return None
    return _with_message(
        {"decision": "RejectOffer", "product_price": target, "_plan": plan},
        ctx,
        target,
    )
