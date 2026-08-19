"""Tests for the compositional framing grammar.

Four properties, in the order they matter:

1. **Legality** — every arm emits either nothing or a legal message, in every
   family and every phase, and never text on a phase that carries none.
2. **Truth** — no arm emits a claim its state does not support, and no arm
   emits a promise about our own future moves that the plan it was handed
   contradicts. This is the one that has already cost us once.
3. **Variety with fixed semantics** — the surface varies enough that a repeat
   opponent cannot key on a fixed string, while the CLAIM an arm makes is
   constant given the state, or the arm is not one treatment.
4. **Totality** — the composer never raises and never mutates its inputs,
   because a message is never worth risking the move over.

Run: ``.venv/bin/python -m pytest experiments/test_framing.py``
"""

from __future__ import annotations

import copy
import json
import math
import os
import random
import statistics
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import framing as F                                            # noqa: E402
from glee_agent.config import Config                            # noqa: E402
from glee_agent.strategies import bargaining, negotiation, persuasion  # noqa: E402
from glee_agent.text import reads_as_recommendation             # noqa: E402

CFG = Config()

#: Arms that are declared to have no safe claim in a family. Everything else
#: must demonstrate at least one eligible state in the grid below.
UNSUPPORTED = {("F6", "persuasion")}


# ---------------------------------------------------------------------------
# state builders
# ---------------------------------------------------------------------------

def barg_game(round_=3, max_rounds=12, money=10_000.0, complete=True,
              d_me=0.9, d_opp=0.8, messages=True, history=None,
              me="player_1", phase="offer"):
    me_is_alice = me == "player_1"
    state = {
        "round": round_,
        "max_rounds": max_rounds,
        "horizon_known": max_rounds is not None,
        "money_to_divide": money,
        "complete_information": complete,
        "messages_allowed": messages,
        "current_player": me,
        "history": history or [],
    }
    state["delta_1" if me_is_alice else "delta_2"] = d_me
    if complete:
        state["delta_2" if me_is_alice else "delta_1"] = d_opp
    if phase == "decision":
        state["last_offer"] = {"proposer": "player_2" if me_is_alice else "player_1",
                               "player_1_gain": money * 0.4,
                               "player_2_gain": money * 0.6, "round": round_ - 1}
    return {"game_id": f"b{round_}-{max_rounds}-{complete}", "game_family": "bargaining",
            "your_player": me, "valid_actions": {"type": phase}, "game_state": state}


def nego_game(round_=3, max_rounds=10, seller=True, messages=True, history=None,
              value=1000.0, phase="offer", last_price=None):
    me = "player_1"
    state = {
        "round": round_, "max_rounds": max_rounds, "horizon_known": max_rounds is not None,
        "messages_allowed": messages, "current_player": me,
        f"{me}_role": "seller" if seller else "buyer",
        f"{me}_value": value, "history": history or [],
    }
    if last_price is not None:
        state["last_offer"] = {"price": last_price, "from_player": "player_2",
                               "round": round_ - 1}
    return {"game_id": f"n{round_}-{seller}", "game_family": "negotiation",
            "your_player": me, "valid_actions": {"type": phase}, "game_state": state}


def pers_game(round_=2, total=5, quality="low", price=100.0, p=0.5, v=200.0, u=0.0,
              history=None, phase="seller_message"):
    state = {"round": round_, "total_rounds": total, "current_quality": quality,
             "product_price": price, "p": p, "v": v, "u": u,
             "messages_allowed": True, "history": history or []}
    return {"game_id": f"p{round_}-{quality}", "game_family": "persuasion",
            "your_player": "player_1", "valid_actions": {"type": phase},
            "game_state": state}


BARG_HISTORY = [
    {"round": 1, "proposer": "player_1",
     "offer": {"player_1_gain": 8_000.0, "player_2_gain": 2_000.0, "proposer": "player_1"}},
    {"round": 2, "proposer": "player_2",
     "offer": {"player_1_gain": 1_500.0, "player_2_gain": 8_500.0, "proposer": "player_2"}},
    {"round": 3, "proposer": "player_1",
     "offer": {"player_1_gain": 7_000.0, "player_2_gain": 3_000.0, "proposer": "player_1"}},
    {"round": 4, "proposer": "player_2",
     "offer": {"player_1_gain": 2_200.0, "player_2_gain": 7_800.0, "proposer": "player_2"}},
]

