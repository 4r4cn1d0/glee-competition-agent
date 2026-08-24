"""Fail-closed tests for the authenticated-dashboard official rating join."""

from __future__ import annotations

import copy
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from scripts import join_official_history as J


SLOT = "conceder"


def _history(*, echo: bool = False):
    rows = [
        {
            "round": 1,
            "offer": {"from_player": "player_1", "price": "10.00"},
            "decision": "RejectOffer",
            "decided_by": "player_2",
            "counteroffer": {"from_player": "player_2", "price": "8.00"},
        },
    ]
    second = {
        "round": 2,
        "decision": "AcceptOffer",
        "decided_by": "player_1",
    }
    if echo:
        second["offer"] = {"from_player": "player_2", "price": "8.00"}
    rows.append(second)
    return rows


def _dashboard_transcript(*, echo: bool = False):
    rows = [
        {"offer": {"role": "seller", "price": "10.00"}},
        {"decision": {"role": "buyer", "action": "RejectOffer"}},
        {"counter": {"role": "buyer", "price": "8.00"}},
    ]
    if echo:
        rows.append({"offer": {"role": "buyer", "price": "8.00"}})
    rows.append({"decision": {"role": "seller", "action": "AcceptOffer"}})
    return rows


def _local_game(game_id: str, *, first_ts: float, final_ts: float | None = None,
                history=None, own_value="6.00", seller_payoff="2.00",
                buyer_payoff="4.00", outcome="agreement", status="completed"):
    turns = [{"ts": first_ts, "action": {"product_price": "10.00"}}]
    if final_ts is not None:
        turns.append({"ts": final_ts, "action": {"decision": "AcceptOffer"}})
    return {
        "game_id": game_id,
        "game_family": "negotiation",
        "your_player": "player_1",
        "status": status,
        "config": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_1_value": own_value,
            "complete_information": False,
            "horizon_known": False,
            "max_rounds": None,
        },
        "result": {
            "outcome": outcome,
            "player_1_payoff": seller_payoff,
            "player_2_payoff": buyer_payoff,
        },
        "history": _history(echo=True) if history is None else history,
        "our_turns": turns,
    }


def _dashboard_row(*, timestamp, rating=3.25, transcript=None,
                   own_value="6.00", seller_payoff="2.00",
                   buyer_payoff="4.00", outcome="agreement"):
    return {
        "slot": SLOT,
        "timestamp": timestamp,
        "role": "seller",
        "outcome": outcome,
        "rating_delta": rating,
        "modal": {
            "setup": {
                "role": "seller",
                "own_value": own_value,
                "complete_information": False,
                "horizon": "unknown",
            },
            "transcript": (_dashboard_transcript()
                           if transcript is None else transcript),
            "terminal_payoffs": {
                "seller": seller_payoff,
                "buyer": buyer_payoff,
            },
        },
    }


def _write_local(tmp_path, game):
    games = tmp_path / SLOT / "games"
    games.mkdir(parents=True, exist_ok=True)
    (games / f"{game['game_id']}.json").write_text(
        json.dumps(game), encoding="utf-8")


def _join(tmp_path, rows, **kwargs):
    return J.join_history(
        rows,
        logs_root=tmp_path,
        slots=[SLOT],
        timestamp_mode=kwargs.pop("timestamp_mode", "first"),
        **kwargs,
    )


def test_unique_join_emits_live_percentile_schema_and_audit(tmp_path):
    _write_local(tmp_path, _local_game("game-one", first_ts=6_000))

    document, report = _join(tmp_path, [_dashboard_row(timestamp=6_030)])

    assert document["_schema"] == "glee.official-rating-join/v1"
    assert list(document) == ["_schema", "games"]
    assert document["games"][0]["slot"] == SLOT
    assert document["games"][0]["game_id"] == "game-one"
    assert document["games"][0]["rating_delta"] == 3.25
    audit = document["games"][0]["join_audit"]
    assert audit["candidate_count"] == 1
    assert audit["timestamp_mode"] == "first"
    assert report["matched"] == 1
    assert report["unresolved"] == report["ambiguous"] == []


def test_repeated_transcript_is_resolved_by_minute_not_nearest_guess(tmp_path):
    _write_local(tmp_path, _local_game("early", first_ts=6_000))
    _write_local(tmp_path, _local_game("late", first_ts=12_000))

    document, report = _join(tmp_path, [_dashboard_row(timestamp=12_020)])

    assert [game["game_id"] for game in document["games"]] == ["late"]
    assert report["ambiguous"] == []


