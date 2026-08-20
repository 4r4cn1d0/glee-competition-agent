#!/usr/bin/env python3
"""Evolve the negotiation policy TABLE -- the policy itself as the learned object.

Genome: 40 floats. ask[seat][own-mult][phase] (32) is what we put on the table;
accept[seat][phase] (8) is the minimum surplus/B we take mid-game. Fitness is
the mean ESTIMATED PERCENTILE delta vs the deployed control on negotiation,
fresh seed per generation, (1+lambda) promotion. Guard rails (strict
profitability, final-round any-positive) live in table_policy and are not
evolvable.

Warm start encodes the session's measurements: the 1.5x seller's harvest floor,
the curve-pricing final asks per multiplier, buyer laddering that stops inside
the interior. The search's job is everything we did NOT think of.

Output: best genome -> models/nego_policy_candidate.json (NOT the live path);
deployment requires the held-out replay_eval confirmation and a fleet.py set,
same as every other change.
"""
from __future__ import annotations

import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.field_data import Field                       # noqa: E402
from sim.replay_eval import _draw_games, _play_arm     # noqa: E402

SCRATCH = os.path.join(REPO, "logs", "sweeps", "table_genome_eval.json")
OUT = os.path.join(REPO, "models", "nego_policy_candidate.json")

CONTROL = {"GLEE_NEGO_BOUND_AS_FLOOR": "1", "GLEE_BARG_OPPONENT_FLOOR": "0.39",
           "GLEE_BARG_OFFER_FLOOR": "0.57", "GLEE_NEGO_MIN_MARGIN": "0.02",
           "GLEE_NEGO_CURVE_PRICING": "1", "GLEE_NEGO_MARGIN_WEIGHT": "0.25",
           "GLEE_NEGO_CONTINUATION_ACCEPT": "1", "GLEE_NEGO_HORIZON_V2": "1",
           "GLEE_OPP_EXPLOIT": "1", "GLEE_NEGO_ENDGAME_V3": "1"}
PHASES = ("open", "early", "late", "end")
MULTS = ("0.8", "1.0", "1.2", "1.5")
GENS = int(os.environ.get("TABLE_GENS", "50"))
LAM = 8
GAMES = 2400

WARM = {
    "ask": {
        "seller": {"0.8": [1.45, 1.40, 1.25, 1.15],
                   "1.0": [1.48, 1.42, 1.35, 1.42],
                   "1.2": [1.55, 1.48, 1.40, 1.42],
                   "1.5": [1.80, 1.72, 1.68, 1.72]},
        "buyer":  {"0.8": [0.52, 0.62, 0.70, 0.77],
                   "1.0": [0.55, 0.68, 0.80, 0.92],
                   "1.2": [0.58, 0.72, 0.88, 1.05],
                   "1.5": [0.60, 0.78, 0.98, 1.22]},
    },
    "accept": {"seller": [0.30, 0.18, 0.08, 0.02],
               "buyer":  [0.30, 0.18, 0.08, 0.02]},
}


def mutate(g, rng, sigma_ask=0.06, sigma_acc=0.03):
    child = json.loads(json.dumps(g))
    for seat in ("seller", "buyer"):
        for m in MULTS:
            child["ask"][seat][m] = [
                min(max(x + rng.gauss(0, sigma_ask), 0.45), 2.2)
                for x in child["ask"][seat][m]]
        child["accept"][seat] = [
            min(max(x + rng.gauss(0, sigma_acc), 0.0), 0.6)
            for x in child["accept"][seat]]
    return child


def fitness(field, draws, rows_ctl, genome):
    with open(SCRATCH, "w", encoding="utf-8") as fh:
        json.dump(genome, fh)
    flags = dict(CONTROL, GLEE_NEGO_TABLE="1", GLEE_NEGO_TABLE_PATH=SCRATCH)
    rows = _play_arm(field, draws, flags)
    d = [b["pct"] - a["pct"] for a, b in zip(rows_ctl, rows)
         if a.get("pct") is not None and b.get("pct") is not None]
    return sum(d) / len(d) if d else 0.0


def main() -> int:
    field = Field()
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 31415)
    best = json.loads(json.dumps(WARM))
    best_ever = -1.0
    for gen in range(GENS):
        seed = rng.randrange(2 ** 30)
        draws = _draw_games(field, ["negotiation"], GAMES, seed)
        rows_ctl = _play_arm(field, draws, CONTROL)
        parent_fit = fitness(field, draws, rows_ctl, best)
        gen_best, gen_vec = parent_fit, None
        for _ in range(LAM):
            child = mutate(best, rng)
            sc = fitness(field, draws, rows_ctl, child)
            if sc > gen_best:
                gen_best, gen_vec = sc, child
        if gen_vec is not None:
            best = gen_vec
        best_ever = max(best_ever, gen_best)
        print(f"gen {gen:2d}  parent {parent_fit:+.4f}  "
              f"{'child promoted ' + format(gen_best, '+.4f') if gen_vec else 'held'}",
              flush=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"_gen": gen, "_fit_last": gen_best, **best}, fh, indent=1)
    print(f"final table -> {os.path.relpath(OUT, REPO)}  "
          f"(confirm on held-out seed before ANY deploy)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
