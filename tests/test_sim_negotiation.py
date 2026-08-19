"""Tests for the local negotiation engine.

These are fidelity tests, not behaviour tests: every assertion is a claim about
what the LIVE server does, taken from docs/reference/glee-docs.md and the SDK
README. A simulator that quietly differs from the server produces tuning that
makes the live agent worse, so the shapes are pinned down key by key — including
the ones that must be ABSENT.
"""

from __future__ import annotations

import math
import random
import re

import pytest

from sim.grid import MONEY_SCALES
from sim.negotiation import (
    DEFAULT_HARD_CAP,
    MAX_MESSAGE_LEN,
    NegotiationEngine,
)
from sim.types import MAX_INVALID_ATTEMPTS, PLAYER_1, PLAYER_2, Config

ENVELOPE_KEYS = {"game_id", "game_family", "your_player", "phase", "opponent",
                 "game_state", "valid_actions", "prompt"}

# Keys from the other two families. Emitting any of them would let a strategy
# branch on a signal the live server never sends in a negotiation game.
FOREIGN_KEYS = ("proposer", "delta_1", "delta_2", "money_to_divide",
                "player_1_gain", "player_2_gain", "product_price", "p", "v", "u",
                "current_quality", "total_rounds", "seller_total_payoff",
                "buyer_total_payoff", "is_seller_know_cv", "seller_message",
                "hard_cap")


def make_engine(**params):
    """A capped, incomplete-information game with a $70 zone of agreement."""
    base = dict(player_1_value=30.0, player_2_value=100.0, max_rounds=5,
                messages_allowed=True, complete_information=False)
    base.update(params)
    hard_cap = base.pop("hard_cap", DEFAULT_HARD_CAP)
    attempts_per_game = base.pop("attempts_per_game", True)
    seed = base.pop("seed", 7)
    return NegotiationEngine(Config("negotiation", base), random.Random(seed),
                             game_id="test-game", hard_cap=hard_cap,
                             attempts_per_game=attempts_per_game)


def offer(engine, price=70.0, **extra):
    return engine.submit(engine.current_player, dict(product_price=price, **extra))


def counter(engine, price, **extra):
    return engine.submit(engine.current_player,
                         dict(decision="RejectOffer", product_price=price, **extra))


def state_of(engine, player=PLAYER_1):
    return engine.observation(player)["game_state"]


#: A dollar amount the way a prompt is allowed to render one: grouped, plain
#: decimal, never an exponent. Deliberately strict, so "$1.45e+06" parses as the
#: amount 1.45 and fails the round-trip against game_state below.
MONEY_RE = re.compile(r"\$([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)(?:\.[0-9]+)?")


def money_in(prompt):
    """Every dollar amount the prompt renders, as floats."""
    return [float(m.group(0)[1:].replace(",", "")) for m in MONEY_RE.finditer(prompt)]


def snapshot(engine):
    """Everything a move may legally change, for 'a rejection changes nothing'."""
    state = state_of(engine, engine.current_player)
    return (engine.current_player, engine.done, state["phase"], state["round"],
            state["last_offer"], state["history"],
            engine.observation(engine.current_player)["valid_actions"])


# --- the observation envelope ------------------------------------------------


def test_observation_envelope_has_exactly_the_api_keys():
    engine = make_engine()
    obs = engine.observation(PLAYER_1)
    assert set(obs) == ENVELOPE_KEYS
    assert obs["game_id"] == "test-game"
    assert obs["game_family"] == "negotiation"
    assert obs["your_player"] == PLAYER_1
    assert isinstance(obs["prompt"], str) and obs["prompt"]


def test_valid_actions_carries_exactly_type_and_fields():
    engine = make_engine()
    for player in (PLAYER_1, PLAYER_2):
        assert set(engine.observation(player)["valid_actions"]) == {"type", "fields"}


def test_your_player_is_the_argument_not_the_current_player():
    engine = make_engine()
    # Round 1 waits on player_1, but player_2 can still inspect the game.
    obs = engine.observation(PLAYER_2)
    assert obs["your_player"] == PLAYER_2
    assert obs["game_state"]["current_player"] == PLAYER_1


def test_top_level_phase_matches_game_state_phase():
    engine = make_engine()
    for _ in range(3):
        obs = engine.observation(engine.current_player)
        assert obs["phase"] == obs["game_state"]["phase"]
        if obs["valid_actions"]["type"] == "offer":
            offer(engine, 90.0)
        else:
            counter(engine, 50.0)


def test_offer_phase_fields():
    engine = make_engine()
    assert engine.observation(PLAYER_1)["valid_actions"] == {
        "type": "offer",
        "fields": {"product_price": "number (required)",
                   "message": "string (optional)"},
    }


def test_decision_fields_are_the_documented_strings():
    engine = make_engine()
    offer(engine, 70.0)
    assert engine.observation(PLAYER_2)["valid_actions"] == {
        "type": "decision",
        "fields": {"decision": "'AcceptOffer', 'RejectOffer', or 'WalkAway'",
                   "product_price": "number (required if RejectOffer - your counteroffer)",
                   "message": "string (optional)"},
    }


def test_final_round_fields_downgrade_the_counteroffer():
    engine = make_engine(max_rounds=1)
    offer(engine, 70.0)
    fields = engine.observation(PLAYER_2)["valid_actions"]["fields"]
    assert fields["decision"] == "'AcceptOffer', 'RejectOffer', or 'WalkAway'"
    assert "required" not in fields["product_price"]


