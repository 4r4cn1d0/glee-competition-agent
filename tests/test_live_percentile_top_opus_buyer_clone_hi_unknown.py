"""Reader tests for the prospective hidden/unknown Opus trajectory arm."""

from __future__ import annotations

import json
import sys

import pytest

from glee_agent import top_opus_buyer_clone_hi_unknown as clone
from scripts import live_percentile


def _gid(treatment: bool, prefix="opus-hi-unknown-reader") -> str:
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


def _history(count: int) -> list[dict]:
    return [
        {
            "round": 2 * index + 2,
            "offer": {
                "price": 10.0 + index,
                "from_player": "player_2",
                "round": 2 * index + 2,
            },
            "decision": "RejectOffer",
            "decided_by": "player_1",
        }
        for index in range(count)
    ]


def _state(*, own=120.0, round_no=1, offer=149.0, messages=False,
           history=None, known=False, complete=False, max_rounds=None):
    state = {
        "round": round_no,
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
            "round": round_no,
        },
        "history": list(history or []),
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if complete:
        state["player_1_value"] = 80.0
    return state


def _record(gid, *, state=None, action_type="decision", action=None,
            source=None, ts=1234.0):
    state = dict(state or _state())
    if action_type == "offer":
        state.pop("last_offer", None)
    expected = None
    if clone.treatment_assignment(gid) is True:
        expected = live_percentile._top_opus_buyer_clone_hi_unknown_expected_action(
            gid, "player_2", state, action_type)
    if action is None:
        action = expected or {"decision": "RejectOffer", "product_price": 90.0}
    action = dict(action)
    action.pop("_plan", None)
    if source is None and expected is not None:
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


