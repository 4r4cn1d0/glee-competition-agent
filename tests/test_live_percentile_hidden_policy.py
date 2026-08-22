"""Arm recovery and zone-share reporting for ``--ab hidden-policy``."""

from __future__ import annotations

import hashlib
import json
import sys

import pytest

from glee_agent import actions, runtime_flags
from scripts import check_reachability, live_percentile


def _gids(treatment: bool, n: int = 2) -> list[str]:
    found = []
    for i in range(10_000):
        gid = f"hidden-policy-report-{i}"
        bit = int(hashlib.sha256(
            ("hidden_policy_v1|" + gid).encode()).hexdigest(), 16) & 1
        if bool(bit) is treatment:
            found.append(gid)
            if len(found) == n:
                return found
    raise AssertionError("could not find enough ids for the requested arm")


def _state(*, seat="player_1", own_value=None, max_rounds=10,
           complete=False):
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
        "horizon_known": max_rounds is not None,
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    if complete:
        other = "player_2" if seat == "player_1" else "player_1"
        state[f"{other}_value"] = 150.0 if role == "seller" else 80.0
    return state


def _final(gid, *, seat="player_1", own_value=None, max_rounds=10,
           outcome="agreement", payoffs=(30.0, 10.0)):
    return {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "status": "completed" if outcome == "agreement" else "no_deal",
        "game_state": _state(
            seat=seat, own_value=own_value, max_rounds=max_rounds),
        "result": {
            "outcome": outcome,
            "player_1_payoff": payoffs[0],
            "player_2_payoff": payoffs[1],
        },
    }


def _diagnostic(*, role="seller", own_mult=0.8, p_zopa=0.75,
                horizon="10", share=None, capture=0.0, pair=None,
                missing=False):
    return {
        "role": role,
        "own_mult": own_mult,
        "p_zopa": p_zopa,
        "horizon": horizon,
        "zone_share": share,
        "realized_capture": capture,
        "pair": pair,
        "reconstruction_missing": missing,
    }


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_hidden_policy_arm_recovers_exact_runtime_hash(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_POLICY_V1", "1")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    for treatment in (False, True):
        expected = "candidate" if treatment else "control"
        for gid in _gids(treatment, 20):
            assert live_percentile.hidden_policy_arm(gid) == expected
            game = {
                "game_id": gid,
                "your_player": "player_1",
                "game_state": _state(),
            }
            context = actions._hidden_policy_context(game)
            assert context is not None
            assert context["treatment"] is treatment
    assert live_percentile.hidden_policy_arm(None) is None


@pytest.mark.parametrize(
    ("seat", "own_value", "expected"),
    [
        ("player_1", 80.0, ("seller", 0.8, 0.75)),
        ("player_1", 100.0, ("seller", 1.0, 0.50)),
        ("player_1", 120.0, ("seller", 1.2, 0.25)),
        ("player_2", 100.0, ("buyer", 1.0, 0.25)),
        ("player_2", 120.0, ("buyer", 1.2, 0.50)),
        ("player_2", 150.0, ("buyer", 1.5, 0.75)),
    ],
)
def test_signal_reports_role_type_and_feasibility(seat, own_value, expected):
    signal = live_percentile._hidden_policy_signal(
        seat, _state(seat=seat, own_value=own_value))

    assert (signal["role"], signal["own_mult"], signal["p_zopa"]) == expected


@pytest.mark.parametrize(
    ("seat", "own_value", "max_rounds", "complete"),
    [
        ("player_1", 150.0, 10, False),
        ("player_2", 80.0, 10, False),
        ("player_1", 80.0, 1, False),
        ("player_1", 83.0, 10, False),
        ("player_1", 80.0, 10, True),
    ],
)
def test_signal_excludes_dead_one_round_off_grid_and_complete_games(
        seat, own_value, max_rounds, complete):
    assert live_percentile._hidden_policy_signal(
        seat, _state(seat=seat, own_value=own_value,
                     max_rounds=max_rounds, complete=complete)) is None


def test_hidden_policy_exposure_requires_eligible_outgoing_price():
    gid = _gids(True, 1)[0]
    rec = {
        "ts": 9000.0,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_1",
        "state": _state(),
        "action": {"product_price": 130.0},
    }
    exposure = live_percentile._hidden_policy_exposure_turn("champion", rec)
    assert exposure[:2] == (("champion", gid), 9000.0)
    assert exposure[2]["role"] == "seller"
    assert exposure[2]["p_zopa"] == 0.75

    rec["action"] = {"decision": "AcceptOffer"}
    assert live_percentile._hidden_policy_exposure_turn("champion", rec) is None
    rec["action"] = {"product_price": 130.0}
    rec["state"]["max_rounds"] = 1
    assert live_percentile._hidden_policy_exposure_turn("champion", rec) is None


def test_cohort_embeds_ineligible_counterpart_slot_before_filtering(
        monkeypatch, tmp_path):
    monkeypatch.setattr(live_percentile, "REPO", str(tmp_path))
    monkeypatch.setattr(live_percentile.time, "time", lambda: 10_000.0)
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.22)
    gid = _gids(True, 1)[0]
    eligible = {
        "ts": 9_500.0,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_1",
        "state": _state(),
        "action": {"product_price": 130.0},
    }
    ineligible_counterpart = {
        "ts": 9_501.0,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "state": _state(seat="player_2", own_value=80.0),
        "action": {"decision": "AcceptOffer"},
    }
    _write_jsonl(tmp_path / "logs/champion/turns.jsonl", [eligible])
    _write_jsonl(
        tmp_path / "logs/hardliner/turns.jsonl", [ineligible_counterpart])
    _write_jsonl(tmp_path / "logs/champion/results.jsonl", [{
        "ts": 9_700.0,
        "game_id": gid,
        "final": _final(gid, outcome="no_deal", payoffs=(0.0, 0.0)),
    }])

    rows = list(live_percentile.hidden_policy_games(1.0))

    assert len(rows) == 1
    assert rows[0][4]["fleet_slots"] == ("champion", "hardliner")
    assert rows[0][-1] == "terminal"


