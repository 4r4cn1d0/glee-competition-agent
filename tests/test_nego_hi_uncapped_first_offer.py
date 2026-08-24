"""Identified hidden no-limit first-offer greed experiment."""

from __future__ import annotations

import os

import pytest

from glee_agent import actions, runtime_flags
from glee_agent.actions import coerce
from scripts import check_reachability, live_percentile

FLAG = "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB"
ARMS = ("control", "share80", "share95")


def _gid(arm: str) -> str:
    for index in range(20_000):
        gid = f"hi-first-offer-{index}"
        if actions.hi_uncapped_first_offer_arm(gid) == arm:
            return gid
    raise AssertionError(f"no id for {arm}")


def _game(*, gid=None, role="seller", own_value=None, prior_prices=0,
          complete=False, known=False, max_rounds=None, family="negotiation"):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    if own_value is None:
        own_value = 120.0 if role == "seller" else 100.0
    history = []
    for index in range(prior_prices):
        history.append({
            "round": index * 2 + 1,
            "offer": {"from_player": me, "price": own_value},
            "decision": "RejectOffer",
            "decided_by": other,
            "counteroffer": {"from_player": other, "price": own_value},
        })
    state = {
        "round": prior_prices * 2 + (1 if role == "seller" else 2),
        "horizon_known": known,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "history": history,
        "messages_allowed": False,
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if complete:
        state[f"{other}_value"] = 150.0 if role == "seller" else 80.0
    action_type = "offer" if role == "seller" and prior_prices == 0 else "decision"
    return {
        "game_id": _gid("share95") if gid is None else gid,
        "game_family": family,
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": action_type},
    }


def _raw(game: dict, price=50.0) -> dict:
    if game["valid_actions"]["type"] == "offer":
        return {"product_price": price}
    return {"decision": "RejectOffer", "product_price": price}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_"):
            monkeypatch.delenv(name, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def test_assignment_is_stable_balanced_and_reader_exact():
    assigned = [actions.hi_uncapped_first_offer_arm(f"balance-{i}")
                for i in range(6000)]
    for arm in ARMS:
        assert 0.30 < assigned.count(arm) / len(assigned) < 0.37
    assert actions.hi_uncapped_first_offer_arm("") is None
    for index in range(500):
        gid = f"reader-{index}"
        assert live_percentile.hi_first_offer_arm(gid) == \
            actions.hi_uncapped_first_offer_arm(gid)


def test_default_off_and_control_are_byte_identical(monkeypatch):
    game = _game(gid=_gid("share95"))
    raw = _raw(game, 133.33)
    assert coerce(dict(raw), game) == raw

    monkeypatch.setenv(FLAG, "1")
    control = _game(gid=_gid("control"))
    raw = _raw(control, 133.33)
    assert coerce(dict(raw), control) == raw


@pytest.mark.parametrize(
    ("role", "own_mult", "arm", "expected_mult"),
    [
        ("seller", 1.2, "share80", 1.44),
        ("seller", 1.2, "share95", 1.485),
        ("buyer", 1.0, "share80", 0.84),
        ("buyer", 1.0, "share95", 0.81),
    ],
)
@pytest.mark.parametrize("base", [100.0, 10_000.0, 1_000_000.0])
def test_candidate_prices_the_unique_support_zone(
        monkeypatch, role, own_mult, arm, expected_mult, base):
    monkeypatch.setenv(FLAG, "1")
    game = _game(gid=_gid(arm), role=role, own_value=own_mult * base)
    assert coerce(_raw(game), game)["product_price"] == \
        pytest.approx(expected_mult * base)


def test_only_the_first_outgoing_price_changes(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    game = _game(gid=_gid("share95"), prior_prices=1)
    raw = _raw(game, 130.0)
    assert coerce(dict(raw), game) == raw


@pytest.mark.parametrize(
    "changes",
    [
        {"complete": True},
        {"known": True, "max_rounds": 10},
        {"known": True, "max_rounds": 1},
        {"role": "seller", "own_value": 100.0},
        {"role": "seller", "own_value": 150.0},
        {"role": "buyer", "own_value": 120.0},
        {"own_value": 137.0},
        {"gid": ""},
        {"family": "bargaining"},
    ],
)
def test_out_of_scope_states_are_unchanged(monkeypatch, changes):
    game = _game(**changes)
    raw = _raw(game, 77.77)
    baseline = coerce(dict(raw), game)
    monkeypatch.setenv(FLAG, "1")
    assert coerce(dict(raw), game) == baseline


@pytest.mark.parametrize("conflict,value", [
    ("GLEE_NEGO_HIDDEN_POLICY_V1", "1"),
    ("GLEE_NEGO_HIDDEN_FLOOR", "1.40"),
])
def test_probe_refuses_a_mixed_hidden_control(monkeypatch, conflict, value):
    game = _game(gid=_gid("share95"))
    monkeypatch.setenv(conflict, value)
    without_probe = coerce(_raw(game, 130.0), game)
    monkeypatch.setenv(FLAG, "1")
    assert coerce(_raw(game, 130.0), game) == without_probe


class _HiddenState(dict):
    def get(self, key, default=None):
        if key == "player_2_value":
            raise AssertionError("read hidden counterpart value")
        return super().get(key, default)


def test_candidate_never_reads_the_hidden_counterpart(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    game = _game(gid=_gid("share95"))
    state = _HiddenState(game["game_state"])
    dict.__setitem__(state, "player_2_value", 150.0)
    game["game_state"] = state
    assert coerce(_raw(game), game)["product_price"] == 148.5


def _record(game: dict, action: dict, ts=1234.0) -> dict:
    return {
        "ts": ts,
        "game_id": game["game_id"],
        "game_family": "negotiation",
        "your_player": game["your_player"],
        "action_type": game["valid_actions"]["type"],
        "state": game["game_state"],
        "action": action,
    }


def test_reachability_registry_and_reader_scope_match_runtime():
    predicate = check_reachability.KNOWN[FLAG][2]
    assert FLAG in check_reachability.POSTCONDITION_FLAGS
    assert predicate(_game(), {}) is True
    assert predicate(_game(prior_prices=1), {}) is False
    assert predicate(_game(known=True, max_rounds=10), {}) is False
    assert predicate(_game(role="seller", own_value=100.0), {}) is False

    game = _game(gid=_gid("share95"))
    exposure = live_percentile._hi_first_offer_exposure_turn(
        "hardliner", _record(game, {"product_price": 148.5}))
    assert exposure[0] == ("hardliner", game["game_id"])
    assert exposure[1] == 1234.0
    assert exposure[2]["wire_ok"] is True


def test_reader_cohorts_a_buyer_that_accepts_before_emitting_a_price():
    game = _game(gid=_gid("share80"), role="buyer", own_value=100.0)
    exposure = live_percentile._hi_first_offer_exposure_turn(
        "randomized", _record(game, {"decision": "AcceptOffer"}))
    assert exposure is not None
    assert exposure[2]["first_price"] is None
    assert exposure[2]["wire_ok"] is True


def test_report_is_explicitly_non_promotion_grade(capsys):
    gid = _gid("share95")
    row = ("hardliner", 0.8, gid, True, {
        "role": "seller", "own_mult": 1.2, "p_zopa": 0.25,
        "horizon": "inf", "zone_share": 0.95, "realized_capture": 0.95,
        "expected_price": 148.5, "wire_ok": True,
    }, "terminal")
    assert live_percentile.report_hi_first_offer([row], 1.0) == 0
    output = capsys.readouterr().out
    assert "LOCAL DIAGNOSTIC ONLY" in output
    assert "PROMOTION BLOCKED BY DESIGN" in output
