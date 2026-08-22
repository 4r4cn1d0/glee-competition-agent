"""Complete-information opening claims and concession floors stay offer-only."""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from glee_agent import actions, dispatch, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.gamelog import GameLog
from glee_agent.strategies import negotiation
from scripts import live_percentile


def _gid(treatment: bool) -> str:
    for i in range(1000):
        gid = f"open-claim-{i}"
        bit = int(hashlib.sha256(("open_claim|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment:
            return gid
    raise AssertionError("could not find both open-claim hash arms")


def _game(*, gid=None, role="seller", complete=True, seller_value=80.0,
          buyer_value=150.0, max_rounds=10, rnd=1, action_type="offer",
          include_other_value=True, last_price=120.0, prior_own_price=False):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    state = {
        "round": rnd,
        "horizon_known": max_rounds is not None,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": seller_value if role == "seller" else buyer_value,
        "history": [],
        "last_offer": None,
        "messages_allowed": False,
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if complete and include_other_value:
        state[f"{other}_value"] = buyer_value if role == "seller" else seller_value
    if action_type == "decision":
        state["last_offer"] = {
            "from_player": other,
            "price": last_price,
            "round": rnd,
        }
    if prior_own_price:
        if role == "seller":
            offer = {"from_player": me, "price": 140.0}
            counter = {"from_player": other, "price": 90.0}
        else:
            offer = {"from_player": other, "price": 140.0}
            counter = {"from_player": me, "price": 90.0}
        state["history"] = [{
            "round": 1,
            "offer": offer,
            "decision": "RejectOffer",
            "decided_by": other,
            "counteroffer": counter,
        }]
    return {
        "game_id": gid or _gid(True),
        "game_family": "negotiation",
        "your_player": me,
        "phase": action_type,
        "game_state": state,
        "valid_actions": {"type": action_type},
    }


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_FAMILIES"):
            monkeypatch.delenv(name, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def test_complete_info_seller_opening_claim_covers_horizon_one(monkeypatch):
    game = _game(gid=_gid(True), max_rounds=1)
    raw = {"product_price": 145.0}
    assert coerce(raw, game) == raw

    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.75")

    assert coerce(raw, game) == {"product_price": 132.50}


def test_complete_info_buyer_first_counter_is_its_opening_claim(monkeypatch):
    game = _game(gid=_gid(True), role="buyer", action_type="decision",
                 rnd=1, max_rounds=10, last_price=140.0)
    raw = {"decision": "RejectOffer", "product_price": 120.0}
    assert coerce(raw, game) == raw

    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.75")

    assert coerce(raw, game) == {
        "decision": "RejectOffer",
        "product_price": 97.50,
    }


@pytest.mark.parametrize(
    ("role", "raw_price", "expected"),
    [("seller", 100.0, 125.50), ("buyer", 130.0, 104.50)],
)
def test_claim_floor_holds_on_late_counter_without_reapplying_opening(
        monkeypatch, role, raw_price, expected):
    game = _game(gid=_gid(True), role=role, action_type="decision", rnd=5,
                 max_rounds=10, prior_own_price=True)
    raw = {"decision": "RejectOffer", "product_price": raw_price}
    assert coerce(raw, game) == raw

    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.90")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.65")

    assert coerce(raw, game) == {
        "decision": "RejectOffer",
        "product_price": expected,
    }


@pytest.mark.parametrize(
    ("role", "raw_price"), [("seller", 140.0), ("buyer", 90.0)],
)
def test_claim_floor_preserves_an_already_higher_claim(monkeypatch, role, raw_price):
    game = _game(gid=_gid(True), role=role, action_type="decision", rnd=5,
                 max_rounds=10, prior_own_price=True)
    raw = {"decision": "RejectOffer", "product_price": raw_price}
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.65")

    assert coerce(raw, game) == raw


@pytest.mark.parametrize(
    ("role", "seller_value", "buyer_value", "action_type", "raw", "expected"),
    [
        ("seller", 80.0, 100.009, "offer", {"product_price": 90.0}, 100.009),
        ("buyer", 80.001, 100.0, "decision",
         {"decision": "RejectOffer", "product_price": 90.0}, 80.001),
    ],
)
def test_opening_claim_above_one_clamps_to_the_visible_zopa(
        monkeypatch, role, seller_value, buyer_value, action_type, raw, expected):
    game = _game(gid=_gid(True), role=role, seller_value=seller_value,
                 buyer_value=buyer_value, action_type=action_type,
                 max_rounds=10)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "1.5")

    action = coerce(raw, game)

    assert action["product_price"] == expected
    assert seller_value <= action["product_price"] <= buyer_value


class _HiddenState(dict):
    """Fail the test if the guard tries to read the hidden opponent value."""

    def get(self, key, default=None):
        if key == "player_2_value":
            raise AssertionError("hidden opponent value was read")
        return super().get(key, default)


def test_hidden_information_exits_before_reading_opponent_value(monkeypatch):
    game = _game(gid=_gid(True), complete=False)
    game["game_state"] = _HiddenState(game["game_state"])
    dict.__setitem__(game["game_state"], "player_2_value", 150.0)
    raw = {"product_price": 123.45}
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.90")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.80")

    assert coerce(raw, game) == raw


def test_default_zero_and_hash_control_are_byte_for_byte_inert(monkeypatch):
    raw = {"product_price": 101.25, "message": "unchanged"}
    candidate = _game(gid=_gid(True))
    absent = coerce(raw, candidate)

    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.0")
    assert coerce(raw, candidate) == absent

    control = _game(gid=_gid(False))
    before = coerce(raw, control)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.75")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.65")
    assert coerce(raw, control) == before


def test_nonfinite_flags_are_inert(monkeypatch):
    game = _game(gid=_gid(True))
    raw = {"product_price": 101.25}
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "nan")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "inf")

    assert coerce(raw, game) == raw


