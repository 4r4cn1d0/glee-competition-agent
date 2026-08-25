#!/usr/bin/env python3
"""Pre-deployment reachability check for a candidate flag.

Answers, BEFORE a 3,000-game arena run or a live deploy, the three questions a
"clean +0.0000 null" cannot: did the gate's preconditions ever hold, did the
gate actually fire, and did firing ever change a submitted action? Each of the
known traps this repo has already paid for shows up as a specific zero here:

  * a flag nested under a gate the control omits (the GLEE_BARG_STONEWALL /
    ACCEPT_FLOOR screen) -> the flag is never even consulted: eligible = 0;
  * a flag the probe transform overwrites (GLEE_BARG_SPE_WEIGHT under the
    composite probe, which replaces barg_spe_weight with the hardliner's 1.0)
    -> consulted state exists but nothing moves: action_changed = 0;
  * a typo'd or nonexistent flag -> all three are 0.

Method: draw N paired games with sim.replay_eval's own field/census machinery,
play them once under the CONTROL arm to bank every game-state our seat was
handed (states are engine-produced, so the record echo and the synthetic
planning clock are exactly as the live strategy sees them -- nothing is
reconstructed by hand), then push each banked state through the family's
decide() twice: control flags vs control + candidate. GLEE_TRACE_GATES=1 is
set on BOTH arms so each plan carries plan["gates_fired"], the ordered list of
gates that changed the pending target/decision that turn.

    .venv/bin/python scripts/check_reachability.py --flag GLEE_NEGO_ULTIMATUM_SHARE=0.80
    .venv/bin/python scripts/check_reachability.py --flag GLEE_BARG_SPE_WEIGHT=1.0
    .venv/bin/python scripts/check_reachability.py --flag GLEE_PERS_P08_R125_PROSE_AB=1 --control-slot composite
    .venv/bin/python scripts/check_reachability.py --flag GLEE_NEGO_NO_SUCH=1

Exit status is 0 only when eligible_count, fired_count and action_changed_count
are ALL positive. A nonzero exit means the candidate as configured cannot be
arena-tested meaningfully: fix the control nesting / flag name first.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from sim import replay_eval  # noqa: E402

TRACE_FLAG = "GLEE_TRACE_GATES"

#: flag -> (family, gate names in plan["gates_fired"], precondition predicate).
#: The predicate runs on (game, control_plan) and says whether the gate's
#: preconditions held in that state regardless of whether the gate is armed.
#: Gate names may be empty for pure value knobs that have no gate of their own
#: (their reachability is judged on consultation + action movement alone).
def _p_ultimatum(game, p):
    return (p.get("zopa") is not None and p.get("capped")
            and p.get("rounds_left", 99) <= 1)


def _p_final_hidden(game, p):
    return (p.get("their_value") is None and p.get("capped")
            and p.get("rounds_left", 99) <= 1)


def _p_rank_price(game, p):
    return (game.get("valid_actions", {}).get("type") == "offer"
            and p.get("capped") and p.get("rounds_left", 99) <= 1)


def _p_span(game, p):
    return (p.get("zopa") is not None and p.get("rounds_left", 0) >= 2
            and game.get("valid_actions", {}).get("type") == "decision")


def _p_offer(game, p):
    return game.get("valid_actions", {}).get("type") == "offer"


def _p_decision(game, p):
    return game.get("valid_actions", {}).get("type") == "decision"


def _p_complete_price(game, p):
    state = game.get("game_state") or {}
    return (state.get("complete_information") is True
            and state.get("player_1_value") is not None
            and state.get("player_2_value") is not None
            and game.get("valid_actions", {}).get("type") in ("offer", "decision"))


def _p_complete_ultimatum(game, p):
    state = game.get("game_state") or {}
    return (_p_complete_price(game, p)
            and game.get("valid_actions", {}).get("type") == "offer"
            and state.get("max_rounds") == 1)


def _p_deterministic_first_principles(game, p):
    """Structural scope of the non-randomized negotiation component."""
    from glee_agent import first_principles

    return first_principles.deterministic_eligible(game)


def _p_agent5_default(game, p):
    return (game.get("game_family") == "negotiation"
            and (game.get("valid_actions") or {}).get("type")
            in ("offer", "decision"))


def _p_barg_p2_h12_d095_silent(game, p):
    """Exact structural scope of Bob's disclosed-H12 silent ladder."""
    from glee_agent import bargaining_p2_commitment

    return bargaining_p2_commitment.eligible_for_flag(
        game, bargaining_p2_commitment.D095_SILENT_FLAG)


def _p_barg_p2_h12_d095_message(game, p):
    """Exact structural scope of Bob's truthful message commitment."""
    from glee_agent import bargaining_p2_commitment

    return bargaining_p2_commitment.eligible_for_flag(
        game, bargaining_p2_commitment.D095_MSG_FLAG)


def _p_barg_p2_h12_d100(game, p):
    """Exact structural scope of Bob's patient all-but-one-cent policy."""
    from glee_agent import bargaining_p2_commitment

    return bargaining_p2_commitment.eligible_for_flag(
        game, bargaining_p2_commitment.D100_FLAG)


def _p_open_claim(game, p):
    from glee_agent.actions import (
        _complete_negotiation_zopa,
        _is_negotiation_opening,
    )

    zopa = _complete_negotiation_zopa(game)
    return (zopa is not None
            and game.get("game_id")
            and game.get("valid_actions", {}).get("type") in ("offer", "decision")
            and _is_negotiation_opening(game))


def _p_hidden_floor(game, p):
    from glee_agent.actions import _num
    from glee_agent.pricing import infer_base

    state = game.get("game_state") or {}
    seat = game.get("your_player") or state.get("current_player")
    return (state.get("complete_information") is False
            and state.get(f"{seat}_role") in ("seller", "buyer")
            and infer_base(_num(state.get(f"{seat}_value"))) is not None
            and bool(game.get("game_id"))
            and game.get("valid_actions", {}).get("type") in ("offer", "decision"))


def _p_hidden_policy(game, p):
    """Whether the new own-grid policy can replace an outgoing hidden price."""
    from glee_agent.actions import _num
    from glee_agent.pricing import infer_base

    if not _p_hidden_floor(game, p):
        return False
    state = game.get("game_state") or {}
    max_rounds = state.get("max_rounds")
    if max_rounds is not None and _num(max_rounds, -1.0) == 1.0:
        return False
    seat = game.get("your_player") or state.get("current_player")
    role = state.get(f"{seat}_role")
    own_value = _num(state.get(f"{seat}_value"))
    base = infer_base(own_value)
    if base is None:
        return False
    own_mult = next(
        (m for m in (0.8, 1.0, 1.2, 1.5)
         if abs(own_value / base - m) <= 1e-6),
        None,
    )
    return (own_mult is not None
            and (own_mult < 1.5 if role == "seller" else own_mult > 0.8))


