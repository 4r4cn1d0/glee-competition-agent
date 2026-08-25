"""Safety contract for deterministic seller demand-collapse truth repair."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.dispatch import make_strategy
from glee_agent.strategies import persuasion
from scripts import check_reachability


FLAG = persuasion.PERS_SELLER_DEMAND_COLLAPSE_TRUTH_V1_FLAG
TRUTH_FLAG = persuasion.PERS_ZERO_MARGIN_TRUTH_V1_FLAG
MARKER = "seller_demand_collapse_truth_v1"
GATE = "pers_seller_demand_collapse_truth_v1"


@pytest.fixture(autouse=True)
def _isolated_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_MODE"):
            monkeypatch.delenv(name, raising=False)
    # Reproduce the deterministic live persuasion baseline without consulting
    # any fleet overlay.  The new flag remains absent/default OFF.
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


def _history(*bought: bool) -> list[dict]:
    return [
        {
            "round": index,
            "quality": "low" if index % 2 else "high",
            "seller_message": "yes",
            "buyer_decision": "yes" if did_buy else "no",
            "bought": did_buy,
        }
        for index, did_buy in enumerate(bought, 1)
    ]


def _seller_game(
        *, game_id: str | None = "demand-collapse", mode: str = "binary",
        quality: str = "low", price: float = 100.0, prior: float = 0.5,
        ratio: float = 3.0, low_value: float = 0.0,
        history: list[dict] | None = None, seat: str = "player_1",
        current_player: str = "player_1", action_type: str | None = None,
        values_known: bool = True) -> dict:
    if action_type is None:
        action_type = (
            "seller_recommendation" if mode == "binary" else "seller_message"
        )
    high_value = ratio * price if values_known else None
    u = low_value * price if values_known else None
    rows = _history(False, False, True) if history is None else history
    return {
        "game_id": game_id,
        "game_family": "persuasion",
        "your_player": seat,
        "valid_actions": {"type": action_type},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "current_player": current_player,
            "current_quality": quality,
            "product_price": price,
            "p": prior,
            "v": high_value,
            "u": u,
            "round": len(rows) + 1,
            "total_rounds": 20,
            "seller_message_type": mode,
            "is_seller_know_cv": values_known,
            "history": rows,
        },
    }


def _buyer_game() -> dict:
    return {
        "game_id": "demand-collapse-buyer",
        "game_family": "persuasion",
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "current_player": "player_2",
            "product_price": 100.0,
            "p": 0.8,
            "v": 200.0,
            "u": 0.0,
            "seller_message_type": "binary",
            "seller_message": "yes",
            "round": 4,
            "total_rounds": 20,
            "history": _history(False, False, True),
        },
    }


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), Config.from_env())


def _enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAG, "1")


def _wire_value(action: dict) -> str:
    return action.get("decision", action.get("message"))


@pytest.mark.parametrize("explicit", [None, "0", "false", "off"])
@pytest.mark.parametrize(
    "game",
    [
        _seller_game(mode="binary"),
        _seller_game(mode="text"),
        _seller_game(quality="high"),
        _seller_game(history=[]),
        _seller_game(values_known=False),
        _buyer_game(),
    ],
)
def test_default_off_and_every_false_spelling_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch, explicit: str | None,
        game: dict) -> None:
    control = _decide(game)
    if explicit is not None:
        monkeypatch.setenv(FLAG, explicit)
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate.get("_plan", {})
    assert GATE not in candidate.get("_plan", {}).get("gates_fired", [])


@pytest.mark.parametrize("mode", ["binary", "text"])
@pytest.mark.parametrize(
    ("prior", "ratio", "low_value"),
    [
        (1.0 / 3.0, 4.0, 0.0),
        (0.5, 2.0, 0.0),       # exact equality is owned here if truth is OFF
        (0.5, 3.0, 0.0),
        (0.8, 1.25, 0.0),      # exact equality at the high prior
        (0.8, 2.0, 0.0),
        (0.5, 1.2, 1.0),       # positive low value also clears the price
    ],
)
@pytest.mark.parametrize("price", [1.0, 100.0, 1_000_000.0])
def test_known_low_collapsed_all_push_changes_exactly_yes_to_no_across_cells(
        monkeypatch: pytest.MonkeyPatch, mode: str, prior: float,
        ratio: float, low_value: float, price: float) -> None:
    game = _seller_game(
        mode=mode, price=price, prior=prior, ratio=ratio,
        low_value=low_value,
    )
    control = _decide(game)
    assert _wire_value(control) == "yes"
    assert control["_plan"]["reason"] == "prior alone justifies purchase"
    assert control["_plan"]["buy_rate"] == pytest.approx(1.0 / 3.0)

    _enable(monkeypatch)
    candidate = _decide(game)

    assert _wire_value(candidate) == "no"
    assert candidate["_plan"][MARKER] is True
    assert candidate["_plan"]["gates_fired"] == [GATE]
    assert candidate["_plan"]["quality_is_high"] is False
    assert candidate["_plan"]["buy_rate"] == control["_plan"]["buy_rate"]
    # Dispatch intentionally strips private ``_plan`` diagnostics from the
    # submitted wire action; the legal wire decision must still match.
    dispatched = make_strategy(Config.from_env())(copy.deepcopy(game))
    assert _wire_value(dispatched) == "no"
    assert set(dispatched) == ({"decision"} if mode == "binary" else {"message"})


@pytest.mark.parametrize("mode", ["binary", "text"])
def test_exact_plan_and_wire_delta_contains_no_unexplained_change(
        monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    game = _seller_game(mode=mode)
    control = _decide(game)
    _enable(monkeypatch)
    candidate = _decide(game)

    assert set(candidate) == set(control)
    wire_key = "decision" if mode == "binary" else "message"
    assert {
        key for key in control
        if control[key] != candidate[key]
    } == {wire_key, "_plan"}
    assert (control[wire_key], candidate[wire_key]) == ("yes", "no")

    off_plan = control["_plan"]
    on_plan = candidate["_plan"]
    assert set(on_plan) - set(off_plan) == {MARKER, "gates_fired"}
    assert set(off_plan) - set(on_plan) == set()
    assert {
        key for key in off_plan
        if off_plan[key] != on_plan[key]
    } == {"recommend", "reason", "lie_rate"}
    assert on_plan[MARKER] is True
    assert on_plan["gates_fired"] == [GATE]
    assert (off_plan["recommend"], on_plan["recommend"]) == (True, False)
    assert (off_plan["lie_rate"], on_plan["lie_rate"]) == (1.0, 0.0)


@pytest.mark.parametrize(
    ("name", "game"),
    [
        ("high quality", _seller_game(quality="high")),
        ("no history", _seller_game(history=[])),
        ("unknown values", _seller_game(values_known=False)),
        ("prior EV below price", _seller_game(prior=1.0 / 3.0, ratio=1.2)),
        ("exactly half bought", _seller_game(history=_history(False, True))),
        ("more than half bought", _seller_game(history=_history(True, True, False))),
    ],
)
def test_nontriggering_seller_states_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch, name: str, game: dict) -> None:
    del name  # pytest id aid; the full output must remain byte-identical.
    control = _decide(game)
    _enable(monkeypatch)
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


def test_flag_has_no_buyer_decision_leakage(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game()
    control = _decide(game)
    _enable(monkeypatch)
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


@pytest.mark.parametrize(
    "game",
    [
        _seller_game(seat="player_2"),
        _seller_game(current_player="player_2"),
    ],
    ids=["wrong-seat", "wrong-current-player"],
)
def test_flag_has_no_wrong_role_leakage(
        monkeypatch: pytest.MonkeyPatch, game: dict) -> None:
    control = _decide(game)
    _enable(monkeypatch)
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


def test_enabled_policy_is_game_id_invariant(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    outputs = [
        _decide(_seller_game(game_id=game_id))
        for game_id in (None, "", "a", "b", "completely-different")
    ]
    assert outputs == [outputs[0]] * len(outputs)
    assert outputs[0]["_plan"]["gates_fired"] == [GATE]
    assert not any(
        "arm" in key or "assignment" in key for key in outputs[0]["_plan"]
    )


def test_zero_margin_truth_preempts_without_double_firing(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _seller_game(prior=0.8, ratio=1.25)

    _enable(monkeypatch)
    demand_only = _decide(game)
    assert demand_only["_plan"]["gates_fired"] == [GATE]

    monkeypatch.setenv(TRUTH_FLAG, "1")
    composed = _decide(game)
    assert _wire_value(composed) == "no"
    assert composed["_plan"]["zero_margin_truth_v1"] is True
    assert composed["_plan"]["gates_fired"] == ["pers_zero_margin_truth_v1"]
    assert MARKER not in composed["_plan"]
    assert GATE not in composed["_plan"]["gates_fired"]


def test_zero_margin_truth_does_not_preempt_strict_positive_margin(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _seller_game(prior=0.8, ratio=2.0)
    monkeypatch.setenv(TRUTH_FLAG, "1")
    _enable(monkeypatch)
    candidate = _decide(game)
    assert _wire_value(candidate) == "no"
    assert candidate["_plan"]["gates_fired"] == [GATE]
    assert "zero_margin_truth_v1" not in candidate["_plan"]


def test_reachability_registry_matches_real_changed_action_scope() -> None:
    game = _seller_game()
    control = _decide(game)["_plan"]
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    assert family == "persuasion"
    assert gates == (GATE,)
    assert predicate(game, control)

    game["game_state"]["history"] = _history(False, True)
    assert not predicate(game, control)
