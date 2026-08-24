"""Outcome collector backlog accounting and scheduling."""

from __future__ import annotations

import json

from scripts import collect


def _jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows),
                    encoding="utf-8")


def test_pending_ids_recognizes_both_outcome_stores(monkeypatch, tmp_path):
    monkeypatch.setattr(collect, "REPO", str(tmp_path))
    log_dir = tmp_path / "logs" / "probe"
    _jsonl(log_dir / "turns.jsonl", [
        {"game_id": "in-results"},
        {"game_id": "pending-old"},
        {"game_id": "in-games"},
        {"game_id": "pending-new"},
        {"game_id": "pending-old"},
    ])
    _jsonl(log_dir / "results.jsonl", [{"game_id": "in-results"}])
    games_dir = log_dir / "games"
    games_dir.mkdir()
    (games_dir / "in-games.json").write_text("{}", encoding="utf-8")

    assert collect.pending_ids("probe") == ["pending-old", "pending-new"]


def test_selected_ids_splits_budget_between_oldest_and_newest():
    pending = [f"game-{index}" for index in range(10)]
    assert collect.selected_ids(pending, 5) == [
        "game-7", "game-8", "game-9", "game-0", "game-1"]
    assert collect.selected_ids(pending[:3], 5) == pending[:3]
    assert collect.selected_ids(pending, 0) == []
