#!/usr/bin/env python3
"""Join the official Agent 5 dashboard export to the bounded local census.

The dashboard history records supply official per-game displayed rating changes.
The local game records supply the exact first returned-action timestamp and the
payoff/configuration fields needed by the frozen preperiod pooled-CDF proxy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from sim.percentile import percentile  # noqa: E402


EXPECTED_FAMILY = {"bargaining": 171, "negotiation": 19, "persuasion": 55}
EXPECTED_WINDOW_FAMILY = {
    ("preclose", "bargaining"): 19,
    ("preclose", "negotiation"): 19,
    ("preclose", "persuasion"): 25,
    ("close", "bargaining"): 152,
    ("close", "persuasion"): 30,
}
WINDOWS = {
    "preclose": (1787981256.596627, 1788007688.480755),
    # The CSV records the last returned action at 11:59:57.872063Z. Add one
    # microsecond because these programmatic intervals use an exclusive end.
    "close": (1788088111.586000, 1788091197.872064),
}
ROLE = {
    ("bargaining", "player_1"): "Alice",
    ("bargaining", "player_2"): "Bob",
    ("negotiation", "player_1"): "seller",
    ("negotiation", "player_2"): "buyer",
    ("persuasion", "player_1"): "seller",
    ("persuasion", "player_2"): "buyer",
}


def replay_actor(family: str, move: dict[str, object]) -> str:
    """Attribute a replay move from the public protocol order, failing closed."""
    round_number = int(move["round"])
    move_type = str(move["move_type"])
    if family == "bargaining":
        if move_type == "offer":
            return "player_1" if round_number % 2 else "player_2"
        if move_type == "decision":
            return "player_2" if round_number % 2 else "player_1"
    elif family == "negotiation":
        if move_type == "offer":
            return "player_1"
        if move_type == "decision":
            return "player_2" if round_number % 2 else "player_1"
    elif family == "persuasion":
        if move_type == "seller_message":
            return "player_1"
        if move_type == "buyer_decision":
            return "player_2"
    raise AssertionError(f"unknown replay phase: {family} {move_type}")


def canonical_action(
    family: str, action_type: str, payload: dict[str, object]
) -> tuple[str, dict[str, object]]:
    """Normalize the one known local/service name difference and wire scalars."""
    normalized = dict(payload)
    if family == "persuasion" and action_type in {"seller_message", "seller_recommendation"}:
        if "message" in normalized:
            return "seller_message", {"message": normalized["message"]}
        assert "decision" in normalized
        decision = normalized["decision"]
        if isinstance(decision, str):
            decision = decision.lower()
        return "seller_message", {"decision": decision}
    if action_type == "offer" or (family == "negotiation" and action_type == "decision"):
        normalized.setdefault("message", "")
    if "decision" in normalized and isinstance(normalized["decision"], str):
        normalized["decision"] = normalized["decision"].lower()
    return action_type, normalized


def assert_payload_equal(left: object, right: object, context: str) -> None:
    if isinstance(left, dict) and isinstance(right, dict):
        assert left.keys() == right.keys(), f"wire key mismatch in {context}"
        for key in left:
            assert_payload_equal(left[key], right[key], f"{context}.{key}")
        return
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        assert math.isclose(float(left), float(right), rel_tol=0, abs_tol=1e-6), context
        return
    assert left == right, f"wire value mismatch in {context}"


def iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def bootstrap_mean_ci(values: list[float], seed: int, draws: int = 20_000) -> list[float] | None:
    """Return a deterministic game-resampling percentile interval for the mean."""
    if not values:
        return None
    if len(values) == 1:
        return [values[0], values[0]]
    rng = random.Random(seed)
    n = len(values)
    means = [sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws)]
    means.sort()
    lo = means[math.floor(0.025 * (draws - 1))]
    hi = means[math.ceil(0.975 * (draws - 1))]
    return [lo, hi]


def summarize(values: list[float], seed: int) -> dict[str, object]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "sum": None, "min": None, "max": None, "mean_ci95": None}
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "sum": sum(values),
        "min": min(values),
        "max": max(values),
        "mean_ci95": bootstrap_mean_ci(values, seed),
    }


def first_action_window(local: dict[str, object]) -> tuple[str, float]:
    turns = local.get("our_turns") or []
    timestamps = [turn.get("ts") for turn in turns if isinstance(turn.get("ts"), (int, float))]
    if not timestamps:
        raise AssertionError(f"no returned-action timestamp for {local.get('game_id')}")
    first_ts = min(timestamps)
    matches = [name for name, (start, end) in WINDOWS.items() if start <= first_ts < end]
    if len(matches) != 1:
        raise AssertionError(f"first action {first_ts} falls outside the audited windows")
    return matches[0], first_ts


def load_rows(
    official_path: Path, games_dir: Path
) -> tuple[list[dict[str, object]], dict[str, object], Counter[str]]:
    doc = json.loads(official_path.read_text(encoding="utf-8"))
    assert doc["schema"] == "glee.agent5.official-final-windows/v1"
    assert doc["counts"] == EXPECTED_FAMILY
    assert doc["rated_games"] == 244
    assert doc["replay_error_count"] == 0
    assert len(doc["games"]) == 245

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    matched_actions: Counter[str] = Counter()
    matched_family_role: Counter[str] = Counter()
    for item in doc["games"]:
        history = item["history"]
        replay = item["replay"]
        game_id = history["game_id"]
        assert game_id not in seen
        seen.add(game_id)
        assert replay["game_id"] == game_id
        assert replay["game_family"] == history["game_family"]

        local_path = games_dir / f"{game_id}.json"
        assert local_path.exists(), f"missing local join for {game_id}"
        local = json.loads(local_path.read_text(encoding="utf-8"))
        family = history["game_family"]
        seat = history["your_player"]
        assert local["game_family"] == family
        assert local["your_player"] == seat
        window, first_ts = first_action_window(local)
        assert_payload_equal(local["result"], history["result"], f"{game_id}.history_result")
        assert_payload_equal(history["result"], replay["result"], f"{game_id}.replay_result")

        replay_moves = [
            move for move in replay.get("moves") or [] if replay_actor(family, move) == seat
        ]
        local_turns = local.get("our_turns") or []
        assert len(replay_moves) == len(local_turns), f"action count mismatch in {game_id}"
        for turn, replay_move in zip(local_turns, replay_moves, strict=True):
            local_type, local_payload = canonical_action(
                family, turn["action_type"], turn["action"]
            )
            replay_type, replay_payload = canonical_action(
                family, replay_move["move_type"], replay_move["move_data"]
            )
            assert turn["round"] == replay_move["round"], f"round mismatch in {game_id}"
            assert local_type == replay_type, f"action type mismatch in {game_id}"
            assert_payload_equal(local_payload, replay_payload, game_id)
            assert replay_move["is_valid"] is True, (
                f"invalid service move in {game_id} round {replay_move['round']} {replay_type}"
            )
            matched_actions[family] += 1
            matched_family_role[f"{family}:{ROLE[(family, seat)]}"] += 1

        official_payoff = history["result"].get(f"{seat}_payoff")
        local_payoff = local.get("our_payoff")
        if isinstance(official_payoff, (int, float)) and isinstance(local_payoff, (int, float)):
            assert math.isclose(float(official_payoff), float(local_payoff), rel_tol=0, abs_tol=0.011)

        delta = history.get("rating_delta")
        rated = isinstance(delta, (int, float))
        proxy = None
        if rated and isinstance(local_payoff, (int, float)):
            proxy = percentile(family, local["config"], seat, float(local_payoff))

        rows.append(
            {
                "game_id": game_id,
                "family": family,
                "seat": seat,
                "role": ROLE[(family, seat)],
                "window": window,
                "first_ts": first_ts,
                "rating_delta": float(delta) if rated else None,
                "payoff": float(local_payoff) if isinstance(local_payoff, (int, float)) else None,
                "zero": bool(rated and float(local_payoff) == 0.0),
                "proxy": proxy,
            }
        )

    assert Counter(row["family"] for row in rows) == Counter(EXPECTED_FAMILY)
    assert Counter((row["window"], row["family"]) for row in rows) == Counter(EXPECTED_WINDOW_FAMILY)
    assert sum(row["rating_delta"] is not None for row in rows) == 244
    assert matched_actions == Counter({"bargaining": 1001, "negotiation": 190, "persuasion": 1097})
    expected_role_actions = Counter(
        {
            "bargaining:Alice": 427,
            "bargaining:Bob": 574,
            "negotiation:seller": 87,
            "negotiation:buyer": 103,
            "persuasion:seller": 440,
            "persuasion:buyer": 657,
        }
    )
    assert matched_family_role == expected_role_actions
    return rows, doc, matched_actions, matched_family_role


def group_summary(rows: list[dict[str, object]], family: str, role: str | None) -> dict[str, object]:
    selected = [row for row in rows if row["family"] == family and (role is None or row["role"] == role)]
    rated = [row for row in selected if row["rating_delta"] is not None]
    deltas = [float(row["rating_delta"]) for row in rated]
    proxies = [float(row["proxy"]) for row in rated if row["proxy"] is not None]
    first = [float(row["first_ts"]) for row in selected]
    return {
        "family": family,
        "role": role or "all",
        "assigned": len(selected),
        "rated": len(rated),
        "zeros": sum(bool(row["zero"]) for row in rated),
        "zero_rate": sum(bool(row["zero"]) for row in rated) / len(rated) if rated else None,
        "proxy": summarize(proxies, 20260831),
        "rating_delta": summarize(deltas, 20260831),
        "first_action_range_utc": [iso_utc(min(first)), iso_utc(max(first))],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("official_json", type=Path)
    parser.add_argument("--games-dir", type=Path, default=REPO / "logs" / "composite" / "games")
    args = parser.parse_args()

    rows, doc, matched_actions, matched_family_role = load_rows(args.official_json, args.games_dir)
    groups: list[tuple[str, str | None]] = [
        ("bargaining", None),
        ("bargaining", "Alice"),
        ("bargaining", "Bob"),
        ("negotiation", None),
        ("negotiation", "seller"),
        ("negotiation", "buyer"),
        ("persuasion", None),
        ("persuasion", "seller"),
        ("persuasion", "buyer"),
    ]
    model_path = REPO / "models" / "percentile_cdf_v3.json"
    output = {
        "source": {
            "official_json": str(args.official_json.resolve()),
            "captured_at": doc["captured_at"],
            "player_id": doc["player_id"],
            "local_games_dir": str(args.games_dir.resolve()),
            "proxy_model": str(model_path),
            "proxy_model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "bootstrap": "20,000 game-level resamples; seed 20260831 for every reported mean",
        },
        "validation": {
            "assignments": len(rows),
            "rated": sum(row["rating_delta"] is not None for row in rows),
            "all_official_ids_joined_locally": True,
            "local_actions_matched_to_valid_replay_moves": sum(matched_actions.values()),
            "matched_actions_by_family": dict(matched_actions),
            "matched_actions_by_family_role": dict(matched_family_role),
            "window_family_counts": {
                f"{window}:{family}": count for (window, family), count in EXPECTED_WINDOW_FAMILY.items()
            },
        },
        "groups": [group_summary(rows, family, role) for family, role in groups],
    }
    print(json.dumps(output, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