NEGO_HISTORY = [
    {"round": 1, "offer": {"price": 2_200.0, "from_player": "player_1"}},
    {"round": 2, "offer": {"price": 900.0, "from_player": "player_2"}},
    {"round": 3, "offer": {"price": 1_900.0, "from_player": "player_1"}},
    {"round": 4, "offer": {"price": 1_050.0, "from_player": "player_2"}},
]

PERS_HISTORY = [
    {"round": 1, "bought": True, "quality": "high", "seller_message": "I recommend this one."},
    {"round": 2, "bought": False, "quality": "low",
     "seller_message": "I would hold off on this one."},
]


def _turns():
    """(label, game, action, plan) over a grid that touches every phase.

    Plans come from the live strategies, so the composer is exercised against
    the exact dict shapes ``dispatch`` will hand it.
    """
    out = []
    grid = []
    for round_, max_rounds in ((1, 12), (3, 12), (5, 12), (11, 12), (12, 12),
                               (1, None), (5, None), (25, None)):
        for complete in (True, False):
            for d_me, d_opp in ((0.8, 0.8), (0.9, 0.95), (1.0, 1.0), (0.95, 0.8)):
                for money in (100.0, 10_000.0, 1_000_000.0):
                    for me in ("player_1", "player_2"):
                        grid.append(barg_game(round_=round_, max_rounds=max_rounds,
                                              money=money, complete=complete,
                                              d_me=d_me, d_opp=d_opp, me=me))
    grid.append(barg_game(round_=5, history=BARG_HISTORY))
    grid.append(barg_game(round_=5, history=BARG_HISTORY, complete=False))
    grid.append(barg_game(round_=25, max_rounds=None, history=BARG_HISTORY))
    grid.append(barg_game(messages=False))
    grid.append(barg_game(phase="decision"))
    for game in grid:
        raw = bargaining.decide(copy.deepcopy(game), CFG)
        plan = raw.pop("_plan", None)
        out.append((f"barg r{game['game_state']['round']}", game, raw, plan))

    ngrid = []
    for round_, max_rounds in ((1, 10), (3, 10), (5, 10), (9, 10), (10, 10),
                               (1, None), (6, None)):
        for seller in (True, False):
            for value in (10.0, 1_000.0, 250_000.0):
                ngrid.append(nego_game(round_=round_, max_rounds=max_rounds,
                                       seller=seller, value=value))
    ngrid.append(nego_game(round_=5, history=NEGO_HISTORY))
    ngrid.append(nego_game(round_=5, history=NEGO_HISTORY, seller=False))
    ngrid.append(nego_game(round_=9, history=NEGO_HISTORY))
    ngrid.append(nego_game(messages=False))
    ngrid.append(nego_game(round_=5, phase="decision", history=NEGO_HISTORY,
                           last_price=1_050.0))
    ngrid.append(nego_game(round_=10, phase="decision", history=NEGO_HISTORY,
                           last_price=3_000.0))
    for game in ngrid:
        raw = negotiation.decide(copy.deepcopy(game), CFG)
        plan = raw.pop("_plan", None)
        out.append((f"nego r{game['game_state']['round']}", game, raw, plan))

    pgrid = []
    for round_, total in ((1, 5), (2, 5), (5, 5)):
        for quality in ("low", "high"):
            for price, v, u in ((100.0, 200.0, 0.0), (100.0, 120.0, 90.0),
                                (100.0, 50.0, 0.0)):
                for history in ([], PERS_HISTORY):
                    pgrid.append(pers_game(round_=round_, total=total, quality=quality,
                                           price=price, v=v, u=u, history=history))
    pgrid.append(pers_game(phase="seller_recommendation"))
    pgrid.append(pers_game(phase="buyer_decision"))
    for game in pgrid:
        raw = persuasion.decide(copy.deepcopy(game), CFG)
        plan = raw.pop("_plan", None)
        out.append((f"pers r{game['game_state']['round']}", game, raw, plan))
    return out


TURNS = _turns()
SEEDS = [random.Random(i) for i in range(4)]


def _messages(arm, seeds=(0,)):
    """All (turn, describe-record) pairs where ``arm`` actually spoke."""
    got = []
    for label, game, action, plan in TURNS:
        for seed in seeds:
            rec = F.describe(arm, game, action, plan, random.Random(seed))
            if rec["text"]:
                got.append((label, game, action, plan, rec))
    return got


