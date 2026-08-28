"""Score-aware release for Test 4's complete/unknown buyer stasis."""

from __future__ import annotations

import copy
import os

import pytest

from glee_agent import nego_score_floor, runtime_flags
from glee_agent.actions import coerce
from glee_agent.config import Config
from glee_agent.strategies import negotiation as N
from scripts import check_reachability


FLAG = N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_FLAG
TARGET = N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_TARGET_FLAG


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in list(os.environ):
        if name.startswith("GLEE_NEGO_") or name == "GLEE_TRACE_GATES":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.setenv("GLEE_NEGO_TEST4_HOTFIX_V1", "1")
    monkeypatch.setenv(FLAG, "0")
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    nego_score_floor._cells = None
    yield
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    nego_score_floor._cells = None


def _game(
    *,
    round_no: int = 75,
    cycles: int = 10,
    seller_value: float = 80.0,
    buyer_value: float = 150.0,
    offer_price: float = 133.2,
    counter_price: float = 100.16,
    messages_allowed: bool = False,
) -> dict:
    history = []
    first_buyer_decision = round_no - 2 * max(cycles, 0)
    for buyer_round in range(first_buyer_decision, round_no, 2):
        history.extend([
            {
                "round": buyer_round,
                "offer": {
                    "price": offer_price,
                    "from_player": "player_1",
                    "round": buyer_round,
                },
                "decision": "RejectOffer",
                "decided_by": "player_2",
                "counteroffer": counter_price,
            },
            {
                "round": buyer_round + 1,
                "offer": {
                    "price": counter_price,
                    "from_player": "player_2",
                    "round": buyer_round + 1,
                },
                "decision": "RejectOffer",
                "decided_by": "player_1",
                "counteroffer": offer_price,
            },
        ])
    state = {
        "game_family": "negotiation",
        "phase": "decision",
        "round": round_no,
        "horizon_known": False,
        "max_rounds": None,
        "complete_information": True,
        "messages_allowed": messages_allowed,
        "current_player": "player_2",
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": seller_value,
        "player_2_value": buyer_value,
        "last_offer": {
            "price": offer_price,
            "from_player": "player_1",
            "round": round_no,
        },
        "history": history,
    }
    return {
        "game_id": "complete-unknown-buyer-score-floor",
        "game_family": "negotiation",
        "your_player": "player_2",
        "phase": "decision",
        "valid_actions": {"type": "decision"},
        "game_state": state,
    }


def _reject(counter_price: float = 100.16, *, message: bool = False) -> dict:
    action = {
        "decision": "RejectOffer",
        "product_price": counter_price,
        "_plan": {"source": "test4_hotfix_v1"},
    }
    if message:
        action["message"] = "Above what I can justify. Here is where I can go."
    return action


def _arm(monkeypatch, target: float = 0.655) -> None:
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(TARGET, str(target))


def _wire(action: dict) -> dict:
    return {
        key: value for key, value in action.items()
        if not str(key).startswith("_")
    }


def _append_score_floor_cycles(
    game: dict, *, first_round: int = 75, stop_round: int = 97,
    offer_price: float = 140.0, boundary: float = 104.99,
) -> None:
    """Extend a pre-activation fixture with completed score-floor cycles."""
    history = game["game_state"]["history"]
    for buyer_round in range(first_round, stop_round, 2):
        history.extend([
            {
                "round": buyer_round,
                "offer": {
                    "price": offer_price,
                    "from_player": "player_1",
                    "round": buyer_round,
                },
                "decision": "RejectOffer",
                "decided_by": "player_2",
                "counteroffer": boundary,
            },
            {
                "round": buyer_round + 1,
                "offer": {
                    "price": boundary,
                    "from_player": "player_2",
                    "round": buyer_round + 1,
                },
                "decision": "RejectOffer",
                "decided_by": "player_1",
                "counteroffer": offer_price,
            },
        ])


