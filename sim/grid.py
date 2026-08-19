"""The GLEE parameter grid -- the configuration space the server actually draws.

You never pick your own numbers: "each configuration is drawn by the server
from a grid of 960 combinations (horizons, sums, valuations, inflation rates,
information conditions), and you never choose yours -- so tuning to one game's
numbers doesn't transfer to the next." A knob tuned against one hand-picked
setting is therefore tuned against nothing. This module reproduces the draw so
a strategy is measured over the spread of configurations it will actually meet,
weighted the way it will meet them.

WHERE THE NUMBERS COME FROM
---------------------------
Every value set and every weight below is **measured from the live server**:
the ``config`` block of 1,521 completed games in ``logs/**/games/*.json``
(511 bargaining, 505 negotiation, 505 persuasion, plus a handful still in
flight), collected across five probes running different policies. The
reproduction is checked by ``analysis/verify_grid.py``, which draws 5,000
configurations per family and compares every marginal against the corpus.

The previous version of this module was built from the GLEE paper
(arXiv:2410.05254, Table 2) and the research dataset's ``config.json`` files.
That grid was wrong in one place, and the error was large: it drew the
negotiation valuation pair uniformly over all 16 (seller, buyer) combinations
in both information conditions, so 62.5% of negotiations had no strictly
positive zone of agreement. The live server's rate is 45.5%, and the whole of
the difference lives in the complete-information branch, which on the live
server has a strict ZOPA in 143 of 143 observed games. Any offline sweep run
against the old grid over-weighted "walk away" configurations by ~17
percentage points of the negotiation family.

WHAT THE CORPUS SAYS, FAMILY BY FAMILY
--------------------------------------
Bargaining -- unchanged from the paper grid; the corpus confirms it.
  * ``delta_1`` x ``delta_2`` is uniform over all 16 pairs of
    {0.8, 0.9, 0.95, 1.0}: chi2 = 10.65, df = 15, p = 0.78 (n = 259
    complete-information games, the only ones where both are visible).
    Own-delta marginals are uniform in BOTH information conditions, so there is
    no hidden restriction on the pair under incomplete information either.
  * ``money_to_divide`` uniform over {100, 10_000, 1_000_000}: chi2 = 2.96,
    df = 2, p = 0.23 (n = 499).
  * ``max_rounds`` uniform over {12, 99}: 261 / 245 (n = 506, p = 0.47).
  * ``complete_information`` 254/499 = 0.509; ``messages_allowed``
    249/499 = 0.499. Both Bernoulli(0.5).
  * All axes pairwise independent (largest chi2 = 1.74, df = 1).
  Grid: 4 x 4 x 3 x 2 x 2 x 2 = 384 points.

Negotiation -- this is what changed.
  * The valuation pair is drawn JOINTLY WITH the information condition:
      - complete information: uniform over the SIX strictly ordered pairs
        (seller factor < buyer factor). Measured directly, uncensored, on
        n = 143 games: all 143 are strictly ordered, 0 equal, 0 inverted;
        uniform over the six, chi2 = 1.13, df = 5, p = 0.95. The wider model
        "uniform over the ten pairs with seller <= buyer" is rejected at
        chi2 = 97.2, df = 9, p = 6e-17.
      - incomplete information: seller and buyer factors independent and
        uniform over all four values, so 16 pairs.
  * ``complete_information`` is therefore NOT a free 50/50 axis. Uniform
    sampling over grid POINTS makes it 6/22 = 0.2727. Measured:
    143/505 = 0.2832, 95% CI [0.2456, 0.3240] -- 6/22 sits at z = +0.53,
    while the old grid's 0.5 sits at z = -9.75 and is decisively refuted.
  * ``scale`` uniform over {100, 10_000, 1_000_000}: chi2 = 2.46, df = 2.
  * ``max_rounds`` uniform over {1, 10, 99}: 156 / 163 / 175 (n = 494).
  * ``messages_allowed`` Bernoulli(0.5): 260/489 = 0.532.
  * The valuation axis is independent of scale, horizon and messages
    (``complete_information`` x ``max_rounds`` chi2 = 0.55, df = 2;
    x ``messages_allowed`` chi2 = 0.06, df = 1; x ``scale`` chi2 = 3.75, df = 2).
  Grid: 22 x 3 x 3 x 2 = 396 points.

Persuasion -- unchanged; the corpus confirms it.
  * ``p`` uniform over {1/3, 0.5, 0.8}: 156 / 154 / 191 (n = 501, chi2 = 5.19,
    df = 2, p = 0.075 -- see ASSUMPTION 4).
  * ``v``/``product_price`` uniform over {1.2, 1.25, 2.0, 3.0, 4.0}:
    chi2 = 4.06, df = 4, p = 0.40 (n = 373 games where ``v`` is visible).
  * ``product_price`` uniform over the three scales; ``is_seller_know_cv`` and
    ``seller_message_type`` both 50/50; ``u`` is 0.0 in all 377 observations;
    ``total_rounds`` is 20 in all 505.
  * All axes pairwise independent (largest chi2 = 14.15, df = 8, p = 0.08).
  Grid: 3 x 5 x 3 x 2 x 2 = 180 points.

384 + 396 + 180 = 960 -- exactly the grid size the competition documents
state. The old module reproduced 384 + 576 + 180 = 1,140 and had to explain
the 960 away as a coincidence between two of the three families. The corrected
negotiation branch makes the documented number come out on the nose, which is
independent structural confirmation of both the six-pair restriction and of
ASSUMPTION 3 below.

CENSORING -- WHY THE NEGOTIATION JOINT HAD TO BE ESTIMATED
-----------------------------------------------------------
Under incomplete information the server sends you your own valuation and omits
the opponent's: of 505 negotiation games, 143 show both values (all complete
information), 189 show only ``player_1_value`` (we were the seller), 173 show
only ``player_2_value`` (we were the buyer). So the joint over (seller, buyer)
is directly observable ONLY on the complete-information branch, and the
incomplete-information branch had to be identified indirectly. Three facts do
it, and they agree:

  1. Your own valuation is never censored, so its marginal is observed without
     bias. Under incomplete information it is uniform over all four factors --
     seller n = 189, chi2 = 1.07, df = 3, p = 0.78; buyer n = 173, chi2 = 5.47,
     df = 3, p = 0.14. In particular the seller's factor is 1.5 in 48 of 189
     games and the buyer's is 0.8 in 55 of 173, both of which are IMPOSSIBLE
     under the complete-information restriction. The restriction therefore does
     not extend to the incomplete-information branch (p < 1e-12).

  2. If the pair is independent, P(strict ZOPA | own factor) is
     (0.75, 0.50, 0.25, 0.00) for a seller at (0.8, 1.0, 1.2, 1.5) and the
     mirror image for a buyer. Agreement rate should be affine in that
     quantity. Pooling the two seats: 7/101, 20/91, 43/87, 54/80 at predicted
     P(ZOPA) of 0.00, 0.25, 0.50, 0.75. Weighted least squares gives
     P(agree) = 0.052 + 0.834 * P(ZOPA), R^2 = 0.988 on 4 points / 2 residual
     degrees of freedom.

  3. That fit's implied P(agree | ZOPA) = 0.886 is an out-of-sample match for
     the agreement rate measured on the DISJOINT complete-information games,
     where a ZOPA is guaranteed: 124/142 = 0.873, 95% CI [0.809, 0.918]. And
     its implied P(agree | no ZOPA) = 0.052 is the rate at which LLM players
     sign deals that lose one of them money, which is a real and separately
     visible phenomenon (15 agreed prices in the corpus sit above the buyer's
     maximum possible valuation of 1.5 x scale).

  See ``analysis/negotiation_joint_estimation.py`` for the whole calculation.

ASSUMPTIONS
-----------
ASSUMPTION 1 (independence within the incomplete-information branch). What
items 1-3 above identify is the pair of own-value marginals and the profile
P(strict ZOPA | own factor) in each seat. Several joints reproduce both; we
take the independent one, which is the maximum-entropy member of that set and
the only one with a mechanism behind it (two independent draws off one axis).
A fully non-parametric estimate of all 16 cells is NOT identified from
observational data -- the opponent's valuation is never revealed under
incomplete information, and agreement is endogenous. Resolving a correlation
of |rho| = 0.1 through the agreement channel would need roughly 4,000
incomplete-information negotiation games per seat (the current 362 resolve
about |rho| = 0.35), which the fleet reaches in ~2 days.

ASSUMPTION 2 (uniform over grid points, not over axes). The docs say the
server draws from the grid but not how. We draw each axis independently and
uniformly, which is uniform over the Cartesian product of the axes as defined
here. Because the negotiation valuation pair and the information condition are
ONE axis of 22 points rather than two independent axes, this reproduces the
measured P(complete_information) = 0.27 rather than 0.5. That is the single
substantive behavioural change in this module.

ASSUMPTION 3 (persuasion buyer type). GLEE varies an ``is_myopic`` axis
(long-living buyer who accumulates payoff and sees the full history, vs. a
fresh myopic buyer each round who sees only summary statistics), which is what
takes persuasion from 180 to 360 combinations in the paper. We fix it to the
long-living buyer and drop the axis: the docs pin it down, no ``is_myopic``
field appears in any of the 505 live persuasion configs, and dropping it is
what makes the three families sum to the documented 960.

ASSUMPTION 4 (persuasion prior). ``p`` = 0.8 appears in 191/501 = 0.381 of
persuasion games against a uniform 1/3 (95% CI [0.339, 0.424], so uniform is
just barely excluded at the 5% level; the omnibus chi2 = 5.19, df = 2 is
p = 0.075 and does not reject). Every other persuasion axis is flatly uniform,
so we treat this as sampling noise and draw uniform. n = 2,000 persuasion games
would settle it; the fleet reaches that in ~4 hours. If it is real, the effect
of getting it wrong is small: it re-weights an axis, it does not add or remove
configurations.

ASSUMPTION 5 (the "infinite" horizon). The corpus contains ``max_rounds`` 12
(bargaining) and 1 or 10 (negotiation) with ``horizon_known`` true, and NO
``max_rounds`` key at all with ``horizon_known`` false -- 242 bargaining and
173 negotiation games. The server never discloses the long cap, and the docs
describe those games as having "NO round limit" with ``max_rounds`` absent. So
``horizon_known`` is derived from the drawn cap, and on an undisclosed cap the
key is dropped rather than passed through. Internally the undisclosed cap is
99 (GLEE's encoding), which matters only to a strategy that could observe it,
and none can. Neither game reaches its cap in practice: with delta 0.9 a
round-99 payoff is 3e-5 of the pot.

ASSUMPTION 6 (currency). GLEE parameterises valuations as a factor times a
scale and the server sends the product as a float (``player_1_value: 80.0``,
``v: 12500.0``, ``u: 0.0``) while sending ``product_price``, ``money_to_divide``,
``max_rounds`` and ``total_rounds`` as ints. We match that exactly. Every
product on this grid is an exact whole number of currency units, so the float
carries no rounding artifact.

CONTRACT WITH THE ENGINES
-------------------------
Keys are named for the documented ``game_state`` fields, so an engine can carry
them straight through -- with two things it still owns:

  * ``horizon_known`` is always present; ``max_rounds`` is present exactly when
    it is true. On an uncapped configuration the key is *absent*, not None,
    which is how the docs describe the field and how the engines read it. Any
    backstop that stops a runaway uncapped game is the engine's own and must
    stay out of ``game_state``.
  * Private information is NOT filtered here -- ``params`` carries both sides'
    numbers whatever ``complete_information`` says, because the engine needs
    them to score the game. Under incomplete information ``observation()`` must
    drop the opponent's ``delta_*`` / ``player_*_value``, and persuasion's
    ``v``/``u`` must reach the seller only when ``is_seller_know_cv``.
"""

