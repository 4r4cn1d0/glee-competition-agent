"""Tests for deterministic Bob commitment policies in disclosed H=12 games."""

from __future__ import annotations

import copy
import math
import os
import random

import pytest

from glee_agent import bargaining_p2_commitment as commitment
from glee_agent import runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.dispatch import make_strategy
from glee_agent.strategies import bargaining
from scripts import check_reachability
from sim.bargaining import BargainingEngine
from sim.types import Config as SimConfig


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("GLEE_BARG", "GLEE_OPP", "GLEE_PROBE")):
            monkeypatch.delenv(key, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _offer_game(*, money=100.0, rnd=2, delta=0.95,
                messages_allowed=False) -> dict:
    return {
        "game_id": f"commit-offer-{money}-{rnd}-{delta}-{messages_allowed}",
        "game_family": "bargaining",
        "your_player": "player_2",
        "phase": "offer",
        "game_state": {
            "round": rnd,
            "phase": "offer",
            "current_player": "player_2",
            "proposer": "player_2",
            "money_to_divide": money,
            "horizon_known": True,
            "max_rounds": 12,
            "complete_information": True,
            "messages_allowed": messages_allowed,
            "history": [],
            "last_offer": None,
            "delta_1": 0.8,
            "delta_2": delta,
        },
        "valid_actions": {
            "type": "offer",
            "fields": {"alice_gain": {}, "bob_gain": {},
                       **({"message": {}} if messages_allowed else {})},
        },
    }


def _decision_game(bob_gain: float, *, money=100.0, rnd=1,
                   delta=0.95, messages_allowed=False) -> dict:
    last = {
        "player_1_gain": money - bob_gain,
        "player_2_gain": bob_gain,
        "proposer": "player_1",
        "round": rnd,
    }
    return {
        "game_id": f"commit-decision-{money}-{rnd}-{delta}",
        "game_family": "bargaining",
        "your_player": "player_2",
        "phase": "decision",
        "game_state": {
            "round": rnd,
            "phase": "decision",
            "current_player": "player_2",
            "proposer": "player_1",
            "money_to_divide": money,
            "horizon_known": True,
            "max_rounds": 12,
            "complete_information": True,
            "messages_allowed": messages_allowed,
            "history": [],
            "last_offer": last,
            "delta_1": 0.8,
            "delta_2": delta,
        },
        "valid_actions": {"type": "decision", "fields": {"decision": {}}},
    }


def _wire(game: dict) -> tuple[dict, dict]:
    raw = bargaining.decide(game, Config(llm_mode="off"))
    plan = raw.pop("_plan")
    return coerce(raw, game), plan


@pytest.mark.parametrize(
    "flag,game",
    [
        (commitment.D095_SILENT_FLAG, _offer_game()),
        (commitment.D095_MSG_FLAG, _offer_game(messages_allowed=True)),
        (commitment.D100_FLAG, _offer_game(delta=1.0)),
        (commitment.D100_FLAG,
         _offer_game(delta=1.0, messages_allowed=True)),
    ],
)
def test_exact_scope_is_eligible_and_trace_predicates_are_public(flag, game):
    assert commitment.eligible_for_flag(game, flag)
    assert commitment.GATE_BY_FLAG[flag]
    for other in commitment.FLAGS:
        if other != flag:
            # D095 silent/message deliberately differ only in channel scope;
            # D100 differs in its exact discount cell.
            assert not commitment.eligible_for_flag(game, other)


def test_decision_scope_accepts_real_odd_receiver_phase_only():
    game = _decision_game(60.0)
    assert commitment.eligible_for_flag(game, commitment.D095_SILENT_FLAG)

    for mutation in ("top_phase", "state_phase", "current", "proposer",
                     "last_proposer", "last_round", "bad_split", "negative",
                     "parity"):
        bad = copy.deepcopy(game)
        if mutation == "top_phase":
            bad["phase"] = "offer"
        elif mutation == "state_phase":
            bad["game_state"]["phase"] = "offer"
        elif mutation == "current":
            bad["game_state"]["current_player"] = "player_1"
        elif mutation == "proposer":
            bad["game_state"]["proposer"] = "player_2"
        elif mutation == "last_proposer":
            bad["game_state"]["last_offer"]["proposer"] = "player_2"
        elif mutation == "last_round":
            bad["game_state"]["last_offer"]["round"] = 3
        elif mutation == "bad_split":
            bad["game_state"]["last_offer"]["player_1_gain"] += 0.01
        elif mutation == "negative":
            bad["game_state"]["last_offer"]["player_2_gain"] = -1.0
        else:
            bad["game_state"]["round"] = 2
            bad["game_state"]["last_offer"]["round"] = 2
        assert not commitment.eligible_for_flag(
            bad, commitment.D095_SILENT_FLAG), mutation


def test_impossible_even_final_receiver_state_fails_closed(monkeypatch):
    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    for bob_gain in (1.0, 100.0):
        game = _decision_game(bob_gain, rnd=12)
        assert not commitment.eligible_for_flag(
            game, commitment.D095_SILENT_FLAG)
        assert commitment.action(game) is None


@pytest.mark.parametrize(
    "mutation",
    ["family", "your_player", "current", "known", "cap", "delta",
     "messages", "round", "phase", "proposer", "money"],
)
def test_offer_scope_fails_closed_outside_exact_cell(mutation):
    game = _offer_game()
    state = game["game_state"]
    if mutation == "family":
        game["game_family"] = "negotiation"
    elif mutation == "your_player":
        game["your_player"] = "player_1"
    elif mutation == "current":
        state["current_player"] = "player_1"
    elif mutation == "known":
        state["horizon_known"] = False
    elif mutation == "cap":
        state["max_rounds"] = 10
    elif mutation == "delta":
        state["delta_2"] = 0.9500000001
    elif mutation == "messages":
        state["messages_allowed"] = True
    elif mutation == "round":
        state["round"] = 3
    elif mutation == "phase":
        game["valid_actions"]["type"] = "decision"
    elif mutation == "proposer":
        state["proposer"] = "player_1"
    else:
        state["money_to_divide"] = 0.0
    assert not commitment.eligible_for_flag(
        game, commitment.D095_SILENT_FLAG)


def test_flag_off_and_armed_but_ineligible_are_byte_identical(monkeypatch):
    game = _offer_game()
    old = bargaining._decide(copy.deepcopy(game), Config(llm_mode="off"))
    assert bargaining.decide(copy.deepcopy(game), Config(llm_mode="off")) == old

    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    ineligible = _offer_game(delta=0.9)
    old_ineligible = bargaining._decide(
        copy.deepcopy(ineligible), Config(llm_mode="off"))
    assert bargaining.decide(
        copy.deepcopy(ineligible), Config(llm_mode="off")) == old_ineligible


def test_multiple_component_flags_fail_closed(monkeypatch):
    game = _offer_game()
    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    monkeypatch.setenv(commitment.D100_FLAG, "1")
    assert commitment.active_flag(game) is None
    assert bargaining.decide(game, Config(llm_mode="off"))["bob_gain"] != 61.0


def test_legacy_random_message_arm_conflicts_only_with_message_policy(monkeypatch):
    msg = _offer_game(messages_allowed=True)
    monkeypatch.setenv(commitment.D095_MSG_FLAG, "1")
    monkeypatch.setenv(commitment.LEGACY_MESSAGE_FLAG, "1")
    assert commitment.active_flag(msg) is None

    monkeypatch.delenv(commitment.D095_MSG_FLAG)
    monkeypatch.setenv(commitment.D100_FLAG, "1")
    d100_msg = _offer_game(delta=1.0, messages_allowed=True)
    assert commitment.active_flag(d100_msg) is None

    # With a closed channel D100 is numeric-only, so there is no message-policy
    # collision.  The old arm cannot attach text to this game.
    assert commitment.active_flag(_offer_game(delta=1.0)) == commitment.D100_FLAG


@pytest.mark.parametrize("money", [100.0, 10_000.0, 1_000_000.0])
def test_silent_ladder_and_terminal_cent_reach_the_wire_exactly(monkeypatch, money):
    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    for rnd, share in {**commitment.SILENT_SHARES, 12: None}.items():
        game = _offer_game(money=money, rnd=rnd)
        action, plan = _wire(game)
        expected_bob = money - 0.01 if rnd == 12 else money * share
        assert action["bob_gain"] == pytest.approx(expected_bob, abs=1e-9)
        assert action["alice_gain"] + action["bob_gain"] == money
        if rnd == 12:
            assert action == {"alice_gain": 0.01, "bob_gain": money - 0.01}
        assert plan["component"] == commitment.D095_SILENT_GATE
        assert "message" not in action


@pytest.mark.parametrize("money", [100.0, 10_000.0, 1_000_000.0])
def test_message_commitment_formula_reaches_wire_without_integer_rounding(
        monkeypatch, money):
    monkeypatch.setenv(commitment.D095_MSG_FLAG, "1")
    for rnd in (2, 4, 6, 8, 10, 12):
        game = _offer_game(
            money=money, rnd=rnd, messages_allowed=True)
        action, _ = _wire(game)
        if rnd == 12:
            expected_bob = money - 0.01
        else:
            floor = (money - 0.01) * 0.95 ** 11
            expected_bob = floor / 0.95 ** rnd - 0.01
        assert action["bob_gain"] == expected_bob
        assert action["alice_gain"] + action["bob_gain"] == money
        assert len(action["message"]) <= 2000


@pytest.mark.parametrize("money", [100.0, 10_000.0, 1_000_000.0])
@pytest.mark.parametrize("messages_allowed", [False, True])
def test_patient_policy_leaves_one_cent_on_every_offer(
        monkeypatch, money, messages_allowed):
    monkeypatch.setenv(commitment.D100_FLAG, "1")
    for rnd in (2, 4, 6, 8, 10, 12):
        game = _offer_game(money=money, rnd=rnd, delta=1.0,
                           messages_allowed=messages_allowed)
        action, plan = _wire(game)
        assert action["alice_gain"] == 0.01
        assert action["bob_gain"] == money - 0.01
        assert action["alice_gain"] + action["bob_gain"] == money
        assert ("message" in action) is messages_allowed
        assert plan["component"] == commitment.D100_GATE


@pytest.mark.parametrize(
    "flag,delta,messages_allowed",
    [
        (commitment.D095_SILENT_FLAG, 0.95, False),
        (commitment.D095_MSG_FLAG, 0.95, True),
        (commitment.D100_FLAG, 1.0, False),
    ],
)
@pytest.mark.parametrize("rnd", [1, 5, 11])
def test_decision_threshold_is_exact_immediately_below_equal_and_above(
        monkeypatch, flag, delta, messages_allowed, rnd):
    monkeypatch.setenv(flag, "1")
    money = 10_000.0
    floor = ((money - 0.01) * 0.95 ** 11
             if delta == 0.95 else money - 0.01)
    required = floor / delta ** (rnd - 1)
    cases = [
        (math.nextafter(required, -math.inf), "reject"),
        (required, "accept"),
        (math.nextafter(required, math.inf), "accept"),
    ]
    for bob_gain, expected in cases:
        action = commitment.action(_decision_game(
            bob_gain, money=money, rnd=rnd, delta=delta,
            messages_allowed=messages_allowed))
        assert action is not None
        assert action["decision"] == expected


def test_message_claim_is_derived_from_same_floor_and_wire_values(monkeypatch):
    monkeypatch.setenv(commitment.D095_MSG_FLAG, "1")
    game = _offer_game(money=100.0, rnd=2, messages_allowed=True)
    action = commitment.action(game)
    assert action is not None
    floor = (100.0 - 0.01) * 0.95 ** 11
    next_required = floor / 0.95 ** 2
    next_alice_max = 100.0 - next_required
    alice_now = action["alice_gain"]
    assert alice_now - next_alice_max == pytest.approx(0.01, abs=1e-12)

    message = action["message"]
    assert f"${alice_now:,.6f}".rstrip("0").rstrip(".") in message
    assert f"${next_required:,.6f}".rstrip("0").rstrip(".") in message
    assert f"${next_alice_max:,.6f}".rstrip("0").rstrip(".") in message
    assert "about one nominal cent better" in message
    assert "one round earlier" in message
    assert "at least" not in message.lower()
    assert "at most" not in message.lower()
    assert "rating" not in message.lower()
    assert "guarante" not in message.lower()
    assert "no intervening" not in message.lower()


def test_patient_message_acknowledges_alices_counter_and_silent_modes_stay_silent(
        monkeypatch):
    monkeypatch.setenv(commitment.D100_FLAG, "1")
    msg = commitment.action(_offer_game(delta=1.0, messages_allowed=True))
    assert msg is not None and "You may counter next round" in msg["message"]
    assert "one round later" in msg["message"]

    silent = commitment.action(_offer_game(delta=1.0, messages_allowed=False))
    assert silent is not None and "message" not in silent


def test_only_an_exact_owned_offer_bypasses_generic_integer_coercion(monkeypatch):
    game = _offer_game(money=100.0, rnd=12)
    candidate = {"alice_gain": 0.01, "bob_gain": 99.99}

    # The generic policy remains whole-dollar on an integer pot.
    off = coerce(candidate, game)
    assert off == {"alice_gain": 0.0, "bob_gain": 100.0}

    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    assert coerce(candidate, game) == candidate

    # A one-cent perturbation no longer exactly matches the independently
    # recomputed component offer, so it follows the unchanged generic path.
    nonmatch = {"alice_gain": 0.02, "bob_gain": 99.98}
    assert commitment.exact_owned_offer(game, nonmatch) is None
    assert coerce(nonmatch, game) == {"alice_gain": 0.0, "bob_gain": 100.0}


def test_commitment_precedes_generic_opponent_floor_and_traces_gate(monkeypatch):
    monkeypatch.setenv(commitment.D095_MSG_FLAG, "1")
    monkeypatch.setenv("GLEE_BARG_OPPONENT_FLOOR", "0.50")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    game = _offer_game(money=100.0, rnd=10, messages_allowed=True)
    action, plan = _wire(game)
    expected = ((100.0 - 0.01) * 0.95 ** 11) / 0.95 ** 10 - 0.01
    assert action["bob_gain"] == expected
    assert action["bob_gain"] > 50.0
    assert plan["gates_fired"] == [commitment.D095_MSG_GATE]


@pytest.mark.parametrize(
    "flag,game",
    [
        (commitment.D095_SILENT_FLAG, _offer_game()),
        (commitment.D095_MSG_FLAG, _offer_game(messages_allowed=True)),
        (commitment.D100_FLAG, _offer_game(delta=1.0)),
    ],
)
def test_each_public_gate_name_is_emitted_when_tracing(
        monkeypatch, flag, game):
    monkeypatch.setenv(flag, "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    action = commitment.action(game)
    assert action is not None
    assert action["_plan"]["gates_fired"] == [commitment.GATE_BY_FLAG[flag]]


@pytest.mark.parametrize(
    "flag,game",
    [
        (commitment.D095_SILENT_FLAG, _offer_game()),
        (commitment.D095_MSG_FLAG, _offer_game(messages_allowed=True)),
        (commitment.D100_FLAG, _offer_game(delta=1.0)),
    ],
)
def test_reachability_registry_uses_the_exact_component_scope(flag, game):
    family, gates, predicate = check_reachability.KNOWN[flag]
    assert family == "bargaining"
    assert gates == (commitment.GATE_BY_FLAG[flag],)
    assert predicate(game, {})


def _engine(*, delta_2: float, messages_allowed: bool) -> BargainingEngine:
    return BargainingEngine(SimConfig("bargaining", {
        "money_to_divide": 100.0,
        "delta_1": 0.8,
        "delta_2": delta_2,
        "max_rounds": 12,
        "messages_allowed": messages_allowed,
        "complete_information": True,
    }), random.Random(7), f"commitment-sim-{delta_2}-{messages_allowed}")


def test_silent_ladder_runs_through_real_simulator_to_terminal_floor(monkeypatch):
    monkeypatch.setenv(commitment.D095_SILENT_FLAG, "1")
    engine = _engine(delta_2=0.95, messages_allowed=False)
    strategy = make_strategy(Config(llm_mode="off"))
    seen = []

    while not engine.done:
        game = engine.observation(engine.current_player)
        state = game["game_state"]
        if engine.current_player == "player_1":
            if state["phase"] == "offer":
                floor = (100.0 - 0.01) * 0.95 ** 11
                required = floor / 0.95 ** (state["round"] - 1)
                bob = math.nextafter(required, -math.inf)
                move = {"alice_gain": 100.0 - bob, "bob_gain": bob}
            else:
                move = {"decision": ("accept" if state["round"] == 12
                                      else "reject")}
        else:
            move = strategy(game)
            if state["phase"] == "offer":
                seen.append((state["round"], move["bob_gain"]))
        result = engine.submit(engine.current_player, move)
        assert result.valid

    assert [rnd for rnd, _ in seen] == [2, 4, 6, 8, 10, 12]
    assert seen[-1][1] == 99.99
    assert engine.result.outcome == "agreement"
    assert engine.result.payoff("player_2") == pytest.approx(
        99.99 * 0.95 ** 11, abs=1e-9)


def test_patient_policy_runs_through_real_simulator_and_closes(monkeypatch):
    monkeypatch.setenv(commitment.D100_FLAG, "1")
    engine = _engine(delta_2=1.0, messages_allowed=True)
    strategy = make_strategy(Config(llm_mode="off"))

    # Alice offers one cent below Bob's exact floor, so Bob rejects.
    assert engine.submit("player_1", {
        "alice_gain": 0.02,
        "bob_gain": 99.98,
        "message": "Your move.",
    }).valid
    decision = strategy(engine.observation("player_2"))
    assert decision == {"decision": "reject"}
    assert engine.submit("player_2", decision).valid

    offer = strategy(engine.observation("player_2"))
    assert offer["alice_gain"] == 0.01 and offer["bob_gain"] == 99.99
    assert "You may counter next round" in offer["message"]
    assert engine.submit("player_2", offer).valid
    assert engine.submit("player_1", {"decision": "accept"}).valid
    assert engine.result.payoff("player_2") == 99.99