# ---------------------------------------------------------------------------
# 1. legality
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("arm", F.ARMS)
def test_every_arm_is_legal_on_every_turn(arm):
    for label, game, action, plan in TURNS:
        for rng in SEEDS:
            text = F.compose(arm, game, action, plan, rng)
            if text is None:
                continue
            assert isinstance(text, str), label
            assert text.strip() == text and text, label
            assert len(text) <= F.MAX_MESSAGE_LEN, label
            assert "\n" not in text and "\r" not in text, label
            assert len(text) <= F.LEN_HI, (arm, label, len(text))
            if game["game_family"] in ("bargaining", "negotiation"):
                assert len(text) >= F.LEN_LO, (arm, label, len(text))


def test_no_text_on_a_phase_that_carries_none():
    """Bargaining decisions, buyer decisions and silent games take no message."""
    silent = [
        barg_game(phase="decision"),
        barg_game(messages=False),
        nego_game(messages=False),
        pers_game(phase="seller_recommendation"),
        pers_game(phase="buyer_decision"),
    ]
    for game in silent:
        family = game["game_family"]
        decide = {"bargaining": bargaining.decide, "negotiation": negotiation.decide,
                  "persuasion": persuasion.decide}[family]
        raw = decide(copy.deepcopy(game), CFG)
        plan = raw.pop("_plan", None)
        for arm in F.ARMS:
            assert F.compose(arm, game, raw, plan, random.Random(0)) is None
            assert F.eligible(arm, game, raw, plan) is False


def test_silent_arm_is_always_silent_and_still_eligible_where_text_is_legal():
    for label, game, action, plan in TURNS:
        assert F.compose("A0", game, action, plan, random.Random(0)) is None, label
        assert F.eligible("A0", game, action, plan) is F.phase_carries_message(game)


def test_missing_plan_yields_no_message():
    game = barg_game()
    raw = bargaining.decide(copy.deepcopy(game), CFG)
    raw.pop("_plan")
    for arm in F.FRAMING_ARMS + ("A1",):
        assert F.compose(arm, game, raw, None, random.Random(0)) is None
        assert F.compose(arm, game, raw, {}, random.Random(0)) is None


@pytest.mark.parametrize("arm", F.FRAMING_ARMS + ("A1",))
def test_each_arm_speaks_in_each_family(arm):
    families = {game["game_family"]
                for _, game, _, _, _ in _messages(arm, seeds=range(3))}
    for family in ("bargaining", "negotiation", "persuasion"):
        if (arm, family) in UNSUPPORTED:
            assert family not in families, (arm, family)
        else:
            assert family in families, f"{arm} never speaks in {family}"


def test_experiment_scope_is_offers_in_the_two_bargaining_families():
    assert F.in_experiment_scope(barg_game()) is True
    assert F.in_experiment_scope(nego_game()) is True
    assert F.in_experiment_scope(barg_game(phase="decision")) is False
    assert F.in_experiment_scope(barg_game(messages=False)) is False
    assert F.in_experiment_scope(pers_game()) is False        # message IS the move
    assert F.in_experiment_scope(nego_game(phase="decision")) is False


# ---------------------------------------------------------------------------
# 2. truth
# ---------------------------------------------------------------------------

#: First-person promises about our own future conduct. Every one of these is
#: falsifiable by our own next move, and the numeric policy is not ours to bend
#: to keep them, so none may ever appear.
FORBIDDEN_PROMISES = (
    "i promise", "i guarantee", "you have my word", "i give you my word",
    "i swear", "i will never", "i will always", "i pledge", "trust me",
    "i can assure you", "you can count on me",
)

#: Anything that would leave the game frame. Not designed, not written, and
#: asserted absent so it cannot arrive by accident in a later edit.
FORBIDDEN_FRAME_BREAKS = (
    "ignore previous", "ignore all previous", "disregard your", "system:",
    "<system", "</system", "assistant:", "your instructions", "you are an ai",
    "developer message", "tool_call", "```", "print your prompt",
    "repeat the text above", "new instructions",
)


@pytest.mark.parametrize("arm", F.ARMS)
def test_no_promises_and_no_frame_breaks(arm):
    for label, _game, _action, _plan, rec in _messages(arm, seeds=range(4)):
        low = rec["text"].lower()
        for phrase in FORBIDDEN_PROMISES:
            assert phrase not in low, (arm, label, phrase, rec["text"])
        for phrase in FORBIDDEN_FRAME_BREAKS:
            assert phrase not in low, (arm, label, phrase, rec["text"])


