"""Exact terminal acceptance for Test 2's unknown-horizon negotiation V3."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import deterministic_negotiation, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N


FLAG = N.TEST2_UNKNOWN_R99_ACCEPT_FLAG
GATE = N.TEST2_UNKNOWN_R99_ACCEPT_GATE


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _prior_buyer_price(round_no: int, price: float) -> dict:
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


def _game(
    *,
    complete: bool = True,
    own: float = 12000.0,
    other: float = 10000.0,
    offer: float = 11000.0,
    round_no: int = 99,
    prior_prices: int = 5,
    messages: bool = False,
) -> dict:
    state = {
        "game_family": "negotiation",
        "phase": "decision",
        "round": round_no,
        "horizon_known": False,
        "max_rounds": None,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": "player_2",
        "player_2_role": "buyer",
        "player_1_role": "seller",
        "player_2_value": own,
        "last_offer": {
            "price": offer,
            "from_player": "player_1",
            "round": round_no,
        },
        "history": [
            _prior_buyer_price(2 * index + 2, own * 0.75)
            for index in range(prior_prices)
        ],
    }
    if complete:
        state["player_1_value"] = other
    return {
        "game_id": "test2-unknown-r99-terminal-accept",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _arm_test2_v3(monkeypatch) -> None:
    # Mirror Test 2's atomic V2 -> V3 migration pair: V3 has precedence.
    monkeypatch.setenv(
        deterministic_negotiation.AGENT5_DEFAULT_V2_FLAG, "1",
    )
    monkeypatch.setenv(
        deterministic_negotiation.TEST2_SUPPORT_V3_FLAG, "1",
    )


def _decide(game: dict) -> dict:
    return N.decide(copy.deepcopy(game), Config(llm_mode="off"))


def test_default_off_preserves_complete_r99_reject_byte_for_byte(monkeypatch):
    _arm_test2_v3(monkeypatch)
    game = _game()

    baseline = _decide(game)
    monkeypatch.setenv(FLAG, "0")
    explicit_off = _decide(game)

    assert baseline == explicit_off
    assert baseline["decision"] == "RejectOffer"
    assert baseline["product_price"] == pytest.approx(10576.0)
    assert GATE not in baseline["_plan"]


def test_complete_r99_reject_becomes_profitable_accept(monkeypatch):
    _arm_test2_v3(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")

    action = _decide(_game())

    assert action["decision"] == "AcceptOffer"
    assert set(action) == {"decision", "_plan"}
    assert action["_plan"]["source"] == (
        deterministic_negotiation.TEST2_SUPPORT_V3
    )
    assert action["_plan"]["component"] == "observed_leader_buyer"
    assert action["_plan"][GATE] == {
        "eligible": True,
        "mode": "deterministic",
        "baseline_decision": "RejectOffer",
        "information": "complete",
        "round": 99,
        "offer_price": 11000.0,
        "own_value": 12000.0,
        "buyer_gain": 1000.0,
    }
    assert action["_plan"]["gates_fired"][-2:] == [
        deterministic_negotiation.TEST2_SUPPORT_V3_GATE,
        GATE,
    ]
    assert coerce(copy.deepcopy(action), _game()) == {
        "decision": "AcceptOffer",
    }


def test_hidden_r99_walk_becomes_profitable_accept(monkeypatch):
    _arm_test2_v3(monkeypatch)
    game = _game(
        complete=False,
        own=100.0,
        offer=89.0,
        prior_prices=49,
    )
    assert _decide(game)["decision"] == "WalkAway"
    monkeypatch.setenv(FLAG, "1")

    action = _decide(game)

    assert action["decision"] == "AcceptOffer"
    assert action["_plan"][GATE]["baseline_decision"] == "WalkAway"
    assert action["_plan"][GATE]["information"] == "hidden"
    assert action["_plan"][GATE]["buyer_gain"] == pytest.approx(11.0)


def test_message_enabled_reject_loses_counter_and_text_on_accept(monkeypatch):
    _arm_test2_v3(monkeypatch)
    game = _game(messages=True)
    baseline = _decide(game)
    assert baseline["decision"] == "RejectOffer"
    assert "product_price" in baseline and "message" in baseline
    monkeypatch.setenv(FLAG, "1")

    action = _decide(game)

    assert set(action) == {"decision", "_plan"}
    assert action["decision"] == "AcceptOffer"


def test_exact_cent_boundary_is_inclusive_at_large_scale(monkeypatch):
    _arm_test2_v3(monkeypatch)
    monkeypatch.setenv(FLAG, "1")

    action = _decide(_game(offer=11999.99))

    assert action["decision"] == "AcceptOffer"
    assert action["_plan"][GATE]["buyer_gain"] == pytest.approx(0.01)


def test_subcent_gain_is_not_promoted(monkeypatch):
    _arm_test2_v3(monkeypatch)
    game = _game(offer=11999.995)
    baseline = _decide(game)
    monkeypatch.setenv(FLAG, "1")

    assert _decide(game) == baseline
    assert baseline["decision"] == "RejectOffer"
    assert GATE not in baseline["_plan"]


def test_better_offer_already_accepted_is_unchanged(monkeypatch):
    _arm_test2_v3(monkeypatch)
    game = _game(offer=10500.0)
    baseline = _decide(game)
    assert baseline["decision"] == "AcceptOffer"
    monkeypatch.setenv(FLAG, "1")

    assert _decide(game) == baseline
    assert GATE not in baseline["_plan"]


def test_round_97_profitable_reject_keeps_v3_continuation(monkeypatch):
    _arm_test2_v3(monkeypatch)
    game = _game(round_no=97)
    baseline = _decide(game)
    monkeypatch.setenv(FLAG, "1")

    assert _decide(game) == baseline
    assert baseline["decision"] == "RejectOffer"
    assert GATE not in baseline["_plan"]


@pytest.mark.parametrize(
    "policy_flag",
    [
        deterministic_negotiation.AGENT5_DEFAULT_FLAG,
        deterministic_negotiation.AGENT5_DEFAULT_V2_FLAG,
    ],
)
def test_other_complete_policies_are_unchanged(monkeypatch, policy_flag):
    monkeypatch.setenv(policy_flag, "1")
    monkeypatch.setenv(FLAG, "1")
    game = _game()

    action = _decide(game)

    assert action["decision"] == "RejectOffer"
    assert GATE not in action["_plan"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda game: game["game_state"].update(
            horizon_known=True, max_rounds=100,
        ),
        lambda game: game["game_state"].update(max_rounds=99),
        lambda game: game["game_state"].update(round=98),
        lambda game: game["game_state"].update(round="99"),
        lambda game: game["game_state"].update(messages_allowed=None),
        lambda game: game["game_state"].pop("complete_information"),
        lambda game: game["game_state"].pop("horizon_known"),
        lambda game: game["game_state"].update(player_2_role="seller"),
        lambda game: game.update(your_player="player_1"),
        lambda game: game["game_state"]["last_offer"].update(
            from_player="player_2",
        ),
        lambda game: game["game_state"]["last_offer"].update(round=98),
        lambda game: game["game_state"]["last_offer"].pop("round"),
        lambda game: game["game_state"].update(game_family="bargaining"),
        lambda game: game["valid_actions"].update(type="offer"),
    ],
    ids=[
        "known-horizon",
        "contradictory-max-rounds",
        "earlier-round",
        "string-round",
        "missing-message-mode",
        "missing-information-mode",
        "missing-horizon-mode",
        "wrong-role",
        "wrong-current-agent",
        "self-offer",
        "stale-offer-round",
        "missing-offer-round",
        "contradictory-nested-family",
        "wrong-phase",
    ],
)
def test_nonmatching_or_malformed_terminal_nodes_are_unchanged(
    monkeypatch, mutate,
):
    _arm_test2_v3(monkeypatch)
    game = _game()
    mutate(game)
    baseline = _decide(game)
    monkeypatch.setenv(FLAG, "1")

    assert _decide(game) == baseline


@pytest.mark.parametrize(
    "offer",
    [12000.0, 12000.01, 0.0, -1.0, None, float("nan")],
)
def test_nonprofitable_nonpositive_and_malformed_offers_are_unchanged(
    monkeypatch, offer,
):
    _arm_test2_v3(monkeypatch)
    game = _game()
    game["game_state"]["last_offer"]["price"] = offer
    baseline = _decide(game)
    monkeypatch.setenv(FLAG, "1")

    assert _decide(game) == baseline


def test_forged_non_v3_plan_fails_closed(monkeypatch):
    _arm_test2_v3(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    game = _game()
    forged = {
        "decision": "RejectOffer",
        "product_price": 10576.0,
        "_plan": {
            "source": deterministic_negotiation.TEST2_SUPPORT_V3,
            "component": "current_hidden_unknown_buyer",
        },
    }

    assert N._maybe_test2_unknown_r99_accept(game, forged) is forged


def test_unexpected_public_action_key_fails_closed(monkeypatch):
    _arm_test2_v3(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    game = _game()
    malformed = _decide(game)
    malformed["seller_value"] = 10000.0

    assert N._maybe_test2_unknown_r99_accept(game, malformed) is malformed
