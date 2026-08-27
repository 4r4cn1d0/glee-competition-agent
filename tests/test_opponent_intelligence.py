from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

from scripts import opponent_intelligence as intel


def _write_game(
    root: Path,
    *,
    game_id: str,
    opponent_name: str = "",
    opponent_type: str = "agent",
    first_share: float = 0.8,
    final_decision: str = "reject",
) -> Path:
    folder = root / "logs" / "champion" / "games"
    folder.mkdir(parents=True, exist_ok=True)
    record = {
        "game_id": game_id,
        "game_family": "bargaining",
        "your_player": "player_2",
        "opponent": {"type": opponent_type, "name": opponent_name},
        "status": "completed",
        "config": {
            "game_family": "bargaining",
            "max_rounds": 12,
            "horizon_known": True,
            "proposer": "player_1",
            "money_to_divide": 100,
            "delta_1": 1.0,
            "delta_2": 0.95,
            "complete_information": True,
            "messages_allowed": True,
        },
        "result": {
            "outcome": "no_deal",
            "player_1_payoff": 0,
            "player_2_payoff": 0,
        },
        "our_payoff": 0,
        "opponent_payoff": 0,
        "rounds_played": 2,
        "history": [
            {
                "round": 1,
                "proposer": "player_1",
                "offer": {
                    "player_1_gain": 100 * first_share,
                    "player_2_gain": 100 * (1 - first_share),
                    "message": "Take this exact deal.",
                    "proposer": "player_1",
                    "round": 1,
                },
                "decision": "reject",
            },
            {
                "round": 2,
                "proposer": "player_2",
                "offer": {
                    "player_1_gain": 40,
                    "player_2_gain": 60,
                    "message": "",
                    "proposer": "player_2",
                    "round": 2,
                },
                "decision": final_decision,
                "response_time_ms": 321,
            },
        ],
        "our_turns": [
            {"ts": 1_800_000_000.0, "round": 1, "phase": "decision"},
            {"ts": 1_800_000_001.0, "round": 2, "phase": "offer"},
        ],
    }
    path = folder / f"{game_id}.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def _write_turn(root: Path, game_id: str, opponent: str) -> None:
    folder = root / "logs" / "champion"
    folder.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": 1_800_000_100.0,
        "game_id": game_id,
        "game_family": "negotiation",
        "your_player": "player_1",
        "phase": "decision",
        "round": 2,
        "opponent": {"type": "agent", "name": opponent},
        "state": {"history": []},
        "action": {"decision": "reject"},
    }
    (folder / "turns.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")


def test_extracts_each_opponent_action_once(tmp_path: Path) -> None:
    path = _write_game(tmp_path, game_id="athena-one", opponent_name="Athena")
    game = json.loads(path.read_text(encoding="utf-8"))

    moves = intel.extract_opponent_moves(game)

    assert [move["move_type"] for move in moves] == ["offer", "decision"]
    assert moves[0]["normalized"]["opponent_own_share"] == 0.8
    assert moves[0]["message_template"] == "take this exact deal."
    assert moves[1]["action"] == {"decision": "reject"}
    assert moves[1]["context"]["our_offer"]["player_1_gain"] == 40


def test_action_tokens_preserve_decision_and_persuasion_context() -> None:
    assert intel._decision("reject_offer") == "reject"
    assert intel._decision("accept_offer") == "accept"
    token = intel.action_token({
        "move_type": "buyer_decision",
        "action": {"decision": "accept"},
        "context": {"our_seller_message": "I recommend buying it."},
        "normalized": {"seller_signal_positive": 1.0},
    })
    assert token == "buyer_decision:accept:positive"
    assert intel.action_token({
        "move_type": "terminal_walkaway",
        "action": {"decision": "walkaway"},
        "normalized": {},
    }) == "terminal_walkaway:walkaway:?"


def test_refresh_exports_named_games_and_exact_hidden_tactic_match(tmp_path: Path) -> None:
    _write_game(tmp_path, game_id="athena-a", opponent_name="Athena")
    _write_game(tmp_path, game_id="athena-b", opponent_name="athena")
    _write_game(
        tmp_path,
        game_id="other",
        opponent_name="Different Bot",
        first_share=0.55,
        final_decision="accept",
    )
    _write_game(
        tmp_path,
        game_id="hidden-clone",
        opponent_type="hidden",
        first_share=0.8,
        final_decision="reject",
    )
    _write_turn(tmp_path, "live-grok", "grok 4.6")
    output = tmp_path / "intel"

    summary = intel.refresh(
        logs_root=tmp_path / "logs",
        output=output,
        slots=("champion",),
        initial_tail_mb=1,
    )

    assert summary["targets"]["athena"]["named_games"] == 2
    assert summary["targets"]["athena"]["moves"] == 4
    assert summary["targets"]["grok 4.6"]["live_unfinalized_turns"] == 1
    matches = [
        json.loads(line)
        for line in (output / "athena" / "tactic_matches.jsonl").read_text().splitlines()
    ]
    hidden = [row for row in matches if row["encounter"]["game_id"] == "hidden-clone"]
    assert hidden
    assert hidden[0]["match"]["identity_claim"] is False
    assert "exact target-unique" in hidden[0]["match"]["label"]
    assert "same observed tactic" in hidden[0]["match"]["reasons"]["interpretation"]
    assert (output / "INDEX.md").exists()
    assert "Athena" in (output / "athena" / "DOSSIER.md").read_text()


