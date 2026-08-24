"""Prospective ITT and mechanism audit for the partial Opus buyer clone."""

from __future__ import annotations

import json
import sys

import pytest

from glee_agent import top_opus_buyer_clone as clone
from scripts import live_percentile


def _gid(treatment: bool, prefix="opus-reader") -> str:
    for index in range(10_000):
        gid = f"{prefix}-{index}"
        if clone.treatment_assignment(gid) is treatment:
            return gid
    raise AssertionError("no id for requested arm")


def _state(*, cap=10, known=True, complete=False, own=120.0,
           seller=80.0, round_no=1, offer=149.0, history=None,
           messages=False):
    state = {
        "round": round_no,
        "horizon_known": known,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_2_value": own,
        "history": list(history or []),
    }
    if known:
        state["max_rounds"] = cap
    if complete:
        state["player_1_value"] = seller
    state["last_offer"] = {
        "price": offer,
        "from_player": "player_1",
        "round": round_no,
    }
    return state


def _record(gid, *, state=None, action_type="decision", action=None,
            source=None, ts=1234.0):
    state = dict(state or _state())
    if action_type == "offer":
        state.pop("last_offer", None)
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "action_type": action_type,
        "state": state,
        "plan": {"source": source} if source else {},
        "action": action or {},
    }


def _diagnostic(gid, *, ts=1234.0, fires=None, fallbacks=0,
                failures=0, contamination=0, collisions=0,
                no_deal=False, walked=False, timeout=False):
    candidate = clone.treatment_assignment(gid) is True
    if fires is None:
        fires = int(candidate)
    return {
        "own_mult": 1.2,
        "complete_information": False,
        "horizon": "10",
        "fleet_slots": ("conceder",),
        "exposure_ts": ts,
        "buyer_turns": 1,
        "identified_action_turns": fires,
        "identified_fires": fires,
        "candidate_fallback_turns": fallbacks,
        "opus_source_turns": fires,
        "wire_failures": failures,
        "control_contamination": contamination,
        "collision_turns": collisions,
        "no_deal": no_deal,
        "walked_away": walked,
        "timeout": timeout,
    }


def _row(gid, *, pct=0.5, closed=True, ts=1234.0, fires=None,
         fallbacks=0, failures=0, contamination=0, collisions=0,
         no_deal=False, walked=False, timeout=False, resolution="terminal"):
    return (
        "conceder",
        pct,
        gid,
        closed,
        _diagnostic(
            gid, ts=ts, fires=fires, fallbacks=fallbacks,
            failures=failures, contamination=contamination,
            collisions=collisions, no_deal=no_deal, walked=walked,
            timeout=timeout),
        resolution,
    )


def _official(tmp_path, records):
    path = tmp_path / "official.json"
    path.write_text(json.dumps({"games": records}), encoding="utf-8")
    return str(path)


def test_reader_assignment_is_exact_production_assignment():
    for index in range(500):
        gid = f"opus-reader-parity-{index}"
        treatment = clone.treatment_assignment(gid)
        expected = "candidate" if treatment else "control"
        assert live_percentile.top_opus_buyer_clone_arm(gid) == expected
    assert live_percentile.top_opus_buyer_clone_arm(None) is None


def test_candidate_identified_action_is_recomputed_without_live_flag():
    gid = _gid(True, "identified")
    record = _record(
        gid,
        action={"decision": "RejectOffer", "product_price": 81.2},
        source="top_opus_buyer_clone",
    )
    exposure = live_percentile._top_opus_buyer_clone_exposure_turn(
        "conceder", record)
    assert exposure[0] == ("conceder", gid)
    assert exposure[2]["first_identified_action"] is True
    assert exposure[2]["first_candidate_fallback"] is False
    assert exposure[2]["first_wire_ok"] is True
    assert exposure[2]["first_mechanism_ok"] is True