def test_opponent_is_disclosed_or_hidden_for_the_whole_game():
    engine = make_engine()
    first = engine.observation(PLAYER_1)["opponent"]
    assert set(first) == {"type", "name"}
    if first["type"] == "hidden":
        assert first["name"] is None
    else:
        assert first["type"] in ("agent", "human") and first["name"]
    offer(engine, 70.0)
    counter(engine, 50.0)
    assert engine.observation(PLAYER_1)["opponent"] == first
    assert engine.observation(PLAYER_2)["opponent"] == first


def test_opponent_disclosure_is_drawn_from_the_injected_rng():
    same = [make_engine(seed=11).observation(PLAYER_1)["opponent"] for _ in range(2)]
    assert same[0] == same[1]
    drawn = {make_engine(seed=s).observation(PLAYER_1)["opponent"]["type"]
             for s in range(40)}
    assert drawn == {"agent", "hidden"}          # both halves are reachable


def test_opponent_can_be_pinned_by_configuration():
    engine = make_engine(disclose_opponent=True, opponent_type="human", opponent_name="Ada")
    assert engine.observation(PLAYER_1)["opponent"] == {"type": "human", "name": "Ada"}
    hidden = make_engine(disclose_opponent=False)
    assert hidden.observation(PLAYER_1)["opponent"] == {"type": "hidden", "name": None}


def test_mutating_an_observation_cannot_corrupt_the_engine():
    engine = make_engine()
    offer(engine, 70.0)
    counter(engine, 50.0)
    obs = engine.observation(PLAYER_1)
    obs["game_state"]["last_offer"]["price"] = 999.0
    obs["game_state"]["history"][0]["offer"]["price"] = 999.0
    obs["game_state"]["history"][0]["counteroffer"]["price"] = 999.0
    obs["game_state"]["history"].append({"round": 99})
    obs["opponent"]["name"] = "spoofed"
    fresh = state_of(engine, PLAYER_1)
    assert fresh["last_offer"]["price"] == 50.0
    assert len(fresh["history"]) == 1
    assert fresh["history"][0]["offer"]["price"] == 70.0
    assert fresh["history"][0]["counteroffer"]["price"] == 50.0


# --- game_state fields -------------------------------------------------------


def test_round_one_is_a_seller_offer_with_a_null_last_offer():
    engine = make_engine()
    obs = engine.observation(PLAYER_1)
    state = obs["game_state"]
    assert engine.current_player == PLAYER_1
    assert obs["phase"] == "offer"
    assert obs["valid_actions"]["type"] == "offer"
    assert state["round"] == 1
    assert state["player_1_role"] == "seller"
    assert state["player_2_role"] == "buyer"
    # null means "nothing yet"; the KEY is present.
    assert "last_offer" in state and state["last_offer"] is None
    assert state["history"] == []
    assert engine.done is False and engine.result is None


def test_roles_are_public_under_incomplete_information():
    state = state_of(make_engine(complete_information=False), PLAYER_2)
    assert state["player_1_role"] == "seller"
    assert state["player_2_role"] == "buyer"


def test_incomplete_information_omits_the_opponent_value_by_key():
    engine = make_engine(complete_information=False,
                         player_1_value=30.0, player_2_value=100.0)
    seller = state_of(engine, PLAYER_1)
    buyer = state_of(engine, PLAYER_2)
    assert seller["player_1_value"] == 30.0
    assert "player_2_value" not in seller          # absent, not None
    assert buyer["player_2_value"] == 100.0
    assert "player_1_value" not in buyer
    assert seller["complete_information"] is False


def test_hidden_value_is_absent_rather_than_null():
    """.get() must be able to tell 'hidden' from a valuation of zero."""
    engine = make_engine(complete_information=False, player_2_value=0.0)
    seller = state_of(engine, PLAYER_1)
    buyer = state_of(engine, PLAYER_2)
    assert seller.get("player_2_value", "MISSING") == "MISSING"
    assert buyer["player_2_value"] == 0.0           # a real zero survives


def test_complete_information_shows_both_values_to_both_players():
    engine = make_engine(complete_information=True,
                         player_1_value=30.0, player_2_value=100.0)
    for player in (PLAYER_1, PLAYER_2):
        state = state_of(engine, player)
        assert state["player_1_value"] == 30.0
        assert state["player_2_value"] == 100.0
        assert state["complete_information"] is True


def test_filtering_survives_into_the_decision_phase():
    engine = make_engine(complete_information=False)
    offer(engine, 70.0)
    assert "player_1_value" not in state_of(engine, PLAYER_2)
    assert "player_2_value" not in state_of(engine, PLAYER_1)


def test_capped_game_reports_max_rounds_and_horizon_known():
    state = state_of(make_engine(max_rounds=3))
    assert state["max_rounds"] == 3
    assert state["horizon_known"] is True


def test_uncapped_game_omits_max_rounds_entirely():
    state = state_of(make_engine(max_rounds=None))
    assert "max_rounds" not in state              # absent, never null
    assert state["horizon_known"] is False


def test_explicit_horizon_known_false_clears_a_stray_max_rounds():
    state = state_of(make_engine(max_rounds=4, horizon_known=False))
    assert "max_rounds" not in state
    assert state["horizon_known"] is False


def test_messages_allowed_flag_is_reported():
    assert state_of(make_engine(messages_allowed=False))["messages_allowed"] is False
    assert state_of(make_engine(messages_allowed=True))["messages_allowed"] is True