def _p_hi_cap10_buyer12_terminal(game, p):
    """Static scope of the round-9 buyer counter postcondition."""
    from glee_agent.actions import _num
    from glee_agent.pricing import infer_base

    state = game.get("game_state") or {}
    seat = game.get("your_player") or state.get("current_player")
    own_value = _num(state.get(f"{seat}_value"), float("nan"))
    base = infer_base(own_value)
    return (state.get("complete_information") is False
            and state.get("horizon_known") is True
            and _num(state.get("max_rounds"), -1.0) == 10.0
            and _num(state.get("round"), -1.0) == 9.0
            and state.get(f"{seat}_role") == "buyer"
            and base is not None
            and abs(own_value / base - 1.2) <= 1e-6
            and bool(game.get("game_id"))
            and game.get("valid_actions", {}).get("type") == "decision")


def _p_hi_cap10_buyer_curve(game, p):
    """Static scope of the broad hidden cap-10 buyer curve postcondition."""
    from glee_agent.actions import _num
    from glee_agent.pricing import infer_base

    state = game.get("game_state") or {}
    seat = game.get("your_player") or state.get("current_player")
    own_value = _num(state.get(f"{seat}_value"), float("nan"))
    base = infer_base(own_value)
    if base is None:
        return False
    own_mult = next(
        (mult for mult in (0.8, 1.0, 1.2, 1.5)
         if abs(own_value / base - mult) <= 1e-6),
        None,
    )
    return (state.get("complete_information") is False
            and state.get("horizon_known") is True
            and _num(state.get("max_rounds"), -1.0) == 10.0
            and state.get(f"{seat}_role") == "buyer"
            and own_mult in (1.0, 1.2, 1.5)
            and bool(game.get("game_id"))
            and game.get("valid_actions", {}).get("type") == "decision")


def _p_top_buyer_clone(game, p):
    """Static scope of the full observed-leader buyer treatment."""
    from glee_agent.top_buyer_clone import eligible
    return eligible(game)


def _p_top_buyer_clone_hi_cap10(game, p):
    """Static scope of the prospective hidden cap-10 leader clone."""
    from glee_agent.top_buyer_clone_hi_cap10 import eligible
    return eligible(game)


def _p_top_opus_buyer_clone(game, p):
    """Static scope of the partial direct-Opus buyer treatment."""
    from glee_agent.top_opus_buyer_clone import eligible
    return eligible(game)


def _p_hi_uncapped_first_offer(game, p):
    """Static scope of the hidden unknown-horizon first-offer probe."""
    from glee_agent.actions import _hidden_own_price_count, _num
    from glee_agent.pricing import infer_base

    state = game.get("game_state") or {}
    seat = game.get("your_player") or state.get("current_player")
    role = state.get(f"{seat}_role")
    own_value = _num(state.get(f"{seat}_value"), float("nan"))
    base = infer_base(own_value)
    if base is None:
        return False
    own_mult = next(
        (mult for mult in (0.8, 1.0, 1.2, 1.5)
         if abs(own_value / base - mult) <= 1e-6),
        None,
    )
    identified = ((role, own_mult) in (("seller", 1.2), ("buyer", 1.0)))
    return (state.get("complete_information") is False
            and state.get("horizon_known") is False
            and state.get("max_rounds") is None
            and role in ("seller", "buyer")
            and identified
            and bool(game.get("game_id"))
            and seat in ("player_1", "player_2")
            and _hidden_own_price_count(state, seat) == 0
            and game.get("valid_actions", {}).get("type")
            in ("offer", "decision"))


def _p_hi_uncapped_extreme_open(game, p):
    """Static scope of the disjoint direct-leader opening probe."""
    from glee_agent.actions import _hidden_own_price_count, _num
    from glee_agent.pricing import infer_base

    state = game.get("game_state") or {}
    seat = game.get("your_player") or state.get("current_player")
    role = state.get(f"{seat}_role")
    own_value = _num(state.get(f"{seat}_value"), float("nan"))
    base = infer_base(own_value)
    if base is None:
        return False
    own_mult = next(
        (mult for mult in (0.8, 1.0, 1.2, 1.5)
         if abs(own_value / base - mult) <= 1e-6),
        None,
    )
    nonunique_viable = ((role == "seller" and own_mult in (0.8, 1.0))
                        or (role == "buyer" and own_mult in (1.2, 1.5)))
    return (state.get("complete_information") is False
            and state.get("horizon_known") is False
            and state.get("max_rounds") is None
            and nonunique_viable
            and bool(game.get("game_id"))
            and seat in ("player_1", "player_2")
            and _hidden_own_price_count(state, seat) == 0
            and game.get("valid_actions", {}).get("type")
            in ("offer", "decision"))


def _p_barg_midgame_decision(game, p):
    return _p_decision(game, p) and p.get("rounds_left", 0) > 2


def _p_bob_offer(game, p):
    return (_p_offer(game, p) and not p.get("me_is_alice", True)
            and p.get("rounds_left", 0) > 2)


def _p_barg_message(game, p):
    return (_p_offer(game, p)
            and (game.get("game_state") or {}).get("messages_allowed") is True)


def _p_barg_no_regress(game, p):
    return (_p_decision(game, p) and p.get("rounds_left", 0) > 1
            and p.get("money", 0) > 0)


def _p_barg_discount_no_regress(game, p):
    signal = p.get("discount_no_regress") or {}
    return bool(signal.get("eligible"))


def _p_barg_high_share_delay(game, p):
    signal = p.get("high_share_delay_guard") or {}
    return bool(signal.get("eligible"))


def _p_barg_accept_floor_exact(game, p):
    signal = p.get("accept_floor_exact_v1") or {}
    return bool(signal.get("eligible"))


def _p_p08_r125_prose(game, p):
    """Action-level scope of the exact p=.8/r=1.25 seller wording gate."""
    state = game.get("game_state") or {}
    try:
        price = float(state.get("product_price"))
        ratio = float(state.get("v")) / price
        prior = float(state.get("p"))
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    return ((game.get("valid_actions") or {}).get("type") == "seller_message"
            and state.get("seller_message_type") == "text"
            and state.get("v") is not None
            and abs(prior - 0.8) <= 1e-9
            and abs(ratio - 1.25) <= 1e-9
            and p.get("recommend") is True)


def _p_pers_p08_positive_prose_v1(game, p):
    """Action-level scope of deterministic p=.8 positive seller prose."""
    state = game.get("game_state") or {}
    try:
        prior = float(state.get("p"))
    except (TypeError, ValueError):
        return False
    return ((game.get("valid_actions") or {}).get("type") == "seller_message"
            and game.get("your_player") == "player_1"
            and state.get("seller_message_type") == "text"
            and abs(prior - 0.8) <= 1e-9
            and p.get("recommend") is True)


