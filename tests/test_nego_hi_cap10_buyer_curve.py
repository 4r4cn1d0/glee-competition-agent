"""Broad direct-leader hidden cap-10 buyer trajectory experiment."""

from __future__ import annotations

import os

import pytest

from glee_agent import actions, runtime_flags
from glee_agent.actions import coerce
from scripts import check_reachability, live_percentile

FLAG = "GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB"


def _gid(treatment: bool) -> str:
    for index in range(10_000):
        gid = f"hi-cap10-buyer-curve-{index}"
        if actions.hi_cap10_buyer_curve_arm(gid) is treatment:
            return gid
    raise AssertionError("no game id for requested arm")


def _game(*, gid=None, own_value=120.0, complete=False, known=True,
          max_rounds=10, index=0, role="buyer", action_type="decision"):
    me = "player_2" if role == "buyer" else "player_1"
    other = "player_1" if me == "player_2" else "player_2"
    history = [
        {
            "round": 1 + 2 * prior,
            "counteroffer": {
                "from_player": me,
                "price": own_value * 0.5,
            },
        }
        for prior in range(index)
    ]
    state = {
        "round": 1 + 2 * index,
        "horizon_known": known,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "last_offer": {
            "from_player": other,
            "price": own_value * 0.95,
            "round": 1 + 2 * index,
        },
        "history": history,
        "messages_allowed": False,
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if complete:
        state[f"{other}_value"] = own_value * 0.8
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
    assigned = [actions.hi_cap10_buyer_curve_arm(f"balance-{i}")
                for i in range(4000)]
    assert 0.45 < sum(assigned) / len(assigned) < 0.55
    assert actions.hi_cap10_buyer_curve_arm("same") == \
        actions.hi_cap10_buyer_curve_arm("same")
    assert actions.hi_cap10_buyer_curve_arm("") is None


def test_analyzer_assignment_is_the_production_assignment():
    for index in range(500):
        gid = f"reader-parity-{index}"
        expected = ("candidate" if actions.hi_cap10_buyer_curve_arm(gid)
                    else "control")
        assert live_percentile.hi_buyer_curve_arm(gid) == expected


def test_default_off_and_hash_control_are_byte_identical(monkeypatch):
    raw = {"decision": "RejectOffer", "product_price": 91.23}
    assert coerce(dict(raw), _game()) == raw

    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), _game(gid=_gid(False))) == raw


@pytest.mark.parametrize("base", [100.0, 10_000.0, 1_000_000.0])
@pytest.mark.parametrize("own_mult", [1.0, 1.2, 1.5])
def test_treatment_copies_the_value_scaled_clod_curve(monkeypatch, base,
                                                       own_mult):
    monkeypatch.setenv(FLAG, "1")
    own_value = own_mult * base
    for index, fraction in enumerate(actions._HI_CAP10_BUYER_CURVE):
        out = coerce(
            {"decision": "RejectOffer", "product_price": own_value * 0.99},
            _game(own_value=own_value, index=index),
        )
        assert out == {
            "decision": "RejectOffer",
            "product_price": pytest.approx(round(own_value * fraction, 2)),
        }


def test_terminal_counter_is_byte_identical_in_both_arms(monkeypatch):
    game = _game(own_value=120.0, index=4)
    raw = {"decision": "RejectOffer", "product_price": 98.9676}
    baseline = coerce(dict(raw), game)
    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), game) == baseline


@pytest.mark.parametrize(
    "changes",
    [
        {"complete": True},
        {"known": False, "max_rounds": None},
        {"max_rounds": 1},
        {"role": "seller"},
        {"own_value": 80.0},
        {"own_value": 123.0},
        {"gid": ""},
        {"action_type": "offer"},
    ],
)
def test_ineligible_states_do_not_move(monkeypatch, changes):
    raw = {"decision": "RejectOffer", "product_price": 91.23}
    game = _game(**changes)
    baseline = coerce(dict(raw), game)
    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), game) == baseline


@pytest.mark.parametrize("decision", ["AcceptOffer", "WalkAway"])
def test_accept_and_walk_decisions_never_change(monkeypatch, decision):
    monkeypatch.setenv(FLAG, "1")
    assert coerce({"decision": decision}, _game()) == {"decision": decision}


