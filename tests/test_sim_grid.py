"""Tests for the GLEE parameter grid sampler.

Four things must hold, and each one protects a different failure.

Reproducibility: a tuning run that cannot be replayed cannot be trusted, and
two strategies compared on different draws are not compared at all.

Shape: an engine reads ``Config.params`` to build ``game_state``, so a missing
or misnamed key surfaces as a simulator that diverges from the live server --
the exact failure the simulator exists to prevent. The expected key sets below
are transcribed from the documented ``game_state`` fields, so this test fails
if the grid ever drifts away from the API.

Coverage: the configurations that actually change the right play -- a
one-round take-it-or-leave-it, an undisclosed horizon, a seller who values the
item above the buyer -- must be *drawn*, not merely enumerable. A sampler that
can technically reach them but effectively never does tunes you for the middle
of the grid and leaves the corners untested.

CALIBRATION, which is new and is the point of this file: the sampler must draw
the distribution the LIVE SERVER draws, not a plausible-looking one. The
previous grid passed every test above while drawing 62.5% of negotiations with
no zone of agreement against the server's 45.5%, and that error silently
invalidated every offline sweep. The calibration tests below pin the marginals
to counts measured from ``logs/**/games/*.json`` (frozen in ``CORPUS`` so the
suite does not depend on live files), and one further test re-measures against
the live logs when they are present, so server drift shows up as a red test
rather than as a quietly wrong sweep.
"""

from __future__ import annotations

import collections
import glob
import json
import math
import os
import random

import pytest

from sim.grid import (
    BARGAINING_DELTAS,
    BARGAINING_HORIZONS,
    HORIZON_DISCLOSURE_CAP,
    MONEY_SCALES,
    NEGOTIATION_HORIZONS,
    NEGOTIATION_VALUE_CONDITIONS,
    NEGOTIATION_VALUE_FACTORS,
    NEGOTIATION_VALUE_PAIRS_COMPLETE,
    NEGOTIATION_VALUE_PAIRS_INCOMPLETE,
    PERSUASION_MESSAGE_TYPES,
    PERSUASION_PRIORS,
    PERSUASION_TOTAL_ROUNDS,
    PERSUASION_VALUE_FACTORS,
    all_configs,
    horizon_is_known,
    sample_config,
)

FAMILIES = ("bargaining", "negotiation", "persuasion")

# Transcribed from the "game_state fields" lists in docs/reference/glee-docs.md,
# keeping only the fields that are *configuration* -- the per-turn fields
# (phase, current_player, round, last_offer, history, ...) are the engine's to
# maintain, not the grid's to draw.
REQUIRED_KEYS = {
    "bargaining": {
        "money_to_divide", "delta_1", "delta_2", "horizon_known",
        "complete_information", "messages_allowed",
    },
    "negotiation": {
        "player_1_value", "player_2_value", "horizon_known",
        "complete_information", "messages_allowed",
    },
    "persuasion": {
        "product_price", "p", "v", "u", "total_rounds", "seller_message_type",
        "is_seller_know_cv",
    },
}

# `max_rounds` is the one field the docs describe as conditionally ABSENT:
# present with the cap when the deadline is disclosed, gone entirely when it is
# not. Absent, not None.
OPTIONAL_KEYS = {
    "bargaining": {"max_rounds"},
    "negotiation": {"max_rounds"},
    "persuasion": set(),
}


def check_keys(config):
    keys = set(config.params)
    family = config.game_family
    assert REQUIRED_KEYS[family] <= keys, REQUIRED_KEYS[family] - keys
    assert keys <= REQUIRED_KEYS[family] | OPTIONAL_KEYS[family], (
        keys - REQUIRED_KEYS[family] - OPTIONAL_KEYS[family])


# Bargaining and persuasion are the paper's grids, confirmed by the live
# corpus. Negotiation is 22 valuation/information points (not 4x4x2), which is
# what makes the three families sum to the documented 960.
EXPECTED_GRID_SIZE = {"bargaining": 384, "negotiation": 396, "persuasion": 180}
DOCUMENTED_TOTAL_COMBINATIONS = 960


def draws(game_family, n=3000, seed=20260819):
    rng = random.Random(seed)
    return [sample_config(game_family, rng) for _ in range(n)]


# --- reproducibility ------------------------------------------------------

