#!/usr/bin/env python3
"""Fit the responder-seat (Bob) bargaining OFFER model.

Bob is player_2: he responds first and proposes on even rounds. His offer side
was never fitted -- it inherited the proposer machinery written for Alice, whose
aspiration derives from ``proposer_share()``. That recursion oscillates with
round parity, and the oscillation is worst exactly in Bob's seat: a disclosed
game states max_rounds = 12, an EVEN cap, so the last proposer is player_2 and
the recursion hands Bob 0.77-1.00 of the pot on every even round while handing
Alice 0.00-0.74 on every odd one. The last word is real; it is also worthless,
because banking it costs ten more rounds of discount (delta_me = 0.8 turns a
round-12 agreement into 8.6% of its face value). So Bob's ask is pinned at the
opponent-floor cap in every configuration -- 532 of his 704 logged offers land
in the single bin [0.60, 0.65) -- and the ask carries no information about
whether this particular opponent will take it.

What actually decides whether an offer closes, measured over the 11,022 offers
we have made across 6,276 logged bargaining games, is the OPPONENT's discount
factor, not our equilibrium claim. At a give of 0.35-0.45 of the pot:

    delta_opp = 0.80  ->  63.6% accept   (n=761)
    delta_opp = 0.90  ->  31.0%          (n=680)
    delta_opp = 0.95  ->  15.5%          (n=723)
    delta_opp = 1.00  ->   6.2%          (n=926)

and the rating is a PERCENTILE of the discounted payoff within the configuration
cell, whose distribution has a 9.6% atom at exactly half the pot: crossing it is
worth +0.095 percentile per 0.01 of pot against +0.025 anywhere else.

So this script fits the three objects an expected-percentile offer rule needs,
all from history strictly before the offer:

  accept   P(the responder accepts | give, round, delta_opp, their last demand)
           -- pure-stdlib L2 logistic, grouped-CV reported.
  cdf      the field's payoff/money distribution per configuration cell, i.e.
           the map from a closed deal to the rating it earns.
  vcont    the MEASURED mean realised percentile after one of our offers was
           rejected at that round -- the value of continuing under our own
           policy, split by whether our clock burns.

Output: models/barg_bob_offer_v1.json, consumed by
glee_agent/strategies/bargaining.py under GLEE_BARG_BOB_OFFER.
"""
from __future__ import annotations

import glob
import json
import math
import os
import random
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
OUT = os.path.join(REPO, "models", "barg_bob_offer_v1.json")

#: Read the live corpus by absolute path: logs/ is gitignored, so a worktree
#: has none of it. Override with GLEE_LOG_ROOT.
LOG_ROOT = os.environ.get("GLEE_LOG_ROOT",
                          "/Users/spiderishi/Coding/GLEE Competition/logs")

FEATURES = ("bias", "give", "give_ge_cliff", "dop_centred", "dop_is_one",
            "dop_unknown", "round_ge_4", "round_is_1", "their_demand")
CLIFF = 0.39


