"""Deterministic, whole-policy buyer-v2 explicit-decline veto tests."""

from __future__ import annotations

import copy
import os
from types import SimpleNamespace

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from glee_agent.text import reads_as_recommendation_expanded
from scripts import check_reachability


FLAG = persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG
_REAL_BUYER_PRIOR_DOC = persuasion._buyer_prior_doc


@pytest.fixture(autouse=True)
def _isolated_persuasion_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_TIGHT_PRIOR", "0.65")
    monkeypatch.setenv("GLEE_PERS_HONEST_ROUNDS", "99")
    monkeypatch.setenv("GLEE_PERS_LIE_SHADING", "0")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _buyer_game(
        message, *, mode: str = "text", p: float = 0.8, v: float = 10.0,
        history: list[dict] | None = None, game_id: str | None = "game-a",
) -> dict:
    game = {
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": {
            "current_player": "player_2",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "product_price": 1.0,
            "p": p,
            "v": v,
            "u": 0.0,
            "seller_message_type": mode,
            "seller_message": message,
            "round": len(history or []) + 1,
            "total_rounds": 20,
            "history": copy.deepcopy(history or []),
        },
    }
    if game_id is not None:
        game["game_id"] = game_id
    return game


def _seller_game() -> dict:
    return {
        "game_id": "seller-game",
        "your_player": "player_1",
        "valid_actions": {"type": "seller_message"},
        "game_state": {
            "current_player": "player_1",
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "product_price": 1.0,
            "p": 0.5,
            "v": 1.2,
            "u": 0.0,
            "current_quality": "low",
            "seller_message_type": "text",
            "round": 2,
            "total_rounds": 20,
            "history": [{
                "round": 1,
                "quality": "low",
                "seller_message": "Not recommended.",
                "buyer_decision": "yes",
                "bought": True,
            }],
        },
    }


def _decide(game: dict) -> dict:
    cfg = SimpleNamespace(pers_lie_shading=0.0, pers_honest_rounds=99)
    return persuasion.decide(copy.deepcopy(game), cfg)


