from __future__ import annotations

import json

import pytest

from scripts import fleet


def _configure_paths(tmp_path, monkeypatch, control):
    path = tmp_path / "control.json"
    path.write_text(json.dumps(control), encoding="utf-8")
    monkeypatch.setattr(fleet, "CONTROL", str(path))
    monkeypatch.setattr(fleet, "CONTROL_LOCK", str(path) + ".lock")
    return path


def test_bank_atomically_preserves_control_and_disables_relaunch(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(
        tmp_path,
        monkeypatch,
        {
            "shift_seconds": 3600,
            "disabled": ["conceder"],
            "drain_now": ["hardliner"],
            "policy": {"composite": "hardliner"},
        },
    )

    assert fleet.bank("composite") == 0
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["shift_seconds"] == 3600
    assert saved["policy"] == {"composite": "hardliner"}
    assert saved["disabled"] == ["composite", "conceder"]
    assert saved["drain_now"] == ["composite", "hardliner"]
    assert saved["bank_latched"] == ["composite"]


def test_start_after_process_is_down_clears_drain_but_retains_one_shot_latch(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(
        tmp_path,
        monkeypatch,
        {
            "disabled": ["composite"],
            "drain_now": ["composite"],
            "bank_latched": ["composite"],
        },
    )
    monkeypatch.setattr(fleet, "_running_slot_command", lambda _probe: (None, ""))

    assert fleet.enable("composite", True) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "disabled": [],
        "drain_now": [],
        "bank_latched": ["composite"],
    }

    assert fleet.enable("composite", False) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "disabled": ["composite"],
        "drain_now": [],
        "bank_latched": ["composite"],
    }


def test_start_cannot_cancel_a_bank_while_the_runner_is_alive(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(
        tmp_path,
        monkeypatch,
        {
            "disabled": ["composite"],
            "drain_now": ["composite"],
            "bank_latched": ["composite"],
        },
    )
    monkeypatch.setattr(
        fleet,
        "_running_slot_command",
        lambda _probe: (1234, "python run_agent.py --max-time 3600"),
    )

    assert fleet.enable("composite", True) == 1
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "disabled": ["composite"],
        "drain_now": ["composite"],
        "bank_latched": ["composite"],
    }


def test_status_labels_distinguish_bank_from_boundary_stop() -> None:
    disabled = {"champion", "composite"}
    drain_now = {"composite"}
    assert fleet._status_label(
        "composite", alive=True, disabled=disabled, drain_now=drain_now
    ) == "BANKING"
    assert fleet._status_label(
        "composite", alive=False, disabled=disabled, drain_now=drain_now
    ) == "BANKED"
    assert fleet._status_label(
        "champion", alive=True, disabled=disabled, drain_now=drain_now
    ) == "STOP-QUEUED"
    assert fleet._status_label(
        "champion", alive=False, disabled=disabled, drain_now=drain_now
    ) == "DISABLED"