@pytest.mark.parametrize("messages_allowed", [False, True])
def test_default_off_is_same_object_and_byte_identical(messages_allowed):
    game = _game(messages_allowed=messages_allowed)
    action = _reject(message=messages_allowed)
    before = copy.deepcopy(action)

    result = N._maybe_complete_unknown_buyer_score_floor(game, action)

    assert result is action
    assert result == before


@pytest.mark.parametrize(
    ("messages_allowed", "boundary", "payoff_floor", "seed_percentile", "cell_n"),
    [
        (False, 104.99, 45.01, 2 / 3, 57),
        (True, 109.99, 40.01, 38 / 53, 53),
    ],
)
def test_exact_transcript_releases_100_16_only_to_104_99(
    messages_allowed, boundary, payoff_floor, seed_percentile, cell_n,
    monkeypatch,
):
    game = _game(messages_allowed=messages_allowed)
    action = _reject(message=messages_allowed)
    _arm(monkeypatch)
    monkeypatch.setenv("GLEE_TRACE_GATES", "1")

    result = N._maybe_complete_unknown_buyer_score_floor(game, action)

    expected = {
        "decision": "RejectOffer",
        "product_price": boundary,
    }
    if messages_allowed:
        expected["message"] = "Above what I can justify. Here is where I can go."
    assert _wire(result) == expected
    metadata = result["_plan"][N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE]
    assert metadata == {
        "eligible": True,
        "mode": "deterministic",
        "trigger": "ten_cycle_stasis",
        "round": 75,
        "cycles": 10,
        "offer_price": 133.2,
        "baseline_counter": 100.16,
        "score_floor_counter": boundary,
        "seller_value": 80.0,
        "buyer_value": 150.0,
        "payoff_floor": payoff_floor,
        "target_percentile": 0.655,
        "achieved_seed_percentile": pytest.approx(seed_percentile),
        "seed_cell_n": cell_n,
    }
    assert N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE \
        in result["_plan"]["gates_fired"]


def test_incoming_price_at_floor_boundary_is_accepted(monkeypatch):
    game = _game(offer_price=104.99)
    _arm(monkeypatch)

    result = N._maybe_complete_unknown_buyer_score_floor(game, _reject())

    assert _wire(result) == {"decision": "AcceptOffer"}
    assert result["_plan"][N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE][
        "payoff_floor"
    ] == 45.01


def test_one_cent_beyond_boundary_is_countered_at_boundary(monkeypatch):
    game = _game(offer_price=105.0)
    _arm(monkeypatch)

    result = N._maybe_complete_unknown_buyer_score_floor(game, _reject())

    assert _wire(result) == {
        "decision": "RejectOffer",
        "product_price": 104.99,
    }


def test_higher_target_uses_next_empirical_atom(monkeypatch):
    game = _game()
    _arm(monkeypatch, target=0.70)

    result = N._maybe_complete_unknown_buyer_score_floor(game, _reject())

    assert result["product_price"] == 100.0
    metadata = result["_plan"][N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE]
    assert metadata["payoff_floor"] == 50.0
    assert metadata["achieved_seed_percentile"] == pytest.approx(42 / 57)


def test_missing_numeric_override_uses_audited_default(monkeypatch):
    game = _game()
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.delenv(TARGET, raising=False)

    result = N._maybe_complete_unknown_buyer_score_floor(game, _reject())

    assert result["product_price"] == 104.99
    assert result["_plan"][N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE][
        "target_percentile"
    ] == N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_DEFAULT_TARGET


def test_emitted_boundary_persists_after_it_breaks_baseline_stasis(monkeypatch):
    game = _game(round_no=75)
    game["game_state"]["history"].extend([
        {
            "round": 75,
            "offer": {
                "price": 133.2,
                "from_player": "player_1",
                "round": 75,
            },
            "decision": "RejectOffer",
            "decided_by": "player_2",
            "counteroffer": 104.99,
        },
        {
            "round": 76,
            "offer": {
                "price": 104.99,
                "from_player": "player_2",
                "round": 76,
            },
            "decision": "RejectOffer",
            "decided_by": "player_1",
            "counteroffer": 132.0,
        },
    ])
    state = game["game_state"]
    state["round"] = 77
    state["last_offer"] = {
        "price": 132.0,
        "from_player": "player_1",
        "round": 77,
    }
    _arm(monkeypatch)

    result = N._maybe_complete_unknown_buyer_score_floor(game, _reject())

    assert result["product_price"] == 104.99
    assert result["_plan"][N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE][
        "trigger"
    ] == "sticky"