@pytest.mark.parametrize(
    ("overlap", "value"),
    [
        ("GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB", "1"),
        ("GLEE_NEGO_HIDDEN_POLICY_V1", "1"),
        ("GLEE_NEGO_HIDDEN_FLOOR", "1.15"),
        ("GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB", "1"),
        ("GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB", "1"),
        ("GLEE_NEGO_STALL_CURRENT_BREAK_AB", "1"),
        ("GLEE_NEGO_CLOSE_AB", "1"),
        ("GLEE_NEGO_PROBE_V1", "1"),
    ],
)
def test_overlapping_experiments_make_the_curve_inert(monkeypatch, overlap,
                                                        value):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(overlap, value)
    assert actions._hi_cap10_buyer_curve_context(_game()) is None


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
    out = coerce(
        {"decision": "RejectOffer", "product_price": 98.0}, game)
    assert out["product_price"] == pytest.approx(
        round(120.0 * actions._HI_CAP10_BUYER_CURVE[0], 2))


def test_reachability_registry_matches_the_runtime_scope():
    predicate = check_reachability.KNOWN[FLAG][2]
    assert FLAG in check_reachability.POSTCONDITION_FLAGS
    assert predicate(_game(), {}) is True
    assert predicate(_game(own_value=80.0), {}) is False
    assert predicate(_game(known=False, max_rounds=None), {}) is False
    assert predicate(_game(role="seller"), {}) is False


def test_itt_cohort_starts_before_action_and_keeps_immediate_accepts():
    game = _game(gid=_gid(True))
    record = {
        "ts": 1234.0,
        "game_id": game["game_id"],
        "game_family": "negotiation",
        "your_player": "player_2",
        "action_type": "decision",
        "state": game["game_state"],
        "action": {"decision": "AcceptOffer"},
    }
    exposure = live_percentile._hi_buyer_curve_exposure_turn(
        "champion", record)
    assert exposure[0] == ("champion", game["game_id"])
    assert exposure[1] == 1234.0
    assert exposure[2]["first_decision"] == "AcceptOffer"


def test_outcome_reader_audits_every_candidate_counter(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.61)
    gid = _gid(True)
    state = _game(gid=gid)["game_state"]
    expected = [round(120.0 * fraction, 2)
                for fraction in actions._HI_CAP10_BUYER_CURVE[:3]]
    state["history"] = [
        {
            "round": 1 + 2 * index,
            "decision": "RejectOffer",
            "decided_by": "player_2",
            "counteroffer": price,
        }
        for index, price in enumerate(expected)
    ]
    final = {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "status": "no_deal",
        "game_state": state,
        "result": {"outcome": "no_deal", "player_1_payoff": 0.0,
                   "player_2_payoff": 0.0},
    }
    row = live_percentile._hi_buyer_curve_row(
        "champion", {"game_id": gid}, final)
    assert row[:4] == ("champion", 0.61, gid, False)
    assert row[4]["wire_prices"] == expected
    assert row[4]["wire_ok"] is True


def test_report_labels_itt_and_checks_the_whole_curve(capsys):
    control, candidate = _gid(False), _gid(True)
    base = {"base": 100.0, "own_mult": 1.2,
            "messages_allowed": False, "fleet_slots": ("champion",)}
    rows = [
        ("champion", 0.4, control, False,
         {**base, "wire_ok": True, "curve_counters": 3}),
        ("champion", 0.7, candidate, True,
         {**base, "wire_ok": True, "curve_counters": 4}),
    ]
    assert live_percentile.report_hi_buyer_curve(rows, 24.0) == 1
    output = capsys.readouterr().out
    assert "intent-to-treat" in output
    assert "all on the frozen four-point" in output
    assert "terminal outcomes missing official delta=2" in output


def test_report_rejects_a_malformed_candidate_curve(capsys):
    control, candidate = _gid(False), _gid(True)
    base = {"base": 100.0, "own_mult": 1.2,
            "messages_allowed": False, "fleet_slots": ("champion",)}
    rows = [
        ("champion", 0.4, control, False,
         {**base, "wire_ok": True, "curve_counters": 1}),
        ("champion", 0.7, candidate, True,
         {**base, "wire_ok": False, "curve_counters": 1,
          "curve_wire_prices": [81.0], "expected_wire_prices": [81.44]}),
    ]
    assert live_percentile.report_hi_buyer_curve(rows, 24.0) == 2
    assert "MECHANISM REJECTION" in capsys.readouterr().out


def test_bargaining_wire_is_independent_of_the_negotiation_flag(monkeypatch):
    game = {
        "game_id": "bargaining-isolation",
        "game_family": "bargaining",
        "your_player": "player_1",
        "game_state": {"money_to_divide": 100.0},
        "valid_actions": {"type": "offer"},
    }
    raw = {"alice_gain": 60.0, "bob_gain": 40.0}
    baseline = coerce(dict(raw), game)
    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), game) == baseline
