#!/usr/bin/env python3
"""Refit the negotiation acceptance curves from the full game corpus.

The strategy's numbers should come from curves, not constants. This fits the
curve that matters most: P(the opponent accepts | our price), on the price/B
axis, where B is the configuration's base value. Values are multiplier x B with
multipliers on the grid {0.8, 1.0, 1.2, 1.5} and bases {100, 1e4, 1e6}, so B is
recoverable from our own valuation alone: of v/0.8, v/1.0, v/1.2, v/1.5, exactly
one lands on a base (the bases are 100x apart, the multipliers span less than
2x). That makes price/B a feature the live strategy can compute at decision
time, hidden information or not.

Curves are split by seat and by round position, because acceptance behaviour is
completely different mid-game (reject and counter) and at the end (take it or
leave it):

  seller/final   our price as seller, offered in a single-round game or the last
                 round of a capped one -- the monopoly-pricing cell
  seller/mid     our price as seller, any other round
  buyer/final    symmetric, our price as buyer (axis is still price/B; LOW
                 prices are aggressive here)
  buyer/mid

Output: models/negotiation_acceptance_v5.json, consumed by glee_agent/pricing.py.
An earlier fit of the same curves (negotiation_field_model.json, 1,197 games)
had 2-12 observations per bin in the final-round seller curve; this refit uses
every logged game.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "models", "negotiation_acceptance_v5.json")

BASES = (100.0, 1e4, 1e6)
MULTS = (0.8, 1.0, 1.2, 1.5)
#: price/B bin edges. Denser around the multiplier grid where rational
#: acceptance steps live, with an irrationality tail above 1.5.
EDGES = [0.0, 0.5, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.35, 1.5, 1.75, 2.0, 3.0, 10.0]


def infer_base(value: float):
    """The configuration's base B, from our own valuation. None if off-grid."""
    for m in MULTS:
        b = value / m
        for base in BASES:
            if abs(b - base) <= base * 1e-6:
                return base
    return None


def wilson(k: int, n: int):
    """95% Wilson interval — behaves at the tiny counts of the tail bins."""
    if n == 0:
        return None
    z = 1.959964
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(centre - half, 0.0), 4), round(min(centre + half, 1.0), 4)]


def iter_finals():
    seen = set()
    for path in glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = rec.get("game_id")
                if gid in seen:
                    continue
                seen.add(gid)
                final = rec.get("final") or {}
                if final.get("game_state"):
                    yield final
    for path in glob.glob(os.path.join(REPO, "logs", "*", "games", "*.json")):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                rec = json.load(fh)
        except (ValueError, OSError):
            continue
        gid = rec.get("game_id")
        if gid in seen:
            continue
        seen.add(gid)
        cfg = rec.get("config") or {}
        if rec.get("history"):
            yield {"game_family": rec.get("game_family"),
                   "your_player": rec.get("your_player"),
                   "game_state": {"history": rec.get("history"), **cfg}}


def fit() -> dict:
    obs = defaultdict(list)   # (seat, position) -> [(price_over_B, accepted)]
    games = 0
    for final in iter_finals():
        if final.get("game_family") != "negotiation":
            continue
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        if not me:
            continue
        my_value = gs.get(f"{me}_value")
        if not my_value:
            continue
        base = infer_base(float(my_value))
        if base is None:
            continue
        my_role = gs.get(f"{me}_role")
        max_rounds = gs.get("max_rounds")
        games += 1
        for rnd in gs.get("history") or []:
            offer = rnd.get("offer") or {}
            if offer.get("from_player") != me:
                continue
            price = offer.get("price")
            decision = str(rnd.get("decision") or "").lower()
            if price is None or not decision or "walk" in decision:
                # A walkaway ends the game rather than judging the price;
                # treating it as a rejection of THIS price would poison the tail.
                continue
            is_final = max_rounds is not None and rnd.get("round") == max_rounds
            key = (my_role or "?", "final" if is_final else "mid")
            obs[key].append((price / base, "accept" in decision))
    curves = {}
    for (seat, pos), pts in obs.items():
        rows = []
        for lo, hi in zip(EDGES, EDGES[1:]):
            inb = [ok for x, ok in pts if lo <= x < hi]
            if not inb:
                continue
            k = sum(inb)
            rows.append({"lo": lo, "hi": hi, "n": len(inb),
                         "p_accept": round(k / len(inb), 4),
                         "ci95": wilson(k, len(inb))})
        curves[f"{seat}_{pos}"] = rows
    return {"_schema": "glee.negotiation_acceptance/v5",
            "_axis": "our offered price divided by the configuration base B "
                     "(B inferred from our own valuation via the value grid)",
            "_games": games,
            "_note": "final = single-round games and the last round of capped "
                     "games; mid = everything else. Walkaways excluded.",
            "curves": curves}


def main() -> int:
    doc = fit()
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, OUT)
    print(f"fitted from {doc['_games']:,} negotiation games -> {os.path.relpath(OUT, REPO)}")
    for name, rows in sorted(doc["curves"].items()):
        print(f"\n  {name}  ({sum(r['n'] for r in rows):,} responses)")
        for r in rows:
            bar = "#" * int(r["p_accept"] * 40)
            print(f"    {r['lo']:>5.2f}-{r['hi']:<5.2f} n={r['n']:>5d}  "
                  f"{r['p_accept']:>6.1%}  {bar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
