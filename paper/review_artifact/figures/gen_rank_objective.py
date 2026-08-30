#!/usr/bin/env python3
"""Generate the finite payoff-to-rank reversal figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


BLUE, ORANGE, GRAY = "#0072B2", "#D55E00", "#666666"


def percentile_map(payoff: np.ndarray | float) -> np.ndarray | float:
    values = np.asarray(payoff)
    return np.where(values < 5.0, 0.0, np.where(values == 5.0, 0.5, 1.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 7.5})
    safe_payoff = 10.0
    risky_payoffs = np.array([0.0, 21.0])
    expected_payoffs = np.array([safe_payoff, risky_payoffs.mean()])
    expected_percentiles = np.array(
        [float(percentile_map(safe_payoff)), float(percentile_map(risky_payoffs).mean())]
    )
    fig = plt.figure(figsize=(5.6, 2.0), dpi=180)
    grid = fig.add_gridspec(2, 2, width_ratios=(1.62, 1.0), hspace=0.95, wspace=0.42)
    ax_map = fig.add_subplot(grid[:, 0])
    ax_map.step([-0.6, 5.0, 22.0], [0.0, 1.0, 1.0], where="post", color=GRAY, linewidth=1.6)
    ax_map.scatter([5.0], [0.5], facecolors="white", edgecolors=GRAY, s=24)
    ax_map.scatter([safe_payoff], [percentile_map(safe_payoff)], color=BLUE, s=30, label="A: 10 surely")
    ax_map.scatter(risky_payoffs, percentile_map(risky_payoffs), facecolors="white", edgecolors=ORANGE, marker="s", s=30, label="B: 0 or 21 equally")
    ax_map.set_xlim(-0.6, 22.0)
    ax_map.set_ylim(0.0, 1.02)
    ax_map.set_xticks([0, 5, 10, 15, 21])
    ax_map.set_yticks([0.0, 0.5, 1.0])
    ax_map.set_xlabel("Payoff")
    ax_map.set_ylabel("Empirical midrank")
    ax_map.set_title("(a) Reference multiset {5}", loc="left", weight="bold")
    ax_map.legend(frameon=False, fontsize=6.4, loc="lower right")
    for axis, values, title, limit in (
        (fig.add_subplot(grid[0, 1]), expected_payoffs, "(b) Expected payoff", 12.0),
        (fig.add_subplot(grid[1, 1]), expected_percentiles, "(c) Expected midrank", 1.05),
    ):
        bars = axis.barh(["A", "B"], values, color=[BLUE, ORANGE], height=0.55)
        bars[1].set_hatch("///")
        for bar, value in zip(bars, values):
            axis.text(value + limit * 0.015, bar.get_y() + bar.get_height() / 2, f"{value:.2f}", va="center", fontsize=7)
        axis.set_xlim(0.0, limit)
        axis.set_title(title, loc="left", weight="bold")
        axis.invert_yaxis()
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.22)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
