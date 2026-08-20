#!/usr/bin/env python3
"""Exact seller policy for persuasion: backward induction over the fitted buyer.

Research-directed replacement for evolutionary search (commit 7a0ed3b): with an
explicit buyer-response table the seller's 20-round problem is a finite MDP --
state (round, lies-caught {0,1,2+}), decision only on LOW-quality rounds
(recommending a high is dominant: conversion is strictly higher on yes and a
truthful yes can never be caught). Backward induction solves it exactly.

Step 2 of the plan rides along: per-(mode, rec) calibration offsets computed by
replaying recent live seller rounds through the table and pinning predicted to
realized conversion (the localized -13pp residual; logit shift, applied to
every cell before planning).

Output: models/pers_policy_dp_v1.json
  policy[mode|p|ratio][lies][round] -> 1 (recommend the low) | 0 (honest no)
plus each cell's expected sale rate under the DP policy vs the current 0.8/2
baseline simulated under the SAME calibrated model -- the honest self-estimate
of the edge, to be validated on the instrument before any wider deploy.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.fit_buyers import rec_of                     # noqa: E402

TABLE = os.path.join(REPO, "models", "pers_buyer_response_v2.json")
OUT = os.path.join(REPO, "models", "pers_policy_dp_v1.json")
PS = {"lo": 1 / 3, "mid": 0.5, "hi": 0.8}
LIES = ("0", "1", "2+")


def logit(x):
    x = min(max(x, 1e-4), 1 - 1e-4)
    return math.log(x / (1 - x))


def inv(z):
    return 1 / (1 + math.exp(-z))


def calibration_offsets(table):
    """Replay recent live seller rounds; one logit offset per (mode, rec)."""
    import glob
    cut = time.time() - 8 * 3600
    pred = defaultdict(list)
    real = defaultdict(list)
    for path in glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl")):
        for line in open(path, encoding="utf-8", errors="replace").readlines()[-2500:]:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("ts", 0) < cut:
                continue
            f = d.get("final") or {}
            gs = f.get("game_state") or {}
            me = f.get("your_player")
            if (f.get("game_family") != "persuasion" or not me
                    or gs.get(f"{me}_role") != "seller" or gs.get("p") is None):
                continue
            mode = gs.get("seller_message_type") or "text"
            p = gs["p"]
            pb = "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")
            v = gs.get("v") or 0
            price = gs.get("product_price") or 1
            rb = min((1.2, 1.25, 2.0, 3.0, 4.0), key=lambda g: abs(g - v / price))
            lies = 0
            for rnd in gs.get("history") or []:
                rec = rec_of(rnd.get("seller_message"))
                if rec is None:
                    continue
                lb = "0" if lies == 0 else ("1" if lies == 1 else "2+")
                key = f"{mode}|{pb}|r{rb}|{'yes' if rec else 'no'}|{lb}"
                cell = table.get(key)
                if cell:
                    tag = (mode, "yes" if rec else "no")
                    pred[tag].append(cell["p"])
                    real[tag].append(1.0 if rnd.get("bought") else 0.0)
                if rnd.get("bought") and rec and str(rnd.get("quality")).lower() == "low":
                    lies += 1
    offs = {}
    for tag in pred:
        n = len(pred[tag])
        if n < 80:
            continue
        offs["|".join(tag)] = round(logit(sum(real[tag]) / n) - logit(sum(pred[tag]) / n), 4)
    return offs


def buy_p(table, offs, mode, pb, rb, rec, lb):
    key = f"{mode}|{pb}|r{rb}|{rec}|{lb}"
    key0 = f"{mode}|{pb}|r{rb}|{rec}|0"
    cell = table.get(key) or table.get(key0)
    if not cell:
        # fall back across ratio buckets
        for r2 in (1.2, 1.25, 2.0, 3.0, 4.0):
            cell = table.get(f"{mode}|{pb}|r{r2}|{rec}|{lb}")
            if cell:
                break
    base = cell["p"] if cell else (0.4 if rec == "yes" else 0.05)
    off = offs.get(f"{mode}|{rec}", 0.0)
    return inv(logit(base) + off)


def solve_cell(table, offs, mode, pb, rb, rounds=20):
    p = PS[pb]
    nxt = {lb: 0.0 for lb in LIES}
    policy = {lb: [0] * rounds for lb in LIES}
    exp_sales = None
    for r in range(rounds - 1, -1, -1):
        cur = {}
        for li, lb in enumerate(LIES):
            lb_up = LIES[min(li + 1, 2)]
            b_yes = buy_p(table, offs, mode, pb, rb, "yes", lb)
            b_no = buy_p(table, offs, mode, pb, rb, "no", lb)
            v_high = b_yes * 1.0 + nxt[lb]
            lie_v = b_yes * (1.0 + nxt[lb_up]) + (1 - b_yes) * nxt[lb]
            hon_v = b_no * 1.0 + nxt[lb]
            best = max(lie_v, hon_v)
            policy[lb][r] = 1 if lie_v > hon_v else 0
            cur[lb] = p * v_high + (1 - p) * best
        nxt = cur
        if r == 0:
            exp_sales = nxt["0"] / rounds
    return policy, exp_sales


def simulate_baseline(table, offs, mode, pb, rb, shading=0.8, rounds=20, iters=3000):
    """Current live seller (0.8 shading of the myopic lie budget) under the SAME model."""
    import random
    from glee_agent.strategies.persuasion import optimal_lie_rate
    p = PS[pb]
    price = 1.0
    v = {1.2: 1.2, 1.25: 1.25, 2.0: 2.0, 3.0: 3.0, 4.0: 4.0}[rb]
    q = optimal_lie_rate(p, v, 0.0, price) * shading
    rng = random.Random(11)
    tot = 0
    for _ in range(iters):
        lies = 0
        lied = 0
        lows = 0
        for r in range(rounds):
            lb = "0" if lies == 0 else ("1" if lies == 1 else "2+")
            high = rng.random() < p
            if high:
                rec = "yes"
            else:
                lows += 1
                rec = "yes" if (r >= 2 and lied < q * lows) else "no"
            b = buy_p(table, offs, mode, pb, rb, rec, lb)
            bought = rng.random() < b
            if bought:
                tot += 1
                if rec == "yes" and not high:
                    lies += 1
            if rec == "yes" and not high:
                lied += 1
    return tot / (iters * rounds)


def main() -> int:
    doc = json.load(open(TABLE))
    table = doc["table"]
    offs = calibration_offsets(table)
    out = {"_schema": "glee.pers_policy_dp/v1",
           "_built": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
           "calibration_offsets": offs, "cells": {}}
    print(f"calibration offsets (logit, pinned to last 8h live): {offs}")
    print(f"\n  {'cell':22s}{'DP sale rate':>13s}{'0.8/2 baseline':>15s}{'edge':>7s}  endgame-lie rounds")
    for mode in ("binary", "text"):
        for pb in ("lo", "mid", "hi"):
            for rb in (1.2, 1.25, 2.0, 3.0, 4.0):
                if not any(k.startswith(f"{mode}|{pb}|r{rb}|") for k in table):
                    continue
                pol, dp_rate = solve_cell(table, offs, mode, pb, rb)
                base = simulate_baseline(table, offs, mode, pb, rb)
                tail = sum(pol["0"][-5:])
                out["cells"][f"{mode}|{pb}|r{rb}"] = {
                    "policy": pol, "dp_sale_rate": round(dp_rate, 4),
                    "baseline_sale_rate": round(base, 4)}
                print(f"  {mode}|{pb}|r{rb:<6}{dp_rate:>12.1%}{base:>15.1%}"
                      f"{dp_rate-base:>+7.1%}  {tail}/5 final rounds lie (state 0)")
    tmp = OUT + ".tmp"
    json.dump(out, open(tmp, "w"), indent=1)
    os.replace(tmp, OUT)
    print(f"\n-> {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
