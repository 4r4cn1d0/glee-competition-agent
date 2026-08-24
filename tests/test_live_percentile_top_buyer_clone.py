"""Official-score and all-turn audit for the observed-leader buyer clone."""

from __future__ import annotations

import json

from glee_agent import top_buyer_clone
from scripts import live_percentile


def _gid(treatment: bool, prefix="top-reader") -> str:
    for index in range(10000):
        gid = f"{prefix}-{index}"
        if top_buyer_clone.treatment_assignment(gid) is treatment:
            return gid
    raise AssertionError("no id for requested arm")


def _state(*, history=None, offer=149.0, messages=False):
    return {
        "round": 1 + 2 * len(history or []),
        "max_rounds": 10,
        "horizon_known": True,
        "complete_information": True,
        "messages_allowed": messages,
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": 120.0,
        "player_2_value": 150.0,
        "last_offer": {"price": offer, "from_player": "player_1", "round": 1},
        "history": list(history or []),
    }


def _record(gid, *, action=None, source="top_buyer_clone", ts=1234.0):
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "action_type": "decision",
        "state": _state(),
        "plan": {"source": source} if source else {},
        "action": action or {
            "decision": "RejectOffer", "product_price": 121.2},
    }


def _row(gid, *, rating_pct=0.5, closed=False, ts=1234.0, failures=0):
    return (
        "conceder", rating_pct, gid, closed,
        {
            "own_mult": 1.5,
            "complete_information": True,
            "horizon": "10",
            "fleet_slots": ("conceder",),
            "exposure_ts": ts,
            "buyer_turns": 1,
            "clone_source_turns": int(
                top_buyer_clone.treatment_assignment(gid) is True),
            "wire_failures": failures,
            "control_contamination": 0,
        },
        "terminal",
    )


def test_reader_assignment_is_production_assignment():
    for index in range(500):
        gid = f"clone-reader-parity-{index}"
        expected = ("candidate" if top_buyer_clone.treatment_assignment(gid)
                    else "control")
        assert live_percentile.top_buyer_clone_arm(gid) == expected


def test_exposure_is_pre_action_and_verifies_first_candidate_wire():
    gid = _gid(True)
    exposure = live_percentile._top_buyer_clone_exposure_turn(
        "conceder", _record(gid))
    assert exposure[0] == ("conceder", gid)
    assert exposure[1] == 1234.0
    assert exposure[2]["first_wire_ok"] is True
    assert exposure[2]["first_source"] == "top_buyer_clone"


def test_exposure_rejects_wrong_candidate_wire_without_selecting_it_out():
    gid = _gid(True)
    exposure = live_percentile._top_buyer_clone_exposure_turn(
        "conceder", _record(
            gid, action={"decision": "RejectOffer", "product_price": 121.21}))
    assert exposure is not None
    assert exposure[2]["first_wire_ok"] is False


def test_wire_audit_includes_the_exact_leader_message():
    gid = _gid(True, "message-wire")
    state = _state(messages=True)
    expected = live_percentile._top_clone_expected_action(
        gid, "player_2", state, "decision")
    assert expected["message"] == top_buyer_clone.BUYER_COUNTER_MESSAGE
    assert live_percentile._top_clone_wire_matches(
        {"decision": "RejectOffer", "product_price": 121.2,
         "message": top_buyer_clone.BUYER_COUNTER_MESSAGE}, expected)
    assert not live_percentile._top_clone_wire_matches(
        {"decision": "RejectOffer", "product_price": 121.2,
         "message": "different"}, expected)


def test_trace_audit_checks_every_candidate_turn_and_control_source(
        monkeypatch, tmp_path):
    candidate, control = _gid(True), _gid(False)
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    records = [
        _record(candidate),
        _record(candidate, action={"decision": "RejectOffer",
                                   "product_price": 121.21}, ts=1235.0),
        _record(control, action={"decision": "RejectOffer",
                                 "product_price": 131.7},
                source="top_buyer_clone", ts=1236.0),
    ]
    (log_dir / "turns.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    rows = [
        _row(candidate),
        _row(control),
    ]
    audited = list(live_percentile._top_buyer_clone_trace_audit(rows))
    by_gid = {row[2]: row[4] for row in audited}
    assert by_gid[candidate]["buyer_turns"] == 2
    assert by_gid[candidate]["wire_failures"] == 1
    assert by_gid[control]["control_contamination"] == 1


def test_outcome_row_keeps_no_deal_and_same_cell_percentile(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.61)
    gid = _gid(True)
    final = {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "status": "no_deal",
        "game_state": _state(),
        "result": {"outcome": "no_deal", "player_1_payoff": 0.0,
                   "player_2_payoff": 0.0},
    }
    row = live_percentile._top_buyer_clone_row(
        "conceder", {"game_id": gid}, final)
    assert row[:4] == ("conceder", 0.61, gid, False)
    assert row[4]["no_deal"] is True


def test_report_rejects_any_wire_failure(capsys):
    candidate, control = _gid(True), _gid(False)
    rows = [_row(control), _row(candidate, failures=1)]
    assert live_percentile.report_top_buyer_clone(rows, 24.0) == 2
    assert "MECHANISM REJECTION" in capsys.readouterr().out


def test_report_rejects_three_consecutive_severe_candidate_losses(
        tmp_path, capsys):
    candidates = [_gid(True, f"severe-{i}") for i in range(3)]
    control = _gid(False, "severe-control")
    rows = [_row(control, ts=1200.0)] + [
        _row(gid, ts=1300.0 + index)
        for index, gid in enumerate(candidates)
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps({"games": [
        {"slot": "conceder", "game_id": control, "rating_delta": 0.0},
        *[
            {"slot": "conceder", "game_id": gid, "rating_delta": -6.0}
            for gid in candidates
        ],
    ]}), encoding="utf-8")
    assert live_percentile.report_top_buyer_clone(
        rows, 24.0, official_path=str(official)) == 2
    assert "three consecutive" in capsys.readouterr().out


def test_report_applies_ten_per_arm_rating_harm_boundary(tmp_path, capsys):
    controls = [_gid(False, f"harm-c-{i}") for i in range(10)]
    candidates = [_gid(True, f"harm-t-{i}") for i in range(10)]
    rows = [
        *[_row(gid, ts=1000.0 + i) for i, gid in enumerate(controls)],
        *[_row(gid, ts=2000.0 + i) for i, gid in enumerate(candidates)],
    ]
    official_records = [
        *[{"slot": "conceder", "game_id": gid, "rating_delta": 0.0}
          for gid in controls],
        *[{"slot": "conceder", "game_id": gid, "rating_delta": -2.0}
          for gid in candidates],
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps({"games": official_records}),
                        encoding="utf-8")
    assert live_percentile.report_top_buyer_clone(
        rows, 24.0, official_path=str(official)) == 2
    assert "<= -1 rating/game" in capsys.readouterr().out