@pytest.mark.parametrize("family", FAMILIES)
def test_same_seed_gives_the_same_sequence(family):
    first = draws(family, n=200, seed=99)
    second = draws(family, n=200, seed=99)
    assert [c.params for c in first] == [c.params for c in second]
    assert [c.key for c in first] == [c.key for c in second]


@pytest.mark.parametrize("family", FAMILIES)
def test_different_seeds_give_different_sequences(family):
    # Guards against a sampler that ignores rng entirely and looks reproducible.
    a = [c.key for c in draws(family, n=200, seed=1)]
    b = [c.key for c in draws(family, n=200, seed=2)]
    assert a != b


@pytest.mark.parametrize("family", FAMILIES)
def test_sampler_draws_only_from_the_rng_it_is_given(family):
    # Reaching for module-level `random` instead of the passed rng makes a run
    # depend on whatever else in the process touched the global state, which is
    # the classic way a "seeded" experiment turns out not to replay.
    rng = random.Random(11)
    expected = [sample_config(family, rng).params for _ in range(50)]

    rng = random.Random(11)
    actual = []
    for _ in range(50):
        random.random()            # noise from anywhere else in the process
        actual.append(sample_config(family, rng).params)
    assert actual == expected


@pytest.mark.parametrize("family", FAMILIES)
def test_each_draw_costs_a_fixed_number_of_rng_calls(family):
    """N configurations must consume exactly N times one configuration's state.

    A variable number of rng calls per draw -- a rejection loop, say -- makes
    two runs with the same seed diverge the moment one of them rejects, so
    "same seed, same configurations" quietly stops being true and two sweep
    arms stop being comparable. The negotiation ZOPA restriction is implemented
    as a single 22-point axis rather than as resampling precisely so this
    stays fixed.
    """
    one = random.Random(5)
    sample_config(family, one)
    after_one = one.getstate()

    stepwise = random.Random(5)
    sample_config(family, stepwise)
    assert stepwise.getstate() == after_one
    sample_config(family, stepwise)
    after_two = stepwise.getstate()

    many = random.Random(5)
    for _ in range(2):
        sample_config(family, many)
    assert many.getstate() == after_two


@pytest.mark.parametrize("family", FAMILIES)
def test_each_draw_owns_its_params_dict(family):
    rng = random.Random(3)
    first, second = sample_config(family, rng), sample_config(family, rng)
    first.params["injected"] = True
    assert "injected" not in second.params
    assert "injected" not in all_configs(family)[0].params


# --- shape ----------------------------------------------------------------

@pytest.mark.parametrize("family", FAMILIES)
def test_every_drawn_config_has_exactly_the_documented_keys(family):
    for config in draws(family, n=500):
        assert config.game_family == family
        check_keys(config)


@pytest.mark.parametrize("family", FAMILIES)
def test_every_enumerated_config_has_exactly_the_documented_keys(family):
    for config in all_configs(family):
        assert config.game_family == family
        check_keys(config)


@pytest.mark.parametrize("family", FAMILIES)
def test_no_param_is_none(family):
    # The docs say an unavailable field is missing from the dict, never present
    # and null -- a strategy doing `state.get("max_rounds")` must be able to
    # trust that None means absent.
    for config in all_configs(family):
        assert all(v is not None for v in config.params.values()), config.params


def test_bargaining_param_values():
    for config in draws("bargaining", n=500):
        p = config.params
        assert p["money_to_divide"] in MONEY_SCALES
        assert p["delta_1"] in BARGAINING_DELTAS
        assert p["delta_2"] in BARGAINING_DELTAS
        assert 0 < p["delta_1"] <= 1 and 0 < p["delta_2"] <= 1
        assert p.get("max_rounds") in (12, None)
        assert isinstance(p["complete_information"], bool)
        assert isinstance(p["messages_allowed"], bool)


def test_negotiation_param_values():
    valid = {float(round(m * f))
             for m in MONEY_SCALES for f in NEGOTIATION_VALUE_FACTORS}
    for config in draws("negotiation", n=500):
        p = config.params
        # Both valuations come from the same scale: a seller minimum of $80 is
        # never paired with a buyer maximum of $1,500,000.
        assert p["player_1_value"] in valid and p["player_2_value"] in valid
        assert p.get("max_rounds") in (1, 10, None)
        ratio = p["player_1_value"] / p["player_2_value"]
        assert any(abs(ratio - a / b) < 1e-9
                   for a in NEGOTIATION_VALUE_FACTORS
                   for b in NEGOTIATION_VALUE_FACTORS)


