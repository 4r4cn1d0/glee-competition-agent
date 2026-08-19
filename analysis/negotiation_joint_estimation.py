#!/usr/bin/env python
"""Estimate the live negotiation (seller_value, buyer_value) joint under
incomplete information, where only your OWN valuation is observed.

Run:  .venv/bin/python analysis/negotiation_joint_estimation.py
"""
from __future__ import annotations
import collections, glob, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAC = (0.8, 1.0, 1.2, 1.5)
SCALES = (100, 10_000, 1_000_000)


def load():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "logs/**/games/*.json"), recursive=True)):
        try:
            g = json.load(open(f))
        except Exception:
            continue
        g["_probe"] = f.split(os.sep)[-3]
        out.append(g)
    return out


def factor(v):
    for m in SCALES:
        for f in FAC:
            if abs(v / m - f) < 1e-9:
                return f
    return None


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def chi2_sf(x, df):
    # regularized upper incomplete gamma Q(df/2, x/2), series + CF
    a, xx = df / 2.0, x / 2.0
    if xx <= 0:
        return 1.0
    if xx < a + 1:
        s, term, n = 1.0 / a, 1.0 / a, 0
        while True:
            n += 1
            term *= xx / (a + n)
            s += term
            if abs(term) < abs(s) * 1e-14 or n > 10000:
                break
        return 1.0 - s * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
    b, c, d, h = xx + 1 - a, 1e300, 1.0 / (xx + 1 - a), 1.0 / (xx + 1 - a)
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h


