"""Arm recovery and outcome reporting for --ab open-claim."""

from __future__ import annotations

import hashlib
import json
import sys

import pytest

from scripts import live_percentile


def _gids(treatment: bool, n: int = 2) -> list[str]:
    found = []
    for i in range(10_000):
        gid = f"ci-report-{i}"
        bit = int(hashlib.sha256(("open_claim|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment:
            found.append(gid)
            if len(found) == n:
                return found
    raise AssertionError("could not find enough open claim hash arms")


def _final(*, gid="eligible", max_rounds=10, complete=True,
           seat="player_1", include_both_values=True, opener="player_1",
           payoff=0.2, outcome="agreement"):
    state = {
        "complete_information": complete,
        "horizon_known": max_rounds is not None,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "history": [],
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if include_both_values:
        state.update(player_1_value=80.0, player_2_value=150.0)
    else:
        state["player_1_value"] = 80.0
    if opener is not None:
        state["history"] = [{
            "round": 1,
            "offer": {"from_player": opener, "price": 120.0, "round": 1},
            "decision": "AcceptOffer" if outcome == "agreement" else "RejectOffer",
        }]
    return {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "status": "completed" if outcome == "agreement" else "no_deal",
        "game_state": state,
        "result": {f"{seat}_payoff": payoff, "outcome": outcome},
    }


def _price_turn(gid, ts, *, max_rounds=10, seat="player_1", rnd=1,
                action_type=None):
    fin = _final(gid=gid, max_rounds=max_rounds, seat=seat, opener=None)
    state = dict(fin["game_state"])
    other = "player_2" if seat == "player_1" else "player_1"
    action_type = action_type or ("offer" if seat == "player_1" else "decision")
    last_offer = None
    if action_type == "decision":
        last_offer = {"from_player": other, "price": 120.0, "round": rnd}
    state.update(round=rnd, current_player=seat, last_offer=last_offer)
    action = {"product_price": 120.0}
    if action_type == "decision":
        action["decision"] = "RejectOffer"
    return {
        "ts": ts,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "round": rnd,
        "action_type": action_type,
        "state": state,
        "action": action,
    }


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records),
                    encoding="utf-8")


def test_arm_recovery_matches_the_required_sha256_bit():
    for treatment in (False, True):
        expected = "candidate" if treatment else "control"
        for gid in _gids(treatment, 20):
            assert live_percentile.open_claim_arm(gid) == expected
            assert live_percentile.open_claim_arm(gid) == expected
    assert live_percentile.open_claim_arm(None) is None


@pytest.mark.parametrize("seat", ("player_1", "player_2"))
@pytest.mark.parametrize("max_rounds", (1, 10, None))
def test_open_claim_row_includes_both_seats_and_every_horizon(
        monkeypatch, seat, max_rounds):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.61)
    fin = _final(max_rounds=max_rounds, seat=seat)

    row = live_percentile._open_claim_row(
        "champion", {"game_id": fin["game_id"]}, fin)

    assert row == ("champion", 0.61, "eligible", True)


def test_open_claim_row_keeps_timeout_without_closed_history(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.12)
    fin = _final(gid="price-timeout", outcome="no_deal", opener=None, payoff=0.0)
    # The standalone seller opening was transmitted, but the opponent timed out
    # before a round entry was closed.  last_offer is the only surviving evidence.
    fin["game_state"]["last_offer"] = {
        "from_player": "player_1", "price": 130.0, "round": 1,
    }

    row = live_percentile._open_claim_row(
        "champion", {"game_id": fin["game_id"]}, fin)

    assert row == ("champion", 0.12, "price-timeout", False)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda f: f["game_state"].update(complete_information=False),
        lambda f: f["game_state"].pop("player_2_value"),
        lambda f: f["game_state"].update(player_2_value=70.0),
        lambda f: f["game_state"].update(player_1_role="buyer"),
        lambda f: f.update(your_player="player_3"),
        lambda f: f["result"].update(outcome="active"),
        lambda f: f.update(game_family="bargaining"),
    ],
    ids=("hidden", "missing-value", "no-zopa", "bad-role-pair",
         "bad-seat", "active", "other-family"),
)
def test_open_claim_row_excludes_every_ineligible_population(monkeypatch, mutate):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.99)
    fin = _final()
    mutate(fin)

    assert live_percentile._open_claim_row(
        "champion", {"game_id": fin["game_id"]}, fin) is None


