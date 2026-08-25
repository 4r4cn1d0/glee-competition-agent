from __future__ import annotations

import copy

import pytest

from glee_agent import deterministic_negotiation as policies
from glee_agent import nego_hidden_terminal_inference
from glee_agent import top_seller_message_clone
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.probes import _composite
from glee_agent.strategies import negotiation


@pytest.fixture(autouse=True)
def _deterministic_flags_off(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "0")
    monkeypatch.setenv(policies.LEADER_REPLICA_FLAG, "0")
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "0")
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_AB", "0")
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB", "0")
    monkeypatch.setenv("GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB", "0")
    monkeypatch.setenv("GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB", "0")
    monkeypatch.setenv("GLEE_NEGO_MSG_ARMS", "0")


def _prior_price(round_no: int, price: float, me: str = "player_2") -> dict:
    return {
        "round": round_no,
        "offer": {
            "price": price,
            "from_player": me,
            "round": round_no,
        },
        "decision": "RejectOffer",
        "decided_by": "player_1",
    }


def _seller_price(round_no: int, price: float) -> dict:
    return {
        "round": round_no,
        "offer": {
            "price": price,
            "from_player": "player_1",
            "round": round_no,
        },
        "decision": "RejectOffer",
        "decided_by": "player_2",
    }


def _buyer_game(
    *,
    complete: bool = False,
    known: bool = True,
    cap: int | None = 10,
    own: float = 120.0,
    other: float = 100.0,
    offer: float = 149.0,
    round_no: int = 1,
    history: list[dict] | None = None,
    messages: bool = False,
) -> dict:
    me, them = "player_2", "player_1"
    state = {
        "game_family": "negotiation",
        "round": round_no,
        "horizon_known": known,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": me,
        f"{me}_role": "buyer",
        f"{them}_role": "seller",
        f"{me}_value": own,
        "last_offer": {
            "price": offer,
            "from_player": them,
            "round": round_no,
        },
        "history": list(history or []),
    }
    if known:
        state["max_rounds"] = cap
    if complete:
        state[f"{them}_value"] = other
    return {
        "game_id": "deterministic-policy-game",
        "game_family": "negotiation",
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": "decision"},
    }


def _seller_game() -> dict:
    game = _buyer_game(complete=True, own=100.0, other=120.0, offer=80.0)
    state = game["game_state"]
    state["current_player"] = game["your_player"] = "player_1"
    state["player_1_role"] = "seller"
    state["player_2_role"] = "buyer"
    state["player_1_value"] = 100.0
    state["player_2_value"] = 120.0
    state["last_offer"] = {
        "price": 80.0,
        "from_player": "player_2",
        "round": 1,
    }
    return game


def _terminal_seller_game(*, complete: bool, own: float = 80.0,
                          other: float = 120.0) -> dict:
    game = _seller_game()
    state = game["game_state"]
    state["round"] = 1
    state["max_rounds"] = 1
    state["complete_information"] = complete
    state["player_1_value"] = own
    if complete:
        state["player_2_value"] = other
    else:
        state.pop("player_2_value", None)
    state.pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}
    return game


def _public(action: dict) -> dict:
    return {key: value for key, value in action.items()
            if not str(key).startswith("_")}


def test_named_profiles_do_not_auto_select_a_negotiation_policy():
    cfg = _composite(Config())
    assert not hasattr(cfg, "nego_policy")
    assert policies.mode() is None


@pytest.mark.parametrize(
    "complete,known,cap",
    [
        (True, True, 1),
        (True, True, 10),
        (True, False, None),
        (False, True, 10),
    ],
)
def test_rank_hybrid_owns_complete_and_hidden_cap10_buyers(
    monkeypatch, complete, known, cap,
):
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "1")
    game = _buyer_game(complete=complete, known=known, cap=cap)
    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["_plan"]["source"] == policies.RANK_HYBRID
    assert action["_plan"]["component"] == "observed_leader_buyer"