def test_open_claim_does_not_reapply_after_our_first_price(monkeypatch):
    game = _game(gid=_gid(True), action_type="decision", rnd=5,
                 prior_own_price=True)
    raw = {"decision": "RejectOffer", "product_price": 110.0}
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.90")

    assert coerce(raw, game) == raw


def test_accept_path_never_reads_offer_flags(monkeypatch):
    game = _game(gid=_gid(True), action_type="decision", rnd=2)

    def fail_if_read(_name, _default):
        raise AssertionError("offer-only flag read on AcceptOffer")

    monkeypatch.setattr(runtime_flags, "as_float", fail_if_read)
    assert coerce({"decision": "AcceptOffer"}, game) == {
        "decision": "AcceptOffer",
    }


def test_flags_do_not_change_the_negotiation_plan_or_acceptance_inputs(monkeypatch):
    game = _game(gid=_gid(True), role="buyer", action_type="decision",
                 rnd=1, max_rounds=10, last_price=120.0)
    cfg = Config.from_env()
    before = negotiation.plan(game, cfg)

    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.90")
    monkeypatch.setenv("GLEE_NEGO_CLAIM_FLOOR", "0.80")

    assert negotiation.plan(game, cfg) == before


def test_runtime_and_reporter_recover_the_same_arm(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.75")
    for i in range(64):
        gid = f"open-claim-cross-check-{i}"
        bit = int(hashlib.sha256(("open_claim|" + gid).encode()).hexdigest(), 16) & 1
        expected_arm = "candidate" if bit else "control"

        assert live_percentile.open_claim_arm(gid) == expected_arm
        action = coerce({"product_price": 100.0}, _game(gid=gid))
        assert action["product_price"] == (132.50 if bit else 100.0)


def test_strategy_exception_fallback_remains_in_the_exposure_cohort(
        monkeypatch, tmp_path):
    game = _game(gid=_gid(True))
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.75")

    def fail(_game, _cfg):
        raise RuntimeError("forced strategy failure")

    monkeypatch.setitem(dispatch.STRATEGIES, "negotiation", fail)
    log = GameLog(str(tmp_path))

    action = dispatch.make_strategy(Config.from_env(), log)(game)

    records = [json.loads(line) for line in
               (tmp_path / "turns.jsonl").read_text(encoding="utf-8").splitlines()]
    fallback = next(rec for rec in records
                    if rec.get("source") == "fallback:strategy-error")
    assert action == {"product_price": 132.50}
    assert fallback["action"] == action
    assert live_percentile._open_claim_exposure_turn("champion", fallback) == (
        ("champion", game["game_id"]), fallback["ts"])
