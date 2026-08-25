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


def test_start_clears_bank_latch_but_ordinary_stop_does_not_create_one(
    tmp_path, monkeypatch
) -> None:
    path = _configure_paths(
        tmp_path,
        monkeypatch,
        {"disabled": ["composite"], "drain_now": ["composite"]},
    )

    assert fleet.enable("composite", True) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "disabled": [],
        "drain_now": [],
    }

    assert fleet.enable("composite", False) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "disabled": ["composite"],
        "drain_now": [],
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
    monkeypatch.setattr(fleet, "_pid_alive", lambda pid: pid == 111)

    assert fleet._live_banking_slots(
        json.loads(control.read_text(encoding="utf-8")),
        json.loads(state.read_text(encoding="utf-8")),
    ) == ["champion"]
    assert fleet.safe_restart() == 1
