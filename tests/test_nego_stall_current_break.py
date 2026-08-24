"""Triggered A/B for a current concession hidden by stale stall history."""

from __future__ import annotations

import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N
from scripts import check_reachability, live_percentile


FLAG = "GLEE_NEGO_STALL_CURRENT_BREAK_AB"


def _gid(treatment: bool) -> str:
    for index in range(20_000):
        gid = f"stall-current-break-{index}"
        if N.stall_current_break_assignment(gid) is treatment:
            return gid
    raise AssertionError(f"no game id for treatment={treatment}")


def _state(*, role="seller", old=0.0, current=440_779.69,
           own_value=800_000.0):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    history = [
        {
            "round": index + 1,
            "offer": {"from_player": other, "price": old},
            "decision": "RejectOffer",
            "decided_by": me,
            "counteroffer": {"from_player": me, "price": own_value * 1.6},
        }
        for index in range(3)
    ]
    return {
        "round": 8,
        "max_rounds": None,
        "horizon_known": False,
        "complete_information": False,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "history": history,
        "last_offer": {
            "from_player": other,
            "price": current,
            "round": 8,
        },
        "messages_allowed": False,
    }


def _game(*, gid=None, **state_kwargs):
    state = _state(**state_kwargs)
    return {
        "game_id": _gid(True) if gid is None else gid,
        "game_family": "negotiation",
        "your_player": state["current_player"],
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _wire(game):
    action = N.decide(game, Config.from_env())
    return {key: value for key, value in action.items() if key != "_plan"}


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


def _arm(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_STALL_POLICY", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    # Freeze the deployed negotiation anchors whose scheduled target the
    # treatment restores; changing either closes the prospective cohort.
    monkeypatch.setenv("GLEE_NEGO_SELLER_ANCHOR", "4.0")
    monkeypatch.setenv("GLEE_NEGO_BUYER_ANCHOR", "0.15")
    monkeypatch.setenv("GLEE_NEGO_BOUND_AS_FLOOR", "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    monkeypatch.setenv(FLAG, "1")


def test_assignment_is_stable_balanced_and_requires_an_id():
    bits = [N.stall_current_break_assignment(f"balance-{index}")
            for index in range(6000)]
    assert 0.47 < sum(bits) / len(bits) < 0.53
    assert all(N.stall_current_break_assignment(f"same-{index}")
               == N.stall_current_break_assignment(f"same-{index}")
               for index in range(500))
    assert N.stall_current_break_assignment("") is None
    assert N.stall_current_break_assignment(None) is None
    for index in range(500):
        gid = f"reader-parity-{index}"
        expected = ("candidate" if N.stall_current_break_assignment(gid)
                    else "control")
        assert live_percentile.stall_current_break_arm(gid) == expected


@pytest.mark.parametrize(
    ("role", "old", "current", "own_value"),
    [
        ("seller", 0.0, 440_779.69, 800_000.0),
        ("buyer", 1_500_000.0, 1_300_000.0, 1_200_000.0),
    ],
)
def test_directional_current_concession_breaks_the_stale_signal(
        role, old, current, own_value):
    state = _state(role=role, old=old, current=current, own_value=own_value)
    stale = N._their_stall_price(state, state["current_player"])
    assert stale == old
    assert N._current_concession_break(
        state, state["current_player"], stale) == current


@pytest.mark.parametrize(
    ("role", "old", "current", "own_value"),
    [
        ("seller", 100.0, 101.0, 80.0),   # exactly 1% is not a break
        ("seller", 100.0, 90.0, 80.0),    # concession away from us
        ("buyer", 100.0, 99.0, 120.0),    # exactly 1% is not a break
        ("buyer", 100.0, 110.0, 120.0),   # concession away from us
    ],
)
def test_small_or_wrong_direction_moves_do_not_break(
        role, old, current, own_value):
    state = _state(role=role, old=old, current=current, own_value=own_value)
    assert N._current_concession_break(
        state, state["current_player"], old) is None


def test_default_off_and_hash_control_preserve_the_wire(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_STALL_POLICY", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    candidate_game = _game(gid=_gid(True))
    baseline = _wire(candidate_game)

    monkeypatch.setenv(FLAG, "1")
    control_game = _game(gid=_gid(False))
    control_flag_off = _wire(control_game)
    monkeypatch.delenv(FLAG)
    assert _wire(control_game) == control_flag_off
    assert baseline["decision"] == "RejectOffer"


@pytest.mark.parametrize(
    ("role", "old", "current", "own_value", "direction"),
    [
        ("seller", 0.0, 440_779.69, 800_000.0, 1),
        ("buyer", 1_500_000.0, 1_300_000.0, 1_200_000.0, -1),
    ],
)
def test_candidate_suppresses_only_the_stale_park(
        monkeypatch, role, old, current, own_value, direction):
    _arm(monkeypatch)
    control = _game(gid=_gid(False), role=role, old=old, current=current,
                    own_value=own_value)
    candidate = _game(gid=_gid(True), role=role, old=old, current=current,
                      own_value=own_value)
    control_action = N.decide(control, Config.from_env())
    candidate_action = N.decide(candidate, Config.from_env())

    assert control_action["decision"] == candidate_action["decision"] \
        == "RejectOffer"
    assert direction * candidate_action["product_price"] \
        > direction * control_action["product_price"]
    cplan = candidate_action["_plan"]
    assert cplan["stall_current_break"]["arm"] == "candidate"
    assert "stall_current_break" in cplan["gates_fired"]
    assert "stall_park" not in cplan["gates_fired"]
    assert control_action["_plan"]["stall_current_break"]["arm"] == "control"


def test_profitable_current_offer_keeps_the_same_accept_decision(monkeypatch):
    _arm(monkeypatch)
    control = _game(gid=_gid(False), old=850_000.0, current=900_000.0)
    candidate = _game(gid=_gid(True), old=850_000.0, current=900_000.0)
    assert _wire(control) == {"decision": "AcceptOffer"}
    assert _wire(candidate) == {"decision": "AcceptOffer"}


@pytest.mark.parametrize("conflict", [
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
    "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HIDDEN_FLOOR",
    "GLEE_NEGO_FIRST_PRINCIPLES",
    "GLEE_NEGO_FP_ALWAYS",
])
def test_conflicting_price_experiments_fail_closed(monkeypatch, conflict):
    monkeypatch.setenv("GLEE_NEGO_STALL_POLICY", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    game = _game(gid=_gid(True))
    baseline = _wire(game)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(conflict, "1")
    assert _wire(game) == baseline


def test_legacy_accept_stack_fails_closed(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_STALL_POLICY", "1")
    game = _game(gid=_gid(True))
    baseline = _wire(game)
    monkeypatch.setenv(FLAG, "1")
    assert _wire(game) == baseline


def test_historical_helper_remains_the_deadgame_and_acceptance_definition():
    state = _state(old=0.0, current=440_779.69)
    me = state["current_player"]
    assert N._their_stall_price(state, me) == 0.0
    assert N._current_concession_break(state, me, 0.0) == 440_779.69
    # The experiment does not mutate the state or globally replace the helper.
    assert N._their_stall_price(state, me) == 0.0


@pytest.mark.parametrize(
    ("role", "candidate", "control", "expected"),
    [
        ("seller", 101.0, 100.0, True),
        ("seller", 99.0, 100.0, False),
        ("buyer", 99.0, 100.0, True),
        ("buyer", 101.0, 100.0, False),
    ],
)
def test_target_direction_guard(role, candidate, control, expected):
    state = _state(role=role)
    me = state["current_player"]
    assert N._target_improves_for_role(
        state, me, candidate, control) is expected


def test_wrong_direction_schedule_is_not_assigned(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.setattr(N.pricing, "stall_park",
                        lambda _value, _seller: 10_000_000.0)
    game = _game(gid=_gid(True))
    action = N.decide(game, Config.from_env())
    metadata = action["_plan"]["stall_current_break"]
    assert metadata["eligible"] is False
    assert "arm" not in metadata
    assert "stall_current_break" not in action["_plan"]["gates_fired"]


def test_reachability_scope_matches_the_production_trigger(monkeypatch):
    predicate = check_reachability.KNOWN[FLAG][2]
    eligible = _game()
    _arm(monkeypatch)
    plan = N.decide(eligible, Config.from_env())["_plan"]
    assert predicate(eligible, plan) is True
    no_break = _game(current=0.0)
    assert predicate(no_break, {}) is False
    wrong_phase = _game()
    wrong_phase["valid_actions"] = {"type": "offer"}
    assert predicate(wrong_phase, {}) is False


def test_reader_cohorts_before_action_and_verifies_plan(monkeypatch):
    _arm(monkeypatch)
    game = _game(gid=_gid(True))
    action = N.decide(game, Config.from_env())
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
    exposure = live_percentile._stall_current_break_exposure_turn(
        "conceder", record)
    assert exposure[0] == ("conceder", game["game_id"])
    assert exposure[1] == 1234.0
    signal = exposure[2]
    assert signal["plan_arm"] == "candidate"
    assert signal["mechanism_ok"] is True
    assert signal["writer_changed"] is True
    assert signal["stale_price"] == 0.0
    assert signal["current_price"] == 440_779.69


def test_report_blocks_without_complete_official_join(capsys):
    control_gid, candidate_gid = _gid(False), _gid(True)
    diagnostic = {
        "role": "seller", "complete": False, "horizon": "inf",
        "scale": 1_000_000.0, "messages": False,
        "mechanism_ok": True, "writer_changed": True,
        "wire_price": 1_400_000.0,
    }
    rows = [
        ("conceder", 0.5, control_gid, True, diagnostic, "terminal"),
        ("conceder", 0.6, candidate_gid, True, diagnostic, "terminal"),
    ]
    assert live_percentile.report_stall_current_break(
        rows, 1.0, since=1000.0, until=2000.0) == 1
    output = capsys.readouterr().out
    assert "local pooled-CDF percentile is diagnostic only" in output
    assert "terminal outcomes missing official delta=2" in output
