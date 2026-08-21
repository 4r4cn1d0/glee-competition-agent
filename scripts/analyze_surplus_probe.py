#!/usr/bin/env python3
"""The causal frontier P(accept | surplus share) from the randomised probe.

Reads live turns.jsonl for probe assignments and the matching per-game files
for what the opponent did NEXT, then reports acceptance/counter/walk rates by
arm. This is the statistic the observational "closes at 60-65% earn +4.68"
result cannot provide: that number conditions on a deal having happened and is
blind to the rejections a greedier ask causes -- the same survivorship trap
that made one-round asks at 0.90/0.95 look optimal before the arena measured
them clearly worse.

Usage: .venv/bin/python scripts/analyze_surplus_probe.py [slot ...]
"""
from __future__ import annotations

import collections
import glob
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wilson(k: int, n: int):
    if n == 0:
        return float("nan"), 0.0, 0.0
    p = k / n
    z = 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def main() -> int:
    slots = sys.argv[1:] or ["champion", "hardliner", "conceder", "composite"]
    # assignment: (game_id, round) -> x
    assign: dict[tuple[str, int], float] = {}
    for slot in slots:
        path = os.path.join(REPO, "logs", slot, "turns.jsonl")
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8", errors="replace"):
            if '"surplus_probe"' not in line:
                continue
            try:
                t = json.loads(line)
            except ValueError:
                continue
            pr = (t.get("plan") or {}).get("surplus_probe")
            if not pr:
                continue
            gid = t.get("game_id")
            rnd = (t.get("state") or {}).get("round")
            if gid and rnd:
                assign[(gid, int(rnd))] = pr["x"]
    if not assign:
        print("no probe assignments found -- is GLEE_NEGO_SURPLUS_PROBE set on a live slot?")
        return 1

    out = collections.defaultdict(lambda: collections.Counter())
    for slot in slots:
        for fp in glob.glob(os.path.join(REPO, "logs", slot, "games", "*.json")):
            try:
                d = json.load(open(fp, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if d.get("game_family") != "negotiation":
                continue
            gid = d.get("game_id")
            me = d.get("your_player")
            hist = d.get("history") or []
            for i, h in enumerate(hist):
                rnd = h.get("round")
                x = assign.get((gid, int(rnd or 0)))
                if x is None:
                    continue
                # the opponent's response to OUR offer in this round
                dec = str(h.get("decision") or "").lower()
                if "accept" in dec:
                    out[x]["accept"] += 1
                elif "walk" in dec:
                    out[x]["walk"] += 1
                else:
                    out[x]["counter"] += 1
    print(f"{len(assign)} probe assignments; responses observed:\n")
    print(f"{'share x':>9s}{'n':>6s}{'P(accept)':>22s}{'P(counter)':>12s}{'P(walk)':>10s}")
    for x in sorted(out):
        c = out[x]
        n = sum(c.values())
        p, lo, hi = wilson(c["accept"], n)
        print(f"{x:>9.2f}{n:>6d}{p:>10.1%} [{lo:.0%},{hi:.0%}]"
              f"{c['counter']/max(n,1):>12.0%}{c['walk']/max(n,1):>10.0%}")
    print("\nThe frontier is P(accept) against x. Expected value of an arm is")
    print("P(accept)*x (plus the continuation value of a counter), so the best x")
    print("is NOT the highest P(accept) nor the highest x -- it is the product's peak.")
    print("\nexpected immediate surplus captured (P(accept) * x):")
    for x in sorted(out):
        c = out[x]
        n = sum(c.values())
        p, _, _ = wilson(c["accept"], n)
        print(f"  x={x:.2f}  {p * x:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
