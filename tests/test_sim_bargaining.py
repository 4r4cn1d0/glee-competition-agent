"""Tests for the local bargaining engine.

These are fidelity tests, not behaviour tests: every assertion is about the
engine emitting exactly what the live server emits and rejecting exactly what
the live server rejects. Where the spec rests on an assumption (A1..A24 in
``sim/bargaining.py``), the test names it, so that a future correction to an
assumption shows up here as a failing test rather than as silent drift.
"""

from __future__ import annotations

import random

import pytest

from sim.bargaining import MAX_MESSAGE_LEN, SAFETY_ROUND_CAP, BargainingEngine
from sim.types import MAX_INVALID_ATTEMPTS, PLAYER_1, PLAYER_2, Config

DEFAULTS = {
    "money_to_divide": 1000,
    "delta_1": 0.9,
    "delta_2": 0.8,
    "max_rounds": 5,
    "messages_allowed": True,
    "complete_information": True,
}


def make_config(**overrides) -> Config:
    params = dict(DEFAULTS)
    params.update(overrides)
    return Config("bargaining", params)


def make_engine(seed=7, **overrides) -> BargainingEngine:
    return BargainingEngine(make_config(**overrides), random.Random(seed), "test-game")


def offer(engine, alice, bob, **extra):
    action = {"alice_gain": alice, "bob_gain": bob}
    action.update(extra)
    return engine.submit(engine.current_player, action)


def decide(engine, decision, **extra):
    action = {"decision": decision}
    action.update(extra)
    return engine.submit(engine.current_player, action)


def half(engine):
    """A legal 50/50 split for whoever is proposing."""
    money = engine.money
    return offer(engine, money / 2, money / 2)


# --- observation shape -------------------------------------------------------


def test_observation_has_the_full_api_shape():
    engine = make_engine()
    game = engine.observation(PLAYER_1)
    assert set(game) == {"game_id", "game_family", "your_player", "phase",
                         "opponent", "game_state", "valid_actions", "prompt"}
    assert game["game_id"] == "test-game"
    assert game["game_family"] == "bargaining"
    assert game["your_player"] == PLAYER_1
    assert game["phase"] == "offer"
    assert isinstance(game["valid_actions"]["fields"], dict)
    assert game["prompt"].strip()


def test_top_level_phase_always_matches_game_state_phase():
    engine = make_engine()
    for _ in range(3):
        for player in (PLAYER_1, PLAYER_2):
            game = engine.observation(player)
            assert game["phase"] == game["game_state"]["phase"]
        if engine.observation(PLAYER_1)["phase"] == "offer":
            half(engine)
        else:
            decide(engine, "reject")


def test_initial_state_fields():
    engine = make_engine()
    state = engine.observation(PLAYER_1)["game_state"]
    assert state["phase"] == "offer"
    assert state["current_player"] == PLAYER_1        # A1 — Alice opens
    assert state["proposer"] == PLAYER_1
    assert state["round"] == 1
    assert state["max_rounds"] == 5
    assert state["horizon_known"] is True
    assert state["money_to_divide"] == 1000
    assert state["last_offer"] is None                # A11 — null, not absent
    assert "last_offer" in state
    assert state["history"] == []
    assert state["messages_allowed"] is True
    assert state["complete_information"] is True


def test_game_state_carries_no_payoff_key_during_play():
    # Bargaining settles once, at the end. A running payoff would be invented.
    engine = make_engine()
    half(engine)
    state = engine.observation(PLAYER_2)["game_state"]
    assert not [key for key in state if "payoff" in key]


def test_offer_valid_actions_payload():
    engine = make_engine()
    actions = engine.observation(PLAYER_1)["valid_actions"]
    assert actions["type"] == "offer"
    assert set(actions["fields"]) == {"alice_gain", "bob_gain", "message"}


def test_offer_fields_omit_message_when_messages_are_not_allowed():
    engine = make_engine(messages_allowed=False)
    assert set(engine.observation(PLAYER_1)["valid_actions"]["fields"]) == {
        "alice_gain", "bob_gain"}


def test_decision_valid_actions_payload():
    engine = make_engine()
    half(engine)
    actions = engine.observation(PLAYER_2)["valid_actions"]
    assert actions["type"] == "decision"
    assert set(actions["fields"]) == {"decision"}


def test_observation_of_the_non_moving_player_still_reports_the_real_turn():
    # current_player is derived from the game, never from who is asking.
    engine = make_engine()
    game = engine.observation(PLAYER_2)
    assert game["your_player"] == PLAYER_2
    assert game["game_state"]["current_player"] == PLAYER_1
    assert game["phase"] == "offer"


def test_observation_rejects_an_unknown_player():
    engine = make_engine()
    with pytest.raises(ValueError):
        engine.observation("player_3")