def _p_pers_zero_margin_truth_v1(game, p):
    """Changed-action scope of deterministic exact-prior equality truth."""
    state = game.get("game_state") or {}
    try:
        price = float(state.get("product_price"))
        prior = float(state.get("p"))
        high_value = float(state.get("v"))
        low_value = float(state.get("u"))
    except (TypeError, ValueError):
        return False
    prior_value = prior * high_value + (1.0 - prior) * low_value
    scale = max(1.0, abs(price), abs(prior_value))
    return ((game.get("valid_actions") or {}).get("type")
            in ("seller_message", "seller_recommendation")
            and game.get("your_player") == "player_1"
            and str(state.get("current_quality") or "").lower() == "low"
            and price > 0.0
            and math.isfinite(prior_value)
            and abs(prior_value - price) <= 1e-9 * scale
            and p.get("recommend") is True)


def _p_p08_r125_binary_truth(game, p):
    """Changed-action scope of the exact p=.8/r=1.25 binary truth gate."""
    state = game.get("game_state") or {}
    try:
        price = float(state.get("product_price"))
        ratio = float(state.get("v")) / price
        prior = float(state.get("p"))
        low_value = float(state.get("u"))
        rounds = int(state.get("total_rounds"))
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    return ((game.get("valid_actions") or {}).get("type")
            == "seller_recommendation"
            and state.get("seller_message_type") == "binary"
            and state.get("v") is not None
            and ("is_seller_know_cv" not in state
                 or state.get("is_seller_know_cv") is True)
            and str(state.get("current_quality") or "").lower() == "low"
            and abs(prior - 0.8) <= 1e-9
            and abs(ratio - 1.25) <= 1e-9
            and abs(low_value) <= 1e-9
            and rounds == 20)


def _p_p08_r125_text_decline_veto(game, p):
    """Pre-action scope of the exact buyer/text decline-veto experiment."""
    state = game.get("game_state") or {}
    seat = game.get("your_player")
    try:
        price = float(state.get("product_price"))
        ratio = float(state.get("v")) / price
        prior = float(state.get("p"))
        low_value = float(state.get("u"))
        rounds = int(state.get("total_rounds"))
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    return ((game.get("valid_actions") or {}).get("type") == "buyer_decision"
            and seat == "player_2"
            and state.get("seller_message_type") == "text"
            and abs(prior - 0.8) <= 1e-9
            and abs(ratio - 1.25) <= 1e-9
            and abs(low_value) <= 1e-9
            and rounds == 20)


def _p_p05_r12_selectivity_unlock(game, p):
    """Structural scope of the exact buyer selectivity-unlock experiment."""
    state = game.get("game_state") or {}
    seat = game.get("your_player")
    try:
        price = float(state.get("product_price"))
        ratio = float(state.get("v")) / price
        prior = float(state.get("p"))
        low_value = float(state.get("u"))
        rounds = float(state.get("total_rounds"))
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    return ((game.get("valid_actions") or {}).get("type") == "buyer_decision"
            and seat == "player_2"
            and state.get("seller_message_type") in ("text", "binary")
            and abs(prior - 0.5) <= 1e-9
            and abs(ratio - 1.2) <= 1e-9
            and abs(low_value) <= 1e-9 * max(1.0, abs(price))
            and abs(rounds - 20.0) <= 20e-9)


def _p_p033_r4_binary_postdecline_pulse(game, p):
    """Pre-action scope where the exact buyer pulse can change a control buy."""
    state = game.get("game_state") or {}
    seat = game.get("your_player")
    try:
        price = float(state.get("product_price"))
        ratio = float(state.get("v")) / price
        prior = float(state.get("p"))
        low_value = float(state.get("u"))
        rounds = float(state.get("total_rounds"))
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    structural = (
            all(math.isfinite(value)
                for value in (price, ratio, prior, low_value, rounds))
            and price > 0.0
            and (game.get("valid_actions") or {}).get("type") == "buyer_decision"
            and seat == "player_2"
            and (state.get("current_player") is None
                 or state.get("current_player") == "player_2")
            and state.get("seller_message_type") == "binary"
            and (state.get("player_2_role") is None
                 or state.get("player_2_role") == "buyer")
            and abs(prior - (1.0 / 3.0)) <= 1e-9
            and abs(ratio - 4.0) <= 1e-9
            and abs(low_value) <= 1e-9 * max(1.0, abs(price))
            and abs(rounds - 20.0) <= 20e-9
            and p.get("buy") is True
            and p.get("buyer_v2") is True
            and p.get("tight") is False
            and p.get("blocked") is False)
    if not structural:
        return False

    def strict(entry):
        message = entry.get("seller_message")
        if isinstance(message, bool):
            return message
        if isinstance(message, str):
            token = message.strip().lower()
            if token == "yes":
                return True
            if token == "no":
                return False
        if message is None and isinstance(entry.get("recommended"), bool):
            return entry.get("recommended")
        return None

    if strict({"seller_message": state.get("seller_message")}) is not True:
        return False
    seen_decline = False
    highs = lows = last_pulsed_lows = 0
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        signal = strict(entry)
        due = (signal is True and seen_decline and lows >= 3
               and 3 * highs - lows <= 0 and lows > last_pulsed_lows)
        if due:
            last_pulsed_lows = lows
            if entry.get("bought") is True:
                return False
        elif signal is True and seen_decline and entry.get("bought") is True:
            quality = str(entry.get("quality") or "").strip().lower()
            if quality == "high":
                highs += 1
            elif quality == "low":
                lows += 1
            else:
                return False
        if signal is False:
            seen_decline = True
    return (seen_decline and lows >= 3 and 3 * highs - lows <= 0
            and lows > last_pulsed_lows)


def _p_buyer_explicit_decline_veto_v1(game, p):
    """Pre-action scope where the deterministic buyer veto can change BUY."""
    from glee_agent.strategies import persuasion
    from glee_agent.text import reads_as_recommendation_expanded

    state = game.get("game_state") or {}
    if ((game.get("valid_actions") or {}).get("type") != "buyer_decision"
            or game.get("your_player") != "player_2"
            or (state.get("current_player") is not None
                and state.get("current_player") != "player_2")
            or p.get("buyer_v2") is not True
            or p.get("buy") is not True):
        return False

    mode = state.get("seller_message_type")
    if mode == "text":
        return reads_as_recommendation_expanded(
            state.get("seller_message")) is False
    if mode == "binary":
        return persuasion._strict_binary_signal({
            "seller_message": state.get("seller_message"),
            "recommended": state.get("recommended"),
        }) is False
    return False


def _p_buyer_explicit_decline_v2(game, p):
    """Pre-action scope where strict current-text V2 can change BUY."""
    from glee_agent.strategies import persuasion

    state = game.get("game_state") or {}
    return ((game.get("valid_actions") or {}).get("type") == "buyer_decision"
            and game.get("your_player") == "player_2"
            and state.get("current_player") in (None, "player_2")
            and state.get("seller_message_type") == "text"
            and p.get("buyer_v2") is True
            and p.get("buy") is True
            and persuasion._explicit_current_text_decline_v2(
                state.get("seller_message")))


