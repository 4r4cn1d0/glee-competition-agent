"""Probe policies for the exploration fleet.

The account's leaderboard place is taken by its BEST agent only — the others
stay on the board unranked. Exploration is therefore free: a deliberately
sacrificial probe costs nothing in standing while its games return real data
about the field. The platform also guarantees "you never play your own agents",
so a probe's every game is against the genuine field, never against us.

The probes are deliberately DIFFERENT from each other. Four copies of one policy
sample the field's response at a single point; four different policies recover
the response *function*. In particular:

* ``randomized`` is the statistically valuable one. By offering across the whole
  feasible range it identifies P(accept | share) directly — the acceptance curve
  every other policy only ever samples near its own operating point. It scores
  badly by construction. That is the price of identification, and it is free.
* ``hardliner`` finds who caves and how far, by never conceding first.
* ``conceder`` finds the field's opening demands — what an opponent extracts
  when nothing pushes back, i.e. the top of their range.
* ``champion`` is the tuned policy under evaluation; its rating is the one that
  counts.

Every probe routes through the same dispatch safety net, so a probe cannot time
out a game or submit an illegal move — a crashing probe would poison the very
dataset it exists to collect (and three self-timeouts in a row trigger a 30
minute queue ban).
"""

from __future__ import annotations

import random
from dataclasses import replace

from .actions import _num, is_final_round


def _champion(cfg):
    return cfg


def _hardliner(cfg):
    """Concede as little as possible, as late as possible."""
    return replace(
        cfg,
        barg_spe_weight=1.0,          # full equilibrium demand, no fairness blend
        barg_uncapped_horizon=60,     # concede only once inflation really bites
        nego_seller_anchor=4.0,
        nego_buyer_anchor=0.15,
        pers_lie_shading=1.0,         # ride the whole Bayesian lie budget
        pers_honest_rounds=0,
    )


def _conceder(cfg):
    """Settle early and cheaply. Reveals what opponents ask for unopposed."""
    return replace(
        cfg,
        barg_spe_weight=0.0,          # even split, always
        barg_uncapped_horizon=5,
        nego_seller_anchor=1.15,
        nego_buyer_anchor=0.85,
        pers_lie_shading=0.0,         # never lie
        pers_honest_rounds=99,
    )


def _composite(cfg):
    """Best measured configuration per family, assembled from the fleet.

    The knobs are family-namespaced, so each family's winning arm can be lifted
    wholesale without the families interfering.

    Reassembled 2026-08-20 from live ratings at ~1,600 games per agent per family,
    which is past the point where the rating has converged (eta is 0.2% at that
    volume, a 10h time constant against 50 games/hr):

        family        champion  hardliner  conceder  composite     ->  taken from
        bargaining      1975.7    2018.1     1917.7    2003.2      ->  hardliner
        negotiation     1866.3    1872.1     1161.7    1759.2      ->  hardliner
        persuasion      1935.3    1861.4     2013.9    1989.8      ->  conceder

    Two of these reverse the previous assembly. Bargaining was taken from conceder
    (flat 50/50) on an earlier percentile estimate; hardliner's full-equilibrium
    demand now leads it by 100 points. Persuasion was taken from hardliner (ride
    the whole lie budget) on a reading that itself reversed an earlier one; the
    honest arm now leads by 152 points, and it is the ordering theory predicts --
    20 rounds with the buyer holding full history means a caught lie costs the
    remaining rounds while gaining a single sale.

    Negotiation stays with hardliner's anchors, but see the note in arms.json:
    composite ran those same anchors and scored 113 points BELOW hardliner, and
    the only difference was three extra negotiation flags. Those are dropped.

    Caveat kept deliberately visible: this still selects the maximum of four noisy
    per-family estimates, which biases the projection upward. It is a measured
    starting point, not a proven optimum.
    """
    c, h = _conceder(cfg), _hardliner(cfg)
    return replace(
        cfg,
        barg_spe_weight=h.barg_spe_weight,          # was conceder's 0.0
        barg_uncapped_horizon=h.barg_uncapped_horizon,
        nego_seller_anchor=h.nego_seller_anchor,
        nego_buyer_anchor=h.nego_buyer_anchor,
        pers_lie_shading=c.pers_lie_shading,        # was hardliner's 1.0
        pers_honest_rounds=c.pers_honest_rounds,
    )


