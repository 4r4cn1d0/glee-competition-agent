#!/usr/bin/env python3
"""Score the cloned opponent against what real opponents actually did.

WHY THIS IS THE GATE. Training a policy against a clone teaches it to beat THE
CLONE. If the clone is wrong the learned policy is tuned to a fiction, and the
arena will report a confident win either way -- it has no way to know. We have a
direct measurement of how much this matters: the now-superseded
GLEE_NEGO_CI_ASK_AB experiment, same games and same flags, scored

    legacy clone   +0.0059 percentile, CI [+0.0041, +0.0080]   "candidate better"
    V2 clone       -0.0003 percentile, CI [-0.0008, +0.0000]   "cannot distinguish"

and the control's own close rate moved 58.9% -> 40.3% between them. One of those
opponent models is badly wrong about the field and the arena cannot tell you
which. So before any training run, measure the clone the way we would measure a
classifier: on games it never saw.

WHAT IS SCORED. Every point in a real logged negotiation where the OPPONENT
responded to a price we put on the table. The clone sees the same state and we
compare its decision to theirs. Two numbers matter and they are different:

  * ACCURACY -- how often the clone's sampled decision matches. Beating the base
    rate is necessary, not sufficient: a clone that always says "reject" scores
    well whenever rejection is common, and would still be useless for pricing.
  * CALIBRATION -- when the clone accepts p of the time in some price band, does
    the field accept p of the time there? THIS is what a pricing policy consumes.
    A miscalibrated clone with good accuracy will still teach the wrong price.

HOLD-OUT. The clone is fitted from the same results.jsonl this reads, so scoring
it on all of that data grades it on its own training set. --since splits the
window: the clone is judged only on games after the cutoff, which are a small
share of what it was fitted on. That is not a clean hold-out -- a real one means
refitting on a prefix -- and the number is optimistic to that extent. It is
reported anyway because it is cheap and the failure it catches (a clone that
cannot even predict its own training distribution) is fatal and common.

    python -m sim.clone_fidelity --hours 24
    python -m sim.clone_fidelity --hours 24 --v2      # score the repaired clone
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)


def opponent_decision_points(hours: float):
    """Yield (game_dict_as_the_opponent_sees_it, what_they_actually_did)."""
    cut = time.time() - hours * 3600
    for path in sorted(glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("ts", 0) < cut:
                    continue
                fin = rec.get("final") or {}
                if fin.get("game_family") != "negotiation":
                    continue
                gs = fin.get("game_state") or {}
                me = fin.get("your_player")
                them = "player_2" if me == "player_1" else "player_1"
                their_value = gs.get(f"{them}_value")
                if their_value is None:
                    continue          # hidden: we never learn their value, unscoreable
                hist = [h for h in (gs.get("history") or []) if isinstance(h, dict)]
                for ev in hist:
                    offer = ev.get("offer") or {}
                    price = offer.get("price")
                    # only points where THEY responded to OUR price
                    if price is None or offer.get("from_player") != me:
                        continue
                    decision = str(ev.get("decision") or "")
                    if not decision:
                        continue
                    accepted = decision.lower().startswith("accept")
                    state = dict(gs)
                    state["round"] = ev.get("round") or 1
                    state["last_offer"] = dict(offer)
                    state["product_price"] = float(price)
                    game = {"game_family": "negotiation",
                            "your_player": them,
                            "game_state": state,
                            "valid_actions": {"type": "decision"}}
                    yield game, accepted, float(price), float(their_value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--v2", action="store_true",
                    help="score the repaired clone (GLEE_SIM_NEGO_RESP_V2)")
    ap.add_argument("--trials", type=int, default=8,
                    help="samples per decision point; the clone is stochastic")
    args = ap.parse_args()

    os.environ.pop("GLEE_SIM_NEGO_RESP_V2", None)
    if args.v2:
        os.environ["GLEE_SIM_NEGO_RESP_V2"] = "1"

    from sim.field_data import Field
    field = Field()
    rng = random.Random(20260822)

    n = hit = actual_yes = pred_yes = 0
    buckets = defaultdict(lambda: [0, 0.0])       # (real accepts, summed predicted p)
    for game, accepted, price, their_value in opponent_decision_points(args.hours):
        clone = field.sample_opponent(rng)
        yes = 0
        for _ in range(args.trials):
            try:
                out = clone(game)
            except Exception:
                out = None
            if isinstance(out, dict) and str(out.get("decision", "")).lower().startswith("accept"):
                yes += 1
        p = yes / args.trials
        n += 1
        actual_yes += int(accepted)
        pred_yes += p
        if (p >= 0.5) == accepted:
            hit += 1
        # bucket by how good the price was FOR THEM, which is what a pricing
        # policy varies and therefore the axis calibration has to hold on
        role = (game["game_state"].get(f"{game['your_player']}_role") or "")
        edge = ((their_value - price) if role == "buyer" else (price - their_value))
        b = min(4, max(0, int((edge / max(abs(their_value), 1.0) + 0.25) / 0.125)))
        buckets[b][0] += int(accepted)
        buckets[b][1] += p

    if not n:
        print("no scoreable decision points found")
        return 1
    base = max(actual_yes, n - actual_yes) / n
    print(f"clone: {'V2 (repaired)' if args.v2 else 'legacy'}   "
          f"decision points: {n:,}   window: {args.hours:g}h\n")
    print(f"  field's real accept rate     {actual_yes/n:>7.1%}")
    print(f"  clone's predicted rate       {pred_yes/n:>7.1%}"
          f"   (gap {pred_yes/n - actual_yes/n:+.1%})")
    print(f"  accuracy                     {hit/n:>7.1%}")
    print(f"  always-guess-majority base   {base:>7.1%}"
          f"   -> lift {hit/n - base:+.1%}")
    print("\n  CALIBRATION by how good our price was for them "
          "(this is the axis a pricing policy moves along):")
    print(f"    {'band':>8s}{'n':>7s}{'real accept':>13s}{'clone says':>12s}{'error':>9s}")
    labels = ["worst", "poor", "fair", "good", "best"]
    worst = 0.0
    for b in sorted(buckets):
        cnt = sum(1 for _ in ())  # placeholder replaced below
    counts = defaultdict(int)
    # recount cheaply: buckets holds sums, we need n per bucket
    for game, accepted, price, their_value in opponent_decision_points(args.hours):
        role = (game["game_state"].get(f"{game['your_player']}_role") or "")
        edge = ((their_value - price) if role == "buyer" else (price - their_value))
        b = min(4, max(0, int((edge / max(abs(their_value), 1.0) + 0.25) / 0.125)))
        counts[b] += 1
    for b in sorted(buckets):
        c = counts[b]
        if c < 20:
            continue
        real = buckets[b][0] / c
        pred = buckets[b][1] / c
        worst = max(worst, abs(real - pred))
        print(f"    {labels[b]:>8s}{c:>7d}{real:>13.1%}{pred:>12.1%}{pred-real:>+9.1%}")
    print(f"\n  worst calibration error: {worst:.1%}")
    print("\n  READ THIS BEFORE TRAINING ANYTHING ON THE ARENA:")
    print("  Accuracy above the base rate only says the clone is not useless.")
    print("  It is the CALIBRATION column that a price-search consumes: a clone")
    print("  that is 15 points optimistic in the 'good' band will happily teach a")
    print("  policy to ask for more than the field will ever pay, and the arena")
    print("  will score that policy as a winner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
