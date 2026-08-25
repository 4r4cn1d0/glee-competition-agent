"""Deterministic promotion tests for the first-principles negotiation policy."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import actions, first_principles as fp, runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation
from scripts import check_reachability


FLAG = fp.DETERMINISTIC_FLAG


@pytest.fixture(autouse=True)
def _clean_negotiation_flags(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    for key in list(os.environ):
        if key.startswith("GLEE_NEGO") or key == "GLEE_TRACE_GATES":
            monkeypatch.delenv(key, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(*, gid="g", complete=True, seller=True, max_rounds=1,
          horizon_known=True, my_value=80.0, their_value=150.0,
          phase="offer", round_no=1, offered=None):
    me = "player_1" if seller else "player_2"
    them = "player_2" if seller else "player_1"
    state = {
        "round": round_no,
        "horizon_known": horizon_known,
        "phase": phase,
        "current_player": me,
        f"{me}_role": "seller" if seller else "buyer",
        f"{them}_role": "buyer" if seller else "seller",
        f"{me}_value": my_value,
        "complete_information": complete,
        "messages_allowed": False,
        "history": [],
    }
    if horizon_known:
        state["max_rounds"] = max_rounds
    if complete:
        state[f"{them}_value"] = their_value
    if offered is not None:
        state["last_offer"] = {
            "price": offered,
            "from_player": them,
            "round": round_no,
        }
    return {
        "game_family": "negotiation",
        "game_id": gid,
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": phase},
    }


def _enable(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


@pytest.mark.parametrize("scale", [1.0, 100.0, 10000.0])
def test_complete_terminal_proposers_leave_exactly_one_cent(monkeypatch, scale):
    _enable(monkeypatch)

    seller_game = _game(
        complete=True,
        seller=True,
        max_rounds=1,
        my_value=80.0 * scale,
        their_value=150.0 * scale,
    )
    seller_wire = actions.coerce(
        negotiation.decide(seller_game, Config()), seller_game)
    assert seller_wire["product_price"] == pytest.approx(150.0 * scale - 0.01)

    buyer_game = _game(
        complete=True,
        seller=False,
        max_rounds=10,
        round_no=10,
        my_value=150.0 * scale,
        their_value=80.0 * scale,
    )
    buyer_wire = actions.coerce(
        negotiation.decide(buyer_game, Config()), buyer_game)
    assert buyer_wire["product_price"] == pytest.approx(80.0 * scale + 0.01)


@pytest.mark.parametrize(
    ("cost", "expected"),
    [(80.0, 119.99), (100.0, 119.99), (120.0, 149.99)],
)
def test_hidden_one_round_seller_uses_score_grid_ask(monkeypatch, cost, expected):
    _enable(monkeypatch)
    game = _game(
        complete=False,
        seller=True,
        max_rounds=1,
        my_value=cost,
    )

    action = negotiation.decide(game, Config())

    assert action["product_price"] == pytest.approx(expected)
    assert action["_plan"]["source"] == fp.DETERMINISTIC_GATE


def test_deterministic_flag_has_no_game_hash_assignment(monkeypatch):
    _enable(monkeypatch)
    for index in range(200):
        game = _game(
            gid=f"deterministic-{index}",
            complete=False,
            seller=True,
            max_rounds=1,
            my_value=80.0,
        )
        assert fp.deterministic_owns(game)
        assert negotiation.decide(game, Config())["product_price"] == 119.99


def test_terminal_component_precedes_selected_leader_replica(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_LEADER_REPLICA_V1", "1")
    game = _game(
        complete=True,
        seller=False,
        max_rounds=10,
        round_no=10,
        my_value=150.0,
        their_value=80.0,
    )

    action = negotiation.decide(game, Config())

    assert action["product_price"] == pytest.approx(80.01)
    assert action["_plan"] == {
        "source": fp.DETERMINISTIC_GATE,
        "component": "first_principles",
    }


def test_cap10_buyer_rejects_midpoint_with_exact_counter(monkeypatch):
    _enable(monkeypatch)
    game = _game(
        complete=True,
        seller=False,
        max_rounds=10,
        round_no=9,
        phase="decision",
        my_value=150.0,
        their_value=80.0,
        offered=115.0,
    )

    action = negotiation.decide(game, Config())

    assert action["decision"] == "RejectOffer"
    assert action["product_price"] == pytest.approx(80.01)


def test_cap10_buyer_accepts_near_total_offer(monkeypatch):
    _enable(monkeypatch)
    game = _game(
        complete=True,
        seller=False,
        max_rounds=10,
        round_no=9,
        phase="decision",
        my_value=150.0,
        their_value=80.0,
        offered=80.20,
    )
    assert negotiation.decide(game, Config())["decision"] == "AcceptOffer"


def test_downstream_price_guards_cannot_rewrite_owned_price(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_CAP", "0.80")
    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    game = _game(
        complete=True,
        seller=True,
        max_rounds=1,
        my_value=80.0,
        their_value=150.0,
    )

    wire = actions.coerce(negotiation.decide(game, Config()), game)

    assert wire["product_price"] == pytest.approx(149.99)


@pytest.mark.parametrize(
    "game",
    [
        _game(complete=True, seller=True, max_rounds=10),
        _game(complete=False, seller=False, max_rounds=1, my_value=150.0),
        _game(complete=False, seller=True, max_rounds=10, my_value=80.0),
        _game(complete=True, seller=True, horizon_known=False),
    ],
)
def test_unsupported_cells_fall_through(monkeypatch, game):
    _enable(monkeypatch)
    assert not fp.deterministic_owns(game)
    assert negotiation.decide(game, Config())["_plan"].get("source") != fp.DETERMINISTIC_GATE


def test_flag_off_is_byte_identical(monkeypatch):
    game = _game(
        complete=False,
        seller=True,
        max_rounds=1,
        my_value=80.0,
    )
    monkeypatch.delenv(FLAG, raising=False)
    before = negotiation.decide(copy.deepcopy(game), Config())

    monkeypatch.setenv(FLAG, "0")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    after = negotiation.decide(copy.deepcopy(game), Config())

    assert before == after
    assert not fp.deterministic_owns(game)


def test_non_negotiation_families_are_never_owned(monkeypatch):
    _enable(monkeypatch)
    for family in ("bargaining", "persuasion"):
        game = _game()
        game["game_family"] = family
        assert not fp.deterministic_owns(game)


def test_reachability_registry_names_the_real_gate():
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    game = _game(complete=False, seller=True, max_rounds=1, my_value=80.0)
    assert family == "negotiation"
    assert gates == (fp.DETERMINISTIC_GATE,)
    assert predicate(game, {})
