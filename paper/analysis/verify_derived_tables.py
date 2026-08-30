#!/usr/bin/env python3
"""Verify arithmetic in the deidentified archive-coverage tables."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_rows(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


coverage = {row["profile"]: row for row in read_rows("log_archive_coverage.csv")}
submitted = coverage["submitted"]
finals = int(submitted["terminal_finals"])
public_total = int(submitted["public_total_at_audit"])
assert (finals, public_total) == (46_301, 46_564)
assert round(100 * finals / public_total, 2) == 99.44

era = {row["family"]: row for row in read_rows("final_policy_era_census.csv")}
assert {family: int(row["games"]) for family, row in era.items()} == {
    "bargaining": 19,
    "negotiation": 19,
    "persuasion": 25,
}
assert sum(int(row["games"]) for row in era.values()) == 63
assert sum(int(row["own_action_records"]) for row in era.values()) == 787
assert sum(int(row["logged_errors"]) for row in era.values()) == 0
assert len({row["start_utc"] for row in era.values()}) == 1
assert len({row["end_utc"] for row in era.values()}) == 1

windows = read_rows("final_policy_two_window_census.csv")
assert len(windows) == 5
assert sum(int(row["joined_games"]) for row in windows) == 245
assert sum(int(row["rated_games"]) for row in windows) == 244
assert sum(int(row["timeouts"]) for row in windows) == 1
assert sum(int(row["own_action_records"]) for row in windows) == 2_288
assert sum(int(row["logged_errors"]) for row in windows) == 0
by_family: dict[str, dict[str, int]] = {}
for row in windows:
    family = row["family"]
    totals = by_family.setdefault(
        family,
        {"joined": 0, "rated": 0, "timeouts": 0, "actions": 0},
    )
    totals["joined"] += int(row["joined_games"])
    totals["rated"] += int(row["rated_games"])
    totals["timeouts"] += int(row["timeouts"])
    totals["actions"] += int(row["own_action_records"])
assert by_family == {
    "bargaining": {"joined": 171, "rated": 171, "timeouts": 0, "actions": 1_001},
    "negotiation": {"joined": 19, "rated": 19, "timeouts": 0, "actions": 190},
    "persuasion": {"joined": 55, "rated": 54, "timeouts": 1, "actions": 1_097},
}

parser_slices = {
    row["slice_id"]: row for row in read_rows("persuasion_parser_coverage.csv")
}
frozen_parser = parser_slices["frozen_forensic"]
assert (
    int(frozen_parser["text_decisions"]),
    int(frozen_parser["strict_miss_turns"]),
    int(frozen_parser["strict_miss_games"]),
    int(frozen_parser["purchased_strict_miss_turns"]),
    int(frozen_parser["purchased_strict_miss_games"]),
) == (14_900, 146, 33, 40, 21)
final_parser = parser_slices["complete_final_era"]
assert (
    int(final_parser["all_persuasion_games"]),
    int(final_parser["buyer_role_games"]),
    int(final_parser["seller_role_games"]),
    int(final_parser["text_decisions"]),
    int(final_parser["strict_miss_turns"]),
    int(final_parser["purchased_strict_miss_turns"]),
    int(final_parser["low_purchased_outcomes"]),
) == (25, 14, 11, 80, 4, 4, 4)

print("PASS: archive coverage is 46,301/46,564 = 99.44%")
print("PASS: pre-close subcohort is 63 games and 787 own actions")
print("PASS: two final-profile windows are 245 joined games, 244 rated games, 1 timeout, 2,288 own actions, 0 logged errors")
print("PASS: persuasion parser denominators match the frozen and pre-close tables")