@pytest.mark.parametrize("key", FOREIGN_KEYS)
def test_no_other_family_keys_leak_into_game_state(key):
    engine = make_engine(complete_information=True)
    assert key not in state_of(engine, PLAYER_1)          # offer phase
    offer(engine, 70.0)
    assert key not in state_of(engine, PLAYER_2)          # decision phase
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert key not in state_of(engine, PLAYER_1)          # completed


def test_no_discounting_keys_and_no_time_decay_of_payoff():
    """A round-7 deal pays exactly what the same price would have paid first."""
    early = make_engine(max_rounds=None, hard_cap=50)
    offer(early, 70.0)
    early.submit(PLAYER_2, {"decision": "AcceptOffer"})

    late = make_engine(max_rounds=None, hard_cap=50)
    offer(late, 70.0)
    for _ in range(6):                       # walk the same price out to round 7
        counter(late, 70.0)
    assert state_of(late)["round"] == 7
    assert state_of(late)["last_offer"] == {"price": 70.0, "message": None,
                                            "from_player": PLAYER_1, "round": 7}
    late.submit(late.current_player, {"decision": "AcceptOffer"})

    assert late.result.player_1_payoff == early.result.player_1_payoff == 40.0
    assert late.result.player_2_payoff == early.result.player_2_payoff == 30.0


# --- turn order and history --------------------------------------------------


def test_offer_hands_the_decision_to_the_buyer():
    engine = make_engine()
    result = offer(engine, 70.0, message="Best price")
    assert (result.valid, result.game_over, result.result) == (True, False, None)
    obs = engine.observation(PLAYER_2)
    assert engine.current_player == PLAYER_2
    assert obs["phase"] == "decision"
    assert obs["valid_actions"]["type"] == "decision"
    assert obs["game_state"]["last_offer"] == {
        "price": 70.0, "message": "Best price", "from_player": PLAYER_1, "round": 1}
    assert obs["game_state"]["round"] == 1
    assert obs["game_state"]["history"] == []       # round 1 is not resolved yet


def test_counteroffer_advances_the_round_and_stays_in_the_decision_phase():
    engine = make_engine()
    offer(engine, 90.0, message="Firm")
    result = counter(engine, 50.0, message="Too high")
    assert result.valid and not result.game_over
    state = state_of(engine, PLAYER_1)
    assert state["round"] == 2
    assert state["phase"] == "decision"            # NOT a fresh "offer" phase
    assert engine.observation(PLAYER_1)["valid_actions"]["type"] == "decision"
    assert engine.current_player == PLAYER_1
    assert state["last_offer"] == {"price": 50.0, "message": "Too high",
                                   "from_player": PLAYER_2, "round": 2}


def test_offer_phase_happens_exactly_once_per_game():
    engine = make_engine(max_rounds=None, hard_cap=12)
    types = []
    while not engine.done:
        types.append(engine.observation(engine.current_player)["valid_actions"]["type"])
        if types[-1] == "offer":
            offer(engine, 80.0)
        else:
            counter(engine, 80.0)
    assert types.count("offer") == 1 and types[0] == "offer"
    assert set(types[1:]) == {"decision"}


def test_current_player_is_always_the_receiver_of_the_standing_offer():
    engine = make_engine(max_rounds=None, hard_cap=15)
    offer(engine, 90.0)
    while not engine.done:
        state = state_of(engine, engine.current_player)
        assert state["last_offer"] is not None
        assert state["current_player"] != state["last_offer"]["from_player"]
        assert state["current_player"] == engine.current_player
        # The documented idiom: on your turn, current_player is you.
        me = state["current_player"]
        assert state[f"{me}_value"] == (30.0 if me == PLAYER_1 else 100.0)
        counter(engine, 60.0)


def test_odd_rounds_are_seller_offers_and_even_rounds_buyer_offers():
    engine = make_engine(max_rounds=None, hard_cap=9)
    offer(engine, 90.0)
    while not engine.done:
        state = state_of(engine, engine.current_player)
        expected = PLAYER_1 if state["round"] % 2 else PLAYER_2
        assert state["last_offer"]["from_player"] == expected
        counter(engine, 60.0)


def test_history_entry_for_a_rejected_round():
    engine = make_engine()
    offer(engine, 90.0, message="Firm")
    counter(engine, 50.0, message="Too high")
    history = state_of(engine, PLAYER_1)["history"]
    assert len(history) == 1
    assert history[0] == {
        "round": 1,
        "offer": {"price": 90.0, "message": "Firm", "from_player": PLAYER_1},
        "decision": "RejectOffer",
        "counteroffer": {"price": 50.0, "message": "Too high", "from_player": PLAYER_2},
        "decided_by": PLAYER_2,
    }


def test_history_is_unfiltered_and_ordered_oldest_first():
    engine = make_engine(complete_information=False)
    offer(engine, 90.0, message="a")
    counter(engine, 50.0, message="b")
    counter(engine, 80.0, message="c")
    counter(engine, 60.0, message="d")
    for player in (PLAYER_1, PLAYER_2):
        history = state_of(engine, player)["history"]
        assert [entry["round"] for entry in history] == [1, 2, 3]
        assert [entry["offer"]["message"] for entry in history] == ["a", "b", "c"]
        assert [entry["decided_by"] for entry in history] == [PLAYER_2, PLAYER_1, PLAYER_2]
        for entry in history:
            assert entry["decided_by"] != entry["offer"]["from_player"]


def test_the_current_round_is_never_in_history_yet():
    engine = make_engine()
    offer(engine, 90.0)
    counter(engine, 50.0)
    state = state_of(engine, PLAYER_1)
    assert state["round"] == 2
    assert [entry["round"] for entry in state["history"]] == [1]