def test_prompt_is_non_empty_on_every_turn_including_after_the_game_ends():
    # A22 — glee_agent/llm.py feeds this straight to the model.
    engine = make_engine(max_rounds=3)
    seen = []
    while not engine.done:
        for player in (PLAYER_1, PLAYER_2):
            seen.append(engine.observation(player)["prompt"])
        if engine.observation(PLAYER_1)["phase"] == "offer":
            half(engine)
        else:
            decide(engine, "reject")
    seen.append(engine.observation(PLAYER_1)["prompt"])
    assert all(text and text.strip() for text in seen)


def test_observation_is_a_copy_that_cannot_corrupt_the_engine():
    engine = make_engine()
    offer(engine, 600, 400)
    state = engine.observation(PLAYER_2)["game_state"]
    state["last_offer"]["player_2_gain"] = 999
    state["history"].append({"bogus": True})
    fresh = engine.observation(PLAYER_2)["game_state"]
    assert fresh["last_offer"]["player_2_gain"] == 400
    assert fresh["history"] == []


# --- turn order --------------------------------------------------------------


def test_offer_moves_to_the_decision_phase_and_flips_current_player():
    engine = make_engine()
    result = offer(engine, 600, 400, message="fair")
    assert result.valid and not result.game_over and result.result is None

    state = engine.observation(PLAYER_2)["game_state"]
    assert state["phase"] == "decision"
    assert state["current_player"] == PLAYER_2       # the receiver
    assert state["proposer"] == PLAYER_1             # still names the offerer
    assert state["round"] == 1
    assert engine.current_player == PLAYER_2


def test_receiver_reads_its_own_share_the_way_the_sdk_example_does():
    engine = make_engine()
    offer(engine, 600, 400)
    state = engine.observation(PLAYER_2)["game_state"]
    assert state["last_offer"][f"{state['current_player']}_gain"] == 400


def test_last_offer_has_exactly_the_documented_keys():
    engine = make_engine()
    offer(engine, 600, 400, message="take it")
    last = engine.observation(PLAYER_1)["game_state"]["last_offer"]
    assert set(last) == {"player_1_gain", "player_2_gain", "message",
                         "proposer", "round"}
    assert last == {"player_1_gain": 600, "player_2_gain": 400,
                    "message": "take it", "proposer": PLAYER_1, "round": 1}


def test_the_rejecter_proposes_next_round():
    engine = make_engine()
    offer(engine, 600, 400)
    decide(engine, "reject")
    state = engine.observation(PLAYER_2)["game_state"]
    assert state["round"] == 2
    assert state["phase"] == "offer"
    assert state["proposer"] == PLAYER_2
    assert state["current_player"] == PLAYER_2


def test_proposer_alternates_by_round_parity():
    # A2 — player_1 on odd rounds, player_2 on even ones.
    engine = make_engine(max_rounds=6)
    seen = []
    for _ in range(6):
        state = engine.observation(PLAYER_1)["game_state"]
        seen.append((state["round"], state["proposer"]))
        half(engine)
        if engine.done:
            break
        decide(engine, "reject")
    assert seen == [(1, PLAYER_1), (2, PLAYER_2), (3, PLAYER_1),
                    (4, PLAYER_2), (5, PLAYER_1), (6, PLAYER_2)]


def test_last_offer_persists_after_a_rejection_tagged_with_its_own_round():
    # A11 — it is the last offer MADE, not the live one.
    engine = make_engine()
    offer(engine, 700, 300, message="mine")
    decide(engine, "reject")
    state = engine.observation(PLAYER_2)["game_state"]
    assert state["phase"] == "offer" and state["round"] == 2
    assert state["last_offer"] == {"player_1_gain": 700, "player_2_gain": 300,
                                   "message": "mine", "proposer": PLAYER_1,
                                   "round": 1}


def test_player_2_proposes_with_alice_bob_keys_from_the_same_fixed_viewpoint():
    engine = make_engine()
    offer(engine, 600, 400)
    decide(engine, "reject")
    assert engine.current_player == PLAYER_2
    assert offer(engine, 250, 750).valid
    last = engine.observation(PLAYER_1)["game_state"]["last_offer"]
    assert last["player_1_gain"] == 250 and last["player_2_gain"] == 750
    assert last["proposer"] == PLAYER_2


# --- history -----------------------------------------------------------------


def test_history_records_completed_rounds_only_in_the_documented_shape():
    engine = make_engine()
    offer(engine, 600, 400, message="hello")
    assert engine.observation(PLAYER_2)["game_state"]["history"] == []
    decide(engine, "reject")
    history = engine.observation(PLAYER_2)["game_state"]["history"]
    assert history == [{
        "round": 1,
        "proposer": PLAYER_1,
        "offer": {"player_1_gain": 600, "player_2_gain": 400, "message": "hello"},
        "decision": "reject",
    }]