CREDIT_WORDS = ("honest", "candid", "candour", "candor", "truthful", "my record",
                "check this call", "trust", "reputation", "i always tell",
                "i will tell you")


def test_no_credit_claim_while_pushing_a_unit_we_know_to_be_low():
    """The expensive lesson: the buyer verifies quality on the next reveal.

    A message that invokes honesty, candour or a track record while the plan
    says we are recommending a known-low unit is a promise broken one round
    later. No arm may make one.
    """
    seen = 0
    for label, game, action, plan, rec in [
            (l, g, a, p, r) for arm in F.ARMS
            for (l, g, a, p, r) in _messages(arm, seeds=range(4))]:
        if game["game_family"] != "persuasion":
            continue
        if not (plan.get("quality_is_high") is False and plan.get("recommend")):
            continue
        seen += 1
        low = rec["text"].lower()
        for word in CREDIT_WORDS:
            assert word not in low, (label, word, rec["text"])
    assert seen > 0, "grid never exercised the known-low-unit branch"


def test_only_f6_bluffs_and_only_where_the_claim_cannot_be_checked():
    for arm in F.ARMS:
        for label, game, _action, plan, rec in _messages(arm, seeds=range(4)):
            if rec["claim_kind"] == "bluff":
                assert arm == "F6", (arm, label, rec["claim_id"])
                state = game["game_state"]
                if game["game_family"] == "bargaining":
                    # Our discount factor is not disclosed to them, so a claim
                    # about our patience is unverifiable rather than a lie about
                    # a visible parameter.
                    assert state.get("complete_information") is False, label
                else:
                    assert game["game_family"] == "negotiation", label
            elif rec["claim_id"] is not None:
                assert rec["claim_kind"] == "fact", (arm, label, rec["claim_id"])


def test_f6_never_fires_when_our_own_schedule_is_about_to_contradict_it():
    for label, game, _action, plan, rec in _messages("F6", seeds=range(4)):
        if game["game_family"] == "bargaining":
            rl = plan.get("rounds_left")
            assert rl is None or rl >= 4, (label, rl)
        else:
            assert plan["rounds_left"] >= 3 and plan["elapsed"] < 0.6, label


def test_f3_commitments_are_facts_the_state_actually_supports():
    """F3 never promises; it states something the rules or the plan guarantee."""
    fired = set()
    for label, game, action, plan, rec in _messages("F3", seeds=range(4)):
        cid = rec["claim_id"]
        fired.add(cid)
        if cid == "f3_terminal_round":
            assert plan["rounds_left"] == 1, label
        elif cid == "f3_last_offer":
            # We do not propose again: with two rounds left the alternation
            # gives the final proposal to the opponent.
            assert plan["rounds_left"] == 2, label
        elif cid == "f3_reservation":
            floor = plan["continuation_if_refused"]
            mine_key = "alice_gain" if game["your_player"] == "player_1" else "bob_gain"
            assert floor > 0 and floor * 0.90 <= action[mine_key] <= floor * 1.05, label
        elif cid in ("f3_nego_terminal", "f3_nego_last_offer"):
            assert plan["capped"] and plan["rounds_left"] <= 2, label
        elif cid == "f3_nego_reservation":
            price, reservation = action["product_price"], plan["reservation"]
            assert (abs(price - reservation) <= 0.02 * max(abs(reservation), 1.0)
                    or plan["elapsed"] >= 0.95), label
        elif cid == "f3_pers_terminal":
            assert plan["round"] >= plan["total_rounds"], label
        else:
            raise AssertionError(f"unknown F3 claim {cid}")
    assert {"f3_terminal_round", "f3_last_offer"} <= fired
    assert {"f3_nego_terminal", "f3_nego_last_offer"} & fired


def test_only_the_commitment_arms_fill_the_commitment_slot():
    for arm in F.ARMS:
        for label, _g, _a, _p, rec in _messages(arm, seeds=range(4)):
            if rec["commitment"]:
                assert arm in ("F3", "F5", "F6"), (arm, label)