from __future__ import annotations

import itertools
import random

from .types import Config

#: Currency scale M, shared by all three families: the pot in bargaining, the
#: valuation scale in negotiation, the fixed price in persuasion. Rationality
#: says the scale is irrelevant; the corpus keeps it precisely because LLM and
#: human play is not scale-invariant.
MONEY_SCALES = (100, 10_000, 1_000_000)

#: Per-round discount multipliers (0.9 = 10% inflation per round). 1.0 means a
#: player suffers no inflation at all, which flips the whole equilibrium: a
#: patient player facing an impatient one can simply wait them out. Uniform
#: over all 16 ordered pairs in the corpus (chi2 = 10.65, df = 15, n = 259).
BARGAINING_DELTAS = (0.8, 0.9, 0.95, 1.0)

#: 12 is the disclosed deadline; 99 is the undisclosed "infinite" horizon.
#: Only those two appear in 265 disclosed and 242 undisclosed live games.
BARGAINING_HORIZONS = (12, 99)

#: V_i = factor * scale. Which PAIRS occur depends on the information
#: condition -- see NEGOTIATION_VALUE_CONDITIONS.
NEGOTIATION_VALUE_FACTORS = (0.8, 1.0, 1.2, 1.5)

#: Under complete information the live server draws only strictly ordered
#: pairs, so a zone of agreement always exists: 143 of 143 observed games,
#: uniform over these six (chi2 = 1.13, df = 5, p = 0.95).
NEGOTIATION_VALUE_PAIRS_COMPLETE = tuple(
    (seller, buyer)
    for seller in NEGOTIATION_VALUE_FACTORS
    for buyer in NEGOTIATION_VALUE_FACTORS
    if seller < buyer
)

