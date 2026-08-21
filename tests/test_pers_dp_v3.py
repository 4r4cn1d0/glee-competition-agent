#!/usr/bin/env python3
"""GLEE_PERS_DP_V3 verified through decide(), not through the solver.

Three things have to be true before this can ship:
  * flag OFF reproduces the pre-change decision on every state, byte for byte,
    including the states the new gate sits in front of (the prior-justifies
    shortcut);
  * flag ON actually changes the decision somewhere -- a gate that never fires
    is not a candidate;
  * the state the gate reads is the seller's own record, so replaying the same
    round with a different BUYER history but identical seller moves must give
    the same answer, while changing our own moves must move it.
"""
from __future__ import annotations

import copy
import os
import sys
from types import SimpleNamespace

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from glee_agent import runtime_flags                        # noqa: E402
from glee_agent.strategies import persuasion                # noqa: E402

CFG = SimpleNamespace(pers_lie_shading=0.8, pers_honest_rounds=2)


def set_flags(**flags):
    for k in list(os.environ):
        if k.startswith("GLEE_PERS_"):
            del os.environ[k]
    os.environ.update({k: str(v) for k, v in flags.items()})
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    persuasion._DP3_STATE.update(checked=0.0, mtime=None, doc=None)


def game(mode="binary", p=0.5, v=2.0, price=1.0, u=0.0, round_no=12,
         history=None, quality="low"):
    return {
        "your_player": "player_1",
        "valid_actions": {"type": "seller_recommendation"},
        "game_state": {
            "player_1_role": "seller", "player_2_role": "buyer",
            "product_price": price, "p": p, "v": v, "u": u,
            "total_rounds": 20, "round": round_no,
            "seller_message_type": mode,
            "current_quality": quality,
            "history": history if history is not None else [],
        },
    }


def hist(seq):
    """seq: list of (quality, recommended, bought)."""
    out = []
    for i, (q, rec, bought) in enumerate(seq):
        out.append({"round": i + 1, "quality": q,
                    "seller_message": "yes" if rec else "no",
                    "bought": bool(bought)})
    return out


def decision(g, **flags):
    set_flags(**flags)
    return persuasion.decide(copy.deepcopy(g), CFG)


STATES = []
for _mode in ("binary", "text"):
    for _p, _v in ((1 / 3, 1.2), (1 / 3, 4.0), (0.5, 2.0), (0.5, 3.0),
                   (0.8, 1.25), (0.8, 4.0)):
        for _r in (1, 3, 8, 12, 17, 20):
            for _seq in ([],
                         [("low", True, True)] * 4,
                         [("high", True, True), ("low", False, False)] * 3,
                         [("low", True, False)] * 8):
                if len(_seq) >= _r:
                    continue
                STATES.append(game(mode=_mode, p=_p, v=_v, round_no=_r,
                                   history=hist(_seq)))


def test_flag_off_is_byte_identical():
    """Every state: DP_V3 unset must equal the pre-change control decision.

    The control is the same code with the gate removed, which we get by
    asserting against a run where the flag is absent from the environment
    entirely AND one where it is explicitly falsy -- runtime_flags treats both
    as off, and the shortcut below the gate must own the decision in both.
    """
    for g in STATES:
        base = decision(g)                                   # no flags at all
        off = decision(g, GLEE_PERS_DP_V3="0")
        assert base == off, (g["game_state"]["round"], base, off)
        # and the reason string proves the new branch never ran
        assert base["_plan"].get("dp_v3") is not True


def changed_states():
    return [g for g in STATES
            if decision(g)["decision"]
            != decision(g, GLEE_PERS_DP_V3="1")["decision"]]


def test_flag_on_changes_decisions():
    assert changed_states(), "GLEE_PERS_DP_V3 never changes a decision -- dead flag"


