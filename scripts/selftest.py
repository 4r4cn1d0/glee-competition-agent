#!/usr/bin/env python
"""Offline self-test: play every family, phase, and information condition
against synthetic game states and assert every action is legal.

This is the check to run before pointing the agent at the live server. A move
the server rejects burns one of five attempts; a strategy that raises submits
nothing at all and the game dies on the 120s turn clock. Both cost real rating,
so both are caught here instead.

    python scripts/selftest.py
"""

from __future__ import annotations

import itertools
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent.actions import MAX_MESSAGE_LEN  # noqa: E402
from glee_agent.config import Config  # noqa: E402
from glee_agent.dispatch import make_strategy  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def check(condition: bool, label: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILURES.append(label)


def assert_legal(game: dict, action: dict) -> None:
    family = game.get("game_family")
    action_type = (game.get("valid_actions") or {}).get("type")
    state = game.get("game_state") or {}
    tag = f"{family}/{action_type}/r{state.get('round')}"

    check(isinstance(action, dict) and bool(action), f"{tag}: empty action")
    message = action.get("message")
    if message is not None:
        check(isinstance(message, str) and 0 < len(message) <= MAX_MESSAGE_LEN,
              f"{tag}: bad message length")
        check(state.get("messages_allowed") is not False,
              f"{tag}: message sent when messages are not allowed")

    if action_type == "offer" and family == "bargaining":
        check({"alice_gain", "bob_gain"} <= set(action), f"{tag}: missing gain keys")
        total = action["alice_gain"] + action["bob_gain"]
        check(total == state["money_to_divide"],
              f"{tag}: gains sum to {total!r}, need {state['money_to_divide']!r}")
        check(min(action["alice_gain"], action["bob_gain"]) >= 0, f"{tag}: negative gain")

    elif action_type == "offer" and family == "negotiation":
        check("product_price" in action, f"{tag}: missing product_price")
        check(action["product_price"] >= 0, f"{tag}: negative price")

    elif action_type == "decision" and family == "bargaining":
        check(action.get("decision") in ("accept", "reject", "walkaway"),
              f"{tag}: bad decision {action.get('decision')!r}")

    elif action_type == "decision" and family == "negotiation":
        check(action.get("decision") in ("AcceptOffer", "RejectOffer", "WalkAway"),
              f"{tag}: bad decision {action.get('decision')!r}")
        final = state.get("max_rounds") is not None and state["round"] >= state["max_rounds"]
        if action.get("decision") == "RejectOffer" and not final:
            check("product_price" in action, f"{tag}: rejection without counteroffer")

    elif action_type in ("seller_recommendation", "buyer_decision"):
        check(action.get("decision") in ("yes", "no"), f"{tag}: bad decision")

    elif action_type is None:
        pass                            # no phase to match; any legal shape will do

    elif action_type == "seller_message":
        check(bool(action.get("message")), f"{tag}: empty seller message")


def bargaining_games():
    for money, (d1, d2), max_rounds, complete, msgs in itertools.product(
        (100, 1000, 33.33),
        ((1.0, 1.0), (0.9, 0.8), (0.5, 0.95)),
        (1, 2, 5, 12, None),
        (True, False),
        (True, False),
    ):
        for player, round_no in itertools.product(("player_1", "player_2"), (1, 2)):
            if max_rounds is not None and round_no > max_rounds:
                continue
            state = {
                "phase": "offer", "current_player": player, "proposer": player,
                "round": round_no, "money_to_divide": money,
                "horizon_known": max_rounds is not None,
                "delta_1": d1, "delta_2": d2 if complete else None,
                "messages_allowed": msgs, "complete_information": complete,
                "last_offer": None, "history": [],
            }
            if max_rounds is not None:
                state["max_rounds"] = max_rounds
            if not complete:
                state.pop("delta_2" if player == "player_1" else "delta_1", None)
            yield {"game_id": "t", "game_family": "bargaining", "your_player": player,
                   "phase": "offer", "opponent": {"type": "hidden", "name": None},
                   "game_state": dict(state), "prompt": "Divide the money.",
                   "valid_actions": {"type": "offer", "fields": {}}}

            other = "player_2" if player == "player_1" else "player_1"
            decision_state = dict(state, phase="decision", current_player=player,
                                  proposer=other)
            decision_state["last_offer"] = {
                "player_1_gain": money * 0.7, "player_2_gain": money * 0.3,
                "message": "take it", "proposer": other, "round": round_no,
            }
            yield {"game_id": "t", "game_family": "bargaining", "your_player": player,
                   "phase": "decision", "opponent": {"type": "agent", "name": "X"},
                   "game_state": decision_state, "prompt": "Accept?",
                   "valid_actions": {"type": "decision", "fields": {}}}


def negotiation_games():
    for (s_val, b_val), max_rounds, complete, msgs in itertools.product(
        ((40, 90), (90, 40), (10, 10.5)),
        (1, 3, 8, None),
        (True, False),
        (True, False),
    ):
        for player, round_no in itertools.product(("player_1", "player_2"), (1, 2)):
            if max_rounds is not None and round_no > max_rounds:
                continue
            state = {
                "phase": "offer", "current_player": player, "round": round_no,
                "player_1_role": "seller", "player_2_role": "buyer",
                "player_1_value": s_val, "player_2_value": b_val,
                "horizon_known": max_rounds is not None,
                "messages_allowed": msgs, "complete_information": complete,
                "last_offer": None, "history": [],
            }
            if max_rounds is not None:
                state["max_rounds"] = max_rounds
            if not complete:
                state.pop("player_2_value" if player == "player_1" else "player_1_value")
            yield {"game_id": "t", "game_family": "negotiation", "your_player": player,
                   "phase": "offer", "opponent": {"type": "human", "name": "H"},
                   "game_state": dict(state), "prompt": "Name a price.",
                   "valid_actions": {"type": "offer", "fields": {}}}

            other = "player_2" if player == "player_1" else "player_1"
            decision_state = dict(state, phase="decision")
            decision_state["last_offer"] = {"price": 65, "message": "final",
                                            "from_player": other, "round": round_no}
            decision_state["history"] = [
                {"round": 1, "offer": {"price": 80, "message": "", "from_player": other},
                 "decision": "RejectOffer", "decided_by": player},
            ]
            yield {"game_id": "t", "game_family": "negotiation", "your_player": player,
                   "phase": "decision", "opponent": {"type": "hidden", "name": None},
                   "game_state": decision_state, "prompt": "Accept?",
                   "valid_actions": {"type": "decision", "fields": {}}}


def persuasion_games():
    history = [
        {"round": 1, "seller_message": "yes", "buyer_decision": "yes", "bought": True,
         "quality": "high", "seller_payoff": 60, "buyer_payoff": 40},
        {"round": 2, "seller_message": "yes", "buyer_decision": "yes", "bought": True,
         "quality": "low", "seller_payoff": 60, "buyer_payoff": -60},
        {"round": 3, "seller_message": "yes", "buyer_decision": "no", "bought": False,
         "seller_payoff": 0, "buyer_payoff": 0},
    ]
    for p, (v, u), price, mode, knows_cv, round_no in itertools.product(
        (0.2, 0.5, 0.8),
        ((100, 0), (50, 10)),
        (30, 60, 95),
        ("text", "binary"),
        (True, False),
        (1, 3, 4),
    ):
        total = 5
        base = {
            "product_price": price, "p": p, "round": round_no, "total_rounds": total,
            "seller_message_type": mode, "is_seller_know_cv": knows_cv,
            "seller_total_payoff": 120, "buyer_total_payoff": -20,
            "history": history[: round_no - 1],
        }
        seller_state = dict(base, phase="seller_message", current_player="player_1",
                            current_quality="low" if round_no % 2 else "high")
        if knows_cv:
            seller_state["v"], seller_state["u"] = v, u
        yield {"game_id": "t", "game_family": "persuasion", "your_player": "player_1",
               "phase": "seller_message", "opponent": {"type": "agent", "name": "B"},
               "game_state": seller_state, "prompt": "Pitch the product.",
               "valid_actions": {"type": "seller_message" if mode == "text"
                                 else "seller_recommendation", "fields": {}}}

        buyer_state = dict(base, phase="buyer_decision", current_player="player_2",
                           v=v, u=u,
                           seller_message="This is excellent!" if mode == "text" else "yes")
        yield {"game_id": "t", "game_family": "persuasion", "your_player": "player_2",
               "phase": "buyer_decision", "opponent": {"type": "hidden", "name": None},
               "game_state": buyer_state, "prompt": "Buy?",
               "valid_actions": {"type": "buyer_decision", "fields": {}}}


def malformed_games():
    """States the server should never send, to prove nothing escapes as an exception."""
    yield {"game_id": "t", "game_family": "bargaining", "your_player": "player_1",
           "phase": "decision", "game_state": {"money_to_divide": 100, "round": 1,
                                               "last_offer": None, "history": []},
           "valid_actions": {"type": "decision", "fields": {}}, "prompt": ""}
    yield {"game_id": "t", "game_family": "negotiation", "your_player": "player_2",
           "phase": "offer", "game_state": {"round": 1, "history": []},
           "valid_actions": {"type": "offer", "fields": {}}, "prompt": ""}
    yield {"game_id": "t", "game_family": "persuasion", "your_player": "player_2",
           "phase": "buyer_decision", "game_state": {"history": None},
           "valid_actions": {"type": "buyer_decision", "fields": {}}, "prompt": ""}
    yield {"game_id": "t", "game_family": "tic_tac_toe", "your_player": "player_1",
           "phase": "offer", "game_state": {"money_to_divide": 10, "history": []},
           "valid_actions": {"type": "offer", "fields": {}}, "prompt": ""}
    # A null state must still produce a phase-shaped action: submitting the
    # wrong shape is an invalid move, and submitting nothing is a timeout.
    for family, action_type in (("bargaining", "offer"), ("bargaining", "decision"),
                                ("negotiation", "offer"), ("negotiation", "decision"),
                                ("persuasion", "seller_message"),
                                ("persuasion", "seller_recommendation"),
                                ("persuasion", "buyer_decision")):
        yield {"game_id": "t", "game_family": family, "your_player": "player_1",
               "phase": action_type, "game_state": None,
               "valid_actions": {"type": action_type, "fields": {}}, "prompt": ""}
    yield {"game_id": "t", "game_family": "bargaining", "your_player": "player_1",
           "phase": "offer", "game_state": {}, "prompt": ""}
    yield {}


def main() -> int:
    # The malformed cases deliberately make strategies raise, so the safety net
    # logs a traceback for each. That is the behaviour under test, not a failure
    # — silence it so the report stays readable.
    logging.disable(logging.CRITICAL)

    cfg = Config.from_env()
    cfg.llm_mode = "off"            # deterministic, no network, no spend
    strategy = make_strategy(cfg, log=None)

    total = 0
    for source in (bargaining_games, negotiation_games, persuasion_games):
        count = 0
        for game in source():
            action = strategy(game)
            assert_legal(game, action)
            count += 1
        total += count
        print(f"  {source.__name__:20s} {count:5d} states")

    malformed = 0
    for game in malformed_games():
        action = strategy(game)     # must not raise
        check(isinstance(action, dict) and bool(action),
              f"malformed {game.get('game_family')}: no fallback action")
        malformed += 1
    print(f"  {'malformed_games':20s} {malformed:5d} states")

    print(f"\n{total + malformed} states, {CHECKS} assertions")
    if FAILURES:
        print(f"\nFAILED ({len(FAILURES)}):")
        for failure in sorted(set(FAILURES))[:25]:
            print("  -", failure)
        return 1
    print("all actions legal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
