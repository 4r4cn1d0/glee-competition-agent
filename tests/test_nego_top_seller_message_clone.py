from __future__ import annotations

import copy
import hashlib
import math

import pytest

from glee_agent import top_seller_message_clone as clone
from glee_agent.config import Config
from glee_agent.strategies import negotiation


@pytest.fixture(autouse=True)
def _default_off(monkeypatch):
    for name in (
        "GLEE_PROBE",
        clone.FLAG,
        "GLEE_NEGO_MSG_ARMS",
        "GLEE_LLM_MODE",
        "GLEE_LLM_FAMILIES",
        "GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB",
        "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB",
    ):
        monkeypatch.delenv(name, raising=False)


def _game_id(candidate: bool, prefix: str = "seller-message") -> str:
    for index in range(10_000):
        game_id = f"{prefix}-{index}"
        if clone.treatment_assignment(game_id) is candidate:
            return game_id
    raise AssertionError("no game id for requested arm")


def _history(own_count: int, me: str = "player_1") -> list[dict]:
    other = "player_2" if me == "player_1" else "player_1"
    rows = []
    for index in range(own_count):
        # The scalar/dict counteroffer is deliberately present: the helper must
        # count only the later offer wire from our seller seat.
        rows.extend((
            {
                "round": 2 * index + 1,
                "offer": {
                    "price": 150.0 - index,
                    "message": "",
                    "from_player": me,
                    "round": 2 * index + 1,
                },
                "decision": "RejectOffer",
                "decided_by": other,
                "counteroffer": {
                    "price": 150.0 - index,
                    "from_player": me,
                },
            },
            {
                "round": 2 * index + 2,
                "offer": {
                    "price": 90.0 + index,
                    "message": "",
                    "from_player": other,
                    "round": 2 * index + 2,
                },
                "decision": "RejectOffer",
                "decided_by": me,
                "counteroffer": 149.0 - index,
            },
        ))
    return rows


def _game(
    *,
    complete: bool = False,
    horizon_known: bool = True,
    max_rounds: int | None = 10,
    own_count: int = 0,
    action_type: str = "offer",
    messages_allowed: bool = True,
    candidate: bool = True,
    role: str = "seller",
) -> dict:
    me, other = "player_1", "player_2"
    state = {
        "game_family": "negotiation",
        "round": 2 * own_count + 1,
        "horizon_known": horizon_known,
        "complete_information": complete,
        "messages_allowed": messages_allowed,
        "current_player": me,
        f"{me}_role": role,
        f"{other}_role": "buyer" if role == "seller" else "seller",
        f"{me}_value": 100.0,
        "history": _history(own_count, me),
    }
    if max_rounds is not None:
        state["max_rounds"] = max_rounds
    return {
        "game_id": _game_id(candidate),
        "game_family": "negotiation",
        "your_player": me,
        "game_state": state,
        "valid_actions": {"type": action_type},
    }


def _action(action_type: str = "offer", *, price=140.0) -> dict:
    action = {
        "product_price": price,
        "custom_non_message": {"raw": [1, 2, 3]},
        "_plan": {
            "source": "control",
            "target": 140.0,
            "gates_fired": ["control_gate"],
        },
    }
    if action_type == "decision":
        action["decision"] = "RejectOffer"
    return action


def _arm(monkeypatch):
    monkeypatch.setenv(clone.FLAG, "1")
    monkeypatch.setenv("GLEE_LLM_MODE", "off")


def test_assignment_is_exact_stable_low_bit_and_malformed_ids_fail_closed():
    ids = [f"game-{index}" for index in range(2_000)]
    expected = [
        bool(hashlib.sha256((clone.SALT + game_id).encode("utf-8")).digest()[-1] & 1)
        for game_id in ids
    ]
    assert [clone.treatment_assignment(game_id) for game_id in ids] == expected
    assert 900 < sum(expected) < 1_100
    for malformed in (None, 7, "", "   "):
        assert clone.treatment_assignment(malformed) is None