def test_f5_never_cites_an_equilibrium_that_undercuts_our_own_ask():
    """Stating a derived number that is below our demand argues against us."""
    seen = 0
    for label, game, action, plan, rec in _messages("F5", seeds=range(4)):
        if game["game_family"] != "bargaining":
            continue
        seen += 1
        money = plan["money"]
        mine_key = "alice_gain" if game["your_player"] == "player_1" else "bob_gain"
        assert action[mine_key] / money <= plan["spe_share"] + 0.005, label
        # And where their discount factor was assumed rather than disclosed,
        # the message says so instead of asserting it as fact.
        state = game["game_state"]
        opp_key = "delta_2" if game["your_player"] == "player_1" else "delta_1"
        known = state.get(opp_key) is not None and state.get("complete_information") is not False
        if not known:
            assert "not disclosed" in rec["text"], label
    assert seen > 0


def test_present_value_claims_never_appear_in_the_final_round():
    """There is no "next round" to discount into when rounds_left is 1."""
    for arm in ("F1", "F2"):
        for label, _g, _a, plan, rec in _messages(arm, seeds=range(4)):
            if plan.get("rounds_left") == 1:
                assert rec["claim_id"] not in ("f1_pv_next_round", "f2_pv_delay",
                                               "f2_own_decay"), (arm, label)


def test_f1_last_word_only_when_the_opponent_really_proposes_last():
    for label, game, _a, plan, rec in _messages("F1", seeds=range(4)):
        if rec["claim_id"] != "f1_last_word":
            continue
        rl = plan["rounds_left"]
        assert rl is not None and rl >= 2 and rl % 2 == 0, (label, rl)
        assert f"round {game['game_state']['round'] + rl - 1}" in rec["text"]


def test_f4_states_the_concession_the_history_actually_records():
    """The ledger arm is the one that must never overstate our own movement."""
    game = barg_game(round_=5, history=BARG_HISTORY)
    raw = bargaining.decide(copy.deepcopy(game), CFG)
    plan = raw.pop("_plan")
    money = plan["money"]
    mine = raw["alice_gain"]
    # We opened at 8,000 of 10,000 in round 1 and are asking `mine` now.
    expected_points = (8_000.0 - mine) / money * 100
    hit = 0
    for seed in range(12):
        rec = F.describe("F4", game, raw, plan, random.Random(seed))
        if not rec["text"]:
            continue
        hit += 1
        assert rec["claim_id"] == "f4_concession_ledger"
        assert "80%" in rec["text"], rec["text"]
        assert f"{expected_points:.1f}".rstrip("0").rstrip(".") in rec["text"], rec["text"]
    assert hit == 12


def test_f4_stays_quiet_when_we_have_not_actually_moved():
    """No prior offer of ours, or no movement, means no concession to claim."""
    game = barg_game(round_=1)
    raw = bargaining.decide(copy.deepcopy(game), CFG)
    plan = raw.pop("_plan")
    assert F.compose("F4", game, raw, plan, random.Random(0)) is None

    flat = [{"round": 1, "proposer": "player_1",
             "offer": {"player_1_gain": 100.0, "player_2_gain": 9_900.0,
                       "proposer": "player_1"}}]
    game = barg_game(round_=3, history=flat)
    raw = bargaining.decide(copy.deepcopy(game), CFG)
    plan = raw.pop("_plan")
    assert F.compose("F4", game, raw, plan, random.Random(0)) is None


def test_persuasion_message_still_carries_the_recommendation():
    """In text mode the message IS the move, so it must parse as the plan's call."""
    checked = 0
    for label, game, action, plan, rec in [
            (l, g, a, p, r) for arm in F.ARMS
            for (l, g, a, p, r) in _messages(arm, seeds=range(4))]:
        if game["game_family"] != "persuasion":
            continue
        checked += 1
        assert reads_as_recommendation(rec["text"]) is bool(plan["recommend"]), \
            (label, plan["recommend"], rec["text"])
    assert checked > 0


def test_every_claim_leaves_room_for_the_other_slots():
    """A claim long enough to crowd out the frame would break the grammar."""
    for arm in F.FRAMING_ARMS:
        for label, _g, _a, _p, rec in _messages(arm, seeds=range(4)):
            assert len(rec["claim_text"]) <= F.LEN_HI - 45, \
                (arm, label, len(rec["claim_text"]))


def test_a1_carries_no_economic_claim():
    for _label, _g, _a, _p, rec in _messages("A1", seeds=range(4)):
        assert rec["claim_id"] is None
        assert rec["claim_kind"] is None
        assert rec["commitment"] is False