def test_accepting_records_the_closing_round_without_a_counteroffer():
    engine = make_engine()
    offer(engine, 70.0)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    entry = state_of(engine, PLAYER_1)["history"][-1]
    assert entry["decision"] == "AcceptOffer"
    assert entry["decided_by"] == PLAYER_2
    assert "counteroffer" not in entry


# --- payoffs -----------------------------------------------------------------


def test_acceptance_payoffs_are_price_minus_value():
    engine = make_engine(player_1_value=30.0, player_2_value=100.0)
    offer(engine, 70.0)
    result = engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert result.valid and result.game_over
    assert result.result == {"player_1_payoff": 40.0, "player_2_payoff": 30.0,
                             "outcome": "agreement"}
    assert engine.result.player_1_payoff == 40.0      # 70 - 30
    assert engine.result.player_2_payoff == 30.0      # 100 - 70
    assert engine.result.outcome == "agreement"
    assert engine.result.rounds_played == 1
    assert engine.result.detail["reason"] == "agreement"
    assert engine.result.detail["price"] == 70.0
    assert engine.result.detail["accepted_by"] == PLAYER_2


def test_seller_accepting_a_buyer_counteroffer_pays_at_that_price():
    engine = make_engine(player_1_value=30.0, player_2_value=100.0)
    offer(engine, 90.0)
    counter(engine, 50.0)
    engine.submit(PLAYER_1, {"decision": "AcceptOffer"})
    assert engine.result.player_1_payoff == 20.0      # 50 - 30
    assert engine.result.player_2_payoff == 50.0      # 100 - 50
    assert engine.result.rounds_played == 2


@pytest.mark.parametrize("price,payoff_1,payoff_2", [
    (30.0, 0.0, 70.0),
    (65.5, 35.5, 34.5),
    (100.0, 70.0, 0.0),
])
def test_price_only_splits_the_surplus(price, payoff_1, payoff_2):
    engine = make_engine(player_1_value=30.0, player_2_value=100.0)
    offer(engine, price)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert engine.result.player_1_payoff == pytest.approx(payoff_1)
    assert engine.result.player_2_payoff == pytest.approx(payoff_2)
    assert (engine.result.player_1_payoff
            + engine.result.player_2_payoff) == pytest.approx(70.0)


def test_a_losing_deal_is_legal_and_the_negative_payoff_is_not_clamped():
    engine = make_engine(player_1_value=30.0, player_2_value=100.0)
    offer(engine, 90.0)
    counter(engine, 10.0)
    engine.submit(PLAYER_1, {"decision": "AcceptOffer"})   # seller sells below cost
    assert engine.result.player_1_payoff == -20.0
    assert engine.result.player_2_payoff == 90.0
    assert engine.result.outcome == "agreement"


def test_buyer_overpaying_is_legal_and_negative():
    engine = make_engine(player_1_value=30.0, player_2_value=100.0)
    offer(engine, 140.0)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert engine.result.player_1_payoff == 110.0
    assert engine.result.player_2_payoff == -40.0


def test_empty_zopa_agreement_hurts_someone_and_no_deal_pays_zero():
    dealt = make_engine(player_1_value=80.0, player_2_value=40.0)
    offer(dealt, 60.0)
    dealt.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert dealt.result.player_1_payoff == -20.0
    assert dealt.result.player_2_payoff == -20.0
    # Payoffs sum to (buyer value - seller value), which is negative here.
    assert dealt.result.player_1_payoff + dealt.result.player_2_payoff == -40.0

    walked = make_engine(player_1_value=80.0, player_2_value=40.0)
    offer(walked, 60.0)
    walked.submit(PLAYER_2, {"decision": "WalkAway"})
    assert (walked.result.player_1_payoff, walked.result.player_2_payoff) == (0.0, 0.0)
    assert walked.result.payoff(PLAYER_1) > dealt.result.payoff(PLAYER_1)


# --- the five terminations ---------------------------------------------------


def test_acceptance_ends_the_game_and_blocks_further_moves():
    engine = make_engine()
    offer(engine, 70.0)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert engine.done
    late = engine.submit(PLAYER_1, {"decision": "AcceptOffer"})
    assert late.valid is False and "not active" in late.error


@pytest.mark.parametrize("walker", [PLAYER_2, PLAYER_1])
def test_walkaway_by_either_player_pays_zero(walker):
    engine = make_engine()
    offer(engine, 90.0)
    if walker == PLAYER_1:
        counter(engine, 50.0)                       # hand the decision back
    result = engine.submit(walker, {"decision": "WalkAway", "message": "Goodbye"})
    assert result.valid and result.game_over
    assert result.result == {"player_1_payoff": 0.0, "player_2_payoff": 0.0,
                             "outcome": "no_deal"}
    assert engine.result.detail == {"reason": "walkaway", "by": walker}
    assert state_of(engine, PLAYER_1)["history"][-1]["decision"] == "WalkAway"


def test_walkaway_is_available_on_the_final_round_too():
    engine = make_engine(max_rounds=1)
    offer(engine, 70.0)
    result = engine.submit(PLAYER_2, {"decision": "WalkAway"})
    assert result.game_over and engine.result.outcome == "no_deal"


