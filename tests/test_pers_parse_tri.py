"""Regression tests for buyer-side tri-state seller-message handling."""

from __future__ import annotations

import copy

import pytest

from glee_agent.strategies import persuasion
from glee_agent.text import reads_as_recommendation


def _buyer_game(message: str, *, p: float, v: float) -> dict:
    return {
        "game_state": {
            "product_price": 1.0,
            "p": p,
            "v": v,
            "u": 0.0,
            "round": 1,
            "total_rounds": 1,
            "seller_message": message,
            "seller_message_type": "text",
            "history": [],
        },
        "valid_actions": {"type": "buyer_decision"},
    }


def _configure_buyer_v2(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep the test independent of live arm overlays and the refittable prior
    # artifact; the uniform fallback still reproduces the original coercion.
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)


def test_parser_abstention_uses_prior_and_does_not_buy_below_breakeven(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_buyer_v2(monkeypatch)
    message = "BOIIIII"
    game = _buyer_game(message, p=0.4, v=2.0)

    assert reads_as_recommendation(message) is None
    assert game["game_state"]["p"] < 1.0 / game["game_state"]["v"]

    monkeypatch.delenv("GLEE_PERS_PARSE_TRI", raising=False)
    unset = persuasion.decide(copy.deepcopy(game), None)
    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", "0")
    explicitly_off = persuasion.decide(copy.deepcopy(game), None)

    # The new flag is inert by default; this is the original bad purchase.
    assert unset == explicitly_off
    assert unset["decision"] == "yes"

    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", "1")
    fixed = persuasion.decide(copy.deepcopy(game), None)

    assert fixed["decision"] == "no"
    assert fixed["_plan"]["recommended"] is None
    assert fixed["_plan"]["p_high"] == pytest.approx(0.4)
    assert fixed["_plan"]["expected_value"] == pytest.approx(0.8)
    assert fixed["_plan"]["parser_prior_below_breakeven"] is True


def test_explicit_decline_is_a_hard_veto(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_buyer_v2(monkeypatch)
    game = _buyer_game("no", p=0.8, v=10.0)
    assert reads_as_recommendation("no") is False

    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", "0")
    assert persuasion.decide(copy.deepcopy(game), None)["decision"] == "yes"

    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", "1")
    fixed = persuasion.decide(copy.deepcopy(game), None)
    assert fixed["decision"] == "no"
    assert fixed["_plan"]["parser_decline_veto"] is True
