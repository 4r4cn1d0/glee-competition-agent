"""Safety tests for the deterministic buyer selective-signal unlock."""

from __future__ import annotations

import copy
import math
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from scripts import check_reachability


FLAG = "GLEE_PERS_BUYER_SELECTIVE_SIGNAL_UNLOCK_V1"
GATE = "buyer_selective_signal_unlock_v1"


@pytest.fixture(autouse=True)
def _isolated_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_TIGHT_PRIOR", "0.65")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(
    *,
    game_id: str = "selective-signal-unlock",
    p: float = 0.5,
    ratio: float = 1.2,
    mode: str = "text",
    declines: int = 2,
    current=None,
    knowledge=True,
    scale: float = 100.0,
) -> dict:
    if current is None:
        current = "yes" if mode == "text" else True
    decline = "no" if mode == "text" else False
    state = {
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "product_price": scale,
        "p": p,
        "v": ratio * scale,
        "u": 0.0,
        "seller_message_type": mode,
        "seller_message": current,
        "round": declines + 1,
        "total_rounds": 20,
        "history": [
            {"seller_message": decline, "bought": False}
            for _ in range(declines)
        ],
    }
    if knowledge is not None:
        state["is_seller_know_cv"] = knowledge
    return {
        "game_id": game_id,
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": state,
    }


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), None)


def _fake_plan(*, expected: float = 103.0, buy: bool = False, **extra) -> dict:
    return {
        "price": 100.0,
        "p": 0.5,
        "v": 120.0,
        "u": 0.0,
        "recommended": True,
        "p_high": expected / 120.0,
        "expected_value": expected,
        "q_posterior": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "observed_rounds": 0,
        "caught_lies": 0,
        "breakeven": 5.0 / 6.0,
        "tight": True,
        "blocked": True,
        "exploration_bonus": 0.0,
        "round": 3,
        "total_rounds": 20,
        "buyer_v2": True,
        "buy": buy,
        **extra,
    }


def _assert_unannotated(action: dict) -> None:
    assert GATE not in action["_plan"]
    assert GATE not in action["_plan"].get("gates_fired", [])


def test_default_off_and_explicit_zero_are_byte_identical() -> None:
    game = _game()
    unset = _decide(game)
    os.environ[FLAG] = "0"
    explicitly_off = _decide(game)
    assert unset == explicitly_off
    assert unset["decision"] == "no"
    _assert_unannotated(unset)


@pytest.mark.parametrize(
    "p,ratio,declines,mode,knowledge,scale",
    [
        (0.5, 1.2, 2, "binary", True, 100.0),
        (0.5, 1.25, 2, "text", False, 10_000.0),
        (1.0 / 3.0, 1.25, 3, "binary", None, 1_000_000.0),
        (1.0 / 3.0, 1.2, 4, "text", True, 100.0),
    ],
)
def test_broad_config_general_policy_unlocks_only_posterior_proved_passes(
    p: float, ratio: float, declines: int, mode: str,
    knowledge, scale: float,
) -> None:
    game = _game(
        p=p, ratio=ratio, declines=declines, mode=mode,
        knowledge=knowledge, scale=scale,
    )
    off = _decide(game)
    assert off["decision"] == "no"
    assert off["_plan"]["blocked"] is True
    assert off["_plan"]["expected_value"] > off["_plan"]["price"]

    os.environ[FLAG] = "1"
    on = _decide(game)
    assert on["decision"] == "yes"
    assert on["_plan"][GATE] is True
    assert on["_plan"][f"{GATE}_prior_declines"] == declines
    assert on["_plan"][f"{GATE}_posterior_edge"] > 0.0
    assert on["_plan"]["gates_fired"] == [GATE]

    expected = copy.deepcopy(off)
    expected["decision"] = "yes"
    expected["_plan"]["buy"] = True
    expected["_plan"][GATE] = True
    expected["_plan"][f"{GATE}_prior_declines"] = declines
    expected["_plan"][f"{GATE}_expected_value"] = off["_plan"][
        "expected_value"]
    expected["_plan"][f"{GATE}_posterior_edge"] = (
        off["_plan"]["expected_value"] - off["_plan"]["price"])
    expected["_plan"]["gates_fired"] = [GATE]
    assert on == expected


def test_policy_is_game_id_invariant() -> None:
    os.environ[FLAG] = "1"
    left = _decide(_game(game_id="left"))
    right = _decide(_game(game_id="right"))
    left_plan = left["_plan"]
    right_plan = right["_plan"]
    assert left == right
    assert left_plan[GATE] is True and right_plan[GATE] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda game: game.update(your_player="player_1"),
        lambda game: game["valid_actions"].update(type="seller_message"),
        lambda game: game["game_state"].update(player_2_role="seller"),
        lambda game: game["game_state"].update(current_player="player_1"),
        lambda game: game["game_state"].update(seller_message_type="unknown"),
    ],
)
def test_wrong_role_action_or_mode_fails_closed(mutate) -> None:
    game = _game()
    plan = _fake_plan()
    mutate(game)
    os.environ[FLAG] = "1"
    assert persuasion._buyer_selective_signal_unlock_v1_trigger(
        game, plan) is None


