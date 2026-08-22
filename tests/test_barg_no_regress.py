"""Regression tests for the bargaining reject/counter consistency guard."""

from __future__ import annotations

import copy
import os
import random

import pytest

from glee_agent import runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import bargaining
from sim.bargaining import BargainingEngine
from sim.types import Config as SimConfig


MONEY = 1000.0
FLAG = "GLEE_BARG_NO_REGRESS"
EPS_FLAG = "GLEE_BARG_NO_REGRESS_EPS"
LIVE_FLAGS = {
    "GLEE_BARG_ACCEPT_FLOOR": "0.50",
    "GLEE_BARG_FLOOR_GAIN": "0.05",
    "GLEE_BARG_OFFER_FLOOR": "0.57",
    "GLEE_BARG_OPPONENT_FLOOR": "0.39",
    "GLEE_BARG_SPE_WEIGHT": "1.0",
}


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("GLEE_BARG", "GLEE_OPP", "GLEE_PROBE")):
            monkeypatch.delenv(key, raising=False)
    for key, value in LIVE_FLAGS.items():
        monkeypatch.setenv(key, value)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _engine() -> BargainingEngine:
    config = SimConfig("bargaining", {
        "money_to_divide": MONEY,
        "delta_1": 0.8,
        "delta_2": 0.95,
        "max_rounds": 12,
        "messages_allowed": False,
        "complete_information": True,
    })
    return BargainingEngine(config, random.Random(7), "no-regress-case")


def _bob_decision(share: float = 0.70) -> tuple[BargainingEngine, dict]:
    engine = _engine()
    assert engine.submit("player_1", {
        "alice_gain": MONEY * (1.0 - share),
        "bob_gain": MONEY * share,
    }).valid
    return engine, engine.observation("player_2")


def _play(g: dict) -> dict:
    raw = bargaining.decide(g, Config.from_env())
    plan = raw.pop("_plan")
    action = coerce(raw, g)
    action["_plan"] = plan
    return action


def test_flag_off_rejects_the_measured_70_then_61_case(monkeypatch):
    _, game = _bob_decision(0.70)
    before = copy.deepcopy(game)

    off = _play(game)
    assert off["decision"] == "reject"
    assert "no_regress" not in off["_plan"]
    assert game == before

    monkeypatch.setenv(EPS_FLAG, "1.0")
    eps_only = _play(game)
    assert eps_only["decision"] == "reject"
    assert "no_regress" not in eps_only["_plan"]


def test_flag_on_accepts_70_instead_of_countering_with_61(monkeypatch):
    _, game = _bob_decision(0.70)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "accept"
    assert out["_plan"]["no_regress"] == {
        "offered_share": 0.7,
        "planned_counter_share": 0.61,
        "epsilon": 0.0,
        "projected_round": 2,
    }


def test_projection_equals_the_real_next_turn_offer(monkeypatch):
    engine, game = _bob_decision(0.70)
    before = copy.deepcopy(game)
    monkeypatch.setenv(FLAG, "1")
    projected = _play(game)["_plan"]["no_regress"]["planned_counter_share"]

    assert engine.submit("player_2", {"decision": "reject"}).valid
    next_game = engine.observation("player_2")
    actual = _play(next_game)

    assert actual["bob_gain"] / MONEY == pytest.approx(projected)
    assert projected == pytest.approx(0.61)
    assert game == before


@pytest.mark.parametrize(
    ("offered", "epsilon", "expected"),
    [
        (0.60, 0.0, "reject"),
        (0.61, 0.0, "accept"),
        (0.609, 0.0, "reject"),
        (0.609, 0.0011, "accept"),
    ],
)
def test_epsilon_is_a_share_tolerance(monkeypatch, offered, epsilon, expected):
    _, game = _bob_decision(offered)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(EPS_FLAG, str(epsilon))

    out = _play(game)

    assert out["decision"] == expected
    assert out["_plan"]["no_regress"]["epsilon"] == epsilon


def test_projection_includes_later_bob_offer_writer(monkeypatch):
    from glee_agent import barg_offer

    _, game = _bob_decision(0.70)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_BARG_BOB_OFFER", "1")
    monkeypatch.setattr(
        barg_offer,
        "best_ask",
        lambda **kwargs: (0.80, {"status": "applied", "reason": "test"}),
    )

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"]["no_regress"]["planned_counter_share"] == 0.80


def test_non_finite_epsilon_fails_closed_to_zero(monkeypatch):
    _, game = _bob_decision(0.609)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(EPS_FLAG, "nan")

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"]["no_regress"]["epsilon"] == 0.0


def test_nonfinal_zero_offer_is_compared_and_still_rejected(monkeypatch):
    _, game = _bob_decision(0.0)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"]["no_regress"]["offered_share"] == 0.0
    assert out["_plan"]["no_regress"]["planned_counter_share"] == 0.61


def test_final_zero_offer_keeps_the_existing_reject(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    state = {
        "round": 12,
        "phase": "decision",
        "current_player": "player_2",
        "proposer": "player_1",
        "money_to_divide": MONEY,
        "horizon_known": True,
        "max_rounds": 12,
        "complete_information": True,
        "messages_allowed": False,
        "history": [],
        "last_offer": {
            "player_1_gain": MONEY,
            "player_2_gain": 0.0,
            "proposer": "player_1",
            "round": 12,
        },
        "delta_1": 0.8,
        "delta_2": 0.95,
    }
    game = {
        "game_id": "terminal-zero",
        "game_family": "bargaining",
        "your_player": "player_2",
        "phase": "decision",
        "game_state": state,
        "valid_actions": {"type": "decision"},
    }

    out = _play(game)

    assert out["decision"] == "reject"
    assert "no_regress" not in out["_plan"]
