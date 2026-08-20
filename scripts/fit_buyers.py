#!/usr/bin/env python3
"""Fit field-buyer response models from our seller-seat persuasion games.

The persuasion arena that could not exist for sellers-as-clones (quality is
hidden from our buyer seat on passed rounds) CAN exist for buyers-as-clones:
in our SELLER games we observe everything a buyer model needs -- the true
quality, our recommendation, their decision, and the history both sides saw.

Model: P(buy | our recommendation, trust state), where trust state counts the
lies the buyer has CAUGHT so far (a lie is only caught when they bought a
recommended low-quality item -- passed rounds reveal nothing to them).
Split by message mode (binary vs text) and prior p bucket.

Output: models/pers_buyer_response_v2.json, consumed by sim/pers_arena.py.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.field_data import _iter_finals   # noqa: E402

OUT = os.path.join(REPO, "models", "pers_buyer_response_v2.json")


def rec_of(msg) -> bool | None:
    if msg is None:
        return None
    s = str(msg).strip().lower()
    if s in ("yes", "true"):
        return True
    if s in ("no", "false"):
        return False
    # text mode: our templates are consistent; classify on the two stems
    if "recommend" in s and "not" not in s and "hold" not in s:
        return True
    if "hold off" in s or "skip" in s or "pass" in s or "not recommend" in s:
        return False
    return True if len(s) > 0 else None      # unknown text reads as positive


def main() -> int:
    tab = defaultdict(lambda: [0, 0])   # (mode, p_bucket, rec, lies_caught_bucket) -> [buys, n]
    games = 0
    for final in _iter_finals():
        if final.get("game_family") != "persuasion":
            continue
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        if not me or gs.get(f"{me}_role") != "seller":
            continue
        p = gs.get("p")
        mode = gs.get("seller_message_type") or "text"
        if p is None:
            continue
        games += 1
        pb = "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")
        lies_caught = 0
        for rnd in gs.get("history") or []:
            rec = rec_of(rnd.get("seller_message"))
            bought = bool(rnd.get("bought"))
            quality = str(rnd.get("quality") or "").lower()
            if rec is None:
                continue
            lb = "0" if lies_caught == 0 else ("1" if lies_caught == 1 else "2+")
            cell = tab[(mode, pb, "yes" if rec else "no", lb)]
            cell[1] += 1
            if bought:
                cell[0] += 1
            if bought and rec and quality == "low":
                lies_caught += 1
    doc = {"_schema": "glee.pers_buyer_response/v2", "_seller_games": games,
           "table": {}}
    for (mode, pb, rec, lb), (buys, n) in sorted(tab.items()):
        if n >= 30:
            doc["table"][f"{mode}|{pb}|{rec}|{lb}"] = {"n": n, "p": round(buys / n, 4)}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, OUT)
    print(f"fitted {games:,} seller games -> {len(doc['table'])} cells -> {os.path.relpath(OUT, REPO)}")
    for k, v in doc["table"].items():
        if "|0" in k or "|2+" in k:
            print(f"  {k:22s} P(buy)={v['p']:5.1%}  (n={v['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
