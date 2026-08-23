"""Tests for promoting the open-claim from a 50/50 hash arm to always-on.

The first block is the one that matters: with GLEE_NEGO_OPEN_CLAIM_ALWAYS unset,
every game must take exactly the same path it took before this flag existed, so
Test 4's running hash experiment is not contaminated.
"""

from __future__ import annotations

import hashlib

import pytest

from glee_agent import actions, runtime_flags


@pytest.fixture(autouse=True)
def _clear():
    runtime_flags._CACHE = None
    yield
    runtime_flags._CACHE = None


def game(*, gid="g1", seller=True, hk=True, mr=1, my=80.0, their=150.0):
    me = "player_1" if seller else "player_2"
    them = "player_2" if seller else "player_1"
    state = {
        "game_family": "negotiation", "round": 1, "max_rounds": mr,
        "horizon_known": hk, "current_player": me,
        f"{me}_role": "seller" if seller else "buyer",
        f"{them}_role": "buyer" if seller else "seller",
        f"{me}_value": my, f"{them}_value": their,
        "complete_information": True, "messages_allowed": False, "history": [],
    }
    return {"game_family": "negotiation", "game_id": gid, "your_player": me,
            "game_state": state, "valid_actions": {"type": "offer"}}


def hash_arm(gid):
    return int(hashlib.sha256(("open_claim|" + gid).encode()).hexdigest(), 16) & 1


CLAIM = {"GLEE_NEGO_OPEN_CLAIM": "0.95", "GLEE_NEGO_CLAIM_FLOOR": "0.80"}


def test_flag_unset_preserves_the_hash_experiment(monkeypatch):
    for k, v in CLAIM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", raising=False)
    for i in range(60):
        gid = f"hash-{i}"
        got = actions._open_claim_treatment(game(gid=gid))
        assert (got is not None) == bool(hash_arm(gid)), gid


def test_always_on_treats_every_game(monkeypatch):
    for k, v in CLAIM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    for i in range(60):
        assert actions._open_claim_treatment(game(gid=f"hash-{i}")) is not None


def test_unknown_horizon_buyer_keeps_opening_but_loses_the_floor(monkeypatch):
    """Round 99 is odd, so the seller owns the terminal node. A buyer holding a
    floor in an unbounded game closed 42% against 94%."""
    for k, v in CLAIM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    opening, floor = actions._open_claim_treatment(
        game(seller=False, hk=False, mr=None, my=150.0, their=80.0))
    assert opening == pytest.approx(0.95)
    assert floor == 0.0


@pytest.mark.parametrize("seller,hk", [(True, False), (True, True), (False, True)])
def test_every_other_seat_keeps_its_floor(monkeypatch, seller, hk):
    for k, v in CLAIM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    my, their = (80.0, 150.0) if seller else (150.0, 80.0)
    opening, floor = actions._open_claim_treatment(
        game(seller=seller, hk=hk, mr=10 if hk else None, my=my, their=their))
    assert opening == pytest.approx(0.95)
    assert floor == pytest.approx(0.80)


def test_always_on_is_inert_without_a_claim_value(monkeypatch):
    monkeypatch.delenv("GLEE_NEGO_OPEN_CLAIM", raising=False)
    monkeypatch.delenv("GLEE_NEGO_CLAIM_FLOOR", raising=False)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    assert actions._open_claim_treatment(game()) is None


def test_hidden_information_never_treated(monkeypatch):
    for k, v in CLAIM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    g = game()
    g["game_state"]["complete_information"] = False
    assert actions._open_claim_treatment(g) is None


def test_always_on_moves_the_wire_price(monkeypatch):
    for k, v in CLAIM.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    g = game(seller=True, hk=False, mr=None, my=80.0, their=150.0)
    out = actions.coerce({"product_price": 100.0}, g)
    # opening claim 0.95 of a 70-wide zone -> 80 + 66.5 = 146.50
    assert out["product_price"] == pytest.approx(146.50)
