from __future__ import annotations

import copy

from glee_agent import runtime_flags, top_buyer_clone
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation


def _game(*, gid="clone-candidate", own=120.0, other=None,
          complete=False, known=True, cap=10, round_no=1,
          phase="decision", history=None, offer=149.0, role="buyer"):
    me, them = "player_2", "player_1"
    state = {
        "game_family": "negotiation",
        "round": round_no,
        "horizon_known": known,
        "complete_information": complete,
        "messages_allowed": False,
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
        state["last_offer"] = {"price": offer, "from_player": them,
                               "round": round_no}
    return {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": phase},
    }


def _candidate_gid(prefix="clone"):
    for i in range(1000):
        gid = f"{prefix}-{i}"
        if top_buyer_clone.treatment_assignment(gid) is True:
            return gid
    raise AssertionError("no candidate id")


def _control_gid(prefix="clone"):
    for i in range(1000):
        gid = f"{prefix}-{i}"
        if top_buyer_clone.treatment_assignment(gid) is False:
            return gid
    raise AssertionError("no control id")


def _prior_price(round_no, price, me="player_2"):
    return {"round": round_no,
            "offer": {"price": price, "from_player": me, "round": round_no},
            "decision": "RejectOffer", "decided_by": "player_1"}


def test_assignment_is_stable_and_balanced():
    bits = [top_buyer_clone.treatment_assignment(f"g-{i}") for i in range(2000)]
    assert bits == [top_buyer_clone.treatment_assignment(f"g-{i}")
                    for i in range(2000)]
    assert 900 < sum(bits) < 1100
    assert top_buyer_clone.treatment_assignment(None) is None


def test_default_off_and_hash_control_preserve_current_policy(monkeypatch):
    monkeypatch.delenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", raising=False)
    assert not top_buyer_clone.owns(_game(gid=_candidate_gid()))
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    assert not top_buyer_clone.owns(_game(gid=_control_gid()))


def test_hidden_buyer_12_replays_exact_7aidara_path(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("clod")
    prices = []
    history = []
    for idx, expected in enumerate((86.0, 86.0, 86.0, 103.0, 103.0)):
        game = _game(gid=gid, own=120.0, phase="decision",
                     round_no=min(2 * idx + 1, 9), history=history, offer=149.0)
        action = top_buyer_clone.action(game)
        prices.append(action["product_price"])
        assert action["decision"] == "RejectOffer"
        assert action["product_price"] == round(expected, 2)
        history.append(_prior_price(2 * idx + 2, action["product_price"]))
    assert prices == [86.0, 86.0, 86.0, 103.0, 103.0]


def test_hidden_paths_are_type_conditioned_literal_price_families(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("support")
    history = [_prior_price(2 * i + 2, 10 + i) for i in range(4)]
    expected = {80.0: 71.69, 100.0: 83.0, 120.0: 103.0, 150.0: 124.5}
    for own, price in expected.items():
        action = top_buyer_clone.action(
            _game(gid=gid, own=own, history=history, round_no=9))
        assert action["product_price"] == price


def test_hidden_accepts_path_endpoint_and_rejects_worse_price(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("accept")
    good = top_buyer_clone.action(_game(gid=gid, own=120.0, offer=103.0))
    bad = top_buyer_clone.action(_game(gid=gid, own=120.0, offer=103.01))
    assert good["decision"] == "AcceptOffer"
    assert bad["decision"] == "RejectOffer"


def test_complete_cap10_uses_frozen_leader_zone_path(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("visible")
    history = []
    expected_shares = top_buyer_clone.COMPLETE_CAP10
    for idx, share in enumerate(expected_shares):
        game = _game(gid=gid, own=150.0, other=100.0, complete=True,
                     history=history, round_no=min(2 * idx + 1, 9), offer=149.0)
        action = top_buyer_clone.action(game)
        assert action["product_price"] == round(150.0 - share * 50.0, 2)
        history.append(_prior_price(2 * idx + 2, action["product_price"]))


def test_complete_acceptance_floor_is_terminal_leader_share(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("visible-accept")
    ceiling = 150.0 - top_buyer_clone.COMPLETE_CAP10[-1] * 50.0
    assert top_buyer_clone.action(
        _game(gid=gid, own=150.0, other=100.0, complete=True,
              offer=ceiling))["decision"] == "AcceptOffer"
    assert top_buyer_clone.action(
        _game(gid=gid, own=150.0, other=100.0, complete=True,
              offer=ceiling + 0.01))["decision"] == "RejectOffer"


def test_actual_terminal_receiver_accepts_any_positive(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("terminal")
    assert top_buyer_clone.action(
        _game(gid=gid, own=120.0, round_no=10, offer=119.99))["decision"] == "AcceptOffer"
    assert top_buyer_clone.action(
        _game(gid=gid, own=120.0, round_no=10, offer=120.0))["decision"] == "RejectOffer"


def test_unknown_hidden_walks_after_eight_prices(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("walk")
    history = [_prior_price(2 * i + 2, 70 + i) for i in range(8)]
    action = top_buyer_clone.action(
        _game(gid=gid, own=120.0, known=False, history=history,
              round_no=17, offer=149.0))
    assert action["decision"] == "WalkAway"


def test_seller_and_bargaining_are_never_owned(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    gid = _candidate_gid("isolation")
    assert not top_buyer_clone.owns(_game(gid=gid, role="seller"))
    bargaining = _game(gid=gid)
    bargaining["game_family"] = "bargaining"
    assert not top_buyer_clone.owns(bargaining)


def test_candidate_bypasses_all_later_price_guards(monkeypatch):
    gid = _candidate_gid("wire")
    game = _game(gid=gid, own=120.0, offer=149.0)
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.99")
    monkeypatch.setenv("GLEE_NEGO_TABLE", "1")
    raw = negotiation.decide(copy.deepcopy(game), Config.from_env())
    wire = coerce(raw, copy.deepcopy(game))
    assert raw["_plan"]["source"] == "top_buyer_clone"
    assert wire["product_price"] == raw["product_price"]


def test_message_enabled_counter_copies_exact_7aidara_sentence(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    game = _game(gid=_candidate_gid("message"), own=120.0, offer=149.0)
    game["game_state"]["messages_allowed"] = True
    action = top_buyer_clone.action(game)
    assert action["message"] == top_buyer_clone.BUYER_COUNTER_MESSAGE


def test_message_disabled_counter_remains_silent(monkeypatch):
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "1")
    action = top_buyer_clone.action(
        _game(gid=_candidate_gid("silent"), own=120.0, offer=149.0))
    assert "message" not in action
