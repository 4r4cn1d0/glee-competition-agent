"""Safety and precedence tests for the exact-name all-family Grok policy."""

from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from glee_agent import actions, dispatch, grok_suppression, runtime_flags
from glee_agent.config import Config
from glee_agent.probes import make_probe


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.delenv(grok_suppression.FLAG, raising=False)
    monkeypatch.delenv("GLEE_LLM_FAMILIES", raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _game(family: str, action_type: str, state: dict, *,
          me: str = "player_1", name: str | None = "grok 4.6") -> dict:
    state = dict(state)
    state.setdefault("current_player", me)
    state.setdefault("round", 1)
    return {
        "game_id": f"{family}-{action_type}-{me}",
        "game_family": family,
        "your_player": me,
        "phase": action_type,
        "opponent": ({"type": "agent", "name": name}
                     if name is not None else {"type": "hidden", "name": None}),
        "game_state": state,
        "valid_actions": {"type": action_type},
    }


def _enable(monkeypatch) -> None:
    monkeypatch.setenv(grok_suppression.FLAG, "1")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _barg_offer(*, me="player_1", name="grok 4.6") -> dict:
    return _game(
        "bargaining",
        "offer",
        {
            "money_to_divide": 100,
            "horizon_known": True,
            "max_rounds": 12,
            "complete_information": True,
            "messages_allowed": True,
        },
        me=me,
        name=name,
    )


def _nego(*, action_type="offer", me="player_1", role="seller",
          complete=True, my_value=100.0, their_value=150.0,
          price=None, round_no=1, max_rounds=10, name="grok 4.6") -> dict:
    them = "player_2" if me == "player_1" else "player_1"
    state = {
        "round": round_no,
        "max_rounds": max_rounds,
        "horizon_known": True,
        "complete_information": complete,
        "messages_allowed": False,
        f"{me}_role": role,
        f"{them}_role": "buyer" if role == "seller" else "seller",
        f"{me}_value": my_value,
    }
    if complete:
        state[f"{them}_value"] = their_value
    if action_type == "decision":
        state["last_offer"] = {
            "from_player": them,
            "price": price,
            "round": round_no,
        }
    return _game("negotiation", action_type, state, me=me, name=name)


def _pers(action_type: str, *, quality="high", name="grok 4.6") -> dict:
    state = {
        "round": 1,
        "total_rounds": 20,
        "product_price": 100,
        "p": 0.5,
        "v": 200,
        "u": 0,
        "seller_message_type": (
            "text" if action_type == "seller_message" else "binary"
        ),
        "current_quality": quality,
        "history": [],
    }
    me = "player_2" if action_type == "buyer_decision" else "player_1"
    return _game("persuasion", action_type, state, me=me, name=name)


def test_default_off_and_non_target_are_inert(monkeypatch) -> None:
    target = _barg_offer()
    assert grok_suppression.eligible(target) is True
    assert grok_suppression.action(target) is None

    _enable(monkeypatch)
    hidden = _barg_offer(name=None)
    other = _barg_offer(name="Athena")
    similar = _barg_offer(name="grok 4.6 clone")
    assert grok_suppression.action(hidden) is None
    assert grok_suppression.action(other) is None
    assert grok_suppression.action(similar) is None


def test_direct_name_normalization_is_conservative(monkeypatch) -> None:
    _enable(monkeypatch)
    game = _barg_offer(name="  GROK   4.6 ")
    assert grok_suppression.matches(game) is True
    assert grok_suppression.action(game) is not None


@pytest.mark.parametrize(
    ("me", "expected"),
    [
        ("player_1", {"alice_gain": 100.0, "bob_gain": 0.0}),
        ("player_2", {"alice_gain": 0.0, "bob_gain": 100.0}),
    ],
)
def test_bargaining_offer_gives_grok_zero(monkeypatch, me, expected) -> None:
    _enable(monkeypatch)
    action = grok_suppression.action(_barg_offer(me=me))
    assert {k: action[k] for k in expected} == expected
    assert action["_plan"]["opponent_payoff_cap"] == 0.0
    assert action["_plan"]["gates_fired"] == [grok_suppression.GATE]


@pytest.mark.parametrize(
    ("alice", "bob", "decision"),
    [(100.0, 0.0, "accept"), (99.99, 0.01, "reject"), (48.0, 52.0, "reject")],
)
def test_bargaining_accepts_only_zero_grok_share(
    monkeypatch, alice, bob, decision,
) -> None:
    _enable(monkeypatch)
    game = _game(
        "bargaining",
        "decision",
        {
            "money_to_divide": 100,
            "last_offer": {"player_1_gain": alice, "player_2_gain": bob},
            "horizon_known": True,
            "max_rounds": 12,
            "complete_information": True,
            "messages_allowed": False,
        },
        me="player_1",
    )
    assert grok_suppression.action(game)["decision"] == decision


@pytest.mark.parametrize(
    ("role", "me", "my_value", "their_value", "expected"),
    [
        ("seller", "player_1", 100.0, 150.0, 150.0),
        ("buyer", "player_2", 150.0, 100.0, 100.0),
    ],
)
def test_complete_negotiation_quotes_grok_zero_profit_boundary(
    monkeypatch, role, me, my_value, their_value, expected,
) -> None:
    _enable(monkeypatch)
    action = grok_suppression.action(_nego(
        role=role, me=me, my_value=my_value, their_value=their_value))
    assert action["product_price"] == expected


@pytest.mark.parametrize(
    ("role", "me", "my_value", "expected"),
    [
        ("seller", "player_1", 100.0, 150.0),
        ("buyer", "player_2", 120.0, 80.0),
        ("seller", "player_1", 1_000_000.0, 1_500_000.0),
        ("buyer", "player_2", 1_200_000.0, 800_000.0),
    ],
)
def test_hidden_negotiation_uses_worst_case_support_boundary(
    monkeypatch, role, me, my_value, expected,
) -> None:
    _enable(monkeypatch)
    action = grok_suppression.action(_nego(
        role=role, me=me, complete=False, my_value=my_value))
    assert action["product_price"] == expected
    assert action["_plan"]["information"] == "hidden"


@pytest.mark.parametrize(
    ("role", "me", "my_value", "their_value", "price", "decision", "counter"),
    [
        ("buyer", "player_2", 150.0, 100.0, 100.0, "AcceptOffer", None),
        ("buyer", "player_2", 150.0, 100.0, 100.01, "RejectOffer", 100.0),
        ("seller", "player_1", 100.0, 150.0, 150.0, "AcceptOffer", None),
        ("seller", "player_1", 100.0, 150.0, 149.99, "RejectOffer", 150.0),
    ],
)
def test_complete_negotiation_accepts_only_zero_grok_profit(
    monkeypatch, role, me, my_value, their_value, price, decision, counter,
) -> None:
    _enable(monkeypatch)
    action = grok_suppression.action(_nego(
        action_type="decision", role=role, me=me, my_value=my_value,
        their_value=their_value, price=price, round_no=3))
    assert action["decision"] == decision
    assert action.get("product_price") == counter


def test_final_negotiation_rejection_has_no_illegal_counter(monkeypatch) -> None:
    _enable(monkeypatch)
    action = grok_suppression.action(_nego(
        action_type="decision", role="buyer", me="player_2",
        my_value=150.0, their_value=100.0, price=119.0,
        round_no=1, max_rounds=1))
    assert action["decision"] == "RejectOffer"
    assert "product_price" not in action


def test_hidden_negotiation_acceptance_is_worst_case_safe(monkeypatch) -> None:
    _enable(monkeypatch)
    seller_safe = grok_suppression.action(_nego(
        action_type="decision", role="seller", me="player_1",
        complete=False, my_value=100.0, price=150.0, round_no=3))
    seller_unsafe = grok_suppression.action(_nego(
        action_type="decision", role="seller", me="player_1",
        complete=False, my_value=100.0, price=149.99, round_no=3))
    buyer_safe = grok_suppression.action(_nego(
        action_type="decision", role="buyer", me="player_2",
        complete=False, my_value=120.0, price=80.0, round_no=3))
    buyer_unsafe = grok_suppression.action(_nego(
        action_type="decision", role="buyer", me="player_2",
        complete=False, my_value=120.0, price=80.01, round_no=3))
    assert seller_safe["decision"] == "AcceptOffer"
    assert seller_unsafe["decision"] == "RejectOffer"
    assert buyer_safe["decision"] == "AcceptOffer"
    assert buyer_unsafe["decision"] == "RejectOffer"


def test_persuasion_denies_sales_without_revealing_quality(monkeypatch) -> None:
    _enable(monkeypatch)
    assert grok_suppression.action(_pers("buyer_decision"))["decision"] == "no"
    assert grok_suppression.action(
        _pers("seller_recommendation", quality="high"))["decision"] == "no"
    assert grok_suppression.action(
        _pers("seller_recommendation", quality="low"))["decision"] == "no"
    high = grok_suppression.action(_pers("seller_message", quality="high"))
    low = grok_suppression.action(_pers("seller_message", quality="low"))
    assert high["message"] == low["message"] == grok_suppression.PERSUASION_DECLINE


def test_negotiation_postconditions_cannot_rewrite_owned_boundary(
    monkeypatch,
) -> None:
    _enable(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM", "0.95")
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    game = _nego(role="seller", me="player_1", my_value=100.0,
                 their_value=150.0)
    owned = grok_suppression.action(game)
    wire = actions.coerce(owned, game)
    assert wire == {"product_price": 150.0}


class _Log:
    def __init__(self):
        self.last = None

    def turn(self, game, action, plan, source):
        self.last = (copy.deepcopy(action), copy.deepcopy(plan), source)


def test_dispatch_bypasses_all_llm_and_message_rewriters(monkeypatch) -> None:
    _enable(monkeypatch)
    monkeypatch.setenv("GLEE_LLM_FAMILIES", "persuasion")

    def forbidden(*args, **kwargs):
        raise AssertionError("suppression action reached an LLM/message rewriter")

    monkeypatch.setattr(dispatch.llm, "propose_action", forbidden)
    monkeypatch.setattr(dispatch.llm, "pers_seller_message", forbidden)
    monkeypatch.setattr(dispatch.llm, "write_message", forbidden)
    log = _Log()
    action = dispatch._play(
        _pers("seller_message", quality="high"),
        SimpleNamespace(llm_mode="full"),
        log,
    )
    assert action == {"message": grok_suppression.PERSUASION_DECLINE}
    assert log.last[1]["source"] == grok_suppression.GATE
    assert log.last[2] == "grok-suppression"


@pytest.mark.parametrize(
    ("game", "expected"),
    [
        (_barg_offer(), {"alice_gain": 100.0, "bob_gain": 0.0}),
        (_nego(role="seller", me="player_1", my_value=100.0,
               their_value=150.0), {"product_price": 150.0}),
        (_pers("buyer_decision"), {"decision": "no"}),
    ],
)
def test_randomized_probe_routes_all_families_through_override(
    monkeypatch, game, expected,
) -> None:
    _enable(monkeypatch)
    strategy, _ = make_probe("randomized", Config.from_env(), seed=123)
    action = strategy(copy.deepcopy(game))
    assert action == expected

