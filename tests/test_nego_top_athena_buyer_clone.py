from __future__ import annotations

import copy

import pytest

from glee_agent import top_athena_buyer_clone as clone


NEW_FLAG = "GLEE_NEGO_TOP_ATHENA_BUYER_CLONE_AB"
OLD_FLAGS = (
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
)


@pytest.fixture(autouse=True)
def _flags_off(monkeypatch):
    monkeypatch.delenv("GLEE_PROBE", raising=False)
    monkeypatch.delenv(NEW_FLAG, raising=False)
    for flag in OLD_FLAGS:
        monkeypatch.delenv(flag, raising=False)


def _game_id(treatment: bool, prefix: str = "athena") -> str:
    for index in range(10_000):
        game_id = f"{prefix}-{index}"
        if clone.treatment_assignment(game_id) is treatment:
            return game_id
    raise AssertionError("no game id for requested arm")


def _message(price: float, allowed: bool) -> str:
    if not allowed:
        return ""
    return clone.BUYER_MESSAGE_TEMPLATE.format(price=price)


def _trace_game(trace, step: int, *, game_id: str | None = None) -> dict:
    me, other = "player_2", "player_1"
    history = []
    for index in range(step):
        seller_round = 2 * index + 1
        buyer_round = seller_round + 1
        history.extend((
            {
                "round": seller_round,
                "offer": {
                    "price": trace.seller_prices[index],
                    "message": trace.seller_messages[index],
                    "from_player": other,
                    "round": seller_round,
                },
                "decision": "RejectOffer",
                "decided_by": me,
                "response_time_ms": 1234,
                "counteroffer": trace.buyer_prices[index],
            },
            {
                "round": buyer_round,
                "offer": {
                    "price": trace.buyer_prices[index],
                    "message": _message(trace.buyer_prices[index],
                                        trace.messages_allowed),
                    "from_player": me,
                    "round": buyer_round,
                },
                "decision": "RejectOffer",
                "decided_by": other,
                "response_time_ms": 4321,
                "counteroffer": trace.seller_prices[index + 1],
            },
        ))
    round_no = 2 * step + 1
    state = {
        "game_family": "negotiation",
        "round": round_no,
        "horizon_known": trace.horizon_known,
        "complete_information": True,
        "messages_allowed": trace.messages_allowed,
        "current_player": me,
        f"{me}_role": "buyer",
        f"{other}_role": "seller",
        f"{me}_value": trace.buyer_value,
        f"{other}_value": trace.seller_value,
        "last_offer": {
            "price": trace.seller_prices[step],
            "message": trace.seller_messages[step],
            "from_player": other,
            "round": round_no,
        },
        "history": history,
    }
    if trace.horizon_known:
        state["max_rounds"] = trace.max_rounds
    return {
        "game_id": game_id or _game_id(True),
        "game_family": "negotiation",
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": "decision"},
    }


def _accept_game(trace, *, game_id: str | None = None) -> dict:
    me, other = "player_2", "player_1"
    state = {
        "game_family": "negotiation",
        "round": 1,
        "max_rounds": 1,
        "horizon_known": True,
        "complete_information": trace.complete,
        "messages_allowed": trace.messages_allowed,
        "current_player": me,
        f"{me}_role": "buyer",
        f"{other}_role": "seller",
        f"{me}_value": trace.buyer_value,
        "last_offer": {
            "price": trace.incoming_price,
            "message": trace.incoming_message,
            "from_player": other,
            "round": 1,
        },
        "history": [],
    }
    if trace.complete:
        state[f"{other}_value"] = trace.seller_value
    return {
        "game_id": game_id or _game_id(True),
        "game_family": "negotiation",
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": "decision"},
    }


def _on(monkeypatch):
    monkeypatch.setenv(NEW_FLAG, "1")


