"""Final-wire guards for complete-information negotiation prices."""

from __future__ import annotations

import os

import pytest

from glee_agent import actions, dispatch, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_FAMILIES"):
            monkeypatch.delenv(name, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(*, role="seller", complete=True, seller_value=80.0,
          buyer_value=150.0, rnd=1, max_rounds=1, action_type="offer"):
    me = "player_1" if role == "seller" else "player_2"
    other = "player_2" if role == "seller" else "player_1"
    state = {
        "round": rnd,
        "max_rounds": max_rounds,
        "horizon_known": True,
        "complete_information": complete,
        "current_player": me,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{me}_value": seller_value if role == "seller" else buyer_value,
        "history": [],
        "messages_allowed": False,
    }
    if complete:
        state[f"{other}_value"] = buyer_value if role == "seller" else seller_value
    if action_type == "decision":
        state["last_offer"] = {
            "from_player": other,
            "price": seller_value if role == "seller" else buyer_value,
        }
    return {
        "game_id": f"guard-{role}-{complete}-{rnd}-{max_rounds}-{action_type}",
        "game_family": "negotiation",
        "your_player": me,
        "phase": action_type,
        "game_state": state,
        "valid_actions": {"type": action_type},
    }


def _wire(game: dict, cfg: Config | None = None) -> dict:
    return dispatch.make_strategy(cfg or Config(llm_mode="off"))(game)


@pytest.mark.parametrize(
    ("game", "bad_price", "bound"),
    [
        (_game(role="seller", seller_value=10_000, buyer_value=12_000,
               max_rounds=10), 21_894.4, 12_000.0),
        (_game(role="buyer", seller_value=8_000, buyer_value=10_000,
               max_rounds=10), 4_548.4, 8_000.0),
    ],
)
def test_zopa_clamp_repairs_complete_info_policy_on_the_wire(
        monkeypatch, game, bad_price, bound):
    off = _wire(game)
    assert off["product_price"] == bad_price

    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    armed = _wire(game)
    assert armed == {"product_price": bound}


def test_zopa_clamp_does_not_fire_in_hidden_information(monkeypatch):
    game = _game(role="seller", complete=False, seller_value=10_000,
                 buyer_value=12_000, max_rounds=10)
    off = _wire(game)
    assert off["product_price"] == 21_894.4

    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    assert _wire(game) == off


def test_zopa_clamp_is_after_full_llm_price_replacement(monkeypatch):
    game = _game(role="seller", seller_value=10_000, buyer_value=12_000,
                 max_rounds=10)
    monkeypatch.setenv("GLEE_LLM_FAMILIES", "negotiation")
    monkeypatch.setattr(
        dispatch.llm, "propose_action",
        lambda _game, _raw, _plan, _cfg: {"product_price": 14_000},
    )
    cfg = Config(llm_mode="full")
    assert _wire(game, cfg)["product_price"] == 14_000.0

    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    assert _wire(game, cfg)["product_price"] == 12_000.0


def test_zopa_clamp_covers_reject_counteroffers(monkeypatch):
    game = _game(role="seller", seller_value=10_000, buyer_value=12_000,
                 max_rounds=10, action_type="decision")
    raw = {"decision": "RejectOffer", "product_price": 14_000}
    assert coerce(raw, game)["product_price"] == 14_000.0

    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    assert coerce(raw, game)["product_price"] == 12_000.0


@pytest.mark.parametrize(
    ("role", "seller_value", "buyer_value", "raw_price", "expected"),
    [
        ("seller", 80.0, 100.009, 150.0, 100.009),
        ("buyer", 80.001, 100.0, 20.0, 80.001),
    ],
)
def test_zopa_clamp_is_still_inside_fractional_bound_after_rounding(
        monkeypatch, role, seller_value, buyer_value, raw_price, expected):
    game = _game(role=role, seller_value=seller_value, buyer_value=buyer_value,
                 max_rounds=10)
    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    action = coerce({"product_price": raw_price}, game)
    assert action["product_price"] == expected
    if role == "seller":
        assert action["product_price"] <= buyer_value
    else:
        assert action["product_price"] >= seller_value


@pytest.mark.parametrize(
    ("role", "baseline", "floored"),
    [
        ("seller", 91.52, 130.40),
        ("buyer", 140.10, 99.60),
    ],
)
def test_ult_floor_raises_our_share_without_horizon_v2(
        monkeypatch, role, baseline, floored):
    game = _game(role=role, seller_value=80, buyer_value=150)
    assert _wire(game)["product_price"] == baseline

    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.72")
    action = _wire(game)
    assert action["product_price"] == floored
    share = ((floored - 80) / 70 if role == "seller"
             else (150 - floored) / 70)
    assert share == pytest.approx(0.72)


def test_ult_cap_defaults_to_point_85_and_is_live_tunable(monkeypatch):
    game = _game(role="seller", seller_value=80, buyer_value=100)
    cfg = Config(llm_mode="off", nego_seller_anchor=4.0, nego_min_margin=0.12)

    # With the floor gate absent, neither the .85 default nor CAP alone changes
    # the historical 1.44-of-ZOPA hardliner ask.
    assert _wire(game, cfg)["product_price"] == 108.80
    monkeypatch.setenv("GLEE_NEGO_ULT_CAP", "0.80")
    assert _wire(game, cfg)["product_price"] == 108.80

    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.01")
    monkeypatch.delenv("GLEE_NEGO_ULT_CAP")
    assert _wire(game, cfg)["product_price"] == 97.00  # .85 of [80, 100]

    monkeypatch.setenv("GLEE_NEGO_ULT_CAP", "0.80")
    assert _wire(game, cfg)["product_price"] == 96.00


def test_ult_cap_remains_exact_after_rounding(monkeypatch):
    game = _game(role="seller", seller_value=80.0, buyer_value=100.009)
    cfg = Config(llm_mode="off", nego_seller_anchor=4.0, nego_min_margin=0.12)
    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.01")

    price = _wire(game, cfg)["product_price"]
    share = (price - 80.0) / (100.009 - 80.0)
    assert share == pytest.approx(0.85)
    assert share <= 0.85


def test_guard_failure_falls_back_inside_the_zopa(monkeypatch):
    game = _game(role="buyer", seller_value=80.001, buyer_value=80.005,
                 max_rounds=10)

    def fail_guard(_action, _game):
        raise RuntimeError("broken live flag read")

    monkeypatch.setattr(actions, "_apply_negotiation_price_guards", fail_guard)
    assert coerce({"product_price": 20.0}, game) == {"product_price": 80.005}


def test_dispatch_last_resort_does_not_reenter_failed_coerce(monkeypatch):
    game = _game(role="buyer", seller_value=80.001, buyer_value=80.005,
                 max_rounds=10)

    def fail_coerce(_action, _game):
        raise RuntimeError("coerce unavailable")

    monkeypatch.setattr(dispatch, "coerce", fail_coerce)
    assert dispatch.make_strategy(Config(llm_mode="off"))(game) == {
        "product_price": 80.005,
    }