def _iter_finals():
    seen = set()
    for path in sorted(glob.glob(os.path.join(LOG_ROOT, "*", "results.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = rec.get("game_id")
                if gid in seen:
                    continue
                seen.add(gid)
                final = rec.get("final") or {}
                if (final.get("game_state") or {}).get("history"):
                    yield final
    for path in sorted(glob.glob(os.path.join(LOG_ROOT, "*", "games", "*.json"))):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                rec = json.load(fh)
        except (ValueError, OSError):
            continue
        gid = rec.get("game_id")
        if gid in seen or not rec.get("history"):
            continue
        seen.add(gid)
        yield {"game_family": rec.get("game_family"),
               "your_player": rec.get("your_player"),
               "game_state": {"history": rec.get("history"),
                              **(rec.get("config") or {}),
                              "result": rec.get("result")}}


def cell_key(money, max_rounds, horizon_known, complete_information) -> str:
    """The rating cell: exactly what the platform scores us within."""
    return "|".join(str(x) for x in (money, max_rounds,
                                     bool(horizon_known), bool(complete_information)))


def _rows():
    """One row per offer WE made, labelled by whether the field took it."""
    rows, cells, cont = [], defaultdict(list), defaultdict(list)
    games = 0
    for final in _iter_finals():
        if final.get("game_family") != "bargaining":
            continue
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        money = gs.get("money_to_divide")
        if not me or not money:
            continue
        them = "player_2" if me == "player_1" else "player_1"
        games += 1
        dme = gs.get(f"delta_{me[-1]}")
        dop = gs.get(f"delta_{them[-1]}")
        res = gs.get("result") or final.get("result") or {}
        key = cell_key(money, gs.get("max_rounds"), gs.get("horizon_known"),
                       gs.get("complete_information"))
        # realised payoff/money -- the axis the rating percentile is taken on
        if res.get("outcome") == "agreement":
            gain = res.get(f"agreed_{me}_gain")
            rnd = res.get("agreed_round") or 1
            realised = (float(gain) / money) * float(dme or 1.0) ** (int(rnd) - 1) \
                if gain is not None else None
        else:
            realised = 0.0
        if realised is not None:
            cells[key].append(round(realised, 4))

        their_demand = None
        for e in gs.get("history") or []:
            if not isinstance(e, dict):
                continue
            off = e.get("offer") or {}
            if not isinstance(off, dict):
                continue
            proposer = off.get("proposer") or e.get("proposer")
            rnd = int(e.get("round") or 1)
            if proposer == me:
                ask = off.get(f"{me}_gain")
                dec = str(e.get("decision") or "").lower()
                if ask is None or dec not in ("accept", "reject", "walkaway"):
                    continue
                rows.append({"give": 1.0 - float(ask) / money, "round": rnd,
                             "dop": dop, "dme": dme, "their_demand": their_demand,
                             "y": 1 if dec == "accept" else 0,
                             "cell": key, "game": id(final)})
                if dec != "accept" and realised is not None:
                    cont[(min(rnd, 6), "patient" if (dme or 1.0) >= 1.0 else "burning")] \
                        .append((key, realised))
            elif proposer == them:
                keep = off.get(f"{them}_gain")
                if keep is not None:
                    their_demand = float(keep) / money
    return rows, cells, cont, games


def featurise(give, rnd, dop, their_demand):
    return [1.0,
            give,
            1.0 if give >= CLIFF else 0.0,
            0.0 if dop is None else (float(dop) - 0.9) * 10.0,
            1.0 if (dop is not None and float(dop) >= 1.0) else 0.0,
            1.0 if dop is None else 0.0,
            1.0 if rnd >= 4 else 0.0,
            1.0 if rnd <= 1 else 0.0,
            0.5 if their_demand is None else float(their_demand)]


def fit_logistic(X, y, lam=0.2, iters=4000, lr=0.35):
    """L2 logistic by plain gradient descent -- no numpy in this repo."""
    k = len(X[0])
    w = [0.0] * k
    n = len(X)
    for _ in range(iters):
        g = [0.0] * k
        for xi, yi in zip(X, y):
            z = sum(wj * xj for wj, xj in zip(w, xi))
            p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
            d = p - yi
            for j in range(k):
                g[j] += d * xi[j]
        for j in range(k):
            gj = g[j] / n + (0.0 if j == 0 else lam * w[j] / n)
            w[j] -= lr * gj
    return w


def logloss(w, X, y):
    tot = 0.0
    for xi, yi in zip(X, y):
        z = sum(wj * xj for wj, xj in zip(w, xi))
        p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
        p = min(max(p, 1e-9), 1 - 1e-9)
        tot += -(yi * math.log(p) + (1 - yi) * math.log(1 - p))
    return tot / len(X)


def auc(w, X, y):
    scores = [sum(wj * xj for wj, xj in zip(w, xi)) for xi in X]
    pos = [s for s, yi in zip(scores, y) if yi == 1]
    neg = [s for s, yi in zip(scores, y) if yi == 0]
    if not pos or not neg:
        return None
    wins = ties = 0
    for p in pos:
        for q in neg:
            if p > q:
                wins += 1
            elif p == q:
                ties += 1
    return (wins + 0.5 * ties) / (len(pos) * len(neg))


def main() -> int:
    rows, cells, cont, games = _rows()
    print(f"corpus: {games} bargaining games, {len(rows)} offers we made, "
          f"accept rate {sum(r['y'] for r in rows)/len(rows):.3f}")

    X = [featurise(r["give"], r["round"], r["dop"], r["their_demand"]) for r in rows]
    y = [r["y"] for r in rows]
    w = fit_logistic(X, y)

    # Grouped CV by game so repeated offers inside one game cannot leak.
    rng = random.Random(11)
    groups = sorted({r["game"] for r in rows})
    rng.shuffle(groups)
    fold = {g: i % 5 for i, g in enumerate(groups)}
    ll = []
    for f in range(5):
        tr = [i for i, r in enumerate(rows) if fold[r["game"]] != f]
        te = [i for i, r in enumerate(rows) if fold[r["game"]] == f]
        if not te:
            continue
        wf = fit_logistic([X[i] for i in tr], [y[i] for i in tr], iters=1500)
        ll.append(logloss(wf, [X[i] for i in te], [y[i] for i in te]))
    base = sum(y) / len(y)
    null = -(base * math.log(base) + (1 - base) * math.log(1 - base))
    print(f"  logistic: cv logloss {sum(ll)/len(ll):.4f} vs intercept-only {null:.4f}; "
          f"in-sample AUC {auc(w, X, y):.4f}")
    for name, coef in zip(FEATURES, w):
        print(f"    {name:>14s} {coef:+.4f}")

    # Payoff CDF per rating cell, quantised to 51 knots.
    cdf = {}
    for key, vals in cells.items():
        if len(vals) < 60:
            continue
        vals.sort()
        cdf[key] = [round(vals[min(len(vals) - 1, int(q * len(vals) / 50))], 4)
                    for q in range(51)]
    print(f"  payoff CDF: {len(cdf)} cells "
          f"({sum(len(v) for v in cells.values())} closed games)")

    # Measured continuation percentile, by round and by whether our clock burns.
    def pct(key, x):
        ref = cells.get(key)
        if not ref:
            return None
        s = sorted(ref)
        import bisect
        lo = bisect.bisect_left(s, x - 1e-9)
        hi = bisect.bisect_right(s, x + 1e-9)
        return (lo + hi) / 2 / len(s)

    vcont = {}
    for (rnd, clock), obs in sorted(cont.items()):
        ps = [pct(k, v) for k, v in obs]
        ps = [p for p in ps if p is not None]
        if len(ps) < 25:
            continue
        vcont[f"{rnd}|{clock}"] = round(sum(ps) / len(ps), 4)
    print("  measured continuation percentile after a rejected offer:")
    for k in sorted(vcont):
        print(f"    round {k}: {vcont[k]:.4f}")

    doc = {
        "_schema": "glee.barg_bob_offer/v1",
        "_corpus_games": games,
        "_offers": len(rows),
        "_accept_rate": round(sum(y) / len(y), 4),
        "accept": {"features": list(FEATURES), "cliff": CLIFF,
                   "coef": [round(c, 5) for c in w],
                   "cv_logloss": round(sum(ll) / len(ll), 4),
                   "intercept_only_logloss": round(null, 4),
                   "auc_in_sample": round(auc(w, X, y), 4)},
        "cdf": cdf,
        "cdf_pooled": sorted(round(v, 4) for vs in cells.values() for v in vs)[::5],
        "vcont": vcont,
        "vcont_default": 0.42,
        "_caveats": [
            "P(accept) is fitted on the field WE met, pooled over opponents; a "
            "named opponent's own profile (models/opponent_profiles.json) is "
            "sharper where it exists.",
            "The CDF is the same object the rating is taken against, so an "
            "argmax over it optimises the true objective -- but it also means "
            "the offline scorer and the policy share a model. The independent "
            "half of any arena result is P(accept), which comes from the "
            "cloned opponents, not from here.",
        ],
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    os.replace(tmp, OUT)
    print(f"wrote {os.path.relpath(OUT, REPO)} "
          f"({os.path.getsize(OUT)/1e3:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