def test_length_is_balanced_between_the_neutral_control_and_every_treatment():
    """Length is a treatment-correlated feature the opponent can see."""
    lengths = {}
    for arm in ("A1",) + F.FRAMING_ARMS:
        vals = [rec["length"] for _l, g, _a, _p, rec in _messages(arm, seeds=range(4))
                if g["game_family"] in ("bargaining", "negotiation")]
        assert vals, arm
        lengths[arm] = statistics.median(vals)
    for arm in F.FRAMING_ARMS:
        assert abs(lengths[arm] - lengths["A1"]) <= 40, (arm, lengths)


# ---------------------------------------------------------------------------
# 3. variety, with the semantics held fixed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("arm", F.FRAMING_ARMS + ("A1",))
def test_surface_varies_but_the_claim_does_not(arm):
    spoke_anywhere = False
    for label, game, action, plan in TURNS:
        texts, claims = set(), set()
        for seed in range(120):
            rec = F.describe(arm, game, action, plan, random.Random(seed))
            if rec["text"] is None:
                continue
            texts.add(rec["text"])
            claims.add(rec["claim_id"])
        if not texts:
            continue
        spoke_anywhere = True
        # The arm is one treatment: the claim it makes is a function of the
        # state, never of the coin.
        assert len(claims) == 1, (arm, label, claims)
        # ...but a repeat opponent must not be able to key on a fixed string.
        assert len(texts) >= 20, (arm, label, len(texts))
    assert spoke_anywhere, arm


def test_composition_is_reproducible_for_a_given_rng_seed():
    for label, game, action, plan in TURNS:
        for arm in F.ARMS:
            a = F.compose(arm, game, action, plan, random.Random(11))
            b = F.compose(arm, game, action, plan, random.Random(11))
            assert a == b, (arm, label)


def test_default_rng_is_deterministic_per_turn():
    game = action = plan = None
    for label, g, a, p in TURNS:
        if g["game_family"] == "bargaining" and F.in_experiment_scope(g):
            game, action, plan = g, a, p
            break
    assert game is not None
    assert F.compose("F2", game, action, plan) == F.compose("F2", game, action, plan)


# ---------------------------------------------------------------------------
# 4. totality: never raises, never mutates
# ---------------------------------------------------------------------------

def test_inputs_are_never_mutated():
    for label, game, action, plan in TURNS:
        before = json.dumps([game, action, plan], sort_keys=True, default=str)
        for arm in F.ARMS:
            F.compose(arm, game, action, plan, random.Random(5))
            F.eligible(arm, game, action, plan)
        after = json.dumps([game, action, plan], sort_keys=True, default=str)
        assert before == after, label


MALFORMED = [
    None, {}, [], "not a game", 0,
    {"game_family": "bargaining"},
    {"game_family": "bargaining", "game_state": None, "valid_actions": None},
    {"game_family": "bargaining", "game_state": {}, "valid_actions": {"type": "offer"}},
    {"game_family": "bargaining", "your_player": "player_1",
     "valid_actions": {"type": "offer"},
     "game_state": {"money_to_divide": 0, "messages_allowed": True}},
    {"game_family": "bargaining", "your_player": "player_1",
     "valid_actions": {"type": "offer"},
     "game_state": {"money_to_divide": float("nan"), "messages_allowed": True,
                    "round": "x", "history": [1, 2, None, {"offer": 3}]}},
    {"game_family": "bargaining", "your_player": None,
     "valid_actions": {"type": "offer"},
     "game_state": {"money_to_divide": -5, "messages_allowed": True,
                    "history": [{"offer": {"proposer": None}}]}},
    {"game_family": "negotiation", "your_player": "player_1",
     "valid_actions": {"type": "offer"},
     "game_state": {"messages_allowed": True, "history": "nope"}},
    {"game_family": "negotiation", "your_player": "player_1",
     "valid_actions": {"type": "offer"},
     "game_state": {"messages_allowed": True, "round": float("inf"),
                    "history": [{"offer": {"price": None, "from_player": 7}}]}},
    {"game_family": "persuasion", "your_player": "player_1",
     "valid_actions": {"type": "seller_message"}, "game_state": {"history": None}},
    {"game_family": "chess", "your_player": "player_1",
     "valid_actions": {"type": "offer"}, "game_state": {"messages_allowed": True}},
    {"game_family": "bargaining", "your_player": "player_1",
     "valid_actions": "offer", "game_state": {"messages_allowed": True}},
]

