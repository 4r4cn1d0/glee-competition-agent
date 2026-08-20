#!/usr/bin/env python3
"""Sweep candidate strategies through the offline arena and rank the survivors.

Stage A varies one knob at a time around the live control; stage B re-runs the
stage-A winners combined, at triple the sample and a fresh seed. The fresh seed
matters: with ~16 candidates at 95% CIs, one spurious "winner" per sweep is
expected, so nothing is promoted on a stage-A result alone.

Only knobs that actually flow through the composite policy are swept. The probe
transform overrides nego_seller_anchor, nego_buyer_anchor, barg_spe_weight and
barg_uncapped_horizon AFTER Config.from_env, so their env vars are inert here --
sweeping them would silently compare the control with itself.

Rankings are family-appropriate: negotiation candidates rank by zero-rate
improvement first (51% of live outcomes sit on the $0 atom; percentile pays for
escaping it) with payoff as the tiebreak; bargaining ranks by payoff share (its
zero rate is ~0 everywhere).

Results land in logs/sweeps/ as JSON, one file per run, so sweeps accumulate.
"""
from __future__ import annotations

import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from sim.field_data import Field                     # noqa: E402
from sim.replay_eval import (_boot_ci, _draw_games,  # noqa: E402
                             _play_arm, DEFAULT_CONTROL)

STAGE_A_GAMES = 2400
STAGE_B_GAMES = 7200

#: name -> flag overrides applied on top of the control.
CANDIDATES = {
    # concession endpoint (the margin/frequency trade)
    "margin=0.02":        {"GLEE_NEGO_MIN_MARGIN": "0.02"},
    "margin=0.08":        {"GLEE_NEGO_MIN_MARGIN": "0.08"},
    "margin=0.12":        {"GLEE_NEGO_MIN_MARGIN": "0.12"},
    # curve pricing and its frequency/margin exponent
    "curve g=0.5":        {"GLEE_NEGO_CURVE_PRICING": "1"},
    "curve g=0.25":       {"GLEE_NEGO_CURVE_PRICING": "1", "GLEE_NEGO_MARGIN_WEIGHT": "0.25"},
    "curve g=1.0":        {"GLEE_NEGO_CURVE_PRICING": "1", "GLEE_NEGO_MARGIN_WEIGHT": "1.0"},
    # planning clock and continuation optimism
    "horizon=6":          {"GLEE_NEGO_HORIZON": "6"},
    "horizon=20":         {"GLEE_NEGO_HORIZON": "20"},
    "deal_odds=0.5":      {"GLEE_NEGO_DEAL_ODDS": "0.5"},
    "deal_odds=0.8":      {"GLEE_NEGO_DEAL_ODDS": "0.8"},
    # the dormant gates, re-tested against the cloned field
    "cont_accept":        {"GLEE_NEGO_CONTINUATION_ACCEPT": "1"},
    "horizon_v2":         {"GLEE_NEGO_HORIZON_V2": "1"},
    "split_cand":         {"GLEE_NEGO_SPLIT_CANDIDATE": "1"},
    # bargaining floors
    "barg_floor=0.55":    {"GLEE_BARG_OFFER_FLOOR": "0.55"},
    "barg_floor=0.60":    {"GLEE_BARG_OFFER_FLOOR": "0.60"},
    "opp_floor=0.30":     {"GLEE_BARG_OPPONENT_FLOOR": "0.30"},
    "opp_floor=0.45":     {"GLEE_BARG_OPPONENT_FLOOR": "0.45"},
}


def evaluate(field, draws, control_rows, flags, families):
    rows = _play_arm(field, draws, flags)
    out = {}
    for fam in families:
        pairs = [(a, b) for a, b in zip(control_rows, rows) if a["family"] == fam]
        if not pairs:
            continue
        n = len(pairs)
        d_norm = [b["norm"] - a["norm"] for a, b in pairs]
        d_zero = [b["zero"] - a["zero"] for a, b in pairs]
        d_close = [b["closed"] - a["closed"] for a, b in pairs]
        out[fam] = {
            "n": n,
            "payoff": sum(d_norm) / n, "payoff_ci": _boot_ci(d_norm),
            "zero": sum(d_zero) / n, "zero_ci": _boot_ci(d_zero),
            "close": sum(d_close) / n, "close_ci": _boot_ci(d_close),
        }
    return out


