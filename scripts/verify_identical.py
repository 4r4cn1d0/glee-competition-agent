#!/usr/bin/env python3
"""Prove the fleet is a carbon copy of itself, or name exactly what differs.

Why this exists. On 2026-08-22 the fleet was reset so every agent runs one
configuration, to measure the only thing four agents can measure when they are
identical: the cross-agent NOISE FLOOR. That number is the floor under every
future claim -- a change smaller than it is unmeasurable no matter how long we
watch. The measurement is worthless if the agents are not actually identical,
and "identical" has four independent surfaces, three of which are invisible in
arms.json:

  1. arms.json      -- the live flag overlay, polled every 3s.
  2. control.json   -- per-slot LAUNCH overrides: policy, families, llm. These
                       apply at the next rotation, not immediately.
  3. the PROBE      -- Config.from_env() builds the config and then make_probe()
                       calls replace() on it, so the probe OVERRIDES the env for
                       barg_spe_weight, barg_uncapped_horizon, nego_seller_anchor,
                       nego_buyer_anchor, pers_lie_shading, pers_honest_rounds.
                       Identical arms entries still leave different agents unless
                       every slot runs the same policy. _champion is the only
                       pass-through profile, which is why the fleet is mapped to
                       it. This surface is why Test 2 ran a 4.0 seller anchor that
                       no flag of its own asked for.
  4. the PROCESS    -- what is running RIGHT NOW. A slot whose policy changed but
                       which has not rotated yet is still playing the old strategy.
                       This is the surface that lies most convincingly: the config
                       looks right and the behaviour is not.

Usage:
    python scripts/verify_identical.py            # config surfaces only
    python scripts/verify_identical.py --behaviour  # also compare live play
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

NAMES = {"champion": "Test 1", "hardliner": "Test 2", "conceder": "Test 3",
         "randomized": "Test 4", "composite": "Agent 5"}

#: The six knobs a probe can silently override. Listed so a failure names the
#: actual field rather than saying "the probe differs".
PROBE_KNOBS = ("barg_spe_weight", "barg_uncapped_horizon", "nego_seller_anchor",
               "nego_buyer_anchor", "pers_lie_shading", "pers_honest_rounds")


def _read(path, default):
    try:
        with open(os.path.join(REPO, path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def check_arms(slots):
    arms = _read("arms.json", {})
    sets = {s: json.dumps(dict(sorted((arms.get(s) or {}).items()))) for s in slots}
    uniq = set(sets.values())
    if len(uniq) == 1:
        n = len(json.loads(next(iter(uniq))))
        return True, f"all {len(slots)} slots carry the same {n} flags"
    # name the offending keys rather than dumping both blobs
    keys = set()
    for s in slots:
        keys |= set((arms.get(s) or {}).keys())
    bad = [k for k in sorted(keys)
           if len({(arms.get(s) or {}).get(k) for s in slots}) > 1]
    return False, f"{len(uniq)} distinct flag sets; disagreeing keys: {bad}"


def check_control(slots):
    ctl = _read("control.json", {})
    problems = []
    for key in ("policy", "families", "llm"):
        table = ctl.get(key) or {}
        vals = {s: table.get(s) for s in slots}
        if len(set(vals.values())) > 1:
            problems.append(f"{key}={vals}")
    if problems:
        return False, "; ".join(problems)
    pol = (ctl.get("policy") or {}).get(slots[0])
    note = f"policy/families/llm identical across slots (policy={pol!r})"
    if pol != "champion":
        return False, (note + " -- but the shared policy is NOT 'champion', the "
                       "only pass-through profile, so it overrides the six env knobs "
                       f"{PROBE_KNOBS}")
    return True, note


def check_processes(slots):
    out = subprocess.run(["ps", "-eo", "command="], capture_output=True, text=True).stdout
    live = {}
    for line in out.splitlines():
        if "run_agent.py" not in line or "--log-dir" not in line:
            continue
        m = re.search(r"--log-dir\s+logs/(\S+)", line)
        p = re.search(r"--probe\s+(\S+)", line)
        if not m or not p:
            continue
        # everything except the slot's own identity must match
        rest = re.sub(r"--log-dir\s+logs/\S+", "", line)
        rest = re.sub(r"^.*run_agent\.py", "", rest).strip()
        live[m.group(1)] = (p.group(1), rest)
    if not live:
        return False, "no agent processes found"
    probes = {s: v[0] for s, v in live.items()}
    args = {s: v[1] for s, v in live.items()}
    if len(set(probes.values())) > 1:
        stale = {NAMES.get(s, s): p for s, p in probes.items()}
        return False, (f"RUNNING probes differ: {stale} -- slots whose policy changed "
                       "have not rotated yet and are still playing the OLD strategy")
    if len(set(args.values())) > 1:
        return False, f"launch args differ: {args}"
    missing = [NAMES.get(s, s) for s in slots if s not in live]
    tail = f" (not running: {missing})" if missing else ""
    return True, f"{len(live)} processes, all --probe {next(iter(probes.values()))}{tail}"


def check_behaviour(slots, hours):
    """Do the agents actually PLAY the same? Config can be right and play wrong."""
    from sim.percentile import percentile          # noqa: E402
    cut = time.time() - hours * 3600
    per = defaultdict(lambda: defaultdict(list))
    for slot in slots:
        path = os.path.join(REPO, "logs", slot, "results.jsonl")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("ts", 0) < cut:
                    continue
                fin = rec.get("final") or {}
                fam, seat = fin.get("game_family"), fin.get("your_player")
                res = fin.get("result") or {}
                pay = res.get(f"{seat}_payoff", res.get("your_payoff"))
                if not fam or not seat or not isinstance(pay, (int, float)):
                    continue
                p = percentile(fam, dict(fin.get("game_state") or {}), seat, float(pay))
                if p is not None:
                    per[fam][slot].append(p)
    print(f"\n  live play, last {hours:g}h -- the SPREAD here is the noise floor")
    for fam in sorted(per):
        row = []
        for slot in slots:
            v = per[fam].get(slot) or []
            row.append(f"{NAMES.get(slot,slot)} {sum(v)/len(v):.4f} (n={len(v)})"
                       if len(v) >= 30 else f"{NAMES.get(slot,slot)} --")
        means = [sum(v) / len(v) for v in per[fam].values() if len(v) >= 30]
        spread = (max(means) - min(means)) if len(means) > 1 else 0.0
        print(f"    {fam:12s} " + "  ".join(row))
        print(f"    {'':12s} spread {spread:.4f} percentile = {8000*spread:.0f} rating-equivalent")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--behaviour", action="store_true",
                    help="also compare realised percentile per agent")
    ap.add_argument("--hours", type=float, default=6.0)
    args = ap.parse_args()

    arms = _read("arms.json", {})
    slots = sorted(s for s, v in arms.items() if isinstance(v, dict))
    print(f"verifying {len(slots)} slots: {', '.join(NAMES.get(s, s) for s in slots)}\n")

    ok = True
    for label, fn in (("arms.json  (live, 3s poll)", check_arms),
                      ("control.json (next launch)", check_control),
                      ("running processes  (NOW)", check_processes)):
        good, msg = fn(slots)
        ok &= good
        print(f"  [{'OK ' if good else 'BAD'}] {label}: {msg}")

    if args.behaviour:
        check_behaviour(slots, args.hours)

    print()
    if ok:
        print("CARBON COPY: every configuration surface agrees.")
    else:
        print("NOT IDENTICAL YET. A 'BAD' on running processes alone usually just")
        print("means a rotation is pending -- policy is read at launch, so it")
        print("resolves at the next shift boundary without touching any process.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
