#!/usr/bin/env python3
"""The DP deploy window, read back off the live logs.

Test 3 (logs/conceder) ran the v1 DP policy from ~04:00Z to ~07:00Z on
2026-08-21: realised lie rate on LOW rounds pinned at 100%, against three
concurrent control arms at their usual 60-70%.  This script isolates those
games and asks the one question the fitted table could not answer -- what
happens to conversion as a function of the RECOMMENDATION RECORD the buyer has
seen, which is the coordinate the always-lie policy destroys.

The DP's state was (round, lies-CAUGHT).  A lie is only caught when the buyer
buys, so within a game that counter is a running tally of the buyer's own
purchases: conditioning on it selects the games that were going well.  The
coordinate the seller actually controls -- how many times it has said "no" --
is absent, and it is the one that pays.
"""
from __future__ import annotations

import math
import os
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.pers_data import iter_rounds, iter_games   # noqa: E402

# 2026-08-21 04:00Z .. 07:00Z, the window Test 3 ran the DP.
DP_LO = 1787284800.0
DP_HI = 1787295600.0


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, c - h, c + h)


def main() -> int:
    rounds = [r for r in iter_rounds() if r["ts"]]
    dp = [r for r in rounds
          if DP_LO <= r["ts"] < DP_HI and r["agent"] == "conceder"]
    ctl = [r for r in rounds
           if DP_LO <= r["ts"] < DP_HI and r["agent"] != "conceder"]
    print(f"# DP window {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime(DP_LO))} "
          f"-> {time.strftime('%H:%MZ', time.gmtime(DP_HI))}")
    for tag, rs in (("DP (Test 3)", dp), ("control arms", ctl)):
        lows = [r for r in rs if r["quality"] == "low"]
        lie = sum(1 for r in lows if r["rec"]) / max(len(lows), 1)
        p, lo, hi = wilson(sum(1 for r in rs if r["bought"]), len(rs))
        gids = len({r["game_id"] for r in rs})
        print(f"  {tag:14s} games={gids:>4}  rounds={len(rs):>5}  "
              f"lie-rate-on-lows={lie:5.1%}  sale-rate={p:5.1%} [{lo:.1%},{hi:.1%}]")
    print()

    # ---- conversion vs the buyer-visible record ---------------------------
    print("Conversion against the recommendation record the buyer has seen.")
    print("The DP arm ran a pure yes-stream; the control arms interleave 'no's.\n")
    print(f"  {'rounds seen':>12} {'DP P(buy|yes)':>15} {'n':>6}   "
          f"{'control P(buy|yes)':>19} {'n':>6}")
    for lo_, hi_ in ((0, 3), (4, 7), (8, 11), (12, 15), (16, 19)):
        row = [f"  {f'{lo_}-{hi_}':>12}"]
        for rs in (dp, ctl):
            v = [r for r in rs if r["rec"] and lo_ <= r["seen"] <= hi_]
            if len(v) < 20:
                row.append(f"{'--':>15} {len(v):>6}")
                continue
            p, a, b = wilson(sum(1 for r in v if r["bought"]), len(v))
            row.append(f"{p:>14.1%}  {len(v):>6}")
        print("   ".join(row))
    print()

    # ---- the decisive contrast: same buyer-visible round, different record --
    print("Same thing on the FULL corpus, controlling for round index --")
    print("P(buy | we recommend) by how many 'no's the buyer has already seen:\n")
    all_rec = [r for r in iter_rounds() if r["rec"]]
    print(f"  {'round':>7} " + "".join(f"{f'{k} nos':>13}" for k in (0, 1, 2, 3)))
    for lo_, hi_ in ((4, 7), (8, 11), (12, 15), (16, 19)):
        cells = []
        for k in (0, 1, 2, 3):
            v = [r for r in all_rec if lo_ <= r["i"] <= hi_
                 and (r["nos_seen"] == k if k < 3 else r["nos_seen"] >= 3)]
            if len(v) < 40:
                cells.append(f"{'--':>13}")
            else:
                p, _, _ = wilson(sum(1 for r in v if r["bought"]), len(v))
                cells.append(f"{p:>9.1%}({len(v)//1000}k)" if len(v) >= 1000
                             else f"{p:>10.1%}   ")
        print(f"  {f'{lo_}-{hi_}':>7} " + "".join(cells))
    print("\n  A 'no' the buyer has seen is worth more conversion than the sale it "
          "\n  cost, and the v1 state space has no coordinate for it.")

    # ---- what the DP arm's games looked like end to end -------------------
    print("\nPer-game outcome in the window (sales out of 20):")
    for tag, agent in (("DP (Test 3)", True), ("control", False)):
        sales = []
        for meta, hist in iter_games():
            if not meta["ts"] or not (DP_LO <= meta["ts"] < DP_HI):
                continue
            if (meta["agent"] == "conceder") != agent:
                continue
            sales.append(sum(1 for h in hist if h.get("bought")) / max(len(hist), 1))
        if not sales:
            continue
        sales.sort()
        n = len(sales)
        print(f"  {tag:12s} n={n:>4}  mean={sum(sales)/n:.1%}  "
              f"p25={sales[n//4]:.0%}  median={sales[n//2]:.0%}  "
              f"p75={sales[3*n//4]:.0%}  "
              f"share of games below 20% sold={sum(1 for s in sales if s < 0.2)/n:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
