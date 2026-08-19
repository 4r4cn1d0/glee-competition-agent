"""Tests for the match runner and percentile scoring.

The engines are stubs on purpose. What is under test here is the runner's
contract with a strategy — that nothing a strategy does escapes as an exception,
that attempts burn and then force-close the game — and the arithmetic of
percentile scoring, which has to be exactly right or every tuning decision made
against it is noise.

Runs under pytest; also runnable directly (``.venv/bin/python
tests/test_sim_arena.py``) so it needs no fixtures and no pytest API.
"""

from __future__ import annotations

import contextlib
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sim  # noqa: E402
from sim.arena import (  # noqa: E402
    ABANDONMENT_PERCENTILE,
    MAX_TURNS_PER_GAME,
    MatchRecord,
    game_rating,
    percentile_scores,
    play,
    run_matches,
)
from sim.types import (  # noqa: E402
    MAX_INVALID_ATTEMPTS,
    PLAYER_1,
    PLAYER_2,
    Config,
    GameResult,
    MoveResult,
)

CONFIG = Config("bargaining", {"money_to_divide": 100})
OTHER_CONFIG = Config("bargaining", {"money_to_divide": 500})

ENGINE_DRAWS = []


class SplitEngine:
    """Player 1 proposes a split of the pot, player 2 accepts or rejects.

    Just enough of a real engine to exercise the runner: it validates actions,
    counts attempts per game, and force-closes as a no-deal when they run out.
    """

    game_family = "bargaining"

    def __init__(self, config, rng, game_id="local"):
        self.config = config
        self.game_id = game_id
        self.pot = config.params["money_to_divide"]
        self.phase = "offer"
        self.offer = None
        self.attempts = {PLAYER_1: MAX_INVALID_ATTEMPTS, PLAYER_2: MAX_INVALID_ATTEMPTS}
        self._result = None
        ENGINE_DRAWS.append((game_id, rng.random()))

    @property
    def done(self):
        return self._result is not None

    @property
    def current_player(self):
        return PLAYER_1 if self.phase == "offer" else PLAYER_2

    @property
    def result(self):
        return self._result

    def observation(self, player):
        return {
            "game_id": self.game_id,
            "game_family": self.game_family,
            "your_player": player,
            "phase": self.phase,
            "opponent": {"type": "hidden", "name": None},
            "game_state": {"money_to_divide": self.pot, "round": 1,
                           "current_player": self.current_player,
                           "last_offer": self.offer, "history": []},
            "valid_actions": {"type": self.phase, "fields": {}},
            "prompt": "split the pot",
        }

    def submit(self, player, action):
        if player != self.current_player:
            return self._reject(player, "not your turn")
        if self.phase == "offer":
            first, second = action.get("alice_gain"), action.get("bob_gain")
            if not _is_number(first) or not _is_number(second):
                return self._reject(player, "gains must be numbers")
            if first < 0 or second < 0 or first + second != self.pot:
                return self._reject(player, f"gains must sum to {self.pot}")
            self.offer = {"player_1_gain": float(first), "player_2_gain": float(second)}
            self.phase = "decision"
            return MoveResult(valid=True)
        decision = action.get("decision")
        if decision not in {"accept", "reject", "walkaway"}:
            return self._reject(player, "bad decision")
        if decision == "accept":
            self._result = GameResult(self.offer["player_1_gain"],
                                      self.offer["player_2_gain"],
                                      "agreement", rounds_played=1)
        else:
            self._result = GameResult(0.0, 0.0, "no_deal", rounds_played=1)
        return MoveResult(valid=True, game_over=True, result=self._result.as_dict())

    def _reject(self, player, error):
        self.attempts[player] -= 1
        if self.attempts[player] <= 0:
            self._result = GameResult(0.0, 0.0, "no_deal", rounds_played=0,
                                      detail={"reason": "attempts_exhausted"})
            return MoveResult(valid=False, game_over=True, error=error,
                              attempts_left=0, result=self._result.as_dict())
        return MoveResult(valid=False, error=error, attempts_left=self.attempts[player])


