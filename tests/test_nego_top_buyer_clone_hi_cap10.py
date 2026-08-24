from __future__ import annotations

import copy

from glee_agent import (top_buyer_clone, top_buyer_clone_hi_cap10 as scoped,
                        top_opus_buyer_clone)
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation


def _game(*, gid: str, complete=False, known=True, cap=10,
          role="buyer", family="negotiation", own=120.0,
          phase="decision", offer=149.0):
    me, other = "player_2", "player_1"
    state = {
        "round": 1,
        "complete_information": complete,
        "horizon_known": known,
        "messages_allowed": False,
        "current_player": me,
        f"{me}_role": role,
        f"{other}_role": "seller" if role == "buyer" else "buyer",
        f"{me}_value": own,
        "history": [],
    }
    if known:
        state["max_rounds"] = cap
    if complete:
        state[f"{other}_value"] = 80.0
    if phase == "decision":
        state["last_offer"] = {
            "price": offer,
            "from_player": other,
            "round": 1,
        }
    return {
        "game_id": gid,
        "game_family": family,
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": phase},
    }


def _gid(candidate: bool, prefix="scoped") -> str:
    for index in range(10_000):
        gid = f"{prefix}-{index}"
        if scoped.treatment_assignment(gid) is candidate:
            return gid
    raise AssertionError("no game id for requested arm")


def _clear_clone_flags(monkeypatch):
    for flag in (scoped.FLAG, *scoped.CONFLICTING_FLAGS):
        monkeypatch.delenv(flag, raising=False)


def test_new_salt_is_stable_balanced_and_distinct():
    ids = [f"g-{index}" for index in range(2_000)]
    bits = [scoped.treatment_assignment(gid) for gid in ids]
    assert bits == [scoped.treatment_assignment(gid) for gid in ids]
    assert 900 < sum(bits) < 1_100
    assert any(scoped.treatment_assignment(gid)
               != top_buyer_clone.treatment_assignment(gid) for gid in ids)
    assert scoped.treatment_assignment(None) is None
    assert scoped.treatment_assignment(123) is None


def test_scope_is_exactly_hidden_known_cap10_negotiation_buyers():
    gid = _gid(True)
    assert scoped.eligible(_game(gid=gid))
    assert scoped.eligible(_game(gid=gid, phase="offer"))
    assert not scoped.eligible(_game(gid=gid, complete=True))
    assert not scoped.eligible(_game(gid=gid, known=False))
    assert not scoped.eligible(_game(gid=gid, cap=1))
    assert not scoped.eligible(_game(gid=gid, cap=11))
    assert not scoped.eligible(_game(gid=gid, role="seller"))
    assert not scoped.eligible(_game(gid=gid, family="bargaining"))


def test_default_off_hash_control_and_conflicts_fail_closed(monkeypatch):
    _clear_clone_flags(monkeypatch)
    candidate = _game(gid=_gid(True))
    control = _game(gid=_gid(False))
    assert not scoped.owns(candidate)

    monkeypatch.setenv(scoped.FLAG, "1")
    assert scoped.owns(candidate)
    assert not scoped.owns(control)

    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    assert not scoped.owns(candidate)
    assert not top_buyer_clone.owns(candidate)

    monkeypatch.delenv("GLEE_NEGO_TOP_BUYER_CLONE_AB")
    monkeypatch.setenv("GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB", "1")
    assert not scoped.owns(candidate)
    assert not top_opus_buyer_clone.enabled()


def test_candidate_replays_frozen_path_and_is_trace_labelled(monkeypatch):
    _clear_clone_flags(monkeypatch)
    monkeypatch.setenv(scoped.FLAG, "1")
    game = _game(gid=_gid(True, "wire"), own=120.0)
    move = scoped.action(copy.deepcopy(game))
    assert move == {
        "decision": "RejectOffer",
        "product_price": 86.0,
        "_plan": {
            "source": scoped.PLAN_SOURCE,
            "target": 86.0,
            "accept_ceiling": 103.0,
            "own_mult": 1.2,
        },
    }

    raw = negotiation.decide(copy.deepcopy(game), Config.from_env())
    wire = coerce(raw, copy.deepcopy(game))
    assert raw["_plan"]["source"] == scoped.PLAN_SOURCE
    assert wire["product_price"] == 86.0


def test_hash_control_falls_through_byte_identically(monkeypatch):
    _clear_clone_flags(monkeypatch)
    game = _game(gid=_gid(False, "control"), own=120.0)
    before = negotiation.decide(copy.deepcopy(game), Config.from_env())
    monkeypatch.setenv(scoped.FLAG, "1")
    after = negotiation.decide(copy.deepcopy(game), Config.from_env())
    assert after == before
    assert (after.get("_plan") or {}).get("source") != scoped.PLAN_SOURCE