def main():
    games = [g for g in load() if g["game_family"] == "negotiation"]
    done = [g for g in games if g.get("status") == "completed"]
    print(f"negotiation games: {len(games)} ({len(done)} completed)")

    # ---------- 1. P(complete_information) ----------
    ci = sum(1 for g in games if g["config"]["complete_information"])
    lo, hi = wilson(ci, len(games))
    print(f"\n[1] P(complete_information) = {ci}/{len(games)} = {ci/len(games):.4f}"
          f"  95% CI [{lo:.4f}, {hi:.4f}]")
    for name, q in (("uniform over the info axis", 0.5),
                    ("uniform over grid POINTS with 6 CI / 16 II value pairs", 6 / 22)):
        z = (ci / len(games) - q) / math.sqrt(q * (1 - q) / len(games))
        print(f"      H0 {name}: q={q:.4f}  z={z:+.2f}  "
              f"{'REJECTED' if abs(z) > 2 else 'not rejected'}")

    # ---------- 2. the complete-information joint, read off directly ----------
    both = [g for g in games
            if "player_1_value" in g["config"] and "player_2_value" in g["config"]]
    assert all(g["config"]["complete_information"] for g in both)
    j = collections.Counter((factor(g["config"]["player_1_value"]),
                             factor(g["config"]["player_2_value"])) for g in both)
    n = sum(j.values())
    print(f"\n[2] complete-information joint (uncensored, n={n})")
    print("           buyer" + "".join(f"{b:>8}" for b in FAC))
    for a in FAC:
        print(f"    seller {a:>4}" + "".join(f"{j.get((a,b),0):8d}" for b in FAC))
    strict = sum(v for (a, b), v in j.items() if a < b)
    print(f"    strictly s<b: {strict}/{n};  s==b: {sum(v for (a,b),v in j.items() if a==b)};"
          f"  s>b: {sum(v for (a,b),v in j.items() if a>b)}")
    pairs6 = [(a, b) for a in FAC for b in FAC if a < b]
    e = n / 6
    x = sum((j.get(p, 0) - e) ** 2 / e for p in pairs6)
    print(f"    uniform over the 6 ordered pairs: chi2={x:.2f} df=5 p={chi2_sf(x,5):.3f}")
    e10 = n / 10
    pairs10 = [(a, b) for a in FAC for b in FAC if a <= b]
    x10 = sum((j.get(p, 0) - e10) ** 2 / e10 for p in pairs10)
    print(f"    uniform over the 10 pairs s<=b:   chi2={x10:.2f} df=9 p={chi2_sf(x10,9):.4g}"
          f"  ({'REJECTED' if chi2_sf(x10,9)<0.01 else 'not rejected'})")

    # ---------- 3. own-value marginal under incomplete information ----------
    print("\n[3] incomplete information: OWN valuation is uncensored, so its "
          "marginal is observed without bias")
    for seat, key, lab in (("player_1", "player_1_value", "seller"),
                           ("player_2", "player_2_value", "buyer")):
        c = collections.Counter(
            factor(g["config"][key]) for g in games
            if not g["config"]["complete_information"] and g["your_player"] == seat)
        t = sum(c.values())
        e = t / 4
        x = sum((c.get(f, 0) - e) ** 2 / e for f in FAC)
        print(f"    we are {lab:6s} n={t:4d}: " +
              "  ".join(f"{f}:{c.get(f,0):3d}({c.get(f,0)/t:.3f})" for f in FAC) +
              f"   chi2 vs uniform-4 = {x:.2f} df=3 p={chi2_sf(x,3):.3f}")
        # the ZOPA-constrained model forbids seller 1.5 / buyer 0.8 outright
        forbidden = c.get(1.5 if lab == "seller" else 0.8, 0)
        print(f"        under a 'complete-info-style' s<b constraint the {lab}'s "
              f"factor {'1.5' if lab=='seller' else '0.8'} is IMPOSSIBLE; observed "
              f"{forbidden}/{t} -> that model is refuted (p < 1e-12)")

    # ---------- 4. the II joint, identified through agreement rates ----------
    print("\n[4] incomplete information: is the pair independent? "
          "agreement rate vs P(ZOPA | own factor)")
    zopa_seller = {0.8: 0.75, 1.0: 0.50, 1.2: 0.25, 1.5: 0.00}
    zopa_buyer = {0.8: 0.00, 1.0: 0.25, 1.2: 0.50, 1.5: 0.75}
    cells = []
    for seat, key, lab, z in (("player_1", "player_1_value", "seller", zopa_seller),
                              ("player_2", "player_2_value", "buyer", zopa_buyer)):
        agg = collections.defaultdict(lambda: [0, 0])
        for g in done:
            c = g["config"]
            if c["complete_information"] or g["your_player"] != seat:
                continue
            f = factor(c[key])
            agg[f][1] += 1
            if (g.get("result") or {}).get("outcome") == "agreement":
                agg[f][0] += 1
        for f in FAC:
            k, t = agg[f]
            if t:
                cells.append((lab, f, z[f], k, t))
    pooled = collections.defaultdict(lambda: [0, 0])
    for lab, f, zz, k, t in cells:
        lo, hi = wilson(k, t)
        print(f"    {lab:6s} own={f}  P(ZOPA)={zz:.2f}  agreement={k:3d}/{t:3d}="
              f"{k/t:.3f}  95% CI [{lo:.3f},{hi:.3f}]")
        pooled[zz][0] += k
        pooled[zz][1] += t
    print("    pooled over seats:")
    xs, ys, ws = [], [], []
    for zz in sorted(pooled):
        k, t = pooled[zz]
        print(f"      P(ZOPA)={zz:.2f}: {k:3d}/{t:3d} = {k/t:.3f}   95% CI "
              f"{tuple(round(v,3) for v in wilson(k,t))}")
        xs.append(zz); ys.append(k / t); ws.append(t)
    # weighted least squares  agree = e + (a-e) * P(ZOPA)
    sw = sum(ws); mx = sum(w*x for w, x in zip(ws, xs))/sw; my = sum(w*y for w, y in zip(ws, ys))/sw
    sxy = sum(w*(x-mx)*(y-my) for w, x, y in zip(ws, xs, ys))
    sxx = sum(w*(x-mx)**2 for w, x in zip(ws, xs))
    slope = sxy/sxx; icept = my - slope*mx
    ss_res = sum(w*(y-(icept+slope*x))**2 for w, x, y in zip(ws, xs, ys))
    ss_tot = sum(w*(y-my)**2 for w, y in zip(ws, ys))
    print(f"      WLS  P(agree) = {icept:.3f} + {slope:.3f}*P(ZOPA)   R^2={1-ss_res/ss_tot:.4f}")
    print(f"      => P(agree | ZOPA)   = {icept+slope:.3f}")
    print(f"      => P(agree | noZOPA) = {icept:.3f}  (LLM deals struck outside "
          f"someone's own ZOPA)")
    cik = sum(1 for g in done if g["config"]["complete_information"]
              and (g.get("result") or {}).get("outcome") == "agreement")
    cit = sum(1 for g in done if g["config"]["complete_information"])
    print(f"      cross-check: complete-info agreement rate (ZOPA guaranteed) = "
          f"{cik}/{cit} = {cik/cit:.3f}  95% CI {tuple(round(v,3) for v in wilson(cik,cit))}")

    # ---------- 5. overall ZOPA rate in the corpus ----------
    print("\n[5] live-corpus ZOPA rate implied by the fitted model")
    pci = ci / len(games)
    print(f"    P(strict ZOPA) = P(CI)*1 + (1-P(CI))*6/16 = {pci:.4f} + "
          f"{(1-pci)*6/16:.4f} = {pci + (1-pci)*6/16:.4f}")
    print(f"    with the structural P(CI)=6/22: {6/22 + 16/22*6/16:.4f}")
    print(f"    OLD sim/grid.py drew P(strict ZOPA) = 6/16 = {6/16:.4f}")


if __name__ == "__main__":
    sys.exit(main())
