#!/usr/bin/env python3
"""Generate a descriptive rating chronology from checked-in evidence.

The plot connects authenticated display snapshots in time order. It is not a
causal interrupted time series and contains no conceptual or decorative panel.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "submitted_agent_rating_checkpoints.csv"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
GRAY = "#6E6E6E"


def load_ratings():
    rows = []
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for key in ("bargaining", "negotiation", "persuasion"):
                row[key] = float(row[key]) if row[key] else None
            rows.append(row)
    return rows


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, pad=2)


def draw_rating_panel(ax, rows):
    specs = [
        ("bargaining", "Bargaining", BLUE, "o", "-"),
        ("negotiation", "Negotiation", ORANGE, "s", "--"),
        ("persuasion", "Persuasion", GREEN, "^", ":"),
    ]
    for key, label, color, marker, line in specs:
        xs = [index for index, row in enumerate(rows, start=1) if row[key] is not None]
        ys = [row[key] for row in rows if row[key] is not None]
        ax.plot(
            xs,
            ys,
            label=label,
            color=color,
            marker=marker,
            linestyle=line,
            linewidth=1.45,
            markersize=4.2,
            markeredgewidth=0.45,
            markeredgecolor="white",
            zorder=3,
        )

    bank_index = 11
    ax.axvline(bank_index, color=GRAY, linewidth=0.75, linestyle=(0, (2, 2)), alpha=0.75, zorder=1)
    ax.annotate(
        "pre-close bank",
        xy=(bank_index, 2603.81),
        xytext=(8.55, 2718),
        fontsize=7.4,
        ha="left",
        va="bottom",
        color="#333333",
        arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=0.7),
    )
    ax.annotate(
        "official close",
        xy=(12, 2804.82),
        xytext=(9.95, 2872),
        fontsize=7.4,
        ha="left",
        va="bottom",
        color="#333333",
        arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=0.7),
    )

    ax.set_ylim(1980, 2910)
    ax.set_ylabel("Submitted-agent rating", fontsize=8.5)
    ax.set_xlabel("Selected checkpoint date", fontsize=8.5)
    ax.set_xticks([1, 4, 8, 10, 12], ["25 Aug", "26 Aug", "27 Aug", "29 Aug", "30 Aug"])
    ax.set_xlim(0.7, 12.3)
    ax.grid(axis="y", color="#BEBEBE", linewidth=0.45, linestyle="--", alpha=0.55)
    ax.legend(frameon=False, fontsize=7.6, ncol=3, loc="lower right")
    style_axis(ax)


def main():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": True,
        }
    )
    rows = load_ratings()
    fig, ax = plt.subplots(figsize=(5.5, 1.60), constrained_layout=False)
    draw_rating_panel(ax, rows)
    fig.subplots_adjust(left=0.10, right=0.995, top=0.97, bottom=0.23)

    for suffix, kwargs in (("pdf", {}), ("png", {"dpi": 350})):
        fig.savefig(HERE / f"fig_strategy_evolution.{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


if __name__ == "__main__":
    main()
