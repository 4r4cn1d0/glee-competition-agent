"""Tests for the responder-seat (Bob) offer rebuild, at decide() level.

Everything here goes through ``decide()`` on a constructed game state, because
that is the only surface the live agent has. A module-level check that
``barg_offer.best_ask`` returns a sensible number proves nothing about whether
the strategy calls it, calls it in the right seat, or lets it through the floors.

The first block is the one that matters most: with GLEE_BARG_BOB_OFFER unset,
``decide()`` must reproduce the PRE-CHANGE module's decision exactly, on every
state in the battery. The pre-change module is loaded from git (HEAD's copy of
glee_agent/strategies/bargaining.py) rather than hand-copied, so the comparison
cannot drift out of date.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.strategies import bargaining

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONEY = 1000.0
FLAG = "GLEE_BARG_BOB_OFFER"

#: The live composite arm this change is screened against.
LIVE_ARM = {"GLEE_BARG_OPPONENT_FLOOR": "0.39",
            "GLEE_BARG_OFFER_FLOOR": "0.57",
            "GLEE_BARG_ACCEPT_FLOOR": "0.50",
            "GLEE_BARG_FLOOR_GAIN": "0.05",
            "GLEE_BARG_STONEWALL": "3"}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in list(os.environ):
        if k.startswith(("GLEE_BARG", "GLEE_OPP", "GLEE_PROBE")):
            monkeypatch.delenv(k, raising=False)
    for k, v in LIVE_ARM.items():
        monkeypatch.setenv(k, v)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _baseline_module():
    """HEAD's glee_agent/strategies/bargaining.py, importable side by side."""
    src = subprocess.run(
        ["git", "-C", REPO, "show", "HEAD:glee_agent/strategies/bargaining.py"],
        capture_output=True, text=True, check=True).stdout
    fd, path = tempfile.mkstemp(suffix=".py", prefix="barg_head_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        # It is a package module ("from .. import runtime_flags"); rewrite the
        # two relative imports to absolute so it can load standalone.
        fh.write(src.replace("from .. import ", "from glee_agent import ")
                    .replace("from ..actions import ", "from glee_agent.actions import "))
    spec = importlib.util.spec_from_file_location("barg_head", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def game(phase="offer", *, me="player_2", rnd=2, max_rounds=12, horizon_known=True,
         delta_1=None, delta_2=None, history=None, last_offer=None, money=MONEY):
    state = {
        "game_family": "bargaining",
        "round": rnd,
        "horizon_known": horizon_known,
        "phase": phase,
        "current_player": me,
        "proposer": me,
        "money_to_divide": money,
        "complete_information": delta_1 is not None and delta_2 is not None,
        "messages_allowed": False,
        "history": history or [],
        "last_offer": last_offer,
    }
    if horizon_known:
        state["max_rounds"] = max_rounds
    if delta_1 is not None:
        state["delta_1"] = delta_1
    if delta_2 is not None:
        state["delta_2"] = delta_2
    return {"game_id": "t", "game_family": "bargaining", "your_player": me,
            "game_state": state,
            "valid_actions": {"type": "offer" if phase == "offer" else "decision"}}


def alice_offered(rnd, bob_gain, money=MONEY):
    """One history entry: Alice proposed, Bob rejected."""
    return {"round": rnd, "proposer": "player_1", "decision": "reject",
            "offer": {"player_1_gain": money - bob_gain, "player_2_gain": bob_gain,
                      "proposer": "player_1", "round": rnd}}


def battery():
    """Every state both arms are compared on."""
    out = []
    for d2 in (1.0, 0.95, 0.9, 0.8):
        for d1 in (1.0, 0.95, 0.9, 0.8):
            for hk, mr in ((True, 12), (False, None)):
                for rnd in (2, 4, 8, 11, 12):
                    if hk and rnd > mr:
                        continue
                    hist = [alice_offered(r, MONEY * 0.40)
                            for r in range(1, rnd, 2)]
                    # complete information: both deltas visible
                    out.append(game(rnd=rnd, max_rounds=mr, horizon_known=hk,
                                    delta_1=d1, delta_2=d2, history=hist))
                    # incomplete information: opponent's delta absent
                    g = game(rnd=rnd, max_rounds=mr, horizon_known=hk,
                             delta_2=d2, history=hist)
                    g["game_state"]["complete_information"] = False
                    out.append(g)
                    # the decision phase must be untouched by an offer-side flag
                    last = alice_offered(rnd, MONEY * 0.44)["offer"]
                    d = game("decision", rnd=rnd, max_rounds=mr, horizon_known=hk,
                             delta_1=d1, delta_2=d2, history=hist, last_offer=last)
                    out.append(d)
    # Alice's seat, which the flag must never touch
    for d1 in (1.0, 0.9, 0.8):
        out.append(game(me="player_1", rnd=3, delta_1=d1, delta_2=0.9,
                        history=[alice_offered(1, MONEY * 0.40)]))
    return out


def _act(mod, g, cfg):
    a = mod.decide(g, cfg)
    return {k: v for k, v in a.items() if k != "_plan"}


# --- (a) flag OFF is byte-identical to the pre-change module ----------------

def test_a_flag_off_reproduces_head_exactly():
    head = _baseline_module()
    cfg = Config.from_env()
    states = battery()
    assert len(states) > 200
    diffs = []
    for g in states:
        import copy
        a = _act(bargaining, copy.deepcopy(g), cfg)
        b = _act(head, copy.deepcopy(g), cfg)
        if a != b:
            diffs.append((g["game_state"], a, b))
    assert not diffs, f"{len(diffs)} of {len(states)} states differ with the flag unset"


def test_a_flag_off_leaves_no_diagnostic_behind():
    cfg = Config.from_env()
    for g in battery():
        p = bargaining.decide(g, cfg).get("_plan") or {}
        assert "bob_offer" not in p


# --- (b) flag ON changes Bob's offer, and only Bob's offer -----------------

def test_b_flag_changes_bobs_offer(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    cfg = Config.from_env()
    monkeypatch.delenv(FLAG)
    off = {}
    for i, g in enumerate(battery()):
        if g["valid_actions"]["type"] != "offer":
            continue
        off[i] = bargaining.decide(g, cfg)["bob_gain"]
    monkeypatch.setenv(FLAG, "1")
    changed = 0
    for i, g in enumerate(battery()):
        if g["valid_actions"]["type"] != "offer":
            continue
        if abs(bargaining.decide(g, cfg)["bob_gain"] - off[i]) > 1e-9:
            changed += 1
    assert changed >= 40, f"only {changed} offers moved; the gate is not firing"


def test_b_alices_offer_is_untouched(monkeypatch):
    cfg = Config.from_env()
    g = game(me="player_1", rnd=3, delta_1=0.9, delta_2=0.9,
             history=[alice_offered(1, MONEY * 0.40)])
    import copy
    before = bargaining.decide(copy.deepcopy(g), cfg)
    monkeypatch.setenv(FLAG, "1")
    after = bargaining.decide(copy.deepcopy(g), cfg)
    assert before["alice_gain"] == after["alice_gain"]
    assert "bob_offer" not in (after.get("_plan") or {})


def test_b_decision_phase_is_untouched(monkeypatch):
    cfg = Config.from_env()
    last = alice_offered(4, MONEY * 0.44)["offer"]
    g = game("decision", rnd=4, delta_1=0.9, delta_2=0.9, last_offer=last,
             history=[alice_offered(1, MONEY * 0.40), alice_offered(3, MONEY * 0.42)])
    import copy
    before = bargaining.decide(copy.deepcopy(g), cfg)["decision"]
    monkeypatch.setenv(FLAG, "1")
    after = bargaining.decide(copy.deepcopy(g), cfg)["decision"]
    assert before == after


# --- (c) the shape of the new behaviour ------------------------------------

def test_c_the_flag_only_ever_raises_the_ask(monkeypatch):
    """Shipped as a floor. The concession direction is unscreenable offline --
    the arena's cloned responders are delta-blind -- so it is not shipped."""
    cfg = Config.from_env()
    import copy
    lowered = []
    for g in battery():
        if g["valid_actions"]["type"] != "offer":
            continue
        monkeypatch.delenv(FLAG, raising=False)
        before = bargaining.decide(copy.deepcopy(g), cfg)["bob_gain"]
        monkeypatch.setenv(FLAG, "1")
        after = bargaining.decide(copy.deepcopy(g), cfg)["bob_gain"]
        if after < before - 1e-9:
            lowered.append((g["game_state"], before, after))
    assert not lowered, f"{len(lowered)} offers were LOWERED by the floor"


def test_c_it_stops_the_concession_schedule_crossing_the_atom(monkeypatch):
    """The undisclosed-horizon decay walks Bob's ask through the 0.50 atom --
    9.6% of the field's whole payoff distribution -- and the floor stops it."""
    cfg = Config.from_env()
    hist = [alice_offered(r, MONEY * 0.40) for r in range(1, 12, 2)]
    g = lambda: game(rnd=12, max_rounds=None, horizon_known=False,
                     delta_1=0.95, delta_2=0.95, history=hist)
    base = bargaining.decide(g(), cfg)["bob_gain"] / MONEY
    monkeypatch.setenv(FLAG, "1")
    lifted = bargaining.decide(g(), cfg)["bob_gain"] / MONEY
    assert base < 0.50 < lifted, (base, lifted)


def test_c_never_asks_less_than_is_already_on_the_table(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    cfg = Config.from_env()
    # Alice has already offered Bob 0.58 of the pot; proposing ourselves less
    # than that is dominated whatever the model says.
    hist = [alice_offered(1, MONEY * 0.58)]
    g = game(rnd=4, max_rounds=None, horizon_known=False,
             delta_1=0.8, delta_2=0.8, history=hist)
    assert bargaining.decide(g, cfg)["bob_gain"] >= MONEY * 0.58 - 1e-9


def test_c_shares_always_sum_to_the_pot(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    cfg = Config.from_env()
    for g in battery():
        if g["valid_actions"]["type"] != "offer":
            continue
        a = bargaining.decide(g, cfg)
        assert abs(a["alice_gain"] + a["bob_gain"] - MONEY) < 1e-6
        assert -1e-9 <= a["bob_gain"] <= MONEY + 1e-9


def test_c_endgame_rounds_are_left_to_the_ultimatum_rules(monkeypatch):
    cfg = Config.from_env()
    hist = [alice_offered(r, MONEY * 0.40) for r in range(1, 12, 2)]
    for rnd in (11, 12):
        g = game(rnd=rnd, delta_1=0.9, delta_2=0.9, history=hist)
        import copy
        before = bargaining.decide(copy.deepcopy(g), cfg)["bob_gain"]
        monkeypatch.setenv(FLAG, "1")
        after = bargaining.decide(copy.deepcopy(g), cfg)["bob_gain"]
        monkeypatch.delenv(FLAG)
        assert before == after, f"round {rnd} (rounds_left <= 2) must not move"


def test_c_weight_interpolates(monkeypatch):
    cfg = Config.from_env()
    hist = [alice_offered(1, MONEY * 0.40)]
    g = lambda: game(rnd=2, delta_1=0.9, delta_2=0.95, history=hist)
    base = bargaining.decide(g(), cfg)["bob_gain"]
    monkeypatch.setenv(FLAG, "1")
    full = bargaining.decide(g(), cfg)["bob_gain"]
    monkeypatch.setenv(FLAG, "0.5")
    half = bargaining.decide(g(), cfg)["bob_gain"]
    assert abs(half - (base + full) / 2.0) < 1e-6, (base, half, full)


def test_c_missing_model_file_is_a_no_op(monkeypatch):
    """An unreadable model must leave the agent playing exactly as before."""
    from glee_agent import barg_offer
    monkeypatch.setattr(barg_offer, "_PATH", "/nonexistent/barg_bob_offer.json")
    barg_offer._STATE.update(checked=0.0, mtime=None, doc=None)
    try:
        cfg = Config.from_env()
        hist = [alice_offered(1, MONEY * 0.40)]
        import copy
        g = game(rnd=2, delta_1=0.9, delta_2=0.95, history=hist)
        before = bargaining.decide(copy.deepcopy(g), cfg)["bob_gain"]
        monkeypatch.setenv(FLAG, "1")
        after = bargaining.decide(copy.deepcopy(g), cfg)["bob_gain"]
        assert before == after
    finally:
        barg_offer._STATE.update(checked=0.0, mtime=None, doc=None)
