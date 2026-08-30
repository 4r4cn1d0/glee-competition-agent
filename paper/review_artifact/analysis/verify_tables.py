#!/usr/bin/env python3
"""Verify released aggregate tables and their reported arithmetic."""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
Z_975 = 1.96


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def near(actual: float, expected: float, tolerance: float = 5e-6) -> None:
    require(math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), f"{actual} != {expected}")


def clone_statistics() -> dict[str, float]:
    checkpoint = rows("clone_checkpoint.csv")
    require(len(checkpoint) == 91, "clone checkpoint row count")
    require([int(row["row_id"]) for row in checkpoint] == list(range(1, 92)), "release row order")

    by_arm = {
        arm: [float(row["rating_change"]) for row in checkpoint if row["arm"] == arm]
        for arm in ("candidate", "control")
    }
    require(len(by_arm["candidate"]) == 44, "candidate count")
    require(len(by_arm["control"]) == 47, "control count")
    candidate_mean = statistics.mean(by_arm["candidate"])
    control_mean = statistics.mean(by_arm["control"])
    difference = candidate_mean - control_mean
    standard_error = math.sqrt(
        statistics.variance(by_arm["candidate"]) / len(by_arm["candidate"])
        + statistics.variance(by_arm["control"]) / len(by_arm["control"])
    )
    lower = difference - Z_975 * standard_error
    upper = difference + Z_975 * standard_error

    strata: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in checkpoint:
        strata[row["stratum"]].append(row)
    require(set(strata) == {"S1", "S2", "S3", "S4"}, "anonymous strata")
    standardized = 0.0
    for group in strata.values():
        candidate = [float(row["rating_change"]) for row in group if row["arm"] == "candidate"]
        control = [float(row["rating_change"]) for row in group if row["arm"] == "control"]
        standardized += len(group) / len(checkpoint) * (
            statistics.mean(candidate) - statistics.mean(control)
        )

    candidate_rows = [row for row in checkpoint if row["arm"] == "candidate"]
    control_rows = [row for row in checkpoint if row["arm"] == "control"]
    candidate_no_deal = sum(row["outcome"] == "no_deal" for row in candidate_rows)
    control_no_deal = sum(row["outcome"] == "no_deal" for row in control_rows)
    no_deal_difference = 100.0 * (
        candidate_no_deal / len(candidate_rows) - control_no_deal / len(control_rows)
    )

    near(candidate_mean, 1.115909)
    near(control_mean, 0.246809)
    near(difference, 0.869101)
    near(lower, -0.730366)
    near(upper, 2.468567)
    near(standardized, 0.990780)
    near(no_deal_difference, 6.141, tolerance=5e-4)

    return {
        "clone_candidate_mean": candidate_mean,
        "clone_control_mean": control_mean,
        "clone_difference": difference,
        "clone_interval_lower": lower,
        "clone_interval_upper": upper,
        "clone_no_deal_difference": no_deal_difference,
    }


