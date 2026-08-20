#!/usr/bin/env python3
"""Refit P(opponent's value multiplier | their role, their first offer).

Hidden-information negotiation is 71% of the family, and 'hidden' overstates it:
the opponent's value is one of four grid points, and their first offer leaks
which. This fits that leak from every game where their multiplier became known
-- complete-information games (visible directly), plus closed hidden games
(inverted from their payoff: seller value = price - payoff, buyer value =
price + payoff).

Supersedes negotiation_value_posterior_v1 (fitted on 1,635 games, 264 labelled).
Output: models/negotiation_value_posterior_v2.json, consumed by glee_agent/pricing.py.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.field_data import _iter_finals, infer_base   # noqa: E402

OUT = os.path.join(REPO, "models", "negotiation_value_posterior_v2.json")
MULTS = (0.8, 1.0, 1.2, 1.5)
#: first-offer price/B buckets. The informative range is 0.5-2.5; a seller
#: opening at 2.4xB is telling you something different from one opening at 1.1xB.
EDGES = [0.0, 0.7, 0.9, 1.05, 1.2, 1.4, 1.6, 1.9, 2.3, 3.0, 99.0]


def bucket(x: float) -> str:
    for lo, hi in zip(EDGES, EDGES[1:]):
        if lo <= x < hi:
            return f"{lo}-{hi}"
    return "out"


def snap(m: float):
    for g in MULTS:
        if abs(m - g) < 0.05:
            return g
    return None


def main() -> int:
    table = defaultdict(Counter)     # (their_role, bucket) -> Counter(mult)
    marginal = Counter()
    labelled = 0
    for final in _iter_finals():
        if final.get("game_family") != "negotiation":
            continue
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        r = final.get("result") or {}
        if not me:
            continue
        them = "player_2" if me == "player_1" else "player_1"
        my_value = gs.get(f"{me}_value")
        base = infer_base(my_value)
        if base is None:
            continue
        their_role = gs.get(f"{them}_role")
        # --- label: their multiplier, observed or inverted -------------------
        their_value = gs.get(f"{them}_value")
        if their_value is None and isinstance(r, dict) and r.get("outcome") == "agreement":
            price = r.get("agreed_price")
            pay = r.get(f"{them}_payoff")
            if isinstance(price, (int, float)) and isinstance(pay, (int, float)):
                their_value = (price - pay) if their_role == "seller" else (price + pay)
        if their_value is None:
            continue
        mult = snap(their_value / base)
        if mult is None:
            continue
        # --- feature: their FIRST offer, if they made one --------------------
        first = None
        for rnd in gs.get("history") or []:
            offer = rnd.get("offer") or {}
            if offer.get("from_player") == them and offer.get("price") is not None:
                first = offer["price"] / base
                break
        labelled += 1
        marginal[mult] += 1
        if first is not None:
            table[(their_role or "?", bucket(first))][mult] += 1
    total = sum(marginal.values())
    doc = {
        "_schema": "glee.negotiation_value_posterior/v2",
        "_labelled": labelled,
        "mults": list(MULTS),
        "marginal": {str(m): round(marginal[m] / total, 4) for m in MULTS},
        "table": {},
    }
    for (role, b), cnt in sorted(table.items()):
        n = sum(cnt.values())
        if n < 15:
            continue
        doc["table"][f"{role}|{b}"] = {
            "n": n, "p": [round(cnt[m] / n, 4) for m in MULTS]}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, OUT)
    print(f"labelled {labelled:,} opponents ({total:,} with multiplier) "
          f"-> {len(doc['table'])} conditional cells -> {os.path.relpath(OUT, REPO)}")
    print(f"  marginal: {doc['marginal']}")
    strongest = sorted(doc["table"].items(),
                       key=lambda kv: -max(kv[1]["p"]))[:6]
    for k, v in strongest:
        print(f"  {k:24s} n={v['n']:>4d}  P(m)={v['p']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
