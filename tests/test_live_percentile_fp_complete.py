"""Exact-CDF reader for the first-principles promotion cells."""

from __future__ import annotations

import hashlib

from glee_agent import first_principles
from scripts import live_percentile


def _gid(treatment: bool) -> str:
    for index in range(1000):
        gid = f"fp-reader-{index}"
        if first_principles.treatment_assignment(gid) is treatment:
            return gid
    raise AssertionError("could not recover both assignment arms")


def _state(*, role="seller", horizon=1, complete=True):
    seat = "player_1" if role == "seller" else "player_2"
    return seat, {
        "current_player": seat,
        "horizon_known": True,
        "max_rounds": horizon,
        "complete_information": complete,
        "messages_allowed": False,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": 80.0,
        "player_2_value": 150.0,
        "round": 1,
    }


def test_reader_uses_the_action_paths_pure_hash_assignment():
    assert first_principles.treatment_assignment(None) is None
    assert live_percentile.fp_complete_arm(None) is None
    for index in range(64):
        gid = f"fp-parity-{index}"
        bit = bool(int(hashlib.sha256(
            ("nego_fp|" + gid).encode()).hexdigest(), 16) & 1)
        assert first_principles.treatment_assignment(gid) is bit
        assert live_percentile.fp_complete_arm(gid) == (
            "candidate" if bit else "control")


def test_signal_contains_only_the_two_measured_positive_complete_cells():
    seller, single = _state(role="seller", horizon=1)
    buyer, cap10 = _state(role="buyer", horizon=10)
    assert live_percentile._fp_complete_signal(seller, single) == {
        "cell": "single/seller", "role": "seller"}
    assert live_percentile._fp_complete_signal(buyer, cap10) == {
        "cell": "cap10/buyer", "role": "buyer"}

    _seat, hidden = _state(role="seller", horizon=1, complete=False)
    assert live_percentile._fp_complete_signal(seller, hidden) is None
    _seat, wrong_role = _state(role="buyer", horizon=1)
    assert live_percentile._fp_complete_signal(buyer, wrong_role) is None


def test_exposure_is_fixed_at_the_first_own_turn_before_action_outcome():
    gid = _gid(True)
    seat, state = _state(role="buyer", horizon=10)
    rec = {
        "ts": 123.0,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "action_type": "decision",
        "state": state,
        "action": {"decision": "RejectOffer", "product_price": 80.01},
    }
    assert live_percentile._fp_complete_exposure_turn("randomized", rec) == (
        ("randomized", gid), 123.0,
        {"cell": "cap10/buyer", "role": "buyer"},
    )
    rec["action_type"] = "offer"
    assert live_percentile._fp_complete_exposure_turn("randomized", rec) is None


def test_terminal_row_uses_exact_official_seed_scorer(monkeypatch):
    gid = _gid(False)
    seat, state = _state(role="seller", horizon=1)
    called = {}

    def exact_score(actual_state, actual_seat, payoff):
        called.update(state=actual_state, seat=actual_seat, payoff=payoff)
        return 0.91

    monkeypatch.setattr(
        live_percentile.official_negotiation_seed, "percentile", exact_score)
    final = {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": seat,
        "status": "completed",
        "game_state": state,
        "result": {"outcome": "agreement", "player_1_payoff": 69.99},
    }
    assert live_percentile._fp_complete_row(
        "randomized", {"game_id": gid}, final) == (
            "randomized", 0.91, gid, True,
            {"cell": "single/seller", "role": "seller"},
        )
    assert called == {"state": state, "seat": seat, "payoff": 69.99}


def test_report_keeps_cells_separate_and_prints_exact_delta(capsys):
    control, candidate = _gid(False), _gid(True)
    rows = [
        ("randomized", 0.60, control, True,
         {"cell": "cap10/buyer", "role": "buyer"}, "terminal"),
        ("randomized", 0.90, candidate, True,
         {"cell": "cap10/buyer", "role": "buyer"}, "terminal"),
    ]
    assert live_percentile.report_fp_complete(rows, 24.0) == 0
    output = capsys.readouterr().out
    assert "exact horizon/information/messages/scale/value-pair/role" in output
    assert "cap10/buyer candidate-control" in output
    assert "official-seed percentile: +0.3000" in output