def _diagnostic(gid, *, slot="conceder", own_mult=1.2, scale=100.0,
                messages=False, ts=1234.0, supported=None, fires=None,
                fallbacks=0, source_turns=None, scope_failures=0,
                wire_failures=0, contamination=0, collisions=0,
                no_deal=False, walked=False, timeout=False):
    candidate = clone.treatment_assignment(gid) is True
    if supported is None:
        supported = int(candidate and not fallbacks)
    if fires is None:
        fires = supported
    if source_turns is None:
        source_turns = fires
    return {
        "own_mult": own_mult,
        "scale": scale,
        "base": scale,
        "messages_allowed": messages,
        "complete_information": False,
        "horizon": "inf",
        "fleet_slots": (slot,),
        "exposure_ts": ts,
        "eligible_turns": 1,
        "supported_action_turns": supported,
        "supported_fires": fires,
        "candidate_fallback_turns": fallbacks,
        "scoped_source_turns": source_turns,
        "scope_failures": scope_failures,
        "wire_failures": wire_failures,
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


def _official(tmp_path, records):
    path = tmp_path / "official.json"
    path.write_text(json.dumps({"games": records}), encoding="utf-8")
    return str(path)


def test_assignment_is_exact_fresh_production_assignment():
    for index in range(500):
        gid = f"opus-hi-unknown-parity-{index}"
        expected = "candidate" if clone.treatment_assignment(gid) else "control"
        assert live_percentile.top_opus_buyer_clone_hi_unknown_arm(gid) == expected
    assert live_percentile.top_opus_buyer_clone_hi_unknown_arm(None) is None


def test_first_eligible_decision_enrolls_before_support():
    candidate = _gid(True, "eligible")
    decision = live_percentile._top_opus_buyer_clone_hi_unknown_exposure_turn(
        "conceder", _record(candidate))
    assert decision[0] == ("conceder", candidate)
    assert decision[2]["first_supported_action"] is True
    assert decision[2]["first_wire_ok"] is True
    assert decision[2]["own_mult"] == 1.2
    assert decision[2]["scale"] == 100.0

    # The scoped production predicate is decision-only. An opening cannot be
    # admitted by a broader reader approximation.
    assert live_percentile._top_opus_buyer_clone_hi_unknown_exposure_turn(
        "conceder", _record(candidate, action_type="offer")) is None


def test_scope_rejects_known_complete_dead_type_and_present_cap():
    candidate = _gid(True, "scope")
    states = (
        _state(known=True, max_rounds=10),
        _state(complete=True),
        _state(own=80.0),
        {**_state(), "max_rounds": None},
        {"round": 1},
    )
    for state in states:
        assert live_percentile._top_opus_buyer_clone_hi_unknown_exposure_turn(
            "conceder", _record(candidate, state=state)) is None


def test_supported_message_wire_and_unsupported_fallback_contract():
    supported = _gid(True, "message")
    state = _state(own=1_200_000.0, offer=1_400_000.0, messages=True)
    expected = live_percentile._top_opus_buyer_clone_hi_unknown_expected_action(
        supported, "player_2", state, "decision")
    assert expected["message"] == (
        "812,000 is what this is worth to me. "
        "Above that the purchase stops making sense."
    )

    fallback = _gid(True, "fallback")
    late = _state(round_no=87, history=_history(43))
    exposure = live_percentile._top_opus_buyer_clone_hi_unknown_exposure_turn(
        "conceder",
        _record(fallback, state=late, source="ordinary_control"),
    )
    assert exposure is not None
    assert exposure[2]["first_supported_action"] is False
    assert exposure[2]["first_candidate_fallback"] is True
    assert exposure[2]["first_wire_ok"] is True

    leaked = live_percentile._top_opus_buyer_clone_hi_unknown_exposure_turn(
        "conceder", _record(fallback, state=late, source=clone.PLAN_SOURCE))
    assert leaked is not None
    assert leaked[2]["first_wire_ok"] is False


def test_trace_audits_supported_fallback_control_and_scope(
        monkeypatch, tmp_path):
    candidate = _gid(True, "trace-candidate")
    control = _gid(False, "trace-control")
    collision = _gid(True, "trace-collision")
    late = _state(round_no=87, history=_history(43))
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    records = [
        _record(candidate, ts=100.0),
        _record(candidate, state=late, source="ordinary_control", ts=101.0),
        _record(candidate, action={"decision": "RejectOffer",
                                   "product_price": 81.21}, ts=102.0),
        _record(control, source=clone.PLAN_SOURCE, ts=103.0),
        _record(collision, source="top_opus_buyer_clone", ts=104.0),
        _record(candidate, state=_state(known=True, max_rounds=10),
                source=clone.PLAN_SOURCE, ts=105.0),
    ]
    (log_dir / "turns.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))

    audited = live_percentile._top_opus_buyer_clone_hi_unknown_trace_audit([
        _row(candidate), _row(control), _row(collision),
    ])
    by_gid = {row[2]: row[4] for row in audited}
    assert by_gid[candidate]["eligible_turns"] == 3
    assert by_gid[candidate]["supported_action_turns"] == 2
    assert by_gid[candidate]["supported_fires"] == 1
    assert by_gid[candidate]["candidate_fallback_turns"] == 1
    assert by_gid[candidate]["wire_failures"] == 1
    assert by_gid[candidate]["scope_failures"] == 1
    assert by_gid[control]["control_contamination"] == 1
    assert by_gid[collision]["collision_turns"] == 1
    assert by_gid[collision]["scope_failures"] == 1


@pytest.mark.parametrize(
    ("status", "outcome", "field"),
    [
        ("no_deal", "no_deal", "no_deal"),
        ("completed", "walked_away", "walked_away"),
        ("timeout", "timeout", "timeout"),
    ],
)
def test_terminal_row_retains_all_nonclose_outcomes(
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
    row = live_percentile._top_opus_buyer_clone_hi_unknown_row(
        "conceder", {"game_id": gid}, final)
    assert row[:4] == ("conceder", 0.17, gid, False)
    assert row[4][field] is True


def test_games_reader_retains_unresolved_fallback_assignment(monkeypatch, tmp_path):
    gid = _gid(True, "pending-fallback")
    state = _state(round_no=87, history=_history(43))
    log_dir = tmp_path / "logs" / "conceder"
    log_dir.mkdir(parents=True)
    (log_dir / "turns.jsonl").write_text(
        json.dumps(_record(gid, state=state, source="ordinary_control",
                           ts=150.0)) + "\n",
        encoding="utf-8")
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 151.0)

    rows = list(live_percentile.top_opus_buyer_clone_hi_unknown_games(
        24.0, since=100.0, until=200.0))
    assert len(rows) == 1
    assert rows[0][2] == gid
    assert rows[0][3] is None
    assert rows[0][-1] == "pending"
    assert rows[0][4]["candidate_fallback_turns"] == 1
    assert rows[0][4]["wire_failures"] == 0


def test_report_prints_official_itt_and_all_strata(tmp_path, capsys):
    controls = [_gid(False, f"report-control-{index}") for index in range(2)]
    candidates = [_gid(True, f"report-candidate-{index}") for index in range(2)]
    rows = [
        _row(controls[0], slot="conceder"),
        _row(candidates[0], slot="conceder"),
        _row(controls[1], slot="champion", own_mult=1.5,
             scale=10_000.0, messages=True, closed=False, no_deal=True),
        _row(candidates[1], slot="champion", own_mult=1.5,
             scale=10_000.0, messages=True, closed=False, walked=True),
    ]
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": controls[0], "rating_delta": 0.0},
        {"slot": "champion", "game_id": controls[1], "rating_delta": 0.0},
        {"slot": "conceder", "game_id": candidates[0], "rating_delta": 2.0},
        {"slot": "champion", "game_id": candidates[1], "rating_delta": 2.0},
    ])
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        rows, 24.0, since=100.0, official_path=official) == 1
    output = capsys.readouterr().out
    assert "official rating delta: +2.0000" in output
    assert "host=conceder" in output
    assert "own_mult=1.5" in output
    assert "messages_allowed=True" in output
    assert "scale=10000.0" in output
    assert "COLLECT MORE" in output