def test_history_entry_has_no_payoff_fields():
    # A12 — bargaining has no per-round payoff to report.
    engine = make_engine()
    half(engine)
    decide(engine, "reject")
    entry = engine.observation(PLAYER_1)["game_state"]["history"][0]
    assert set(entry) == {"round", "proposer", "offer", "decision"}
    assert set(entry["offer"]) == {"player_1_gain", "player_2_gain", "message"}


def test_the_round_that_ends_the_game_is_appended_to_history():
    engine = make_engine()
    offer(engine, 600, 400)
    decide(engine, "accept")
    history = engine.observation(PLAYER_1)["game_state"]["history"]
    assert [entry["decision"] for entry in history] == ["accept"]


def test_walkaway_and_final_round_rejection_are_recorded_distinctly():
    walk = make_engine(max_rounds=1)
    half(walk)
    decide(walk, "walkaway")
    reject = make_engine(max_rounds=1)
    half(reject)
    decide(reject, "reject")

    assert walk.result.as_dict() == reject.result.as_dict()      # both (0, 0)
    assert walk.observation(PLAYER_1)["game_state"]["history"][0]["decision"] == "walkaway"
    assert reject.observation(PLAYER_1)["game_state"]["history"][0]["decision"] == "reject"
    assert walk.result.detail["reason"] == "walkaway"
    assert reject.result.detail["reason"] == "max_rounds"


# --- payoffs -----------------------------------------------------------------


def test_round_one_agreement_is_undiscounted():
    # A3 — the exponent is (round - 1), so round 1 pays the nominal gains.
    engine = make_engine()
    offer(engine, 600, 400)
    result = decide(engine, "accept")
    assert result.valid and result.game_over
    assert result.result == {"player_1_payoff": 600, "player_2_payoff": 400,
                             "outcome": "agreement"}
    assert engine.result.rounds_played == 1
    assert engine.result.detail["reason"] == "accept"
    assert engine.done


def test_agreement_in_round_three_is_discounted_by_delta_squared():
    # delta_1 = 0.9, delta_2 = 0.8, agreement on (600, 400) in round 3:
    #   player_1 = 600 * 0.9^2 = 600 * 0.81 = 486.0
    #   player_2 = 400 * 0.8^2 = 400 * 0.64 = 256.0
    engine = make_engine()
    offer(engine, 900, 100)
    decide(engine, "reject")               # round 2, Bob proposes
    offer(engine, 100, 900)
    decide(engine, "reject")               # round 3, Alice proposes
    assert engine.observation(PLAYER_1)["game_state"]["round"] == 3
    offer(engine, 600, 400)
    result = decide(engine, "accept")

    assert result.result["player_1_payoff"] == pytest.approx(486.0, abs=1e-9)
    assert result.result["player_2_payoff"] == pytest.approx(256.0, abs=1e-9)
    assert engine.result.rounds_played == 3
    assert engine.result.payoff(PLAYER_1) == pytest.approx(486.0, abs=1e-9)
    assert engine.result.payoff(PLAYER_2) == pytest.approx(256.0, abs=1e-9)


def test_the_two_players_discount_at_their_own_rates():
    # Round 2 agreement on (500, 500) with delta_1 = 0.5, delta_2 = 1.0:
    #   player_1 = 500 * 0.5 = 250.0, player_2 = 500 * 1.0 = 500.0
    engine = make_engine(delta_1=0.5, delta_2=1.0)
    half(engine)
    decide(engine, "reject")
    offer(engine, 500, 500)
    result = decide(engine, "accept")
    assert result.result["player_1_payoff"] == pytest.approx(250.0, abs=1e-9)
    assert result.result["player_2_payoff"] == pytest.approx(500.0, abs=1e-9)


def test_result_reports_realized_not_nominal_amounts():
    # A4 — the accepted offer's nominal gains stay in detail, out of the wire.
    engine = make_engine(delta_1=0.5, delta_2=0.5)
    half(engine)
    decide(engine, "reject")
    offer(engine, 800, 200)
    result = decide(engine, "accept")
    assert result.result["player_1_payoff"] == pytest.approx(400.0, abs=1e-9)
    assert engine.result.detail["nominal"] == {"player_1_gain": 800,
                                               "player_2_gain": 200}


def test_the_pot_never_shrinks_with_inflation():
    engine = make_engine()
    for _ in range(2):
        half(engine)
        decide(engine, "reject")
    state = engine.observation(PLAYER_1)["game_state"]
    assert state["round"] == 3
    assert state["money_to_divide"] == 1000