@pytest.mark.parametrize(
    "complete,known,cap,cell",
    [
        (False, True, 1, "hidden_cap1"),
        (False, True, 10, "hidden_cap10"),
        (False, False, None, "hidden_unknown"),
        (True, True, 10, "complete_cap10"),
        (True, False, None, "complete_unknown"),
    ],
)
def test_exact_evidence_cells_are_eligible(complete, known, cap, cell):
    game = _game(complete=complete, horizon_known=known, max_rounds=cap)
    action = _action()
    assert clone.evidence_cell(game) == cell
    assert clone.eligible(game, action)


def test_complete_cap1_and_other_caps_fail_closed():
    for complete, cap in ((True, 1), (False, 2), (True, 20)):
        game = _game(complete=complete, max_rounds=cap)
        action = _action()
        assert clone.evidence_cell(game) is None
        assert not clone.eligible(game, action)


@pytest.mark.parametrize(
    "count,expected",
    [
        (0, clone.FIRST_PRICE_MESSAGE),
        (1, clone.EARLY_COUNTER_MESSAGE),
        (3, clone.EARLY_COUNTER_MESSAGE),
        (4, clone.LATE_COUNTER_MESSAGE),
        (9, clone.LATE_COUNTER_MESSAGE),
        (10, None),
        (25, None),
    ],
)
def test_literal_message_table_and_offer_only_count(count, expected):
    game = _game(own_count=count)
    assert clone.prior_seller_price_count(game) == count
    assert clone.message_for_price_count(count) == expected


@pytest.mark.parametrize("count", [0, 1, 3, 4, 9])
@pytest.mark.parametrize("action_type", ["offer", "decision"])
def test_candidate_changes_only_message_and_adjacent_trace(
    monkeypatch, count, action_type,
):
    _arm(monkeypatch)
    game = _game(own_count=count, action_type=action_type)
    before = _action(action_type)
    frozen = copy.deepcopy(before)
    after = clone.attach(game, before)
    expected = clone.message_for_price_count(count)

    assert after is not before
    assert before == frozen
    assert after["decision"] == before["decision"] if action_type == "decision" else True
    assert after["product_price"] == before["product_price"]
    assert after["custom_non_message"] == before["custom_non_message"]
    assert after["message"] == expected
    assert after["_plan"]["source"] == "control"
    assert after["_plan"]["target"] == 140.0
    assert after["_plan"]["gates_fired"] == ["control_gate", clone.GATE]
    assert after["_plan"][clone.PLAN_TRACE]["prior_seller_price_count"] == count
    assert clone.audit_message_only(before, after, expected)
    audit = clone.fingerprint_audit(before, after)
    assert audit["wire_changed"] is True
    assert audit["non_message_unchanged"] is True


def test_default_off_hash_control_and_unsupported_tail_return_same_object(monkeypatch):
    candidate_game = _game(candidate=True)
    control_game = _game(candidate=False)
    action = _action()
    assert clone.attach(candidate_game, action) is action

    _arm(monkeypatch)
    assert clone.attach(control_game, action) is action
    tail_game = _game(candidate=True, own_count=10)
    assert clone.attach(tail_game, action) is action


@pytest.mark.parametrize(
    "mutator",
    [
        lambda game, action: game.update(game_family="bargaining"),
        lambda game, action: game["game_state"].update(messages_allowed=False),
        lambda game, action: game["game_state"].update(player_1_role="buyer"),
        lambda game, action: game["valid_actions"].update(type="seller_message"),
        lambda game, action: action.update(decision="AcceptOffer"),
        lambda game, action: action.update(decision="WalkAway"),
        lambda game, action: action.pop("product_price"),
        lambda game, action: action.update(product_price=math.inf),
        lambda game, action: action.update(product_price="140"),
    ],
)
def test_ineligible_states_and_non_price_decisions_are_identity_noops(
    monkeypatch, mutator,
):
    _arm(monkeypatch)
    game = _game(action_type="decision")
    action = _action("decision")
    mutator(game, action)
    frozen = copy.deepcopy(action)
    assert clone.attach(game, action) is action
    assert action == frozen


