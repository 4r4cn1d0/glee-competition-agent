"""Regression coverage for the continuous ratings snapshotter."""

from __future__ import annotations

import io
import json
import sys
import types

import pytest

from scripts import snapshot as snapshot_script


def _env(version: str) -> dict[str, str]:
    return {f"GLEE_KEY_TEST{i}": f"{version}-{i}" for i in range(1, 6)}


def _write_env(path, values: dict[str, str]) -> None:
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()),
                    encoding="utf-8")


def test_test4_slot_is_randomized() -> None:
    slots = dict(snapshot_script.KEYS)
    assert slots["GLEE_KEY_TEST4"] == "randomized"
    assert "specialist" not in slots.values()


def test_env_rotation_replaces_mapping_and_read_failure_keeps_last_good(
        tmp_path, capsys) -> None:
    path = tmp_path / ".env"
    _write_env(path, _env("old"))
    old = snapshot_script.reload_env(None, path)

    _write_env(path, _env("new"))
    new = snapshot_script.reload_env(old, path)
    assert new["GLEE_KEY_TEST4"] == "new-4"

    path.unlink()
    fallback = snapshot_script.reload_env(new, path)
    assert fallback is new
    warning = capsys.readouterr().err
    assert "cannot reload .env" in warning
    assert "using last good key mapping" in warning


def test_main_reloads_env_before_every_poll(tmp_path, monkeypatch) -> None:
    class StopLoop(Exception):
        pass

    mappings = iter([_env("first"), _env("second")])
    seen = []
    monkeypatch.setattr(snapshot_script, "LOCK", str(tmp_path / "snapshot.lock"))
    monkeypatch.setattr(snapshot_script, "reload_env", lambda _old: next(mappings))
    monkeypatch.setattr(
        snapshot_script, "snapshot",
        lambda env: seen.append(env.copy()) or {})
    monkeypatch.setattr(
        snapshot_script, "report_slot_failures", lambda _row, _streaks: 0)

    def stop_after_two_polls(_interval):
        if len(seen) == 2:
            raise StopLoop

    monkeypatch.setattr(snapshot_script.time, "sleep", stop_after_two_polls)
    with pytest.raises(StopLoop):
        snapshot_script.main()

    assert [env["GLEE_KEY_TEST4"] for env in seen] == ["first-4", "second-4"]
    assert not (tmp_path / "snapshot.lock").exists()


def test_slot_failure_warning_escalates_per_slot_and_resets(capsys) -> None:
    streaks = {}
    failed = {"randomized": {"error": "[403] Agent is deactivated"}}

    for _ in range(3):
        assert snapshot_script.report_slot_failures(failed, streaks) == 1

    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 3
    assert all("slot randomized" in line for line in lines)
    assert "WARNING" in lines[0] and "1 consecutive poll" in lines[0]
    assert "PERSISTENT ERROR" in lines[2] and "3 consecutive polls" in lines[2]

    snapshot_script.report_slot_failures(
        {"randomized": {"bargaining": [2100, 10]}}, streaks)
    snapshot_script.report_slot_failures(failed, streaks)
    assert streaks["randomized"] == 1
    assert "1 consecutive poll" in capsys.readouterr().err


def test_snapshot_uses_reloaded_env_for_board_auth_and_randomized_slot(
        tmp_path, monkeypatch) -> None:
    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key

        def stats(self):
            scores = {family: {"rating": 2100.0, "games_played": 10}
                      for family in ("bargaining", "negotiation", "persuasion")}
            if self.api_key == "fresh-5":
                return {"scores": scores}
            return {"agent_id": f"id-{self.api_key}", "scores": scores}

    requests = []

    def fake_urlopen(request, timeout):
        assert timeout == 20
        requests.append(request)
        data = [{"player_name": "missing id", "rank": 1, "rating": 2300.0},
                {"player_id": "id-fresh-4", "player_name": "Test 4",
                 "rank": 7, "rating": 2200.0}]
        return io.BytesIO(json.dumps(data).encode("utf-8"))

    monkeypatch.setitem(sys.modules, "glee_sdk",
                        types.SimpleNamespace(GleeClient=FakeClient))
    monkeypatch.setattr(snapshot_script.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(snapshot_script, "OUT", str(tmp_path / "history.jsonl"))
    monkeypatch.setenv("GLEE_KEY_TEST1", "stale-process-key")

    row = snapshot_script.snapshot(_env("fresh"))

    assert len(requests) == 4
    assert any(request.full_url.endswith("/api/leaderboard/overall")
               for request in requests)
    assert all(request.get_header("Authorization") == "Bearer fresh-1"
               for request in requests)
    assert "randomized" in row and "specialist" not in row
    assert all(len(board["ours"]) == 1 and
               board["ours"][0]["slot"] == "randomized"
               for board in row["boards"].values())