def test_persuasion_param_values():
    for config in draws("persuasion", n=500):
        p = config.params
        assert p["product_price"] in MONEY_SCALES
        assert p["p"] in PERSUASION_PRIORS
        assert 0 < p["p"] < 1
        assert p["total_rounds"] == PERSUASION_TOTAL_ROUNDS
        assert p["seller_message_type"] in PERSUASION_MESSAGE_TYPES
        assert isinstance(p["is_seller_know_cv"], bool)
        # The trade only makes sense if a good product beats the price and a
        # bad one does not; the docs fix the low value at $0.
        assert p["u"] == 0
        assert p["u"] < p["product_price"] < p["v"]
        assert p["v"] / p["product_price"] in PERSUASION_VALUE_FACTORS


def test_valuations_match_the_types_and_precision_the_server_sends():
    # The live server sends valuations as floats (`player_1_value: 80.0`,
    # `v: 12500.0`, `u: 0.0`) and round caps / prices / pots as ints. factor *
    # scale is a whole number at every grid point, so a fractional cent here
    # would be a bug, not a rounding fact of life.
    for config in all_configs("negotiation"):
        for key in ("player_1_value", "player_2_value"):
            value = config.params[key]
            assert isinstance(value, float) and value == round(value)
    for config in all_configs("persuasion"):
        for key in ("v", "u"):
            value = config.params[key]
            assert isinstance(value, float) and value == round(value)
        assert isinstance(config.params["product_price"], int)
        assert isinstance(config.params["total_rounds"], int)
    for config in all_configs("bargaining"):
        assert isinstance(config.params["money_to_divide"], int)


# --- the grid itself ------------------------------------------------------

@pytest.mark.parametrize("family", FAMILIES)
def test_grid_size_matches_the_live_grid(family):
    configs = all_configs(family)
    assert len(configs) == EXPECTED_GRID_SIZE[family]
    assert len({c.key for c in configs}) == len(configs), "duplicate config keys"


def test_the_three_families_sum_to_the_documented_960_combinations():
    # docs/reference/glee-docs.md: "drawn by the server from a grid of 960
    # combinations". This is the one number the organizers publish about the
    # grid, and it is the check that catches a family-level miscount -- the old
    # negotiation branch (576 points) missed it by 180.
    assert sum(len(all_configs(f)) for f in FAMILIES) == DOCUMENTED_TOTAL_COMBINATIONS


@pytest.mark.parametrize("family", FAMILIES)
def test_sampler_only_draws_points_that_are_on_the_grid(family):
    grid = {c.key for c in all_configs(family)}
    assert {c.key for c in draws(family)} <= grid


@pytest.mark.parametrize("family", FAMILIES)
def test_sampler_reaches_most_of_the_grid(family):
    # Uniform sampling over N points needs ~N ln N draws for full coverage;
    # 3,000 draws over 396 points should comfortably clear 90%.
    grid = all_configs(family)
    seen = {c.key for c in draws(family)}
    assert len(seen) > 0.9 * len(grid)


@pytest.mark.parametrize("family", FAMILIES)
def test_the_sampler_is_uniform_over_the_enumerated_grid(family):
    # The sampler and the enumerator share one axis definition, so this checks
    # the thing that definition is for: drawing a point is drawing uniformly
    # from `all_configs`. A rejection-sampling or reweighting implementation
    # would enumerate 396 negotiation points and then draw them 16:6 wrong.
    grid = [c.key for c in all_configs(family)]
    counts = collections.Counter(c.key for c in draws(family, n=40 * len(grid),
                                                      seed=4242))
    expected = 40.0
    chi2 = sum((counts.get(k, 0) - expected) ** 2 / expected for k in grid)
    df = len(grid) - 1
    # ~4.5 sigma of the chi2 null; a correct sampler fails this ~1 in 10^5 runs.
    assert chi2 < df + 4.5 * math.sqrt(2 * df), (chi2, df)


def test_unknown_family_is_rejected():
    with pytest.raises(ValueError):
        sample_config("chess", random.Random(0))
    with pytest.raises(ValueError):
        all_configs("chess")


