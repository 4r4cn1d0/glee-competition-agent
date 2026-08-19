#!/usr/bin/env python
"""Deep statistics across the whole fleet.

    python scripts/fleet_stats.py --fetch     # pull outcomes, then analyse
    python scripts/fleet_stats.py             # analyse what is already stored

A caution the numbers themselves cannot carry: GLEE does NOT score win/loss.
A payoff becomes a percentile against the field on the SAME configuration in the
SAME seat. So "beat the opponent" is a diagnostic, not the objective — you can
lose every head-to-head and still rate well by losing less than the field does
on that configuration. The metric that genuinely tracks rating is the no-deal
rate, because a no-deal pays zero and zero is the bottom of every distribution.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLEET = [("GLEE_KEY_TEST1", "champion"), ("GLEE_KEY_TEST2", "hardliner"),
         ("GLEE_KEY_TEST3", "conceder"), ("GLEE_KEY_TEST4", "randomized"),
         ("GLEE_KEY_TEST5", "composite")]


def load_env() -> None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def game_ids(probe: str) -> list[str]:
    path = os.path.join(REPO, "logs", probe, "turns.jsonl")
    seen = []
    if not os.path.exists(path):
        return seen
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                gid = json.loads(line).get("game_id")
            except json.JSONDecodeError:
                continue
            if gid and gid not in seen:
                seen.append(gid)
    return seen


def fetch(probe: str, key: str, rate: float) -> int:
    """Pull final states, gently — the agent is still playing and shares the
    60 req/min budget with its own game loop."""
    from glee_sdk import GleeAPIError, GleeClient
    from glee_agent.gamelog import GameLog
    log = GameLog(os.path.join(REPO, "logs", probe))
    have = {f[:-5] for f in os.listdir(log.games_dir) if f.endswith(".json")}
    todo = [g for g in game_ids(probe) if g not in have]
    client = GleeClient(api_key=key)
    written = 0
    for gid in todo:
        try:
            state = client.game_state(gid)
        except GleeAPIError as exc:
            if exc.status_code == 429:
                time.sleep(5); continue
            continue
        except Exception:
            continue
        if state.get("status") == "active":
            continue                      # still in play; no outcome yet
        log.write_game_record(gid, state)
        written += 1
        time.sleep(rate)
    return written


def load(probe: str) -> list[dict]:
    d = os.path.join(REPO, "logs", probe, "games")
    out = []
    if not os.path.isdir(d):
        return out
    for name in os.listdir(d):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, name), encoding="utf-8") as handle:
                out.append(json.load(handle))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:5.1f}%" if d else "    -"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--rate", type=float, default=0.9, help="seconds between API calls")
    args = ap.parse_args()
    load_env()

    if args.fetch:
        for env_key, probe in FLEET:
            key = os.environ.get(env_key)
            if key:
                print(f"  fetching {probe}...", flush=True)
                print(f"    +{fetch(probe, key, args.rate)} records")

    data = {probe: load(probe) for _, probe in FLEET}
    total = sum(len(v) for v in data.values())
    if not total:
        print("No completed games stored yet. Run with --fetch.")
        return 0
    print(f"\n{total} completed games across the fleet\n")

    # ---------- headline table ----------
    print("=" * 100)
    print("PER AGENT x FAMILY".center(100))
    print("=" * 100)
    hdr = (f"{'agent':11s} {'family':12s} {'games':>5s} {'no-deal':>8s} {'zero-pay':>8s} "
           f"{'beat opp':>8s} {'our share':>9s} {'mean payoff':>13s} {'med round':>9s}")
    print(hdr); print("-" * len(hdr))
    for _, probe in FLEET:
        rows = collections.defaultdict(list)
        for g in data[probe]:
            rows[g.get("game_family")].append(g)
        for fam in ("bargaining", "negotiation", "persuasion"):
            gs = rows.get(fam) or []
            if not gs:
                continue
            n = len(gs)
            nd = sum(1 for g in gs if (g.get("result") or {}).get("outcome") == "no_deal"
                     or g.get("status") == "no_deal")
            mine = [g.get("our_payoff") for g in gs if isinstance(g.get("our_payoff"), (int, float))]
            theirs = [g.get("opponent_payoff") for g in gs
                      if isinstance(g.get("opponent_payoff"), (int, float))]
            zero = sum(1 for v in mine if v == 0)
            beat = sum(1 for g in gs
                       if isinstance(g.get("our_payoff"), (int, float))
                       and isinstance(g.get("opponent_payoff"), (int, float))
                       and g["our_payoff"] > g["opponent_payoff"])
            shares = []
            for g in gs:
                a, b = g.get("our_payoff"), g.get("opponent_payoff")
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and (a + b) > 0:
                    shares.append(a / (a + b))
            rounds = [g.get("rounds_played", 0) for g in gs]
            print(f"{probe:11s} {fam:12s} {n:5d} {pct(nd, n):>8s} {pct(zero, len(mine)):>8s} "
                  f"{pct(beat, n):>8s} "
                  f"{(f'{statistics.mean(shares):.0%}' if shares else '-'):>9s} "
                  f"{(statistics.mean(mine) if mine else 0):13,.1f} "
                  f"{(statistics.median(rounds) if rounds else 0):9.0f}")

    # ---------- the diagnostic that matters: capped vs uncapped ----------
    print()
    print("=" * 100)
    print("HORIZON: capped games vs UNCAPPED  (the freeze bug lived here)".center(100))
    print("=" * 100)
    print(f"{'agent':11s} {'family':12s} {'horizon':10s} {'games':>5s} {'no-deal':>8s} {'our share':>9s}")
    print("-" * 60)
    for _, probe in FLEET:
        for fam in ("bargaining", "negotiation"):
            for label, want in (("capped", True), ("UNCAPPED", False)):
                gs = [g for g in data[probe]
                      if g.get("game_family") == fam
                      and bool((g.get("config") or {}).get("horizon_known")) is want]
                if not gs:
                    continue
                nd = sum(1 for g in gs if (g.get("result") or {}).get("outcome") == "no_deal"
                         or g.get("status") == "no_deal")
                shares = []
                for g in gs:
                    a, b = g.get("our_payoff"), g.get("opponent_payoff")
                    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and (a + b) > 0:
                        shares.append(a / (a + b))
                print(f"{probe:11s} {fam:12s} {label:10s} {len(gs):5d} {pct(nd, len(gs)):>8s} "
                      f"{(f'{statistics.mean(shares):.0%}' if shares else '-'):>9s}")

    # ---------- who are we actually playing ----------
    print()
    print("=" * 100)
    print("OPPONENTS FACED".center(100))
    print("=" * 100)
    opp = collections.Counter()
    opp_res = collections.defaultdict(lambda: [0, 0])
    for _, probe in FLEET:
        for g in data[probe]:
            o = g.get("opponent") or {}
            name = o.get("name") or f"<{o.get('type', '?')}>"
            opp[name] += 1
            a, b = g.get("our_payoff"), g.get("opponent_payoff")
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                opp_res[name][0] += 1
                opp_res[name][1] += 1 if a > b else 0
    for name, n in opp.most_common(14):
        tot, won = opp_res[name]
        print(f"  {name:28s} {n:4d} games   beat them {pct(won, tot)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
