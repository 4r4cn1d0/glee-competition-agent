#!/usr/bin/env python
"""Continuously fetch game outcomes while the fleet keeps playing.

    nohup python scripts/collect.py &        # run alongside the supervisor
    python scripts/collect.py --once         # one backfill pass, then exit

Why this exists: per-game records are written by GameLog.finalize(), which only
runs when a run EXITS. Once the fleet was made continuous it stopped exiting, so
outcomes stopped being written — 82-100% of games had no payoff record, while
turns.jsonl kept every move. The move log alone cannot tell you what a game was
worth, so every model that needs an outcome (the acceptance curve, the
per-configuration segmentation) was training on a small and increasingly stale
slice.

This runs as a separate process on purpose. It never touches the agents' code
path, so it cannot cost a game, and it can be started, stopped or restarted
without disturbing play.

Rate: each key has its own 60 requests/minute budget shared with its agent, and
the agents already run close to it. The default here is deliberately gentle —
comfortably faster than games are produced (~3/min/agent), slow enough to leave
the agent its headroom.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLEET = [("GLEE_KEY_TEST1", "champion"), ("GLEE_KEY_TEST2", "hardliner"),
         ("GLEE_KEY_TEST3", "conceder"), ("GLEE_KEY_TEST4", "randomized"),
         ("GLEE_KEY_TEST5", "composite")]


def load_env() -> None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def pending_ids(probe: str) -> list[str]:
    """Game ids seen in the move log that have no outcome record yet."""
    log_dir = os.path.join(REPO, "logs", probe)
    turns = os.path.join(log_dir, "turns.jsonl")
    if not os.path.exists(turns):
        return []
    games_dir = os.path.join(log_dir, "games")
    os.makedirs(games_dir, exist_ok=True)
    have = {name[:-5] for name in os.listdir(games_dir) if name.endswith(".json")}
    seen: list[str] = []
    added = set()
    with open(turns, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                gid = json.loads(line).get("game_id")
            except json.JSONDecodeError:
                continue                      # a torn final line while appending
            if gid and gid not in have and gid not in added:
                added.add(gid)
                seen.append(gid)
    return seen


def sweep(probe: str, key: str, rate: float, budget: int) -> tuple[int, int]:
    """Fetch up to ``budget`` outcomes. Returns (written, still_active)."""
    from glee_sdk import GleeAPIError, GleeClient

    from glee_agent.gamelog import GameLog
    log = GameLog(os.path.join(REPO, "logs", probe))
    client = GleeClient(api_key=key)
    written = active = 0
    for gid in pending_ids(probe)[:budget]:
        try:
            state = client.game_state(gid)
        except GleeAPIError as exc:
            if exc.status_code == 429:
                time.sleep(10)                # the shared budget is tight
            continue
        except Exception:
            continue
        if state.get("status") == "active":
            active += 1                       # not finished; try again next pass
            continue
        try:
            log.write_game_record(gid, state)
            written += 1
        except Exception:
            pass
        time.sleep(rate)
    return written, active



def _claim_singleton(name: str) -> None:
    """Refuse to start if another instance is already running.

    Two supervisors each launch their own five agents and both overwrite
    logs/supervisor.json, so neither can see the other's children. That is
    exactly how fifteen agent processes ended up sharing five API keys, each
    key's 60 req/min budget split three ways and the processes racing each
    other for the same moves. A lock file holding a live PID makes the mistake
    impossible rather than merely unlikely.
    """
    import errno
    lock = os.path.join(REPO, "logs", f"{name}.lock")
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    if os.path.exists(lock):
        try:
            with open(lock, encoding="utf-8") as handle:
                other = int(handle.read().strip())
        except (ValueError, OSError):
            other = None
        if other and other != os.getpid():
            try:
                os.kill(other, 0)          # signal 0 just tests existence
            except OSError as exc:
                if exc.errno != errno.ESRCH:
                    raise
            else:
                print(f"{name} already running as pid {other}; refusing to start "
                      f"a second one. Stop it first, or remove {lock} if stale.",
                      file=sys.stderr)
                raise SystemExit(1)
    with open(lock, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    import atexit
    atexit.register(lambda: os.path.exists(lock) and os.remove(lock))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rate", type=float, default=6.0,
                        help="seconds between API calls per agent (default 6 = 10/min)")
    parser.add_argument("--budget", type=int, default=200,
                        help="max fetches per agent per pass")
    parser.add_argument("--interval", type=float, default=60.0,
                        help="seconds between passes")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    load_env()

    _claim_singleton("collector")
    stopping = {"flag": False}
    signal.signal(signal.SIGINT, lambda *_: stopping.update(flag=True))
    signal.signal(signal.SIGTERM, lambda *_: stopping.update(flag=True))

    print(f"collector started (rate {60/args.rate:.0f} req/min per agent)", flush=True)
    while not stopping["flag"]:
        total_w = total_a = total_p = 0
        for env_key, probe in FLEET:
            key = os.environ.get(env_key)
            if not key:
                continue
            outstanding = len(pending_ids(probe))
            total_p += outstanding
            w, a = sweep(probe, key, args.rate, args.budget)
            total_w += w
            total_a += a
        print(f"  [{time.strftime('%H:%M:%S')}] wrote {total_w}, "
              f"{total_a} still active, {total_p} outstanding before pass", flush=True)
        if args.once:
            break
        for _ in range(int(args.interval)):
            if stopping["flag"]:
                break
            time.sleep(1)
    print("collector stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