def test_horizon_known_is_derived_from_the_cap():
    assert horizon_is_known(1) and horizon_is_known(HORIZON_DISCLOSURE_CAP)
    assert not horizon_is_known(HORIZON_DISCLOSURE_CAP + 1)
    assert not horizon_is_known(0)
    # GLEE draws a real cap for every game and simply declines to state the
    # long one; what reaches the players is a cap or nothing at all.
    assert all(not horizon_is_known(h) for h in BARGAINING_HORIZONS if h == 99)
    assert all(not horizon_is_known(h) for h in NEGOTIATION_HORIZONS if h == 99)
    for family in ("bargaining", "negotiation"):
        for config in all_configs(family):
            p = config.params
            assert p["horizon_known"] == ("max_rounds" in p), p
            if p["horizon_known"]:
                assert p["max_rounds"] <= HORIZON_DISCLOSURE_CAP


@pytest.mark.parametrize("family", ("bargaining", "negotiation"))
def test_uncapped_configs_omit_max_rounds_entirely(family):
    uncapped = [c for c in all_configs(family) if not c.params["horizon_known"]]
    assert uncapped
    for config in uncapped:
        assert "max_rounds" not in config.params


# --- the negotiation valuation structure ----------------------------------
#
# This is the block that would have caught the old bug. The live server ties
# the valuation pair to the information condition: complete information always
# has a strictly positive zone of agreement (143/143 observed games), while
# incomplete information draws the two factors independently and so produces
# no-ZOPA and zero-surplus configurations at their combinatorial rates.

def test_the_two_negotiation_value_supports_are_what_the_corpus_shows():
    assert NEGOTIATION_VALUE_PAIRS_COMPLETE == (
        (0.8, 1.0), (0.8, 1.2), (0.8, 1.5), (1.0, 1.2), (1.0, 1.5), (1.2, 1.5))
    assert len(NEGOTIATION_VALUE_PAIRS_INCOMPLETE) == 16
    assert set(NEGOTIATION_VALUE_PAIRS_COMPLETE) < set(
        NEGOTIATION_VALUE_PAIRS_INCOMPLETE)
    assert len(NEGOTIATION_VALUE_CONDITIONS) == 22


def test_complete_information_negotiations_always_have_a_zone_of_agreement():
    complete = [c for c in all_configs("negotiation")
                if c.params["complete_information"]]
    assert len(complete) == 6 * 3 * 3 * 2
    for config in complete:
        p = config.params
        assert p["player_1_value"] < p["player_2_value"], p
    # and the sampler agrees, not just the enumerator
    drawn = [c.params for c in draws("negotiation", n=5000)
             if c.params["complete_information"]]
    assert drawn
    assert all(p["player_1_value"] < p["player_2_value"] for p in drawn)


def test_incomplete_information_negotiations_reach_every_valuation_pair():
    seen = {(c.params["player_1_value"] / scale, c.params["player_2_value"] / scale)
            for c in all_configs("negotiation")
            if not c.params["complete_information"]
            for scale in MONEY_SCALES
            if c.params["player_1_value"] / scale in NEGOTIATION_VALUE_FACTORS}
    assert seen == set(NEGOTIATION_VALUE_PAIRS_INCOMPLETE)
    # The three regimes a negotiation strategy has to tell apart all occur,
    # and all three occur ONLY under incomplete information -- which is exactly
    # why a walk-away rule has to work without seeing the opponent's number.
    drawn = [c.params for c in draws("negotiation", n=5000)]
    kinds = collections.Counter(
        ("surplus" if p["player_1_value"] < p["player_2_value"] else
         "zero" if p["player_1_value"] == p["player_2_value"] else "none")
        for p in drawn if not p["complete_information"])
    assert kinds["surplus"] and kinds["zero"] and kinds["none"]


def test_the_probability_of_complete_information_is_six_over_twentytwo():
    # Not 1/2. Uniform sampling over grid POINTS with 6 complete-information
    # valuation pairs against 16 incomplete-information ones gives 0.273, and
    # the corpus measured 143/505 = 0.283 (95% CI [0.246, 0.324]).
    enumerated = [c for c in all_configs("negotiation")]
    share = sum(c.params["complete_information"] for c in enumerated) / len(enumerated)
    assert abs(share - 6 / 22) < 1e-12
    drawn = draws("negotiation", n=20000, seed=808)
    share = sum(c.params["complete_information"] for c in drawn) / len(drawn)
    assert abs(share - 6 / 22) < 0.015, share
    # bargaining, by contrast, really is a free 50/50 axis (254/499 measured)
    barg = draws("bargaining", n=20000, seed=808)
    assert abs(sum(c.params["complete_information"] for c in barg) / len(barg)
               - 0.5) < 0.015