@pytest.mark.parametrize(
    ("raw_horizon", "expected"), [("10.0", "10"), ("unknown", "invalid")],
)
def test_signal_handles_numeric_string_and_malformed_horizons(
        raw_horizon, expected):
    state = _state()
    state["max_rounds"] = raw_horizon

    assert live_percentile._hidden_policy_signal(
        "player_1", state)["horizon"] == expected


def test_reachability_registry_uses_the_same_static_scope():
    name = "GLEE_NEGO_HIDDEN_POLICY_V1"
    predicate = check_reachability.KNOWN[name][2]
    game = {
        "game_id": "reachability-policy",
        "your_player": "player_1",
        "valid_actions": {"type": "offer"},
        "game_state": _state(),
    }

    assert name in check_reachability.POSTCONDITION_FLAGS
    assert predicate(game, {}) is True
    game["game_state"]["max_rounds"] = 1
    assert predicate(game, {}) is False
    game["game_state"] = _state(own_value=150.0)
    assert predicate(game, {}) is False


@pytest.mark.parametrize(
    ("seat", "own_value", "payoffs", "share", "pair"),
    [
        ("player_1", 80.0, (30.0, 10.0), 0.75, "S0.8-B1.2"),
        ("player_2", 150.0, (20.0, 30.0), 0.60, "S1-B1.5"),
    ],
)
def test_closed_zone_is_reconstructed_from_both_payoffs(
        monkeypatch, seat, own_value, payoffs, share, pair):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.64)
    gid = _gids(True, 1)[0]

    row = live_percentile._hidden_policy_row(
        "champion", {"game_id": gid},
        _final(gid, seat=seat, own_value=own_value, payoffs=payoffs))

    assert row[:4] == ("champion", 0.64, gid, True)
    assert row[4]["zone_share"] == pytest.approx(share)
    assert row[4]["realized_capture"] == pytest.approx(share)
    assert row[4]["pair"] == pair


