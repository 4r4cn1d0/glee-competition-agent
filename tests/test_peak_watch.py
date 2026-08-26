from __future__ import annotations

import json
import signal

import pytest

from scripts import peak_watch


def test_clean_stop_signal_uses_internal_shutdown_path() -> None:
    # The polling loop deliberately catches ordinary API/JSON Exceptions.  The
    # shutdown sentinel must bypass that catch so SIGTERM cannot be swallowed
    # when it arrives in the middle of a poll.
    assert not issubclass(peak_watch.StopRequested, Exception)
    with pytest.raises(peak_watch.StopRequested):
        peak_watch._request_clean_stop(signal.SIGTERM, None)


def test_signal_during_poll_exits_main_and_releases_singleton(monkeypatch) -> None:
    class FakeLock:
        closed = False

        def close(self):
            self.closed = True

    lock = FakeLock()
    monkeypatch.setattr(peak_watch, "_claim_singleton", lambda: lock)
    monkeypatch.setattr(peak_watch.fcntl, "flock", lambda *_args: None)
    monkeypatch.setattr(
        peak_watch.signal,
        "signal",
        lambda _signal, _handler: signal.SIG_DFL,
    )

    def stop_mid_poll():
        peak_watch._request_clean_stop(signal.SIGTERM, None)

    monkeypatch.setattr(peak_watch, "read_control_strict", stop_mid_poll)

    assert peak_watch.main() == 0
    assert lock.closed


def test_eligible_thresholds_filters_disabled_latched_and_invalid() -> None:
    control = {
        "bank_thresholds": {
            "champion": 2400,
            "hardliner": "2450.5",
            "conceder": "bad",
            "randomized": 2500,
            "composite": 2505,
        },
        "disabled": ["hardliner"],
        "bank_latched": ["randomized"],
    }
    with pytest.raises(peak_watch.fleet.ControlUpdateError):
        peak_watch.eligible_thresholds(control)

    control["bank_thresholds"]["conceder"] = 2300
    assert peak_watch.eligible_thresholds(control) == {
        "champion": 2400.0,
        "conceder": 2300.0,
        "composite": 2505.0,
    }


def test_eligible_family_thresholds_filters_disabled_and_latched() -> None:
    control = {
        "bank_family_thresholds": {
            "champion": {"family": "bargaining", "threshold": 2600},
            "hardliner": {"family": "negotiation", "threshold": "2720.5"},
            "randomized": {"family": "persuasion", "threshold": 2500},
        },
        "disabled": ["hardliner"],
        "bank_latched": ["randomized"],
    }
    assert peak_watch.eligible_family_thresholds(control) == {
        "champion": ("bargaining", 2600.0)
    }


def test_matching_rows_uses_authenticated_player_ids_not_names() -> None:
    board = [
        {"player_id": "other", "player_name": "composite", "rating": 2700},
        {"player_id": "ours", "player_name": "renamed", "rating": 2505},
    ]
    assert peak_watch.matching_rows(board, {"ours": "composite"}) == {
        "composite": {
            "player_id": "ours",
            "player_name": "renamed",
            "rating": 2505,
            "row": 2,
        }
    }


def test_trigger_observation_uses_actual_slot_process_not_lagging_state(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        peak_watch.fleet,
        "_running_slot_command",
        lambda _slot: (777, "Python run_agent.py --log-dir logs/composite"),
    )
    monkeypatch.setattr(peak_watch, "_overlay_hash", lambda _slot: "arm-hash")
    monkeypatch.setattr(peak_watch, "_code_head", lambda: "head")

    observation = peak_watch.capture_observation(
        "composite",
        {"rank": 1, "row": 2, "player_id": "five"},
    )

    assert observation["pid"] == 777
    assert observation["process_command"].endswith("logs/composite")
    assert observation["arms_sha256_at_observation"] == "arm-hash"


