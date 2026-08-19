#!/usr/bin/env python
"""Launch the exploration fleet: several agents, different policies, one field.

    python scripts/run_fleet.py --max-time 1800          # run the fleet for 30 min
    python scripts/run_fleet.py --status                 # ratings for every agent
    python scripts/run_fleet.py --stop                   # stop a running fleet

Each agent runs as its own process with its own API key, its own probe policy
and its own log directory, so their data stays separable but merges cleanly.

Only the account's BEST agent takes a leaderboard rank, so the sacrificial
probes cost nothing in standing. The platform guarantees an agent never plays
its own account's agents, so every game a probe plays is against the real field.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PID_FILE = os.path.join(REPO, "logs", "fleet.pids")

#: agent env-var -> probe policy. The champion carries the tuned strategy and is
#: the one whose rating matters; the rest exist to collect data.
FLEET = [
    ("GLEE_KEY_TEST1", "champion"),
    ("GLEE_KEY_TEST2", "hardliner"),
    ("GLEE_KEY_TEST3", "conceder"),
    ("GLEE_KEY_TEST4", "randomized"),
    ("GLEE_KEY_TEST5", "composite"),
]


def load_env() -> None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def status() -> int:
    from glee_sdk import GleeAPIError, GleeClient
    print(f"{'agent':10s} {'probe':12s} {'family':12s} {'display':>9s} {'raw~':>9s} {'games':>6s}")
    print("-" * 64)
    for env_key, probe in FLEET:
        key = os.environ.get(env_key)
        if not key:
            print(f"{env_key:10s} {probe:12s} (no key set)")
            continue
        try:
            stats = GleeClient(api_key=key).stats()
        except GleeAPIError as exc:
            print(f"{env_key:10s} {probe:12s} ERROR {exc}")
            continue
        name = stats.get("agent_name", "?")
        scores = stats.get("scores") or {}
        if not scores:
            print(f"{name:10s} {probe:12s} {'-':12s} {'-':>9s} {'-':>9s} {0:6d}")
        for family, entry in sorted(scores.items()):
            games = entry.get("games_played", 0)
            shrink = games / (games + 30) if games else 0.0
            raw = ((entry["rating"] - 1000 * (1 - shrink)) / shrink) if shrink else float("nan")
            print(f"{name:10s} {probe:12s} {family:12s} {entry['rating']:9.1f} "
                  f"{raw:9.1f} {games:6d}")
    return 0


def stop() -> int:
    if not os.path.exists(PID_FILE):
        print("no fleet running (no logs/fleet.pids)")
        return 0
    stopped = 0
    with open(PID_FILE, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            pid = int(line.split()[0])
            try:
                # SIGINT so run_agent's handler leaves the matchmaking queue.
                # An agent left queued gets matched after it stops polling and
                # loses those games to timeout.
                os.kill(pid, signal.SIGINT)
                stopped += 1
            except ProcessLookupError:
                pass
    os.remove(PID_FILE)
    print(f"sent SIGINT to {stopped} agent(s); they will drain in-flight games and exit")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-time", type=float, default=1800,
                        help="seconds each agent runs before draining and stopping")
    parser.add_argument("--max-games", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--families", default="bargaining,negotiation,persuasion")
    parser.add_argument("--only", help="comma-separated probe names to launch")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()

    load_env()
    if args.status:
        return status()
    if args.stop:
        return stop()

    only = {p.strip() for p in args.only.split(",")} if args.only else None
    python = os.path.join(REPO, ".venv", "bin", "python")
    os.makedirs(os.path.join(REPO, "logs"), exist_ok=True)

    launched = []
    for env_key, probe in FLEET:
        if only and probe not in only:
            continue
        key = os.environ.get(env_key)
        if not key:
            print(f"skipping {probe}: {env_key} not set", file=sys.stderr)
            continue
        log_dir = os.path.join("logs", probe)
        cmd = [python, "run_agent.py", "--probe", probe, "--log-dir", log_dir,
               "--llm-mode", "off", "--concurrency", str(args.concurrency),
               "--families", args.families, "--max-time", str(args.max_time), "--quiet"]
        if args.max_games:
            cmd += ["--max-games", str(args.max_games)]
        if probe == "randomized":
            cmd += ["--seed", "20260819"]
        env = dict(os.environ, GLEE_API_KEY=key, GLEE_LOG_DIR=log_dir)
        out = open(os.path.join(REPO, "logs", f"{probe}.out"), "a", encoding="utf-8")
        proc = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=out,
                                stderr=subprocess.STDOUT)
        launched.append((proc.pid, probe))
        print(f"  launched {probe:12s} pid={proc.pid}  key={env_key}  logs/{probe}/")
        time.sleep(0.5)          # stagger, so they do not all hit matchmaking at once

    if not launched:
        print("nothing launched", file=sys.stderr)
        return 1
    with open(PID_FILE, "w", encoding="utf-8") as handle:
        for pid, probe in launched:
            handle.write(f"{pid} {probe}\n")
    print(f"\n{len(launched)} agents running for up to {args.max_time:.0f}s.")
    print("  watch:  tail -f logs/*.out        stop:  python scripts/run_fleet.py --stop")
    print("  study:  .venv/bin/python scripts/transcript.py --log-dir logs/<probe>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
