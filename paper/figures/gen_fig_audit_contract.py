"""Generate the action-level audit contract figure used in the paper."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(__file__).resolve().parent


def main() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    stages = [
        ("Visible\nstate", "Pre-action\neligibility"),
        ("Family\nplan", "Plan and\nfinal owner"),
        ("Ordered\ngates", "Eligible, fired,\naction changed"),
        ("Schema\nconversion", "Exact off/on\naction diff"),
        ("Returned\naction", "Post-coercion\nturn log"),
        ("Joined\noutcome", "All assigned\noutcomes"),
    ]
    failures = [
        "Selected cohort",
        "Treatment leakage",
        "Unreachable gate",
        "Action overwritten",
        "Unverified receipt",
        "Missing imputed",
    ]

    fig, ax = plt.subplots(figsize=(7.1, 2.15))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.0)
    ax.axis("off")

    navy = "#214761"
    pale = "#E8F1F5"
    teal = "#17807E"
    coral = "#C9574E"
    gray = "#4B5563"

    xs = [0.25, 2.25, 4.25, 6.25, 8.25, 10.25]
    width, height = 1.50, 0.96

    ax.text(
        0.25,
        3.77,
        "Action-level evidence contract",
        fontsize=10.2,
        fontweight="bold",
        color=navy,
        va="top",
    )
    ax.text(
        11.75,
        3.76,
        "A policy is treated only after conversion",
        fontsize=7.7,
        color=gray,
        va="top",
        ha="right",
    )

    for i, ((title, evidence), fail, x) in enumerate(zip(stages, failures, xs)):
        box = FancyBboxPatch(
            (x, 2.32),
            width,
            height,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            linewidth=1.2,
            edgecolor=navy,
            facecolor=pale,
        )
        ax.add_patch(box)
        ax.text(
            x + width / 2,
            2.80,
            title,
            ha="center",
            va="center",
            fontweight="bold",
            color=navy,
            linespacing=0.95,
        )
        ax.text(
            x + width / 2,
            1.88,
            evidence,
            ha="center",
            va="center",
            color=teal,
            fontweight="bold",
            linespacing=1.08,
        )
        ax.plot(
            [x + 0.17, x + width - 0.17],
            [1.43, 1.43],
            color=coral,
            lw=1.1,
            solid_capstyle="round",
        )
        ax.text(
            x + width / 2,
            1.16,
            fail,
            ha="center",
            va="center",
            color=coral,
            fontsize=7.25,
        )
        if i < len(xs) - 1:
            arrow = FancyArrowPatch(
                (x + width + 0.07, 2.80),
                (xs[i + 1] - 0.07, 2.80),
                arrowstyle="-|>",
                mutation_scale=9,
                linewidth=1.05,
                color=navy,
            )
            ax.add_patch(arrow)

    fig.subplots_adjust(left=0.01, right=0.995, top=0.98, bottom=0.04)
    for suffix in ("pdf", "png"):
        fig.savefig(
            OUT / f"fig_audit_contract.{suffix}",
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
