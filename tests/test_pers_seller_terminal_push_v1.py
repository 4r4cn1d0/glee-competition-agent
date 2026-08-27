"""Safety contract for the deterministic final-round seller push."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import runtime_flags
from glee_agent.config import Config
from glee_agent.dispatch import make_strategy
from glee_agent.strategies import persuasion


FLAG = persuasion.PERS_SELLER_TERMINAL_PUSH_V1_FLAG
MARKER = "seller_terminal_push_v1"
GATE = "pers_seller_terminal_push_v1"


@pytest.fixture(autouse=True)
def _isolated_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name in (
                "GLEE_PROBE", "GLEE_TRACE_GATES", "GLEE_LLM_MODE"):
            monkeypatch.delenv(name, raising=False)
    # Reproduce the shared deterministic persuasion baseline without reading a
    # live fleet overlay.  In particular, terminal push remains absent/OFF.
    monkeypatch.setenv("GLEE_PERS_BUYER_V2", "1")
    monkeypatch.setenv("GLEE_PERS_BUYER_TIGHT_PRIOR", "0.65")
    monkeypatch.setenv("GLEE_PERS_MSG_STYLE", "token")
    monkeypatch.setenv("GLEE_PERS_KEEP_MSG", "1")
    monkeypatch.setenv("GLEE_PERS_HONEST_ROUNDS", "99")
    monkeypatch.setenv("GLEE_PERS_LIE_SHADING", "0")
    monkeypatch.setenv("GLEE_LLM_MODE", "off")
    monkeypatch.setattr(persuasion, "_buyer_prior_doc", lambda: None)
    monkeypatch.setattr(persuasion, "_dp_policy", lambda: None)
    monkeypatch.setattr(persuasion, "_dp_policy_v2", lambda: None)
    monkeypatch.setattr(persuasion, "_dp_policy_v3", lambda: None)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _history() -> list[dict]:
    return [
        {
            "round": round_no,
            "quality": "high" if round_no % 3 == 0 else "low",
            "seller_message": "yes" if round_no % 3 == 0 else "no",
            "buyer_decision": "no",
            "bought": False,
        }
        for round_no in range(1, 20)
    ]


def _seller_game(
        *, mode: str = "binary", quality: str = "low", round_no: int = 20,
        total_rounds: int | None = 20, prior: float = 1.0 / 3.0,
        ratio: float = 1.2, seat: str = "player_1",
        current_player: str = "player_1", role: str = "seller",
        family: str = "persuasion") -> dict:
    action_type = "seller_recommendation" if mode == "binary" else "seller_message"
    state = {
        "player_1_role": role,
        "player_2_role": "buyer",
        "current_player": current_player,
        "current_quality": quality,
        "product_price": 100.0,
        "p": prior,
        "v": ratio * 100.0,
        "u": 0.0,
        "round": round_no,
        "seller_message_type": mode,
        "is_seller_know_cv": True,
        "history": _history()[:max(round_no - 1, 0)],
    }
    if total_rounds is not None:
        state["total_rounds"] = total_rounds
    return {
        "game_id": "terminal-push",
        "game_family": family,
        "your_player": seat,
        "valid_actions": {"type": action_type},
        "game_state": state,
    }


def _buyer_game() -> dict:
    return {
        "game_id": "terminal-push-buyer",
        "game_family": "persuasion",
        "your_player": "player_2",
        "valid_actions": {"type": "buyer_decision"},
        "game_state": {
            "player_1_role": "seller",
            "player_2_role": "buyer",
            "current_player": "player_2",
            "product_price": 100.0,
            "p": 1.0 / 3.0,
            "v": 200.0,
            "u": 0.0,
            "seller_message_type": "binary",
            "seller_message": "yes",
            "round": 20,
            "total_rounds": 20,
            "history": _history(),
        },
    }


def _decide(game: dict) -> dict:
    return persuasion.decide(copy.deepcopy(game), Config.from_env())


def _wire(action: dict) -> str:
    return action.get("decision", action.get("message"))


@pytest.mark.parametrize("explicit", [None, "0", "false", "off"])
@pytest.mark.parametrize("mode", ["binary", "text"])
def test_default_off_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, explicit: str | None,
        mode: str) -> None:
    game = _seller_game(mode=mode)
    control = _decide(game)
    if explicit is not None:
        monkeypatch.setenv(FLAG, explicit)
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


@pytest.mark.parametrize("mode", ["binary", "text"])
def test_final_low_baseline_decline_changes_only_to_legal_yes(
        monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    game = _seller_game(mode=mode)
    control = _decide(game)
    assert _wire(control) == "no"
    assert control["_plan"]["recommend"] is False

    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert _wire(candidate) == "yes"
    assert candidate["_plan"][MARKER] is True
    assert candidate["_plan"]["gates_fired"] == [GATE]

    wire_key = "decision" if mode == "binary" else "message"
    assert set(candidate) == set(control)
    assert {key for key in control if control[key] != candidate[key]} == {
        wire_key, "_plan"
    }
    off_plan, on_plan = control["_plan"], candidate["_plan"]
    assert set(on_plan) - set(off_plan) == {MARKER, "gates_fired"}
    assert set(off_plan) - set(on_plan) == set()
    assert {key for key in off_plan if off_plan[key] != on_plan[key]} == {
        "recommend"
    }
    assert (off_plan["recommend"], on_plan["recommend"]) == (False, True)
    assert on_plan["gates_fired"] == [GATE]

    # The dispatcher strips diagnostics and returns only a protocol-legal wire.
    dispatched = make_strategy(Config.from_env())(copy.deepcopy(game))
    assert dispatched == {wire_key: "yes"}


@pytest.mark.parametrize(
    ("name", "game"),
    [
        ("high", _seller_game(quality="high")),
        ("baseline yes", _seller_game(prior=0.5, ratio=3.0)),
        ("nonfinal", _seller_game(round_no=19)),
        ("non-20 terminal", _seller_game(round_no=10, total_rounds=10)),
        ("round beyond total", _seller_game(round_no=21)),
        ("missing total", _seller_game(total_rounds=None)),
        ("wrong seat", _seller_game(seat="player_2")),
        ("wrong current player", _seller_game(current_player="player_2")),
        ("wrong role", _seller_game(role="buyer")),
        ("wrong family", _seller_game(family="negotiation")),
    ],
)
def test_nontriggering_seller_states_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch, name: str, game: dict) -> None:
    del name
    control = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


def test_buyer_path_is_byte_identical(monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game()
    control = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


def test_omitted_redundant_seller_role_remains_reachable(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _seller_game()
    game["game_state"].pop("player_1_role")
    control = _decide(game)
    assert _wire(control) == "no"
    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert _wire(candidate) == "yes"
    assert candidate["_plan"]["gates_fired"] == [GATE]


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        (persuasion.PERS_ZERO_MARGIN_TRUTH_V1_FLAG, "1"),
        (persuasion.PERS_SELLER_DEMAND_COLLAPSE_TRUTH_V1_FLAG, "1"),
        (persuasion.PERS_SELLER_POSITIVE_PASS_STREAK_TRUTH_V1_FLAG, "1"),
        ("GLEE_PERS_DP", "1"),
        ("GLEE_PERS_DP_V3", "1"),
        ("GLEE_PERS_BACKLOAD_AB", "2"),
        ("GLEE_PERS_BACKLOAD_AB", "-1"),
        ("GLEE_PERS_BACKLOAD_AB", "nan"),
        ("GLEE_PERS_P08_R125_BINARY_TRUTH_AB", "1"),
        ("GLEE_PERS_P08_R125_PROSE_AB", "1"),
        (persuasion.PERS_P08_POSITIVE_PROSE_V1_FLAG, "1"),
    ],
)
def test_optional_seller_flags_fail_closed_without_overlap(
        monkeypatch: pytest.MonkeyPatch, flag: str, value: str) -> None:
    game = _seller_game()
    monkeypatch.setenv(flag, value)
    control = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


@pytest.mark.parametrize(
    ("round_value", "total_value"),
    [
        ("20", 20),
        (20, "20"),
        (float("nan"), 20),
        (20, float("nan")),
        (float("inf"), 20),
        (20, float("-inf")),
        (True, 20),
        (20, False),
        (None, 20),
        (20, None),
    ],
)
def test_malformed_or_non_numeric_round_fields_fail_closed(
        monkeypatch: pytest.MonkeyPatch, round_value, total_value) -> None:
    game = _seller_game()
    game["game_state"]["round"] = round_value
    game["game_state"]["total_rounds"] = total_value
    control = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert candidate == control
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


@pytest.mark.parametrize(
    "baseline_extra",
    [
        {"gates_fired": ["some_existing_seller_gate"]},
        {"backload_arm": True},
        {"dp": True},
        {"dp_v3": True},
        {"zero_margin_truth_v1": True},
        {"seller_demand_collapse_truth_v1": True},
        {"seller_positive_pass_streak_truth_v1": True},
        {"p08_r125_binary_truth_arm": "truth"},
        {"p08_r125_prose_arm": "prose"},
        {"p08_positive_prose_v1": True},
    ],
)
def test_recognized_plan_markers_fail_closed(
        monkeypatch: pytest.MonkeyPatch, baseline_extra: dict) -> None:
    game = _seller_game()
    baseline = _decide(game)["_plan"]
    baseline.update(baseline_extra)
    monkeypatch.setattr(
        persuasion, "_seller_plan_baseline", lambda _game, _cfg: copy.deepcopy(baseline)
    )
    monkeypatch.setenv(FLAG, "1")
    candidate = _decide(game)
    assert candidate["_plan"] == baseline
    assert MARKER not in candidate["_plan"]
    assert GATE not in candidate["_plan"].get("gates_fired", [])


def test_enabled_policy_is_game_id_invariant(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAG, "1")
    outputs = []
    for game_id in (None, "", "a", "b", "completely-different"):
        game = _seller_game()
        game["game_id"] = game_id
        outputs.append(_decide(game))
    assert outputs == [outputs[0]] * len(outputs)
    assert outputs[0]["_plan"]["gates_fired"] == [GATE]
    assert not any(
        "arm" in key or "assignment" in key for key in outputs[0]["_plan"]
    )
