#!/usr/bin/env python3
"""Buyer-seat persuasion arena: replay logged seller streams against candidates.

The seller-side arena (pers_arena.py) plays against buyer CLONES and carries a
do-not-trust flag because its conversion cells never matched live. This referee
has no clone problem: on the buyer seat the opponent's behaviour is the logged
recommendation stream itself -- real recorded data -- and a candidate buyer is
just a flag dict evaluated through the SAME strategies.persuasion.decide() the
live fleet runs, so the thing that wins here is byte-for-byte the thing that
deploys.

Two stated approximations:

  * Seller streams are replayed frozen: a counterfactual buyer that buys
    differently cannot make the seller recommend differently. Field sellers are
    overwhelmingly template bots, but adaptive ones exist (ours is one), so the
    adaptivity of the population is audited separately, not assumed away.
  * Quality on rounds the ORIGINAL buyer skipped was never revealed and is
    imputed from P(high | this seller, mode, prior-bin, rec, round-tercile)
    fitted on all observed rounds (scripts/fit_seller_imputation.py). Each game
    is replayed under K independent imputation draws; candidates share the
    exact draws, so imputation noise cancels in every pairwise comparison.

Scoring currency: mean payoff normalised by price, plus loss (<=0) and negative
rates, per (mode, prior-bin, v/price-bin) cell -- there is no fitted percentile
model for persuasion, and that limitation is stated rather than papered over.
Deltas vs the control arm are paired per (game, draw) and bootstrapped by game.

Usage:
    .venv/bin/python -m sim.pers_buyer_replay candidates.json [--draws 3]
        [--limit N] [--seed 11] [--json out.json]

candidates.json: {"name": {FLAG: value, ...}, ...}. The control arm "v1" (no
flags: the live v1 buyer) is always added; "historical" (the decisions actually
taken at the time) is reported as an anchor.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import random
import sys
from collections import defaultdict
from types import SimpleNamespace

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

SLOTS = ("champion", "hardliner", "conceder", "randomized", "composite")
IMPUTE_PATH = os.path.join(REPO, "models", "pers_seller_imputation_v1.json")
#: Read-time smoothing toward the config prior, in pseudo-observations.
ALPHA = 4.0
RATIO_BINS = (1.2, 1.25, 2.0, 3.0, 4.0)

_CFG = SimpleNamespace(pers_lie_shading=1.0, pers_honest_rounds=0)


def _set_flags(flags: dict) -> None:
    from glee_agent import runtime_flags
    for k in list(os.environ):
        if k.startswith("GLEE_PERS_") or k == "GLEE_PROBE":
            del os.environ[k]
    os.environ.update({k: str(v) for k, v in flags.items()})
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def pbin(p: float) -> str:
    return "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")


def tercile(round_no: int, total: int) -> str:
    f = round_no / max(total, 1)
    return "early" if f <= 1 / 3 else ("mid" if f <= 2 / 3 else "late")


def load_games(limit: int | None):
    from glee_agent.strategies.persuasion import _recommended
    games = []
    for slot in SLOTS:
        for fp in glob.glob(os.path.join(REPO, "logs", slot, "games", "*.json")):
            try:
                with open(fp, encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                continue
            if d.get("game_family") != "persuasion":
                continue
            cfg = d.get("config") or {}
            me = d.get("your_player")
            if cfg.get(f"{me}_role") != "buyer":
                continue
            hist = [h for h in (d.get("history") or []) if isinstance(h, dict)]
            if not hist:
                continue
            price = float(cfg.get("product_price") or 0)
            v = float(cfg.get("v") or 0)
            if price <= 0 or v <= 0:
                continue
            games.append({
                "game_id": d.get("game_id") or os.path.basename(fp),
                "mode": cfg.get("seller_message_type") or "text",
                "p": float(cfg.get("p") or 0.5),
                "v": v, "u": float(cfg.get("u") or 0.0), "price": price,
                "total": int(cfg.get("total_rounds") or len(hist)),
                "name": (d.get("opponent") or {}).get("name") or "hidden",
                "rounds": [{
                    "round": int(h.get("round") or i + 1),
                    "seller_message": h.get("seller_message"),
                    "rec": _recommended(h),
                    "quality": (str(h.get("quality", "")).lower()
                                if h.get("bought") and str(h.get("quality", "")).lower()
                                in ("high", "low") else None),
                    "hist_bought": bool(h.get("bought")),
                } for i, h in enumerate(hist)],
            })
    games.sort(key=lambda g: g["game_id"])
    return games[:limit] if limit else games


def _impute_table():
    try:
        with open(IMPUTE_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("table") or {}
    except (OSError, ValueError):
        return {}


def p_high_for(table: dict, g: dict, rnd: dict) -> float:
    r = "yes" if rnd["rec"] else "no"
    pb = pbin(g["p"])
    t = tercile(rnd["round"], g["total"])
    for key in (f"{g['name']}|{g['mode']}|{pb}|{r}|{t}",
                f"{g['name']}|{g['mode']}|{pb}|{r}",
                f"{g['mode']}|{pb}|{r}|{t}",
                f"{g['mode']}|{pb}|{r}"):
        cell = table.get(key)
        if cell:
            return (cell["high"] + ALPHA * g["p"]) / (cell["n"] + ALPHA)
    return g["p"]


def imputed_qualities(table: dict, g: dict, draw: int, seed: int) -> list[str]:
    """Quality per round: logged where observed, drawn where not.

    The RNG is keyed on (game, draw) only -- every candidate sees identical
    quality realisations, which is what makes the comparisons paired.
    """
    key = hashlib.sha256(f"{g['game_id']}|{draw}|{seed}".encode()).digest()
    rng = random.Random(key)
    out = []
    for rnd in g["rounds"]:
        if rnd["quality"] is not None:
            out.append(rnd["quality"])
        else:
            out.append("high" if rng.random() < p_high_for(table, g, rnd) else "low")
    return out


def replay(decide, g: dict, qualities: list[str]) -> dict:
    """One candidate, one game, one quality draw -> payoff and buy pattern."""
    sim_history: list[dict] = []
    payoff = bought = junk = 0.0
    for rnd, q in zip(g["rounds"], qualities):
        state = {
            "product_price": g["price"], "p": g["p"], "v": g["v"], "u": g["u"],
            "total_rounds": g["total"], "round": rnd["round"],
            "seller_message": rnd["seller_message"],
            "seller_message_type": g["mode"],
            "history": sim_history,
        }
        act = decide({"game_state": state, "your_player": "player_2",
                      "valid_actions": {"type": "buyer_decision"}}, _CFG)
        buy = str(act.get("decision", "")).lower() == "yes"
        entry = {"round": rnd["round"], "seller_message": rnd["seller_message"],
                 "bought": buy}
        if buy:
            bought += 1
            payoff += (g["v"] if q == "high" else g["u"]) - g["price"]
            junk += q == "low"
            entry["quality"] = q            # revealed only on purchase
        sim_history.append(entry)
    return {"payoff": payoff, "bought": bought, "junk": junk}


def historical_result(g: dict, qualities: list[str]) -> dict:
    payoff = bought = junk = 0.0
    for rnd, q in zip(g["rounds"], qualities):
        if rnd["hist_bought"]:
            bought += 1
            payoff += (g["v"] if q == "high" else g["u"]) - g["price"]
            junk += q == "low"
    return {"payoff": payoff, "bought": bought, "junk": junk}


def cell_of(g: dict) -> str:
    ratio = min(RATIO_BINS, key=lambda r: abs(r - g["v"] / g["price"]))
    return f"{g['mode']}|{pbin(g['p'])}|r{ratio}"


def boot_ci(deltas_by_game: list[float], B: int = 3000, seed: int = 7):
    if not deltas_by_game:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    n = len(deltas_by_game)
    means = []
    for _ in range(B):
        means.append(sum(deltas_by_game[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return (sum(deltas_by_game) / n,
            means[int(0.025 * B)], means[int(0.975 * B)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", help="JSON file: {name: {FLAG: val, ...}}")
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--json", dest="json_out", default=None)
    args = ap.parse_args()

    with open(args.candidates, encoding="utf-8") as fh:
        candidates = json.load(fh)
    arms = {"v1": {}}
    arms.update({k: v for k, v in candidates.items() if k != "v1"})

    games = load_games(args.limit)
    table = _impute_table()
    print(f"replaying {len(games):,} buyer-seat games x {args.draws} draws "
          f"x {len(arms)} arms (+historical anchor)")

    draws = {(g["game_id"], k): imputed_qualities(table, g, k, args.seed)
             for g in games for k in range(args.draws)}

    from glee_agent.strategies import persuasion
    per_arm: dict[str, dict] = {}
    for arm_name, flags in arms.items():
        _set_flags(flags)
        rows = {}
        for g in games:
            acc = {"payoff": 0.0, "bought": 0.0, "junk": 0.0}
            for k in range(args.draws):
                r = replay(persuasion.decide, g, draws[(g["game_id"], k)])
                for f in acc:
                    acc[f] += r[f] / args.draws
            rows[g["game_id"]] = acc
        per_arm[arm_name] = rows
    _set_flags({})

    hist_rows = {}
    for g in games:
        acc = {"payoff": 0.0, "bought": 0.0, "junk": 0.0}
        for k in range(args.draws):
            r = historical_result(g, draws[(g["game_id"], k)])
            for f in acc:
                acc[f] += r[f] / args.draws
        hist_rows[g["game_id"]] = acc
    per_arm["historical"] = hist_rows

    by_cell = defaultdict(list)
    for g in games:
        by_cell[cell_of(g)].append(g)

    report = {"games": len(games), "draws": args.draws, "arms": {}}
    print(f"\n{'arm':16s}{'pay/price':>10s}{'loss%':>7s}{'neg%':>7s}"
          f"{'d(pay/price) vs v1 [95% CI]':>32s}")
    for arm_name in list(arms) + ["historical"]:
        rows = per_arm[arm_name]
        norm = [rows[g["game_id"]]["payoff"] / g["price"] for g in games]
        loss = sum(1 for g in games if rows[g["game_id"]]["payoff"] <= 1e-9)
        neg = sum(1 for g in games if rows[g["game_id"]]["payoff"] < -1e-9)
        deltas = [(rows[g["game_id"]]["payoff"]
                   - per_arm["v1"][g["game_id"]]["payoff"]) / g["price"]
                  for g in games]
        mean_d, lo, hi = boot_ci(deltas)
        marker = " *" if (lo > 0 or hi < 0) and arm_name != "v1" else ""
        print(f"{arm_name:16s}{sum(norm)/len(norm):>10.3f}"
              f"{loss/len(games):>7.1%}{neg/len(games):>7.1%}"
              f"{mean_d:>+14.3f} [{lo:+.3f},{hi:+.3f}]{marker}")
        cells = {}
        for cell, gs in sorted(by_cell.items()):
            cd = [(rows[g["game_id"]]["payoff"]
                   - per_arm["v1"][g["game_id"]]["payoff"]) / g["price"]
                  for g in gs]
            cm, cl, ch = boot_ci(cd, B=1500)
            cells[cell] = {"n": len(gs), "delta": round(cm, 4),
                           "ci": [round(cl, 4), round(ch, 4)],
                           "pay_over_price": round(
                               sum(rows[g["game_id"]]["payoff"] / g["price"]
                                   for g in gs) / len(gs), 4)}
        report["arms"][arm_name] = {
            "flags": arms.get(arm_name, {}),
            "pay_over_price": round(sum(norm) / len(norm), 4),
            "loss_rate": round(loss / len(games), 4),
            "neg_rate": round(neg / len(games), 4),
            "delta_vs_v1": round(mean_d, 4), "ci": [round(lo, 4), round(hi, 4)],
            "cells": cells,
        }

    best = max((a for a in report["arms"] if a not in ("v1", "historical")),
               key=lambda a: report["arms"][a]["delta_vs_v1"], default=None)
    if best:
        b = report["arms"][best]
        print(f"\nbest arm: {best}  delta {b['delta_vs_v1']:+.3f} "
              f"[{b['ci'][0]:+.3f},{b['ci'][1]:+.3f}] pay/price "
              f"({'CI clear' if b['ci'][0] > 0 else 'CI NOT clear'})")
        print("worst cells for best arm:")
        for cell, c in sorted(b["cells"].items(), key=lambda kv: kv[1]["delta"])[:4]:
            print(f"  {cell:22s} n={c['n']:<5d} d={c['delta']:+.3f} "
                  f"[{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}]")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
        print(f"report -> {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
