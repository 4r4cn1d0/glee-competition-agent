#!/usr/bin/env python3
"""Why the persuasion DP's planning model disagreed with the live field.

Three questions, answered off the live logs:

  1. What did the v1 policy actually DO?  (spoiler: lie in every cell, every
     round, every trust state -- a pure spammer.)
  2. Does the buyer's response depend on anything the v1 state space omits?
     The fitted table is P(buy | mode, p, ratio, rec, lies-CAUGHT).  The buyer
     also sees every recommendation we make, bought or not.  If P(buy|yes)
     falls with the yes-RATE we have shown, the DP's belief that lying is free
     until caught is false, and a policy that pushes the yes-rate to 1.0 walks
     straight off the support of the table it was solved against.
  3. How far off the support does the always-lie policy sit?

Run: .venv/bin/python scripts/diag_pers_dp.py
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.pers_data import iter_rounds, LIVE   # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, c - h, c + h)


def boot_diff(a, b, iters=4000, seed=7):
    """Bootstrap CI on mean(a) - mean(b)."""
    rng = random.Random(seed)
    if not a or not b:
        return (0.0, 0.0, 0.0)
    na, nb = len(a), len(b)
    d = []
    for _ in range(iters):
        sa = sum(a[rng.randrange(na)] for _ in range(na)) / na
        sb = sum(b[rng.randrange(nb)] for _ in range(nb)) / nb
        d.append(sa - sb)
    d.sort()
    return (sum(a) / na - sum(b) / nb, d[int(0.025 * iters)], d[int(0.975 * iters)])


def main() -> int:
    rounds = list(iter_rounds())
    print(f"# {len({r['game_id'] for r in rounds}):,} logged seller games, "
          f"{len(rounds):,} rounds\n")

    # ---- 1. what v1 decided -------------------------------------------------
    v1 = json.load(open(os.path.join(REPO, "models", "pers_policy_dp_v1.json")))
    tot = lie = 0
    for c in v1["cells"].values():
        for lb, pol in c["policy"].items():
            tot += len(pol)
            lie += sum(pol)
    print(f"1. v1 policy: {lie}/{tot} state-rounds recommend the LOW unit "
          f"({lie/tot:.0%}).  It is the always-lie policy.")
    print(f"   calibration offsets (logit): {v1['calibration_offsets']}")
    print("   -> a 'no' in binary mode was shifted by "
          f"{v1['calibration_offsets'].get('binary|no'):+.2f} logits, i.e. honesty "
          "was priced at ~0 conversion, so lying dominates by construction.\n")

    # ---- 2. the omitted state variable -------------------------------------
    print("2. P(buy | we recommended) against the seller record the buyer has SEEN")
    print("   (lies-CAUGHT held fixed; yes-rate is over prior rounds only)\n")
    print(f"   {'caught':>7} {'yes-rate seen':>15} {'n':>7} {'P(buy|yes)':>11}  95% CI")
    bucket = defaultdict(list)
    for r in rounds:
        if not r["rec"] or r["seen"] < 4:
            continue
        yr = r["yes_rate"]
        yb = "<0.70" if yr < 0.70 else ("0.70-0.90" if yr < 0.90 else ">=0.90")
        cb = "0" if r["caught"] == 0 else ("1" if r["caught"] == 1 else "2+")
        bucket[(cb, yb)].append(1.0 if r["bought"] else 0.0)
    for cb in ("0", "1", "2+"):
        for yb in ("<0.70", "0.70-0.90", ">=0.90"):
            v = bucket.get((cb, yb)) or []
            if len(v) < 50:
                continue
            p, lo, hi = wilson(sum(v), len(v))
            print(f"   {cb:>7} {yb:>15} {len(v):>7} {p:>10.1%}  [{lo:.1%}, {hi:.1%}]")
        hi_ = bucket.get((cb, ">=0.90")) or []
        lo_ = bucket.get((cb, "<0.70")) or []
        if len(hi_) >= 50 and len(lo_) >= 50:
            d, l, h = boot_diff(hi_, lo_)
            print(f"   {'':>7} {'spammy - selective':>15} "
                  f"{'':>7} {d:>+10.1%}  [{l:+.1%}, {h:+.1%}]")
    print()

    # per-mode, since the DP solves per mode
    print("   same contrast per mode (all trust states pooled):")
    for mode in ("binary", "text"):
        hi_ = [1.0 if r["bought"] else 0.0 for r in rounds
               if r["rec"] and r["seen"] >= 4 and r["mode"] == mode and r["yes_rate"] >= 0.90]
        lo_ = [1.0 if r["bought"] else 0.0 for r in rounds
               if r["rec"] and r["seen"] >= 4 and r["mode"] == mode and r["yes_rate"] < 0.70]
        if len(hi_) >= 50 and len(lo_) >= 50:
            d, l, h = boot_diff(hi_, lo_)
            print(f"     {mode:7s} spammy {sum(hi_)/len(hi_):.1%} (n={len(hi_)})  vs "
                  f"selective {sum(lo_)/len(lo_):.1%} (n={len(lo_)})  "
                  f"delta {d:+.1%} [{l:+.1%}, {h:+.1%}]")
    print()

    # ---- 3. support of the fitted table vs where the DP plans ---------------
    n_all = sum(1 for r in rounds if r["seen"] >= 4)
    n_spam = sum(1 for r in rounds if r["seen"] >= 4 and r["yes_rate"] >= 0.95)
    print(f"3. support: {n_spam/n_all:.1%} of the fitted rounds sit at a yes-rate "
          f">= 0.95 ({n_spam:,}/{n_all:,}).")
    print("   The v1 policy drives every low round to 'yes', so its realised "
          "yes-rate is 1.0 -- it plans almost entirely outside the region the "
          "table was measured on, and the table has no coordinate that would "
          "have told it so.\n")

    # ---- 4. does the caught-lie coordinate even carry the punishment? -------
    print("4. what the v1 state space DID see -- P(buy|yes) by lies caught:")
    for cb, lo_, hi_ in (("0", 0, 0), ("1", 1, 1), ("2+", 2, 99)):
        v = [1.0 if r["bought"] else 0.0 for r in rounds
             if r["rec"] and lo_ <= r["caught"] <= hi_]
        p, l, h = wilson(sum(v), len(v))
        print(f"   caught={cb:>2}  n={len(v):>6}  P(buy|yes)={p:.1%} [{l:.1%},{h:.1%}]")
    print("   Conversion barely moves with caught lies -- which is exactly why "
          "the DP concluded lying is free.  The punishment lives in the "
          "recommendation record, a coordinate v1 does not have.\n")

    # ---- 5. sales are not the currency -------------------------------------
    from sim.percentile import percentile
    print("5. sales -> percentile is strongly non-linear (the DP maximised sales):")
    for key in ("binary|lo|r4.0", "binary|mid|r2.0", "text|mid|r3.0"):
        mode, pb, rb = key.split("|")
        rb = float(rb[1:])
        ex = next((r for r in rounds if r["mode"] == mode and r["pb"] == pb
                   and r["rb"] == rb), None)
        if not ex:
            continue
        params = {"product_price": ex["price"], "p": ex["p"], "v": ex["v"],
                  "total_rounds": 20, "seller_message_type": mode}
        row = []
        for s in (4, 8, 12, 16, 20):
            q = percentile("persuasion", params, "player_1", ex["price"] * s)
            row.append(f"{s:>2}:{'--' if q is None else format(q, '.2f')}")
        print(f"   {key:16s} sales->pct  " + "  ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
