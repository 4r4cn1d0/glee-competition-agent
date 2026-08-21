#!/usr/bin/env python3
"""Persuasion seller DP v3: exogenous state, percentile objective.

Two changes from v1, each aimed at one of the two reasons v1 lost 13pp live.

1. STATE.  v1's trust coordinate was lies CAUGHT, which only increments when the
   buyer bought -- an outcome, not a control.  Planning against it, the DP read
   "conversion rises after caught lies" as the consequence of lying and shipped
   the always-lie policy in all 30 cells.  v3's state is the seller's own record:
   L = lies told, n = declines shown, t = rounds elapsed.  The planner moves
   those by acting, they are exogenous in the fitted data, and the v3 buyer model
   (models/pers_buyer_response_v3*.json) prices them.

2. OBJECTIVE.  v1 maximised expected SALES.  The rating currency is the
   percentile of payoff within the game's configuration cell, and
   models/percentile_cdf_v3.json now carries persuasion seller cells.  Percentile
   is a monotone but very non-linear function of sales -- in text|mid|r3.0 the
   step from 16 to 20 sales is worth 0.42 of percentile while the step from 4 to
   8 is worth 0.03 -- so the risk profile a sales-maximiser wants and the one a
   percentile-maximiser wants are different policies.  Solving for percentile
   needs cumulative sales S in the state, which is why the v3 policy is indexed
   by S and v1's was not.

State (t, L, n, S); high-quality rounds are always recommended (a truthful yes
converts strictly better and cannot be caught), so the only decision is on LOW
rounds: recommend it (L+1) or decline (n+1).

Output: models/pers_policy_dp_v3.json
  cells["mode|pb|rratio"]["policy"]["t|L|n"] = a string of '0'/'1' indexed by S,
  '1' meaning recommend the low unit.  The action is very nearly monotone in S
  (a threshold: gamble while few sales are banked and the CDF is still convex,
  protect the total once it is not) but not exactly -- 0.3% to 2.8% of states
  per cell break it -- so the exact action is stored rather than a threshold
  that would be right almost always and silently wrong in the corners.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.fit_buyers_v3 import predict, load as load_buyers   # noqa: E402
from glee_agent.strategies.persuasion import optimal_lie_rate    # noqa: E402
from sim.percentile import percentile                            # noqa: E402

OUT = os.path.join(REPO, "models", "pers_policy_dp_v3.json")
PS = {"lo": 1 / 3, "mid": 0.5, "hi": 0.8}
RATIOS = (1.2, 1.25, 2.0, 3.0, 4.0)
ROUNDS = 20


def terminal_values(mode, pb, rb, objective):
    """Value of ending with S sales, S = 0..ROUNDS."""
    price = 1.0
    params = {"product_price": price, "p": PS[pb], "v": rb * price,
              "total_rounds": ROUNDS, "seller_message_type": mode}
    if objective == "sales":
        return [s / ROUNDS for s in range(ROUNDS + 1)]
    vals = []
    for s in range(ROUNDS + 1):
        q = percentile("persuasion", params, "player_1", price * s)
        vals.append(q)
    if any(v is None for v in vals):
        return None
    return vals


def buy_table(buyers, mode, pb, rb, qstar):
    """P(buy) for every (rec, L, n, t) the solver can reach."""
    tab = {}
    for t in range(ROUNDS):
        for n in range(t + 1):
            for L in range(t - n + 1):
                for rec in (True, False):
                    p = predict(buyers, mode, pb, rb, rec, L, n, t, qstar)
                    tab[(rec, L, n, t)] = 0.0 if p is None else p
    return tab


def solve_cell(buyers, mode, pb, rb, objective="percentile"):
    """Backward induction over (t, L, n, S).  Returns (thresholds, E[value])."""
    term = terminal_values(mode, pb, rb, objective)
    if term is None:
        return None
    p = PS[pb]
    qstar = optimal_lie_rate(p, rb, 0.0, 1.0)
    tab = buy_table(buyers, mode, pb, rb, qstar)

    # V[(L, n)][S] at the START of round t
    V = {}
    for n in range(ROUNDS + 1):
        for L in range(ROUNDS + 1 - n):
            V[(L, n)] = list(term)
    thresh = {}
    for t in range(ROUNDS - 1, -1, -1):
        nxt = V
        V = {}
        for n in range(t + 1):
            for L in range(t - n + 1):
                cur = [0.0] * (ROUNDS + 1)
                b_hi = tab[(True, L, n, t)]
                b_lie = b_hi
                b_no = tab[(False, L, n, t)]
                v_same = nxt[(L, n)]
                v_lie = nxt[(L + 1, n)]
                v_no = nxt[(L, n + 1)]
                lie_at = []
                for S in range(t + 1):
                    S1 = min(S + 1, ROUNDS)
                    # high quality: recommend (dominant), buyer buys w.p. b_hi
                    high = b_hi * v_same[S1] + (1 - b_hi) * v_same[S]
                    # low quality: lie (L+1) or decline (n+1)
                    lie = b_lie * v_lie[S1] + (1 - b_lie) * v_lie[S]
                    hon = b_no * v_no[S1] + (1 - b_no) * v_no[S]
                    lie_at.append(lie > hon + 1e-12)
                    cur[S] = p * high + (1 - p) * max(lie, hon)
                for S in range(t + 1, ROUNDS + 1):
                    cur[S] = cur[t] if t >= 0 else 0.0
                V[(L, n)] = cur
                thresh[f"{t}|{L}|{n}"] = "".join("1" if x else "0" for x in lie_at)
        # unreachable (L, n) pairs still need entries for the next step back
        for n in range(ROUNDS + 1):
            for L in range(ROUNDS + 1 - n):
                V.setdefault((L, n), list(term))
    return thresh, V[(0, 0)][0], qstar


def monotonicity_report(buyers, mode, pb, rb):
    """How often the optimal action is NOT monotone in S (threshold is a lie)."""
    term = terminal_values(mode, pb, rb, "percentile")
    if term is None:
        return None
    p = PS[pb]
    qstar = optimal_lie_rate(p, rb, 0.0, 1.0)
    tab = buy_table(buyers, mode, pb, rb, qstar)
    V = {}
    for n in range(ROUNDS + 1):
        for L in range(ROUNDS + 1 - n):
            V[(L, n)] = list(term)
    bad = tot = 0
    for t in range(ROUNDS - 1, -1, -1):
        nxt, V = V, {}
        for n in range(t + 1):
            for L in range(t - n + 1):
                cur = [0.0] * (ROUNDS + 1)
                b_hi = tab[(True, L, n, t)]
                b_no = tab[(False, L, n, t)]
                v_same, v_lie, v_no = nxt[(L, n)], nxt[(L + 1, n)], nxt[(L, n + 1)]
                acts = []
                for S in range(t + 1):
                    S1 = min(S + 1, ROUNDS)
                    high = b_hi * v_same[S1] + (1 - b_hi) * v_same[S]
                    lie = b_hi * v_lie[S1] + (1 - b_hi) * v_lie[S]
                    hon = b_no * v_no[S1] + (1 - b_no) * v_no[S]
                    acts.append(lie > hon + 1e-12)
                    cur[S] = p * high + (1 - p) * max(lie, hon)
                for S in range(t + 1, ROUNDS + 1):
                    cur[S] = cur[t]
                V[(L, n)] = cur
                tot += 1
                # monotone means acts is a run of True then a run of False
                if acts and any(acts[i] and not acts[i - 1] for i in range(1, len(acts))):
                    bad += 1
        for n in range(ROUNDS + 1):
            for L in range(ROUNDS + 1 - n):
                V.setdefault((L, n), list(term))
    return bad, tot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--buyers", default=os.path.join(
        REPO, "models", "pers_buyer_response_v3_all.json"))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--objective", default="percentile",
                    choices=("percentile", "sales"))
    ap.add_argument("--monotonicity", action="store_true")
    args = ap.parse_args()

    buyers = load_buyers(args.buyers)
    out = {"_schema": "glee.pers_policy_dp/v3",
           "_buyers": os.path.basename(args.buyers),
           "_objective": args.objective,
           "_note": ("state is (round, lies TOLD, declines SHOWN, sales); the "
                     "v1 lies-CAUGHT coordinate was an outcome and inverted the "
                     "sign of the lie gradient"),
           "rounds": ROUNDS, "cells": {}}
    print(f"buyers: {os.path.basename(args.buyers)}   objective: {args.objective}\n")
    print(f"  {'cell':18s}{'E[value]':>10}{'q*':>7}   lie-through-S* at "
          f"(L=0,n=0) by round")
    for mode in ("binary", "text"):
        for pb in ("lo", "mid", "hi"):
            for rb in RATIOS:
                r = solve_cell(buyers, mode, pb, rb, args.objective)
                if r is None:
                    print(f"  {mode}|{pb}|r{rb:<6} -- no percentile cell, skipped")
                    continue
                thresh, val, qstar = r
                key = f"{mode}|{pb}|r{rb}"
                out["cells"][key] = {"policy": thresh, "value": round(val, 4),
                                     "qstar": round(qstar, 4)}
                sig = ""
                for t in range(ROUNDS):
                    a = thresh.get(f"{t}|0|0", "0")
                    sig += "L" if a == "1" * len(a) else (
                        "." if "1" not in a else "t")
                print(f"  {key:18s}{val:>10.4f}{qstar:>7.2f}   {sig}")
                if args.monotonicity:
                    bad, tot = monotonicity_report(buyers, mode, pb, rb)
                    if bad:
                        print(f"      non-monotone in S: {bad}/{tot} states")
    print("\n  L = lie at every sales count, . = never lie, t = threshold in S")
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    os.replace(tmp, args.out)
    print(f"\n-> {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
