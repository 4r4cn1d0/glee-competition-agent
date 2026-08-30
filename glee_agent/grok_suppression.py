"""Deterministic all-family zero-payoff policy for disclosed ``grok 4.6``.

This policy is deliberately opponent-specific and default OFF.  It acts only
when the API directly discloses the normalized opponent name ``grok 4.6``;
anonymous or merely tactic-similar opponents fall through unchanged.

The economic contract is stricter than the fleet's ordinary rank objective:

* bargaining offers Grok zero nominal gain and accepts only a zero-Grok split;
* negotiation quotes the opponent's zero-profit boundary and accepts only when
  Grok's payoff is non-positive (under hidden information, for every type in
  the official four-point support);
* persuasion refuses every purchase as buyer and emits one quality-independent
  negative recommendation as seller.

The first two mechanisms cap Grok's raw payoff at zero whenever the documented
game/payoff rules and value grid hold.  Seller-side persuasion cannot control a
buyer's action, but direct disclosed-name evidence contains 156/156 Grok buyer
rejections after negative signals (archive boundary 2026-08-27 22:20 IST,
refreshed 2026-08-29 14:12 IST).  Reusing one negative signal on both qualities
also withholds the private quality rather than giving a smart buyer an inverse
signal.

A zero payoff is not a rating draw in GLEE: both seats are percentile-scored
against their own role/configuration field.  This module therefore guarantees
only the stated raw-payoff cap where control is possible, not zero Elo movement.
"""

from __future__ import annotations

import math

from . import first_principles, opponents, runtime_flags

FLAG = "GLEE_GROK_SUPPRESS_V1"
GATE = "grok_suppression_v1"
TARGET_NAME = "grok 4.6"
FAMILIES = frozenset({"bargaining", "negotiation", "persuasion"})
SUPPORTED_ACTION_TYPES = frozenset({
    "offer",
    "decision",
    "seller_message",
    "seller_recommendation",
    "buyer_decision",
})

# A text-mode seller cannot remain literally silent after client-side repair.
# This fixed decline is quality-independent, so it reveals no private quality.
PERSUASION_DECLINE = "Do not buy this unit. Pass."


