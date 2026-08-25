"""Support-exact additions for the second Agent 5 negotiation policy.

The hidden-value generator draws each role independently and uniformly from
``{80, 100, 120, 150} * scale``.  Only 6/16 hidden pairs are feasible.  This
module uses that *official support*, not accepted-deal data, in two places:

* In hidden seller games selected by the owning whole-policy mode, replace only
  an outgoing seller price with the rank-grid ask already used by the one-round
  component.  The live stack could still ask 187.59 with cost 100 even though
  the largest buyer value is 150.  The replacement is 119.99 for costs 80/100
  and 149.99 for cost 120.  Cost 150 is structurally dead and stays with the
  existing dead-game policy.  V2 owns the unknown-horizon helper; the separate
  Test 2 V3 selector also owns the cap-10 helper.
* In hidden cap-10 games where the buyer owns the last offer and no earlier
  seller ask identifies a tighter cost ceiling, bid one cent above the highest
  seller type strictly below our value.  This is 80.01/100.01/120.01 for buyer
  values 100/120/150.  Buyer value 80 is structurally dead and falls through.

The unknown-horizon helper deliberately preserves the existing decision.  A
previous broad policy that accepted every profitable hidden unknown-horizon
offer measured -0.06628 exact percentile per exposed decision (375 exposed,
156 changed) and -0.00614 cohort ITT over 4,050 games.  Repricing a rejection
therefore must not silently revive that failed acceptance policy.

Activation belongs to the mutually-exclusive whole-policy selector.  This
module has no runtime flag, game hash, or cross-family behavior.
"""

from __future__ import annotations

import math

from . import first_principles


EPS = first_principles.EPS
UNKNOWN_SELLER_COMPONENT = "hidden_unknown_seller_support"
CAP10_SELLER_COMPONENT = "hidden_cap10_seller_support"
TERMINAL_BUYER_COMPONENT = "hidden_cap10_terminal_support"


def _finite(value) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _seat(game: dict) -> tuple[dict, str, str, float, float] | None:
    if not isinstance(game, dict) or game.get("game_family") != "negotiation":
        return None
    state = game.get("game_state")
    if not isinstance(state, dict):
        return None
    me_game = game.get("your_player")
    me_state = state.get("current_player")
    if me_game not in ("player_1", "player_2"):
        return None
    if me_state not in (None, me_game):
        return None
    me = me_game
    other = "player_2" if me == "player_1" else "player_1"
    own_value = _finite(state.get(f"{me}_value"))
    if own_value is None:
        return None
    scale = first_principles.scale_of(own_value)
    if scale is None:
        return None
    return state, me, other, own_value, scale


def _hidden_unknown_seller_context(
    game: dict,
) -> tuple[dict, str, str, float, float] | None:
    seat = _seat(game)
    if seat is None:
        return None
    state, me, other, own_value, scale = seat
    if state.get(f"{me}_role") != "seller":
        return None
    if state.get(f"{other}_role") != "buyer":
        return None
    if state.get("complete_information") is not False:
        return None
    if state.get("horizon_known") is not False:
        return None
    if state.get("max_rounds") is not None:
        return None
    phase = (game.get("valid_actions") or {}).get("type")
    if phase not in ("offer", "decision"):
        return None
    base = own_value / scale
    # Seller 150 has no feasible counterpart anywhere in the hidden support.
    # Preserve the already-measured dead-game harvester rather than replacing
    # one free-roll with an unmeasured one.
    if base >= max(first_principles.GRID) - 1e-9:
        return None
    return state, me, other, own_value, scale


def hidden_unknown_seller_eligible(game: dict) -> bool:
    """Whether V2 may own an outgoing price in this seller cell."""
    try:
        return _hidden_unknown_seller_context(game) is not None
    except Exception:
        return False


def _hidden_cap10_seller_context(
    game: dict,
) -> tuple[dict, str, str, float, float] | None:
    """Return the supported hidden cap-10 seller seat, never a decision rule.

    In Test 2's first 59 post-V2 official outcomes, all seven hidden cap-10
    seller openings exceeded the largest supported buyer value.  The seller
    slice retained every outcome (four agreements, two no-deals, one walk) and
    summed -1.2 rating; two agreements left us only 0.40 and 0.85 at -5.7 and
    -6.3.  This helper fixes that literal support violation while callers keep
    the existing accept/reject/walk decision unchanged.
    """
    seat = _seat(game)
    if seat is None:
        return None
    state, me, other, own_value, scale = seat
    if state.get(f"{me}_role") != "seller":
        return None
    if state.get(f"{other}_role") != "buyer":
        return None
    if state.get("complete_information") is not False:
        return None
    if state.get("horizon_known") is not True:
        return None
    max_rounds = _finite(state.get("max_rounds"))
    if max_rounds is None or not max_rounds.is_integer() or int(max_rounds) != 10:
        return None
    phase = (game.get("valid_actions") or {}).get("type")
    if phase not in ("offer", "decision"):
        return None
    base = own_value / scale
    if base >= max(first_principles.GRID) - 1e-9:
        return None
    return state, me, other, own_value, scale


def hidden_cap10_seller_eligible(game: dict) -> bool:
    """Whether Test 2 V3 may own an outgoing price in this seller cell."""
    try:
        return _hidden_cap10_seller_context(game) is not None
    except Exception:
        return False


def hidden_cap10_seller_ask(game: dict) -> float | None:
    """Return the support-grid ask in a hidden cap-10 seller cell."""
    context = _hidden_cap10_seller_context(game)
    if context is None:
        return None
    _state, _me, _other, own_value, _scale = context
    return round(first_principles.rank_grid_ask(own_value), 2)


