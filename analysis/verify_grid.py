#!/usr/bin/env python
"""Proof that sim/grid.py now draws what the live server draws.

Samples 5,000 configurations per family from the OLD grid (archived in
``analysis/grid_legacy.py``) and from the NEW one, and prints both against the
live corpus in ``logs/**/games/*.json``, marginal by marginal, with a chi2
goodness-of-fit of each sampler against the observed counts.

    .venv/bin/python analysis/verify_grid.py

The corpus is CENSORED: under incomplete information the server sends you your
own valuation and omits the opponent's. So each axis is compared in the frame
where the corpus can actually see it --

  * bargaining ``delta``: pooled over both sides (both visible under complete
    information, exactly one under incomplete), because the pair is uniform
    over all 16 and the pooled marginal is therefore the whole story;
  * negotiation valuations: the full joint under complete information (where
    both are visible), and the OWN-side marginal under incomplete information
    (where only one is);
  * persuasion ``v``: only the 373 games where it is disclosed.

Comparing a sampler's uncensored draw against a censored corpus without doing
this is how the old grid survived: its complete-information marginals were
wrong in a direction the pooled numbers hid.
"""
from __future__ import annotations

import collections
import glob
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from analysis.grid_legacy import sample_config as sample_old   # noqa: E402
from sim.grid import MONEY_SCALES, NEGOTIATION_VALUE_FACTORS   # noqa: E402
from sim.grid import all_configs, sample_config as sample_new  # noqa: E402
from analysis.grid_legacy import all_configs as all_configs_old  # noqa: E402

N_DRAWS = 5000
SEED = 20260819
FAMILIES = ("bargaining", "negotiation", "persuasion")


# --------------------------------------------------------------------------
# statistics (no scipy in this repo)

def chi2_sf(x, df):
    a, xx = df / 2.0, x / 2.0
    if xx <= 0:
        return 1.0
    if xx < a + 1:
        total = term = 1.0 / a
        for n in range(1, 10000):
            term *= xx / (a + n)
            total += term
            if abs(term) < abs(total) * 1e-14:
                break
        return 1.0 - total * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
    b, c, d = xx + 1 - a, 1e300, 1.0 / (xx + 1 - a)
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h


def gof(observed: dict, model: dict):
    """chi2 of measured counts against a sampler's probabilities."""
    keys = sorted(set(observed) | set(model), key=str)
    n = sum(observed.values())
    chi2, impossible = 0.0, []
    for key in keys:
        expected = model.get(key, 0.0) * n
        if expected <= 0:
            if observed.get(key, 0):
                impossible.append(key)
            continue
        chi2 += (observed.get(key, 0) - expected) ** 2 / expected
    df = len(keys) - 1
    if impossible:
        return float("inf"), df, impossible
    return chi2, df, []


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (centre - half, centre + half)


# --------------------------------------------------------------------------
# the live corpus

def load_corpus():
    out = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, "logs/**/games/*.json"),
                                 recursive=True)):
        try:
            with open(path) as handle:
                game = json.load(handle)
        except (OSError, ValueError):
            continue
        if game.get("config"):
            out[game["game_family"]].append(game)
    return out


def factor(value):
    for scale in MONEY_SCALES:
        for f in NEGOTIATION_VALUE_FACTORS:
            if abs(value / scale - f) < 1e-9:
                return f
    return None


def corpus_axes(family, games):
    """The corpus, cut into the frames where it is uncensored."""
    out = collections.defaultdict(collections.Counter)
    for game in games:
        c, seat = game["config"], game.get("your_player")
        if family == "bargaining":
            out["money_to_divide"][c["money_to_divide"]] += 1
            out["horizon_known"][c["horizon_known"]] += 1
            out["complete_information"][c["complete_information"]] += 1
            out["messages_allowed"][c["messages_allowed"]] += 1
            for key in ("delta_1", "delta_2"):
                if key in c:
                    out["delta (pooled, visible only)"][c[key]] += 1
            if "delta_1" in c and "delta_2" in c:
                out["delta pair | complete info"][(c["delta_1"], c["delta_2"])] += 1
        elif family == "negotiation":
            out["complete_information"][c["complete_information"]] += 1
            out["max_rounds (None = undisclosed)"][c.get("max_rounds")] += 1
            out["messages_allowed"][c["messages_allowed"]] += 1
            if c["complete_information"]:
                if "player_1_value" in c and "player_2_value" in c:
                    out["value pair | complete info"][
                        (factor(c["player_1_value"]), factor(c["player_2_value"]))] += 1
            else:
                if "player_1_value" in c:
                    out["seller factor | incomplete info"][factor(c["player_1_value"])] += 1
                if "player_2_value" in c:
                    out["buyer factor | incomplete info"][factor(c["player_2_value"])] += 1
        else:
            out["p"][c["p"]] += 1
            out["product_price"][c["product_price"]] += 1
            out["is_seller_know_cv"][c["is_seller_know_cv"]] += 1
            out["seller_message_type"][c["seller_message_type"]] += 1
            out["total_rounds"][c["total_rounds"]] += 1
            if "v" in c:
                out["v factor (visible only)"][round(c["v"] / c["product_price"], 3)] += 1
            if "u" in c:
                out["u (visible only)"][c["u"]] += 1
    return out


