"""Tests for the framing-experiment randomiser.

These are design tests, not behaviour tests. Each one asserts a property the
inference depends on, and is named after the property rather than the method, so
that a change which breaks the design shows up here as a failing *claim* rather
than as a diff:

* reproducibility        — same arrival stream, same arms, across processes
* within-block balance   — balance is enforced per block, not per experiment
* propensity correctness — the recorded probabilities are the real ones
* the kill switch        — one flag reverts everything, instantly
* numeric invariance     — the arm cannot reach the numbers, and if it ever
                           does the whole experiment stops rather than the turn

Run: .venv/bin/python -m pytest experiments/test_assign.py
"""

from __future__ import annotations

import collections
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments import assign as E  # noqa: E402

ARMS = (E.SILENT, E.NEUTRAL, "F1", "F2", "F5")


# --------------------------------------------------------------------------
# Fixtures and builders
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """No ambient environment, no leaked hard stop, no leaked default."""
    for name in list(os.environ):
        if name.startswith("GLEE_EXPERIMENT"):
            monkeypatch.delenv(name, raising=False)
    E.clear_hard_stop()
    E.reset_default_assigner()
    yield
    E.clear_hard_stop()
    E.reset_default_assigner()


def make_assigner(tmp_path, **kwargs) -> E.Assigner:
    params = dict(experiment_id="test-1", arms=ARMS, reps=2, weights={E.NEUTRAL: 2},
                  log_dir=str(tmp_path), enabled=True,
                  kill_file=str(tmp_path / "KILL"))
    params.update(kwargs)
    # Several tests pin a single arm so the draw is deterministic and the test
    # is about the mechanism rather than about which arm came up. Production
    # refuses a pool of one (it is not a randomisation); those tests opt out.
    if len(params["arms"]) == 1:
        params.setdefault("min_pool_size", 1)
    return E.Assigner(**params)


def make_game(game_id="g0", rnd=1, money=1000.0, opponent=("hidden", None),
              messages_allowed=True, complete_information=True,
              family="bargaining", action_type="offer", me="player_1"):
    return {
        "game_id": game_id,
        "game_family": family,
        "your_player": me,
        "opponent": {"type": opponent[0], "name": opponent[1]},
        "valid_actions": {"type": action_type},
        "game_state": {
            "round": rnd, "phase": "offer", "money_to_divide": money,
            "messages_allowed": messages_allowed,
            "complete_information": complete_information,
            "horizon_known": False, "proposer": me, "current_player": me,
            "delta_1": 0.9, "delta_2": 0.8, "last_offer": None, "history": [],
        },
    }


def make_action(share_to_me=0.6, money=1000.0):
    mine = round(share_to_me * money, 2)
    return {"alice_gain": mine, "bob_gain": money - mine}


PLAN = {"spe_share": 0.5555, "rounds_left": 9, "delta_me": 0.9, "delta_opp": 0.8,
        "aspiration": 555.5}


def neutral_composer(game, action, plan, arm):
    """A stand-in for experiments/framings.py — length-matched, argument-free."""
    return (f"[{arm}] This proposal leaves you the stated amount in round "
            f"{(game.get('game_state') or {}).get('round')}. "
            + "Stating the split plainly and without embellishment. " * 2)


def drive(assigner, n, share=0.6, opponent=("hidden", None), rnd=1,
          game_prefix="g", plan=PLAN):
    """n distinct decision points through the assigner; returns the arms drawn."""
    out = []
    for i in range(n):
        game = make_game(f"{game_prefix}{i}", rnd=rnd, opponent=opponent)
        ctx = E.context_of(game, make_action(share), plan)
        out.append(assigner.draw(ctx))
    return out


# --------------------------------------------------------------------------
# 1. Reproducibility
# --------------------------------------------------------------------------

def test_same_arrival_stream_gives_identical_arms(tmp_path):
    """Two independent assigners, same id and arm set, same stream, same arms.

    This is what makes the experiment auditable: the assignment can be
    recomputed from the log rather than trusted.
    """
    first = [a.arm for a in drive(make_assigner(tmp_path / "a"), 60)]
    second = [a.arm for a in drive(make_assigner(tmp_path / "b"), 60)]
    assert first == second
    assert len(set(first)) == len(ARMS), "all arms should appear in 60 draws"


