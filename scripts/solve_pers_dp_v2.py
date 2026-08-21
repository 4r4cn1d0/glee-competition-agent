#!/usr/bin/env python3
"""Per-archetype DP seller policies: the same exact induction, four opponents.

The v1 policy plans against the AVERAGE buyer. The archetype clustering
(models/pers_buyer_archetypes_v1.json) says the average is a fiction: 16 of 33
named buyers keep buying at ~0.92 on a recommendation after catching two lies,
while a small skeptic cluster drops toward 0.57. One policy for both leaves
sales on the table against the forgiving majority and burns trust against the
skeptics. This solver reruns the v1 backward induction once per archetype,
against that archetype's POOLED response table (global table as fallback for
its thin cells), and ships a dispatch map from opponent name to archetype.

Output: models/pers_policy_dp_v2.json
  cells["a{k}|mode|p|ratio"] -> v1-shaped policy cell (per-archetype)
  cells["mode|p|ratio"]      -> the v1 pooled policy (fallback, unchanged)
  names[name]                -> archetype index

Consumed behind GLEE_PERS_DP_ARCH; a missing name, hidden opponent, or absent
archetype cell falls through to the pooled policy, which is exactly v1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.solve_pers_dp import (TABLE, calibration_offsets, solve_cell,
                                   simulate_baseline)                # noqa: E402

ARCH = os.path.join(REPO, "models", "pers_buyer_archetypes_v1.json")
OUT = os.path.join(REPO, "models", "pers_policy_dp_v2.json")
#: An archetype cell must rest on at least this many pooled observations to
#: override the global cell -- planning against 6 samples is astrology.
MIN_CELL_N = 25


def pooled_archetype_tables(doc, arch):
    named = doc["named"]
    tables = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))   # k -> cell -> [n, p*n]
    for name, k in arch["names"].items():
        t = named.get(name)
        if not t:
            continue
        for cell, v in t.items():
            n = v.get("n", 0)
            if n <= 0:
                continue
            acc = tables[k][cell]
            acc[0] += n
            acc[1] += v["p"] * n
    return {k: {cell: {"n": n, "p": pn / n}
                for cell, (n, pn) in cells.items() if n >= MIN_CELL_N}
            for k, cells in tables.items()}


def main() -> int:
    doc = json.load(open(TABLE))
    table = doc["table"]
    arch = json.load(open(ARCH))
    offs = calibration_offsets(table)
    arch_tables = pooled_archetype_tables(doc, arch)

    v1 = json.load(open(os.path.join(REPO, "models", "pers_policy_dp_v1.json")))
    out = {"_schema": "glee.pers_policy_dp/v2",
           "_built": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
           "calibration_offsets": offs,
           "names": arch["names"],
           "cells": dict(v1["cells"])}          # pooled fallback = v1 verbatim

    print(f"archetype pooled tables: " +
          ", ".join(f"a{k}:{len(t)} cells" for k, t in sorted(arch_tables.items())))
    for k, at in sorted(arch_tables.items()):
        merged = dict(table)
        merged.update(at)                        # archetype cells override
        for mode in ("binary", "text"):
            for pb in ("lo", "mid", "hi"):
                for rb in (1.2, 1.25, 2.0, 3.0, 4.0):
                    if not any(c.startswith(f"{mode}|{pb}|r{rb}|") for c in at):
                        continue                 # no archetype signal: fallback rules
                    pol, dp_rate = solve_cell(merged, offs, mode, pb, rb)
                    pooled = out["cells"].get(f"{mode}|{pb}|r{rb}")
                    delta = (dp_rate - pooled["dp_sale_rate"]) if pooled else None
                    out["cells"][f"a{k}|{mode}|{pb}|r{rb}"] = {
                        "policy": pol, "dp_sale_rate": round(dp_rate, 4)}
                    if delta is not None and abs(delta) >= 0.02:
                        lies_tail = sum(pol["0"][-5:])
                        print(f"  a{k}|{mode}|{pb}|r{rb:<5} sale {dp_rate:.1%} "
                              f"vs pooled {pooled['dp_sale_rate']:.1%} "
                              f"({delta:+.1%}); endgame lies {lies_tail}/5")
    tmp = OUT + ".tmp"
    json.dump(out, open(tmp, "w"), indent=1)
    os.replace(tmp, OUT)
    n_arch = sum(1 for c in out["cells"] if c.startswith("a"))
    print(f"\n{n_arch} archetype cells + {len(v1['cells'])} pooled fallback "
          f"-> {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
