"""Regression tests for the deterministic P1 unknown-horizon delay repair."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import bargaining_p2_commitment as commitment
from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import bargaining
from scripts import check_reachability


MONEY = 1000.0
FLAG = "GLEE_BARG_P1_UNKNOWN_DISCOUNT_DOMINANCE_V1"
GATE = "p1_unknown_discount_dominance_v1"
BASE_FLAGS = {
    # Exact Test 2 peak stack pinned by the candidate.  Every alternative
    # acceptance/floor path is explicit OFF so this file cannot accidentally
    # test a different strategy composition inherited from the shell.
    "GLEE_BARG_ACCEPT_FLOOR": "0.50",
    "GLEE_BARG_FLOOR_GAIN": "0.05",
    "GLEE_BARG_OFFER_FLOOR": "0.57",
    "GLEE_BARG_OPPONENT_FLOOR": "0.39",
    "GLEE_BARG_SPE_WEIGHT": "1.0",
    "GLEE_BARG_UNCAPPED_HORIZON": "60",
    "GLEE_BARG_UNDISCLOSED_HORIZON": "99",
    "GLEE_BARG_BOB_OFFER": "1",
    "GLEE_BARG_DISCOUNT_NO_REGRESS": "0",
    "GLEE_BARG_DISCOUNT_NO_REGRESS_AB": "0",
    "GLEE_BARG_NO_REGRESS": "0",
    "GLEE_BARG_HIGH_SHARE_DELAY_GUARD": "0",
    "GLEE_BARG_ACCEPT_FLOOR_EXACT_V1": "0",
    "GLEE_BARG_OBSERVED_GAIN": "0",
    "GLEE_BARG_ECON_STALL": "0",
    "GLEE_BARG_STONEWALL": "0",
    "GLEE_OPP_EXPLOIT": "0",
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


def _opponent_offer(round_no: int, player_1_share: float) -> dict:
    gain = MONEY * player_1_share
    return {
        "round": round_no,
        "proposer": "player_2",
        "offer": {
            "player_1_gain": gain,
            "player_2_gain": MONEY - gain,
            "proposer": "player_2",
            "round": round_no,
        },
        "decision": "reject",
    }


def _decision_game(
    *,
    current_share: float = 0.47,
    current_round: int = 42,
    delta_me: float = 0.95,
    game_id: str | None = "p1-unknown-delay-case",
    messages_allowed: bool = False,
) -> dict:
    current_gain = MONEY * current_share
    game = {
        "game_id": game_id,
        "game_family": "bargaining",
        "your_player": "player_1",
        "phase": "decision",
        "opponent": "field-agent",
        "game_state": {
            "round": current_round,
            "horizon_known": False,
            "phase": "decision",
            "current_player": "player_1",
            "proposer": "player_2",
            "money_to_divide": MONEY,
            "delta_1": delta_me,
            "delta_2": 0.9,
            "complete_information": True,
            "messages_allowed": messages_allowed,
            "last_offer": {
                "player_1_gain": current_gain,
                "player_2_gain": MONEY - current_gain,
                "proposer": "player_2",
                "round": current_round,
            },
            "history": [
                _opponent_offer(current_round - 4, current_share - 0.02),
                _opponent_offer(current_round - 2, current_share - 0.01),
            ],
        },
        "valid_actions": {"type": "decision", "fields": {"decision": {}}},
        "prompt": "Accept or reject.",
    }
    if game_id is None:
        game.pop("game_id")
    return game


def _p2_commitment_game() -> dict:
    return {
        "game_id": "p2-commitment-isolation",
        "game_family": "bargaining",
        "your_player": "player_2",
        "phase": "decision",
        "game_state": {
            "round": 1,
            "phase": "decision",
            "current_player": "player_2",
            "proposer": "player_1",
            "money_to_divide": 100.0,
            "horizon_known": True,
            "max_rounds": 12,
            "complete_information": True,
            "messages_allowed": False,
            "history": [],
            "last_offer": {
                "player_1_gain": 40.0,
                "player_2_gain": 60.0,
                "proposer": "player_1",
                "round": 1,
            },
            "delta_1": 0.8,
            "delta_2": 0.95,
        },
        "valid_actions": {"type": "decision", "fields": {"decision": {}}},
    }


def _play(game: dict) -> dict:
    return bargaining.decide(copy.deepcopy(game), Config.from_env())


def _wire(action: dict) -> dict:
    return {key: value for key, value in action.items() if key != "_plan"}


def _gates(action: dict) -> list[str]:
    return action.get("_plan", {}).get("gates_fired", [])


def test_flag_absent_and_explicit_zero_are_byte_identical(monkeypatch):
    game = _decision_game()
    before = copy.deepcopy(game)

    absent = _play(game)
    monkeypatch.setenv(FLAG, "0")
    explicit_zero = _play(game)

    assert absent == explicit_zero
    assert absent["decision"] == "reject"
    assert GATE not in absent["_plan"]
    assert game == before


@pytest.mark.parametrize("game_id", [None, "deterministic-a", "deterministic-b"])
@pytest.mark.parametrize("messages_allowed", [False, True])
def test_exact_unknown_p1_target_accepts_without_hash_or_channel_assignment(
    monkeypatch, game_id, messages_allowed,
):
    game = _decision_game(
        game_id=game_id, messages_allowed=messages_allowed)
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")

    candidate = _play(game)

    assert control["decision"] == "reject"
    assert candidate["decision"] == "accept"
    assert GATE in _gates(candidate)
    signal = candidate["_plan"][GATE]
    assert signal["eligible"] is True
    assert signal["mode"] == "deterministic"
    assert signal["offered_share"] == pytest.approx(0.47)
    assert signal["planned_counter_share"] == pytest.approx(0.489)
    assert signal["discounted_counter_share"] == pytest.approx(0.46455)
    assert signal["delta_me"] == pytest.approx(0.95)
    assert signal["projected_round"] == 43
    assert signal["observations"] == 3
    assert signal["prior_best_share"] == pytest.approx(0.46)


@pytest.mark.parametrize("share", [0.45, 0.499])
def test_share_band_boundaries_are_inclusive_low_exclusive_high(
    monkeypatch, share,
):
    game = _decision_game(current_share=share)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "accept"
    assert out["_plan"][GATE]["eligible"] is True


def _structural_case(game: dict, case: str) -> None:
    state = game["game_state"]
    if case == "p2-seat":
        game["your_player"] = "player_2"
        state["current_player"] = "player_2"
    elif case == "wrong-current-player":
        state["current_player"] = "player_2"
    elif case == "horizon-flag-missing":
        state.pop("horizon_known")
    elif case == "horizon-disclosed":
        state["horizon_known"] = True
    elif case == "hidden-cap-present":
        state["max_rounds"] = 99
    elif case == "before-round-10":
        state["round"] = 8
        state["last_offer"]["round"] = 8
        state["history"] = [
            _opponent_offer(4, 0.45),
            _opponent_offer(6, 0.46),
        ]
    elif case == "delta-0.9":
        state["delta_1"] = 0.9
    elif case == "delta-1.0":
        state["delta_1"] = 1.0
    elif case == "delta-near-0.95":
        state["delta_1"] = 0.9500000001
    elif case == "zero-offer":
        state["last_offer"]["player_1_gain"] = 0.0
        state["last_offer"]["player_2_gain"] = MONEY
    elif case == "below-share-band":
        state["last_offer"]["player_1_gain"] = 449.0
        state["last_offer"]["player_2_gain"] = 551.0
    elif case == "at-upper-share-bound":
        state["last_offer"]["player_1_gain"] = 500.0
        state["last_offer"]["player_2_gain"] = 500.0
    elif case == "already-accepted":
        state["last_offer"]["player_1_gain"] = 510.0
        state["last_offer"]["player_2_gain"] = 490.0
    elif case == "synthetic-last-round":
        state["round"] = 99
        state["last_offer"]["round"] = 99
        state["history"] = [
            _opponent_offer(95, 0.45),
            _opponent_offer(97, 0.46),
        ]
    elif case == "only-two-offers":
        state["history"] = state["history"][-1:]
    elif case == "current-unprovenanced":
        state["last_offer"].pop("proposer")
        state["proposer"] = None
    elif case == "current-round-mismatch":
        state["last_offer"]["round"] = state["round"] - 2
    elif case == "withdrawn-current":
        state["history"][0] = _opponent_offer(
            state["round"] - 4, 0.49)
    elif case == "nonpositive-money":
        state["money_to_divide"] = 0.0
    elif case == "offer-phase":
        game["phase"] = "offer"
        state["phase"] = "offer"
        state["current_player"] = "player_1"
        state["proposer"] = "player_1"
        game["valid_actions"] = {"type": "offer", "fields": {}}
    else:
        raise AssertionError(case)


@pytest.mark.parametrize("case", [
    "p2-seat",
    "wrong-current-player",
    "horizon-flag-missing",
    "horizon-disclosed",
    "hidden-cap-present",
    "before-round-10",
    "delta-0.9",
    "delta-1.0",
    "delta-near-0.95",
    "zero-offer",
    "below-share-band",
    "at-upper-share-bound",
    "already-accepted",
    "synthetic-last-round",
    "only-two-offers",
    "current-unprovenanced",
    "current-round-mismatch",
    "withdrawn-current",
    "nonpositive-money",
    "offer-phase",
])
def test_every_structural_edge_fails_closed(monkeypatch, case):
    game = _decision_game()
    _structural_case(game, case)
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")

    candidate = _play(game)

    assert _wire(candidate) == _wire(control)
    assert GATE not in _gates(candidate)


@pytest.mark.parametrize(("knob", "value"), [
    ("GLEE_BARG_ACCEPT_FLOOR", "0.49"),
    ("GLEE_BARG_FLOOR_GAIN", "0.04"),
    ("GLEE_BARG_SPE_WEIGHT", "0.99"),
    ("GLEE_BARG_OFFER_FLOOR", "0.56"),
    ("GLEE_BARG_OPPONENT_FLOOR", "0.38"),
    ("GLEE_BARG_UNCAPPED_HORIZON", "59"),
    ("GLEE_BARG_UNDISCLOSED_HORIZON", "98"),
])
def test_candidate_is_pinned_to_the_exact_test2_numeric_stack(
    monkeypatch, knob, value,
):
    game = _decision_game()
    monkeypatch.setenv(knob, value)
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")

    candidate = _play(game)

    assert _wire(candidate) == _wire(control)
    assert GATE not in _gates(candidate)


@pytest.mark.parametrize(("overlap", "value"), [
    ("GLEE_BARG_DISCOUNT_NO_REGRESS", "1"),
    ("GLEE_BARG_DISCOUNT_NO_REGRESS_AB", "1"),
    ("GLEE_BARG_NO_REGRESS", "1"),
    ("GLEE_BARG_HIGH_SHARE_DELAY_GUARD", "1"),
    ("GLEE_BARG_ACCEPT_FLOOR_EXACT_V1", "1"),
    ("GLEE_BARG_OBSERVED_GAIN", "1"),
    ("GLEE_BARG_ECON_STALL", "0.01"),
    ("GLEE_BARG_STONEWALL", "4"),
    ("GLEE_OPP_EXPLOIT", "1"),
])
def test_candidate_fails_closed_on_every_overlapping_policy(
    monkeypatch, overlap, value,
):
    game = _decision_game()
    monkeypatch.setenv(overlap, value)
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")

    candidate = _play(game)

    assert _wire(candidate) == _wire(control)
    assert GATE not in _gates(candidate)


def test_strict_margin_does_not_accept_a_rounding_tie(monkeypatch):
    game = _decision_game()
    offered_share = 0.47
    discounted_share = offered_share - 0.5e-12
    counter_share = discounted_share / 0.95

    def rounding_tie(_game, _cfg):
        return {
            "alice_gain": MONEY * counter_share,
            "bob_gain": MONEY * (1.0 - counter_share),
        }

    monkeypatch.setattr(bargaining, "_post_reject_offer", rounding_tie)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"][GATE]["eligible"] is False
    assert GATE not in _gates(out)


def test_projection_exception_fails_closed_and_is_traced(monkeypatch):
    game = _decision_game()

    def broken_projection(_game, _cfg):
        raise RuntimeError("synthetic projection failure")

    monkeypatch.setattr(bargaining, "_post_reject_offer", broken_projection)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert out["_plan"][GATE]["eligible"] is False
    assert out["_plan"][GATE]["status"] == "projection_failed"
    assert GATE not in _gates(out)


@pytest.mark.parametrize("bad_gain", [float("nan"), -1.0, MONEY + 1.0])
def test_malformed_projected_counter_fails_closed(monkeypatch, bad_gain):
    game = _decision_game()

    def malformed_projection(_game, _cfg):
        return {"alice_gain": bad_gain, "bob_gain": MONEY - bad_gain}

    monkeypatch.setattr(bargaining, "_post_reject_offer", malformed_projection)
    monkeypatch.setenv(FLAG, "1")

    out = _play(game)

    assert out["decision"] == "reject"
    assert GATE not in _gates(out)


def test_p2_commitment_component_is_byte_identical_with_candidate_armed(
    monkeypatch,
):
    game = _p2_commitment_game()
    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")

    candidate = _play(game)

    assert candidate == control
    assert candidate["_plan"]["component"] == commitment.D095_SILENT_GATE
    assert GATE not in candidate["_plan"]


def test_reachability_registry_uses_candidate_plan_eligibility(monkeypatch):
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    assert family == "bargaining"
    assert gates == (GATE,)

    game = _decision_game()
    control = _play(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _play(game)

    assert not predicate(game, control["_plan"])
    assert predicate(game, candidate["_plan"])