def _p_stall_current_break(game, p):
    """Pre-action scope of the current-offer stale-stall treatment."""
    if game.get("game_family") != "negotiation":
        return False
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player")
    if (game.get("valid_actions") or {}).get("type") != "decision":
        return False
    from glee_agent.strategies import negotiation
    stale = negotiation._their_stall_price(state, me)
    metadata = p.get("stall_current_break") or {}
    return (stale is not None
            and negotiation._current_concession_break(state, me, stale)
            is not None
            and metadata.get("eligible") is True)


def _p_hidden_min_share_veto(game, p):
    """Pre-action scope where the current stack would accept a low-share offer."""
    if game.get("game_family") != "negotiation":
        return False
    if (game.get("valid_actions") or {}).get("type") != "decision":
        return False
    metadata = p.get("hidden_min_share_veto") or {}
    return (metadata.get("eligible") is True
            and metadata.get("control_acceptor") in (
                "table_accept", "stall_accept", "continuation_accept"))


def _p_table_vcont_precedence(game, p):
    """Pre-action direct-TABLE scope with identified improving-price evidence."""
    if game.get("game_family") != "negotiation":
        return False
    if (game.get("valid_actions") or {}).get("type") != "decision":
        return False
    metadata = p.get("table_vcont_precedence") or {}
    return (metadata.get("eligible") is True
            and metadata.get("distinct_opponent_prices", 0) >= 3
            and metadata.get("continuation_value", 0.0)
            > metadata.get("surplus_now", 0.0))


def _p_complete_unknown_late_stasis(game, p):
    """Candidate-plan scope of the deterministic late mutual-stasis guard."""
    if game.get("game_family") != "negotiation":
        return False
    state = game.get("game_state") or {}
    metadata = p.get("complete_unknown_late_stasis_v1") or {}
    return (state.get("complete_information") is True
            and state.get("horizon_known") is False
            and state.get("max_rounds") is None
            and (game.get("valid_actions") or {}).get("type") == "decision"
            and metadata.get("eligible") is True
            and metadata.get("cycles", 0) >= 10)


KNOWN = {
    "GLEE_NEGO_ZOPA_CLAMP": ("negotiation", (), _p_complete_price),
    "GLEE_NEGO_ULT_FLOOR": ("negotiation", (), _p_complete_ultimatum),
    "GLEE_NEGO_ULT_CAP": ("negotiation", (), _p_complete_ultimatum),
    "GLEE_NEGO_OPEN_CLAIM": ("negotiation", (), _p_open_claim),
    "GLEE_NEGO_CLAIM_FLOOR": ("negotiation", (), _p_complete_price),
    "GLEE_NEGO_HIDDEN_FLOOR": ("negotiation", (), _p_hidden_floor),
    "GLEE_NEGO_HIDDEN_POLICY_V1": ("negotiation", (), _p_hidden_policy),
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB": (
        "negotiation", (), _p_hi_cap10_buyer12_terminal),
    "GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB": (
        "negotiation", (), _p_hi_cap10_buyer_curve),
    "GLEE_NEGO_TOP_BUYER_CLONE_AB": (
        "negotiation", (), _p_top_buyer_clone),
    "GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB": (
        "negotiation", (), _p_top_buyer_clone_hi_cap10),
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB": (
        "negotiation", (), _p_top_opus_buyer_clone),
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB": (
        "negotiation", (), _p_hi_uncapped_first_offer),
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB": (
        "negotiation", (), _p_hi_uncapped_extreme_open),
    "GLEE_NEGO_ULTIMATUM_SHARE": ("negotiation", ("ultimatum",), _p_ultimatum),
    "GLEE_NEGO_RANK_PRICE_AB": ("negotiation", ("rank_price",), _p_rank_price),
    "GLEE_NEGO_POSTERIOR": ("negotiation", ("posterior",), _p_final_hidden),
    "GLEE_NEGO_CURVE_PRICING": ("negotiation", ("curve_final",), _p_final_hidden),
    "GLEE_NEGO_ACCEPT_SPAN": ("negotiation", ("span_veto",), _p_span),
    "GLEE_NEGO_RECIP_DAMP": ("negotiation", ("recip_damp",), lambda g, p: True),
    "GLEE_NEGO_DEADGAME_V1": ("negotiation", ("deadgame", "deadgame_walk"),
                              lambda g, p: p.get("opponent_bound") is not None),
    "GLEE_NEGO_STALL_POLICY": ("negotiation", ("stall_park", "stall_accept"),
                               lambda g, p: True),
    "GLEE_NEGO_STALL_CURRENT_BREAK_AB": (
        "negotiation", ("stall_current_break",), _p_stall_current_break),
    "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB": (
        "negotiation", ("hidden_min_share_veto",), _p_hidden_min_share_veto),
    "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB": (
        "negotiation", ("table_vcont_precedence",),
        _p_table_vcont_precedence),
    "GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1": (
        "negotiation", ("complete_unknown_late_stasis_v1",),
        _p_complete_unknown_late_stasis),
    "GLEE_NEGO_DETERMINISTIC_FP_V1": (
        "negotiation", ("deterministic_first_principles_v1",),
        _p_deterministic_first_principles),
    "GLEE_NEGO_AGENT5_DEFAULT_V1": (
        "negotiation", ("agent5_default_v1",), _p_agent5_default),
    "GLEE_NEGO_AGENT5_DEFAULT_V2": (
        "negotiation", ("agent5_default_v2",), _p_agent5_default),
    "GLEE_NEGO_TABLE": ("negotiation", ("table", "table_accept"),
                        lambda g, p: p.get("their_value") is None),
    "GLEE_NEGO_PROBE_V1": ("negotiation", ("probe_hold", "time_driven"),
                           lambda g, p: True),
    "GLEE_NEGO_SPLIT_CANDIDATE": ("negotiation", ("split",), lambda g, p: True),
    "GLEE_BARG_ACCEPT_FLOOR": ("bargaining", ("accept_floor",),
                               _p_barg_midgame_decision),
    "GLEE_BARG_FLOOR_GAIN": ("bargaining", ("floor_gain",),
                             _p_barg_midgame_decision),
    "GLEE_BARG_STONEWALL": ("bargaining", ("stonewall_release",
                                           "stonewall_extortion"),
                            _p_barg_midgame_decision),
    "GLEE_BARG_STONEWALL_MIN": ("bargaining", ("stonewall_extortion",),
                                _p_barg_midgame_decision),
    "GLEE_BARG_BOB_OFFER": ("bargaining", ("bob_offer",), _p_bob_offer),
    "GLEE_BARG_NO_REGRESS": ("bargaining", ("no_regress",),
                             _p_barg_no_regress),
    "GLEE_BARG_DISCOUNT_NO_REGRESS_AB": (
        "bargaining", ("discount_no_regress",),
        _p_barg_discount_no_regress),
    "GLEE_BARG_DISCOUNT_NO_REGRESS": (
        "bargaining", ("discount_no_regress",),
        _p_barg_discount_no_regress),
    "GLEE_BARG_HIGH_SHARE_DELAY_GUARD": (
        "bargaining", ("high_share_delay_guard",),
        _p_barg_high_share_delay),
    "GLEE_BARG_ACCEPT_FLOOR_EXACT_V1": (
        "bargaining", ("accept_floor_exact_v1",),
        _p_barg_accept_floor_exact),
    "GLEE_BARG_P2_H12_D095_SILENT_V1": (
        "bargaining", ("barg_p2_h12_d095_silent_v1",),
        _p_barg_p2_h12_d095_silent),
    "GLEE_BARG_P2_H12_D095_MSG_COMMIT_V1": (
        "bargaining", ("barg_p2_h12_d095_msg_commit_v1",),
        _p_barg_p2_h12_d095_message),
    "GLEE_BARG_P2_H12_D100_COMMIT_V1": (
        "bargaining", ("barg_p2_h12_d100_commit_v1",),
        _p_barg_p2_h12_d100),
    # Test 4's custom randomized probe bypasses STRATEGIES.  This default-off
    # router is the prerequisite that makes bargaining gates reachable there.
    "GLEE_PROBE_RANDOMIZED_BARG_BASE": (
        "bargaining", (), lambda g, p: True),
    "GLEE_BARG_MSG": ("bargaining", ("barg_msg",), _p_barg_message),
    "GLEE_BARG_OPPONENT_FLOOR": ("bargaining", ("opp_floor",), _p_offer),
    "GLEE_OPP_EXPLOIT": ("bargaining", ("opp_exploit",), lambda g, p: True),
    "GLEE_PERS_P08_R125_PROSE_AB": (
        "persuasion", ("p08_r125_prose",), _p_p08_r125_prose),
    "GLEE_PERS_P08_R125_BINARY_TRUTH_AB": (
        "persuasion", ("p08_r125_binary_truth",),
        _p_p08_r125_binary_truth),
    "GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB": (
        "persuasion", ("p08_r125_text_decline_veto",),
        _p_p08_r125_text_decline_veto),
    "GLEE_PERS_P05_R12_SELECTIVITY_UNLOCK_AB": (
        "persuasion", ("p05_r12_selectivity_unlock",),
        _p_p05_r12_selectivity_unlock),
    "GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB": (
        "persuasion", ("p033_r4_binary_postdecline_pulse",),
        _p_p033_r4_binary_postdecline_pulse),
    "GLEE_PERS_BUYER_EXPLICIT_DECLINE_VETO_V1": (
        "persuasion", ("buyer_explicit_decline_veto_v1",),
        _p_buyer_explicit_decline_veto_v1),
    "GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2": (
        "persuasion", ("buyer_explicit_decline_v2",),
        _p_buyer_explicit_decline_v2),
    "GLEE_PERS_ZERO_MARGIN_TRUTH_V1": (
        "persuasion", ("pers_zero_margin_truth_v1",),
        _p_pers_zero_margin_truth_v1),
    "GLEE_PERS_P08_POSITIVE_PROSE_V1": (
        "persuasion", ("pers_p08_positive_prose_v1",),
        _p_pers_p08_positive_prose_v1),
    # Pure value knobs read through Config.from_env — no gate of their own.
    # NOTE: the composite probe transform (glee_agent/probes.py) OVERWRITES
    # barg_spe_weight, barg_uncapped_horizon and both nego anchors, so those
    # env flags are inert under the live composite: this checker reports that
    # as action_changed = 0.
    "GLEE_BARG_SPE_WEIGHT": ("bargaining", (), _p_offer),
    "GLEE_BARG_UNKNOWN_DELTA": ("bargaining", (), lambda g, p: True),
    "GLEE_NEGO_SELLER_ANCHOR": ("negotiation", (), lambda g, p: True),
    "GLEE_NEGO_BUYER_ANCHOR": ("negotiation", (), lambda g, p: True),
}

