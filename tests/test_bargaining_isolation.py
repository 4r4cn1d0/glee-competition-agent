"""Proof that negotiation flags cannot move a single bargaining decision.

Test 2 holds the field's best bargaining rating and it is not ours to risk. This
file exists so that deploying negotiation policy onto that agent is backed by a
test rather than by an argument about module boundaries.
"""

from __future__ import annotations

import json

import pytest

from glee_agent import first_principles as fp, runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import bargaining

NEGO_FLAGS = {
    "GLEE_NEGO_FIRST_PRINCIPLES": "1",
    "GLEE_NEGO_FP_ALWAYS": "1",
    "GLEE_NEGO_OPEN_CLAIM": "0.95",
    "GLEE_NEGO_CLAIM_FLOOR": "0.80",
    "GLEE_NEGO_OPEN_CLAIM_ALWAYS": "1",
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB": "1",
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB": "1",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB": "1",
}


@pytest.fixture(autouse=True)
def _clear():
    runtime_flags._CACHE = None
    yield
    runtime_flags._CACHE = None


def barg_game(*, gid, rnd, me, money, my_val, rounds, offer=None, phase="offer"):
    them = "player_2" if me == "player_1" else "player_1"
    state = {
        "game_family": "bargaining", "round": rnd, "max_rounds": rounds,
        "horizon_known": True, "phase": "ongoing", "current_player": me,
        f"{me}_role": "alice" if me == "player_1" else "bob",
        f"{them}_role": "bob" if me == "player_1" else "alice",
        "money": money, f"{me}_discount": my_val, f"{them}_discount": 0.9,
        "complete_information": True, "messages_allowed": False, "history": [],
    }
    if offer is not None:
        state["last_offer"] = {"price": offer, "from_player": them, "round": rnd}
    return {"game_family": "bargaining", "game_id": gid, "your_player": me,
            "game_state": state, "valid_actions": {"type": phase}}


def battery():
    out = []
    i = 0
    for money in (100.0, 10000.0, 1000000.0):
        for rounds in (1, 5, 10, 12):
            for rnd in (1, 2, 3, rounds):
                for me in ("player_1", "player_2"):
                    for disc in (0.8, 0.9, 0.95):
                        for phase, offer in (("offer", None), ("decision", money * 0.4)):
                            i += 1
                            out.append(barg_game(gid=f"b{i}", rnd=rnd, me=me, money=money,
                                                 my_val=disc, rounds=rounds,
                                                 offer=offer, phase=phase))
    return out


def _decide_all(games):
    return [json.dumps(bargaining.decide(g, Config()), sort_keys=True, default=str)
            for g in games]


def test_negotiation_flags_do_not_move_any_bargaining_decision(monkeypatch):
    games = battery()
    assert len(games) > 500, "battery too small to be evidence"

    for k in NEGO_FLAGS:
        monkeypatch.delenv(k, raising=False)
    runtime_flags._CACHE = None
    off = _decide_all(games)

    for k, v in NEGO_FLAGS.items():
        monkeypatch.setenv(k, v)
    runtime_flags._CACHE = None
    on = _decide_all(games)

    diffs = [i for i, (a, b) in enumerate(zip(off, on)) if a != b]
    assert not diffs, (
        f"{len(diffs)} of {len(games)} bargaining decisions changed when negotiation "
        f"flags were set; first at index {diffs[0]}:\n  off={off[diffs[0]]}\n  on={on[diffs[0]]}")


def test_first_principles_disowns_every_non_negotiation_family(monkeypatch):
    for k, v in NEGO_FLAGS.items():
        monkeypatch.setenv(k, v)
    for fam in ("bargaining", "persuasion", None, "", "negotiation_v2"):
        g = barg_game(gid="x", rnd=1, me="player_1", money=100.0, my_val=0.9, rounds=10)
        g["game_family"] = fam
        g["game_state"]["game_family"] = fam
        assert not fp.owns(g), f"first_principles claimed a {fam!r} game"
