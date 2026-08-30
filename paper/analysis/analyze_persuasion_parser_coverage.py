#!/usr/bin/env python3
"""Audit the submitted persuasion buyer parser on a frozen turn archive.

This script is descriptive. The V2 and V3 selectors were developed after
examining related logs, so their disagreements with V1 are counterexamples,
not an independently annotated recall or precision estimate. Outcomes are
joined only after classification and are not used by the decision-time rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from glee_agent.strategies.persuasion import (  # noqa: E402
    _explicit_current_text_decline_v2 as decline_v2,
    _explicit_current_text_decline_v3 as decline_v3,
)
from glee_agent.text import reads_as_recommendation_expanded  # noqa: E402


FROZEN_START = 1787607315.0
FROZEN_END = 1787747687.0
FULL_END = 1788007035.0
FINAL_START = 1787981256.596627
FINAL_END = 1788007688.480755


EXPECTED: dict[str, dict[str, Any]] = {
    "frozen": {
        "slice": {"since": FROZEN_START, "until_exclusive": FROZEN_END},
        "buyer_decisions": 29_280,
        "buyer_games": 1_464,
        "text_decisions": 14_900,
        "text_games": 745,
        "binary_decisions": 14_380,
        "binary_games": 719,
        "labels": {
            "v1_negative": 3_069,
            "v2_strict_miss": 94,
            "v3_strict_miss": 52,
            "other": 11_685,
        },
        "strict_miss_decisions": 146,
        "strict_miss_games": 33,
        "purchased_strict_misses": 40,
        "purchased_strict_miss_games": 21,
        "passed_strict_misses": 106,
        "purchased_outcomes": {"low": 40, "high": 0, "missing": 0},
        "text_row_sha256": "06c03922067870a4bbc5323abc113ba4973e10c76336b689561aa4bb5b92a65f",
    },
    "full": {
        "slice": {"since": FROZEN_START, "until_exclusive": FULL_END},
        "buyer_decisions": 30_660,
        "buyer_games": 1_533,
        "text_decisions": 15_560,
        "text_games": 778,
        "binary_decisions": 15_100,
        "binary_games": 755,
        "labels": {
            "v1_negative": 3_132,
            "v2_strict_miss": 98,
            "v3_strict_miss": 52,
            "other": 12_278,
        },
        "strict_miss_decisions": 150,
        "strict_miss_games": 34,
        "purchased_strict_misses": 44,
        "purchased_strict_miss_games": 22,
        "passed_strict_misses": 106,
        "purchased_outcomes": {"low": 44, "high": 0, "missing": 0},
        "text_row_sha256": "49da1a17cad7da6a5f3a3a8627dd54ab7505a27da64f971d071f454846ae929e",
    },
    "final": {
        "slice": {"since": FINAL_START, "until_exclusive": FINAL_END},
        "all_persuasion_games": 25,
        "seller_role_games": 11,
        "buyer_role_games": 14,
        "buyer_decisions": 280,
        "buyer_games": 14,
        "text_decisions": 80,
        "text_games": 4,
        "binary_decisions": 200,
        "binary_games": 10,
        "labels": {
            "v1_negative": 2,
            "v2_strict_miss": 4,
            "v3_strict_miss": 0,
            "other": 74,
        },
        "strict_miss_decisions": 4,
        "strict_miss_games": 1,
        "purchased_strict_misses": 4,
        "purchased_strict_miss_games": 1,
        "passed_strict_misses": 0,
        "purchased_outcomes": {"low": 4, "high": 0, "missing": 0},
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", required=True, type=Path, help="private turns.jsonl archive")
    parser.add_argument("--since", required=True, type=float, help="inclusive Unix timestamp")
    parser.add_argument("--until", type=float, help="exclusive Unix timestamp")
    parser.add_argument(
        "--expect",
        choices=sorted(EXPECTED),
        help="assert one of the paper's frozen audit slices",
    )
    return parser.parse_args()


def stream_rows(path: Path, since: float, until: float | None) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
            timestamp = row.get("ts", 0)
            if timestamp < since or (until is not None and timestamp >= until):
                continue
            if row.get("game_family") == "persuasion":
                yield row


def is_buyer_decision(row: dict[str, Any]) -> bool:
    state = row.get("state") or {}
    return (
        row.get("your_player") == "player_2"
        and row.get("phase") == "buyer_decision"
        and row.get("action_type") == "buyer_decision"
        and state.get("current_player") == "player_2"
    )


def classify(message: Any) -> str:
    v1_negative = reads_as_recommendation_expanded(message) is False
    v2 = decline_v2(message)
    v3 = decline_v3(message)
    assert sum((v1_negative, v2, v3)) <= 1
    if v1_negative:
        return "v1_negative"
    if v2:
        return "v2_strict_miss"
    if v3:
        return "v3_strict_miss"
    return "other"


def opponent_visibility(row: dict[str, Any]) -> str:
    opponent = row.get("opponent") or {}
    return "hidden" if opponent.get("type") == "hidden" else "named"


def audit(path: Path, since: float, until: float | None) -> dict[str, Any]:
    persuasion_rows = list(stream_rows(path, since, until))
    all_games = {str(row["game_id"]) for row in persuasion_rows}
    seller_games = {
        str(row["game_id"]) for row in persuasion_rows if row.get("your_player") == "player_1"
    }
    buyer_role_games = {
        str(row["game_id"]) for row in persuasion_rows if row.get("your_player") == "player_2"
    }

    rows = [row for row in persuasion_rows if is_buyer_decision(row)]
    keys = [(str(row["game_id"]), int(row["round"])) for row in rows]
    if len(keys) != len(set(keys)):
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        raise AssertionError(f"duplicate buyer decisions: {duplicates[:5]}")
    for row in rows:
        assert (row.get("plan") or {}).get("buyer_v2") is True
        assert row.get("source") == "heuristic"

    text_rows = [
        row for row in rows if (row.get("state") or {}).get("seller_message_type") == "text"
    ]
    binary_rows = [
        row for row in rows if (row.get("state") or {}).get("seller_message_type") == "binary"
    ]
    if len(text_rows) + len(binary_rows) != len(rows):
        raise AssertionError("buyer archive contains an unexpected seller_message_type")

    labeled: list[tuple[dict[str, Any], str]] = []
    for row in text_rows:
        message = (row.get("state") or {}).get("seller_message")
        labeled.append((row, classify(message)))

    labels = Counter(label for _, label in labeled)
    exact_messages: dict[str, set[str]] = defaultdict(set)
    for row, label in labeled:
        exact_messages[label].add(str((row.get("state") or {}).get("seller_message")))

    strict = [
        row for row, label in labeled if label in {"v2_strict_miss", "v3_strict_miss"}
    ]
    purchased = [
        row
        for row in strict
        if str((row.get("action") or {}).get("decision", "")).lower() == "yes"
    ]

    history_outcome: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        for item in (row.get("state") or {}).get("history") or []:
            if isinstance(item, dict) and item.get("round") is not None:
                history_outcome[(str(row["game_id"]), int(item["round"]))] = item

    outcomes = Counter()
    for row in purchased:
        outcome = history_outcome.get((str(row["game_id"]), int(row["round"])))
        if outcome is None:
            outcomes["missing"] += 1
            continue
        assert outcome.get("bought") is True
        quality = str(outcome.get("quality", "")).lower()
        outcomes[quality if quality in {"low", "high"} else "missing"] += 1

    digest = hashlib.sha256()
    for row in sorted(text_rows, key=lambda item: (item["ts"], item["game_id"], int(item["round"]))):
        state = row.get("state") or {}
        canonical = {
            "ts": row["ts"],
            "game_id": row["game_id"],
            "round": row.get("round"),
            "message": state.get("seller_message"),
            "decision": (row.get("action") or {}).get("decision"),
            "history": state.get("history"),
        }
        digest.update((json.dumps(canonical, sort_keys=True, separators=(",", ":")) + "\n").encode())

    turn_visibility = Counter(opponent_visibility(row) for row in text_rows)
    game_visibility: dict[str, set[str]] = defaultdict(set)
    for row in text_rows:
        game_visibility[str(row["game_id"])].add(opponent_visibility(row))
    visibility_games = Counter()
    for labels_seen in game_visibility.values():
        visibility_games["hidden" if labels_seen == {"hidden"} else "named"] += 1

    return {
        "slice": {"since": since, "until_exclusive": until},
        "all_persuasion_games": len(all_games),
        "seller_role_games": len(seller_games),
        "buyer_role_games": len(buyer_role_games),
        "buyer_decisions": len(rows),
        "buyer_games": len({str(row["game_id"]) for row in rows}),
        "text_decisions": len(text_rows),
        "text_games": len({str(row["game_id"]) for row in text_rows}),
        "binary_decisions": len(binary_rows),
        "binary_games": len({str(row["game_id"]) for row in binary_rows}),
        "labels": {name: labels.get(name, 0) for name in (
            "v1_negative", "v2_strict_miss", "v3_strict_miss", "other"
        )},
        "distinct_messages_by_label": {
            name: len(exact_messages.get(name, set()))
            for name in ("v1_negative", "v2_strict_miss", "v3_strict_miss", "other")
        },
        "strict_miss_decisions": len(strict),
        "strict_miss_games": len({str(row["game_id"]) for row in strict}),
        "purchased_strict_misses": len(purchased),
        "purchased_strict_miss_games": len({str(row["game_id"]) for row in purchased}),
        "passed_strict_misses": len(strict) - len(purchased),
        "purchased_outcomes": {
            "low": outcomes.get("low", 0),
            "high": outcomes.get("high", 0),
            "missing": outcomes.get("missing", 0),
        },
        "opponent_visibility_text_turns": dict(sorted(turn_visibility.items())),
        "opponent_visibility_text_games": dict(sorted(visibility_games.items())),
        "text_row_sha256": digest.hexdigest(),
    }


def assert_expected(summary: dict[str, Any], name: str) -> None:
    for key, expected in EXPECTED[name].items():
        actual = summary.get(key)
        if actual != expected:
            raise AssertionError(f"{name}.{key}: expected {expected!r}, got {actual!r}")


def main() -> None:
    args = parse_args()
    summary = audit(args.turns, args.since, args.until)
    if args.expect:
        assert_expected(summary, args.expect)
        print(f"PASS: {args.expect} parser-coverage slice matches the paper", file=sys.stderr)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
