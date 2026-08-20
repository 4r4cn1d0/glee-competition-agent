#!/usr/bin/env python3
"""Continuous position logger: ratings + leaderboard standing every interval.

The operator asked for positions and rankings logged at the cadence of play,
not reconstructed after the fact. Appends one JSON line per interval to
logs/ratings_history.jsonl: every agent's per-family rating and games, plus
each family's top-50 cutoff and, when any of our agents appear in a top-50
list, their row. Budget: one stats() call per key per interval (the 60/min
per-key budget is shared with the live agent) plus three unauthenticated
leaderboard fetches.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
LOCK = os.path.join(REPO, "logs", "snapshot.lock")
OUT = os.path.join(REPO, "logs", "ratings_history.jsonl")
KEYS = [("GLEE_KEY_TEST1", "champion"), ("GLEE_KEY_TEST2", "hardliner"),
        ("GLEE_KEY_TEST3", "conceder"), ("GLEE_KEY_TEST4", "specialist"),
        ("GLEE_KEY_TEST5", "composite")]
INTERVAL = 600


def snapshot(env):
    from glee_sdk import GleeClient
    row = {"ts": time.time()}
    ids = {}
    for key, slot in KEYS:
        try:
            s = GleeClient(api_key=env[key]).stats()
            sc = s.get("scores") or {}
            row[slot] = {f: [(sc.get(f) or {}).get("rating"),
                             (sc.get(f) or {}).get("games_played")]
                         for f in ("bargaining", "negotiation", "persuasion")}
            ids[s.get("agent_id")] = slot
        except Exception as exc:
            row[slot] = {"error": str(exc)[:80]}
    boards = {}
    for fam in ("bargaining", "negotiation", "persuasion"):
        try:
            with urllib.request.urlopen(
                    f"https://glee-competition.com/api/leaderboard?family={fam}",
                    timeout=20) as fh:
                data = json.load(fh)
            board = {"cutoff": min(r["rating"] for r in data)}
            ours = [{"slot": ids.get(r.get("player_id"), r.get("player_name")),
                     "row": i + 1, "rank": r.get("rank"), "rating": r.get("rating")}
                    for i, r in enumerate(data)
                    if r.get("player_id") in ids]
            if ours:
                board["ours"] = ours
            boards[fam] = board
        except Exception:
            pass
    if boards:
        row["boards"] = boards
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def main() -> int:
    if os.path.exists(LOCK):
        try:
            pid = int(open(LOCK).read().strip())
            os.kill(pid, 0)
            print(f"already running (pid {pid})")
            return 1
        except (OSError, ValueError):
            pass                       # stale lock: owner is dead, reclaim
    with open(LOCK, "w") as fh:
        fh.write(str(os.getpid()))
    env = dict(line.strip().split("=", 1)
               for line in open(os.path.join(REPO, ".env"))
               if "=" in line and not line.startswith("#"))
    try:
        while True:
            row = snapshot(env)
            onb = sum(len((b or {}).get("ours", []))
                      for b in (row.get("boards") or {}).values())
            print(f"[{time.strftime('%H:%M:%S')}] snapshot ok"
                  f"{' — ON A BOARD x' + str(onb) if onb else ''}", flush=True)
            time.sleep(INTERVAL)
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