def test_nonclose_has_zero_itt_capture_but_no_conditional_share(monkeypatch):
    monkeypatch.setattr(live_percentile, "percentile", lambda *_args: 0.12)
    gid = _gids(False, 1)[0]

    row = live_percentile._hidden_policy_row(
        "champion", {"game_id": gid},
        _final(gid, outcome="no_deal", payoffs=(0.0, 0.0)))

    assert row[3] is False
    assert row[4]["zone_share"] is None
    assert row[4]["realized_capture"] == 0.0
    assert row[4]["pair"] is None


@pytest.mark.parametrize(
    ("own_value", "payoffs"),
    [(80.0, (0.0, 0.0)), (100.0, (-10.0, -10.0))],
)
def test_nonpositive_zone_agreement_does_not_manufacture_a_share(
        own_value, payoffs):
    signal = live_percentile._hidden_policy_signal(
        "player_1", _state(own_value=own_value))

    diagnostic = live_percentile._hidden_zone_diagnostics(
        "player_1",
        {"player_1_payoff": payoffs[0], "player_2_payoff": payoffs[1]},
        True, signal)

    assert diagnostic["zone_share"] is None
    assert diagnostic["realized_capture"] == 0.0


def test_missing_opponent_payoff_is_explicit_and_blocks_zone_metric():
    signal = live_percentile._hidden_policy_signal("player_1", _state())

    diagnostic = live_percentile._hidden_zone_diagnostics(
        "player_1", {"player_1_payoff": 30.0}, True, signal)

    assert diagnostic["zone_share"] is None
    assert diagnostic["realized_capture"] is None
    assert diagnostic["reconstruction_missing"] is True


def test_off_grid_positive_reconstruction_is_excluded_and_explicit():
    signal = live_percentile._hidden_policy_signal("player_1", _state())

    diagnostic = live_percentile._hidden_zone_diagnostics(
        "player_1", {"player_1_payoff": 31.0, "player_2_payoff": 10.0},
        True, signal)

    assert diagnostic["zone_share"] is None
    assert diagnostic["realized_capture"] is None
    assert diagnostic["reconstruction_invalid"] is True


@pytest.mark.parametrize(
    ("seat", "own_value", "result", "expected_share"),
    [
        ("player_1", 80.0,
         {"your_payoff": 30.0, "opponent_payoff": 10.0}, 0.75),
        ("player_2", 150.0,
         {"your_payoff": 30.0, "opponent_payoff": 20.0}, 0.60),
    ],
)
def test_generic_payoff_schema_maps_our_and_opponent_seats(
        seat, own_value, result, expected_share):
    signal = live_percentile._hidden_policy_signal(
        seat, _state(seat=seat, own_value=own_value))

    diagnostic = live_percentile._hidden_zone_diagnostics(
        seat, result, True, signal)

    assert diagnostic["zone_share"] == pytest.approx(expected_share)


def test_report_pairs_conditional_share_with_itt_capture(capsys):
    controls = _gids(False)
    candidates = _gids(True)
    rows = [
        ("champion", 0.40, controls[0], True,
         _diagnostic(share=0.50, capture=0.50, pair="S0.8-B1.2")),
        ("champion", 0.60, controls[1], True,
         _diagnostic(share=0.50, capture=0.50, pair="S0.8-B1.2")),
        ("champion", 0.80, candidates[0], True,
         _diagnostic(share=0.90, capture=0.90, pair="S0.8-B1.2")),
        ("champion", 0.10, candidates[1], False,
         _diagnostic(share=None, capture=0.0)),
    ]

    assert live_percentile.report_hidden_policy(rows, 24.0) == 0

    output = capsys.readouterr().out
    assert "pct=" in output and "close=" in output
    assert "closed-zone-share median[IQR]=" in output
    assert "zone-capture-ITT=" in output
    assert "conditional median closed-zone share: +0.400" in output
    assert "mean reconstructed-zone capture: -0.0500" in output
    assert "selected on closing" in output
    assert "S0.8-B1.2=2" in output
    assert "pooled own-signal strata" in output


