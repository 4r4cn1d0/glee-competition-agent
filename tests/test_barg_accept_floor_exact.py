"""Regression tests for exact discount-derived bargaining floor equality."""

from __future__ import annotations

import copy
import math
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import bargaining


FLAG = "GLEE_BARG_ACCEPT_FLOOR_EXACT_V1"
LIVE_STACK = {
    "GLEE_BARG_ACCEPT_FLOOR": "0.50",
    "GLEE_BARG_FLOOR_GAIN": "0.05",
    "GLEE_BARG_OFFER_FLOOR": "0.57",
    "GLEE_BARG_OPPONENT_FLOOR": "0.39",
    "GLEE_BARG_SPE_WEIGHT": "1.0",
    "GLEE_BARG_DISCOUNT_NO_REGRESS": "1",
    "GLEE_TRACE_GATES": "1",
}


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("GLEE_BARG", "GLEE_OPP")):
            monkeypatch.delenv(key, raising=False)
    for key, value in LIVE_STACK.items():
        monkeypatch.setenv(key, value)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _decision_state(delta: float, share: float, *, player: str = "player_1",
                    known: bool = True, messages: bool = False,
                    complete: bool = True, money: float = 100.0,
                    offset: float = 0.0, round_no: int | None = None) -> dict:
    """A frozen midgame state where continuation is below the exact floor."""
    opponent = "player_2" if player == "player_1" else "player_1"
    round_no = round_no or (8 if player == "player_1" else 7)
    opponent_gain = share * money + offset
    own_gain = 0.57 * money

    def _offer(proposer: str, receiver_gain: float) -> dict:
        if player == "player_1":
            alice_gain, bob_gain = receiver_gain, money - receiver_gain
        else:
            alice_gain, bob_gain = money - receiver_gain, receiver_gain
        if proposer == player:
            alice_gain, bob_gain = (
                (own_gain, money - own_gain) if player == "player_1"
                else (money - own_gain, own_gain))
        return {
            "player_1_gain": alice_gain,
            "player_2_gain": bob_gain,
            "proposer": proposer,
        }

    history = []
    for prior_round in range(1, round_no):
        proposer = "player_1" if prior_round % 2 else "player_2"
        offer = _offer(proposer, opponent_gain)
        offer["round"] = prior_round
        history.append({
            "round": prior_round,
            "proposer": offer["proposer"],
            "offer": offer,
            "decision": "reject",
        })
    live = _offer(opponent, opponent_gain)
    live["round"] = round_no
    state = {
        "game_family": "bargaining",
        "round": round_no,
        "horizon_known": known,
        "phase": "decision",
        "current_player": player,
        "proposer": opponent,
        "money_to_divide": money,
        "complete_information": complete,
        "messages_allowed": messages,
        "last_offer": live,
        "history": history,
    }
    own_delta_key = "delta_1" if player == "player_1" else "delta_2"
    opponent_delta_key = "delta_2" if player == "player_1" else "delta_1"
    state[own_delta_key] = delta
    if complete:
        state[opponent_delta_key] = 0.95
    if known:
        state["max_rounds"] = 12
    return {
        "game_id": (f"accept-floor-exact-{delta}-{share}-{player}-"
                    f"{known}-{messages}-{complete}-{money}-{offset}-{round_no}"),
        "game_family": "bargaining",
        "your_player": player,
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _play(game: dict) -> dict:
    raw = bargaining.decide(copy.deepcopy(game), Config.from_env())
    plan = raw.pop("_plan")
    action = coerce(raw, game)
    action["_plan"] = plan
    return action


@pytest.mark.parametrize(("delta", "share"), [(0.8, 0.20), (0.9, 0.45)])
def test_flag_repairs_only_the_exact_float_boundary(monkeypatch, delta, share):
    game = _decision_state(delta, share)

    control = _play(game)
    assert control["decision"] == "reject"
    assert "accept_floor_exact_v1" not in control["_plan"]

    monkeypatch.setenv(FLAG, "1")
    candidate = _play(game)
    assert candidate["decision"] == "accept"
    assert candidate["_plan"]["accept_floor_exact_v1"]["eligible"] is True
    assert "accept_floor_exact_v1" in candidate["_plan"]["gates_fired"]


def test_absent_and_explicit_zero_are_byte_identical(monkeypatch):
    game = _decision_state(0.8, 0.20)
    absent = _play(game)

    monkeypatch.setenv(FLAG, "0")
    explicit_zero = _play(game)

    assert explicit_zero == absent


@pytest.mark.parametrize(("delta", "share"), [(0.8, 0.20), (0.9, 0.45)])
@pytest.mark.parametrize("player", ["player_1", "player_2"])
@pytest.mark.parametrize("known", [True, False])
@pytest.mark.parametrize("messages", [True, False])
@pytest.mark.parametrize("complete", [True, False])
@pytest.mark.parametrize("money", [100.0, 10_000.0, 1_000_000.0])
def test_exact_stack_reaches_both_roles_and_configuration_dimensions(
        monkeypatch, delta, share, player, known, messages, complete, money):
    monkeypatch.setenv(FLAG, "1")

    out = _play(_decision_state(
        delta, share, player=player, known=known, messages=messages,
        complete=complete, money=money))

    assert out["decision"] == "accept"
    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is True


@pytest.mark.parametrize(("delta", "share"), [(0.8, 0.1999), (0.9, 0.4499)])
def test_even_one_cent_below_a_hundred_dollar_boundary_still_rejects(
        monkeypatch, delta, share):
    monkeypatch.setenv(FLAG, "1")
    out = _play(_decision_state(delta, share))

    assert out["decision"] == "reject"
    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is False


@pytest.mark.parametrize(("delta", "share"), [(0.8, 0.20), (0.9, 0.45)])
def test_next_float_below_the_wire_atom_still_rejects(monkeypatch, delta, share):
    target = share * 100.0
    offset = math.nextafter(target, -math.inf) - target
    monkeypatch.setenv(FLAG, "1")

    out = _play(_decision_state(delta, share, offset=offset))

    assert out["decision"] == "reject"
    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is False


@pytest.mark.parametrize(("name", "value"), [
    ("GLEE_BARG_ACCEPT_FLOOR", "0.49"),
    ("GLEE_BARG_FLOOR_GAIN", "0.04"),
    ("GLEE_BARG_DISCOUNT_NO_REGRESS", "0"),
    ("GLEE_BARG_DISCOUNT_NO_REGRESS_AB", "1"),
    ("GLEE_BARG_NO_REGRESS", "1"),
    ("GLEE_BARG_OBSERVED_GAIN", "1"),
    ("GLEE_BARG_STONEWALL", "4"),
    ("GLEE_BARG_ECON_STALL", "0.001"),
    ("GLEE_OPP_EXPLOIT", "1"),
])
def test_flag_fails_closed_outside_the_measured_stack(monkeypatch, name, value):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(name, value)

    out = _play(_decision_state(0.8, 0.20))

    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is False
    assert "accept_floor_exact_v1" not in out["_plan"]["gates_fired"]


def test_other_discount_values_are_untouched(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    out = _play(_decision_state(0.95, 0.50))

    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is False
    assert "accept_floor_exact_v1" not in out["_plan"]["gates_fired"]


@pytest.mark.parametrize("delta", [0.95, 1.0])
def test_patient_discount_cells_are_untouched(monkeypatch, delta):
    monkeypatch.setenv(FLAG, "1")
    out = _play(_decision_state(delta, 0.50))

    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is False
    assert "accept_floor_exact_v1" not in out["_plan"]["gates_fired"]


def test_continuation_value_can_still_block_the_exact_atom(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    out = _play(_decision_state(
        0.8, 0.20, player="player_2", round_no=1))

    assert out["decision"] == "reject"
    signal = out["_plan"]["accept_floor_exact_v1"]
    assert signal["pre_floor_threshold_share"] > 0.20
    assert signal["eligible"] is False


def test_final_two_rounds_and_zero_offer_are_untouched(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    final_two = _play(_decision_state(
        0.8, 0.20, player="player_2", round_no=11))
    zero = _play(_decision_state(0.8, 0.0))

    assert final_two["_plan"]["rounds_left"] == 2
    assert final_two["_plan"]["accept_floor_exact_v1"]["eligible"] is False
    assert zero["decision"] == "reject"
    assert zero["_plan"]["accept_floor_exact_v1"]["eligible"] is False


def test_an_offer_the_old_path_already_accepts_is_not_claimed(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    out = _play(_decision_state(0.8, 0.50))

    assert out["decision"] == "accept"
    assert out["_plan"]["accept_floor_exact_v1"]["eligible"] is False


def test_zero_pot_fails_closed_without_division(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    out = _play(_decision_state(0.8, 0.20, money=0.0))

    signal = out["_plan"]["accept_floor_exact_v1"]
    assert signal["eligible"] is False
    assert signal["offered_share"] is None


def test_malformed_pot_fails_closed_without_division(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    game = _decision_state(0.8, 0.20)
    game["game_state"]["money_to_divide"] = "not-a-number"
    out = _play(game)

    signal = out["_plan"]["accept_floor_exact_v1"]
    assert signal["eligible"] is False
    assert signal["offered_share"] is None


def test_high_share_guard_can_coexist_and_keeps_first_ownership(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_BARG_HIGH_SHARE_DELAY_GUARD", "1")

    low = _play(_decision_state(0.8, 0.20))
    high = _play(_decision_state(0.9, 0.45))

    assert low["decision"] == "accept"
    assert low["_plan"]["accept_floor_exact_v1"]["eligible"] is True
    assert high["decision"] == "accept"
    assert high["_plan"]["accept_floor_exact_v1"]["eligible"] is False
    assert "high_share_delay_guard" in high["_plan"]["gates_fired"]


def test_bob_commitment_component_keeps_ownership(monkeypatch):
    game = _decision_state(
        0.95, 0.60, player="player_2", round_no=1, known=True,
        messages=False)
    monkeypatch.setenv("GLEE_BARG_P2_H12_D095_SILENT_V1", "1")
    control = bargaining.decide(copy.deepcopy(game), Config.from_env())

    monkeypatch.setenv(FLAG, "1")
    candidate = bargaining.decide(copy.deepcopy(game), Config.from_env())

    assert candidate == control
    assert "accept_floor_exact_v1" not in candidate["_plan"]
