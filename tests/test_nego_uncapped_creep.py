"""The uncapped planning clock must keep approaching without ever arriving.

Pinning `elapsed` at 0.85 in a game with no deadline did not slow the concession
walk, it stopped it: `concession = 0.85**2 = 0.7225` from the round the planning
horizon expires until the game dies, so `target` never moved again. Measured over
1,988 uncapped games carrying at least eight of our own offers, 84.5% contain a
run of five or more byte-identical prices, the median longest run is 38, and the
runs start at a median round of 11 -- exactly where the default horizon of 10
expires. Those games close 5.4% of the time and score 0.3667, against 87.4% and
0.6023 for uncapped games settled by round 10. In all 93 complete-information
games of the grinding cohort a zone of agreement existed, and our own frozen
price sat inside it in 91.4% of them.

NOT ARMED, AND THE DIAGNOSIS ABOVE IS LARGELY WRONG. A six-way adversarial
review measured that this walk owns our price on only 11.6-22.5% of late
uncapped turns; STALL_POLICY's park branch writes 62.4-69.2% of them and
overwrites `target` after the concession line, so the byte-identical runs are
stall_park re-emitting the previous price rather than a frozen clock. None of the
93 complete-information games cited above are reachable by this code (0 of 7,961
schedule-owned late turns are complete-information). Measured effect across three
independent routes: -0.027 to +0.0007 percentile. The paragraph above is kept
because it is what the runs actually look like, not because it identifies a cause.

These tests therefore pin what keeps the code SAFE ON DISK: inert by default,
monotone, continuous at the horizon, never a surrender, and fail-closed on a
malformed flag.
"""
from __future__ import annotations

import os

import pytest

from glee_agent.strategies import negotiation as N

FLOOR = N._UNCAPPED_FLOOR


@pytest.fixture(autouse=True)
def _clean_env():
    """No uncapped flag may leak in from the ambient environment."""
    saved = {k: v for k, v in os.environ.items() if k.startswith("GLEE_NEGO_UNCAPPED")}
    for k in saved:
        del os.environ[k]
    yield
    os.environ.update(saved)


def _elapsed(ceiling: float, half: float, rnd: int, horizon: int = 10) -> float:
    """The call-site arithmetic, kept in step with negotiation.plan()."""
    c = min(max(ceiling, FLOOR), 0.99)
    if c <= FLOOR:
        return FLOOR
    extra = max(0.0, rnd - horizon)
    return FLOOR + (c - FLOOR) * (extra / (extra + max(half, 1e-9)))


# --- inert by default -------------------------------------------------------

def test_the_default_is_byte_identical_to_the_clamp_it_replaces():
    assert N._uncapped_ceiling("any-game-id") == FLOOR
    for rnd in (10, 11, 20, 40, 400):
        assert _elapsed(N._uncapped_ceiling("g"), 10.0, rnd) == FLOOR


def test_a_ceiling_at_or_below_the_floor_cannot_move_the_clock():
    for ceiling in (0.0, 0.5, FLOOR):
        assert _elapsed(ceiling, 10.0, 50) == FLOOR


# --- the walk advances, and keeps advancing ---------------------------------

def test_the_walk_actually_moves_once_armed():
    before = _elapsed(FLOOR, 10.0, 30)
    after = _elapsed(0.97, 10.0, 30)
    assert after > before
    # the whole point: the round-30 offer differs from the round-11 offer
    assert _elapsed(0.97, 10.0, 30) > _elapsed(0.97, 10.0, 11)


def test_the_schedule_is_monotone_in_round():
    seq = [_elapsed(0.97, 10.0, r) for r in range(10, 120)]
    assert all(b >= a for a, b in zip(seq, seq[1:]))


def test_it_is_continuous_at_the_horizon():
    """No jump at the boundary: at the horizon itself we sit exactly on the floor."""
    assert _elapsed(0.97, 10.0, 10) == FLOOR
    assert _elapsed(0.97, 10.0, 9) == FLOOR          # extra clamps at 0


# --- but never surrenders (ENDGAME_V3 failure 2) ----------------------------

def test_it_never_reaches_full_capitulation():
    """Failure 2 was full-value bids by round 12; the ceiling must bar that."""
    for rnd in (50, 500, 10_000):
        assert _elapsed(0.97, 10.0, rnd) < 1.0
        assert _elapsed(0.97, 10.0, rnd) ** 2 < 1.0


def test_an_absurd_ceiling_is_capped_below_one():
    assert _elapsed(99.0, 10.0, 10_000) <= 0.99
    assert _elapsed(99.0, 10.0, 10_000) ** 2 < 1.0


# --- randomised assignment --------------------------------------------------

