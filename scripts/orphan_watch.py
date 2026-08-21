#!/usr/bin/env python3
"""Count games we moved in but never saw finish -- the invisible rating killer.

An ABANDONED game is scored by the server at the 5th percentile. Our play earns
~0.52, so each abandonment swaps a 0.52 for a 0.05. The damage is large and, far
worse, it is STRUCTURALLY INVISIBLE to every other meter we have: an abandoned
game never writes a line to results.jsonl, so the percentile meter, the arena and
the rating all keep looking healthy while forfeits pile up. On 2026-08-22 that
gap hid 920 abandoned games in 12 hours -- 775 of them in the single hour a
supervisor restart stranded in-flight games -- and it showed up only as an
unexplained -243 on Test 1's persuasion rating hours later.

The signal is simply: a game id we submitted a move for, with no result, and no
move from us for longer than the server's turn clock could tolerate.

    python scripts/orphan_watch.py                 # last 3h
    python scripts/orphan_watch.py --hours 12
    python scripts/orphan_watch.py --alert 20      # exit 2 if any agent exceeds

Run it after ANY fleet intervention, and on a schedule. A restart that strands
games should be visible in seconds, not hours.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = {"champion": "Test 1", "hardliner": "Test 2", "conceder": "Test 3",
         "randomized": "Test 4", "composite": "Agent 5"}

#: A game counts as abandoned only once our last move is older than this.
#:
#: CALIBRATED, because the first guess was wrong and inflated the damage ~2x.
#: 600s looked safe -- the server closes a game 120s into OUR turn -- but that
#: reasoning ignores the time we spend WAITING on the opponent, during which we
#: legitimately make no move. Measured on games that actually COMPLETED: gaps
#: between our own moves exceed 600s in 18.1% of bargaining, 14.2% of
#: negotiation and 4.7% of persuasion games, with p90 around 2,200-2,800s and a
#: maximum near 5,700s. At 600s the monitor was calling healthy in-flight games
#: dead and reported 1,139 abandoned in 12h against a true 457.
#:
#: 6000s sits just past the observed maximum, so a game only counts once it is
#: outside anything a live game has ever done.
COLD_SECONDS = 6000


def scan(hours: float):
    cut = time.time() - hours * 3600
    now = time.time()
    played = defaultdict(dict)
    done = defaultdict(set)
    flush = defaultdict(list)     # ts of every result we have, to find the watermark
    for path in glob.glob(os.path.join(REPO, "logs", "*", "turns.jsonl")):
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
                gid = rec.get("game_id")
                if ts >= cut and gid:
                    played[slot][gid] = max(played[slot].get(gid, 0), ts)
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
                if rec.get("ts", 0) >= cut and rec.get("game_id"):
                    done[slot].add(rec["game_id"])
                if rec.get("ts"):
                    flush[slot].append(rec["ts"])
    out = {}
    for slot in NAMES:
        # RESULTS ARE FLUSHED ONLY AT PROCESS EXIT (run_agent.py:154 calls
        # log.finalize in a finally block), so results.jsonl is written in a
        # batch at each shift rotation -- roughly every 83 minutes -- while
        # turns.jsonl streams continuously. A game played by the CURRENT process
        # therefore has no result line yet no matter how healthy it was, and a
        # naive "no result" test counts an entire shift's play as abandoned.
        # That is what produced a phantom 65-game "spike" minutes after a
        # rotation on 2026-08-22.
        #
        # So judge a game only once a flush has happened AFTER our last move in
        # it. Games newer than the watermark are simply not yet knowable.
        watermark = max(flush[slot], default=0.0)
        judged = [(g, ts) for g, ts in played[slot].items() if ts < watermark]
        orph = [g for g, ts in judged
                if g not in done[slot] and now - ts > COLD_SECONDS]
        out[slot] = (len(orph), len(judged), len(played[slot]) - len(judged))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=3.0)
    ap.add_argument("--alert", type=int, default=None,
                    help="exit 2 if any agent has more orphans than this")
    args = ap.parse_args()
    res = scan(args.hours)
    worst = 0
    print(f"abandoned games, last {args.hours:g}h "
          f"(each is scored at the 5th percentile against our ~0.52)")
    print(f"{'agent':9} {'judged':>8} {'ABANDONED':>10} {'rate':>7} "
          f"{'drag':>9} {'awaiting flush':>15}")
    for slot, (orph, judged, pending) in sorted(res.items(), key=lambda kv: -kv[1][0]):
        if not judged and not pending:
            continue
        worst = max(worst, orph)
        rate = orph / judged if judged else 0.0
        drag = rate * (0.52 - 0.05)
        print(f"{NAMES[slot]:9} {judged:>8} {orph:>10} {100*rate:>6.1f}% "
              f"{-drag:>9.4f} {pending:>15}")
    if args.alert is not None and worst > args.alert:
        print(f"\nALERT: {worst} abandoned games exceeds threshold {args.alert}. "
              f"Something stranded in-flight games -- check for a restart, a "
              f"stalled process, or a platform outage.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
