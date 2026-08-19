#!/usr/bin/env python
"""Re-run the offline knob sweeps against the OLD grid and the NEW one.

    .venv/bin/python analysis/rerun_sweeps.py --games 120 --seeds 8

The point is not the sweeps -- it is whether recalibrating ``sim/grid.py``
changed what they say. Both grids are swept in the same process, with the same
agent code, the same opponents, the same seeds and the same arms. The only
difference between an OLD row and a NEW row is the configuration distribution.

WHICH SWEEPS, AND ONE CORRECTION TO THE BRIEF
---------------------------------------------
``GLEE_BARG_SPE_WEIGHT`` and ``GLEE_NEGO_DEAL_ODDS`` are the two knobs that
were previously swept against the broken grid. ``GLEE_NEGO_DEAL_ODDS`` needs
care: it feeds ``continuation_value``, which only reaches the acceptance
decision when ``GLEE_NEGO_CONTINUATION_ACCEPT`` is set (see
``glee_agent/strategies/negotiation.py:_continuation_accept_enabled``). With
that flag off -- its default, and the state the earlier sweep ran in -- every
arm of the knob produces a bit-identical game. So the earlier "no effect on
``GLEE_NEGO_DEAL_ODDS``" was not a measurement of a small effect; it was a
measurement of a disconnected wire, and it would have read the same on any
grid. This script therefore sweeps it BOTH ways and reports both, plus the
gate itself, which is the decision the knob actually serves.

METHOD, and why it is not one table
-----------------------------------
``scripts/tournament.py`` prints one rating per arm from one seed. That number
is a percentile against a local field on ~120 drawn configurations, and picking
the best of k such numbers is picking the max of k noisy arms, which is biased
upward by construction. So this script:

  * repeats the whole sweep over ``--seeds`` independent configuration draws;
  * reports each arm's mean rating with the standard error ACROSS seeds;
  * reports the PAIRED difference against the incumbent default, seed by seed.
    Within a seed every arm meets identical configurations against identical
    opponents, so seed-level common variation cancels and the paired standard
    error is the honest yardstick -- it is several times smaller than the
    unpaired one;
  * quantifies the winner's curse on the PAIRED scale: with k rival arms and
    paired standard error s, the expected overstatement of the best paired
    difference is about s * E[max of k standard normals].

Ratings are percentiles against a LOCAL heuristic field. They do not predict a
leaderboard rating, and the absolute numbers mean nothing. Only differences
between arms on the same grid -- and the change in those differences between
grids -- are interpretable.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import logging
import math
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import sim.grid                                          # noqa: E402
from analysis import grid_legacy                         # noqa: E402

import tournament                                        # noqa: E402
from sim import opponents                                # noqa: E402
from sim.arena import percentile_scores                  # noqa: E402

# E[max of k iid standard normals]; used to quantify winner's-curse inflation.
E_MAX_STD_NORMAL = {0: 0.0, 1: 0.000, 2: 0.564, 3: 0.846, 4: 1.029, 5: 1.163,
                    6: 1.267, 7: 1.352, 8: 1.424, 9: 1.485, 10: 1.539}

CONTINUATION_GATE = "GLEE_NEGO_CONTINUATION_ACCEPT"

# (label, knob, family, arms, incumbent default, fixed environment)
SWEEPS = [
    ("GLEE_BARG_SPE_WEIGHT", "GLEE_BARG_SPE_WEIGHT", "bargaining",
     ["0.0", "0.15", "0.35", "0.5", "0.65", "0.8", "0.95"], "0.65", {}),
    ("GLEE_NEGO_DEAL_ODDS, continuation-accept OFF (as previously swept)",
     "GLEE_NEGO_DEAL_ODDS", "negotiation",
     ["0.0", "0.25", "0.45", "0.65", "0.85", "1.0"], "0.65", {CONTINUATION_GATE: "0"}),
    ("GLEE_NEGO_DEAL_ODDS, continuation-accept ON (the knob actually connected)",
     "GLEE_NEGO_DEAL_ODDS", "negotiation",
     ["0.0", "0.25", "0.45", "0.65", "0.85", "1.0"], "0.65", {CONTINUATION_GATE: "1"}),
    ("GLEE_NEGO_CONTINUATION_ACCEPT itself (the gate, at the default odds)",
     CONTINUATION_GATE, "negotiation", ["0", "1"], "0", {}),
]


@contextlib.contextmanager
def legacy_grid():
    """Swap sim.grid's sampler for the pre-recalibration one.

    ``sim.sample_config`` imports from ``sim.grid`` inside its body on every
    call and ``sim.arena.run_matches`` goes through it, so patching the module
    attribute is enough and nothing has to be reimported.
    """
    saved = sim.grid.sample_config
    sim.grid.sample_config = grid_legacy.sample_config
    try:
        yield
    finally:
        sim.grid.sample_config = saved


@contextlib.contextmanager
def environment(**values):
    """Set env vars for the whole match, not just for Config construction.

    ``tournament.build_strategy`` restores the environment as soon as the
    Config is built, but the continuation gate is read at DECISION time, so it
    has to be live while the games are played.
    """
    saved = {k: os.environ.get(k) for k in values}
    os.environ.update({k: str(v) for k, v in values.items()})
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def one_sweep(knob, family, arms, games, seed, fixed):
    """One seed: {arm: mean rating}, {arm: no-deal rate}, {arm: mean payoff}."""
    with environment(**fixed):
        built = [(value, tournament.build_strategy({knob: value, **fixed})[0])
                 for value in arms]
        per_arm_env = {value: {**fixed, knob: value} for value in arms}
        records = []
        # Arms whose knob is read at decision time need their environment live
        # while they play, so each arm is played inside its own env block. The
        # seed is the same for every arm, so they still meet identical configs.
        for value, strategy in built:
            with environment(**per_arm_env[value]):
                records += tournament.play_arm(
                    family, value, strategy, tuple(sorted(opponents.OPPONENTS)),
                    games, seed)
        # The shared baseline field, played once on the same configurations.
        with environment(**fixed):
            seen = {}
            for name in sorted(opponents.OPPONENTS):
                mine = tournament.play_arm(
                    family, f"baseline:{name}", tournament.fresh(opponents.get(name), seed),
                    tuple(sorted(opponents.OPPONENTS)), games, seed)
                key = tournament.signature(mine)
                if key in seen:
                    continue
                seen[key] = name
                records += mine

    ratings = tournament.ratings_by(percentile_scores(records)["scored"])
    rating = {v: (statistics.mean(ratings[(v, family)])
                  if ratings.get((v, family)) else float("nan")) for v in arms}
    no_deal, payoff = {}, {}
    for value in arms:
        group = [r for r in records if r.name == value]
        no_deal[value] = (sum(1 for r in group if r.outcome == "no_deal")
                          / len(group)) if group else float("nan")
        payoff[value] = statistics.mean([r.payoff for r in group] or [float("nan")])
    return rating, no_deal, payoff


def summarise(label, arms, default, per_seed, no_deal, payoff, out=print):
    n = len(per_seed)
    out(f"\n  {label}  ({n} seeds)")
    out(f"      {'arm':>6}  {'mean rating':>12}  {'se':>7}  "
        f"{'paired vs ' + default:>16}  {'se':>7}     {'no-deal':>8}  {'mean payoff':>14}")
    means, dmeans, dses = {}, {}, {}
    for value in arms:
        series = [s[value] for s in per_seed]
        means[value] = statistics.mean(series)
        se = (statistics.stdev(series) / math.sqrt(n)) if n > 1 else float("nan")
        diffs = [s[value] - s[default] for s in per_seed]
        dmeans[value] = statistics.mean(diffs)
        dses[value] = ((statistics.stdev(diffs) / math.sqrt(n))
                       if n > 1 and len(set(diffs)) > 1 else 0.0)
        star = " *" if dses[value] > 0 and abs(dmeans[value]) > 2 * dses[value] else ""
        out(f"      {value:>6}  {means[value]:12.1f}  {se:7.1f}  "
            f"{dmeans[value]:+16.1f}  {dses[value]:7.1f}{star:<3}  "
            f"{statistics.mean([s[value] for s in no_deal]):7.1%}  "
            f"{statistics.mean([s[value] for s in payoff]):14.2f}")

    rivals = [v for v in arms if v != default]
    best = max(rivals, key=lambda v: dmeans[v]) if rivals else default
    scale = statistics.mean([dses[v] for v in rivals]) if rivals else 0.0
    bias = scale * E_MAX_STD_NORMAL.get(len(rivals), 1.5)
    if all(d == 0.0 for d in dmeans.values()):
        out("      every arm is bit-identical: the knob is INERT in this "
            "configuration and this sweep measures nothing.")
    else:
        out(f"      best rival arm {best}: paired {dmeans[best]:+.1f} +/- {dses[best]:.1f}; "
            f"picking the max of {len(rivals)} rivals inflates that by ~{bias:.1f}, "
            f"so read it as {dmeans[best] - bias:+.1f}.")
    out("      * = |paired difference from the default| exceeds 2 paired standard errors.")
    return means, dmeans, dses


def spearman(a, b):
    def rank(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0.0] * len(xs)
        for pos, i in enumerate(order):
            r[i] = pos + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else float("nan")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--games", type=int, default=120,
                        help="configurations per arm per opponent per seed")
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--seed0", type=int, default=20260819)
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)
    seeds = [args.seed0 + 1000 * i for i in range(args.seeds)]

    print(f"grid sizes   OLD: bargaining {len(grid_legacy.all_configs('bargaining'))}, "
          f"negotiation {len(grid_legacy.all_configs('negotiation'))}, "
          f"persuasion {len(grid_legacy.all_configs('persuasion'))}  (total "
          f"{sum(len(grid_legacy.all_configs(f)) for f in ('bargaining','negotiation','persuasion'))})")
    print(f"             NEW: bargaining {len(sim.grid.all_configs('bargaining'))}, "
          f"negotiation {len(sim.grid.all_configs('negotiation'))}, "
          f"persuasion {len(sim.grid.all_configs('persuasion'))}  (total "
          f"{sum(len(sim.grid.all_configs(f)) for f in ('bargaining','negotiation','persuasion'))})")
    print(f"{args.games} configs x 2 seats x {len(opponents.OPPONENTS)} opponents "
          f"x {args.seeds} seeds, per arm, per grid")

    for label, knob, family, arms, default, fixed in SWEEPS:
        print(f"\n{'='*100}\n{label}\n  knob={knob} family={family} arms={arms} "
              f"default={default} fixed={fixed or '{}'}\n{'='*100}")
        results = {}
        for grid_label, ctx in (("OLD grid (pre-recalibration)", legacy_grid),
                                ("NEW grid (fitted to the live server)",
                                 contextlib.nullcontext)):
            per_seed, nd, po = [], [], []
            with ctx():
                for seed in seeds:
                    with contextlib.redirect_stderr(io.StringIO()):
                        r, d, p = one_sweep(knob, family, arms, args.games, seed, fixed)
                    per_seed.append(r)
                    nd.append(d)
                    po.append(p)
            results[grid_label] = summarise(grid_label, arms, default, per_seed, nd, po)

        (old_m, old_d, old_s), (new_m, new_d, new_s) = results.values()
        print("\n  DID THE CONCLUSION CHANGE?")
        print(f"      {'arm':>6}  {'OLD paired':>11}  {'NEW paired':>11}  {'shift':>8}"
              f"   {'OLD rank':>9}  {'NEW rank':>9}")
        rank_old = {v: i + 1 for i, v in enumerate(sorted(arms, key=lambda v: -old_d[v]))}
        rank_new = {v: i + 1 for i, v in enumerate(sorted(arms, key=lambda v: -new_d[v]))}
        for value in arms:
            print(f"      {value:>6}  {old_d[value]:+11.1f}  {new_d[value]:+11.1f}  "
                  f"{new_d[value]-old_d[value]:+8.1f}   {rank_old[value]:9d}  "
                  f"{rank_new[value]:9d}")
        b_old = max(arms, key=lambda v: old_d[v])
        b_new = max(arms, key=lambda v: new_d[v])
        inert_old = all(d == 0.0 for d in old_d.values())
        inert_new = all(d == 0.0 for d in new_d.values())
        print(f"      best arm: OLD {b_old} -> NEW {b_new}"
              f"   {'(UNCHANGED)' if b_old == b_new else '(CHANGED)'}"
              f"{'  [both inert -- the comparison is vacuous]' if inert_old and inert_new else ''}")
        print(f"      monotone decreasing in the knob:  "
              f"OLD {all(old_d[a] >= old_d[b] for a, b in zip(arms, arms[1:]))}   "
              f"NEW {all(new_d[a] >= new_d[b] for a, b in zip(arms, arms[1:]))}")
        print(f"      Spearman rank correlation of the two arm orderings: "
              f"{spearman([old_d[v] for v in arms], [new_d[v] for v in arms]):+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
