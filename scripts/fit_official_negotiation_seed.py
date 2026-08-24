#!/usr/bin/env python3
"""Build the full-configuration negotiation CDF from the official GLEE corpus.

The competition documentation says payoffs are ranked against the same
configuration and role, and explicitly lists valuations among the 960 grid
axes.  The older local v3 model intentionally pooled the hidden counterpart
value because our own live logs do not reveal it.  That pooling is useful for
rough diagnostics but is not the competition's scoring key.

This fitter consumes the public ``Data/llm_vs_llm/negotiation`` directory from
https://github.com/eilamshapira/GLEE and writes all 1,152 role-specific cells:
3 horizons x 2 information conditions x 2 message modes x 3 scales x 16 value
pairs x 2 roles.  Payoffs are normalized by the monetary scale but scale stays
in the key, matching the literal configuration.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "models" / "negotiation_seed_cdf_full.json"
ACCEPT = {"AcceptOffer", "BuyFromJhon", "SellToJhon"}


def cell_key(horizon: int, complete: bool, messages: bool, scale: int,
             seller_mult: float, buyer_mult: float, role: str) -> str:
    return "|".join(str(value) for value in (
        "negotiation-seed", horizon, complete, messages, scale,
        f"{seller_mult:.1f}", f"{buyer_mult:.1f}", role,
    ))


def _last_price(rows: list[dict]) -> float | None:
    for row in reversed(rows):
        raw = str(row.get("product_price") or "").replace(",", "").strip()
        if not raw:
            continue
        try:
            price = float(raw)
        except ValueError:
            continue
        if math.isfinite(price):
            return price
    return None


def build(data_root: Path) -> dict:
    cells = defaultdict(list)
    games = 0
    decisions = defaultdict(int)
    failures = []
    for config_path in data_root.rglob("config.json"):
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            args = config["game_args"]
            scale = int(float(args["product_price_order"]))
            seller_mult = float(args["seller_value"])
            buyer_mult = float(args["buyer_value"])
            horizon = int(args["max_rounds"])
            complete = bool(args["complete_information"])
            messages = bool(args["messages_allowed"])
            with config_path.with_name("game.csv").open(
                    newline="", encoding="utf-8-sig", errors="replace") as fh:
                rows = list(csv.DictReader(fh))
            decision = str(rows[-1].get("decision") or "").strip() if rows else ""
            decisions[decision] += 1
            if decision == "RejectOffer":
                seller_payoff = buyer_payoff = 0.0
            elif decision in ACCEPT:
                price = _last_price(rows)
                if price is None:
                    raise ValueError("accepted game has no finite price")
                normalized_price = price / scale
                seller_payoff = normalized_price - seller_mult
                buyer_payoff = buyer_mult - normalized_price
            else:
                raise ValueError(f"unknown terminal decision {decision!r}")
            cells[cell_key(horizon, complete, messages, scale, seller_mult,
                           buyer_mult, "seller")].append(round(seller_payoff, 8))
            cells[cell_key(horizon, complete, messages, scale, seller_mult,
                           buyer_mult, "buyer")].append(round(buyer_payoff, 8))
            games += 1
        except Exception as exc:  # report every malformed official artifact
            failures.append(f"{config_path}: {exc}")

    if failures:
        sample = "\n".join(failures[:10])
        raise RuntimeError(f"failed to parse {len(failures)} game(s):\n{sample}")
    sizes = [len(values) for values in cells.values()]
    if games != 32_403 or len(cells) != 1_152 or min(sizes, default=0) < 50:
        raise RuntimeError(
            f"official-corpus shape drift: games={games}, cells={len(cells)}, "
            f"min_cell={min(sizes, default=0)}")
    return {
        "_schema": "glee.negotiation_seed_cdf/full-v1",
        "_source": "https://github.com/eilamshapira/GLEE",
        "_games": games,
        "_role_samples": games * 2,
        "_terminal_decisions": dict(sorted(decisions.items())),
        "cells": {key: sorted(values) for key, values in sorted(cells.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_root", type=Path,
                        help="official Data/llm_vs_llm/negotiation directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    options = parser.parse_args()
    document = build(options.data_root)
    options.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = options.out.with_suffix(options.out.suffix + ".tmp")
    temporary.write_text(json.dumps(document, separators=(",", ":")),
                         encoding="utf-8")
    os.replace(temporary, options.out)
    sizes = [len(values) for values in document["cells"].values()]
    print(f"fitted {document['_games']:,} official games -> "
          f"{len(sizes):,} exact role cells (n={min(sizes)}..{max(sizes)}) -> "
          f"{options.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
