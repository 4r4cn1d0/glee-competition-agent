"""Prospective ITT reader for the hidden known-horizon cap-10 clone slice."""

from __future__ import annotations

import json
import sys

import pytest

from glee_agent import top_buyer_clone_hi_cap10 as clone
from scripts import live_percentile


def _gid(treatment: bool, prefix="scoped-reader") -> str:
    for index in range(10_000):
        gid = f"{prefix}-{index}"
        if clone.treatment_assignment(gid) is treatment:
            return gid
    raise AssertionError("no id for requested arm")


def _gids(treatment: bool, count: int, prefix: str) -> list[str]:
    found = []
    for index in range(100_000):
        gid = f"{prefix}-{index}"
        if clone.treatment_assignment(gid) is treatment:
            found.append(gid)
            if len(found) == count:
                return found
    raise AssertionError("not enough ids for requested arm")


def _state(*, own=120.0, cap=10, known=True, complete=False,
           messages=False, offer=149.0, history=None):
    state = {
        "round": 1,
        "horizon_known": known,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_2_value": own,
        "last_offer": {
            "price": offer,
            "from_player": "player_1",
            "round": 1,
        },
        "history": list(history or []),
    }
    if known:
        state["max_rounds"] = cap
    if complete:
        state["player_1_value"] = 80.0
    return state


def _record(gid, *, state=None, action_type="decision", action=None,
            source=None, ts=1234.0):
    state = dict(state or _state())
    if action is None and clone.treatment_assignment(gid) is True:
        action = live_percentile._top_buyer_clone_hi_cap10_expected_action(
            gid, "player_2", state)
    action = dict(action or {})
    action.pop("_plan", None)
    if source is None and clone.treatment_assignment(gid) is True:
        source = clone.PLAN_SOURCE
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "action_type": action_type,
        "state": state,
        "plan": {"source": source} if source else {},
        "action": action,
    }


def _diagnostic(gid, *, own_mult=1.2, scale=100.0, messages=False,
                ts=1234.0, failures=0, contamination=0, collisions=0,
                no_deal=False, walked=False, timeout=False, slot="conceder"):
    candidate = clone.treatment_assignment(gid) is True
    return {
        "own_mult": own_mult,
        "scale": scale,
        "base": scale,
        "messages_allowed": messages,
        "complete_information": False,
        "horizon": "10",
        "fleet_slots": (slot,),
        "exposure_ts": ts,
        "buyer_turns": 1,
        "scoped_source_turns": int(candidate),
        "wire_failures": failures,
        "control_contamination": contamination,
        "collision_turns": collisions,
        "no_deal": no_deal,
        "walked_away": walked,
        "timeout": timeout,
    }


def _row(gid, *, slot="conceder", pct=0.5, closed=True,
         resolution="terminal", **diagnostic):
    return (
        slot,
        pct,
        gid,
        closed,
        _diagnostic(gid, slot=slot, **diagnostic),
        resolution,
    )


def _official(tmp_path, rows):
    path = tmp_path / "official.json"
    path.write_text(json.dumps({"games": rows}), encoding="utf-8")
    return str(path)


def test_assignment_uses_only_the_scoped_production_salt():
    for index in range(500):
        gid = f"scoped-parity-{index}"
        expected = ("candidate" if clone.treatment_assignment(gid)
                    else "control")
        assert live_percentile.top_buyer_clone_hi_cap10_arm(gid) == expected
    assert live_percentile.top_buyer_clone_hi_cap10_arm(None) is None


def test_exposure_requires_exact_eligible_first_decision_and_audits_wire():
    gid = _gid(True, "eligible")
    exposure = live_percentile._top_buyer_clone_hi_cap10_exposure_turn(
        "conceder", _record(gid))
    assert exposure[0] == ("conceder", gid)
    assert exposure[1] == 1234.0
    assert exposure[2]["first_source"] == clone.PLAN_SOURCE
    assert exposure[2]["first_wire_ok"] is True
    assert exposure[2]["first_mechanism_ok"] is True
    assert exposure[2]["own_mult"] == 1.2
    assert exposure[2]["scale"] == 100.0

    for record in (
        _record(gid, action_type="offer"),
        _record(gid, state=_state(complete=True)),
        _record(gid, state=_state(known=False)),
        _record(gid, state=_state(cap=1)),
        _record(gid, state={"round": 1}),
    ):
        assert live_percentile._top_buyer_clone_hi_cap10_exposure_turn(
            "conceder", record) is None