def test_counteroffer_echoes_do_not_increment_prior_wire_count():
    game = _game(own_count=1)
    history = game["game_state"]["history"]
    history[0]["counteroffer"] = {
        "price": 150.0,
        "from_player": "player_1",
        "round": 1,
    }
    history[1]["counteroffer"] = {
        "price": 149.0,
        "from_player": "player_1",
        "round": 2,
    }
    assert clone.prior_seller_price_count(game) == 1


@pytest.mark.parametrize("msg_arms", ["1", "N0,N1", "pin:N2"])
def test_existing_negotiation_message_arms_fail_closed(monkeypatch, msg_arms):
    _arm(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_MSG_ARMS", msg_arms)
    game, action = _game(), _action()
    assert clone.attach(game, action) is action


@pytest.mark.parametrize("mode", ["messages", "full"])
def test_active_negotiation_llm_message_or_full_mode_fails_closed(monkeypatch, mode):
    _arm(monkeypatch)
    monkeypatch.setenv("GLEE_LLM_MODE", mode)
    monkeypatch.setenv("GLEE_LLM_FAMILIES", "persuasion,negotiation")
    game, action = _game(), _action()
    assert clone.attach(game, action) is action


def test_buyer_only_cap10_and_opus_arms_do_not_globally_conflict(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.setenv("GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB", "1")
    monkeypatch.setenv("GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB", "1")
    game, action = _game(), _action()
    after = clone.attach(game, action)
    assert after is not action
    assert after["message"] == clone.FIRST_PRICE_MESSAGE


def test_existing_matching_message_gets_no_unearned_trace(monkeypatch):
    _arm(monkeypatch)
    game = _game(own_count=1)
    action = _action()
    action["message"] = clone.EARLY_COUNTER_MESSAGE
    frozen = copy.deepcopy(action)
    assert clone.attach(game, action) is action
    assert action == frozen


def test_pure_helper_uses_explicit_ownership_without_runtime_reads():
    game, action = _game(), _action()
    after = clone.apply_clone(
        game,
        action,
        armed=True,
        msg_arms_armed=False,
        llm_mode="off",
        llm_families=(),
    )
    assert after is not action
    assert after["message"] == clone.FIRST_PRICE_MESSAGE

    assert clone.apply_clone(
        game,
        action,
        armed=True,
        msg_arms_armed=True,
        llm_mode="off",
        llm_families=(),
    ) is action


def test_fingerprint_audit_detects_any_non_message_drift():
    before = _action()
    after = copy.deepcopy(before)
    after["message"] = clone.FIRST_PRICE_MESSAGE
    assert clone.audit_message_only(before, after, clone.FIRST_PRICE_MESSAGE)

    after["product_price"] += 0.01
    assert not clone.audit_message_only(before, after, clone.FIRST_PRICE_MESSAGE)
    audit = clone.fingerprint_audit(before, after)
    assert audit["wire_changed"] is True
    assert audit["non_message_unchanged"] is False


def test_composite_profile_selects_whole_deterministic_leader_policy(monkeypatch):
    game = _game(own_count=2)
    control = _action()
    monkeypatch.setattr(
        negotiation,
        "_decide",
        lambda observed_game, cfg: copy.deepcopy(control),
    )
    cfg = Config(nego_policy="leader_replica", llm_mode="off")

    result = negotiation.decide(game, cfg)

    assert result["message"] == clone.EARLY_COUNTER_MESSAGE
    assert result["product_price"] == control["product_price"]
    assert result["_plan"][clone.PLAN_TRACE]["arm"] == "leader_replica"
