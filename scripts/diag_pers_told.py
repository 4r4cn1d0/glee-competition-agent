#!/usr/bin/env python3
"""lies TOLD vs lies CAUGHT: the coordinate swap that makes the DP identifiable.

The v1 buyer table conditions on lies CAUGHT.  A lie is caught only when the
buyer BOUGHT a recommended low unit, so the counter is a function of the
buyer's own purchase history: conditioning on it selects for buyers who are
buying.  Pooled, that reads as "conversion rises to 80% after two caught lies",
and a DP that takes the table as its transition kernel concludes lying is
self-reinforcing.  It shipped the always-lie policy and lost 13pp.

lies TOLD is the same information minus the selection.  Under the shading
heuristic the seller's recommendation at round t is a deterministic function of
(cell, q*, the quality sequence nature drew) -- it does not read the buyer at
all in the knows-values branch.  So the count of lies told by round t is
EXOGENOUS: independent of buyer type given the cell.  Regressing purchase on it
identifies the causal price of lying, which is what a planner needs.

This script shows the two gradients side by side on the same rounds.
"""
from __future__ import annotations

import math
import os
import random
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.pers_data import iter_rounds   # noqa: E402
from scripts.diag_pers_window import DP_LO, DP_HI   # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, c - h, c + h)


def told_rounds():
    """Heuristic-era rounds, carrying the exogenous lies-TOLD counter."""
    out = []
    cur = None
    told = 0
    for r in iter_rounds():
        if r["ts"] and DP_LO <= r["ts"] < DP_HI and r["agent"] == "conceder":
            continue                      # the DP window is not heuristic data
        if r["game_id"] != cur:
            cur, told = r["game_id"], 0
        r = dict(r, told=told)
        out.append(r)
        if r["rec"] and r["quality"] == "low":
            told += 1
    return out


def strat_delta(rows, key_of, hi_of, lo_of, min_n=15):
    """Stratified (inverse-variance) difference in P(buy), hi-group minus lo."""
    strata = defaultdict(lambda: ([], []))
    for r in rows:
        y = 1.0 if r["bought"] else 0.0
        if hi_of(r):
            strata[key_of(r)][0].append(y)
        elif lo_of(r):
            strata[key_of(r)][1].append(y)
    num = den = 0.0
    n_s = 0
    for a, b in strata.values():
        if len(a) < min_n or len(b) < min_n:
            continue
        pa, pb = sum(a) / len(a), sum(b) / len(b)
        var = pa * (1 - pa) / len(a) + pb * (1 - pb) / len(b) + 1e-6
        num += (pa - pb) / var
        den += 1 / var
        n_s += 1
    if not den:
        return None
    est, se = num / den, math.sqrt(1 / den)
    return est, est - 1.96 * se, est + 1.96 * se, n_s


def main() -> int:
    rows = [r for r in told_rounds() if r["rec"]]
    print(f"# {len(rows):,} heuristic-era rounds where we recommended\n")

    # stratify on everything exogenous the DP also conditions on
    key = lambda r: (r["mode"], r["pb"], r["rb"], min(r["i"] // 5, 3))

    print("P(buy | we recommend), stratified by (mode, prior, ratio, round-block).")
    print("Same rounds, same strata -- only the trust coordinate changes.\n")
    for tag, hi, lo in (
        ("lies CAUGHT   2+ vs 0", lambda r: r["caught"] >= 2, lambda r: r["caught"] == 0),
        ("lies TOLD     2+ vs 0", lambda r: r["told"] >= 2, lambda r: r["told"] == 0),
        ("lies TOLD     4+ vs 0", lambda r: r["told"] >= 4, lambda r: r["told"] == 0),
    ):
        d = strat_delta(rows, key, hi, lo)
        if d:
            print(f"  {tag:24s} {d[0]:+7.1%}  [{d[1]:+.1%}, {d[2]:+.1%}]  "
                  f"({d[3]} strata)")
    print()
    print("  CAUGHT reads positive because it is an outcome -- it only ticks up")
    print("  when the buyer bought.  TOLD is a function of nature's quality draw")
    print("  and our fixed lie budget, so it is exogenous, and it prices lying")
    print("  the way a planner needs: negative.\n")

    # ---- the shape of the TOLD gradient, for the solver --------------------
    print("P(buy | we recommend) by lies TOLD so far (all strata pooled):")
    for t in range(0, 8):
        v = [r for r in rows if (r["told"] == t if t < 7 else r["told"] >= 7)]
        if len(v) < 100:
            continue
        p, lo_, hi_ = wilson(sum(1 for r in v if r["bought"]), len(v))
        bar = "#" * int(p * 50)
        print(f"  told={t if t<7 else '7+':>2}  n={len(v):>6}  {p:5.1%} "
              f"[{lo_:.1%},{hi_:.1%}]  {bar}")
    print()

    # per mode, since the solver runs per mode
    print("per mode (stratified 2+ vs 0 told):")
    for mode in ("binary", "text"):
        sub = [r for r in rows if r["mode"] == mode]
        d = strat_delta(sub, key, lambda r: r["told"] >= 2, lambda r: r["told"] == 0)
        if d:
            print(f"  {mode:8s} {d[0]:+7.1%}  [{d[1]:+.1%}, {d[2]:+.1%}]  ({d[3]} strata)")
    print()

    # ---- placebo: told counter should not predict FUTURE quality ----------
    hi = [1.0 if r["quality"] == "high" else 0.0 for r in rows if r["told"] >= 2]
    lo = [1.0 if r["quality"] == "high" else 0.0 for r in rows if r["told"] == 0]
    print(f"placebo (exogeneity check): P(this round is HIGH | told>=2) = "
          f"{sum(hi)/len(hi):.1%} vs {sum(lo)/len(lo):.1%} at told=0 -- the "
          f"counter\n  tracks the quality draw, so the raw contrast must be read "
          f"inside strata, which\n  is what the table above does.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