def test_exposure_retains_bad_candidate_and_contaminated_control():
    candidate = _gid(True, "bad-wire")
    bad = live_percentile._top_buyer_clone_hi_cap10_exposure_turn(
        "conceder",
        _record(candidate, action={"decision": "RejectOffer",
                                   "product_price": 86.01}),
    )
    assert bad is not None
    assert bad[2]["first_wire_ok"] is False

    control = _gid(False, "bad-control")
    contaminated = live_percentile._top_buyer_clone_hi_cap10_exposure_turn(
        "conceder",
        _record(control, action={"decision": "RejectOffer",
                                 "product_price": 86.0},
                source=clone.PLAN_SOURCE),
    )
    assert contaminated is not None
    assert contaminated[2]["first_wire_ok"] is False


def test_trace_audit_checks_all_candidate_turns_control_and_collisions(
        monkeypatch, tmp_path):
    candidate = _gid(True, "trace-candidate")
    control = _gid(False, "trace-control")
    collision = _gid(True, "trace-collision")
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    records = [
        _record(candidate, ts=100.0),
        _record(candidate, action={"decision": "RejectOffer",
                                   "product_price": 86.01}, ts=101.0),
        _record(control, action={"decision": "RejectOffer",
                                 "product_price": 86.0},
                source=clone.PLAN_SOURCE, ts=102.0),
        _record(collision, action={"decision": "RejectOffer",
                                   "product_price": 86.0},
                source="top_buyer_clone", ts=103.0),
    ]
    (log_dir / "turns.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))

    audited = live_percentile._top_buyer_clone_hi_cap10_trace_audit([
        _row(candidate), _row(control), _row(collision),
    ])
    by_gid = {row[2]: row[4] for row in audited}
    assert by_gid[candidate]["buyer_turns"] == 2
    assert by_gid[candidate]["wire_failures"] == 1
    assert by_gid[control]["control_contamination"] == 1
    assert by_gid[collision]["collision_turns"] == 1
    assert by_gid[collision]["wire_failures"] == 1


@pytest.mark.parametrize(
    ("status", "outcome", "field"),
    [
        ("no_deal", "no_deal", "no_deal"),
        ("completed", "walked_away", "walked_away"),
        ("timeout", "timeout", "timeout"),
    ],
)
def test_terminal_row_retains_nonclose_outcomes(
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
    row = live_percentile._top_buyer_clone_hi_cap10_row(
        "conceder", {"game_id": gid}, final)
    assert row[:4] == ("conceder", 0.17, gid, False)
    assert row[4][field] is True


def test_games_reader_retains_unresolved_assigned_decision(monkeypatch, tmp_path):
    gid = _gid(True, "pending")
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    (log_dir / "turns.jsonl").write_text(
        json.dumps(_record(gid, ts=150.0)) + "\n", encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 151.0)

    rows = list(live_percentile.top_buyer_clone_hi_cap10_games(
        24.0, since=100.0, until=200.0))
    assert len(rows) == 1
    assert rows[0][2] == gid
    assert rows[0][3] is None
    assert rows[0][-1] == "pending"
    assert rows[0][4]["scoped_source_turns"] == 1


def test_report_joins_official_outcomes_and_prints_all_strata(tmp_path, capsys):
    control_a = _gid(False, "report-control-a")
    candidate_a = _gid(True, "report-candidate-a")
    control_b = _gid(False, "report-control-b")
    candidate_b = _gid(True, "report-candidate-b")
    rows = [
        _row(control_a, slot="conceder"),
        _row(candidate_a, slot="conceder"),
        _row(control_b, slot="champion", own_mult=1.5, scale=10_000.0,
             messages=True, closed=False, no_deal=True),
        _row(candidate_b, slot="champion", own_mult=1.5, scale=10_000.0,
             messages=True, closed=False, walked=True),
    ]
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": control_a, "rating_delta": 0.0},
        {"slot": "conceder", "game_id": candidate_a, "rating_delta": 2.0},
        {"slot": "champion", "game_id": control_b, "rating_delta": 0.0},
        {"slot": "champion", "game_id": candidate_b, "rating_delta": 2.0},
    ])
    assert live_percentile.report_top_buyer_clone_hi_cap10(
        rows, 24.0, since=100.0, official_path=official) == 1
    output = capsys.readouterr().out
    assert "official rating delta: +2.0000" in output
    assert "no-deal rate" in output
    assert "walk-away rate" in output
    assert "host=conceder" in output
    assert "own_mult=1.5" in output
    assert "messages_allowed=True" in output
    assert "scale=10000.0" in output
    assert "COLLECT MORE" in output