def sampler_axes(family, sampler, n=N_DRAWS, seed=SEED):
    """The same cuts, taken from a sampler's draws."""
    rng = random.Random(seed)
    out = collections.defaultdict(collections.Counter)
    for _ in range(n):
        p = sampler(family, rng).params
        if family == "bargaining":
            out["money_to_divide"][p["money_to_divide"]] += 1
            out["horizon_known"][p["horizon_known"]] += 1
            out["complete_information"][p["complete_information"]] += 1
            out["messages_allowed"][p["messages_allowed"]] += 1
            out["delta (pooled, visible only)"][p["delta_1"]] += 1
            out["delta (pooled, visible only)"][p["delta_2"]] += 1
            if p["complete_information"]:
                out["delta pair | complete info"][(p["delta_1"], p["delta_2"])] += 1
        elif family == "negotiation":
            scale = next(m for m in MONEY_SCALES
                         if round(p["player_1_value"] / m, 6) in NEGOTIATION_VALUE_FACTORS)
            s, b = p["player_1_value"] / scale, p["player_2_value"] / scale
            out["complete_information"][p["complete_information"]] += 1
            out["max_rounds (None = undisclosed)"][p.get("max_rounds")] += 1
            out["messages_allowed"][p["messages_allowed"]] += 1
            if p["complete_information"]:
                out["value pair | complete info"][(round(s, 3), round(b, 3))] += 1
            else:
                out["seller factor | incomplete info"][round(s, 3)] += 1
                out["buyer factor | incomplete info"][round(b, 3)] += 1
        else:
            out["p"][p["p"]] += 1
            out["product_price"][p["product_price"]] += 1
            out["is_seller_know_cv"][p["is_seller_know_cv"]] += 1
            out["seller_message_type"][p["seller_message_type"]] += 1
            out["total_rounds"][p["total_rounds"]] += 1
            out["v factor (visible only)"][round(p["v"] / p["product_price"], 3)] += 1
            out["u (visible only)"][p["u"]] += 1
    return out


def as_probs(counter):
    total = sum(counter.values())
    return {k: v / total for k, v in counter.items()} if total else {}


# --------------------------------------------------------------------------

def report_family(family, games, out=print):
    corpus = corpus_axes(family, games)
    old = sampler_axes(family, sample_old)
    new = sampler_axes(family, sample_new)

    out(f"\n{'='*88}\n{family.upper()}   live n={len(games)}   "
        f"{N_DRAWS} draws per sampler\n{'='*88}")
    for axis in corpus:
        observed = corpus[axis]
        n = sum(observed.values())
        pold, pnew = as_probs(old.get(axis, collections.Counter())), as_probs(new.get(axis, collections.Counter()))
        keys = sorted(set(observed) | set(pold) | set(pnew), key=str)
        cold, dfo, impo = gof(dict(observed), pold)
        cnew, dfn, impn = gof(dict(observed), pnew)
        out(f"\n  {axis}   (n={n})")
        out(f"      {'value':>26}  {'live':>8}  {'OLD grid':>9}  {'NEW grid':>9}")
        for key in keys:
            live = observed.get(key, 0) / n if n else 0.0
            out(f"      {str(key):>26}  {live:8.4f}  {pold.get(key, 0.0):9.4f}  "
                f"{pnew.get(key, 0.0):9.4f}")
        def verdict(chi2, df, imp):
            if imp:
                return f"chi2=inf  (sampler gives probability 0 to {imp[:3]}) REJECTED"
            p = chi2_sf(chi2, df) if df > 0 else 1.0
            mark = "ok" if p > 1e-3 else "REJECTED"
            return f"chi2={chi2:8.2f} df={df:2d} p={p:.3g}  {mark}"
        out(f"      OLD vs live: {verdict(cold, dfo, impo)}")
        out(f"      NEW vs live: {verdict(cnew, dfn, impn)}")