def test_seed_depends_only_on_design_coordinates(tmp_path):
    """The arm PRNG must not be reachable from the numbers.

    ``randomized_strategy`` holds one ``random.Random(seed)`` stream consumed in
    call order to draw the offer share. If the arm draw shared that stream, arm
    and share would be deterministically correlated and the experiment would
    measure nothing. So the seed is asserted to be a pure function of the design
    coordinates and of nothing else.
    """
    assigner = make_assigner(tmp_path)
    seeds = set()
    # All three leave the responder inside [0.38, 0.40): one design point.
    for share in (0.605, 0.610, 0.615):
        ctx = E.context_of(make_game("gX"), make_action(share), PLAN)
        assigner._memo.clear()
        assigner._counters.clear()
        seeds.add(assigner.draw(ctx).arm_rng_seed)
    assert len(seeds) == 1
    seed = seeds.pop()
    assert assigner.experiment_id in seed and assigner.arm_set_version in seed
    for token in ("605", "610", "615", "alice_gain", "bob_gain"):
        assert token not in seed


def test_numeric_action_does_not_move_the_arm_within_a_stratum(tmp_path):
    """Vary only the number, holding the stratum fixed: the arms must not move.

    Blocking is on the share *bucket*; two offers inside the same bucket are the
    same design point, so any dependence of the arm on the exact number would be
    a leak from the outcome side of the estimand into the treatment side.
    """
    low = [a.arm for a in drive(make_assigner(tmp_path / "a"), 40, share=0.605)]
    high = [a.arm for a in drive(make_assigner(tmp_path / "b"), 40, share=0.615)]
    assert low == high

    # The converse, so the test is not vacuous: crossing a bucket boundary is
    # meant to be a different design point and a different block.
    across = [a.arm for a in drive(make_assigner(tmp_path / "c"), 40, share=0.60)]
    assert across != low


def test_repeat_decision_point_is_idempotent_and_consumes_no_slot(tmp_path):
    """An SDK retry after a rejected move re-presents the same turn.

    It must get the same arm — and it must NOT eat a second block slot, because
    retries are not independent of the arm (a long message is likelier to be
    rejected), so charging them to the block would bias its composition.
    """
    assigner = make_assigner(tmp_path)
    game, action = make_game("g-retry"), make_action()
    ctx = E.context_of(game, action, PLAN)

    first = assigner.draw(ctx)
    again = assigner.draw(ctx)
    third = assigner.draw(E.context_of(game, make_action(0.61), PLAN))

    assert again.arm == first.arm == third.arm
    assert again.repeat is True and first.repeat is False
    assert assigner._counters[first.block_key] == 1, "one slot for three presentations"


def test_replay_resumes_the_same_sequence_after_a_restart(tmp_path):
    """The fleet restarts constantly. A restart that restarted every block would
    re-randomise the first positions over and over and quietly break balance."""
    uninterrupted = [a.arm for a in drive(make_assigner(tmp_path / "u"), 40)]

    live = make_assigner(tmp_path / "r")
    for i in range(17):
        game, action = make_game(f"g{i}"), make_action()
        ctx = E.context_of(game, action, PLAN)
        assignment = live.draw(ctx)
        live.record(game, action, PLAN, ctx, assignment, {}, "sent",
                    E.numeric_fingerprint(action), after=E.numeric_fingerprint(action),
                    message="x")

    restarted = make_assigner(tmp_path / "r")
    assert restarted.replay() == 17, "counters rebuilt from the log, not reset"

    resumed = []
    for i in range(17, 40):
        ctx = E.context_of(make_game(f"g{i}"), make_action(), PLAN)
        resumed.append(restarted.draw(ctx).arm)

    # The restart is invisible: the interrupted run and the uninterrupted one
    # are the same sequence, including across the block boundary at position 12.
    assert uninterrupted == uninterrupted[:17] + resumed


def test_replay_ignores_records_from_another_arm_set_version(tmp_path):
    """Killing an arm bumps arm_set_version; the old block state must not be
    carried into the new one, or the first new block starts mid-permutation."""
    assigner = make_assigner(tmp_path)
    for i in range(6):
        game, action = make_game(f"g{i}"), make_action()
        ctx = E.context_of(game, action, PLAN)
        assigner.record(game, action, PLAN, ctx, assigner.draw(ctx), {}, "sent",
                        "before", after="before", message="x")

    successor = make_assigner(tmp_path)
    successor.kill_arm("F1")
    assert successor.arm_set_version != assigner.arm_set_version
    assert successor.replay() == 0


# --------------------------------------------------------------------------
# 2. Within-block balance
# --------------------------------------------------------------------------

