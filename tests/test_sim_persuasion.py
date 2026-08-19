"""Tests for the persuasion engine.

These are fidelity tests, not behaviour tests: what matters is that the dict
shapes, the filtering, the payoffs and the rejections match what the live server
does, because a strategy tuned against a simulator that quietly differs is worse
off than one that was never tuned.

Quality draws are pinned with a scripted rng so the payoff assertions are exact
numbers computed by hand rather than statistics.
"""

from __future__ import annotations

import random

import pytest

from sim.persuasion import MAX_MESSAGE_LEN, PersuasionEngine
from sim.types import MAX_INVALID_ATTEMPTS, Config

SELLER = "player_1"
BUYER = "player_2"

BUY = {"decision": "yes"}
PASS = {"decision": "no"}
PITCH = {"message": "This one is worth it."}


class ScriptedRandom:
    """Stands in for random.Random with a scripted ``random()`` stream.

    ``_draw_quality`` is "high" iff ``random() < p``, so 0.0 forces high and 1.0
    forces low for every p in [0, 1].
    """

    def __init__(self, values):
        self._values = list(values)
        self.calls = 0

    def random(self):
        value = self._values[self.calls % len(self._values)]
        self.calls += 1
        return value


def make_config(**overrides) -> Config:
    params = {"product_price": 40, "p": 0.5, "v": 100, "u": 0,
              "total_rounds": 3, "seller_message_type": "text",
              "is_seller_know_cv": True,
              # Pin the opponent-disclosure coin flip so the rng stream is
              # nothing but quality draws.
              "disclose_opponent": True, "opponent_name": "foe"}
    params.update(overrides)
    return Config("persuasion", params)


def make_engine(qualities=("high",), rng=None, **overrides) -> PersuasionEngine:
    stream = rng or ScriptedRandom([0.0 if q == "high" else 1.0 for q in qualities])
    return PersuasionEngine(make_config(**overrides), stream, "g1")


def seller_action(engine, message="ok"):
    return {"message": message} if engine.seller_message_type == "text" else BUY


def play(engine, buyer_decisions, message="ok"):
    """Run the game out, the buyer deciding from ``buyer_decisions`` per round."""
    decisions = list(buyer_decisions)
    while not engine.done:
        player = engine.current_player
        if player == SELLER:
            engine.submit(player, seller_action(engine, message))
        else:
            engine.submit(player, {"decision": decisions.pop(0)})
    return engine.result


# --------------------------------------------------------------- envelope shape

ENVELOPE_KEYS = {"game_id", "game_family", "your_player", "phase", "opponent",
                 "game_state", "valid_actions", "prompt"}


def test_observation_has_exactly_the_api_envelope():
    engine = make_engine()
    for player in (SELLER, BUYER):
        obs = engine.observation(player)
        assert set(obs) == ENVELOPE_KEYS
        assert obs["game_id"] == "g1"
        assert obs["game_family"] == "persuasion"
        assert obs["your_player"] == player
        assert isinstance(obs["prompt"], str) and obs["prompt"]
        assert isinstance(obs["valid_actions"]["fields"], dict)


def test_engine_declares_its_family():
    assert PersuasionEngine.game_family == "persuasion"
    assert make_engine().game_family == "persuasion"


def test_top_level_phase_mirrors_game_state_phase():
    engine = make_engine(("high", "high", "high"))
    for _ in range(6):
        for player in (SELLER, BUYER):
            obs = engine.observation(player)
            assert obs["phase"] == obs["game_state"]["phase"]
        if engine.done:
            break
        engine.submit(engine.current_player,
                      seller_action(engine) if engine.current_player == SELLER else BUY)


def test_opponent_field_is_disclosed_or_hidden_and_fixed_for_the_game():
    disclosed = make_engine(("high",), total_rounds=1)
    assert disclosed.observation(SELLER)["opponent"] == {"type": "agent", "name": "foe"}

    hidden = make_engine(("high",), total_rounds=1, disclose_opponent=False)
    assert hidden.observation(BUYER)["opponent"] == {"type": "hidden", "name": None}

    before = hidden.observation(SELLER)["opponent"]
    hidden.submit(SELLER, PITCH)
    assert hidden.observation(BUYER)["opponent"] == before