#: Under incomplete information the two factors are drawn independently and
#: uniformly, so every pair occurs -- including the 6 with no zone of agreement
#: and the 4 with exactly zero surplus. Identified from the uncensored own-value
#: marginals plus the agreement-rate profile; see the module docstring.
NEGOTIATION_VALUE_PAIRS_INCOMPLETE = tuple(
    itertools.product(NEGOTIATION_VALUE_FACTORS, NEGOTIATION_VALUE_FACTORS))

#: The valuation pair and the information condition are ONE axis, because the
#: support of the pair depends on the condition. 6 + 16 = 22 points, which is
#: what makes P(complete_information) = 6/22 = 0.273 rather than 0.5.
NEGOTIATION_VALUE_CONDITIONS = tuple(
    [(pair, True) for pair in NEGOTIATION_VALUE_PAIRS_COMPLETE]
    + [(pair, False) for pair in NEGOTIATION_VALUE_PAIRS_INCOMPLETE])

#: 1 is take-it-or-leave-it (one offer, one accept/reject, no counteroffer),
#: 10 is a disclosed cap, 99 is the undisclosed "infinite" horizon.
NEGOTIATION_HORIZONS = (1, 10, 99)

#: Prior probability the round's product is high quality.
PERSUASION_PRIORS = (1 / 3, 0.5, 0.8)

