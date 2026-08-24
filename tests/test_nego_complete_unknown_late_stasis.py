"""Deterministic late mutual-stasis guard for complete unknown horizons."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import deterministic_negotiation, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N


FLAG = N.COMPLETE_UNKNOWN_LATE_STASIS_FLAG


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _owners(monkeypatch):
    for name in (
        "GLEE_NEGO_BOUND_AS_FLOOR",
        "GLEE_NEGO_CONTINUATION_ACCEPT",
        "GLEE_NEGO_CURVE_PRICING",
        "GLEE_NEGO_DEADGAME_V1",
        "GLEE_NEGO_ENDGAME_V3",
        "GLEE_NEGO_HORIZON_V2",
        "GLEE_NEGO_OPEN_CLAIM_ALWAYS",
        "GLEE_NEGO_POSTERIOR",
        "GLEE_NEGO_STALL_POLICY",
        "GLEE_NEGO_TABLE",
    ):
        monkeypatch.setenv(name, "1")
    monkeypatch.setenv("GLEE_NEGO_ACCEPT_SPAN", "0.48")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.80")
    monkeypatch.setenv("GLEE_NEGO_FINAL_OPTION", "0.60")
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.95")
    monkeypatch.setenv("GLEE_NEGO_SPAN_INVARIANT", "0.40")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")


def _game(*, role="buyer", round_no=75, cycles=10):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    own_value = 80.0 if role == "seller" else 120.0
    other_value = 120.0 if role == "seller" else 80.0
    offer = 90.0 if role == "seller" else 110.0
    placeholder_counter = 100.0
    history = []
    first_our_decision = round_no - 2 * max(cycles, 0)
    for own_round in range(first_our_decision, round_no, 2):
        history.extend([
            {
                "round": own_round,
                "offer": {
                    "price": offer,
                    "from_player": other,
                    "round": own_round,
                },
                "decision": "RejectOffer",
                "decided_by": me,
                "counteroffer": placeholder_counter,
            },
            {
                "round": own_round + 1,
                "offer": {
                    "price": placeholder_counter,
                    "from_player": me,
                    "round": own_round + 1,
                },
                "decision": "RejectOffer",
                "decided_by": other,
                "counteroffer": offer,
            },
        ])
    state = {
        "game_family": "negotiation",
        "round": round_no,
        "horizon_known": False,
        "max_rounds": None,
        "complete_information": True,
        "messages_allowed": True,
        "current_player": me,
        f"{me}_role": role,
        f"{other}_role": "buyer" if role == "seller" else "seller",
        f"{me}_value": own_value,
        f"{other}_value": other_value,
        "last_offer": {
            "price": offer,
            "from_player": other,
            "round": round_no,
        },
        "history": history,
    }
    return {
        "game_id": f"complete-unknown-late-{role}-{round_no}-{cycles}",
        "game_family": "negotiation",
        "your_player": me,
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _align_history_with_baseline(game):
    """Make every prior own counter equal the current unarmed public counter."""
    baseline = N.decide(copy.deepcopy(game), Config.from_env())
    assert baseline["decision"] == "RejectOffer"
    counter = coerce(_wire(baseline), copy.deepcopy(game))["product_price"]
    state = game["game_state"]
    me = state["current_player"]
    for entry in state["history"]:
        if entry.get("decided_by") == me:
            entry["counteroffer"] = counter
        offer = entry.get("offer") or {}
        if offer.get("from_player") == me:
            offer["price"] = counter
    return counter


def _wire(action):
    return {key: value for key, value in action.items()
            if not str(key).startswith("_")}


@pytest.mark.parametrize("role", ["seller", "buyer"])
def test_default_off_is_byte_identical(role, monkeypatch):
    _owners(monkeypatch)
    game = _game(role=role)
    _align_history_with_baseline(game)
    absent = N.decide(copy.deepcopy(game), Config.from_env())
    monkeypatch.setenv(FLAG, "0")
    explicit_zero = N.decide(copy.deepcopy(game), Config.from_env())

    assert explicit_zero == absent
    assert "complete_unknown_late_stasis_v1" not in absent["_plan"]


@pytest.mark.parametrize("role", ["seller", "buyer"])
def test_exact_ten_cycle_stasis_changes_only_reject_to_accept(role, monkeypatch):
    _owners(monkeypatch)
    game = _game(role=role)
    counter = _align_history_with_baseline(game)
    control = N.decide(copy.deepcopy(game), Config.from_env())
    monkeypatch.setenv(FLAG, "1")
    candidate = N.decide(copy.deepcopy(game), Config.from_env())

    assert coerce(_wire(control), copy.deepcopy(game)) == {
        "decision": "RejectOffer",
        "product_price": counter,
    }
    assert _wire(candidate) == {"decision": "AcceptOffer"}
    metadata = candidate["_plan"]["complete_unknown_late_stasis_v1"]
    assert metadata == {
        "eligible": True,
        "round": 75,
        "cycles": 10,
        "offer_price": 90.0 if role == "seller" else 110.0,
        "counter_price": counter,
        "mode": "deterministic",
    }
    assert "complete_unknown_late_stasis_v1" in candidate["_plan"]["gates_fired"]


def test_guard_wraps_the_deterministic_leader_buyer(monkeypatch):
    _owners(monkeypatch)
    monkeypatch.setenv(deterministic_negotiation.LEADER_REPLICA_FLAG, "1")
    game = _game(role="buyer")
    _align_history_with_baseline(game)
    control = N.decide(copy.deepcopy(game), Config.from_env())
    assert control["_plan"]["source"] == deterministic_negotiation.LEADER_REPLICA

    monkeypatch.setenv(FLAG, "1")
    candidate = N.decide(copy.deepcopy(game), Config.from_env())
    assert _wire(candidate) == {"decision": "AcceptOffer"}
    assert candidate["_plan"]["source"] == deterministic_negotiation.LEADER_REPLICA
    assert candidate["_plan"]["complete_unknown_late_stasis_v1"]["cycles"] == 10


def test_nine_cycles_and_record_echoes_are_not_ten_cycles(monkeypatch):
    _owners(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    game = _game(cycles=9)
    _align_history_with_baseline(game)
    action = N.decide(copy.deepcopy(game), Config.from_env())

    assert action["decision"] == "RejectOffer"
    metadata = action["_plan"]["complete_unknown_late_stasis_v1"]
    assert metadata["eligible"] is False
    assert metadata["cycles"] == 9
    assert "complete_unknown_late_stasis_v1" not in action["_plan"]["gates_fired"]


@pytest.mark.parametrize(
    "changed", ["offer", "counter", "bridge_offer", "bridge_counter"])
def test_one_changed_cycle_breaks_exact_stasis(changed, monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    state = game["game_state"]
    me = state["current_player"]
    own_entries = [entry for entry in state["history"]
                   if entry.get("decided_by") == me]
    prior = own_entries[-3]
    if changed == "offer":
        prior["offer"]["price"] += 0.01
    elif changed == "counter":
        prior["counteroffer"] += 0.01
    else:
        bridge = state["history"][state["history"].index(prior) + 1]
        if changed == "bridge_offer":
            bridge["offer"]["price"] += 0.01
        else:
            bridge["counteroffer"] += 0.01
    monkeypatch.setenv(FLAG, "1")
    action = N.decide(copy.deepcopy(game), Config.from_env())

    assert action["decision"] == "RejectOffer"
    assert action["_plan"]["complete_unknown_late_stasis_v1"]["cycles"] < 10


@pytest.mark.parametrize(
    "mutation",
    [
        "too_early",
        "hidden",
        "known_horizon",
        "infeasible",
        "not_profitable",
        "baseline_accept",
    ],
)
def test_scope_fences_fail_closed(mutation, monkeypatch):
    _owners(monkeypatch)
    game = _game()
    counter = _align_history_with_baseline(game)
    state = game["game_state"]
    action = {"decision": "RejectOffer", "product_price": counter, "_plan": {}}
    if mutation == "too_early":
        state["round"] = 74
        state["last_offer"]["round"] = 74
    elif mutation == "hidden":
        state["complete_information"] = False
    elif mutation == "known_horizon":
        state["horizon_known"] = True
        state["max_rounds"] = 100
    elif mutation == "infeasible":
        state["player_1_value"] = 130.0
    elif mutation == "not_profitable":
        state["last_offer"]["price"] = 120.0
    elif mutation == "baseline_accept":
        action = {"decision": "AcceptOffer", "_plan": {}}
    monkeypatch.setenv(FLAG, "1")

    assert N._maybe_complete_unknown_late_stasis(game, action) == action


@pytest.mark.parametrize(
    "conflict",
    [
        "GLEE_NEGO_CLOSE_AB",
        "GLEE_NEGO_SURPLUS_PROBE",
        "GLEE_NEGO_TOP_BUYER_CLONE_AB",
        "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB",
        "GLEE_NEGO_MSG_ARMS",
    ],
)
def test_randomized_or_overlapping_flags_fail_closed(conflict, monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(conflict, "1")
    action = N.decide(copy.deepcopy(game), Config.from_env())

    assert action["decision"] == "RejectOffer"
    assert "complete_unknown_late_stasis_v1" not in action["_plan"]


def test_changed_measured_stack_fails_closed(monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_NEGO_ACCEPT_SPAN", "0.47")

    assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
        == "RejectOffer"


def test_dict_counter_schema_requires_matching_provenance(monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    for entry in game["game_state"]["history"]:
        entry["counteroffer"] = {
            "price": entry["counteroffer"],
            "from_player": entry["decided_by"],
            "round": entry["round"],
        }
    monkeypatch.setenv(FLAG, "1")
    assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
        == "AcceptOffer"

    game["game_state"]["history"][-1]["counteroffer"]["from_player"] = \
        game["game_state"]["current_player"]
    assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
        == "RejectOffer"


def test_canonical_history_without_nested_offer_rounds_is_supported(monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    for entry in game["game_state"]["history"]:
        entry["offer"].pop("round")
    monkeypatch.setenv(FLAG, "1")
    assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
        == "AcceptOffer"

    game["game_state"]["history"][-2]["offer"]["round"] = "wrong"
    assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
        == "RejectOffer"


def test_both_deterministic_selectors_and_nonfinite_arm_fail_closed(monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(deterministic_negotiation.RANK_HYBRID_FLAG, "1")
    monkeypatch.setenv(deterministic_negotiation.LEADER_REPLICA_FLAG, "1")
    assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
        == "RejectOffer"

    monkeypatch.delenv(deterministic_negotiation.RANK_HYBRID_FLAG)
    monkeypatch.delenv(deterministic_negotiation.LEADER_REPLICA_FLAG)
    for malformed in ("nan", "typo"):
        monkeypatch.setenv("GLEE_NEGO_SURPLUS_PROBE", malformed)
        assert N.decide(copy.deepcopy(game), Config.from_env())["decision"] \
            == "RejectOffer"
