"""Tests for the per-game, hand-written bargaining message experiment."""

from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import os
import random

import pytest

from glee_agent import llm, messages, runtime_flags
from glee_agent.config import Config
from glee_agent.dispatch import make_strategy
from glee_agent.strategies import bargaining
from scripts import live_percentile


MONEY = 1000.0


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("GLEE_BARG", "GLEE_LLM", "GLEE_OPP", "GLEE_PROBE")):
            monkeypatch.delenv(key, raising=False)
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    yield


def _gid_for(arm: str) -> str:
    for index in range(10_000):
        gid = f"barg-arm-{index}"
        if messages.bargaining_arm(gid) == arm:
            return gid
    raise AssertionError(f"no game id found for {arm}")


def _offer_game(*, gid="barg", rnd=2, share=0.60, history=None,
                messages_allowed=True) -> dict:
    return {
        "game_id": gid,
        "game_family": "bargaining",
        "your_player": "player_2",
        "phase": "offer",
        "game_state": {
            "round": rnd,
            "phase": "offer",
            "current_player": "player_2",
            "proposer": "player_2",
            "money_to_divide": MONEY,
            "horizon_known": True,
            "max_rounds": 12,
            "complete_information": True,
            "messages_allowed": messages_allowed,
            "history": history or [],
            "last_offer": None,
            "delta_1": 0.8,
            "delta_2": 0.95,
        },
        "valid_actions": {"type": "offer", "fields": {}},
    }


def _numeric(action: dict) -> dict:
    return {key: value for key, value in action.items()
            if key != "message" and not str(key).startswith("_")}


def test_flag_off_is_silent_and_flag_on_reaches_the_template_bank(monkeypatch):
    game = _offer_game(gid=_gid_for("B1"))
    off = bargaining.decide(game, Config.from_env())
    assert "message" not in off
    assert "barg_msg_arm" not in off["_plan"]

    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")
    on = bargaining.decide(game, Config.from_env())
    assert on["message"]
    assert on["_plan"]["barg_msg_arm"]["arm"] == "B1"
    assert _numeric(on) == _numeric(off)


def test_hash_assignment_is_exact_and_stable_for_the_whole_game():
    seen = set()
    for index in range(100):
        gid = f"hash-{index}"
        expected_index = int(hashlib.sha256(
            (messages.BARG_ARM_SALT + gid).encode()).hexdigest(), 16)
        expected = messages.BARG_ARMS[expected_index % len(messages.BARG_ARMS)]
        assert messages.bargaining_arm(gid) == expected
        seen.add(expected)
        for rnd in (1, 2, 7, 12, 99):
            assert messages.bargaining_arm(_offer_game(gid=gid, rnd=rnd)["game_id"]) == expected
    assert seen == set(messages.BARG_ARMS)
    assert messages.bargaining_arm(None) is None
    assert messages.bargaining_arm("") is None


def test_all_arms_preserve_the_split_and_share_one_length_band(monkeypatch):
    baseline = bargaining.decide(_offer_game(), Config.from_env())
    baseline_numeric = _numeric(baseline)
    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")

    seen = {}
    for arm in messages.BARG_ARMS:
        action = bargaining.decide(_offer_game(gid=_gid_for(arm)), Config.from_env())
        record = action["_plan"]["barg_msg_arm"]
        assert record["arm"] == arm
        assert record["numeric_invariant_ok"] is True
        assert _numeric(action) == baseline_numeric
        seen[arm] = action.get("message")
        if arm == "B0":
            assert "message" not in action
            assert record["outcome"] == "silent"
        else:
            assert messages.BARG_ARM_LEN_LO <= len(action["message"]) <= messages.BARG_ARM_LEN_HI
            assert record["outcome"] == "sent"

    assert seen["B0"] is None
    assert len({seen["B1"], seen["B2"], seen["B3"]}) == 3


