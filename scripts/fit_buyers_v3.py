#!/usr/bin/env python3
"""Buyer-response model v3: conditioned on what the SELLER did, not on outcomes.

v2 fitted P(buy | mode, prior, ratio, rec, lies-CAUGHT).  Lies-caught only ever
increments when the buyer BOUGHT a recommended low unit, so it is a tally of the
buyer's own purchases.  Conditioning a transition kernel on it inverts the sign
of the thing a planner cares about: pooled, conversion appears to RISE 42pp
after two caught lies, and the DP that planned against it shipped the always-lie
policy and lost 13pp of conversion live.

v3 replaces that coordinate with the seller's own action record:

    L = lies TOLD so far      (recommended low units, bought or not)
    n = declines shown so far (rounds we said no)
    t = rounds elapsed        (so recommendations shown = t - n)

All three are exogenous in the fitted data.  In the knows-values branch the
shading heuristic's recommendation at round t is a deterministic function of the
cell, q*, and the quality sequence nature drew -- it never reads the buyer.  So
L, n and t are independent of buyer type given the cell, and the regression
identifies the causal price of lying rather than the selection that comes with
it.  They are also the coordinates the seller CONTROLS, which is what makes them
usable as a DP state: the planner can move them, and moving them is the decision.

The functional form carries the one piece of theory that matters.  A Bayesian
buyer keeps buying while the seller's apparent lie rate stays under the
sustainable ceiling

    q* = p(v - price) / ((1 - p)(price - u)),

and stops when it does not, so conversion should not fall linearly in L -- it
should fall off a cliff once the visible lie rate qhat = L / (t - n) crosses q*,
and fall harder the more rounds of evidence the buyer has had to notice.  The
model gets `excess = max(0, qhat - q*)` and its evidence-weighted form as
features; without them a linear-in-L fit cannot bend hard enough to call the
always-lie regime, and under-prices exactly the policy the DP is tempted by.

    logit P(buy) = a[cell] + b . (rec, L, n, t, qhat, excess, seen*excess,
                                  rec*L, rec*n, rec*qhat, rec*excess)

Fitted with Adam on bucketed sufficient statistics (every feature is a function
of the discrete tuple (cell, rec, L, n, t), so identical rows collapse; there is
no numpy in this venv and the bucketing is what makes the fit tractable).

Output: models/pers_buyer_response_v3.json
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from scripts.pers_data import iter_rounds, RATIOS          # noqa: E402
from scripts.diag_pers_window import DP_LO, DP_HI          # noqa: E402
from glee_agent.strategies.persuasion import optimal_lie_rate   # noqa: E402

OUT = os.path.join(REPO, "models", "pers_buyer_response_v3.json")
FEATS = ("rec", "L", "n", "t", "qhat", "excess", "ev_excess",
         "recL", "recn", "recq", "recx")
L2 = 3e-4


def features(rec, L, n, t, qstar):
    """Feature vector -- every entry a function of our own moves plus q*."""
    recs = max(t - n, 0)
    qhat = (L / recs) if recs > 0 else 0.0
    excess = max(0.0, qhat - qstar)
    ev = min(recs, 10) / 10.0            # how much evidence the buyer has had
    r = 1.0 if rec else 0.0
    return (r, L / 10.0, n / 10.0, t / 10.0, qhat, excess, ev * excess,
            r * L / 10.0, r * n / 10.0, r * qhat, r * excess)


def qstar_of(r):
    return optimal_lie_rate(r["p"], r["v"], r["u"], r["price"])


def rounds_with_told(exclude_dp=True):
    """Every logged seller round, carrying the exogenous lies-TOLD counter."""
    out = []
    cur, told = None, 0
    for r in iter_rounds():
        in_dp = bool(r["ts"] and DP_LO <= r["ts"] < DP_HI and r["agent"] == "conceder")
        if r["game_id"] != cur:
            cur, told = r["game_id"], 0
        rr = dict(r, told=told, dp_window=in_dp)
        if not (exclude_dp and in_dp):
            out.append(rr)
        if rr["rec"] and rr["quality"] == "low":
            told += 1
    return out


def bucketize(rows):
    """Collapse identical (cell, rec, L, n, t, q*) rows to (x, buys, n)."""
    agg = defaultdict(lambda: [0, 0])
    for r in rows:
        key = (r["pb"], r["rb"], bool(r["rec"]), r["told"], r["nos_seen"],
               r["i"], round(qstar_of(r), 2))
        a = agg[key]
        a[1] += 1
        a[0] += 1 if r["bought"] else 0
    cells = sorted({(k[0], k[1]) for k in agg})
    ci = {c: i for i, c in enumerate(cells)}
    data = []
    for (pb, rb, rec, L, n, t, qs), (k, m) in agg.items():
        data.append((ci[(pb, rb)], features(rec, L, n, t, qs), float(k), float(m)))
    return cells, ci, data


def fit_mode(rows, iters=4000, lr=0.08, verbose=False):
    cells, ci, data = bucketize(rows)
    nf = len(FEATS)
    a = [0.0] * len(cells)
    b = [0.0] * nf
    ma, va = [0.0] * len(cells), [0.0] * len(cells)
    mb, vb = [0.0] * nf, [0.0] * nf
    N = sum(m for _, _, _, m in data)
    b1, b2, eps = 0.9, 0.999, 1e-8
    for it in range(1, iters + 1):
        ga = [0.0] * len(cells)
        gb = [0.0] * nf
        ll = 0.0
        for c, x, k, m in data:
            z = a[c]
            for j in range(nf):
                z += b[j] * x[j]
            z = 30.0 if z > 30.0 else (-30.0 if z < -30.0 else z)
            p = 1.0 / (1.0 + math.exp(-z))
            e = p * m - k                       # d(-loglik)/dz summed over bucket
            ga[c] += e
            for j in range(nf):
                gb[j] += e * x[j]
            ll += k * math.log(max(p, 1e-12)) + (m - k) * math.log(max(1 - p, 1e-12))
        bc1 = 1 - b1 ** it
        bc2 = 1 - b2 ** it
        for i in range(len(a)):
            g = ga[i] / N
            ma[i] = b1 * ma[i] + (1 - b1) * g
            va[i] = b2 * va[i] + (1 - b2) * g * g
            a[i] -= lr * (ma[i] / bc1) / (math.sqrt(va[i] / bc2) + eps)
        for j in range(nf):
            g = gb[j] / N + L2 * b[j]
            mb[j] = b1 * mb[j] + (1 - b1) * g
            vb[j] = b2 * vb[j] + (1 - b2) * g * g
            b[j] -= lr * (mb[j] / bc1) / (math.sqrt(vb[j] / bc2) + eps)
        if verbose and it % 1000 == 0:
            print(f"    it{it:>5} loglik/n {ll/N:.4f}  ({len(data):,} buckets)")
    out = {"cells": {f"{pb}|r{rb}": round(a[ci[(pb, rb)]], 4) for pb, rb in cells},
           "beta": {f: round(v, 4) for f, v in zip(FEATS, b)}}
    out["cell_slope"] = _cell_slopes(rows, out, iters=1500, lr=0.05)
    return out


def _cell_slopes(rows, model, iters=2500, lr=0.08, l2=0.003):
    """Per-cell correction to the price of lying, on top of the pooled fit.

    The pooled coefficients are shared across a mode's fifteen cells, so a
    strong average penalty for a visible lie bleeds into cells where lying is
    genuinely close to free -- the high v/price cells, where the prior alone
    almost clears the price and buyers do keep buying.  Left uncorrected the
    solver turns honest in exactly those cells and gives up sales for nothing;
    the seller replay measured that as the candidate's worst cells.

    Stage two therefore fits two extra numbers per cell, an intercept and a
    slope on rec*qhat, shrunk to zero by L2 so a thin cell stays at the pooled
    answer.  q* already varies by cell in the theory; this lets the data say so.
    """
    by_cell = defaultdict(list)
    for r in rows:
        recs = max(r["i"] - r["nos_seen"], 0)
        qhat = (r["told"] / recs) if recs > 0 else 0.0
        base = predict({"modes": {"m": model}}, "m", r["pb"], r["rb"], r["rec"],
                       r["told"], r["nos_seen"], r["i"], qstar_of(r))
        z0 = math.log(max(base, 1e-9) / max(1 - base, 1e-9))
        by_cell[f"{r['pb']}|r{r['rb']}"].append(
            (z0, 1.0 if r["rec"] else 0.0, qhat, 1.0 if r["bought"] else 0.0))
    out = {}
    for cell, obs in by_cell.items():
        if len(obs) < 300:
            continue
        a = s = 0.0
        n = len(obs)
        for _ in range(iters):
            ga = gs = 0.0
            for z0, rec, qhat, y in obs:
                z = z0 + a + s * rec * qhat
                z = 30.0 if z > 30.0 else (-30.0 if z < -30.0 else z)
                e = 1.0 / (1.0 + math.exp(-z)) - y
                ga += e
                gs += e * rec * qhat
            a -= lr * (ga / n + l2 * a)
            s -= lr * (gs / n + l2 * s)
        out[cell] = [round(a, 4), round(s, 4)]
    return out


def predict(model, mode, pb, rb, rec, told, nos, i, qstar):
    m = model["modes"].get(mode)
    if not m:
        return None
    a = m["cells"].get(f"{pb}|r{rb}")
    if a is None:
        for rb2 in RATIOS:
            a = m["cells"].get(f"{pb}|r{rb2}")
            if a is not None:
                break
    if a is None:
        return None
    x = features(rec, told, nos, i, qstar)
    z = a + sum(m["beta"][f] * xi for f, xi in zip(FEATS, x))
    slope = (m.get("cell_slope") or {}).get(f"{pb}|r{rb}")
    if slope:
        recs = max(i - nos, 0)
        qhat = (told / recs) if recs > 0 else 0.0
        z += slope[0] + slope[1] * (1.0 if rec else 0.0) * qhat
    return 1.0 / (1.0 + math.exp(-max(min(z, 30.0), -30.0)))


def predict_row(model, r):
    return predict(model, r["mode"], r["pb"], r["rb"], r["rec"], r["told"],
                   r["nos_seen"], r["i"], qstar_of(r))


def load(path=OUT):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-dp", action="store_true",
                    help="refit on ALL rounds including the v1 DP window "
                         "(ship model); default holds the window out so it can "
                         "serve as the falsification set")
    ap.add_argument("--out", default=None)
    ap.add_argument("--iters", type=int, default=4000)
    args = ap.parse_args()

    all_rows = rounds_with_told(exclude_dp=False)
    train = all_rows if args.include_dp else [r for r in all_rows if not r["dp_window"]]
    held = [r for r in all_rows if r["dp_window"]]
    print(f"train: {len(train):,} rounds, {len({r['game_id'] for r in train}):,} games"
          f"  ({'INCLUDING' if args.include_dp else 'excluding'} the DP window)")
    print(f"DP window: {len(held):,} rounds, "
          f"{len({r['game_id'] for r in held}):,} games\n")

    doc = {"_schema": "glee.pers_buyer_response/v3",
           "_note": ("conditioned on lies TOLD and declines SHOWN -- both "
                     "exogenous under the shading heuristic and both under the "
                     "seller's control; the v2 lies-CAUGHT coordinate is an "
                     "outcome and inverts the sign of the lie gradient"),
           "_train_rounds": len(train),
           "_includes_dp_window": bool(args.include_dp),
           "modes": {}}
    for mode in ("binary", "text"):
        rows = [r for r in train if r["mode"] == mode]
        print(f"fitting {mode} on {len(rows):,} rounds")
        doc["modes"][mode] = fit_mode(rows, iters=args.iters, verbose=True)
        b = doc["modes"][mode]["beta"]
        print("  beta: " + "  ".join(f"{f}={b[f]:+.2f}" for f in FEATS))
        qs = 0.35
        for L, n, t in ((0, 2, 8), (5, 2, 8), (10, 0, 14), (14, 0, 19)):
            p = predict(doc, mode, "mid", 2.0, True, L, n, t, qs)
            print(f"    P(buy|yes) mid|r2.0 q*={qs}  L={L:>2} n={n} t={t:>2} "
                  f"-> {p:.1%}")
        print()

    out = args.out or OUT
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, out)
    print(f"-> {os.path.relpath(out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
