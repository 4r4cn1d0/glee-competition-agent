"""Safety and mechanism coverage for the exact binary seller truth arm."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.dispatch import make_strategy
from glee_agent.strategies import persuasion


@pytest.fixture(autouse=True)
def _isolated_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_MODE"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GLEE_PERS_MSG_STYLE", "token")
    monkeypatch.setenv("GLEE_PERS_KEEP_MSG", "1")
    monkeypatch.setenv("GLEE_PERS_HONEST_ROUNDS", "99")
    monkeypatch.setenv("GLEE_LLM_MODE", "off")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(game_id: str, *, p: float = 0.8, ratio: float = 1.25,
          mode: str = "binary", quality: str = "low", rounds: int = 20,
          knows_values: bool = True, low_value: float = 0.0,
          seat: str = "player_1") -> dict:
    action_type = "seller_recommendation" if mode == "binary" else "seller_message"
    if seat == "player_2":
        action_type = "buyer_decision"
    price = 100.0
    return {
        "game_id": game_id,
        "game_family": "persuasion",
        "your_player": seat,
        "phase": action_type,
        "valid_actions": {"type": action_type},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "current_player": seat,
            "current_quality": quality,
            "product_price": price,
            "p": p,
            "v": price * ratio if knows_values else None,
            "u": low_value if knows_values else None,
            "round": 1,
            "total_rounds": rounds,
            "seller_message_type": mode,
            "is_seller_know_cv": knows_values,
            "history": [],
        },
    }


def _assigned(candidate: bool) -> str:
    for index in range(1000):
        game_id = f"p08-r125-binary-truth-test-{index}"
        if persuasion.p08_r125_binary_truth_assignment(game_id) is candidate:
            return game_id
    raise AssertionError("no game id found for requested arm")


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), Config.from_env())


def test_assignment_is_stable_balanced_independent_and_missing_fails_closed():
    ids = [f"truth-g-{index}" for index in range(2000)]
    truth = [persuasion.p08_r125_binary_truth_assignment(gid) for gid in ids]
    prose = [persuasion.p08_r125_prose_assignment(gid) for gid in ids]
    assert 0.45 < sum(truth) / len(truth) < 0.55
    assert truth == [persuasion.p08_r125_binary_truth_assignment(gid)
                     for gid in ids]
    assert truth != prose
    assert persuasion.p08_r125_binary_truth_assignment("") is None
    assert persuasion.p08_r125_binary_truth_assignment(None) is None


def test_default_off_and_enabled_control_are_full_object_identical(
        monkeypatch: pytest.MonkeyPatch):
    game = _game(_assigned(False))
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_BINARY_TRUTH_AB", "1")
    on = _decide(game)
    assert on == off
    assert on["decision"] == "yes"
    assert "p08_r125_binary_truth_arm" not in on["_plan"]


def test_candidate_declines_only_low_quality_and_traces_changed_action(
        monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GLEE_PERS_P08_R125_BINARY_TRUTH_AB", "1")
    game = _game(_assigned(True), quality="low")
    candidate = _decide(game)
    assert candidate["decision"] == "no"
    assert candidate["_plan"]["recommend"] is False
    assert candidate["_plan"]["p08_r125_binary_truth_arm"] == "truth"
    assert candidate["_plan"]["gates_fired"] == ["p08_r125_binary_truth"]
    wire = make_strategy(Config.from_env())(copy.deepcopy(game))
    assert wire["decision"] == "no"


def test_candidate_keeps_high_recommendation_but_records_stable_arm(
        monkeypatch: pytest.MonkeyPatch):
    game = _game(_assigned(True), quality="high")
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_BINARY_TRUTH_AB", "1")
    candidate = _decide(game)
    assert off["decision"] == candidate["decision"] == "yes"
    assert candidate["_plan"]["p08_r125_binary_truth_arm"] == "truth"
    assert "gates_fired" not in candidate["_plan"]


@pytest.mark.parametrize(
    "changes",
    [
        {"p": 0.5},
        {"ratio": 1.2},
        {"ratio": 2.0},
        {"mode": "text"},
        {"rounds": 10},
        {"knows_values": False},
        {"low_value": 5.0},
        {"seat": "player_2"},
    ],
)
def test_neighbor_cells_roles_and_modes_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch, changes: dict):
    game = _game(_assigned(True), **changes)
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_BINARY_TRUTH_AB", "1")
    on = _decide(game)
    assert on == off


def test_explicit_false_known_value_marker_fails_closed(
        monkeypatch: pytest.MonkeyPatch):
    game = _game(_assigned(True))
    game["game_state"]["is_seller_know_cv"] = False
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_BINARY_TRUTH_AB", "1")
    assert _decide(game) == off
