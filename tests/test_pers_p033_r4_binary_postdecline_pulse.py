"""Safety tests for the exact p=1/3, v=4P buyer bait-pulse arm."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from scripts import check_reachability


FLAG = "GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB"
GATE = "p033_r4_binary_postdecline_pulse"


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
    for index in range(4000):
        game_id = f"p033-r4-postdecline-pulse-{index}"
        assigned = persuasion.p033_r4_binary_postdecline_pulse_assignment(
            game_id)
        if assigned is candidate:
            return game_id
    raise AssertionError("assignment not found")


def _motivating_prefix() -> list[dict]:
    return [
        {"round": 1, "seller_message": "yes", "bought": True,
         "quality": "high"},
        {"round": 2, "seller_message": "no", "bought": False},
        {"round": 3, "seller_message": "no", "bought": False},
        {"round": 4, "seller_message": "no", "bought": False},
        {"round": 5, "seller_message": "yes", "bought": True,
         "quality": "high"},
        {"round": 6, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 7, "seller_message": "yes", "bought": True,
         "quality": "low"},
        {"round": 8, "seller_message": "yes", "bought": True,
         "quality": "low"},
    ]


def _game(
    game_id: str,
    *,
    price: float = 100.0,
    current=True,
    history: list[dict] | None = None,
    knowledge=True,
) -> dict:
    if history is None:
        history = _motivating_prefix()
    state = {
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "product_price": price,
        "p": 1.0 / 3.0,
        "v": 4.0 * price,
        "u": 0.0,
        "seller_message_type": "binary",
        "seller_message": current,
        "round": len(history) + 1,
        "total_rounds": 20,
        "history": copy.deepcopy(history),
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


def _fake_plan(price: float = 100.0, *, buy: bool = True, **extra) -> dict:
    return {
        "price": price,
        "p": 1.0 / 3.0,
        "v": 4.0 * price,
        "u": 0.0,
        "recommended": True,
        "p_high": 0.30,
        "expected_value": 1.20 * price,
        "q_posterior": [0.1, 0.1, 0.2, 0.2, 0.2, 0.2],
        "observed_rounds": 4,
        "caught_lies": 3,
        "breakeven": 0.25,
        "tight": False,
        "blocked": False,
        "exploration_bonus": 0.0,
        "round": 9,
        "total_rounds": 20,
        "buyer_v2": True,
        "buy": buy,
        **extra,
    }


def _decide_with_plan(
    monkeypatch: pytest.MonkeyPatch,
    game: dict,
    plan: dict | None = None,
) -> dict:
    frozen = copy.deepcopy(plan or _fake_plan(
        float(game["game_state"]["product_price"])))
    monkeypatch.setattr(
        persuasion,
        "buyer_plan_v2",
        lambda _game, _cfg: copy.deepcopy(frozen),
    )
    return persuasion.decide(copy.deepcopy(game), None)


def _assert_unannotated(action: dict) -> None:
    plan = action["_plan"]
    assert all(not str(key).startswith(GATE) for key in plan)
    assert GATE not in plan.get("gates_fired", [])


def test_flag_default_off_and_explicit_zero_are_byte_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True))
    unset = _decide_with_plan(monkeypatch, game)
    monkeypatch.setenv(FLAG, "0")
    explicitly_off = _decide_with_plan(monkeypatch, game)
    assert explicitly_off == unset
    assert unset["decision"] == "yes"
    _assert_unannotated(unset)


def test_hash_control_is_byte_identical_to_flag_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(False))
    off = _decide_with_plan(monkeypatch, game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide_with_plan(monkeypatch, game)
    assert on == off
    _assert_unannotated(on)


def test_candidate_changes_only_buy_to_pass_with_complete_adjacent_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True))
    off = _decide_with_plan(monkeypatch, game)
    assert off["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    on = _decide_with_plan(monkeypatch, game)
    assert on["decision"] == "no"
    expected = copy.deepcopy(off)
    expected["decision"] = "no"
    expected["_plan"]["buy"] = False
    expected["_plan"].update({
        GATE: True,
        f"{GATE}_first_decline_round": 2,
        f"{GATE}_postdecline_highs": 1,
        f"{GATE}_postdecline_lows": 3,
        f"{GATE}_postdecline_margin": 0,
        f"{GATE}_prior_pulses": 0,
        f"{GATE}_last_pulsed_low_count": 0,
        "gates_fired": [GATE],
    })
    assert on == expected


def test_real_buyer_v2_reproduces_the_motivating_round9_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True))
    off = persuasion.decide(copy.deepcopy(game), None)
    assert off["decision"] == "yes"
    assert off["_plan"]["p_high"] > off["_plan"]["breakeven"]

    monkeypatch.setenv(FLAG, "1")
    on = persuasion.decide(copy.deepcopy(game), None)
    assert on["decision"] == "no"
    assert on["_plan"][GATE] is True
    assert on["_plan"][f"{GATE}_postdecline_highs"] == 1
    assert on["_plan"][f"{GATE}_postdecline_lows"] == 3


def test_pulse_resumes_then_requires_a_new_bought_yes_low(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(FLAG, "1")
    gid = _gid(True)
    after_pulse = _motivating_prefix() + [
        {"round": 9, "seller_message": "yes", "bought": False},
    ]
    resumed = _decide_with_plan(monkeypatch, _game(gid, history=after_pulse))
    assert resumed["decision"] == "yes"
    _assert_unannotated(resumed)

    after_new_low = after_pulse + [
        {"round": 10, "seller_message": "yes", "bought": True,
         "quality": "low"},
    ]
    repulsed = _decide_with_plan(
        monkeypatch, _game(gid, history=after_new_low))
    assert repulsed["decision"] == "no"
    assert repulsed["_plan"][f"{GATE}_prior_pulses"] == 1
    assert repulsed["_plan"][f"{GATE}_postdecline_lows"] == 4
    assert repulsed["_plan"][f"{GATE}_last_pulsed_low_count"] == 3


def test_exact_motivating_stream_pulses_only_on_predeclared_rounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(FLAG, "1")
    gid = _gid(True)
    stream = [
        ("yes", "high"), ("no", None), ("no", None), ("no", None),
        ("yes", "high"), ("yes", "low"), ("yes", "low"),
        ("yes", "low"), ("yes", "low"), ("yes", "low"),
        ("yes", "high"), ("yes", "low"), ("yes", "low"),
        ("yes", "high"), ("yes", "low"), ("yes", "low"),
        ("yes", "low"), ("yes", "low"), ("yes", "low"),
        ("yes", "low"),
    ]
    history: list[dict] = []
    pulsed = []
    payoff_units = 0
    for round_no, (message, quality) in enumerate(stream, 1):
        game = _game(gid, current=message, history=history)
        game["game_state"]["round"] = round_no
        action = _decide_with_plan(monkeypatch, game)
        bought = action["decision"] == "yes" and message == "yes"
        if action["_plan"].get(GATE) is True:
            pulsed.append(round_no)
        if bought:
            payoff_units += 3 if quality == "high" else -1
        history.append({
            "round": round_no,
            "seller_message": message,
            "bought": bought,
            "quality": quality if bought else None,
        })
    assert pulsed == [9, 11, 13, 16, 18, 20]
    assert payoff_units == 1


@pytest.mark.parametrize(
    "history,current",
    [
        pytest.param([
            {"seller_message": "yes", "bought": True, "quality": "low"}
            for _ in range(3)
        ], True, id="lows-before-any-decline"),
        pytest.param([
            {"seller_message": "no", "bought": False},
            {"seller_message": "yes", "bought": True, "quality": "low"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
        ], True, id="only-two-lows"),
        pytest.param([
            {"seller_message": "no", "bought": False},
            {"seller_message": "yes", "bought": True, "quality": "high"},
            {"seller_message": "yes", "bought": True, "quality": "high"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
        ], True, id="precision-above-breakeven"),
        pytest.param([
            {"seller_message": "no", "bought": False},
            {"seller_message": "yes", "bought": False, "quality": "low"},
            {"seller_message": "yes", "bought": False, "quality": "low"},
            {"seller_message": "yes", "bought": False, "quality": "low"},
        ], True, id="passed-qualities-never-count"),
        pytest.param([
            {"seller_message": "no", "bought": False},
            {"seller_message": "yes", "bought": True},
            {"seller_message": "yes", "bought": True, "quality": "low"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
        ], True, id="bought-hidden-quality-fails-closed"),
        pytest.param(_motivating_prefix(), False, id="current-no"),
        pytest.param(_motivating_prefix(), "buy", id="fuzzy-current-token"),
        pytest.param([
            {"seller_message": "I would pass.", "bought": False},
            {"seller_message": "yes", "bought": True, "quality": "low"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
            {"seller_message": "yes", "bought": True, "quality": "low"},
        ], True, id="fuzzy-history-decline"),
    ],
)
def test_nontriggering_histories_are_byte_identical_and_unannotated(
    monkeypatch: pytest.MonkeyPatch, history: list[dict], current,
) -> None:
    game = _game(_gid(True), history=history, current=current)
    off = _decide_with_plan(monkeypatch, game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide_with_plan(monkeypatch, game)
    assert on == off
    _assert_unannotated(on)


def test_control_refusal_is_never_reannotated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = _game(_gid(True))
    off = _decide_with_plan(monkeypatch, game, _fake_plan(buy=False))
    monkeypatch.setenv(FLAG, "1")
    on = _decide_with_plan(monkeypatch, game, _fake_plan(buy=False))
    assert on == off
    assert on["decision"] == "no"
    _assert_unannotated(on)


@pytest.mark.parametrize("price", [100.0, 10_000.0, 1_000_000.0])
@pytest.mark.parametrize("knowledge", [True, False, None])
def test_scale_invariance_and_both_seller_knowledge_configurations(
    monkeypatch: pytest.MonkeyPatch, price: float, knowledge,
) -> None:
    monkeypatch.setenv(FLAG, "1")
    action = _decide_with_plan(
        monkeypatch,
        _game(_gid(True), price=price, knowledge=knowledge),
        _fake_plan(price),
    )
    assert action["decision"] == "no"
    assert action["_plan"][GATE] is True


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda game: game.update(your_player="player_1"),
                     id="wrong-seat"),
        pytest.param(lambda game: game["valid_actions"].update(type="decision"),
                     id="wrong-action"),
        pytest.param(lambda game: game["game_state"].update(
            current_player="player_1"), id="wrong-current-player"),
        pytest.param(lambda game: game["game_state"].update(
            player_2_role="seller"), id="wrong-role"),
        pytest.param(lambda game: game["game_state"].update(
            seller_message_type="text"), id="wrong-mode"),
        pytest.param(lambda game: game["game_state"].update(p=0.34),
                     id="wrong-prior"),
        pytest.param(lambda game: game["game_state"].update(v=300.0),
                     id="wrong-ratio"),
        pytest.param(lambda game: game["game_state"].update(u=1.0),
                     id="wrong-low-value"),
        pytest.param(lambda game: game["game_state"].update(total_rounds=10),
                     id="wrong-horizon"),
        pytest.param(lambda game: game["game_state"].update(p="bad"),
                     id="malformed-number"),
    ],
)
def test_exact_structural_scope_fails_closed(
    monkeypatch: pytest.MonkeyPatch, mutate,
) -> None:
    game = _game(_gid(True))
    mutate(game)
    off = _decide_with_plan(monkeypatch, game)
    monkeypatch.setenv(FLAG, "1")
    on = _decide_with_plan(monkeypatch, game)
    assert on == off
    _assert_unannotated(on)


@pytest.mark.parametrize(
    "name",
    persuasion._P033_R4_BINARY_POSTDECLINE_PULSE_CONFLICT_FLAGS,
)
def test_every_conflicting_buyer_flag_fails_closed(
    monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    game = _game(_gid(True))
    off = _decide_with_plan(monkeypatch, game)
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(name, "1")
    on = _decide_with_plan(monkeypatch, game)
    assert on == off
    _assert_unannotated(on)


@pytest.mark.parametrize(
    "extra",
    [
        pytest.param({"gates_fired": ["other"]}, id="existing-gate"),
        pytest.param({"uninformed_veto": True}, id="uninformed-veto"),
        pytest.param({"rank_gate_arm": True}, id="rank-metadata"),
        pytest.param({"buyer_selectivity_arm": True}, id="selectivity-metadata"),
        pytest.param({"lcb_bound": 0.2}, id="lcb-metadata"),
        pytest.param({"parser_abstained": True}, id="parser-metadata"),
        pytest.param({"buyer_v2": False}, id="wrong-buyer"),
        pytest.param({"tight": True}, id="tight-plan"),
        pytest.param({"blocked": True}, id="blocked-plan"),
    ],
)
def test_conflicting_plan_paths_fail_closed(
    monkeypatch: pytest.MonkeyPatch, extra: dict,
) -> None:
    game = _game(_gid(True))
    plan = _fake_plan(**extra)
    off = _decide_with_plan(monkeypatch, game, plan)
    monkeypatch.setenv(FLAG, "1")
    on = _decide_with_plan(monkeypatch, game, plan)
    assert on == off
    _assert_unannotated(on)


def test_assignment_is_stable_balanced_and_independent() -> None:
    ids = [f"assignment-{index}" for index in range(2000)]
    first = [persuasion.p033_r4_binary_postdecline_pulse_assignment(gid)
             for gid in ids]
    second = [persuasion.p033_r4_binary_postdecline_pulse_assignment(gid)
              for gid in ids]
    assert first == second
    assert 900 <= sum(value is True for value in first) <= 1100
    other = [persuasion.p05_r12_selectivity_unlock_assignment(gid)
             for gid in ids]
    assert any(a != b for a, b in zip(first, other))
    assert persuasion.p033_r4_binary_postdecline_pulse_assignment("") is None


def test_reachability_registry_matches_exact_structural_scope() -> None:
    game = _game(_gid(True))
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    assert family == "persuasion"
    assert gates == (GATE,)
    assert predicate(game, _fake_plan())
    game["game_state"]["p"] = 0.5
    assert not predicate(game, _fake_plan())


def test_randomized_probe_bypasses_the_persuasion_strategy_arm() -> None:
    game = _game(_gid(True))
    control = {
        "GLEE_PERS_BUYER_V2": "1",
        "GLEE_PERS_BUYER_TIGHT_PRIOR": "0.65",
        FLAG: "0",
    }
    candidate = {**control, FLAG: "1"}
    off = check_reachability._replay(
        [game], control, probe_name="randomized")
    on = check_reachability._replay(
        [game], candidate, probe_name="randomized")
    assert off[0][0] == on[0][0]
    assert off[0][1] == on[0][1] == {}