def test_opponent_disclosure_is_drawn_from_the_injected_rng():
    # No explicit disclose_opponent: the coin flip comes off the rng stream.
    params = make_config().params
    params.pop("disclose_opponent")
    always_hidden = PersuasionEngine(Config("persuasion", params),
                                     ScriptedRandom([0.99]), "g")
    always_shown = PersuasionEngine(Config("persuasion", params),
                                    ScriptedRandom([0.1]), "g")
    assert always_hidden.observation(SELLER)["opponent"]["type"] == "hidden"
    assert always_shown.observation(SELLER)["opponent"]["type"] == "agent"


def test_observation_works_for_the_player_who_is_not_to_move():
    engine = make_engine(("high", "high"), total_rounds=2)
    obs = engine.observation(BUYER)               # seller's turn
    assert obs["your_player"] == BUYER
    assert obs["game_state"]["current_player"] == SELLER
    assert obs["valid_actions"]["type"] == "seller_message"


# --------------------------------------------------------------- turn structure

def test_turn_order_alternates_seller_first_for_exactly_two_moves_per_round():
    engine = make_engine(("high", "low", "high"), total_rounds=3)
    seen = []
    while not engine.done:
        player = engine.current_player
        seen.append(player)
        engine.submit(player, seller_action(engine) if player == SELLER else BUY)
    assert seen == [SELLER, BUYER] * 3
    assert len(seen) == 2 * 3


def test_text_mode_action_type_is_seller_message():
    engine = make_engine(seller_message_type="text")
    obs = engine.observation(SELLER)
    assert obs["game_state"]["phase"] == "seller_message"
    assert obs["valid_actions"]["type"] == "seller_message"
    assert set(obs["valid_actions"]["fields"]) == {"message"}


def test_binary_mode_keeps_the_seller_message_phase_but_changes_the_action_type():
    engine = make_engine(seller_message_type="binary")
    obs = engine.observation(SELLER)
    # The subtlety that burns attempts live: phase does NOT say "binary".
    assert obs["phase"] == "seller_message"
    assert obs["game_state"]["phase"] == "seller_message"
    assert obs["valid_actions"]["type"] == "seller_recommendation"
    assert set(obs["valid_actions"]["fields"]) == {"decision"}


def test_buyer_phase_action_shape():
    engine = make_engine()
    engine.submit(SELLER, PITCH)
    obs = engine.observation(BUYER)
    assert obs["phase"] == "buyer_decision"
    assert obs["game_state"]["current_player"] == BUYER
    assert obs["valid_actions"]["type"] == "buyer_decision"
    assert set(obs["valid_actions"]["fields"]) == {"decision"}


def test_completed_game_exposes_no_pending_action():
    engine = make_engine(("high",), total_rounds=1)
    play(engine, ["yes"])
    obs = engine.observation(BUYER)
    assert obs["phase"] == "completed"
    assert obs["valid_actions"]["type"] is None
    assert obs["valid_actions"]["fields"] == {}


# ------------------------------------------------------------ state field shape

COMMON_KEYS = {"phase", "current_player", "product_price", "p", "seller_message",
               "seller_message_type", "round", "total_rounds",
               "seller_total_payoff", "history"}

# Every key the documented persuasion field list allows, across all views. A
# state key outside this set is the dangerous direction of infidelity: a
# strategy tuned here would branch on it and then KeyError against a server that
# never sends it. `is_seller_know_cv` is deliberately NOT here — the docs name it
# only as the configuration condition on the v/u bullet, never as a state field.
DOCUMENTED_KEYS = COMMON_KEYS | {"v", "u", "buyer_total_payoff", "current_quality"}


def test_round_one_state_is_the_documented_fresh_state():
    engine = make_engine(("high", "high"), total_rounds=2)
    state = engine.observation(SELLER)["game_state"]
    assert state["round"] == 1
    assert state["total_rounds"] == 2
    assert state["history"] == []                 # present and empty, never absent
    assert "seller_message" in state and state["seller_message"] is None
    assert state["seller_total_payoff"] == 0
    assert engine.observation(BUYER)["game_state"]["buyer_total_payoff"] == 0


def test_both_players_always_see_the_common_fields():
    engine = make_engine(("high", "low"), total_rounds=2, is_seller_know_cv=False)
    for player in (SELLER, BUYER):
        assert COMMON_KEYS <= set(engine.observation(player)["game_state"])


