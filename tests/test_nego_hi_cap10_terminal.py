"""Narrow hidden cap-10 buyer terminal-counter experiment."""

from __future__ import annotations

import os
import random

import pytest

from glee_agent import actions, runtime_flags
from glee_agent.actions import coerce
from scripts import check_reachability, live_percentile
from sim.negotiation import NegotiationEngine
from sim.types import Config as SimConfig

FLAG = "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB"


def _gid(treatment: bool) -> str:
    for index in range(10_000):
        gid = f"hi-cap10-buyer12-{index}"
        if actions.hi_cap10_buyer12_terminal_arm(gid) is treatment:
            return gid
    raise AssertionError("no game id for requested arm")


def _game(*, gid=None, own_value=120.0, complete=False, known=True,
          max_rounds=10, rnd=9, role="buyer", action_type="decision"):
    me = "player_2" if role == "buyer" else "player_1"
    other = "player_1" if me == "player_2" else "player_2"
    state = {
        "round": rnd,
        "horizon_known": known,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "last_offer": {"from_player": other, "price": 140.0, "round": rnd},
        "history": [],
        "messages_allowed": False,
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if complete:
        state[f"{other}_value"] = 80.0 if role == "buyer" else 150.0
    return {
        "game_id": _gid(True) if gid is None else gid,
        "game_family": "negotiation",
        "your_player": me,
        "phase": action_type,
        "game_state": state,
        "valid_actions": {"type": action_type},
    }


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_"):
            monkeypatch.delenv(name, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def test_assignment_is_stable_balanced_and_requires_an_id():
    assigned = [actions.hi_cap10_buyer12_terminal_arm(f"balance-{i}")
                for i in range(4000)]
    assert 0.45 < sum(assigned) / len(assigned) < 0.55
    assert actions.hi_cap10_buyer12_terminal_arm("same") == \
        actions.hi_cap10_buyer12_terminal_arm("same")
    assert actions.hi_cap10_buyer12_terminal_arm("") is None


def test_analyzer_assignment_is_the_production_assignment():
    for index in range(500):
        gid = f"reader-parity-{index}"
        expected = ("candidate" if actions.hi_cap10_buyer12_terminal_arm(gid)
                    else "control")
        assert live_percentile.hi_terminal_arm(gid) == expected


def test_default_off_and_hash_control_are_byte_identical(monkeypatch):
    raw = {"decision": "RejectOffer", "product_price": 98.75}
    assert coerce(dict(raw), _game()) == raw

    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), _game(gid=_gid(False))) == raw


@pytest.mark.parametrize("base", [100.0, 10_000.0, 1_000_000.0])
def test_treatment_posts_base_plus_one_cent_at_every_scale(monkeypatch, base):
    monkeypatch.setenv(FLAG, "1")
    action = coerce(
        {"decision": "RejectOffer", "product_price": base * 0.989676},
        _game(own_value=1.2 * base),
    )
    assert action == {
        "decision": "RejectOffer",
        "product_price": pytest.approx(base + 0.01),
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"complete": True},
        {"known": False, "max_rounds": None},
        {"max_rounds": 1},
        {"rnd": 8},
        {"role": "seller"},
        {"own_value": 100.0},
        {"own_value": 123.0},
        {"gid": ""},
    ],
)
def test_ineligible_states_do_not_move(monkeypatch, changes):
    raw = {"decision": "RejectOffer", "product_price": 98.75}
    game = _game(**changes)
    baseline = coerce(dict(raw), game)
    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), game) == baseline


