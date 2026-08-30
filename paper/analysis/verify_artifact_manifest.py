#!/usr/bin/env python3
"""Verify the frozen submitted-policy source, model, and overlay receipts."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parent
ASSET_MANIFEST = PAPER / "data" / "submitted_policy_asset_manifest.csv"
BANK_MANIFEST = PAPER / "data" / "submitted_agent_bank_manifest.csv"
EXPECTED_COMBINED = (
    "1969fa1c5ef4c6d11d2ab565ece5fcbb40eb4e05a89fd7031edd58eaf521498c"
)
REQUIRED_DEFAULTS = {
    ("shared", "LLM_MODE", "off"),
    ("bargaining", "BARG_UNKNOWN_DELTA", "0.90"),
    ("bargaining", "BARG_UNDISCLOSED_HORIZON", "99"),
    ("negotiation", "NEGO_HORIZON", "10"),
    ("negotiation", "NEGO_DEAL_ODDS", "0.65"),
    ("negotiation", "BOULWARE_EXPONENT", "2.0"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_assets() -> None:
    with ASSET_MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 23, f"expected 23 policy assets, found {len(rows)}"
    combined_input = bytearray()
    for expected_order, row in enumerate(rows, start=1):
        assert int(row["order"]) == expected_order
        relative = row["path"]
        actual = sha256(ROOT / relative)
        assert actual == row["sha256"], f"hash mismatch: {relative}"
        combined_input.extend(f"{actual}  {relative}\n".encode())
    combined = hashlib.sha256(combined_input).hexdigest()
    assert combined == EXPECTED_COMBINED, "ordered manifest checksum mismatch"


def verify_bank() -> None:
    with BANK_MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    flags = [row for row in rows if row["record_type"] == "flag"]
    assert len(flags) == 81, f"expected 81 overlay flags, found {len(flags)}"
    recorded = {(row["scope"], row["key"], row["value"]) for row in rows}
    missing = REQUIRED_DEFAULTS - recorded
    assert not missing, f"missing behavior-affecting defaults: {sorted(missing)}"


if __name__ == "__main__":
    verify_assets()
    verify_bank()
    print("PASS: 23 policy assets, ordered checksum, 81 flags, and defaults")