def test_no_view_ever_carries_a_key_outside_the_documented_field_list():
    # Every phase of every information condition, so a key added to one branch
    # of the filtering cannot slip through.
    for knows_cv in (True, False):
        for mode in ("text", "binary"):
            engine = make_engine(("high", "low"), total_rounds=2,
                                 is_seller_know_cv=knows_cv,
                                 seller_message_type=mode)
            for step in (None, "seller", "buyer", "seller", "buyer"):
                if step == "seller":
                    engine.submit(SELLER, seller_action(engine))
                elif step == "buyer":
                    engine.submit(BUYER, BUY)
                for player in (SELLER, BUYER):
                    keys = set(engine.observation(player)["game_state"])
                    assert keys <= DOCUMENTED_KEYS, sorted(keys - DOCUMENTED_KEYS)


def test_the_information_condition_itself_is_not_a_state_field():
    # The docs name `is_seller_know_cv` only as the configuration condition on
    # the v/u bullet. Emitting it invites a tuned strategy to index it and
    # KeyError live; the seller can still infer it from whether `v` reached it.
    for knows_cv in (True, False):
        engine = make_engine(("high",), total_rounds=1, is_seller_know_cv=knows_cv)
        for player in (SELLER, BUYER):
            assert "is_seller_know_cv" not in engine.observation(player)["game_state"]
        assert ("v" in engine.observation(SELLER)["game_state"]) is knows_cv


def test_persuasion_state_carries_no_foreign_family_keys():
    engine = make_engine(("high", "low"), total_rounds=2)
    engine.submit(SELLER, PITCH)
    forbidden = {"messages_allowed", "complete_information", "max_rounds",
                 "horizon_known", "last_offer", "delta_1", "delta_2",
                 "money_to_divide", "player_1_role", "player_2_role",
                 "player_1_value", "player_2_value", "discount"}
    for player in (SELLER, BUYER):
        state = engine.observation(player)["game_state"]
        assert forbidden.isdisjoint(state)


def test_seller_message_holds_only_the_current_round_and_resets():
    engine = make_engine(("high", "high"), total_rounds=2)
    engine.submit(SELLER, {"message": "round one pitch"})
    assert engine.observation(BUYER)["game_state"]["seller_message"] == "round one pitch"
    engine.submit(BUYER, BUY)
    # New round: the message is cleared, the old one lives only in history.
    state = engine.observation(SELLER)["game_state"]
    assert state["round"] == 2
    assert state["seller_message"] is None
    assert state["history"][0]["seller_message"] == "round one pitch"


def test_binary_history_records_the_literal_decision_string():
    engine = make_engine(("high", "low"), total_rounds=2, seller_message_type="binary")
    engine.submit(SELLER, {"decision": "no"})
    engine.submit(BUYER, PASS)
    entry = engine.observation(BUYER)["game_state"]["history"][0]
    assert entry["seller_message"] == "no"
    assert isinstance(entry["seller_message"], str)


def test_history_entries_are_oldest_first_with_the_documented_keys():
    engine = make_engine(("high", "low", "high"), total_rounds=3)
    play(engine, ["yes", "yes", "no"])
    history = engine.observation(SELLER)["game_state"]["history"]
    assert [h["round"] for h in history] == [1, 2, 3]
    assert set(history[0]) == {"round", "seller_message", "buyer_decision", "bought",
                               "quality", "seller_payoff", "buyer_payoff"}
    assert [h["bought"] for h in history] == [True, True, False]
    assert [h["buyer_decision"] for h in history] == ["yes", "yes", "no"]


def test_history_payoffs_are_per_round_increments_not_running_totals():
    engine = make_engine(("high", "high", "high"), total_rounds=3, product_price=40)
    play(engine, ["yes", "yes", "yes"])
    state = engine.observation(BUYER)["game_state"]
    assert [h["seller_payoff"] for h in state["history"]] == [40, 40, 40]
    assert [h["buyer_payoff"] for h in state["history"]] == [60, 60, 60]
    assert state["seller_total_payoff"] == 120
    assert state["buyer_total_payoff"] == 180


def test_running_totals_update_after_each_completed_round():
    engine = make_engine(("high", "low", "high"), total_rounds=3, product_price=40)
    engine.submit(SELLER, PITCH)
    engine.submit(BUYER, BUY)
    assert engine.observation(SELLER)["game_state"]["seller_total_payoff"] == 40
    assert engine.observation(BUYER)["game_state"]["buyer_total_payoff"] == 60
    engine.submit(SELLER, PITCH)
    engine.submit(BUYER, BUY)                     # low quality: -40
    assert engine.observation(SELLER)["game_state"]["seller_total_payoff"] == 80
    assert engine.observation(BUYER)["game_state"]["buyer_total_payoff"] == 20


# ---------------------------------------------------------- private information

