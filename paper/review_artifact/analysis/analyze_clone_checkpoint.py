#!/usr/bin/env python3
"""Reproduce the deidentified 91-game buyer-clone checkpoint summary.

The source table contains no game IDs, opponent names, prices, messages, or
valuations. It reproduces the reported outcome analysis but cannot re-audit the
original hash assignment or action-history joins.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data" / "clone_checkpoint.csv"
Z_975 = 1.96


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    **row,
                    "rating_change": float(row["rating_change"]),
                    "messages": row["messages"].lower() == "true",
                }
            )
    return rows


def normal_difference(candidate: list[float], control: list[float]) -> tuple[float, float, float, float]:
    difference = statistics.mean(candidate) - statistics.mean(control)
    standard_error = math.sqrt(
        statistics.variance(candidate) / len(candidate)
        + statistics.variance(control) / len(control)
    )
    return (
        difference,
        standard_error,
        difference - Z_975 * standard_error,
        difference + Z_975 * standard_error,
    )


def summarize(rows: list[dict[str, object]]) -> None:
    by_arm = {
        arm: [float(row["rating_change"]) for row in rows if row["arm"] == arm]
        for arm in ("candidate", "control")
    }
    difference, standard_error, lower, upper = normal_difference(
        by_arm["candidate"], by_arm["control"]
    )
    print("Unstratified rating change")
    print(
        f"  candidate n={len(by_arm['candidate'])}, mean={statistics.mean(by_arm['candidate']):.6f}"
    )
    print(f"  control   n={len(by_arm['control'])}, mean={statistics.mean(by_arm['control']):.6f}")
    print(
        f"  difference={difference:.6f}, SE={standard_error:.6f}, "
        f"normal 95% interval=[{lower:.6f}, {upper:.6f}]"
    )

    strata: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        strata[str(row["stratum"])].append(row)

    weighted_difference = 0.0
    weighted_variance = 0.0
    print("Profile-stratum rating changes")
    for stratum in sorted(strata):
        group = strata[stratum]
        candidate = [float(row["rating_change"]) for row in group if row["arm"] == "candidate"]
        control = [float(row["rating_change"]) for row in group if row["arm"] == "control"]
        stratum_difference, stratum_se, _, _ = normal_difference(candidate, control)
        weight = len(group) / len(rows)
        weighted_difference += weight * stratum_difference
        weighted_variance += weight**2 * stratum_se**2
        print(
            f"  {stratum}: n={len(group)}, candidate={len(candidate)}, control={len(control)}, "
            f"difference={stratum_difference:.6f}, realized weight={weight:.6f}"
        )

    weighted_se = math.sqrt(weighted_variance)
    print("Profile-stratum-standardized rating change")
    print(
        f"  difference={weighted_difference:.6f}, SE={weighted_se:.6f}, "
        f"normal 95% interval=[{weighted_difference - Z_975 * weighted_se:.6f}, "
        f"{weighted_difference + Z_975 * weighted_se:.6f}]"
    )

    candidate_rows = [row for row in rows if row["arm"] == "candidate"]
    control_rows = [row for row in rows if row["arm"] == "control"]
    candidate_no_deals = sum(row["outcome"] == "no_deal" for row in candidate_rows)
    control_no_deals = sum(row["outcome"] == "no_deal" for row in control_rows)
    p_candidate = candidate_no_deals / len(candidate_rows)
    p_control = control_no_deals / len(control_rows)
    no_deal_difference = p_candidate - p_control
    no_deal_se = math.sqrt(
        p_candidate * (1 - p_candidate) / len(candidate_rows)
        + p_control * (1 - p_control) / len(control_rows)
    )
    print("No-deal rate")
    print(
        f"  candidate={candidate_no_deals}/{len(candidate_rows)}, "
        f"control={control_no_deals}/{len(control_rows)}"
    )
    print(
        f"  difference={100 * no_deal_difference:.3f} percentage points, "
        f"Wald 95% interval=[{100 * (no_deal_difference - Z_975 * no_deal_se):.3f}, "
        f"{100 * (no_deal_difference + Z_975 * no_deal_se):.3f}]"
    )


if __name__ == "__main__":
    summarize(load_rows())
