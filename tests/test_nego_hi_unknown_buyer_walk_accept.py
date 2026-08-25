"""Pointwise copied-buyer walk-to-profitable-accept repair."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import deterministic_negotiation, runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N


FLAG = N.HI_UNKNOWN_BUYER_WALK_ACCEPT_FLAG
GATE = N.HI_UNKNOWN_BUYER_WALK_ACCEPT_GATE


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
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


def _game(*, own: float = 120.0, offer: float = 119.97,
          prior_prices: int = 8) -> dict:
    round_no = 2 * prior_prices + 1
    state = {
        "game_family": "negotiation",
        "phase": "decision",
        "round": round_no,
        "horizon_known": False,
        "max_rounds": None,
        "complete_information": False,
        "messages_allowed": False,
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
            _prior_buyer_price(2 * index + 2, 70.0 + index)
            for index in range(prior_prices)
        ],
    }
    return {
        "game_id": "agent5-v1-profitable-walk",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _arm_agent5_v1(monkeypatch) -> None:
    monkeypatch.setenv(deterministic_negotiation.AGENT5_DEFAULT_FLAG, "1")


def _decide(game: dict) -> dict:
    return N.decide(copy.deepcopy(game), Config(llm_mode="off"))


def test_default_off_preserves_the_selected_walk_byte_for_byte(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    game = _game()

    baseline = _decide(game)
    monkeypatch.setenv(FLAG, "0")
    explicit_off = _decide(game)

    assert baseline == explicit_off
    assert baseline["decision"] == "WalkAway"
    assert baseline["_plan"]["source"] == (
        deterministic_negotiation.AGENT5_DEFAULT
    )


def test_exact_agent5_v1_walk_accepts_the_profitable_standing_offer(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")

    action = _decide(_game())

    assert action["decision"] == "AcceptOffer"
    assert set(action) == {"decision", "_plan"}
    assert action["_plan"]["source"] == (
        deterministic_negotiation.AGENT5_DEFAULT
    )
    assert action["_plan"]["component"] == "observed_leader_buyer"
    assert action["_plan"][GATE] == {
        "eligible": True,
        "mode": "deterministic",
        "baseline_decision": "WalkAway",
        "round": 17,
        "offer_price": 119.97,
        "own_value": 120.0,
        "buyer_gain": pytest.approx(0.03),
    }
    assert action["_plan"]["gates_fired"][-2:] == [
        deterministic_negotiation.AGENT5_DEFAULT_GATE,
        GATE,
    ]


def test_test2_v3_same_observed_walk_is_also_pointwise_repaired(monkeypatch):
    monkeypatch.setenv(deterministic_negotiation.TEST2_SUPPORT_V3_FLAG, "1")
    monkeypatch.setenv(FLAG, "1")

    action = _decide(_game(own=150.0, offer=148.49))

    assert action["decision"] == "AcceptOffer"
    assert action["_plan"]["source"] == (
        deterministic_negotiation.TEST2_SUPPORT_V3
    )
    assert action["_plan"]["component"] == "observed_leader_buyer"
    assert action["_plan"][GATE]["buyer_gain"] == pytest.approx(1.51)


def test_explicit_message_on_cell_uses_the_same_terminal_dominance(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    game = _game(own=150.0, offer=134.7816)
    game["game_state"]["messages_allowed"] = True

    action = _decide(game)

    assert action["decision"] == "AcceptOffer"
    assert action["_plan"][GATE]["buyer_gain"] == pytest.approx(15.2184)


def test_redundant_nested_family_may_be_absent_but_not_contradictory(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    canonical_engine = _game()
    canonical_engine["game_state"].pop("game_family")
    contradictory = _game()
    contradictory["game_state"]["game_family"] = "bargaining"

    assert _decide(canonical_engine)["decision"] == "AcceptOffer"
    assert _decide(contradictory)["decision"] == "WalkAway"


def test_one_cent_boundary_is_inclusive_but_a_smaller_gain_fails_closed(
    monkeypatch,
):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")

    exact_cent = _decide(_game(offer=119.99))
    sub_cent = _decide(_game(offer=119.991))

    assert exact_cent["decision"] == "AcceptOffer"
    assert sub_cent["decision"] == "WalkAway"
    assert GATE not in sub_cent["_plan"]


def test_one_cent_boundary_survives_large_value_float_representation(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")

    action = _decide(_game(own=150.0, offer=149.99))

    assert action["decision"] == "AcceptOffer"
    assert action["_plan"][GATE]["buyer_gain"] == pytest.approx(0.01)


def test_earlier_profitable_reject_and_counter_are_unchanged(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    game = _game(prior_prices=7)
    baseline = _decide(game)
    assert baseline["decision"] == "RejectOffer"
    assert baseline["product_price"] == 103.0

    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)

    assert candidate == baseline


def test_offer_phase_is_unchanged(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    game = _game()
    game["phase"] = "offer"
    game["game_state"]["phase"] = "offer"
    game["game_state"].pop("last_offer")
    game["valid_actions"] = {"type": "offer"}
    baseline = _decide(game)

    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)

    assert candidate == baseline
    assert "decision" not in candidate
    assert candidate["product_price"] == 103.0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda game: game["game_state"].update(
            complete_information=True, player_1_value=80.0,
        ),
        lambda game: game["game_state"].update(
            horizon_known=True, max_rounds=99,
        ),
        lambda game: game["game_state"].update(max_rounds=99),
        lambda game: game["game_state"].update(player_2_role="seller"),
        lambda game: game.update(your_player="player_1"),
        lambda game: game["game_state"]["last_offer"].update(
            from_player="player_2",
        ),
        lambda game: game["game_state"]["last_offer"].update(round=16),
        lambda game: game["game_state"]["last_offer"].pop("round"),
        lambda game: game["game_state"].update(messages_allowed=None),
        lambda game: game["game_state"].pop("complete_information"),
        lambda game: game["game_state"].pop("horizon_known"),
    ],
    ids=[
        "complete-information",
        "known-horizon",
        "contradictory-max-rounds",
        "seller",
        "wrong-current-agent",
        "self-offer",
        "stale-offer-round",
        "missing-offer-round",
        "missing-message-mode",
        "missing-information-mode",
        "missing-horizon-mode",
    ],
)
def test_nonmatching_cells_and_malformed_provenance_are_unchanged(
    monkeypatch, mutate,
):
    _arm_agent5_v1(monkeypatch)
    game = _game()
    mutate(game)
    baseline = _decide(game)

    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)

    assert candidate == baseline


@pytest.mark.parametrize("offer", [120.0, 120.01, 0.0, -1.0, None, float("nan")])
def test_nonprofitable_nonpositive_and_malformed_prices_are_unchanged(
    monkeypatch, offer,
):
    _arm_agent5_v1(monkeypatch)
    game = _game()
    game["game_state"]["last_offer"]["price"] = offer
    baseline = _decide(game)

    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)

    assert candidate == baseline


def test_agent5_v2_walk_is_not_changed(monkeypatch):
    monkeypatch.setenv(deterministic_negotiation.AGENT5_DEFAULT_V2_FLAG, "1")
    monkeypatch.setenv(FLAG, "1")

    action = _decide(_game())

    assert action["decision"] == "WalkAway"
    assert action["_plan"]["source"] != (
        deterministic_negotiation.AGENT5_DEFAULT
    )
    assert GATE not in action["_plan"]


def test_forged_walk_without_exact_agent5_plan_source_fails_closed(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    game = _game()
    forged = {
        "decision": "WalkAway",
        "_plan": {
            "source": deterministic_negotiation.AGENT5_DEFAULT,
            "component": "current_hidden_unknown_buyer",
        },
    }

    assert N._maybe_hi_unknown_buyer_walk_accept(game, forged) is forged


def test_malformed_walk_action_with_a_public_counter_fails_closed(monkeypatch):
    _arm_agent5_v1(monkeypatch)
    monkeypatch.setenv(FLAG, "1")
    game = _game()
    malformed = {
        "decision": "WalkAway",
        "product_price": 103.0,
        "_plan": {
            "source": deterministic_negotiation.AGENT5_DEFAULT,
            "component": "observed_leader_buyer",
        },
    }

    assert N._maybe_hi_unknown_buyer_walk_accept(
        game, malformed,
    ) is malformed


@pytest.mark.parametrize(
    "mutate",
    [
        lambda game: game["game_state"].update(round={"price": 17}),
        lambda game: game["game_state"].update(
            player_2_value={"price": 120.0},
        ),
        lambda game: game["game_state"]["last_offer"].update(
            round={"price": 17},
        ),
        lambda game: game["game_state"]["last_offer"].update(
            price={"price": 119.97},
        ),
        lambda game: game["game_state"]["last_offer"].update(
            price=10 ** 10000,
        ),
    ],
    ids=["round", "own-value", "offer-round", "offer-price", "huge-price"],
)
def test_nested_dicts_are_never_accepted_as_scalar_wire_fields(
    monkeypatch, mutate,
):
    _arm_agent5_v1(monkeypatch)
    baseline = _decide(_game())
    assert baseline["decision"] == "WalkAway"
    monkeypatch.setenv(FLAG, "1")
    malformed_game = _game()
    mutate(malformed_game)

    assert N._maybe_hi_unknown_buyer_walk_accept(
        malformed_game, baseline,
    ) is baseline
