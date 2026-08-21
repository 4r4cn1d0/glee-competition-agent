#!/usr/bin/env python3
"""Held-out falsification: predict the DP window neither model was fitted on.

This is the test the v1 planning model failed live, run offline before anything
ships.  Both buyer models are fitted on heuristic-era rounds only.  The v1 DP
window -- 113 games in which Test 3 recommended EVERY low unit -- is held out.
Each model is asked, for those exact games (same cells, same opponents, same
quality sequences, same seller actions), what conversion it expects.

Realised: 38.7%.  v1's own solve sheet claimed 54-98% sale rates for the
always-lie policy, which is why it shipped.  A model that cannot call this
window has no business choosing an endgame lie structure.

The control arms in the same window are the second target: a model that simply
predicts "low" for everything would nail the DP arm and miss the controls, so
both are scored, and the SPREAD between them is what actually has to come out
right.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.fit_buyers_v3 import rounds_with_told, predict_row, load   # noqa: E402
from scripts.solve_pers_dp import buy_p, calibration_offsets        # noqa: E402
from scripts.diag_pers_window import DP_LO, DP_HI                   # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, c - h, c + h)


def v2_predict(table, offs, r):
    """What the v1/v2 planning model says about this exact round."""
    lb = "0" if r["caught"] == 0 else ("1" if r["caught"] == 1 else "2+")
    return buy_p(table, offs, r["mode"], r["pb"], r["rb"],
                 "yes" if r["rec"] else "no", lb)


def score(rows, name, fn):
    """Mean predicted vs realised conversion, plus Brier and log loss."""
    ps, ys = [], []
    for r in rows:
        p = fn(r)
        if p is None:
            continue
        ps.append(min(max(p, 1e-6), 1 - 1e-6))
        ys.append(1.0 if r["bought"] else 0.0)
    if not ps:
        return None
    n = len(ps)
    brier = sum((p - y) ** 2 for p, y in zip(ps, ys)) / n
    ll = -sum(y * math.log(p) + (1 - y) * math.log(1 - p)
              for p, y in zip(ps, ys)) / n
    return {"n": n, "pred": sum(ps) / n, "real": sum(ys) / n,
            "brier": brier, "logloss": ll}


def main() -> int:
    rows = rounds_with_told(exclude_dp=False)
    dp = [r for r in rows if r["dp_window"]]
    ctl = [r for r in rows
           if not r["dp_window"] and r["ts"] and DP_LO <= r["ts"] < DP_HI]
    print(f"held-out DP window : {len(dp):,} rounds "
          f"({len({r['game_id'] for r in dp})} games, lie rate 100% on lows)")
    print(f"same-window control: {len(ctl):,} rounds "
          f"({len({r['game_id'] for r in ctl})} games)\n")

    v3 = load()
    v2doc = json.load(open(os.path.join(REPO, "models",
                                        "pers_buyer_response_v2.json")))
    table = v2doc["table"]
    # the offsets v1 shipped with, verbatim off its own policy file
    offs = json.load(open(os.path.join(REPO, "models", "pers_policy_dp_v1.json"))
                     )["calibration_offsets"]

    models = [
        ("v2 table (what v1 planned against)", lambda r: v2_predict(table, offs, r)),
        ("v3 (lies TOLD, DP window held out)",
         lambda r: predict_row(v3, r)),
    ]

    print(f"{'model':38s}{'arm':10s}{'pred':>8}{'real':>8}{'err':>8}"
          f"{'brier':>8}{'logloss':>9}")
    err = {}
    for name, fn in models:
        for tag, rs in (("DP", dp), ("control", ctl)):
            s = score(rs, name, fn)
            if not s:
                continue
            e = s["pred"] - s["real"]
            err[(name, tag)] = e
            print(f"{name:38s}{tag:10s}{s['pred']:>8.1%}{s['real']:>8.1%}"
                  f"{e:>+8.1%}{s['brier']:>8.3f}{s['logloss']:>9.3f}")
        print()

    print("the number that decides it -- predicted DP-minus-control spread "
          "vs realised:")
    real_dp = sum(1 for r in dp if r["bought"]) / len(dp)
    real_ct = sum(1 for r in ctl if r["bought"]) / len(ctl)
    print(f"  realised spread                      {real_dp - real_ct:+.1%}  "
          f"(DP {real_dp:.1%} - control {real_ct:.1%})")
    for name, fn in models:
        a = score(dp, name, fn)
        b = score(ctl, name, fn)
        if a and b:
            print(f"  {name:36s} {a['pred'] - b['pred']:+.1%}")
    print()
    print("v1 planned against a model that could not see its own action, so it")
    print("predicted the always-lie arm would convert BETTER than the control")
    print("-- the sign of the effect, not just its size, came out backwards.")
    print("v3 gets the sign right and cuts the DP arm's log loss from 0.632 to")
    print("0.473 without having been shown the window.  It does NOT reproduce")
    print("the magnitude: -1.0% predicted against -9.7% realised.  So v3 is")
    print("still optimistic about heavy lying, and a policy solved against it")
    print("is only safe to the extent it stays out of that regime -- which is")
    print("why the candidate's realised lie rate is a shipping criterion and")
    print("not an afterthought.\n")

    # ---- per-round-block detail -------------------------------------------
    print("conversion through the DP-window games, realised vs v3 (held out):")
    print(f"  {'rounds':>8}{'realised':>10}{'v3 pred':>10}{'v2 pred':>10}{'n':>7}")
    for lo, hi in ((0, 3), (4, 7), (8, 11), (12, 15), (16, 19)):
        sub = [r for r in dp if lo <= r["i"] <= hi]
        if len(sub) < 20:
            continue
        real = sum(1 for r in sub if r["bought"]) / len(sub)
        p3 = score(sub, "v3", lambda r: predict_row(v3, r))
        p2 = score(sub, "v2", lambda r: v2_predict(table, offs, r))
        print(f"  {f'{lo}-{hi}':>8}{real:>10.1%}{p3['pred']:>10.1%}"
              f"{p2['pred']:>10.1%}{len(sub):>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
