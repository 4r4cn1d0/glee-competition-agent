#!/usr/bin/env python3
"""Generate the anonymous action-level evidence contract figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.0})
    stages = [
        ("Visible\nstate", "Eligibility"),
        ("Family\nplan", "Final owner"),
        ("Ordered\ngates", "Action changed"),
        ("Schema\nconversion", "Exact diff"),
        ("Returned\naction", "Local record"),
        ("Joined\noutcome", "All outcomes"),
    ]
    failures = [
        "Selected cohort",
        "Treatment leakage",
        "Unreachable gate",
        "Action overwritten",
        "Unverified receipt",
        "Missing retained",
    ]
    navy, pale, teal, coral = "#214761", "#E8F1F5", "#17807E", "#C9574E"
    fig, ax = plt.subplots(figsize=(7.2, 2.3), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.text(0.2, 3.72, "Action-level evidence contract", fontsize=11, weight="bold", color=navy)
    xs = [0.25, 2.25, 4.25, 6.25, 8.25, 10.25]
    for index, ((title, evidence), failure, x) in enumerate(zip(stages, failures, xs)):
        ax.add_patch(
            FancyBboxPatch(
                (x, 2.25),
                1.5,
                0.95,
                boxstyle="round,pad=0.04,rounding_size=0.08",
                linewidth=1.1,
                edgecolor=navy,
                facecolor=pale,
            )
        )
        ax.text(x + 0.75, 2.73, title, ha="center", va="center", weight="bold", color=navy)
        ax.text(x + 0.75, 1.82, evidence, ha="center", va="center", weight="bold", color=teal)
        ax.plot([x + 0.15, x + 1.35], [1.42, 1.42], color=coral, linewidth=1.1)
        ax.text(x + 0.75, 1.16, failure, ha="center", va="center", fontsize=7.1, color=coral)
        if index < len(xs) - 1:
            ax.add_patch(
                FancyArrowPatch(
                    (x + 1.57, 2.73),
                    (xs[index + 1] - 0.07, 2.73),
                    arrowstyle="-|>",
                    mutation_scale=9,
                    linewidth=1.0,
                    color=navy,
                )
            )
    fig.subplots_adjust(left=0.01, right=0.995, top=0.98, bottom=0.04)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
