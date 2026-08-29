#!/usr/bin/env python3
"""Generate the strategy-evolution figure from checked-in evidence.

The rating panel is deliberately descriptive. It plots authenticated display
snapshots around dated strategy boundaries, not a causal interrupted time
series. The audit panel reproduces audited estimates from the checked-in
evidence and labels retrospective or repeatedly inspected quantities as such.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "agent5_rating_checkpoints.csv"

BLUE = "#4C72B0"
ORANGE = "#DD8452"
GREEN = "#55A868"
RED = "#C44E52"
PURPLE = "#8172B3"
GRAY = "#6E6E6E"
LIGHT = "#F4F4F2"


def load_ratings():
    rows = []
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["timestamp"] = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            for key in ("bargaining", "negotiation", "persuasion"):
                row[key] = float(row[key]) if row[key] else None
            rows.append(row)
    return rows


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=7, pad=2)


def draw_rating_panel(ax, rows):
    specs = [
        ("bargaining", "Bargaining", BLUE, "o", "-"),
        ("negotiation", "Negotiation", ORANGE, "s", "--"),
        ("persuasion", "Persuasion", GREEN, "^", ":"),
    ]
    for key, label, color, marker, line in specs:
        xs = [row["timestamp"] for row in rows if row[key] is not None]
        ys = [row[key] for row in rows if row[key] is not None]
        ax.plot(
            xs,
            ys,
            label=label,
            color=color,
            marker=marker,
            linestyle=line,
            linewidth=1.25,
            markersize=3.6,
            markeredgewidth=0.45,
            markeredgecolor="white",
            zorder=3,
        )

    boundaries = [
        (datetime(2026, 8, 25, 6, 21), "N: whole-policy V1"),
        (datetime(2026, 8, 25, 7, 29), "B: narrow P2 owner"),
    ]
    for x, text in boundaries:
        ax.axvline(x, color=GRAY, linewidth=0.65, linestyle=(0, (2, 2)), alpha=0.85, zorder=1)
    ax.annotate(
        "Whole-policy V1 and narrow P2 owner\nactivated within the shaded interval",
        xy=(datetime(2026, 8, 25, 6, 55), 2820),
        xytext=(datetime(2026, 8, 26, 2, 0), 2862),
        fontsize=6.7,
        color="#333333",
        ha="left",
        va="bottom",
        arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=0.65),
    )
    ax.axvspan(boundaries[0][0], boundaries[1][0], color="#DDE5EF", alpha=0.55, zorder=0)

    reset_boundary = datetime(2026, 8, 29, 10, 57)
    ax.axvline(reset_boundary, color=PURPLE, linewidth=0.65, linestyle=(0, (2, 2)), alpha=0.8, zorder=1)
    ax.text(
        reset_boundary,
        2030,
        "P reset copied",
        fontsize=6.2,
        color=PURPLE,
        rotation=90,
        ha="right",
        va="bottom",
    )

    ax.annotate(
        "Final bank\n2603.81 / 2620.36 / 2344.79",
        xy=(datetime(2026, 8, 29, 18, 18), 2620.36),
        xytext=(datetime(2026, 8, 28, 16, 0), 2435),
        fontsize=6.7,
        ha="center",
        va="top",
        color="#333333",
        arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=0.65),
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.82),
    )

    ax.set_ylim(1980, 2910)
    ax.set_ylabel("Displayed family rating", fontsize=8)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d Aug"))
    ax.grid(axis="y", color="#BEBEBE", linewidth=0.45, linestyle="--", alpha=0.55)
    ax.legend(frameon=False, fontsize=6.8, ncol=3, loc="lower right", bbox_to_anchor=(1.0, 0.005))
    ax.text(
        0.0,
        1.07,
        "(a) Dated Agent 5 snapshots",
        transform=ax.transAxes,
        fontsize=8.2,
        fontweight="bold",
        ha="left",
        va="bottom",
    )
    style_axis(ax)


def add_box(ax, x, y, width, height, text, edge, face, *, weight="normal"):
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.015,rounding_size=0.018",
        linewidth=0.75,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(box)
    ax.text(
        x + 0.018,
        y + height / 2,
        text,
        fontsize=6.7,
        color="#252525",
        ha="left",
        va="center",
        fontweight=weight,
        linespacing=1.12,
    )


def draw_audit_panel(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 1.03, "(b) Positive-looking claims after full audit", fontsize=8.2, fontweight="bold", ha="left")
    ax.text(0.02, 0.91, "Initial estimate", fontsize=7, fontweight="bold", color=GRAY)
    ax.text(0.59, 0.91, "Corrected status", fontsize=7, fontweight="bold", color=GRAY)

    rows = [
        (
            0.71,
            "+0.07138, 352 selected\naccept profitable offers",
            "-0.06628, 375 exposed\n-0.00614, 4,050 cohort",
            "Different replay estimands;\nlater agreements retained",
            RED,
        ),
        (
            0.48,
            "+0.0121 percentile\naggressive surplus",
            "INVALID",
            "Unsupported replies and\nthree bundled semantics",
            RED,
        ),
        (
            0.25,
            "+1.812 rating/game\nleader clone, early look",
            "+0.869, stopped n=91\nnom. 95% [-0.73, 2.47]",
            "Earlier n=45 look;\nno-deals +6.14 pp",
            PURPLE,
        ),
        (
            0.02,
            "11,737 missing finals\ncoded as low-rank losses",
            "UNRESOLVED",
            "Reader fixed; analyses reopened",
            BLUE,
        ),
    ]
    height = 0.17
    for y, left, right, note, color in rows:
        add_box(ax, 0.015, y, 0.35, height, left, GRAY, LIGHT)
        arrow = FancyArrowPatch(
            (0.385, y + height / 2),
            (0.555, y + height / 2),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.8,
            color=color,
        )
        ax.add_patch(arrow)
        add_box(ax, 0.575, y, 0.225, height, right, color, "#FFFFFF", weight="bold")
        ax.text(0.82, y + height / 2, note, fontsize=6.25, ha="left", va="center", color="#3A3A3A", linespacing=1.1)


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
    fig = plt.figure(figsize=(5.5, 4.1), constrained_layout=False)
    grid = fig.add_gridspec(2, 1, height_ratios=[1.25, 1.15], hspace=0.42)
    draw_rating_panel(fig.add_subplot(grid[0]), rows)
    draw_audit_panel(fig.add_subplot(grid[1]))
    fig.subplots_adjust(left=0.10, right=0.995, top=0.955, bottom=0.035)

    for suffix, kwargs in (("pdf", {}), ("png", {"dpi": 350})):
        fig.savefig(HERE / f"fig_strategy_evolution.{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


if __name__ == "__main__":
    main()