def test_report_excludes_game_ids_seen_in_multiple_slots_from_pool(capsys):
    duplicated = _gids(True, 1)[0]
    control = _gids(False, 1)[0]
    rows = [
        ("champion", 0.9, duplicated, True,
         _diagnostic(share=0.9, capture=0.9)),
        ("hardliner", 0.1, duplicated, False, _diagnostic()),
        ("champion", 0.5, control, True,
         _diagnostic(share=0.5, capture=0.5)),
    ]

    live_percentile.report_hidden_policy(rows, 24.0)

    output = capsys.readouterr().out
    assert "excluded 1 game id(s)" in output
    assert not any(line.startswith("POOLED") and "candidate" in line
                   for line in output.splitlines())


def test_embedded_fleet_slots_prevent_slots_filter_from_hiding_selfplay(capsys):
    duplicated = _gids(True, 1)[0]
    diagnostic = _diagnostic(share=0.9, capture=0.9)
    diagnostic["fleet_slots"] = ("champion", "hardliner")

    live_percentile.report_hidden_policy([
        ("champion", 0.9, duplicated, True, diagnostic),
    ], 24.0)

    output = capsys.readouterr().out
    assert "excluded 1 game id(s)" in output
    assert not any(line.startswith("POOLED") for line in output.splitlines())


def test_abandonment_keeps_signal_and_zero_capture_in_its_stratum(capsys):
    candidate = _gids(True, 1)[0]
    diagnostic = _diagnostic()
    diagnostic["fleet_slots"] = ("champion",)

    live_percentile.report_hidden_policy([
        ("champion", 0.05, candidate, False, diagnostic, "abandoned"),
    ], 24.0)

    output = capsys.readouterr().out
    stratum = next(line for line in output.splitlines()
                   if line.strip().startswith("seller") and "candidate" in line)
    assert "  1" in stratum and "0.0%" in stratum
    assert stratum.endswith("0.000")


def test_report_warns_when_closed_reconstruction_is_missing(capsys):
    candidate = _gids(True, 1)[0]
    live_percentile.report_hidden_policy([
        ("champion", 0.5, candidate, True,
         _diagnostic(capture=None, missing=True)),
    ], 24.0)

    assert "MISSING RECONSTRUCTION" in capsys.readouterr().out


def test_report_explains_off_grid_and_nonpositive_share_denominators(capsys):
    candidates = _gids(True)
    offgrid = _diagnostic(capture=None)
    offgrid["reconstruction_invalid"] = True
    nonpositive = _diagnostic(capture=0.0, pair="S0.8-B0.8")
    nonpositive["nonpositive_zone"] = True

    live_percentile.report_hidden_policy([
        ("champion", 0.4, candidates[0], True, offgrid),
        ("champion", 0.5, candidates[1], True, nonpositive),
    ], 24.0)

    output = capsys.readouterr().out
    assert "OFF-GRID RECONSTRUCTION" in output
    assert "UNDEFINED CLOSED SHARE" in output


def test_cli_routes_hidden_policy_and_returns_nonzero_without_exposures(
        monkeypatch, capsys):
    monkeypatch.setattr(
        live_percentile, "hidden_policy_games", lambda _hours, **_kwargs: iter(()))
    monkeypatch.setattr(
        sys, "argv", ["live_percentile.py", "--ab", "hidden-policy"])

    assert live_percentile.main() == 1
    assert "no eligible hidden-policy price exposures" in capsys.readouterr().out
