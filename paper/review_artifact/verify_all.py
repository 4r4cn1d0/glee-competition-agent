#!/usr/bin/env python3
"""Run the closed-bundle integrity, privacy, arithmetic, and figure checks."""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = "MANIFEST.sha256"
ALLOWED_FILES = frozenset(
    {
        "DATA_DICTIONARY.md",
        "LICENSES.md",
        MANIFEST,
        "README.md",
        "REPRODUCIBILITY_BOUNDARY.md",
        "analysis/analyze_clone_checkpoint.py",
        "analysis/render_tables.py",
        "analysis/verify_math_policy.py",
        "analysis/verify_tables.py",
        "data/archive_coverage_anonymous.csv",
        "data/clone_checkpoint.csv",
        "data/experiment_registry_public.csv",
        "data/final_era_census_anonymous.csv",
        "data/outcome_summary.csv",
        "data/parser_coverage_aggregate.csv",
        "data/rating_trajectory_relative.csv",
        "data/reported_claims.csv",
        "figures/expected/rank_objective.png",
        "figures/expected/rating_trajectory.png",
        "figures/gen_rank_objective.py",
        "figures/gen_rating_trajectory.py",
        "policy/__init__.py",
        "policy/policy_spec.json",
        "policy/reference_policy.py",
        "policy/synthetic_test_vectors.json",
        "requirements.lock",
        "tables/clone_checkpoint_summary.md",
        "tables/final_era_summary.md",
        "tables/reported_claims.md",
        "verify_all.py",
    }
)
TEXT_SUFFIXES = {".md", ".py", ".json", ".csv", ".lock"}
FIGURE_SPECS = {
    "rank_objective": (1044, 432),
    "rating_trajectory": (1152, 503),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def closed_allowlist() -> None:
    actual: set[str] = set()
    for path in ROOT.rglob("*"):
        require(not path.is_symlink(), f"symbolic link rejected: {path.relative_to(ROOT)}")
        if path.is_file():
            actual.add(path.relative_to(ROOT).as_posix())
    missing = sorted(ALLOWED_FILES - actual)
    extra = sorted(actual - ALLOWED_FILES)
    require(not missing, f"allowlist missing files: {missing}")
    require(not extra, f"allowlist rejected files: {extra}")
    print(f"allowlist: PASS ({len(actual)} files)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest() -> None:
    entries: dict[str, str] = {}
    for line in (ROOT / MANIFEST).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, separator, name = line.partition("  ")
        require(bool(separator), f"malformed manifest line: {line}")
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"invalid digest: {name}")
        require(name not in entries, f"duplicate manifest entry: {name}")
        entries[name] = digest
    expected = ALLOWED_FILES - {MANIFEST}
    require(set(entries) == expected, "manifest entries do not match the closed allowlist")
    for name in sorted(entries):
        require(sha256(ROOT / name) == entries[name], f"manifest mismatch: {name}")
    print(f"manifest: PASS ({len(entries)} digests)")


def privacy_scan() -> None:
    remote_pattern = re.compile(r"\b(?:" + "ht" + r"tps?|" + "ft" + r"p)://", re.IGNORECASE)
    patterns = [
        ("remote address", remote_pattern),
        ("absolute machine path", re.compile(r"(?<![A-Za-z0-9])/(?:Users|home|root|private|var|tmp|opt|srv)/")),
        ("drive-qualified path", re.compile(r"\b[A-Za-z]:\\(?:Users|Documents|Desktop)\\")),
        ("wall-clock record", re.compile(r"\b20\d{2}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z?\b")),
        ("epoch-like record", re.compile(r"\b1[6-9]\d{8}(?:\.\d+)?\b")),
        ("email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
        ("environment file", re.compile(r"(?<![A-Za-z0-9_-])\.env(?:$|[./\s])")),
        ("universal identifier", re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")),
        ("embedded private digest", re.compile(r"\b[0-9a-fA-F]{32,64}\b")),
        (
            "credential assignment",
            re.compile(
                r"\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+-]{8,}",
                re.IGNORECASE,
            ),
        ),
    ]
    denied_literals = [
        "." + "ai" + "/",
        "glee" + "_" + "agent",
        "arms" + ".json",
        "control" + ".json",
        "." + "jsonl",
        "Rank" + "Smith",
        "Agent" + " 5",
        "compo" + "site",
        "spider" + "ishi",
    ]
    scanned = 0
    for name in sorted(ALLOWED_FILES):
        path = ROOT / name
        if path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in patterns:
            if label == "embedded private digest" and name == MANIFEST:
                continue
            match = pattern.search(text)
            require(match is None, f"privacy scan found {label} in {name}")
        for literal in denied_literals:
            require(literal.lower() not in text.lower(), f"privacy scan found denied source literal in {name}")
        scanned += 1
    print(f"privacy_scan: PASS ({scanned} text files)")


def dependency_check() -> None:
    require(sys.version_info >= (3, 9), "verification requires Python 3.9 or later")
    required = {"matplotlib": "3.9.4", "numpy": "2.0.2"}
    for package, expected in required.items():
        actual = importlib.metadata.version(package)
        require(actual == expected, f"{package} version {actual}, expected {expected}")
    print(f"dependencies: PASS (Python {sys.version_info.major}.{sys.version_info.minor}, 2 pinned packages)")


def run(command: list[str], expected_fragments: tuple[str, ...]) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    require(result.returncode == 0, f"command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    for fragment in expected_fragments:
        require(fragment in result.stdout, f"missing output fragment {fragment!r}")
    print(result.stdout.strip())


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), f"not a PNG: {path.name}")
    require(len(data) > 24, f"truncated PNG: {path.name}")
    return struct.unpack(">II", data[16:24])


def figure_check() -> None:
    with tempfile.TemporaryDirectory(prefix="anonymous-review-") as temporary:
        destination = Path(temporary)
        for stem, dimensions in FIGURE_SPECS.items():
            output = destination / f"{stem}.png"
            run(
                [sys.executable, str(ROOT / "figures" / f"gen_{stem}.py"), "--output", str(output)],
                (),
            )
            require(output.stat().st_size > 5000, f"generated figure too small: {stem}")
            require(png_dimensions(output) == dimensions, f"generated dimensions differ: {stem}")
            expected = ROOT / "figures" / "expected" / f"{stem}.png"
            require(png_dimensions(expected) == dimensions, f"reference dimensions differ: {stem}")
    print(f"figures: PASS ({len(FIGURE_SPECS)} regenerated)")


def main() -> None:
    closed_allowlist()
    verify_manifest()
    privacy_scan()
    dependency_check()
    run([sys.executable, "analysis/verify_math_policy.py"], ("verify_math_policy: PASS",))
    run([sys.executable, "analysis/verify_tables.py"], ("verify_tables: PASS",))
    run([sys.executable, "analysis/render_tables.py", "--check"], ("render_tables: PASS",))
    run(
        [sys.executable, "analysis/analyze_clone_checkpoint.py"],
        ("difference=0.869101", "difference=0.990780", "difference=6.141 percentage points"),
    )
    figure_check()
    print("verify_all: PASS")


if __name__ == "__main__":
    main()