def zopa_report(games, out=print):
    out(f"\n{'='*88}\nZONE OF AGREEMENT -- the headline number\n{'='*88}")

    # live, complete information: directly observable
    both = [g["config"] for g in games
            if "player_1_value" in g["config"] and "player_2_value" in g["config"]]
    ci_zopa = sum(1 for c in both if c["player_1_value"] < c["player_2_value"])
    lo, hi = wilson(ci_zopa, len(both))
    out(f"\n  live, complete information (both valuations visible, n={len(both)}):")
    out(f"      strict ZOPA {ci_zopa}/{len(both)} = {ci_zopa/len(both):.4f}  "
        f"95% CI [{lo:.4f}, {hi:.4f}]")

    # live, overall: estimated, because the incomplete branch is censored
    n = len(games)
    ci = sum(1 for g in games if g["config"]["complete_information"])
    p_ci = ci / n
    lo, hi = wilson(ci, n)
    est = p_ci + (1 - p_ci) * 6 / 16
    est_lo = lo + (1 - lo) * 6 / 16
    est_hi = hi + (1 - hi) * 6 / 16
    out(f"\n  live, overall (ESTIMATED -- the incomplete branch is censored):")
    out(f"      P(complete information)      = {ci}/{n} = {p_ci:.4f}  "
        f"95% CI [{lo:.4f}, {hi:.4f}]")
    out(f"      P(ZOPA | complete)           = 1.0000  (measured, {ci_zopa}/{len(both)})")
    out(f"      P(ZOPA | incomplete)         = 6/16 = 0.3750  (independent uniform "
        f"pair; see analysis/negotiation_joint_estimation.py)")
    out(f"      => P(strict ZOPA)            = {est:.4f}  95% CI [{min(est_lo,est_hi):.4f},"
        f" {max(est_lo,est_hi):.4f}]")

    for label, sampler in (("OLD grid", sample_old), ("NEW grid", sample_new)):
        rng = random.Random(SEED)
        draws = [sampler("negotiation", rng).params for _ in range(N_DRAWS)]
        strict = sum(1 for p in draws if p["player_1_value"] < p["player_2_value"])
        zero = sum(1 for p in draws if p["player_1_value"] == p["player_2_value"])
        none = N_DRAWS - strict - zero
        cinfo = sum(1 for p in draws if p["complete_information"])
        ci_bad = sum(1 for p in draws
                     if p["complete_information"]
                     and p["player_1_value"] >= p["player_2_value"])
        out(f"\n  {label} ({N_DRAWS} draws):")
        out(f"      P(complete information)      = {cinfo/N_DRAWS:.4f}")
        out(f"      P(strict ZOPA)               = {strict/N_DRAWS:.4f}")
        out(f"      P(zero surplus)              = {zero/N_DRAWS:.4f}")
        out(f"      P(NO zone of agreement)      = {none/N_DRAWS:.4f}")
        out(f"      complete-info games with no strict ZOPA = {ci_bad}/{cinfo} = "
            f"{ci_bad/cinfo:.4f}   (live: 0/{len(both)})")

    out(f"\n  grid sizes:  bargaining / negotiation / persuasion / total")
    o = [len(all_configs_old(f)) for f in FAMILIES]
    nw = [len(all_configs(f)) for f in FAMILIES]
    out(f"      OLD:  {o[0]} / {o[1]} / {o[2]} / {sum(o)}")
    out(f"      NEW:  {nw[0]} / {nw[1]} / {nw[2]} / {sum(nw)}   "
        f"<- docs/reference/glee-docs.md says 960")


def main():
    corpus = load_corpus()
    total = sum(len(v) for v in corpus.values())
    print(f"live corpus: {total} games "
          + ", ".join(f"{k}={len(v)}" for k, v in sorted(corpus.items())))
    for family in FAMILIES:
        report_family(family, corpus[family])
    zopa_report(corpus["negotiation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