def test_final_round_rejection_is_the_round_cap_biting():
    engine = make_engine(max_rounds=2)
    offer(engine, 90.0)
    counter(engine, 50.0)                           # round 2 == the cap
    assert state_of(engine, PLAYER_1)["round"] == 2
    result = engine.submit(PLAYER_1, {"decision": "RejectOffer"})
    assert result.valid and result.game_over
    assert result.result["outcome"] == "no_deal"
    assert (engine.result.player_1_payoff, engine.result.player_2_payoff) == (0.0, 0.0)
    assert engine.result.detail == {"reason": "final_round_rejection", "by": PLAYER_1}
    assert engine.result.rounds_played == 2


def test_the_game_can_never_mechanically_exceed_max_rounds():
    engine = make_engine(max_rounds=3)
    offer(engine, 90.0)
    counter(engine, 50.0)
    counter(engine, 80.0)
    assert state_of(engine, PLAYER_2)["round"] == 3
    # Round 3 is final: a counteroffer has nowhere to go.
    rejected = engine.submit(PLAYER_2, {"decision": "RejectOffer", "product_price": 40.0})
    assert rejected.valid is False
    assert state_of(engine, PLAYER_2)["round"] == 3
    engine.submit(PLAYER_2, {"decision": "RejectOffer"})
    assert engine.done and engine.result.outcome == "no_deal"


def test_timeout_hook_closes_the_game_as_a_no_deal():
    engine = make_engine()
    offer(engine, 70.0)
    result = engine.timeout(PLAYER_2)
    assert result.valid and result.game_over
    assert (engine.result.player_1_payoff, engine.result.player_2_payoff) == (0.0, 0.0)
    assert engine.result.outcome == "no_deal"
    assert engine.result.detail == {"reason": "timeout", "by": PLAYER_2}
    assert engine.timeout(PLAYER_1).valid is False   # already over


def test_timeout_is_available_in_the_opening_offer_phase():
    engine = make_engine()
    engine.timeout(PLAYER_1)
    assert engine.done and engine.result.outcome == "no_deal"
    assert state_of(engine, PLAYER_1)["history"] == []


def test_invalid_move_exhaustion_force_closes_as_a_no_deal():
    engine = make_engine()
    offer(engine, 70.0)
    for attempt in range(MAX_INVALID_ATTEMPTS):
        result = engine.submit(PLAYER_2, {"decision": "accept"})   # bargaining literal
        assert result.valid is False
        assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1 - attempt
    assert engine.done
    assert result.game_over and result.attempts_left == 0
    assert result.result == {"player_1_payoff": 0.0, "player_2_payoff": 0.0,
                             "outcome": "no_deal"}
    assert engine.result.detail["reason"] == "invalid_moves"
    assert engine.result.detail["by"] == PLAYER_2


def test_every_no_deal_route_pays_exactly_zero():
    routes = []

    walked = make_engine(); offer(walked, 70.0)
    walked.submit(PLAYER_2, {"decision": "WalkAway"}); routes.append(walked)

    capped = make_engine(max_rounds=1); offer(capped, 70.0)
    capped.submit(PLAYER_2, {"decision": "RejectOffer"}); routes.append(capped)

    timed = make_engine(); offer(timed, 70.0)
    timed.timeout(PLAYER_2); routes.append(timed)

    burned = make_engine(); offer(burned, 70.0)
    for _ in range(MAX_INVALID_ATTEMPTS):
        burned.submit(PLAYER_2, {"decision": "nope"})
    routes.append(burned)

    hard = make_engine(max_rounds=None, hard_cap=3); offer(hard, 90.0)
    while not hard.done:
        counter(hard, 60.0)
    routes.append(hard)

    reasons = set()
    for engine in routes:
        assert engine.done and engine.result.outcome == "no_deal"
        assert engine.result.player_1_payoff == 0.0
        assert engine.result.player_2_payoff == 0.0
        reasons.add(engine.result.detail["reason"])
    # Same payoffs, distinguishable causes: the rating layer treats them
    # differently, so detail must separate them.
    assert reasons == {"walkaway", "final_round_rejection", "timeout",
                       "invalid_moves", "hard_cap"}


# --- take-it-or-leave-it and even caps ---------------------------------------


def test_take_it_or_leave_it_accept():
    engine = make_engine(max_rounds=1, player_1_value=30.0, player_2_value=100.0)
    assert state_of(engine, PLAYER_1)["max_rounds"] == 1
    offer(engine, 80.0)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert engine.result.player_1_payoff == 50.0
    assert engine.result.player_2_payoff == 20.0


def test_take_it_or_leave_it_rejection_ends_it_and_the_seller_never_decides():
    engine = make_engine(max_rounds=1)
    offer(engine, 80.0)
    assert engine.current_player == PLAYER_2
    result = engine.submit(PLAYER_2, {"decision": "RejectOffer"})
    assert result.game_over
    assert engine.result.detail["reason"] == "final_round_rejection"
    # The seller was never handed a decision phase in this configuration.
    assert [entry["decided_by"] for entry in state_of(engine, PLAYER_1)["history"]] == [PLAYER_2]


def test_take_it_or_leave_it_rejects_a_counteroffer():
    engine = make_engine(max_rounds=1)
    offer(engine, 80.0)
    result = engine.submit(PLAYER_2, {"decision": "RejectOffer", "product_price": 40.0})
    assert result.valid is False
    assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1
    assert engine.done is False


