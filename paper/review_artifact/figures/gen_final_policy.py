#!/usr/bin/env python3
"""Generate the anonymous owner-precedence policy figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402


NAVY = "#173B57"
BLUE = "#DCEAF3"
TEAL = "#DDF0EA"
AMBER = "#F7E8C8"
ROSE = "#F3DEDE"
INK = "#1F2933"
GRAY = "#68727D"


def box(ax, x: float, y: float, width: float, height: float, text: str, face: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.025,rounding_size=0.035",
            linewidth=0.8,
            edgecolor=NAVY,
            facecolor=face,
        )
    )
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=6.5, color=INK)


def arrow(ax, start: tuple[float, float], end: tuple[float, float], dashed: bool = False) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=0.8,
            color=NAVY,
            linestyle=(0, (2, 2)) if dashed else "solid",
        )
    )


def lane(ax, y: float, label: str, nodes: list[tuple[str, str]], relations: list[str]) -> None:
    ax.text(0.25, y + 0.31, label, fontsize=7.0, color=NAVY, weight="bold", va="center")
    xs, widths = [1.43, 4.42, 7.42], [2.55, 2.55, 2.28]
    for index, ((text, face), x, width) in enumerate(zip(nodes, xs, widths)):
        box(ax, x, y, width, 0.62, text, face)
        if index < 2:
            relation = relations[index]
            arrow(ax, (x + width + 0.08, y + 0.31), (xs[index + 1] - 0.08, y + 0.31), relation == "else")
            ax.text((x + width + xs[index + 1]) / 2, y + 0.47, relation, fontsize=5.3, color=GRAY, ha="center")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.0})
    fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=180)
    ax.set_xlim(0, 14.15)
    ax.set_ylim(0, 5.15)
    ax.axis("off")
    ax.text(0.18, 4.96, "Visible game state", fontsize=8.4, color=NAVY, weight="bold", va="top")
    chips = ["family", "role", "horizon", "information", "communication", "history"]
    chip_x = [2.30, 3.37, 4.44, 5.65, 7.08, 8.73]
    chip_w = [0.88, 0.88, 1.02, 1.24, 1.44, 0.92]
    for text, x, width in zip(chips, chip_x, chip_w):
        box(ax, x, 4.55, width, 0.36, text, "white")
    box(ax, 4.15, 3.84, 3.55, 0.46, "deterministic dispatcher and ordered ownership", BLUE)
    arrow(ax, (6.27, 4.53), (6.27, 4.32))
    lane(
        ax,
        2.96,
        "Bargaining",
        [
            ("silent player 2 owner\n12 rounds, discount .95", TEAL),
            ("finite recursion or\nhidden cap and clock", AMBER),
            ("continuation and\nempirical floors", AMBER),
        ],
        ["else", "then"],
    )
    lane(
        ax,
        2.10,
        "Negotiation",
        [
            ("one-round seller;\ncomplete 10-round buyer", TEAL),
            ("hidden terminal\nconditional bound", TEAL),
            ("buyer path or\nseller fallback", AMBER),
        ],
        ["else", "else"],
    )
    lane(
        ax,
        1.24,
        "Persuasion",
        [
            ("seller value or\nhistory rule", TEAL),
            ("buyer posterior and\ncredibility adjustment", AMBER),
            ("buy-to-pass\ndecline veto", ROSE),
        ],
        ["else", "then"],
    )
    box(ax, 10.05, 1.13, 1.82, 2.55, "schema conversion\n\nnumeric postguards\n\nlegal fallback", ROSE)
    box(ax, 10.05, 0.41, 1.82, 0.5, "returned action", BLUE)
    box(ax, 12.23, 0.41, 1.62, 0.5, "trace to outcome", "white")
    for y in (3.27, 2.41, 1.55):
        arrow(ax, (9.78, y), (10.01, y))
    arrow(ax, (10.96, 1.10), (10.96, 0.95))
    arrow(ax, (11.91, 0.66), (12.19, 0.66), dashed=True)
    ax.text(13.8, 0.12, "dashed: else priority; solid: then", fontsize=5.9, color=GRAY, ha="right")
    fig.subplots_adjust(left=0.01, right=0.995, top=0.99, bottom=0.01)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