class NeverEndingEngine:
    """Accepts every move and never finishes — the runner must still stop."""

    game_family = "bargaining"

    def __init__(self, config, rng, game_id="local"):
        self.game_id = game_id
        self.turns = 0

    done = False
    result = None
    current_player = PLAYER_1

    def observation(self, player):
        return {"game_id": self.game_id, "game_family": self.game_family,
                "your_player": player, "phase": "offer",
                "opponent": {"type": "hidden", "name": None},
                "game_state": {"round": 7}, "valid_actions": {"type": "offer", "fields": {}},
                "prompt": ""}

    def submit(self, player, action):
        self.turns += 1
        return MoveResult(valid=True)


class ExplodingEngine(SplitEngine):
    """Raises on any action it does not like, instead of reporting it."""

    def submit(self, player, action):
        if "alice_gain" not in action and "decision" not in action:
            raise TypeError("unexpected action shape")
        return super().submit(player, action)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@contextlib.contextmanager
def patched(**attrs):
    """Swap module-level hooks on ``sim``; ``play`` resolves them at call time."""
    saved = {name: getattr(sim, name) for name in attrs}
    for name, value in attrs.items():
        setattr(sim, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(sim, name, value)


def engine_factory(cls):
    def make(config, rng, game_id="local"):
        return cls(config, rng, game_id)
    return make


def fair_offer(game):
    pot = game["game_state"]["money_to_divide"]
    return {"alice_gain": pot / 2, "bob_gain": pot / 2}


def accept(game):
    return {"decision": "accept"}


def reject(game):
    return {"decision": "reject"}


def p1_strategy(game):
    return fair_offer(game) if game["phase"] == "offer" else accept(game)


def greedy(game):
    pot = game["game_state"]["money_to_divide"]
    if game["phase"] == "offer":
        return {"alice_gain": pot * 0.9, "bob_gain": pot * 0.1}
    return accept(game)


def picky(game):
    """Proposes an even split, and rejects anything short of 60% of the pot."""
    state = game["game_state"]
    pot = state["money_to_divide"]
    if game["phase"] == "offer":
        return {"alice_gain": pot / 2, "bob_gain": pot / 2}
    mine = state["last_offer"][f"{game['your_player']}_gain"]
    return accept(game) if mine >= 0.6 * pot else reject(game)


def boom(game):
    raise RuntimeError("strategy is broken")


def record(payoff, name="s", role=PLAYER_1, config=CONFIG, outcome="agreement",
           **kwargs):
    return MatchRecord(config=config, game_family=config.game_family, role=role,
                       payoff=payoff, opponent_payoff=0.0, outcome=outcome,
                       rounds_played=1, opponent_name="foe", name=name, **kwargs)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol


# --- play --------------------------------------------------------------------


def test_play_reaches_agreement():
    with patched(make_engine=engine_factory(SplitEngine)):
        result = play(CONFIG, p1_strategy, p1_strategy, random.Random(1))
    assert result.outcome == "agreement"
    assert result.player_1_payoff == 50 and result.player_2_payoff == 50
    assert result.detail["arena"]["moves"] == {PLAYER_1: 1, PLAYER_2: 1}
    assert result.detail["arena"]["abandoned_by"] is None


def test_play_rejection_is_a_no_deal():
    with patched(make_engine=engine_factory(SplitEngine)):
        result = play(CONFIG, p1_strategy, reject, random.Random(1))
    assert result.outcome == "no_deal"
    assert result.player_1_payoff == 0 and result.player_2_payoff == 0
    # A legal rejection is not abandonment: it must not be scored as one.
    assert result.detail["arena"]["abandoned_by"] is None
    assert result.detail["arena"]["invalid"] == {PLAYER_1: 0, PLAYER_2: 0}


def test_raising_strategy_does_not_crash_the_run():
    with patched(make_engine=engine_factory(SplitEngine)):
        result = play(CONFIG, boom, accept, random.Random(1))
    assert result.outcome == "no_deal"
    assert result.player_1_payoff == 0 and result.player_2_payoff == 0
    arena = result.detail["arena"]
    assert arena["abandoned_by"] == PLAYER_1
    assert arena["invalid"][PLAYER_1] == MAX_INVALID_ATTEMPTS
    assert arena["moves"][PLAYER_1] == 0
    assert any("RuntimeError" in message for message in arena["errors"])


def test_non_dict_action_is_treated_as_an_invalid_move():
    def returns_none(game):
        return None

    with patched(make_engine=engine_factory(SplitEngine)):
        result = play(CONFIG, returns_none, accept, random.Random(1))
    assert result.outcome == "no_deal"
    assert result.detail["arena"]["abandoned_by"] == PLAYER_1
    assert any("not a dict" in message for message in result.detail["arena"]["errors"])


def test_illegal_action_burns_attempts_then_force_closes():
    def bad_sum(game):
        return {"alice_gain": 1, "bob_gain": 1}   # never sums to the pot

    with patched(make_engine=engine_factory(SplitEngine)):
        result = play(CONFIG, bad_sum, accept, random.Random(1))
    assert result.outcome == "no_deal"
    assert result.detail["arena"]["invalid"][PLAYER_1] == MAX_INVALID_ATTEMPTS
    assert result.detail["arena"]["abandoned_by"] == PLAYER_1


def test_second_player_can_abandon_too():
    def bad_decision(game):
        return {"decision": "maybe"}

    with patched(make_engine=engine_factory(SplitEngine)):
        result = play(CONFIG, fair_offer, bad_decision, random.Random(1))
    arena = result.detail["arena"]
    assert arena["abandoned_by"] == PLAYER_2
    assert arena["moves"][PLAYER_1] == 1     # player 1 did make a legal move
    assert arena["invalid"][PLAYER_2] == MAX_INVALID_ATTEMPTS


def test_engine_raising_on_a_garbage_action_does_not_crash():
    with patched(make_engine=engine_factory(ExplodingEngine)):
        result = play(CONFIG, boom, accept, random.Random(1))
    assert result.outcome == "no_deal"
    assert result.detail["arena"]["abandoned_by"] == PLAYER_1
    assert any("engine raised" in message for message in result.detail["arena"]["errors"])


def test_engine_that_never_ends_is_force_closed():
    with patched(make_engine=engine_factory(NeverEndingEngine)):
        result = play(CONFIG, fair_offer, fair_offer, random.Random(1))
    assert result.outcome == "no_deal"
    assert result.detail["arena"]["forced"] == "turn_cap"
    assert result.detail["arena"]["turns"] == MAX_TURNS_PER_GAME
    assert result.rounds_played == 7      # read back off the engine's state


# --- run_matches -------------------------------------------------------------


def configs_from(*configs):
    """A sample_config stand-in that cycles a fixed list."""
    sequence = list(configs)
    drawn = {"n": 0}

    def sample(game_family, rng):
        rng.random()                       # consume, as a real sampler would
        config = sequence[drawn["n"] % len(sequence)]
        drawn["n"] += 1
        return config

    return sample


def test_run_matches_plays_both_seats():
    with patched(make_engine=engine_factory(SplitEngine),
                 sample_config=configs_from(CONFIG, OTHER_CONFIG)):
        records = run_matches("bargaining", greedy, p1_strategy, n=2, seed=5)

    assert len(records) == 4
    assert [r.role for r in records] == [PLAYER_1, PLAYER_2, PLAYER_1, PLAYER_2]
    # Each config is played from both seats, so the pair shares a config.
    assert records[0].config is records[1].config
    assert records[2].config is records[3].config
    assert all(r.name == "greedy" for r in records)
    assert all(r.opponent_name == "p1_strategy" for r in records)

    # Seat 1: greedy proposes 90/10 and the opponent accepts. Seat 2: the
    # opponent now proposes, 50/50, and greedy accepts. Payoffs are always
    # reported from the record's own seat.
    assert close(records[0].payoff, 90) and close(records[0].opponent_payoff, 10)
    assert close(records[1].payoff, 50) and close(records[1].opponent_payoff, 50)


def test_run_matches_without_swap_plays_one_seat():
    with patched(make_engine=engine_factory(SplitEngine),
                 sample_config=configs_from(CONFIG)):
        records = run_matches("bargaining", greedy, p1_strategy, n=3, seed=5,
                              swap_roles=False)
    assert len(records) == 3
    assert all(r.role == PLAYER_1 for r in records)


def test_run_matches_is_deterministic_in_its_seed():
    def run(seed):
        with patched(make_engine=engine_factory(SplitEngine),
                     sample_config=configs_from(CONFIG, OTHER_CONFIG)):
            return run_matches("bargaining", greedy, p1_strategy, n=3, seed=seed)

    first, second = run(11), run(11)
    assert [r.payoff for r in first] == [r.payoff for r in second]
    assert [r.config.key for r in first] == [r.config.key for r in second]


def test_swapped_pair_shares_one_engine_seed():
    """Common random numbers: the two seats differ only by who sat where."""
    del ENGINE_DRAWS[:]
    with patched(make_engine=engine_factory(SplitEngine),
                 sample_config=configs_from(CONFIG, OTHER_CONFIG)):
        run_matches("bargaining", greedy, p1_strategy, n=2, seed=3)
    draws = [value for _, value in ENGINE_DRAWS]
    assert len(draws) == 4
    assert draws[0] == draws[1]           # pair 0, both seats
    assert draws[2] == draws[3]           # pair 1, both seats
    assert draws[0] != draws[2]           # different pairs are independent


def test_names_can_be_overridden():
    with patched(make_engine=engine_factory(SplitEngine),
                 sample_config=configs_from(CONFIG)):
        records = run_matches("bargaining", greedy, p1_strategy, n=1, seed=5,
                              name="candidate", opponent_name="baseline")
    assert records[0].name == "candidate"
    assert records[0].opponent_name == "baseline"


def test_run_matches_survives_a_broken_strategy_end_to_end():
    with patched(make_engine=engine_factory(SplitEngine),
                 sample_config=configs_from(CONFIG)):
        records = run_matches("bargaining", boom, p1_strategy, n=2, seed=5)
    assert len(records) == 4
    assert all(r.outcome == "no_deal" for r in records)
    assert all(r.abandoned for r in records)
    assert all(r.invalid_actions == MAX_INVALID_ATTEMPTS for r in records)
    # Scoring the wreckage must not raise either.
    scores = percentile_scores(records)
    assert scores["n_dropped"] == 4       # never made a legal move: dropped
    assert scores["mean_game_rating"] is None


# --- percentile scoring ------------------------------------------------------


def test_percentiles_and_ratings_are_hand_checkable():
    records = [record(10, "a"), record(20, "b"), record(30, "c"), record(40, "d")]
    scores = percentile_scores(records)

    by_name = {e["name"]: e for e in scores["scored"]}
    # midrank: (below + 0.5 * equal) / n -> 0.5/4, 1.5/4, 2.5/4, 3.5/4
    assert close(by_name["a"]["percentile"], 0.125)
    assert close(by_name["b"]["percentile"], 0.375)
    assert close(by_name["c"]["percentile"], 0.625)
    assert close(by_name["d"]["percentile"], 0.875)
    # 2000 + 8000 * (p - 0.5)
    assert close(by_name["a"]["game_rating"], -1000.0)
    assert close(by_name["b"]["game_rating"], 1000.0)
    assert close(by_name["c"]["game_rating"], 3000.0)
    assert close(by_name["d"]["game_rating"], 5000.0)
    # A balanced field averages exactly the centre of the scale.
    assert close(scores["mean_game_rating"], 2000.0)
    assert close(scores["mean_percentile"], 0.5)
    assert scores["n_scored"] == 4 and scores["n_unscored"] == 0
    assert scores["n_groups"] == 1 and scores["n_groups_scored"] == 1


def test_ties_take_the_midrank():
    records = [record(10, "a"), record(10, "b"), record(20, "c"), record(20, "d")]
    scores = percentile_scores(records)
    by_name = {e["name"]: e for e in scores["scored"]}
    # two tied at the bottom: (0 + 0.5 * 2) / 4
    assert close(by_name["a"]["percentile"], 0.25)
    assert close(by_name["b"]["percentile"], 0.25)
    assert close(by_name["c"]["percentile"], 0.75)
    assert close(by_name["d"]["percentile"], 0.75)
    assert close(by_name["a"]["game_rating"], 0.0)
    assert close(by_name["c"]["game_rating"], 4000.0)
    assert close(scores["mean_game_rating"], 2000.0)


def test_a_whole_group_tied_sits_at_the_centre():
    records = [record(7, name) for name in "abc"]
    scores = percentile_scores(records)
    assert all(close(e["percentile"], 0.5) for e in scores["scored"])
    assert close(scores["mean_game_rating"], 2000.0)


def test_groups_too_small_are_unscored_not_invented():
    scores = percentile_scores([record(10, "a")])
    assert scores["n_scored"] == 0
    assert scores["n_unscored"] == 1
    assert scores["mean_game_rating"] is None
    assert scores["unscored"][0]["status"] == "group_too_small"
    assert scores["unscored"][0]["percentile"] is None
    assert scores["n_groups_scored"] == 0


def test_min_group_is_adjustable():
    records = [record(10, "a"), record(20, "b")]
    assert percentile_scores(records, min_group=3)["n_scored"] == 0
    assert percentile_scores(records, min_group=2)["n_scored"] == 2


def test_roles_and_configs_are_scored_separately():
    records = [
        record(10, "a", role=PLAYER_1), record(20, "b", role=PLAYER_1),
        record(99, "c", role=PLAYER_2), record(98, "d", role=PLAYER_2),
        record(50, "e", config=OTHER_CONFIG), record(60, "f", config=OTHER_CONFIG),
    ]
    scores = percentile_scores(records)
    assert scores["n_groups"] == 3
    by_name = {e["name"]: e for e in scores["scored"]}
    # 99 is the top of its own group, not of the pool.
    assert close(by_name["c"]["percentile"], 0.75)
    assert close(by_name["a"]["percentile"], 0.25)
    assert close(by_name["e"]["percentile"], 0.25)


def test_abandonment_scores_at_the_fifth_percentile():
    records = [record(10, "a"), record(20, "b"),
               record(0.0, "crash", moves_made=2, abandoned=True, outcome="no_deal")]
    scores = percentile_scores(records)
    by_name = {e["name"]: e for e in scores["scored"]}
    assert close(by_name["crash"]["percentile"], ABANDONMENT_PERCENTILE)
    assert close(by_name["crash"]["game_rating"], -1600.0)
    assert by_name["crash"]["status"] == "abandoned"
    # The wreck stays out of the pool the honest games are ranked against.
    assert close(by_name["a"]["percentile"], 0.25)
    assert scores["groups"][by_name["a"]["group"]]["size"] == 2


def test_the_abandoners_opponent_is_voided():
    records = [record(10, "a"), record(20, "b"),
               record(0.0, "victim", moves_made=3, opponent_abandoned=True)]
    scores = percentile_scores(records)
    assert scores["n_voided"] == 1
    assert scores["voided"][0]["name"] == "victim"
    assert scores["voided"][0]["percentile"] is None
    assert all(e["name"] != "victim" for e in scores["scored"])


def test_abandoning_without_ever_moving_is_dropped():
    records = [record(10, "a"), record(20, "b"),
               record(0.0, "crash", moves_made=0, abandoned=True)]
    scores = percentile_scores(records)
    assert scores["n_dropped"] == 1
    assert scores["dropped"][0]["status"] == "never_moved"
    assert scores["n_scored"] == 2
    assert close(scores["mean_game_rating"], 2000.0)


def test_breakdowns_separate_the_strategies_being_compared():
    records = [record(30, "candidate"), record(10, "baseline"),
               record(40, "candidate", config=OTHER_CONFIG),
               record(20, "baseline", config=OTHER_CONFIG)]
    scores = percentile_scores(records)
    assert close(scores["by_name"]["candidate"]["mean_game_rating"], 4000.0)
    assert close(scores["by_name"]["baseline"]["mean_game_rating"], 0.0)
    assert scores["by_name"]["candidate"]["n_scored"] == 2
    assert scores["by_family"]["bargaining"]["n_scored"] == 4
    assert scores["by_role"][PLAYER_1]["n_scored"] == 4


def test_unscored_records_still_appear_in_breakdowns():
    scores = percentile_scores([record(10, "lonely")])
    assert scores["by_name"]["lonely"]["n_scored"] == 0
    assert scores["by_name"]["lonely"]["n_unscored"] == 1
    assert scores["by_name"]["lonely"]["mean_game_rating"] is None


def test_empty_pool_scores_nothing():
    scores = percentile_scores([])
    assert scores["n_records"] == 0
    assert scores["mean_game_rating"] is None
    assert scores["by_name"] == {}


def test_game_rating_map():
    assert close(game_rating(0.5), 2000.0)
    assert close(game_rating(1.0), 6000.0)
    assert close(game_rating(0.0), -2000.0)
    assert close(game_rating(ABANDONMENT_PERCENTILE), -1600.0)


def test_end_to_end_two_strategies_share_a_pool():
    """The intended tuning workflow: same seed, two runs, one scored pool."""
    def run(candidate, name):
        with patched(make_engine=engine_factory(SplitEngine),
                     sample_config=configs_from(CONFIG, OTHER_CONFIG)):
            return run_matches("bargaining", candidate, p1_strategy, n=2, seed=99,
                               name=name)

    pool = run(greedy, "greedy") + run(picky, "picky")
    scores = percentile_scores(pool)
    assert scores["n_unscored"] == 0          # same seed -> the groups line up
    assert scores["n_groups"] == 4            # 2 configs x 2 roles
    # Seat 1: greedy takes 90%, picky proposes an even split -> greedy on top.
    # Seat 2: greedy accepts the even split, picky rejects it into a $0 no-deal
    # -> greedy on top again. Two-record groups give 0.75 and 0.25.
    assert all(close(e["percentile"], 0.75)
               for e in scores["scored"] if e["name"] == "greedy")
    assert all(close(e["percentile"], 0.25)
               for e in scores["scored"] if e["name"] == "picky")
    assert close(scores["by_name"]["greedy"]["mean_game_rating"], 4000.0)
    assert close(scores["by_name"]["picky"]["mean_game_rating"], 0.0)
    # The pool as a whole still centres on 2000: percentiles are zero-sum.
    assert close(scores["mean_game_rating"], 2000.0)


if __name__ == "__main__":
    failures = 0
    tests = sorted((name, fn) for name, fn in list(globals().items())
                   if name.startswith("test_") and callable(fn))
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            import traceback
            traceback.print_exc()
        else:
            print(f"ok   {name}")
    print(f"\n{len(tests) - failures} passed, {failures} failed")
    sys.exit(1 if failures else 0)
