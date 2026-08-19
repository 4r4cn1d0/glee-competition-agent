#!/usr/bin/env python
"""Read a played game as a narrative — what we thought, did, and got back.

    python scripts/transcript.py                 # list every stored game
    python scripts/transcript.py 4ff134c5        # one game, in full (prefix is enough)
    python scripts/transcript.py --family bargaining --worst 3
    python scripts/transcript.py --rebuild       # rebuild records from the logs

Per-game records live in logs/games/*.json and are written automatically when a
run finishes. The server's history covers BOTH sides; our own reasoning for each
move is merged in from turns.jsonl.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent.config import Config  # noqa: E402


def load_games(log_dir: str) -> list[dict]:
    games = []
    for path in sorted(glob.glob(os.path.join(log_dir, "games", "*.json"))):
        try:
            with open(path, encoding="utf-8") as handle:
                games.append(json.load(handle))
        except (OSError, json.JSONDecodeError):
            continue
    return games


def rebuild(log_dir: str) -> int:
    """Regenerate per-game records from turns.jsonl + results.jsonl."""
    from glee_agent.gamelog import GameLog
    log = GameLog(log_dir)
    results_path = os.path.join(log_dir, "results.jsonl")
    if not os.path.exists(results_path):
        print("no results.jsonl to rebuild from", file=sys.stderr)
        return 0
    latest: dict[str, dict] = {}
    with open(results_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record.get("final"), dict):
                latest[record["game_id"]] = record["final"]
    for game_id, final in latest.items():
        log.write_game_record(game_id, final)
    return len(latest)


def _money(value) -> str:
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return str(value)


def summarise(game: dict) -> str:
    outcome = (game.get("result") or {}).get("outcome") or game.get("status") or "?"
    opponent = (game.get("opponent") or {}).get("name") or (game.get("opponent") or {}).get("type")
    return (f"{game['game_id'][:8]}  {str(game.get('game_family')):12s} "
            f"as {str(game.get('your_player')):9s} "
            f"rounds {game.get('rounds_played', 0):3d}  "
            f"me {_money(game.get('our_payoff')):>14s}  "
            f"them {_money(game.get('opponent_payoff')):>14s}  "
            f"{outcome:12s} vs {opponent}")


def render(game: dict) -> str:
    me = game.get("your_player")
    lines = [
        "=" * 78,
        f"{game.get('game_family', '?').upper()}  {game['game_id']}",
        f"  we are {me}   opponent: {json.dumps(game.get('opponent'))}",
        f"  outcome: {game.get('status')}  ->  us {_money(game.get('our_payoff'))}"
        f"  /  them {_money(game.get('opponent_payoff'))}",
        "=" * 78,
        "CONFIG",
    ]
    for key in sorted(game.get("config") or {}):
        lines.append(f"    {key:24s} {game['config'][key]}")

    # Our reasoning, indexed by round, so it can be shown beside the move.
    plans = {}
    for turn in game.get("our_turns") or []:
        if turn.get("round") is not None:
            plans.setdefault(turn["round"], []).append(turn)

    lines.append("")
    lines.append("PLAY")
    for entry in game.get("history") or []:
        if not isinstance(entry, dict):
            continue
        rnd = entry.get("round")
        lines.append(f"  --- round {rnd} ---")
        for key in ("proposer", "offer", "decision", "counteroffer", "decided_by",
                    "seller_message", "buyer_decision", "bought", "quality",
                    "seller_payoff", "buyer_payoff", "price", "response_time_ms"):
            if key not in entry:
                continue
            value = entry[key]
            who = ""
            if key == "proposer":
                who = "  (us)" if value == me else "  (them)"
            lines.append(f"      {key:18s} {json.dumps(value, default=str)}{who}")
        for turn in plans.get(rnd, []):
            lines.append(f"      >> we played    {json.dumps(turn.get('action'), default=str)}")
            plan = turn.get("plan") or {}
            if plan:
                keep = {k: v for k, v in plan.items()
                        if k in ("aspiration", "continuation", "realistic_continuation",
                                 "opponent_evidence", "spe_share", "rounds_left",
                                 "effective_horizon", "target", "reservation",
                                 "opponent_bound", "expected_value", "p_high",
                                 "lie_rate", "recommend", "reason")}
                if keep:
                    lines.append(f"      >> because      {json.dumps(keep, default=str)}")
            if turn.get("error"):
                lines.append(f"      >> ERROR        {turn['error']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("game_id", nargs="?", help="game id or unique prefix")
    parser.add_argument("--log-dir", default=Config.from_env().log_dir)
    parser.add_argument("--family", help="only this game family")
    parser.add_argument("--worst", type=int, metavar="N",
                        help="show the N lowest-payoff games in full")
    parser.add_argument("--rebuild", action="store_true",
                        help="regenerate records from turns.jsonl + results.jsonl")
    args = parser.parse_args()

    if args.rebuild:
        print(f"rebuilt {rebuild(args.log_dir)} game records into {args.log_dir}/games/")

    games = load_games(args.log_dir)
    if args.family:
        games = [g for g in games if g.get("game_family") == args.family]
    if not games:
        print(f"No stored games in {args.log_dir}/games/. Play some, or --rebuild.")
        return 0

    if args.game_id:
        matches = [g for g in games if g["game_id"].startswith(args.game_id)]
        if not matches:
            print(f"No game matching {args.game_id!r}", file=sys.stderr)
            return 1
        for game in matches:
            print(render(game))
        return 0

    if args.worst:
        ranked = sorted(games, key=lambda g: (g.get("our_payoff") is None,
                                              g.get("our_payoff") or 0))
        for game in ranked[: args.worst]:
            print(render(game))
            print()
        return 0

    print(f"{len(games)} stored games in {args.log_dir}/games/\n")
    for game in sorted(games, key=lambda g: (g.get("game_family") or "", g["game_id"])):
        print("  " + summarise(game))
    print("\nRun with a game id (or prefix) to see the full transcript.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
