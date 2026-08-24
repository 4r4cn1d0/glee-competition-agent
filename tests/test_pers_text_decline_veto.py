"""Exact-cell buyer explicit-decline veto mechanism tests."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from glee_agent.text import (
    reads_as_recommendation,
    reads_as_recommendation_expanded,
)


@pytest.fixture(autouse=True)
def _isolated_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_TIGHT_PRIOR", "0.65")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _gid(candidate: bool) -> str:
    for index in range(1000):
        gid = f"text-decline-veto-{index}"
        if persuasion.p08_r125_text_decline_veto_assignment(gid) is candidate:
            return gid
    raise AssertionError("assignment not found")


def _game(game_id: str, *, message: str = "Not recommended.") -> dict:
    return {
        "game_id": game_id,
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": {
            "current_player": "player_2",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "product_price": 100.0,
            "p": 0.8,
            "v": 125.0,
            "u": 0.0,
            "is_seller_know_cv": True,
            "seller_message_type": "text",
            "seller_message": message,
            "round": 1,
            "total_rounds": 20,
            "history": [],
        },
    }


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), None)


def test_expanded_decline_reader_is_pure_and_flag_independent(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLEE_PERS_PARSE_V2", "0")
    assert reads_as_recommendation("Not recommended.") is None
    assert reads_as_recommendation_expanded("Not recommended.") is False
    assert reads_as_recommendation_expanded("Recommended.") is True


def test_flag_default_off_and_hash_control_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_game = _game(_gid(True))
    unset = _decide(candidate_game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB", "0")
    explicitly_off = _decide(candidate_game)
    assert unset == explicitly_off

    control_game = _game(_gid(False))
    control_off = _decide(control_game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB", "1")
    control_on = _decide(control_game)
    assert control_on == control_off
    assert control_on["decision"] == "yes"
    assert "p08_r125_text_decline_veto" not in control_on["_plan"]


def test_candidate_vetoes_v2_only_decline_and_traces_action_change(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(_gid(True))
    assert _decide(game)["decision"] == "yes"

    monkeypatch.setenv("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB", "1")
    candidate = _decide(game)
    assert candidate["decision"] == "no"
    assert candidate["_plan"]["p08_r125_text_decline_veto"] is True
    assert candidate["_plan"]["gates_fired"] == [
        "p08_r125_text_decline_veto"]


@pytest.mark.parametrize("message", ["yes", "Recommended.", "BOIIIII"])
def test_candidate_never_changes_positive_or_abstaining_messages(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    game = _game(_gid(True), message=message)
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB", "1")
    on = _decide(game)
    assert on == off


@pytest.mark.parametrize(
    "field,value",
    [
        ("p", 0.5),
        ("v", 120.0),
        ("u", 1.0),
        ("total_rounds", 10),
        ("seller_message_type", "binary"),
    ],
)
def test_candidate_cannot_reach_neighbor_configuration(
        monkeypatch: pytest.MonkeyPatch, field: str, value) -> None:
    game = _game(_gid(True))
    game["game_state"][field] = value
    off = _decide(game)
    monkeypatch.setenv("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB", "1")
    on = _decide(game)
    assert on == off


@pytest.mark.parametrize("knows", [True, False])
def test_both_seller_knowledge_configurations_are_observable_union(
        monkeypatch: pytest.MonkeyPatch, knows: bool) -> None:
    game = _game(_gid(True))
    # The documented active server state omits this config key entirely.  The
    # action rule therefore cannot condition on it; both official cells share
    # one randomized, production-observable gate.
    game["game_state"].pop("player_1_role")
    game["game_state"].pop("player_2_role")
    game["game_state"].pop("is_seller_know_cv")
    monkeypatch.setenv("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB", "1")
    assert _decide(game)["decision"] == "no"

    game["game_state"]["is_seller_know_cv"] = knows
    assert _decide(game)["decision"] == "no"


def test_assignment_is_stable_balanced_and_fails_closed_without_gid() -> None:
    bits = [persuasion.p08_r125_text_decline_veto_assignment(f"gid-{i}")
            for i in range(1000)]
    assert bits == [
        persuasion.p08_r125_text_decline_veto_assignment(f"gid-{i}")
        for i in range(1000)]
    assert 400 < sum(bits) < 600
    assert persuasion.p08_r125_text_decline_veto_assignment("") is None
    assert persuasion.p08_r125_text_decline_veto_assignment(None) is None
