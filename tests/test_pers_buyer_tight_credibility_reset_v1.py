"""Safety tests for the deterministic tight-cell credibility reset."""

from __future__ import annotations

import copy
import math
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from scripts import check_reachability


FLAG = persuasion.PERS_BUYER_TIGHT_CREDIBILITY_RESET_V1_FLAG
GATE = "buyer_tight_credibility_reset_v1"
_DEFAULT_CURRENT = object()


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
    game_id: str = "tight-credibility-reset",
    p: float = 0.8,
    ratio: float = 1.25,
    mode: str = "binary",
    current=_DEFAULT_CURRENT,
    history: list[dict] | None = None,
    price: float = 100.0,
    knowledge=True,
) -> dict:
    if current is _DEFAULT_CURRENT:
        current = "yes"
    history = copy.deepcopy(history or [])
    state = {
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "product_price": price,
        "p": p,
        "v": ratio * price,
        "u": 0.0,
        "seller_message_type": mode,
        "seller_message": current,
        "round": len(history) + 1,
        "total_rounds": 20,
        "history": history,
    }
    if knowledge is not None:
        state["is_seller_know_cv"] = knowledge
    return {
        "game_id": game_id,
        "game_family": "persuasion",
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": state,
    }


def _fake_plan(
    *,
    p: float = 0.8,
    ratio: float = 1.25,
    price: float = 100.0,
    expected: float = 103.0,
    buy: bool = True,
    blocked: bool = False,
    **extra,
) -> dict:
    return {
        "price": price,
        "p": p,
        "v": ratio * price,
        "u": 0.0,
        "recommended": True,
        "p_high": expected / (ratio * price),
        "expected_value": expected,
        "q_posterior": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "observed_rounds": 0,
        "caught_lies": 0,
        "breakeven": 1.0 / ratio,
        "tight": True,
        "blocked": blocked,
        "exploration_bonus": 0.0,
        "round": 1,
        "total_rounds": 20,
        "buyer_v2": True,
        "buy": buy,
        **extra,
    }


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), None)


def _decide_with_plan(
    monkeypatch: pytest.MonkeyPatch,
    game: dict,
    plan: dict,
) -> dict:
    frozen = copy.deepcopy(plan)
    monkeypatch.setattr(
        persuasion, "buyer_plan_v2",
        lambda _game, _cfg: copy.deepcopy(frozen),
    )
    return _decide(game)


def _assert_unannotated(action: dict) -> None:
    plan = action["_plan"]
    assert all(not str(key).startswith(GATE) for key in plan)
    assert GATE not in plan.get("gates_fired", [])


def test_default_off_and_explicit_zero_are_byte_identical() -> None:
    game = _game()
    unset = _decide(game)
    os.environ[FLAG] = "0"
    explicit_zero = _decide(game)
    assert explicit_zero == unset
    _assert_unannotated(unset)


@pytest.mark.parametrize("mode,current,decline", [
    ("binary", "yes", "no"),
    ("text", "I recommend this one.", "I would hold off on this one."),
])
def test_no_credibility_changes_only_buy_to_pass_with_adjacent_trace(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    current: str,
    decline: str,
) -> None:
    # A decline followed by a caught recommended LOW leaves the last event as a
    # credibility failure.  The current strict positive is therefore vetoed.
    game = _game(mode=mode, current=current, history=[
        {"seller_message": decline, "bought": False},
        {"seller_message": current, "bought": True, "quality": "low"},
    ])
    plan = _fake_plan()
    off = _decide_with_plan(monkeypatch, game, plan)
    assert off["decision"] == "yes"
    os.environ[FLAG] = "1"
    on = _decide_with_plan(monkeypatch, game, plan)

    expected = copy.deepcopy(off)
    expected["decision"] = "no"
    expected["_plan"]["buy"] = False
    expected["_plan"].update({
        GATE: True,
        f"{GATE}_direction": "buy_to_pass",
        f"{GATE}_credit_valid": False,
        f"{GATE}_last_decline_index": 0,
        f"{GATE}_last_caught_low_index": 1,
        f"{GATE}_prior_value": 100.0,
        f"{GATE}_expected_value": 103.0,
        f"{GATE}_posterior_edge": 3.0,
        "gates_fired": [GATE],
    })
    assert on == expected


