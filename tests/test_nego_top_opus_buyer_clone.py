from __future__ import annotations

import copy
import hashlib

import pytest

from glee_agent import top_opus_buyer_clone as clone
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation


NEW_FLAG = "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB"
OLD_FLAG = "GLEE_NEGO_TOP_BUYER_CLONE_AB"


@pytest.fixture(autouse=True)
def _flags_off(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.delenv(NEW_FLAG, raising=False)
    monkeypatch.delenv(OLD_FLAG, raising=False)


def _candidate_gid(prefix="opus"):
    for index in range(1000):
        gid = f"{prefix}-{index}"
        if clone.treatment_assignment(gid) is True:
            return gid
    raise AssertionError("no treatment id")


def _control_gid(prefix="opus"):
    for index in range(1000):
        gid = f"{prefix}-{index}"
        if clone.treatment_assignment(gid) is False:
            return gid
    raise AssertionError("no control id")


def _prior_price(round_no, price, me="player_2"):
    return {
        "round": round_no,
        "offer": {"price": price, "from_player": me, "round": round_no},
        "decision": "RejectOffer",
        "decided_by": "player_1",
    }


def _history(count, me="player_2"):
    return [_prior_price(2 * index + 2, 10.0 + index, me)
            for index in range(count)]


def _game(*, gid=None, own=120.0, other=None, complete=False,
          known=True, cap=10, round_no=1, phase="decision", offer=149.0,
          history=None, role="buyer", messages=False, family="negotiation"):
    me, them = "player_2", "player_1"
    state = {
        "game_family": family,
        "round": round_no,
        "horizon_known": known,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": me,
        f"{me}_role": role,
        f"{them}_role": "seller" if role == "buyer" else "buyer",
        f"{me}_value": own,
        "history": list(history or []),
    }
    if known:
        state["max_rounds"] = cap
    if other is not None:
        state[f"{them}_value"] = other
    if phase == "decision":
        state["last_offer"] = {
            "price": offer,
            "from_player": them,
            "round": round_no,
        }
    return {
        "game_id": gid or _candidate_gid(),
        "game_family": family,
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": phase},
    }


def _on(monkeypatch):
    monkeypatch.setenv(NEW_FLAG, "1")


def test_assignment_is_stable_balanced_and_fails_closed():
    bits = [clone.treatment_assignment(f"game-{i}") for i in range(2000)]
    assert bits == [clone.treatment_assignment(f"game-{i}")
                    for i in range(2000)]
    assert 900 < sum(bits) < 1100
    assert clone.treatment_assignment(None) is None
    assert clone.treatment_assignment(42) is None
    assert clone.treatment_assignment("  ") is None


def test_default_off_hash_control_and_old_clone_collision(monkeypatch):
    candidate = _game(gid=_candidate_gid("candidate"))
    assert not clone.owns(candidate)
    assert clone.action(candidate) is None

    _on(monkeypatch)
    assert not clone.owns(_game(gid=_control_gid("control")))
    assert clone.owns(candidate)

    monkeypatch.setenv(OLD_FLAG, "1")
    assert not clone.owns(candidate)
    assert clone.action(candidate) is None


def test_only_negotiation_buyer_seat_is_eligible(monkeypatch):
    _on(monkeypatch)
    assert clone.owns(_game())
    sdk_shape = _game()
    sdk_shape["game_state"].pop("game_family")
    assert clone.owns(sdk_shape)
    assert not clone.owns(_game(role="seller"))
    assert not clone.owns(_game(family="bargaining"))


@pytest.mark.parametrize("mutation", [
    lambda game: game.pop("game_state"),
    lambda game: game["game_state"].pop("history"),
    lambda game: game["game_state"].__setitem__("history", [None]),
    lambda game: game["game_state"].__setitem__("round", "1"),
    lambda game: game["game_state"].__setitem__("complete_information", None),
    lambda game: game["game_state"].__setitem__("player_2_value", float("nan")),
    lambda game: game["game_state"].__setitem__("last_offer", {"price": 149.0}),
])
def test_missing_or_malformed_state_fails_closed(monkeypatch, mutation):
    _on(monkeypatch)
    game = _game()
    mutation(game)
    assert not clone.eligible(game)
    assert not clone.owns(game)
    assert clone.action(game) is None


def test_complete_cap10_replays_exact_observed_first_four(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("complete-cap10")
    expected = (806000.00, 806058.53, 806936.44, 810740.74)
    history = []
    for index, price in enumerate(expected):
        action = clone.action(_game(
            gid=gid,
            own=1_000_000.0,
            other=800_000.0,
            complete=True,
            round_no=2 * index + 1,
            offer=900_000.0,
            history=history,
        ))
        assert action["decision"] == "RejectOffer"
        assert action["product_price"] == price
        assert action["_plan"]["source"] == "top_opus_buyer_clone"
        history.append(_prior_price(2 * index + 2, price))

    # The observed fifth price selected among .02/.10/.20 of the visible zone;
    # no public state identified that selector, so the current policy owns it.
    assert clone.action(_game(
        gid=gid,
        own=1_000_000.0,
        other=800_000.0,
        complete=True,
        round_no=9,
        offer=900_000.0,
        history=history,
    )) is None


def test_hidden_cap10_replays_exact_scaled_first_four(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("hidden-cap10")
    expected = (812000.00, 812490.17, 819842.71, 851703.70)
    history = []
    for index, price in enumerate(expected):
        action = clone.action(_game(
            gid=gid,
            own=1_200_000.0,
            round_no=2 * index + 1,
            offer=1_300_000.0,
            history=history,
        ))
        assert action["decision"] == "RejectOffer"
        assert action["product_price"] == price
        history.append(_prior_price(2 * index + 2, price))

    assert clone.action(_game(
        gid=gid,
        own=1_200_000.0,
        round_no=9,
        offer=1_300_000.0,
        history=history,
    )) is None
    assert clone.HIDDEN_CAP10_UNIDENTIFIED_FIFTH_BY_TYPE == (
        (1.0, 0.824000000000),
        (1.2, 0.686666666667),
        (1.5, 0.686666666667),
    )


def test_hidden_unknown_replays_all_observed_coefficients_then_falls_back(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("hidden-unknown")

    first = clone.action(_game(
        gid=gid,
        own=1_000_000.0,
        known=False,
        round_no=1,
        offer=1_400_000.0,
    ))
    assert first["product_price"] == 676666.67

    history = _history(42)
    forty_third = clone.action(_game(
        gid=gid,
        own=1_000_000.0,
        known=False,
        round_no=85,
        offer=1_400_000.0,
        history=history,
    ))
    assert len(clone.HIDDEN_UNKNOWN_COEFFICIENTS) == 43
    assert forty_third["product_price"] == 767078.99

    assert clone.action(_game(
        gid=gid,
        own=1_000_000.0,
        known=False,
        round_no=87,
        offer=1_400_000.0,
        history=_history(43),
    )) is None
    assert clone.HIDDEN_UNKNOWN_UNIDENTIFIED_HOLD_COUNT == 6
    assert clone.HIDDEN_UNKNOWN_UNIDENTIFIED_B_FLOOR == 0.824
    assert clone.HIDDEN_UNKNOWN_UNIDENTIFIED_FINAL_COEFFICIENT == 0.84416667


def test_reject_is_copied_only_for_incoming_price_worse_than_wire(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("reject-boundary")
    worse = clone.action(_game(gid=gid, own=120.0, offer=90.0))
    equal = clone.action(_game(gid=gid, own=120.0, offer=81.2))
    better = clone.action(_game(gid=gid, own=120.0, offer=80.0))
    assert worse["decision"] == "RejectOffer"
    assert worse["product_price"] == 81.2
    assert equal is None
    assert better is None


def test_dispatch_preserves_copied_wire_but_not_unidentified_fallback(
        monkeypatch):
    _on(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.99")
    gid = next(
        candidate
        for index in range(10_000)
        for candidate in (f"dispatch-{index}",)
        if (clone.treatment_assignment(candidate) is True
            and int(hashlib.sha256(
                ("hidden_floor|" + candidate).encode()).hexdigest(), 16) & 1)
    )

    copied_game = _game(gid=gid, own=120.0, offer=149.0)
    raw = negotiation.decide(copy.deepcopy(copied_game), Config.from_env())
    copied_wire = coerce(raw, copy.deepcopy(copied_game))
    assert raw["_plan"]["source"] == "top_opus_buyer_clone"
    assert copied_wire["product_price"] == 81.2

    # Known horizon 20 has no observed Opus wire.  It must execute the current
    # policy including the live hidden-price postcondition, not gain an
    # accidental exemption merely because the game hash is candidate.
    fallback_game = _game(
        gid=gid, own=120.0, cap=20, round_no=1, offer=149.0)
    assert clone.owns(fallback_game)
    assert clone.action(fallback_game) is None
    fallback_raw = negotiation.decide(
        copy.deepcopy(fallback_game), Config.from_env())
    fallback_wire = coerce(fallback_raw, copy.deepcopy(fallback_game))
    assert fallback_wire["product_price"] <= 1.0


def test_observed_acceptance_states_are_time_and_type_conditioned(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("accept")

    complete_single = _game(
        gid=gid, own=1_200_000.0, other=1_000_000.0,
        complete=True, cap=1, round_no=1, offer=1_078_000.0)
    assert clone.action(complete_single)["decision"] == "AcceptOffer"
    worse = copy.deepcopy(complete_single)
    worse["game_state"]["last_offer"]["price"] = 1_078_000.01
    assert clone.action(worse) is None

    hidden_single = _game(
        gid=gid, own=10_000.0, cap=1, round_no=1, offer=9_500.0)
    assert clone.action(hidden_single)["decision"] == "AcceptOffer"

    late_history = _history(31)
    late = _game(
        gid=gid, own=100.0, known=False, round_no=63,
        offer=80.0, history=late_history)
    assert clone.action(late)["decision"] == "AcceptOffer"
    early = _game(
        gid=gid, own=100.0, known=False, round_no=61,
        offer=80.0, history=_history(30))
    assert clone.action(early)["decision"] == "RejectOffer"


def test_complete_unknown_late_accepts_do_not_generalize_early(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("complete-unknown-accept")
    late = _game(
        gid=gid, own=120.0, other=80.0, complete=True, known=False,
        round_no=67, offer=96.0, history=_history(33))
    assert clone.action(late)["decision"] == "AcceptOffer"

    early = _game(
        gid=gid, own=120.0, other=80.0, complete=True, known=False,
        round_no=65, offer=96.0, history=_history(32))
    assert clone.action(early) is None


def test_only_observed_hidden_point8_family_walks(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("walk")
    walked = clone.action(_game(
        gid=gid, own=80.0, known=False, round_no=1, offer=397.06))
    assert walked["decision"] == "WalkAway"
    assert walked["_plan"]["source"] == "top_opus_buyer_clone"

    # Hidden cap-1 mixed WalkAway and RejectOffer in the corpus, so it falls back.
    assert clone.action(_game(
        gid=gid, own=80.0, cap=1, round_no=1, offer=108.8)) is None


def test_exact_opus_message_template_only_when_messages_are_allowed(monkeypatch):
    _on(monkeypatch)
    gid = _candidate_gid("message")
    action = clone.action(_game(
        gid=gid,
        own=1_200_000.0,
        offer=1_400_000.0,
        messages=True,
    ))
    assert action["message"] == (
        "812,000 is what this is worth to me. "
        "Above that the purchase stops making sense."
    )

    silent = clone.action(_game(
        gid=gid,
        own=1_200_000.0,
        offer=1_400_000.0,
        messages=False,
    ))
    assert "message" not in silent