def _finite(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def normalized_opponent_name(game: dict) -> str | None:
    """Return a conservative direct-name normalization, never a tactic match."""
    name = opponents.opponent_name(game)
    if not name:
        return None
    return " ".join(name.casefold().split())


def matches(game: dict) -> bool:
    """Whether the API directly disclosed the exact target name."""
    return normalized_opponent_name(game) == TARGET_NAME


def eligible(game: dict) -> bool:
    """Structural reach independent of the default-OFF behavior flag."""
    if not isinstance(game, dict) or game.get("game_family") not in FAMILIES:
        return False
    if not matches(game):
        return False
    valid = game.get("valid_actions")
    return (isinstance(valid, dict)
            and valid.get("type") in SUPPORTED_ACTION_TYPES)


def owns(game: dict) -> bool:
    """Whether this component owns the current move end to end."""
    try:
        return eligible(game) and runtime_flags.enabled(FLAG)
    except Exception:
        return False


def is_plan(plan) -> bool:
    return isinstance(plan, dict) and plan.get("source") == GATE


def _plan(game: dict, mechanism: str, **extra) -> dict:
    state = game.get("game_state") or {}
    return {
        "source": GATE,
        "component": "all_family_zero_payoff_cap",
        "gates_fired": [GATE],
        "opponent_name": TARGET_NAME,
        "family": game.get("game_family"),
        "round": state.get("round"),
        "mechanism": mechanism,
        **extra,
    }


def _players(game: dict) -> tuple[str, str, dict] | None:
    state = game.get("game_state")
    if not isinstance(state, dict):
        return None
    me = state.get("current_player") or game.get("your_player")
    if me not in ("player_1", "player_2") or game.get("your_player") != me:
        return None
    them = "player_2" if me == "player_1" else "player_1"
    return me, them, state


def _bargaining_action(game: dict) -> dict | None:
    parsed = _players(game)
    if parsed is None:
        return None
    me, them, state = parsed
    money = _finite(state.get("money_to_divide"))
    if money is None or money <= 0.0:
        return None
    action_type = (game.get("valid_actions") or {}).get("type")

    if action_type == "offer":
        # If Grok accepts, its nominal and discounted payoffs are both zero; if
        # it rejects through the cap, both seats receive zero.
        out = {
            "alice_gain": money if me == "player_1" else 0.0,
            "bob_gain": money if me == "player_2" else 0.0,
            "_plan": _plan(
                game,
                "bargaining_zero_share_offer",
                opponent_payoff_cap=0.0,
                my_nominal_gain=money,
                opponent_nominal_gain=0.0,
            ),
        }
        return out

    if action_type != "decision":
        return None
    offer = state.get("last_offer")
    if not isinstance(offer, dict):
        return None
    aliases = {
        "player_1": ("player_1_gain", "alice_gain"),
        "player_2": ("player_2_gain", "bob_gain"),
    }
    mine = next((_finite(offer.get(key)) for key in aliases[me]
                 if _finite(offer.get(key)) is not None), None)
    theirs = next((_finite(offer.get(key)) for key in aliases[them]
                   if _finite(offer.get(key)) is not None), None)
    if mine is None or theirs is None:
        return None
    accept = theirs <= 1e-9 and mine >= -1e-9
    return {
        "decision": "accept" if accept else "reject",
        "_plan": _plan(
            game,
            "bargaining_zero_share_accept" if accept
            else "bargaining_positive_share_reject",
            opponent_payoff_cap=0.0,
            offered_to_me=mine,
            offered_to_opponent=theirs,
        ),
    }


def _negotiation_context(game: dict) -> dict | None:
    parsed = _players(game)
    if parsed is None:
        return None
    me, them, state = parsed
    role = state.get(f"{me}_role")
    if role not in ("seller", "buyer"):
        return None
    my_value = _finite(state.get(f"{me}_value"))
    if my_value is None or my_value < 0.0:
        return None

    complete = state.get("complete_information") is True
    if complete:
        opponent_value = _finite(state.get(f"{them}_value"))
        if opponent_value is None or opponent_value < 0.0:
            return None
        boundary = opponent_value
    else:
        scale = first_principles.scale_of(my_value)
        if scale is None:
            return None
        # Hidden values are independently supported on {80,100,120,150}*scale.
        # The seller's 150*scale ask and buyer's 80*scale bid give every possible
        # Grok type at most zero payoff, while never crossing our reservation.
        opponent_value = None
        boundary = (150.0 if role == "seller" else 80.0) * scale

    return {
        "me": me,
        "them": them,
        "state": state,
        "role": role,
        "my_value": my_value,
        "complete": complete,
        "opponent_value": opponent_value,
        "boundary": boundary,
    }


def _negotiation_action(game: dict) -> dict | None:
    context = _negotiation_context(game)
    if context is None:
        return None
    state = context["state"]
    role = context["role"]
    my_value = context["my_value"]
    complete = context["complete"]
    boundary = context["boundary"]
    opponent_value = context["opponent_value"]
    action_type = (game.get("valid_actions") or {}).get("type")
    common = {
        "opponent_payoff_cap": 0.0,
        "information": "complete" if complete else "hidden",
        "role": role,
        "zero_profit_boundary": boundary,
    }

    if action_type == "offer":
        return {
            "product_price": boundary,
            "_plan": _plan(game, "negotiation_zero_profit_offer", **common),
        }
    if action_type != "decision":
        return None

    last_offer = state.get("last_offer")
    if not isinstance(last_offer, dict):
        return None
    price = _finite(last_offer.get("price"))
    if price is None or price < 0.0:
        return None

    if role == "seller":
        # Hidden: 1.5*scale is the buyer type with the largest possible gain.
        opponent_bound = opponent_value if complete else boundary
        opponent_gain_upper = opponent_bound - price
        my_gain = price - my_value
    else:
        # Hidden: .8*scale is the seller type with the largest possible gain.
        opponent_bound = opponent_value if complete else boundary
        opponent_gain_upper = price - opponent_bound
        my_gain = my_value - price
    accept = opponent_gain_upper <= 1e-9 and my_gain >= -1e-9
    metadata = {
        **common,
        "offered_price": price,
        "my_payoff": my_gain,
        "opponent_payoff_upper_bound": opponent_gain_upper,
    }
    if accept:
        return {
            "decision": "AcceptOffer",
            "_plan": _plan(game, "negotiation_zero_profit_accept", **metadata),
        }

    max_rounds = _finite(state.get("max_rounds"))
    round_no = _finite(state.get("round"))
    final = (max_rounds is not None and round_no is not None
             and round_no >= max_rounds)
    out = {
        "decision": "RejectOffer",
        "_plan": _plan(game, "negotiation_positive_profit_reject", **metadata),
    }
    if not final:
        out["product_price"] = boundary
    return out


def _persuasion_action(game: dict) -> dict | None:
    action_type = (game.get("valid_actions") or {}).get("type")
    if action_type == "buyer_decision":
        return {
            "decision": "no",
            "_plan": _plan(
                game,
                "persuasion_buyer_pass",
                opponent_payoff_cap=0.0,
            ),
        }
    if action_type == "seller_recommendation":
        return {
            "decision": "no",
            "_plan": _plan(
                game,
                "persuasion_quality_independent_decline",
                opponent_payoff_cap="observational",
                direct_negative_signal_rejections="156/156",
            ),
        }
    if action_type == "seller_message":
        return {
            "message": PERSUASION_DECLINE,
            "_plan": _plan(
                game,
                "persuasion_quality_independent_decline",
                opponent_payoff_cap="observational",
                direct_negative_signal_rejections="156/156",
            ),
        }
    return None


def action(game: dict) -> dict | None:
    """Return the owned legal-shape action, or ``None`` to preserve baseline."""
    if not owns(game):
        return None
    family = game.get("game_family")
    if family == "bargaining":
        return _bargaining_action(game)
    if family == "negotiation":
        return _negotiation_action(game)
    if family == "persuasion":
        return _persuasion_action(game)
    return None
