"""Literal-configuration scoring for the complete-information claim arm."""

from __future__ import annotations

from scripts import live_percentile


def _gid(arm: str) -> str:
    for index in range(1000):
        gid = f"open-official-{index}"
        if live_percentile.open_claim_arm(gid) == arm:
            return gid
    raise AssertionError("could not recover both claim arms")


def _state():
    return {
        "current_player": "player_2",
        "horizon_known": False,
        "complete_information": True,
        "messages_allowed": True,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": 80.0,
        "player_2_value": 150.0,
        "round": 1,
    }


def test_exact_signal_is_pre_action_and_preserves_visible_type():
    assert live_percentile._open_claim_official_signal(
        "player_2", _state()) == {
            "cell": "unknown/buyer",
            "role": "buyer",
            "horizon": "unknown",
            "seller_mult": 0.8,
            "buyer_mult": 1.5,
            "messages_allowed": True,
        }

    gid = _gid("candidate")
    rec = {
        "ts": 10.0,
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "state": _state(),
        "action": {"decision": "RejectOffer", "product_price": 94.0},
    }
    key, stamp, signal = live_percentile._open_claim_official_exposure_turn(
        "randomized", rec)
    assert key == ("randomized", gid)
    assert stamp == 10.0
    assert signal["cell"] == "unknown/buyer"
    assert signal["seller_mult"] == 0.8


def test_exact_outcome_never_calls_the_local_pooled_cdf(monkeypatch):
    gid = _gid("control")

    def local_failure(*_args, **_kwargs):
        raise AssertionError("local pooled scorer must not be used")

    monkeypatch.setattr(live_percentile, "percentile", local_failure)
    monkeypatch.setattr(
        live_percentile.official_negotiation_seed, "percentile",
        lambda state, seat, payoff: 0.73,
    )
    final = {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": "player_2",
        "status": "completed",
        "game_state": _state(),
        "result": {"outcome": "agreement", "player_2_payoff": 56.0},
    }
    row = live_percentile._open_claim_official_row(
        "randomized", {"game_id": gid}, final)
    assert row[:4] == ("randomized", 0.73, gid, True)
    assert row[4]["cell"] == "unknown/buyer"


def test_report_exposes_unknown_buyer_seller_type_interaction(capsys):
    control, candidate = _gid("control"), _gid("candidate")
    signal = {
        "cell": "unknown/buyer", "role": "buyer", "horizon": "unknown",
        "seller_mult": 0.8, "buyer_mult": 1.5,
        "messages_allowed": False,
    }
    rows = [
        ("randomized", 0.20, control, True, signal, "terminal"),
        ("randomized", 0.60, candidate, True, signal, "terminal"),
    ]
    assert live_percentile.report_open_claim_official(rows, 24.0) == 0
    output = capsys.readouterr().out
    assert "unknown/buyer S0.8 candidate-control" in output
    assert "official-seed percentile: +0.4000" in output
    assert "never condition the score comparison on agreement" in output