def test_even_cap_makes_the_seller_the_final_decider():
    engine = make_engine(max_rounds=4)
    offer(engine, 90.0)
    counter(engine, 40.0)
    counter(engine, 85.0)
    counter(engine, 45.0)                              # round 4, buyer's offer
    state = state_of(engine, PLAYER_1)
    assert state["round"] == 4
    assert state["current_player"] == PLAYER_1
    assert state["last_offer"]["from_player"] == PLAYER_2
    assert "required" not in engine.observation(PLAYER_1)["valid_actions"]["fields"]["product_price"]
    engine.submit(PLAYER_1, {"decision": "RejectOffer"})
    assert engine.done and engine.result.detail["by"] == PLAYER_1


# --- uncapped games ----------------------------------------------------------


def test_uncapped_games_never_reach_a_final_round():
    engine = make_engine(max_rounds=None, hard_cap=50)
    offer(engine, 90.0)
    for _ in range(8):
        fields = engine.observation(engine.current_player)["valid_actions"]["fields"]
        assert fields["product_price"] == "number (required if RejectOffer - your counteroffer)"
        bare = engine.submit(engine.current_player, {"decision": "RejectOffer"})
        assert bare.valid is False                    # no counteroffer, no successor
        counter(engine, 60.0)
    assert not engine.done


def test_hard_cap_is_a_simulator_artifact_and_never_visible():
    engine = make_engine(max_rounds=None, hard_cap=3)
    offer(engine, 90.0)
    counter(engine, 50.0)
    counter(engine, 85.0)
    state = state_of(engine, PLAYER_1)
    assert state["round"] == 3
    assert "max_rounds" not in state and state["horizon_known"] is False
    assert "hard_cap" not in state
    result = counter(engine, 55.0)                    # would open round 4
    assert result.game_over and engine.result.outcome == "no_deal"
    assert engine.result.detail == {"reason": "hard_cap", "hard_cap": 3}


# --- invalid moves -----------------------------------------------------------


@pytest.mark.parametrize("action", [
    {},                                    # no price at all
    {"price": 70},                         # wrong key
    {"message": "hello"},
    {"product_price": None},
    {"product_price": "70"},               # numeric string: rejected, not parsed
    {"product_price": "cheap"},
    {"product_price": True},               # bool is not a price
    {"product_price": float("nan")},
    {"product_price": float("inf")},
    {"product_price": [70]},
    {"product_price": 70, "message": "x" * (MAX_MESSAGE_LEN + 1)},
    {"product_price": 70, "message": 70},
])
def test_invalid_offers_are_rejected(action):
    engine = make_engine()
    result = engine.submit(PLAYER_1, action)
    assert result.valid is False and result.error
    assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1
    assert engine.observation(PLAYER_1)["phase"] == "offer"
    assert state_of(engine, PLAYER_1)["last_offer"] is None


@pytest.mark.parametrize("action", [
    "AcceptOffer", None, 42, ["AcceptOffer"], ("product_price", 70),
    {"decision": "AcceptOffer"},                 # a decision in the offer phase
    {"decision": "WalkAway"},                    # no walking away before an offer
])
def test_non_dict_and_wrong_phase_actions_are_rejected_in_the_offer_phase(action):
    engine = make_engine()
    result = engine.submit(PLAYER_1, action)
    assert result.valid is False and result.error
    assert engine.done is False
    assert engine.observation(PLAYER_1)["phase"] == "offer"


@pytest.mark.parametrize("decision", [
    "accept", "reject", "walkaway",        # bargaining literals
    "yes", "no",                           # persuasion literals
    "acceptoffer", "ACCEPTOFFER", "Accept Offer", "AcceptOffer ",
    "", None, 1, True,
])
def test_decision_literals_are_exact(decision):
    engine = make_engine()
    offer(engine, 70.0)
    action = {} if decision is None else {"decision": decision}
    result = engine.submit(PLAYER_2, action)
    assert result.valid is False
    assert engine.done is False
    assert state_of(engine, PLAYER_2)["round"] == 1


@pytest.mark.parametrize("action", [
    {"decision": "RejectOffer"},                              # no counteroffer
    {"decision": "RejectOffer", "product_price": None},
    {"decision": "RejectOffer", "product_price": "60"},
    {"decision": "RejectOffer", "product_price": float("nan")},
    {"decision": "RejectOffer", "price": 60},
    {"decision": "AcceptOffer", "message": "y" * (MAX_MESSAGE_LEN + 1)},
    {"decision": "WalkAway", "message": 5},
])
def test_invalid_decisions_are_rejected(action):
    engine = make_engine(max_rounds=5)
    offer(engine, 70.0)
    result = engine.submit(PLAYER_2, action)
    assert result.valid is False and result.error
    assert engine.done is False


def test_a_rejected_move_does_not_advance_the_game():
    engine = make_engine()
    offer(engine, 70.0)
    before = snapshot(engine)
    engine.submit(PLAYER_2, {"decision": "reject", "product_price": 50.0})
    assert snapshot(engine) == before


def test_a_rejected_offer_does_not_advance_the_game():
    engine = make_engine()
    before = snapshot(engine)
    engine.submit(PLAYER_1, {"product_price": "free"})
    assert snapshot(engine) == before


def test_attempts_are_counted_per_player():
    """The seller burns four, then offers; the buyer still has the full five."""
    engine = make_engine()
    for attempt in range(MAX_INVALID_ATTEMPTS - 1):
        result = engine.submit(PLAYER_1, {})
        assert result.valid is False
        assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1 - attempt
    offer(engine, 70.0)
    result = engine.submit(PLAYER_2, {"decision": "nope"})
    assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1
    assert engine.done is False
    # The seller's own budget was NOT refilled by the valid move.
    counter(engine, 50.0)
    assert engine.submit(PLAYER_1, {"decision": "nope"}).attempts_left == 0
    assert engine.done and engine.result.detail["by"] == PLAYER_1


