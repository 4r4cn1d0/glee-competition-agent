"""Randomized precedence test between TABLE and observed continuation value."""

from __future__ import annotations

import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N
from scripts import live_percentile


FLAG = "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB"


def _gid(treatment: bool) -> str:
    for index in range(20_000):
        gid = f"table-vcont-{index}"
        if N.table_vcont_precedence_assignment(gid) is treatment:
            return gid
    raise AssertionError(f"no game id for treatment={treatment}")


def _game(*, gid=None, role="seller", complete=False, rnd=6,
          max_rounds=10, prices=None):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    own_value = 80.0 if role == "seller" else 120.0
    if prices is None:
        # Three distinct concessions create v_cont=27.04 against a current
        # surplus of 20.0 in both seats.  At elapsed=.6 TABLE's thresholds are
        # only 3.446B seller / 7.592B buyer, so control accepts directly.
        prices = [60.0, 80.0, 100.0] if role == "seller" \
            else [140.0, 130.0, 100.0]
    state = {
        "round": rnd,
        "max_rounds": max_rounds,
        "horizon_known": True,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "history": [
            {"round": 1,
             "offer": {"from_player": other, "price": prices[0], "round": 1}},
            {"round": 3,
             "offer": {"from_player": other, "price": prices[1], "round": 3}},
        ],
        "last_offer": {"from_player": other, "price": prices[-1], "round": rnd},
        "messages_allowed": False,
    }
    if complete:
        state[f"{other}_value"] = 150.0 if role == "seller" else 80.0
    return {
        "game_id": _gid(True) if gid is None else gid,
        "game_family": "negotiation",
        "your_player": me,
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_AGENT_SLOT", raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _owners(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_HORIZON_V2", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    monkeypatch.setenv("GLEE_NEGO_TABLE", "1")
    monkeypatch.setenv("GLEE_NEGO_STALL_POLICY", "1")
    monkeypatch.setenv("GLEE_NEGO_FINAL_OPTION", "0.6")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")


def _arm(monkeypatch):
    _owners(monkeypatch)
    monkeypatch.setenv(FLAG, "1")


def _wire(action):
    return {key: value for key, value in action.items() if key != "_plan"}


def _decide(game):
    return N.decide(game, Config.from_env())


def test_assignment_is_stable_balanced_and_requires_an_id():
    bits = [N.table_vcont_precedence_assignment(f"balance-{index}")
            for index in range(6000)]
    assert 0.47 < sum(bits) / len(bits) < 0.53
    assert all(N.table_vcont_precedence_assignment(f"same-{index}")
               == N.table_vcont_precedence_assignment(f"same-{index}")
               for index in range(500))
    assert N.table_vcont_precedence_assignment("") is None
    assert N.table_vcont_precedence_assignment(None) is None
    for index in range(500):
        gid = f"reader-parity-{index}"
        expected = ("candidate" if N.table_vcont_precedence_assignment(gid)
                    else "control")
        assert live_percentile.table_vcont_precedence_arm(gid) == expected


def test_default_off_is_byte_identical_to_the_direct_table_accept(monkeypatch):
    _owners(monkeypatch)
    action = _decide(_game(gid=_gid(True)))
    assert _wire(action) == {"decision": "AcceptOffer"}
    assert "table_vcont_precedence" not in action["_plan"]
    assert "table_accept" in action["_plan"]["gates_fired"]


@pytest.mark.parametrize("role", ["seller", "buyer"])
def test_control_accepts_and_candidate_uses_the_existing_counter(monkeypatch, role):
    _arm(monkeypatch)
    control = _decide(_game(gid=_gid(False), role=role))
    candidate = _decide(_game(gid=_gid(True), role=role))

    assert _wire(control) == {"decision": "AcceptOffer"}
    assert control["_plan"]["table_vcont_precedence"]["arm"] == "control"
    assert "table_accept" in control["_plan"]["gates_fired"]

    assert candidate["decision"] == "RejectOffer"
    meta = candidate["_plan"]["table_vcont_precedence"]
    assert meta["arm"] == "candidate"
    assert meta["distinct_opponent_prices"] == 3
    assert meta["continuation_value"] > meta["surplus_now"]
    assert candidate["product_price"] == meta["counter_price"]
    assert candidate["_plan"]["table_accept_vetoed"] is True
    assert "table_accept_below" not in candidate["_plan"]
    assert "table_vcont_precedence" in candidate["_plan"]["gates_fired"]


def test_candidate_wire_is_exactly_the_existing_non_table_fallthrough(monkeypatch):
    _arm(monkeypatch)
    candidate = _wire(_decide(_game(gid=_gid(True))))

    monkeypatch.setenv(FLAG, "0")
    monkeypatch.setenv("GLEE_NEGO_TABLE", "0")
    baseline = _wire(_decide(_game(gid=_gid(True))))
    assert candidate == baseline


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"complete": True}, "complete information"),
        ({"rnd": 10}, "real final"),
        ({"prices": [80.0, 80.0, 100.0]}, "fewer than three distinct prices"),
        ({"prices": [60.0, 100.0, 100.0]}, "current offer stalls"),
        ({"prices": [120.0, 110.0, 100.0]}, "wrong-direction seller trend"),
    ],
)
def test_nonidentified_or_owned_states_are_identical_between_hash_arms(
        monkeypatch, changes, reason):
    _arm(monkeypatch)
    control = _wire(_decide(_game(gid=_gid(False), **changes)))
    candidate = _wire(_decide(_game(gid=_gid(True), **changes)))
    assert candidate == control, reason