def test_report_fails_closed_on_wire_control_or_collision(tmp_path, capsys):
    control = _gid(False, "mechanism-control")
    candidate = _gid(True, "mechanism-candidate")
    rows = [
        _row(control, contamination=1),
        _row(candidate, failures=1, collisions=1),
    ]
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": control, "rating_delta": 0.0},
        {"slot": "conceder", "game_id": candidate, "rating_delta": 0.0},
    ])
    assert live_percentile.report_top_buyer_clone_hi_cap10(
        rows, 24.0, since=100.0, official_path=official) == 2
    output = capsys.readouterr().out
    assert "MECHANISM REJECTION" in output
    assert "candidate-wire/control/collision" in output


def test_harm_look_uses_20_per_arm_and_ten_point_no_deal_boundary(
        tmp_path, capsys):
    controls = _gids(False, 20, "harm-controls")
    candidates = _gids(True, 20, "harm-candidates")
    rows = [_row(gid) for gid in controls]
    rows.extend(_row(gid, no_deal=index < 2, closed=index >= 2)
                for index, gid in enumerate(candidates))
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": gid, "rating_delta": 0.0}
        for gid in controls + candidates
    ])
    assert live_percentile.report_top_buyer_clone_hi_cap10(
        rows, 24.0, since=100.0, official_path=official) == 2
    assert "no-deal rate is >=10pp worse" in capsys.readouterr().out


def test_fixed_final_passes_only_when_every_promotion_gate_passes(
        tmp_path, capsys):
    controls = _gids(False, 40, "final-controls")
    candidates = _gids(True, 40, "final-candidates")
    hosts = ("champion", "composite", "conceder", "randomized")
    own_types = (0.8, 1.0, 1.2, 1.5)
    scales = (100.0, 10_000.0, 1_000_000.0)
    rows = []
    official_rows = []
    for treatment, gids in ((False, controls), (True, candidates)):
        for index, gid in enumerate(gids):
            host = hosts[index % len(hosts)]
            rows.append(_row(
                gid,
                slot=host,
                pct=0.56 if treatment else 0.50,
                own_mult=own_types[index % len(own_types)],
                messages=bool(index % 2),
                scale=scales[index % len(scales)],
            ))
            official_rows.append({
                "slot": host,
                "game_id": gid,
                "rating_delta": 2.0 if treatment else 0.0,
            })
    official = _official(tmp_path, official_rows)
    assert live_percentile.report_top_buyer_clone_hi_cap10(
        rows, 24.0, since=100.0, official_path=official) == 0
    assert "PROMOTION GATE PASSED" in capsys.readouterr().out


def test_report_retains_unresolved_assignment_and_blocks(tmp_path, capsys):
    control = _gid(False, "unresolved-control")
    candidate = _gid(True, "unresolved-candidate")
    rows = [
        _row(control),
        _row(candidate, pct=None, closed=None, resolution="pending"),
    ]
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": control, "rating_delta": 0.0},
    ])
    assert live_percentile.report_top_buyer_clone_hi_cap10(
        rows, 24.0, since=100.0, official_path=official) == 1
    output = capsys.readouterr().out
    assert "assigned=1" in output
    assert "unresolved=1" in output
    assert "READ BLOCKED" in output


def test_report_and_cli_require_clean_t0(monkeypatch, capsys):
    assert live_percentile.report_top_buyer_clone_hi_cap10([], 24.0) == 2
    assert "CLEAN T0 REQUIRED" in capsys.readouterr().out

    monkeypatch.setattr(
        sys, "argv",
        ["live_percentile.py", "--ab", "top-buyer-clone-hi-cap10"],
    )
    with pytest.raises(SystemExit) as exc:
        live_percentile.main()
    assert exc.value.code == 2