def test_the_overall_zopa_rate_matches_the_live_corpus():
    # THE headline number. Old grid: 6/16 = 0.375 of negotiations had a strict
    # ZOPA. Live: P(CI) + (1 - P(CI)) * 6/16 = 0.545 at the structural 6/22,
    # measured 0.552 from the corpus.
    drawn = [c.params for c in draws("negotiation", n=20000, seed=1234)]
    zopa = sum(p["player_1_value"] < p["player_2_value"] for p in drawn) / len(drawn)
    expected = 6 / 22 + (16 / 22) * (6 / 16)
    assert abs(zopa - expected) < 0.02, zopa
    assert 0.50 < zopa < 0.60, zopa       # the corpus point estimate is 0.552
    assert zopa > 0.45                    # the old grid drew 0.375


# --- calibration against the live corpus ----------------------------------
#
# Counts measured on 2026-08-19 from logs/**/games/*.json, 1,630 games over
# five probes (549 bargaining, 540 negotiation, 541 persuasion). Regenerate with
# `.venv/bin/python analysis/fit_grid.py --emit`. Each entry is (axis label, {value: count}). Censored axes are
# recorded in the only frame where they are observable: the negotiation
# valuation pair under complete information, and the own-side valuation under
# incomplete information.

CORPUS = {
    "bargaining": {
        "money_to_divide": {100: 172, 10_000: 173, 1_000_000: 204},
        "horizon_known": {True: 289, False: 260},
        "complete_information": {True: 277, False: 272},
        "messages_allowed": {True: 270, False: 279},
        "delta_own": {0.8: 201, 0.9: 206, 0.95: 218, 1.0: 201},
    },
    "negotiation": {
        "complete_information": {True: 150, False: 390},
        "max_rounds_or_none": {1: 166, 10: 186, None: 188},
        "messages_allowed": {True: 249, False: 291},
        "seller_factor_incomplete": {0.8: 45, 1.0: 54, 1.2: 52, 1.5: 49},
        "buyer_factor_incomplete": {0.8: 58, 1.0: 48, 1.2: 41, 1.5: 43},
    },
    "persuasion": {
        "p": {1 / 3: 171, 0.5: 164, 0.8: 206},
        "value_factor": {1.2: 92, 1.25: 81, 2.0: 86, 3.0: 74, 4.0: 73},
        "product_price": {100: 169, 10_000: 203, 1_000_000: 169},
        "is_seller_know_cv": {True: 274, False: 267},
        "seller_message_type": {"text": 279, "binary": 262},
    },
}

# A correct grid fails a chi2 goodness-of-fit at this level about 1 run in
# 1,000 per axis. Anything the grid gets structurally wrong -- the old 0.5
# information rate, say -- lands many orders of magnitude below it.
CALIBRATION_ALPHA = 1e-3


def chi2_sf(x, df):
    """Upper tail of chi2 -- regularized Q(df/2, x/2), no scipy in this repo."""
    a, xx = df / 2.0, x / 2.0
    if xx <= 0:
        return 1.0
    if xx < a + 1:
        total = term = 1.0 / a
        for n in range(1, 10000):
            term *= xx / (a + n)
            total += term
            if abs(term) < abs(total) * 1e-14:
                break
        return 1.0 - total * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
    b, c, d = xx + 1 - a, 1e300, 1.0 / (xx + 1 - a)
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h


def goodness_of_fit(observed: dict, model: dict) -> tuple:
    """chi2 of a measured count table against the sampler's own probabilities."""
    keys = sorted(set(observed) | set(model), key=str)
    n = sum(observed.values())
    chi2 = 0.0
    for key in keys:
        expected = model.get(key, 0.0) * n
        if expected <= 0:
            # The sampler assigns zero probability to something the server
            # actually drew. That is a structural miss, not a tail event.
            if observed.get(key, 0):
                return float("inf"), len(keys) - 1
            continue
        chi2 += (observed.get(key, 0) - expected) ** 2 / expected
    return chi2, len(keys) - 1