#: Buyer's high-quality value as a multiple of the price; always above 1, so a
#: sale is always worth it to the buyer *if* the product is genuinely high
#: quality. 1.2 leaves almost no margin for a bad buy, 4.0 forgives many.
PERSUASION_VALUE_FACTORS = (1.2, 1.25, 2.0, 3.0, 4.0)

#: Buyer's low-quality value as a multiple of the price. GLEE's `c` parameter,
#: 0.0 in all 377 live observations -- the docs say the same ("worth `u`,
#: $0 in our configurations") -- so it is a constant here, not an axis.
PERSUASION_LOW_VALUE_FACTOR = 0.0

PERSUASION_MESSAGE_TYPES = ("text", "binary")

#: Every one of the 505 live persuasion configurations runs 20 rounds.
PERSUASION_TOTAL_ROUNDS = 20

#: GLEE states the deadline in the rules prompt only when it is this short or
#: shorter; a longer cap exists but is never revealed. This is what makes
#: `horizon_known` a derived field rather than an independent axis.
HORIZON_DISCLOSURE_CAP = 20

#: Provenance for every claim in the docstring: the live corpus this grid was
#: fitted to. Bumped whenever the fit is re-run, so a reader can tell how much
#: evidence is behind the weights.
CORPUS = {
    "source": "logs/**/games/*.json (five probes: champion, hardliner, "
              "conceder, randomized, composite)",
    "as_of": "2026-08-19",
    "games": {"bargaining": 511, "negotiation": 505, "persuasion": 505},
    "negotiation_both_values_visible": 143,
    "negotiation_own_value_only": 362,
}


def horizon_is_known(max_rounds: int) -> bool:
    """Whether the players are told the deadline for this round cap."""
    return 0 < max_rounds <= HORIZON_DISCLOSURE_CAP


def _money(factor_times_scale: float) -> float:
    """A dollar amount from a factor * scale product (see ASSUMPTION 6).

    The server sends valuations as floats and every grid point is an exact
    whole number of currency units, so rounding first removes the 1e-14 float
    artifact a bare product can carry without changing the type the engines and
    strategies see.
    """
    return float(round(factor_times_scale))


def _horizon(max_rounds: int) -> dict:
    """The horizon fields for a drawn cap.

    An undisclosed deadline is not a deadline as far as anyone playing the game
    can tell, so it is dropped rather than passed along for an engine to
    remember to hide.
    """
    if horizon_is_known(max_rounds):
        return {"max_rounds": max_rounds, "horizon_known": True}
    return {"horizon_known": False}


