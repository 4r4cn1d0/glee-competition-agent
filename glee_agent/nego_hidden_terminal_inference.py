"""Reservation-bound inference for hidden-information cap-10 buyers.

The terminal buyer cannot see the seller's value, but the seller's own earlier
offers are binding proposals: an individually rational seller with cost ``c``
does not offer to sell below ``c``.  On the public four-point support, the
lowest observed seller ask therefore gives a conservative discrete upper bound
on cost.  Examples on the unit scale:

* seller asked 97  -> only cost 80 is consistent -> terminal bid 80.01;
* seller asked 119 -> costs 80 or 100 are consistent -> bid 100.01;
* seller asked 149 -> costs 80/100/120 are consistent -> bid 120.01.

The bid leaves at least one cent to every seller type consistent with its own
offer.  It does not infer from accepted deals, outcomes, messages, or our own
prices.  If no opponent offer below our value supplies a bound, the helper
returns ``None`` and the complete Agent 5 policy keeps its observed-leader
fallback.  The caller owns activation; this module has no runtime flag or hash.
"""

from __future__ import annotations

import math

from . import first_principles


EPS = 0.01
COMPONENT = "hidden_cap10_terminal_inference"


def _finite(value) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _context(game: dict) -> tuple[dict, str, str, float, float] | None:
    if game.get("game_family") != "negotiation":
        return None
    if game.get("your_player") != "player_2":
        return None
    if (game.get("valid_actions") or {}).get("type") != "offer":
        return None
    state = game.get("game_state")
    if not isinstance(state, dict):
        return None
    me = state.get("current_player") or game.get("your_player")
    if me != "player_2" or state.get(f"{me}_role") != "buyer":
        return None
    seller = "player_1"
    if state.get(f"{seller}_role") != "seller":
        return None
    if state.get("complete_information") is not False:
        return None
    if state.get("horizon_known") is not True:
        return None
    round_no = _finite(state.get("round"))
    maximum = _finite(state.get("max_rounds"))
    if round_no != 10.0 or maximum != 10.0:
        return None
    own_value = _finite(state.get(f"{me}_value"))
    if own_value is None:
        return None
    scale = first_principles.scale_of(own_value)
    if scale is None:
        return None
    return state, me, seller, own_value, scale


def _seller_prices(state: dict, seller: str) -> list[float]:
    """Collect distinct opponent price wires, ignoring our own and malformed data."""
    prices: list[float] = []
    seen: set[tuple[float, object]] = set()

    def add(candidate, fallback_round=None) -> None:
        if not isinstance(candidate, dict):
            return
        if candidate.get("from_player") != seller:
            return
        price = _finite(candidate.get("price"))
        if price is None or price < 0.0:
            return
        marker = (round(price, 8), candidate.get("round", fallback_round))
        if marker in seen:
            return
        seen.add(marker)
        prices.append(price)

    history = state.get("history") or []
    if isinstance(history, (list, tuple)):
        for entry in history:
            if not isinstance(entry, dict):
                continue
            add(entry.get("offer"), entry.get("round"))
            add(entry.get("counteroffer"), entry.get("round"))
    add(state.get("last_offer"), state.get("round"))
    return prices


def action(game: dict) -> dict | None:
    """Return the inferred terminal bid, or ``None`` without a safe bound."""
    context = _context(game)
    if context is None:
        return None
    state, _me, seller, own_value, scale = context
    prices = [price for price in _seller_prices(state, seller)
              if price < own_value - 1e-9]
    if not prices:
        return None
    lowest_ask = min(prices)

    # Costs at or above our value are structurally infeasible.  Among feasible
    # types, use the greatest grid value no larger than the seller's own ask;
    # the resulting bid is safe for every lower type as well.
    feasible_costs = [
        base * scale
        for base in first_principles.GRID
        if base * scale < own_value - 1e-9
        and base * scale <= lowest_ask + 1e-9
    ]
    if not feasible_costs:
        return None
    ceiling = max(feasible_costs)
    price = ceiling + EPS
    if price >= own_value:
        return None
    return {
        "product_price": round(price, 2),
        "_plan": {
            "source": COMPONENT,
            "component": COMPONENT,
            "seller_offer_count": len(prices),
            "lowest_seller_ask": lowest_ask,
            "inferred_cost_ceiling": ceiling,
        },
    }


__all__ = ["EPS", "COMPONENT", "action"]
