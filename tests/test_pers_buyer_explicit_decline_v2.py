"""Strict deterministic current-action text decline V2 tests."""

from __future__ import annotations

import copy
import os
from types import SimpleNamespace

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from glee_agent.text import reads_as_recommendation_expanded
from scripts import check_reachability


FLAG = persuasion.PERS_BUYER_EXPLICIT_DECLINE_V2_FLAG
GATE = "buyer_explicit_decline_v2"


@pytest.fixture(autouse=True)
def _isolated_persuasion_flags(monkeypatch: pytest.MonkeyPatch):
    for name in list(os.environ):
        if name.startswith("GLEE_PERS_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
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
        history: list[dict] | None = None) -> dict:
    return {
        "game_id": "decline-v2-game",
        "game_family": "persuasion",
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


def _seller_game(message: str) -> dict:
    game = _buyer_game(message)
    game["your_player"] = "player_1"
    game["valid_actions"] = {"type": "seller_message"}
    game["game_state"].update(
        current_player="player_1", current_quality="low")
    return game


def _decide(game: dict) -> dict:
    cfg = SimpleNamespace(pers_lie_shading=0.0, pers_honest_rounds=99)
    return persuasion.decide(copy.deepcopy(game), cfg)


@pytest.mark.parametrize(
    "message",
    [
        "I would not buy this one.",
        "I wouldn't purchase this item.",
        "You should not take this product.",
        "This one is not worth buying.",
        "There is no strong recommendation from me.",
        "Don't touch this product.",
        "Pass this one.",
        "Skip the unit.",
        "It looks tempting, but I would not buy this one.",
        "Sit this round out; the next product may be worth it.",
        "Sit this round out; better opportunities may be worth it later.",
        "Ordinary unit today — wait for the next one, which may be high "
        "quality and worth it.",
        "No strong recommendation from me; a future product may be worth it.",
        "Don't touch this product; the next unit could be high quality.",
        ("Honestly? Sit this round out. I'd rather keep your trust for the "
         "rounds that are actually worth it."),
        ("I'll be straight with you: this one is ordinary. Wait for the next "
         "-- I'll tell you when it's worth it."),
        "This one's below standard - I wouldn't buy it myself.",
        "Don't touch this. You'll regret it.",
        "Actually, I would not buy it.",
    ],
)
def test_strict_direct_v1_miss_changes_only_buy_to_pass(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    # These are intentionally outside V1: False would mean the existing live
    # guard already owns the message and V2 must not duplicate its metadata.
    assert reads_as_recommendation_expanded(message) is not False
    game = _buyer_game(message)
    off = _decide(game)
    assert off["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)

    assert on["decision"] == "no"
    assert on["_plan"]["buyer_explicit_decline_v2"] is True
    assert on["_plan"]["gates_fired"] == [GATE]
    expected = copy.deepcopy(off)
    expected["decision"] = "no"
    expected["_plan"]["buy"] = False
    expected["_plan"]["buyer_explicit_decline_v2"] = True
    expected["_plan"]["gates_fired"] = [GATE]
    assert on == expected


@pytest.mark.parametrize(
    "message",
    [
        "This one is high quality, but I would not buy it.",
        "Next, I would not buy this high quality item.",
        "I would not buy this one, though it is worth it.",
        "No strong recommendation, but this one is a clear buy.",
        "The current unit is high quality. I would not buy it.",
        "Last round I said I would not buy that one.",
        "I would not buy the previous one.",
        "Including low quality items, I would not buy every product.",
        "Earlier I warned you not to buy that item.",
        "I don't buy that argument.",
        "I would not buy into that claim.",
        "You should not take this recommendation lightly.",
        "Do not touch the controls.",
        "No strong recommendation; actually, this is a good deal.",
        "I would not buy it; this is worth the price.",
        "I would not buy it; this is worth your money.",
        "No strong recommendation; this is a strong pick.",
        "No strong recommendation; this is a high confidence buy.",
        "No strong recommendation; this is the real thing.",
        "No strong recommendation; consider it.",
        "No strong recommendation; definitely a good buy.",
        "No strong recommendation; yes on this round.",
        "No strong recommendation; I can recommend it.",
        "No strong recommendation; I stand behind it.",
        "No strong recommendation; this is one of the strongest.",
        "No strong recommendation. Another reason: I recommend it.",
        "No strong recommendation. Next, I recommend it.",
        "I would not buy it. Next, consider it.",
        "I would not buy it. In the future, I recommend it.",
        "I would not buy it, except that this is excellent.",
        "I would not buy it. Just kidding — this is excellent.",
        "I would not buy it. Actually, this is excellent.",
        "I would not buy it. On second thought, this is excellent.",
        "You said I would not buy this one.",
        "Yesterday, I would not buy this one.",
        "On round 3, I would not buy this one.",
        'Someone said, "I would not buy this one."',
        "Recommended.",
        "BOIIIII",
        "",
        None,
    ],
)
def test_positive_ambiguous_history_and_unknown_text_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch, message) -> None:
    game = _buyer_game(message)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


@pytest.mark.parametrize(
    "message",
    [
        "Not recommended.",
        "I recommend skipping this one.",
        "Save your money.",
        "I would hold off on this one.",
    ],
)
def test_messages_already_owned_by_v1_are_not_relabelled(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    assert reads_as_recommendation_expanded(message) is False
    game = _buyer_game(message)
    off = _decide(game)

    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off

    monkeypatch.setenv(persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG, "1")
    both = _decide(game)
    assert both["decision"] == "no"
    assert both["_plan"]["gates_fired"] == [
        "buyer_explicit_decline_veto_v1"]
    assert "buyer_explicit_decline_v2" not in both["_plan"]


def test_live_v1_and_v2_coexist_on_a_v1_miss(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game(
        "I would not buy this one; a future product may be worth it.")
    monkeypatch.setenv(
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG, "1")
    v1 = _decide(game)
    assert v1["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    both = _decide(game)
    assert both["decision"] == "no"
    assert both["_plan"]["gates_fired"] == [GATE]
    assert "buyer_explicit_decline_veto_v1" not in both["_plan"]


@pytest.mark.parametrize("message", ["no", False, "yes", True, None])
def test_binary_wire_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, message) -> None:
    game = _buyer_game(message, mode="binary")
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


def test_existing_pass_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch) -> None:
    game = _buyer_game("I would not buy this one.", p=0.4, v=1.2)
    off = _decide(game)
    assert off["decision"] == "no"
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


def test_history_only_decline_does_not_change_a_current_positive(
        monkeypatch: pytest.MonkeyPatch) -> None:
    history = [{
        "round": 1,
        "seller_message": "I would not buy this one.",
        "buyer_decision": "no",
        "bought": False,
    }]
    game = _buyer_game("Recommended.", history=history)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


@pytest.mark.parametrize("scope", ["seller", "legacy", "seat", "player"])
def test_non_buyer_v2_scope_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, scope: str) -> None:
    game = _buyer_game("I would not buy this one.")
    if scope == "seller":
        game = _seller_game("I would not buy this one.")
    elif scope == "legacy":
        monkeypatch.setenv("GLEE_PERS_BUYER_V2", "0")
    elif scope == "seat":
        game["your_player"] = "player_1"
    else:
        game["game_state"]["current_player"] = "player_1"
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


def test_default_off_does_not_consult_the_new_classifier(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(_message):
        raise AssertionError("default-OFF guard consulted V2 classifier")

    monkeypatch.setattr(
        persuasion, "_explicit_current_text_decline_v2", fail_if_called)
    assert _decide(_buyer_game("I would not buy this one."))["decision"] == "yes"


def test_game_id_does_not_affect_the_deterministic_policy(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAG, "1")
    outputs = []
    for game_id in (None, "a", "b", "different"):
        game = _buyer_game("I would not buy this one.")
        game["game_id"] = game_id
        outputs.append(_decide(game))
    assert outputs == [outputs[0]] * len(outputs)
    assert not any("arm" in key or "assignment" in key
                   for key in outputs[0]["_plan"])


def test_reachability_registration_matches_strict_change_scope() -> None:
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    plan = {"buyer_v2": True, "buy": True}

    assert family == "persuasion"
    assert gates == (GATE,)
    assert predicate(_buyer_game(
        "Sit this round out; the next product may be worth it."), plan) is True
    assert predicate(_buyer_game("Recommended."), plan) is False
    assert predicate(_buyer_game(
        "Sit this round out; the next product may be worth it.",
        mode="binary"), plan) is False
    assert predicate(_buyer_game(
        "Sit this round out; the next product may be worth it."), {
            **plan, "buy": False}) is False


def test_reachability_replay_proves_eligible_fired_and_action_changed() -> None:
    game = _buyer_game(
        "Sit this round out; the next product may be worth it.")
    control = {
        "GLEE_PERS_BUYER_V2": "1",
        "GLEE_PERS_BUYER_TIGHT_PRIOR": "0.65",
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG: "1",
        FLAG: "0",
        "GLEE_TRACE_GATES": "1",
    }
    candidate = {**control, FLAG: "1"}

    prefixes = check_reachability.replay_eval.FLAG_PREFIXES
    affected = lambda key: (key.startswith(prefixes)
                            or key in {"GLEE_PROBE", "GLEE_LLM_MODE",
                                       "GLEE_TRACE_GATES"})
    saved = {key: value for key, value in os.environ.items()
             if affected(key)}
    try:
        off = check_reachability._replay(
            [game], control, probe_name="composite")[0]
        on = check_reachability._replay(
            [game], candidate, probe_name="composite")[0]
        predicate = check_reachability.KNOWN[FLAG][2]

        assert predicate(game, off[1]) is True
        assert off[0]["decision"] == "yes"
        assert on[0]["decision"] == "no"
        assert off[1].get("gates_fired") in (None, [])
        assert on[1]["gates_fired"] == [GATE]
        assert check_reachability._action_differs(off[0], on[0]) is True
    finally:
        for key in list(os.environ):
            if affected(key):
                del os.environ[key]
        os.environ.update(saved)
        runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
