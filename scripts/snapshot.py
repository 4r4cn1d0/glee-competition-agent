#!/usr/bin/env python3
"""Continuous position logger: ratings + leaderboard standing every interval.

The operator asked for positions and rankings logged at the cadence of play,
not reconstructed after the fact. Appends one JSON line per interval to
logs/ratings_history.jsonl: every agent's per-family rating and games, plus
each family's top-50 cutoff and, when any of our agents appear in a top-50
list, their row. Budget: one stats() call per key per interval (the 60/min
per-key budget is shared with the live agent) plus three authenticated
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
ENV = os.path.join(REPO, ".env")
KEYS = [("GLEE_KEY_TEST1", "champion"), ("GLEE_KEY_TEST2", "hardliner"),
        ("GLEE_KEY_TEST3", "conceder"), ("GLEE_KEY_TEST4", "randomized"),
        ("GLEE_KEY_TEST5", "composite")]
INTERVAL = 600
FAILURE_ESCALATION_POLLS = 3


def load_env(path=ENV):
    """Return a complete key mapping, or raise so the caller can retain its cache."""
    env = {}
    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    missing = [key for key, _slot in KEYS if not env.get(key)]
    if missing:
        raise ValueError("missing required keys: " + ", ".join(missing))
    return env


def reload_env(last_good, path=ENV):
    """Read .env for this poll, retaining the last complete mapping on failure."""
    try:
        return load_env(path)
    except (OSError, UnicodeError, ValueError) as exc:
        fallback = ("using last good key mapping" if last_good is not None
                    else "no last good key mapping; skipping this poll")
        print(f"[{time.strftime('%H:%M:%S')}] WARNING: cannot reload .env "
              f"({type(exc).__name__}: {exc}); {fallback}",
              file=sys.stderr, flush=True)
        return last_good


def report_slot_failures(row, failure_streaks):
    """Warn for every failed slot and track consecutive failures per slot."""
    failures = 0
    for _key, slot in KEYS:
        result = row.get(slot)
        if isinstance(result, dict) and "error" in result:
            failures += 1
            streak = failure_streaks.get(slot, 0) + 1
            failure_streaks[slot] = streak
            level = ("PERSISTENT ERROR"
                     if streak >= FAILURE_ESCALATION_POLLS else "WARNING")
            poll_word = "poll" if streak == 1 else "polls"
            print(f"[{time.strftime('%H:%M:%S')}] {level}: slot {slot} ratings "
                  f"poll failed ({streak} consecutive {poll_word}): "
                  f"{result['error']}", file=sys.stderr, flush=True)
        else:
            failure_streaks.pop(slot, None)
    return failures


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
            agent_id = s.get("agent_id")
            if agent_id:
                ids[agent_id] = slot
            else:
                print(f"[{time.strftime('%H:%M:%S')}] WARNING: slot {slot} "
                      "stats response has no agent_id; board identity unavailable",
                      file=sys.stderr, flush=True)
        except Exception as exc:
            row[slot] = {"error": str(exc)[:80]}
    boards = {}
    for fam in ("bargaining", "negotiation", "persuasion"):
        try:
            # The endpoint 403s without auth; this failed silently from the day
            # the snapshotter was built, so no snapshot carried board data until
            # 2026-08-21. Bearer auth + UA fixed it; failures are warned below.
            # Use the mapping reloaded for this poll. Reading process env here
            # would keep a launch-time key alive after a later rotation.
            _key = env.get("GLEE_KEY_TEST1") or env.get("GLEE_API_KEY", "")
            req = urllib.request.Request(
                f"https://glee-competition.com/api/leaderboard?family={fam}",
                headers={"Authorization": f"Bearer {_key}",
                         "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as fh:
                data = json.load(fh)
            board = {"cutoff": min(r["rating"] for r in data)}
            ours = [{"slot": ids.get(r.get("player_id"), r.get("player_name")),
                     "row": i + 1, "rank": r.get("rank"), "rating": r.get("rating")}
                    for i, r in enumerate(data)
                    if r.get("player_id") in ids]
            if ours:
                board["ours"] = ours
            boards[fam] = board
        except Exception as exc:
            print(f"[{time.strftime('%H:%M:%S')}] WARNING: {fam} leaderboard "
                  f"poll failed: {str(exc)[:80]}", file=sys.stderr, flush=True)
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
    env = None
    failure_streaks = {}
    try:
        while True:
            # A Test 4 key rotation left the old daemon blind for about 30 hours
            # and omitted 1,310 games. Reload every poll, but only replace the
            # cached mapping after a complete read so a transient file problem
            # cannot kill the daemon or discard working keys.
            env = reload_env(env)
            if env is None:
                time.sleep(INTERVAL)
                continue
            row = snapshot(env)
            failures = report_slot_failures(row, failure_streaks)
            onb = sum(len((b or {}).get("ours", []))
                      for b in (row.get("boards") or {}).values())
            status = ("ratings snapshot ok" if not failures else
                      f"snapshot complete — SLOT FAILURES {failures}/{len(KEYS)}")
            print(f"[{time.strftime('%H:%M:%S')}] {status}"
                  f"{' — ON A BOARD x' + str(onb) if onb else ''}", flush=True)
            time.sleep(INTERVAL)
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