@pytest.mark.parametrize(
    "message",
    [
        "Not recommended.",
        "I recommend skipping this one.",
        "I recommend passing on this product.",
        "I recommend against buying it.",
        "I am advising you to skip.",
        "I am not asking you to buy.",
        "I'd skip this one.",
        "I would skip this one.",
        "Save your cash.",
        "Save your money.",
        "This is not worth what I am asking.",
        "This is not worth what I'm asking.",
    ],
)
def test_whole_text_policy_vetoes_an_existing_buy_on_every_expanded_decline(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    game = _buyer_game(message)
    assert reads_as_recommendation_expanded(message) is False
    assert _decide(game)["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)

    assert on["decision"] == "no"
    assert on["_plan"]["buyer_explicit_decline_veto_v1"] is True
    assert on["_plan"]["gates_fired"] == ["buyer_explicit_decline_veto_v1"]


@pytest.mark.parametrize("message", ["Recommended.", "BOIIIII", None, "", {}, []])
def test_positive_unknown_and_malformed_current_text_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch, message) -> None:
    history = [{
        "round": 1,
        "quality": "low",
        "seller_message": "Not recommended.",
        "buyer_decision": "yes",
        "bought": True,
    }]
    game = _buyer_game(message, history=history)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


def test_expanded_decline_history_does_not_change_the_posterior(
        monkeypatch: pytest.MonkeyPatch) -> None:
    history = [{
        "round": 1,
        "seller_message": "Not recommended.",
        "buyer_decision": "no",
        "bought": False,
    }]
    game = _buyer_game("Recommended.", history=history)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


@pytest.mark.parametrize(
    "message",
    [
        "Inspected this one personally — it's the high-grade unit today. "
        "At this price it's an easy call.",
        "Serviceable unit today. Worth it.",
    ],
)
def test_late_positive_or_unknown_text_cannot_reopen_a_spammer_purchase(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    # Regression from completed game 15cced7b-9a3d-48bc-9414-76e2dc53b7ca:
    # after four bought highs and five bought lows, the live fitted prior makes
    # buyer-v2 refuse.  The rejected broad tri-state implementation reset the
    # current signal/history and changed this state to BUY; the final veto must
    # leave every non-decline state byte-identical.
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", _REAL_BUYER_PRIOR_DOC)
    history = [
        {
            "round": round_no,
            "quality": quality,
            "seller_message": "yes",
            "buyer_decision": "yes",
            "bought": True,
        }
        for round_no, quality in enumerate(
            ["high"] * 4 + ["low"] * 5, start=1)
    ]
    game = _buyer_game(message, p=0.5, v=2.0, history=history)
    off = _decide(game)
    assert off["decision"] == "no"

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


def test_existing_pass_on_a_decline_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game("Not recommended.", p=0.4, v=1.2)
    off = _decide(game)
    assert off["decision"] == "no"
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off
    assert "buyer_explicit_decline_veto_v1" not in on["_plan"]


@pytest.mark.parametrize("message", ["yes", True])
def test_positive_binary_buyer_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, message) -> None:
    game = _buyer_game(message, mode="binary")
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


@pytest.mark.parametrize("message", ["no", False])
def test_strict_binary_decline_vetoes_an_existing_buy(
        monkeypatch: pytest.MonkeyPatch, message) -> None:
    game = _buyer_game(message, mode="binary")
    off = _decide(game)
    assert off["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)

    assert on["decision"] == "no"
    assert on["_plan"]["buyer_explicit_decline_veto_v1"] is True
    assert on["_plan"]["gates_fired"] == [
        "buyer_explicit_decline_veto_v1"]


def test_binary_recommended_false_fallback_vetoes_an_existing_buy(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game(None, mode="binary")
    game["game_state"]["recommended"] = False
    off = _decide(game)
    assert off["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)

    assert on["decision"] == "no"
    assert on["_plan"]["buyer_explicit_decline_veto_v1"] is True


@pytest.mark.parametrize("message", ["Not recommended.", None, "", {}, []])
def test_unknown_binary_wire_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, message) -> None:
    game = _buyer_game(message, mode="binary")
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


def test_seller_is_byte_identical_even_with_a_v2_only_decline_in_history(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _seller_game()
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


def test_legacy_buyer_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game("Not recommended.")
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "0")
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


@pytest.mark.parametrize("scope_break", ["action", "seat", "current_player"])
def test_out_of_contract_buyer_scope_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, scope_break: str) -> None:
    game = _buyer_game("Not recommended.")
    if scope_break == "action":
        game["valid_actions"]["type"] = "unknown_action"
    elif scope_break == "seat":
        game["your_player"] = "player_1"
    else:
        game["game_state"]["current_player"] = "player_1"

    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


def test_veto_is_last_and_cannot_be_revived_by_an_old_overlay(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game("Not recommended.", p=0.4, v=1.2)
    monkeypatch.setattr(persuasion, "_rank_buy_arm", lambda _game: True)

    off = _decide(game)
    assert off["decision"] == "yes"
    assert off["_plan"]["rank_buy_arm"] is True

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on["decision"] == "no"
    assert on["_plan"]["rank_buy_arm"] is True
    assert on["_plan"]["buyer_explicit_decline_veto_v1"] is True
    assert on["_plan"]["gates_fired"] == [
        "rank_buy", "buyer_explicit_decline_veto_v1"]


def test_policy_never_turns_pass_into_buy_across_a_state_grid(
        monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [
        ("Not recommended.", "text"),
        ("I recommend skipping this one.", "text"),
        ("no", "text"),
        ("Recommended.", "text"),
        ("yes", "text"),
        ("BOIIIII", "text"),
        (None, "text"),
        ("no", "binary"),
        (False, "binary"),
        ("yes", "binary"),
        (True, "binary"),
        ("Not recommended.", "binary"),
    ]
    games = [
        _buyer_game(message, mode=mode, p=p, v=v, history=history,
                    game_id=f"{i}-{j}-{k}")
        for i, (message, mode) in enumerate(signals)
        for j, (p, v) in enumerate(((1 / 3, 1.2), (0.5, 2.0), (0.8, 10.0)))
        for k, history in enumerate(([], [{
            "round": 1,
            "quality": "low",
            "seller_message": "yes",
            "buyer_decision": "yes",
            "bought": True,
        }]))
    ]
    off = [_decide(game) for game in games]
    monkeypatch.setenv(FLAG, "1")
    on = [_decide(game) for game in games]

    changed = 0
    for game, control, candidate in zip(games, off, on):
        if control == candidate:
            continue
        changed += 1
        assert control["decision"] == "yes"
        assert candidate["decision"] == "no"
        state = game["game_state"]
        if state["seller_message_type"] == "text":
            assert reads_as_recommendation_expanded(
                state["seller_message"]) is False
        else:
            assert persuasion._strict_binary_signal(state) is False
    assert changed > 0


def test_assignment_is_deterministic_and_does_not_read_game_id(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAG, "1")
    outputs = [
        _decide(_buyer_game("Not recommended.", game_id=game_id))
        for game_id in (None, "game-a", "game-b", "completely-different")
    ]
    assert outputs == [outputs[0]] * len(outputs)
    assert not any("arm" in key or "assignment" in key
                   for key in outputs[0]["_plan"])


def test_contrast_after_a_decline_keeps_the_final_recommendation(
        monkeypatch: pytest.MonkeyPatch) -> None:
    message = (
        "I recommend skipping this one, but this one is high quality and "
        "I recommend it."
    )
    assert reads_as_recommendation_expanded(message) is True
    game = _buyer_game(message)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off


def test_flag_unset_and_explicit_zero_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch) -> None:
    games = [
        _buyer_game("Not recommended."),
        _buyer_game("BOIIIII", p=0.4, v=2.0),
        _buyer_game("Recommended."),
        _buyer_game("yes", mode="binary"),
        _buyer_game("no", mode="binary"),
        _seller_game(),
    ]
    unset = [_decide(game) for game in games]
    monkeypatch.setenv(FLAG, "0")
    explicitly_off = [_decide(game) for game in games]
    assert explicitly_off == unset


def test_flag_off_does_not_consult_the_expanded_parser(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(_message):
        raise AssertionError("default-OFF guard consulted its new parser")

    monkeypatch.setattr(
        persuasion, "reads_as_recommendation_expanded", fail_if_called)
    assert _decide(_buyer_game("Not recommended."))["decision"] == "yes"


@pytest.mark.parametrize(
    ("message", "mode"),
    [
        ("Not recommended.", "text"),
        ("I recommend passing on this product.", "text"),
        ("no", "binary"),
        (False, "binary"),
    ],
)
def test_reachability_registration_matches_the_change_scope(
        message, mode: str) -> None:
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    plan = {"buyer_v2": True, "buy": True}

    assert family == "persuasion"
    assert gates == ("buyer_explicit_decline_veto_v1",)
    assert predicate(_buyer_game(message, mode=mode), plan) is True
    assert predicate(_buyer_game(message, mode=mode), {
        **plan, "buy": False}) is False


@pytest.mark.parametrize(
    ("message", "mode"),
    [
        ("Recommended.", "text"),
        ("BOIIIII", "text"),
        ("yes", "binary"),
        ("Not recommended.", "binary"),
    ],
)
def test_reachability_predicate_rejects_non_declines(
        message, mode: str) -> None:
    predicate = check_reachability.KNOWN[FLAG][2]
    assert predicate(_buyer_game(message, mode=mode), {
        "buyer_v2": True, "buy": True}) is False