@pytest.mark.parametrize(
    "known,cap,component",
    [
        (True, 1, "current_hidden_terminal_buyer"),
        (False, None, "current_hidden_unknown_buyer"),
    ],
)
def test_rank_hybrid_keeps_current_hidden_terminal_and_unknown_buyers(
    monkeypatch, known, cap, component,
):
    game = _buyer_game(complete=False, known=known, cap=cap)
    control = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "1")
    candidate = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert _public(candidate) == _public(control)
    assert candidate["_plan"]["deterministic_policy"] == policies.RANK_HYBRID
    assert candidate["_plan"]["component"] == component


def test_full_replica_is_distinct_in_hidden_unknown_horizon(monkeypatch):
    history = [_prior_price(2 * index + 2, 70.0 + index)
               for index in range(8)]
    game = _buyer_game(
        complete=False,
        known=False,
        cap=None,
        history=history,
        round_no=17,
    )
    monkeypatch.setenv(policies.LEADER_REPLICA_FLAG, "1")

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["decision"] == "WalkAway"
    assert action["_plan"]["source"] == policies.LEADER_REPLICA


def test_rank_hybrid_keeps_seller_public_behavior_byte_identical(monkeypatch):
    game = _seller_game()
    control = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "1")
    candidate = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert _public(candidate) == _public(control)
    assert candidate["_plan"]["component"] == "current_seller"


def test_full_replica_adds_only_observed_seller_message(monkeypatch):
    game = _seller_game()
    game["game_state"]["messages_allowed"] = True
    game["valid_actions"] = {"type": "decision"}
    control = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    monkeypatch.setenv(policies.LEADER_REPLICA_FLAG, "1")
    candidate = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert candidate["message"] == top_seller_message_clone.FIRST_PRICE_MESSAGE
    assert top_seller_message_clone.audit_message_only(
        control, candidate, top_seller_message_clone.FIRST_PRICE_MESSAGE,
    )
    assert candidate["_plan"][top_seller_message_clone.PLAN_TRACE]["arm"] == (
        "leader_replica"
    )


def test_both_flags_on_fail_closed_to_the_existing_stack(monkeypatch):
    game = _buyer_game(complete=False, known=True, cap=10)
    control = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "1")
    monkeypatch.setenv(policies.LEADER_REPLICA_FLAG, "1")
    conflicted = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert policies.mode() is None
    assert conflicted == control


def test_deterministic_buyer_wire_owns_downstream_price_guards(monkeypatch):
    game = _buyer_game(complete=False, known=True, cap=10)
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.99")
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    raw = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    wire = coerce(copy.deepcopy(raw), copy.deepcopy(game))

    assert raw["product_price"] == 86.0
    assert wire["product_price"] == raw["product_price"]


def test_deterministic_policy_bypasses_legacy_random_message_bank(
    monkeypatch,
):
    game = _buyer_game(complete=False, known=True, cap=10)
    monkeypatch.setenv(policies.RANK_HYBRID_FLAG, "1")
    monkeypatch.setattr(negotiation.nego_arms, "enabled", lambda: True)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("legacy randomized message bank was called")

    monkeypatch.setattr(negotiation.nego_arms, "attach", forbidden)
    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    assert action["_plan"]["source"] == policies.RANK_HYBRID