def randomized_strategy(rng: random.Random):
    """Offer across the whole feasible range to identify the acceptance curve.

    Deliberately unconditioned on the state beyond legality: any adaptation
    would correlate our offers with the situation and confound the estimate of
    how the field responds to a given share.
    """

    def strategy(game: dict) -> dict:
        state = game.get("game_state") or {}
        family = game.get("game_family")
        action_type = (game.get("valid_actions") or {}).get("type")

        if family == "bargaining":
            money = _num(state.get("money_to_divide"), 0.0)
            if action_type == "offer":
                mine = rng.uniform(0.05, 0.95) * money
                me_is_alice = game.get("your_player") == "player_1"
                return {"alice_gain": mine if me_is_alice else money - mine,
                        "bob_gain": money - mine if me_is_alice else mine}
            offer = state.get("last_offer") or {}
            mine = _num(offer.get(f"{state.get('current_player')}_gain"), 0.0)
            # A uniformly drawn threshold traces out the acceptance curve.
            return {"decision": "accept" if mine >= rng.uniform(0.0, 0.7) * money
                    else "reject"}

        if family == "negotiation":
            me = state.get("current_player") or game.get("your_player")
            role = state.get(f"{me}_role")
            value = _num(state.get(f"{me}_value"), 1.0)
            span = (1.0, 3.0) if role == "seller" else (0.2, 1.0)
            if action_type == "offer":
                return {"product_price": round(value * rng.uniform(*span), 2)}
            price = _num((state.get("last_offer") or {}).get("price"), 0.0)
            profitable = price >= value if role == "seller" else price <= value
            if profitable and rng.random() < 0.6:
                return {"decision": "AcceptOffer"}
            if is_final_round(state):
                return {"decision": "AcceptOffer" if profitable else "RejectOffer"}
            return {"decision": "RejectOffer",
                    "product_price": round(value * rng.uniform(*span), 2)}

        # persuasion
        if action_type in ("seller_message", "seller_recommendation"):
            recommend = rng.random() < 0.5
            if action_type == "seller_recommendation":
                return {"decision": "yes" if recommend else "no"}
            return {"message": "I recommend this one." if recommend
                    else "I would hold off on this one."}
        price = _num(state.get("product_price"), 0.0)
        expected = (_num(state.get("p"), 0.5) * _num(state.get("v"), 0.0)
                    + (1 - _num(state.get("p"), 0.5)) * _num(state.get("u"), 0.0))
        return {"decision": "yes" if expected >= price * rng.uniform(0.4, 1.6) else "no"}

    return strategy


#: name -> (config transform, custom strategy factory or None)
PROBES = {
    "champion": (_champion, None),
    "composite": (_composite, None),
    "hardliner": (_hardliner, None),
    "conceder": (_conceder, None),
    "randomized": (_champion, randomized_strategy),
}


def make_probe(name: str, cfg, log=None, seed: int | None = None):
    """Build the strategy callable for a named probe."""
    from .dispatch import make_strategy

    try:
        transform, custom = PROBES[name]
    except KeyError:
        raise ValueError(f"unknown probe {name!r}; choose from {sorted(PROBES)}") from None

    probe_cfg = transform(cfg)
    if custom is None:
        return make_strategy(probe_cfg, log), probe_cfg

    # A custom policy still goes through the dispatch safety net: it is wrapped
    # so an exception or an illegal action degrades to a legal move instead of
    # timing the game out.
    rng = random.Random(seed)
    inner = custom(rng)
    base = make_strategy(probe_cfg, log)

    def strategy(game: dict) -> dict:
        from .actions import coerce, safe_action
        try:
            action = coerce(inner(game), game)
        except Exception:
            action = None
        if not action:
            return base(game)
        if log is not None:
            log.turn(game, action, None, source=f"probe:{name}")
        return action

    return strategy, probe_cfg
