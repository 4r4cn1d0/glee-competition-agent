"""Recoverable ITT reporting for ``--ab pers-selectivity``."""

from __future__ import annotations

import json
import sys

import pytest

from glee_agent.strategies.persuasion import buyer_selectivity_assignment
from scripts import live_percentile


def _gid(candidate: bool, suffix: str = "") -> str:
    for index in range(10_000):
        gid = f"pers-selectivity-report-{suffix}-{index}"
        if buyer_selectivity_assignment(gid) is candidate:
            return gid
    raise AssertionError(f"could not find assignment bit {candidate}")


def _history(*, with_decline: bool = True):
    rows = [
        {"round": 1, "seller_message": "yes", "bought": True,
         "quality": "high"},
        {"round": 2, "seller_message": "yes", "bought": False},
    ]
    if with_decline:
        rows.append({"round": 3, "seller_message": "no", "bought": False})
    rows.append({"round": len(rows) + 1, "seller_message": "yes",
                 "bought": True, "quality": "low"})
    return rows


def _state(*, p=0.5, v=30.0, u=10.0, price=20.0, history=None):
    return {
        "phase": "buyer_decision",
        "current_player": "player_2",
        "product_price": price,
        "p": p,
        "v": v,
        "u": u,
        "round": len(history or []) + 1,
        "total_rounds": 20,
        "seller_message": "yes",
        "seller_message_type": "binary",
        "history": list(history or []),
    }


def _turn(gid, *, ts=9_500.0, seat="player_2", state=None):
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": seat,
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": state or _state(),
        "action": {"decision": "yes"},
    }


def _final(gid, *, payoff=-10.0, history=None, outcome="completed"):
    return {
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "status": "completed" if outcome == "completed" else "no_deal",
        "game_state": _state(history=history or []),
        "result": {
            "outcome": outcome,
            "player_1_payoff": 40.0,
            "player_2_payoff": payoff,
        },
    }


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _diagnostic(*, declines=0, payoff=10.0):
    return {
        "price": 20.0,
        "p": 0.5,
        "v": 30.0,
        "u": 10.0,
        "prior_value": 20.0,
        "seller_message_type": "binary",
        "total_rounds": 20,
        "payoff": payoff,
        "payoff_per_price": payoff / 20.0,
        "rounds": 4,
        "purchases": 2,
        "purchase_rate": 0.5,
        "pre_decline_buys": 2 if declines == 0 else 1,
        "bought_lows": 1,
        "bought_highs": 1,
        "decline_count": declines,
    }


def test_arm_recovery_uses_the_runtime_assignment_helper():
    for candidate in (False, True):
        gid = _gid(candidate)
        expected = "candidate" if candidate else "control"
        assert live_percentile.pers_selectivity_arm(gid) == expected
    assert live_percentile.pers_selectivity_arm(None) is None


def test_exposure_uses_general_u_and_production_break_even_tolerance():
    gid = _gid(True)
    exposure = live_percentile._pers_selectivity_exposure_turn(
        "champion", _turn(gid))

    assert exposure[:2] == (("champion", gid), 9_500.0)
    assert exposure[2]["prior_value"] == pytest.approx(20.0)
    assert exposure[2]["u"] == 10.0

    above = _turn(gid, state=_state(price=19.99))
    assert live_percentile._pers_selectivity_exposure_turn(
        "champion", above) is None
    within_guard_tolerance = _turn(gid, state=_state(price=20.0 - 1e-8))
    assert live_percentile._pers_selectivity_exposure_turn(
        "champion", within_guard_tolerance) is not None
    wrong_seat = _turn(gid, seat="player_1")
    assert live_percentile._pers_selectivity_exposure_turn(
        "champion", wrong_seat) is None
    wrong_action = _turn(gid)
    wrong_action["action_type"] = "seller_message"
    assert live_percentile._pers_selectivity_exposure_turn(
        "champion", wrong_action) is None


