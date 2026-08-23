"""The buyer is scored on rank, not on money, and the two disagree at p*r <= 1.

Our buyer gate is money-EV: buy iff the posterior beats (price-u)/(v-u), i.e.
1/r when u=0. At p*r <= 1 an always-recommend seller leaves the posterior at the
prior exactly, so that gate refuses every purchase. But the competition scores
PERCENTILE. The rank-indifference threshold is

    q_rank = [F(S) - F(S+u-P)] / [F(S+v-P) - F(S+u-P)]

which is not (P-u)/(v-u). On fitted numbers for the text p=.5, r=1.2 cell
(F(-P)=.0284, F(0)=.4498, F(+.2P)=.8734) q_rank is 0.4987 against a money gate of
0.8333 -- 33 probability points stricter than the objective, and on the prior
alone rank says BUY where money says REFUSE.

The logs agree in shape: across 3,800 buyer games at p*r < 1 we score 0.4813 and
refuse outright in 75.8% of them (percentile 0.4651), while games where we bought
75-99% scored 0.7329. The mirror is the tell -- as SELLER in the same cell we
score 0.6505, our best cell anywhere, which is only possible because the buyers
facing us do buy. That evidence is observational and our buyer is adaptive, so it
is confounded by reverse causation; this arm randomises to settle it.

These tests pin the properties that make it safe to arm on a live agent.
"""
from __future__ import annotations

import os

import pytest

from glee_agent.strategies import persuasion as P


@pytest.fixture(autouse=True)
def _clean_env():
    saved = {k: v for k, v in os.environ.items() if k.startswith("GLEE_PERS_RANK_BUY")}
    for k in saved:
        del os.environ[k]
    yield
    os.environ.update(saved)


def _game(*, role="buyer", p=1 / 3, v=2_000_000.0, price=1_000_000.0,
          gid="g", rnd=1, history=None):
    me = "player_2" if role == "buyer" else "player_1"
    return {
        "game_id": gid, "game_family": "persuasion", "your_player": me,
        "phase": "decision",
        "valid_actions": {"type": "decision" if role == "buyer" else "message"},
        "game_state": {
            "player_1_role": "seller", "player_2_role": "buyer",
            "p": p, "v": v, "u": 0.0, "product_price": price,
            "round": rnd, "total_rounds": 20, "history": history or [],
        },
    }


# --- inert unless deliberately armed ----------------------------------------

def test_it_is_inert_with_no_flag_set():
    assert not any(P._rank_buy_arm(_game(gid="g%d" % i)) for i in range(300))


@pytest.mark.parametrize("bad", ["nan", "NaN", "inf", "-inf", "", "abc", "0", "-1", "  "])
def test_a_malformed_or_nonpositive_threshold_fails_closed(bad):
    """NaN comparisons are all False, so an unguarded check would arm on a typo."""
    os.environ["GLEE_PERS_RANK_BUY_AB"] = bad
    assert not any(P._rank_buy_arm(_game(gid="g%d" % i)) for i in range(200))


# --- scoping: it must not reach any cell we already win ---------------------

def test_it_never_fires_on_the_seller_seat():
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
    assert not any(P._rank_buy_arm(_game(role="seller", gid="g%d" % i))
                   for i in range(400))


def test_it_never_fires_above_the_threshold():
    """buyer p*r > 1 scores 0.5521 and buys 84% of rounds; keep the arm out."""
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
    assert not any(P._rank_buy_arm(_game(p=0.5, v=4_000_000.0, gid="g%d" % i))
                   for i in range(400))


def test_it_never_fires_when_the_cell_is_blind():
    """Without v there is no p*r to test, so the arm must abstain."""
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
    for missing in ({"v": 0.0}, {"product_price": 0.0}, {"p": 0.0}):
        g = _game(gid="g1")
        g["game_state"].update(missing)
        assert not P._rank_buy_arm(g)


def test_the_threshold_is_respected_exactly():
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "0.7"
    # p*r = 0.66 is inside; p*r = 0.99 is outside a 0.7 threshold
    inside = sum(P._rank_buy_arm(_game(p=0.33, v=2e6, gid="g%d" % i)) for i in range(400))
    outside = sum(P._rank_buy_arm(_game(p=0.33, v=3e6, gid="g%d" % i)) for i in range(400))
    assert inside > 0
    assert outside == 0


# --- randomisation ----------------------------------------------------------

def test_assignment_is_balanced_and_stable():
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
    treated = [P._rank_buy_arm(_game(gid="game-%d" % i)) for i in range(2000)]
    assert 0.45 < sum(treated) / len(treated) < 0.55
    # a game must never flip arm between rounds
    for i in range(200):
        g = "g%d" % i
        assert P.rank_buy_assignment(g) == P.rank_buy_assignment(g)


def test_a_missing_game_id_is_control_not_treatment():
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
    assert P.rank_buy_assignment("") is None
    assert P.rank_buy_assignment(None) is None
    assert not P._rank_buy_arm(_game(gid=""))


def test_the_salt_is_independent_of_the_selectivity_arms():
    """A shared salt would correlate the experiments and make neither readable."""
    agree = sum(1 for i in range(3000)
                if P.rank_buy_assignment("g%d" % i) == P.buyer_selectivity_assignment("g%d" % i))
    assert 0.45 < agree / 3000 < 0.55


# --- the real decision path -------------------------------------------------

def test_the_arm_is_one_directional_through_decide():
    """It may turn a refusal into a purchase; it must never do the reverse."""
    from glee_agent.config import Config
    os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
    cfg = Config.from_env()
    flipped = kept = 0
    for i in range(300):
        gid = "g%d" % i
        g = _game(gid=gid)
        os.environ.pop("GLEE_PERS_RANK_BUY_AB", None)
        base = P.decide(g, cfg)["decision"]
        os.environ["GLEE_PERS_RANK_BUY_AB"] = "1.0"
        armed = P.decide(g, cfg)["decision"]
        if base == "yes":
            assert armed == "yes", "the arm turned a purchase into a refusal"
            kept += 1
        elif armed == "yes":
            flipped += 1
    assert flipped > 0, "the arm never fired on the live decide() path"


def test_decide_is_unchanged_when_the_arm_is_off():
    from glee_agent.config import Config
    cfg = Config.from_env()
    before = [P.decide(_game(gid="g%d" % i), cfg)["decision"] for i in range(200)]
    after = [P.decide(_game(gid="g%d" % i), cfg)["decision"] for i in range(200)]
    assert before == after
    assert all(d in ("yes", "no") for d in before)