def sampled_axes(family, n=5000, seed=31337):
    """The sampler's marginals, cut the same way the corpus can observe them."""
    configs = [c.params for c in draws(family, n=n, seed=seed)]
    out = collections.defaultdict(collections.Counter)
    for p in configs:
        if family == "bargaining":
            out["money_to_divide"][p["money_to_divide"]] += 1
            out["horizon_known"][p["horizon_known"]] += 1
            out["complete_information"][p["complete_information"]] += 1
            out["messages_allowed"][p["messages_allowed"]] += 1
            # "own delta" -- the corpus sees exactly one delta per incomplete
            # game and both per complete one, so pool both sides.
            out["delta_own"][p["delta_1"]] += 1
            out["delta_own"][p["delta_2"]] += 1
        elif family == "negotiation":
            out["complete_information"][p["complete_information"]] += 1
            out["max_rounds_or_none"][p.get("max_rounds")] += 1
            out["messages_allowed"][p["messages_allowed"]] += 1
            if not p["complete_information"]:
                scale = next(m for m in MONEY_SCALES
                             if p["player_1_value"] / m in NEGOTIATION_VALUE_FACTORS)
                out["seller_factor_incomplete"][round(p["player_1_value"] / scale, 3)] += 1
                out["buyer_factor_incomplete"][round(p["player_2_value"] / scale, 3)] += 1
        else:
            out["p"][p["p"]] += 1
            out["value_factor"][round(p["v"] / p["product_price"], 3)] += 1
            out["product_price"][p["product_price"]] += 1
            out["is_seller_know_cv"][p["is_seller_know_cv"]] += 1
            out["seller_message_type"][p["seller_message_type"]] += 1
    return {axis: {k: v / sum(c.values()) for k, v in c.items()}
            for axis, c in out.items()}


@pytest.mark.parametrize(
    "family,axis",
    [(f, a) for f in FAMILIES for a in CORPUS[f]],
    ids=[f"{f}-{a}" for f in FAMILIES for a in CORPUS[f]],
)
def test_sampled_marginal_matches_the_live_corpus(family, axis):
    model = sampled_axes(family)[axis]
    chi2, df = goodness_of_fit(CORPUS[family][axis], model)
    p = chi2_sf(chi2, df) if df > 0 else 1.0
    assert p > CALIBRATION_ALPHA, (
        f"{family}.{axis}: chi2={chi2:.2f} df={df} p={p:.2e}\n"
        f"  corpus  {CORPUS[family][axis]}\n"
        f"  sampler {({k: round(v, 4) for k, v in sorted(model.items(), key=str)})}")


def test_the_old_uniform_information_rate_would_fail_this_suite():
    # Proof the calibration test above has teeth: feed it the distribution the
    # OLD grid drew for negotiation's information condition and it must reject.
    chi2, df = goodness_of_fit(CORPUS["negotiation"]["complete_information"],
                               {True: 0.5, False: 0.5})
    assert chi2_sf(chi2, df) < 1e-15, chi2


def test_the_old_valuation_grid_would_fail_this_suite():
    # Same for the valuation pair: the old grid drew all 16 pairs under
    # complete information, which puts positive mass on seller > buyer. The
    # corpus has 143 complete-information games and zero such pairs.
    old_complete = {True: 10 / 16, False: 6 / 16}   # P(ZOPA) under the old draw
    observed = {True: 143, False: 0}
    chi2, df = goodness_of_fit(observed, old_complete)
    assert chi2_sf(chi2, df) < 1e-15, chi2


# --- calibration re-measured against the live logs, when they exist -------

LOG_GLOB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs", "**", "games", "*.json")
MIN_LIVE_GAMES = 200


def live_configs(family):
    out = []
    for path in glob.glob(LOG_GLOB, recursive=True):
        try:
            with open(path) as handle:
                game = json.load(handle)
        except (OSError, ValueError):
            continue        # a game the collector is mid-write on
        if game.get("game_family") == family and game.get("config"):
            out.append((game["config"], game.get("your_player")))
    return out


