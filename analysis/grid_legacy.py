"""ARCHIVE -- sim/grid.py exactly as it stood before the 2026-08-19
recalibration. Kept verbatim (only the ``.types`` import is rewritten so it
loads outside the package) so ``analysis/verify_grid.py`` can sample the OLD
distribution and the NEW one in the same process and print them side by side.
Nothing else should import this module.

Its error, for the record: it drew the negotiation valuation pair uniformly
over all 16 (seller, buyer) combinations regardless of the information
condition, and drew ``complete_information`` as a free 50/50 axis. The live
server restricts complete-information negotiations to the 6 strictly ordered
pairs, which also makes complete information 6/22 of the family rather than
1/2. The original docstring follows unedited.

The GLEE parameter grid -- the configuration space the server draws from.

You never pick your own numbers: "each configuration is drawn by the server
from a grid of 960 combinations (horizons, sums, valuations, inflation rates,
information conditions), and you never choose yours -- so tuning to one game's
numbers doesn't transfer to the next." A knob tuned against one hand-picked
setting is therefore tuned against nothing. This module reproduces the draw so
a strategy is measured over the spread of configurations it will actually meet,
weighted the way it will meet them.

WHERE THE NUMBERS COME FROM
---------------------------
The competition docs name the parameters -- the documented ``game_state``
fields tell you exactly which knobs exist per family -- but publish no values.
Two sources fill that in, and they agree:

  * The GLEE paper (arXiv:2410.05254), Table 2, publishes the grid used to
    collect the research dataset. That matters more than a paper citation
    usually would: percentile scoring is "seeded by the GLEE research dataset",
    so the competition's configurations are the ones that dataset covers.
  * The reference implementation (github.com/eilamshapira/GLEE) ships the
    ``config.json`` of every game in that dataset. A random sample of 900 of
    them (300 per family, from ``Data/llm_vs_llm``) was aggregated: the value
    set of every axis below is what those files contain, and every pairwise
    combination of every axis appeared, confirming a full Cartesian product
    with no forbidden corners.

So the value sets are measured, not invented. Paper Table 2 and the sampled
configs both give 384 bargaining, 576 negotiation and 360 persuasion
combinations.

ASSUMPTIONS
-----------
ASSUMPTION 1 (grid size). The docs say 960 combinations; the published GLEE
grid is 1,320 (384 + 576 + 360). The competition's own grid is not published,
so the discrepancy cannot be resolved from anything authoritative. Noting only
that 384 + 576 = 960 exactly -- the two alternating-offer families alone -- we
reproduce the published per-family grids rather than inventing a 960-point
reduction, because every point here is one the research dataset actually
contains and therefore one the percentile scoring can rank you on. Revisit if
the organizers publish the competition grid.

ASSUMPTION 2 (persuasion buyer type). GLEE varies a ``is_myopic`` axis
(long-living buyer who accumulates payoff and sees the full history, vs. a
fresh myopic buyer each round who sees only summary statistics), which is what
takes persuasion from 180 to 360 combinations. We fix it to the long-living
buyer and drop the axis, because the docs pin it down: the buyer "knows only
`p` -- and the whole interaction history", "Payoffs sum across rounds", and no
``is_myopic`` field appears in the documented persuasion state. Emitting myopic
games would be inventing a mechanic the server never signals. Persuasion is
therefore 180 combinations here.

ASSUMPTION 3 (draw distribution). The docs say the server draws from the grid
but not how. We draw each axis independently and uniformly, which is exactly
uniform over the Cartesian product. If the server weights configurations (for
instance toward those with the most seed data), our spread is wider than the
live one -- the safe direction to be wrong in.

ASSUMPTION 4 (the "infinite" horizon). Table 2 writes T = infinity and notes it
means "a very large value of T, unknown to the players"; the sampled configs
encode it as ``max_rounds`` 99 for both bargaining and negotiation. GLEE
discloses the deadline to the players only when ``max_rounds <= 20`` (see
``build_max_round`` in games/bargaining/bargaining.py and the same test in
negotiation.py), which is precisely the documented ``horizon_known`` flag. So
``horizon_known`` is derived from the drawn cap, not drawn itself.

On the undisclosed points we then drop ``max_rounds`` from ``params`` rather
than passing GLEE's hidden 99 through, because the docs describe those games as
having "NO round limit" with ``max_rounds`` *absent*, and the engines own a
private backstop for runaway games already. The cost is that a local uncapped
game can outlive a live one, which is immaterial: neither reaches its cap in
practice (with delta 0.9 a round-99 payoff is 3e-5 of the pot), both end a
runaway as an identical $0 no-deal, and a player who is told nothing about the
deadline cannot pace to 99 rather than 500 in any case.

ASSUMPTION 5 (currency). GLEE parameterises valuations as a factor times a
scale: negotiation values are ``product_price_order * seller_value`` /
``buyer_value``, persuasion values are ``product_price * v`` and
``product_price * c``. We store the products. Every product on this grid is an
exact integer, so we store ints; GLEE computes them as float products, which
can carry a 1e-14 artifact that would be noise in a dollar amount either way.

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

from sim.types import Config

#: Currency scale M, shared by all three families: the pot in bargaining, the
#: valuation scale in negotiation, the fixed price in persuasion. Rationality
#: says the scale is irrelevant; the paper keeps it precisely because LLM and
#: human play is not scale-invariant.
MONEY_SCALES = (100, 10_000, 1_000_000)

#: Per-round discount multipliers (0.9 = 10% inflation per round). 1.0 means a
#: player suffers no inflation at all, which flips the whole equilibrium: a
#: patient player facing an impatient one can simply wait them out.
BARGAINING_DELTAS = (0.8, 0.9, 0.95, 1.0)

#: 12 is the disclosed deadline; 99 is the paper's "infinite" horizon, large
#: and never shown to the players.
BARGAINING_HORIZONS = (12, 99)

#: V_i = factor * scale. The seller's factor may exceed the buyer's, in which
#: case there is no price both sides prefer to no deal and walking away is the
#: correct play -- 6 of the 16 pairs, so this is not a rare corner.
NEGOTIATION_VALUE_FACTORS = (0.8, 1.0, 1.2, 1.5)

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
#: constant 0 across the whole dataset -- the docs say the same ("worth `u`,
#: $0 in our configurations") -- so it is a constant here, not an axis.
PERSUASION_LOW_VALUE_FACTOR = 0.0

PERSUASION_MESSAGE_TYPES = ("text", "binary")

#: Every persuasion configuration in the dataset runs 20 rounds.
PERSUASION_TOTAL_ROUNDS = 20

#: GLEE states the deadline in the rules prompt only when it is this short or
#: shorter; a longer cap exists but is never revealed. This is what makes
#: `horizon_known` a derived field rather than an independent axis.
HORIZON_DISCLOSURE_CAP = 20


def horizon_is_known(max_rounds: int) -> bool:
    """Whether the players are told the deadline for this round cap."""
    return 0 < max_rounds <= HORIZON_DISCLOSURE_CAP


def _money(factor_times_scale: float) -> int:
    """A dollar amount from a factor * scale product (see ASSUMPTION 5)."""
    return int(round(factor_times_scale))


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
# and the enumerator so the two cannot drift apart. Axis names are internal;
# the builders below translate them into the documented state-field names.
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
        ("seller_factor", NEGOTIATION_VALUE_FACTORS),
        ("buyer_factor", NEGOTIATION_VALUE_FACTORS),
        ("scale", MONEY_SCALES),
        ("max_rounds", NEGOTIATION_HORIZONS),
        ("complete_information", (True, False)),
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
    scale = draw["scale"]
    params = {
        # player_1 is always the seller (its value is a minimum acceptable
        # price), player_2 always the buyer (a maximum).
        "player_1_value": _money(scale * draw["seller_factor"]),
        "player_2_value": _money(scale * draw["buyer_factor"]),
        "complete_information": draw["complete_information"],
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
    ASSUMPTION 3) and keeps the number of ``rng`` calls fixed per draw, so a
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
    """
    axes = _axes(game_family)
    names = [name for name, _ in axes]
    build = _BUILDERS[game_family]
    return [Config(game_family, build(dict(zip(names, combo))))
            for combo in itertools.product(*(values for _, values in axes))]
