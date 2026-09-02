#!/usr/bin/env python3
"""Generate a wall-clock-free descriptive rating trajectory."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rating_trajectory_relative.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.0})
    fig, ax = plt.subplots(figsize=(6.4, 2.8), dpi=180)
    specs = [
        ("bargaining", "Bargaining", "#0072B2", "o", "-"),
        ("negotiation", "Negotiation", "#D55E00", "s", "--"),
        ("persuasion", "Persuasion", "#009E73", "^", ":"),
    ]
    for key, label, color, marker, linestyle in specs:
        x = [int(row["sequence_index"]) for row in rows if row[key]]
        y = [float(row[key]) for row in rows if row[key]]
        ax.plot(
            x,
            y,
            label=label,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.45,
            markersize=4.2,
        )
    ax.axvline(11, color="#6E6E6E", linewidth=0.8, linestyle=(0, (2, 2)), alpha=0.8)
    ax.text(10.92, 2040, "pre-close bank", fontsize=6.8, color="#555555", rotation=90, va="bottom", ha="right")
    ax.annotate(
        "official close",
        xy=(12, 2804.82),
        xytext=(11.1, 2870),
        fontsize=7.2,
        arrowprops={"arrowstyle": "->", "color": "#666666", "linewidth": 0.7},
    )
    ax.set_xlim(1, 12.4)
    ax.set_ylim(1980, 2910)
    ax.set_xlabel("Relative checkpoint order")
    ax.set_ylabel("Displayed family rating")
    ax.set_title("Selected display-rating checkpoints", loc="left", fontsize=10, weight="bold")
    ax.grid(axis="y", color="#BEBEBE", linewidth=0.5, linestyle="--", alpha=0.55)
    ax.legend(frameon=False, ncol=3, fontsize=7, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.88, bottom=0.18)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
