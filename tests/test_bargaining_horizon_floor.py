"""Tests for the undisclosed horizon and the empirical offer floor.

Both exist to repair one measured failure: with ``delta_opp = 1.0`` the
alternating-offers equilibrium says the share we can secure is 0 whenever the
opponent holds the last word, so the solver proposed itself nothing (four live
games were agreed at exactly $0) and its acceptance threshold cleared every
offer including $0. Live, that cell returned 39.3% of the pot against 52.8%
everywhere else (n=58 vs 155).

The numbers asserted below are the ones the fix is argued from, so a change
that quietly moves them fails here rather than on the live server.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from glee_agent.config import Config
from glee_agent.strategies.bargaining import (
    _rounds_left,
    decide,
    plan,
    proposer_share,
)

MONEY = 1000.0


def game(phase="offer", *, me="player_1", rnd=1, max_rounds=12, horizon_known=True,
         delta_1=None, delta_2=None, history=None, last_offer=None, money=MONEY):
    state = {
        "game_family": "bargaining",
        "round": rnd,
        "horizon_known": horizon_known,
        "phase": phase,
        "current_player": me,
        "proposer": "player_1",
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


def their_offer(rnd, my_gain, me="player_1", money=MONEY):
    other = "player_2" if me == "player_1" else "player_1"
    return {f"{me}_gain": my_gain, f"{other}_gain": money - my_gain,
            "proposer": other, "round": rnd}


def my_share(action, me="player_1"):
    return action["alice_gain" if me == "player_1" else "bob_gain"] / MONEY


# --- (a) the undisclosed horizon is 99, not infinity ------------------------

def test_a_disclosed_horizon_counts_down_from_max_rounds():
    assert _rounds_left({"max_rounds": 12, "round": 1, "horizon_known": True}, 99) == (12, True)
    assert _rounds_left({"max_rounds": 12, "round": 12, "horizon_known": True}, 99) == (1, True)


def test_a_undisclosed_horizon_counts_down_from_the_real_cap():
    # A live game with horizon_known=false terminated no_deal/round_cap_reached
    # at round 99. It is not uncapped; it is a cap the server does not state.
    assert _rounds_left({"round": 1, "horizon_known": False}, 99) == (99, False)
    assert _rounds_left({"round": 99, "horizon_known": False}, 99) == (1, False)
    assert _rounds_left({"round": 140, "horizon_known": False}, 99) == (1, False)


def test_a_the_finite_recursion_does_not_by_itself_repair_delta_opp_1():
    # The whole reason (b) exists. At 99 rounds left the equilibrium share is
    # delta_me ** 49 -- still zero to three places for three of the four grid
    # values, which is exactly the measured defect.
    assert proposer_share(0.80, 1.0, 99) == pytest.approx(0.000, abs=5e-4)
    assert proposer_share(0.90, 1.0, 99) == pytest.approx(0.006, abs=5e-4)
    assert proposer_share(0.95, 1.0, 99) == pytest.approx(0.081, abs=5e-4)
    assert proposer_share(1.00, 1.0, 99) == pytest.approx(1.000, abs=5e-4)
    # and with an even number of rounds left the opponent holds the last word,
    # so it is exactly zero for every delta_me.
    for d in (0.80, 0.90, 0.95, 1.00):
        assert proposer_share(d, 1.0, 98) == 0.0


def test_a_the_endgame_rules_now_reach_an_undisclosed_game():
    # Round 99 of an undisclosed game is a final round: a rejection pays $0, so
    # any positive offer beats it. Modelled as infinite, this never fired and a
    # live game ground to the cap for 0-0.
    g = game("decision", rnd=99, horizon_known=False, delta_1=0.9, delta_2=0.9,
             last_offer=their_offer(99, 1.0))
    p = plan(g, Config())
    assert p["rounds_left"] == 1 and p["horizon_known"] is False
    assert decide(g, Config())["decision"] == "accept"


def test_a_disclosed_games_keep_their_concession_clock_off():
    # The inflation clock is what paces an undisclosed game; a 12-round cap
    # always binds first and the recursion already prices it.
    assert plan(game(rnd=1, delta_1=0.9, delta_2=0.9), Config())["effective_horizon"] is None
    assert plan(game(rnd=1, horizon_known=False, delta_1=0.9, delta_2=0.9),
                Config())["effective_horizon"] == 29


# --- (b) the empirical floor ------------------------------------------------

def test_b_the_solver_no_longer_proposes_itself_nothing():
    # Reproduces the four live $0 agreements: full SPE weight, delta_opp = 1.0.
    hardliner = replace(Config(), barg_spe_weight=1.0)
    for delta_me, max_rounds, known in ((0.95, 12, True), (1.0, 12, True),
                                        (0.95, None, False), (0.9, None, False)):
        g = game(rnd=1, max_rounds=max_rounds, horizon_known=known,
                 delta_1=delta_me, delta_2=1.0)
        assert my_share(decide(g, hardliner)) >= 0.499


def test_b_the_default_blend_no_longer_opens_at_17_percent():
    g = game(rnd=1, delta_1=0.9, delta_2=1.0)
    assert plan(g, Config())["spe_share"] == pytest.approx(0.0, abs=1e-9)
    # 0.65 * 0 + 0.35 * 0.5 = 0.175 was the pre-fix opening.
    assert my_share(decide(g, Config())) >= 0.499


def test_b_the_floor_is_a_floor_and_never_a_cap():
    # Where the equilibrium already asks for more, the floor must not pull it in.
    g = game(rnd=1, delta_1=1.0, delta_2=0.8)
    assert my_share(decide(g, Config())) > 0.6


def test_b_the_floor_is_switchable_for_an_ab_test():
    g = game(rnd=1, delta_1=0.9, delta_2=1.0)
    off = replace(Config(), barg_offer_floor=0.0)
    assert my_share(decide(g, off)) == pytest.approx(0.175, abs=1e-6)
    assert my_share(decide(g, Config())) >= 0.499


def test_b_the_acceptance_threshold_is_never_zero_in_the_degenerate_corner():
    # spe_continuation is exactly 0 here, which used to clear any offer at all.
    # Round 2, so player_2 proposed and player_1 responds; ten rounds follow,
    # an even number, so the opponent holds the last word and never discounts.
    g = game("decision", rnd=2, me="player_1", delta_1=0.9, delta_2=1.0,
             last_offer=their_offer(2, 0.05 * MONEY))
    p = plan(g, Config())
    assert p["delta_opp"] == 1.0
    assert p["continuation"] == 0.0                    # the equilibrium is degenerate
    assert p["realistic_continuation"] == pytest.approx(0.5 * MONEY * 0.9)
    assert decide(g, Config())["decision"] == "reject"


def test_b_agreeing_to_exactly_nothing_is_never_accepted_while_rounds_remain():
    # Five live games were settled at exactly $0. Rejecting cannot pay less.
    for known, cap, rnd in ((True, 12, 4), (False, None, 4), (False, None, 50)):
        g = game("decision", rnd=rnd, max_rounds=cap, horizon_known=known,
                 me="player_2", delta_1=1.0, delta_2=0.9,
                 history=[{"round": r, "proposer": "player_1",
                           "offer": their_offer(r, 0.0, me="player_2"),
                           "decision": "reject"} for r in range(1, rnd, 2)],
                 last_offer=their_offer(rnd, 0.0, me="player_2"))
        assert decide(g, Config())["decision"] == "reject"


def test_b_the_degenerate_ceiling_is_confined_to_delta_opp_1():
    # Same state, opponent discounts: the equilibrium is well posed and stands.
    g = game("decision", rnd=2, me="player_2", delta_1=0.95, delta_2=0.9,
             last_offer=their_offer(2, 0.30 * MONEY, me="player_2"))
    p = plan(g, Config())
    assert p["realistic_continuation"] == pytest.approx(p["continuation"])
    assert "ceiling" not in p["opponent_evidence"]


def test_b_a_close_ultimatum_still_beats_the_floor():
    # With two rounds left the last word is real and checkable, so the
    # equilibrium keeps the acceptance threshold rather than the field level.
    g = game("decision", rnd=11, me="player_1", delta_1=1.0, delta_2=1.0,
             last_offer=their_offer(11, 0.30 * MONEY))
    p = plan(g, Config())
    assert p["rounds_left"] == 2
    assert "ceiling" not in p["opponent_evidence"]


# --- the fix must not deadlock ---------------------------------------------

def test_the_floor_still_concedes_against_a_stonewalling_opponent():
    # The opponent repeats 20% for ten rounds of an undisclosed game. Holding at
    # the floor forever is how a game dies at the cap paying zero.
    hist = [{"round": r, "proposer": "player_2",
             "offer": their_offer(r, 0.20 * MONEY), "decision": "reject"}
            for r in range(2, 22, 2)]
    g = game(rnd=23, horizon_known=False, delta_1=0.9, delta_2=1.0, history=hist)
    assert my_share(decide(g, Config())) < 0.499
    d = game("decision", rnd=24, horizon_known=False, delta_1=0.9, delta_2=1.0,
             history=hist, last_offer=their_offer(24, 0.20 * MONEY))
    assert decide(d, Config())["decision"] == "accept"


def test_every_action_stays_legal_across_the_grid():
    for me in ("player_1", "player_2"):
        for known, cap in ((True, 12), (False, None)):
            for d_me in (0.8, 0.9, 0.95, 1.0):
                for d_opp in (0.8, 0.9, 0.95, 1.0, None):
                    d1, d2 = (d_me, d_opp) if me == "player_1" else (d_opp, d_me)
                    for rnd in (1, 2, 11, 12, 98, 99, 100):
                        g = game(rnd=rnd, max_rounds=cap, horizon_known=known,
                                 delta_1=d1, delta_2=d2, me=me)
                        a = decide(g, Config())
                        assert a["alice_gain"] >= 0 and a["bob_gain"] >= 0
                        assert a["alice_gain"] + a["bob_gain"] == pytest.approx(MONEY)
                        d = game("decision", rnd=rnd, max_rounds=cap,
                                 horizon_known=known, delta_1=d1, delta_2=d2, me=me,
                                 last_offer=their_offer(rnd, 0.3 * MONEY, me=me))
                        assert decide(d, Config())["decision"] in ("accept", "reject")