@pytest.mark.parametrize("mode,current,decline", [
    ("binary", "yes", "no"),
    ("text", "yes", "Not recommended."),
])
def test_newer_decline_unlocks_only_tight_prior_pass(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    current: str,
    decline: str,
) -> None:
    game = _game(
        p=0.5, ratio=1.2, mode=mode, current=current,
        history=[{"seller_message": decline, "bought": False}],
    )
    plan = _fake_plan(
        p=0.5, ratio=1.2, expected=103.0, buy=False, blocked=True)
    off = _decide_with_plan(monkeypatch, game, plan)
    assert off["decision"] == "no"
    os.environ[FLAG] = "1"
    on = _decide_with_plan(monkeypatch, game, plan)

    expected = copy.deepcopy(off)
    expected["decision"] = "yes"
    expected["_plan"]["buy"] = True
    expected["_plan"].update({
        GATE: True,
        f"{GATE}_direction": "pass_to_buy",
        f"{GATE}_credit_valid": True,
        f"{GATE}_last_decline_index": 0,
        f"{GATE}_last_caught_low_index": -1,
        f"{GATE}_prior_value": 60.0,
        f"{GATE}_expected_value": 103.0,
        f"{GATE}_posterior_edge": 3.0,
        "gates_fired": [GATE],
    })
    assert on == expected


def test_real_buyer_v2_covers_both_failure_directions() -> None:
    # Equality-prior spam is bought by control; no earned credibility vetoes it.
    spam = _game(p=0.8, ratio=1.25)
    spam_off = _decide(spam)
    assert spam_off["decision"] == "yes"

    # Low-prior selectivity makes the posterior profitable but the .65 fence
    # still blocks control.  A strict decline is the newer credibility event.
    selective = _game(
        p=0.5, ratio=1.2,
        history=[{"seller_message": "no", "bought": False}] * 2,
    )
    selective_off = _decide(selective)
    assert selective_off["decision"] == "no"
    assert selective_off["_plan"]["blocked"] is True
    assert selective_off["_plan"]["expected_value"] > 100.0

    os.environ[FLAG] = "1"
    spam_on = _decide(spam)
    selective_on = _decide(selective)
    assert spam_on["decision"] == "no"
    assert spam_on["_plan"][f"{GATE}_direction"] == "buy_to_pass"
    assert selective_on["decision"] == "yes"
    assert selective_on["_plan"][f"{GATE}_direction"] == "pass_to_buy"


def test_caught_low_then_new_decline_restores_credibility_without_annotation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = [
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": True, "quality": "low"},
        {"seller_message": "no", "bought": False},
    ]
    game = _game(history=history)
    plan = _fake_plan(buy=True)
    off = _decide_with_plan(monkeypatch, game, plan)
    os.environ[FLAG] = "1"
    on = _decide_with_plan(monkeypatch, game, plan)
    assert on == off
    assert on["decision"] == "yes"
    _assert_unannotated(on)


@pytest.mark.parametrize("history,valid", [
    ([], False),
    ([{"seller_message": "no", "bought": False}], True),
    ([
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": True, "quality": "high"},
    ], True),
    ([
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": False, "quality": "low"},
    ], True),
    ([
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": True, "quality": "low"},
    ], False),
    ([
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": True, "quality": "low"},
        {"seller_message": "no", "bought": False},
    ], True),
])
def test_ordered_history_uses_only_latest_decline_or_caught_low(
    history: list[dict], valid: bool,
) -> None:
    game = _game(p=0.5, ratio=1.2, history=history)
    trace = persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, _fake_plan(
            p=0.5, ratio=1.2, buy=not valid, blocked=valid))
    assert trace is not None
    assert trace["credit_valid"] is valid
    assert trace["target_buy"] is valid


