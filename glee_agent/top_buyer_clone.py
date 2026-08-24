"""Observed-leader negotiation policy for the buyer seat.

This is intentionally an experiment, not a claim that private source code was
recovered.  The public state and our direct transcripts identify the leaders'
wire actions exactly in some cells and not in others.  Treatment games replay
only the identified regularities; controls keep the complete current stack.

Why buyer-only: in the operator's 63-game official window sellers earned
``+47.9`` while buyers lost ``-24.4``.  Buyer no-deals alone lost ``-22.5``.
Replacing the seller policy would overwrite the half that is already winning.

The two measured pieces are:

* Complete information: Athena, 7aidara_Gamma, and opus 5(4) opened at roughly
  96--98.5% of the visible zone.  Their observed cap-10 terminal claims were
  75.8%, 77.4%, and 65.0%; the frozen pointwise median path below copies that
  common level rather than our 50% median.
* Hidden information: two completed Clod buyer-1.2B games used first-four
  normalized paths whose midpoint was
  ``[.6786404167,.6788316667,.6838475,.71674625]`` and then bid ``1.008B``.
  The seller cost was ``1.0B``, so that final wire left the seller ``.008B``
  and captured 96% of the .2B zone.  Literal .677B and 1.015B openings from
  other top agents match the same own-value scaling for buyer 1.0B/1.5B.

The cross-type hidden terminal rule is therefore an explicit extrapolation:
bid .008B above the next lower support point.  It is randomized per game and
reported separately by own type; no selected agreement is treated as causal
proof.
"""

from __future__ import annotations

import hashlib
import math

from . import pricing, runtime_flags


SALT = "nego_top_buyer_clone_v1|"
EPS_SHARE = 0.008
HIDDEN_EARLY = (
    0.6786404167,
    0.6788316667,
    0.6838475000,
    0.7167462500,
)

# Pointwise median of the three directly observed cap-10 leader paths.  The
# fifth point is the median terminal claim (Athena .758, 7aidara .774, opus
# .650), not a fitted smooth curve.
COMPLETE_CAP10 = (0.970000, 0.969875, 0.968600, 0.951000, 0.758000)

# Unknown-horizon direct paths disagree on speed but share their high level.
# This table follows the observed median while all three paths overlap and then
# holds 7aidara's observed .681 endpoint, inside the measured .64--.77 leader
# settlement band.  It is frozen before live use.
COMPLETE_UNKNOWN = (0.9600, 0.9504, 0.9486, 0.9368, 0.8922, 0.7708, 0.6810)

_MULTS = (0.8, 1.0, 1.2, 1.5)


def _num(value, default=math.nan) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def treatment_assignment(game_id) -> bool | None:
    """Stable candidate bit recoverable from the game id alone."""
    gid = str(game_id or "")
    if not gid:
        return None
    digest = hashlib.sha256((SALT + gid).encode()).hexdigest()
    return bool(int(digest, 16) & 1)


def enabled() -> bool:
    return runtime_flags.enabled("GLEE_NEGO_TOP_BUYER_CLONE_AB")


def _seat(game: dict):
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player")
    if me not in ("player_1", "player_2"):
        return None
    other = "player_2" if me == "player_1" else "player_1"
    if state.get(f"{me}_role") != "buyer":
        return None
    own_value = _num(state.get(f"{me}_value"))
    base = pricing.infer_base(own_value) if math.isfinite(own_value) else None
    if base is None:
        return None
    own_mult = next(
        (m for m in _MULTS if abs(own_value / base - m) <= 1e-6),
        None,
    )
    if own_mult is None:
        return None
    return state, me, other, own_value, base, own_mult


def eligible(game: dict) -> bool:
    """The clone owns every well-formed negotiation buyer decision/offer."""
    if game.get("game_family") != "negotiation":
        return False
    if (game.get("valid_actions") or {}).get("type") not in ("offer", "decision"):
        return False
    return _seat(game) is not None and bool(game.get("game_id"))


def owns(game: dict) -> bool:
    """True only for hash-candidate buyer games while the arm is live."""
    try:
        return (enabled() and eligible(game)
                and treatment_assignment(game.get("game_id")) is True)
    except Exception:
        return False


def _own_price_count(state: dict, me: str) -> int:
    """Count our prior distinct price utterances, collapsing record echoes."""
    seen = []
    previous = None
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if not isinstance(offer, dict) or offer.get("from_player") != me:
                continue
            price = _num(offer.get("price"))
            if not math.isfinite(price):
                continue
            marker = (round(price, 8), offer.get("round"))
            if marker != previous:
                seen.append(marker)
                previous = marker
    return len(seen)


