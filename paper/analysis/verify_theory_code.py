#!/usr/bin/env python3
"""Executable checks for the paper's mathematical and code-alignment claims.

This script is deliberately lightweight. It does not read live state, start an
agent, replay games, or estimate a treatment effect. It checks exact algebra and
selected deterministic branches against the checked-in implementation.
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from glee_agent import (  # noqa: E402
    barg_offer,
    bargaining_p2_commitment as p2_commitment,
    first_principles,
    nego_hidden_terminal_inference,
)
from glee_agent.strategies import bargaining, persuasion  # noqa: E402
from sim import official_negotiation_seed  # noqa: E402


TOL = 1e-10


def close(left: float, right: float, tolerance: float = TOL) -> None:
    if not math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{left!r} != {right!r}")


def midrank(reference: tuple[float, ...], payoff: float) -> float:
    return sum(
        float(value < payoff) + 0.5 * float(value == payoff)
        for value in reference
    ) / len(reference)


def check_objective_results() -> None:
    """Check the rank map, mature block weights, and a finite rank reversal."""
    values = (-1.0, 0.0, 1.0)
    cutpoints = (-2.0, -1.0, 0.0, 1.0, 2.0)
    for reference in itertools.product(values, repeat=4):
        for lower, upper in itertools.combinations(cutpoints, 2):
            jump = midrank(reference, upper) - midrank(reference, lower)
            counted = (
                sum(lower < value < upper for value in reference)
                + 0.5 * sum(value == lower for value in reference)
                + 0.5 * sum(value == upper for value in reference)
            ) / len(reference)
            close(jump, counted)

    for rating in (100.0, 1000.0, 2600.0, 4999.0):
        for eta in (0.002, 0.01):
            deltas = [eta * ((2000.0 + 8000.0 * (q - 0.5)) - rating)
                      for q in (0.0, 0.2, 0.5, 0.9, 1.0)]
            assert deltas == sorted(deltas)

    # An exact empirical-CDF counterexample, rather than a smooth surrogate.
    reference = (5.0,)
    payoff_a = 10.0
    payoff_b = (0.0, 21.0)
    assert sum(payoff_b) / 2.0 > payoff_a
    rank_a = midrank(reference, payoff_a)
    rank_b = sum(midrank(reference, value) for value in payoff_b) / 2.0
    assert rank_a > rank_b
    close(rank_a, 1.0)
    close(rank_b, 0.5)

    # At the documented mature eta, the final 19/19/25-game blocks directly
    # replace only these shares of the inherited raw-rating state.
    close(100.0 * (1.0 - (1.0 - 0.002) ** 19), 3.7323690354366)
    close(100.0 * (1.0 - (1.0 - 0.002) ** 25), 4.881819928888687)


def recursive_proposer_share(delta_me: float, delta_opp: float, rounds: int) -> float:
    if rounds == 1:
        return 1.0
    return 1.0 - delta_opp * recursive_proposer_share(
        delta_opp, delta_me, rounds - 1
    )


def check_bargaining_theory() -> None:
    """Match the appendix recursion and parity result to production code."""
    for delta_me in (0.8, 0.9, 0.95, 1.0):
        for delta_opp in (0.8, 0.9, 0.95, 1.0):
            for rounds in range(1, 25):
                expected = recursive_proposer_share(delta_me, delta_opp, rounds)
                actual = bargaining.proposer_share(delta_me, delta_opp, rounds)
                close(actual, expected)

    for delta_me in (0.8, 0.9, 0.95, 1.0):
        for m in range(0, 10):
            close(
                bargaining.proposer_share(delta_me, 1.0, 2 * m + 1),
                delta_me**m,
            )
            if m >= 1:
                close(bargaining.proposer_share(delta_me, 1.0, 2 * m), 0.0)

    for delta_me, delta_opp in ((0.8, 0.9), (0.9, 0.95), (0.95, 0.8)):
        stationary = (1.0 - delta_opp) / (1.0 - delta_me * delta_opp)
        close(bargaining.proposer_share(delta_me, delta_opp, None), stationary)

    # One-period gain heuristic, including the patient boundary omitted in an
    # earlier draft. Waiting yields delta * (s + gain); accepting yields s.
    for delta in (0.5, 0.8, 0.95):
        for current in (0.01, 0.2, 0.8):
            for gain in (0.001, 0.05, 0.2):
                wait_margin = delta * (current + gain) - current
                threshold_margin = delta * gain / (1.0 - delta) - current
                if math.isclose(wait_margin, 0.0, abs_tol=TOL):
                    assert math.isclose(threshold_margin, 0.0, abs_tol=TOL)
                else:
                    assert (wait_margin > 0.0) == (threshold_margin > 0.0)
    for current in (0.01, 0.2, 0.8):
        for gain in (0.001, 0.05, 0.2):
            assert current + gain > current

    # The fitted bargaining CDF bucket is a deliberate coarsening of the
    # official configuration. It retains only pot, cap, horizon observability,
    # and information observability. Role, both discounts, and message mode do
    # not enter the key, and an absent bucket uses the fully pooled CDF.
    key = barg_offer.cell_key(100.0, 12, True, True)
    assert key.split("|") == ["100.0", "12", "True", "True"]
    retained_keys = {
        barg_offer.cell_key(money, horizon, horizon_known, complete)
        for money in (100.0, 10_000.0)
        for horizon in (1, 12)
        for horizon_known in (False, True)
        for complete in (False, True)
    }
    assert len(retained_keys) == 16
    omitted_dimension_keys = {
        barg_offer.cell_key(100.0, 12, True, True)
        for _role in ("alice", "bob")
        for _delta_me in (0.8, 1.0)
        for _delta_opp in (0.8, 1.0)
        for _messages_allowed in (False, True)
    }
    assert omitted_dimension_keys == {key}
    exact_knots = [0.1, 0.5, 0.9]
    pooled_knots = [0.0, 0.5, 1.0]
    assert barg_offer._cdf(
        {"cdf": {key: exact_knots}, "cdf_pooled": pooled_knots}, key
    ) is exact_knots
    assert barg_offer._cdf(
        {"cdf": {}, "cdf_pooled": pooled_knots}, key
    ) is pooled_knots


def p2_game(round_no: int, action_type: str, bob_gain: float = 0.0) -> dict:
    money = 100.0
    proposer = "player_2" if action_type == "offer" else "player_1"
    state = {
        "phase": action_type,
        "current_player": "player_2",
        "proposer": proposer,
        "round": round_no,
        "max_rounds": 12,
        "horizon_known": True,
        "money_to_divide": money,
        "delta_2": 0.95,
        "messages_allowed": False,
        "last_offer": None,
    }
    if action_type == "decision":
        state["last_offer"] = {
            "player_1_gain": money - bob_gain,
            "player_2_gain": bob_gain,
            "proposer": "player_1",
            "round": round_no,
        }
    return {
        "game_family": "bargaining",
        "phase": action_type,
        "your_player": "player_2",
        "valid_actions": {"type": action_type},
        "game_state": state,
    }


def check_banked_p2_owner() -> None:
    """Check the banked silent P2 ladder, floor decisions, and turn parity."""
    enabled = lambda flag: flag == p2_commitment.D095_SILENT_FLAG
    with patch.object(p2_commitment.runtime_flags, "enabled", side_effect=enabled):
        for round_no, share in p2_commitment.SILENT_SHARES.items():
            action = p2_commitment.action(p2_game(round_no, "offer"))
            assert action is not None
            close(float(action["bob_gain"]), 100.0 * share)

        terminal = p2_commitment.action(p2_game(12, "offer"))
        assert terminal is not None
        close(float(terminal["alice_gain"]), 0.01)
        close(float(terminal["bob_gain"]), 99.99)

        floor = (100.0 - 0.01) * 0.95**11
        for round_no in (1, 3, 5, 7, 9, 11):
            required = floor / 0.95 ** (round_no - 1)
            reject = p2_commitment.action(
                p2_game(round_no, "decision", required - 0.001)
            )
            accept = p2_commitment.action(
                p2_game(round_no, "decision", required)
            )
            assert reject is not None and reject["decision"] == "reject"
            assert accept is not None and accept["decision"] == "accept"

        # Bob proposes on even round 12. A terminal Bob decision is unreachable.
        assert not p2_commitment.eligible_for_flag(
            p2_game(12, "decision", 0.01), p2_commitment.D095_SILENT_FLAG
        )


def negotiation_offer_game(
    *,
    round_no: int,
    max_rounds: int,
    complete: bool,
    seller_value: float,
    buyer_value: float,
    player: str,
    history: list[dict] | None = None,
) -> dict:
    state = {
        "phase": "offer",
        "current_player": player,
        "round": round_no,
        "max_rounds": max_rounds,
        "horizon_known": True,
        "complete_information": complete,
        "player_1_role": "seller",
        "player_2_role": "buyer",
        "player_1_value": seller_value if complete or player == "player_1" else None,
        "player_2_value": buyer_value if complete or player == "player_2" else None,
        "history": history or [],
        "last_offer": None,
    }
    return {
        "game_family": "negotiation",
        "your_player": player,
        "phase": "offer",
        "valid_actions": {"type": "offer"},
        "game_state": state,
    }


def hidden_seller_seed_score(
    cost_mult: float,
    target_mult: float,
    *,
    bases: tuple[float, ...],
    message_modes: tuple[bool, ...],
) -> float:
    """Average exact seed midrank over declared latent and visible support."""
    scores = []
    for base in bases:
        seller_value = cost_mult * base
        ask = target_mult * base - first_principles.EPS
        for messages_allowed in message_modes:
            state = {
                "horizon_known": True,
                "max_rounds": 1,
                "complete_information": False,
                "messages_allowed": messages_allowed,
            }
            for buyer_mult in official_negotiation_seed.VALUE_MULTS:
                buyer_value = buyer_mult * base
                payoff = ask - seller_value if buyer_value > ask else 0.0
                score = official_negotiation_seed.percentile(
                    state,
                    "player_1",
                    payoff,
                    seller_value=seller_value,
                    buyer_value=buyer_value,
                )
                assert score is not None
                scores.append(score)
    expected_count = (
        len(bases)
        * len(message_modes)
        * len(official_negotiation_seed.VALUE_MULTS)
    )
    assert len(scores) == expected_count
    return sum(scores) / len(scores)


def check_negotiation_owners() -> None:
    """Check the exact first-principles cells and hidden terminal bound owner."""
    seller_terminal = negotiation_offer_game(
        round_no=1,
        max_rounds=1,
        complete=True,
        seller_value=80.0,
        buyer_value=100.0,
        player="player_1",
    )
    assert first_principles.deterministic_eligible(seller_terminal)
    close(float(first_principles.action(seller_terminal)["product_price"]), 99.99)

    buyer_terminal = negotiation_offer_game(
        round_no=10,
        max_rounds=10,
        complete=True,
        seller_value=80.0,
        buyer_value=100.0,
        player="player_2",
    )
    assert first_principles.deterministic_eligible(buyer_terminal)
    close(float(first_principles.action(buyer_terminal)["product_price"]), 80.01)

    hidden_single_seller = negotiation_offer_game(
        round_no=1,
        max_rounds=1,
        complete=False,
        seller_value=80.0,
        buyer_value=100.0,
        player="player_1",
    )
    assert first_principles.deterministic_eligible(hidden_single_seller)
    close(
        float(first_principles.action(hidden_single_seller)["product_price"]),
        119.99,
    )

    history = [
        {
            "round": 1,
            "offer": {"from_player": "player_1", "price": 119.0, "round": 1},
        }
    ]
    hidden_cap10_buyer = negotiation_offer_game(
        round_no=10,
        max_rounds=10,
        complete=False,
        seller_value=80.0,
        buyer_value=150.0,
        player="player_2",
        history=history,
    )
    inferred = nego_hidden_terminal_inference.action(hidden_cap10_buyer)
    assert inferred is not None
    close(float(inferred["product_price"]), 100.01)

    # The hard-coded hidden one-round seller bank ignores visible message mode
    # and monetary scale. Its declared construction therefore averages the
    # exact seed CDF over all four latent buyer values, both message modes, and
    # all three supported bases. Each candidate evaluation contains 24 full
    # configuration cells, rather than one fixed latent-value cell.
    value_mults = tuple(value / 100.0 for value in first_principles.GRID)
    assert value_mults == official_negotiation_seed.VALUE_MULTS
    bases = tuple(100.0 * scale for scale in first_principles.SCALES)
    assert bases == (100.0, 10_000.0, 1_000_000.0)
    message_modes = (False, True)
    expected_scores = {
        (0.8, 1.0): 0.27178055991671385,
        (0.8, 1.2): 0.37712776513441976,
        (0.8, 1.5): 0.3594569717717026,
        (1.0, 1.2): 0.28218332289055975,
        (1.0, 1.5): 0.2506265664160401,
        (1.2, 1.5): 0.24618861269553194,
    }
    for (cost_mult, target_mult), expected in expected_scores.items():
        actual = hidden_seller_seed_score(
            cost_mult,
            target_mult,
            bases=bases,
            message_modes=message_modes,
        )
        close(actual, expected)

    bank_targets = {0.8: 1.2, 1.0: 1.2, 1.2: 1.5}
    for cost_mult, bank_target in bank_targets.items():
        candidates = tuple(
            target for target in value_mults if target > cost_mult
        )
        best_target = max(
            candidates,
            key=lambda target: hidden_seller_seed_score(
                cost_mult,
                target,
                bases=bases,
                message_modes=message_modes,
            ),
        )
        close(best_target, bank_target)
        for base in bases:
            expected_ask = bank_target * base - first_principles.EPS
            close(first_principles.rank_grid_ask(cost_mult * base), expected_ask)

    for base in bases:
        close(first_principles.rank_grid_ask(1.5 * base), 2.0 * base)

    # The pooled .8-cost optimum is not the optimum in every fixed visible
    # cell. This guards the manuscript against reverting to that stronger claim.
    no_message_small = {
        target: hidden_seller_seed_score(
            0.8,
            target,
            bases=(100.0,),
            message_modes=(False,),
        )
        for target in (1.2, 1.5)
    }
    assert no_message_small[1.5] > no_message_small[1.2]
    message_small = {
        target: hidden_seller_seed_score(
            0.8,
            target,
            bases=(100.0,),
            message_modes=(True,),
        )
        for target in (1.2, 1.5)
    }
    assert message_small[1.2] > message_small[1.5]


def manual_uniform_q_posterior(history: list[dict], p: float) -> list[float]:
    q_grid = persuasion._Q_GRID
    epsilon = persuasion._EPS
    weights = [1.0] * len(q_grid)
    for entry in history:
        rec = persuasion._recommended(entry)
        quality = str(entry.get("quality", "")).lower()
        for index, q in enumerate(q_grid):
            if entry.get("bought") and quality in ("high", "low"):
                if quality == "high":
                    likelihood = p * ((1.0 - epsilon) if rec else epsilon)
                else:
                    likelihood = (1.0 - p) * (q if rec else (1.0 - q))
            else:
                pr_yes = p * (1.0 - epsilon) + (1.0 - p) * q
                likelihood = pr_yes if rec else (1.0 - pr_yes)
            weights[index] *= max(likelihood, 1e-12)
    total = sum(weights)
    return [weight / total for weight in weights]


def seller_game(
    *, p: float, v: float | None, u: float | None, history: list[dict]
) -> dict:
    return {
        "game_family": "persuasion",
        "your_player": "player_1",
        "valid_actions": {"type": "seller_recommendation"},
        "game_state": {
            "phase": "seller_recommendation",
            "current_player": "player_1",
            "round": len(history) + 1,
            "total_rounds": 20,
            "product_price": 1.0,
            "p": p,
            "v": v,
            "u": u,
            "current_quality": "low",
            "history": history,
        },
    }


def check_persuasion_theory_and_policy() -> None:
    """Check the obedience threshold, q-grid update, and banked seller rules."""
    for p, v, u, price in (
        (0.5, 2.0, 0.0, 1.0),
        (0.33, 4.0, 0.0, 1.0),
        (0.8, 1.25, 0.0, 1.0),
    ):
        formula = p * (v - price) / ((1.0 - p) * (price - u))
        expected = min(max(formula, 0.0), 1.0)
        close(persuasion.optimal_lie_rate(p, v, u, price), expected)

    history = [
        {"bought": True, "quality": "low", "seller_message": "yes"},
        {"bought": True, "quality": "high", "seller_message": "yes"},
        {"bought": False, "seller_message": "no"},
    ]
    with patch.object(persuasion, "_buyer_prior_doc", return_value=None):
        actual = persuasion._q_posterior(history, 0.5, "text")
    expected = manual_uniform_q_posterior(history, 0.5)
    for left, right in zip(actual, expected):
        close(left, right)

    config = SimpleNamespace(pers_lie_shading=1.0, pers_honest_rounds=0)
    float_flags = {
        "GLEE_PERS_HONEST_ROUNDS": 99.0,
        "GLEE_PERS_LIE_SHADING": 0.0,
        "GLEE_PERS_BACKLOAD_AB": 0.0,
    }
    as_float = lambda name, default=0.0: float_flags.get(name, default)
    with (
        patch.object(persuasion.runtime_flags, "enabled", return_value=False),
        patch.object(persuasion.runtime_flags, "as_float", side_effect=as_float),
    ):
        weakly_profitable = persuasion._seller_plan_baseline(
            seller_game(p=0.8, v=1.25, u=0.0, history=[]), config
        )
        below_price = persuasion._seller_plan_baseline(
            seller_game(p=0.5, v=1.2, u=0.0, history=[]), config
        )
        unknown_active = persuasion._seller_plan_baseline(
            seller_game(p=0.5, v=None, u=None, history=[]), config
        )
        unknown_stalled = persuasion._seller_plan_baseline(
            seller_game(
                p=0.5,
                v=None,
                u=None,
                history=[
                    {"bought": True},
                    {"bought": False},
                    {"bought": False},
                ],
            ),
            config,
        )

    assert weakly_profitable["recommend"] is True
    assert below_price["recommend"] is False
    assert unknown_active["recommend"] is True
    assert unknown_stalled["recommend"] is False


def main() -> None:
    checks = (
        ("objective algebra and finite empirical rank reversal", check_objective_results),
        ("bargaining recursion and parity", check_bargaining_theory),
        ("banked P2 bargaining owner", check_banked_p2_owner),
        ("negotiation structural owners", check_negotiation_owners),
        ("persuasion threshold, posterior, and seller policy", check_persuasion_theory_and_policy),
    )
    for label, check in checks:
        check()
        print(f"PASS: {label}")
    print(f"PASS: {len(checks)} verification groups")


if __name__ == "__main__":
    main()