def test_the_last_attempt_of_the_seller_ends_the_game_in_the_offer_phase():
    engine = make_engine()
    for _ in range(MAX_INVALID_ATTEMPTS):
        result = engine.submit(PLAYER_1, {"product_price": "free"})
    assert result.game_over and result.attempts_left == 0
    assert engine.done and engine.result.outcome == "no_deal"
    assert engine.result.detail["by"] == PLAYER_1


def test_per_move_attempt_budget_is_available_as_a_flag():
    engine = make_engine(attempts_per_game=False)
    for _ in range(MAX_INVALID_ATTEMPTS - 1):
        engine.submit(PLAYER_1, {})
    offer(engine, 70.0)                       # a valid move resets the budget
    counter(engine, 50.0)
    result = engine.submit(PLAYER_1, {"decision": "bogus"})
    assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1


def test_out_of_turn_moves_are_errors_not_invalid_moves():
    engine = make_engine()
    result = engine.submit(PLAYER_2, {"product_price": 70.0})
    assert result.valid is False and "turn" in result.error
    assert result.attempts_left == MAX_INVALID_ATTEMPTS       # nothing consumed
    offer(engine, 70.0)
    result = engine.submit(PLAYER_1, {"decision": "AcceptOffer"})
    assert result.valid is False and result.attempts_left == MAX_INVALID_ATTEMPTS
    assert engine.done is False


def test_moves_after_the_game_ends_are_errors_not_invalid_moves():
    engine = make_engine()
    offer(engine, 70.0)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    result = engine.submit(PLAYER_1, {"decision": "WalkAway"})
    assert result.valid is False and result.attempts_left == MAX_INVALID_ATTEMPTS
    assert engine.result.outcome == "agreement"               # unchanged


def test_an_unknown_player_is_an_error():
    engine = make_engine()
    result = engine.submit("player_3", {"product_price": 70.0})
    assert result.valid is False and "not a player" in result.error
    assert engine.done is False


def test_unknown_keys_in_an_action_are_ignored():
    engine = make_engine()
    # The live strategy attaches a "_plan" key for logging; the server ignores it.
    assert offer(engine, 70.0, _plan={"target": 70.0}).valid
    assert engine.submit(PLAYER_2, {"decision": "AcceptOffer", "_plan": {}}).valid


def test_any_finite_price_is_legal_however_foolish():
    for price in (-25.0, 0, 1e9):
        engine = make_engine()
        assert offer(engine, price).valid
        assert state_of(engine, PLAYER_2)["last_offer"]["price"] == float(price)
        assert isinstance(state_of(engine, PLAYER_2)["last_offer"]["price"], float)


# --- messages ----------------------------------------------------------------


def test_a_message_at_the_length_limit_is_legal():
    engine = make_engine()
    text = "x" * MAX_MESSAGE_LEN
    assert offer(engine, 70.0, message=text).valid
    assert state_of(engine, PLAYER_2)["last_offer"]["message"] == text


def test_messages_ride_on_offers_counters_accepts_and_walkaways():
    engine = make_engine()
    offer(engine, 90.0, message="opening")
    assert counter(engine, 50.0, message="counter").valid
    assert state_of(engine, PLAYER_1)["last_offer"]["message"] == "counter"
    assert engine.submit(PLAYER_1, {"decision": "AcceptOffer", "message": "deal"}).valid

    parting = make_engine()
    offer(parting, 90.0)
    assert parting.submit(PLAYER_2, {"decision": "WalkAway", "message": "bye"}).valid


def test_messages_are_dropped_when_the_game_forbids_them():
    engine = make_engine(messages_allowed=False)
    result = offer(engine, 70.0, message="psst")
    assert result.valid                     # dropped, not rejected (assumption 7)
    assert state_of(engine, PLAYER_2)["last_offer"]["message"] is None


def test_an_offer_without_a_message_carries_a_null_message():
    engine = make_engine()
    offer(engine, 70.0)
    assert state_of(engine, PLAYER_2)["last_offer"]["message"] is None


# --- the completed game ------------------------------------------------------


def test_completed_observation_reports_the_result():
    engine = make_engine()
    offer(engine, 70.0, message="Best price")
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    for player in (PLAYER_1, PLAYER_2):
        obs = engine.observation(player)
        assert obs["phase"] == "completed"
        assert obs["game_state"]["phase"] == "completed"
        assert obs["valid_actions"] is None
        assert obs["status"] == "completed"
        assert obs["result"] == {"player_1_payoff": 40.0, "player_2_payoff": 30.0,
                                 "outcome": "agreement"}
        # No move is awaited, so nobody is the current player.
        assert "current_player" not in obs["game_state"]
        # The record survives for post-game inspection.
        assert obs["game_state"]["last_offer"]["price"] == 70.0
        assert len(obs["game_state"]["history"]) == 1


def test_a_no_deal_reports_status_no_deal():
    engine = make_engine()
    offer(engine, 70.0)
    engine.submit(PLAYER_2, {"decision": "WalkAway"})
    assert engine.observation(PLAYER_1)["status"] == "no_deal"


def test_filtering_still_applies_after_the_game_ends():
    engine = make_engine(complete_information=False)
    offer(engine, 70.0)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert "player_2_value" not in state_of(engine, PLAYER_1)
    assert "player_1_value" not in state_of(engine, PLAYER_2)


# --- prompt ------------------------------------------------------------------