def test_malformed_control_fails_closed_without_overwrite(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(tmp_path, monkeypatch, {})
    path.write_text("{", encoding="utf-8")
    monkeypatch.setattr(fleet, "_running_slot_command", lambda _probe: (None, ""))

    with pytest.raises(fleet.ControlUpdateError):
        fleet.bank("composite")
    assert path.read_text(encoding="utf-8") == "{"


def test_valid_json_schema_corruption_fails_closed_without_rewrite(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(tmp_path, monkeypatch, {"disabled": "composite"})
    monkeypatch.setattr(fleet, "_running_slot_command", lambda _probe: (None, ""))

    with pytest.raises(fleet.ControlUpdateError):
        fleet.bank("composite")
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "disabled": "composite"
    }


def test_bank_refuses_unknown_or_unbounded_live_slot(tmp_path, monkeypatch) -> None:
    path = _configure_paths(tmp_path, monkeypatch, {"shift_seconds": 3600})
    assert fleet.bank("agent5") == 1

    monkeypatch.setattr(
        fleet,
        "_running_slot_command",
        lambda _probe: (1234, "python run_agent.py --probe hardliner"),
    )
    assert fleet.bank("composite") == 1
    assert json.loads(path.read_text(encoding="utf-8")) == {"shift_seconds": 3600}


def test_safe_restart_refuses_only_live_bank_latches(tmp_path, monkeypatch) -> None:
    control = tmp_path / "control.json"
    state = tmp_path / "supervisor.json"
    control.write_text(
        json.dumps({"drain_now": ["champion", "composite"]}),
        encoding="utf-8",
    )
    state.write_text(
        json.dumps({"agents": {"champion": 111, "composite": None}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(fleet, "CONTROL", str(control))
    monkeypatch.setattr(fleet, "STATE", str(state))
    monkeypatch.setattr(
        fleet,
        "_running_slot_command",
        lambda probe: (
            (111, "python run_agent.py") if probe == "champion" else (None, "")
        ),
    )

    assert fleet._live_banking_slots(
        json.loads(control.read_text(encoding="utf-8")),
        json.loads(state.read_text(encoding="utf-8")),
    ) == ["champion"]
    assert fleet.safe_restart() == 1


def test_actual_process_table_maps_physical_slot_from_log_dir() -> None:
    output = """
      111 Python run_agent.py --probe hardliner --log-dir logs/composite --max-time 3600
      222 Python run_agent.py --probe champion --log-dir logs/hardliner --max-time 3600
      333 zsh -c rg run_agent.py --log-dir logs/champion
    """
    assert fleet._slot_processes_from_ps(output) == {
        "composite": (
            111,
            "Python run_agent.py --probe hardliner --log-dir logs/composite --max-time 3600",
        ),
        "hardliner": (
            222,
            "Python run_agent.py --probe champion --log-dir logs/hardliner --max-time 3600",
        ),
    }


def test_peak_threshold_is_one_shot_and_banks_atomically(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(tmp_path, monkeypatch, {"shift_seconds": 3600})
    monkeypatch.setattr(
        fleet,
        "_running_slot_command",
        lambda _probe: (1234, "python run_agent.py --max-time 3600"),
    )
    monkeypatch.setattr(fleet, "_ensure_peak_watcher", lambda: 4321)

    assert fleet.set_peak("randomized", "2505") == 0
    assert not fleet.bank_observed_peak("randomized", 2504.99)
    assert fleet.bank_observed_peak(
        "randomized", 2505.0, {"pid": 1234, "overlay_sha256": "abc"}
    )
    assert not fleet.bank_observed_peak("randomized", 2600.0)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["bank_thresholds"] == {"randomized": 2505.0}
    assert saved["bank_latched"] == ["randomized"]
    assert saved["disabled"] == ["randomized"]
    assert saved["drain_now"] == ["randomized"]
    assert saved["bank_observations"]["randomized"]["observed_rating"] == 2505.0
    assert saved["bank_observations"]["randomized"]["threshold"] == 2505.0
    assert saved["bank_observations"]["randomized"]["pid"] == 1234

    assert fleet.set_peak("randomized", None) == 0
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["bank_thresholds"] == {}
    assert saved["bank_latched"] == []
    assert saved["bank_observations"] == {}


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "0", "-1", "bad"])
def test_peak_rejects_non_finite_and_non_positive_thresholds(
    tmp_path, monkeypatch, value
) -> None:
    path = _configure_paths(tmp_path, monkeypatch, {"shift_seconds": 3600})
    monkeypatch.setattr(
        fleet,
        "_ensure_peak_watcher",
        lambda: pytest.fail("watcher must not start for an invalid threshold"),
    )

    assert fleet.set_peak("composite", value) == 1
    assert json.loads(path.read_text(encoding="utf-8")) == {"shift_seconds": 3600}