def test_every_completed_block_is_exactly_balanced(tmp_path):
    """Balance is a per-block property, not a per-experiment one.

    Simple randomisation drifts out of balance exactly in the thin strata that
    carry the effect, and intake here is sequential and restart-prone. So the
    claim is the strong one: each *completed* block holds exactly reps*weight
    copies of each arm, no matter how many blocks are drawn.
    """
    assigner = make_assigner(tmp_path)
    assignments = drive(assigner, 12 * 9)
    blocks = collections.defaultdict(collections.Counter)
    for a in assignments:
        blocks[(a.block_key, a.block_index)][a.arm] += 1

    length = assignments[0].block_length
    assert length == 12          # 4 arms x 2 reps + neutral x 2 reps x 2 weight
    completed = [c for c in blocks.values() if sum(c.values()) == length]
    assert len(completed) == 9
    for counter in completed:
        for arm in ARMS:
            expected = assigner.reps * assigner.weights.get(arm, 1)
            assert counter[arm] == expected, (arm, dict(counter))


def test_balance_holds_within_strata_not_merely_overall(tmp_path):
    """Opponent identity moves P(accept) by 46 points, so an arm that lands
    disproportionately on one opponent manufactures an effect. Blocking must
    therefore balance *inside* each stratum, and imbalance inside any stratum is
    bounded by one partial block regardless of how the strata interleave."""
    assigner = make_assigner(tmp_path)
    opponents = [("hidden", None), ("agent", "Quantile"), ("agent", "pas-2"),
                 ("agent", "nobody-in-particular")]
    per_stratum = collections.defaultdict(collections.Counter)
    for i in range(600):
        opponent = opponents[i % len(opponents)]
        share = (0.55, 0.62, 0.70)[i % 3]
        game = make_game(f"g{i}", opponent=opponent, rnd=1 + (i % 2))
        ctx = E.context_of(game, make_action(share), PLAN)
        a = assigner.draw(ctx)
        per_stratum[a.stratum_id][a.arm] += 1

    assert len(per_stratum) >= 8, "the interleaving must actually hit many strata"
    for stratum, counter in per_stratum.items():
        total = sum(counter.values())
        for arm in ARMS:
            target = total * assigner.reps * assigner.weights.get(arm, 1) / 12
            # One partial block is the worst case a permuted block can be off by.
            assert abs(counter[arm] - target) <= assigner.reps * 2, (stratum, arm,
                                                                    dict(counter))


def test_blocks_are_keyed_by_arm_pool_so_conditional_arms_cannot_unbalance(tmp_path):
    """F6 is only defined under incomplete information, F4 only from round 2.

    If those arms sat in every block and were skipped when undefined, the block
    would never fill and never balance. Blocks are therefore formed over the
    eligible pool, and the pool is part of the key.
    """
    assigner = make_assigner(tmp_path, arms=E.ARM_SETS["stage1"])
    complete = E.context_of(make_game("gc", complete_information=True,
                                      family="negotiation"),
                            {"product_price": 120.0}, PLAN)
    incomplete = E.context_of(make_game("gi", complete_information=False,
                                        family="negotiation"),
                              {"product_price": 120.0}, PLAN)
    pool_c = E.arm_pool(complete, assigner.arms)
    pool_i = E.arm_pool(incomplete, assigner.arms)
    assert "F6" in pool_i and "F6" not in pool_c
    assert assigner.draw(complete).block_key != assigner.draw(incomplete).block_key
    assert "F4" not in pool_i, "round 1 has no prior offer of ours"


# --------------------------------------------------------------------------
# 3. Propensities
# --------------------------------------------------------------------------

def test_conditional_propensities_sum_to_one_at_every_draw(tmp_path):
    for a in drive(make_assigner(tmp_path), 200):
        assert a.propensities.keys() == set(a.pool)
        assert sum(a.propensities.values()) == pytest.approx(1.0)
        assert 0.0 < a.p_assign_conditional <= 1.0
        assert a.p_assign_conditional == pytest.approx(a.propensities[a.arm])


def test_marginal_propensities_sum_to_one_and_match_the_weights(tmp_path):
    assigner = make_assigner(tmp_path)
    marginals = {a.arm: a.p_assign for a in drive(assigner, 12)}
    assert sum(marginals.values()) == pytest.approx(1.0)
    assert marginals[E.NEUTRAL] == pytest.approx(4 / 12), "weight 2 x reps 2"
    assert marginals["F1"] == pytest.approx(2 / 12)
    assert sum(marginals[a] for a in ARMS) == pytest.approx(1.0)


def test_conditional_propensity_is_the_real_one_not_the_marginal(tmp_path):
    """With permuted blocks the per-draw probability is NOT 1/k — it depends on
    how much of the block is already spent. Randomisation-based inference needs
    the value that actually applied, so both are recorded and the conditional
    one is checked against the block's own remaining composition."""
    assigner = make_assigner(tmp_path)
    assignments = drive(assigner, 12)
    seen = collections.Counter()
    for a in assignments:
        remaining = a.block_length - a.block_position
        for arm in a.pool:
            budget = assigner.reps * assigner.weights.get(arm, 1)
            expected = (budget - seen[arm]) / remaining
            assert a.propensities[arm] == pytest.approx(expected)
        seen[a.arm] += 1
    assert assignments[-1].p_assign_conditional == 1.0, "last slot is forced"
    assert any(a.p_assign_conditional != a.p_assign for a in assignments)


