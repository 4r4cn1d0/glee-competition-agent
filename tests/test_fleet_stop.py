from __future__ import annotations

import json

from glee_sdk import GleeClient

from glee_agent.fleet_stop import CooperativeGleeClient, CooperativeStopLimit


def _write_control(path, drain_now=(), **extra):
    path.write_text(
        json.dumps({"drain_now": list(drain_now), **extra}),
        encoding="utf-8",
    )


def test_sdk_elapsed_comparison_preserves_numeric_limit(tmp_path) -> None:
    control = tmp_path / "control.json"
    _write_control(control)
    limit = CooperativeStopLimit(
        60.0, physical_slot="champion", control_path=control
    )

    assert not (59.999 >= limit)
    assert 60.0 >= limit
    assert limit.latched
    assert limit.reason == "max_time"


def test_live_bank_flip_fires_for_physical_slot_only(tmp_path) -> None:
    control = tmp_path / "control.json"
    _write_control(control)
    limit = CooperativeStopLimit(
        3600.0, physical_slot="composite", control_path=control
    )

    assert not (10.0 >= limit)
    _write_control(control, drain_now=("hardliner",))
    assert not (11.0 >= limit)
    _write_control(control, drain_now=("composite",))
    assert 12.0 >= limit
    assert limit.reason == "fleet_control"


def test_seen_stop_is_latched_even_if_control_is_reenabled(tmp_path) -> None:
    control = tmp_path / "control.json"
    _write_control(control, drain_now=("randomized",))
    limit = CooperativeStopLimit(
        None, physical_slot="randomized", control_path=control
    )

    assert limit.control_stop_requested()
    _write_control(control)
    assert limit.control_stop_requested()
    assert 0.0 >= limit


def test_malformed_control_retains_last_complete_state(tmp_path) -> None:
    control = tmp_path / "control.json"
    _write_control(control, drain_now=("conceder",))
    limit = CooperativeStopLimit(
        None, physical_slot="champion", control_path=control
    )

    assert not limit.control_stop_requested()
    control.write_text("{", encoding="utf-8")
    assert not limit.control_stop_requested()

    # A fresh valid read replaces the retained state and can then fire.
    _write_control(control, drain_now=("champion",))
    assert limit.control_stop_requested()


def test_missing_slot_is_inert_for_standalone_runner(tmp_path) -> None:
    control = tmp_path / "control.json"
    _write_control(control, drain_now=("champion", "composite"))
    limit = CooperativeStopLimit(
        None, physical_slot=None, control_path=control
    )

    assert not limit.control_stop_requested()
    assert not (10_000.0 >= limit)


def test_real_sdk_run_uses_native_lossless_drain_after_live_flip(
    tmp_path, monkeypatch
) -> None:
    """Pin the SDK 0.0.5 comparison and drain contract we intentionally use."""
    control = tmp_path / "control.json"
    _write_control(control)
    limit = CooperativeStopLimit(
        3600.0, physical_slot="champion", control_path=control
    )
    client = GleeClient(api_key="test-key", base_url="https://invalid.test")
    queue_states = []
    leave_calls = []
    pending_calls = 0

    def queue(family):
        queue_states.append(json.loads(control.read_text(encoding="utf-8")))
        return {"status": "queued", "game_family": family}

    def pending_games():
        nonlocal pending_calls
        pending_calls += 1
        if pending_calls == 1:
            _write_control(control, drain_now=("champion",))
        return []

    monkeypatch.setattr(client, "queue", queue)
    monkeypatch.setattr(client, "leave_queue", lambda family=None: leave_calls.append(family) or {})
    monkeypatch.setattr(client, "pending_games", pending_games)
    monkeypatch.setattr(client, "stats", lambda: {"active_games": 0})

    client.run(
        lambda _game: {},
        game_families=["bargaining"],
        poll_interval=0.001,
        max_time=limit,
        concurrency=1,
    )

    assert limit.latched and limit.reason == "fleet_control"
    assert pending_calls >= 2
    assert leave_calls  # limit transition and finalizer both use this safe API
    assert all(not state.get("drain_now") for state in queue_states)


def test_queue_fence_closes_request_during_topup_race(tmp_path, monkeypatch) -> None:
    control = tmp_path / "control.json"
    _write_control(control)
    limit = CooperativeStopLimit(
        3600.0, physical_slot="hardliner", control_path=control
    )
    client = CooperativeGleeClient(
        api_key="test-key",
        base_url="https://invalid.test",
        stop_limit=limit,
    )
    base_queues = []
    leaves = []
    monkeypatch.setattr(
        GleeClient,
        "queue",
        lambda _self, family: base_queues.append(family) or {"status": "queued"},
    )
    monkeypatch.setattr(
        GleeClient,
        "leave_queue",
        lambda _self, family=None: leaves.append(family) or {},
    )

    assert client.queue("bargaining") == {"status": "queued"}
    _write_control(control, drain_now=("hardliner",))
    assert client.queue("negotiation") == {
        "status": "draining",
        "game_family": "negotiation",
    }
    assert client.queue("persuasion")["status"] == "draining"
    assert base_queues == ["bargaining"]
    assert leaves == [None]