def test_family_observation_captures_same_sample_activity_pid_and_stack(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        peak_watch.fleet,
        "_running_slot_command",
        lambda _slot: (777, "Python run_agent.py --log-dir logs/composite"),
    )
    monkeypatch.setattr(peak_watch, "_overlay_hash", lambda _slot: "arm-hash")
    monkeypatch.setattr(peak_watch, "_code_head", lambda: "head")
    monkeypatch.setattr(
        peak_watch,
        "game_count_deltas",
        lambda slot, stats, now=None: {
            "slot": slot,
            "current": stats["scores"]["negotiation"]["games_played"],
            "sample_ts": now,
        },
    )
    stats = {
        "agent_id": "five",
        "active_games": 4,
        "scores": {
            "bargaining": {"rating": 2501, "games_played": 101},
            "negotiation": {"rating": 2720.5, "games_played": 102},
            "persuasion": {"rating": 2403, "games_played": 103},
        },
    }

    observation = peak_watch.capture_family_observation(
        "composite", "negotiation", stats
    )

    assert observation["pid"] == 777
    assert observation["arms_sha256_at_observation"] == "arm-hash"
    assert observation["workspace_head_at_observation"] == "head"
    assert observation["active_games_at_observation"] == 4
    assert observation["authenticated_scores_at_observation"] == stats["scores"]
    assert observation["activity_deltas"]["current"] == 102
    assert observation["activity_deltas"]["sample_ts"] == observation["observed_ts"]