def test_horvitz_thompson_weights_recover_the_block_size(tmp_path):
    """The point of recording p_assign is that 1/p is an unbiased inverse-
    probability weight. Over completed blocks the weights must reconstruct the
    number of decision points exactly."""
    assigner = make_assigner(tmp_path)
    assignments = drive(assigner, 12 * 5)
    # Each arm contributes (copies in block) x (L / copies) = L per block, so
    # five completed blocks over a five-arm pool must weight up to 5 x 5 x L.
    total = sum(1.0 / a.p_assign for a in assignments)
    assert total == pytest.approx(len(ARMS) * 12 * 5)
    per_arm = collections.Counter()
    for a in assignments:
        per_arm[a.arm] += 1.0 / a.p_assign
    for arm in ARMS:
        assert per_arm[arm] == pytest.approx(12 * 5)


# --------------------------------------------------------------------------
# 4. The kill switch
# --------------------------------------------------------------------------

def test_experiment_is_off_unless_explicitly_turned_on(tmp_path):
    """A fleet that has not opted in must behave exactly as it does today."""
    assigner = E.Assigner(log_dir=str(tmp_path), kill_file=str(tmp_path / "KILL"))
    assert assigner.enabled is False
    action = make_action()
    assert assigner.attach(make_game(), action, PLAN, compose=neutral_composer) is False
    assert "message" not in action
    assert not os.path.exists(os.path.join(str(tmp_path), E.LOG_FILENAME))


def test_env_flag_turns_it_on_and_off(tmp_path, monkeypatch):
    assigner = E.Assigner(log_dir=str(tmp_path), kill_file=str(tmp_path / "KILL"))
    monkeypatch.setenv("GLEE_EXPERIMENT", "on")
    assert assigner.enabled is True
    monkeypatch.setenv("GLEE_EXPERIMENT", "off")
    assert assigner.enabled is False


def test_kill_file_reverts_without_a_restart(tmp_path):
    """An arm misbehaving at 03:00 must be revertible by an operator with a
    filesystem and no deploy."""
    # A single treatment arm, so the draw is deterministic and the test is
    # about the switch rather than about which arm came up.
    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action()
    assert assigner.attach(make_game("g1"), action, PLAN, compose=neutral_composer)
    assert "message" in action

    assigner.kill("monitor: walkaway rate")
    assert assigner.enabled is False
    action2 = make_action()
    assert assigner.attach(make_game("g2"), action2, PLAN,
                           compose=neutral_composer) is False
    assert "message" not in action2

    assigner.revive()
    assert assigner.enabled is True


def test_killing_one_arm_removes_it_and_bumps_the_version(tmp_path):
    assigner = make_assigner(tmp_path)
    before = assigner.arm_set_version
    assigner.kill_arm("F2")
    assert assigner.arm_set_version != before
    arms = {a.arm for a in drive(assigner, 100)}
    assert "F2" not in arms
    assert E.NEUTRAL in arms and E.SILENT in arms


def test_killing_every_arm_disables_the_experiment(tmp_path):
    assigner = make_assigner(tmp_path)
    for arm in ARMS:
        assigner.kill_arm(arm)
    assert assigner.enabled is False


def test_module_level_attach_is_a_one_line_no_op_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("GLEE_LOG_DIR", str(tmp_path))
    action = make_action()
    assert E.attach(make_game(), action, PLAN, compose=neutral_composer) is False
    assert action == make_action()


# --------------------------------------------------------------------------
# 5. Numeric invariance — the estimand is defined at a held-fixed action
# --------------------------------------------------------------------------

def test_attaching_a_message_changes_nothing_numeric(tmp_path):
    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    for i in range(40):
        action = make_action(0.6)
        before = E.numeric_fingerprint(action)
        assigner.attach(make_game(f"g{i}"), action, PLAN, compose=neutral_composer)
        assert E.numeric_fingerprint(action) == before
        assert action["alice_gain"] == 600.0 and action["bob_gain"] == 400.0


def test_a_composer_that_touches_a_number_hard_stops_the_experiment(tmp_path):
    """This is the failure that would invalidate every record already collected,
    not merely the current turn, so it stops the experiment rather than the turn
    — and it leaves the caller's action untouched so the game proceeds."""
    def saboteur(game, action, plan, arm):
        action["alice_gain"] = 999.0
        return neutral_composer(game, action, plan, arm)

    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action(0.6)
    handled = assigner.attach(make_game("g-bad"), action, PLAN, compose=saboteur)

    assert handled is False
    assert "message" not in action
    assert E.hard_stopped() is not None
    assert assigner.enabled is False, "one violation stops all arms"

    records = read_log(tmp_path)
    assert records[-1]["experiment"]["outcome"] == "invariance_violation"
    assert records[-1]["experiment"]["numeric_invariant_ok"] is False