@pytest.mark.parametrize("family", FAMILIES)
def test_the_grid_still_matches_the_live_server(family):
    """Re-measure from logs/ rather than the frozen CORPUS table.

    This is the drift alarm. CORPUS is a snapshot; the server can change, and
    if it does, every offline sweep silently goes stale again. Skipped when the
    logs are absent (a fresh checkout) or too thin to say anything.
    """
    games = live_configs(family)
    if len(games) < MIN_LIVE_GAMES:
        pytest.skip(f"only {len(games)} live {family} games in logs/")

    counts = collections.defaultdict(collections.Counter)
    for config, seat in games:
        if family == "bargaining":
            counts["money_to_divide"][config["money_to_divide"]] += 1
            counts["horizon_known"][config["horizon_known"]] += 1
            counts["complete_information"][config["complete_information"]] += 1
            counts["messages_allowed"][config["messages_allowed"]] += 1
            for key in ("delta_1", "delta_2"):
                if key in config:
                    counts["delta_own"][config[key]] += 1
        elif family == "negotiation":
            counts["complete_information"][config["complete_information"]] += 1
            counts["max_rounds_or_none"][config.get("max_rounds")] += 1
            counts["messages_allowed"][config["messages_allowed"]] += 1
            if not config["complete_information"]:
                for key, axis in (("player_1_value", "seller_factor_incomplete"),
                                  ("player_2_value", "buyer_factor_incomplete")):
                    if key not in config:
                        continue
                    scale = next((m for m in MONEY_SCALES
                                  if round(config[key] / m, 3)
                                  in NEGOTIATION_VALUE_FACTORS), None)
                    if scale:
                        counts[axis][round(config[key] / scale, 3)] += 1
        else:
            counts["p"][config["p"]] += 1
            if "v" in config:
                counts["value_factor"][round(config["v"] / config["product_price"], 3)] += 1
            counts["product_price"][config["product_price"]] += 1
            counts["is_seller_know_cv"][config["is_seller_know_cv"]] += 1
            counts["seller_message_type"][config["seller_message_type"]] += 1

    model = sampled_axes(family)
    failures = []
    for axis, observed in counts.items():
        chi2, df = goodness_of_fit(dict(observed), model[axis])
        p = chi2_sf(chi2, df) if df > 0 else 1.0
        if p <= CALIBRATION_ALPHA:
            failures.append(f"{family}.{axis}: n={sum(observed.values())} "
                            f"chi2={chi2:.2f} df={df} p={p:.2e} "
                            f"live={dict(observed)} "
                            f"grid={ {k: round(v, 4) for k, v in model[axis].items()} }")
    assert not failures, "\n".join(failures)


def test_complete_information_negotiations_in_the_logs_all_have_a_zopa():
    """The single fact the old grid got wrong, checked against live games."""
    games = [c for c, _ in live_configs("negotiation")
             if "player_1_value" in c and "player_2_value" in c]
    if len(games) < 50:
        pytest.skip(f"only {len(games)} fully-observed live negotiations")
    assert all(c["complete_information"] for c in games)
    inverted = [c for c in games if c["player_1_value"] >= c["player_2_value"]]
    assert not inverted, (
        f"{len(inverted)} of {len(games)} complete-information negotiations have "
        f"no strict zone of agreement -- the grid's six-pair restriction is "
        f"no longer true and sim/grid.py must be refitted")


# --- the edge configurations that change the right play -------------------

def _reachable(family, predicate, n=3000):
    """Whether `predicate` holds for some enumerated config AND some drawn one."""
    enumerated = any(predicate(c.params) for c in all_configs(family))
    drawn = any(predicate(c.params) for c in draws(family, n=n))
    return enumerated, drawn