def test_candidate_fallback_is_enrolled_and_not_mislabeled_as_fire():
    gid = _gid(True, "fallback")
    exposure = live_percentile._top_opus_buyer_clone_exposure_turn(
        "conceder",
        _record(
            gid,
            state=_state(cap=20),
            action={"decision": "RejectOffer", "product_price": 70.0},
            source="ordinary_control",
        ),
    )
    assert exposure is not None
    assert exposure[2]["first_identified_action"] is False
    assert exposure[2]["first_candidate_fallback"] is True
    assert exposure[2]["first_wire_ok"] is True


def test_buyer_opening_is_an_itt_exposure_not_selected_out():
    gid = _gid(True, "opening")
    exposure = live_percentile._top_opus_buyer_clone_exposure_turn(
        "conceder",
        _record(
            gid,
            action_type="offer",
            action={"product_price": 81.2},
            source="top_opus_buyer_clone",
        ),
    )
    assert exposure is not None
    assert exposure[2]["first_action_type"] == "offer"
    assert exposure[2]["first_identified_action"] is True
    assert exposure[2]["first_wire_ok"] is True


def test_trace_audit_distinguishes_fire_fallback_control_and_collision(
        monkeypatch, tmp_path):
    candidate = _gid(True, "trace-candidate")
    control = _gid(False, "trace-control")
    collision = _gid(True, "trace-collision")
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    records = [
        _record(
            candidate,
            action={"decision": "RejectOffer", "product_price": 81.2},
            source="top_opus_buyer_clone",
            ts=100.0,
        ),
        _record(
            candidate,
            state=_state(cap=20),
            action={"decision": "RejectOffer", "product_price": 70.0},
            source="ordinary_control",
            ts=101.0,
        ),
        _record(
            candidate,
            action={"decision": "RejectOffer", "product_price": 81.21},
            source="top_opus_buyer_clone",
            ts=102.0,
        ),
        _record(
            control,
            action={"decision": "RejectOffer", "product_price": 70.0},
            source="top_opus_buyer_clone",
            ts=103.0,
        ),
        _record(
            collision,
            action={"decision": "RejectOffer", "product_price": 90.0},
            source="top_buyer_clone",
            ts=104.0,
        ),
    ]
    (log_dir / "turns.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))

    rows = [_row(candidate), _row(control), _row(collision)]
    audited = list(live_percentile._top_opus_buyer_clone_trace_audit(rows))
    by_gid = {row[2]: row[4] for row in audited}
    assert by_gid[candidate]["identified_action_turns"] == 2
    assert by_gid[candidate]["identified_fires"] == 1
    assert by_gid[candidate]["candidate_fallback_turns"] == 1
    assert by_gid[candidate]["wire_failures"] == 1
    assert by_gid[control]["control_contamination"] == 1
    assert by_gid[collision]["collision_turns"] == 1


@pytest.mark.parametrize(
    ("status", "outcome", "field"),
    [
        ("no_deal", "no_deal", "no_deal"),
        ("completed", "walked_away", "walked_away"),
        ("timeout", "timeout", "timeout"),
    ],
)
def test_terminal_row_retains_each_nonclose_outcome(
        monkeypatch, status, outcome, field):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.17)
    gid = _gid(True, f"terminal-{field}")
    final = {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "status": status,
        "game_state": _state(),
        "result": {
            "outcome": outcome,
            "player_1_payoff": 0.0,
            "player_2_payoff": 0.0,
        },
    }
    row = live_percentile._top_opus_buyer_clone_row(
        "conceder", {"game_id": gid}, final)
    assert row[:4] == ("conceder", 0.17, gid, False)
    assert row[4][field] is True


def test_games_reader_retains_unresolved_assigned_opening(
        monkeypatch, tmp_path):
    gid = _gid(True, "pending-opening")
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    record = _record(
        gid,
        action_type="offer",
        action={"product_price": 81.2},
        source="top_opus_buyer_clone",
        ts=150.0,
    )
    (log_dir / "turns.jsonl").write_text(
        json.dumps(record) + "\n", encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 151.0)

    rows = list(live_percentile.top_opus_buyer_clone_games(
        24.0, since=100.0, until=200.0))
    assert len(rows) == 1
    assert rows[0][2] == gid
    assert rows[0][3] is None
    assert rows[0][-1] == "pending"
    assert rows[0][4]["identified_fires"] == 1


