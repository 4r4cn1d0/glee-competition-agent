#!/usr/bin/env python3
"""(1+lambda) evolutionary search over the continuous strategy knobs.

The sweep tests knobs one at a time on a grid; this searches the joint space.
Each generation draws a FRESH game seed (so the winner is not overfitted to one
draw of the field), perturbs the current best with per-knob gaussian noise,
and promotes a child only if its combined fitness beats the parent ON THAT
GENERATION'S SEED. The final winner must then beat the deployed configuration
on a held-out seed before anyone deploys it -- the sweep's stage-B rule.

Fitness is the percentile-shaped objective, not raw payoff:
    barg payoff delta + nego payoff delta - 2 x nego zero-rate delta
(zeros weighted because 51% of live negotiation outcomes sit on the $0 atom and
escaping it is what the rating pays for).
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from sim.field_data import Field                    # noqa: E402
from sim.replay_eval import (_draw_games, _play_arm,  # noqa: E402
                             DEFAULT_CONTROL)

#: knob -> (min, max, sigma). Everything else rides along from the control.
SPACE = {
    "GLEE_NEGO_MIN_MARGIN":    (0.005, 0.15, 0.015),
    "GLEE_NEGO_MARGIN_WEIGHT": (0.05, 1.5, 0.12),
    "GLEE_BARG_OFFER_FLOOR":   (0.50, 0.68, 0.015),
    "GLEE_NEGO_ZOPA_SHARE":    (0.10, 0.50, 0.05),
}
LAMBDA = 6
GENERATIONS = 14
GAMES = 2400


def fitness(field, draws, rows_ctl, flags):
    rows = _play_arm(field, draws, flags)
    score = 0.0
    for fam, wz in (("bargaining", 0.0), ("negotiation", 2.0)):
        pairs = [(a, b) for a, b in zip(rows_ctl, rows) if a["family"] == fam]
        if not pairs:
            continue
        n = len(pairs)
        d_pay = sum(b["norm"] - a["norm"] for a, b in pairs) / n
        d_zero = sum(b["zero"] - a["zero"] for a, b in pairs) / n
        score += d_pay - wz * d_zero
    return score


def main() -> int:
    field = Field()
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 4242)
    best = {k: float(DEFAULT_CONTROL.get(k, (lo + hi) / 2))
            for k, (lo, hi, _s) in SPACE.items()}
    log = []
    for gen in range(GENERATIONS):
        seed = rng.randrange(2 ** 30)
        draws = _draw_games(field, ["bargaining", "negotiation"], GAMES, seed)
        base_flags = dict(DEFAULT_CONTROL,
                          **{k: f"{v:.4f}" for k, v in best.items()})
        rows_ctl = _play_arm(field, draws, base_flags)
        gen_best, gen_vec = 0.0, None      # parent scores 0 against itself
        for _ in range(LAMBDA):
            child = {}
            for k, (lo, hi, sigma) in SPACE.items():
                child[k] = min(max(best[k] + rng.gauss(0, sigma), lo), hi)
            flags = dict(DEFAULT_CONTROL, **{k: f"{v:.4f}" for k, v in child.items()})
            sc = fitness(field, draws, rows_ctl, flags)
            if sc > gen_best:
                gen_best, gen_vec = sc, child
        if gen_vec is not None:
            best = gen_vec
        log.append({"gen": gen, "seed": seed, "improved": gen_vec is not None,
                    "fitness_vs_parent": round(gen_best, 5),
                    "best": {k: round(v, 4) for k, v in best.items()}})
        print(f"gen {gen:2d}  {'improved' if gen_vec is not None else 'held    '}"
              f"  fit {gen_best:+.5f}  {json.dumps(log[-1]['best'])}", flush=True)
    out = os.path.join(REPO, "logs", "sweeps",
                       f"evolve_{time.strftime('%Y%m%dT%H%M%S')}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"space": {k: list(v) for k, v in SPACE.items()},
                   "generations": log, "final": log[-1]["best"]}, fh, indent=1)
    print("final candidate (confirm on a held-out seed before deploying):")
    print(json.dumps(dict(DEFAULT_CONTROL,
                          **{k: f"{v:.4f}" for k, v in best.items()}), indent=1))
    print(f"saved -> {os.path.relpath(out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
