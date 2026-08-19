"""Append-only record of every turn, so strategies can be tuned from evidence.

The SDK swallows each move's result inside its own loop, so a strategy never
sees how a game ended. Turns are therefore logged as they happen and outcomes
are fetched afterwards by game id — ``GET /api/agent/games/{id}`` works after a
game is over. ``scripts/analyze.py`` joins the two.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time

logger = logging.getLogger("glee.log")


class GameLog:
    """Thread-safe JSONL writer. Safe to share across the SDK's worker pool."""

    def __init__(self, log_dir: str = "logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.dir = log_dir
        self.turns_path = os.path.join(log_dir, "turns.jsonl")
        self.results_path = os.path.join(log_dir, "results.jsonl")
        # One self-contained file per game, for reading and for fitting
        # opponent models. turns.jsonl is append-only and interleaves every
        # game at once, which is fine for machines and useless for studying a
        # single match.
        self.games_dir = os.path.join(log_dir, "games")
        os.makedirs(self.games_dir, exist_ok=True)
        self._lock = threading.Lock()
        self._seen: set[str] = set()

    @property
    def game_ids(self) -> list[str]:
        with self._lock:
            return sorted(self._seen)

    def turn(self, game: dict, action: dict, plan: dict | None, source: str) -> None:
        """Record one decision. ``source`` is which layer produced the action."""
        game_id = game.get("game_id", "?")
        record = {
            "ts": time.time(),
            "game_id": game_id,
            "game_family": game.get("game_family"),
            "your_player": game.get("your_player"),
            "phase": game.get("phase"),
            "round": (game.get("game_state") or {}).get("round"),
            "opponent": game.get("opponent"),
            "action_type": (game.get("valid_actions") or {}).get("type"),
            "state": game.get("game_state"),
            "plan": plan,
            "action": {k: v for k, v in action.items() if not k.startswith("_")},
            "source": source,
        }
        with self._lock:
            self._seen.add(game_id)
            self._append(self.turns_path, record)

    def error(self, game: dict, exc: BaseException, stage: str) -> None:
        with self._lock:
            self._seen.add(game.get("game_id", "?"))
            self._append(self.turns_path, {
                "ts": time.time(),
                "game_id": game.get("game_id", "?"),
                "game_family": game.get("game_family"),
                "stage": stage,
                "error": f"{type(exc).__name__}: {exc}",
            })

    def finalize(self, client, game_ids: list[str] | None = None) -> int:
        """Fetch and record the final state of every game seen. Returns the count."""
        ids = game_ids if game_ids is not None else self.game_ids
        written = 0
        for game_id in ids:
            try:
                state = client.game_state(game_id)
            except Exception as exc:
                logger.warning("Could not fetch final state for %s: %s", game_id, exc)
                continue
            with self._lock:
                self._append(self.results_path, {"ts": time.time(), "game_id": game_id,
                                                 "final": state})
            try:
                self.write_game_record(game_id, state)
            except Exception as exc:
                logger.warning("Could not write game record for %s: %s", game_id, exc)
            written += 1
        return written

    def write_game_record(self, game_id: str, final: dict) -> str:
        """Merge our per-turn reasoning with the server's full history.

        The server's final game_state carries the WHOLE match — both sides'
        offers, messages and decisions — while turns.jsonl carries only our own
        moves plus the reasoning behind them. Joining the two is what makes a
        game studyable: what we thought, what we did, what they did back.
        """
        our_turns = []
        try:
            with open(self.turns_path, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if record.get("game_id") != game_id:
                        continue
                    our_turns.append({k: record.get(k) for k in
                                      ("ts", "round", "phase", "action_type",
                                       "action", "plan", "source", "error", "stage")})
        except OSError:
            pass

        state = final.get("game_state") or {}
        history = state.get("history") or []
        # Static configuration is everything that does not change round to
        # round — the axes a percentile is scored within.
        config = {k: v for k, v in state.items()
                  if k not in ("history", "last_offer", "phase", "current_player",
                               "round", "seller_message", "current_quality",
                               "seller_total_payoff", "buyer_total_payoff")}
        me = final.get("your_player") or (our_turns[0].get("player") if our_turns else None)
        result = final.get("result") or {}
        other = "player_2" if me == "player_1" else "player_1"

        record = {
            "game_id": game_id,
            "game_family": final.get("game_family"),
            "your_player": me,
            "opponent": final.get("opponent"),
            "status": final.get("status"),
            "config": config,
            "result": result,
            "our_payoff": result.get(f"{me}_payoff"),
            "opponent_payoff": result.get(f"{other}_payoff"),
            "rounds_played": len(history),
            "history": history,
            "our_turns": our_turns,
        }
        path = os.path.join(self.games_dir, f"{game_id}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, default=str)
        return path

    def _append(self, path: str, record: dict) -> None:
        """Caller holds the lock."""
        try:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, default=str) + "\n")
        except OSError as exc:
            logger.warning("Could not write log record: %s", exc)