@pytest.mark.parametrize("dashboard_ts", [6_120, 6_240])
def test_dual_anchor_accepts_plus_or_minus_one_minute_from_completion(
        tmp_path, dashboard_ts):
    _write_local(tmp_path, _local_game(
        "dual", first_ts=6_000, final_ts=6_180))

    document, report = _join(
        tmp_path, [_dashboard_row(timestamp=dashboard_ts)], timestamp_mode="dual")

    assert [game["game_id"] for game in document["games"]] == ["dual"]
    audit = document["games"][0]["join_audit"]
    assert audit["minute_tolerance"] == 1
    assert audit["local_completion_ts"] == 6_180
    assert report["unresolved"] == []


def test_money_is_canonicalized_to_exact_half_up_cents(tmp_path):
    assert J.money_to_cents("1.005") == 101
    assert J.money_to_cents(1.005) == 101
    _write_local(tmp_path, _local_game(
        "cents", first_ts=6_000, own_value="1.005",
        seller_payoff="1.005", buyer_payoff="2.005"))
    row = _dashboard_row(
        timestamp=6_000, own_value="1.01",
        seller_payoff="1.01", buyer_payoff="2.01")

    document, report = _join(tmp_path, [row])

    assert [game["game_id"] for game in document["games"]] == ["cents"]
    assert report["unresolved"] == []


def test_counteroffer_record_echo_is_collapsed_on_either_side(tmp_path):
    _write_local(tmp_path, _local_game(
        "echo", first_ts=6_000, history=_history(echo=True)))
    without_echo = _dashboard_row(
        timestamp=6_000, transcript=_dashboard_transcript(echo=False))

    document, _report = _join(tmp_path, [without_echo])

    assert [game["game_id"] for game in document["games"]] == ["echo"]


def test_duplicate_dashboard_rows_are_ambiguous_even_if_ratings_differ(tmp_path):
    _write_local(tmp_path, _local_game("only-local", first_ts=6_000))
    first = _dashboard_row(timestamp=6_000, rating=1.0)
    second = copy.deepcopy(first)
    second["rating_delta"] = 9.0

    document, report = _join(tmp_path, [first, second])

    assert document["games"] == []
    assert [issue["dashboard_row"] for issue in report["ambiguous"]] == [0, 1]
    assert all(issue["candidate_count"] == 1 for issue in report["ambiguous"])
    assert all("rating excluded" in issue["reason"]
               for issue in report["ambiguous"])


def test_missing_modal_data_is_unresolved_not_guessed(tmp_path):
    _write_local(tmp_path, _local_game("local", first_ts=6_000))
    row = _dashboard_row(timestamp=6_000)
    del row["modal"]["terminal_payoffs"]

    document, report = _join(tmp_path, [row])

    assert document["games"] == []
    assert report["ambiguous"] == []
    assert report["unresolved"][0]["dashboard_row"] == 0
    assert "payoffs" in report["unresolved"][0]["reason"]


def test_no_deal_terminal_status_and_walk_label_share_wire_outcome(tmp_path):
    local_history = [{
        "round": 1,
        "offer": {"from_player": "player_2", "price": "8.00"},
        "decision": "WalkAway",
        "decided_by": "player_1",
    }]
    dashboard_transcript = [
        {"offer": {"role": "buyer", "price": "8.00"}},
        {"decision": {"role": "seller", "action": "WalkAway"}},
    ]
    _write_local(tmp_path, _local_game(
        "no-deal", first_ts=6_000, history=local_history,
        seller_payoff=0, buyer_payoff=0, outcome="no_deal", status="no_deal"))
    row = _dashboard_row(
        timestamp=6_000, transcript=dashboard_transcript,
        seller_payoff=0, buyer_payoff=0, outcome="walked away")

    document, report = _join(tmp_path, [row])

    assert [game["game_id"] for game in document["games"]] == ["no-deal"]
    assert report["unresolved"] == []


def test_rating_never_enters_fingerprint_or_candidate_key(tmp_path):
    _write_local(tmp_path, _local_game("rating-independent", first_ts=6_000))
    low = _dashboard_row(timestamp=6_000, rating=-8.75)
    high = _dashboard_row(timestamp=6_000, rating=7.5)
    low_record, _ = J._dashboard_records(
        [low], slots={SLOT}, dashboard_timezone=None)
    high_record, _ = J._dashboard_records(
        [high], slots={SLOT}, dashboard_timezone=None)

    assert low_record[0].fingerprint == high_record[0].fingerprint
    document, _report = _join(tmp_path, [high])
    assert document["games"][0]["game_id"] == "rating-independent"
    assert document["games"][0]["rating_delta"] == 7.5


def test_auto_mode_freezes_only_discriminating_timestamp_semantics(tmp_path):
    _write_local(tmp_path, _local_game(
        "calibration", first_ts=6_000, final_ts=6_180))

    document, report = _join(
        tmp_path, [_dashboard_row(timestamp=6_180)], timestamp_mode="auto")

    assert document["games"][0]["join_audit"]["timestamp_mode"] == "completion"
    assert report["timestamp_mode_source"] == "auto-calibrated"


