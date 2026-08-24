"""Exact live-prefix joins for decisions on the first incoming offer."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts import join_official_history as joiner


SLOT = "conceder"


def _turn(game_id="first-decision", *, decision="AcceptOffer",
          offer="10.00", from_player="player_1", ts=6_000):
    return {
        "ts": ts,
        "game_id": game_id,
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "action_type": "decision",
        "state": {
            "game_family": "negotiation",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "player_2_value": "12.00",
            "complete_information": False,
            "horizon_known": True,
            "max_rounds": 1,
            "history": [],
            "last_offer": {
                "price": offer,
                "from_player": from_player,
                "round": 1,
            },
        },
        "action": {"decision": decision},
    }


def _dashboard(*, decision="AcceptOffer", offer="10.00", rating=3.5):
    agreement = decision == "AcceptOffer"
    return {
        "slot": SLOT,
        "timestamp": 6_000,
        "role": "buyer",
        "outcome": "agreement" if agreement else "no_deal",
        "rating_delta": rating,
        "modal": {
            "setup": {
                "role": "buyer",
                "own_value": "12.00",
                "complete_information": False,
                "horizon": 1,
            },
            "transcript": [
                {"offer": {"role": "seller", "price": offer}},
                {"decision": {"role": "buyer", "action": decision}},
            ],
            "terminal_payoffs": {
                "seller": "2.00" if agreement else "0.00",
                "buyer": "2.00" if agreement else "0.00",
            },
        },
    }


def _write_turns(tmp_path, *turns):
    slot = tmp_path / SLOT
    slot.mkdir(parents=True)
    (slot / "games").mkdir()
    (slot / "turns.jsonl").write_text(
        "".join(json.dumps(turn) + "\n" for turn in turns),
        encoding="utf-8",
    )


def _join(tmp_path, dashboard):
    return joiner.join_history(
        [dashboard],
        logs_root=tmp_path,
        slots=[SLOT],
        timestamp_mode="first",
        include_live_turns=True,
    )


@pytest.mark.parametrize("decision", ["AcceptOffer", "RejectOffer"])
def test_first_incoming_offer_decision_joins_exact_dashboard_prefix(
        tmp_path, decision):
    _write_turns(tmp_path, _turn(decision=decision))

    document, report = _join(tmp_path, _dashboard(decision=decision))

    assert [game["game_id"] for game in document["games"]] == [
        "first-decision"]
    assert document["games"][0]["join_audit"]["match_rule"] == (
        "exact-modal-turn-prefix+first-minute/v1")
    assert report["unresolved"] == report["ambiguous"] == []


def test_live_record_prefix_contains_last_offer_before_our_decision():
    local = joiner._live_turn_record(
        _turn(), slot=SLOT, path=Path("turns.jsonl"),
        first_ts=6_000, last_ts=6_000)

    assert local.transcript_key == (
        ("offer", "seller", 1_000),
        ("decision", "buyer", "accept"),
    )


def test_existing_history_does_not_duplicate_last_offer():
    turn = _turn()
    turn["state"]["history"] = [{
        "round": 1,
        "offer": {"price": "10.00", "from_player": "player_1"},
    }]
    local = joiner._live_turn_record(
        turn, slot=SLOT, path=Path("turns.jsonl"),
        first_ts=6_000, last_ts=6_000)

    assert local.transcript_key == (
        ("offer", "seller", 1_000),
        ("decision", "buyer", "accept"),
    )


def test_empty_history_offer_action_does_not_import_stale_last_offer():
    turn = _turn()
    turn["phase"] = turn["action_type"] = "offer"
    turn["action"] = {"product_price": "9.00"}
    local = joiner._live_turn_record(
        turn, slot=SLOT, path=Path("turns.jsonl"),
        first_ts=6_000, last_ts=6_000)

    assert local.transcript_key == (("offer", "buyer", 900),)


@pytest.mark.parametrize("mutation", [
    lambda state: state.pop("last_offer"),
    lambda state: state.__setitem__("last_offer", None),
    lambda state: state["last_offer"].pop("price"),
    lambda state: state["last_offer"].pop("from_player"),
    lambda state: state["last_offer"].__setitem__(
        "from_player", "player_2"),
])
def test_missing_or_nonincoming_last_offer_fails_closed(mutation):
    turn = _turn()
    mutation(turn["state"])

    with pytest.raises(joiner.JoinInputError):
        joiner._live_turn_record(
            turn, slot=SLOT, path=Path("turns.jsonl"),
            first_ts=6_000, last_ts=6_000)


def test_same_minute_wrong_offer_remains_unresolved_not_time_guessed(tmp_path):
    _write_turns(tmp_path, _turn(offer="10.00"))

    document, report = _join(tmp_path, _dashboard(offer="10.01"))

    assert document["games"] == []
    assert report["ambiguous"] == []
    assert report["unresolved"][0]["candidate_count"] == 0
    assert "exact fingerprint/turn-prefix" in report["unresolved"][0]["reason"]


def test_rating_remains_outside_live_prefix_key():
    low = _dashboard(rating=-8.0)
    high = copy.deepcopy(low)
    high["rating_delta"] = 7.5
    low_records, low_errors = joiner._dashboard_records(
        [low], slots={SLOT}, dashboard_timezone=None)
    high_records, high_errors = joiner._dashboard_records(
        [high], slots={SLOT}, dashboard_timezone=None)

    assert low_errors == high_errors == []
    assert low_records[0].setup_key == high_records[0].setup_key
    assert low_records[0].transcript_key == high_records[0].transcript_key
    assert low_records[0].fingerprint == high_records[0].fingerprint


def _prefix_records(suffix):
    prefix = (("offer", "seller", 1_200),
              ("decision", "buyer", "reject"),
              ("counter", "buyer", 900))
    dashboard = joiner.DashboardRecord(
        row=0, slot=SLOT, timestamp_raw=6_000, minute_utc=100,
        role="buyer", outcome="no_deal", rating_delta=0,
        fingerprint="unused", setup_key="same",
        transcript_key=prefix + suffix,
    )
    local = joiner.LocalRecord(
        slot=SLOT, game_id="terminal-counter", path="turns.jsonl",
        fingerprint=None, first_ts=6_000, completion_ts=6_000,
        setup_key="same", transcript_key=prefix,
        match_rule="exact-modal-turn-prefix",
    )
    return dashboard, local


def test_terminal_opponent_reject_with_counter_is_one_compound_suffix():
    dashboard, local = _prefix_records((
        ("decision", "seller", "reject"),
        ("counter", "seller", 1_001),
    ))

    assert joiner._turn_prefix_matches(dashboard, local)


@pytest.mark.parametrize("suffix", [
    (("decision", "buyer", "reject"), ("counter", "buyer", 1_001)),
    (("decision", "seller", "accept"), ("counter", "seller", 1_001)),
    (("decision", "seller", "reject"), ("offer", "seller", 1_001)),
    (("decision", "seller", "reject"), ("counter", "buyer", 1_001)),
    (("decision", "seller", "reject"), ("counter", "seller", 1_001),
     ("decision", "buyer", "reject")),
])
def test_other_multi_event_suffixes_still_fail_closed(suffix):
    dashboard, local = _prefix_records(suffix)

    assert not joiner._turn_prefix_matches(dashboard, local)