def test_heavy_inflation_can_make_a_later_better_split_worth_less():
    # Not a rule, a consequence: the engine must not round or clamp it away.
    early = make_engine(delta_1=0.2, delta_2=0.2)
    offer(early, 400, 600)
    decide(early, "accept")

    late = make_engine(delta_1=0.2, delta_2=0.2)
    half(late)
    decide(late, "reject")
    offer(late, 1000, 0)
    decide(late, "accept")

    assert late.result.payoff(PLAYER_1) == pytest.approx(200.0, abs=1e-9)
    assert early.result.payoff(PLAYER_1) == 400
    assert late.result.payoff(PLAYER_1) < early.result.payoff(PLAYER_1)


# --- termination -------------------------------------------------------------


def test_walkaway_pays_both_players_zero_immediately():
    engine = make_engine()
    half(engine)
    result = decide(engine, "walkaway")
    assert result.valid and result.game_over
    assert result.result == {"player_1_payoff": 0.0, "player_2_payoff": 0.0,
                             "outcome": "no_deal"}
    assert engine.result.detail["reason"] == "walkaway"
    assert engine.result.rounds_played == 1


def test_rejection_in_the_final_round_of_a_capped_game_is_a_no_deal():
    engine = make_engine(max_rounds=2)
    half(engine)
    decide(engine, "reject")
    assert not engine.done
    half(engine)
    result = decide(engine, "reject")
    assert result.game_over
    assert result.result["outcome"] == "no_deal"
    assert result.result["player_1_payoff"] == 0.0
    assert engine.result.rounds_played == 2
    assert engine.result.detail["reason"] == "max_rounds"


def test_ultimatum_never_enters_a_second_offer_phase():
    engine = make_engine(max_rounds=1)
    assert engine.observation(PLAYER_2)["game_state"]["max_rounds"] == 1
    half(engine)
    decide(engine, "reject")
    assert engine.done
    state = engine.observation(PLAYER_1)["game_state"]
    assert state["round"] == 1
    assert state["phase"] == "completed"
    assert len(state["history"]) == 1


def test_ultimatum_acceptance_is_undiscounted():
    engine = make_engine(max_rounds=1, delta_1=0.5, delta_2=0.5)
    offer(engine, 999, 1)
    result = decide(engine, "accept")
    assert result.result == {"player_1_payoff": 999, "player_2_payoff": 1,
                             "outcome": "agreement"}


def test_an_uncapped_game_hides_max_rounds_and_never_reaches_a_final_round():
    # A19 — horizon_known false means there is genuinely no cap.
    engine = make_engine(max_rounds=None)
    state = engine.observation(PLAYER_1)["game_state"]
    assert state["horizon_known"] is False
    assert "max_rounds" not in state
    assert state.get("max_rounds") is None
    with pytest.raises(KeyError):
        state["max_rounds"]

    for _ in range(20):
        half(engine)
        decide(engine, "reject")
        assert not engine.done
    assert engine.observation(PLAYER_1)["game_state"]["round"] == 21


def test_the_safety_cap_closes_a_runaway_game_and_is_never_visible():
    # A20 — two stubborn players with no deadline and no erosion.
    engine = make_engine(max_rounds=None, delta_1=1.0, delta_2=1.0)
    while not engine.done:
        state = engine.observation(engine.current_player)["game_state"]
        assert "max_rounds" not in state
        assert "safety" not in " ".join(state).lower()
        if state["phase"] == "offer":
            half(engine)
        else:
            decide(engine, "reject")
    assert engine.result.outcome == "no_deal"
    assert engine.result.detail["reason"] == "safety_cap"
    assert engine.result.rounds_played == SAFETY_ROUND_CAP
    assert engine.result.player_1_payoff == 0.0


def test_observation_after_termination_reports_completed(caplog):
    # A14 — GET /games/{id} keeps working; there is nothing actionable to do.
    engine = make_engine()
    offer(engine, 600, 400)
    decide(engine, "accept")
    game = engine.observation(PLAYER_2)
    assert game["phase"] == "completed"
    assert game["game_state"]["phase"] == "completed"
    assert game["valid_actions"]["type"] is None
    assert game["valid_actions"]["fields"] == {}
    assert game["result"] == {"player_1_payoff": 600, "player_2_payoff": 400,
                              "outcome": "agreement"}
    assert game["status"] == "completed"
    assert game["prompt"].strip()


def test_a_no_deal_game_reports_status_no_deal():
    engine = make_engine()
    half(engine)
    decide(engine, "walkaway")
    assert engine.observation(PLAYER_1)["status"] == "no_deal"


# --- private information -----------------------------------------------------