# These flags execute after the strategy plan is removed, in actions.coerce().
# Their firing evidence is consultation plus a changed final numeric action,
# rather than a name in plan["gates_fired"].
POSTCONDITION_FLAGS = {
    "GLEE_NEGO_ZOPA_CLAMP", "GLEE_NEGO_ULT_FLOOR", "GLEE_NEGO_ULT_CAP",
    "GLEE_NEGO_OPEN_CLAIM", "GLEE_NEGO_CLAIM_FLOOR",
    "GLEE_NEGO_OPEN_CLAIM_ALWAYS",
    "GLEE_NEGO_HIDDEN_FLOOR", "GLEE_NEGO_HIDDEN_POLICY_V1",
    "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB",
    "GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB",
    "GLEE_NEGO_TOP_BUYER_CLONE_AB",
    "GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB",
    "GLEE_NEGO_TOP_OPUS_BUYER_CLONE_AB",
    "GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB",
    "GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB",
    "GLEE_NEGO_FIRST_PRINCIPLES",
    "GLEE_PROBE_RANDOMIZED_BARG_BASE",
}

#: names consulted by runtime_flags.get during the current decide() call
_CONSULTED: set[str] = set()


def _install_flag_spy() -> None:
    from glee_agent import runtime_flags
    orig = runtime_flags.get

    def spy(name: str):
        _CONSULTED.add(name)
        return orig(name)

    runtime_flags.get = spy


