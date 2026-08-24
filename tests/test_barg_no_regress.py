"""Regression tests for the bargaining reject/counter consistency guard."""

from __future__ import annotations

import copy
import os
import random

import pytest

from glee_agent import runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.probes import make_probe, RANDOMIZED_BARG_BASE_FLAG
from glee_agent.strategies import bargaining
from sim.bargaining import BargainingEngine
from sim.types import Config as SimConfig


MONEY = 1000.0
FLAG = "GLEE_BARG_NO_REGRESS"
EPS_FLAG = "GLEE_BARG_NO_REGRESS_EPS"
DISCOUNT_AB_FLAG = "GLEE_BARG_DISCOUNT_NO_REGRESS_AB"
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


def _engine(*, game_id: str = "no-regress-case",
            delta_2: float = 0.95) -> BargainingEngine:
    config = SimConfig("bargaining", {
        "money_to_divide": MONEY,
        "delta_1": 0.8,
        "delta_2": delta_2,
        "max_rounds": 12,
        "messages_allowed": False,
        "complete_information": True,
    })
    return BargainingEngine(config, random.Random(7), game_id)


def _bob_decision(share: float = 0.70, *, game_id: str = "no-regress-case",
                  delta_2: float = 0.95) -> tuple[BargainingEngine, dict]:
    engine = _engine(game_id=game_id, delta_2=delta_2)
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


def _gid_for_discount_arm(wanted: str) -> str:
    for index in range(100):
        gid = f"discount-no-regress-{index}"
        if bargaining.discount_no_regress_assignment(gid) == wanted:
            return gid
    raise AssertionError(f"no game id found for {wanted}")


class _TurnLog:
    def __init__(self):
        self.rows = []

    def turn(self, game, action, plan, source):
        self.rows.append({
            "game": copy.deepcopy(game),
            "action": copy.deepcopy(action),
            "plan": copy.deepcopy(plan),
            "source": source,
        })


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


def test_discount_arm_is_stable_and_requires_a_game_id():
    candidate = _gid_for_discount_arm("candidate")
    control = _gid_for_discount_arm("control")

    assert bargaining.discount_no_regress_assignment(candidate) == "candidate"
    assert bargaining.discount_no_regress_assignment(candidate) == "candidate"
    assert bargaining.discount_no_regress_assignment(control) == "control"
    assert bargaining.discount_no_regress_assignment("") is None


def test_discount_arm_flag_off_keeps_the_old_reject_and_plan(monkeypatch):
    gid = _gid_for_discount_arm("candidate")
    _, game = _bob_decision(0.60, game_id=gid)

    out = _play(game)

    assert out["decision"] == "reject"
    assert "discount_no_regress" not in out["_plan"]


def test_discount_candidate_accepts_when_next_counter_is_worth_less(monkeypatch):
    gid = _gid_for_discount_arm("candidate")
    _, game = _bob_decision(0.60, game_id=gid)
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")

    out = _play(game)

    assert out["decision"] == "accept"
    assert out["_plan"]["discount_no_regress"] == {
        "arm": "candidate",
        "eligible": True,
        "offered_share": 0.6,
        "planned_counter_share": 0.61,
        "discounted_counter_share": 0.5795,
        "delta_me": 0.95,
        "projected_round": 2,
    }


def test_discount_hash_control_logs_same_signal_but_keeps_reject(monkeypatch):
    gid = _gid_for_discount_arm("control")
    _, game = _bob_decision(0.60, game_id=gid)
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"]["discount_no_regress"]["arm"] == "control"
    assert out["_plan"]["discount_no_regress"]["eligible"] is True


def test_discount_arm_excludes_the_measured_harmful_patient_cell(monkeypatch):
    gid = _gid_for_discount_arm("candidate")
    _, game = _bob_decision(0.60, game_id=gid, delta_2=1.0)
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "discount_no_regress" not in out["_plan"]


def test_discount_candidate_never_turns_a_zero_offer_into_an_accept(monkeypatch):
    gid = _gid_for_discount_arm("candidate")
    _, game = _bob_decision(0.0, game_id=gid)
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "discount_no_regress" not in out["_plan"]