@pytest.mark.parametrize("missing", [
    "GLEE_NEGO_HORIZON_V2",
    "GLEE_NEGO_CONTINUATION_ACCEPT",
    "GLEE_NEGO_TABLE",
    "GLEE_NEGO_STALL_POLICY",
])
def test_missing_stack_owner_fails_closed(monkeypatch, missing):
    _arm(monkeypatch)
    monkeypatch.setenv(missing, "0")
    assert _wire(_decide(_game(gid=_gid(True)))) == \
        _wire(_decide(_game(gid=_gid(False))))


def test_wrong_final_option_value_fails_closed(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_FINAL_OPTION", "0.5")
    assert _wire(_decide(_game(gid=_gid(True)))) == \
        _wire(_decide(_game(gid=_gid(False))))


@pytest.mark.parametrize("conflict", [
    "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB",
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
    "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HIDDEN_FLOOR",
    "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
    "GLEE_NEGO_FIRST_PRINCIPLES",
    "GLEE_NEGO_FP_ALWAYS",
    "GLEE_NEGO_RANK_PRICE_AB",
    "GLEE_NEGO_CLOSE_AB",
    "GLEE_NEGO_UNCAPPED_AB",
    "GLEE_NEGO_SURPLUS_PROBE",
])
def test_overlapping_experiments_fail_closed(monkeypatch, conflict):
    _arm(monkeypatch)
    monkeypatch.setenv(conflict, "1")
    assert _wire(_decide(_game(gid=_gid(True)))) == \
        _wire(_decide(_game(gid=_gid(False))))


def test_hidden_min_share_arm_also_refuses_the_new_overlap(monkeypatch):
    _owners(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB", "1")
    monkeypatch.setenv(FLAG, "1")
    low_offer = _game(gid=_gid(True), prices=[60.0, 70.0, 85.0])
    # Both experiments fail closed instead of assigning the same game twice.
    action = _decide(low_offer)
    assert action["decision"] == "AcceptOffer"
    assert "hidden_min_share_veto" not in action["_plan"]
    assert "table_vcont_precedence" not in action["_plan"]


@pytest.mark.parametrize("treatment", [False, True])
def test_reader_cohorts_first_direct_table_accept_and_audits_wire(
        monkeypatch, treatment):
    _arm(monkeypatch)
    game = _game(gid=_gid(treatment))
    action = _decide(game)
    plan = action.pop("_plan")
    record = {
        "ts": 1234.0,
        "game_id": game["game_id"],
        "game_family": "negotiation",
        "your_player": game["your_player"],
        "action_type": "decision",
        "state": game["game_state"],
        "action": action,
        "plan": plan,
    }
    exposure = live_percentile._table_vcont_precedence_exposure_turn(
        "conceder", record)
    assert exposure[0] == ("conceder", game["game_id"])
    assert exposure[1] == 1234.0
    diagnostic = exposure[2]
    assert diagnostic["plan_arm"] == ("candidate" if treatment else "control")
    assert diagnostic["mechanism_ok"] is True
    assert diagnostic["distinct_opponent_prices"] == 3
    assert diagnostic["continuation_value"] > diagnostic["surplus_now"]
    assert diagnostic["action_decision"] == (
        "RejectOffer" if treatment else "AcceptOffer")


def test_reader_rejects_a_malformed_candidate_counter(monkeypatch):
    _arm(monkeypatch)
    game = _game(gid=_gid(True))
    action = _decide(game)
    plan = action.pop("_plan")
    action["product_price"] += 1.0
    record = {
        "ts": 1234.0,
        "game_id": game["game_id"],
        "game_family": "negotiation",
        "your_player": game["your_player"],
        "action_type": "decision",
        "state": game["game_state"],
        "action": action,
        "plan": plan,
    }
    exposure = live_percentile._table_vcont_precedence_exposure_turn(
        "conceder", record)
    assert exposure[2]["mechanism_ok"] is False


def test_report_blocks_without_complete_official_join(capsys):
    diagnostic = {
        "role": "seller", "horizon": "10", "own_multiplier": 0.8,
        "scale": 100.0, "messages": False, "mechanism_ok": True,
        "action_decision": "AcceptOffer",
    }
    rows = [
        ("conceder", 0.45, _gid(False), True, diagnostic, "terminal"),
        ("conceder", 0.60, _gid(True), False, diagnostic, "terminal"),
    ]
    assert live_percentile.report_table_vcont_precedence(
        rows, 1.0, since=1000.0, until=2000.0) == 1
    output = capsys.readouterr().out
    assert "local pooled-CDF percentile is diagnostic only" in output
    assert "terminal outcomes missing official delta=2" in output
    assert "every agreement/no-deal/walk/pending" in output