def test_terminal_row_reports_normalized_payoff_and_mechanisms(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.37)
    gid = _gid(False)

    row = live_percentile._pers_selectivity_row(
        "champion", {"game_id": gid},
        _final(gid, payoff=-10.0, history=_history(with_decline=True)),
    )

    assert row[:4] == ("champion", 0.37, gid, True)
    diagnostic = row[4]
    assert diagnostic["payoff_per_price"] == pytest.approx(-0.5)
    assert diagnostic["purchases"] == 2
    assert diagnostic["purchase_rate"] == pytest.approx(0.5)
    assert diagnostic["pre_decline_buys"] == 1
    assert diagnostic["bought_lows"] == 1
    assert diagnostic["bought_highs"] == 1
    assert diagnostic["decline_count"] == 1


def test_cohort_uses_first_eligible_decision_and_exact_window(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.42)
    before = _gid(False, "before")
    included = _gid(True, "included")
    at_until = _gid(False, "until")
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _turn(before, ts=8_999.0),
        _turn(before, ts=9_100.0),
        _turn(included, ts=9_000.0),
        _turn(at_until, ts=9_500.0),
    ])
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 9_800.0, "game_id": gid,
         "final": _final(gid, payoff=10.0, history=_history(with_decline=False))}
        for gid in (before, included, at_until)
    ])

    rows = list(live_percentile.pers_selectivity_games(
        24.0, since=9_000.0, until=9_500.0))

    assert len(rows) == 1
    assert rows[0][2] == included
    assert rows[0][4]["decline_count"] == 0
    assert rows[0][-1] == "terminal"


def test_report_is_itt_counts_pending_abandoned_and_excludes_duplicates(capsys):
    control = _gid(False, "report-control")
    candidate = _gid(True, "report-candidate")
    pending = _gid(True, "report-pending")
    abandoned = _gid(False, "report-abandoned")
    duplicated = _gid(True, "report-duplicate")
    duplicate_diagnostic = _diagnostic(declines=1)
    duplicate_diagnostic["fleet_slots"] = ("champion", "hardliner")

    assert live_percentile.report_pers_selectivity([
        ("champion", 0.40, control, True, _diagnostic(declines=1), "terminal"),
        # No decline: this remains in the candidate primary estimate.
        ("champion", 0.60, candidate, True, _diagnostic(declines=0), "terminal"),
        ("champion", None, pending, None, {"price": 20.0}, "pending"),
        ("champion", 0.05, abandoned, False, {"price": 20.0}, "abandoned"),
        ("champion", 0.99, duplicated, True, duplicate_diagnostic, "terminal"),
    ], 24.0) == 0

    output = capsys.readouterr().out
    pooled_candidate = next(
        line for line in output.splitlines()
        if line.startswith("POOLED") and "candidate" in line)
    assert "pct=0.6000" in pooled_candidate
    assert "terminal=1" in pooled_candidate and "pend=1" in pooled_candidate
    assert "not conditioned on an eventual decline" in output
    assert "abnd=1" in output
    assert "INCOMPLETE OUTCOMES: pending=1, invalid-final=0" in output
    assert "excluded 1 game id(s)" in output
    assert "pooled exactly-one-decline diagnostic" in output
    assert "descriptive/post-treatment" in output
    assert "pooled pre-treatment exact-cell diagnostics" in output
    assert "20 0.5 1.5 10 binary 20 equality" in output
    assert "FALSIFICATION WARNING" in output


def test_cli_routes_pers_selectivity(monkeypatch, capsys):
    monkeypatch.setattr(
        live_percentile, "pers_selectivity_games",
        lambda _hours, **_kwargs: iter(()),
    )
    monkeypatch.setattr(
        sys, "argv", ["live_percentile.py", "--ab", "pers-selectivity",
                      "--since", "9000", "--until", "9500"],
    )

    assert live_percentile.main() == 1
    output = capsys.readouterr().out
    assert "first eligible buyer-decision exposure window: [9000, 9500)" in output
    assert "no eligible persuasion buyer-decision exposures" in output