def aggregate_statistics() -> dict[str, float]:
    computed: dict[str, float] = {}

    trajectory = rows("rating_trajectory_relative.csv")
    require([int(row["sequence_index"]) for row in trajectory] == list(range(1, 13)), "relative order")
    final_rating = trajectory[-1]
    require(final_rating["event"] == "official_final_display", "official final row")
    computed.update(
        {
            "final_display_bargaining": float(final_rating["bargaining"]),
            "final_display_negotiation": float(final_rating["negotiation"]),
            "final_display_persuasion": float(final_rating["persuasion"]),
            "final_display_overall": float(final_rating["overall_rating"]),
            "final_agent_track_place": float(final_rating["agent_track_place"]),
            "final_overall_place": float(final_rating["overall_place"]),
        }
    )

    archive = rows("archive_coverage_anonymous.csv")
    require(len(archive) == 5, "archive row count")
    focal = archive[0]
    require(focal["profile_label"] == "focal", "focal row first")
    records = int(focal["per_game_records"])
    finals = int(focal["terminal_finals"])
    unresolved = int(focal["unresolved"])
    public_total = int(focal["public_total"])
    require(records == finals + unresolved, "focal local archive partition")
    require(int(final_rating["public_games"]) == public_total, "final display and archive public totals")
    coverage = 100.0 * finals / public_total
    near(float(focal["coverage_percent"]), round(coverage, 2), tolerance=1e-9)
    computed.update(
        {
            "focal_public_games": float(public_total),
            "focal_terminal_finals": float(finals),
            "focal_archive_coverage": float(focal["coverage_percent"]),
        }
    )

    census = rows("final_era_census_anonymous.csv")
    require([row["family"] for row in census] == ["bargaining", "negotiation", "persuasion"], "family order")
    joined_games = sum(int(row["joined_games"]) for row in census)
    rated_games = sum(int(row["rated_games"]) for row in census)
    timeout_games = sum(int(row["timeout_games"]) for row in census)
    total_actions = sum(int(row["own_action_records"]) for row in census)
    total_errors = sum(int(row["logged_errors"]) for row in census)
    require(joined_games == 245, "final joined games")
    require(rated_games == 244, "final rated games")
    require(timeout_games == 1, "final timeouts")
    require(total_actions == 2288, "final own actions")
    require(total_errors == 0, "final logged errors")
    for row in census:
        require(
            int(row["role_a_games"]) + int(row["role_b_games"]) == int(row["joined_games"]),
            "role totals",
        )
        require(
            int(row["rated_games"]) + int(row["timeout_games"]) == int(row["joined_games"]),
            "rated and timeout partition",
        )
    require(
        census[0]["terminal_summary"] == "171 agreements"
        and census[0]["recorded_action_summary"] == "503 offers; 414 rejects; 84 accepts",
        "bargaining final census",
    )
    require(
        census[1]["terminal_summary"] == "13 agreements; 3 walks; 3 no-deals"
        and census[1]["recorded_action_summary"]
        == "10 initial offers; 171 rejects or counters; 7 accepts; 2 own walks",
        "negotiation final census",
    )
    require(
        census[2]["terminal_summary"] == "54 completed games; 1 timeout"
        and census[2]["recorded_action_summary"]
        == "buyer yes/no 456/201; seller positive/negative 316/124",
        "persuasion final census",
    )
    computed.update(
        {
            "final_policy_joined_games": float(joined_games),
            "final_policy_rated_games": float(rated_games),
            "final_policy_timeouts": float(timeout_games),
            "final_policy_actions": float(total_actions),
            "final_policy_logged_errors": float(total_errors),
        }
    )

    parser = rows("parser_coverage_aggregate.csv")
    require(len(parser) == 3, "parser slice count")
    preclose_parser = next(row for row in parser if row["slice"] == "preclose_final_policy_subcohort")
    require(int(preclose_parser["buyer_role_games"]) + int(preclose_parser["seller_role_games"]) == 25, "preclose parser games")
    require(int(preclose_parser["text_decisions"]) == 80, "preclose text decisions")
    require(int(preclose_parser["strict_miss_turns"]) == 4, "preclose strict misses")
    require(int(preclose_parser["purchased_strict_miss_turns"]) == 4, "preclose purchased misses")
    require(int(preclose_parser["low_purchased_outcomes"]) == 4, "preclose low outcomes")
    require(int(preclose_parser["high_purchased_outcomes"]) == 0, "preclose high outcomes")
    computed.update(
        {
            "preclose_parser_text_decisions": 80.0,
            "preclose_parser_strict_misses": 4.0,
            "preclose_parser_low_purchases": 4.0,
        }
    )

    registry = rows("experiment_registry_public.csv")
    require(len(registry) == 35, "registry count")
    require([int(row["record_number"]) for row in registry] == list(range(1, 36)), "registry order")
    dispositions = Counter(row["terminal_disposition"] for row in registry)
    computed.update(
        {
            "registry_records": 35.0,
            "registry_reached": float(sum(int(row["action_changing_reach"]) for row in registry)),
            "registry_historically_live": float(sum(int(row["historically_live"]) for row in registry)),
            "registry_staged_only": float(sum(int(row["staged_only"]) for row in registry)),
            "registry_adverse": float(dispositions["adverse"]),
            "registry_stopped_or_superseded": float(dispositions["stopped_or_superseded"]),
            "registry_no_terminal_efficacy": float(dispositions["no_terminal_efficacy"]),
        }
    )
    require(computed["registry_reached"] == 33, "reached count")
    require(computed["registry_historically_live"] == 25, "live count")
    require(computed["registry_staged_only"] == 1, "staged count")
    require(computed["registry_adverse"] == 7, "adverse count")
    require(computed["registry_stopped_or_superseded"] == 17, "stopped count")
    require(computed["registry_no_terminal_efficacy"] == 11, "unterminated count")

    outcomes = {row["measure"]: row for row in rows("outcome_summary.csv")}
    near(float(outcomes["clone_rating_difference"]["estimate"]), 0.869101)
    near(float(outcomes["clone_no_deal_difference"]["estimate"]), 6.141)
    require(sum(key.startswith("broad_bargaining_floor_seed_") for key in outcomes) == 3, "three negative bargaining seeds")
    concession_rows = [row for key, row in outcomes.items() if key.startswith("faster_seller_concession_seed_")]
    require(len(concession_rows) == 2, "two archived concession diagnostics")
    require(
        all(row["status"] == "invalidated_diagnostic_sign_unresolved" for row in concession_rows),
        "concession diagnostics must remain classified as invalidated",
    )

    return computed


def verify_claims(computed: dict[str, float]) -> None:
    computed.update(
        {
            "safe_action_expected_payoff": 10.0,
            "risky_action_expected_payoff": 10.5,
            "safe_action_expected_midrank": 1.0,
            "risky_action_expected_midrank": 0.5,
        }
    )
    claims = rows("reported_claims.csv")
    require(len(claims) == len(computed), "reported claim coverage")
    claim_names = {row["claim"] for row in claims}
    require(claim_names == set(computed), "reported claim key mismatch")
    for row in claims:
        near(float(row["value"]), computed[row["claim"]], tolerance=5e-4)


def verify_schema_privacy() -> None:
    forbidden_headers = {
        "timestamp",
        "source_location",
        "opponent" + "_" + "name",
        "opponent" + "_" + "id",
        "game" + "_" + "id",
        "agent" + "_" + "id",
        "host",
        "process_id",
        "assignment_salt",
    }
    for path in sorted(DATA.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        require(not forbidden_headers.intersection(header), f"forbidden header in {path.name}")


def main() -> None:
    verify_schema_privacy()
    computed = clone_statistics()
    computed.update(aggregate_statistics())
    verify_claims(computed)
    print(f"verify_tables: PASS ({len(computed)} reported claims)")


if __name__ == "__main__":
    main()