def test_corpus_accounting_and_identified_support_are_literal():
    assert clone.CORPUS_COUNTS == {
        "athena_buyer_games": 21,
        "complete_games": 5,
        "hidden_games": 16,
        "response_decisions": 157,
        "rejects": 152,
        "accepts": 4,
        "walks": 1,
        "counter_wires": 148,
        "complete_counter_wires": 21,
        "hidden_counter_wires": 127,
        "counter_wires_with_exact_generic_message": 35,
        "counter_wires_without_message": 113,
    }
    assert sum(len(trace.buyer_prices)
               for trace in clone.COMPLETE_COUNTER_TRACES) == 21
    assert len(clone.SINGLE_ROUND_ACCEPT_TRACES) == 4
    assert {trace.type_basis for trace in clone.SINGLE_ROUND_ACCEPT_TRACES} == {
        "public_complete_information",
        "agreement_payoff_inference",
    }


def test_assignment_is_stable_balanced_and_fails_closed():
    bits = [clone.treatment_assignment(f"game-{index}")
            for index in range(2000)]
    assert bits == [clone.treatment_assignment(f"game-{index}")
                    for index in range(2000)]
    assert 900 < sum(bits) < 1100
    assert clone.treatment_assignment(None) is None
    assert clone.treatment_assignment(7) is None
    assert clone.treatment_assignment("  ") is None


def test_default_off_hash_control_and_both_clone_collisions(monkeypatch):
    game = _trace_game(clone.COMPLETE_COUNTER_TRACES[0], 0)
    assert clone.eligible(game)
    assert not clone.owns(game)
    assert clone.action(game) is None

    _on(monkeypatch)
    assert clone.owns(game)
    assert clone.action(game) is not None
    assert not clone.owns(_trace_game(
        clone.COMPLETE_COUNTER_TRACES[0], 0,
        game_id=_game_id(False, "control")))

    for flag in OLD_FLAGS:
        monkeypatch.setenv(flag, "1")
        assert not clone.enabled()
        assert not clone.owns(game)
        assert clone.action(game) is None
        monkeypatch.delenv(flag)


@pytest.mark.parametrize(
    "trace,step",
    [(trace, step)
     for trace in clone.COMPLETE_COUNTER_TRACES
     for step in range(len(trace.buyer_prices))],
)
def test_all_21_complete_counter_wires_are_exact(monkeypatch, trace, step):
    _on(monkeypatch)
    game = _trace_game(trace, step)
    action = clone.action(game)
    assert action == {
        "decision": "RejectOffer",
        "product_price": trace.buyer_prices[step],
        **({"message": _message(trace.buyer_prices[step], True)}
           if trace.messages_allowed else {}),
        "_plan": {
            "source": "top_athena_buyer_clone",
            "evidence": "exact_complete_history_counter",
            "source_game_id": trace.source_game_id,
            "step": step,
        },
    }
    assert clone.matches_wire(game, action)


def test_counter_requires_exact_price_message_and_full_history(monkeypatch):
    _on(monkeypatch)
    trace = clone.COMPLETE_COUNTER_TRACES[0]
    game = _trace_game(trace, 2)

    mutations = []
    changed = copy.deepcopy(game)
    changed["game_state"]["last_offer"]["price"] += 0.01
    mutations.append(changed)
    changed = copy.deepcopy(game)
    changed["game_state"]["last_offer"]["message"] += " "
    mutations.append(changed)
    changed = copy.deepcopy(game)
    changed["game_state"]["history"][0]["counteroffer"] += 0.01
    mutations.append(changed)
    changed = copy.deepcopy(game)
    changed["game_state"]["history"][1]["offer"]["message"] += " "
    mutations.append(changed)
    changed = copy.deepcopy(game)
    changed["game_state"]["history"].append({})
    mutations.append(changed)

    for changed in mutations:
        assert not clone.eligible(changed)
        assert not clone.owns(changed)
        assert clone.action(changed) is None


