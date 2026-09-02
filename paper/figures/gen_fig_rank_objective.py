#!/usr/bin/env python3
"""Generate the rank-objective counterexample used in the paper."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


OUTPUT_DIR = Path(__file__).resolve().parent
BLUE = "#0072B2"
ORANGE = "#D55E00"
ORANGE_LIGHT = "#F7D9CA"
GRAY = "#666666"


def percentile_map(payoff: np.ndarray | float) -> np.ndarray | float:
    """Exact-equality midrank against the finite reference multiset D={5}."""
    values = np.asarray(payoff)
    return np.where(values < 5.0, 0.0, np.where(values == 5.0, 0.5, 1.0))


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
            "savefig.bbox": None,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

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

    fig = plt.figure(figsize=(5.8, 2.4))
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=(1.62, 1.0),
        height_ratios=(1.0, 1.0),
        wspace=0.56,
        hspace=1.45,
    )

    ax_cdf = fig.add_subplot(grid[:, 0])
    ax_cdf.step(
        [-0.6, 5.0, 22.0],
        [0.0, 1.0, 1.0],
        where="post",
        color=GRAY,
        linewidth=1.6,
    )
    ax_cdf.scatter(
        [5.0],
        [0.5],
        facecolors="white",
        edgecolors=GRAY,
        linewidths=1.2,
        s=24,
        zorder=4,
    )
    ax_cdf.scatter(
        [action_a_payoff],
        [percentile_map(action_a_payoff)],
        color=BLUE,
        marker="o",
        s=30,
        zorder=3,
    )
    ax_cdf.scatter(
        action_b_payoffs,
        percentile_map(action_b_payoffs),
        facecolors=ORANGE_LIGHT,
        edgecolors=ORANGE,
        marker="s",
        linewidths=1.3,
        s=30,
        zorder=3,
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
    ax_cdf.set_ylim(-0.04, 1.04)
    ax_cdf.set_xticks([0, 5, 10, 15, 21])
    ax_cdf.set_yticks([0.0, 0.5, 1.0])
    ax_cdf.set_xlabel(r"Payoff $y$")
    ax_cdf.set_ylabel(r"Cell percentile $Q_D(y)$")
    ax_cdf.set_title(r"(a) Midrank map for $D=\{5\}$", loc="left")
    ax_cdf.set_axisbelow(True)
    ax_cdf.grid(axis="y", color="#D0D0D0", linewidth=0.5, alpha=0.55)
    ax_cdf.annotate(
        r"tie: $Q_D(5)=0.5$",
        xy=(5.0, 0.5),
        xytext=(6.1, 0.38),
        color="#4A4A4A",
        fontsize=7.0,
        arrowprops={"arrowstyle": "-", "color": GRAY, "linewidth": 0.7},
    )

    labels = ["A: sure", "B: lottery"]
    bar_facecolors = [BLUE, ORANGE_LIGHT]
    bar_edgecolors = [BLUE, ORANGE]
    hatches = ["", "///"]

    ax_payoff = fig.add_subplot(grid[0, 1])
    bars = ax_payoff.barh(
        labels,
        expected_payoffs,
        color=bar_facecolors,
        edgecolor=bar_edgecolors,
        linewidth=0.8,
        height=0.55,
    )
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
    ax_payoff.set_xlabel("Expected payoff")
    ax_payoff.set_title("(b) Money criterion", loc="left")
    ax_payoff.set_axisbelow(True)
    ax_payoff.grid(axis="x", color="#D0D0D0", linewidth=0.5, alpha=0.55)

    ax_rank = fig.add_subplot(grid[1, 1])
    bars = ax_rank.barh(
        labels,
        expected_percentiles,
        color=bar_facecolors,
        edgecolor=bar_edgecolors,
        linewidth=0.8,
        height=0.55,
    )
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
    ax_rank.set_xlabel("Expected cell percentile")
    ax_rank.set_title("(c) Rank criterion", loc="left")
    ax_rank.set_axisbelow(True)
    ax_rank.grid(axis="x", color="#D0D0D0", linewidth=0.5, alpha=0.55)

    for axis in (ax_payoff, ax_rank):
        axis.tick_params(axis="both", which="major", pad=2)
        axis.invert_yaxis()

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=GRAY,
            marker="o",
            markerfacecolor="white",
            markeredgecolor=GRAY,
            linewidth=1.5,
            markersize=4.2,
            label=r"Reference map $Q_D(y)$",
        ),
        (
            Line2D(
                [0],
                [0],
                color=BLUE,
                marker="o",
                linestyle="none",
                markersize=5,
            ),
            Patch(facecolor=BLUE, edgecolor=BLUE, linewidth=0.8),
        ),
        (
            Line2D(
                [0],
                [0],
                color=ORANGE,
                marker="s",
                markerfacecolor=ORANGE_LIGHT,
                markeredgewidth=1.2,
                linestyle="none",
                markersize=5,
            ),
            Patch(
                facecolor=ORANGE_LIGHT,
                edgecolor=ORANGE,
                hatch="///",
                linewidth=0.8,
            ),
        ),
    ]
    fig.legend(
        handles=legend_handles,
        labels=[
            r"Reference map $Q_D(y)$",
            r"$A$: sure payoff $10$",
            r"$B$: payoff $0$ or $21$, each with probability $1/2$",
        ],
        handler_map={tuple: HandlerTuple(ndivide=None, pad=0.25)},
        loc="lower center",
        bbox_to_anchor=(0.5, 0.005),
        ncol=3,
        frameon=True,
        fancybox=False,
        facecolor="white",
        edgecolor="#A8A8A8",
        fontsize=6.8,
        handlelength=2.2,
        handletextpad=0.5,
        columnspacing=1.0,
        borderpad=0.35,
    )
    fig.subplots_adjust(left=0.095, right=0.98, top=0.90, bottom=0.31)

    fig.savefig(OUTPUT_DIR / "fig_rank_objective.pdf")
    fig.savefig(OUTPUT_DIR / "fig_rank_objective.png", dpi=300)


if __name__ == "__main__":
    main()
