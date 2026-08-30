#!/usr/bin/env python3
"""Generate the compact returned-action audit figure for the paper."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(__file__).resolve().parent

NAVY = "#173B57"
PALE = "#EAF1F5"
ACCENT = "#DCEDE8"
AMBER = "#F5E8C8"
INK = "#1F2933"
GRAY = "#66717C"


def rounded_box(ax, x, y, width, height, text, *, face, bold=False) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.045",
        linewidth=0.85,
        edgecolor=NAVY,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=7.1,
        color=INK,
        fontweight="bold" if bold else "normal",
        linespacing=1.05,
    )


def main() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(7.05, 1.55))
    ax.set_xlim(0, 12.2)
    ax.set_ylim(0, 2.65)
    ax.axis("off")

    titles = [
        "Visible\nstate",
        "Final decision\nauthority",
        "Postguards\nand schema",
        "Returned\naction",
        "Joined\noutcome",
    ]
    evidence = [
        "eligible",
        "selected",
        "independent\nspecification",
        "exact match\nand receipt scope",
        "descriptive or\ncausal status",
    ]
    xs = [0.18, 2.62, 5.06, 7.50, 9.94]
    box_width = 1.86

    ax.text(0.18, 2.48, "Action construction", color=NAVY, fontsize=7.5,
            fontweight="bold", va="center")
    ax.text(0.18, 0.58, "Evidence required", color=NAVY, fontsize=7.5,
            fontweight="bold", va="center")

    faces = [PALE, PALE, PALE, ACCENT, AMBER]
    for index, (x, title, check, face) in enumerate(zip(xs, titles, evidence, faces)):
        rounded_box(ax, x, 1.36, box_width, 0.78, title, face=face,
                    bold=index == 3)
        ax.plot([x + box_width / 2, x + box_width / 2], [1.31, 1.08],
                color="#8CA0AE", linewidth=0.75)
        ax.text(x + box_width / 2, 0.80, check, ha="center", va="center",
                fontsize=6.6, color=GRAY, linespacing=1.03)
        if index < len(xs) - 1:
            arrow = FancyArrowPatch(
                (x + box_width + 0.08, 1.75),
                (xs[index + 1] - 0.08, 1.75),
                arrowstyle="-|>",
                mutation_scale=8,
                linewidth=0.85,
                color=NAVY,
            )
            ax.add_patch(arrow)

    ax.text(
        11.80,
        0.20,
        "Outcome success is not execution conformance",
        ha="right",
        va="center",
        fontsize=6.5,
        color=GRAY,
        fontstyle="italic",
    )

    fig.subplots_adjust(left=0.005, right=0.995, top=0.98, bottom=0.02)
    fig.savefig(OUT / "fig_audit_contract.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(
        OUT / "fig_audit_contract.png",
        dpi=350,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