def test_discount_arm_fails_closed_when_nominal_guard_is_armed(monkeypatch):
    gid = _gid_for_discount_arm("candidate")
    _, game = _bob_decision(0.60, game_id=gid)
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert "discount_no_regress" not in out["_plan"]
    assert out["_plan"]["no_regress"]["planned_counter_share"] == 0.61


def test_test4_route_off_keeps_random_bargaining_probe(monkeypatch):
    gid = _gid_for_discount_arm("candidate")
    _, game = _bob_decision(0.60, game_id=gid)
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")
    log = _TurnLog()

    probe, _ = make_probe("randomized", Config.from_env(), log=log, seed=7)
    probe(game)

    assert log.rows[-1]["source"] == "probe:randomized"
    assert log.rows[-1]["plan"] is None


@pytest.mark.parametrize(
    ("arm", "expected"),
    [("candidate", "accept"), ("control", "reject")],
)
def test_test4_route_reaches_discount_strategy_arm(monkeypatch, arm, expected):
    gid = _gid_for_discount_arm(arm)
    _, game = _bob_decision(0.60, game_id=gid)
    monkeypatch.setenv(RANDOMIZED_BARG_BASE_FLAG, "1")
    monkeypatch.setenv(DISCOUNT_AB_FLAG, "1")
    log = _TurnLog()

    probe, _ = make_probe("randomized", Config.from_env(), log=log, seed=7)
    out = probe(game)

    assert out["decision"] == expected
    assert log.rows[-1]["source"] == "heuristic"
    signal = log.rows[-1]["plan"]["discount_no_regress"]
    assert signal["arm"] == arm
    assert signal["eligible"] is True


@pytest.mark.parametrize("family", ["negotiation", "persuasion"])
def test_test4_route_leaves_other_randomized_families_unchanged(monkeypatch, family):
    if family == "negotiation":
        game = {
            "game_id": "test4-route-negotiation",
            "game_family": family,
            "your_player": "player_1",
            "game_state": {
                "current_player": "player_1",
                "player_1_role": "seller",
                "player_1_value": 100.0,
            },
            "valid_actions": {"type": "offer"},
        }
    else:
        game = {
            "game_id": "test4-route-persuasion",
            "game_family": family,
            "your_player": "player_1",
            "game_state": {"current_quality": "high"},
            "valid_actions": {"type": "seller_recommendation"},
        }

    off, _ = make_probe("randomized", Config.from_env(), seed=11)
    expected = off(copy.deepcopy(game))
    monkeypatch.setenv(RANDOMIZED_BARG_BASE_FLAG, "1")
    on, _ = make_probe("randomized", Config.from_env(), seed=11)

    assert on(copy.deepcopy(game)) == expected


@pytest.mark.parametrize(
    ("arm", "decision", "gates"),
    [
        ("candidate", "accept", ["discount_no_regress"]),
        ("control", "reject", []),
    ],
)
def test_live_reader_recovers_first_trigger_and_audits_wire(
        arm, decision, gates):
    from scripts import live_percentile

    gid = _gid_for_discount_arm(arm)
    rec = {
        "ts": 123.0,
        "game_id": gid,
        "game_family": "bargaining",
        "round": 3,
        "plan": {
            "discount_no_regress": {
                "arm": arm,
                "eligible": True,
                "offered_share": 0.60,
                "planned_counter_share": 0.61,
                "discounted_counter_share": 0.5795,
                "delta_me": 0.95,
                "projected_round": 4,
            },
            "gates_fired": gates,
        },
        "action": {"decision": decision},
    }

    key, ts, diagnostic = live_percentile._barg_discount_no_regress_exposure_turn(
        "hardliner", rec)

    assert key == ("hardliner", gid)
    assert ts == 123.0
    assert diagnostic["assignment_ok"] is True
    assert diagnostic["wire_ok"] is True
    assert diagnostic["trace_ok"] is True


def test_live_reader_ignores_noneligible_discount_signal():
    from scripts import live_percentile

    gid = _gid_for_discount_arm("control")
    rec = {
        "ts": 123.0,
        "game_id": gid,
        "game_family": "bargaining",
        "plan": {"discount_no_regress": {
            "arm": "control", "eligible": False}},
        "action": {"decision": "reject"},
    }

    assert live_percentile._barg_discount_no_regress_exposure_turn(
        "hardliner", rec) is None


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
