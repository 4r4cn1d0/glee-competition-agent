"""Batch and atomic per-game outcome logging."""

from __future__ import annotations

import json

from glee_agent.gamelog import GameLog


def _game(game_id, payoff):
    return {
        "game_id": game_id,
        "game_family": "negotiation",
        "your_player": "player_1",
        "status": "completed",
        "opponent": {"type": "hidden", "name": None},
        "game_state": {
            "game_family": "negotiation",
            "round": 1,
            "current_player": "player_1",
            "history": [],
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_1_value": 80.0,
            "complete_information": False,
        },
        "result": {
            "outcome": "agreement",
            "player_1_payoff": payoff,
            "player_2_payoff": 10.0,
        },
    }


def test_batch_join_preserves_each_games_own_turns_and_is_atomic(tmp_path):
    log = GameLog(str(tmp_path))
    for game_id, price in (("one", 90.0), ("two", 100.0), ("one", 95.0)):
        log.turn({
            "game_id": game_id,
            "game_family": "negotiation",
            "your_player": "player_1",
            "game_state": {"round": 1},
            "valid_actions": {"type": "offer"},
        }, {"product_price": price}, {"marker": game_id}, "heuristic")

    assert log.write_game_records([
        ("one", _game("one", 15.0)),
        ("two", _game("two", 20.0)),
    ]) == 2
    one = json.loads((tmp_path / "games" / "one.json").read_text())
    two = json.loads((tmp_path / "games" / "two.json").read_text())
    assert [turn["action"]["product_price"] for turn in one["our_turns"]] == [90.0, 95.0]
    assert [turn["action"]["product_price"] for turn in two["our_turns"]] == [100.0]
    assert list((tmp_path / "games").glob("*.tmp")) == []


def test_finalize_fetches_then_uses_the_batch_writer(monkeypatch, tmp_path):
    log = GameLog(str(tmp_path))
    finals = {"one": _game("one", 15.0), "two": _game("two", 20.0)}

    class Client:
        def game_state(self, game_id):
            return finals[game_id]

    calls = []
    original = log.write_game_records

    def recording_batch(rows):
        rows = list(rows)
        calls.append([game_id for game_id, _final in rows])
        return original(rows)

    monkeypatch.setattr(log, "write_game_records", recording_batch)
    assert log.finalize(Client(), ["one", "two"]) == 2
    assert calls == [["one", "two"]]
    assert len((tmp_path / "results.jsonl").read_text().splitlines()) == 2