@pytest.mark.parametrize("current", [
    "no",
    "I would hold off on this one.",
    "I have thoughts.",
    "I recommend the next one, but do not buy this one.",
    "I recommend considering it, not buying it.",
    "I recommend waiting.",
    "I recommend you pass.",
    "I recommend this one, but maybe wait.",
    "I said yes last round because that unit was high quality. This one is ordinary.",
    "The previous unit was strongly recommended and high quality. This one is ordinary.",
    "Yesterday I recommended it and it was high quality; nothing special now.",
    "People say yes to high quality items. I have no view now.",
    None,
])
def test_negative_or_ambiguous_current_message_is_byte_identical(
    monkeypatch: pytest.MonkeyPatch, current,
) -> None:
    game = _game(mode="text", current=current, history=[
        {"seller_message": "no", "bought": False},
    ])
    plan = _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True)
    off = _decide_with_plan(monkeypatch, game, plan)
    os.environ[FLAG] = "1"
    on = _decide_with_plan(monkeypatch, game, plan)
    assert on == off
    _assert_unannotated(on)


@pytest.mark.parametrize("historical_only", [
    "The previous one was mediocre.",
    "Last round was low quality.",
    "Earlier it was nothing special.",
    "I said to hold off last round.",
    "The next one may be low quality.",
])
def test_history_or_future_only_negative_does_not_earn_credibility(
    historical_only: str,
) -> None:
    game = _game(
        p=0.5, ratio=1.2, mode="text", current="yes",
        history=[{"seller_message": historical_only, "bought": False}],
    )
    plan = _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True)
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, plan) is None


def test_ambiguous_bought_low_revokes_earlier_credibility() -> None:
    game = _game(
        p=0.5, ratio=1.2, mode="text", current="yes",
        history=[
            {"seller_message": "no", "bought": False},
            {"seller_message": "I have thoughts.", "bought": True,
             "quality": "low"},
        ],
    )
    trace = persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, _fake_plan(p=0.5, ratio=1.2, buy=True, blocked=False))
    assert trace is not None
    assert trace["direction"] == "buy_to_pass"
    assert trace["last_decline_index"] == 0
    assert trace["last_caught_low_index"] == 1


@pytest.mark.parametrize("bad_entry", [
    "not-a-dict",
    {"seller_message": "no"},
    {"seller_message": "no", "bought": 0},
    {"seller_message": "yes", "bought": True},
])
def test_malformed_history_fails_closed(bad_entry) -> None:
    game = _game(
        p=0.5, ratio=1.2,
        history=[{"seller_message": "no", "bought": False}, bad_entry],
    )
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True)) is None


@pytest.mark.parametrize("mutate", [
    lambda game: game.update(game_family="negotiation"),
    lambda game: game.update(your_player="player_1"),
    lambda game: game["valid_actions"].update(type="seller_message"),
    lambda game: game["game_state"].update(player_2_role="seller"),
    lambda game: game["game_state"].update(current_player="player_1"),
    lambda game: game["game_state"].update(seller_message_type="unknown"),
    lambda game: game["game_state"].update(product_price="bad"),
    lambda game: game["game_state"].update(history="bad"),
])
def test_wrong_scope_or_malformed_state_fails_closed(mutate) -> None:
    game = _game(history=[{"seller_message": "no", "bought": False}])
    mutate(game)
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True)) is None


@pytest.mark.parametrize("plan", [
    _fake_plan(ratio=1.2, buy=False, blocked=False),
    _fake_plan(ratio=1.2, buy=False, blocked=True, expected=100.0),
    _fake_plan(ratio=1.2, buy=False, blocked=True, expected=100.0 + 5e-8),
    _fake_plan(ratio=1.2, buy=False, blocked=True, expected=math.nan),
    _fake_plan(ratio=1.2, buy=False, blocked=True, buyer_v2=False),
    _fake_plan(ratio=1.2, buy=False, blocked=True, tight=False),
    _fake_plan(ratio=1.2, buy=False, blocked=True, breakeven=0.7),
])
def test_never_revives_a_non_tight_prior_control_pass(plan: dict) -> None:
    game = _game(
        p=0.5, ratio=1.2,
        history=[{"seller_message": "no", "bought": False}],
    )
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, plan) is None