def test_buyer_never_sees_current_quality_in_any_phase_or_round():
    engine = make_engine(("high", "low", "high"), total_rounds=3)
    while not engine.done:
        assert "current_quality" not in engine.observation(BUYER)["game_state"]
        player = engine.current_player
        engine.submit(player, seller_action(engine) if player == SELLER else BUY)
        assert "current_quality" not in engine.observation(BUYER)["game_state"]


def test_seller_sees_current_quality_in_both_phases_of_an_active_round():
    engine = make_engine(("low", "high"), total_rounds=2)
    assert engine.observation(SELLER)["game_state"]["current_quality"] == "low"
    engine.submit(SELLER, PITCH)
    # Still the seller's round; GET works between turns.
    assert engine.observation(SELLER)["game_state"]["current_quality"] == "low"
    engine.submit(BUYER, PASS)
    assert engine.observation(SELLER)["game_state"]["current_quality"] == "high"


def test_current_quality_is_dropped_once_the_game_completes():
    engine = make_engine(("high",), total_rounds=1)
    play(engine, ["yes"])
    assert "current_quality" not in engine.observation(SELLER)["game_state"]


def test_seller_without_cv_knowledge_sees_no_valuations_and_no_buyer_payoffs():
    engine = make_engine(("high", "low"), total_rounds=2, is_seller_know_cv=False)
    play(engine, ["yes", "yes"])
    state = engine.observation(SELLER)["game_state"]
    # Absent, not None — a strategy must not be able to read a masked value.
    assert "v" not in state
    assert "u" not in state
    assert "buyer_total_payoff" not in state
    assert all("buyer_payoff" not in h for h in state["history"])


def test_seller_with_cv_knowledge_sees_valuations_and_buyer_payoffs():
    engine = make_engine(("high", "low"), total_rounds=2, is_seller_know_cv=True)
    play(engine, ["yes", "yes"])
    state = engine.observation(SELLER)["game_state"]
    assert state["v"] == 100 and state["u"] == 0
    assert state["buyer_total_payoff"] == 20      # (100-40) + (0-40)
    assert [h["buyer_payoff"] for h in state["history"]] == [60, -40]


def test_buyer_always_sees_its_own_valuations_in_every_information_condition():
    for knows in (True, False):
        engine = make_engine(("high",), total_rounds=1, is_seller_know_cv=knows)
        state = engine.observation(BUYER)["game_state"]
        assert state["v"] == 100 and state["u"] == 0
        assert "buyer_total_payoff" in state


def test_buyer_learns_quality_only_for_rounds_it_bought():
    engine = make_engine(("high", "low", "high"), total_rounds=3)
    play(engine, ["yes", "no", "yes"])
    history = engine.observation(BUYER)["game_state"]["history"]
    assert history[0]["quality"] == "high"
    assert "quality" not in history[1]            # passed: a permanent hole
    assert history[2]["quality"] == "high"
    # The seller's record has no holes.
    seller_history = engine.observation(SELLER)["game_state"]["history"]
    assert [h["quality"] for h in seller_history] == ["high", "low", "high"]


def test_the_buyers_quality_gap_survives_the_end_of_the_game():
    engine = make_engine(("low",), total_rounds=1)
    play(engine, ["no"])
    assert engine.done
    assert "quality" not in engine.observation(BUYER)["game_state"]["history"][0]


def test_final_round_quality_reaches_the_buyer_only_once_the_game_is_over():
    engine = make_engine(("high",), total_rounds=1)
    engine.submit(SELLER, PITCH)
    # Deciding now, the buyer has no quality information at all.
    assert "current_quality" not in engine.observation(BUYER)["game_state"]
    assert engine.observation(BUYER)["game_state"]["history"] == []
    engine.submit(BUYER, BUY)
    assert engine.observation(BUYER)["game_state"]["history"][0]["quality"] == "high"


def test_seller_prompt_does_not_leak_the_buyers_valuation():
    engine = make_engine(("high",), total_rounds=1, is_seller_know_cv=False,
                         v=137, product_price=40)
    assert "137" not in engine.observation(SELLER)["prompt"]
    engine.submit(SELLER, PITCH)
    assert "137" in engine.observation(BUYER)["prompt"]


def test_completed_prompt_does_not_leak_the_buyers_total_to_an_uninformed_seller():
    engine = make_engine(("high",), total_rounds=1, is_seller_know_cv=False,
                         v=137, product_price=40)
    play(engine, ["yes"])
    assert "97" not in engine.observation(SELLER)["prompt"]   # 137 - 40
    assert "97" in engine.observation(BUYER)["prompt"]


