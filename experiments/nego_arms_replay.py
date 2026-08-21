"""Intake, balance and read-out for the negotiation message arms.

Two modes, and the first one is the reason this file exists before any live
record does:

``intake``
    Replays every logged negotiation turn through the randomiser exactly as the
    live agent would run it, WITHOUT touching a number. It answers the questions
    that decide whether the experiment can be powered at all: how many turns are
    design points, which arms are defined on them, what the realised message
    lengths look like per arm, and — the one that matters — whether the assigned
    arm is uncorrelated with the price we were going to name anyway. The last is
    a permutation test, and it is run against ``block_key`` because the eligible
    pool is state-dependent and is therefore a pre-treatment confounder.

``report``
    Once the flag has been live, joins each ``plan.msg_arm`` record in
    turns.jsonl to what the opponent did next, and reports acceptance by arm
    against the N1 reference with a block-weighted estimate and a bootstrap CI.
    A0-style silence is contrasted separately: a framing measured against
    silence is confounded with the mere presence of text.

Usage (logs are gitignored, so point it at the fleet's directory):

    .venv/bin/python -m experiments.nego_arms_replay intake \\
        --logs "/Users/you/GLEE Competition/logs"
    .venv/bin/python -m experiments.nego_arms_replay report --logs .../logs

Stdlib only: numpy and scipy are not in the fleet's venv and the analysis of a
live experiment is not the place to add a dependency.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from glee_agent import messages, nego_arms          # noqa: E402


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def turn_records(logs: str):
    """Every logged turn, in file order, from every agent's directory."""
    paths = sorted(glob.glob(os.path.join(logs, "*", "turns.jsonl")))
    if not paths:
        paths = sorted(glob.glob(os.path.join(logs, "turns.jsonl")))
    for path in paths:
        probe = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                record["_probe"] = probe
                yield record


def as_game(record: dict) -> dict:
    """Rebuild the ``game`` dict the strategy saw from a logged turn."""
    return {
        "game_id": record.get("game_id"),
        "game_family": record.get("game_family"),
        "your_player": record.get("your_player"),
        "phase": record.get("phase"),
        "game_state": record.get("state") or {},
        "opponent": record.get("opponent") or {},
        "valid_actions": {"type": record.get("action_type")},
    }


# --------------------------------------------------------------------------
# intake
# --------------------------------------------------------------------------

