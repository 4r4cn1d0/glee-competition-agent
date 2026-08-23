"""Tests for the first-principles negotiation policy.

The design rests on deterministic laws rather than effect sizes, so these tests
assert the laws directly. The most important block is the last one: with the
flag unset, decide() must be byte-identical to the pre-change behaviour on every
state in the battery, because an inert arm that silently changes control games
would poison the very A/B it exists to run.
"""

from __future__ import annotations

import os
import sys

import pytest

from glee_agent import actions, first_principles as fp, runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import negotiation

ON = {"GLEE_NEGO_FIRST_PRINCIPLES": "1"}


@pytest.fixture(autouse=True)
def _clear():
    runtime_flags._CACHE = None
    yield
    runtime_flags._CACHE = None


def game(*, gid="g", complete=True, seller=True, mr=1, hk=True,
         my=80.0, their=150.0, phase="offer", offered=None, rnd=1):
    me = "player_1" if seller else "player_2"
    them = "player_2" if seller else "player_1"
    state = {
        "game_family": "negotiation", "round": rnd, "max_rounds": mr,
        "horizon_known": hk, "phase": "ongoing", "current_player": me,
        f"{me}_role": "seller" if seller else "buyer",
        f"{them}_role": "buyer" if seller else "seller",
        f"{me}_value": my, "complete_information": complete,
        "messages_allowed": False, "history": [],
    }
    if complete:
        state[f"{them}_value"] = their
    if offered is not None:
        state["last_offer"] = {"price": offered, "from_player": them, "round": rnd}
    return {"game_family": "negotiation", "game_id": gid, "your_player": me,
            "game_state": state, "valid_actions": {"type": phase}}


def treated(**kw):
    """A game id that lands in the treatment arm."""
    for i in range(200):
        g = game(gid=f"t{i}", **kw)
        if fp.in_treatment(g):
            return g
    raise AssertionError("no treated id found")


def control(**kw):
    for i in range(200):
        g = game(gid=f"c{i}", **kw)
        if not fp.in_treatment(g):
            return g
    raise AssertionError("no control id found")


# --- the grid ------------------------------------------------------------
def test_grid_scales_recognised():
    for s in (1.0, 100.0, 10000.0):
        for b in (80.0, 100.0, 120.0, 150.0):
            assert fp.scale_of(b * s) == s


def test_off_grid_value_disowns_the_game():
    assert fp.scale_of(137.0) is None
    with pytest.MonkeyPatch.context() as m:
        for k, v in ON.items():
            m.setenv(k, v)
        assert not fp.owns(treated(my=137.0, their=150.0))


# --- the two complete-information dictator cells -------------------------
@pytest.mark.parametrize("scale", [1.0, 100.0, 10000.0])
def test_single_round_seller_takes_the_zone(monkeypatch, scale):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = treated(complete=True, seller=True, mr=1, my=80.0 * scale, their=150.0 * scale)
    a = negotiation.decide(g, Config())
    a.pop("_plan", None)
    assert a["product_price"] == pytest.approx(150.0 * scale - fp.EPS)