def _collect_states(field, draws, flags, families, target_flag=None,
                    probe_name="composite"):
    """Play the control arm once, banking a deep copy of every state our seat
    was handed (both offer and decision phases), in the wanted families.

    The named probe must match replay.  In particular, Test 4's randomized
    policy produces a different bargaining state distribution from composite;
    generating with one and replaying with the other is not exact-stack
    reachability even when the final paired action comparison is valid.
    """
    from sim import Config as SimConfig
    from sim.arena import play

    replay_eval._set_flags(flags)
    from glee_agent.config import Config
    from glee_agent.probes import make_probe
    strategy, _ = make_probe(probe_name, Config.from_env(), seed=20260824)
    banked: list[dict] = []
    wanted = set(families)

    def recorder(game: dict) -> dict:
        strategy_game = game
        if game.get("game_family") in wanted:
            banked_game = copy.deepcopy(game)
            if (target_flag ==
                    "GLEE_NEGO_HI_UNKNOWN_BUYER_WALK_ACCEPT_V1"):
                # Live negotiation history echoes the enclosing round inside
                # each ``offer`` object.  The local engine currently omits that
                # redundant field, which prevents the copied production policy
                # from counting repeated price utterances and reaching its
                # observed round-17 walk. Restore the live wire shape only in
                # this reachability bank; engine play itself is unchanged.
                history = (banked_game.get("game_state") or {}).get("history")
                for entry in history if isinstance(history, list) else ():
                    if not isinstance(entry, dict):
                        continue
                    offer = entry.get("offer")
                    if (isinstance(offer, dict) and "round" not in offer
                            and entry.get("round") is not None):
                        offer["round"] = entry["round"]
                    counter = entry.get("counteroffer")
                    if (isinstance(counter, dict)
                            and isinstance(counter.get("price"), (int, float))):
                        # The live API emits this echo as the bare numeric
                        # counter price; leaving the simulator's wrapper dict
                        # would count every buyer utterance twice.
                        entry["counteroffer"] = counter["price"]
                strategy_game = banked_game
            banked.append(banked_game)
        return strategy(strategy_game)

    for family, params, seat, game_seed in draws:
        grng = random.Random(game_seed)
        if family == "persuasion":
            from sim.opponents import get
            if seat == "player_1":
                opponent = get("trust_tracking_buyer")
            else:
                # Buyer gates need a seller that reaches both positive and
                # measured V2-only negative text.  The registered honest seller
                # says "would not recommend", which the legacy control already
                # parses correctly and therefore cannot prove a final decline
                # veto changes wire behavior.  This local reachability opponent
                # emits the authenticated failure phrase without changing the
                # arena or production opponent model.
                honest = get("honest_seller")

                if (target_flag ==
                        "GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB"):
                    # The ordinary honest seller never produces the exact
                    # post-decline false-positive stream this guard needs.  A
                    # quality-independent first `no` followed by `yes` gives
                    # engine-revealed bought outcomes enough support to prove
                    # eligible>0, fired>0 and action_changed>0 without changing
                    # any arena or live opponent implementation.
                    def bait_then_spam_seller(game):
                        state = game.get("game_state") or {}
                        action_type = (game.get("valid_actions") or {}).get("type")
                        try:
                            round_no = int(float(state.get("round") or 1))
                        except (TypeError, ValueError):
                            round_no = 1
                        positive = round_no > 1
                        if action_type == "seller_message":
                            return {"message": "yes" if positive else "no"}
                        if action_type == "seller_recommendation":
                            return {"decision": "yes" if positive else "no"}
                        return honest(game)

                    bait_then_spam_seller.name = "bait_then_spam_seller"
                    opponent = bait_then_spam_seller
                    # Skip the decline-phrase fixture below.
                    exact_decline_fixture = False
                else:
                    exact_decline_fixture = True

                def exact_decline_seller(game):
                    state = game.get("game_state") or {}
                    quality = str(state.get("current_quality") or "").lower()
                    action_type = (game.get("valid_actions") or {}).get("type")
                    if action_type == "seller_message":
                        if quality == "high":
                            message = "Recommended."
                        elif (target_flag ==
                              "GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2"):
                            # The ordinary exact-decline fixture is owned by
                            # V1.  V2 needs a real direct-current decline whose
                            # future-positive wording cancels to parser-neutral
                            # under the exact live control stack.
                            message = ("Sit this round out; the next product "
                                       "may be worth it.")
                        else:
                            message = "Not recommended."
                        return {"message": message}
                    if action_type == "seller_recommendation":
                        return {"decision": "yes" if quality == "high" else "no"}
                    return honest(game)

                exact_decline_seller.name = "exact_decline_seller"
                if exact_decline_fixture:
                    opponent = exact_decline_seller
        else:
            opponent = field.sample_opponent(random.Random(game_seed + 1))
            if (target_flag == "GLEE_BARG_ACCEPT_FLOOR_EXACT_V1"
                    and family == "bargaining"):
                # Ordinary field draws need not land exactly on the decimal
                # 20%/45% wire atoms. This reachability-only opponent repeats
                # the exact economic boundary and rejects our counters, giving
                # the real local engine enough turns to expose the production
                # float comparison. It changes neither the arena field nor any
                # production opponent implementation.
                field_opponent = opponent

                def exact_floor_opponent(game):
                    state = game.get("game_state") or {}
                    action_type = (game.get("valid_actions") or {}).get("type")
                    if action_type == "decision":
                        return {"decision": "reject"}
                    if action_type != "offer":
                        return field_opponent(game)
                    mover = game.get("your_player") or state.get("current_player")
                    receiver = "player_2" if mover == "player_1" else "player_1"
                    delta_key = "delta_1" if receiver == "player_1" else "delta_2"
                    try:
                        money = float(state.get("money_to_divide"))
                    except (TypeError, ValueError):
                        return field_opponent(game)
                    try:
                        delta = float(state.get(delta_key))
                    except (TypeError, ValueError):
                        delta = None
                    if delta in (0.8, 0.9):
                        share = 0.20 if delta == 0.8 else 0.45
                    else:
                        # Hidden information correctly omits the receiver's
                        # discount from this opponent's observation. Alternate
                        # the two public wire atoms rather than smuggling that
                        # hidden value into the fixture; every d=.8/.9 receiver
                        # is offered its own exact boundary on alternating turns.
                        round_no = int(float(state.get("round") or 1))
                        offer_index = (round_no + 1) // 2
                        share = 0.20 if offer_index % 2 else 0.45
                    if share is None or not math.isfinite(money) or money <= 0.0:
                        return field_opponent(game)
                    receiver_gain = share * money
                    if receiver == "player_1":
                        return {"alice_gain": receiver_gain,
                                "bob_gain": money - receiver_gain}
                    return {"alice_gain": money - receiver_gain,
                            "bob_gain": receiver_gain}

                exact_floor_opponent.name = "exact_floor_opponent"
                opponent = exact_floor_opponent
            if (target_flag ==
                    "GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1"
                    and family == "negotiation"
                    and params.get("complete_information") is True
                    and params.get("horizon_known") is False):
                # Ordinary field clones often close before round 75, so a zero
                # here would test opponent sampling rather than gate reach. This
                # reachability-only opponent holds a strictly feasible low-share
                # offer in the same local engine (including record echoes and the
                # real synthetic unknown-horizon clock). It changes neither the
                # arena opponent pool nor production behavior.
                field_opponent = opponent

                def exact_mutual_stasis_opponent(game):
                    state = game.get("game_state") or {}
                    action_type = (game.get("valid_actions") or {}).get("type")
                    me = state.get("current_player") or game.get("your_player")
                    role = state.get(f"{me}_role")
                    try:
                        seller = float(state.get("player_1_value"))
                        buyer = float(state.get("player_2_value"))
                    except (TypeError, ValueError):
                        return field_opponent(game)
                    span = buyer - seller
                    if not math.isfinite(span) or span <= 0.0:
                        return field_opponent(game)
                    # Give the recorder 25% of the visible span, below its live
                    # .48 accept fence, in either role.
                    price = seller + (0.75 if role == "seller" else 0.25) * span
                    if action_type == "offer":
                        return {"product_price": price}
                    if action_type == "decision":
                        return {"decision": "RejectOffer",
                                "product_price": price}
                    return field_opponent(game)

                exact_mutual_stasis_opponent.name = "exact_mutual_stasis"
                opponent = exact_mutual_stasis_opponent
            if (target_flag ==
                    "GLEE_NEGO_HI_UNKNOWN_BUYER_WALK_ACCEPT_V1"
                    and family == "negotiation"
                    and params.get("complete_information") is False
                    and params.get("horizon_known") is False
                    and isinstance(params.get("messages_allowed"), bool)):
                # Ordinary field clones closed every one of 12,000 sampled
                # games before exposing the copied policy's eight-price walk.
                # Hold the same 1.455B ask seen in two complete live examples
                # and reject counters so the local engine supplies canonical
                # history/offer echoes through round 17.  The seller derives B
                # from only its own visible value; no hidden buyer value leaks
                # into the fixture.  For buyer=1.5B and seller<=1.2B the offer
                # is profitable for both parties, exactly the repaired state.
                field_opponent = opponent

                def exact_profitable_walk_opponent(game):
                    from glee_agent.pricing import infer_base

                    state = game.get("game_state") or {}
                    action_type = (game.get("valid_actions") or {}).get("type")
                    me = state.get("current_player") or game.get("your_player")
                    if state.get(f"{me}_role") != "seller":
                        return field_opponent(game)
                    try:
                        own_value = float(state.get(f"{me}_value"))
                    except (TypeError, ValueError):
                        return field_opponent(game)
                    base = infer_base(own_value)
                    if base is None:
                        return field_opponent(game)
                    price = max(own_value + 0.01, 1.455 * base)
                    if action_type == "offer":
                        return {"product_price": price}
                    if action_type == "decision":
                        return {"decision": "RejectOffer",
                                "product_price": price}
                    return field_opponent(game)

                exact_profitable_walk_opponent.name = "exact_profitable_walk"
                opponent = exact_profitable_walk_opponent
        params = dict(params)
        if opponent.name != "__field__":
            params["opponent_name"] = opponent.name
            params["disclose_opponent"] = random.Random(game_seed + 2).random() < 0.5
        s1, s2 = (recorder, opponent) if seat == "player_1" else (opponent, recorder)
        # A stable distinct id gives per-game hash arms both treatment bits while
        # keeping the banked control state paired with both direct replays.  The
        # old implicit id was the literal "local", so a salted arm assigned every
        # banked state to one bit and could report a false zero-reachability null.
        gid = f"sim-{game_seed:08x}"
        play(SimConfig(family, dict(params)), s1, s2, grng, game_id=gid)
    return banked


