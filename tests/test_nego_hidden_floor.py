"""Hidden-information concession floors stay randomized and offer-only."""

from __future__ import annotations

import hashlib
import os

import pytest

from glee_agent import actions, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation
from scripts import live_percentile


def _gid(treatment: bool) -> str:
    for i in range(1000):
        gid = f"hidden-floor-{i}"
        bit = int(hashlib.sha256(("hidden_floor|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment:
            return gid
    raise AssertionError("could not find both hidden-floor hash arms")


def _game(*, gid=None, role="seller", complete=False, own_value=None,
          action_type="decision", rnd=9, max_rounds=10):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if me == "player_1" else "player_1"
    if own_value is None:
        own_value = 80.0 if role == "seller" else 150.0
    state = {
        "round": rnd,
        "max_rounds": max_rounds,
        "horizon_known": True,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": own_value,
        "history": [],
        "last_offer": None,
        "messages_allowed": False,
    }
    if complete:
        state[f"{other}_value"] = 150.0 if role == "seller" else 80.0
    if action_type == "decision":
        state["last_offer"] = {
            "from_player": other,
            "price": 100.0,
            "round": rnd,
        }
    return {
        "game_id": gid if gid is not None else _gid(True),
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


def test_hidden_seller_floor_holds_on_a_late_counter(monkeypatch):
    game = _game(gid=_gid(True), role="seller")
    raw = {"decision": "RejectOffer", "product_price": 110.0}
    assert coerce(raw, game) == raw

    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert coerce(raw, game) == {
        "decision": "RejectOffer",
        "product_price": 140.0,
    }


def test_hidden_buyer_floor_holds_late_in_the_mirrored_direction(monkeypatch):
    game = _game(gid=_gid(True), role="buyer")
    raw = {"decision": "RejectOffer", "product_price": 110.0}
    assert coerce(raw, game) == raw

    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    # Reflecting 1.40B around B gives 0.60B; min(), not max(), prevents the
    # buyer from conceding upward past that price.
    assert coerce(raw, game) == {
        "decision": "RejectOffer",
        "product_price": 60.0,
    }


@pytest.mark.parametrize(
    ("role", "raw_price"), [("seller", 160.0), ("buyer", 50.0)],
)
def test_hidden_floor_preserves_an_already_more_aggressive_price(
        monkeypatch, role, raw_price):
    game = _game(gid=_gid(True), role=role)
    raw = {"decision": "RejectOffer", "product_price": raw_price}
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert coerce(raw, game) == raw


@pytest.mark.parametrize("role", ["seller", "buyer"])
def test_complete_information_games_are_unaffected(monkeypatch, role):
    game = _game(gid=_gid(True), role=role, complete=True)
    raw = {"decision": "RejectOffer", "product_price": 110.0}
    before = coerce(raw, game)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert coerce(raw, game) == before


def test_default_zero_and_hash_control_are_byte_for_byte_inert(monkeypatch):
    raw = {"decision": "RejectOffer", "product_price": 110.0,
           "message": "unchanged"}
    candidate = _game(gid=_gid(True))
    absent = coerce(raw, candidate)

    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "0.0")
    assert coerce(raw, candidate) == absent

    control = _game(gid=_gid(False))
    before = coerce(raw, control)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")
    assert coerce(raw, control) == before


@pytest.mark.parametrize("setting", ["nan", "inf", "-1", "2.01"])
def test_invalid_floor_settings_are_inert(monkeypatch, setting):
    game = _game(gid=_gid(True))
    raw = {"decision": "RejectOffer", "product_price": 110.0}
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", setting)

    assert coerce(raw, game) == raw


def test_missing_game_id_and_off_grid_own_value_are_inert(monkeypatch):
    raw = {"decision": "RejectOffer", "product_price": 110.0}
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert coerce(raw, _game(gid="")) == raw
    assert coerce(raw, _game(gid=_gid(True), own_value=83.0)) == raw


class _HiddenState(dict):
    """Fail if the guard tries to inspect the hidden opponent value."""

    def get(self, key, default=None):
        if key == "player_2_value":
            raise AssertionError("hidden opponent value was read")
        return super().get(key, default)


def test_hidden_floor_uses_only_our_value(monkeypatch):
    game = _game(gid=_gid(True), role="seller")
    game["game_state"] = _HiddenState(game["game_state"])
    dict.__setitem__(game["game_state"], "player_2_value", 150.0)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert coerce({"product_price": 110.0}, {
        **game,
        "phase": "offer",
        "valid_actions": {"type": "offer"},
    }) == {"product_price": 140.0}


def test_accept_path_never_reads_hidden_floor(monkeypatch):
    game = _game(gid=_gid(True), action_type="decision")

    def fail_if_read(_name, _default):
        raise AssertionError("offer-only flag read on AcceptOffer")

    monkeypatch.setattr(runtime_flags, "as_float", fail_if_read)
    assert coerce({"decision": "AcceptOffer"}, game) == {
        "decision": "AcceptOffer",
    }


def test_flag_does_not_change_the_plan_or_acceptance_inputs(monkeypatch):
    game = _game(gid=_gid(True), role="buyer", action_type="decision")
    cfg = Config.from_env()
    before = negotiation.plan(game, cfg)

    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.40")

    assert negotiation.plan(game, cfg) == before


def test_runtime_and_reporter_recover_the_same_arm(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.15")
    for i in range(64):
        gid = f"hidden-floor-cross-check-{i}"
        expected = live_percentile.hidden_floor_arm(gid)
        treatment = actions._hidden_floor_treatment(
            _game(gid=gid, action_type="offer"))

        assert (treatment is not None) is (expected == "candidate")