def test_incomplete_information_omits_the_opponent_delta_key_entirely():
    engine = make_engine(complete_information=False)
    alice = engine.observation(PLAYER_1)["game_state"]
    bob = engine.observation(PLAYER_2)["game_state"]

    assert alice["delta_1"] == 0.9
    assert "delta_2" not in alice
    with pytest.raises(KeyError):
        alice["delta_2"]

    assert bob["delta_2"] == 0.8
    assert "delta_1" not in bob
    with pytest.raises(KeyError):
        bob["delta_1"]

    # A player always knows that it is missing something.
    assert alice["complete_information"] is False
    assert bob["complete_information"] is False


def test_complete_information_shows_both_deltas_to_both_players():
    engine = make_engine(complete_information=True)
    for player in (PLAYER_1, PLAYER_2):
        state = engine.observation(player)["game_state"]
        assert state["delta_1"] == 0.9
        assert state["delta_2"] == 0.8


def test_everything_except_the_deltas_is_identical_in_both_views():
    engine = make_engine(complete_information=False)
    offer(engine, 700, 300, message="secret to nobody")
    decide(engine, "reject")
    alice = engine.observation(PLAYER_1)["game_state"]
    bob = engine.observation(PLAYER_2)["game_state"]
    shared = {key for key in list(alice) + list(bob)} - {"delta_1", "delta_2"}
    for key in shared:
        assert alice[key] == bob[key], key


def test_a_message_is_delivered_verbatim_to_the_receiver():
    engine = make_engine(complete_information=False)
    offer(engine, 600, 400, message="my delta is 0.99, I can wait forever")
    state = engine.observation(PLAYER_2)["game_state"]
    assert state["last_offer"]["message"] == "my delta is 0.99, I can wait forever"


# --- opponent disclosure -----------------------------------------------------


def test_opponent_is_drawn_once_and_never_changes():
    # A15 — a per-turn redraw would leak what the live server never leaks.
    for seed in range(12):
        engine = make_engine(seed=seed, max_rounds=4)
        first = {p: dict(engine.observation(p)["opponent"]) for p in (PLAYER_1, PLAYER_2)}
        while not engine.done:
            for player in (PLAYER_1, PLAYER_2):
                assert engine.observation(player)["opponent"] == first[player]
            if engine.observation(PLAYER_1)["phase"] == "offer":
                half(engine)
            else:
                decide(engine, "reject")
        for player in (PLAYER_1, PLAYER_2):
            assert engine.observation(player)["opponent"] == first[player]


def test_opponent_is_either_fully_disclosed_or_fully_hidden():
    hidden = disclosed = 0
    for seed in range(60):
        engine = make_engine(seed=seed)
        views = [engine.observation(p)["opponent"] for p in (PLAYER_1, PLAYER_2)]
        types = {view["type"] for view in views}
        if types == {"hidden"}:
            hidden += 1
            assert all(view["name"] is None for view in views)
        else:
            disclosed += 1
            for view in views:
                assert view["type"] in ("agent", "human")
                assert isinstance(view["name"], str) and view["name"]
    assert hidden and disclosed


def test_all_randomness_comes_from_the_injected_rng():
    import sim.bargaining as module

    # Nothing to reach the global generator with: runs must be reproducible
    # from the seed the arena hands in.
    assert not hasattr(module, "random")

    a = BargainingEngine(make_config(), random.Random(99))
    b = BargainingEngine(make_config(), random.Random(99))
    assert a.observation(PLAYER_1)["opponent"] == b.observation(PLAYER_1)["opponent"]
    draws = {tuple(sorted(BargainingEngine(make_config(), random.Random(s))
                          .observation(PLAYER_1)["opponent"].items()))
             for s in range(40)}
    assert len(draws) > 1


# --- invalid moves -----------------------------------------------------------


def rejected(engine, action, player=None):
    player = player or engine.current_player
    result = engine.submit(player, action)
    assert result.valid is False, action
    assert result.error
    return result


def test_offer_requires_both_gains():
    engine = make_engine()
    rejected(engine, {"alice_gain": 600})
    rejected(engine, {"bob_gain": 400})
    rejected(engine, {})


def test_offer_gains_must_be_json_numbers():
    engine = make_engine()
    for bad in ("600", True, None, [600], {"value": 600}):
        rejected(engine, {"alice_gain": bad, "bob_gain": 400})


def test_offer_gains_must_sum_to_the_pot():
    engine = make_engine()
    result = rejected(engine, {"alice_gain": 600, "bob_gain": 300})
    assert "sum" in result.error.lower()
    rejected(engine, {"alice_gain": 600, "bob_gain": 500})


def test_offer_gains_must_be_non_negative():
    # A9 — (1200, -200) sums correctly for a pot of 1000 and is still invalid.
    engine = make_engine()
    rejected(engine, {"alice_gain": 1200, "bob_gain": -200})
    rejected(engine, {"alice_gain": -200, "bob_gain": 1200})


def test_an_offer_of_the_whole_pot_is_legal():
    engine = make_engine()
    assert offer(engine, 1000, 0).valid
    assert engine.observation(PLAYER_2)["game_state"]["last_offer"]["player_2_gain"] == 0


