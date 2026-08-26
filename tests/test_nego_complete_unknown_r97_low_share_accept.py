"""Buyer/P2 round-97 low-share acceptance guard."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N


FLAG = N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_FLAG
OLD_FLAG = N.COMPLETE_UNKNOWN_LATE_STASIS_FLAG


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv(FLAG, "0")
    monkeypatch.setenv(OLD_FLAG, "0")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(
    *,
    round_no: int = 97,
    cycles: int = 10,
    seller_value: float = 80.0,
    buyer_value: float = 100.0,
    offer_price: float = 98.0,
    counter_price: float = 82.0,
    messages_allowed: bool = True,
) -> dict:
    history = []
    first_buyer_decision = round_no - 2 * max(cycles, 0)
    for buyer_round in range(first_buyer_decision, round_no, 2):
        history.extend([
            {
                "round": buyer_round,
                "offer": {
                    "price": offer_price,
                    "from_player": "player_1",
                    "round": buyer_round,
                },
                "decision": "RejectOffer",
                "decided_by": "player_2",
                "counteroffer": counter_price,
            },
            {
                "round": buyer_round + 1,
                "offer": {
                    "price": counter_price,
                    "from_player": "player_2",
                    "round": buyer_round + 1,
                },
                "decision": "RejectOffer",
                "decided_by": "player_1",
                "counteroffer": offer_price,
            },
        ])
    state = {
        "game_family": "negotiation",
        "phase": "decision",
        "round": round_no,
        "horizon_known": False,
        "max_rounds": None,
        "complete_information": True,
        "messages_allowed": messages_allowed,
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": seller_value,
        "player_2_value": buyer_value,
        "last_offer": {
            "price": offer_price,
            "from_player": "player_1",
            "round": round_no,
        },
        "history": history,
    }
    return {
        "game_id": "complete-unknown-r97-low-share",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _reject(counter_price: float = 82.0, *, message: bool = False) -> dict:
    action = {
        "decision": "RejectOffer",
        "product_price": counter_price,
        "_plan": {"source": "unit-fixture"},
    }
    if message:
        action["message"] = "Holding here."
    return action


def _wire(action: dict) -> dict:
    return {
        key: value for key, value in action.items()
        if not str(key).startswith("_")
    }


@pytest.mark.parametrize("messages_allowed", [False, True])
def test_default_off_is_same_object_and_byte_identical(messages_allowed):
    game = _game(messages_allowed=messages_allowed)
    action = _reject(message=messages_allowed)
    before = copy.deepcopy(action)

    result = N._maybe_complete_unknown_r97_low_share_accept(game, action)

    assert result is action
    assert action == before


@pytest.mark.parametrize("messages_allowed", [False, True])
def test_exact_scope_changes_only_reject_to_accept(
    messages_allowed, monkeypatch,
):
    game = _game(messages_allowed=messages_allowed)
    action = _reject(message=messages_allowed)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")

    result = N._maybe_complete_unknown_r97_low_share_accept(game, action)

    assert _wire(result) == {"decision": "AcceptOffer"}
    assert result["_plan"]["source"] == "unit-fixture"
    metadata = result["_plan"][N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_GATE]
    assert metadata == {
        "eligible": True,
        "mode": "deterministic",
        "baseline_decision": "RejectOffer",
        "round": 97,
        "cycles": 10,
        "offer_price": 98.0,
        "counter_price": 82.0,
        "seller_value": 80.0,
        "buyer_value": 100.0,
        "buyer_gain": 2.0,
        "zopa": 20.0,
        "buyer_zopa_share": 0.1,
        "max_buyer_zopa_share": 0.2,
    }
    assert N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_GATE \
        in result["_plan"]["gates_fired"]


def test_top_level_dispatch_applies_after_baseline_policy(monkeypatch):
    game = _game()
    baseline = _reject()
    monkeypatch.setattr(
        N, "_decide", lambda received, cfg: copy.deepcopy(baseline))
    monkeypatch.setenv(FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert _wire(result) == {"decision": "AcceptOffer"}
    assert result["_plan"][N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_GATE][
        "eligible"
    ] is True


@pytest.mark.parametrize(
    ("seller_value", "offer_price", "expected"),
    [
        (80.0, 96.0, "AcceptOffer"),       # exactly 20% of a $20 ZOPA
        (80.0, 95.99, "RejectOffer"),      # just above the 20% fence
        (99.95, 99.99, "AcceptOffer"),     # exactly one cent and 20%
        (99.95, 99.9901, "RejectOffer"),   # less than one cent
    ],
)
def test_cent_and_zopa_share_boundaries(
    seller_value, offer_price, expected, monkeypatch,
):
    game = _game(seller_value=seller_value, offer_price=offer_price)
    monkeypatch.setenv(FLAG, "1")

    result = N._maybe_complete_unknown_r97_low_share_accept(game, _reject())

    assert result["decision"] == expected


@pytest.mark.parametrize("round_no", [1, 75, 96, 98, 99])
def test_only_wire_round_97_is_owned(round_no, monkeypatch):
    game = _game(round_no=round_no)
    action = _reject()
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action


@pytest.mark.parametrize(
    "mutation",
    [
        "hidden",
        "known_horizon",
        "finite_unknown_cap",
        "wrong_player",
        "wrong_roles",
        "wrong_family",
        "wrong_phase",
        "wrong_action_type",
        "missing_message_mode",
        "equal_values",
        "reversed_values",
        "string_value",
        "bad_offer_provenance",
        "bad_offer_round",
    ],
)
def test_information_role_legality_and_provenance_fences(
    mutation, monkeypatch,
):
    game = _game()
    state = game["game_state"]
    if mutation == "hidden":
        state["complete_information"] = False
    elif mutation == "known_horizon":
        state["horizon_known"] = True
        state["max_rounds"] = 100
    elif mutation == "finite_unknown_cap":
        state["max_rounds"] = 99
    elif mutation == "wrong_player":
        state["current_player"] = "player_1"
    elif mutation == "wrong_roles":
        state["player_1_role"], state["player_2_role"] = "buyer", "seller"
    elif mutation == "wrong_family":
        state["game_family"] = "bargaining"
    elif mutation == "wrong_phase":
        state["phase"] = "offer"
    elif mutation == "wrong_action_type":
        game["valid_actions"]["type"] = "offer"
    elif mutation == "missing_message_mode":
        state.pop("messages_allowed")
    elif mutation == "equal_values":
        state["player_1_value"] = state["player_2_value"]
    elif mutation == "reversed_values":
        state["player_1_value"] = 120.0
    elif mutation == "string_value":
        state["player_2_value"] = "100"
    elif mutation == "bad_offer_provenance":
        state["last_offer"]["from_player"] = "player_2"
    elif mutation == "bad_offer_round":
        state["last_offer"]["round"] = 96
    action = _reject()
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action


def test_nine_completed_cycles_do_not_count_current_counter(monkeypatch):
    game = _game(cycles=9)
    action = _reject()
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action


@pytest.mark.parametrize(
    "changed", ["seller_offer", "buyer_counter", "bridge_offer", "bridge_counter"]
)
def test_any_change_inside_ten_cycle_window_fails_closed(changed, monkeypatch):
    game = _game()
    history = game["game_state"]["history"]
    buyer_entry = history[-4]
    seller_entry = history[-3]
    if changed == "seller_offer":
        buyer_entry["offer"]["price"] -= 0.01
    elif changed == "buyer_counter":
        buyer_entry["counteroffer"] += 0.01
    elif changed == "bridge_offer":
        seller_entry["offer"]["price"] += 0.01
    else:
        seller_entry["counteroffer"] -= 0.01
    action = _reject()
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action


def test_projected_current_counter_must_match_recorded_stasis(monkeypatch):
    game = _game()
    action = _reject(counter_price=82.01)
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action


@pytest.mark.parametrize(
    "action",
    [
        {"decision": "AcceptOffer", "_plan": {}},
        {"decision": "WalkAway", "_plan": {}},
        {"decision": "RejectOffer", "_plan": {}},
        {"decision": "RejectOffer", "product_price": 82.0, "extra": 1,
         "_plan": {}},
        {"decision": "RejectOffer", "product_price": 82.0,
         "_plan": "forged"},
    ],
)
def test_non_owned_or_malformed_baseline_actions_are_unchanged(
    action, monkeypatch,
):
    game = _game()
    before = copy.deepcopy(action)
    monkeypatch.setenv(FLAG, "1")

    result = N._maybe_complete_unknown_r97_low_share_accept(game, action)

    assert result is action
    assert result == before


def test_both_overlapping_late_stasis_flags_fail_closed(monkeypatch):
    game = _game()
    action = _reject()
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(OLD_FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action
    assert FLAG in N._COMPLETE_UNKNOWN_LATE_STASIS_CONFLICTS


def test_canonical_history_without_nested_round_is_supported(monkeypatch):
    game = _game()
    for entry in game["game_state"]["history"]:
        entry["offer"].pop("round")
    monkeypatch.setenv(FLAG, "1")

    result = N._maybe_complete_unknown_r97_low_share_accept(game, _reject())

    assert result["decision"] == "AcceptOffer"


def test_duplicate_history_round_fails_closed(monkeypatch):
    game = _game()
    game["game_state"]["history"].append(
        copy.deepcopy(game["game_state"]["history"][-1])
    )
    action = _reject()
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_r97_low_share_accept(game, action) is action
