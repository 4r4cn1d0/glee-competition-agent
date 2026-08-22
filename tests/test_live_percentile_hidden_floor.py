"""Arm recovery and outcome reporting for ``--ab hidden-floor``."""

from __future__ import annotations

import hashlib
import json
import sys

import pytest

from scripts import live_percentile


def _gids(treatment: bool, n: int = 2) -> list[str]:
    found = []
    for i in range(10000):
        gid = f"hidden-floor-report-{i}"
        bit = int(hashlib.sha256(("hidden_floor|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment:
            found.append(gid)
            if len(found) == n:
                return found
    raise AssertionError("could not find enough ids for the requested arm")


def _state(*, seat="player_1", complete=False, own_value=None,
           max_rounds=10):
    role = "seller" if seat == "player_1" else "buyer"
    if own_value is None:
        own_value = 80.0 if role == "seller" else 150.0
    state = {
        "round": 5,
        "complete_information": complete,
        "current_player": seat,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        f"{seat}_value": own_value,
        "history": [],
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
        state["horizon_known"] = True
    else:
        state["horizon_known"] = False
    if complete:
        other = "player_2" if seat == "player_1" else "player_1"
        state[f"{other}_value"] = 150.0 if role == "seller" else 80.0
    return state


def _final(gid, *, seat="player_1", complete=False, own_value=None,
           outcome="agreement", max_rounds=10, payoff=12.0):
    state = _state(
        seat=seat, complete=complete, own_value=own_value,
        max_rounds=max_rounds)
    return {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "status": "completed" if outcome == "agreement" else "no_deal",
        "game_state": state,
        "result": {
            "outcome": outcome,
            f"{seat}_payoff": payoff,
        },
    }


def _turn(gid, *, ts=9000.0, seat="player_1", complete=False,
          own_value=None, with_price=True):
    action = {"product_price": 110.0} if with_price else {"decision": "AcceptOffer"}
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "state": _state(seat=seat, complete=complete, own_value=own_value),
        "action": action,
    }


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_hidden_floor_arm_recovers_the_exact_runtime_hash():
    for treatment in (False, True):
        expected = "candidate" if treatment else "control"
        for gid in _gids(treatment, 20):
            assert live_percentile.hidden_floor_arm(gid) == expected
    assert live_percentile.hidden_floor_arm(None) is None


@pytest.mark.parametrize(
    ("seat", "max_rounds"),
    [("player_1", 1), ("player_1", None), ("player_2", 10)],
)
def test_hidden_floor_row_includes_both_seats_and_every_horizon(
        monkeypatch, seat, max_rounds):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.61)
    gid = _gids(True, 1)[0]

    row = live_percentile._hidden_floor_row(
        "champion", {"game_id": gid},
        _final(gid, seat=seat, max_rounds=max_rounds))

    assert row == ("champion", 0.61, gid, True)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda fin: fin["game_state"].update(complete_information=True),
        lambda fin: fin["game_state"].pop("complete_information"),
        lambda fin: fin["game_state"].pop("player_1_value"),
        lambda fin: fin["game_state"].update(player_1_value=83.0),
        lambda fin: fin["game_state"].update(player_1_role="observer"),
        lambda fin: fin.update(your_player="observer"),
        lambda fin: fin.update(game_family="bargaining"),
        lambda fin: fin.update(status="active", result={"outcome": "active"}),
    ],
    ids=("complete", "missing-marker", "missing-own-value", "off-grid",
         "bad-role", "bad-seat", "other-family", "active"),
)
def test_hidden_floor_row_excludes_ineligible_outcomes(monkeypatch, mutate):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.99)
    gid = _gids(True, 1)[0]
    fin = _final(gid)
    mutate(fin)

    assert live_percentile._hidden_floor_row(
        "champion", {"game_id": gid}, fin) is None


def test_hidden_floor_row_keeps_close_results_when_cdf_is_unknown(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: None)
    gid = _gids(False, 1)[0]

    row = live_percentile._hidden_floor_row(
        "champion", {"game_id": gid},
        _final(gid, outcome="no_deal", payoff=0.0))

    assert row == ("champion", None, gid, False)


