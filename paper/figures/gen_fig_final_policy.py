#!/usr/bin/env python3
"""Generate the strategy-first map of the final banked GLEE policy.

The figure records deterministic owner precedence at the August 29 bank.  It
does not encode or imply the causal value of any component.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent

NAVY = "#173B57"
BLUE = "#DCEAF3"
TEAL = "#DDF0EA"
AMBER = "#F7E8C8"
ROSE = "#F3DEDE"
INK = "#1F2933"
GRAY = "#68727D"
WHITE = "#FFFFFF"


def box(ax, x, y, w, h, text, *, face=WHITE, edge=NAVY, size=6.5, weight="normal"):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.035",
        linewidth=0.8,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=INK,
        fontweight=weight,
        linespacing=1.08,
    )


def arrow(ax, start, end, *, color=NAVY, style="-|>", dashed=False, width=0.8):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=8,
        linewidth=width,
        color=color,
        linestyle=(0, (2, 2)) if dashed else "solid",
        connectionstyle="arc3,rad=0",
    )
    ax.add_patch(patch)


def lane(ax, y, label, nodes, relations):
    ax.text(0.25, y + 0.31, label, ha="left", va="center", fontsize=7.0,
            color=NAVY, fontweight="bold")
    xs = [1.43, 4.42, 7.42]
    widths = [2.55, 2.55, 2.28]
    for index, ((text, face), x, w) in enumerate(zip(nodes, xs, widths)):
        box(ax, x, y, w, 0.62, text, face=face)
        if index < 2:
            relation = relations[index]
            arrow(
                ax,
                (x + w + 0.08, y + 0.31),
                (xs[index + 1] - 0.08, y + 0.31),
                dashed=relation == "else",
            )
            ax.text(
                (x + w + xs[index + 1]) / 2,
                y + 0.47,
                relation,
                ha="center",
                va="center",
                fontsize=5.3,
                color=GRAY,
            )


def main() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(7.05, 2.85))
    ax.set_xlim(0, 14.15)
    ax.set_ylim(0, 5.15)
    ax.axis("off")

    ax.text(0.18, 4.98, "Visible GLEE state", fontsize=8.2, color=NAVY,
            fontweight="bold", va="top")
    chips = ["family", "role", "horizon", "information", "communication", "history"]
    chip_x = [2.30, 3.37, 4.44, 5.65, 7.08, 8.73]
    chip_w = [0.88, 0.88, 1.02, 1.24, 1.44, 0.92]
    for text, x, w in zip(chips, chip_x, chip_w):
        box(ax, x, 4.57, w, 0.36, text, face=WHITE, edge="#7890A3", size=6.2)

    box(
        ax,
        4.15,
        3.86,
        3.55,
        0.46,
        "deterministic dispatcher and ordered policy ownership",
        face=BLUE,
        weight="bold",
        size=6.8,
    )
    arrow(ax, (6.27, 4.55), (6.27, 4.34))

    lane(
        ax,
        2.98,
        "Bargaining",
        [
            ("silent Bob owner\nT=12, $\\delta_2=.95$", TEAL),
            ("finite recursion or\nhidden cap + clock", AMBER),
            ("continuation and\nempirical floors", AMBER),
        ],
        ["else", "then"],
    )
    lane(
        ax,
        2.12,
        "Negotiation",
        [
            ("one-round seller;\ncomplete T=10 buyer", TEAL),
            ("hidden T=10 terminal\nbound inference", TEAL),
            ("leader buyer path /\nseller fallback", AMBER),
        ],
        ["else", "else"],
    )
    lane(
        ax,
        1.26,
        "Persuasion",
        [
            ("seller prior-value\nand buy-rate rules", TEAL),
            ("buyer posterior +\ncredibility reset", AMBER),
            ("BUY→PASS\ndecline veto", ROSE),
        ],
        ["else", "then"],
    )

    box(
        ax,
        10.05,
        1.15,
        1.82,
        2.55,
        "schema coercion\n\nnumeric postguards\n\nlegal fallback",
        face=ROSE,
        weight="bold",
        size=6.5,
    )
    box(ax, 10.05, 0.43, 1.82, 0.50, "returned action", face=BLUE, weight="bold")
    box(ax, 12.23, 0.43, 1.62, 0.50, "trace → outcome", face=WHITE,
        edge="#7890A3")
    for y in (3.29, 2.43, 1.57):
        arrow(ax, (9.78, y), (10.01, y), color=NAVY, width=0.7)
    arrow(ax, (10.96, 1.12), (10.96, 0.97))
    arrow(ax, (11.91, 0.68), (12.19, 0.68), color="#7890A3", dashed=True)

    ax.add_patch(FancyBboxPatch((0.20, 0.07), 0.26, 0.17, boxstyle="round,pad=0.01",
                                facecolor=TEAL, edgecolor=NAVY, linewidth=0.55))
    ax.text(0.57, 0.15, "structural owner", fontsize=5.9, color=GRAY, va="center")
    ax.add_patch(FancyBboxPatch((1.82, 0.07), 0.26, 0.17, boxstyle="round,pad=0.01",
                                facecolor=AMBER, edgecolor=NAVY, linewidth=0.55))
    ax.text(2.19, 0.15, "model or field heuristic", fontsize=5.9, color=GRAY, va="center")
    ax.add_patch(FancyBboxPatch((4.01, 0.07), 0.26, 0.17, boxstyle="round,pad=0.01",
                                facecolor=ROSE, edgecolor=NAVY, linewidth=0.55))
    ax.text(4.38, 0.15, "safety / coercion", fontsize=5.9, color=GRAY, va="center")
    ax.text(13.84, 0.15, "dashed = else priority; solid = then", fontsize=5.9,
            color=GRAY, ha="right", va="center")

    fig.subplots_adjust(left=0.01, right=0.995, top=0.99, bottom=0.01)
    for suffix, kwargs in (("pdf", {}), ("png", {"dpi": 350})):
        fig.savefig(HERE / f"fig_final_policy.{suffix}", bbox_inches="tight", facecolor="white", **kwargs)
    plt.close(fig)


if __name__ == "__main__":
    main()