# ------------------------------------------------------------------- payoffs

def test_exact_payoffs_for_a_hand_computed_game():
    # price 40, v 100, u 0, qualities high/low/high/low, buyer buys 1, 2 and 4.
    #   seller = 40 * 3                                    = 120
    #   buyer  = (100-40) + (0-40) + 0 + (0-40)            = -20
    engine = make_engine(("high", "low", "high", "low"), total_rounds=4,
                         product_price=40, v=100, u=0)
    result = play(engine, ["yes", "yes", "no", "yes"])
    assert result.player_1_payoff == 120
    assert result.player_2_payoff == -20
    assert result.outcome == "completed"
    assert result.rounds_played == 4
    assert result.as_dict() == {"player_1_payoff": 120, "player_2_payoff": -20,
                                "outcome": "completed"}


def test_seller_is_paid_the_price_regardless_of_quality():
    engine = make_engine(("low", "low"), total_rounds=2, product_price=40)
    result = play(engine, ["yes", "yes"])
    assert result.player_1_payoff == 80
    assert result.player_2_payoff == -80          # u = 0, so exactly -price twice


def test_a_pass_pays_both_sides_nothing_and_does_not_end_the_game():
    engine = make_engine(("high", "high"), total_rounds=2, product_price=40)
    engine.submit(SELLER, PITCH)
    engine.submit(BUYER, PASS)
    assert not engine.done
    state = engine.observation(BUYER)["game_state"]
    assert state["history"][0]["seller_payoff"] == 0
    assert state["history"][0]["buyer_payoff"] == 0
    assert state["seller_total_payoff"] == 0 and state["buyer_total_payoff"] == 0


def test_payoffs_are_undiscounted_so_round_order_does_not_matter():
    early = make_engine(("high", "low"), total_rounds=2, product_price=40)
    late = make_engine(("low", "high"), total_rounds=2, product_price=40)
    assert play(early, ["yes", "yes"]).player_2_payoff == \
        play(late, ["yes", "yes"]).player_2_payoff == 20
    # A late sale is worth exactly as much as an early one.
    first = make_engine(("high", "high"), total_rounds=2, product_price=40)
    second = make_engine(("high", "high"), total_rounds=2, product_price=40)
    assert play(first, ["yes", "no"]).player_1_payoff == \
        play(second, ["no", "yes"]).player_1_payoff == 40


def test_integral_configurations_stay_integral():
    engine = make_engine(("high",), total_rounds=1, product_price=40, v=100, u=0)
    result = play(engine, ["yes"])
    assert isinstance(result.player_1_payoff, int)
    assert isinstance(result.player_2_payoff, int)


def test_negative_buyer_total_is_representable():
    engine = make_engine(("low", "low", "low"), total_rounds=3, product_price=25)
    result = play(engine, ["yes", "yes", "yes"])
    assert result.player_2_payoff == -75
    assert result.player_1_payoff == 75


# --------------------------------------------------------------- terminations

def test_natural_completion_is_signalled_only_on_the_buyers_final_move():
    engine = make_engine(("high", "high"), total_rounds=2, product_price=40)
    engine.submit(SELLER, PITCH)
    engine.submit(BUYER, BUY)
    seller_final = engine.submit(SELLER, PITCH)   # last seller move of the game
    assert seller_final.valid and seller_final.game_over is False
    assert seller_final.result is None
    assert not engine.done

    buyer_final = engine.submit(BUYER, BUY)
    assert buyer_final.valid and buyer_final.game_over is True
    assert buyer_final.result == {"player_1_payoff": 80, "player_2_payoff": 120,
                                  "outcome": "completed"}
    assert engine.done
    assert engine.observation(SELLER)["phase"] == "completed"


def test_a_valid_move_reports_no_attempt_accounting():
    engine = make_engine()
    move = engine.submit(SELLER, PITCH)
    assert move.valid and move.error is None and move.attempts_left is None


def test_moving_in_a_finished_game_is_rejected_without_burning_an_attempt():
    engine = make_engine(("high",), total_rounds=1)
    play(engine, ["yes"])
    move = engine.submit(SELLER, PITCH)
    assert move.valid is False
    assert "not active" in move.error
    assert move.attempts_left is None             # API-level 400, not an invalid move
    assert engine.result.outcome == "completed"   # unchanged


