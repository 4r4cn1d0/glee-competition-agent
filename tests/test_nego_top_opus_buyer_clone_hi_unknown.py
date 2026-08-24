from __future__ import annotations

import copy

import pytest

from glee_agent import (top_opus_buyer_clone,
                        top_opus_buyer_clone_hi_unknown as clone)
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation


NEW_FLAG = "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB"
CONFLICTS = (
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_ATHENA_BUYER_CLONE_AB",
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB",
    "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB",
    "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
    "GLEE_NEGO_CLOSE_AB",
    "GLEE_NEGO_PROBE_V1",
)


@pytest.fixture(autouse=True)
def _flags_off(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.delenv(NEW_FLAG, raising=False)
    monkeypatch.delenv("GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB", raising=False)
    monkeypatch.delenv("GLEE_NEGO_HIDDEN_FLOOR", raising=False)
    for flag in CONFLICTS:
        monkeypatch.delenv(flag, raising=False)


def _gid(candidate: bool, prefix: str = "opus-hi-unknown") -> str:
    for index in range(10_000):
        game_id = f"{prefix}-{index}"
        if clone.treatment_assignment(game_id) is candidate:
            return game_id
    raise AssertionError("no game id for requested arm")


def _prior_price(round_no: int, price: float) -> dict:
    return {
        "round": round_no,
        "offer": {
            "price": price,
            "from_player": "player_2",
            "round": round_no,
        },
        "decision": "RejectOffer",
        "decided_by": "player_1",
    }


def _history(count: int) -> list[dict]:
    return [_prior_price(2 * index + 2, 10.0 + index)
            for index in range(count)]


def _game(*, game_id: str | None = None, own: float = 120.0,
          round_no: int = 1, offer: float = 149.0,
          history: list[dict] | None = None, messages: bool = False,
          complete: bool = False, known: bool = False,
          max_rounds: int | None = None, role: str = "buyer",
          family: str = "negotiation") -> dict:
    me, other = "player_2", "player_1"
    state = {
        "game_family": family,
        "round": round_no,
        "horizon_known": known,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": me,
        f"{me}_role": role,
        f"{other}_role": "seller" if role == "buyer" else "buyer",
        f"{me}_value": own,
        "history": list(history or []),
        "last_offer": {
            "price": offer,
            "from_player": other,
            "round": round_no,
        },
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    return {
        "game_id": game_id or _gid(True),
        "game_family": family,
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": "decision"},
    }


def _on(monkeypatch):
    monkeypatch.setenv(NEW_FLAG, "1")


def test_assignment_is_stable_balanced_and_fails_closed():
    bits = [clone.treatment_assignment(f"game-{index}")
            for index in range(2000)]
    assert bits == [clone.treatment_assignment(f"game-{index}")
                    for index in range(2000)]
    assert 900 < sum(bits) < 1100
    assert clone.treatment_assignment(None) is None
    assert clone.treatment_assignment(7) is None
    assert clone.treatment_assignment(" ") is None


def test_default_off_hash_control_and_conflicts_fail_closed(monkeypatch):
    candidate = _game(game_id=_gid(True, "candidate"))
    control = _game(game_id=_gid(False, "control"))
    assert clone.eligible(candidate)
    assert not clone.owns(candidate)

    _on(monkeypatch)
    assert clone.owns(candidate)
    assert not clone.owns(control)
    for flag in CONFLICTS:
        monkeypatch.setenv(flag, "1")
        assert not clone.enabled()
        assert not clone.owns(candidate)
        monkeypatch.delenv(flag)

    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "0.01")
    assert not clone.enabled()


def test_known_cap10_clone_can_coexist_because_scope_is_disjoint(monkeypatch):
    _on(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB", "1")
    unknown = _game(game_id=_gid(True, "coexist"))
    assert clone.enabled()
    assert clone.owns(unknown)

    cap10 = copy.deepcopy(unknown)
    cap10["game_state"]["horizon_known"] = True
    cap10["game_state"]["max_rounds"] = 10
    assert not clone.eligible(cap10)


@pytest.mark.parametrize("own,expected", [
    (100.0, 67.67),
    (120.0, 81.2),
    (150.0, 101.5),
])
def test_first_hidden_unknown_wire_copies_exact_opus_coefficient(
        monkeypatch, own, expected):
    _on(monkeypatch)
    game = _game(game_id=_gid(True, f"type-{own}"), own=own,
                 offer=own + 40.0)
    scoped = clone.action(game)
    observed = top_opus_buyer_clone.identified_action(game)
    assert scoped["decision"] == "RejectOffer"
    assert scoped["product_price"] == expected
    assert scoped["product_price"] == observed["product_price"]
    assert scoped["_plan"] == {
        **observed["_plan"],
        "source": "top_opus_buyer_clone_hi_unknown",
    }


def test_structurally_dead_type_and_other_regimes_fall_through(monkeypatch):
    _on(monkeypatch)
    assert not clone.eligible(_game(own=80.0, offer=397.06))
    assert not clone.eligible(_game(known=True, max_rounds=10))
    assert not clone.eligible(_game(known=True, max_rounds=1))
    assert not clone.eligible(_game(complete=True))
    assert not clone.eligible(_game(role="seller"))
    assert not clone.eligible(_game(family="bargaining"))

    outgoing = _game()
    outgoing["valid_actions"]["type"] = "offer"
    outgoing["game_state"].pop("last_offer")
    assert not clone.eligible(outgoing)

    leaked_cap = _game()
    leaked_cap["game_state"]["max_rounds"] = 99
    assert not clone.eligible(leaked_cap)

    null_cap = _game()
    null_cap["game_state"]["max_rounds"] = None
    assert not clone.eligible(null_cap)


def test_message_and_late_fallback_are_literal(monkeypatch):
    _on(monkeypatch)
    game = _game(game_id=_gid(True, "message"), own=1_200_000.0,
                 offer=1_400_000.0, messages=True)
    action = clone.action(game)
    assert action["message"] == (
        "812,000 is what this is worth to me. "
        "Above that the purchase stops making sense."
    )

    # Coefficient 43 is the frozen evidence boundary. Candidate assignment
    # remains in the ITT cohort, but this turn must execute full control.
    late = _game(game_id=_gid(True, "late"), own=120.0,
                 round_no=87, offer=149.0, history=_history(43))
    assert clone.owns(late)
    assert clone.action(late) is None


def test_dispatch_and_coerce_preserve_only_supported_scoped_wire(monkeypatch):
    _on(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB", "1")
    game = _game(game_id=_gid(True, "dispatch"), own=120.0, offer=149.0)
    raw = negotiation.decide(copy.deepcopy(game), Config.from_env())
    wire = coerce(raw, copy.deepcopy(game))
    assert raw["_plan"]["source"] == clone.PLAN_SOURCE
    assert raw["product_price"] == 81.2
    assert wire["product_price"] == 81.2
    assert clone.matches_wire(game, raw)

    control = _game(game_id=_gid(False, "dispatch-control"),
                    own=120.0, offer=149.0)
    control_raw = negotiation.decide(copy.deepcopy(control), Config.from_env())
    assert (control_raw.get("_plan") or {}).get("source") != clone.PLAN_SOURCE
    assert not clone.matches_wire(control, clone.action(control))


@pytest.mark.parametrize("mutation", [
    lambda game: game.pop("game_state"),
    lambda game: game["game_state"].pop("history"),
    lambda game: game["game_state"].__setitem__("history", [None]),
    lambda game: game["game_state"].__setitem__("round", "1"),
    lambda game: game["game_state"].__setitem__("horizon_known", None),
    lambda game: game["game_state"].__setitem__("player_2_value", float("nan")),
    lambda game: game["game_state"].__setitem__("last_offer", {"price": 149.0}),
])
def test_malformed_states_fail_closed(monkeypatch, mutation):
    _on(monkeypatch)
    game = _game()
    mutation(game)
    assert not clone.eligible(game)
    assert not clone.owns(game)
    assert clone.action(game) is None
