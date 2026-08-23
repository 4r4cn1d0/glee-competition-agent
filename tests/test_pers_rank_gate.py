"""The buyer's money gate is the wrong bar in eight tight cells — but only in DP form.

Buy-iff-posterior-clears-(price-u)/(v-u) is money-optimal and rank-suboptimal:
the competition scores percentile, and the rank-indifference threshold

    q_rank = [F(S) - F(S+u-P)] / [F(S+v-P) - F(S+u-P)]

does not equal the money bar. That much was established earlier today. What was
NOT established, and what cost us a live arm, is that the one-shot formula above
is exact only in the LAST round. Applied as a standing rule it is rank-negative
in every p*r <= 1 cell: buy-iff-recommended at q=0.50 scores 0.056 against 0.4498
for refusing, because the effective 20-round threshold is 0.80-0.85 -- back at the
money gate. The gap survives only when the threshold is computed with the
continuation intact, which is what _rank_dp does.

Measured on the shipped CDF, at a third of the way through a 20-round game:

    text|0.33|1.2    money 0.833   rank 0.510   gap +0.324
    text|0.5|1.25    money 0.800   rank 0.555   gap +0.245
    text|0.8|1.25    money 0.800   rank 0.817   gap -0.017   (no gap)

Eight of the twelve tight buyer cells carry a material gap; the four p=0.8 cells
do not, and the gate correctly leaves those alone.

SAFETY. `tight` means breakeven >= 0.75, i.e. r <= 1.333. On the live
(1.2, 1.25, 2, 3, 4) x (1/3, 0.5, 0.8) grid, {tight} and {p*r > 1} are DISJOINT,
so this cannot reach buyer p*r>1 (0.5521); being buyer-only it cannot reach
seller p*r<1 (0.6505). Those two cells are the ones we already win. The `tight`
guard is the entire safety argument and must not be relaxed.
"""
from __future__ import annotations

import os

import pytest

from glee_agent.strategies import persuasion as P
from sim.percentile import _load


@pytest.fixture(autouse=True)
def _clean_env():
    saved = {k: v for k, v in os.environ.items()
             if k.startswith("GLEE_PERS_RANK_GATE") or k == "GLEE_PERS_BUYER_V2"}
    for k in saved:
        del os.environ[k]
    # The gate lives in buyer_plan_v2, which is what the live fleet runs.
    os.environ["GLEE_PERS_BUYER_V2"] = "1"
    P._RANK_DP_CACHE.clear()
    yield
    os.environ.pop("GLEE_PERS_BUYER_V2", None)
    os.environ.update(saved)
    P._RANK_DP_CACHE.clear()


def _samples(key="persuasion|text|0.33|1.2|buyer|20"):
    s = _load().get(key)
    if not s:
        pytest.skip("cell %s absent from the shipped CDF" % key)
    return s


# --- the DP itself ----------------------------------------------------------

def test_the_gap_is_real_in_the_low_prior_tight_cells():
    """Where the spec says buy more, the threshold must be materially below money.

    q_hat is NOT free: the code derives it as min(1, p/m_hat), and the threshold
    is very sensitive to it -- at p=0.33 an inconsistent q_hat=0.9 gives 0.883
    (above the money gate) where the consistent 0.37 gives 0.510. Any test or
    analysis that picks the two independently is measuring a state the agent can
    never actually be in.
    """
    for key, p in (("persuasion|text|0.33|1.2|buyer|20", 1 / 3),
                   ("persuasion|text|0.5|1.25|buyer|20", 0.5)):
        s = _load().get(key)
        if not s:
            continue
        ratio = float(key.split("|")[3])
        v, price = 100.0 * ratio, 100.0
        breakeven = price / v
        m = 0.9
        q = min(1.0, p / m)
        thr = P._q_rank_threshold(s, 7, 20, 0, 0, v, 0.0, price, m, q)
        assert thr is not None
        assert thr < breakeven - 0.10, "%s: rank %.3f vs money %.3f" % (key, thr, breakeven)


def test_the_high_prior_cells_show_no_gap_and_are_left_alone():
    """p=0.8 tight cells: rank and money agree, so the gate must not loosen."""
    key = "persuasion|text|0.8|1.25|buyer|20"
    s = _load().get(key)
    if not s:
        pytest.skip("cell absent")
    thr = P._q_rank_threshold(s, 7, 20, 0, 0, 125.0, 0.0, 100.0, 0.9, 0.9)
    assert thr is not None
    assert thr > 0.75, "expected no material loosening, got %.3f" % thr


def test_at_the_horizon_the_dp_collapses_to_the_one_shot_formula():
    """At t=T there is no continuation, so V(t+1) is the terminal layer."""
    s = _samples()
    thr = P._q_rank_threshold(s, 20, 20, 0, 0, 120.0, 0.0, 100.0, 0.9, 0.9)
    F = lambda x: P._midrank(s, x)
    hold, win, lose = F(0.0), F((120.0 - 100.0) / (100.0 * 20)), F(-100.0 / (100.0 * 20))
    expected = (hold - lose) / (win - lose)
    assert thr == pytest.approx(expected, abs=1e-9)


