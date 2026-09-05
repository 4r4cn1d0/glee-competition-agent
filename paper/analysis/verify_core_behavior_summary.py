#!/usr/bin/env python3
"""Verify descriptive core behavior aggregates from the bounded final audit.

Usage: .venv/bin/python paper/analysis/verify_core_behavior_summary.py OFFICIAL_EXPORT.json

Requires Python >= 3.10 because the reused replay validator uses strict zip.

Reads the exact private 245-game export and its existing local joins, reusing
the action-to-replay checks in analyze_final_window_outcomes.load_rows. Only
deidentified aggregates are emitted. No files, live controls, or network
resources are changed. These selected-state descriptions are not treatment
effects, and plan labels do not independently validate inference or parsing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from paper.analysis.analyze_final_window_outcomes import load_rows  # noqa: E402


EXPORT_SHA256 = "b777bfc314adb7ec4a522641118a39bebe0fb9153ce98030f8eaa49c8f06ca98"


def summarize(official_path: Path, games_dir: Path) -> dict[str, object]:
    """Validate the pinned cohort before aggregating any selected states."""
    with (ROOT / "paper/data/final_window_official_export_manifest.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        manifest = {row["field"]: row["value"] for row in csv.DictReader(handle)}
    assert manifest["sha256"] == EXPORT_SHA256
    assert hashlib.sha256(official_path.read_bytes()).hexdigest() == EXPORT_SHA256
    rows, _, matched_actions, _ = load_rows(official_path, games_dir)
    assert len(rows) == 245 and sum(matched_actions.values()) == 2_288

    information: Counter[str] = Counter()
    horizons: Counter[str] = Counter()
    hidden_capped_buyers: list[dict[str, object]] = []
    complete_unknown: list[dict[str, object]] = []
    complete_outcomes: Counter[str] = Counter()
    negotiation_outcomes: Counter[str] = Counter()
    seller_quality: Counter[tuple[str, bool]] = Counter()
    seller_bought: Counter[tuple[str, bool]] = Counter()
    low_positive_routes: Counter[str] = Counter()
    reset_directions: Counter[str] = Counter()
    reset_games: set[str] = set()
    seller_games = 0

    for row in rows:
        local_path = games_dir / f"{row['game_id']}.json"
        local = json.loads(local_path.read_text(encoding="utf-8"))
        config = local["config"]
        if row["family"] == "negotiation":
            complete = config["complete_information"]
            assert isinstance(complete, bool)
            known = config["horizon_known"]
            assert isinstance(known, bool)
            cap = config.get("max_rounds") if known else None
            assert not known or cap in (1, 10)
            information["complete" if complete else "hidden"] += 1
            horizons[f"known_{cap}" if known else "unknown"] += 1
            outcome = local["result"]["outcome"]
            negotiation_outcomes[outcome] += 1
            item = {
                "outcome": outcome,
                "rounds": local["rounds_played"],
                "rating_delta": row["rating_delta"],
            }
            if complete:
                # Do not infer hidden opponent values or hidden feasibility.
                assert config["player_2_value"] > config["player_1_value"]
                complete_outcomes[outcome] += 1
                if not known:
                    complete_unknown.append(item)
            if not complete and cap == 10 and row["role"] == "buyer":
                hidden_capped_buyers.append(item)

        if row["family"] != "persuasion":
            continue
        history = {entry["round"]: entry for entry in local["history"]}
        assert len(history) == len(local["history"])
        if row["role"] == "seller":
            seller_games += 1
            for turn in local["our_turns"]:
                plan = turn["plan"]
                observed = history[turn["round"]]
                quality = observed["quality"]
                positive = plan["recommend"]
                assert quality in ("high", "low") and isinstance(positive, bool)
                assert plan["quality_is_high"] is (quality == "high")
                assert isinstance(observed["bought"], bool)
                seller_quality[(quality, positive)] += 1
                seller_bought[(quality, positive)] += int(observed["bought"])
                if quality == "low" and positive:
                    reason = plan["reason"]
                    assert reason in (
                        "prior alone justifies purchase", "no valuations; tracking buyer"
                    )
                    route = "prior_value" if reason == "prior alone justifies purchase" else "unknown_value_history"
                    low_positive_routes[route] += 1
        else:
            for turn in local["our_turns"]:
                plan = turn["plan"]
                marker = "buyer_tight_credibility_reset_v1"
                if plan.get(marker):
                    assert marker in plan["gates_fired"]
                    direction = plan[f"{marker}_direction"]
                    assert direction in ("buy_to_pass", "pass_to_buy")
                    assert plan["buy"] is (direction == "pass_to_buy")
                    reset_directions[direction] += 1
                    reset_games.add(str(row["game_id"]))

    assert information == {"complete": 7, "hidden": 12}
    assert horizons == {"known_1": 3, "known_10": 8, "unknown": 8}
    assert negotiation_outcomes == {"agreement": 13, "walked_away": 3, "no_deal": 3}
    assert complete_outcomes == {"agreement": 6, "no_deal": 1}
    assert len(hidden_capped_buyers) == 3
    assert all(item["outcome"] == "agreement" and item["rounds"] == 10
               for item in hidden_capped_buyers)
    capped_mean = statistics.fmean(item["rating_delta"] for item in hidden_capped_buyers)
    assert math.isclose(capped_mean, -1.8, rel_tol=0, abs_tol=1e-10)
    assert len(complete_unknown) == 3
    assert sorted(item["rounds"] for item in complete_unknown) == [40, 96, 97]
    assert Counter(item["outcome"] for item in complete_unknown) == {"agreement": 2, "no_deal": 1}
    assert [item["rounds"] for item in complete_unknown if item["outcome"] == "no_deal"] == [96]
    assert seller_games == 22
    assert seller_quality == {("high", True): 230, ("low", True): 86, ("low", False): 124}
    assert seller_bought == {("high", True): 142, ("low", True): 67, ("low", False): 0}
    assert low_positive_routes == {"prior_value": 31, "unknown_value_history": 55}
    assert reset_directions == {"buy_to_pass": 10, "pass_to_buy": 5}
    assert len(reset_games) == 4

    return {
        "status": "PASS",
        "export_sha256": EXPORT_SHA256,
        "scope": {"assignments": 245, "rated_games": 244, "matched_valid_actions": 2288},
        "negotiation": {
            "games": 19,
            "information": dict(information),
            "horizons": dict(horizons),
            "outcomes": dict(negotiation_outcomes),
            "complete_positive_surplus_outcomes": dict(complete_outcomes),
            "hidden_ten_round_buyers": {
                "games": 3, "agreements": 3, "agreement_round": 10,
                "mean_displayed_rating_delta": round(capped_mean, 6),
            },
            "complete_unknown_horizon": {
                "games": 3, "terminal_rounds": [40, 96, 97],
                "agreements": 2, "no_deals": 1, "no_deal_round": 96,
            },
        },
        "persuasion": {
            "seller_games": seller_games,
            "seller_decisions": sum(seller_quality.values()),
            "high": {"positive": 230, "negative": 0, "purchased_after_positive": 142},
            "low": {"positive": 86, "negative": 124, "purchased_after_positive": 67,
                    "purchased_after_negative": 0},
            "low_positive_plan_routes": dict(low_positive_routes),
            "buyer_reset": {"games": len(reset_games), **dict(reset_directions)},
        },
        "interpretation": "Descriptive selected-state counts, not causal effects; plan labels are not independent parser or posterior validation.",
    }


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Python >= 3.10 is required; use the project .venv/bin/python.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("official_json", type=Path)
    parser.add_argument("--games-dir", type=Path, default=ROOT / "logs/composite/games")
    args = parser.parse_args()
    try:
        result = summarize(args.official_json, args.games_dir)
    except (AssertionError, OSError, ValueError, KeyError, TypeError):
        # The reused join validator may include private IDs in exceptions.
        # Do not echo those contexts into shareable aggregate output.
        raise SystemExit("FAIL: private-input validation did not pass; no records emitted.") from None
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