def test_silent_arm_is_recorded_and_not_backfilled_by_dispatch(monkeypatch):
    class Capture:
        def __init__(self):
            self.turns = []

        def turn(self, game, action, plan, source):
            self.turns.append((action, plan, source))

        def error(self, *args, **kwargs):
            raise AssertionError("strategy unexpectedly failed")

    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")
    capture = Capture()
    action = make_strategy(Config.from_env(), capture)(_offer_game(gid=_gid_for("B0")))

    assert "message" not in action
    _, plan, source = capture.turns[-1]
    assert plan["barg_msg_arm"]["outcome"] == "silent"
    assert source.endswith("+barg-arm-B0")


@pytest.mark.parametrize(
    ("failure_mode", "expected_reason"),
    (("raise", "exception"), ("invalid", "invalid-composer-result")),
)
def test_failed_non_silent_composition_keeps_assignment_record(
        monkeypatch, failure_mode, expected_reason):
    class Capture:
        def __init__(self):
            self.turns = []

        def turn(self, game, action, plan, source):
            self.turns.append((action, plan, source))

        def error(self, *args, **kwargs):
            raise AssertionError("strategy unexpectedly failed")

    def broken_composer(*args, **kwargs):
        if failure_mode == "raise":
            raise RuntimeError("forced template failure")
        return "not a composer record"

    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")
    monkeypatch.setattr(messages, "bargaining_arm_message", broken_composer)
    capture = Capture()
    action = make_strategy(Config.from_env(), capture)(
        _offer_game(gid=_gid_for("B2")))

    assert "message" not in action
    _, plan, source = capture.turns[-1]
    assert plan["barg_msg_arm"]["arm"] == "B2"
    assert plan["barg_msg_arm"]["outcome"] == "compose_failed"
    assert plan["barg_msg_arm"]["reason"] == expected_reason
    assert source.endswith("+barg-arm-B2")