@pytest.mark.parametrize(
    "game",
    [
        _game(declines=0),
        _game(current="I have thoughts."),
        _game(current="no"),
        _game(current="This is an absolute trap."),
    ],
)
def test_no_proof_or_nonpositive_current_message_is_byte_identical(
    game: dict,
) -> None:
    off = _decide(game)
    os.environ[FLAG] = "1"
    assert _decide(game) == off
    _assert_unannotated(off)


def test_expanded_historical_decline_counts_as_observable_selectivity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(declines=0)
    game["game_state"]["history"] = [
        {"seller_message": "Not recommended.", "bought": False},
        {"seller_message": "I would hold off on this one.", "bought": False},
    ]
    game["game_state"]["round"] = 3
    # The live legacy posterior deliberately treats "Not recommended." as an
    # abstention/recommendation.  Isolate the unlock's stricter evidence reader
    # here; the production rule still requires its control posterior to clear.
    monkeypatch.setattr(
        persuasion, "buyer_plan_v2", lambda _game, _cfg: _fake_plan())
    os.environ[FLAG] = "1"
    action = _decide(game)
    assert action["decision"] == "yes"
    assert action["_plan"][f"{GATE}_prior_declines"] == 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"buy": True},
        {"buyer_v2": False},
        {"tight": False},
        {"blocked": False},
        {"expected": 100.0},
        {"expected": 100.0 + 5e-8},
        {"expected": math.nan},
    ],
)
def test_never_overrides_nonmatching_control_plan(
    monkeypatch: pytest.MonkeyPatch, overrides: dict,
) -> None:
    game = _game()
    monkeypatch.setattr(
        persuasion, "buyer_plan_v2", lambda _game, _cfg: _fake_plan(**overrides))
    off = _decide(game)
    os.environ[FLAG] = "1"
    on = _decide(game)
    if math.isnan(overrides.get("expected", 0.0)):
        assert on["decision"] == off["decision"] == "no"
        assert math.isnan(on["_plan"]["expected_value"])
        assert math.isnan(off["_plan"]["expected_value"])
    else:
        assert on == off
    _assert_unannotated(on)


@pytest.mark.parametrize(
    "name,value",
    [
        ("GLEE_PERS_BUYER_GUARD", "0.1"),
        ("GLEE_PERS_BUYER_STRIKE", "1"),
        ("GLEE_PERS_BUYER_LCB", "0.1"),
        ("GLEE_PERS_RANK_GATE_AB", "1"),
        ("GLEE_PERS_RANK_BUY_AB", "1"),
        ("GLEE_PERS_BUYER_SELECTIVITY_AB", "1"),
        ("GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB", "1"),
        ("GLEE_PERS_BUYER_SELECTIVITY_MARGIN", "0.1"),
        ("GLEE_PERS_UNINFORMED_VETO", "0.1"),
        ("GLEE_PERS_PARSE_TRI", "1"),
        ("GLEE_PERS_PARSE_V2", "1"),
        ("GLEE_PERS_P05_R12_SELECTIVITY_UNLOCK_AB", "1"),
    ],
)
def test_conflicting_optional_buyer_paths_fail_closed(
    name: str, value: str,
) -> None:
    game = _game()
    os.environ[name] = value
    conflict_control = _decide(game)
    os.environ[FLAG] = "1"
    assert _decide(game) == conflict_control
    _assert_unannotated(conflict_control)


def test_live_v1_v2_v3_decline_veto_stack_is_compatible() -> None:
    game = _game()
    os.environ["GLEE_PERS_BUYER_EXPLICIT_DECLINE_VETO_V1"] = "1"
    os.environ["GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2"] = "1"
    os.environ["GLEE_PERS_BUYER_EXPLICIT_DECLINE_V3"] = "1"
    off = _decide(game)
    os.environ[FLAG] = "1"
    on = _decide(game)
    assert off["decision"] == "no"
    assert on["decision"] == "yes"
    assert on["_plan"]["gates_fired"] == [GATE]


def test_reachability_registry_matches_real_trigger() -> None:
    game = _game()
    control = _decide(game)["_plan"]
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    assert family == "persuasion"
    assert gates == (GATE,)
    assert predicate(game, control)
    game["game_state"]["history"] = []
    assert not predicate(game, control)