def hidden_unknown_seller_ask(game: dict) -> float | None:
    """Return the fixed support-grid ask, or ``None`` outside the exact cell."""
    context = _hidden_unknown_seller_context(game)
    if context is None:
        return None
    _state, _me, _other, own_value, _scale = context
    return round(first_principles.rank_grid_ask(own_value), 2)


def _carries_outgoing_seller_price(game: dict, action: dict) -> bool:
    phase = (game.get("valid_actions") or {}).get("type")
    if phase == "offer":
        return action.get("decision") is None
    if phase == "decision":
        return action.get("decision") == "RejectOffer"
    return False


def apply_hidden_unknown_seller(game: dict, action: dict) -> dict:
    """Replace only the outgoing seller price; preserve the baseline decision."""
    if not isinstance(action, dict):
        return action
    ask = hidden_unknown_seller_ask(game)
    if ask is None or not _carries_outgoing_seller_price(game, action):
        return action

    result = dict(action)
    previous_price = _finite(result.get("product_price"))
    result["product_price"] = ask

    old_plan = result.get("_plan")
    if old_plan is not None and not isinstance(old_plan, dict):
        return action
    plan = dict(old_plan or {})
    previous_source = plan.get("source")
    if previous_source is not None and previous_source != UNKNOWN_SELLER_COMPONENT:
        plan.setdefault("evidence_source", previous_source)
    plan["source"] = UNKNOWN_SELLER_COMPONENT
    plan["component"] = UNKNOWN_SELLER_COMPONENT
    plan["support_ask"] = ask
    plan["previous_price"] = previous_price
    plan["price_changed"] = previous_price is None or abs(previous_price - ask) > 1e-9
    result["_plan"] = plan
    return result


def apply_hidden_cap10_seller(game: dict, action: dict) -> dict:
    """Replace only a cap-10 seller counter/ask; preserve its decision."""
    if not isinstance(action, dict):
        return action
    ask = hidden_cap10_seller_ask(game)
    if ask is None or not _carries_outgoing_seller_price(game, action):
        return action

    result = dict(action)
    previous_price = _finite(result.get("product_price"))
    result["product_price"] = ask

    old_plan = result.get("_plan")
    if old_plan is not None and not isinstance(old_plan, dict):
        return action
    plan = dict(old_plan or {})
    previous_source = plan.get("source")
    if previous_source is not None and previous_source != CAP10_SELLER_COMPONENT:
        plan.setdefault("evidence_source", previous_source)
    plan["source"] = CAP10_SELLER_COMPONENT
    plan["component"] = CAP10_SELLER_COMPONENT
    plan["support_ask"] = ask
    plan["previous_price"] = previous_price
    plan["price_changed"] = previous_price is None or abs(previous_price - ask) > 1e-9
    result["_plan"] = plan
    return result


def matches_hidden_unknown_seller_wire(game: dict, wire: dict) -> bool:
    """Whether ``wire`` carries the V2-owned seller support price."""
    if not isinstance(wire, dict):
        return False
    ask = hidden_unknown_seller_ask(game)
    price = _finite(wire.get("product_price"))
    return (
        ask is not None
        and price is not None
        and _carries_outgoing_seller_price(game, wire)
        and abs(price - ask) <= 1e-9
    )


def matches_hidden_cap10_seller_wire(game: dict, wire: dict) -> bool:
    """Whether ``wire`` carries the Test 2 V3 cap-10 seller price."""
    if not isinstance(wire, dict):
        return False
    ask = hidden_cap10_seller_ask(game)
    price = _finite(wire.get("product_price"))
    return (
        ask is not None
        and price is not None
        and _carries_outgoing_seller_price(game, wire)
        and abs(price - ask) <= 1e-9
    )


def terminal_buyer_action(game: dict) -> dict | None:
    """Insure the cap-10 buyer's last offer from the exact hidden support."""
    seat = _seat(game)
    if seat is None:
        return None
    state, me, other, own_value, scale = seat
    if game.get("your_player") != "player_2" or me != "player_2":
        return None
    if (game.get("valid_actions") or {}).get("type") != "offer":
        return None
    if state.get(f"{me}_role") != "buyer" or state.get(f"{other}_role") != "seller":
        return None
    if state.get("complete_information") is not False:
        return None
    if state.get("horizon_known") is not True:
        return None
    if _finite(state.get("round")) != 10.0 or _finite(state.get("max_rounds")) != 10.0:
        return None

    base = own_value / scale
    lower_types = [value for value in first_principles.GRID
                   if value < base - 1e-9]
    if not lower_types:
        # Buyer 80 cannot trade with any supported seller type.
        return None
    supported_cost_ceiling = max(lower_types) * scale
    price = round(first_principles.rank_grid_bid(own_value), 2)
    if price >= own_value or abs(price - (supported_cost_ceiling + EPS)) > 1e-9:
        return None
    return {
        "product_price": price,
        "_plan": {
            "source": TERMINAL_BUYER_COMPONENT,
            "component": TERMINAL_BUYER_COMPONENT,
            "supported_cost_ceiling": supported_cost_ceiling,
        },
    }


__all__ = [
    "EPS",
    "UNKNOWN_SELLER_COMPONENT",
    "CAP10_SELLER_COMPONENT",
    "TERMINAL_BUYER_COMPONENT",
    "hidden_unknown_seller_eligible",
    "hidden_unknown_seller_ask",
    "apply_hidden_unknown_seller",
    "matches_hidden_unknown_seller_wire",
    "hidden_cap10_seller_eligible",
    "hidden_cap10_seller_ask",
    "apply_hidden_cap10_seller",
    "matches_hidden_cap10_seller_wire",
    "terminal_buyer_action",
]
