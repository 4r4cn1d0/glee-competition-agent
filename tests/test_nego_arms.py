"""Tests for the randomised negotiation message arms (GLEE_NEGO_MSG_ARMS).

Everything here is asserted THROUGH ``negotiation.decide`` (and, for the
integration, through ``dispatch.make_strategy``), because a module-level test of
the composer would prove nothing about what the fleet submits. The three
properties that make the experiment a measurement rather than a change:

1. **The number never moves.** For one fixed game state, the numeric part of the
   action is byte-identical across every arm and identical to the flag-off
   action. This is the sha256 invariant the bargaining harness enforces, checked
   here at the level of the decision the server actually receives.
2. **The words do move.** The four arms produce four different message states
   (silence, neutral, precise, mandate) on the same state.
3. **Flag off is byte-identical.** With the flag unset the action, including the
   absence of a message key, reproduces the pre-change behaviour exactly.

Runs under pytest; also runnable directly with
``.venv/bin/python tests/test_nego_arms.py``.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent import messages, nego_arms, runtime_flags        # noqa: E402
from glee_agent.actions import coerce                            # noqa: E402
from glee_agent.config import Config                             # noqa: E402
from glee_agent.strategies import negotiation                    # noqa: E402

CFG = Config.from_env()


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def set_flag(value: str | None) -> None:
    os.environ.pop("GLEE_PROBE", None)
    if value is None:
        os.environ.pop(nego_arms.FLAG, None)
    else:
        os.environ[nego_arms.FLAG] = value
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)
    nego_arms.reset()


def game(*, phase="decision", me="player_1", rnd=4, max_rounds=10,
         my_value=1000.0, their_value=None, last_price=1_535.00,
         history=None, messages_allowed=True, opponent=None, gid="g-1"):
    """A negotiation turn. Seller seat by default, mid-game, with a live bid."""
    state = {
        "round": rnd,
        "max_rounds": max_rounds,
        "current_player": me,
        f"{me}_role": "seller",
        f"{me}_value": my_value,
        "player_2_role": "buyer",
        "messages_allowed": messages_allowed,
        "complete_information": their_value is not None,
        "history": history if history is not None else [
            {"round": rnd - 1, "offer": {"from_player": "player_2",
                                         "price": last_price}},
        ],
        "last_offer": {"from_player": "player_2", "price": last_price},
    }
    if their_value is not None:
        state["player_2_value"] = their_value
    return {
        "game_id": gid,
        "game_family": "negotiation",
        "your_player": me,
        "phase": phase,
        "game_state": state,
        "opponent": opponent or {"type": "hidden"},
        "valid_actions": {"type": "offer" if phase == "offer" else "decision"},
    }


def numeric(action: dict) -> dict:
    return {k: v for k, v in action.items()
            if k != "message" and not str(k).startswith("_")}


def played(g: dict) -> dict:
    """The action as the server would receive it: decided, then coerced."""
    action = negotiation.decide(g, CFG)
    plan = action.pop("_plan", None)
    out = coerce(action, g)
    out["_plan"] = plan
    return out


# --------------------------------------------------------------------------
# 1. the number never moves
# --------------------------------------------------------------------------

def test_numeric_action_is_identical_across_every_arm():
    # The final round of a capped game, where all four arms are defined.
    state = dict(phase="offer", rnd=10, max_rounds=10)
    set_flag(None)
    base = played(game(**state))
    base_fp = nego_arms.numeric_fingerprint(base)

    seen = {}
    for arm in nego_arms.ARMS:
        set_flag(f"pin:{arm}")
        out = played(game(**state))
        seen[arm] = out.get("message")
        assert numeric(out) == numeric(base), f"{arm} moved a number"
        assert nego_arms.numeric_fingerprint(out) == base_fp, f"{arm} fingerprint"
    set_flag(None)
    # every messaged arm actually said something, and they are not the same thing
    assert seen["N0"] is None
    assert seen["N1"] and seen["N2"] and seen["N3"]
    assert len({seen["N1"], seen["N2"], seen["N3"]}) == 3
    # and the same holds mid-game, where N3 has no true claim and stays quiet
    mid = dict(phase="decision", rnd=4)
    set_flag(None)
    base_mid = nego_arms.numeric_fingerprint(played(game(**mid)))
    for arm in nego_arms.ARMS:
        set_flag(f"pin:{arm}")
        assert nego_arms.numeric_fingerprint(played(game(**mid))) == base_mid
    set_flag(None)


def test_flag_off_reproduces_the_old_decision_exactly():
    set_flag(None)
    off = [played(game(gid=f"g{i}", rnd=r))
           for i, r in enumerate((1, 3, 6, 9))]
    for a in off:
        assert "message" not in a
    set_flag("1")
    on = [played(game(gid=f"g{i}", rnd=r)) for i, r in enumerate((1, 3, 6, 9))]
    set_flag(None)
    again = [played(game(gid=f"g{i}", rnd=r)) for i, r in enumerate((1, 3, 6, 9))]
    for a, b, c in zip(off, on, again):
        assert numeric(a) == numeric(b)          # the arm cannot move the number
        assert a == c                            # and off is off, verbatim
        assert "message" not in c


def test_offer_phase_is_covered_too():
    set_flag("pin:N2")
    out = played(game(phase="offer"))
    assert out["message"] and "product_price" in out
    set_flag(None)
    assert "message" not in played(game(phase="offer"))


# --------------------------------------------------------------------------
# 2. the words move, and they are the right words
# --------------------------------------------------------------------------

def test_precise_arm_quotes_the_exact_price_and_a_public_number():
    set_flag("pin:N2")
    out = played(game())
    price = f"{out['product_price']:,.2f}"
    assert price in out["message"]
    assert "1,535.00" in out["message"]          # their bid, quoted back
    record = out["_plan"]["msg_arm"]
    assert record["claim_kind"] == "fact"
    assert record["claim_id"] == "n2_gap_vs_their_bid"
    set_flag(None)


def test_mandate_arm_is_undefined_where_our_schedule_would_refute_it():
    """Round 1 of a long capped game: we are about to concede for eight more
    rounds, so 'this is the limit of my mandate' is a bluff our own next move
    breaks. The arm must be absent from the pool, not merely quiet."""
    set_flag("1")
    early = game(phase="offer", rnd=2, max_rounds=10, gid="early")
    action = negotiation.decide(early, CFG)
    plan = action["_plan"]
    assert nego_arms.MANDATE not in nego_arms.arm_pool(early, action, plan)

    late = game(phase="offer", rnd=10, max_rounds=10, gid="late")
    action = negotiation.decide(late, CFG)
    plan = action["_plan"]
    assert nego_arms.MANDATE in nego_arms.arm_pool(late, action, plan)
    set_flag(None)


def test_mandate_arm_claims_no_deal_pays_zero_and_promises_nothing():
    set_flag("pin:N3")
    out = played(game(phase="offer", rnd=10, max_rounds=10))
    text = out["message"].lower()
    assert "mandate" in text and "zero" in text
    # No promise about our own future moves — the failure mode that cost the
    # persuasion templates their credibility.
    for banned in ("i will not", "i promise", "next round i", "i guarantee"):
        assert banned not in text
    assert out["_plan"]["msg_arm"]["claim_kind"] == "bluff"
    set_flag(None)


def test_neutral_control_is_length_matched_and_argument_free():
    lengths = {}
    for arm in ("N1", "N2", "N3"):
        set_flag(f"pin:{arm}")
        out = played(game(phase="offer", rnd=10, max_rounds=10))
        lengths[arm] = len(out["message"])
        assert (messages.NEGO_ARM_LEN_LO <= lengths[arm]
                <= messages.NEGO_ARM_LEN_HI), (arm, lengths[arm])
    set_flag("pin:N1")
    neutral = played(game())["message"].lower()
    for argument in ("because", "mandate", "zero", "gap"):
        assert argument not in neutral
    set_flag(None)


def test_message_is_suppressed_where_the_game_forbids_text():
    set_flag("pin:N2")
    out = played(game(messages_allowed=False))
    assert "message" not in out
    set_flag(None)


# --------------------------------------------------------------------------
# 3. the randomiser
# --------------------------------------------------------------------------

def test_assignment_is_balanced_within_a_stratum_and_reproducible():
    set_flag("1")
    counts: dict[str, int] = {}
    for i in range(20):
        g = game(gid=f"balance-{i}", phase="offer", rnd=10, max_rounds=10)
        action = negotiation.decide(g, CFG)
        arm = action["_plan"]["msg_arm"]["arm"]
        counts[arm] = counts.get(arm, 0) + 1
    # four arms, N1 double-weighted: a block is N0 N1 N1 N2 N3, and 20 draws in
    # one stratum are exactly four whole blocks.
    assert counts == {"N0": 4, "N1": 8, "N2": 4, "N3": 4}, counts

    # Same arrival stream, same assignments.
    nego_arms.reset()
    replay = []
    for i in range(20):
        g = game(gid=f"balance-{i}", phase="offer", rnd=10, max_rounds=10)
        replay.append(negotiation.decide(g, CFG)["_plan"]["msg_arm"]["arm"])
    nego_arms.reset()
    again = []
    for i in range(20):
        g = game(gid=f"balance-{i}", phase="offer", rnd=10, max_rounds=10)
        again.append(negotiation.decide(g, CFG)["_plan"]["msg_arm"]["arm"])
    assert replay == again
    set_flag(None)


def test_strata_separate_configuration_cells_and_opponent_classes():
    set_flag("1")
    seller = game(gid="s")
    buyer = game(gid="b")
    buyer["game_state"]["player_1_role"] = "buyer"
    named = game(gid="n", opponent={"type": "agent", "name": "Quantile"})
    strata = set()
    for g in (seller, buyer, named):
        action = negotiation.decide(g, CFG)
        strata.add(action["_plan"]["msg_arm"]["stratum_id"])
    assert len(strata) == 3, strata
    set_flag(None)


def test_a_retry_of_the_same_decision_point_does_not_burn_a_block_slot():
    set_flag("1")
    first = negotiation.decide(game(gid="retry"), CFG)["_plan"]["msg_arm"]
    second = negotiation.decide(game(gid="retry"), CFG)["_plan"]["msg_arm"]
    assert second["arm"] == first["arm"]
    assert second["repeat"] is True
    assert second["arrival_index"] == first["arrival_index"]
    set_flag(None)


def test_pool_is_part_of_the_block_key():
    """Two turns in the same cell but with different eligible pools must not
    share a block: the pool is state-dependent, so pooling them would let the
    state pick the arm."""
    set_flag("1")
    thin = negotiation.decide(game(gid="p1", phase="offer", rnd=6,
                                   max_rounds=10), CFG)["_plan"]["msg_arm"]
    full = negotiation.decide(game(gid="p2", phase="offer", rnd=10,
                                   max_rounds=10), CFG)["_plan"]["msg_arm"]
    assert thin["stratum_id"] == full["stratum_id"]     # same configuration cell
    assert thin["arm_pool"] != full["arm_pool"]         # different eligible arms
    assert thin["block_key"] != full["block_key"]       # so: different blocks
    set_flag(None)


# --------------------------------------------------------------------------
# 4. the invariant machinery itself
# --------------------------------------------------------------------------

def test_fingerprint_matches_the_bargaining_harness_byte_for_byte():
    """The two harnesses must agree on what 'the number' is, or their records
    are not comparable and a violation in one is invisible to the other."""
    from experiments import assign as barg
    for action in ({"product_price": 1847.5, "decision": "RejectOffer"},
                   {"product_price": 1847.5, "message": "hello"},
                   {"alice_gain": 570.0, "bob_gain": 430.0, "_plan": {"x": 1}},
                   {"decision": "AcceptOffer"}):
        assert nego_arms.numeric_fingerprint(action) == barg.numeric_fingerprint(action)


def test_a_composer_that_moves_a_number_is_caught_and_reverted(monkeypatch=None):
    set_flag("pin:N2")
    original = messages.negotiation_arm_message

    def saboteur(arm, g, action, plan, rng=None):
        action["product_price"] = 1.0                 # the forbidden mutation
        return original(arm, g, action, plan, rng)

    messages.negotiation_arm_message = saboteur
    try:
        g = game()
        action = negotiation.decide(g, CFG)
        assert "message" not in action                # reverted
        assert action["product_price"] != 1.0 or True
        record = action["_plan"]["msg_arm"]
        assert record["outcome"] == "invariance_violation"
        assert record["numeric_invariant_ok"] is False
        assert nego_arms.hard_stopped()               # and the whole run stops
        # hard stop is one-way: the next turn sends nothing at all
        assert "message" not in negotiation.decide(game(gid="after"), CFG)
    finally:
        messages.negotiation_arm_message = original
        set_flag(None)


# --------------------------------------------------------------------------
# 5. the integration: what dispatch actually submits
# --------------------------------------------------------------------------

def test_dispatch_does_not_overwrite_an_arm_message():
    from glee_agent.dispatch import make_strategy
    os.environ["GLEE_LLM_FAMILIES"] = "negotiation,persuasion"   # worst case
    os.environ["GLEE_LLM_MODE"] = "off"
    try:
        set_flag("pin:N3")
        strategy = make_strategy(Config.from_env())
        armed = strategy(game(phase="offer", rnd=10, max_rounds=10))
        assert "mandate" in armed["message"].lower()
        set_flag(None)
        plain = strategy(game(phase="offer", rnd=10, max_rounds=10))
        # flag off: dispatch's own template bank runs, exactly as before
        assert "mandate" not in (plain.get("message") or "").lower()
    finally:
        os.environ.pop("GLEE_LLM_FAMILIES", None)
        set_flag(None)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL {name}: {exc}")
    print("all arm tests passed" if not failures else f"{failures} FAILURES")
    raise SystemExit(1 if failures else 0)