MALFORMED_ACTIONS = [
    None, {}, [], "x", {"alice_gain": None, "bob_gain": None},
    {"alice_gain": "1e400", "bob_gain": float("nan")},
    {"product_price": "abc"}, {"product_price": float("-inf")},
    {"decision": "AcceptOffer"}, {"message": " "},
]

MALFORMED_PLANS = [
    None, {}, [], "x", 3,
    {"money": None, "rounds_left": "soon", "delta_me": "fast"},
    {"delta_me": float("nan"), "delta_opp": None, "spe_share": "half",
     "rounds_left": -4, "continuation_if_refused": "x"},
    {"i_am_seller": "yes", "reservation": None, "target": [], "elapsed": "late",
     "rounds_left": None, "my_value": "free"},
    {"recommend": "maybe", "quality_is_high": "sort of", "round": None,
     "total_rounds": "five"},
    {"recommend": True, "quality_is_high": False, "round": 1, "total_rounds": 3},
]


@pytest.mark.parametrize("arm", F.ARMS + ("", "nope", None, 7))
def test_never_raises_on_malformed_state(arm):
    for game in MALFORMED:
        for action in MALFORMED_ACTIONS:
            for plan in MALFORMED_PLANS:
                text = F.compose(arm, game, action, plan, random.Random(0))
                assert text is None or (isinstance(text, str)
                                        and 0 < len(text) <= F.MAX_MESSAGE_LEN)
                rec = F.describe(arm, game, action, plan, random.Random(0))
                assert isinstance(rec, dict) and "reason" in rec
                assert F.eligible(arm, game, action, plan) in (True, False)


def test_never_raises_under_a_fuzzed_grid():
    rng = random.Random(20260819)
    corruptions = ("drop", "none", "string", "nan", "negative", "huge", "unicode")
    for _ in range(400):
        label, game, action, plan = rng.choice(TURNS)
        game = copy.deepcopy(game)
        action = copy.deepcopy(action)
        plan = copy.deepcopy(plan) if isinstance(plan, dict) else plan
        for target in (game.get("game_state") or {}, action,
                       plan if isinstance(plan, dict) else {}):
            if not isinstance(target, dict) or not target:
                continue
            key = rng.choice(list(target))
            how = rng.choice(corruptions)
            if how == "drop":
                target.pop(key, None)
            elif how == "none":
                target[key] = None
            elif how == "string":
                target[key] = "not a number"
            elif how == "nan":
                target[key] = float("nan")
            elif how == "negative":
                target[key] = -abs(rng.random()) * 1e6
            elif how == "huge":
                target[key] = 1e308 * 10
            else:
                target[key] = "‮\U0001f4a3" * 3
        for arm in F.ARMS:
            text = F.compose(arm, game, action, plan, random.Random(rng.random()))
            assert text is None or (isinstance(text, str)
                                    and 0 < len(text) <= F.MAX_MESSAGE_LEN)


def test_a_broken_rng_degrades_to_silence_rather_than_an_exception():
    class Hostile:
        def choice(self, options):
            raise RuntimeError("boom")

        def shuffle(self, seq):
            raise RuntimeError("boom")

    game = barg_game()
    raw = bargaining.decide(copy.deepcopy(game), CFG)
    plan = raw.pop("_plan")
    for arm in F.ARMS:
        assert F.compose(arm, game, raw, plan, Hostile()) is None


def test_message_survives_the_agents_own_repair_layer_unchanged():
    """``coerce`` must not have to trim anything we emit."""
    from glee_agent.actions import coerce
    for label, game, action, plan in TURNS:
        if not F.in_experiment_scope(game):
            continue
        for arm in F.ARMS:
            text = F.compose(arm, game, action, plan, random.Random(1))
            if text is None:
                continue
            baseline = coerce(dict(action), game)
            candidate = dict(action)
            candidate["message"] = text
            repaired = coerce(candidate, game)
            assert repaired.get("message") == text, (arm, label)
            # The numeric fields must be byte-identical with and without the
            # message: attaching text may not move a single number.
            for key in ("alice_gain", "bob_gain", "product_price"):
                if key in baseline:
                    assert math.isclose(repaired[key], baseline[key], rel_tol=0.0,
                                        abs_tol=0.0), (arm, label, key)
            assert set(repaired) - {"message"} == set(baseline) - {"message"}