def test_moving_out_of_turn_is_rejected_and_costs_no_attempt():
    engine = make_engine(("high", "high"), total_rounds=2)
    move = engine.submit(BUYER, BUY)              # seller's turn
    assert move.valid is False
    assert "not your turn" in move.error
    assert move.attempts_left is None
    assert engine.current_player == SELLER
    # The buyer's full budget is intact.
    engine.submit(SELLER, PITCH)
    assert engine.submit(BUYER, {"decision": "maybe"}).attempts_left == 4


def test_five_invalid_moves_force_close_the_game_as_a_no_deal():
    engine = make_engine(("high", "high", "high"), total_rounds=3, product_price=40)
    engine.submit(SELLER, PITCH)
    engine.submit(BUYER, BUY)                     # a profitable round is banked
    assert engine.observation(SELLER)["game_state"]["seller_total_payoff"] == 40

    seen = []
    for _ in range(MAX_INVALID_ATTEMPTS):
        seen.append(engine.submit(SELLER, {"decision": "yes"}).attempts_left)
    assert seen == [4, 3, 2, 1, 0]
    assert engine.done
    # Force-close discards everything already earned.
    assert engine.result.player_1_payoff == 0
    assert engine.result.player_2_payoff == 0
    assert engine.result.outcome == "no_deal"
    assert engine.result.detail["abandoned_by"] == SELLER


def test_the_fifth_rejection_reports_the_no_deal_result():
    engine = make_engine(("high",), total_rounds=1)
    for _ in range(MAX_INVALID_ATTEMPTS - 1):
        engine.submit(SELLER, {})
    final = engine.submit(SELLER, {})
    assert final.valid is False
    assert final.attempts_left == 0
    assert final.game_over is True
    assert final.result == {"player_1_payoff": 0, "player_2_payoff": 0,
                            "outcome": "no_deal"}


def test_a_buyer_can_also_force_close_the_game():
    engine = make_engine(("high",), total_rounds=1)
    engine.submit(SELLER, PITCH)
    for _ in range(MAX_INVALID_ATTEMPTS):
        engine.submit(BUYER, {"decision": "accept"})
    assert engine.done
    assert engine.result.outcome == "no_deal"
    assert engine.result.detail["abandoned_by"] == BUYER


def test_the_attempt_budget_is_per_player():
    engine = make_engine(("high", "high"), total_rounds=2)
    for _ in range(MAX_INVALID_ATTEMPTS - 1):
        engine.submit(SELLER, {})
    assert not engine.done
    engine.submit(SELLER, PITCH)                  # a valid move gets through
    # The buyer starts with its own untouched budget.
    assert engine.submit(BUYER, {}).attempts_left == 4


def test_the_attempt_budget_is_per_game_and_survives_a_valid_move():
    engine = make_engine(("high", "high"), total_rounds=2)
    assert engine.submit(SELLER, {}).attempts_left == 4
    assert engine.submit(SELLER, {}).attempts_left == 3
    engine.submit(SELLER, PITCH)
    engine.submit(BUYER, BUY)
    # Round 2, same game: the counter did not reset.
    assert engine.submit(SELLER, {}).attempts_left == 2


# ------------------------------------------------------------- invalid actions

@pytest.mark.parametrize("action", [
    None, [], "yes", 7, ("message", "hi"),
])
def test_a_non_dict_action_is_invalid(action):
    engine = make_engine()
    move = engine.submit(SELLER, action)
    assert move.valid is False and move.attempts_left == 4


@pytest.mark.parametrize("action", [
    {},                                   # nothing at all
    {"decision": "yes"},                  # the binary shape in a text game
    {"message": None},
    {"message": 42},
    {"message": True},
    {"msg": "typo"},
])
def test_text_mode_seller_action_validation(action):
    engine = make_engine(seller_message_type="text")
    move = engine.submit(SELLER, action)
    assert move.valid is False and move.attempts_left == 4
    assert engine.observation(SELLER)["phase"] == "seller_message"


@pytest.mark.parametrize("message", ["", " ", "   \n ", "\t"])
def test_an_empty_seller_message_is_legal_and_burns_no_attempt(message):
    # Length is the only documented way a message can be invalid, and fair play
    # names silence as legal content. Rejecting it here would train the agent
    # away from a move the server accepts, and would cost it an attempt it
    # would not really lose.
    engine = make_engine(("high", "high"), total_rounds=2)
    move = engine.submit(SELLER, {"message": message})
    assert move.valid is True
    assert move.attempts_left is None             # nothing was burned
    assert engine.observation(BUYER)["phase"] == "buyer_decision"


