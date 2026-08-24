"""Focused safety tests for the exact p=.5/r=1.2 buyer unlock arm."""

from __future__ import annotations

import copy
import math
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from scripts import check_reachability


FLAG = "GLEE_PERS_P05_R12_SELECTIVITY_UNLOCK_AB"
GATE = "p05_r12_selectivity_unlock"


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


def _gid(candidate: bool) -> str:
    for index in range(2000):
        game_id = f"p05-r12-unlock-{index}"
        if persuasion.p05_r12_selectivity_unlock_assignment(game_id) is candidate:
            return game_id
    raise AssertionError("assignment not found")


def _game(
    game_id: str,
    *,
    mode: str = "text",
    declines: int = 2,
    current=None,
    knowledge=True,
) -> dict:
    if current is None:
        current = "yes" if mode == "text" else True
    historical_decline = "no" if mode == "text" else False
    history = [
        {"seller_message": historical_decline, "bought": False}
        for _ in range(declines)
    ]
    state = {
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "product_price": 100.0,
        "p": 0.5,
        "v": 120.0,
        "u": 0.0,
        "seller_message_type": mode,
        "seller_message": current,
        "round": declines + 1,
        "total_rounds": 20,
        "history": history,
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


def _assert_unannotated(action: dict) -> None:
    plan = action["_plan"]
    assert all(not key.startswith("p05_r12_selectivity_unlock") for key in plan)
    assert GATE not in plan.get("gates_fired", [])


def _fake_plan(*, expected: float = 101.0, buy: bool = False, **extra) -> dict:
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


def test_flag_default_off_and_explicit_zero_are_byte_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True))
    unset = _decide(game)
    monkeypatch.setenv(FLAG, "0")
    explicitly_off = _decide(game)
    assert unset == explicitly_off
    assert unset["decision"] == "no"
    _assert_unannotated(unset)


def test_hash_control_is_byte_identical_to_flag_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(False))
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off
    _assert_unannotated(on)


@pytest.mark.parametrize(
    "game",
    [
        pytest.param(_game(_gid(True), declines=0), id="no-decline"),
        pytest.param(_game(_gid(True), declines=1), id="ev-below-price"),
        pytest.param(_game(_gid(True), current="I have thoughts."),
                     id="ambiguous-current"),
        pytest.param({**_game(""), "game_id": ""}, id="missing-id"),
    ],
)
def test_nontriggering_candidates_are_byte_identical_and_unannotated(
    monkeypatch: pytest.MonkeyPatch, game: dict,
) -> None:
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off
    _assert_unannotated(on)


def test_candidate_changes_only_pass_to_buy_and_records_exact_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True))
    off = _decide(game)
    assert off["decision"] == "no"
    assert off["_plan"]["buyer_v2"] is True
    assert off["_plan"]["tight"] is True
    assert off["_plan"]["blocked"] is True
    assert off["_plan"]["expected_value"] > off["_plan"]["price"]

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on["decision"] == "yes"
    assert on["_plan"][GATE] is True
    assert on["_plan"][f"{GATE}_prior_declines"] == 2
    assert on["_plan"][f"{GATE}_expected_value"] == pytest.approx(
        off["_plan"]["expected_value"])
    assert on["_plan"]["gates_fired"] == [GATE]
    expected = copy.deepcopy(off)
    expected["decision"] = "yes"
    expected["_plan"]["buy"] = True
    expected["_plan"][GATE] = True
    expected["_plan"][f"{GATE}_prior_declines"] = 2
    expected["_plan"][f"{GATE}_expected_value"] = off["_plan"][
        "expected_value"]
    expected["_plan"]["gates_fired"] = [GATE]
    assert on == expected


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda game: game.update(your_player="player_1"),
                     id="wrong-seat"),
        pytest.param(lambda game: game["valid_actions"].update(type="decision"),
                     id="wrong-action-type"),
        pytest.param(lambda game: game["game_state"].update(
            player_2_role="seller"), id="wrong-role"),
        pytest.param(lambda game: game["game_state"].update(
            current_player="player_1"), id="wrong-current-player"),
        pytest.param(lambda game: game["game_state"].update(p=0.50001),
                     id="wrong-prior"),
        pytest.param(lambda game: game["game_state"].update(v=125.0),
                     id="wrong-ratio"),
        pytest.param(lambda game: game["game_state"].update(u=0.01),
                     id="wrong-low-value"),
        pytest.param(lambda game: game["game_state"].update(total_rounds=10),
                     id="wrong-horizon"),
        pytest.param(lambda game: game["game_state"].update(total_rounds=20.5),
                     id="noninteger-horizon"),
        pytest.param(lambda game: game["game_state"].update(
            seller_message_type="prose"), id="wrong-mode"),
    ],
)
def test_exact_structural_scope_fails_closed(
    monkeypatch: pytest.MonkeyPatch, mutate,
) -> None:
    game = _game(_gid(True))
    mutate(game)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off
    _assert_unannotated(on)


def test_reachability_registry_matches_exact_structural_scope() -> None:
    game = _game(_gid(True))
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    assert family == "persuasion"
    assert gates == (GATE,)
    assert predicate(game, _fake_plan())
    game["game_state"]["p"] = 0.8
    assert not predicate(game, _fake_plan())