def test_refresh_is_incremental_and_updates_changed_canonical_file(tmp_path: Path) -> None:
    path = _write_game(tmp_path, game_id="gill", opponent_name="gill bates")
    output = tmp_path / "intel"
    first = intel.refresh(
        logs_root=tmp_path / "logs", output=output, slots=("champion",), initial_tail_mb=1
    )
    second = intel.refresh(
        logs_root=tmp_path / "logs", output=output, slots=("champion",), initial_tail_mb=1
    )
    assert first["scan"]["updated"] == 1
    assert second["scan"].get("updated", 0) == 0
    assert second["scan"]["unchanged"] == 1

    game = json.loads(path.read_text(encoding="utf-8"))
    game["history"][1]["decision"] = "accept"
    path.write_text(json.dumps(game) + " ", encoding="utf-8")
    third = intel.refresh(
        logs_root=tmp_path / "logs", output=output, slots=("champion",), initial_tail_mb=1
    )
    assert third["scan"]["updated"] == 1
    with sqlite3.connect(output / "opponent_intelligence.sqlite3") as db:
        action = db.execute(
            "SELECT action_json FROM target_moves WHERE encounter_id='champion:gill' AND ordinal=2"
        ).fetchone()[0]
    assert json.loads(action) == {"decision": "accept"}


def test_hidden_games_are_never_relabelled_as_target_identity(tmp_path: Path) -> None:
    for suffix in ("a", "b", "c"):
        _write_game(tmp_path, game_id=f"athena-{suffix}", opponent_name="Athena")
    _write_game(tmp_path, game_id="hidden", opponent_type="hidden")
    output = tmp_path / "intel"
    intel.refresh(
        logs_root=tmp_path / "logs", output=output, slots=("champion",), initial_tail_mb=1
    )
    with sqlite3.connect(output / "opponent_intelligence.sqlite3") as db:
        row = db.execute(
            """
            SELECT g.opponent_name,g.target_key,m.target_key,m.reasons_json
            FROM tactic_matches m JOIN games g USING(encounter_id)
            WHERE g.game_id='hidden'
            """
        ).fetchone()
    assert row[0] == ""
    assert row[1] == ""
    assert row[2] == "athena"
    assert json.loads(row[3])["identity_claim"] is False


def test_family_role_similarity_alone_does_not_create_tactic_match(tmp_path: Path) -> None:
    for index in range(8):
        path = _write_game(
            tmp_path,
            game_id=f"athena-{index}",
            opponent_name="Athena",
            first_share=0.8 + index * 0.01,
        )
        game = json.loads(path.read_text(encoding="utf-8"))
        game["config"]["max_rounds"] = 12 + index
        path.write_text(json.dumps(game), encoding="utf-8")
    hidden = _write_game(
        tmp_path,
        game_id="generic-hidden",
        opponent_type="hidden",
        first_share=0.84,
    )
    game = json.loads(hidden.read_text(encoding="utf-8"))
    game["config"]["max_rounds"] = 99
    hidden.write_text(json.dumps(game), encoding="utf-8")
    output = tmp_path / "intel"

    intel.refresh(
        logs_root=tmp_path / "logs", output=output, slots=("champion",), initial_tail_mb=1
    )

    with sqlite3.connect(output / "opponent_intelligence.sqlite3") as db:
        assert db.execute(
            "SELECT COUNT(*) FROM tactic_matches WHERE encounter_id='champion:generic-hidden'"
        ).fetchone()[0] == 0


def test_fixed_archive_boundary_excludes_older_files_and_persists(tmp_path: Path) -> None:
    cutoff = time.time() - 60
    old = _write_game(tmp_path, game_id="old-athena", opponent_name="Athena")
    os.utime(old, (cutoff - 10, cutoff - 10))
    _write_game(tmp_path, game_id="new-athena", opponent_name="Athena")
    output = tmp_path / "intel"

    first = intel.refresh(
        logs_root=tmp_path / "logs",
        output=output,
        slots=("champion",),
        initial_tail_mb=1,
        archive_start_ts=cutoff,
    )
    second = intel.refresh(
        logs_root=tmp_path / "logs",
        output=output,
        slots=("champion",),
        initial_tail_mb=1,
    )

    assert first["targets"]["athena"]["named_games"] == 1
    assert first["scan"]["before_archive_start"] == 1
    assert second["archive_start_ts"] == cutoff
    with sqlite3.connect(output / "opponent_intelligence.sqlite3") as db:
        assert db.execute("SELECT game_id FROM games").fetchall() == [("new-athena",)]