@pytest.mark.parametrize("trace", clone.SINGLE_ROUND_ACCEPT_TRACES)
def test_four_single_round_accepts_are_exact_not_thresholds(monkeypatch, trace):
    _on(monkeypatch)
    game = _accept_game(trace)
    action = clone.action(game)
    assert action == {
        "decision": "AcceptOffer",
        "_plan": {
            "source": "top_athena_buyer_clone",
            "evidence": "exact_single_round_accept",
            "source_game_id": trace.source_game_id,
            "type_basis": trace.type_basis,
        },
    }

    cheaper = copy.deepcopy(game)
    cheaper["game_state"]["last_offer"]["price"] -= 0.01
    assert clone.action(cheaper) is None
    extra_message = copy.deepcopy(game)
    extra_message["game_state"]["last_offer"]["message"] = "deal?"
    assert clone.action(extra_message) is None


def test_hidden_multi_round_and_walk_families_fall_through(monkeypatch):
    _on(monkeypatch)
    trace = clone.SINGLE_ROUND_ACCEPT_TRACES[2]
    hidden = _accept_game(trace)
    hidden["game_state"]["round"] = 1
    hidden["game_state"]["max_rounds"] = 10
    hidden["game_state"]["last_offer"].update(
        price=1_400_000.0, round=1)
    assert not clone.eligible(hidden)
    assert clone.action(hidden) is None

    unknown = copy.deepcopy(hidden)
    unknown["game_state"].pop("max_rounds")
    unknown["game_state"]["horizon_known"] = False
    assert clone.action(unknown) is None
    assert len(clone.HIDDEN_MULTIROUND_UNIDENTIFIED_COUNTER_FAMILIES) == 3


@pytest.mark.parametrize("mutation", [
    lambda game: game.__setitem__("game_family", "bargaining"),
    lambda game: game["game_state"].__setitem__("player_2_role", "seller"),
    lambda game: game["game_state"].__setitem__("current_player", "player_1"),
    lambda game: (game.__setitem__("your_player", "player_1"),
                  game["game_state"].__setitem__("current_player", "player_1"),
                  game["game_state"].__setitem__("player_1_role", "buyer"),
                  game["game_state"].__setitem__("player_2_role", "seller")),
    lambda game: game["valid_actions"].__setitem__("type", "offer"),
    lambda game: game["game_state"].__setitem__("round", "1"),
    lambda game: game["game_state"].__setitem__("history", [None]),
    lambda game: game["game_state"]["last_offer"].__setitem__("price", float("nan")),
    lambda game: game["game_state"]["last_offer"].__setitem__("from_player", "player_2"),
])
def test_scope_and_malformed_states_fail_closed(monkeypatch, mutation):
    _on(monkeypatch)
    game = _trace_game(clone.COMPLETE_COUNTER_TRACES[0], 0)
    mutation(game)
    assert not clone.eligible(game)
    assert not clone.owns(game)
    assert clone.action(game) is None


def test_hidden_accept_never_uses_leaked_seller_value(monkeypatch):
    _on(monkeypatch)
    hidden = next(trace for trace in clone.SINGLE_ROUND_ACCEPT_TRACES
                  if not trace.complete)
    game = _accept_game(hidden)
    game["game_state"]["player_1_value"] = 80.0
    assert clone.action(game) is None


def test_sdk_missing_empty_message_is_equivalent_to_no_wire(monkeypatch):
    _on(monkeypatch)
    silent = clone.COMPLETE_COUNTER_TRACES[-1]
    game = _trace_game(silent, 1)
    game["game_state"]["last_offer"].pop("message")
    for entry in game["game_state"]["history"]:
        entry["offer"].pop("message")
    assert clone.action(game)["product_price"] == silent.buyer_prices[1]


def test_matches_wire_rejects_semantic_changes(monkeypatch):
    _on(monkeypatch)
    game = _trace_game(clone.COMPLETE_COUNTER_TRACES[0], 0)
    action = clone.action(game)
    assert clone.matches_wire(game, action)
    changed = dict(action)
    changed["product_price"] += 0.01
    assert not clone.matches_wire(game, changed)
    assert not clone.matches_wire(game, None)