def intake(logs: str, seed_note: str = "") -> int:
    nego_arms.reset()
    os.environ[nego_arms.FLAG] = "1"
    os.environ.pop("GLEE_PROBE", None)
    from glee_agent import runtime_flags
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)

    total = eligible = 0
    pools: dict[tuple, int] = {}
    arms: dict[str, int] = {}
    claims: dict[str, int] = {}
    lengths: dict[str, list] = {}
    strata: dict[str, int] = {}
    rows = []                       # (block_key, arm, normalised price)

    for record in turn_records(logs):
        if record.get("game_family") != "negotiation":
            continue
        plan = record.get("plan")
        action = dict(record.get("action") or {})
        if not isinstance(plan, dict) or not plan:
            continue
        game = as_game(record)
        total += 1
        if not nego_arms.carries_offer(game, action):
            continue
        pool = nego_arms.arm_pool(game, action, plan)
        pools[pool] = pools.get(pool, 0) + 1
        if len(pool) < nego_arms.MIN_POOL:
            continue
        drawn = nego_arms.assign(game, action, plan)
        if drawn is None:
            continue
        eligible += 1
        arm = drawn["arm"]
        arms[arm] = arms.get(arm, 0) + 1
        strata[drawn["stratum_id"]] = strata.get(drawn["stratum_id"], 0) + 1
        composed = messages.negotiation_arm_message(arm, game, action, plan)
        if composed.get("text"):
            lengths.setdefault(arm, []).append(len(composed["text"]))
            claims[str(composed.get("claim_id"))] = \
                claims.get(str(composed.get("claim_id")), 0) + 1
        value = float(plan.get("my_value") or 0.0)
        price = float(action.get("product_price") or 0.0)
        if value > 0:
            rows.append((drawn["block_key"], arm, price / value))

    print(f"negotiation turns with a plan       : {total:,}")
    print(f"design points (price + open channel): "
          f"{sum(pools.values()):,}")
    print(f"assigned (pool >= {nego_arms.MIN_POOL})              : {eligible:,}\n")

    print("arm allocation")
    for arm in nego_arms.ARMS:
        n = arms.get(arm, 0)
        share = n / eligible if eligible else 0.0
        print(f"  {arm}  {n:>7,}  {share:6.1%}   {messages.NEGO_ARM_SEMANTICS[arm][:52]}")
    print("\npools (which arms were defined together)")
    for pool, n in sorted(pools.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {','.join(pool) or '(none)':<20} {n:>7,}")
    print("\nclaims that fired")
    for claim, n in sorted(claims.items(), key=lambda kv: -kv[1]):
        print(f"  {claim:<24} {n:>7,}")
    print("\nrealised message length by arm (the balance table that matters: a "
          "\n  per-arm length difference is a treatment the opponent can see)")
    for arm in nego_arms.ARMS:
        seen = lengths.get(arm) or []
        if not seen:
            print(f"  {arm}  (silent)")
            continue
        seen_sorted = sorted(seen)
        print(f"  {arm}  n={len(seen):>6,}  mean={sum(seen)/len(seen):6.1f}  "
              f"median={seen_sorted[len(seen_sorted)//2]:>4}  "
              f"min={seen_sorted[0]:>4}  max={seen_sorted[-1]:>4}")
    print(f"\nstrata occupied: {len(strata)}  "
          f"(largest {max(strata.values()) if strata else 0:,} turns)")

    print("\nbalance: is the arm correlated with the price we were going to name?")
    for key_name, keyfn in (("block_key", lambda r: r[0]),
                            ("stratum only", lambda r: r[0].split("||")[0])):
        stat, null, p = permutation_balance(rows, keyfn)
        print(f"  by {key_name:<13} imbalance {stat:.4f} vs null {null:.4f}, "
              f"p = {p:.3f}")
    print("\n  (the price is fixed BEFORE the draw, so any correlation here is "
          "\n   evidence of a leak in the randomiser, not an effect.)")
    return 0


def permutation_balance(rows, keyfn, draws: int = 400, seed: int = 11):
    """Mean |per-arm block-centred price| against its permutation null.

    Prices are centred within the grouping key, so the statistic asks only
    whether an arm systematically drew richer or poorer states than its
    block-mates — which, since the price is final before the arm is drawn, can
    only happen if the draw is leaking.
    """
    if not rows:
        return 0.0, 0.0, 1.0
    groups: dict = {}
    for row in rows:
        groups.setdefault(keyfn(row), []).append(row)

    def statistic(assignment):
        sums: dict = {}
        counts: dict = {}
        for key, members in groups.items():
            values = [m[2] for m in members]
            mean = sum(values) / len(values)
            for member, arm in zip(members, assignment[key]):
                sums[arm] = sums.get(arm, 0.0) + (member[2] - mean)
                counts[arm] = counts.get(arm, 0) + 1
        return (sum(abs(sums[a]) / counts[a] for a in sums) / len(sums)) if sums else 0.0

    observed = {key: [m[1] for m in members] for key, members in groups.items()}
    stat = statistic(observed)
    rng = random.Random(seed)
    null = []
    for _ in range(draws):
        shuffled = {}
        for key, members in groups.items():
            labels = [m[1] for m in members]
            rng.shuffle(labels)
            shuffled[key] = labels
        null.append(statistic(shuffled))
    mean_null = sum(null) / len(null)
    p = sum(1 for value in null if value >= stat) / len(null)
    return stat, mean_null, p


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def report(logs: str) -> int:
    """Acceptance by arm, once the flag has been live.

    The outcome is turn-level and is read off the game's own record: did the
    opponent's next move accept the price this message was attached to. That is
    the estimand the per-turn randomisation identifies; a game-level read would
    be an intention-to-treat over a mixture of arms.
    """
    by_arm: dict[str, list] = {}
    blocks: dict[str, dict] = {}
    seen = 0
    for record in turn_records(logs):
        design = ((record.get("plan") or {}).get("msg_arm")
                  if isinstance(record.get("plan"), dict) else None)
        if not isinstance(design, dict) or design.get("repeat"):
            continue
        seen += 1
        outcome = accepted_next(logs, record)
        if outcome is None:
            continue
        arm = design.get("arm")
        by_arm.setdefault(arm, []).append(outcome)
        blocks.setdefault(design.get("block_key"), {}).setdefault(arm, []).append(outcome)

    if not seen:
        print("no msg_arm records yet — the flag has not run live.")
        print("Intake and balance can be replayed today with the `intake` mode; "
              "this read-out needs a deployment.")
        return 0
    print(f"records: {seen:,}\n")
    reference = nego_arms.NEUTRAL
    for arm in nego_arms.ARMS:
        values = by_arm.get(arm) or []
        if not values:
            continue
        rate = sum(values) / len(values)
        print(f"  {arm}  n={len(values):>6,}  accepted {rate:6.1%}")
    print("\nblock-weighted contrasts against "
          f"{reference} (bootstrap over blocks, 95% CI):")
    for arm in nego_arms.ARMS:
        if arm == reference:
            continue
        deltas = []
        for cell in blocks.values():
            here, there = cell.get(arm), cell.get(reference)
            if here and there:
                deltas.append(sum(here) / len(here) - sum(there) / len(there))
        if not deltas:
            continue
        lo, hi = boot_ci(deltas)
        print(f"  {arm} - {reference}: {sum(deltas)/len(deltas):+.3f}  "
              f"95% CI [{lo:+.3f}, {hi:+.3f}]  (blocks={len(deltas)})")
    print("\nNote: N0 is silence. Its contrast measures the CHANNEL, not a "
          "framing;\nno framing arm may use it as the reference.")
    return 0


def accepted_next(logs: str, record: dict):
    """Whether the opponent accepted the price this turn put on the table.

    Read from the per-game file the fleet already writes, so no extra logging
    exists for this experiment to depend on.
    """
    path = os.path.join(logs, record.get("_probe", ""), "games",
                        f"{record.get('game_id')}.json")
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError):
        return None
    history = (doc.get("final_state") or doc.get("state") or {}).get("history") or []
    round_no = record.get("round")
    for entry in history:
        if not isinstance(entry, dict):
            continue
        if entry.get("round") in (round_no, (round_no or 0) + 1):
            decision = str(entry.get("decision") or entry.get("action") or "")
            if decision:
                return 1.0 if "accept" in decision.lower() else 0.0
    return None


def boot_ci(values, draws: int = 4000, seed: int = 7):
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(draws))
    return means[int(0.025 * draws)], means[int(0.975 * draws)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("mode", choices=("intake", "report"))
    parser.add_argument("--logs", default="logs")
    args = parser.parse_args()
    return intake(args.logs) if args.mode == "intake" else report(args.logs)


if __name__ == "__main__":
    raise SystemExit(main())
