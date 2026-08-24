"""Regression tests for the deterministic high-share bargaining delay guard."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import bargaining


MONEY = 1000.0
FLAG = "GLEE_BARG_HIGH_SHARE_DELAY_GUARD"
BASE_FLAGS = {
    "GLEE_BARG_ACCEPT_FLOOR": "0.50",
    "GLEE_BARG_FLOOR_GAIN": "0.05",
    "GLEE_BARG_OFFER_FLOOR": "0.57",
    "GLEE_BARG_OPPONENT_FLOOR": "0.39",
    "GLEE_BARG_SPE_WEIGHT": "1.0",
    "GLEE_BARG_UNCAPPED_HORIZON": "60",
    "GLEE_BARG_DISCOUNT_NO_REGRESS": "1",
    "GLEE_BARG_DISCOUNT_NO_REGRESS_AB": "0",
    "GLEE_BARG_NO_REGRESS": "0",
    "GLEE_BARG_OBSERVED_GAIN": "0",
    "GLEE_TRACE_GATES": "1",
}


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("GLEE_BARG", "GLEE_OPP", "GLEE_PROBE", "GLEE_TRACE")):
            monkeypatch.delenv(key, raising=False)
    for key, value in BASE_FLAGS.items():
        monkeypatch.setenv(key, value)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _offer(proposer: str, round_no: int, player_2_share: float) -> dict:
    player_2_gain = MONEY * player_2_share
    return {
        "round": round_no,
        "proposer": proposer,
        "offer": {
            "player_1_gain": MONEY - player_2_gain,
            "player_2_gain": player_2_gain,
            "proposer": proposer,
            "round": round_no,
        },
        "decision": "reject",
    }


def _decision_game(*, current_share: float = 0.46, delta_me: float = 0.95,
                   current_round: int = 5, max_rounds: int = 12) -> dict:
    current_gain = MONEY * current_share
    return {
        "game_id": "high-share-delay-case",
        "game_family": "bargaining",
        "your_player": "player_2",
        "phase": "decision",
        "opponent": "field-agent",
        "game_state": {
            "round": current_round,
            "max_rounds": max_rounds,
            "horizon_known": True,
            "phase": "decision",
            "current_player": "player_2",
            "proposer": "player_1",
            "money_to_divide": MONEY,
            "delta_1": 0.9,
            "delta_2": delta_me,
            "complete_information": True,
            "messages_allowed": False,
            "last_offer": {
                "player_1_gain": MONEY - current_gain,
                "player_2_gain": current_gain,
                "proposer": "player_1",
                "round": current_round,
            },
            "history": [
                _offer("player_1", 1, 0.40),
                _offer("player_2", 2, 0.61),
                _offer("player_1", 3, 0.43),
                _offer("player_2", 4, 0.61),
            ],
        },
        "valid_actions": {"type": "decision", "fields": {"decision": {}}},
        "prompt": "Accept or reject.",
    }


def _play(game: dict) -> dict:
    return bargaining.decide(game, Config.from_env())


def test_flag_off_and_explicit_zero_are_byte_identical(monkeypatch):
    game = _decision_game()
    before = copy.deepcopy(game)

    absent = _play(game)
    monkeypatch.setenv(FLAG, "0")
    explicit_zero = _play(game)

    assert absent == explicit_zero
    assert absent["decision"] == "reject"
    assert "high_share_delay_guard" not in absent["_plan"]
    assert game == before


def test_high_share_slow_concession_changes_only_reject_to_accept(monkeypatch):
    game = _decision_game()
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")

    candidate = _play(game)

    assert control["decision"] == "reject"
    assert candidate["decision"] == "accept"
    signal = candidate["_plan"]["high_share_delay_guard"]
    assert signal == {
        "eligible": True,
        "offered_share": 0.46,
        "minimum_share": 0.45,
        "observed_gain": 0.015,
        "observations": 3,
        "prior_best_share": 0.43,
        "candidate_threshold_share": 0.442225,
        "mode": "deterministic",
    }
    assert "high_share_delay_guard" in candidate["_plan"]["gates_fired"]


@pytest.mark.parametrize("share", [0.0, 0.20, 0.30, 0.349, 0.40, 0.449])
def test_extortion_fence_never_releases_below_45_percent(monkeypatch, share):
    game = _decision_game(current_share=share)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    if share > 0.0:
        assert out["_plan"]["high_share_delay_guard"]["eligible"] is False
    assert "high_share_delay_guard" not in out["_plan"]["gates_fired"]


def test_helper_uses_entry_proposer_and_excludes_our_offers():
    state = _decision_game()["game_state"]
    for entry in state["history"]:
        entry["offer"].pop("proposer")
    state["last_offer"].pop("proposer")

    evidence = bargaining._genuine_opponent_gain(state, "player_2", MONEY)

    assert evidence == {
        "rate": pytest.approx(0.015),
        "offers": 3,
        "first_round": 1,
        "last_round": 5,
        "last_gain": 460.0,
        "prior_best_gain": 430.0,
    }


def test_helper_deduplicates_current_offer_when_history_echoes_it():
    state = _decision_game()["game_state"]
    state["history"].append({
        **copy.deepcopy(state["last_offer"]),
        "offer": copy.deepcopy(state["last_offer"]),
        "decision": "reject",
    })

    evidence = bargaining._genuine_opponent_gain(state, "player_2", MONEY)

    assert evidence is not None
    assert evidence["offers"] == 3


@pytest.mark.parametrize("bad", ["nan", "inf", -1.0, MONEY + 1.0])
def test_malformed_opponent_gain_fails_closed(monkeypatch, bad):
    game = _decision_game()
    game["game_state"]["history"][0]["offer"]["player_2_gain"] = bad
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "high_share_delay_guard" not in out["_plan"]


def test_two_genuine_opponent_offers_are_not_enough(monkeypatch):
    game = _decision_game()
    game["game_state"]["history"] = game["game_state"]["history"][2:]
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "high_share_delay_guard" not in out["_plan"]


def test_patient_player_is_unchanged(monkeypatch):
    game = _decision_game(delta_me=1.0)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "high_share_delay_guard" not in out["_plan"]


def test_guard_requires_the_deterministic_discount_stack(monkeypatch):
    game = _decision_game()
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_BARG_DISCOUNT_NO_REGRESS", "0")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "high_share_delay_guard" not in out["_plan"]


@pytest.mark.parametrize(("knob", "value"), [
    ("GLEE_BARG_ACCEPT_FLOOR", "0.49"),
    ("GLEE_BARG_ACCEPT_FLOOR", "0.60"),
    ("GLEE_BARG_FLOOR_GAIN", "0.04"),
    ("GLEE_BARG_FLOOR_GAIN", "0.06"),
])
def test_guard_is_pinned_to_the_measured_peak_stack(monkeypatch, knob, value):
    game = _decision_game()
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(knob, value)

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"]["high_share_delay_guard"]["eligible"] is False


@pytest.mark.parametrize("overlap", [
    "GLEE_BARG_DISCOUNT_NO_REGRESS_AB",
    "GLEE_BARG_NO_REGRESS",
    "GLEE_BARG_OBSERVED_GAIN",
    "GLEE_BARG_ECON_STALL",
    "GLEE_BARG_STONEWALL",
    "GLEE_OPP_EXPLOIT",
])
def test_guard_fails_closed_on_legacy_overlap(monkeypatch, overlap):
    game = _decision_game()
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(overlap, "1")

    out = _play(game)

    assert "high_share_delay_guard" not in out["_plan"]
    assert "high_share_delay_guard" not in out["_plan"]["gates_fired"]


def test_withdrawn_high_offer_cannot_trigger(monkeypatch):
    game = _decision_game(current_share=0.45)
    game["game_state"]["history"][0] = _offer("player_1", 1, 0.46)
    game["game_state"]["history"][2] = _offer("player_1", 3, 0.49)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"]["high_share_delay_guard"]["eligible"] is False
    assert "high_share_delay_guard" not in out["_plan"]["gates_fired"]


@pytest.mark.parametrize("share", [0.45, 0.46, 0.49])
def test_delta_point_8_has_no_action_change_under_the_pinned_stack(monkeypatch, share):
    game = _decision_game(current_share=share, delta_me=0.8)
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _play(game)

    assert candidate["decision"] == control["decision"]
    assert "high_share_delay_guard" not in candidate["_plan"]["gates_fired"]


@pytest.mark.parametrize("share", [0.10, 0.30, 0.449, 0.45, 0.46, 0.499, 0.50, 0.60])
def test_guard_never_changes_an_accept_to_reject(monkeypatch, share):
    game = _decision_game(current_share=share)
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _play(game)

    if control["decision"] == "accept":
        assert candidate["decision"] == "accept"
