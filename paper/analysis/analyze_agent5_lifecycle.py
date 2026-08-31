#!/usr/bin/env python3
"""Build a descriptive Agent 5 lifecycle census from the private local archive.

The analysis unit is an assigned game. Development eras are operational time
segments, not treatments. The script never conditions a family summary on a
successful agreement or completed deal. It reads logs but writes only aggregate
CSV files under paper/data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
GAMES_DIR = ROOT / "logs" / "composite" / "games"
RATINGS_PATH = ROOT / "logs" / "ratings_history.jsonl"
DATA_DIR = ROOT / "paper" / "data"


@dataclass(frozen=True)
class Era:
    key: str
    label: str
    start_ts: float
    end_ts: float
    boundary_basis: str


def utc_ts(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


# The local monitor continued polling after the competition closed and the
# endpoint stopped changing. Freeze the paper's trajectory at the first settled
# post-close poll so reruns cannot add duplicate observations.
RATING_CUTOFF_UTC = "2026-08-30T12:01:32.549750Z"
RATING_CUTOFF_TS = utc_ts(RATING_CUTOFF_UTC)


ERAS = (
    Era(
        "rapid_search",
        "Rapid search",
        float("-inf"),
        utc_ts("2026-08-22T10:54:50Z"),
        "first local record to identical-fleet baseline epoch",
    ),
    Era(
        "measurement_rank_pivot",
        "Measurement and rank pivot",
        utc_ts("2026-08-22T10:54:50Z"),
        utc_ts("2026-08-24T20:05:52Z"),
        "identical-fleet baseline to final randomized-arm shutdown",
    ),
    Era(
        "deterministic_assembly",
        "Deterministic assembly",
        utc_ts("2026-08-24T20:05:52Z"),
        utc_ts("2026-08-29T05:27:36.596627Z"),
        "randomized-arm shutdown to first declared final-policy turn",
    ),
    Era(
        "final_audit",
        "Final audited policy",
        utc_ts("2026-08-29T05:27:36.596627Z"),
        utc_ts("2026-08-30T12:00:00Z"),
        "first declared final-policy turn to competition close",
    ),
)

FAMILIES = ("bargaining", "negotiation", "persuasion")


def iso_utc(ts: float | None) -> str:
    if ts is None or not math.isfinite(ts):
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def era_for(ts: float) -> Era | None:
    for era in ERAS:
        if era.start_ts <= ts < era.end_ts:
            return era
    return None


def first_turn_ts(game: dict[str, Any]) -> float | None:
    values = []
    for turn in game.get("our_turns") or []:
        value = turn.get("ts")
        if isinstance(value, (int, float)) and math.isfinite(value):
            values.append(float(value))
    return min(values) if values else None


def role_for(game: dict[str, Any]) -> str:
    family = game.get("game_family")
    player = game.get("your_player")
    if family == "bargaining":
        return "Alice" if player == "player_1" else "Bob"
    config = game.get("config") or {}
    role = config.get("player_1_role" if player == "player_1" else "player_2_role")
    if isinstance(role, str) and role:
        return role.lower()
    if family in {"negotiation", "persuasion"}:
        return "seller" if player == "player_1" else "buyer"
    return str(player or "unknown")


def normalized_outcome(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "missing"
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "no_deal": "no_deal",
        "nodeal": "no_deal",
        "walkaway": "walk",
        "walk_away": "walk",
        "walked_away": "walk",
        "agreement": "agreement",
        "agreed": "agreement",
        "completed": "completed",
        "timeout": "timeout",
        "timed_out": "timeout",
        "invalid_moves": "invalid",
        "invalid_moves_exceeded": "invalid",
        "invalid": "invalid",
        "abandoned": "abandoned",
        "failed": "failed",
    }
    return aliases.get(key, key)


def action_semantics(family: str, turn: dict[str, Any]) -> str:
    action = turn.get("action") or {}
    plan = turn.get("plan") or {}
    phase = str(turn.get("phase") or "").lower()
    action_type = str(turn.get("action_type") or "").lower()

    if family == "bargaining":
        if "alice_gain" in action or "bob_gain" in action or action_type == "offer":
            return "offer"
        decision = str(action.get("decision") or action.get("action") or "").lower()
        if "accept" in decision:
            return "accept"
        if "walk" in decision:
            return "walk"
        if "reject" in decision:
            return "reject"

    if family == "negotiation":
        if "product_price" in action or action_type == "offer":
            return "offer_or_counter"
        decision = str(action.get("decision") or action.get("action") or "").lower()
        if "accept" in decision:
            return "accept"
        if "walk" in decision:
            return "walk"
        if "reject" in decision:
            return "reject_or_counter"

    if family == "persuasion":
        if "seller" in phase or action_type == "seller_message":
            recommend = plan.get("recommend")
            if isinstance(recommend, bool):
                return "seller_positive" if recommend else "seller_negative"
            message = str(action.get("message") or "").strip().lower()
            if message in {"yes", "true", "1", "buy", "positive"}:
                return "seller_positive"
            if message in {"no", "false", "0", "pass", "negative"}:
                return "seller_negative"
            return "seller_other"
        if "buyer" in phase or action_type == "buyer_decision":
            buy = plan.get("buy")
            if isinstance(buy, bool):
                return "buyer_buy" if buy else "buyer_pass"
            decision = str(
                action.get("decision")
                or action.get("action")
                or action.get("message")
                or ""
            ).strip().lower()
            if decision in {"yes", "true", "1", "buy", "accept"}:
                return "buyer_buy"
            if decision in {"no", "false", "0", "pass", "reject"}:
                return "buyer_pass"
            return "buyer_other"

    return f"other:{action_type or phase or 'unknown'}"


def aggregate_key(era: str, family: str) -> tuple[str, str]:
    return era, family


def update_game_bucket(bucket: Counter[str], game: dict[str, Any], ts: float) -> None:
    family = str(game.get("game_family") or "unknown")
    role = role_for(game)
    status = normalized_outcome(game.get("status"))
    result = game.get("result") or (game.get("config") or {}).get("result") or {}
    outcome = normalized_outcome(result.get("outcome"))
    payoff = game.get("our_payoff")

    bucket["assignments"] += 1
    bucket[f"role:{role}"] += 1
    bucket[f"status:{status}"] += 1
    bucket[f"outcome:{outcome}"] += 1
    bucket["actions"] += len(game.get("our_turns") or [])
    bucket["first_ts_sum"] += ts

    if isinstance(payoff, (int, float)) and math.isfinite(payoff):
        bucket["payoff_observed"] += 1
        bucket["payoff_sum"] += float(payoff)
        if abs(float(payoff)) <= 1e-9:
            bucket["zero_payoff"] += 1
        if float(payoff) <= 1e-9:
            bucket["nonpositive_payoff"] += 1

        config = game.get("config") or {}
        if family == "bargaining":
            scale = config.get("money_to_divide")
        elif family == "persuasion":
            scale = config.get("product_price")
        else:
            scale = None
        if isinstance(scale, (int, float)) and math.isfinite(scale) and scale > 0:
            bucket["normalized_payoff_observed"] += 1
            bucket["normalized_payoff_sum"] += float(payoff) / float(scale)

    for turn in game.get("our_turns") or []:
        semantic = action_semantics(family, turn)
        bucket[f"action:{semantic}"] += 1
        source = str(turn.get("source") or "missing")
        bucket[f"source:{source}"] += 1
        if turn.get("error") not in (None, "", False):
            bucket["logged_action_errors"] += 1


def bucket_row(
    era: Era | None,
    family: str,
    bucket: Counter[str],
    first_ts: float | None,
    last_ts: float | None,
) -> dict[str, Any]:
    n = bucket["assignments"]
    payoff_n = bucket["payoff_observed"]
    norm_n = bucket["normalized_payoff_observed"]
    row: dict[str, Any] = {
        "era": era.key if era else "lifetime",
        "era_label": era.label if era else "Lifetime local archive",
        "boundary_basis": era.boundary_basis if era else "all timestamped local Agent 5 assignments",
        "start_utc": iso_utc(first_ts),
        "end_utc": iso_utc(last_ts),
        "family": family,
        "assignments": n,
        "actions": bucket["actions"],
        "payoff_observed": payoff_n,
        "zero_payoff": bucket["zero_payoff"],
        "zero_rate": bucket["zero_payoff"] / payoff_n if payoff_n else "",
        "nonpositive_payoff": bucket["nonpositive_payoff"],
        "nonpositive_rate": bucket["nonpositive_payoff"] / payoff_n if payoff_n else "",
        "mean_payoff": bucket["payoff_sum"] / payoff_n if payoff_n else "",
        "mean_normalized_payoff": bucket["normalized_payoff_sum"] / norm_n if norm_n else "",
        "normalized_payoff_observed": norm_n,
        "logged_action_errors": bucket["logged_action_errors"],
    }
    for role in ("Alice", "Bob", "seller", "buyer", "unknown"):
        row[f"role_{role.lower()}"] = bucket[f"role:{role}"]
    for status in ("completed", "failed", "active", "missing"):
        row[f"status_{status}"] = bucket[f"status:{status}"]
    for outcome in (
        "agreement",
        "completed",
        "no_deal",
        "walk",
        "timeout",
        "invalid",
        "abandoned",
        "failed",
        "missing",
    ):
        row[f"outcome_{outcome}"] = bucket[f"outcome:{outcome}"]
    for semantic in (
        "offer",
        "accept",
        "reject",
        "walk",
        "offer_or_counter",
        "reject_or_counter",
        "seller_positive",
        "seller_negative",
        "seller_other",
        "buyer_buy",
        "buyer_pass",
        "buyer_other",
    ):
        row[f"action_{semantic}"] = bucket[f"action:{semantic}"]
    row["source_heuristic"] = bucket["source:heuristic"]
    row["source_llm"] = bucket["source:llm"]
    row["source_missing"] = bucket["source:missing"]
    known_action_total = sum(
        value for key, value in bucket.items() if key.startswith("action:") and not key.startswith("action:other:")
    )
    row["action_other"] = bucket["actions"] - known_action_total
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{lineno}: {exc}") from exc
            if isinstance(value, dict):
                yield value


def rating_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    snapshots: list[dict[str, Any]] = []
    for record in iter_jsonl(RATINGS_PATH):
        ts = record.get("ts")
        composite = record.get("composite")
        if not isinstance(ts, (int, float)) or not isinstance(composite, dict):
            continue
        if float(ts) > RATING_CUTOFF_TS:
            continue
        row: dict[str, Any] = {"timestamp_utc": iso_utc(float(ts)), "timestamp": float(ts)}
        usable = True
        ratings = []
        for family in FAMILIES:
            value = composite.get(family)
            if not isinstance(value, list) or len(value) < 2:
                usable = False
                break
            rating, games = value[:2]
            row[f"{family}_rating"] = rating
            row[f"{family}_games"] = games
            ratings.append(float(rating))
        if usable:
            row["mean_family_rating"] = sum(ratings) / len(ratings)
            snapshots.append(row)

    snapshots.sort(key=lambda row: float(row["timestamp"]))
    era_rows: list[dict[str, Any]] = []
    for era in ERAS:
        eligible = [
            row for row in snapshots if era.start_ts <= float(row["timestamp"]) < era.end_ts
        ]
        if not eligible:
            continue
        first, last = eligible[0], eligible[-1]
        row = {
            "era": era.key,
            "era_label": era.label,
            "boundary_basis": era.boundary_basis,
            "first_snapshot_utc": first["timestamp_utc"],
            "last_snapshot_utc": last["timestamp_utc"],
            "snapshots": len(eligible),
        }
        for family in FAMILIES:
            row[f"{family}_rating_first"] = first[f"{family}_rating"]
            row[f"{family}_rating_last"] = last[f"{family}_rating"]
            row[f"{family}_rating_change"] = (
                float(last[f"{family}_rating"]) - float(first[f"{family}_rating"])
            )
            row[f"{family}_games_first"] = first[f"{family}_games"]
            row[f"{family}_games_last"] = last[f"{family}_games"]
            row[f"{family}_game_increments"] = (
                int(last[f"{family}_games"]) - int(first[f"{family}_games"])
            )
        row["mean_family_rating_first"] = first["mean_family_rating"]
        row["mean_family_rating_last"] = last["mean_family_rating"]
        row["mean_family_rating_change"] = (
            float(last["mean_family_rating"]) - float(first["mean_family_rating"])
        )
        era_rows.append(row)
    return snapshots, era_rows


def main() -> None:
    if not GAMES_DIR.is_dir():
        raise SystemExit(f"missing {GAMES_DIR}")

    era_buckets: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    life_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    daily_buckets: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    time_bounds: dict[tuple[str, str], list[float]] = defaultdict(list)
    life_bounds: dict[str, list[float]] = defaultdict(list)
    daily_bounds: dict[tuple[str, str], list[float]] = defaultdict(list)
    parse_errors: list[str] = []
    no_turn_timestamp = 0

    paths = sorted(GAMES_DIR.glob("*.json"))
    for index, path in enumerate(paths, 1):
        try:
            with path.open("r", encoding="utf-8") as handle:
                game = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            parse_errors.append(f"{path.name}: {exc}")
            continue
        if not isinstance(game, dict):
            parse_errors.append(f"{path.name}: non-object JSON")
            continue
        family = str(game.get("game_family") or "unknown")
        if family not in FAMILIES:
            parse_errors.append(f"{path.name}: unexpected family {family}")
            continue
        ts = first_turn_ts(game)
        if ts is None:
            no_turn_timestamp += 1
            continue
        era = era_for(ts)
        if era is None:
            parse_errors.append(f"{path.name}: timestamp outside declared eras {ts}")
            continue

        key = aggregate_key(era.key, family)
        update_game_bucket(era_buckets[key], game, ts)
        time_bounds[key].append(ts)
        update_game_bucket(life_buckets[family], game, ts)
        life_bounds[family].append(ts)
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        day_key = (day, family)
        update_game_bucket(daily_buckets[day_key], game, ts)
        daily_bounds[day_key].append(ts)

        if index % 5000 == 0:
            print(f"scanned {index}/{len(paths)} game files", flush=True)

    if parse_errors:
        preview = "\n".join(parse_errors[:20])
        raise RuntimeError(f"encountered {len(parse_errors)} archive errors:\n{preview}")

    era_rows: list[dict[str, Any]] = []
    for era in ERAS:
        for family in FAMILIES:
            key = aggregate_key(era.key, family)
            values = time_bounds.get(key, [])
            era_rows.append(
                bucket_row(
                    era,
                    family,
                    era_buckets[key],
                    min(values) if values else None,
                    max(values) if values else None,
                )
            )

    lifetime_rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        values = life_bounds.get(family, [])
        lifetime_rows.append(
            bucket_row(
                None,
                family,
                life_buckets[family],
                min(values) if values else None,
                max(values) if values else None,
            )
        )

    daily_rows: list[dict[str, Any]] = []
    for day, family in sorted(daily_buckets):
        values = daily_bounds[(day, family)]
        row = bucket_row(
            None,
            family,
            daily_buckets[(day, family)],
            min(values) if values else None,
            max(values) if values else None,
        )
        row["era"] = day
        row["era_label"] = f"UTC day {day}"
        row["boundary_basis"] = "calendar-day descriptive bin"
        daily_rows.append(row)

    snapshots, rating_eras = rating_rows()
    for row in snapshots:
        row.pop("timestamp", None)

    write_csv(DATA_DIR / "agent5_lifecycle_era_census.csv", era_rows)
    write_csv(DATA_DIR / "agent5_lifecycle_family_census.csv", lifetime_rows)
    write_csv(DATA_DIR / "agent5_lifecycle_daily_census.csv", daily_rows)
    write_csv(DATA_DIR / "agent5_lifecycle_rating_snapshots.csv", snapshots)
    write_csv(DATA_DIR / "agent5_lifecycle_rating_eras.csv", rating_eras)
    rating_path = DATA_DIR / "agent5_lifecycle_rating_snapshots.csv"
    write_csv(
        DATA_DIR / "agent5_lifecycle_manifest.csv",
        [
            {
                "artifact": rating_path.name,
                "source": str(RATINGS_PATH.relative_to(ROOT)),
                "cutoff_utc_inclusive": RATING_CUTOFF_UTC,
                "rows": len(snapshots),
                "sha256": hashlib.sha256(rating_path.read_bytes()).hexdigest(),
            }
        ],
    )

    print(
        json.dumps(
            {
                "game_files": len(paths),
                "timestamped_games": sum(row["assignments"] for row in lifetime_rows),
                "no_turn_timestamp": no_turn_timestamp,
                "rating_snapshots": len(snapshots),
                "outputs": [
                    "paper/data/agent5_lifecycle_era_census.csv",
                    "paper/data/agent5_lifecycle_family_census.csv",
                    "paper/data/agent5_lifecycle_daily_census.csv",
                    "paper/data/agent5_lifecycle_rating_snapshots.csv",
                    "paper/data/agent5_lifecycle_rating_eras.csv",
                    "paper/data/agent5_lifecycle_manifest.csv",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
