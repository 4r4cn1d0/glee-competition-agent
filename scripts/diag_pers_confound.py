#!/usr/bin/env python3
"""The confound that killed the persuasion DP: the trust coordinate is an OUTCOME.

The v1 buyer table is P(buy | mode, p, ratio, rec, lies-CAUGHT).  A lie is only
"caught" when the buyer BOUGHT a recommended low unit -- so the caught-lie
counter is a running tally of how gullible this particular buyer has proven to
be, not a measure of how much trust we have spent.  Pooled across buyers it
reads as "conversion RISES to 80% after two caught lies", and the DP, taking
that as the causal transition of its own action, concludes lying is not merely
free but self-reinforcing.  Hence the degenerate always-lie policy, and hence
-13pp live.

This script separates the two by holding the buyer identity fixed:

  A. between buyers: how much of the caught-lie gradient is just buyer type?
  B. within buyer  : the same gradient re-estimated inside each opponent name,
                     pooled by inverse-variance -- the coefficient the DP
                     actually needs.
  C. within buyer, within game-cell: our own fleet arms run different lie
     shadings against a randomly assigned field, so arm is a quasi-experiment
     on lie rate; sale rate per arm is the causal read.
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


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, c - h, c + h)


def main() -> int:
    rounds = [r for r in iter_rounds() if r["rec"]]
    print(f"# {len(rounds):,} rounds where we recommended, "
          f"{len({r['opponent'] for r in rounds if r['opponent']})} named opponents\n")

    # ---- A. between-buyer heterogeneity ------------------------------------
    by_name = defaultdict(list)
    for r in rounds:
        if r["opponent"]:
            by_name[r["opponent"]].append(r)
    print("A. between-buyer heterogeneity in P(buy|yes) -- the confounder:")
    rates = []
    for name, rs in sorted(by_name.items(), key=lambda kv: -len(kv[1])):
        if len(rs) < 200:
            continue
        k = sum(1 for r in rs if r["bought"])
        rates.append((k / len(rs), name, len(rs)))
    rates.sort()
    for p, name, n in rates[:4] + rates[-4:]:
        print(f"   {name:28s} n={n:>6}  P(buy|yes)={p:.1%}")
    if rates:
        print(f"   spread across {len(rates)} buyers with n>=200: "
              f"{rates[0][0]:.1%} .. {rates[-1][0]:.1%}\n")

    # ---- B. the caught-lie gradient, pooled vs within-buyer ----------------
    def gradient(rs):
        """P(buy|yes, caught>=2) - P(buy|yes, caught==0) on a set of rounds."""
        a = [1.0 if r["bought"] else 0.0 for r in rs if r["caught"] >= 2]
        b = [1.0 if r["bought"] else 0.0 for r in rs if r["caught"] == 0]
        if len(a) < 25 or len(b) < 25:
            return None
        return (sum(a) / len(a) - sum(b) / len(b), len(a), len(b))

    g = gradient(rounds)
    print(f"B. caught-lie gradient  P(buy|2+ caught) - P(buy|0 caught)")
    print(f"   POOLED across buyers      : {g[0]:+.1%}   "
          f"(n={g[1]:,} / {g[2]:,})   <- what v1 planned against")

    # within-name, inverse-variance pooled
    num = den = 0.0
    per = []
    for name, rs in by_name.items():
        a = [1.0 if r["bought"] else 0.0 for r in rs if r["caught"] >= 2]
        b = [1.0 if r["bought"] else 0.0 for r in rs if r["caught"] == 0]
        if len(a) < 25 or len(b) < 25:
            continue
        pa, pb_ = sum(a) / len(a), sum(b) / len(b)
        var = pa * (1 - pa) / len(a) + pb_ * (1 - pb_) / len(b)
        if var <= 0:
            continue
        per.append((name, pa - pb_, len(a) + len(b)))
        num += (pa - pb_) / var
        den += 1 / var
    if den:
        est = num / den
        se = math.sqrt(1 / den)
        print(f"   WITHIN buyer (fixed effect): {est:+.1%}  "
              f"[{est-1.96*se:+.1%}, {est+1.96*se:+.1%}]  "
              f"({len(per)} buyers)   <- the causal read")
        print(f"   -> {100*(1 - est/g[0]):.0f}% of the pooled gradient is buyer "
              f"identity, not our lying.")
    pos = sum(1 for _, d, _ in per if d > 0)
    print(f"   sign within buyer: {pos}/{len(per)} positive\n")

    # same within (buyer, mode, p-bin, ratio) cell -- the DP's own cell
    num = den = 0.0
    cells = 0
    by_cell = defaultdict(list)
    for r in rounds:
        if r["opponent"]:
            by_cell[(r["opponent"], r["mode"], r["pb"], r["rb"])].append(r)
    for key, rs in by_cell.items():
        a = [1.0 if r["bought"] else 0.0 for r in rs if r["caught"] >= 2]
        b = [1.0 if r["bought"] else 0.0 for r in rs if r["caught"] == 0]
        if len(a) < 20 or len(b) < 20:
            continue
        pa, pb_ = sum(a) / len(a), sum(b) / len(b)
        var = pa * (1 - pa) / len(a) + pb_ * (1 - pb_) / len(b) + 1e-6
        per_ = pa - pb_
        num += per_ / var
        den += 1 / var
        cells += 1
    if den:
        est = num / den
        se = math.sqrt(1 / den)
        print(f"   WITHIN (buyer x mode x p x ratio): {est:+.1%} "
              f"[{est-1.96*se:+.1%}, {est+1.96*se:+.1%}]  ({cells} cells)\n")

    # ---- C. arm-level quasi-experiment on the whole game -------------------
    print("C. game-level: does a higher realised lie rate buy more sales?")
    print("   (per game, within (mode,p,ratio) cell and opponent; lie rate = "
           "share of LOW rounds we recommended)")
    games = defaultdict(list)
    for r in iter_rounds():
        games[r["game_id"]].append(r)
    rows = []
    for gid, rs in games.items():
        lows = [r for r in rs if r["quality"] == "low"]
        if len(lows) < 4:
            continue
        lie_rate = sum(1 for r in lows if r["rec"]) / len(lows)
        sale = sum(1 for r in rs if r["bought"]) / len(rs)
        rows.append(((rs[0]["opponent"], rs[0]["mode"], rs[0]["pb"], rs[0]["rb"]),
                     lie_rate, sale))
    strata = defaultdict(list)
    for key, lr, sale in rows:
        strata[key].append((lr, sale))
    num = den = 0.0
    n_str = 0
    for key, vals in strata.items():
        hi = [s for lr, s in vals if lr >= 0.9]
        lo = [s for lr, s in vals if lr <= 0.6]
        if len(hi) < 8 or len(lo) < 8:
            continue
        mh, ml = sum(hi) / len(hi), sum(lo) / len(lo)
        vh = sum((x - mh) ** 2 for x in hi) / max(len(hi) - 1, 1) / len(hi)
        vl = sum((x - ml) ** 2 for x in lo) / max(len(lo) - 1, 1) / len(lo)
        var = vh + vl + 1e-9
        num += (mh - ml) / var
        den += 1 / var
        n_str += 1
    if den:
        est, se = num / den, math.sqrt(1 / den)
        print(f"   stratified sale-rate delta (lie>=0.9 minus lie<=0.6): "
              f"{est:+.1%} [{est-1.96*se:+.1%}, {est+1.96*se:+.1%}] "
              f"over {n_str} strata")
    else:
        print("   too few strata with both arms")

    # unstratified, for the contrast
    hi = [s for _, lr, s in rows if lr >= 0.9]
    lo = [s for _, lr, s in rows if lr <= 0.6]
    print(f"   UNstratified: {sum(hi)/len(hi):.1%} (n={len(hi)}) vs "
          f"{sum(lo)/len(lo):.1%} (n={len(lo)}) = "
          f"{sum(hi)/len(hi)-sum(lo)/len(lo):+.1%}  <- the same confound at game level")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
