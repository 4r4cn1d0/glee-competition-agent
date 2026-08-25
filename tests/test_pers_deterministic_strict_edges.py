"""Deterministic strict-edge persuasion policy tests."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.dispatch import make_strategy
from glee_agent.strategies import persuasion
from scripts import check_reachability


TRUTH_FLAG = persuasion.PERS_ZERO_MARGIN_TRUTH_V1_FLAG
PROSE_FLAG = persuasion.PERS_P08_POSITIVE_PROSE_V1_FLAG


@pytest.fixture(autouse=True)
def _isolated_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_MODE"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_TIGHT_PRIOR", "0.65")
    monkeypatch.setenv("GLEE_PERS_MSG_STYLE", "token")
    monkeypatch.setenv("GLEE_PERS_KEEP_MSG", "1")
    monkeypatch.setenv("GLEE_PERS_HONEST_ROUNDS", "99")
    monkeypatch.setenv("GLEE_PERS_LIE_SHADING", "0")
    monkeypatch.setenv("GLEE_LLM_MODE", "off")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _seller_game(
        *, game_id: str | None = "strict-edge", mode: str = "binary",
        quality: str = "low", price: float = 100.0, prior: float = 0.8,
        high_value: float | None = 125.0, low_value: float | None = 0.0,
        round_no: int = 1) -> dict:
    action_type = "seller_recommendation" if mode == "binary" else "seller_message"
    return {
        "game_id": game_id,
        "game_family": "persuasion",
        "your_player": "player_1",
        "valid_actions": {"type": action_type},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "current_player": "player_1",
            "current_quality": quality,
            "product_price": price,
            "p": prior,
            "v": high_value,
            "u": low_value,
            "round": round_no,
            "total_rounds": 20,
            "seller_message_type": mode,
            "is_seller_know_cv": high_value is not None,
            "history": [],
        },
    }


def _buyer_game(message: str) -> dict:
    return {
        "game_id": "strict-edge-buyer",
        "game_family": "persuasion",
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "current_player": "player_2",
            "product_price": 1.0,
            "p": 0.8,
            "v": 10.0,
            "u": 0.0,
            "seller_message_type": "text",
            "seller_message": message,
            "round": 1,
            "total_rounds": 20,
            "history": [],
        },
    }


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), Config.from_env())


@pytest.mark.parametrize(
    ("prior", "high_value"),
    [(0.8, 125.0), (0.5, 200.0), (1.0 / 3.0, 300.0)],
)
@pytest.mark.parametrize("price", [100.0, 10_000.0, 1_000_000.0])
def test_zero_margin_truth_declines_low_across_exact_equality_cells_and_scales(
        monkeypatch: pytest.MonkeyPatch, prior: float, high_value: float,
        price: float) -> None:
    game = _seller_game(
        price=price, prior=prior, high_value=high_value * price / 100.0)
    off = _decide(game)
    assert off["decision"] == "yes"

    monkeypatch.setenv(TRUTH_FLAG, "1")
    on = _decide(game)

    assert on["decision"] == "no"
    assert on["_plan"]["zero_margin_truth_v1"] is True
    assert on["_plan"]["gates_fired"] == ["pers_zero_margin_truth_v1"]
    assert make_strategy(Config.from_env())(copy.deepcopy(game))["decision"] == "no"


def test_zero_margin_truth_preserves_high_and_non_equality_cells(
        monkeypatch: pytest.MonkeyPatch) -> None:
    games = [
        _seller_game(quality="high"),
        _seller_game(high_value=150.0),
        _seller_game(high_value=120.0),
        _seller_game(high_value=None, low_value=None),
    ]
    controls = [_decide(game) for game in games]
    monkeypatch.setenv(TRUTH_FLAG, "1")
    assert [_decide(game) for game in games] == controls


def test_zero_margin_truth_uses_no_game_assignment(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TRUTH_FLAG, "1")
    outputs = []
    for game_id in (None, "a", "b", "different"):
        outputs.append(_decide(_seller_game(game_id=game_id)))
    assert outputs == [outputs[0]] * len(outputs)
    assert not any("arm" in key or "assignment" in key
                   for key in outputs[0]["_plan"])


def test_positive_prose_changes_only_p08_positive_text_wire(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _seller_game(mode="text", quality="high")
    off = _decide(game)
    assert off["message"] == "yes"

    monkeypatch.setenv(PROSE_FLAG, "1")
    on = _decide(game)

    assert on["message"] == "I recommend this one."
    assert on["_plan"]["recommend"] is True
    assert on["_plan"]["p08_positive_prose_v1"] is True
    assert on["_plan"]["gates_fired"] == ["pers_p08_positive_prose_v1"]
    assert make_strategy(Config.from_env())(copy.deepcopy(game))["message"] == on["message"]


def test_positive_prose_preserves_negative_other_prior_and_binary(
        monkeypatch: pytest.MonkeyPatch) -> None:
    games = [
        _seller_game(mode="text", quality="low", high_value=120.0),
        _seller_game(mode="text", quality="high", prior=0.5),
        _seller_game(mode="binary", quality="high"),
    ]
    controls = [_decide(game) for game in games]
    assert controls[0]["message"] == "no"
    monkeypatch.setenv(PROSE_FLAG, "1")
    assert [_decide(game) for game in games] == controls


def test_three_deterministic_components_compose_without_cross_role_leakage(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TRUTH_FLAG, "1")
    monkeypatch.setenv(PROSE_FLAG, "1")
    monkeypatch.setenv(persuasion.PERS_BUYER_EXPLICIT_DECLINE_V2_FLAG, "1")

    low = _decide(_seller_game(mode="text", quality="low"))
    high = _decide(_seller_game(mode="text", quality="high"))
    buyer = _decide(_buyer_game(
        "Sit this round out; the next product may be worth it."))

    assert low["message"] == "no"
    assert low["_plan"]["gates_fired"] == ["pers_zero_margin_truth_v1"]
    assert high["message"] == "I recommend this one."
    assert high["_plan"]["gates_fired"] == ["pers_p08_positive_prose_v1"]
    assert buyer["decision"] == "no"
    assert buyer["_plan"]["gates_fired"] == ["buyer_explicit_decline_v2"]


def test_reachability_registration_matches_deterministic_scopes() -> None:
    truth_family, truth_gates, truth_predicate = check_reachability.KNOWN[TRUTH_FLAG]
    prose_family, prose_gates, prose_predicate = check_reachability.KNOWN[PROSE_FLAG]

    assert truth_family == prose_family == "persuasion"
    assert truth_gates == ("pers_zero_margin_truth_v1",)
    assert prose_gates == ("pers_p08_positive_prose_v1",)
    assert truth_predicate(_seller_game(), {"recommend": True}) is True
    assert truth_predicate(
        _seller_game(high_value=150.0), {"recommend": True}) is False
    assert prose_predicate(
        _seller_game(mode="text", quality="high"), {"recommend": True}) is True
    assert prose_predicate(
        _seller_game(mode="binary", quality="high"), {"recommend": True}) is False
