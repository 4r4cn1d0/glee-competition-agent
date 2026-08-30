#!/usr/bin/env python3
"""Verify disclosed mathematical identities and synthetic policy behavior."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from policy import reference_policy as policy  # noqa: E402


def close(actual: object, expected: object, tolerance: float = 1e-9) -> bool:
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and math.isclose(
            float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance
        )
    if isinstance(expected, list):
        return isinstance(actual, (list, tuple)) and len(actual) == len(expected) and all(
            close(a, e, tolerance) for a, e in zip(actual, expected)
        )
    return actual == expected


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_vectors() -> int:
    path = ROOT / "policy" / "synthetic_test_vectors.json"
    vectors = json.loads(path.read_text(encoding="utf-8"))
    for vector in vectors:
        function = getattr(policy, vector["function"])
        actual = function(**vector["kwargs"])
        require(close(actual, vector["expected"]), f"synthetic vector failed: {vector['name']}")
    return len(vectors)


def run_identities() -> int:
    checks = 0

    safe_payoff = 10.0
    risky_payoffs = (0.0, 21.0)
    safe_rank = policy.empirical_midrank((5.0,), safe_payoff)
    risky_rank = sum(policy.empirical_midrank((5.0,), value) for value in risky_payoffs) / 2.0
    require(sum(risky_payoffs) / 2.0 > safe_payoff, "payoff reversal premise failed")
    require(risky_rank < safe_rank, "rank reversal conclusion failed")
    checks += 2

    low_update = policy.raw_rating_update(2500.0, 0.4)
    high_update = policy.raw_rating_update(2500.0, 0.6)
    require(high_update > low_update, "rating update must increase with adjusted percentile")
    require(policy.game_rating(0.5) == 2000.0, "median game rating target failed")
    checks += 2

    require(math.isclose(policy.final_block_weight(19), 0.037323690354366), "19-game weight")
    require(math.isclose(policy.final_block_weight(25), 0.048818199288886865), "25-game weight")
    checks += 2

    clock_grid = {0.8: 14, 0.9: 29, 0.95: 59, 1.0: 60}
    for discount, expected in clock_grid.items():
        require(policy.effective_bargaining_clock(discount) == expected, f"clock grid {discount}")
    checks += len(clock_grid)

    require(math.isclose(policy.finite_proposer_share(0.9, 0.95, 3), 0.905), "finite recursion")
    require(
        math.isclose(policy.stationary_proposer_share(0.9, 0.95), 0.3448275862068968),
        "stationary share",
    )
    require(math.isclose(policy.finite_proposer_share(0.8, 1.0, 2), 0.0), "patient parity even")
    require(math.isclose(policy.finite_proposer_share(0.8, 1.0, 3), 0.8), "patient parity odd")
    checks += 4

    support = (0.8, 1.0, 1.2, 1.5)
    feasible = sum(buyer > seller for seller in support for buyer in support)
    require(feasible == 6, "hidden support feasibility count")
    require(policy.strict_trade_interval(1.0, 1.0) is None, "strict trade boundary")
    checks += 2

    terminal_rank = policy.terminal_proposal_rank(0.25, 10.0, (5.0,))
    require(math.isclose(terminal_rank, 0.25), "terminal proposal identity")
    require(math.isclose(policy.empirical_midrank((0.0, 0.0), 0.0), 0.5), "zero atom midrank")
    checks += 2

    threshold = policy.buyer_break_even_probability(1.5, 0.0, 1.0)
    require(math.isclose(threshold, 2.0 / 3.0), "buyer break-even threshold")
    require(
        policy.persuasion_seller_recommendation("low", 1.0, None, None, False) == "yes",
        "unknown-value initial seller rule",
    )
    require(
        policy.persuasion_seller_recommendation("low", 1.0, None, 0.4, False) == "no",
        "unknown-value historical seller rule",
    )
    checks += 3

    return checks


def verify_declarative_spec() -> int:
    spec = json.loads((ROOT / "policy" / "policy_spec.json").read_text(encoding="utf-8"))
    bargaining = spec["effective_generic_bargaining"]
    negotiation = spec["effective_generic_negotiation"]
    checks = 0

    expected_bargaining = {
        "hidden_opponent_discount": 0.9,
        "hidden_recursion_horizon": 99,
        "intermediate_own_share_floor": 0.57,
        "opponent_share_floor_before_rank": 0.39,
        "configured_floor_gain": 0.05,
        "maximum_acceptance_share_floor": 0.5,
        "realistic_continuation_multiplier": 0.98,
    }
    for key, expected in expected_bargaining.items():
        require(close(bargaining[key], expected), f"bargaining spec field {key}")
        checks += 1
    rank_search = bargaining["local_rank_search"]
    require(
        [rank_search[key] for key in ("share_minimum", "share_maximum", "share_step", "required_gain_over_continuation")]
        == [0.2, 0.95, 0.01, 0.005],
        "bargaining rank-search spec",
    )
    require(rank_search["direction"] == "upward_floor_only", "bargaining rank direction")
    checks += 2
    grid = bargaining["inflation_clock"]["reference_grid"]
    require(grid == {"0.8": 14, "0.9": 29, "0.95": 59, "1.0": 60}, "clock spec grid")
    require(bargaining["inflation_clock"]["cap"] == 60, "clock cap")
    checks += 2

    seller = negotiation["seller_price_pipeline"]
    require(
        [seller[key] for key in ("boulware_exponent", "visible_zopa_opponent_share", "minimum_margin", "outgoing_visible_span_floor")]
        == [2.0, 0.39, 0.02, 0.4],
        "negotiation seller pipeline",
    )
    require(
        negotiation["active_complete_information_postguards"]
        == {"first_outgoing_share": 0.95, "later_wire_share_floor": 0.8},
        "negotiation active postguards",
    )
    require(
        [(row["component"], row["value"]) for row in negotiation["configured_but_shadowed"]]
        == [("final_proposer_option", 0.6), ("generic_visible_terminal_ultimatum", 0.8)],
        "negotiation shadowed writers",
    )
    require(negotiation["acceptance_parameters"]["visible_span_veto"] == 0.48, "visible veto")
    require(
        negotiation["acceptance_parameters"]["continuation_deal_probability"] == 0.65,
        "continuation probability",
    )
    require(len(negotiation["fallback_decision_order"]) == 8, "fallback order")
    checks += 6
    return checks


def main() -> None:
    vector_count = run_vectors()
    identity_count = run_identities()
    spec_count = verify_declarative_spec()
    print(
        f"verify_math_policy: PASS ({vector_count} vectors, "
        f"{identity_count} identities, {spec_count} spec checks)"
    )


if __name__ == "__main__":
    main()