@pytest.mark.parametrize("mode", ["text", "binary"])
@pytest.mark.parametrize("knowledge", [True, False, None])
def test_both_modes_and_both_seller_knowledge_cells_are_one_union(
    monkeypatch: pytest.MonkeyPatch, mode: str, knowledge,
) -> None:
    game = _game(_gid(True), mode=mode, knowledge=knowledge)
    monkeypatch.setenv(FLAG, "1")
    action = _decide(game)
    assert action["decision"] == "yes"
    assert action["_plan"][GATE] is True


@pytest.mark.parametrize("current", ["I have thoughts.", "", "no", False])
def test_current_signal_must_be_strictly_positive_not_legacy_ambiguous(
    monkeypatch: pytest.MonkeyPatch, current,
) -> None:
    game = _game(_gid(True), current=current)
    monkeypatch.setattr(
        persuasion, "buyer_plan_v2", lambda _game, _cfg: _fake_plan())
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off
    _assert_unannotated(on)


def test_prior_decline_must_be_strict_not_expanded_or_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True), declines=0)
    game["game_state"]["history"] = [
        {"seller_message": "Not recommended.", "bought": False},
        {"seller_message": "Not recommended.", "bought": False},
    ]
    monkeypatch.setattr(
        persuasion, "buyer_plan_v2", lambda _game, _cfg: _fake_plan())
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off

    game["game_state"]["history"] = [
        {"seller_message": "I would hold off on this one.", "bought": False}
    ]
    changed = _decide(game)
    assert changed["decision"] == "yes"
    assert changed["_plan"][f"{GATE}_prior_declines"] == 1


@pytest.mark.parametrize(
    "expected,changes",
    [
        (100.0, False),
        (100.0 + 5e-8, False),
        (100.0 + 1e-5, True),
        (math.nan, False),
    ],
)
def test_existing_posterior_ev_must_clear_price_with_relative_tolerance(
    monkeypatch: pytest.MonkeyPatch, expected: float, changes: bool,
) -> None:
    game = _game(_gid(True))
    monkeypatch.setattr(
        persuasion,
        "buyer_plan_v2",
        lambda _game, _cfg: _fake_plan(expected=expected),
    )
    monkeypatch.setenv(FLAG, "1")
    action = _decide(game)
    assert (action["decision"] == "yes") is changes
    assert (GATE in action["_plan"]) is changes


@pytest.mark.parametrize(
    "overrides",
    [
        {"buy": True},
        {"buyer_v2": False},
        {"tight": False},
        {"blocked": False},
    ],
)
def test_never_overlays_a_buy_or_non_v2_non_tight_nonblocked_plan(
    monkeypatch: pytest.MonkeyPatch, overrides: dict,
) -> None:
    game = _game(_gid(True))
    monkeypatch.setattr(
        persuasion,
        "buyer_plan_v2",
        lambda _game, _cfg: _fake_plan(**overrides),
    )
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
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
    ],
)
def test_conflicting_buyer_flags_fail_closed_against_their_own_control(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str,
) -> None:
    game = _game(_gid(True))
    monkeypatch.setenv(name, value)
    conflict_control = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    conflict_treatment = _decide(game)
    assert conflict_treatment == conflict_control
    _assert_unannotated(conflict_treatment)


@pytest.mark.parametrize(
    "conflict",
    [
        {"rank_gate_arm": True},
        {"rank_buy_arm": True},
        {"buyer_selectivity_arm": "candidate"},
        {"lcb_veto": True},
        {"parser_abstained": True},
        {"uninformed_veto": True},
        {"gates_fired": ["some_existing_gate"]},
    ],
)
def test_conflicting_plan_metadata_fails_closed(
    monkeypatch: pytest.MonkeyPatch, conflict: dict,
) -> None:
    game = _game(_gid(True))
    monkeypatch.setattr(
        persuasion,
        "buyer_plan_v2",
        lambda _game, _cfg: _fake_plan(**copy.deepcopy(conflict)),
    )
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    assert on == off
    assert GATE not in on["_plan"]


def test_assignment_is_stable_balanced_independent_and_missing_id_is_control() -> None:
    assert persuasion.PERS_P05_R12_SELECTIVITY_UNLOCK_SALT == (
        "pers_p05_r12_selectivity_unlock_v1|")
    bits = [
        persuasion.p05_r12_selectivity_unlock_assignment(f"gid-{index}")
        for index in range(2000)
    ]
    assert bits == [
        persuasion.p05_r12_selectivity_unlock_assignment(f"gid-{index}")
        for index in range(2000)
    ]
    assert 0.45 < sum(bits) / len(bits) < 0.55
    for other in (
        persuasion.rank_gate_assignment,
        persuasion.rank_buy_assignment,
        persuasion.buyer_selectivity_assignment,
        persuasion.p08_r125_text_decline_veto_assignment,
    ):
        agreement = sum(
            bit == other(f"gid-{index}")
            for index, bit in enumerate(bits)
        ) / len(bits)
        assert 0.45 < agreement < 0.55
    assert persuasion.p05_r12_selectivity_unlock_assignment("") is None
    assert persuasion.p05_r12_selectivity_unlock_assignment(None) is None
