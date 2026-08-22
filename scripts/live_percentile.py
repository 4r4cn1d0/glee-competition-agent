#!/usr/bin/env python3
"""Score our REAL completed games as percentiles. The meter the arena is not.

Why this exists. Two things were being used to judge a strategy change and both
are poor:

  * the ARENA, whose negotiation opponent clone cannot price aggression -- it
    bins on _price_bin (0.1 of base) while the moves we test are often smaller
    than one bin, consults a survivorship-selected value-keyed table first, and
    FALLS BACK to "profitable -> AcceptOffer" (sim/field_data.py:343), which
    grants any greedy ask it has never observed;
  * the LIVE RATING, which is a lagged, shrunk, opponent-adjusted transform of
    percentile. The measured cross-agent noise floor on IDENTICAL code is +/-125
    rating, so a +2-rating change is 62x below the noise and unobservable.

But the rating is a transform of a quantity we can compute ourselves for every
finished game: the percentile of our payoff within its exact configuration cell.
That is the RAW signal the rating is a noisy average of, and per-game it has far
more statistical power than watching a rating drift.

So: replay our own results.jsonl through the same fitted CDF the simulator uses
(models/percentile_cdf_v3.json), and report mean percentile per agent, family,
cell and era. No simulation, no cloned opponent, no assumption about how the
field responds -- these are the payoffs the field actually paid us.

    python scripts/live_percentile.py                      # last 24h, by agent
    python scripts/live_percentile.py --hours 6 --by cell
    python scripts/live_percentile.py --split 1787342160   # A/B across a deploy
    python scripts/live_percentile.py --ab rank-price      # terminal-price arm
    python scripts/live_percentile.py --ab barg-msg        # B0 silence vs B1-B3

CAVEAT, stated because it decides how far the numbers can be pushed: the cell
CDF is fitted from logged field payoffs, OUR OWN GAMES INCLUDED, so it is a
self-referential yardstick and drifts as the field drifts. It is reliable for
COMPARING two of our own arms measured in the same window against the same CDF,
which is what it is for. It is not an independent estimate of our true rank.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.percentile import percentile          # noqa: E402
from glee_agent.messages import BARG_ARMS, bargaining_arm  # noqa: E402

NAMES = {"champion": "Test 1", "hardliner": "Test 2", "conceder": "Test 3",
         "randomized": "Test 4", "composite": "Agent 5"}


def mean_ci(xs):
    """Mean with a normal 95% interval. n<2 gives no interval, not a fake one."""
    n = len(xs)
    if n == 0:
        return None, 0.0, 0.0, 0
    m = sum(xs) / n
    if n < 2:
        return m, m, m, n
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    half = 1.96 * math.sqrt(var / n)
    return m, m - half, m + half, n


def games(hours):
    """Yield score and message eligibility fields for finished games."""
    cut = time.time() - hours * 3600
    for path in sorted(glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl"))):
        slot = os.path.basename(os.path.dirname(path))
        if slot not in NAMES:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                ts = rec.get("ts", 0)
                if ts < cut:
                    continue
                fin = rec.get("final") or {}
                fam = fin.get("game_family")
                seat = fin.get("your_player")
                gs = fin.get("game_state") or {}
                res = fin.get("result") or {}
                if not fam or not seat:
                    continue
                pay = res.get(f"{seat}_payoff")
                if pay is None:
                    pay = res.get("your_payoff")
                if not isinstance(pay, (int, float)):
                    continue
                params = dict(gs)
                pct = percentile(fam, params, seat, float(pay))
                if pct is None:            # unknown cell -- no opinion, skip
                    continue
                yield (slot, ts, fam, pct, rec.get("game_id"),
                       gs.get("messages_allowed"))


def report_barg_msg(rows, hours):
    """Report the primary silence/text contrast and each assigned text register."""
    arms = defaultdict(lambda: defaultdict(list))
    for slot, _ts, fam, pct, gid, messages_allowed in rows:
        if fam != "bargaining" or messages_allowed is not True or not gid:
            continue
        arm = bargaining_arm(gid)
        if arm is not None:
            arms[slot][arm].append(pct)

    print(f"GLEE_BARG_MSG, bargaining only, last {hours:g}h")
    print("eligibility: messages_allowed=true; scope --hours/--slots to an era "
          "where GLEE_BARG_MSG was armed")
    print("primary contrast: B0 assigned silence vs pooled B1-B3 assigned text")
    print(f"{'agent':9} {'silence':>20} {'text':>20} {'delta':>20}")
    pooled = defaultdict(list)
    for slot, assigned in sorted(arms.items()):
        for arm, values in assigned.items():
            pooled[arm].extend(values)
        silent = assigned.get("B0", [])
        text_arms = [pct for arm in BARG_ARMS[1:] for pct in assigned.get(arm, [])]
        c, _clo, chi, cn = mean_ci(silent)
        d, _dlo, dhi, dn = mean_ci(text_arms)
        if c is None or d is None or cn < 30 or dn < 30:
            continue
        se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
        print(f"{NAMES[slot]:9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
              f"{d - c:+.4f} +/-{1.96*se:.4f}")

    silent = pooled.get("B0", [])
    text_arms = [pct for arm in BARG_ARMS[1:] for pct in pooled.get(arm, [])]
    c, _clo, chi, cn = mean_ci(silent)
    d, _dlo, dhi, dn = mean_ci(text_arms)
    if c is not None and d is not None and cn and dn:
        se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
        delta = d - c
        verdict = ("TEXT BETTER" if delta > 1.96 * se else
                   "TEXT WORSE" if delta < -1.96 * se else
                   "cannot distinguish yet")
        print(f"{'POOLED':9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
              f"{delta:+.4f} +/-{1.96*se:.4f}   -> {verdict}")

    print("\nexploratory register contrasts against B0 silence")
    print(f"{'arm':9} {'silence':>20} {'register':>20} {'delta':>20}")
    for arm in BARG_ARMS[1:]:
        d, _dlo, dhi, dn = mean_ci(pooled.get(arm, []))
        if c is None or d is None or not cn or not dn:
            continue
        se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
        print(f"{arm:9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
              f"{d - c:+.4f} +/-{1.96*se:.4f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--split", type=float, default=None,
                    help="unix ts; compare games before vs after it")
    ap.add_argument("--slots", default="")
    ap.add_argument("--ab", nargs="?", const="zopa",
                    choices=("zopa", "rank-price", "barg-msg"),
                    help="split games by a recoverable hash arm; bare --ab "
                         "keeps the legacy GLEE_NEGO_ZOPA_AB report")
    args = ap.parse_args()
    keep = {s.strip() for s in args.slots.split(",") if s.strip()}

    rows = [r for r in games(args.hours) if not keep or r[0] in keep]

    if args.ab:
        if args.ab == "barg-msg":
            report_barg_msg(rows, args.hours)
            return 0
        # Recompute the arm from the game id -- the SAME pure function the agent
        # used. Nothing is logged and nothing can drift out of sync.
        if args.ab == "rank-price":
            label, salt = "GLEE_NEGO_RANK_PRICE_AB", "rank_price_ab|"
        else:
            label, salt = "GLEE_NEGO_ZOPA_AB", "zopa_ab|"
        arms = defaultdict(lambda: defaultdict(list))
        for slot, ts, fam, pct, gid, _messages_allowed in rows:
            if fam != "negotiation" or not gid:
                continue
            bit = int(hashlib.sha256((salt + str(gid)).encode()).hexdigest(), 16) & 1
            arms[slot]["candidate" if bit else "control"].append(pct)
        print(f"{label}, negotiation only, last {args.hours:g}h")
        print(f"{'agent':9} {'control':>20} {'candidate':>20} {'delta':>20}")
        pooled = defaultdict(list)
        for slot, a in sorted(arms.items()):
            for k, v in a.items():
                pooled[k].extend(v)
            c, clo, chi, cn = mean_ci(a.get("control", []))
            d, dlo, dhi, dn = mean_ci(a.get("candidate", []))
            if c is None or d is None or cn < 30 or dn < 30:
                continue
            se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
            print(f"{NAMES[slot]:9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
                  f"{d - c:+.4f} +/-{1.96*se:.4f}")
        c, clo, chi, cn = mean_ci(pooled.get("control", []))
        d, dlo, dhi, dn = mean_ci(pooled.get("candidate", []))
        if c is not None and d is not None and cn and dn:
            se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
            delta = d - c
            verdict = ("CANDIDATE BETTER" if delta > 1.96 * se else
                       "CANDIDATE WORSE" if delta < -1.96 * se else
                       "cannot distinguish yet")
            print(f"{'POOLED':9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
                  f"{delta:+.4f} +/-{1.96*se:.4f}   -> {verdict}")
            need = (1.96 * 0.30 / max(abs(delta), 0.004)) ** 2 * 2
            print(f"  games/arm for a decisive read at this effect size: ~{need:.0f}")
        return 0
    if not rows:
        print("no scoreable games in window")
        return 1

    if args.split:
        buckets = defaultdict(lambda: defaultdict(list))
        for slot, ts, fam, pct, _gid, _messages_allowed in rows:
            arm = "after" if ts >= args.split else "before"
            buckets[(slot, fam)][arm].append(pct)
        print(f"{'agent':9} {'family':12} {'before':>22} {'after':>22} {'delta':>18}")
        for (slot, fam), arms in sorted(buckets.items()):
            b, blo, bhi, bn = mean_ci(arms.get("before", []))
            a, alo, ahi, an = mean_ci(arms.get("after", []))
            if b is None or a is None or bn < 30 or an < 30:
                continue
            # difference of independent means
            d = a - b
            se = math.sqrt(((bhi - b) / 1.96) ** 2 + ((ahi - a) / 1.96) ** 2)
            mark = "  *" if abs(d) > 1.96 * se else ""
            print(f"{NAMES[slot]:9} {fam:12} {b:.4f} (n={bn:>5}) {a:.4f} (n={an:>5}) "
                  f"{d:+.4f} +/-{1.96*se:.4f}{mark}")
        return 0

    agg = defaultdict(list)
    for slot, ts, fam, pct, _gid, _messages_allowed in rows:
        agg[(slot, fam)].append(pct)
        agg[(slot, "ALL")].append(pct)
    print(f"our REALISED percentile, last {args.hours:g}h "
          f"(0.5 = the field's median; the rating tracks this)")
    print(f"{'agent':9} {'family':12} {'mean pct':>9} {'95% CI':>18} {'n':>7} {'~rating':>9}")
    for (slot, fam), xs in sorted(agg.items()):
        m, lo, hi, n = mean_ci(xs)
        if n < 20:
            continue
        rating = 2000 + 8000 * (m - 0.5)
        print(f"{NAMES[slot]:9} {fam:12} {m:>9.4f} [{lo:.4f},{hi:.4f}] {n:>7} {rating:>9.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
