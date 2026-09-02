#!/usr/bin/env python3
"""Generate the finite payoff-to-rank reversal figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.legend_handler import HandlerTuple  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


BLUE, ORANGE, ORANGE_LIGHT, GRAY = "#0072B2", "#D55E00", "#F7D9CA", "#666666"


def percentile_map(payoff: np.ndarray | float) -> np.ndarray | float:
    values = np.asarray(payoff)
    return np.where(values < 5.0, 0.0, np.where(values == 5.0, 0.5, 1.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 7.5,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "axes.titleweight": "bold",
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    safe_payoff = 10.0
    risky_payoffs = np.array([0.0, 21.0])
    expected_payoffs = np.array([safe_payoff, risky_payoffs.mean()])
    expected_percentiles = np.array(
        [float(percentile_map(safe_payoff)), float(percentile_map(risky_payoffs).mean())]
    )
    fig = plt.figure(figsize=(5.8, 2.4), dpi=180)
    grid = fig.add_gridspec(2, 2, width_ratios=(1.62, 1.0), hspace=1.45, wspace=0.56)
    ax_map = fig.add_subplot(grid[:, 0])
    ax_map.step([-0.6, 5.0, 22.0], [0.0, 1.0, 1.0], where="post", color=GRAY, linewidth=1.6)
    ax_map.scatter([5.0], [0.5], facecolors="white", edgecolors=GRAY, linewidths=1.2, s=24, zorder=4)
    ax_map.scatter([safe_payoff], [percentile_map(safe_payoff)], color=BLUE, marker="o", s=30, zorder=3)
    ax_map.scatter(
        risky_payoffs,
        percentile_map(risky_payoffs),
        facecolors=ORANGE_LIGHT,
        edgecolors=ORANGE,
        marker="s",
        linewidths=1.3,
        s=30,
        zorder=3,
    )
    for value in (0.0, 10.0, 21.0):
        ax_map.vlines(
            value,
            0.0,
            percentile_map(value),
            color="#B8B8B8",
            linewidth=0.7,
            linestyle="--",
            zorder=1,
        )
    ax_map.set_xlim(-0.6, 22.0)
    ax_map.set_ylim(-0.04, 1.04)
    ax_map.set_xticks([0, 5, 10, 15, 21])
    ax_map.set_yticks([0.0, 0.5, 1.0])
    ax_map.set_xlabel(r"Payoff $y$")
    ax_map.set_ylabel(r"Cell percentile $Q_D(y)$")
    ax_map.set_title(r"(a) Midrank map for $D=\{5\}$", loc="left")
    ax_map.set_axisbelow(True)
    ax_map.grid(axis="y", color="#D0D0D0", linewidth=0.5, alpha=0.55)
    ax_map.annotate(
        r"tie: $Q_D(5)=0.5$",
        xy=(5.0, 0.5),
        xytext=(6.1, 0.38),
        color="#4A4A4A",
        fontsize=7.0,
        arrowprops={"arrowstyle": "-", "color": GRAY, "linewidth": 0.7},
    )
    labels = ["A: sure", "B: lottery"]
    for axis, values, title, xlabel, limit, value_format in (
        (
            fig.add_subplot(grid[0, 1]),
            expected_payoffs,
            "(b) Money criterion",
            "Expected payoff",
            12.0,
            ".1f",
        ),
        (
            fig.add_subplot(grid[1, 1]),
            expected_percentiles,
            "(c) Rank criterion",
            "Expected cell percentile",
            1.05,
            ".2f",
        ),
    ):
        bars = axis.barh(
            labels,
            values,
            color=[BLUE, ORANGE_LIGHT],
            edgecolor=[BLUE, ORANGE],
            linewidth=0.8,
            height=0.55,
        )
        bars[1].set_hatch("///")
        for bar, value in zip(bars, values):
            axis.text(
                value + limit * 0.015,
                bar.get_y() + bar.get_height() / 2,
                format(value, value_format),
                va="center",
                fontsize=7,
            )
        axis.set_xlim(0.0, limit)
        axis.set_title(title, loc="left")
        axis.set_xlabel(xlabel)
        axis.set_axisbelow(True)
        axis.grid(axis="x", color="#D0D0D0", linewidth=0.5, alpha=0.55)
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