def test_an_empty_seller_message_is_recorded_verbatim_not_repaired():
    engine = make_engine(("high", "high"), total_rounds=2)
    engine.submit(SELLER, {"message": ""})
    # Present as the empty string, distinguishable from the None that means
    # "the seller has not spoken this round yet".
    assert engine.observation(BUYER)["game_state"]["seller_message"] == ""
    engine.submit(BUYER, BUY)
    assert engine.observation(BUYER)["game_state"]["history"][0]["seller_message"] == ""
    assert engine.observation(SELLER)["game_state"]["seller_message"] is None


def test_silence_plays_out_a_whole_game_without_ending_it_early():
    engine = make_engine(("high", "low", "high"), total_rounds=3)
    result = play(engine, ["yes", "no", "yes"], message="")
    assert result.outcome == "completed"
    assert result.rounds_played == 3
    assert result.player_1_payoff == 80          # two sales at $40


def test_a_message_at_the_limit_is_accepted_and_one_over_is_not():
    engine = make_engine(("high", "high"), total_rounds=2)
    assert engine.submit(SELLER, {"message": "x" * MAX_MESSAGE_LEN}).valid is True
    engine.submit(BUYER, PASS)
    over = engine.submit(SELLER, {"message": "x" * (MAX_MESSAGE_LEN + 1)})
    assert over.valid is False
    assert str(MAX_MESSAGE_LEN) in over.error


@pytest.mark.parametrize("action", [
    {},
    {"message": "great product"},         # the text shape in a binary game
    {"decision": "Yes"},                  # case-sensitive
    {"decision": "YES"},
    {"decision": True},
    {"decision": 1},
    {"decision": "recommend"},
    {"decision": None},
])
def test_binary_mode_seller_action_validation(action):
    engine = make_engine(seller_message_type="binary")
    move = engine.submit(SELLER, action)
    assert move.valid is False and move.attempts_left == 4


@pytest.mark.parametrize("action", [
    {},
    {"message": "I'll take it"},
    {"decision": "accept"},               # bargaining vocabulary
    {"decision": "reject"},
    {"decision": "walkaway"},
    {"decision": "AcceptOffer"},          # negotiation vocabulary
    {"decision": "RejectOffer"},
    {"decision": "WalkAway"},
    {"decision": "buy"},
    {"decision": "Yes"},
    {"decision": True},
    {"decision": 0},
])
def test_buyer_action_validation(action):
    engine = make_engine()
    engine.submit(SELLER, PITCH)
    move = engine.submit(BUYER, action)
    assert move.valid is False and move.attempts_left == 4


@pytest.mark.parametrize("action", [
    {"decision": "yes", "product_price": 60},
    {"alice_gain": 500, "bob_gain": 500},
    {"decision": "yes", "bob_gain": 1},
])
def test_cross_family_keys_are_rejected(action):
    engine = make_engine(seller_message_type="binary")
    move = engine.submit(SELLER, action)
    assert move.valid is False and move.attempts_left == 4


def test_unknown_extra_keys_are_ignored_rather_than_rejected():
    engine = make_engine(("high", "high"), total_rounds=2)
    assert engine.submit(SELLER, {"message": "hi", "confidence": 0.9}).valid is True
    assert engine.submit(BUYER, {"decision": "yes", "reasoning": "cheap"}).valid is True
    assert engine.observation(SELLER)["game_state"]["seller_total_payoff"] == 40


def test_a_rejected_move_does_not_advance_the_game():
    engine = make_engine(("high", "high"), total_rounds=2)
    before = engine.observation(SELLER)["game_state"]
    engine.submit(SELLER, {"decision": "yes"})
    after = engine.observation(SELLER)["game_state"]
    assert engine.current_player == SELLER
    assert after["phase"] == before["phase"] == "seller_message"
    assert after["round"] == before["round"] == 1
    assert after["history"] == [] and after["seller_message"] is None
    assert after["seller_total_payoff"] == 0


def test_rejection_does_not_consume_the_rounds_quality_draw():
    engine = make_engine(("high", "low"), total_rounds=2)
    assert engine.observation(SELLER)["game_state"]["current_quality"] == "high"
    engine.submit(SELLER, {})
    engine.submit(SELLER, {})
    assert engine.observation(SELLER)["game_state"]["current_quality"] == "high"


# ------------------------------------------------------------------ edge cases

