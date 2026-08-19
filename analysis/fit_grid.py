#!/usr/bin/env python
"""Refit sim/grid.py from the live corpus and print every number it cites.

    .venv/bin/python analysis/fit_grid.py            # the statistics
    .venv/bin/python analysis/fit_grid.py --emit     # the frozen CORPUS table
                                                     # for tests/test_sim_grid.py

The fleet keeps playing, so the corpus grows and every count below is a
snapshot. Run this again to refit; nothing here is hand-entered. What must NOT
drift is the structure -- the six-pair restriction under complete information,
the uniform own-value marginal under incomplete information -- and
``tests/test_sim_grid.py::test_the_grid_still_matches_the_live_server`` fails
if it does.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from analysis.verify_grid import chi2_sf, wilson              # noqa: E402
from sim.grid import (MONEY_SCALES, NEGOTIATION_VALUE_FACTORS,  # noqa: E402
                      PERSUASION_VALUE_FACTORS)

FAC = NEGOTIATION_VALUE_FACTORS
DELTAS = (0.8, 0.9, 0.95, 1.0)


def load():
    out = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, "logs/**/games/*.json"),
                                 recursive=True)):
        try:
            with open(path) as handle:
                game = json.load(handle)
        except (OSError, ValueError):
            continue
        if game.get("config"):
            out[game["game_family"]].append(game)
    return out


def factor(value):
    for scale in MONEY_SCALES:
        for f in FAC:
            if abs(value / scale - f) < 1e-9:
                return f
    return None


def uniform_gof(counter, support):
    n = sum(counter.values())
    e = n / len(support)
    chi2 = sum((counter.get(v, 0) - e) ** 2 / e for v in support)
    return chi2, len(support) - 1, chi2_sf(chi2, len(support) - 1), n


def line(label, counter, support):
    chi2, df, p, n = uniform_gof(counter, support)
    body = "  ".join(f"{v}:{counter.get(v, 0)}" for v in support)
    print(f"    {label:38s} n={n:4d}  {body}")
    print(f"    {'':38s} uniform: chi2={chi2:6.2f} df={df} p={p:.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print the CORPUS literal for tests/test_sim_grid.py")
    args = ap.parse_args()

    corpus = load()
    total = sum(len(v) for v in corpus.values())
    B, N, P = corpus["bargaining"], corpus["negotiation"], corpus["persuasion"]
    print(f"corpus: {total} games  bargaining={len(B)} negotiation={len(N)} "
          f"persuasion={len(P)}")

    # ---------------- bargaining ----------------
    print("\nBARGAINING")
    line("money_to_divide", collections.Counter(g["config"]["money_to_divide"] for g in B),
         MONEY_SCALES)
    line("max_rounds (12 / undisclosed)",
         collections.Counter(g["config"].get("max_rounds", "none") for g in B), (12, "none"))
    line("complete_information",
         collections.Counter(g["config"]["complete_information"] for g in B), (True, False))
    line("messages_allowed",
         collections.Counter(g["config"]["messages_allowed"] for g in B), (True, False))
    own = collections.Counter()
    for g in B:
        for key in ("delta_1", "delta_2"):
            if key in g["config"]:
                own[g["config"][key]] += 1
    line("delta (pooled over visible sides)", own, DELTAS)
    both = [g["config"] for g in B if "delta_1" in g["config"] and "delta_2" in g["config"]]
    pair = collections.Counter((c["delta_1"], c["delta_2"]) for c in both)
    support = [(a, b) for a in DELTAS for b in DELTAS]
    chi2, df, p, n = uniform_gof(pair, support)
    print(f"    delta PAIR | complete info            n={n:4d}  "
          f"uniform over all 16: chi2={chi2:.2f} df={df} p={p:.4f}")
    for cond in (True, False):
        c = collections.Counter()
        for g in B:
            key = "delta_1" if g.get("your_player") == "player_1" else "delta_2"
            if g["config"]["complete_information"] == cond and key in g["config"]:
                c[g["config"][key]] += 1
        line(f"own delta | complete_information={cond}", c, DELTAS)

    # ---------------- negotiation ----------------
    print("\nNEGOTIATION")
    ci = sum(1 for g in N if g["config"]["complete_information"])
    lo, hi = wilson(ci, len(N))
    print(f"    complete_information                 {ci}/{len(N)} = {ci/len(N):.4f}  "
          f"95% CI [{lo:.4f}, {hi:.4f}]")
    for q, name in ((6 / 22, "6/22 (uniform over grid points)"), (0.5, "1/2 (old grid)")):
        z = (ci / len(N) - q) / math.sqrt(q * (1 - q) / len(N))
        print(f"        vs {name:34s} q={q:.4f}  z={z:+6.2f}"
              f"  {'REJECTED' if abs(z) > 2 else 'ok'}")
    line("max_rounds (1 / 10 / undisclosed)",
         collections.Counter(g["config"].get("max_rounds", "none") for g in N),
         (1, 10, "none"))
    line("messages_allowed",
         collections.Counter(g["config"]["messages_allowed"] for g in N), (True, False))
    vis = collections.Counter(("player_1_value" in g["config"], "player_2_value" in g["config"])
                              for g in N)
    print(f"    valuation visibility (p1, p2)        {dict(vis)}")
    pairs = collections.Counter()
    for g in N:
        c = g["config"]
        if "player_1_value" in c and "player_2_value" in c:
            pairs[(factor(c["player_1_value"]), factor(c["player_2_value"]))] += 1
    n = sum(pairs.values())
    strict = sum(v for (a, b), v in pairs.items() if a < b)
    eq = sum(v for (a, b), v in pairs.items() if a == b)
    print(f"    value pair | complete info           n={n:4d}  strict s<b={strict}  "
          f"s==b={eq}  s>b={n - strict - eq}")
    six = [(a, b) for a in FAC for b in FAC if a < b]
    chi2, df, p, _ = uniform_gof(pairs, six)
    print(f"        uniform over the 6 ordered pairs: chi2={chi2:.2f} df={df} p={p:.4f}"
          f"   counts {[pairs.get(k, 0) for k in six]}")
    ten = [(a, b) for a in FAC for b in FAC if a <= b]
    chi2, df, p, _ = uniform_gof(pairs, ten)
    print(f"        uniform over the 10 pairs s<=b:   chi2={chi2:.2f} df={df} p={p:.3g}")
    for seat, key, lab in (("player_1", "player_1_value", "seller"),
                           ("player_2", "player_2_value", "buyer")):
        c = collections.Counter(factor(g["config"][key]) for g in N
                                if not g["config"]["complete_information"]
                                and g.get("your_player") == seat
                                and key in g["config"])
        line(f"own {lab} factor | incomplete info", c, FAC)
        banned = 1.5 if lab == "seller" else 0.8
        print(f"    {'':38s} factor {banned} is impossible under the "
              f"complete-info restriction; observed {c.get(banned, 0)}/{sum(c.values())}")

    # ---------------- persuasion ----------------
    print("\nPERSUASION")
    line("p", collections.Counter(round(g["config"]["p"], 4) for g in P),
         (0.3333, 0.5, 0.8))
    line("product_price", collections.Counter(g["config"]["product_price"] for g in P),
         MONEY_SCALES)
    line("is_seller_know_cv",
         collections.Counter(g["config"]["is_seller_know_cv"] for g in P), (True, False))
    line("seller_message_type",
         collections.Counter(g["config"]["seller_message_type"] for g in P),
         ("text", "binary"))
    line("v / product_price (visible only)",
         collections.Counter(round(g["config"]["v"] / g["config"]["product_price"], 3)
                             for g in P if "v" in g["config"]),
         PERSUASION_VALUE_FACTORS)
    print(f"    total_rounds                         "
          f"{dict(collections.Counter(g['config']['total_rounds'] for g in P))}")
    print(f"    u (visible only)                     "
          f"{dict(collections.Counter(g['config']['u'] for g in P if 'u' in g['config']))}")

    if args.emit:
        emit(B, N, P)
    return 0


def emit(B, N, P):
    def counts(games, key):
        return dict(collections.Counter(g["config"][key] for g in games))

    own_delta = collections.Counter()
    for g in B:
        for key in ("delta_1", "delta_2"):
            if key in g["config"]:
                own_delta[g["config"][key]] += 1
    nego = {"complete_information": counts(N, "complete_information"),
            "max_rounds_or_none": dict(collections.Counter(
                g["config"].get("max_rounds") for g in N)),
            "messages_allowed": counts(N, "messages_allowed")}
    for seat, key, axis in (("player_1", "player_1_value", "seller_factor_incomplete"),
                            ("player_2", "player_2_value", "buyer_factor_incomplete")):
        nego[axis] = dict(collections.Counter(
            factor(g["config"][key]) for g in N
            if not g["config"]["complete_information"]
            and g.get("your_player") == seat and key in g["config"]))
    table = {
        "bargaining": {
            "money_to_divide": counts(B, "money_to_divide"),
            "horizon_known": counts(B, "horizon_known"),
            "complete_information": counts(B, "complete_information"),
            "messages_allowed": counts(B, "messages_allowed"),
            "delta_own": dict(own_delta),
        },
        "negotiation": nego,
        "persuasion": {
            "p": dict(collections.Counter(g["config"]["p"] for g in P)),
            "value_factor": dict(collections.Counter(
                round(g["config"]["v"] / g["config"]["product_price"], 3)
                for g in P if "v" in g["config"])),
            "product_price": counts(P, "product_price"),
            "is_seller_know_cv": counts(P, "is_seller_know_cv"),
            "seller_message_type": counts(P, "seller_message_type"),
        },
    }
    print("\n\n# --- paste into tests/test_sim_grid.py ---")
    print("CORPUS = {")
    for family, axes in table.items():
        print(f'    "{family}": {{')
        for axis, c in axes.items():
            items = ", ".join(
                f"{'1 / 3' if isinstance(k, float) and abs(k - 1/3) < 1e-9 else repr(k)}: {v}"
                for k, v in sorted(c.items(), key=lambda kv: (kv[0] is None, str(kv[0]))))
            print(f'        "{axis}": {{{items}}},')
        print("    },")
    print("}")


if __name__ == "__main__":
    raise SystemExit(main())
