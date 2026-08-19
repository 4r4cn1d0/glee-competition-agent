#!/usr/bin/env python
"""Verify the API key and the local install without playing a game.

``GET /api/agent/stats`` is not competition-gated, so a successful response
proves the key is valid and requests reach the platform even outside the
competition window.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_sdk import GleeAPIError, GleeClient  # noqa: E402

from glee_agent.config import Config  # noqa: E402


def main() -> int:
    cfg = Config.from_env()
    if not cfg.api_key:
        print("FAIL  GLEE_API_KEY is not set")
        return 1
    if not cfg.api_key.startswith("glee_"):
        print(f"WARN  key does not look like a GLEE key (starts {cfg.api_key[:6]!r})")

    client = (GleeClient(api_key=cfg.api_key, base_url=cfg.base_url)
              if cfg.base_url else GleeClient(api_key=cfg.api_key))
    try:
        stats = client.stats()
    except GleeAPIError as exc:
        hint = {401: "the key matches no agent — check for typos, or reset it",
                403: "missing header, deactivated agent, or unaccepted Terms of Service"}
        print(f"FAIL  {exc}\n      {hint.get(exc.status_code, '')}")
        return 1

    print(f"OK    key valid — agent {stats.get('agent_name')!r} ({stats.get('agent_id')})")
    print(f"      active games: {stats.get('active_games')}")
    scores = stats.get("scores") or {}
    if not scores:
        print("      no completed games yet (new agents start at 1000)")
    for family, entry in sorted(scores.items()):
        games = entry.get("games_played", 0)
        # The API returns the display rating, already shrunk toward 1000 by
        # g/(g+30). Inverting it shows what the play has actually earned.
        shrink = games / (games + 30) if games else 0.0
        raw = (entry["rating"] - 1000 * (1 - shrink)) / shrink if shrink else float("nan")
        print(f"      {family:12s} display {entry['rating']:7.1f}  "
              f"raw ~{raw:7.1f}  games {games}")

    if cfg.llm_mode != "off":
        try:
            import litellm  # noqa: F401
            print(f"OK    litellm installed; model {cfg.llm_model}")
        except ImportError:
            print("WARN  litellm missing — LLM mode will fall back to heuristics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