def test_malformed_post_activation_trail_fails_closed(monkeypatch):
    game = _game(round_no=75)
    game["game_state"]["history"].extend([
        {
            "round": 75,
            "offer": {"price": 133.2, "from_player": "player_1", "round": 75},
            "decision": "RejectOffer",
            "decided_by": "player_2",
            "counteroffer": 104.99,
        },
        {
            "round": 76,
            "offer": {"price": 100.16, "from_player": "player_2", "round": 76},
            "decision": "RejectOffer",
            "decided_by": "player_1",
            "counteroffer": 132.0,
        },
    ])
    state = game["game_state"]
    state["round"] = 77
    state["last_offer"] = {"price": 132.0, "from_player": "player_1", "round": 77}
    action = _reject()
    _arm(monkeypatch)

    assert N._maybe_complete_unknown_buyer_score_floor(game, action) is action


@pytest.mark.parametrize("pre_activation_cycles", [9, 10])
def test_matching_boundary_without_proved_transition_is_not_sticky(
    pre_activation_cycles, monkeypatch,
):
    game = _game(
        round_no=75,
        cycles=pre_activation_cycles,
        offer_price=133.2,
        counter_price=104.99,
    )
    _append_score_floor_cycles(
        game, first_round=75, stop_round=77, offer_price=133.2)
    state = game["game_state"]
    state["round"] = 77
    state["last_offer"] = {
        "price": 133.2,
        "from_player": "player_1",
        "round": 77,
    }
    action = _reject()
    _arm(monkeypatch)

    assert N._maybe_complete_unknown_buyer_score_floor(game, action) is action


def test_transition_from_nonbaseline_price_is_not_sticky(monkeypatch):
    game = _game(
        round_no=75,
        cycles=10,
        offer_price=133.2,
        counter_price=99.0,
    )
    _append_score_floor_cycles(
        game, first_round=75, stop_round=77, offer_price=133.2)
    state = game["game_state"]
    state["round"] = 77
    state["last_offer"] = {
        "price": 133.2,
        "from_player": "player_1",
        "round": 77,
    }
    action = _reject(counter_price=100.16)
    _arm(monkeypatch)

    assert N._maybe_complete_unknown_buyer_score_floor(game, action) is action


def test_top_level_test4_dispatch_emits_score_floor_wire(monkeypatch):
    game = _game()
    _arm(monkeypatch)

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert result["decision"] == "RejectOffer"
    assert result["product_price"] == 104.99
    assert coerce(result, game)["product_price"] == 104.99
    assert result["_plan"][N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE][
        "eligible"
    ] is True