def _replay(states, flags, probe_name="composite"):
    """Run decide() directly on every banked state under this flag set.

    Direct decide() (not the dispatch wrapper) so the returned action still
    carries _plan — dispatch pops it before submission. The cfg goes through
    the SAME composite probe transform the arena and the live fleet use, which
    is exactly what makes transform-overwritten flags visibly inert here.
    """
    replay_eval._set_flags(flags)
    from glee_agent.config import Config
    from glee_agent.actions import coerce
    from glee_agent.dispatch import STRATEGIES
    from glee_agent.probes import make_probe

    class _ReplayLog:
        """Capture the plan dispatch logs before custom wrappers discard it."""

        plan = None

        def turn(self, game, action, plan, source):
            self.plan = copy.deepcopy(plan)

    replay_log = _ReplayLog()
    strategy, cfg = make_probe(
        probe_name, Config.from_env(), log=replay_log, seed=20260824)
    from glee_agent.probes import PROBES
    custom_probe = PROBES[probe_name][1] is not None
    out = []
    for game in states:
        _CONSULTED.clear()
        if custom_probe:
            # Custom probes bypass STRATEGIES entirely in production. Running
            # their wrapped callable here is what exposes an otherwise false
            # positive where a flag fires only under the composite heuristic.
            # A flagged router may deliberately re-enter dispatch, whose plan
            # is removed from the returned wire action but retained in the live
            # turn log; capture it through the same logger interface so nested
            # gate reachability remains auditable.
            replay_log.plan = None
            action = strategy(copy.deepcopy(game))
            plan = replay_log.plan
        else:
            action = STRATEGIES[game["game_family"]](copy.deepcopy(game), cfg)
            plan = action.pop("_plan", None) if isinstance(action, dict) else None
        # Final-action guards run here in production, after strategy planning.
        # Replaying through coerce makes action_changed describe the wire action.
        action = coerce(action, game)
        out.append((action, plan if isinstance(plan, dict) else {},
                    frozenset(_CONSULTED)))
    return out


_NUMERIC_KEYS = ("product_price", "alice_gain", "bob_gain")


