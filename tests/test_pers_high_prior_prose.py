"""Safety and mechanism coverage for the p=.8 seller text wording arm."""

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


def _game(game_id: str, *, p: float = 0.8, mode: str = "text",
          quality: str = "high", round_no: int = 1,
          seat: str = "player_1") -> dict:
    action_type = "seller_message" if mode == "text" else "seller_recommendation"
    if seat == "player_2":
        action_type = "buyer_decision"
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
            "product_price": 100.0,
            "p": p,
            "v": 125.0,
            "u": 0.0,
            "round": round_no,
            "total_rounds": 20,
            "seller_message_type": mode,
            "is_seller_know_cv": True,
            "history": [],
        },
    }


def _assigned(candidate: bool) -> str:
    for index in range(1000):
        game_id = f"high-prior-prose-test-{index}"
        if persuasion.p08_r125_prose_assignment(game_id) is candidate:
            return game_id
    raise AssertionError("no game id found for requested arm")


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), Config.from_env())


def test_assignment_is_stable_balanced_and_missing_ids_fail_closed():
    bits = [persuasion.p08_r125_prose_assignment(f"g-{i}")
            for i in range(2000)]
    assert 0.45 < sum(bits) / len(bits) < 0.55
    assert bits == [persuasion.p08_r125_prose_assignment(f"g-{i}")
                    for i in range(2000)]
    assert persuasion.p08_r125_prose_assignment("") is None
    assert persuasion.p08_r125_prose_assignment(None) is None


def test_default_off_and_enabled_control_are_wire_identical(
        monkeypatch: pytest.MonkeyPatch):
    game = _game(_assigned(False))
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_PROSE_AB", "1")
    on = _decide(game)

    assert on == off
    assert on["message"] == "yes"
    assert "p08_r125_prose_arm" not in on["_plan"]


def test_candidate_changes_only_positive_wire_text_and_is_preserved_by_dispatch(
        monkeypatch: pytest.MonkeyPatch):
    game = _game(_assigned(True))
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_PROSE_AB", "1")
    candidate = _decide(game)

    assert off["message"] == "yes"
    assert candidate["message"] != "yes"
    assert candidate["_plan"]["recommend"] == off["_plan"]["recommend"] is True
    assert candidate["_plan"]["p08_r125_prose_arm"] == "prose"
    assert candidate["_plan"]["gates_fired"] == ["p08_r125_prose"]
    assert len(candidate["message"]) <= 2000

    wire = make_strategy(Config.from_env())(copy.deepcopy(game))
    assert wire["message"] == candidate["message"]


def test_candidate_copy_never_depends_on_private_quality(
        monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GLEE_PERS_P08_R125_PROSE_AB", "1")
    game = _game(_assigned(True), round_no=7)
    plan = {"recommend": True, "round": 7, "total_rounds": 20,
            "quality_is_high": True}
    high = persuasion._p08_r125_prose_message(copy.deepcopy(game), plan.copy())
    game["game_state"]["current_quality"] = "low"
    plan["quality_is_high"] = False
    low = persuasion._p08_r125_prose_message(copy.deepcopy(game), plan.copy())
    assert high == low


@pytest.mark.parametrize(
    "changes",
    [
        {"p": 0.5},
        {"mode": "binary"},
        {"seat": "player_2"},
    ],
)
def test_other_priors_modes_and_roles_are_untouched(
        monkeypatch: pytest.MonkeyPatch, changes: dict):
    game = _game(_assigned(True), **changes)
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_PROSE_AB", "1")
    on = _decide(game)
    assert on == off


def test_negative_recommendation_remains_literal_no(
        monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GLEE_PERS_P08_R125_PROSE_AB", "1")
    game = _game(_assigned(True), quality="low")
    plan = {"recommend": False, "round": 1, "total_rounds": 20,
            "quality_is_high": False}
    assert persuasion._p08_r125_prose_message(game, plan) is None
    assert "p08_r125_prose_arm" not in plan