def test_assignment_is_balanced_stable_and_hash_derived():
    os.environ["GLEE_NEGO_UNCAPPED_AB"] = "0.97"
    treated = [N._uncapped_ceiling("game-%d" % i) > FLOOR for i in range(2000)]
    assert 0.45 < sum(treated) / len(treated) < 0.55
    # stable: the same game must never flip arm mid-game
    assert all(N._uncapped_ceiling("g%d" % i) == N._uncapped_ceiling("g%d" % i)
               for i in range(200))


def test_a_missing_game_id_falls_back_to_control_not_treatment():
    os.environ["GLEE_NEGO_UNCAPPED_AB"] = "0.97"
    assert N._uncapped_ceiling("") == FLOOR
    assert N._uncapped_ceiling(None) == FLOOR


def test_the_ab_salt_is_independent_of_the_other_negotiation_arms():
    """Sharing a salt would correlate arms and confound both experiments."""
    os.environ["GLEE_NEGO_UNCAPPED_AB"] = "0.97"
    os.environ["GLEE_NEGO_ZOPA_AB"] = "0.10"
    agree = sum(1 for i in range(2000)
                if (N._uncapped_ceiling("g%d" % i) > FLOOR)
                == (N._zopa_share("g%d" % i, 0.39) == 0.10))
    assert 0.45 < agree / 2000 < 0.55


def test_the_plain_flag_still_works_without_the_ab():
    os.environ["GLEE_NEGO_UNCAPPED_CEILING"] = "0.95"
    assert N._uncapped_ceiling("g") == pytest.approx(0.95)


def test_the_ab_overrides_the_plain_flag_only_on_the_treated_half():
    os.environ["GLEE_NEGO_UNCAPPED_CEILING"] = "0.90"
    os.environ["GLEE_NEGO_UNCAPPED_AB"] = "0.97"
    seen = {round(N._uncapped_ceiling("g%d" % i), 6) for i in range(500)}
    assert seen == {0.90, 0.97}


# --- a malformed flag must fail CLOSED, not open ----------------------------
#
# min/max propagate NaN and every NaN comparison is False, so an unguarded 'nan'
# skipped the inert branch, carried NaN through target, and reached
# actions.coerce -- which sanitised it into a $0.00 offer. Found by adversarial
# review, not by the tests above, which is exactly why the tests below call the
# real code instead of a copy of the arithmetic.

@pytest.mark.parametrize("bad", ["nan", "NaN", "inf", "-inf", "", "abc", "  "])
def test_a_malformed_ceiling_falls_back_to_the_floor(bad):
    os.environ["GLEE_NEGO_UNCAPPED_CEILING"] = bad
    got = N._uncapped_ceiling("g")
    assert got == FLOOR, "%r produced %r, which is not the inert floor" % (bad, got)


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "abc"])
def test_a_malformed_ab_cannot_arm_the_treatment(bad):
    os.environ["GLEE_NEGO_UNCAPPED_AB"] = bad
    assert all(N._uncapped_ceiling("g%d" % i) == FLOOR for i in range(50))


# --- the real code path, not a reimplementation of it -----------------------

def _uncapped_game(gid="creep-probe", rnd=40, own_value=80.0):
    """A hidden-information uncapped seller state past the planning horizon."""
    return {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_1",
        "phase": "offer",
        "valid_actions": {"type": "offer"},
        "game_state": {
            "round": rnd,
            "max_rounds": None,
            "horizon_known": False,
            "complete_information": False,
            "current_player": "player_1",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_1_value": own_value,
            "history": [],
            "last_offer": None,
            "messages_allowed": False,
        },
    }


def _price(game):
    from glee_agent.config import Config
    return N.plan(game, Config.from_env()).get("target")


def test_plan_is_unchanged_by_default_on_a_real_uncapped_state():
    """The control fleet must be untouched: this calls plan(), not a copy."""
    baseline = _price(_uncapped_game(rnd=40))
    assert baseline is not None
    # same state, same answer, at every round past the horizon
    for rnd in (11, 25, 60):
        os.environ.pop("GLEE_NEGO_UNCAPPED_AB", None)
        assert _price(_uncapped_game(rnd=rnd)) == pytest.approx(baseline)


def test_a_nan_flag_cannot_produce_a_nan_price_through_plan():
    import math as _m
    os.environ["GLEE_NEGO_UNCAPPED_CEILING"] = "nan"
    got = _price(_uncapped_game(rnd=40))
    assert got is not None and _m.isfinite(got), "plan() emitted %r" % got
    os.environ.pop("GLEE_NEGO_UNCAPPED_CEILING", None)
    assert got == pytest.approx(_price(_uncapped_game(rnd=40)))