def test_a_coerce_that_rewrites_the_numbers_is_caught_too(tmp_path):
    """The after-fingerprint is taken on the action as it will be SUBMITTED, so
    a repair layer that quietly renormalises the split is caught as well."""
    def coerce(action, game):
        out = dict(action)
        out["alice_gain"] = 1.0
        out["bob_gain"] = 999.0
        return out

    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action(0.6)
    assert assigner.attach(make_game("g-c"), action, PLAN,
                           compose=neutral_composer, coerce=coerce) is False
    assert E.hard_stopped() is not None


def test_a_benign_coerce_is_applied_in_place(tmp_path):
    """dispatch re-coerces after attaching a message (the 2,000-char cap). The
    attach must run that same repair itself, so its after-hash is the real one
    and the caller's own re-coerce is idempotent."""
    def coerce(action, game):
        out = dict(action)
        out["message"] = (out.get("message") or "")[:50]
        return out

    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action(0.6)
    assert assigner.attach(make_game("g-ok"), action, PLAN,
                           compose=neutral_composer, coerce=coerce) is True
    assert len(action["message"]) == 50
    assert E.hard_stopped() is None


def test_message_is_capped_at_the_design_band(tmp_path):
    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action()
    assigner.attach(make_game("g-long"), action, PLAN,
                    compose=lambda *a: "x" * 5000)
    if "message" in action:
        assert len(action["message"]) <= E.MAX_MESSAGE_CHARS <= 2000


# --------------------------------------------------------------------------
# 6. Eligibility, the SILENT arm, and the log contract
# --------------------------------------------------------------------------

