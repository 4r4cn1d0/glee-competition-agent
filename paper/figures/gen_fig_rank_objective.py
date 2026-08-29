#!/usr/bin/env python3
"""Generate the rank-objective counterexample used in the paper."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = Path(__file__).resolve().parent
BLUE = "#0072B2"
ORANGE = "#D55E00"
GRAY = "#666666"


def percentile_map(payoff: np.ndarray | float) -> np.ndarray | float:
    """A valid monotone reference CDF for the constructive example."""
    return 1.0 / (1.0 + np.exp(-(np.asarray(payoff) - 5.0) / 2.5))


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 7.5,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "axes.titleweight": "bold",
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    x = np.linspace(0.0, 21.5, 500)
    action_a_payoff = 10.0
    action_b_payoffs = np.array([0.0, 21.0])
    expected_payoffs = np.array(
        [action_a_payoff, float(action_b_payoffs.mean())]
    )
    expected_percentiles = np.array(
        [
            float(percentile_map(action_a_payoff)),
            float(percentile_map(action_b_payoffs).mean()),
        ]
    )

    fig = plt.figure(figsize=(5.5, 1.72))
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=(1.62, 1.0),
        height_ratios=(1.0, 1.0),
        wspace=0.42,
        hspace=0.95,
    )

    ax_cdf = fig.add_subplot(grid[:, 0])
    ax_cdf.plot(x, percentile_map(x), color=GRAY, linewidth=1.6)
    ax_cdf.scatter(
        [action_a_payoff],
        [percentile_map(action_a_payoff)],
        color=BLUE,
        marker="o",
        s=30,
        zorder=3,
        label=r"$A$: payoff $10$ surely",
    )
    ax_cdf.scatter(
        action_b_payoffs,
        percentile_map(action_b_payoffs),
        facecolors="white",
        edgecolors=ORANGE,
        marker="s",
        linewidths=1.3,
        s=30,
        zorder=3,
        label=r"$B$: payoff $0$ or $21$ equally",
    )
    for value in (0.0, 10.0, 21.0):
        ax_cdf.vlines(
            value,
            0.0,
            percentile_map(value),
            color="#B8B8B8",
            linewidth=0.7,
            linestyle="--",
            zorder=1,
        )
    ax_cdf.set_xlim(-0.6, 22.0)
    ax_cdf.set_ylim(0.0, 1.02)
    ax_cdf.set_xticks([0, 5, 10, 15, 21])
    ax_cdf.set_yticks([0.0, 0.5, 1.0])
    ax_cdf.set_xlabel(r"Payoff $y$")
    ax_cdf.set_ylabel(r"Cell percentile $Q(y)$")
    ax_cdf.set_title("(a) Nonlinear percentile map", loc="left")
    ax_cdf.grid(axis="y", color="#D0D0D0", linewidth=0.5, alpha=0.55)
    ax_cdf.legend(
        loc="lower right",
        frameon=False,
        fontsize=6.6,
        handletextpad=0.45,
        borderaxespad=0.2,
    )

    labels = ["A", "B"]
    colors = [BLUE, ORANGE]
    hatches = ["", "///"]

    ax_payoff = fig.add_subplot(grid[0, 1])
    bars = ax_payoff.barh(labels, expected_payoffs, color=colors, height=0.55)
    for bar, hatch, value in zip(bars, hatches, expected_payoffs):
        bar.set_hatch(hatch)
        ax_payoff.text(
            value + 0.12,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            fontsize=7,
        )
    ax_payoff.set_xlim(0.0, 12.0)
    ax_payoff.set_xticks([0, 5, 10])
    ax_payoff.set_title("(b) Expected payoff", loc="left")
    ax_payoff.grid(axis="x", color="#D0D0D0", linewidth=0.5, alpha=0.55)

    ax_rank = fig.add_subplot(grid[1, 1])
    bars = ax_rank.barh(labels, expected_percentiles, color=colors, height=0.55)
    for bar, hatch, value in zip(bars, hatches, expected_percentiles):
        bar.set_hatch(hatch)
        ax_rank.text(
            value + 0.018,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}",
            va="center",
            fontsize=7,
        )
    ax_rank.set_xlim(0.0, 1.05)
    ax_rank.set_xticks([0.0, 0.5, 1.0])
    ax_rank.set_title("(c) Expected percentile", loc="left")
    ax_rank.grid(axis="x", color="#D0D0D0", linewidth=0.5, alpha=0.55)

    for axis in (ax_payoff, ax_rank):
        axis.tick_params(axis="both", which="major", pad=2)
        axis.invert_yaxis()

    fig.savefig(OUTPUT_DIR / "fig_rank_objective.pdf")
    fig.savefig(OUTPUT_DIR / "fig_rank_objective.png", dpi=300)


if __name__ == "__main__":
    main()