def test_a_receiver_may_reject_the_whole_pot_offer_out_of_spite():
    engine = make_engine(max_rounds=1)
    offer(engine, 1000, 0)
    result = decide(engine, "reject")
    assert result.result == {"player_1_payoff": 0.0, "player_2_payoff": 0.0,
                             "outcome": "no_deal"}


@pytest.mark.parametrize("bad", ["Accept", "ACCEPT", "AcceptOffer", "Reject",
                                 "WalkAway", "yes", "walk away", "", 1, None])
def test_decision_literals_are_case_sensitive(bad):
    # A21 — bargaining is lowercase where negotiation is CamelCase. The engine
    # never repairs case; that is the client's job (glee_agent/actions.py).
    engine = make_engine()
    half(engine)
    rejected(engine, {"decision": bad})
    assert decide(engine, "accept").valid


@pytest.mark.parametrize("good", ["accept", "reject", "walkaway"])
def test_the_three_lowercase_decisions_are_accepted(good):
    engine = make_engine()
    half(engine)
    assert decide(engine, good).valid


def test_decision_key_is_required():
    engine = make_engine()
    half(engine)
    rejected(engine, {})
    rejected(engine, {"message": "I accept"})


def test_a_decision_in_the_offer_phase_is_invalid():
    engine = make_engine()
    result = rejected(engine, {"decision": "accept"})
    assert "offer" in result.error
    assert engine.observation(PLAYER_1)["game_state"]["phase"] == "offer"


def test_the_proposer_cannot_walk_away_from_its_own_turn():
    engine = make_engine()
    rejected(engine, {"decision": "walkaway"})
    assert not engine.done
    assert engine.observation(PLAYER_1)["game_state"]["phase"] == "offer"


def test_an_offer_in_the_decision_phase_is_invalid():
    engine = make_engine()
    half(engine)
    result = rejected(engine, {"alice_gain": 400, "bob_gain": 600})
    assert "decision" in result.error
    assert engine.observation(PLAYER_2)["game_state"]["phase"] == "decision"


def test_non_dict_actions_are_invalid():
    engine = make_engine()
    for bad in (None, "accept", 5, ["alice_gain", 500]):
        rejected(engine, bad)


def test_an_over_long_message_is_an_invalid_move_that_costs_an_attempt():
    engine = make_engine()
    result = engine.submit(PLAYER_1, {"alice_gain": 600, "bob_gain": 400,
                                      "message": "x" * (MAX_MESSAGE_LEN + 1)})
    assert result.valid is False
    assert result.attempts_left == MAX_INVALID_ATTEMPTS - 1
    assert engine.observation(PLAYER_1)["game_state"]["last_offer"] is None
    assert offer(engine, 600, 400, message="x" * MAX_MESSAGE_LEN).valid


def test_an_invalid_move_advances_nothing():
    engine = make_engine()
    before = engine.observation(PLAYER_1)["game_state"]
    rejected(engine, {"alice_gain": 600, "bob_gain": 300})
    assert engine.observation(PLAYER_1)["game_state"] == before
    assert engine.current_player == PLAYER_1
    assert not engine.done


def test_attempts_left_counts_down_and_the_fifth_closes_the_game():
    engine = make_engine()
    seen = []
    for _ in range(MAX_INVALID_ATTEMPTS):
        result = engine.submit(PLAYER_1, {"alice_gain": 1, "bob_gain": 1})
        seen.append(result.attempts_left)
    assert seen == [4, 3, 2, 1, 0]

    assert engine.done
    assert result.valid is False
    assert result.game_over is True
    assert result.result == {"player_1_payoff": 0.0, "player_2_payoff": 0.0,
                             "outcome": "no_deal"}
    assert engine.result.outcome == "no_deal"
    assert engine.result.detail["reason"] == "invalid_attempts"
    assert engine.result.detail["offender"] == PLAYER_1
    assert engine.result.detail["invalid_attempts"] == {PLAYER_1: 5, PLAYER_2: 0}


def test_a_valid_move_does_not_refund_an_attempt():
    # A6 — "5 attempts per GAME": the budget is cumulative, so the move that
    # follows four burned attempts leaves one, not five.
    engine = make_engine()
    for _ in range(MAX_INVALID_ATTEMPTS - 1):
        engine.submit(PLAYER_1, {"alice_gain": 1, "bob_gain": 1})
    assert offer(engine, 600, 400).valid
    assert decide(engine, "reject").valid
    assert engine.current_player == PLAYER_2
    assert half(engine).valid
    # player_1 is the receiver again, and is down to its last attempt.
    result = engine.submit(PLAYER_1, {"decision": "nope"})
    assert result.attempts_left == 0
    assert result.game_over is True
    assert engine.result.detail["reason"] == "invalid_attempts"


