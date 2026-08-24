"""Support-aware randomized veto for hidden low-share acceptances."""

from __future__ import annotations

import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N
from scripts import check_reachability, live_percentile


FLAG = "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB"


def _gid(treatment: bool) -> str:
    for index in range(20_000):
        gid = f"hidden-min-share-{index}"
        if N.hidden_min_share_veto_assignment(gid) is treatment:
            return gid
    raise AssertionError(f"no game id for treatment={treatment}")


def _game(*, gid=None, role="seller", own_value=None, offer=None, rnd=4,
          max_rounds=10, complete=False):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    if own_value is None:
        own_value = 80.0 if role == "seller" else 120.0
    if offer is None:
        offer = own_value + 2.0 if role == "seller" else own_value - 2.0
    state = {
        "round": rnd,
        "max_rounds": max_rounds,
        "horizon_known": True,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        # Two identical prior offers make the current continuation estimate the
        # standing surplus times survival.  Thus the deployed control accepts
        # this profitable offer, giving the veto a real decision to isolate.
        "history": [
            {"round": 1,
             "offer": {"from_player": other, "price": offer, "round": 1}},
            {"round": 3,
             "offer": {"from_player": other, "price": offer, "round": 3}},
        ],
        "last_offer": {"from_player": other, "price": offer, "round": rnd},
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


def _arm(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_HORIZON_V2", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    monkeypatch.setenv("GLEE_NEGO_TABLE", "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    monkeypatch.setenv(FLAG, "1")


def _wire(game):
    action = N.decide(game, Config.from_env())
    return {key: value for key, value in action.items() if key != "_plan"}


def test_assignment_is_stable_balanced_and_requires_an_id():
    bits = [N.hidden_min_share_veto_assignment(f"balance-{index}")
            for index in range(6000)]
    assert 0.47 < sum(bits) / len(bits) < 0.53
    assert all(N.hidden_min_share_veto_assignment(f"same-{index}")
               == N.hidden_min_share_veto_assignment(f"same-{index}")
               for index in range(500))
    assert N.hidden_min_share_veto_assignment("") is None
    assert N.hidden_min_share_veto_assignment(None) is None
    for index in range(500):
        gid = f"reader-parity-{index}"
        expected = ("candidate" if N.hidden_min_share_veto_assignment(gid)
                    else "control")
        assert live_percentile.hidden_min_share_veto_arm(gid) == expected


@pytest.mark.parametrize(
    ("own_value", "seller", "base", "multiplier", "zone"),
    [
        (80.0, True, 100.0, 0.8, 20.0),
        (100.0, True, 100.0, 1.0, 20.0),
        (120.0, True, 100.0, 1.2, 30.0),
        (100.0, False, 100.0, 1.0, 20.0),
        (120.0, False, 100.0, 1.2, 20.0),
        (150.0, False, 100.0, 1.5, 30.0),
        (8_000.0, True, 10_000.0, 0.8, 2_000.0),
        (1_500_000.0, False, 1_000_000.0, 1.5, 300_000.0),
    ],
)
def test_smallest_positive_zone_follows_the_official_support(
        own_value, seller, base, multiplier, zone):
    signal = N.hidden_min_positive_zone(own_value, seller)
    assert signal == {
        "base": base,
        "own_multiplier": multiplier,
        "min_positive_zone": pytest.approx(zone),
    }


@pytest.mark.parametrize(("own_value", "seller"), [
    (150.0, True), (80.0, False), (123.0, True), (float("nan"), False),
])
def test_dead_or_off_grid_types_have_no_positive_support_zone(own_value, seller):
    assert N.hidden_min_positive_zone(own_value, seller) is None


@pytest.mark.parametrize(
    ("role", "own_value", "offer", "expected_share"),
    [
        ("seller", 80.0, 82.0, 0.10),
        ("seller", 120.0, 125.0, 1 / 6),
        ("buyer", 120.0, 118.0, 0.10),
        ("buyer", 150.0, 145.0, 1 / 6),
    ],
)
def test_signal_is_role_symmetric_and_uses_only_observed_own_value(
        role, own_value, offer, expected_share):
    game = _game(role=role, own_value=own_value, offer=offer)
    signal = N.hidden_min_share_signal(
        game["game_state"], game["your_player"])
    assert signal["role"] == role
    assert signal["positive_zone_share_upper"] == pytest.approx(expected_share)
    assert signal["surplus"] > 0


@pytest.mark.parametrize(
    ("role", "own_value", "offer"),
    [
        ("seller", 80.0, 88.0),       # exactly 40% of the .2B minimum
        ("buyer", 120.0, 112.0),      # mirrored exact boundary
        ("seller", 80.0, 80.0),       # zero payoff
        ("buyer", 120.0, 121.0),      # losing offer
    ],
)
def test_exact_boundary_and_nonprofitable_offers_are_not_signals(
        role, own_value, offer):
    game = _game(role=role, own_value=own_value, offer=offer)
    assert N.hidden_min_share_signal(
        game["game_state"], game["your_player"]) is None


def test_default_off_and_hash_control_keep_the_accept_wire(monkeypatch):
    game = _game(gid=_gid(True))
    monkeypatch.setenv("GLEE_NEGO_HORIZON_V2", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    monkeypatch.setenv("GLEE_NEGO_TABLE", "1")
    assert _wire(game) == {"decision": "AcceptOffer"}

    _arm(monkeypatch)
    control = N.decide(_game(gid=_gid(False)), Config.from_env())
    assert {key: value for key, value in control.items() if key != "_plan"} == {
        "decision": "AcceptOffer"}
    assert control["_plan"]["hidden_min_share_veto"]["arm"] == "control"


@pytest.mark.parametrize(("role", "own_value", "offer"), [
    ("seller", 80.0, 82.0),
    ("buyer", 120.0, 118.0),
])
def test_candidate_rejects_only_the_control_acceptance(
        monkeypatch, role, own_value, offer):
    _arm(monkeypatch)
    control = N.decide(
        _game(gid=_gid(False), role=role, own_value=own_value, offer=offer),
        Config.from_env())
    candidate = N.decide(
        _game(gid=_gid(True), role=role, own_value=own_value, offer=offer),
        Config.from_env())
    assert control["decision"] == "AcceptOffer"
    assert candidate["decision"] == "RejectOffer"
    assert candidate["product_price"] == \
        candidate["_plan"]["hidden_min_share_veto"]["counter_price"]
    assert candidate["_plan"]["hidden_min_share_veto"]["arm"] == "candidate"
    assert "hidden_min_share_veto" in candidate["_plan"]["gates_fired"]


def test_direct_table_accept_is_also_isolated(monkeypatch):
    _arm(monkeypatch)
    # At elapsed=.6 the seller table accepts >=.03446B; a five-dollar surplus
    # is therefore a direct table accept but only 25% of the minimum .2B ZOPA.
    control = N.decide(
        _game(gid=_gid(False), own_value=80.0, offer=85.0, rnd=6),
        Config.from_env())
    candidate = N.decide(
        _game(gid=_gid(True), own_value=80.0, offer=85.0, rnd=6),
        Config.from_env())
    assert control["decision"] == "AcceptOffer"
    assert "table_accept" in control["_plan"]["gates_fired"]
    assert control["_plan"]["hidden_min_share_veto"]["control_acceptor"] \
        == "table_accept"
    assert candidate["decision"] == "RejectOffer"
    assert candidate["_plan"]["hidden_min_share_veto"]["control_acceptor"] \
        == "table_accept"


def test_real_final_round_any_positive_is_never_vetoed(monkeypatch):
    _arm(monkeypatch)
    candidate_game = _game(
        gid=_gid(True), own_value=80.0, offer=80.01, rnd=10)
    candidate = N.decide(candidate_game, Config.from_env())
    assert candidate["decision"] == "AcceptOffer"
    assert "hidden_min_share_veto" not in candidate["_plan"]
    assert N.hidden_min_share_signal(
        candidate_game["game_state"], candidate_game["your_player"]) is None


@pytest.mark.parametrize("fp_flag", [
    "GLEE_NEGO_FIRST_PRINCIPLES", "GLEE_NEGO_FP_ALWAYS",
])
def test_disjoint_first_principles_flags_do_not_shadow_the_arm(
        monkeypatch, fp_flag):
    _arm(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_FIRST_PRINCIPLES", "1")
    monkeypatch.setenv(fp_flag, "1")
    candidate = N.decide(_game(gid=_gid(True)), Config.from_env())
    assert candidate["decision"] == "RejectOffer"
    assert "hidden_min_share_veto" in candidate["_plan"]["gates_fired"]


@pytest.mark.parametrize("changes", [
    {"complete": True},
    {"own_value": 150.0},              # dead seller extreme
    {"own_value": 123.0},              # off-grid value
    {"offer": 88.0},                   # exact 40% boundary
])
def test_ineligible_states_are_identical_between_arms(monkeypatch, changes):
    _arm(monkeypatch)
    control = _wire(_game(gid=_gid(False), **changes))
    candidate = _wire(_game(gid=_gid(True), **changes))
    assert candidate == control


@pytest.mark.parametrize("conflict", [
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
    "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HIDDEN_FLOOR",
    "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
    "GLEE_NEGO_RANK_PRICE_AB",
    "GLEE_NEGO_CLOSE_AB",
    "GLEE_NEGO_UNCAPPED_AB",
    "GLEE_NEGO_SURPLUS_PROBE",
])
def test_conflicting_experiments_fail_closed(monkeypatch, conflict):
    monkeypatch.setenv("GLEE_NEGO_HORIZON_V2", "1")
    monkeypatch.setenv("GLEE_NEGO_CONTINUATION_ACCEPT", "1")
    monkeypatch.setenv("GLEE_NEGO_TABLE", "1")
    game = _game(gid=_gid(True))
    monkeypatch.setenv(conflict, "1")
    baseline = _wire(game)
    monkeypatch.setenv(FLAG, "1")
    assert _wire(game) == baseline


@pytest.mark.parametrize("missing_owner", [
    "GLEE_NEGO_HORIZON_V2", "GLEE_NEGO_CONTINUATION_ACCEPT", "GLEE_NEGO_TABLE",
])
def test_missing_accept_stack_owner_fails_closed(monkeypatch, missing_owner):
    _arm(monkeypatch)
    monkeypatch.setenv(missing_owner, "0")
    game = _game(gid=_gid(True))
    armed = _wire(game)
    monkeypatch.setenv(FLAG, "0")
    assert _wire(game) == armed


def test_reachability_scope_uses_the_logged_pre_action_acceptance(monkeypatch):
    _arm(monkeypatch)
    game = _game(gid=_gid(True))
    plan = N.decide(game, Config.from_env())["_plan"]
    predicate = check_reachability.KNOWN[FLAG][2]
    assert predicate(game, plan) is True
    assert predicate(game, {}) is False
    wrong_phase = _game(gid=_gid(True))
    wrong_phase["valid_actions"] = {"type": "offer"}
    assert predicate(wrong_phase, plan) is False


@pytest.mark.parametrize("treatment", [False, True])
def test_reader_cohorts_first_control_acceptance_and_audits_wire(
        monkeypatch, treatment):
    _arm(monkeypatch)
    game = _game(gid=_gid(treatment))
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
    exposure = live_percentile._hidden_min_share_veto_exposure_turn(
        "conceder", record)
    assert exposure[0] == ("conceder", game["game_id"])
    assert exposure[1] == 1234.0
    diagnostic = exposure[2]
    assert diagnostic["plan_arm"] == ("candidate" if treatment else "control")
    assert diagnostic["mechanism_ok"] is True
    assert diagnostic["positive_zone_share_upper"] == pytest.approx(0.10)
    assert diagnostic["action_decision"] == (
        "RejectOffer" if treatment else "AcceptOffer")


def test_reader_rejects_a_malformed_candidate_wire(monkeypatch):
    _arm(monkeypatch)
    game = _game(gid=_gid(True))
    action = N.decide(game, Config.from_env())
    plan = action.pop("_plan")
    action["product_price"] += 1.0
    record = {
        "ts": 1234.0, "game_id": game["game_id"],
        "game_family": "negotiation", "your_player": game["your_player"],
        "action_type": "decision", "state": game["game_state"],
        "action": action, "plan": plan,
    }
    exposure = live_percentile._hidden_min_share_veto_exposure_turn(
        "conceder", record)
    assert exposure[2]["mechanism_ok"] is False


def test_report_blocks_without_complete_official_join(capsys):
    diagnostic = {
        "role": "seller", "horizon": "10", "own_multiplier": 0.8,
        "scale": 100.0, "messages": False,
        "control_acceptor": "continuation_accept", "mechanism_ok": True,
    }
    rows = [
        ("conceder", 0.45, _gid(False), True, diagnostic, "terminal"),
        ("conceder", 0.60, _gid(True), False, diagnostic, "terminal"),
    ]
    assert live_percentile.report_hidden_min_share_veto(
        rows, 1.0, since=1000.0, until=2000.0) == 1
    output = capsys.readouterr().out
    assert "local pooled-CDF percentile is diagnostic only" in output
    assert "terminal outcomes missing official delta=2" in output
    assert "every agreement/no-deal/walk/pending" in output
