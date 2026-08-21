#!/usr/bin/env python3
"""The persuasion message fix, read as a difference-in-differences.

The treated cell is (seller, p=0.8, TEXT), which scored at the 0.3657 percentile
over 24h against 0.5368 for the SAME configuration in binary mode -- about 926
rating-equivalent in that cell, dragging the family by roughly -75 rating. Cause:
dispatch.py recomposed action["message"] from the template bank, so the message
that IS the recommendation in text mode was replaced every turn and
GLEE_PERS_MSG_STYLE was inert.

BINARY-mode games are untouched by GLEE_PERS_KEEP_MSG, so they are a concurrent
control for field drift. Reporting both means a rise in text that is really the
whole field moving cannot be mistaken for the fix working.

Reports MEAN and SD, because the operator's bar is improvement AND lower
variance -- a change that lifts the average while widening the spread is not a
win here, since the rating is an average over games and a fat lower tail is what
produces the -80 swings.

    python scripts/pers_cell.py --hours 24
    python scripts/pers_cell.py --split <unix_ts>     # before vs after the fix
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.percentile import percentile          # noqa: E402

NAMES = {"champion": "Test 1", "hardliner": "Test 2", "conceder": "Test 3",
         "composite": "Agent 5"}


def rows(hours):
    cut = time.time() - hours * 3600
    for path in glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl")):
        slot = os.path.basename(os.path.dirname(path))
        if slot not in NAMES:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                ts = rec.get("ts", 0)
                if ts < cut:
                    continue
                fin = rec.get("final") or {}
                if fin.get("game_family") != "persuasion":
                    continue
                seat = fin.get("your_player")
                if seat != "player_1":            # seller seat only
                    continue
                gs = fin.get("game_state") or {}
                res = fin.get("result") or {}
                pay = res.get(f"{seat}_payoff", res.get("your_payoff"))
                if not isinstance(pay, (int, float)):
                    continue
                p = percentile("persuasion", dict(gs), seat, float(pay))
                if p is None:
                    continue
                mode = gs.get("seller_message_type") or "text"
                prior = round(gs.get("p") or 0, 2)
                yield slot, ts, prior, mode, p


def describe(xs):
    n = len(xs)
    if n < 2:
        return None
    m = statistics.mean(xs)
    sd = statistics.pstdev(xs)
    half = 1.96 * sd / math.sqrt(n)
    return m, sd, half, n


def show(label, data):
    d = describe(data)
    if not d:
        print(f"  {label:34} n too small ({len(data)})")
        return None
    m, sd, half, n = d
    print(f"  {label:34} mean {m:.4f} +/-{half:.4f}   sd {sd:.4f}   n={n:>5}")
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--split", type=float, default=None)
    args = ap.parse_args()
    data = list(rows(args.hours))
    if not data:
        print("no scoreable seller persuasion games in window")
        return 1

    def sel(mode, lo=None, hi=None, prior=0.8):
        return [p for _s, ts, pr, md, p in data
                if md == mode and pr == prior
                and (lo is None or ts >= lo) and (hi is None or ts < hi)]

    print(f"SELLER persuasion, prior p=0.8, last {args.hours:g}h")
    if args.split:
        print("\nTREATED cell (text) -- the fix applies here:")
        b = show("before", sel("text", hi=args.split))
        a = show("after ", sel("text", lo=args.split))
        print("\nCONTROL cell (binary) -- untouched by the flag:")
        cb = show("before", sel("binary", hi=args.split))
        ca = show("after ", sel("binary", lo=args.split))
        if b and a and cb and ca:
            did = (a[0] - b[0]) - (ca[0] - cb[0])
            se = math.sqrt(sum((x[2] / 1.96) ** 2 for x in (a, b, ca, cb)))
            print(f"\n  text change      {a[0]-b[0]:+.4f}")
            print(f"  binary change    {ca[0]-cb[0]:+.4f}   (field drift)")
            print(f"  DIFF-IN-DIFF     {did:+.4f} +/-{1.96*se:.4f}"
                  f"   -> {'REAL' if abs(did) > 1.96*se else 'not distinguishable yet'}")
            print(f"  variance in the treated cell: sd {b[1]:.4f} -> {a[1]:.4f} "
                  f"({'LOWER, good' if a[1] < b[1] else 'HIGHER, bad'})")
        return 0

    show("text   (treated)", sel("text"))
    show("binary (control)", sel("binary"))
    print("\nby agent, text cell:")
    per = defaultdict(list)
    for s, ts, pr, md, p in data:
        if md == "text" and pr == 0.8:
            per[s].append(p)
    for s, v in sorted(per.items(), key=lambda kv: -len(kv[1])):
        show(NAMES[s], v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