def test_cumulative_invalid_moves_close_the_game_across_rounds():
    # A6 — one malformed action before every valid one. Under a per-move budget
    # this runs forever; under the documented per-game budget player_1 abandons
    # the game on its fifth invalid move, which live scores at the 5th
    # percentile. Catching that locally is the whole point of the simulator.
    engine = make_engine(max_rounds=None, horizon_known=False)
    seen = []
    for _ in range(4 * MAX_INVALID_ATTEMPTS):
        if engine.done:
            break
        player = engine.current_player
        if player == PLAYER_1:
            seen.append(engine.submit(player, {"nonsense": True}).attempts_left)
            if engine.done:
                break
        if engine.observation(player)["phase"] == "offer":
            assert half(engine).valid
        else:
            assert decide(engine, "reject").valid

    assert seen == [4, 3, 2, 1, 0]
    assert engine.done
    assert engine.result.outcome == "no_deal"
    assert engine.result.detail["reason"] == "invalid_attempts"
    assert engine.result.detail["offender"] == PLAYER_1
    assert engine.result.detail["invalid_attempts"] == {PLAYER_1: 5, PLAYER_2: 0}
    # It really did survive several complete rounds before dying.
    assert engine.result.rounds_played == MAX_INVALID_ATTEMPTS


def test_each_player_has_its_own_cumulative_budget():
    engine = make_engine()
    for _ in range(2):
        engine.submit(PLAYER_1, {"alice_gain": 1, "bob_gain": 1})
    assert half(engine).valid
    # player_2 starts fresh: player_1's two burned attempts are not its problem.
    assert engine.submit(PLAYER_2, {"decision": "maybe"}).attempts_left == 4
    assert decide(engine, "reject").valid
    # ...but player_2's own count carries across the round boundary.
    assert engine.submit(PLAYER_2, {"alice_gain": 1, "bob_gain": 1}).attempts_left == 3
    assert half(engine).valid
    # ...and so does player_1's: it resumes at 2 left, not at a fresh 5.
    assert engine.submit(PLAYER_1, {"decision": "nope"}).attempts_left == 2


# --- ignored rather than rejected --------------------------------------------


def test_unknown_extra_keys_are_ignored():
    # A7 — rejecting them would make this stricter than the server. The repo's
    # own bargaining strategy attaches a "_plan" key to every action.
    engine = make_engine()
    result = engine.submit(PLAYER_1, {"alice_gain": 600, "bob_gain": 400,
                                      "player_1_gain": 1, "player_2_gain": 2,
                                      "_plan": {"aspiration": 600}})
    assert result.valid
    last = engine.observation(PLAYER_2)["game_state"]["last_offer"]
    assert last["player_1_gain"] == 600 and last["player_2_gain"] == 400
    assert engine.submit(PLAYER_2, {"decision": "accept", "_plan": {}}).valid


def test_player_n_gain_keys_alone_are_not_enough():
    engine = make_engine()
    rejected(engine, {"player_1_gain": 600, "player_2_gain": 400})


def test_a_message_is_stripped_when_messages_are_not_allowed():
    # A8 — ignored, not rejected, including an over-long one.
    engine = make_engine(messages_allowed=False)
    assert offer(engine, 600, 400, message="x" * (MAX_MESSAGE_LEN + 1)).valid
    assert engine.observation(PLAYER_2)["game_state"]["last_offer"]["message"] is None


def test_a_message_on_a_decision_is_stripped():
    engine = make_engine()
    offer(engine, 600, 400)
    assert decide(engine, "reject", message="no thanks").valid
    assert engine.observation(PLAYER_1)["game_state"]["history"][0]["offer"]["message"] is None


def test_a_non_string_message_is_dropped_rather_than_rejected():
    engine = make_engine()
    assert offer(engine, 600, 400, message=42).valid
    assert engine.observation(PLAYER_2)["game_state"]["last_offer"]["message"] is None


def test_an_absent_or_null_message_becomes_null():
    engine = make_engine()
    assert offer(engine, 600, 400, message=None).valid
    assert engine.observation(PLAYER_2)["game_state"]["last_offer"]["message"] is None


# --- transport-level failures ------------------------------------------------


def test_moving_out_of_turn_is_not_an_invalid_move():
    # A23 — live this is HTTP 400, not {"valid": false}: no attempt is consumed.
    engine = make_engine()
    result = engine.submit(PLAYER_2, {"alice_gain": 500, "bob_gain": 500})
    assert result.valid is False
    assert result.attempts_left is None
    assert engine.observation(PLAYER_1)["game_state"]["last_offer"] is None
    # The real budget is untouched.
    assert engine.submit(PLAYER_1, {"alice_gain": 1, "bob_gain": 1}).attempts_left == 4


