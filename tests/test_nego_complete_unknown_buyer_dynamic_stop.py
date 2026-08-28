"""State-based stopping for Test 4's complete/unknown buyer policy."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import nego_score_floor, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N
from scripts import check_reachability


FLAG = N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_FLAG


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    nego_score_floor._cells = None
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    nego_score_floor._cells = None


def _owners(monkeypatch) -> None:
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
        "GLEE_NEGO_TEST4_HOTFIX_V1",
        "GLEE_NEGO_COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_V1",
        "GLEE_NEGO_TEST2_UNKNOWN_R99_ACCEPT_V1",
    ):
        monkeypatch.setenv(name, "1")
    monkeypatch.setenv("GLEE_NEGO_ACCEPT_SPAN", "0.48")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.80")
    monkeypatch.setenv("GLEE_NEGO_FINAL_OPTION", "0.60")
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.95")
    monkeypatch.setenv("GLEE_NEGO_SPAN_INVARIANT", "0.40")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")


def _game(
    *,
    round_no: int = 31,
    cycles: int = 10,
    offer_price: float = 95.0,
    seller_value: float = 80.0,
    buyer_value: float = 120.0,
    messages_allowed: bool = False,
) -> dict:
    placeholder_counter = 90.0
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
                "counteroffer": placeholder_counter,
            },
            {
                "round": buyer_round + 1,
                "offer": {
                    "price": placeholder_counter,
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
        "game_id": f"dynamic-stop-{round_no}-{cycles}-{offer_price}",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _wire(action: dict) -> dict:
    return {
        key: value for key, value in action.items()
        if not str(key).startswith("_")
    }


def _align_history_with_baseline(game: dict) -> float:
    """Replace placeholders with the actual coerced Test 4 counter wire."""
    baseline = N.decide(copy.deepcopy(game), Config.from_env())
    assert baseline["decision"] == "RejectOffer"
    projected = coerce(_wire(baseline), copy.deepcopy(game))
    assert projected["decision"] == "RejectOffer"
    counter = projected["product_price"]
    for entry in game["game_state"]["history"]:
        if entry.get("decided_by") == "player_2":
            entry["counteroffer"] = counter
        offer = entry.get("offer") or {}
        if offer.get("from_player") == "player_2":
            offer["price"] = counter
    return counter


def test_default_absent_and_explicit_zero_are_byte_identical(monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    absent = N.decide(copy.deepcopy(game), Config.from_env())
    monkeypatch.setenv(FLAG, "0")
    explicit_zero = N.decide(copy.deepcopy(game), Config.from_env())

    assert absent == explicit_zero
    assert N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE not in absent["_plan"]


def test_round31_ten_cycle_above_median_changes_only_reject_to_accept(
    monkeypatch,
):
    _owners(monkeypatch)
    game = _game()
    counter = _align_history_with_baseline(game)
    control = N.decide(copy.deepcopy(game), Config.from_env())
    monkeypatch.setenv(FLAG, "1")
    candidate = N.decide(copy.deepcopy(game), Config.from_env())

    assert coerce(_wire(control), copy.deepcopy(game)) == {
        "decision": "RejectOffer",
        "product_price": counter,
    }
    assert _wire(candidate) == {"decision": "AcceptOffer"}
    metadata = candidate["_plan"][
        N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE
    ]
    assert metadata == {
        "eligible": True,
        "mode": "deterministic",
        "baseline_decision": "RejectOffer",
        "round": 31,
        "cycles": 10,
        "offer_price": 95.0,
        "counter_price": counter,
        "seller_value": 80.0,
        "buyer_value": 120.0,
        "buyer_gain": 25.0,
        "accept_seed_percentile": pytest.approx(0.6090909090909091),
        "minimum_seed_percentile": 0.50,
        "seed_cell_n": 55,
    }
    assert N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE \
        in candidate["_plan"]["gates_fired"]


def test_nine_cycles_do_not_fire(monkeypatch):
    _owners(monkeypatch)
    game = _game(cycles=9)
    _align_history_with_baseline(game)
    monkeypatch.setenv(FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert result["decision"] == "RejectOffer"
    assert N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE not in result["_plan"]


def test_below_median_offer_does_not_fire(monkeypatch):
    _owners(monkeypatch)
    game = _game(offer_price=100.0)
    _align_history_with_baseline(game)
    monkeypatch.setenv(FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert result["decision"] == "RejectOffer"
    assert nego_score_floor.payoff_percentile(
        game["game_state"], "player_2", 80.0, 120.0, 20.0,
    ) == pytest.approx((0.2909090909090909, 55))
    assert N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE not in result["_plan"]


@pytest.mark.parametrize("mutation", ["hidden", "known", "infeasible", "seller"])
def test_nonowned_cells_fail_closed(mutation, monkeypatch):
    _owners(monkeypatch)
    game = _game()
    _align_history_with_baseline(game)
    action = N.decide(copy.deepcopy(game), Config.from_env())
    state = game["game_state"]
    if mutation == "hidden":
        state["complete_information"] = False
    elif mutation == "known":
        state["horizon_known"] = True
        state["max_rounds"] = 99
    elif mutation == "infeasible":
        state["player_2_value"] = 80.0
    else:
        state["current_player"] = "player_1"
        game["your_player"] = "player_1"
    before = copy.deepcopy(action)
    monkeypatch.setenv(FLAG, "1")

    result = N._maybe_complete_unknown_buyer_dynamic_stop(game, action)

    assert result is action
    assert result == before


def test_rejected_score_floor_conflict_fails_closed(monkeypatch):
    _owners(monkeypatch)
    game = _game(round_no=75)
    _align_history_with_baseline(game)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert result["decision"] == "RejectOffer"
    assert N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE not in result["_plan"]
    assert N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE not in result["_plan"]


def test_round99_remains_owned_by_terminal_guard(monkeypatch):
    _owners(monkeypatch)
    game = _game(round_no=99)
    monkeypatch.setenv(FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert _wire(result) == {"decision": "AcceptOffer"}
    assert N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE not in result["_plan"]
    assert N.TEST2_UNKNOWN_R99_ACCEPT_GATE in result["_plan"]


def test_payoff_rank_lookup_fails_closed_outside_exact_visible_cell():
    state = _game()["game_state"]
    assert nego_score_floor.payoff_percentile(
        state, "player_2", 80.0, 120.0, float("nan"),
    ) is None
    state["complete_information"] = False
    assert nego_score_floor.payoff_percentile(
        state, "player_2", 80.0, 120.0, 25.0,
    ) is None


def test_reachability_predicate_recognizes_exact_candidate_metadata():
    game = _game()
    plan = {
        N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE: {
            "eligible": True,
            "round": 31,
            "cycles": 10,
            "accept_seed_percentile": 0.50,
            "minimum_seed_percentile": 0.50,
            "seed_cell_n": 55,
        },
    }

    assert check_reachability._p_complete_unknown_buyer_dynamic_stop(
        game, plan,
    )
    plan[N.COMPLETE_UNKNOWN_BUYER_DYNAMIC_STOP_GATE]["cycles"] = 9
    assert not check_reachability._p_complete_unknown_buyer_dynamic_stop(
        game, plan,
    )
