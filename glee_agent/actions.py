"""Client-side validation and repair of actions.

The SDK does not retry a rejected move: it logs a warning, burns one of the five
per-game attempts, and leaves the turn clock running. So every action is repaired
into a legal shape *here*, before it reaches the wire.

``coerce`` is total — it always returns something the server will accept, falling
back to a conservative legal move rather than raising.
"""

from __future__ import annotations

import logging
import math

MAX_MESSAGE_LEN = 2000

BARGAINING_DECISIONS = {"accept", "reject", "walkaway"}
NEGOTIATION_DECISIONS = {"AcceptOffer", "RejectOffer", "WalkAway"}
YES_NO = {"yes", "no"}

logger = logging.getLogger("glee.actions")


class InvalidAction(Exception):
    """Raised internally when an action cannot be repaired; never escapes."""


def _num(value, default: float = 0.0) -> float:
    """Coerce anything model- or heuristic-shaped into a finite float."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else default
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "").replace("%", "")
        try:
            parsed = float(cleaned)
        except ValueError:
            return default
        return parsed if math.isfinite(parsed) else default
    return default


def _clean_message(action: dict, state: dict) -> None:
    """Trim an over-long message, and drop it entirely when the game forbids one.

    A message over 2,000 chars is an invalid move and costs an attempt.
    """
    msg = action.get("message")
    if msg is None:
        return
    if state.get("messages_allowed") is False:
        action.pop("message", None)
        return
    if not isinstance(msg, str):
        action.pop("message", None)
        return
    msg = msg.strip()
    if not msg:
        action.pop("message", None)
    elif len(msg) > MAX_MESSAGE_LEN:
        action["message"] = msg[: MAX_MESSAGE_LEN - 1].rstrip()
    else:
        action["message"] = msg


def _split_exactly(my_gain: float, money: float) -> tuple[float, float]:
    """Return (my_gain, other_gain) summing to ``money`` under float arithmetic.

    The server requires the two gains to sum to ``money_to_divide`` exactly, so
    the partner share is *derived* rather than rounded independently. Integer
    pots stay integral, which sidesteps float representation entirely.
    """
    my_gain = min(max(my_gain, 0.0), money)
    if float(money).is_integer():
        mine = float(round(my_gain))
        mine = min(max(mine, 0.0), money)
        return mine, float(money) - mine
    mine = round(my_gain, 2)
    other = round(money - mine, 2)
    if mine + other != money:          # residual from the rounding
        other = money - mine
    return mine, other


def coerce(action, game: dict) -> dict:
    """Repair ``action`` into a legal move for the game's current phase."""
    state = game.get("game_state") or {}
    family = game.get("game_family")
    action_type = (game.get("valid_actions") or {}).get("type")

    if not isinstance(action, dict):
        logger.warning("Non-dict action %r; using safe fallback", action)
        return safe_action(game)

    action = dict(action)
    try:
        if action_type == "offer" and family == "bargaining":
            out = _coerce_bargaining_offer(action, game)
        elif action_type == "offer" and family == "negotiation":
            out = _coerce_negotiation_offer(action, state)
        elif action_type == "decision" and family == "bargaining":
            out = _coerce_bargaining_decision(action)
        elif action_type == "decision" and family == "negotiation":
            out = _coerce_negotiation_decision(action, state)
        elif action_type in ("seller_recommendation", "buyer_decision"):
            out = _coerce_yes_no(action)
        elif action_type == "seller_message":
            out = _coerce_seller_message(action)
        else:
            logger.warning("Unknown action type %r; using safe fallback", action_type)
            return safe_action(game)
    except InvalidAction as exc:
        logger.warning("Could not repair action %r (%s); using safe fallback", action, exc)
        return safe_action(game)

    _clean_message(out, state)
    return out


