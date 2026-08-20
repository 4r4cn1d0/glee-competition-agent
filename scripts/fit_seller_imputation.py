#!/usr/bin/env python3
"""Fit the two models the buyer-seat persuasion arena and buyer stand on.

1. Quality imputation (models/pers_seller_imputation_v1.json). Replaying a
   counterfactual buyer against a logged seller stream needs the quality of
   rounds the ORIGINAL buyer skipped -- and quality is only logged on purchases.
   Imputation draws it from P(high | this seller's recommendation), fitted on
   every round where quality WAS observed. Keys narrow-to-wide so a named seller
   with history gets their own rate and a stranger gets the field's:

       name|mode|pbin|rec|tercile  ->  name|mode|pbin|rec
       ->  mode|pbin|rec|tercile   ->  mode|pbin|rec

   The round-tercile axis exists because purchases are not a random sample of
   rounds: buyers explore early and flee after a caught lie, and sellers
   front-load honesty (ours literally has an honest_rounds knob), so a fit
   pooled over rounds would launder early-game honesty onto late-game lies.

2. Lie-rate prior (models/pers_buyer_prior_v1.json). The buyer's type posterior
   needs a prior over the seller's lie rate q. Uniform is a guess; this is the
   measured field: for each logged game, the posterior over a q grid given that
   game's full evidence (recommendation stream + observed qualities), averaged
   over games per (mode, pbin) cell.

Fitted from buyer-seat games only -- the only games where the opposing seller
is the field rather than us.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from glee_agent.strategies.persuasion import _recommended  # noqa: E402

IMPUTE_OUT = os.path.join(REPO, "models", "pers_seller_imputation_v1.json")
PRIOR_OUT = os.path.join(REPO, "models", "pers_buyer_prior_v1.json")
SLOTS = ("champion", "hardliner", "conceder", "randomized", "composite")
Q_GRID = (0.0, 0.125, 0.25, 0.5, 0.75, 1.0)
#: Chance a seller declines to recommend a HIGH unit. Every observed policy
#: (including ours) recommends all highs; epsilon keeps likelihoods off zero.
EPS = 0.02


def pbin(p: float) -> str:
    return "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")


def tercile(round_no: int, total: int) -> str:
    f = round_no / max(total, 1)
    return "early" if f <= 1 / 3 else ("mid" if f <= 2 / 3 else "late")


def iter_buyer_games():
    for slot in SLOTS:
        for fp in glob.glob(os.path.join(REPO, "logs", slot, "games", "*.json")):
            try:
                with open(fp, encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                continue
            if d.get("game_family") != "persuasion":
                continue
            cfg = d.get("config") or {}
            me = d.get("your_player")
            if cfg.get(f"{me}_role") != "buyer":
                continue
            hist = d.get("history")
            if isinstance(hist, list) and hist:
                yield d, cfg, hist


def main() -> int:
    counts = defaultdict(lambda: [0, 0])          # key -> [n, highs]
    prior_acc = defaultdict(lambda: [0.0] * len(Q_GRID))
    prior_n = defaultdict(int)
    games = 0

    for d, cfg, hist in iter_buyer_games():
        games += 1
        mode = cfg.get("seller_message_type") or "text"
        p = float(cfg.get("p") or 0.5)
        pb = pbin(p)
        total = int(cfg.get("total_rounds") or len(hist))
        name = (d.get("opponent") or {}).get("name") or "hidden"

        like = [1.0] * len(Q_GRID)
        for h in hist:
            if not isinstance(h, dict):
                continue
            rec = _recommended(h)
            rnd = int(h.get("round") or 0)
            quality = str(h.get("quality", "")).lower()
            if h.get("bought") and quality in ("high", "low"):
                r = "yes" if rec else "no"
                for key in (f"{name}|{mode}|{pb}|{r}|{tercile(rnd, total)}",
                            f"{name}|{mode}|{pb}|{r}",
                            f"{mode}|{pb}|{r}|{tercile(rnd, total)}",
                            f"{mode}|{pb}|{r}"):
                    counts[key][0] += 1
                    counts[key][1] += quality == "high"
                for i, q in enumerate(Q_GRID):
                    if quality == "high":
                        like[i] *= p * ((1 - EPS) if rec else EPS)
                    else:
                        like[i] *= (1 - p) * (q if rec else (1 - q))
            else:
                # quality unobserved: the recommendation alone still speaks --
                # its marginal frequency is what identifies an all-yes spammer
                for i, q in enumerate(Q_GRID):
                    pr = p * (1 - EPS) + (1 - p) * q
                    like[i] *= pr if rec else (1 - pr)
        z = sum(like)
        if z > 0:
            cell = f"{mode}|{pb}"
            for i in range(len(Q_GRID)):
                prior_acc[cell][i] += like[i] / z
            prior_n[cell] += 1

    doc = {"_schema": "glee.pers_seller_imputation/v1", "_games": games,
           "table": {k: {"n": n, "high": h} for k, (n, h) in counts.items()
                     if n >= 5}}
    tmp = IMPUTE_OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    os.replace(tmp, IMPUTE_OUT)

    prior_doc = {"_schema": "glee.pers_buyer_prior/v1", "_games": games,
                 "q_grid": list(Q_GRID), "eps": EPS,
                 "cells": {c: {"n": prior_n[c],
                               "prior": [round(x / prior_n[c], 5) for x in acc]}
                           for c, acc in prior_acc.items() if prior_n[c] >= 20}}
    tmp = PRIOR_OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(prior_doc, fh)
    os.replace(tmp, PRIOR_OUT)

    named = sum(1 for k in doc["table"] if not k.startswith(("binary|", "text|")))
    print(f"imputation: {games:,} buyer-seat games -> {len(doc['table'])} keys "
          f"({named} named) -> {os.path.relpath(IMPUTE_OUT, REPO)}")
    for c, cell in sorted(prior_doc["cells"].items()):
        pretty = " ".join(f"q{q}:{w:.2f}" for q, w in zip(Q_GRID, cell["prior"]))
        print(f"  q-prior {c:12s} n={cell['n']:<5d} {pretty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
