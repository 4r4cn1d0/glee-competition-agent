#!/usr/bin/env python3
"""Render deterministic Markdown tables from the released inputs."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPECTED = ROOT / "tables"
Z_975 = 1.96


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def clone_table() -> str:
    rows = read_rows("clone_checkpoint.csv")
    candidate = [float(row["rating_change"]) for row in rows if row["arm"] == "candidate"]
    control = [float(row["rating_change"]) for row in rows if row["arm"] == "control"]
    difference = statistics.mean(candidate) - statistics.mean(control)
    standard_error = math.sqrt(
        statistics.variance(candidate) / len(candidate)
        + statistics.variance(control) / len(control)
    )
    lower = difference - Z_975 * standard_error
    upper = difference + Z_975 * standard_error
    candidate_no_deal = sum(row["outcome"] == "no_deal" for row in rows if row["arm"] == "candidate")
    control_no_deal = sum(row["outcome"] == "no_deal" for row in rows if row["arm"] == "control")
    no_deal_difference = 100.0 * (candidate_no_deal / len(candidate) - control_no_deal / len(control))
    return "\n".join(
        [
            "# Clone checkpoint summary",
            "",
            "| Measure | Value |",
            "| --- | ---: |",
            f"| Candidate | n={len(candidate)}, mean={statistics.mean(candidate):.6f} |",
            f"| Control | n={len(control)}, mean={statistics.mean(control):.6f} |",
            f"| Difference | {difference:.6f} |",
            f"| Normal 95% interval | [{lower:.6f}, {upper:.6f}] |",
            f"| No-deal difference | {no_deal_difference:.3f} percentage points |",
            "",
        ]
    )


def final_era_table() -> str:
    rows = read_rows("final_era_census_anonymous.csv")
    lines = [
        "# Complete two-window final-policy census",
        "",
        "| Family | Joined, rated, timeout | Roles across joined games | Terminal outcomes | Recorded own actions | Own actions | Errors |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        counts = f"{row['joined_games']}, {row['rated_games']}, {row['timeout_games']}"
        roles = f"{row['role_a']}={row['role_a_games']}, {row['role_b']}={row['role_b_games']}"
        lines.append(
            f"| {row['family']} | {counts} | {roles} | {row['terminal_summary']} | "
            f"{row['recorded_action_summary']} | {row['own_action_records']} | {row['logged_errors']} |"
        )
    joined = sum(int(row["joined_games"]) for row in rows)
    rated = sum(int(row["rated_games"]) for row in rows)
    timeouts = sum(int(row["timeout_games"]) for row in rows)
    actions = sum(int(row["own_action_records"]) for row in rows)
    errors = sum(int(row["logged_errors"]) for row in rows)
    lines.append(
        f"| **Total** | **{joined}, {rated}, {timeouts}** | | | | **{actions}** | **{errors}** |"
    )
    lines.append("")
    return "\n".join(lines)


def claims_table() -> str:
    rows = read_rows("reported_claims.csv")
    lines = [
        "# Reproducible aggregate claims",
        "",
        "| Claim | Value | Unit | Boundary |",
        "| --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['claim']} | {row['value']} | {row['unit']} | {row['boundary']} |")
    lines.append("")
    return "\n".join(lines)


def rendered() -> dict[str, str]:
    return {
        "clone_checkpoint_summary.md": clone_table(),
        "final_era_summary.md": final_era_table(),
        "reported_claims.md": claims_table(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    outputs = rendered()
    if args.check:
        for name, content in outputs.items():
            expected = (EXPECTED / name).read_text(encoding="utf-8")
            if content != expected:
                raise AssertionError(f"rendered table differs: {name}")
        print(f"render_tables: PASS ({len(outputs)} tables)")
        return
    if args.output_dir is None:
        raise SystemExit("provide --check or --output-dir")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content, encoding="utf-8")
    print(f"render_tables: wrote {len(outputs)} tables")


if __name__ == "__main__":
    main()
