"""Intent-to-treat reader coverage for ``--ab pers-truth``."""

from __future__ import annotations

import json

from glee_agent.strategies import persuasion
from scripts import check_reachability, live_percentile


def _gid(candidate: bool) -> str:
    for index in range(1000):
        gid = f"pers-truth-reader-{index}"
        if persuasion.p08_r125_binary_truth_assignment(gid) is candidate:
            return gid
    raise AssertionError("assignment not found")


def _state():
    return {
        "current_player": "player_1",
        "current_quality": "low",
        "product_price": 100.0,
        "p": 0.8,
        "v": 125.0,
        "u": 0.0,
        "round": 1,
        "total_rounds": 20,
        "seller_message_type": "binary",
        "history": [],
    }


def test_exposure_is_fixed_at_first_seller_turn_before_buyer_response():
    gid = _gid(True)
    rec = {
        "ts": 123.0,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_1",
        "action_type": "seller_recommendation",
        "state": _state(),
        "action": {"decision": "no"},
        "plan": {"recommend": False},
        "opponent": {"type": "hidden", "name": None},
    }
    key, stamp, signal = live_percentile._pers_truth_exposure_turn(
        "hardliner", rec)
    assert key == ("hardliner", gid)
    assert stamp == 123.0
    assert signal["ratio"] == 1.25
    assert signal["first_quality"] == "low"
    assert signal["first_recommend"] is False


def test_exact_reachability_predicate_rejects_neighbor_cells():
    game = {
        "your_player": "player_1",
        "valid_actions": {"type": "seller_recommendation"},
        "game_state": _state(),
    }
    predicate = check_reachability.KNOWN[
        "GLEE_PERS_P08_R125_BINARY_TRUTH_AB"][2]
    assert predicate(game, {"recommend": False})
    game["game_state"]["v"] = 120.0
    assert not predicate(game, {"recommend": False})

    final_config = _state()
    final_config["is_seller_know_cv"] = False
    assert live_percentile._pers_truth_signal("player_1", final_config) is None


def _diagnostic(messages, qualities):
    return {
        "price": 100.0,
        "p": 0.8,
        "v": 125.0,
        "u": 0.0,
        "ratio": 1.25,
        "total_rounds": 20,
        "first_decision": messages[0],
        "first_recommend": messages[0] == "yes",
        "first_quality": qualities[0],
        "seller_messages": messages,
        "qualities": qualities,
        "purchases": 10,
        "purchase_rate": 0.5,
        "payoff_per_price": 10.0,
        "zero_outcome": False,
        "fleet_slots": ("hardliner",),
    }


def test_report_joins_official_deltas_and_audits_quality_conditioned_wire(
        tmp_path, capsys):
    control_gid = _gid(False)
    candidate_gid = _gid(True)
    qualities = ["high", "low"] * 10
    rows = [
        ("hardliner", 0.4, control_gid, True,
         _diagnostic(["yes"] * 20, qualities), "terminal"),
        ("hardliner", 0.6, candidate_gid, True,
         _diagnostic(["yes", "no"] * 10, qualities), "terminal"),
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "hardliner", "game_id": control_gid, "rating_delta": -1.0},
        {"slot": "hardliner", "game_id": candidate_gid, "rating_delta": 2.0},
    ]), encoding="utf-8")

    assert live_percentile.report_pers_truth(
        rows, 24.0, since=100.0, official_path=str(official)) == 0
    output = capsys.readouterr().out
    assert "OFFICIAL per-game rating delta: +3.0000" in output
    assert "local same-cell percentile (diagnostic): +0.2000" in output
    assert "mechanism failures=0" in output


def test_candidate_low_yes_is_an_immediate_mechanism_rejection(
        tmp_path, capsys):
    gid = _gid(True)
    qualities = ["high", "low"] * 10
    row = ("hardliner", 0.9, gid, True,
           _diagnostic(["yes"] * 20, qualities), "terminal")
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "hardliner", "game_id": gid, "rating_delta": 9.0},
    ]), encoding="utf-8")

    assert live_percentile.report_pers_truth(
        [row], 24.0, since=100.0, official_path=str(official)) == 2
    assert "MECHANISM REJECTION" in capsys.readouterr().out


def test_unresolved_assignment_is_visible_and_blocks_promotion(capsys):
    gid = _gid(False)
    diagnostic = _diagnostic(["yes"], ["low"])
    diagnostic["seller_messages"] = []
    diagnostic["qualities"] = []
    row = ("hardliner", None, gid, None, diagnostic, "cold-missing")

    assert live_percentile.report_pers_truth(
        [row], 24.0, since=100.0) == 0
    output = capsys.readouterr().out
    assert "unresolved=1" in output
    assert "PROMOTION BLOCKED" in output
