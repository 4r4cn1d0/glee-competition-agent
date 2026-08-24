"""All-assigned ITT reader tests for ``--ab pers-decline-veto``."""

from __future__ import annotations

import json

from glee_agent.strategies import persuasion
from scripts import check_reachability, live_percentile


def _gid(candidate: bool) -> str:
    for index in range(1000):
        gid = f"pers-decline-reader-{index}"
        if persuasion.p08_r125_text_decline_veto_assignment(gid) is candidate:
            return gid
    raise AssertionError("assignment not found")


def _state(message: str = "Recommended.") -> dict:
    return {
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "product_price": 100.0,
        "p": 0.8,
        "v": 125.0,
        "u": 0.0,
        "is_seller_know_cv": True,
        "seller_message_type": "text",
        "seller_message": message,
        "round": 1,
        "total_rounds": 20,
        "history": [],
    }


def _diagnostic(*, bought_declines: int = 0, veto_traces: int = 0) -> dict:
    messages = ["Not recommended."] + ["Recommended."] * 19
    return {
        "price": 100.0,
        "p": 0.8,
        "v": 125.0,
        "u": 0.0,
        "ratio": 1.25,
        "total_rounds": 20,
        "seller_message_type": "text",
        "is_seller_know_cv": True,
        "seller_messages": messages,
        "buyer_decisions": ["no"] + ["yes"] * 19,
        "qualities": ["low"] + ["high"] * 19,
        "purchases": 19,
        "purchase_rate": 0.95,
        "explicit_declines": 1,
        "bought_explicit_declines": bought_declines,
        "first_decline_round": 1,
        "payoff_per_price": 4.75,
        "zero_outcome": False,
        "negative_outcome": False,
        "eligible_turns": 20,
        "veto_traces": veto_traces,
        "trace_failures": 0,
        "fleet_slots": ("hardliner",),
    }


def test_exposure_is_first_decision_even_without_a_decline() -> None:
    gid = _gid(True)
    rec = {
        "ts": 123.0,
        "game_id": gid,
        "game_family": "persuasion",
        "your_player": "player_2",
        "phase": "buyer_decision",
        "action_type": "buyer_decision",
        "state": _state("Recommended."),
        "action": {"decision": "yes"},
        "plan": {"buy": True},
        "opponent": {"type": "hidden", "name": None},
    }
    key, stamp, signal = live_percentile._pers_decline_veto_exposure_turn(
        "hardliner", rec)
    assert key == ("hardliner", gid)
    assert stamp == 123.0
    assert signal["first_message"] == "Recommended."
    assert signal["first_decision"] == "yes"


def test_exact_reachability_predicate_rejects_neighbor_cells() -> None:
    game = {
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": _state("Not recommended."),
    }
    predicate = check_reachability.KNOWN[
        "GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB"][2]
    assert predicate(game, {"buy": True})
    game["game_state"]["v"] = 120.0
    assert not predicate(game, {"buy": True})
    assert live_percentile._pers_decline_veto_signal(
        "player_2", game["game_state"]) is None


def test_report_joins_official_all_assigned_arms(tmp_path, capsys) -> None:
    control_gid = _gid(False)
    candidate_gid = _gid(True)
    rows = [
        ("hardliner", 0.4, control_gid, True, _diagnostic(), "terminal"),
        ("hardliner", 0.7, candidate_gid, True,
         _diagnostic(veto_traces=1), "terminal"),
    ]
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "hardliner", "game_id": control_gid, "rating_delta": -1.0},
        {"slot": "hardliner", "game_id": candidate_gid, "rating_delta": 2.0},
    ]), encoding="utf-8")

    assert live_percentile.report_pers_decline_veto(
        rows, 24.0, since=100.0, official_path=str(official)) == 1
    output = capsys.readouterr().out
    assert "OFFICIAL per-game rating delta: +3.0000" in output
    assert "veto traces=1" in output
    assert "PROMOTION BLOCKED" in output


def test_candidate_bought_decline_is_mechanism_rejection(
        tmp_path, capsys) -> None:
    gid = _gid(True)
    rows = [("hardliner", 0.9, gid, True,
             _diagnostic(bought_declines=1), "terminal")]
    official = tmp_path / "official.json"
    official.write_text(json.dumps([
        {"slot": "hardliner", "game_id": gid, "rating_delta": 9.0},
    ]), encoding="utf-8")
    assert live_percentile.report_pers_decline_veto(
        rows, 24.0, since=100.0, official_path=str(official)) == 2
    assert "MECHANISM REJECTION" in capsys.readouterr().out


def test_no_decline_unresolved_assignment_remains_in_itt(capsys) -> None:
    gid = _gid(False)
    diagnostic = _diagnostic()
    diagnostic.update({
        "seller_messages": [],
        "explicit_declines": 0,
        "bought_explicit_declines": 0,
    })
    row = ("hardliner", None, gid, None, diagnostic, "cold-missing")
    assert live_percentile.report_pers_decline_veto(
        [row], 24.0, since=100.0) == 1
    output = capsys.readouterr().out
    assert "unresolved=1" in output
    assert "PROMOTION BLOCKED" in output


def test_authenticated_buyer_transcript_recovers_missing_final(
        tmp_path, capsys) -> None:
    gid = _gid(True)
    messages = ["Not recommended."] + ["Recommended."] * 19
    qualities = ["low"] + ["high"] * 19
    decisions = ["pass"] + ["buy"] * 19
    diagnostic = _diagnostic(veto_traces=1)
    diagnostic["seller_messages"] = []
    row = ("hardliner", None, gid, None, diagnostic, "cold-missing")
    official = tmp_path / "official.json"
    official.write_text(json.dumps([{
        "source": "authenticated-dashboard-transcript",
        "family": "persuasion",
        "role": "buyer",
        "terminal": True,
        "slot": "hardliner",
        "game_id": gid,
        "rating_delta": 2.5,
        "persuasion": {
            "price": 100.0,
            "p": 0.8,
            "v": 125.0,
            "u": 0.0,
            "mode": "text",
            "is_seller_know_cv": True,
            "rounds": 20,
            "seller_messages": messages,
            "qualities": qualities,
            "buyer_decisions": decisions,
            "buyer_payoff": 475.0,
        },
    }]), encoding="utf-8")
    assert live_percentile.report_pers_decline_veto(
        [row], 24.0, since=100.0, official_path=str(official)) == 1
    output = capsys.readouterr().out
    assert "official-dR=2.5000" in output
    assert "terminal=1 pending=0" in output
