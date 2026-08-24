"""Intent-to-treat reader coverage for ``--ab pers-prose``."""

from __future__ import annotations

import json

from glee_agent.strategies import persuasion
from scripts import check_reachability, live_percentile


def _gid(candidate: bool) -> str:
    for index in range(1000):
        gid = f"pers-prose-reader-{index}"
        if persuasion.p08_r125_prose_assignment(gid) is candidate:
            return gid
    raise AssertionError("assignment not found")


def _state():
    return {
        "current_player": "player_1",
        "product_price": 100.0,
        "p": 0.8,
        "v": 125.0,
        "u": 0.0,
        "round": 1,
        "total_rounds": 20,
        "seller_message_type": "text",
        "history": [],
    }


def test_exposure_is_fixed_before_the_first_message_outcome():
    gid = _gid(True)
    rec = {
        "ts": 123.0,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_1",
        "action_type": "seller_message",
        "state": _state(),
        "action": {"message": "This one is worth taking. My record on these "
                              "is the reason to take this one seriously."},
        "plan": {"recommend": True},
        "opponent": {"type": "hidden", "name": None},
    }
    key, stamp, signal = live_percentile._pers_prose_exposure_turn(
        "randomized", rec)
    assert key == ("randomized", gid)
    assert stamp == 123.0
    assert signal["ratio"] == 1.25
    assert signal["first_recommend"] is True


def test_exact_reachability_predicate_rejects_neighbor_cells():
    game = {
        "your_player": "player_1",
        "valid_actions": {"type": "seller_message"},
        "game_state": _state(),
    }
    predicate = check_reachability.KNOWN[
        "GLEE_PERS_P08_R125_PROSE_AB"][2]
    assert predicate(game, {"recommend": True})
    game["game_state"]["v"] = 120.0
    assert not predicate(game, {"recommend": True})

    final_config = _state()
    final_config["is_seller_know_cv"] = False
    assert live_percentile._pers_prose_signal("player_1", final_config) is None


def _diagnostic(message: str):
    return {
        "price": 100.0,
        "p": 0.8,
        "v": 125.0,
        "u": 0.0,
        "ratio": 1.25,
        "total_rounds": 20,
        "first_message": message,
        "first_recommend": True,
        "seller_messages": [message] * 20,
        "purchase_rate": 0.5,
        "payoff_per_price": 10.0,
        "zero_outcome": False,
        "fleet_slots": ("randomized",),
    }


def test_report_joins_official_deltas_and_keeps_local_score_diagnostic(
        tmp_path, capsys):
    control_gid = _gid(False)
    candidate_gid = _gid(True)
    prose = ("This one is worth taking. My record on these is the reason to "
             "take this one seriously.")
    rows = [
        ("randomized", 0.4, control_gid, True, _diagnostic("yes"), "terminal"),
        ("randomized", 0.6, candidate_gid, True, _diagnostic(prose), "terminal"),
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "randomized", "game_id": control_gid, "rating_delta": -1.0},
        {"slot": "randomized", "game_id": candidate_gid, "rating_delta": 2.0},
    ]), encoding="utf-8")

    assert live_percentile.report_pers_prose(
        rows, 24.0, since=100.0, official_path=str(official)) == 0
    output = capsys.readouterr().out
    assert "OFFICIAL per-game rating delta: +3.0000" in output
    assert "local same-cell percentile (diagnostic): +0.2000" in output
    assert "mechanism failures=0" in output


def test_mechanism_mismatch_rejects_even_with_a_good_official_delta(
        tmp_path, capsys):
    gid = _gid(True)
    row = ("composite", 0.9, gid, True, _diagnostic("yes"), "terminal")
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "composite", "game_id": gid, "rating_delta": 9.0},
    ]), encoding="utf-8")

    assert live_percentile.report_pers_prose(
        [row], 24.0, since=100.0, official_path=str(official)) == 2
    assert "MECHANISM REJECTION" in capsys.readouterr().out


def test_unresolved_assignments_remain_visible_and_block_promotion(capsys):
    gid = _gid(False)
    row = ("composite", None, gid, None, {
        **_diagnostic("yes"), "seller_messages": []}, "cold-missing")

    assert live_percentile.report_pers_prose(
        [row], 24.0, since=100.0) == 0
    output = capsys.readouterr().out
    assert "unresolved=1" in output
    assert "PROMOTION BLOCKED" in output
