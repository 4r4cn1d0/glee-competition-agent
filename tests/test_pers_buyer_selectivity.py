"""Focused reachability and safety tests for the buyer-selectivity A/B arm."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion


@pytest.fixture(autouse=True)
def _isolated_buyer(monkeypatch: pytest.MonkeyPatch):
    """Keep tests independent of live overlays and the refittable prior file."""
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(
    game_id: str,
    *,
    message: str = "yes",
    history: list[dict] | None = None,
    p: float = 0.8,
    v: float = 1.2,
    u: float = 0.0,
    price: float = 1.0,
    total_rounds: int = 20,
) -> dict:
    history = copy.deepcopy(history or [])
    return {
        "game_id": game_id,
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "product_price": price,
            "p": p,
            "v": v,
            "u": u,
            "round": len(history) + 1,
            "total_rounds": total_rounds,
            "seller_message": message,
            "seller_message_type": "binary",
            "history": history,
        },
    }


def _game_id(candidate: bool, *, strike: bool | None = None) -> str:
    for index in range(1000):
        game_id = f"selectivity-test-{index}"
        if (persuasion.buyer_selectivity_assignment(game_id) is candidate
                and (strike is None
                     or persuasion.buyer_selectivity_strike_assignment(
                         game_id) is strike)):
            return game_id
    raise AssertionError(
        f"could not find assignment bits candidate={candidate}, strike={strike}")


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), None)


def test_flag_default_off_is_byte_for_byte_inert(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(_game_id(True))

    unset = _decide(game)
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "0")
    explicitly_off = _decide(game)

    assert unset == explicitly_off
    assert unset["decision"] == "yes"
    assert "buyer_selectivity_arm" not in unset["_plan"]


def test_assignment_is_stable_and_enabled_control_is_inert(
        monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = _game_id(True)
    control_id = _game_id(False)

    assert persuasion.buyer_selectivity_assignment(candidate_id) is True
    assert persuasion.buyer_selectivity_assignment(candidate_id) is True
    assert persuasion.buyer_selectivity_assignment(control_id) is False
    assert persuasion.buyer_selectivity_assignment(None) is None
    assert persuasion.buyer_selectivity_assignment("") is None

    control_game = _game(control_id)
    control_off = _decide(control_game)
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    control_on = _decide(control_game)

    assert control_on["decision"] == control_off["decision"] == "yes"
    assert control_on["_plan"]["buyer_selectivity_arm"] == "control"
    # Arm metadata is the only permitted control-side change.
    assert {
        key: value for key, value in control_on["_plan"].items()
        if not key.startswith("buyer_selectivity_")
    } == control_off["_plan"]


def test_strike_assignment_is_independent_and_flag_default_off(
        monkeypatch: pytest.MonkeyPatch) -> None:
    strike_id = _game_id(True, strike=True)
    no_strike_id = _game_id(True, strike=False)
    control_strike_id = _game_id(False, strike=True)
    control_no_strike_id = _game_id(False, strike=False)

    assert persuasion.buyer_selectivity_strike_assignment(strike_id) is True
    assert persuasion.buyer_selectivity_strike_assignment(no_strike_id) is False
    assert persuasion.buyer_selectivity_strike_assignment(None) is None
    assert persuasion.buyer_selectivity_strike_assignment("") is None

    history = [
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": True, "quality": "low"},
    ]
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    strike_off = _decide(_game(strike_id, history=history))
    assert strike_off["decision"] == "yes"
    assert strike_off["_plan"]["buyer_selectivity_strike_arm"] == "off"

    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB", "1")
    no_strike = _decide(_game(no_strike_id, history=history))
    strike = _decide(_game(strike_id, history=history))
    control_no_strike = _decide(_game(control_no_strike_id, history=history))
    control_strike = _decide(_game(control_strike_id, history=history))
    assert no_strike["decision"] == "yes"
    assert no_strike["_plan"]["buyer_selectivity_strike_arm"] == "no-strike"
    assert strike["decision"] == "no"
    assert strike["_plan"]["buyer_selectivity_strike_arm"] == "strike"
    assert strike["_plan"]["buyer_selectivity_veto"] == "bought_low_strike"
    assert control_no_strike["decision"] == control_strike["decision"] == "yes"
    assert control_no_strike["_plan"]["buyer_selectivity_strike_arm"] == (
        "no-strike")
    assert control_strike["_plan"]["buyer_selectivity_strike_arm"] == "strike"


def test_candidate_vetoes_without_a_prior_decline(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(_game_id(True))
    assert _decide(game)["decision"] == "yes"

    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")
    candidate = _decide(game)

    assert candidate["decision"] == "no"
    assert candidate["_plan"]["buyer_selectivity_arm"] == "candidate"
    assert candidate["_plan"]["buyer_selectivity_veto"] == "no_prior_decline"
    assert candidate["_plan"]["buyer_selectivity_declines"] == 0
    assert candidate["_plan"]["gates_fired"] == ["buyer_selectivity"]


def test_prior_equality_is_eligible_not_treated_as_positive_ev(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(_game_id(True), p=0.8, v=1.25)
    assert game["game_state"]["p"] * game["game_state"]["v"] == pytest.approx(1.0)
    assert _decide(game)["decision"] == "yes"

    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    candidate = _decide(game)

    assert candidate["decision"] == "no"
    assert candidate["_plan"]["buyer_selectivity_prior_value"] == pytest.approx(1.0)
    assert candidate["_plan"]["buyer_selectivity_veto"] == "no_prior_decline"


@pytest.mark.parametrize("p,v", [(0.8, 2.0), (0.5, 4.0), (1 / 3, 4.0)])
def test_prior_positive_cells_are_byte_for_byte_untouched(
        monkeypatch: pytest.MonkeyPatch, p: float, v: float) -> None:
    game = _game(_game_id(True), p=p, v=v)
    assert game["game_state"]["p"] * game["game_state"]["v"] > 1.0
    off = _decide(game)

    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    on = _decide(game)

    assert on == off
    assert on["decision"] == "yes"
    assert "buyer_selectivity_arm" not in on["_plan"]


def test_eligibility_uses_full_prior_value_when_low_value_is_nonzero(
        monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = _game_id(True)
    # Looking only at p*v would call this equality.  The low outcome is worth
    # .5, so the true prior value is 1.25 and the arm must never be consulted.
    positive = _game(candidate_id, p=0.5, v=2.0, u=0.5)
    off = _decide(positive)
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    on = _decide(positive)
    assert on == off
    assert "buyer_selectivity_arm" not in on["_plan"]

    # This neighboring state has prior value .8 and remains eligible.
    eligible = _decide(_game(candidate_id, p=0.2, v=2.0, u=0.5))
    assert eligible["_plan"]["buyer_selectivity_arm"] == "candidate"
    assert eligible["_plan"]["buyer_selectivity_prior_value"] == pytest.approx(0.8)


@pytest.mark.parametrize("parse_tri", ["0", "1"])
def test_current_message_must_be_explicit_yes_independent_of_legacy_parser(
        monkeypatch: pytest.MonkeyPatch, parse_tri: str) -> None:
    # Legacy mode coerces unreadable text to a recommendation.  The safety arm
    # must use the tri-state signal directly even when that legacy mode is live.
    history = [{"seller_message": "no", "bought": False}]
    game = _game(_game_id(True), message="This is a product.", history=history)
    assert persuasion._recommendation_signal(
        {"seller_message": game["game_state"]["seller_message"]}) is None

    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", parse_tri)
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    candidate = _decide(game)

    assert candidate["decision"] == "no"
    assert candidate["_plan"]["buyer_selectivity_p_high"] == pytest.approx(0.8)
    if parse_tri == "0":
        # The legacy control would buy the unreadable string, so the arm owns
        # the changed action and records its reason.
        assert candidate["_plan"]["buyer_selectivity_veto"] == (
            "current_not_explicit_yes")
    else:
        # The tri-state control already refuses an abstention.  This overlay is
        # veto-only and therefore records no redundant action change.
        assert candidate["_plan"]["parser_abstained"] is True
        assert "buyer_selectivity_veto" not in candidate["_plan"]


def test_treatment_posterior_preserves_historical_parser_abstentions(
        monkeypatch: pytest.MonkeyPatch) -> None:
    history = [
        {"seller_message": "no", "bought": False},
        {"seller_message": "This is a product.", "bought": False},
    ]
    game = _game(_game_id(True), message="yes", history=history)
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")

    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", "0")
    legacy_stack = _decide(game)
    monkeypatch.setenv("GLEE_PERS_PARSE_TRI", "1")
    tri_stack = _decide(game)

    assert legacy_stack["_plan"]["p_high"] != pytest.approx(
        tri_stack["_plan"]["p_high"])
    assert legacy_stack["_plan"]["buyer_selectivity_p_high"] == pytest.approx(
        tri_stack["_plan"]["buyer_selectivity_p_high"])


def test_prior_decline_unlocks_only_when_posterior_strictly_clears(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(
        _game_id(True),
        history=[{"seller_message": "no", "bought": False}],
    )
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")

    clears = _decide(game)
    assert clears["_plan"]["p_high"] > clears["_plan"]["breakeven"]
    assert clears["decision"] == "yes"
    assert "buyer_selectivity_veto" not in clears["_plan"]

    # Put all posterior mass on an indiscriminate q=1 seller.  A prior decline
    # alone must not override the now-unprofitable recommendation posterior.
    monkeypatch.setattr(
        persuasion, "_q_posterior", lambda *_args, **_kwargs: [0, 0, 0, 0, 0, 1])
    fails = _decide(game)
    assert fails["_plan"]["buyer_selectivity_p_high"] < fails["_plan"]["breakeven"]
    assert fails["_plan"]["buyer_selectivity_posterior_gap"] < 0
    assert fails["decision"] == "no"
    # The base posterior rejects this state too; a veto-only overlay does not
    # claim an action change it did not make.
    assert "buyer_selectivity_veto" not in fails["_plan"]


def test_positive_margin_can_veto_an_otherwise_profitable_posterior(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(
        _game_id(True),
        history=[{"seller_message": "no", "bought": False}],
    )
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    # q=0 makes an explicit yes maximally informative: p_high=1 and the gap
    # over the 5/6 breakeven threshold is 1/6.
    monkeypatch.setattr(
        persuasion, "_q_posterior", lambda *_args, **_kwargs: [1, 0, 0, 0, 0, 0])

    no_margin = _decide(game)
    assert no_margin["decision"] == "yes"
    assert no_margin["_plan"]["buyer_selectivity_posterior_gap"] == pytest.approx(1 / 6)

    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_MARGIN", "0.20")
    margin = _decide(game)
    assert margin["decision"] == "no"
    assert margin["_plan"]["buyer_selectivity_veto"] == (
        "posterior_not_strictly_profitable")


def test_any_bought_low_is_a_permanent_strike(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _game(
        _game_id(True, strike=True),
        history=[
            {"seller_message": "no", "bought": False},
            {"seller_message": "yes", "bought": True, "quality": "low"},
        ],
    )
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB", "1")
    # Even a maximally favorable posterior cannot reopen buying after the loss.
    monkeypatch.setattr(
        persuasion, "_q_posterior", lambda *_args, **_kwargs: [1, 0, 0, 0, 0, 0])

    candidate = _decide(game)

    assert candidate["_plan"]["p_high"] > candidate["_plan"]["breakeven"]
    assert candidate["decision"] == "no"
    assert candidate["_plan"]["buyer_selectivity_caught_low"] is True
    assert candidate["_plan"]["buyer_selectivity_veto"] == "bought_low_strike"


def test_decline_once_then_nineteen_lows_costs_at_most_one_purchase(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_AB", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB", "1")
    game_id = _game_id(True, strike=True)
    history = [{"seller_message": "no", "bought": False}]
    decisions = []

    for _round in range(2, 21):
        result = _decide(_game(game_id, history=history))
        bought = result["decision"] == "yes"
        decisions.append(bought)
        entry = {"seller_message": "yes", "bought": bought}
        if bought:
            entry["quality"] = "low"
        history.append(entry)

    assert decisions[0] is True, "the decline must make the treatment reachable"
    assert sum(decisions) == 1
    assert all(not bought for bought in decisions[1:])
