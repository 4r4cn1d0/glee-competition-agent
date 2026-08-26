"""Regression contract for the coherent Test 4 negotiation hotfix."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import deterministic_negotiation as policies
from glee_agent import nego_support_v2, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation


HOTFIX_FLAG = policies.TEST4_HOTFIX_V1_FLAG
HOTFIX_POLICY = policies.TEST4_HOTFIX_V1


@pytest.fixture(autouse=True)
def _clean_negotiation_flags(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _current_test4(monkeypatch) -> None:
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    monkeypatch.setenv(HOTFIX_FLAG, "0")


def _test4_hotfix(monkeypatch) -> None:
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "0")
    monkeypatch.setenv(HOTFIX_FLAG, "1")
    assert policies.mode() == HOTFIX_POLICY


def _decide(game: dict) -> dict:
    return negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))


def _public(action: dict) -> dict:
    return {
        key: value
        for key, value in action.items()
        if not str(key).startswith("_")
    }


def _buyer_price(round_no: int, price: float) -> dict:
    return {
        "round": round_no,
        "offer": {
            "price": price,
            "from_player": "player_2",
            "round": round_no,
        },
        "decision": "RejectOffer",
        "decided_by": "player_1",
    }


def _hidden_unknown_profitable_walk() -> dict:
    prior_prices = 8
    round_no = 2 * prior_prices + 1
    return {
        "game_id": "test4-hidden-unknown-profitable-walk",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": {
            "game_family": "negotiation",
            "phase": "decision",
            "round": round_no,
            "horizon_known": False,
            "max_rounds": None,
            "complete_information": False,
            "messages_allowed": False,
            "current_player": "player_2",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_2_value": 120.0,
            "last_offer": {
                "price": 119.97,
                "from_player": "player_1",
                "round": round_no,
            },
            "history": [
                _buyer_price(2 * index + 2, 70.0 + index)
                for index in range(prior_prices)
            ],
        },
    }


def _hidden_seller_offer(*, known_horizon: bool, own: float = 100.0) -> dict:
    state = {
        "game_family": "negotiation",
        "phase": "offer",
        "round": 1,
        "horizon_known": known_horizon,
        "complete_information": False,
        "messages_allowed": False,
        "current_player": "player_1",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": own,
        "history": [],
    }
    if known_horizon:
        state["max_rounds"] = 10
    else:
        state["max_rounds"] = None
    return {
        "game_id": (
            "test4-hidden-cap10-seller"
            if known_horizon
            else "test4-hidden-unknown-seller"
        ),
        "game_family": "negotiation",
        "your_player": "player_1",
        "phase": "offer",
        "valid_actions": {"type": "offer"},
        "game_state": state,
    }


def _complete_unknown_round97_low_share() -> dict:
    round_no = 97
    offer_price = 98.5
    counter_price = 85.76
    history = []
    for buyer_round in range(round_no - 20, round_no, 2):
        history.extend([
            {
                "round": buyer_round,
                "offer": {
                    "price": offer_price,
                    "from_player": "player_1",
                    "round": buyer_round,
                },
                "decision": "RejectOffer",
                "decided_by": "player_2",
                "counteroffer": counter_price,
            },
            {
                "round": buyer_round + 1,
                "offer": {
                    "price": counter_price,
                    "from_player": "player_2",
                    "round": buyer_round + 1,
                },
                "decision": "RejectOffer",
                "decided_by": "player_1",
                "counteroffer": offer_price,
            },
        ])
    return {
        "game_id": "test4-complete-unknown-round97-low-share",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": {
            "game_family": "negotiation",
            "phase": "decision",
            "round": round_no,
            "horizon_known": False,
            "max_rounds": None,
            "complete_information": True,
            "messages_allowed": False,
            "current_player": "player_2",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_1_value": 80.0,
            "player_2_value": 100.0,
            "last_offer": {
                "price": offer_price,
                "from_player": "player_1",
                "round": round_no,
            },
            "history": history,
        },
    }


def _hidden_cap10_terminal_buyer() -> dict:
    return {
        "game_id": "test4-hidden-cap10-terminal-buyer",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "offer",
        "valid_actions": {"type": "offer"},
        "game_state": {
            "game_family": "negotiation",
            "phase": "offer",
            "round": 10,
            "horizon_known": True,
            "max_rounds": 10,
            "complete_information": False,
            "messages_allowed": False,
            "current_player": "player_2",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_2_value": 120.0,
            "history": [],
        },
    }


def _unknown_round99_profitable_offer() -> dict:
    game = _complete_unknown_round97_low_share()
    state = game["game_state"]
    game["game_id"] = "test4-unknown-round99-profitable-offer"
    state["round"] = 99
    state["last_offer"] = {
        "price": 90.0,
        "from_player": "player_1",
        "round": 99,
    }
    state["history"] = [_buyer_price(2 * index + 2, 82.0)
                        for index in range(5)]
    return game


@pytest.mark.parametrize(
    "game_factory",
    [
        _hidden_unknown_profitable_walk,
        lambda: _hidden_seller_offer(known_horizon=False),
        lambda: _hidden_seller_offer(known_horizon=True),
        _complete_unknown_round97_low_share,
        _hidden_cap10_terminal_buyer,
        _unknown_round99_profitable_offer,
    ],
    ids=[
        "hidden-unknown-profitable-walk",
        "hidden-unknown-seller-support",
        "hidden-cap10-seller-support",
        "complete-unknown-round97-low-share",
        "hidden-cap10-terminal-buyer",
        "unknown-round99-profitable-offer",
    ],
)
def test_hotfix_selector_explicit_off_preserves_current_test4_byte_for_byte(
    monkeypatch, game_factory,
):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = game_factory()
    baseline = _decide(game)

    monkeypatch.setenv(HOTFIX_FLAG, "0")
    explicit_off = _decide(game)

    assert explicit_off == baseline


def test_hidden_unknown_buyer_accepts_profitable_offer_instead_of_walking(
    monkeypatch,
):
    game = _hidden_unknown_profitable_walk()
    _current_test4(monkeypatch)
    baseline = _decide(game)
    assert _public(baseline) == {"decision": "WalkAway"}

    _test4_hotfix(monkeypatch)
    fixed = _decide(game)

    assert _public(fixed) == {"decision": "AcceptOffer"}


@pytest.mark.parametrize("known_horizon", [False, True], ids=["unknown", "cap10"])
@pytest.mark.parametrize(
    ("own", "expected"),
    [(80.0, 119.99), (100.0, 119.99), (120.0, 149.99)],
)
def test_hidden_seller_offer_uses_the_official_support_grid(
    monkeypatch, known_horizon, own, expected,
):
    game = _hidden_seller_offer(known_horizon=known_horizon, own=own)
    _current_test4(monkeypatch)
    baseline = _decide(game)
    assert baseline["product_price"] > 150.0

    _test4_hotfix(monkeypatch)
    fixed = _decide(game)
    wire = coerce(copy.deepcopy(fixed), copy.deepcopy(game))
    support_ask = (
        nego_support_v2.hidden_cap10_seller_ask(game)
        if known_horizon
        else nego_support_v2.hidden_unknown_seller_ask(game)
    )

    assert support_ask == pytest.approx(expected)
    assert fixed["product_price"] == pytest.approx(expected)
    assert wire["product_price"] == pytest.approx(expected)
    assert own < wire["product_price"] < 150.0


def test_complete_unknown_round97_remains_independently_switchable(
    monkeypatch,
):
    game = _complete_unknown_round97_low_share()
    state = game["game_state"]
    buyer_share = (
        (state["player_2_value"] - state["last_offer"]["price"])
        / (state["player_2_value"] - state["player_1_value"])
    )
    assert buyer_share == pytest.approx(0.075)

    _current_test4(monkeypatch)
    baseline = _decide(game)
    assert _public(baseline) == {
        "decision": "RejectOffer",
        "product_price": 85.76,
    }

    _test4_hotfix(monkeypatch)
    selector_only = _decide(game)
    assert _public(selector_only) == {
        "decision": "RejectOffer",
        "product_price": 85.76,
    }

    monkeypatch.setenv(
        negotiation.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_FLAG, "1",
    )
    fixed = _decide(game)

    assert _public(fixed) == {"decision": "AcceptOffer"}


def test_hotfix_keeps_v3_hidden_terminal_cent_bid(monkeypatch):
    _test4_hotfix(monkeypatch)

    action = _decide(_hidden_cap10_terminal_buyer())

    assert _public(action) == {"product_price": 100.01}
    assert action["_plan"]["source"] == HOTFIX_POLICY
    assert action["_plan"]["component"] == (
        nego_support_v2.TERMINAL_BUYER_COMPONENT
    )


def test_hotfix_accepts_profitable_offer_at_true_round99(monkeypatch):
    game = _unknown_round99_profitable_offer()
    _current_test4(monkeypatch)
    assert _public(_decide(game))["decision"] == "RejectOffer"

    _test4_hotfix(monkeypatch)
    action = _decide(game)

    assert _public(action) == {"decision": "AcceptOffer"}
    assert negotiation.TEST2_UNKNOWN_R99_ACCEPT_GATE in action["_plan"]


def test_hotfix_masks_v1_during_atomic_selector_migration(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    monkeypatch.setenv(HOTFIX_FLAG, "1")

    assert policies.mode() == HOTFIX_POLICY
    action = _decide(_hidden_seller_offer(known_horizon=True))
    assert action["_plan"]["source"] == HOTFIX_POLICY
    assert action["product_price"] == pytest.approx(119.99)