def test_report_requires_clean_t0(capsys):
    assert live_percentile.report_top_opus_buyer_clone([], 24.0) == 2
    assert "CLEAN T0 REQUIRED" in capsys.readouterr().out


def test_report_outputs_official_itt_and_fire_fallback_diagnostics(
        tmp_path, capsys):
    controls = [_gid(False, f"report-control-{index}") for index in range(2)]
    candidates = [_gid(True, f"report-candidate-{index}") for index in range(2)]
    rows = [
        _row(controls[0], pct=0.4, no_deal=True, closed=False, fires=0),
        _row(controls[1], pct=0.4, fires=0),
        _row(candidates[0], pct=0.6, fires=1),
        _row(candidates[1], pct=0.6, fires=0, fallbacks=1,
             walked=True, closed=False),
    ]
    official = _official(tmp_path, [
        *[{"slot": "conceder", "game_id": gid, "rating_delta": 0.0}
          for gid in controls],
        *[{"slot": "conceder", "game_id": gid, "rating_delta": 2.0}
          for gid in candidates],
    ])
    assert live_percentile.report_top_opus_buyer_clone(
        rows, 24.0, since=100.0, official_path=official) == 0
    output = capsys.readouterr().out
    assert "official rating delta: +2.0000" in output
    assert "games with identified fire=1, fallback-only=1, " \
           "unaudited/no-turn=0" in output
    assert "no-deal rate" in output
    assert "walk-away rate" in output
    assert "PROSPECTIVE READ COMPLETE" in output


def test_report_blocks_on_unresolved_without_dropping_assignment(
        tmp_path, capsys):
    control = _gid(False, "unresolved-control")
    candidate = _gid(True, "unresolved-candidate")
    rows = [
        _row(control, fires=0),
        _row(candidate, pct=None, closed=None, fires=0, fallbacks=1,
             resolution="pending"),
    ]
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": control, "rating_delta": 0.0},
    ])
    assert live_percentile.report_top_opus_buyer_clone(
        rows, 24.0, since=100.0, official_path=official) == 1
    output = capsys.readouterr().out
    assert "assigned=1" in output
    assert "unresolved=1" in output
    assert "READ BLOCKED" in output


def test_report_rejects_wire_control_and_collision_failures(
        tmp_path, capsys):
    control = _gid(False, "mechanism-control")
    candidate = _gid(True, "mechanism-candidate")
    rows = [
        _row(control, fires=0, contamination=1),
        _row(candidate, failures=1, collisions=1),
    ]
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": control, "rating_delta": 0.0},
        {"slot": "conceder", "game_id": candidate, "rating_delta": 0.0},
    ])
    assert live_percentile.report_top_opus_buyer_clone(
        rows, 24.0, since=100.0, official_path=official) == 2
    output = capsys.readouterr().out
    assert "MECHANISM REJECTION" in output
    assert "candidate-wire/control/collision" in output


def test_report_applies_prospective_rating_harm_boundary(tmp_path, capsys):
    controls = [_gid(False, f"harm-control-{index}") for index in range(10)]
    candidates = [_gid(True, f"harm-candidate-{index}") for index in range(10)]
    rows = [
        *[_row(gid, fires=0, ts=1000.0 + index)
          for index, gid in enumerate(controls)],
        *[_row(gid, ts=2000.0 + index)
          for index, gid in enumerate(candidates)],
    ]
    official = _official(tmp_path, [
        *[{"slot": "conceder", "game_id": gid, "rating_delta": 0.0}
          for gid in controls],
        *[{"slot": "conceder", "game_id": gid, "rating_delta": -2.0}
          for gid in candidates],
    ])
    assert live_percentile.report_top_opus_buyer_clone(
        rows, 24.0, since=100.0, official_path=official) == 2
    assert "<= -1 rating/game" in capsys.readouterr().out


def test_cli_requires_since_before_reading_logs(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["live_percentile.py", "--ab", "top-opus-buyer-clone"])
    with pytest.raises(SystemExit) as exc:
        live_percentile.main()
    assert exc.value.code == 2
