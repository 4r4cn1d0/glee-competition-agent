#!/usr/bin/env python3
"""Fit empirical payoff distributions per configuration cell, for percentile scoring.

The competition converts a payoff into a percentile against every payoff earned
on the same configuration in the same role. Every proxy metric we optimize
(payoff, close rate, zero rate) is an approximation of that, and they can
disagree: the first evolver run traded -0.4% payoff for -1.8pp zeros and neither
the arena nor the operator could say which the RATING prefers. This model is the
answer: score a simulated payoff by its rank in the observed distribution for
its cell.

Samples come from both sides of every logged game: our own payoff, and the
opponent's payoff, which is a genuine field sample for the mirror seat. Two
approximations, stated plainly:

  * our own payoffs contaminate the distribution with our own policy (~half the
    samples). The ATOMS (mass at $0, mass at the even split) are field-focal and
    robust; the far tails are least trustworthy.
  * in hidden-information negotiation the opponent's value multiplier is
    unknown, so cells there marginalise over it. Complete-information games
    provide the cleanly-celled samples.

Output: models/percentile_cdf_v3.json, consumed by sim.percentile.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.field_data import _iter_finals, infer_base   # noqa: E402

OUT = os.path.join(REPO, "models", "percentile_cdf_v3.json")
MAX_PER_CELL = 2000


def barg_cell(gs, role_seat):
    return "|".join(str(x) for x in (
        "bargaining", gs.get("money_to_divide"), gs.get("max_rounds"),
        bool(gs.get("horizon_known")), bool(gs.get("complete_information"))))


def nego_cell(base, mult, role, gs):
    # ROLE is part of the configuration cell. Its omission let 1.5xB BUYER
    # windfalls pollute the 1.5xB SELLER cell, manufacturing the phantom "39%
    # positive harvest" that briefly justified endgame v3's third fix.
    return "|".join(str(x) for x in (
        "negotiation", base, mult, role, gs.get("max_rounds"),
        bool(gs.get("horizon_known")), bool(gs.get("complete_information"))))


def main() -> int:
    cells = defaultdict(list)
    games = 0
    for final in _iter_finals():
        fam = final.get("game_family")
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        r = final.get("result") or {}
        if not me or not isinstance(r, dict):
            continue
        them = "player_2" if me == "player_1" else "player_1"
        mine, theirs = r.get(f"{me}_payoff"), r.get(f"{them}_payoff")
        games += 1
        if fam == "bargaining":
            money = gs.get("money_to_divide")
            if not money:
                continue
            # both seats of bargaining share a cell: the game is symmetric up to
            # the deltas, which are folded into the empirical distribution
            key = barg_cell(gs, None)
            for v in (mine, theirs):
                if isinstance(v, (int, float)):
                    cells[key].append(round(v / money, 4))
        elif fam == "negotiation":
            my_value = gs.get(f"{me}_value")
            base = infer_base(my_value)
            if base is None:
                continue
            if isinstance(mine, (int, float)):
                cells[nego_cell(base, round(my_value / base, 2),
                                gs.get(f"{me}_role"), gs)].append(
                    round(mine / base, 4))
            their_value = gs.get(f"{them}_value")
            if isinstance(theirs, (int, float)) and their_value:
                cells[nego_cell(base, round(their_value / base, 2),
                                gs.get(f"{them}_role"), gs)].append(
                    round(theirs / base, 4))
    doc = {"_schema": "glee.percentile_cdf/v3", "_games": games,
           "cells": {k: sorted(v)[-MAX_PER_CELL:] if len(v) > MAX_PER_CELL
                     else sorted(v)
                     for k, v in cells.items() if len(v) >= 25}}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    os.replace(tmp, OUT)
    ns = [len(v) for v in doc["cells"].values()]
    print(f"fitted {games:,} games -> {len(doc['cells'])} cells "
          f"(median {sorted(ns)[len(ns)//2]} samples/cell) "
          f"-> {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