def test_offer_phase_is_outside_the_arm(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    game = _game(action_type="offer")
    raw = {"decision": "RejectOffer", "product_price": 98.75}
    assert actions._hi_cap10_buyer12_terminal_context(raw, game) is None


@pytest.mark.parametrize("decision", ["AcceptOffer", "WalkAway"])
def test_accept_and_walk_decisions_never_change(monkeypatch, decision):
    monkeypatch.setenv(FLAG, "1")
    assert coerce({"decision": decision}, _game()) == {"decision": decision}


def test_treatment_is_the_final_writer_against_hostile_hidden_guards(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")
    action = coerce(
        {"decision": "RejectOffer", "product_price": 20.0}, _game())
    assert action["product_price"] == pytest.approx(100.01)


class _HiddenState(dict):
    def get(self, key, default=None):
        if key == "player_1_value":
            raise AssertionError("read hidden seller value")
        return super().get(key, default)


def test_treatment_never_reads_the_hidden_seller_value(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    game = _game()
    state = _HiddenState(game["game_state"])
    dict.__setitem__(state, "player_1_value", 100.0)
    game["game_state"] = state
    assert coerce(
        {"decision": "RejectOffer", "product_price": 98.0}, game
    )["product_price"] == pytest.approx(100.01)


def test_reachability_registry_matches_the_runtime_scope():
    predicate = check_reachability.KNOWN[FLAG][2]
    eligible = _game()
    assert FLAG in check_reachability.POSTCONDITION_FLAGS
    assert predicate(eligible, {}) is True
    assert predicate(_game(rnd=8), {}) is False
    assert predicate(_game(own_value=100.0), {}) is False


def test_itt_cohort_starts_before_terminal_reach_or_action(monkeypatch):
    game = _game(rnd=1)
    record = {
        "ts": 1234.0,
        "game_id": game["game_id"],
        "game_family": "negotiation",
        "your_player": "player_2",
        "action_type": "decision",
        "state": game["game_state"],
        "action": {"decision": "AcceptOffer"},
    }
    exposure = live_percentile._hi_terminal_exposure_turn("champion", record)
    assert exposure[0] == ("champion", game["game_id"])
    assert exposure[1] == 1234.0


def test_outcome_reader_audits_the_literal_terminal_wire(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.61)
    gid = _gid(True)
    state = _game(gid=gid)["game_state"]
    state["history"] = [{
        "round": 9,
        "decision": "RejectOffer",
        "decided_by": "player_2",
        "counteroffer": 100.01,
    }]
    final = {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "status": "no_deal",
        "game_state": state,
        "result": {"outcome": "no_deal", "player_1_payoff": 0.0,
                   "player_2_payoff": 0.0},
    }
    row = live_percentile._hi_terminal_row(
        "champion", {"game_id": gid}, final)
    assert row[:4] == ("champion", 0.61, gid, False)
    assert row[4]["reached_terminal_counter"] is True
    assert row[4]["wire_price"] == pytest.approx(100.01)


def test_report_labels_local_cdf_and_checks_wire(capsys):
    control, candidate = _gid(False), _gid(True)
    base = {"base": 100.0, "expected_wire_price": 100.01,
            "fleet_slots": ("champion",)}
    rows = [
        ("champion", 0.4, control, False,
         {**base, "reached_terminal_counter": True, "wire_price": 98.9}),
        ("champion", 0.7, candidate, True,
         {**base, "reached_terminal_counter": True, "wire_price": 100.01}),
    ]
    assert live_percentile.report_hi_terminal(rows, 24.0) == 0
    output = capsys.readouterr().out
    assert "not the official full-configuration score" in output
    assert "intent-to-treat" in output
    assert "all exactly base+$0.01" in output


def test_round9_counter_is_the_round10_standing_offer(monkeypatch):
    gid = _gid(True)
    engine = NegotiationEngine(
        SimConfig("negotiation", {
            "player_1_value": 100.0,
            "player_2_value": 120.0,
            "max_rounds": 10,
            "horizon_known": True,
            "complete_information": False,
            "messages_allowed": False,
        }),
        random.Random(0),
        gid,
    )
    assert engine.submit("player_1", {"product_price": 150.0}).valid
    for rnd in range(1, 9):
        player = engine.current_player
        counter = 95.0 if player == "player_2" else 145.0
        assert engine.submit(player, {
            "decision": "RejectOffer", "product_price": counter,
        }).valid, rnd

    game = engine.observation("player_2")
    assert game["game_state"]["round"] == 9
    monkeypatch.setenv(FLAG, "1")
    wire = coerce(
        {"decision": "RejectOffer", "product_price": 98.5}, game)
    assert engine.submit("player_2", wire).valid

    round10 = engine.observation("player_1")["game_state"]
    assert round10["round"] == 10
    assert round10["last_offer"]["price"] == pytest.approx(100.01)