# The axes, in the order they are drawn. One definition feeds both the sampler
# and the enumerator so the two cannot drift apart, and drawing one value per
# axis is exactly uniform over their product -- which is the whole grid. Axis
# names are internal; the builders below translate them into the documented
# state-field names.
#
# Note the negotiation entry: "value_condition" is a single 22-point axis
# carrying (valuation pair, complete_information) together, because the pair's
# support depends on the condition. Splitting them would be the old bug.
_AXES = {
    "bargaining": (
        ("delta_1", BARGAINING_DELTAS),
        ("delta_2", BARGAINING_DELTAS),
        ("money_to_divide", MONEY_SCALES),
        ("max_rounds", BARGAINING_HORIZONS),
        ("complete_information", (True, False)),
        ("messages_allowed", (True, False)),
    ),
    "negotiation": (
        ("value_condition", NEGOTIATION_VALUE_CONDITIONS),
        ("scale", MONEY_SCALES),
        ("max_rounds", NEGOTIATION_HORIZONS),
        ("messages_allowed", (True, False)),
    ),
    "persuasion": (
        ("p", PERSUASION_PRIORS),
        ("value_factor", PERSUASION_VALUE_FACTORS),
        ("product_price", MONEY_SCALES),
        ("is_seller_know_cv", (True, False)),
        ("seller_message_type", PERSUASION_MESSAGE_TYPES),
    ),
}


def _bargaining_params(draw: dict) -> dict:
    params = {
        "money_to_divide": draw["money_to_divide"],
        "delta_1": draw["delta_1"],
        "delta_2": draw["delta_2"],
        "complete_information": draw["complete_information"],
        "messages_allowed": draw["messages_allowed"],
    }
    return {**params, **_horizon(draw["max_rounds"])}


def _negotiation_params(draw: dict) -> dict:
    (seller_factor, buyer_factor), complete = draw["value_condition"]
    scale = draw["scale"]
    params = {
        # player_1 is always the seller (its value is a minimum acceptable
        # price), player_2 always the buyer (a maximum). True in all 505 live
        # negotiation configs: player_1_role is "seller" without exception.
        "player_1_value": _money(scale * seller_factor),
        "player_2_value": _money(scale * buyer_factor),
        "complete_information": complete,
        "messages_allowed": draw["messages_allowed"],
    }
    return {**params, **_horizon(draw["max_rounds"])}


def _persuasion_params(draw: dict) -> dict:
    price = draw["product_price"]
    return {
        "product_price": price,
        "p": draw["p"],
        "v": _money(price * draw["value_factor"]),
        "u": _money(price * PERSUASION_LOW_VALUE_FACTOR),
        "total_rounds": PERSUASION_TOTAL_ROUNDS,
        "seller_message_type": draw["seller_message_type"],
        "is_seller_know_cv": draw["is_seller_know_cv"],
    }


_BUILDERS = {
    "bargaining": _bargaining_params,
    "negotiation": _negotiation_params,
    "persuasion": _persuasion_params,
}


def _axes(game_family: str):
    try:
        return _AXES[game_family]
    except KeyError:
        raise ValueError(f"unknown game family {game_family!r}") from None


def sample_config(game_family: str, rng: random.Random) -> Config:
    """Draw one configuration the way the server draws from the GLEE grid.

    Drawing each axis independently is uniform over the full product (see
    ASSUMPTION 2) and keeps the number of ``rng`` calls fixed per draw, so a
    seeded run replays identically.
    """
    draw = {name: rng.choice(values) for name, values in _axes(game_family)}
    return Config(game_family, _BUILDERS[game_family](draw))


def all_configs(game_family: str) -> list[Config]:
    """Every configuration in the family's grid, in a stable order.

    For sweeping the whole space instead of sampling it -- a strategy change
    that helps on average can still be a disaster in one corner (a 1-round
    negotiation, an opponent who suffers no inflation), and only an exhaustive
    pass finds those.

    Note that enumerating is NOT the same experiment as sampling: the grid is
    not a balanced design across the information condition. Negotiation has 6
    complete-information valuation pairs against 16 incomplete-information
    ones, so an exhaustive pass weights the incomplete branch 16/22 exactly as
    the sampler does, but a per-cell summary of an exhaustive pass is a summary
    of an unbalanced design and must be read as such.
    """
    axes = _axes(game_family)
    names = [name for name, _ in axes]
    build = _BUILDERS[game_family]
    return [Config(game_family, build(dict(zip(names, combo))))
            for combo in itertools.product(*(values for _, values in axes))]
