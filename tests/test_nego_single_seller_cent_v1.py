"""Seller-only fleet promotion tests for one-round negotiation asks."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import actions, first_principles as fp, runtime_flags
from glee_agent.config import Config
from glee_agent.probes import make_probe
from glee_agent.strategies import negotiation
from scripts import check_reachability


FLAG = fp.SINGLE_SELLER_FLAG


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    for key in list(os.environ):
        if key.startswith("GLEE_NEGO") or key == "GLEE_TRACE_GATES":
            monkeypatch.delenv(key, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(
    *,
    game_id: str = "single-seller",
    family: str = "negotiation",
    seller: bool = True,
    complete: bool = True,
    max_rounds: int | None = 1,
    horizon_known: bool = True,
    phase: str = "offer",
    own_value: float = 80.0,
    buyer_value: float = 120.0,
) -> dict:
    me = "player_1" if seller else "player_2"
    them = "player_2" if seller else "player_1"
    state = {
        "round": 1,
        "horizon_known": horizon_known,
        "current_player": me,
        f"{me}_role": "seller" if seller else "buyer",
        f"{them}_role": "buyer" if seller else "seller",
        f"{me}_value": own_value,
        "complete_information": complete,
        "messages_allowed": False,
        "history": [],
    }
    if horizon_known:
        state["max_rounds"] = max_rounds
    if complete:
        state[f"{them}_value"] = buyer_value
    return {
        "game_family": family,
        "game_id": game_id,
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": phase},
    }


def _enable(monkeypatch) -> None:
    monkeypatch.setenv(FLAG, "1")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


@pytest.mark.parametrize("scale", [1.0, 100.0, 10000.0])
def test_complete_one_round_seller_leaves_visible_buyer_one_cent(
    monkeypatch, scale,
):
    _enable(monkeypatch)
    game = _game(
        complete=True,
        own_value=80.0 * scale,
        buyer_value=120.0 * scale,
    )

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    wire = actions.coerce(copy.deepcopy(action), copy.deepcopy(game))

    assert wire["product_price"] == pytest.approx(120.0 * scale - 0.01)
    assert 120.0 * scale - wire["product_price"] == pytest.approx(0.01)
    assert action["_plan"]["source"] == fp.SINGLE_SELLER_GATE
    assert action["_plan"]["component"] == fp.SINGLE_SELLER_COMPONENT


@pytest.mark.parametrize(
    ("cost", "expected"),
    [(80.0, 119.99), (100.0, 119.99), (120.0, 149.99), (150.0, 200.0)],
)
def test_hidden_one_round_seller_uses_official_support_grid(
    monkeypatch, cost, expected,
):
    _enable(monkeypatch)
    game = _game(complete=False, own_value=cost)

    action = negotiation.decide(game, Config(llm_mode="off"))

    assert action["product_price"] == pytest.approx(expected)
    assert action["_plan"]["source"] == fp.SINGLE_SELLER_GATE


def test_hidden_rule_does_not_claim_to_know_private_buyer_value(monkeypatch):
    _enable(monkeypatch)
    low_buyer = _game(complete=False, own_value=80.0, buyer_value=100.0)
    high_buyer = _game(complete=False, own_value=80.0, buyer_value=150.0)

    low_action = negotiation.decide(low_buyer, Config(llm_mode="off"))
    high_action = negotiation.decide(high_buyer, Config(llm_mode="off"))

    # buyer_value is omitted from both hidden game states, so the same supported
    # ask is required. It extracts one cent only when the private type is 120.
    assert low_action["product_price"] == high_action["product_price"] == 119.99


def test_flag_is_deterministic_and_game_id_invariant(monkeypatch):
    _enable(monkeypatch)
    for index in range(100):
        game = _game(
            game_id=f"single-seller-{index}",
            complete=False,
            own_value=80.0,
        )
        assert fp.single_seller_owns(game)
        assert negotiation.decide(game, Config(llm_mode="off"))["product_price"] == 119.99


def test_seller_flag_precedes_whole_policy_without_changing_price(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_TEST2_SUPPORT_V3", "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    game = _game(complete=False, own_value=80.0)

    action = negotiation.decide(game, Config(llm_mode="off"))

    assert action["product_price"] == pytest.approx(119.99)
    assert action["_plan"] == {
        "source": fp.SINGLE_SELLER_GATE,
        "component": fp.SINGLE_SELLER_COMPONENT,
        "gates_fired": [fp.SINGLE_SELLER_GATE],
    }


def test_randomized_probe_routes_target_without_shifting_later_rng(monkeypatch):
    target = _game(complete=False, own_value=80.0)
    later = _game(
        game_id="later-randomized-turn",
        complete=False,
        max_rounds=10,
        own_value=80.0,
    )

    control_strategy, _ = make_probe(
        "randomized", Config(llm_mode="off"), seed=20260828)
    control_target = control_strategy(copy.deepcopy(target))
    control_later = control_strategy(copy.deepcopy(later))

    _enable(monkeypatch)
    candidate_strategy, _ = make_probe(
        "randomized", Config(llm_mode="off"), seed=20260828)
    candidate_target = candidate_strategy(copy.deepcopy(target))
    candidate_later = candidate_strategy(copy.deepcopy(later))

    assert candidate_target["product_price"] == pytest.approx(119.99)
    assert candidate_target != control_target
    assert candidate_later == control_later


def test_downstream_price_guards_cannot_rewrite_seller_price(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_CAP", "0.80")
    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    game = _game(complete=True, own_value=80.0, buyer_value=150.0)

    wire = actions.coerce(negotiation.decide(game, Config(llm_mode="off")), game)

    assert wire["product_price"] == pytest.approx(149.99)


@pytest.mark.parametrize(
    "game",
    [
        _game(seller=False),
        _game(max_rounds=10),
        _game(horizon_known=False, max_rounds=None),
        _game(phase="decision"),
        _game(family="bargaining"),
        _game(own_value=81.0),
    ],
)
def test_every_non_target_cell_is_byte_identical(monkeypatch, game):
    control = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    _enable(monkeypatch)
    candidate = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert candidate == control
    assert not fp.single_seller_owns(game)


def test_flag_off_is_byte_identical(monkeypatch):
    game = _game(complete=False, own_value=80.0)
    before = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    monkeypatch.setenv(FLAG, "0")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    after = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert after == before
    assert not fp.single_seller_owns(game)


def test_reachability_registry_names_exact_seller_gate():
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    target = _game(complete=False, own_value=80.0)
    buyer = _game(seller=False)

    assert family == "negotiation"
    assert gates == (fp.SINGLE_SELLER_GATE,)
    assert predicate(target, {}) is True
    assert predicate(buyer, {}) is False