def _coerce_bargaining_offer(action: dict, game: dict) -> dict:
    state = game.get("game_state") or {}
    money = _num(state.get("money_to_divide"), 0.0)
    if money <= 0:
        raise InvalidAction("money_to_divide missing")

    me_is_alice = game.get("your_player") == "player_1"
    # Accept either naming; a model given the state often echoes player_N keys.
    alice = action.get("alice_gain", action.get("player_1_gain"))
    bob = action.get("bob_gain", action.get("player_2_gain"))

    if alice is None and bob is None:
        raise InvalidAction("no gains proposed")
    if alice is None:
        alice = money - _num(bob)
    if bob is None:
        bob = money - _num(alice)

    my_gain = _num(alice) if me_is_alice else _num(bob)
    mine, theirs = _split_exactly(my_gain, money)
    out = {"alice_gain": mine if me_is_alice else theirs,
           "bob_gain": theirs if me_is_alice else mine}
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_negotiation_offer(action: dict, state: dict) -> dict:
    price = action.get("product_price", action.get("price"))
    if price is None:
        raise InvalidAction("no price proposed")
    out = {"product_price": max(0.0, round(_num(price), 2))}
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_bargaining_decision(action: dict) -> dict:
    raw = str(action.get("decision", "")).strip().lower().replace(" ", "").replace("_", "")
    alias = {"acceptoffer": "accept", "rejectoffer": "reject", "walkaway": "walkaway",
             "yes": "accept", "no": "reject", "quit": "walkaway"}
    decision = raw if raw in BARGAINING_DECISIONS else alias.get(raw, "")
    if not decision:
        raise InvalidAction(f"unrecognised decision {action.get('decision')!r}")
    out = {"decision": decision}
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_negotiation_decision(action: dict, state: dict) -> dict:
    raw = str(action.get("decision", "")).strip().lower().replace(" ", "").replace("_", "")
    alias = {"accept": "AcceptOffer", "acceptoffer": "AcceptOffer", "yes": "AcceptOffer",
             "reject": "RejectOffer", "rejectoffer": "RejectOffer", "no": "RejectOffer",
             "counter": "RejectOffer", "counteroffer": "RejectOffer",
             "walkaway": "WalkAway", "walk": "WalkAway", "quit": "WalkAway"}
    decision = alias.get(raw, "")
    if not decision:
        raise InvalidAction(f"unrecognised decision {action.get('decision')!r}")

    out: dict = {"decision": decision}
    if decision == "RejectOffer" and not is_final_round(state):
        # Off the final round a rejection must carry a counteroffer; without one
        # the move is invalid. Fall back to repeating our own valuation.
        price = action.get("product_price", action.get("price"))
        if price is None:
            me = state.get("current_player", "")
            price = state.get(f"{me}_value")
        if price is None:
            raise InvalidAction("rejection without a counteroffer")
        out["product_price"] = max(0.0, round(_num(price), 2))
    if "message" in action:
        out["message"] = action["message"]
    return out


def _coerce_yes_no(action: dict) -> dict:
    raw = str(action.get("decision", action.get("buy", ""))).strip().lower()
    alias = {"yes": "yes", "y": "yes", "true": "yes", "buy": "yes", "recommend": "yes",
             "accept": "yes", "no": "no", "n": "no", "false": "no", "pass": "no",
             "decline": "no", "reject": "no"}
    decision = alias.get(raw, "")
    if not decision:
        raise InvalidAction(f"unrecognised decision {action.get('decision')!r}")
    return {"decision": decision}


def _coerce_seller_message(action: dict) -> dict:
    msg = action.get("message")
    if not isinstance(msg, str) or not msg.strip():
        raise InvalidAction("empty seller message")
    return {"message": msg}


def is_final_round(state: dict) -> bool:
    """True when this is the last round of a capped game (no counteroffer exists)."""
    max_rounds = state.get("max_rounds")
    if max_rounds is None:
        return False           # uncapped game: there is always a next round
    return _num(state.get("round"), 1) >= _num(max_rounds, 1)


def safe_action(game: dict) -> dict:
    """A guaranteed-legal conservative move for the current phase.

    Used whenever a strategy fails, an LLM reply is unusable, or an action
    cannot be repaired. Every branch is a move the server accepts; burning one
    move on a mediocre-but-legal action beats burning the 120s turn clock.
    """
    state = game.get("game_state") or {}
    family = game.get("game_family")
    action_type = (game.get("valid_actions") or {}).get("type")

    if action_type == "offer":
        if family == "bargaining":
            money = _num(state.get("money_to_divide"), 0.0)
            mine, theirs = _split_exactly(money / 2, money)
            me_is_alice = game.get("your_player") == "player_1"
            return {"alice_gain": mine if me_is_alice else theirs,
                    "bob_gain": theirs if me_is_alice else mine}
        me = state.get("current_player", game.get("your_player", ""))
        return {"product_price": max(0.0, round(_num(state.get(f"{me}_value"), 1.0), 2))}

    if action_type == "seller_message":
        return {"message": "I recommend this product."}
    if action_type in ("seller_recommendation", "buyer_decision"):
        return {"decision": "yes"}

    # A decision phase. Accepting is the safe default: a no-deal pays $0, which
    # scores at the bottom of the percentile scale.
    if family == "bargaining":
        return {"decision": "accept"}
    return {"decision": "AcceptOffer"}
