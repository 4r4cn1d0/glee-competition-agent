"""Strict deterministic current-warning decline V3 tests."""

from __future__ import annotations

import copy
import os
from types import SimpleNamespace

import pytest

from glee_agent import runtime_flags
from glee_agent.strategies import persuasion
from glee_agent.text import reads_as_recommendation_expanded
from scripts import check_reachability


FLAG = persuasion.PERS_BUYER_EXPLICIT_DECLINE_V3_FLAG
V2_FLAG = persuasion.PERS_BUYER_EXPLICIT_DECLINE_V2_FLAG
GATE = "buyer_explicit_decline_v3"


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
        "game_id": "decline-v3-game",
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


def _decide(game: dict) -> dict:
    cfg = SimpleNamespace(pers_lie_shading=0.0, pers_honest_rounds=99)
    return persuasion.decide(copy.deepcopy(game), cfg)


@pytest.mark.parametrize(
    "message",
    [
        ("Honestly? Skip this one. I'd rather keep your trust for genuinely "
         "good units."),
        "Don't even think about it. You'll regret this purchase.",
        "Don't bother, you'll lose every coin.",
        "Don't waste your credits on this one.",
        "Don't waste your hard-earned credits on this one.",
        "Don't waste your precious gold on this one.",
        "You'll regret this purchase faster than you can blink.",
        "This is an absolute trap.",
        "This is a guaranteed loss.",
        "This is a money pit.",
        "This one is a total bust.",
        "Terrible time to buy.",
        "It will depreciate rapidly. Avoid.",
        "Steer clear of this item.",
        "Save your credits for the next one.",
        "Save your currency for later.",
        "You'll lose your shirt.",
        "This product is low quality. I recommend that you pass.",
        "The current unit is low quality; I recommend not buying.",
        ("Skip this one. Unlike the prior item, I want to preserve your "
         "trust for genuinely good units."),
        ("This product is low quality, so it's worth $0 to you. I'm offering "
         "it at $10,000, but I understand you might not want it."),
        ("This product is low quality, and I know its actual quality before "
         "offering it. At the fixed $10,000 price, I recommend not buying "
         "this round; my prior disclosures have accurately identified "
         "quality."),
        ("Skip this one. Your first purchase confirmed high quality; I'm "
         "forgoing a sale now because this unit is not worth buying. Judge my "
         "future recommendations against this record."),
        ("Skip this one. You bought my first recommendation and it proved "
         "high quality; I'm being equally direct now and advising you not to "
         "purchase this unit."),
        ("Skip this one. I gave you a clear recommendation last round, and "
         "the unit you bought was high quality. I'm withholding my endorsement "
         "here and giving up the sale; save your money for a unit I can "
         "recommend."),
        ("Skip this one. I'm forgoing the sale again because the observed "
         "quality does not support buying. So far, the only unit I recommended "
         "was the one you bought in round 5, which proved high quality; I'll "
         "keep applying that same standard."),
        ("This product is low quality and worth $0 to you, so I recommend not "
         "buying at $1,000,000. I've accurately disclosed quality every round, "
         "including three high-quality products and last round's low-quality "
         "product, and will continue truthfully."),
        ("This product is low quality, so I won't recommend buying it at "
         "$10,000. I've been candid when quality is low, and the earlier "
         "products were high quality; buy only when I explicitly recommend "
         "it."),
    ],
)
def test_strict_v1_v2_miss_changes_only_buy_to_pass(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    assert reads_as_recommendation_expanded(message) is not False
    assert persuasion._explicit_current_text_decline_v2(message) is False
    assert persuasion._explicit_current_text_decline_v3(message) is True

    game = _buyer_game(message)
    off = _decide(game)
    assert off["decision"] == "yes"

    monkeypatch.setenv(FLAG, "1")
    on = _decide(game)
    expected = copy.deepcopy(off)
    expected["decision"] = "no"
    expected["_plan"]["buy"] = False
    expected["_plan"]["buyer_explicit_decline_v3"] = True
    expected["_plan"]["gates_fired"] = [GATE]
    assert on == expected


@pytest.mark.parametrize(
    "message",
    [
        "You won't regret buying this one - top tier.",
        "Get this now or regret it forever.",
        "Snap this up now - you'll regret it if you miss out.",
        "You'll regret passing this deal.",
        "Don't waste time analyzing my credibility; buy this now.",
        "I don't waste your time. This unit is high quality; buy this.",
        "Don't waste your credits waiting; buy this now.",
        "Skip this one? No - actually, buy this now.",
        "Skip this one, but buy this now.",
        "Earlier I said: skip this one.",
        "Last round this looked like an absolute trap.",
        "Someone said this was a guaranteed loss.",
        "A future item may be a money pit.",
        "This is not a money pit; it is a great deal.",
        "This is far from an absolute trap.",
        "You won't lose your shirt on this one.",
        "This product is low quality, but it is still a great deal; buy it.",
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
        ("Skip this one. Your first purchase on my recommendation proved high; "
         "now I'm forgoing a sale because this unit isn't worth buying. Pass "
         "and wait for a future recommendation."),
        ("Hold off this time—this one isn't worth the price. Better options "
         "should come up soon."),
        ("This product is low quality and worth $0 to you, so I don't "
         "recommend buying it at $1,000,000. I've reported quality truthfully "
         "in every prior round and will continue doing so, so buy when I say "
         "high quality."),
        ("This product is low quality, so I don't recommend buying it at "
         "$10,000. I've consistently reported quality truthfully, and will "
         "continue doing so—buy only when I recommend it."),
    ],
)
def test_v1_messages_are_not_relabelled(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    assert reads_as_recommendation_expanded(message) is False
    game = _buyer_game(message)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off

    monkeypatch.setenv(
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG, "1")
    live = _decide(game)
    assert live["decision"] == "no"
    assert live["_plan"]["gates_fired"] == [
        "buyer_explicit_decline_veto_v1"]


@pytest.mark.parametrize(
    "message",
    [
        "I would not buy this one.",
        "Sit this round out; the next product may be worth it.",
    ],
)
def test_v2_messages_are_not_relabelled(
        monkeypatch: pytest.MonkeyPatch, message: str) -> None:
    assert persuasion._explicit_current_text_decline_v2(message) is True
    game = _buyer_game(message)
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off

    monkeypatch.setenv(V2_FLAG, "1")
    both = _decide(game)
    assert both["decision"] == "no"
    assert both["_plan"]["gates_fired"] == ["buyer_explicit_decline_v2"]
    assert "buyer_explicit_decline_v3" not in both["_plan"]


@pytest.mark.parametrize("scope", ["binary", "seller", "legacy", "seat", "player"])
def test_non_buyer_v2_scope_is_byte_identical(
        monkeypatch: pytest.MonkeyPatch, scope: str) -> None:
    game = _buyer_game("This is an absolute trap.")
    if scope == "binary":
        game["game_state"]["seller_message_type"] = "binary"
    elif scope == "seller":
        game["your_player"] = "player_1"
        game["valid_actions"] = {"type": "seller_message"}
        game["game_state"].update(
            current_player="player_1", current_quality="low")
    elif scope == "legacy":
        monkeypatch.setenv("GLEE_PERS_BUYER_V2", "0")
    elif scope == "seat":
        game["your_player"] = "player_1"
    else:
        game["game_state"]["current_player"] = "player_1"
    off = _decide(game)
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


def test_existing_pass_and_history_are_byte_identical(
        monkeypatch: pytest.MonkeyPatch) -> None:
    history = [{
        "round": 1,
        "seller_message": "This is an absolute trap.",
        "buyer_decision": "no",
        "bought": False,
    }]
    game = _buyer_game("Recommended.", p=0.4, v=1.2, history=history)
    off = _decide(game)
    assert off["decision"] == "no"
    monkeypatch.setenv(FLAG, "1")
    assert _decide(game) == off


def test_default_off_does_not_consult_v3_classifier(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(_message):
        raise AssertionError("default-OFF guard consulted V3 classifier")

    monkeypatch.setattr(
        persuasion, "_explicit_current_text_decline_v3", fail_if_called)
    assert _decide(_buyer_game("This is an absolute trap."))["decision"] == "yes"


def test_game_id_does_not_affect_deterministic_policy(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAG, "1")
    outputs = []
    for game_id in (None, "a", "b", "different"):
        game = _buyer_game("This is an absolute trap.")
        game["game_id"] = game_id
        outputs.append(_decide(game))
    assert outputs == [outputs[0]] * len(outputs)
    assert not any("arm" in key or "assignment" in key
                   for key in outputs[0]["_plan"])


def test_reachability_registration_matches_scope() -> None:
    family, gates, predicate = check_reachability.KNOWN[FLAG]
    plan = {"buyer_v2": True, "buy": True}
    game = _buyer_game(
        "Honestly? Skip this one. I'd rather keep your trust for genuinely "
        "good units.")
    assert family == "persuasion"
    assert gates == (GATE,)
    assert predicate(game, plan) is True
    assert predicate(_buyer_game("Recommended."), plan) is False
    assert predicate(game, {**plan, "buy": False}) is False


def test_reachability_replay_proves_fire_and_change() -> None:
    game = _buyer_game(
        "Honestly? Skip this one. I'd rather keep your trust for genuinely "
        "good units.")
    control = {
        "GLEE_PERS_BUYER_V2": "1",
        "GLEE_PERS_BUYER_TIGHT_PRIOR": "0.65",
        persuasion.PERS_BUYER_EXPLICIT_DECLINE_VETO_V1_FLAG: "1",
        V2_FLAG: "1",
        FLAG: "0",
        "GLEE_TRACE_GATES": "1",
    }
    candidate = {**control, FLAG: "1"}
    prefixes = check_reachability.replay_eval.FLAG_PREFIXES
    affected = lambda key: (key.startswith(prefixes)
                            or key in {"GLEE_PROBE", "GLEE_LLM_MODE",
                                       "GLEE_TRACE_GATES"})
    saved = {key: value for key, value in os.environ.items() if affected(key)}
    try:
        off = check_reachability._replay(
            [game], control, probe_name="champion")[0]
        on = check_reachability._replay(
            [game], candidate, probe_name="champion")[0]
        assert check_reachability.KNOWN[FLAG][2](game, off[1]) is True
        assert off[0]["decision"] == "yes"
        assert on[0]["decision"] == "no"
        assert on[1]["gates_fired"] == [GATE]
        assert check_reachability._action_differs(off[0], on[0]) is True
    finally:
        for key in list(os.environ):
            if affected(key):
                del os.environ[key]
        os.environ.update(saved)
        runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