def test_round97_existing_low_share_accept_has_precedence(monkeypatch):
    game = _game(round_no=97, offer_price=140.0)
    _arm(monkeypatch)
    monkeypatch.setenv(N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert result["decision"] == "AcceptOffer"
    assert N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_GATE in result["_plan"]
    assert N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE not in result["_plan"]


def test_round97_guard_survives_real_score_floor_activation(monkeypatch):
    game = _game(round_no=75, offer_price=140.0)
    _append_score_floor_cycles(game)
    state = game["game_state"]
    state["round"] = 97
    state["last_offer"] = {
        "price": 140.0,
        "from_player": "player_1",
        "round": 97,
    }
    _arm(monkeypatch)
    monkeypatch.setenv(N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_FLAG, "1")

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert _wire(result) == {"decision": "AcceptOffer"}
    metadata = result["_plan"][
        N.COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_GATE
    ]
    assert metadata["counter_price"] == 104.99
    assert metadata["stasis_counter_source"] == "score_floor"
    assert N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE not in result["_plan"]


@pytest.mark.parametrize("round_no", [97, 99])
def test_last_counter_and_terminal_are_left_to_existing_endgame(
    round_no, monkeypatch,
):
    game = _game(round_no=round_no)
    action = _reject()
    _arm(monkeypatch)

    result = N._maybe_complete_unknown_buyer_score_floor(game, action)

    assert result is action


def test_test4_round99_pointwise_salvage_still_supersedes_floor(monkeypatch):
    game = _game(round_no=99)
    _arm(monkeypatch)

    result = N.decide(copy.deepcopy(game), Config.from_env())

    assert result["decision"] == "AcceptOffer"
    assert N.TEST2_UNKNOWN_R99_ACCEPT_GATE in result["_plan"]
    assert N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE not in result["_plan"]


@pytest.mark.parametrize(
    "mutation",
    [
        "hidden",
        "known_horizon",
        "finite_unknown_cap",
        "seller_seat",
        "wrong_roles",
        "too_early",
        "nine_cycles",
        "equal_values",
        "string_value",
        "bad_offer_provenance",
        "bad_offer_round",
        "other_policy",
        "old_stasis_conflict",
        "invalid_target",
        "unreachable_target",
    ],
)
def test_scope_model_and_conflict_fences(mutation, monkeypatch):
    game = _game()
    state = game["game_state"]
    _arm(monkeypatch)
    if mutation == "hidden":
        state["complete_information"] = False
    elif mutation == "known_horizon":
        state["horizon_known"] = True
        state["max_rounds"] = 99
    elif mutation == "finite_unknown_cap":
        state["max_rounds"] = 99
    elif mutation == "seller_seat":
        state["current_player"] = "player_1"
        game["your_player"] = "player_1"
    elif mutation == "wrong_roles":
        state["player_1_role"], state["player_2_role"] = "buyer", "seller"
    elif mutation == "too_early":
        game = _game(round_no=73)
    elif mutation == "nine_cycles":
        game = _game(cycles=9)
    elif mutation == "equal_values":
        state["player_1_value"] = 150.0
    elif mutation == "string_value":
        state["player_2_value"] = "150"
    elif mutation == "bad_offer_provenance":
        state["last_offer"]["from_player"] = "player_2"
    elif mutation == "bad_offer_round":
        state["last_offer"]["round"] = 74
    elif mutation == "other_policy":
        monkeypatch.setenv("GLEE_NEGO_TEST4_HOTFIX_V1", "0")
        monkeypatch.setenv("GLEE_NEGO_AGENT5_DEFAULT_V1", "1")
    elif mutation == "old_stasis_conflict":
        monkeypatch.setenv(N.COMPLETE_UNKNOWN_LATE_STASIS_FLAG, "1")
    elif mutation == "invalid_target":
        monkeypatch.setenv(TARGET, "nan")
    elif mutation == "unreachable_target":
        monkeypatch.setenv(TARGET, "0.9999")
    action = _reject()

    assert N._maybe_complete_unknown_buyer_score_floor(game, action) is action


def test_seed_floor_is_exact_and_does_not_pool_counterpart_values():
    state = _game()["game_state"]

    floor = nego_score_floor.cent_payoff_floor(
        state, "player_2", 80.0, 150.0, 0.655, 69.99,
    )

    assert floor == pytest.approx((45.01, 2 / 3, 57))
    assert nego_score_floor.cent_payoff_floor(
        {**state, "complete_information": False},
        "player_2",
        80.0,
        150.0,
        0.655,
        69.99,
    ) is None


def test_reachability_registry_uses_candidate_metadata():
    game = _game()
    plan = {
        N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE: {
            "eligible": True,
            "round": 75,
            "target_percentile": 0.655,
            "achieved_seed_percentile": 2 / 3,
            "seed_cell_n": 57,
        },
    }

    family, gates, predicate = check_reachability.KNOWN[FLAG]

    assert family == "negotiation"
    assert gates == (N.COMPLETE_UNKNOWN_BUYER_SCORE_FLOOR_GATE,)
    assert predicate(game, plan) is True
