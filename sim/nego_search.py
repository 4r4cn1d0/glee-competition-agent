#!/usr/bin/env python3
"""Search the negotiation parameter space against the cloned field.

WHY A SEARCH AND NOT MORE ONE-AT-A-TIME SWEEPS. The strategy has eight continuous
knobs and we have only ever moved them individually. Individually is exactly how
you miss an optimum that lives in a combination: concede faster AND leave them
less of the visible zone may beat either alone, and no single-knob sweep can see
it.

WHY A HOLD-OUT IS NOT OPTIONAL. Trying N configurations on one set of games and
keeping the best is a lottery: with enough draws something wins on noise alone.
At 4,000 games the per-config standard error on mean percentile is roughly 0.004,
so the best of 60 configs is expected to sit about 2.3 standard errors high --
about +0.009 -- PURELY from selection, which is larger than every real negotiation
effect measured today. So every configuration is scored on a SEARCH set, and only
the survivors are re-scored on a VALIDATION set of different games they were never
selected on. A candidate that wins on search and dies on validation was noise, and
that is the outcome this file exists to catch.

The clone is always V2. The legacy clone accepts any profitable price, is +16
points optimistic exactly where pricing decisions live, and scores WORSE than
always guessing (see sim/clone_fidelity.py). A search against it would happily
converge on asking for everything.

    python -m sim.nego_search --configs 40 --games 3000 --validate 3000
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

#: The live negotiation stack, which is also the control every candidate is
#: measured against. GLEE_SIM_NEGO_RESP_V2 is a CLONE flag, not a strategy flag,
#: and must be present in BOTH arms or the two are playing different opponents.
BASE = {
    "GLEE_SIM_NEGO_RESP_V2": "1",
    "GLEE_NEGO_BOUND_AS_FLOOR": "1", "GLEE_NEGO_CONTINUATION_ACCEPT": "1",
    "GLEE_NEGO_CURVE_PRICING": "1", "GLEE_NEGO_HORIZON_V2": "1",
    "GLEE_NEGO_ENDGAME_V3": "1", "GLEE_NEGO_STALL_POLICY": "1",
    "GLEE_NEGO_DEADGAME_V1": "1", "GLEE_NEGO_TABLE": "1",
    "GLEE_NEGO_POSTERIOR": "1",
    "GLEE_NEGO_MARGIN_WEIGHT": "0.40", "GLEE_NEGO_MIN_MARGIN": "0.02",
    "GLEE_NEGO_ACCEPT_SPAN": "0.48", "GLEE_NEGO_ULTIMATUM_SHARE": "0.80",
    "GLEE_NEGO_SPAN_INVARIANT": "0.40", "GLEE_NEGO_FINAL_OPTION": "0.6",
    "GLEE_NEGO_SELLER_ANCHOR": "4.0", "GLEE_NEGO_BUYER_ANCHOR": "0.15",
}

#: name -> (low, high, decimals). Ranges are deliberately wide enough to contain
#: the current value comfortably inside them, so the search can move in either
#: direction rather than only away from where we already are.
SPACE = {
    "GLEE_NEGO_BOULWARE":        (0.5, 3.0, 2),
    "GLEE_NEGO_ACCEPT_SPAN":     (0.20, 0.80, 2),
    "GLEE_NEGO_ZOPA_SHARE":      (0.10, 0.50, 2),
    "GLEE_NEGO_MIN_MARGIN":      (0.00, 0.15, 3),
    "GLEE_NEGO_MARGIN_WEIGHT":   (0.10, 0.70, 2),
    "GLEE_NEGO_ULTIMATUM_SHARE": (0.60, 0.90, 2),
    "GLEE_NEGO_SPAN_INVARIANT":  (0.20, 0.60, 2),
    "GLEE_NEGO_FINAL_OPTION":    (0.30, 0.90, 2),
}


def sample(rng):
    return {k: f"{round(rng.uniform(lo, hi), d):.{d}f}"
            for k, (lo, hi, d) in SPACE.items()}


def score(field, draws, flags):
    """Mean percentile of this flag set over these exact games."""
    from sim.replay_eval import _play_arm
    rows = _play_arm(field, draws, flags)
    ps = [r["pct"] for r in rows if r.get("pct") is not None]
    cl = [1.0 if r["closed"] else 0.0 for r in rows]
    return (sum(ps) / len(ps) if ps else 0.0,
            sum(cl) / len(cl) if cl else 0.0, len(ps))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--configs", type=int, default=40)
    ap.add_argument("--games", type=int, default=3000, help="search-set size")
    ap.add_argument("--validate", type=int, default=3000, help="hold-out size")
    ap.add_argument("--keep", type=int, default=5, help="how many finalists to validate")
    ap.add_argument("--seed", type=int, default=20260822)
    args = ap.parse_args()

    from sim.field_data import Field
    from sim.replay_eval import _draw_games
    field = Field()
    # Disjoint seeds: the validation games are DIFFERENT games, not a reshuffle.
    search_draws = _draw_games(field, ["negotiation"], args.games, args.seed)
    valid_draws = _draw_games(field, ["negotiation"], args.validate, args.seed + 999983)

    base_s = score(field, search_draws, BASE)
    print(f"control on SEARCH set    pct {base_s[0]:.4f}  close {base_s[1]:.1%}  n={base_s[2]}")
    base_v = score(field, valid_draws, BASE)
    print(f"control on VALIDATION set pct {base_v[0]:.4f}  close {base_v[1]:.1%}  n={base_v[2]}\n")

    rng = random.Random(args.seed)
    results = []
    for i in range(args.configs):
        cand = {**BASE, **sample(rng)}
        m, c, n = score(field, search_draws, cand)
        results.append((m - base_s[0], c - base_s[1], cand))
        print(f"  [{i+1:>3}/{args.configs}] search delta {m-base_s[0]:+.4f}  "
              f"close {c-base_s[1]:+.3f}", flush=True)

    results.sort(key=lambda r: -r[0])
    print(f"\nTop {args.keep} on the search set, now re-scored on games they were "
          f"NEVER selected on:\n")
    print(f"{'rank':>5s}{'search delta':>14s}{'VALIDATION delta':>18s}{'close delta':>13s}   verdict")
    survivors = []
    for rank, (d, dc, cand) in enumerate(results[:args.keep], 1):
        m, c, n = score(field, valid_draws, cand)
        vd = m - base_v[0]
        # Selection inflates the search delta; only the validation number counts.
        holds = vd > 0 and vd >= 0.4 * d
        if holds:
            survivors.append((vd, c - base_v[1], cand))
        print(f"{rank:>5d}{d:>+14.4f}{vd:>+18.4f}{c-base_v[1]:>+13.3f}   "
              f"{'HOLDS UP' if holds else 'was noise'}")
    print()
    if not survivors:
        print("NOTHING SURVIVED. Every apparent winner shrank or reversed on games it")
        print("was not selected on -- which is what selection on noise looks like, and")
        print("is the expected outcome when the true effects are near zero.")
        return 0
    survivors.sort(key=lambda r: -r[0])
    vd, dc, best = survivors[0]
    print(f"BEST SURVIVING CONFIG   validation delta {vd:+.4f} percentile "
          f"= {8000*vd:+.0f} rating-equivalent, close {dc:+.3f}")
    for k in sorted(SPACE):
        if best[k] != BASE.get(k):
            print(f"    {k}: {BASE.get(k, '(default)')} -> {best[k]}")
    print("\nThis is a CLONE result. The clone is well calibrated where we have")
    print("explored and silent where we have not, so treat it as a screen that")
    print("earns a live randomised A/B, never as a result on its own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