def test_single_round_game():
    engine = make_engine(("high",), total_rounds=1, product_price=40)
    obs = engine.observation(BUYER)
    assert obs["game_state"]["total_rounds"] == 1
    move_1 = engine.submit(SELLER, PITCH)
    assert move_1.game_over is False
    move_2 = engine.submit(BUYER, BUY)
    assert move_2.game_over is True
    assert engine.result.player_1_payoff == 40
    assert engine.result.player_2_payoff == 60
    assert engine.result.rounds_played == 1


def test_p_zero_never_draws_a_high_quality_unit():
    engine = make_engine(rng=random.Random(11), p=0.0, total_rounds=8)
    play(engine, ["yes"] * 8)
    qualities = [h["quality"] for h in engine.observation(SELLER)["game_state"]["history"]]
    assert qualities == ["low"] * 8


def test_p_one_always_draws_a_high_quality_unit():
    engine = make_engine(rng=random.Random(11), p=1.0, total_rounds=8)
    play(engine, ["yes"] * 8)
    qualities = [h["quality"] for h in engine.observation(SELLER)["game_state"]["history"]]
    assert qualities == ["high"] * 8


def test_quality_draws_come_from_the_injected_rng_and_replay_identically():
    def qualities(seed):
        engine = make_engine(rng=random.Random(seed), p=0.5, total_rounds=12)
        play(engine, ["no"] * 12)
        state = engine.observation(SELLER)["game_state"]
        return [h["quality"] for h in state["history"]]

    assert qualities(1234) == qualities(1234)
    # A real draw, not a constant: two seeds must not agree by construction.
    assert qualities(1234) != qualities(4321)
    assert set(qualities(1234)) == {"high", "low"}


def test_the_engine_never_touches_the_global_random_module(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("engine used the global random module")

    for name in ("random", "randint", "choice", "uniform", "getrandbits"):
        monkeypatch.setattr(random, name, explode)
    engine = make_engine(("high", "low", "high"), total_rounds=3)
    play(engine, ["yes", "no", "yes"])
    assert engine.done


def test_one_quality_draw_per_round():
    stream = ScriptedRandom([0.0] * 20)
    engine = PersuasionEngine(make_config(total_rounds=6), stream, "g")
    play(engine, ["yes"] * 6)
    assert stream.calls == 6                      # disclose_opponent is pinned


def test_prior_alone_justifies_buying_is_just_a_configuration():
    # p*v + (1-p)*u = 0.9*100 = 90 >= price 50. The mechanics do not change.
    engine = make_engine(("high", "low"), total_rounds=2, p=0.9, product_price=50)
    state = engine.observation(BUYER)["game_state"]
    assert state["p"] * state["v"] + (1 - state["p"]) * state["u"] >= state["product_price"]
    result = play(engine, ["yes", "yes"])
    assert result.player_1_payoff == 100
    assert result.player_2_payoff == 0            # (100-50) + (0-50)


def test_never_rational_to_buy_configuration_still_pays_out_as_specified():
    # v <= price: even a certainly-high unit loses money.
    engine = make_engine(("high", "high"), total_rounds=2, v=30, product_price=40)
    result = play(engine, ["yes", "yes"])
    assert result.player_1_payoff == 80
    assert result.player_2_payoff == -20


def test_float_configurations_are_carried_through_unrounded():
    engine = make_engine(("high", "low"), total_rounds=2, product_price=12.5,
                         v=33.75, u=0.0)
    result = play(engine, ["yes", "yes"])
    assert result.player_1_payoff == pytest.approx(25.0)
    assert result.player_2_payoff == pytest.approx(33.75 - 12.5 - 12.5)


def test_buyer_prompt_tolerates_a_binary_recommendation_and_a_text_pitch():
    binary = make_engine(("high",), total_rounds=1, seller_message_type="binary")
    binary.submit(SELLER, {"decision": "no"})
    assert "does not recommend" in binary.observation(BUYER)["prompt"]

    text = make_engine(("high",), total_rounds=1)
    text.submit(SELLER, {"message": "top shelf"})
    assert "top shelf" in text.observation(BUYER)["prompt"]


def test_engine_is_reachable_through_the_registry():
    try:
        from sim import make_engine as build
    except ImportError as exc:                    # pragma: no cover
        pytest.skip(f"sim registry not importable yet: {exc}")
    try:
        engine = build(make_config(total_rounds=1), random.Random(0), "reg")
    except ImportError as exc:                    # a sibling engine is still being written
        pytest.skip(f"sibling engine missing: {exc}")
    assert isinstance(engine, PersuasionEngine)
    assert engine.game_id == "reg"