def test_auto_mode_refuses_nondiscriminating_anchor(tmp_path):
    _write_local(tmp_path, _local_game(
        "same-minute", first_ts=6_000, final_ts=6_030))

    with pytest.raises(J.JoinInputError, match="cannot distinguish"):
        _join(tmp_path, [_dashboard_row(timestamp=6_010)], timestamp_mode="auto")


def test_authenticated_dashboard_timestamp_requires_and_uses_timezone():
    rendered = "Aug 24, 2026 7:08 PM"
    expected = datetime(
        2026, 8, 24, 19, 8, tzinfo=ZoneInfo("Asia/Kolkata")).timestamp()

    assert J._timestamp_epoch(rendered, "Asia/Kolkata") == expected
    with pytest.raises(J.JoinInputError, match="requires --dashboard-timezone"):
        J._timestamp_epoch(rendered, None)


def test_timeout_is_a_distinct_terminal_event(tmp_path):
    local_history = [{
        "round": 1,
        "offer": {"from_player": "player_2", "price": "8.00"},
        "decision": "timeout",
        "decided_by": "player_1",
        "timed_out_by": "player_1",
    }]
    dashboard_transcript = [
        {"offer": {"role": "buyer", "price": "8.00"}},
        {"decision": {"role": "seller", "action": "TimedOut"}},
    ]
    _write_local(tmp_path, _local_game(
        "timed-out", first_ts=6_000, history=local_history,
        seller_payoff=0, buyer_payoff=0, outcome="timeout", status="no_deal"))
    row = _dashboard_row(
        timestamp=6_000, transcript=dashboard_transcript,
        seller_payoff=0, buyer_payoff=0, outcome="no deal")

    document, report = _join(tmp_path, [row])

    assert [game["game_id"] for game in document["games"]] == ["timed-out"]
    assert report["local_errors"] == []


def test_active_live_snapshot_is_ignored_not_reported(tmp_path):
    _write_local(tmp_path, _local_game(
        "active-snapshot", first_ts=5_000, status="active"))
    _write_local(tmp_path, _local_game("completed", first_ts=6_000))

    document, report = _join(tmp_path, [_dashboard_row(timestamp=6_000)])

    assert [game["game_id"] for game in document["games"]] == ["completed"]
    assert report["local_errors"] == []


def test_raw_authenticated_card_and_modal_capture_matches_structured_row():
    card = (
        "NegotiationYou played Seller vs an agentAgreement · "
        "Aug 24, 2026 7:08 PMRating+3.25›")
    # The dialog is newest-first and includes prose containing the word
    # "accepting". Only the standalone final action line is semantic.
    modal = """Negotiation
Game transcript

Aug 24, 2026, 7:08 PM

GAME SETUP

Your valuation:
$6.00
Max rounds:
No limit
Messages:
Allowed
Round 2
You (Buyer)

Offered: $8.00

Accept

Round 1
You (Seller)

Offered: $10.00“A sentence about accepting a fair deal.”

Rejectcounter: $8.00

FINAL RESULT — YOU REACHED A DEAL

YOUR PAYOFF

$2.00

OPPONENT

$4.00"""
    captured, captured_errors = J._dashboard_records(
        [{"slot": SLOT, "card_text": card, "modal_text": modal}],
        slots={SLOT}, dashboard_timezone="Asia/Kolkata")
    structured = _dashboard_row(
        timestamp="Aug 24, 2026 7:08 PM", rating=3.25)
    expected, expected_errors = J._dashboard_records(
        [structured], slots={SLOT}, dashboard_timezone="Asia/Kolkata")

    assert captured_errors == expected_errors == []
    assert captured[0].fingerprint == expected[0].fingerprint
    assert captured[0].rating_delta == 3.25
    assert captured[0].minute_utc == expected[0].minute_utc


def test_raw_capture_fails_closed_on_missing_round_decision():
    card = (
        "NegotiationYou played Buyer vs an agentNo deal · "
        "Aug 24, 2026 7:08 PMRating-7.1›")
    modal = """Your valuation:
$1,200,000
Max rounds:
1
Round 1
Seller

Offered: $1,200,000

FINAL RESULT — NO DEAL WAS REACHED
YOUR PAYOFF
$0
OPPONENT
$0"""

    records, errors = J._dashboard_records(
        [{"slot": SLOT, "card_text": card, "modal_text": modal}],
        slots={SLOT}, dashboard_timezone="Asia/Kolkata")

    assert records == []
    assert "missing decision" in errors[0]["reason"]