def test_frozen_harm_look_uses_only_first_twenty_per_arm(tmp_path, capsys):
    controls = _gids(False, 20, "frozen-harm-control")
    candidates = _gids(True, 21, "frozen-harm-candidate")
    rows = [
        *[_row(gid, ts=1000.0 + index) for index, gid in enumerate(controls)],
        *[_row(gid, ts=2000.0 + index) for index, gid in enumerate(candidates)],
    ]
    official = _official(tmp_path, [
        *[{"slot": "conceder", "game_id": gid, "rating_delta": 0.0}
          for gid in controls],
        *[{"slot": "conceder", "game_id": gid,
           "rating_delta": 1.0 if index < 20 else -100.0}
          for index, gid in enumerate(candidates)],
    ])
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        rows, 24.0, since=100.0, official_path=official) == 1
    output = capsys.readouterr().out
    assert "frozen harm look: first 20" in output
    assert "HARM REJECTION" not in output
    assert "COLLECT MORE" in output


def test_frozen_harm_look_rejects_wholly_negative_official_ci(tmp_path, capsys):
    controls = _gids(False, 20, "harm-control")
    candidates = _gids(True, 20, "harm-candidate")
    rows = [_row(gid) for gid in controls + candidates]
    official = _official(tmp_path, [
        *[{"slot": "conceder", "game_id": gid, "rating_delta": 0.0}
          for gid in controls],
        *[{"slot": "conceder", "game_id": gid, "rating_delta": -2.0}
          for gid in candidates],
    ])
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        rows, 24.0, since=100.0, official_path=official) == 2
    assert "HARM REJECTION" in capsys.readouterr().out