def test_agent5_default_is_one_mutually_exclusive_whole_policy(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    assert policies.mode() == policies.AGENT5_DEFAULT

    monkeypatch.setenv(policies.LEADER_REPLICA_FLAG, "1")
    assert policies.mode() is None


def test_agent5_default_hard_precedence_uses_hidden_terminal_rule(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _terminal_seller_game(complete=False, own=80.0)

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["product_price"] == pytest.approx(119.99)
    assert action["_plan"]["source"] == policies.AGENT5_DEFAULT
    assert action["_plan"]["component"] == "first_principles"


def test_agent5_default_hard_precedence_uses_cap10_buyer_cent(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(
        complete=True,
        known=True,
        cap=10,
        own=150.0,
        other=80.0,
        round_no=10,
    )
    game["game_state"].pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["product_price"] == pytest.approx(80.01)
    assert action["_plan"]["source"] == policies.AGENT5_DEFAULT
    assert action["_plan"]["component"] == "first_principles"


def test_agent5_default_uses_observed_leader_for_other_buyer_cells(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(complete=False, known=True, cap=10)

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["_plan"]["source"] == policies.AGENT5_DEFAULT
    assert action["_plan"]["component"] == "observed_leader_buyer"


def test_agent5_owned_price_bypasses_every_downstream_guard(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.99")
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_FLOOR", "0.50")
    monkeypatch.setenv("GLEE_NEGO_ULT_CAP", "0.80")
    monkeypatch.setenv("GLEE_NEGO_ZOPA_CLAMP", "1")
    game = _terminal_seller_game(complete=False, own=80.0)

    raw = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    wire = coerce(copy.deepcopy(raw), copy.deepcopy(game))

    assert raw["product_price"] == pytest.approx(119.99)
    assert wire["product_price"] == raw["product_price"]


def test_agent5_default_names_unreplaced_seller_fallback(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _seller_game()

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["_plan"]["deterministic_policy"] == policies.AGENT5_DEFAULT
    assert action["_plan"]["component"] == "current_seller"


def test_agent5_default_bypasses_randomized_message_attachment(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(complete=False, known=True, cap=10)
    monkeypatch.setattr(negotiation.nego_arms, "enabled", lambda: True)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("legacy randomized message bank was called")

    monkeypatch.setattr(negotiation.nego_arms, "attach", forbidden)
    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    assert action["_plan"]["source"] == policies.AGENT5_DEFAULT


@pytest.mark.parametrize(
    ("seller_ask", "expected"),
    [(97.0, 80.01), (119.0, 100.01), (149.0, 120.01)],
)
def test_agent5_hidden_terminal_uses_seller_ask_as_cost_ceiling(
    monkeypatch, seller_ask, expected,
):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(
        complete=False,
        known=True,
        cap=10,
        own=150.0,
        round_no=10,
        history=[_seller_price(9, seller_ask)],
    )
    game["game_state"].pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["product_price"] == pytest.approx(expected)
    assert action["_plan"]["source"] == policies.AGENT5_DEFAULT
    assert action["_plan"]["component"] == (
        nego_hidden_terminal_inference.COMPONENT)


def test_agent5_hidden_terminal_uses_strongest_observed_bound(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(
        complete=False,
        known=True,
        cap=10,
        own=150.0,
        round_no=10,
        history=[
            _seller_price(1, 149.0),
            _prior_price(2, 81.0),       # our own bid is not evidence
            _seller_price(9, 119.0),
        ],
    )
    game["game_state"].pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))

    assert action["product_price"] == pytest.approx(100.01)
    assert action["_plan"]["lowest_seller_ask"] == pytest.approx(119.0)
    assert action["_plan"]["seller_offer_count"] == 2


def test_agent5_hidden_terminal_inference_scales_absolute_cent(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(
        complete=False,
        known=True,
        cap=10,
        own=15000.0,
        round_no=10,
        history=[_seller_price(9, 9700.0)],
    )
    game["game_state"].pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    assert action["product_price"] == pytest.approx(8000.01)


def test_agent5_hidden_terminal_without_bound_keeps_leader_fallback(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    game = _buyer_game(
        complete=False,
        known=True,
        cap=10,
        own=150.0,
        round_no=10,
        history=[],
    )
    game["game_state"].pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}

    action = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    assert action["_plan"]["component"] == "observed_leader_buyer"


def test_agent5_hidden_terminal_bound_is_not_rewritten(monkeypatch):
    monkeypatch.setenv(policies.AGENT5_DEFAULT_FLAG, "1")
    monkeypatch.setenv("GLEE_NEGO_HIDDEN_FLOOR", "1.99")
    monkeypatch.setenv("GLEE_NEGO_OPEN_CLAIM_ALWAYS", "1")
    game = _buyer_game(
        complete=False,
        known=True,
        cap=10,
        own=150.0,
        round_no=10,
        history=[_seller_price(9, 97.0)],
    )
    game["game_state"].pop("last_offer", None)
    game["valid_actions"] = {"type": "offer"}

    raw = negotiation.decide(copy.deepcopy(game), Config(llm_mode="off"))
    wire = coerce(copy.deepcopy(raw), copy.deepcopy(game))
    assert raw["product_price"] == pytest.approx(80.01)
    assert wire["product_price"] == raw["product_price"]