def test_the_threshold_is_a_probability():
    s = _samples()
    for t in range(1, 21):
        for a, b in ((0, 0), (3, 1), (0, 4)):
            thr = P._q_rank_threshold(s, t, 20, a, b, 120.0, 0.0, 100.0, 0.9, 0.9)
            if thr is not None:
                assert -0.01 <= thr <= 1.01, "t=%d a=%d b=%d -> %r" % (t, a, b, thr)


def test_the_cache_returns_identical_values():
    s = _samples()
    a = P._q_rank_threshold(s, 5, 20, 1, 0, 120.0, 0.0, 100.0, 0.9, 0.9)
    b = P._q_rank_threshold(s, 5, 20, 1, 0, 120.0, 0.0, 100.0, 0.9, 0.9)
    assert a == b
    assert len(P._RANK_DP_CACHE) >= 1


# --- assignment -------------------------------------------------------------

def test_assignment_is_balanced_stable_and_independent():
    treated = [P.rank_gate_assignment("g%d" % i) for i in range(2000)]
    assert 0.45 < sum(treated) / len(treated) < 0.55
    assert all(P.rank_gate_assignment("g%d" % i) == P.rank_gate_assignment("g%d" % i)
               for i in range(200))
    # must not correlate with any other persuasion salt
    for other in (P.buyer_selectivity_assignment, P.rank_buy_assignment):
        agree = sum(1 for i in range(2000)
                    if P.rank_gate_assignment("g%d" % i) == other("g%d" % i))
        assert 0.45 < agree / 2000 < 0.55


def test_a_missing_game_id_is_control():
    assert P.rank_gate_assignment("") is None
    assert P.rank_gate_assignment(None) is None


# --- the live decide() path -------------------------------------------------

def _game(*, p=1 / 3, ratio=1.2, gid="g", rnd=5, total=20, history=None,
          mode="text", msg="I recommend this one."):
    price = 100.0
    return {
        "game_id": gid, "game_family": "persuasion", "your_player": "player_2",
        "phase": "decision", "valid_actions": {"type": "decision"},
        "game_state": {
            "player_1_role": "seller", "player_2_role": "buyer",
            "p": p, "v": price * ratio, "u": 0.0, "product_price": price,
            "round": rnd, "total_rounds": total,
            "seller_message_type": mode, "seller_message": msg,
            "history": history or [],
        },
    }


def test_it_is_inert_with_no_flag_set():
    from glee_agent.config import Config
    cfg = Config.from_env()
    for i in range(60):
        out = P.decide(_game(gid="g%d" % i), cfg)
        assert not (out.get("_plan") or {}).get("rank_gate_arm")


def test_a_malformed_flag_fails_closed():
    from glee_agent.config import Config
    cfg = Config.from_env()
    for bad in ("nan", "inf", "-inf", "", "abc", "0", "-1"):
        os.environ["GLEE_PERS_RANK_GATE_AB"] = bad
        for i in range(20):
            out = P.decide(_game(gid="g%d" % i), cfg)
            assert not (out.get("_plan") or {}).get("rank_gate_arm"), bad


def test_it_never_fires_outside_tight_cells():
    """ratio 3.0 => breakeven 0.333, not tight, and p*r>1 -- must never fire."""
    from glee_agent.config import Config
    os.environ["GLEE_PERS_RANK_GATE_AB"] = "0.5"
    cfg = Config.from_env()
    for i in range(120):
        out = P.decide(_game(ratio=3.0, gid="g%d" % i), cfg)
        assert not (out.get("_plan") or {}).get("rank_gate_arm")


def test_it_never_fires_in_the_last_three_rounds():
    """The threshold bottoms out exactly where P(high|rec) collapses."""
    from glee_agent.config import Config
    os.environ["GLEE_PERS_RANK_GATE_AB"] = "0.5"
    cfg = Config.from_env()
    for rnd in (18, 19, 20):
        fired = any((P.decide(_game(gid="g%d" % i, rnd=rnd), cfg).get("_plan") or {})
                    .get("rank_gate_arm") for i in range(60))
        assert not fired, "fired at round %d of 20" % rnd


def test_it_does_fire_mid_game_on_the_treated_half():
    from glee_agent.config import Config
    os.environ["GLEE_PERS_RANK_GATE_AB"] = "0.5"
    cfg = Config.from_env()
    fired = sum(1 for i in range(200)
                if (P.decide(_game(gid="g%d" % i, rnd=6), cfg).get("_plan") or {})
                .get("rank_gate_arm"))
    assert fired > 0, "the gate never fired on the live decide() path"
    assert fired < 200, "the gate fired on every game; assignment is not splitting"


def test_the_control_half_is_bit_identical_to_the_flag_being_off():
    from glee_agent.config import Config
    cfg = Config.from_env()
    off = [P.decide(_game(gid="g%d" % i, rnd=6), cfg)["decision"] for i in range(200)]
    os.environ["GLEE_PERS_RANK_GATE_AB"] = "0.5"
    on = [P.decide(_game(gid="g%d" % i, rnd=6), cfg) for i in range(200)]
    for i, out in enumerate(on):
        if not (out.get("_plan") or {}).get("rank_gate_arm"):
            assert out["decision"] == off[i], "control game %d changed" % i
