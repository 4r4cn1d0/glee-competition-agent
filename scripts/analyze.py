#!/usr/bin/env python
"""Summarise logged games so strategy changes can be judged on evidence.

    python scripts/analyze.py              # read logs/
    python scripts/analyze.py --fetch      # first pull final states for any
                                           # game seen in turns.jsonl but
                                           # missing from results.jsonl

The headline number to watch is the no-deal rate. A no-deal pays $0, which lands
near the bottom of the percentile scale, so it costs far more rating than a
merely mediocre deal — if aggression is climbing the no-deal rate, it is losing.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent.config import Config  # noqa: E402


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log-dir", default=Config.from_env().log_dir)
    parser.add_argument("--fetch", action="store_true",
                        help="pull missing final states from the API first")
    args = parser.parse_args()

    turns = read_jsonl(os.path.join(args.log_dir, "turns.jsonl"))
    results = read_jsonl(os.path.join(args.log_dir, "results.jsonl"))

    if args.fetch:
        from glee_sdk import GleeClient

        from glee_agent.gamelog import GameLog
        cfg = Config.from_env()
        if not cfg.api_key:
            print("--fetch needs GLEE_API_KEY", file=sys.stderr)
            return 1
        client = (GleeClient(api_key=cfg.api_key, base_url=cfg.base_url)
                  if cfg.base_url else GleeClient(api_key=cfg.api_key))
        have = {r["game_id"] for r in results}
        missing = sorted({t.get("game_id") for t in turns if t.get("game_id")} - have)
        if missing:
            print(f"fetching {len(missing)} game results...")
            GameLog(args.log_dir).finalize(client, missing)
            results = read_jsonl(os.path.join(args.log_dir, "results.jsonl"))

    if not turns:
        print(f"No turns logged in {args.log_dir}/. Play some games first.")
        return 0

    # --- turn-level health ---
    errors = [t for t in turns if "error" in t]
    by_family = collections.Counter(t.get("game_family") for t in turns if "error" not in t)
    by_source = collections.Counter(t.get("source") for t in turns if "error" not in t)
    games = {t.get("game_id") for t in turns if t.get("game_id")}

    print(f"{len(turns)} turns across {len(games)} games")
    for family, count in sorted(by_family.items()):
        print(f"  {str(family):12s} {count:5d} turns")
    print("\naction source")
    for source, count in sorted(by_source.items()):
        print(f"  {str(source):22s} {count:5d}")
    if errors:
        print(f"\n{len(errors)} STRATEGY ERRORS (each one fell back to a safe move):")
        for message, count in collections.Counter(e.get("error") for e in errors).most_common(5):
            print(f"  {count:4d}x {message}")

    # --- outcome-level results ---
    latest = {r["game_id"]: r["final"] for r in results if isinstance(r.get("final"), dict)}
    if not latest:
        print("\nNo final states recorded yet — run with --fetch to pull them.")
        return 0

    player_of = {}
    for turn in turns:
        if turn.get("your_player"):
            player_of[turn["game_id"]] = turn["your_player"]

    stats: dict[str, dict] = collections.defaultdict(
        lambda: {"payoffs": [], "opp": [], "no_deal": 0, "n": 0, "zero": 0})
    for game_id, final in latest.items():
        family = final.get("game_family") or "?"
        entry = stats[family]
        entry["n"] += 1
        status = final.get("status")
        result = final.get("result") or {}
        me = player_of.get(game_id, "player_1")
        other = "player_2" if me == "player_1" else "player_1"
        mine = result.get(f"{me}_payoff")
        theirs = result.get(f"{other}_payoff")
        if status == "no_deal" or result.get("outcome") == "no_deal":
            entry["no_deal"] += 1
        if isinstance(mine, (int, float)):
            entry["payoffs"].append(float(mine))
            if mine == 0:
                entry["zero"] += 1
        if isinstance(theirs, (int, float)):
            entry["opp"].append(float(theirs))

    print(f"\noutcomes ({len(latest)} completed games)")
    header = f"  {'family':12s} {'games':>6s} {'no-deal':>8s} {'zero-pay':>9s} {'mean':>9s} {'median':>9s} {'vs opp':>9s}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for family, entry in sorted(stats.items()):
        payoffs = entry["payoffs"]
        mean = statistics.mean(payoffs) if payoffs else float("nan")
        median = statistics.median(payoffs) if payoffs else float("nan")
        opp_mean = statistics.mean(entry["opp"]) if entry["opp"] else float("nan")
        share = mean - opp_mean if entry["opp"] else float("nan")
        print(f"  {family:12s} {entry['n']:6d} "
              f"{entry['no_deal'] / entry['n']:7.0%} "
              f"{entry['zero'] / max(1, len(payoffs)):8.0%} "
              f"{mean:9.2f} {median:9.2f} {share:+9.2f}")
    print("\n  'vs opp' is your mean payoff minus theirs — positive means you are")
    print("  taking the larger half. Rating is percentile-scored against the field")
    print("  on the same configuration, so watch no-deal rate first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