def test_unknown_cdf_still_counts_in_close_rate(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: None)
    fin = _final(gid="unknown-cdf", outcome="no_deal", payoff=0.0)

    row = live_percentile._open_claim_row(
        "champion", {"game_id": fin["game_id"]}, fin)

    assert row == ("champion", None, "unknown-cdf", False)


def test_timeout_is_a_terminal_non_close(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.05)
    fin = _final(gid="timed-out", outcome="no_deal", payoff=0.0)
    fin.update(status="no_deal")
    fin["result"]["outcome"] = "timeout"

    assert live_percentile._open_claim_row(
        "champion", {"game_id": fin["game_id"]}, fin
    ) == ("champion", 0.05, "timed-out", False)


def test_status_only_no_deal_is_terminal_but_unknown_outcome_is_pending():
    status_only = _final(gid="status-only", outcome="no_deal", payoff=0.0)
    status_only["result"].pop("outcome")
    status_only["status"] = "no_deal"
    unknown = _final(gid="unknown-terminal-label")
    unknown["result"]["outcome"] = "mystery"

    assert live_percentile._terminal_close(status_only) is False
    assert live_percentile._terminal_close(unknown) is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["state"].update(complete_information=False),
        lambda r: r["state"].pop("player_2_value"),
        lambda r: r["state"].update(player_2_value=70.0),
        lambda r: r["state"].update(
            player_1_role="seller", player_2_role="seller"),
        lambda r: r["action"].pop("product_price"),
        lambda r: r["state"].update(current_player="player_2"),
        lambda r: r.update(game_family="bargaining"),
    ],
    ids=("hidden", "missing-value", "no-zopa", "bad-role-pair", "no-price",
         "wrong-current-player", "other-family"),
)
def test_exposure_cohort_excludes_ineligible_turns(mutate):
    rec = _price_turn("not-eligible", 9_000.0)
    mutate(rec)

    assert live_percentile._open_claim_exposure_turn("champion", rec) is None


@pytest.mark.parametrize(
    "rec",
    [
        _price_turn("horizon-one", 9_000.0, max_rounds=1),
        _price_turn("buyer-first-counter", 9_001.0, seat="player_2"),
        _price_turn("later-counter", 9_002.0, rnd=7, action_type="decision"),
    ],
    ids=("horizon-one", "buyer", "later-round"),
)
def test_exposure_cohort_includes_both_seats_rounds_and_horizons(rec):
    assert live_percentile._open_claim_exposure_turn("champion", rec) == (
        ("champion", rec["game_id"]), rec["ts"])


def test_terminal_final_outranks_a_newer_active_snapshot():
    key = ("champion", "prefer-terminal")
    terminal = _final(gid=key[1], outcome="no_deal")
    active = _final(gid=key[1])
    active.update(status="active")
    active["result"]["outcome"] = "active"
    latest = {}

    live_percentile._prefer_final(
        latest, key, 100.0, {"game_id": key[1]}, terminal)
    live_percentile._prefer_final(
        latest, key, 200.0, {"game_id": key[1]}, active)

    assert latest[key][2] is terminal


def test_open_claim_cohort_uses_first_price_not_result_collection_time(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.63)
    current, old = "current-exposure", "old-exposure"
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _price_turn(current, 7_000.0),
        _price_turn(old, 5_000.0),
    ])
    # The in-window price was fetched before the nominal window; the old price
    # was fetched inside it. Only exposure time may define the cohort.
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 5_100.0, "game_id": current,
         "final": _final(gid=current)},
        {"ts": 9_900.0, "game_id": old, "final": _final(gid=old)},
    ])

    rows = list(live_percentile.open_claim_games(1.0))

    assert rows == [("champion", 0.63, current, True, "terminal")]


def test_open_claim_cohort_joins_collector_files_and_keeps_missing_outcomes(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.22)
    collected, missing = "collector-only", "missing-final"
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _price_turn(collected, 9_000.0),
        _price_turn(missing, 9_100.0),
    ])
    game = _final(gid=collected, outcome="no_deal", payoff=0.0)
    record = {
        "game_id": collected,
        "game_family": game["game_family"],
        "your_player": game["your_player"],
        "status": game["status"],
        "config": {k: v for k, v in game["game_state"].items()
                   if k != "history"},
        "result": game["result"],
        "history": game["game_state"]["history"],
    }
    game_path = tmp_path / f"logs/champion/games/{collected}.json"
    game_path.parent.mkdir(parents=True, exist_ok=True)
    game_path.write_text(json.dumps(record), encoding="utf-8")

    rows = list(live_percentile.open_claim_games(1.0))

    assert ("champion", 0.22, collected, False, "terminal") in rows
    assert ("champion", None, missing, None, "pending") in rows


