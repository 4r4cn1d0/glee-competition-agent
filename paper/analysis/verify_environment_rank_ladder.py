#!/usr/bin/env python3
"""Recompute the appendix's one-currency-cent probe from the frozen seed.

The seed stores payoff / base, so a currency payoff of 0.01 must be queried
at 0.01 / base. Querying at 0.01 instead measures one percent of the base.
These are pooled descriptive midranks, not same-cell official scores.
This script reads only the seed and, optionally, the manuscript. It writes
no files and makes no network or live-fleet calls.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "models" / "negotiation_seed_cdf_full.json"
SEED_SHA256 = "f828dc51501b7473b016b1d9ecc844ba7792128d2a9bcff757265c5404f61505"
EXPECTED_COUNTS = {
    (True, 100): 898,
    (True, 10_000): 904,
    (True, 1_000_000): 906,
    (False, 100): 904,
    (False, 10_000): 900,
    (False, 1_000_000): 901,
}


def midrank(values: list[float], probe: float) -> float:
    """Equation (midrank), using exact equality and the sorted frozen values."""
    return (
        bisect.bisect_left(values, probe) + bisect.bisect_right(values, probe)
    ) / (2 * len(values))


def compute_rows() -> list[dict[str, object]]:
    raw = SEED.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SEED_SHA256, "frozen seed hash changed"
    document = json.loads(raw)
    assert document["_schema"] == "glee.negotiation_seed_cdf/full-v1"
    assert document["_games"] == 32_403
    cells = document["cells"]
    assert len(cells) == 1_152
    assert sum(len(values) for values in cells.values()) == 64_806

    results = []
    for complete in (True, False):
        for base in (100, 10_000, 1_000_000):
            selected = [
                values
                for key, values in cells.items()
                if key.split("|")[1:5] == ["1", str(complete), "False", str(base)]
                and key.endswith("|seller")
            ]
            assert len(selected) == 16
            values = sorted(value for cell in selected for value in cell)
            assert len(values) == EXPECTED_COUNTS[(complete, base)]
            q_zero = midrank(values, 0.0)
            q_cent = midrank(values, 0.01 / base)
            q_max = midrank(values, max(values))
            results.append({
                "information": "Complete" if complete else "Hidden",
                "base": base,
                "cells": len(selected),
                "n": len(values),
                "normalized_cent_probe": 0.01 / base,
                "q_zero": q_zero,
                "q_currency_cent": q_cent,
                "q_max_reference": q_max,
                "closing_gain": q_cent - q_zero,
                "price_gain": q_max - q_cent,
                "q_one_percent_of_base": midrank(values, 0.01),
            })
    return results


def latex_row(row: dict[str, object]) -> str:
    exponent = {100: 2, 10_000: 4, 1_000_000: 6}[row["base"]]
    return (
        f'{row["information"]} & $10^{exponent}$ & {row["n"]} & '
        f'{row["q_zero"]:.3f} & {row["q_currency_cent"]:.3f} & '
        f'$+{row["closing_gain"]:.3f}$ & $+{row["price_gain"]:.3f}$ \\\\'
    ).replace("0.", ".")


def check_manuscript(rows: list[dict[str, object]]) -> None:
    manuscript = (ROOT / "paper" / "appendix.tex").read_text(encoding="utf-8")
    table = manuscript.split(r"\label{tab:rank-ladder}", 1)[1].split(r"\end{table}", 1)[0]
    actual = [line.strip() for line in table.splitlines()
              if line.startswith(("Complete &", "Hidden &"))]
    expected = [latex_row(row) for row in rows]
    canonical = lambda line: re.sub(r"\s+", "", line)
    assert [canonical(row) for row in actual] == [canonical(row) for row in expected], (
        "rank-ladder table does not match the frozen one-currency-cent computation"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-manuscript", action="store_true")
    args = parser.parse_args()
    rows = compute_rows()
    print(json.dumps({"seed_sha256": SEED_SHA256, "rows": rows}, indent=2))
    print("LaTeX rows:")
    for row in rows:
        print(latex_row(row))
    if args.check_manuscript:
        check_manuscript(rows)
        print("PASS: printed rank-ladder rows match the frozen one-currency-cent probe")


if __name__ == "__main__":
    main()