EDGE_CASES = [
    # Single-round take-it-or-leave-it: the responder has no counteroffer, so
    # anything above zero beats rejecting. Only negotiation has T = 1.
    ("negotiation", "take-it-or-leave-it",
     lambda p: p.get("max_rounds") == 1 and p["horizon_known"]),
    # Capped horizons, where backward induction is exact.
    ("bargaining", "capped horizon",
     lambda p: p["horizon_known"] and p["max_rounds"] > 1),
    ("negotiation", "capped horizon",
     lambda p: p["horizon_known"] and p["max_rounds"] > 1),
    # Uncapped: the deadline exists but is never disclosed, so an engine must
    # hide `max_rounds` and a strategy must not assume one.
    ("bargaining", "uncapped horizon",
     lambda p: not p["horizon_known"] and "max_rounds" not in p),
    ("negotiation", "uncapped horizon",
     lambda p: not p["horizon_known"] and "max_rounds" not in p),
    # Information conditions.
    ("bargaining", "complete information", lambda p: p["complete_information"]),
    ("bargaining", "incomplete information", lambda p: not p["complete_information"]),
    ("negotiation", "complete information", lambda p: p["complete_information"]),
    ("negotiation", "incomplete information", lambda p: not p["complete_information"]),
    ("persuasion", "seller knows buyer values", lambda p: p["is_seller_know_cv"]),
    ("persuasion", "seller blind to buyer values", lambda p: not p["is_seller_know_cv"]),
    # Communication channel on and off.
    ("bargaining", "messages allowed", lambda p: p["messages_allowed"]),
    ("bargaining", "messages forbidden", lambda p: not p["messages_allowed"]),
    ("negotiation", "messages allowed", lambda p: p["messages_allowed"]),
    ("negotiation", "messages forbidden", lambda p: not p["messages_allowed"]),
    # No gains from trade: the seller's minimum exceeds the buyer's maximum, so
    # every feasible price loses someone money and walking away is correct.
    # On the live server this happens ONLY under incomplete information, which
    # is what makes it hard: you cannot see that it is happening.
    ("negotiation", "no gains from trade",
     lambda p: p["player_1_value"] > p["player_2_value"]),
    ("negotiation", "gains from trade",
     lambda p: p["player_1_value"] < p["player_2_value"]),
    ("negotiation", "zero surplus",
     lambda p: p["player_1_value"] == p["player_2_value"]),
    ("negotiation", "no gains from trade, and you cannot see it",
     lambda p: p["player_1_value"] > p["player_2_value"]
     and not p["complete_information"]),
    # Persuasion in both message modes: "binary" removes language entirely and
    # leaves only a recommend/don't-recommend signal.
    ("persuasion", "text messages",
     lambda p: p["seller_message_type"] == "text"),
    ("persuasion", "binary recommendation",
     lambda p: p["seller_message_type"] == "binary"),
    # A prior below one half makes an unconditional recommendation worthless to
    # the buyer, which is where reputation has to do the work.
    ("persuasion", "minority of products are high quality", lambda p: p["p"] < 0.5),
    ("persuasion", "majority of products are high quality", lambda p: p["p"] > 0.5),
    # Both ends of the currency scale, since LLM opponents are not
    # scale-invariant even though the equilibrium is.
    ("bargaining", "smallest pot", lambda p: p["money_to_divide"] == min(MONEY_SCALES)),
    ("bargaining", "largest pot", lambda p: p["money_to_divide"] == max(MONEY_SCALES)),
    # A player who suffers no inflation can wait the other side out forever.
    ("bargaining", "one side immune to inflation",
     lambda p: (p["delta_1"] == 1.0) != (p["delta_2"] == 1.0)),
    ("bargaining", "both sides discounted",
     lambda p: p["delta_1"] < 1.0 and p["delta_2"] < 1.0),
]


@pytest.mark.parametrize(
    "family,name,predicate",
    EDGE_CASES,
    ids=[f"{fam}-{name}" for fam, name, _ in EDGE_CASES],
)
def test_edge_configuration_is_reachable(family, name, predicate):
    enumerated, drawn = _reachable(family, predicate)
    assert enumerated, f"{family}: {name} is not in the grid at all"
    assert drawn, f"{family}: {name} is in the grid but the sampler never draws it"


def test_the_hardest_negotiation_corner_is_reachable():
    # All three of the awkward features at once: one shot, no surplus to split,
    # and you cannot see the other side's valuation. A strategy that only works
    # when it can haggle fails exactly here.
    def predicate(p):
        return (p.get("max_rounds") == 1
                and p["player_1_value"] > p["player_2_value"]
                and not p["complete_information"])

    enumerated, drawn = _reachable("negotiation", predicate)
    assert enumerated and drawn


# --- the grid actually drives the engines ---------------------------------

@pytest.mark.parametrize("family", FAMILIES)
def test_every_grid_point_builds_an_engine(family):
    """The grid is only useful if the engines accept all of it.

    A configuration the engine rejects is a silent hole in the sweep: the
    arena skips it, tuning never sees that corner, and the first time the
    strategy meets it is in a live rated game. This is the test that catches a
    grid and an engine disagreeing about a field's convention.
    """
    from sim import make_engine

    for config in all_configs(family):
        engine = make_engine(config, random.Random(0), "grid-check")
        state = engine.observation(engine.current_player)["game_state"]
        # The horizon convention has to survive the round trip into the view a
        # strategy reads: told the deadline, or told nothing.
        if family != "persuasion":
            assert state["horizon_known"] == config.params["horizon_known"]
            if config.params["horizon_known"]:
                assert state["max_rounds"] == config.params["max_rounds"]
            else:
                assert "max_rounds" not in state