def test_prompt_describes_the_situation_without_leaking_the_opponent_value():
    engine = make_engine(player_1_value=30.0, player_2_value=137.5,
                         complete_information=False, max_rounds=5)
    seller_prompt = engine.observation(PLAYER_1)["prompt"]
    assert "seller" in seller_prompt and "30" in seller_prompt
    assert "137.5" not in seller_prompt
    offer(engine, 70.0)
    buyer_prompt = engine.observation(PLAYER_2)["prompt"]
    assert "buyer" in buyer_prompt and "137.5" in buyer_prompt
    assert "70" in buyer_prompt


def test_prompt_flags_the_final_round_and_the_ending():
    engine = make_engine(max_rounds=1)
    offer(engine, 70.0)
    assert "no deal" in engine.observation(PLAYER_2)["prompt"]
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})
    assert "closed at" in engine.observation(PLAYER_1)["prompt"]


def test_prompt_survives_an_uncapped_game_and_a_no_deal_ending():
    engine = make_engine(max_rounds=None)
    assert "no round limit" in engine.observation(PLAYER_1)["prompt"]
    offer(engine, 70.0)
    engine.timeout(PLAYER_2)
    assert "no deal" in engine.observation(PLAYER_1)["prompt"]


def test_prompt_renders_money_grouped_and_exact_on_every_money_scale():
    """``prompt`` is the field an LLM strategy actually reads, and the docs' one
    sample renders money grouped and in full ("dividing $1,000 with Bob"). A
    six-significant-digit format silently turns the two larger scales into
    "$1.2e+06" -- a number the live server would never send, on two thirds of
    drawn configurations.
    """
    for scale in MONEY_SCALES:
        seller_value = 1.2 * scale
        buyer_value = 1.5 * scale
        price = 1.45 * scale + 0.5          # deliberately not a round number
        engine = make_engine(player_1_value=seller_value, player_2_value=buyer_value,
                             max_rounds=5)

        opening = engine.observation(PLAYER_1)["prompt"]
        assert "e+" not in opening.lower(), opening
        assert f"${seller_value:,.0f}" in opening, opening

        offer(engine, price)
        view = engine.observation(PLAYER_2)
        prompt = view["prompt"]
        assert "e+" not in prompt.lower(), prompt
        assert f"${buyer_value:,.0f}" in prompt, prompt
        # The prose must not contradict the state it describes: the price the
        # buyer is told about is the price game_state carries, digit for digit.
        assert view["game_state"]["last_offer"]["price"] == price
        assert price in money_in(prompt), prompt


def test_prompt_of_a_closed_game_renders_price_and_payoff_exactly():
    engine = make_engine(player_1_value=1_200_000.0, player_2_value=1_500_000.0,
                         max_rounds=5)
    offer(engine, 1_450_000.5)
    engine.submit(PLAYER_2, {"decision": "AcceptOffer"})

    seller_prompt = engine.observation(PLAYER_1)["prompt"]
    assert "e+" not in seller_prompt.lower(), seller_prompt
    assert "$1,450,000.50" in seller_prompt, seller_prompt
    assert "$250,000.50" in seller_prompt, seller_prompt      # 1,450,000.50 - 1,200,000

    buyer_prompt = engine.observation(PLAYER_2)["prompt"]
    assert "$49,999.50" in buyer_prompt, buyer_prompt         # 1,500,000 - 1,450,000.50


def test_prompt_keeps_a_price_finer_than_cents_rather_than_rounding_it():
    """Sub-cent prices are legal (assumption 5), and a prompt that rounds one is
    a prompt that disagrees with ``last_offer["price"]``."""
    engine = make_engine(max_rounds=5)
    offer(engine, 70.125)
    view = engine.observation(PLAYER_2)
    assert view["game_state"]["last_offer"]["price"] == 70.125
    assert 70.125 in money_in(view["prompt"]), view["prompt"]


# --- driving the engine the way the arena does -------------------------------


def test_the_documented_strategy_runs_unmodified_against_the_engine():
    """The strategy from the docs' quick start, verbatim."""
    def negotiation_strategy(game):
        state = game["game_state"]
        me = state["current_player"]
        role = state[f"{me}_role"]
        my_value = state[f"{me}_value"]
        if game["valid_actions"]["type"] == "offer":
            return {"product_price": my_value * (1.5 if role == "seller" else 0.7)}
        price = state["last_offer"]["price"]
        profitable = price >= my_value if role == "seller" else price <= my_value
        if profitable:
            return {"decision": "AcceptOffer"}
        return {"decision": "RejectOffer",
                "product_price": my_value * (1.3 if role == "seller" else 0.8)}

    engine = make_engine(player_1_value=30.0, player_2_value=100.0, max_rounds=6)
    while not engine.done:
        player = engine.current_player
        result = engine.submit(player, negotiation_strategy(engine.observation(player)))
        assert result.valid, result.error
    # Seller opens at 45, which is already under the buyer's 100: instant deal.
    assert engine.result.outcome == "agreement"
    assert engine.result.player_1_payoff == pytest.approx(15.0)
    assert engine.result.player_2_payoff == pytest.approx(55.0)
    assert math.isclose(engine.result.player_1_payoff + engine.result.player_2_payoff, 70.0)


def test_a_full_game_is_reproducible_from_one_seed():
    def run():
        engine = make_engine(seed=99, max_rounds=None, hard_cap=6)
        offer(engine, 90.0)
        while not engine.done:
            counter(engine, 60.0)
        return (engine.observation(PLAYER_1), engine.result.as_dict(),
                engine.result.detail)
    assert run() == run()