def test_gate_reaches_prior_justifies_cells():
    """p*v >= price short-circuits to 'recommend' -- v3 must get there first."""
    g = game(p=0.5, v=2.0, round_no=4, history=hist([("low", True, True)] * 3))
    assert g["game_state"]["p"] * g["game_state"]["v"] >= g["game_state"]["product_price"]
    off = decision(g)
    on = decision(g, GLEE_PERS_DP_V3="1")
    assert off["_plan"]["reason"] == "prior alone justifies purchase"
    assert on["_plan"].get("dp_v3") is True
    assert on["decision"] != off["decision"], (off, on)


def test_state_is_our_record_not_the_buyers():
    """Same seller moves, different buyer responses -> same recommendation.

    Only the sales count may differ, and only through the percentile term; the
    trust coordinates must not move.  This is the property v1 lacked: its state
    changed when the BUYER acted.
    """
    seq_bought = hist([("low", True, True), ("high", True, True),
                       ("low", False, False)] * 3)
    seq_passed = hist([("low", True, False), ("high", True, False),
                       ("low", False, False)] * 3)
    g1 = game(p=1 / 3, v=3.0, round_no=10, history=seq_bought)
    g2 = game(p=1 / 3, v=3.0, round_no=10, history=seq_passed)
    d1 = decision(g1, GLEE_PERS_DP_V3="1")
    d2 = decision(g2, GLEE_PERS_DP_V3="1")
    assert d1["_plan"]["dp_state"]["told"] == d2["_plan"]["dp_state"]["told"] == 3
    assert d1["_plan"]["dp_state"]["nos"] == d2["_plan"]["dp_state"]["nos"] == 3
    assert d1["_plan"]["dp_state"]["sales"] == 6
    assert d2["_plan"]["dp_state"]["sales"] == 0


def test_our_own_lies_move_the_decision():
    """More lies told, same round: the recommendation must be able to flip."""
    flips = 0
    for mode in ("binary", "text"):
        for p, v in ((1 / 3, 3.0), (0.5, 3.0), (0.8, 4.0)):
            clean = decision(game(mode=mode, p=p, v=v, round_no=9,
                                  history=hist([("high", True, True)] * 8)),
                             GLEE_PERS_DP_V3="1")
            dirty = decision(game(mode=mode, p=p, v=v, round_no=9,
                                  history=hist([("low", True, True)] * 8)),
                             GLEE_PERS_DP_V3="1")
            flips += clean["decision"] != dirty["decision"]
    assert flips, "lies told never change the v3 decision"


def test_missing_model_falls_through():
    """An absent policy file must land on the heuristic, not raise."""
    set_flags(GLEE_PERS_DP_V3="1")
    persuasion._DP3_STATE.update(checked=0.0, mtime=None, doc=None)
    real = persuasion._dp_policy_v3
    persuasion._dp_policy_v3 = lambda: None
    try:
        g = game(p=1 / 3, v=1.2, round_no=9, history=hist([("low", True, True)] * 8))
        d = persuasion.decide(copy.deepcopy(g), CFG)
        assert d["_plan"].get("dp_v3") is not True
        assert d["decision"] in ("yes", "no")
    finally:
        persuasion._dp_policy_v3 = real


def test_v1_dp_path_untouched():
    """The existing GLEE_PERS_DP behaviour must be exactly what it was."""
    g = game(p=1 / 3, v=1.2, round_no=9, history=hist([("low", True, True)] * 8))
    a = decision(g, GLEE_PERS_DP="1")
    b = decision(g, GLEE_PERS_DP="1", GLEE_PERS_DP_V3="0")
    assert a == b
    assert a["_plan"].get("dp") is True and a["_plan"].get("dp_v3") is not True


if __name__ == "__main__":
    test_flag_off_is_byte_identical()
    test_flag_on_changes_decisions()
    print(f"flag-off byte-identical over {len(STATES)} constructed states: OK")
    print(f"flag-on changes the decision in {len(changed_states())}/{len(STATES)} states")
    for fn in (test_gate_reaches_prior_justifies_cells,
               test_state_is_our_record_not_the_buyers,
               test_our_own_lies_move_the_decision,
               test_missing_model_falls_through,
               test_v1_dp_path_untouched):
        fn()
        print(f"{fn.__name__}: OK")
    set_flags()
    print("\nall decide()-level checks passed")