def test_prior_profitable_and_non_tight_cells_are_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = [
        (_game(p=0.8, ratio=2.0), _fake_plan(
            p=0.8, ratio=2.0, buy=True, tight=False, breakeven=0.5)),
        (_game(p=0.9, ratio=1.25), _fake_plan(
            p=0.9, ratio=1.25, buy=True, blocked=False)),
    ]
    os.environ[FLAG] = "1"
    for game, plan in cases:
        off = _decide_with_plan(monkeypatch, game, plan)
        _assert_unannotated(off)


def test_bought_positive_with_missing_quality_fails_closed() -> None:
    game = _game(history=[
        {"seller_message": "no", "bought": False},
        {"seller_message": "yes", "bought": True},
    ])
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, _fake_plan()) is None


@pytest.mark.parametrize(
    "name", persuasion._BUYER_TIGHT_CREDIBILITY_RESET_V1_CONFLICT_FLAGS,
)
def test_every_conflicting_optional_buyer_path_fails_closed(
    name: str,
) -> None:
    game = _game(history=[{"seller_message": "no", "bought": False}])
    os.environ[name] = "1"
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True)) is None


@pytest.mark.parametrize("extra", [
    {"gates_fired": ["other"]},
    {"uninformed_veto": True},
    {"rank_gate_arm": "candidate"},
    {"buyer_selectivity_arm": "candidate"},
    {"lcb_bound": 0.8},
    {"parser_abstained": True},
])
def test_conflicting_plan_metadata_fails_closed(extra: dict) -> None:
    game = _game(history=[{"seller_message": "no", "bought": False}])
    plan = _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True, **extra)
    assert persuasion._buyer_tight_credibility_reset_v1_candidate(
        game, plan) is None


def test_v1_v2_v3_decline_stack_is_compatible_and_keeps_final_precedence() -> None:
    game = _game(
        p=0.5, ratio=1.2, mode="text", current="yes",
        history=[{"seller_message": "no", "bought": False}] * 2,
    )
    for name in (
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG,
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_V2_FLAG,
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_V3_FLAG,
        FLAG,
    ):
        os.environ[name] = "1"
    positive = _decide(game)
    assert positive["decision"] == "yes"
    assert positive["_plan"]["gates_fired"] == [GATE]

    game["game_state"]["seller_message"] = "I recommend waiting; do not buy this."
    negative = _decide(game)
    assert negative["decision"] == "no"
    assert GATE not in negative["_plan"].get("gates_fired", [])


def test_game_id_knowledge_and_scale_do_not_change_policy() -> None:
    os.environ[FLAG] = "1"
    actions = []
    for game_id in ("left", "right"):
        for knowledge in (True, False, None):
            for price in (100.0, 10_000.0, 1_000_000.0):
                game = _game(
                    game_id=game_id, p=0.5, ratio=1.2,
                    history=[{"seller_message": "no", "bought": False}] * 2,
                    knowledge=knowledge, price=price,
                )
                action = _decide(game)
                actions.append(action["decision"])
                assert action["_plan"][GATE] is True
    assert set(actions) == {"yes"}


def test_reachability_registry_matches_both_action_directions() -> None:
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    assert family == "persuasion"
    assert gates == (GATE,)

    buy_to_pass = _game()
    assert predicate(buy_to_pass, _fake_plan())

    pass_to_buy = _game(
        p=0.5, ratio=1.2,
        history=[{"seller_message": "no", "bought": False}],
    )
    assert predicate(
        pass_to_buy,
        _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True),
    )
    pass_to_buy["game_state"]["seller_message"] = "no"
    assert not predicate(
        pass_to_buy,
        _fake_plan(p=0.5, ratio=1.2, buy=False, blocked=True),
    )