def _fixed_final(tmp_path, *, candidate_type_1_score=2.0,
                 candidate_no_deals=0, candidate_pct=0.56):
    controls = _gids(False, 40, "final-controls")
    candidates = _gids(True, 40, "final-candidates")
    hosts = ("champion", "composite", "conceder", "randomized")
    own_types = (1.0, 1.2, 1.5)
    scales = (100.0, 10_000.0, 1_000_000.0)
    rows = []
    official_rows = []
    for treatment, gids in ((False, controls), (True, candidates)):
        for index, gid in enumerate(gids):
            host = hosts[index % len(hosts)]
            own_mult = own_types[index % len(own_types)]
            # Keep any final-only no-deal test outside the frozen first-20
            # harm look so it exercises the separate +5pp promotion boundary.
            no_deal = (treatment and candidate_no_deals
                       and index >= 40 - candidate_no_deals)
            rows.append(_row(
                gid,
                slot=host,
                pct=candidate_pct if treatment else 0.50,
                closed=not no_deal,
                no_deal=no_deal,
                own_mult=own_mult,
                messages=bool(index % 2),
                scale=scales[index % len(scales)],
                ts=(2000.0 if treatment else 1000.0) + index,
            ))
            score = 0.0
            if treatment:
                score = (candidate_type_1_score
                         if own_mult == 1.0 else 2.0)
            official_rows.append({
                "slot": host,
                "game_id": gid,
                "rating_delta": score,
            })
    return rows, _official(tmp_path, official_rows)


def test_fixed_final_passes_every_precommitted_gate(tmp_path, capsys):
    rows, official = _fixed_final(tmp_path)
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        rows, 24.0, since=100.0, official_path=official) == 0
    output = capsys.readouterr().out
    assert "PROMOTION GATE PASSED" in output


def test_fixed_final_rejects_negative_own_type_point(tmp_path, capsys):
    rows, official = _fixed_final(tmp_path, candidate_type_1_score=-0.1)
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        rows, 24.0, since=100.0, official_path=official) == 2
    output = capsys.readouterr().out
    assert "FINAL REJECTION" in output
    assert "own_mult=1.0" in output


def test_fixed_final_rejects_more_than_five_point_no_deal_harm(tmp_path, capsys):
    rows, official = _fixed_final(tmp_path, candidate_no_deals=3)
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        rows, 24.0, since=100.0, official_path=official) == 2
    assert "FINAL REJECTION" in capsys.readouterr().out


def test_report_rejects_mechanism_and_blocks_unresolved_join(tmp_path, capsys):
    control = _gid(False, "failure-control")
    candidate = _gid(True, "failure-candidate")
    official = _official(tmp_path, [
        {"slot": "conceder", "game_id": control, "rating_delta": 0.0},
        {"slot": "conceder", "game_id": candidate, "rating_delta": 0.0},
    ])
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        [_row(control), _row(candidate, wire_failures=1)],
        24.0, since=100.0, official_path=official) == 2
    assert "MECHANISM REJECTION" in capsys.readouterr().out

    assert live_percentile.report_top_opus_buyer_clone_hi_unknown(
        [_row(control),
         _row(candidate, pct=None, closed=None, resolution="pending")],
        24.0, since=100.0, official_path=official) == 1
    output = capsys.readouterr().out
    assert "unresolved=1" in output
    assert "READ BLOCKED" in output


def test_report_and_cli_require_clean_t0(monkeypatch, capsys):
    assert live_percentile.report_top_opus_buyer_clone_hi_unknown([], 24.0) == 2
    assert "CLEAN T0 REQUIRED" in capsys.readouterr().out
    monkeypatch.setattr(
        sys, "argv",
        ["live_percentile.py", "--ab",
         "top-opus-buyer-clone-hi-unknown"],
    )
    with pytest.raises(SystemExit) as exc:
        live_percentile.main()
    assert exc.value.code == 2
