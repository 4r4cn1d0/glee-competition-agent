#!/usr/bin/env python3
"""Generate the Agent 5 rating and strategy chronology used in the core paper.

The input is produced by ``paper/analysis/analyze_agent5_lifecycle.py`` from
the append-only rating snapshot archive and freezes at the first settled poll
after competition close. Timestamps are parsed as UTC. Lines connect
authenticated observations only and are not treatment effects.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "agent5_lifecycle_rating_snapshots.csv"


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "ts": parse_utc(row["timestamp_utc"]),
                    "bargaining": float(row["bargaining_rating"]),
                    "negotiation": float(row["negotiation_rating"]),
                    "persuasion": float(row["persuasion_rating"]),
                }
            )
    return rows


# Recorded development events, not randomized interventions. Event 1 is an
# assembly commit timestamp, not verified runtime activation. Event 3 is the
# common-policy baseline boundary, not a reset of the competition ratings.
BOUNDARIES = [
    ("1", "2026-08-20T00:45:20Z"),  # code assembled from then-leading family policies
    ("2", "2026-08-21T14:09:40Z"),  # bargaining stonewall explicitly rolled back
    ("3", "2026-08-22T10:54:50Z"),  # identical-policy measurement baseline
    ("4", "2026-08-25T00:51:24Z"),  # deterministic negotiation dispatcher activated
    ("5", "2026-08-29T05:27:36.596627Z"),  # final persuasion overlay and audit boundary
]
COMPETITION_CLOSE = parse_utc("2026-08-30T11:59:59Z")


def main() -> None:
    rows = load_rows()
    times = [row["ts"] for row in rows]

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 7.5,
            "axes.labelsize": 8,
            "legend.fontsize": 7.2,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(5.55, 2.05), dpi=220)

    styles = {
        "bargaining": ("Bargaining", "#0072B2", "-"),
        "negotiation": ("Negotiation", "#D55E00", "--"),
        "persuasion": ("Persuasion", "#009E73", "-."),
    }
    for key, (label, color, linestyle) in styles.items():
        ax.plot(
            times,
            [row[key] for row in rows],
            color=color,
            linestyle=linestyle,
            linewidth=1.05,
            label=label,
            solid_capstyle="round",
            zorder=3,
        )

    ax.axvline(
        COMPETITION_CLOSE,
        color="#222222",
        linewidth=0.75,
        linestyle=(0, (3, 2)),
        label="Competition close",
        zorder=2,
    )

    ymax = 2910
    for number, value in BOUNDARIES:
        stamp = parse_utc(value)
        ax.axvline(stamp, color="#6B6B6B", linewidth=0.55, linestyle=":", zorder=1)
        ax.text(
            stamp,
            ymax - 12,
            number,
            ha="center",
            va="top",
            fontsize=6.7,
            weight="bold",
            color="#333333",
            bbox={"boxstyle": "circle,pad=0.14", "facecolor": "white", "edgecolor": "#777777", "linewidth": 0.45},
            clip_on=False,
            zorder=5,
        )

    ax.set_ylim(1600, ymax)
    ax.set_xlim(times[0] - timedelta(minutes=20), times[-1] + timedelta(hours=1))
    ax.set_ylabel("Displayed family rating")
    ax.set_xlabel("August 2026 (UTC)", labelpad=1.5)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2, tz=timezone.utc))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz=timezone.utc))
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, alpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        loc="lower right",
        frameon=True,
        framealpha=0.94,
        edgecolor="#CCCCCC",
        ncol=1,
        handlelength=2.4,
        borderpad=0.35,
        labelspacing=0.25,
    )
    fig.tight_layout(pad=0.35)

    fig.savefig(HERE / "fig_agent5_lifecycle.pdf", bbox_inches="tight")
    fig.savefig(HERE / "fig_agent5_lifecycle.png", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