def test_hidden_floor_exposure_requires_a_hidden_outgoing_price():
    gid = _gids(True, 1)[0]
    rec = _turn(gid, seat="player_2")
    assert live_percentile._hidden_floor_exposure_turn("champion", rec) == (
        ("champion", gid), 9000.0)

    assert live_percentile._hidden_floor_exposure_turn(
        "champion", _turn(gid, complete=True)) is None
    assert live_percentile._hidden_floor_exposure_turn(
        "champion", _turn(gid, own_value=83.0)) is None
    assert live_percentile._hidden_floor_exposure_turn(
        "champion", _turn(gid, with_price=False)) is None
    wrong_player = _turn(gid)
    wrong_player["state"]["current_player"] = "player_2"
    assert live_percentile._hidden_floor_exposure_turn(
        "champion", wrong_player) is None


def test_hidden_floor_cohort_uses_only_hidden_price_exposures(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.22)
    hidden_gid = _gids(True, 1)[0]
    complete_gid = "complete-price"
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _turn(hidden_gid, ts=9_500.0),
        _turn(complete_gid, ts=9_500.0, complete=True),
    ])
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 9_700.0, "game_id": hidden_gid,
         "final": _final(hidden_gid, outcome="no_deal", payoff=0.0)},
        {"ts": 9_700.0, "game_id": complete_gid,
         "final": _final(complete_gid, complete=True)},
    ])

    rows = list(live_percentile.hidden_floor_games(1.0))

    assert rows == [("champion", 0.22, hidden_gid, False, "terminal")]


def test_hidden_floor_cli_reports_percentile_and_close_rate_per_arm(
        monkeypatch, capsys):
    controls = _gids(False)
    candidates = _gids(True)
    rows = [
        ("champion", 0.20, controls[0], True),
        ("champion", 0.40, controls[1], True),
        ("champion", 0.70, candidates[0], True),
        ("champion", 0.90, candidates[1], False),
    ]
    monkeypatch.setattr(
        live_percentile, "hidden_floor_games", lambda _hours, **_kwargs: iter(rows))
    monkeypatch.setattr(sys, "argv", ["live_percentile.py", "--ab", "hidden-floor"])

    assert live_percentile.main() == 0

    output = capsys.readouterr().out
    pooled_control = next(line for line in output.splitlines()
                          if line.startswith("POOLED") and "control" in line)
    pooled_candidate = next(line for line in output.splitlines()
                            if line.startswith("POOLED") and "candidate" in line)
    assert "0.3000" in pooled_control and "100.0%" in pooled_control
    assert "0.8000" in pooled_candidate and "50.0%" in pooled_candidate
    assert "mean percentile +0.5000; close rate -50.0%" in output
    assert "CLOSE-RATE VETO" in output
    assert "complete_information=false" in output
    assert "supported own-value base" in output
    assert "at least one outgoing price" in output


def test_hidden_floor_report_uses_separate_score_and_close_denominators(capsys):
    control = _gids(False, 1)[0]
    candidate = _gids(True, 1)[0]

    live_percentile.report_hidden_floor([
        ("champion", 0.50, control, True),
        ("champion", 0.75, candidate, True),
        ("champion", None, candidate, False),
    ], 24.0)

    candidate_line = next(line for line in capsys.readouterr().out.splitlines()
                          if line.startswith("POOLED") and "candidate" in line)
    assert candidate_line.split() == [
        "POOLED", "candidate", "0.7500", "1", "50.0%", "2", "0", "0", "0"]


def test_hidden_floor_cli_returns_nonzero_without_exposures(monkeypatch, capsys):
    monkeypatch.setattr(
        live_percentile, "hidden_floor_games", lambda _hours, **_kwargs: iter(()))
    monkeypatch.setattr(sys, "argv", ["live_percentile.py", "--ab", "hidden-floor"])

    assert live_percentile.main() == 1
    assert "no eligible hidden-information price exposures" in capsys.readouterr().out