def _action_differs(a: dict, b: dict) -> bool:
    if (a.get("decision") or None) != (b.get("decision") or None):
        return True
    if (a.get("message") or None) != (b.get("message") or None):
        return True
    for k in _NUMERIC_KEYS:
        va, vb = a.get(k), b.get(k)
        if (va is None) != (vb is None):
            return True
        if va is not None and abs(float(va) - float(vb)) > 1e-9:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--flag", required=True, metavar="NAME=VALUE",
                    help="candidate flag, e.g. GLEE_NEGO_ULTIMATUM_SHARE=0.80")
    ap.add_argument("--family", default=None,
                    choices=("negotiation", "bargaining", "persuasion"),
                    help="restrict to one family (default: inferred from the "
                         "flag prefix, else both)")
    ap.add_argument("--n", type=int, default=800, help="games to draw")
    ap.add_argument("--seed", type=int, default=20260821)
    default_control = json.dumps(replay_eval.DEFAULT_CONTROL)
    ap.add_argument("--control", default=default_control,
                    help="JSON control flag dict (default: simulator snapshot; "
                         "pass the target's current stack before deployment)")
    ap.add_argument("--control-slot", default=None,
                    help="read the exact named slot stack from arms.json; this "
                         "overrides --control")
    ap.add_argument("--probe-name", default=None,
                    choices=("champion", "composite", "hardliner", "conceder",
                             "randomized"),
                    help="probe wrapper to replay (default: --control-slot, or "
                         "composite for a JSON control); use this when adding a "
                         "prospective routing flag to a live-slot JSON stack")
    args = ap.parse_args()

    if "=" not in args.flag:
        print(f"--flag must be NAME=VALUE, got {args.flag!r}")
        return 2
    name, value = args.flag.split("=", 1)
    name = name.strip()

    known = KNOWN.get(name)
    if args.family:
        families = [args.family]
    elif known:
        families = [known[0]]
    elif name.startswith("GLEE_NEGO"):
        families = ["negotiation"]
    elif name.startswith("GLEE_BARG"):
        families = ["bargaining"]
    elif name.startswith("GLEE_PERS"):
        families = ["persuasion"]
    else:
        families = ["bargaining", "negotiation"]

    if args.control_slot:
        arms_path = os.path.join(REPO, "arms.json")
        with open(arms_path, encoding="utf-8") as handle:
            arms = json.load(handle)
        if args.control_slot not in arms:
            print(f"unknown --control-slot {args.control_slot!r}; available: "
                  f"{', '.join(sorted(arms))}")
            return 2
        control = dict(arms[args.control_slot])
        print(f"using exact live stack for slot {args.control_slot!r}")
    else:
        control = dict(json.loads(args.control))
    if not args.control_slot and args.control == default_control:
        print("warning: using replay_eval.DEFAULT_CONTROL, which is a simulator "
              "snapshot; pass the actual target fleet stack with --control "
              "before treating this as deployment evidence.")
    control[TRACE_FLAG] = "1"
    candidate = dict(control)
    candidate[name] = value
    if control.get(name) == candidate[name]:
        print(f"note: control already carries {name}={value!r}; the two arms "
              "are identical and action_changed can only be 0.")

    _install_flag_spy()

    if families == ["persuasion"]:
        from sim import sample_config
        rng = random.Random(args.seed)
        draws = []
        for _ in range(args.n):
            config = sample_config("persuasion", rng)
            seat = "player_1" if rng.getrandbits(1) else "player_2"
            draws.append(("persuasion", config.params, seat,
                          rng.randrange(2 ** 31)))
        field = None
    else:
        from sim.field_data import Field
        field = Field()
        draws = replay_eval._draw_games(field, families, args.n, args.seed)
    probe_name = args.probe_name or args.control_slot or "composite"
    print(f"flag      : {name}={value}")
    print(f"families  : {', '.join(families)}")
    print(f"collecting states from {len(draws)} control-arm games...")
    states = _collect_states(
        field, draws, control, families, target_flag=name,
        probe_name=probe_name)
    print(f"banked {len(states)} decision points; replaying twice "
          "(control vs control+candidate)...")

    ctl = _replay(states, control, probe_name=probe_name)
    cnd = _replay(states, candidate, probe_name=probe_name)

    gate_names = set(known[1]) if known else set()
    eligible = fired = changed = wrong_direction = 0
    examples: list[str] = []
    for game, (a_ctl, p_ctl, _), (a_cnd, p_cnd, consulted) in zip(states, ctl, cnd):
        g_ctl = p_ctl.get("gates_fired") or []
        g_cnd = p_cnd.get("gates_fired") or []

        if known:
            try:
                # This treatment records its pre-action directional eligibility
                # only while the candidate flag is consulted. Its hash-control
                # games record the same metadata, so p_cnd is still an exact,
                # assignment-independent eligibility check.
                predicate_plan = (p_cnd if name in (
                                  "GLEE_NEGO_STALL_CURRENT_BREAK_AB",
                                  "GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB",
                                  "GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB",
                                  "GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1",
                                  "GLEE_BARG_DISCOUNT_NO_REGRESS_AB",
                                  "GLEE_BARG_DISCOUNT_NO_REGRESS",
                                  "GLEE_BARG_HIGH_SHARE_DELAY_GUARD",
                                  "GLEE_BARG_ACCEPT_FLOOR_EXACT_V1")
                                  else p_ctl)
                ok = bool(known[2](game, predicate_plan))
            except Exception:
                ok = False
        else:
            # Unknown flag: eligibility = the code actually read it. A flag
            # nested under a gate the control omits, or a nonexistent flag,
            # is never consulted and lands at 0 here.
            ok = name in consulted
        if ok:
            eligible += 1

        if name in POSTCONDITION_FLAGS:
            hit = name in consulted and _action_differs(a_ctl, a_cnd)
        elif gate_names:
            hit = any(g in g_cnd for g in gate_names)
        else:
            # No gate of its own: count states where arming the flag changed
            # WHICH gates fired (an indirect trace of reaching new code).
            hit = g_cnd != g_ctl
        if hit:
            fired += 1

        if _action_differs(a_ctl, a_cnd):
            changed += 1
            if name == "GLEE_NEGO_STALL_CURRENT_BREAK_AB":
                st = game.get("game_state") or {}
                me = st.get("current_player") or game.get("your_player")
                role = st.get(f"{me}_role")
                ctl_price = a_ctl.get("product_price")
                cnd_price = a_cnd.get("product_price")
                directional = (
                    a_ctl.get("decision") == a_cnd.get("decision")
                    and ctl_price is not None
                    and cnd_price is not None
                    and ((role == "seller" and cnd_price > ctl_price)
                         or (role == "buyer" and cnd_price < ctl_price))
                )
                wrong_direction += int(not directional)
            if len(examples) < 3:
                st = game.get("game_state") or {}
                examples.append(
                    f"    e.g. {game.get('game_family')}/"
                    f"{game.get('valid_actions', {}).get('type')}"
                    f" r{st.get('round')}: {a_ctl} -> {a_cnd}"
                    f" gates={g_cnd}")

    print()
    print(f"  eligible_count       {eligible:6d}   "
          "(states where the gate's preconditions held)")
    if name in POSTCONDITION_FLAGS:
        fired_basis = "final-action postcondition consulted and changed wire action"
    else:
        fired_basis = (f"gate {sorted(gate_names) if gate_names else '<trace diff>'} "
                       "in plan['gates_fired']")
    print(f"  fired_count          {fired:6d}   ({fired_basis})")
    print(f"  action_changed_count {changed:6d}   "
          "(submitted actions differ between the two arms)")
    if name == "GLEE_NEGO_STALL_CURRENT_BREAK_AB":
        print(f"  wrong_direction_count{wrong_direction:6d}   "
              "(candidate wire is not strictly more favorable for our role)")
    for line in examples:
        print(line)

    failures = [label for label, v in
                (("eligible", eligible), ("fired", fired),
                 ("action_changed", changed)) if v <= 0]
    if failures:
        print(f"\nFAIL: {', '.join(failures)} = 0 -- the candidate as "
              "configured is not reachable/effective; do not arena-test or "
              "deploy it until this passes.")
        if eligible == 0:
            print("  hint: never consulted -> wrong name, or nested under a "
                  "gate this control leaves off (the STONEWALL/ACCEPT_FLOOR "
                  "trap).")
        elif changed == 0:
            print("  hint: consulted but inert -> check the probe transform "
                  "(glee_agent/probes.py overwrites several cfg knobs) and "
                  "whether another gate overrides it downstream.")
        return 1
    if wrong_direction:
        print(f"\nFAIL: {wrong_direction} stale-break action(s) moved the wire "
              "against our role; do not deploy it until this is zero.")
        return 1
    print("\nPASS: the candidate is reachable, fires, and moves real actions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