def test_poll_once_banks_first_authenticated_threshold_observation(
    tmp_path, monkeypatch
) -> None:
    control = tmp_path / "control.json"
    control.write_text(
        json.dumps({"bank_thresholds": {"composite": 2505}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(peak_watch.fleet, "CONTROL", str(control))
    monkeypatch.setattr(
        peak_watch,
        "fetch_overall",
        lambda _key: [{
            "player_id": "agent-five-id",
            "rating": 2505.25,
            "rank": 1,
        }],
    )
    bank_calls = []
    monkeypatch.setattr(
        peak_watch.fleet,
        "bank_observed_peak",
        lambda slot, rating, observation: (
            bank_calls.append((slot, rating, observation["pid"])) or True
        ),
    )
    monkeypatch.setattr(
        peak_watch,
        "capture_observation",
        lambda _slot, _row: {"pid": 1234, "arms_sha256_at_observation": "abc"},
    )

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key

        def stats(self):
            return {"active_games": 7, "scores": {}}

    events = []
    monkeypatch.setattr(peak_watch, "GleeClient", FakeClient)
    monkeypatch.setattr(
        peak_watch,
        "record_event",
        lambda slot, threshold, row, observation, stats: events.append(
            (slot, threshold, row["rating"], stats["active_games"])
        ),
    )

    triggered = peak_watch.poll_once(
        {"GLEE_KEY_TEST1": "auth", "GLEE_KEY_TEST5": "agent-five-key"},
        {"agent-five-id": "composite"},
    )

    assert triggered.triggered == ["composite"]
    assert triggered.missing_identity == []
    assert bank_calls == [("composite", 2505.25, 1234)]
    assert events == [("composite", 2505.0, 2505.25, 7)]


def test_poll_once_banks_first_authenticated_family_threshold_observation(
    monkeypatch,
) -> None:
    control = {
        "bank_family_thresholds": {
            "composite": {"family": "negotiation", "threshold": 2720}
        }
    }

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "agent-five-key"

        def stats(self):
            return {
                "agent_id": "agent-five-id",
                "active_games": 6,
                "scores": {
                    "bargaining": {"rating": 2500, "games_played": 100},
                    "negotiation": {"rating": 2720.25, "games_played": 101},
                    "persuasion": {"rating": 2400, "games_played": 102},
                },
            }

    monkeypatch.setattr(peak_watch, "GleeClient", FakeClient)
    monkeypatch.setattr(
        peak_watch,
        "fetch_overall",
        lambda _key: pytest.fail("family-only trigger must not fetch overall board"),
    )
    monkeypatch.setattr(
        peak_watch,
        "capture_family_observation",
        lambda _slot, family, _stats: {
            "pid": 1234,
            "family": family,
            "activity_deltas": {"current": {"negotiation": 101}},
        },
    )
    bank_calls = []
    monkeypatch.setattr(
        peak_watch.fleet,
        "bank_observed_family_peak",
        lambda slot, family, rating, observation: (
            bank_calls.append((slot, family, rating, observation["pid"])) or True
        ),
    )
    events = []
    monkeypatch.setattr(
        peak_watch,
        "record_event",
        lambda slot, threshold, row, observation, stats: events.append(
            (slot, threshold, row["family"], row["rating"], stats["active_games"])
        ),
    )

    result = peak_watch.poll_once(
        {"GLEE_KEY_TEST5": "agent-five-key"},
        {"agent-five-id": "composite"},
        control=control,
    )

    assert result == peak_watch.PollResult(["composite"], [])
    assert bank_calls == [("composite", "negotiation", 2720.25, 1234)]
    assert events == [("composite", 2720.0, "negotiation", 2720.25, 6)]


def test_poll_once_malformed_control_is_visible_not_silent_disarm(
    tmp_path, monkeypatch
) -> None:
    control = tmp_path / "control.json"
    control.write_text("{", encoding="utf-8")
    monkeypatch.setattr(peak_watch.fleet, "CONTROL", str(control))

    with pytest.raises(json.JSONDecodeError):
        peak_watch.poll_once({}, {})


@pytest.mark.parametrize(
    "control",
    [
        {"disabled": "composite"},
        {"bank_latched": {"composite": True}},
        {"bank_thresholds": []},
        {"bank_thresholds": {"composite": "nan"}},
    ],
)
def test_valid_json_with_bad_control_schema_fails_closed(control) -> None:
    with pytest.raises(peak_watch.fleet.ControlUpdateError):
        peak_watch.eligible_thresholds(control)


def test_identify_agents_isolates_failures_and_rejects_duplicate_ids(
    monkeypatch,
) -> None:
    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key

        def stats(self):
            if self.api_key == "bad":
                raise RuntimeError("unavailable")
            return {"agent_id": "duplicate", "scores": {}}

    monkeypatch.setattr(peak_watch, "GleeClient", FakeClient)
    ids, stats, errors = peak_watch.identify_agents(
        {
            "GLEE_KEY_TEST1": "one",
            "GLEE_KEY_TEST2": "bad",
            "GLEE_KEY_TEST5": "five",
        },
        {"champion", "hardliner", "composite"},
    )

    assert ids == {}
    assert set(stats) == {"champion", "composite"}
    assert "unavailable" in errors["hardliner"]
    assert "duplicate authenticated agent_id" in errors["champion"]
    assert "duplicate authenticated agent_id" in errors["composite"]


def test_poll_tries_another_authenticated_armed_key_when_test1_is_bad(
    monkeypatch,
) -> None:
    attempts = []

    def fake_fetch(key):
        attempts.append(key)
        if key == "revoked-test1":
            raise PermissionError("403")
        return [{"player_id": "five", "rating": 2400}]

    monkeypatch.setattr(peak_watch, "fetch_overall", fake_fetch)
    result = peak_watch.poll_once(
        {
            "GLEE_KEY_TEST1": "revoked-test1",
            "GLEE_KEY_TEST5": "healthy-test5",
        },
        {"one": "champion", "five": "composite"},
        control={
            "bank_thresholds": {"champion": 9999, "composite": 9999},
        },
    )

    assert attempts == ["revoked-test1", "healthy-test5"]
    assert result == peak_watch.PollResult([], ["champion"])


def test_activity_delta_uses_first_snapshot_after_cutoff_conservatively(
    tmp_path, monkeypatch
) -> None:
    history = tmp_path / "ratings_history.jsonl"
    now = 200000.0

    def cell(count):
        return {
            family: [2400.0, count]
            for family in peak_watch.FAMILIES
        }

    records = [
        {"ts": now - 86420, "composite": cell(80)},
        {"ts": now - 86380, "composite": cell(90)},
        {"ts": now - 80000, "composite": cell(95)},
    ]
    history.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    monkeypatch.setattr(peak_watch, "HISTORY_PATH", history)
    stats = {
        "scores": {
            family: {"games_played": 100}
            for family in peak_watch.FAMILIES
        }
    }

    result = peak_watch.game_count_deltas("composite", stats, now=now)
    assert result["24h"] == {
        family: 10 for family in peak_watch.FAMILIES
    }