def test_submitting_to_a_finished_game_is_not_an_invalid_move():
    engine = make_engine()
    offer(engine, 600, 400)
    decide(engine, "accept")
    result = engine.submit(PLAYER_2, {"decision": "reject"})
    assert result.valid is False
    assert result.attempts_left is None
    assert engine.result.outcome == "agreement"
    assert engine.result.payoff(PLAYER_1) == 600


def test_an_unknown_player_is_not_an_invalid_move():
    engine = make_engine()
    result = engine.submit("player_3", {"alice_gain": 500, "bob_gain": 500})
    assert result.valid is False
    assert result.attempts_left is None


# --- configuration edge cases ------------------------------------------------


def test_a_non_integer_pot_still_requires_an_exact_sum():
    engine = make_engine(money_to_divide=33.33)
    mine = 11.11
    assert offer(engine, mine, 33.33 - mine).valid
    result = decide(engine, "accept")
    assert result.result["player_1_payoff"] == pytest.approx(11.11, abs=1e-9)
    assert result.result["player_2_payoff"] == pytest.approx(22.22, abs=1e-9)


def test_the_sum_check_tolerates_float_noise_but_not_a_real_gap():
    # A10 — a small absolute tolerance, not a licence to be sloppy.
    engine = make_engine()
    assert engine.submit(PLAYER_1, {"alice_gain": 600, "bob_gain": 400.0000001}).valid
    engine = make_engine()
    assert engine.submit(PLAYER_1, {"alice_gain": 600, "bob_gain": 400.01}).valid is False


def test_delta_of_one_means_no_erosion_at_all():
    engine = make_engine(delta_1=1.0, delta_2=1.0, max_rounds=4)
    half(engine)
    decide(engine, "reject")
    offer(engine, 300, 700)
    result = decide(engine, "accept")
    assert result.result["player_1_payoff"] == 300
    assert result.result["player_2_payoff"] == 700


def test_asymmetric_deltas_make_the_last_word_worth_the_whole_pot():
    # Parity, not concession pattern: with max_rounds = 2 Bob proposes last and
    # a final-round refusal pays Alice nothing, so an off-by-one in the round
    # bookkeeping would flip who holds it.
    engine = make_engine(max_rounds=2, delta_1=0.5, delta_2=0.95)
    half(engine)
    decide(engine, "reject")
    state = engine.observation(PLAYER_2)["game_state"]
    assert state["round"] == 2 and state["proposer"] == PLAYER_2
    offer(engine, 0, 1000)
    result = decide(engine, "accept")
    assert result.result["player_1_payoff"] == 0
    assert result.result["player_2_payoff"] == pytest.approx(950.0, abs=1e-9)


@pytest.mark.parametrize("params", [
    {"money_to_divide": 0},
    {"money_to_divide": -5},
    {"delta_1": 0.0},
    {"delta_2": 1.5},
    {"max_rounds": 0},
    {"max_rounds": None, "horizon_known": True},
    {"max_rounds": 3, "horizon_known": False},
])
def test_an_impossible_configuration_is_refused_at_construction(params):
    with pytest.raises(ValueError):
        BargainingEngine(make_config(**params), random.Random(1))


def test_horizon_known_may_be_stated_explicitly_when_it_agrees():
    engine = make_engine(max_rounds=None, horizon_known=False)
    assert engine.observation(PLAYER_1)["game_state"]["horizon_known"] is False
    engine = make_engine(max_rounds=3, horizon_known=True)
    assert engine.observation(PLAYER_1)["game_state"]["max_rounds"] == 3


# --- registry ----------------------------------------------------------------


def test_the_registry_builds_this_engine_for_a_bargaining_config():
    pytest.importorskip("sim.negotiation")
    pytest.importorskip("sim.persuasion")
    from sim import make_engine as build

    engine = build(make_config(), random.Random(0), "reg")
    assert isinstance(engine, BargainingEngine)
    assert engine.game_family == "bargaining"


def test_the_repos_own_strategy_plays_a_whole_game_through_the_engine():
    # The point of the simulator: a strategy written for the live wire runs
    # against it unmodified, "_plan" key and all.
    pytest.importorskip("glee_agent.strategies.bargaining")
    from glee_agent.config import Config as AgentConfig
    from glee_agent.strategies.bargaining import decide as strategy

    cfg = AgentConfig()
    for seed in range(6):
        for max_rounds in (1, 2, 5, None):
            for complete in (True, False):
                engine = make_engine(seed=seed, max_rounds=max_rounds,
                                     complete_information=complete)
                while not engine.done:
                    player = engine.current_player
                    action = strategy(engine.observation(player), cfg)
                    result = engine.submit(player, action)
                    assert result.valid, (result.error, action)
                assert engine.result is not None
