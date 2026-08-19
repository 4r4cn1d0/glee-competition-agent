#!/usr/bin/env python
"""Tune the real agent offline, against the local simulator instead of the queue.

    python scripts/tournament.py --games 200
    python scripts/tournament.py --family bargaining --opponent docs_baseline --games 100
    python scripts/tournament.py --sweep GLEE_BARG_SPE_WEIGHT=0.4,0.65,0.9 --games 150

Every live game is permanently percentile-scored, so tuning a knob on the server
costs rating whether the knob helps or not. This plays the SAME callable the SDK
would call — ``glee_agent.dispatch.make_strategy`` with ``llm_mode`` forced to
"off" — against ``sim.opponents``, and scores it the way the server scores:
percentile against the field on the same configuration in the same seat.

WHY A FIELD, NOT A DUEL
-----------------------
The competition does not score win/loss. A payoff becomes a percentile against
every payoff earned on that configuration in that role, so a lone strategy has
nothing to be a percentile OF: one payoff per (configuration, role) group ranks
against itself at 0.5 and scores exactly 2000, which looks like data and is not.
So each run plays a whole field — the agent plus every ``sim.opponents``
archetype — over the SAME drawn configurations against the same opponent, and
hands the pooled records to ``sim.arena.percentile_scores``. The agent's rating
is then its standing among that field, which is the quantity the server measures.
Field members that turn out to play a family identically are collapsed to one
seat first: several ``sim.opponents`` archetypes are persuasion specialists that
fall back to the reference agent everywhere else, and a percentile taken against
four copies of one policy measures how many clones it has, not how good it is.

The ratings printed here are relative to that local field. They are not a
prediction of a leaderboard rating: ``percentile_scores`` deliberately omits the
opponent-strength adjustment, the rating update, and the display shrinkage,
all of which need the live field (see sim/arena.py).

WHY --sweep POOLS THE ARMS
--------------------------
Sweep arms share one seed, so every arm meets the identical configurations with
identical engine draws and identical opponent behaviour — the only difference is
the knob. All arms are then scored in ONE pool together with the shared field, so
an arm's rating is literally its percentile against the other arms and the field
on the same configuration. Re-drawing configurations per arm, or scoring each arm
in its own pool, would compare arms across different games and report noise.

ASSUMPTION: the knob is applied through ``Config.from_env`` with the environment
variable set, because that is the path the live agent takes; a name
``from_env`` does not read is rejected rather than silently ignored.
"""

from __future__ import annotations

import argparse
import copy
import logging
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent.config import Config  # noqa: E402
from glee_agent.dispatch import make_strategy  # noqa: E402
from sim import opponents  # noqa: E402
from sim.arena import percentile_scores, run_matches  # noqa: E402

FAMILIES = ("bargaining", "negotiation", "persuasion")
DEFAULT_SEED = 20260819
AGENT = "agent"


def fresh(policy, seed: int):
    """A private copy of a baseline policy with any RNG re-seeded.

    ``sim.opponents.OPPONENTS`` holds singletons, and ``random_valid`` carries
    mutable RNG state. Shared across arms that state makes two "same seed" runs
    see different opponent behaviour, which is exactly the noise --sweep exists
    to remove.
    """
    clone = copy.deepcopy(policy)
    for value in vars(clone).values():
        if isinstance(value, random.Random):
            value.seed(seed)
    return clone


def build_strategy(overrides: dict) -> tuple:
    """The live agent, built the live way, with the sweep knob in place.

    Returns ``(strategy, cfg)``. ``llm_mode`` is forced off: a tournament is
    tens of thousands of turns and the heuristic layer is what the knobs move.
    """
    saved = {name: os.environ.get(name) for name in overrides}
    try:
        for name, value in overrides.items():
            os.environ[name] = str(value)
        cfg = Config.from_env()
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    cfg.llm_mode = "off"
    return make_strategy(cfg), cfg


def parse_sweep(spec: str) -> tuple:
    """``GLEE_BARG_SPE_WEIGHT=0.4,0.65,0.9`` -> ("GLEE_...", ["0.4", ...])."""
    name, sep, values = spec.partition("=")
    name = name.strip()
    arms = [v.strip() for v in values.split(",") if v.strip()]
    if not sep or not name or len(arms) < 2:
        raise ValueError(f"--sweep wants KNOB=v1,v2[,v3]; got {spec!r}")
    return name, arms


def check_knob(name: str, arms: list) -> None:
    """Refuse a knob ``Config.from_env`` does not read.

    Silently ignoring a misspelled variable would produce a sweep table whose
    arms differ by nothing and whose spread is pure sampling noise — the single
    most misleading output this script could print.
    """
    configs = [build_strategy({name: value})[1] for value in arms]
    if all(c == configs[0] for c in configs[1:]):
        raise SystemExit(
            f"tournament: {name!r} changes nothing in Config.from_env() across "
            f"{arms} — check the variable name (see glee_agent/config.py)")


def play_arm(family, arm_name, strategy, opponent_names, games, seed) -> list:
    """One field member's records for one family, over every chosen opponent."""
    records = []
    for opponent_name in opponent_names:
        records += run_matches(
            family, strategy, fresh(opponents.get(opponent_name), seed),
            games, seed, name=arm_name, opponent_name=opponent_name)
    return records


def signature(records) -> tuple:
    """A policy's payoff vector for one family, in a canonical game order."""
    return tuple(r.payoff for r in
                 sorted(records, key=lambda r: (r.opponent_name, r.game_id)))


