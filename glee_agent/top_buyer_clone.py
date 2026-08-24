"""Observed-leader negotiation policy for the buyer seat.

This is intentionally an experiment, not a claim that private source code was
recovered.  The public state and our direct transcripts identify the leaders'
wire actions exactly in some cells and not in others.  Treatment games replay
only the identified regularities; controls keep the complete current stack.

Why buyer-only: in the operator's 63-game official window sellers earned
``+47.9`` while buyers lost ``-24.4``.  Buyer no-deals alone lost ``-22.5``.
Replacing the seller policy would overwrite the half that is already winning.

The two measured pieces are:

* Complete information: 15 games across the four 7aidara labels reproduce the
  same buyer path exactly: start by claiming 96% of the visible zone, then
  concede to 89.8%, 83.6%, 77.4%, and hold 77.4% in cap-10 games.  Unknown
  horizons use the same prefix and reach 71.2% on the fifth bid.
* Hidden information: 7aidara's 30 buyer games reveal four deterministic path
  families.  Their private-type labels are directly identified only at 1.5B,
  so mapping the other monotone paths to .8B/1.0B/1.2B is an explicit
  randomized hypothesis.  The literal price paths, however, are copied rather
  than fitted or smoothed.

The same incoming price can be rejected repeatedly and accepted later in the
leader corpus, so a static reservation-price model is false.  This treatment
keeps decision state explicit and is reported separately by own type; no
selected agreement is treated as causal proof.
"""

from __future__ import annotations

import hashlib
import math

from . import pricing, runtime_flags


SALT = "nego_top_buyer_clone_v1|"
SCOPED_CAP10_FLAG = "GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB"
# These are literal price/B paths shared by 7aidara, Alpha, Beta, and Gamma.
# Repeated values are meaningful holds, not interpolation artifacts.  The .8
# path is structurally dead against an individually rational seller but is kept
# because copying the complete policy means retaining its dead-cell behavior.
HIDDEN_PATHS = {
    0.8: (0.360000, 0.471508, 0.569815, 0.652831, 0.716938, 0.752000),
    1.0: (0.830000, 0.830000, 0.830000, 0.830000),
    1.2: (0.860000, 0.860000, 0.860000, 1.030000, 1.030000),
    1.5: (0.905000, 0.905000, 1.075000, 1.075000,
          1.245000, 1.245000, 1.245000, 1.245000),
}

# Exact 7aidara buyer claim shares from 15 complete-information games.  Price
# is seller value plus (1 - claim) times the visible zone.
COMPLETE_CAP10 = (0.960, 0.898, 0.836, 0.774, 0.774)
COMPLETE_UNKNOWN = (0.960, 0.898, 0.836, 0.774, 0.712)

_MULTS = (0.8, 1.0, 1.2, 1.5)
BUYER_COUNTER_MESSAGE = "Above what I can justify. Here is where I can go."


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
    # If both generations are accidentally armed, neither may own a game.  The
    # scoped module performs the reciprocal check against this broad flag.
    return (runtime_flags.enabled("GLEE_NEGO_TOP_BUYER_CLONE_AB")
            and not runtime_flags.enabled(SCOPED_CAP10_FLAG))


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


def _hidden_target(state: dict, me: str, own_value: float,
                   base: float, own_mult: float) -> tuple[float, float | None]:
    index = _own_price_count(state, me)
    path = HIDDEN_PATHS[own_mult]
    target = path[min(index, len(path) - 1)] * base
    ceiling = path[-1] * base
    # Preserve individual rationality if malformed external values ever reach
    # this otherwise finite-support table.
    target = min(max(target, 0.0), own_value - 0.01)
    ceiling = min(max(ceiling, 0.0), own_value - 0.01)
    return target, ceiling


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

    def counter() -> dict:
        move = {"decision": "RejectOffer", "product_price": target,
                "_plan": plan}
        # All 72 observed 7aidara offers in message-enabled games carried text;
        # every buyer counter used this exact quality-neutral sentence.  It
        # reveals neither private value nor whether this is the final hold.
        if state.get("messages_allowed") is True:
            move["message"] = BUYER_COUNTER_MESSAGE
        return move

    if phase == "offer":
        return {"product_price": target, "_plan": plan}

    if phase != "decision":
        return None
    offered = _num((state.get("last_offer") or {}).get("price"))
    if not math.isfinite(offered):
        return counter()
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

    return counter()


def matches_wire(game: dict, wire: dict) -> bool:
    """Whether a public wire exactly matches the complete buyer policy.

    The composite launch profile uses this policy deterministically, without
    the old hash flag.  ``actions.coerce`` strips ``_plan`` before its numeric
    postconditions, so semantic recomputation is the only reliable ownership
    check that prevents a later legacy price writer from creating a hybrid.
    """
    if not isinstance(wire, dict):
        return False
    try:
        expected = action(game)
    except Exception:
        return False
    if not isinstance(expected, dict):
        return False
    return all(
        wire.get(key) == expected.get(key)
        for key in ("decision", "product_price", "message")
    )