def _final_round(state: dict) -> bool:
    return (state.get("horizon_known") is True
            and _num(state.get("round"), -1) >= _num(state.get("max_rounds"), math.inf))


def _hidden_boundary(base: float, own_mult: float) -> float | None:
    """Top-buyer terminal: .008B above the next lower support point."""
    lower = {1.0: 0.8, 1.2: 1.0, 1.5: 1.2}.get(own_mult)
    return None if lower is None else (lower + EPS_SHARE) * base


def _hidden_target(state: dict, me: str, own_value: float,
                   base: float, own_mult: float) -> tuple[float, float | None]:
    index = _own_price_count(state, me)
    boundary = _hidden_boundary(base, own_mult)
    if boundary is None:
        # Buyer .8B has no rational seller below it.  A positive-cent bid keeps
        # an irrational seller exploitable without offering a loss.
        safe = max(0.0, own_value - 0.01)
        return safe, None
    if index < len(HIDDEN_EARLY):
        target = own_value * HIDDEN_EARLY[index]
    else:
        target = boundary
    # The observed sequence is monotone toward the support boundary.  Guarding
    # the literal price also prevents a malformed scale from crossing our value.
    target = min(max(target, 0.0), boundary, own_value - 0.01)
    return target, boundary


def _complete_target(state: dict, me: str, other: str,
                     own_value: float) -> tuple[float, float | None]:
    seller_value = _num(state.get(f"{other}_value"))
    span = own_value - seller_value
    if not math.isfinite(seller_value) or span <= 0.0:
        return max(0.0, own_value - 0.01), None
    index = _own_price_count(state, me)
    if state.get("horizon_known") is True:
        maximum = _num(state.get("max_rounds"), 10.0)
        path = COMPLETE_CAP10 if maximum > 1.0 else (COMPLETE_CAP10[0],)
    else:
        path = COMPLETE_UNKNOWN
    share = path[min(index, len(path) - 1)]
    floor_share = path[-1]
    target = own_value - share * span
    accept_ceiling = own_value - floor_share * span
    return target, accept_ceiling


def _target(game: dict) -> tuple[float, float | None, tuple] | None:
    seat = _seat(game)
    if seat is None:
        return None
    state, me, other, own_value, base, own_mult = seat
    if state.get("complete_information") is True:
        target, ceiling = _complete_target(state, me, other, own_value)
    else:
        target, ceiling = _hidden_target(state, me, own_value, base, own_mult)
    return max(0.0, round(target, 2)), ceiling, seat


def action(game: dict) -> dict | None:
    """Return the full buyer move for an owned treatment game."""
    resolved = _target(game)
    if resolved is None:
        return None
    target, accept_ceiling, seat = resolved
    state, me, _other, own_value, _base, own_mult = seat
    phase = (game.get("valid_actions") or {}).get("type")
    plan = {"source": "top_buyer_clone", "target": target,
            "accept_ceiling": accept_ceiling, "own_mult": own_mult}

    if phase == "offer":
        return {"product_price": target, "_plan": plan}

    if phase != "decision":
        return None
    offered = _num((state.get("last_offer") or {}).get("price"))
    if not math.isfinite(offered):
        return {"decision": "RejectOffer", "product_price": target,
                "_plan": plan}
    gain = own_value - offered

    # At an actual terminal receiver node there is no next counter.  The field
    # accepted every recorded terminal offer leaving a positive amount and none
    # leaving zero, so preserve that exact boundary behavior.
    if _final_round(state):
        decision = "AcceptOffer" if gain > 0.0 else "RejectOffer"
        return {"decision": decision, "_plan": plan}

    if gain > 0.0 and accept_ceiling is not None and offered <= accept_ceiling + 1e-9:
        return {"decision": "AcceptOffer", "_plan": plan}

    # Athena walked after eight hidden unknown-horizon buyer prices while the
    # seller remained outside its boundary.  That exact stopping observation is
    # copied only in the same information/horizon regime.
    if (state.get("complete_information") is False
            and state.get("horizon_known") is False
            and _own_price_count(state, me) >= 8):
        return {"decision": "WalkAway", "_plan": plan}

    return {"decision": "RejectOffer", "product_price": target, "_plan": plan}