def test_open_claim_cohort_supports_a_bounded_post_disarm_window(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.60)
    armed, after_disarm = "armed", "after-disarm"
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _price_turn(armed, 7_000.0),
        _price_turn(after_disarm, 8_000.0),
    ])
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 9_000.0, "game_id": armed, "final": _final(gid=armed)},
        {"ts": 9_100.0, "game_id": after_disarm,
         "final": _final(gid=after_disarm)},
    ])

    rows = list(live_percentile.open_claim_games(
        24.0, since=6_500.0, until=7_500.0))

    assert rows == [("champion", 0.60, armed, True, "terminal")]


def test_later_counter_cannot_pull_a_pre_window_game_into_the_cohort(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    gid = "first-price-predates-arm"
    first = _price_turn(gid, 6_000.0)
    later = _price_turn(gid, 7_000.0, rnd=5, action_type="decision")
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [first, later])
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 9_000.0, "game_id": gid, "final": _final(gid=gid)},
    ])

    rows = list(live_percentile.open_claim_games(
        24.0, since=6_500.0, until=7_500.0))

    assert rows == []


def test_cold_missing_outcome_counts_as_abandonment(monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 20_000.0)
    gid = "cold-missing"
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [
        _price_turn(gid, 7_000.0),
    ])
    # A later collection watermark plus the calibrated 6000-second cold gap
    # makes the absent result a scored abandonment, not an innocent pending game.
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [
        {"ts": 15_000.0, "game_id": "unrelated", "final": {}},
    ])

    rows = list(live_percentile.open_claim_games(
        24.0, since=6_500.0, until=7_500.0))

    assert rows == [("champion", 0.05, gid, False, "abandoned")]


def test_open_claim_cli_reports_percentile_and_close_rate_per_arm(
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
        live_percentile, "open_claim_games", lambda _hours, **_kwargs: iter(rows))
    monkeypatch.setattr(sys, "argv", ["live_percentile.py", "--ab", "open-claim"])

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
    assert "complete_information=true" in output
    assert "either seat/horizon" in output
    assert "at least one outgoing price" in output
    assert "scope --hours/--slots to an era" in output


def test_report_uses_separate_percentile_and_close_denominators(capsys):
    control = _gids(False, 1)[0]
    candidate = _gids(True, 1)[0]

    live_percentile.report_open_claim([
        ("champion", 0.50, control, True),
        ("champion", 0.75, candidate, True),
        ("champion", None, candidate, False),
    ], 40.0)

    candidate_line = next(line for line in capsys.readouterr().out.splitlines()
                          if line.startswith("POOLED") and "candidate" in line)
    fields = candidate_line.split()
    assert fields == [
        "POOLED", "candidate", "0.7500", "1", "50.0%", "2", "0", "0", "0"]


def test_pending_outcomes_are_reported_and_block_promotion(capsys):
    control = _gids(False, 1)[0]
    candidate = _gids(True, 1)[0]

    live_percentile.report_open_claim([
        ("champion", 0.50, control, True),
        ("champion", None, candidate, None),
    ], 40.0)

    output = capsys.readouterr().out
    candidate_line = next(line for line in output.splitlines()
                          if line.startswith("POOLED") and "candidate" in line)
    assert candidate_line.split() == [
        "POOLED", "candidate", "n/a", "0", "n/a", "0", "0", "1", "0"]
    assert "INCOMPLETE OUTCOMES: pending=1, invalid-final=0" in output
    assert "not promotion-grade" in output


def test_open_claim_cli_returns_nonzero_when_the_window_has_no_exposures(
        monkeypatch, capsys):
    monkeypatch.setattr(
        live_percentile, "open_claim_games", lambda _hours, **_kwargs: iter(()))
    monkeypatch.setattr(sys, "argv", ["live_percentile.py", "--ab", "open-claim"])

    assert live_percentile.main() == 1
    assert "no eligible complete-information price exposures" in capsys.readouterr().out