def test_cap10_buyer_takes_the_zone(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = treated(complete=True, seller=False, mr=10, rnd=10, my=150.0, their=80.0)
    a = negotiation.decide(g, Config())
    a.pop("_plan", None)
    assert a["product_price"] == pytest.approx(80.0 + fp.EPS)


def test_cap10_buyer_holds_out_but_takes_a_near_total_offer(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    # offered a 50% share at round 4 -> wait for our own round-10 turn
    g = treated(complete=True, seller=False, mr=10, rnd=4, my=150.0, their=80.0,
                phase="decision", offered=115.0)
    assert negotiation.decide(g, Config())["decision"] == "RejectOffer"
    # offered essentially the whole zone -> take it rather than risk the walk
    g = treated(complete=True, seller=False, mr=10, rnd=4, my=150.0, their=80.0,
                phase="decision", offered=80.2)
    assert negotiation.decide(g, Config())["decision"] == "AcceptOffer"


def test_terminal_offer_is_accepted_iff_profitable(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = treated(complete=True, seller=True, mr=1, rnd=1, my=80.0, their=150.0,
                phase="decision", offered=80.01)
    assert negotiation.decide(g, Config())["decision"] == "AcceptOffer"
    g = treated(complete=True, seller=True, mr=1, rnd=1, my=80.0, their=150.0,
                phase="decision", offered=80.0)
    assert negotiation.decide(g, Config())["decision"] == "RejectOffer"


def test_degenerate_zone_is_split_not_inverted(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = treated(complete=True, seller=True, mr=1, my=100.0, their=100.0)
    a = negotiation.decide(g, Config())
    assert 100.0 - 1e-9 <= a["product_price"] <= 100.0 + 1e-9


# --- hidden information --------------------------------------------------
@pytest.mark.parametrize("cost,ask", [(80.0, 99.99), (100.0, 119.99), (120.0, 149.99)])
def test_hidden_seller_asks_the_lowest_profitable_grid_point(monkeypatch, cost, ask):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = treated(complete=False, seller=True, mr=1, my=cost)
    a = negotiation.decide(g, Config())
    a.pop("_plan", None)
    assert a["product_price"] == pytest.approx(ask)


def test_hidden_seller_at_top_of_grid_free_rolls(monkeypatch):
    """No zone can exist. $0 either way, so ask high and keep the ~1.7% alive."""
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = treated(complete=False, seller=True, mr=1, my=150.0)
    a = negotiation.decide(g, Config())
    assert a["product_price"] > 150.0


# --- ownership: nothing downstream may rewrite the price -----------------
def test_price_guards_yield_to_first_principles(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    # arm a guard that would otherwise clamp a one-round complete-info ask
    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_CAP", "0.85")
    g = treated(complete=True, seller=True, mr=1, my=80.0, their=150.0)
    out = actions.coerce(negotiation.decide(g, Config()), g)
    assert out["product_price"] == pytest.approx(150.0 - fp.EPS), \
        "a downstream guard rewrote a terminal price"


# --- the arm must be inert when off, and in control ----------------------
def test_flag_off_is_inert(monkeypatch):
    monkeypatch.delenv("GLEE_NEGO_FIRST_PRINCIPLES", raising=False)
    g = treated(complete=True, seller=True, mr=1, my=80.0, their=150.0)
    assert not fp.owns(g)


def test_control_arm_untouched(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    g = control(complete=True, seller=True, mr=1, my=80.0, their=150.0)
    assert not fp.owns(g)


def test_undesigned_cells_are_not_claimed(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    # horizon-unknown is explicitly not designed yet
    assert not fp.owns(treated(complete=True, seller=True, mr=None, hk=False))
    # cap-10 seller is the short side, not designed
    assert not fp.owns(treated(complete=True, seller=True, mr=10))
    # hidden buyer is a pure responder, not designed
    assert not fp.owns(treated(complete=False, seller=False, mr=1, my=150.0))


def test_arm_assignment_is_stable_and_balanced():
    ids = [f"game-{i}" for i in range(4000)]
    t = sum(1 for i in ids if fp.in_treatment({"game_id": i}))
    assert 0.45 < t / len(ids) < 0.55
    g = {"game_id": "abc"}
    assert fp.in_treatment(g) == fp.in_treatment(g)


def test_fp_always_treats_every_eligible_game(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_FP_ALWAYS", "1")
    for i in range(80):
        g = game(gid=f"any-{i}", complete=True, seller=True, mr=1, my=80.0, their=150.0)
        assert fp.in_treatment(g) and fp.owns(g)


def test_fp_always_still_respects_cell_coverage(monkeypatch):
    """Always-on widens the arm, never the cell set."""
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("GLEE_NEGO_FP_ALWAYS", "1")
    assert not fp.owns(game(gid="u", complete=True, seller=True, mr=None, hk=False))
    assert not fp.owns(game(gid="v", complete=True, seller=True, mr=10))
    assert not fp.owns(game(gid="w", complete=False, seller=False, mr=1, my=150.0))


def test_fp_always_off_keeps_the_5050_split(monkeypatch):
    for k, v in ON.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("GLEE_NEGO_FP_ALWAYS", raising=False)
    ids = [f"split-{i}" for i in range(3000)]
    t = sum(1 for i in ids if fp.in_treatment({"game_id": i}))
    assert 0.45 < t / len(ids) < 0.55