def read_log(tmp_path, name=E.LOG_FILENAME):
    path = os.path.join(str(tmp_path), name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_ineligible_turns_are_never_assigned(tmp_path):
    assigner = make_assigner(tmp_path)
    cases = [
        make_game("g1", messages_allowed=False),
        make_game("g2", action_type="decision"),
        make_game("g3", family="persuasion", action_type="seller_message"),
    ]
    for game in cases:
        action = make_action()
        assert assigner.attach(game, action, PLAN, compose=neutral_composer) is False
        assert "message" not in action
    assert read_log(tmp_path) == []


def test_negotiation_counteroffers_are_design_points(tmp_path):
    """A negotiation counteroffer is submitted as a *decision* carrying a price,
    not as an "offer". Taking the design's eligibility rule literally admits only
    round 1 of a negotiation and silently deletes the Stage-1 screening venue —
    and F4_RECIPROCITY with it, since F4 is undefined before round 2. Measured
    over the fleet's 61k logged turns the literal rule yields 0 eligible F4
    turns; this rule yields 784.
    """
    counter = make_game("g-counter", rnd=4, family="negotiation",
                        action_type="decision")
    ctx = E.context_of(counter, {"decision": "RejectOffer", "product_price": 180.0},
                       PLAN)
    assert ctx.carries_offer is True
    assert E.eligible(ctx)[0] is True
    assert "F4" in E.arm_pool(ctx, E.ARM_SETS["stage1"])

    # A bare accept or walkaway ends the exchange; there is nothing to persuade
    # about and it is not a design point.
    for bare in ({"decision": "AcceptOffer"}, {"decision": "WalkAway"}):
        ctx = E.context_of(counter, bare, PLAN)
        assert ctx.carries_offer is False
        assert E.eligible(ctx)[0] is False


def test_silent_arm_is_handled_and_recorded(tmp_path):
    """Silence is a named legal strategy and is the reference for the
    message-presence contrast. Logging only messaged turns would make this arm
    invisible and the denominator wrong — the exact error that made the earlier
    observational reading confuse "chose silence" with "was forbidden to speak".
    """
    assigner = make_assigner(tmp_path, arms=(E.SILENT,), weights={})
    action = make_action()
    assert assigner.attach(make_game("g-silent"), action, PLAN,
                           compose=neutral_composer) is True
    assert "message" not in action

    records = read_log(tmp_path)
    assert len(records) == 1
    design = records[0]["experiment"]
    assert design["arm"] == E.SILENT and design["outcome"] == "silent"
    assert design["message_len"] == 0
    assert design["numeric_invariant_ok"] is True


def test_compose_failure_falls_back_rather_than_faking_silence(tmp_path):
    """A treatment arm whose composer returns nothing must NOT become a silent
    turn — that would leak treatment mass into the control and bias the one
    contrast the design cannot lose. It falls back to today's templates and is
    logged as such so the analysis can drop it."""
    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action()
    assert assigner.attach(make_game("g-nc"), action, PLAN,
                           compose=lambda *a: None) is False
    assert "message" not in action
    assert read_log(tmp_path)[0]["experiment"]["outcome"] == "compose_failed"


def test_record_uses_the_gamelog_envelope(tmp_path):
    """scripts/transcript.py reads a fixed set of keys back out of a turn
    record. The experiment log has to carry all of them or the tooling that
    already exists stops working on it."""
    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action()
    assigner.attach(make_game("g-env"), action, PLAN, compose=neutral_composer)
    record = read_log(tmp_path)[0]

    for key in ("ts", "game_id", "game_family", "your_player", "phase", "round",
                "opponent", "action_type", "state", "plan", "action", "source"):
        assert key in record, key
    for key in ("ts", "round", "phase", "action_type", "action", "plan", "source",
                "error", "stage"):
        assert key in record, f"transcript.py reads {key}"
    assert record["source"].startswith("experiment:")
    assert record["plan"] == PLAN
    assert record["action"]["alice_gain"] == 600.0


def test_records_never_go_into_turns_jsonl(tmp_path):
    """Appending to turns.jsonl would make GameLog.write_game_record emit each
    of our moves twice and silently corrupt every stored transcript."""
    assigner = make_assigner(tmp_path)
    assigner.attach(make_game("g-sep"), make_action(), PLAN, compose=neutral_composer)
    assert os.path.exists(os.path.join(str(tmp_path), E.LOG_FILENAME))
    assert not os.path.exists(os.path.join(str(tmp_path), "turns.jsonl"))


def test_record_carries_every_blocking_variable_and_the_plan(tmp_path):
    """The design must be reconstructable from the log without guessing."""
    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action(0.6)
    assigner.attach(make_game("g-full", opponent=("agent", "Quantile")), action,
                    PLAN, probe="randomized", compose=neutral_composer)
    design = read_log(tmp_path)[0]["experiment"]

    for key in ("experiment_id", "arm_set_version", "stratifier_version", "probe",
                "arm", "arm_pool", "pool_id", "stratum_id", "block_key",
                "block_index", "block_position", "block_length", "arrival_index",
                "p_assign", "p_assign_conditional", "propensities", "arm_rng_seed",
                "eligibility_flags", "share_bucket", "opponent_class", "round_class",
                "share_to_responder", "money_to_divide", "horizon_known",
                "complete_information", "delta_me", "delta_opp", "rounds_left",
                "spe_share", "message_len", "message_sha256", "length_band_ok",
                "numeric_action_sha256_before", "numeric_action_sha256_after",
                "numeric_invariant_ok", "decision_key", "repeat"):
        assert key in design, key

    assert design["probe"] == "randomized"
    assert design["opponent_class"] == "Quantile"
    assert design["share_to_responder"] == pytest.approx(0.4)
    assert design["share_bucket"] == "s3"          # [0.40, 0.42)
    assert design["spe_share"] == PLAN["spe_share"]
    assert design["eligibility_flags"] == {"venue_ok": True, "messages_allowed": True,
                                           "carries_offer": True, "we_propose": True}


def test_records_follow_the_callers_own_log_directory(tmp_path):
    """Five agents, five log directories. Records must land beside the games
    they belong to, or the join in analyse.py is a guess."""
    class FakeLog:
        dir = str(tmp_path / "randomized")

    assigner = make_assigner(tmp_path)
    assigner.attach(make_game("g-dir"), make_action(), PLAN, log=FakeLog(),
                    compose=neutral_composer)
    assert read_log(tmp_path) == []
    assert len(read_log(tmp_path / "randomized")) == 1


# --------------------------------------------------------------------------
# 7. Stratification
# --------------------------------------------------------------------------

def test_share_buckets_straddle_the_measured_acceptance_cliff(tmp_path):
    """The cliff sits at 0.40 to the responder: P(accept) is .13 just below and
    .60 just above. The buckets exist to keep those two apart."""
    def bucket(share_to_them):
        game = make_game()
        action = make_action(1.0 - share_to_them)
        return E.context_of(game, action, PLAN).share_bucket

    assert bucket(0.30) == "s0"
    assert bucket(0.36) == "s1"
    assert bucket(0.39) == "s2"
    assert bucket(0.41) == "s3"
    assert bucket(0.45) == "s4"
    assert bucket(0.55) == "s5"
    assert bucket(0.399) != bucket(0.401), "the cliff must not sit inside a bucket"


def test_opponent_class_pools_the_long_tail(tmp_path):
    def klass(opponent):
        return E.context_of(make_game(opponent=opponent), make_action(),
                            PLAN).opponent_class

    assert klass(("hidden", None)) == "hidden"
    assert klass(("agent", "Quantile")) == "Quantile"
    assert klass(("agent", "theta")) == "other-agent"


# --------------------------------------------------------------------------
# 8. Interop with the composer (experiments/framing.py)
# --------------------------------------------------------------------------

def test_a_pool_of_one_is_not_a_randomisation(tmp_path):
    """Where only one arm has a true claim available, the propensity is 1.0 and
    the block carries no contrast at all. Assigning there would inflate that arm
    — in practice A0, which is eligible everywhere — with turns that can never
    be compared to anything. Measured over the fleet's logged turns, 2,698 of
    8,740 otherwise-eligible turns are exactly this case."""
    assigner = make_assigner(tmp_path, arms=E.ARM_SETS["stage1"])
    action = make_action()
    handled = assigner.attach(
        make_game("g-lonely"), action, PLAN, compose=neutral_composer,
        arm_eligible=lambda arm, *rest: arm == E.SILENT)

    assert handled is False, "left to the existing template path"
    assert read_log(tmp_path)[0]["experiment"]["outcome"] == "no_arm_defined"

    permissive = make_assigner(tmp_path / "p", arms=E.ARM_SETS["stage1"],
                               min_pool_size=1)
    assert permissive.attach(make_game("g-lonely"), make_action(), PLAN,
                             compose=neutral_composer,
                             arm_eligible=lambda arm, *rest: arm == E.SILENT) is True


def test_the_estimation_stratum_is_block_key_not_stratum_id(tmp_path):
    """The eligible pool is state-dependent, so it is a confounder unless the
    analysis conditions on it.

    Here an arm is eligible only on high offers. Grouping by stratum_id then
    shows the arm predicting the share — not because the randomisation leaked,
    but because the pool did. Grouping by block_key (stratum x pool), which is
    what the assigner actually randomised inside, removes it. Measured on the
    fleet's 62,786 logged turns the same contrast is p=0.000 by stratum_id and
    p=0.377 by block_key.
    """
    assigner = make_assigner(tmp_path)

    def high_offers_only(arm, game, action, plan):
        if arm != "F5":
            return True
        return action.get("bob_gain", 0) > 390

    for i in range(200):
        # Both leave the responder inside [0.38, 0.40) — one bucket, one
        # stratum, but two different eligible pools.
        share_to_me = 0.605 if i % 2 else 0.615
        action = make_action(share_to_me)
        assigner.attach(make_game(f"g{i}"), action, PLAN,
                        compose=neutral_composer, arm_eligible=high_offers_only)

    rows = [(r["experiment"], r["action"]["bob_gain"]) for r in read_log(tmp_path)
            if r["experiment"]["arm"]]

    def spread(key):
        groups = collections.defaultdict(lambda: collections.defaultdict(list))
        for design, share in rows:
            groups[design[key]][design["arm"]].append(share)
        worst = 0.0
        for arms in groups.values():
            everything = [v for vs in arms.values() for v in vs]
            centre = sum(everything) / len(everything)
            for values in arms.values():
                if len(values) >= 5:
                    worst = max(worst, abs(sum(values) / len(values) - centre))
        return worst

    assert spread("stratum_id") > 2.0, "pool confounding is visible, as expected"
    assert spread("block_key") == 0.0, "inside a block the arm predicts nothing"


def test_arm_eligibility_narrows_the_pool_before_the_draw(tmp_path):
    """An arm with no true claim available on this turn must be excluded BEFORE
    the draw, not after. Drawing it and then discovering it has nothing to say
    would spend a block slot on a turn that goes quiet — which both unbalances
    the block and leaks treatment mass into the silent control."""
    assigner = make_assigner(tmp_path)
    seen = []

    def arm_eligible(arm, game, action, plan):
        seen.append(arm)
        return arm != "F2"

    for i in range(24):
        action = make_action()
        assigner.attach(make_game(f"g{i}"), action, PLAN, compose=neutral_composer,
                        arm_eligible=arm_eligible)

    assert "F2" in seen, "the filter really was offered the arm"
    arms = {r["experiment"]["arm"] for r in read_log(tmp_path)}
    assert "F2" not in arms
    assert {E.SILENT, E.NEUTRAL, "F1", "F5"} <= arms

    # A narrowed pool is a different block, not a corrupted one.
    pools = {tuple(r["experiment"]["arm_pool"]) for r in read_log(tmp_path)}
    assert pools == {(E.SILENT, E.NEUTRAL, "F1", "F5")}


def test_composer_provenance_is_recorded_not_interpreted(tmp_path):
    """framing.describe() returns the text plus which claim fired and whether it
    was fact or bluff. That belongs in the record — and nowhere else: it must
    not be able to reach back into the assignment."""
    def describing(game, action, plan, arm):
        return {"text": neutral_composer(game, action, plan, arm),
                "claim": "pv_rebase", "kind": "fact",
                "grammar_version": "framing-grammar-1"}

    assigner = make_assigner(tmp_path, arms=("F1",), weights={})
    action = make_action()
    assert assigner.attach(make_game("g-prov"), action, PLAN, compose=describing)
    design = read_log(tmp_path)[0]["experiment"]
    assert design["composer"]["claim"] == "pv_rebase"
    assert design["composer"]["grammar_version"] == "framing-grammar-1"
    assert design["arm"] == "F1" and design["arm_label"] == "reference re-basing"
    assert "text" not in design["composer"], "text is recorded by hash and length"
    assert design["message_len"] == len(action["message"])


def test_arm_codes_match_the_composer_module():
    """This module and framing.py must name the same cells the same way; a
    translation table between them is a place for the arms to drift apart."""
    framing = pytest.importorskip("experiments.framing")
    assert set(E.ARM_SETS["stage1"]) == set(framing.ARMS)
    assert E.SILENT in framing.CONTROL_ARMS and E.NEUTRAL in framing.CONTROL_ARMS


def test_framing_hooks_bind_end_to_end(tmp_path):
    """The whole path, with the real composer: draw an arm, get real text, and
    hold the numbers fixed."""
    pytest.importorskip("experiments.framing")
    compose, arm_eligible = E.framing_hooks()
    assert compose is not None and arm_eligible is not None

    assigner = make_assigner(tmp_path, arms=E.ARM_SETS["stage1"])
    sent = 0
    for i in range(60):
        action = make_action(0.6)
        before = E.numeric_fingerprint(action)
        handled = assigner.attach(make_game(f"g{i}"), action, PLAN,
                                  probe="randomized", compose=compose,
                                  arm_eligible=arm_eligible)
        assert E.numeric_fingerprint(action) == before
        if handled and "message" in action:
            sent += 1
            assert 0 < len(action["message"]) <= E.MAX_MESSAGE_CHARS
    assert E.hard_stopped() is None
    assert sent > 0, "the real composer produced real text through the randomiser"


def test_a_broken_composer_never_takes_a_turn_down(tmp_path, monkeypatch):
    """The composer is third-party to this module. If it raises, or vanishes,
    the turn must fall back to today's templates rather than escaping into the
    SDK — where a raised exception submits nothing and the game stalls to a
    120-second timeout scored at the 5th percentile."""
    framing = pytest.importorskip("experiments.framing")

    def explode(*args, **kwargs):
        raise RuntimeError("composer is broken")

    monkeypatch.setattr(framing, "describe", explode)
    monkeypatch.setattr(framing, "compose", explode)
    monkeypatch.setattr(framing, "eligible", explode)

    compose, arm_eligible = E.framing_hooks()
    assigner = make_assigner(tmp_path, arms=E.ARM_SETS["stage1"])
    action = make_action()
    handled = assigner.attach(make_game("g-broken"), action, PLAN,
                              compose=compose, arm_eligible=arm_eligible)
    assert handled is False
    assert "message" not in action
    assert E.hard_stopped() is None, "a broken composer is not a design violation"


def test_concurrent_draws_do_not_corrupt_a_block(tmp_path):
    """The SDK runs a worker pool, so two turns in the same stratum are drawn
    concurrently. Losing that race would double-issue a block slot and quietly
    unbalance the block that the whole design rests on."""
    import threading

    assigner = make_assigner(tmp_path)
    drawn, lock = [], threading.Lock()

    def worker(base):
        for i in range(30):
            ctx = E.context_of(make_game(f"t{base}-{i}"), make_action(), PLAN)
            a = assigner.draw(ctx)
            with lock:
                drawn.append((a.block_key, a.block_index, a.block_position))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(drawn) == 240
    assert len(set(drawn)) == 240, "every draw took a distinct block slot"


def test_unparseable_state_never_raises(tmp_path):
    """Every entry point is total: a malformed game costs a message, never a
    turn. The fleet's record is 0 invalid moves in 24,472 turns and nothing here
    is allowed to be the first."""
    assigner = make_assigner(tmp_path)
    for game in ({}, {"game_state": None}, {"game_family": "bargaining"},
                 {"game_id": None, "game_state": {"money_to_divide": "??"}}):
        action = {}
        assert assigner.attach(game, action, None, compose=neutral_composer) is False
    assert E.assign({}, {}, None) is None