def test_dispatch_never_calls_an_llm_for_bargaining_messages(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("bargaining reached an LLM hook")

    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")
    monkeypatch.setenv("GLEE_LLM_FAMILIES", "bargaining,persuasion")
    monkeypatch.setattr(llm, "write_message", forbidden)
    monkeypatch.setattr(llm, "propose_action", forbidden)
    cfg = replace(Config.from_env(), llm_mode="full")

    action = make_strategy(cfg)(_offer_game(gid=_gid_for("B2")))

    assert action["message"]
    assert "both sides receive zero" in action["message"]


def test_message_quotes_the_wire_coerced_split(monkeypatch):
    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")
    game = _offer_game(gid=_gid_for("B1"))
    game["game_state"]["delta_1"] = 0.8
    game["game_state"]["delta_2"] = 0.8
    cfg = Config.from_env()
    raw = bargaining._decide(game, cfg)
    assert raw["alice_gain"] != round(raw["alice_gain"])

    action = make_strategy(cfg)(game)

    assert action["alice_gain"] == round(raw["alice_gain"])
    assert f"{action['alice_gain']:,.2f}" in action["message"]
    assert f"{raw['alice_gain']:,.2f}" not in action["message"]


def test_forbidden_channel_and_missing_game_id_stay_silent(monkeypatch):
    monkeypatch.setenv(messages.BARG_MSG_FLAG, "1")

    forbidden = bargaining.decide(
        _offer_game(gid=_gid_for("B2"), messages_allowed=False), Config.from_env())
    missing = bargaining.decide(_offer_game(gid=""), Config.from_env())
    unknown_channel = _offer_game(gid=_gid_for("B2"))
    unknown_channel["game_state"].pop("messages_allowed")
    unknown = bargaining.decide(unknown_channel, Config.from_env())

    assert "message" not in forbidden and "barg_msg_arm" not in forbidden["_plan"]
    assert "message" not in missing and "barg_msg_arm" not in missing["_plan"]
    assert "message" not in unknown and "barg_msg_arm" not in unknown["_plan"]


def test_arm_text_is_invariant_to_private_plan_and_game_state_fields():
    game_a = _offer_game(gid="leak-invariance")
    game_b = copy.deepcopy(game_a)
    game_b["game_state"].update(
        complete_information=False,
        horizon_known=False,
        delta_2=1.0,
    )
    game_b["game_state"].pop("delta_1")
    game_b["game_state"].pop("max_rounds")
    action = {"alice_gain": 400.0, "bob_gain": 600.0}
    private_a = {
        "delta_me": 0.8,
        "delta_opp": 1.0,
        "rounds_left": 1,
        "aspiration": 900.0,
        "offer_floor": 570.0,
        "realistic_continuation": 850.0,
        "planned_counter_share": 0.61,
        "opponent_evidence": {"basis": "opponent not conceding"},
    }
    private_b = {
        "delta_me": 1.0,
        "delta_opp": 0.8,
        "rounds_left": 99,
        "aspiration": 400.0,
        "offer_floor": 0.0,
        "realistic_continuation": 100.0,
        "planned_counter_share": 0.80,
        "opponent_evidence": {"basis": "projected from concession trend"},
    }

    for arm in ("B1", "B2", "B3"):
        left = messages.bargaining_arm_message(
            arm, game_a, action, private_a, random.Random(91))
        right = messages.bargaining_arm_message(
            arm, game_b, action, private_b, random.Random(91))
        assert left == right


@pytest.mark.parametrize(
    ("phrases", "holding_plan", "other_plan", "holding_share", "other_share"),
    [
        (("This is the last round", "There is no round after this one"),
         {"rounds_left": 1}, {"rounds_left": 5}, 0.60, 0.60),
        (("Delay costs you more per round",
          "Your value decays faster than mine here"),
         {"delta_me": 0.95, "delta_opp": 0.80},
         {"delta_me": 0.80, "delta_opp": 0.95}, 0.60, 0.60),
        (("Every round we spend costs us both real value",
          "Inflation takes a bite out of this each round"),
         {"delta_me": 0.90, "delta_opp": 0.90},
         {"delta_me": 1.0, "delta_opp": 1.0}, 0.60, 0.60),
        (("rounds left before this pays nothing",),
         {"rounds_left": 3}, {"rounds_left": 5}, 0.60, 0.60),
        (("You have not moved in several rounds",
          "Neither of us gains by repeating ourselves into a zero"),
         {"opponent_evidence": {"basis": "opponent not conceding"}},
         {"opponent_evidence": {"basis": "projected trend"}}, 0.60, 0.60),
        (("priced this off the discount rates",),
         {}, {}, 0.60, 0.55),
    ],
)
def test_retired_hidden_state_phrases_emit_on_neither_side_of_old_gate(
        phrases, holding_plan, other_plan, holding_share, other_share):
    emission_counts = []
    for plan, share in ((holding_plan, holding_share),
                        (other_plan, other_share)):
        game = _offer_game()
        action = {
            "alice_gain": MONEY * (1.0 - share),
            "bob_gain": MONEY * share,
        }
        count = 0
        for arm in messages.BARG_ARMS:
            for seed in range(64):
                text = messages.bargaining_arm_message(
                    arm, game, action, plan, random.Random(seed)).get("text") or ""
                count += any(phrase in text for phrase in phrases)
        emission_counts.append(count)
    assert emission_counts == [0, 0]


def test_non_silent_arms_are_tightly_length_matched_without_failures():
    lengths = {arm: [] for arm in messages.BARG_ARMS[1:]}
    for money, seat, moved in (
        (1.0, "player_1", False),
        (1_000.0, "player_2", False),
        (1_000_000.0, "player_1", True),
        (123_456_789.12, "player_2", True),
    ):
        other = "player_2" if seat == "player_1" else "player_1"
        history = []
        if moved:
            history = [{
                "round": 2,
                "proposer": seat,
                "offer": {
                    f"{seat}_gain": money * 0.70,
                    f"{other}_gain": money * 0.30,
                },
            }]
        game = _offer_game(history=history)
        game["your_player"] = seat
        game["game_state"].update(
            current_player=seat,
            proposer=seat,
            money_to_divide=money,
            round=4,
        )
        action = {
            "alice_gain": money * (0.60 if seat == "player_1" else 0.40),
            "bob_gain": money * (0.60 if seat == "player_2" else 0.40),
        }
        for arm in messages.BARG_ARMS[1:]:
            for seed in range(32):
                out = messages.bargaining_arm_message(
                    arm, game, action, rng=random.Random(seed))
                assert out["reason"] == "ok", (money, seat, moved, arm, seed, out)
                lengths[arm].append(len(out["text"]))

    assert all(abs(length - messages.BARG_ARM_TARGET_LEN) <= 1
               for arm_lengths in lengths.values() for length in arm_lengths)


def test_percentile_report_excludes_message_disabled_games(monkeypatch, capsys):
    monkeypatch.setattr(live_percentile, "bargaining_arm", lambda gid: gid)
    rows = [
        ("champion", 1.0, "bargaining", 0.40, "B0", True),
        ("champion", 1.0, "bargaining", 0.60, "B1", True),
        ("champion", 1.0, "bargaining", 0.00, "B0", False),
        ("champion", 1.0, "bargaining", 1.00, "B2", False),
    ]

    live_percentile.report_barg_msg(rows, 24.0)

    output = capsys.readouterr().out
    pooled = next(line for line in output.splitlines()
                  if line.startswith("POOLED"))
    assert "0.4000 (n=    1)" in pooled
    assert "0.6000 (n=    1)" in pooled
    assert "scope --hours/--slots to an era" in output


def test_concession_phrases_emit_on_both_sides_of_the_old_share_gate():
    phrases = (
        "That is a serious move toward you",
        "I have come a long way to you",
    )
    emission_counts = {}
    for own_share in (0.40, 0.60):
        current_to_them = MONEY * (1.0 - own_share)
        prior_to_them = current_to_them - 100.0
        history = [{
            "round": 2,
            "proposer": "player_2",
            "decision": "reject",
            "offer": {
                "player_1_gain": prior_to_them,
                "player_2_gain": MONEY - prior_to_them,
            },
        }]
        game = _offer_game(share=own_share, history=history)
        action = {
            "alice_gain": current_to_them,
            "bob_gain": MONEY * own_share,
        }
        counts = {phrase: 0 for phrase in phrases}
        for seed in range(1000):
            text = messages.bargaining_arm_message(
                "B3", game, action, rng=random.Random(seed))["text"]
            for phrase in phrases:
                counts[phrase] += phrase in text
        emission_counts[own_share] = counts

    for counts in emission_counts.values():
        assert all(count > 0 for count in counts.values()), emission_counts
    assert emission_counts == {
        0.40: {phrases[0]: 503, phrases[1]: 497},
        0.60: {phrases[0]: 503, phrases[1]: 497},
    }


def test_concession_phrases_require_public_prior_movement():
    action = {"alice_gain": 400.0, "bob_gain": 600.0}
    no_move = _offer_game(history=[])
    tiny_move = _offer_game(history=[{
        "round": 2,
        "proposer": "player_2",
        "offer": {"player_1_gain": 399.0, "player_2_gain": 601.0},
    }])
    malformed = _offer_game(history=[{
        "round": 2,
        "proposer": "player_2",
        "offer": {"player_1_gain": "not-a-gain", "player_2_gain": 601.0},
    }])
    for game in (no_move, tiny_move, malformed):
        for seed in range(64):
            out = messages.bargaining_arm_message(
                "B3", game, action, rng=random.Random(seed))
            assert out["claim_id"] == "b3_public_allocation"
            assert "serious move" not in out["text"]
            assert "come a long way" not in out["text"]