def collect(families, opponent_names, arms, games, seed, quiet=False) -> list:
    """Play every arm and the baseline field into one poolable record list.

    The field members play the same opponents over the same seed as the arms, so
    every (configuration, role) group ends up holding one payoff per arm plus one
    per surviving baseline — enough for a percentile to mean something.

    Baselines that produce an IDENTICAL payoff vector for a family are collapsed
    to one member. Several ``sim.opponents`` archetypes are persuasion
    specialists that fall back to the reference agent outside persuasion, so an
    undeduplicated field seats several copies of ``docs_baseline`` in bargaining and
    the percentile stops measuring the strategy and starts measuring how many
    clones a policy happens to have. The live field has distinct players.
    """
    records = []
    for family in families:
        for arm_name, arm in arms:
            records += play_arm(family, arm_name, arm, opponent_names, games, seed)

        seen, collapsed = {}, []
        for name in sorted(opponents.OPPONENTS):
            mine = play_arm(family, f"baseline:{name}",
                            fresh(opponents.get(name), seed),
                            opponent_names, games, seed)
            key = signature(mine)
            if key in seen:
                collapsed.append(f"{name}->{seen[key]}")
                continue
            seen[key] = name
            records += mine
        if not quiet:
            note = f" (duplicate baselines collapsed: {', '.join(collapsed)})" if collapsed else ""
            print(f"  played {family}: {len(records)} records{note}", file=sys.stderr)
    return records


def ratings_by(entries) -> dict:
    """(name, family) -> the game ratings the scorer assigned, for averaging."""
    buckets = {}
    for entry in entries:
        if entry["percentile"] is None:
            continue
        buckets.setdefault((entry["name"], entry["game_family"]), []).append(
            entry["game_rating"])
    return buckets


def report(records, scores, arm_names, families) -> None:
    ratings = ratings_by(scores["scored"])
    per_arm = {}
    for record in records:
        if record.name in arm_names:
            per_arm.setdefault((record.name, record.game_family), []).append(record)

    def mean_rating(arm, family=None):
        keys = [(arm, family)] if family else [(arm, f) for f in families]
        values = [r for key in keys for r in ratings.get(key, [])]
        return statistics.mean(values) if values else float("nan")

    multi = len(arm_names) > 1
    width = max([8] + [len(n) for n in arm_names]) if multi else 0
    lead = f"{'arm':<{width}s} " if multi else ""
    header = (f"  {lead}{'family':12s} {'games':>6s} {'no-deal':>8s} "
              f"{'mean payoff':>14s} {'rating':>8s}")
    print()
    print(header)
    print("  " + "-" * (len(header) - 2))

    def rows(arm):
        for family in families:
            group = per_arm.get((arm, family), [])
            if not group:
                continue
            yield (family, len(group),
                   sum(1 for r in group if r.outcome == "no_deal") / len(group),
                   statistics.mean(r.payoff for r in group),
                   mean_rating(arm, family))

    # Sorted by overall rating, so the winning arm is the top block.
    for arm in sorted(arm_names, key=lambda a: -mean_rating(a)):
        played = 0
        for i, (family, n, no_deal, payoff, rating) in enumerate(rows(arm)):
            played += n
            tag = f"{arm if i == 0 else '':<{width}s} " if multi else ""
            print(f"  {tag}{family:12s} {n:6d} {no_deal:7.1%} "
                  f"{payoff:14.2f} {rating:8.1f}")
        tag = f"{'':<{width}s} " if multi else ""
        print(f"  {tag}{'OVERALL':12s} {played:6d} {'':8s} {'':14s} "
              f"{mean_rating(arm):8.1f}")

    print(f"\n  scored {scores['n_scored']} of {scores['n_records']} records over "
          f"{scores['n_groups_scored']}/{scores['n_groups']} configuration groups"
          f" ({scores['n_unscored']} unscored, {scores['n_voided']} voided,"
          f" {scores['n_dropped']} dropped)")
    print("  Ratings are percentiles against this local field only \u2014 compare arms,")
    print("  never the absolute number. Mean payoff is per family; the three")
    print("  families use different currency scales and do not add up.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--games", type=int, default=100,
                        help="configurations drawn per family per opponent "
                             "(each is played from both seats)")
    parser.add_argument("--family", choices=FAMILIES, action="append",
                        help="restrict to one family (repeatable)")
    parser.add_argument("--opponent", action="append",
                        choices=sorted(opponents.OPPONENTS),
                        help="restrict to one baseline opponent (repeatable)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="drives the configuration draw; shared by every arm")
    parser.add_argument("--sweep", metavar="KNOB=v1,v2",
                        help="re-run the same seeded configs across values of a "
                             "Config environment knob")
    parser.add_argument("--quiet", action="store_true", help="no progress lines")
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)   # the agent narrates every turn at INFO

    families = tuple(args.family) if args.family else FAMILIES
    opponent_names = tuple(args.opponent) if args.opponent else tuple(sorted(opponents.OPPONENTS))

    if args.sweep:
        knob, values = parse_sweep(args.sweep)
        check_knob(knob, values)
        arms = [(value, build_strategy({knob: value})[0]) for value in values]
        print(f"sweep {knob} over {values}", flush=True)
    else:
        arms = [(AGENT, build_strategy({})[0])]

    arm_names = [name for name, _ in arms]
    total = len(arm_names) + len(opponents.OPPONENTS)
    print(f"{args.games} configs x 2 seats x {len(opponent_names)} opponents x "
          f"up to {total} field members x {len(families)} families "
          f"<= {args.games * 2 * len(opponent_names) * total * len(families)} games",
          flush=True)

    records = collect(families, opponent_names, arms, args.games, args.seed,
                      quiet=args.quiet)
    scores = percentile_scores(records)
    report(records, scores, arm_names, families)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