def _sig(delta, ci, good_negative=False):
    """'++'/'--' when the CI clears zero, '+'/'-' when only the point does."""
    if ci is None:
        return "?"
    lo, hi = ci
    better = delta < 0 if good_negative else delta > 0
    clear = hi < 0 if good_negative else lo > 0
    worse_clear = lo > 0 if good_negative else hi < 0
    if clear:
        return "++"
    if worse_clear:
        return "--"
    return "+" if better else "-"


def report(results, fam, key, good_negative=False):
    print(f"\n  {fam.upper()} — ranked by "
          f"{'zero-rate reduction' if good_negative else 'payoff gain'}")
    print(f"  {'candidate':16s}{'payoff Δ':>12s}{'zero Δ':>10s}{'close Δ':>10s}  verdict")
    rows = [(name, r[fam]) for name, r in results.items() if fam in r]
    rows.sort(key=lambda kv: kv[1][key], reverse=not good_negative)
    for name, r in rows:
        print(f"  {name:16s}{r['payoff']:>+12.4f}{r['zero']:>+10.3f}{r['close']:>+10.3f}"
              f"   payoff{_sig(r['payoff'], r['payoff_ci'])}"
              f" zero{_sig(r['zero'], r['zero_ci'], good_negative=True)}")
    return rows


def main() -> int:
    global CANDIDATES
    if len(sys.argv) > 1:
        # a JSON file of {name: {FLAG: value, ...}} replaces the built-in set,
        # so each round of the standing loop can bring its own candidates
        with open(sys.argv[1], encoding="utf-8") as fh:
            CANDIDATES = json.load(fh)
    field = Field()
    families = ["bargaining", "negotiation"]
    os.makedirs(os.path.join(REPO, "logs", "sweeps"), exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")

    print(f"STAGE A: {len(CANDIDATES)} candidates x {STAGE_A_GAMES} paired games")
    draws = _draw_games(field, families, STAGE_A_GAMES, seed=101)
    control_rows = _play_arm(field, draws, DEFAULT_CONTROL)
    results = {}
    for name, overrides in CANDIDATES.items():
        flags = dict(DEFAULT_CONTROL, **overrides)
        t0 = time.time()
        results[name] = evaluate(field, draws, control_rows, flags, families)
        print(f"  {name:16s} done in {time.time()-t0:5.1f}s")
    nego = report(results, "negotiation", "zero", good_negative=True)
    barg = report(results, "bargaining", "payoff")

    # STAGE B: combine every negotiation knob whose zero-rate CI cleared zero
    # with every bargaining knob whose payoff CI cleared zero; confirm on a
    # FRESH seed at 3x the games.
    nego_win = [n for n, r in nego
                if r["zero_ci"] and r["zero_ci"][1] < 0]
    barg_win = [n for n, r in barg
                if r["payoff_ci"] and r["payoff_ci"][0] > 0]
    print(f"\n  stage-A survivors: nego={nego_win or 'none'}  barg={barg_win or 'none'}")
    combo = dict(DEFAULT_CONTROL)
    for name in nego_win + barg_win:
        combo.update(CANDIDATES[name])
    out = {"_stamp": stamp, "stage_a": results, "survivors": nego_win + barg_win}
    if nego_win or barg_win:
        print(f"\nSTAGE B: combined survivors at {STAGE_B_GAMES} games, fresh seed")
        print(f"  combo: {json.dumps({k: v for k, v in combo.items() if DEFAULT_CONTROL.get(k) != v}, sort_keys=True)}")
        draws_b = _draw_games(field, families, STAGE_B_GAMES, seed=202)
        control_b = _play_arm(field, draws_b, DEFAULT_CONTROL)
        confirmed = evaluate(field, draws_b, control_b, combo, families)
        out["stage_b"] = {"combo": combo, "result": confirmed}
        for fam in families:
            r = confirmed.get(fam)
            if not r:
                continue
            print(f"  {fam:12s} payoff {r['payoff']:+.4f} {r['payoff_ci']}  "
                  f"zero {r['zero']:+.3f} {r['zero_ci']}  close {r['close']:+.3f}")
    path = os.path.join(REPO, "logs", "sweeps", f"sweep_{stamp}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(f"\nsaved -> {os.path.relpath(path, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
