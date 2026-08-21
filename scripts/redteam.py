#!/usr/bin/env python3
"""Red-team evolver: search for the opponent that exploits OUR stack hardest.

``scripts/evolve.py`` searches our own knobs to play the field better. This
searches the OPPONENT's knobs to play US worse, which is a different objective
and finds different things: a knob that is fine on average against the observed
field can still have a shape that an opponent who is aiming at it can open up.
The field has not aimed at us yet. The point of this script is to find what it
would get if it did, while a fix is still free.

    # what each named attack takes off us, against the field's own baseline
    python scripts/redteam.py --mode catalogue --family bargaining --games 3000

    # search for something worse
    python scripts/redteam.py --mode evolve --family negotiation --games 2000

    # which of our decision rules fired in the games the winner won
    python scripts/redteam.py --mode diagnose --family bargaining --attack best.json

    # ...and which of them the attack is actually EATING (turn each off in turn)
    python scripts/redteam.py --mode ablate --family bargaining --attack best.json

FITNESS is the ADVERSARY's own estimated percentile (sim/percentile.py) in games
played against our live stack -- not its payoff, and not our loss. Percentile is
what the competition pays, and it is the only currency in which "this opponent
would out-rank us" is a statement about rating rather than about dollars.

The baseline every number is quoted against is the CLONED FIELD's percentile on
the same drawn games against the same stack: an attack is only interesting to
the extent it beats what an ordinary opponent already gets. Both arms see the
same configurations, seats and disclosure coins, so the comparison is paired.

WHAT THIS CANNOT SEE, said before trusting it: the adversary is parametric, not
an LLM, so it never talks its way into anything; percentile cells come from our
own fitted CDF, so an attack that drives play into a configuration region the
field never visited is scored against a thin cell; and a genome that beats us
here has not been shown to beat the FIELD, so "exploitable" here means "there
exists an opponent who would profit", not "the field is about to do this".
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from sim.adversary import (ARCHETYPES, GENOME_SPACE, Adversary,  # noqa: E402
                           clamp_genome, default_genome)
from sim.field_data import Field                                  # noqa: E402
from sim.percentile import percentile as _pct                     # noqa: E402
from sim.replay_eval import DEFAULT_CONTROL, _build_strategy, _draw_games, _set_flags  # noqa: E402

#: The stack the fleet actually runs -- DEFAULT_CONTROL plus today's live arm.
#: This is what the adversary is being evolved against; if the fleet's arm
#: changes, this changes the same day or the whole run is aimed at a ghost.
LIVE_STACK = dict(DEFAULT_CONTROL, **{"GLEE_NEGO_ULTIMATUM_SHARE": "0.80",
                                      "GLEE_NEGO_MARGIN_WEIGHT": "0.40",
                                      "GLEE_NEGO_POSTERIOR": "1",
                                      "GLEE_BARG_STONEWALL": "3"})

#: Which knobs a given family's search is allowed to move. Mutating negotiation
#: knobs during a bargaining search is pure noise: it cannot change a single
#: decision, but it does change the genome, so the log stops meaning anything.
FAMILY_KNOBS = {"bargaining": [k for k in GENOME_SPACE if k.startswith("b_")],
                "negotiation": [k for k in GENOME_SPACE if k.startswith("n_")]}


def other(seat: str) -> str:
    return "player_2" if seat == "player_1" else "player_1"


def _play_vs(field, draws, flags, adversary=None, sink=None):
    """Play every drawn game of ``draws`` with our stack against one opponent.

    ``adversary=None`` plays the cloned field opponent the draw selected -- the
    baseline arm. Otherwise the clone is replaced by the adversary while every
    other feature of the draw (configuration, seat, disclosed name, engine seed)
    is held identical, so the two arms differ ONLY in who is sitting across the
    table.
    """
    from sim import Config as SimConfig
    from sim.arena import play

    strategy = (_build_strategy(flags) if sink is None
                else _instrumented_strategy(flags, sink))
    rows = []
    for family, params, seat, game_seed in draws:
        grng = random.Random(game_seed)
        clone = field.sample_opponent(random.Random(game_seed + 1))
        params = dict(params)
        if clone.name != "__field__":
            params["opponent_name"] = clone.name
            params["disclose_opponent"] = random.Random(game_seed + 2).random() < 0.5
        foe = adversary if adversary is not None else clone
        s1, s2 = (strategy, foe) if seat == "player_1" else (foe, strategy)
        result = play(SimConfig(family, dict(params)), s1, s2, grng)
        seat_them = other(seat)
        scale = params.get("money_to_divide") or params.get(f"{seat}_value") or 1.0
        scale_them = params.get("money_to_divide") or params.get(f"{seat_them}_value") or 1.0
        rows.append({
            "family": family,
            "closed": result.outcome == "agreement",
            "rounds": result.rounds_played,
            "us_norm": result.payoff(seat) / scale,
            "them_norm": result.payoff(seat_them) / scale_them,
            "us_pct": _pct(family, params, seat, result.payoff(seat)),
            "them_pct": _pct(family, params, seat_them, result.payoff(seat_them)),
        })
    return rows


def _instrumented_strategy(flags, sink: Counter):
    """Our stack, plus a tally of which of its own decision rules fired.

    Calls the family ``decide`` directly so the ``_plan`` dict survives -- the
    dispatcher pops it, and with no game log attached it is simply discarded.
    Used only by ``--mode diagnose``: it is the difference between "the attack
    wins" and "the attack wins BECAUSE this named rule fired".
    """
    _set_flags(flags)
    from glee_agent.actions import coerce, safe_action
    from glee_agent.config import Config
    from glee_agent.strategies import bargaining, negotiation

    cfg = Config.from_env()
    cfg.llm_mode = "off"
    table = {"bargaining": bargaining.decide, "negotiation": negotiation.decide}

    #: plan keys whose mere presence means the named rule fired this turn
    FLAGS = ("stonewall_release", "accept_floor_applied", "span_veto",
             "table_accept_below", "recip_damped", "deadgame", "ultimatum",
             "probe_hold", "time_driven", "opponent_floor_applied")

    def strategy(game: dict) -> dict:
        decide = table.get(game.get("game_family"))
        if decide is None:
            return safe_action(game)
        try:
            raw = decide(game, cfg)
        except Exception:
            return safe_action(game)
        plan = raw.pop("_plan", None) or {}
        sink["turns"] += 1
        for key in FLAGS:
            if plan.get(key):
                sink[key] += 1
        return coerce(raw, game)

    return strategy


def _summary(rows, family):
    rows = [r for r in rows if r["family"] == family]
    n = max(1, len(rows))
    them = [r["them_pct"] for r in rows if r["them_pct"] is not None]
    us = [r["us_pct"] for r in rows if r["us_pct"] is not None]
    return {
        "n": len(rows),
        "them_pct": sum(them) / len(them) if them else 0.0,
        "us_pct": sum(us) / len(us) if us else 0.0,
        "them_norm": sum(r["them_norm"] for r in rows) / n,
        "us_norm": sum(r["us_norm"] for r in rows) / n,
        "close": sum(1 for r in rows if r["closed"]) / n,
        "rounds": sum(r["rounds"] for r in rows) / n,
    }


def _boot_ci(deltas, B=2000, seed=11):
    """Paired bootstrap CI. A CI spanning zero reads "cannot distinguish"."""
    if not deltas:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(deltas)
    means = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(B))
    return means[int(0.025 * B)], means[int(0.975 * B)]


def _paired(rows_base, rows_adv, family, key):
    return [b[key] - a[key]
            for a, b in zip(rows_base, rows_adv)
            if a["family"] == family and a[key] is not None and b[key] is not None]


def fitness(field, draws, flags, genome, family):
    rows = _play_vs(field, draws, flags, Adversary(genome))
    return _summary(rows, family)["them_pct"], rows


# --------------------------------------------------------------------------
# modes
# --------------------------------------------------------------------------

def mode_catalogue(field, draws, flags, family, extra=None):
    """Score every named attack against the cloned-field baseline."""
    base = _play_vs(field, draws, flags)
    b = _summary(base, family)
    print(f"BASELINE  cloned field vs our stack, {b['n']} games ({family})")
    print(f"  field percentile {b['them_pct']:.4f}   our percentile {b['us_pct']:.4f}"
          f"   close {b['close']:.1%}   mean rounds {b['rounds']:.1f}\n")
    print(f"  {'attack':20s}{'THEIR pct':>11s}{'delta':>9s}{'95% CI':>20s}"
          f"{'our pct':>10s}{'we lose':>9s}{'close':>8s}{'rnds':>7s}")
    attacks = dict(ARCHETYPES)
    if extra:
        attacks.update(extra)
    out = []
    for name, genome in attacks.items():
        rows = _play_vs(field, draws, flags, Adversary(genome, name))
        s = _summary(rows, family)
        d_them = _paired(base, rows, family, "them_pct")
        d_us = _paired(base, rows, family, "us_pct")
        lo, hi = _boot_ci(d_them)
        gain = sum(d_them) / max(1, len(d_them))
        loss = sum(d_us) / max(1, len(d_us))
        out.append({"attack": name, "them_pct": s["them_pct"], "gain": gain,
                    "ci": [lo, hi], "us_pct": s["us_pct"], "our_loss": loss,
                    "close": s["close"], "rounds": s["rounds"],
                    "genome": {k: round(genome[k], 4) for k in FAMILY_KNOBS[family]}})
        print(f"  {name:20s}{s['them_pct']:>11.4f}{gain:>+9.4f}"
              f"{f'[{lo:+.4f},{hi:+.4f}]':>20s}{s['us_pct']:>10.4f}{loss:>+9.4f}"
              f"{s['close']:>8.1%}{s['rounds']:>7.1f}")
    out.sort(key=lambda r: -r["gain"])
    return {"baseline": b, "attacks": out}


#: Probability that a mutation RESAMPLES a knob across its whole range instead
#: of nudging it. Local gaussian search alone is not enough here: the first run
#: of this script started from the linear conceder and converged on a 0.391
#: adversary while the hand-written lowball repeater in the catalogue was
#: already scoring 0.584. The exploit basin needs three knobs to move together
#: (a long stall run AND a high accept threshold AND deep patience), and a
#: sigma-sized step in any one of them alone makes the genome WORSE, so a pure
#: hill climb can never reach it from the field's own behaviour.
MACRO_RATE = 0.25


def mode_evolve(field, flags, family, games, generations, lam, rng):
    """(1+lambda) hill climb on the adversary's genome, warm-started.

    A FRESH game seed every generation, exactly as scripts/evolve.py does: an
    adversary that only beats us on one draw of the field is an artefact of that
    draw, and the whole point is to find shapes that survive re-drawing.

    Generation 0 evaluates the whole hand-written catalogue and adopts the best
    of it as the parent. That is not a shortcut past the search -- it is what
    stops the search reporting a local optimum as "the worst we found" when a
    named archetype in the same file already beats it.
    """
    knobs = FAMILY_KNOBS[family]
    log = []
    seed = rng.randrange(2 ** 30)
    draws = _draw_games(field, [family], games, seed)
    best, best_score = None, -1.0
    for name, genome in ARCHETYPES.items():
        score, _ = fitness(field, draws, flags, genome, family)
        print(f"seed  {name:20s} adversary pct {score:.4f}", flush=True)
        if score > best_score:
            best, best_score = clamp_genome(dict(genome)), score
    print(f"warm start -> {best_score:.4f}\n", flush=True)

    for gen in range(generations):
        if gen:
            seed = rng.randrange(2 ** 30)
            draws = _draw_games(field, [family], games, seed)
        base = _play_vs(field, draws, flags)
        b = _summary(base, family)
        parent, _ = fitness(field, draws, flags, best, family)
        gen_best, gen_vec = parent, None
        for _ in range(lam):
            child = dict(best)
            for k in knobs:
                lo, hi, sigma, _doc = GENOME_SPACE[k]
                if rng.random() < MACRO_RATE:
                    child[k] = rng.uniform(lo, hi)
                else:
                    child[k] = min(max(child[k] + rng.gauss(0, sigma), lo), hi)
            score, _ = fitness(field, draws, flags, child, family)
            if score > gen_best:
                gen_best, gen_vec = score, child
        if gen_vec is not None:
            best = clamp_genome(gen_vec)
        best_score = gen_best
        log.append({"gen": gen, "seed": seed, "improved": gen_vec is not None,
                    "adversary_pct": round(gen_best, 5),
                    "field_pct": round(b["them_pct"], 5),
                    "best": {k: round(best[k], 4) for k in knobs}})
        print(f"gen {gen:2d}  {'improved' if gen_vec is not None else 'held    '}"
              f"  adversary pct {gen_best:.4f}  (field {b['them_pct']:.4f})  "
              f"{json.dumps(log[-1]['best'])}", flush=True)
    return best, best_score, log


def mode_ablate(field, draws, flags, family, genome, label):
    """Turn each of OUR flags off in turn and re-fight the attack.

    "Which rule is the attack eating?" is not answerable from the firing counts
    alone -- a rule can fire constantly and cost nothing. It is answerable by
    removing the rule: if OUR percentile against the attack goes UP when a flag
    is removed, that flag is the hole, and the column beside it says what
    removing it would cost us against the ordinary field.

    A flag worth defending shows both: a large positive ``attacked`` delta and a
    ``field`` delta that is negative or nil (i.e. we keep the flag, and gate the
    hole). A flag with a large positive delta in BOTH columns was simply a bad
    flag and does not need a red team to find.
    """
    adversary = Adversary(genome, label)
    full_field = _summary(_play_vs(field, draws, flags), family)
    full_atk = _summary(_play_vs(field, draws, flags, adversary), family)
    print(f"=== flag ablation under {label} ({family}, {full_atk['n']} games) ===")
    print(f"  full stack: our percentile {full_field['us_pct']:.4f} vs field, "
          f"{full_atk['us_pct']:.4f} vs attack\n")
    print(f"  {'flag removed':32s}{'vs field':>11s}{'delta':>9s}"
          f"{'vs attack':>11s}{'delta':>9s}")
    rows = []
    for key in sorted(flags):
        cut = {k: v for k, v in flags.items() if k != key}
        s_field = _summary(_play_vs(field, draws, cut), family)
        s_atk = _summary(_play_vs(field, draws, cut, adversary), family)
        d_field = s_field["us_pct"] - full_field["us_pct"]
        d_atk = s_atk["us_pct"] - full_atk["us_pct"]
        rows.append({"flag": key, "field_pct": s_field["us_pct"], "d_field": d_field,
                     "attack_pct": s_atk["us_pct"], "d_attack": d_atk})
        print(f"  {key:32s}{s_field['us_pct']:>11.4f}{d_field:>+9.4f}"
              f"{s_atk['us_pct']:>11.4f}{d_atk:>+9.4f}")
    rows.sort(key=lambda r: -r["d_attack"])
    return {"full_field": full_field, "full_attack": full_atk, "ablations": rows}


def mode_diagnose(field, draws, flags, family, genome, label):
    """Which of OUR rules fired in the games this attack played."""
    sink_base, sink_adv = Counter(), Counter()
    base = _play_vs(field, draws, flags, sink=sink_base)
    rows = _play_vs(field, draws, flags, Adversary(genome, label), sink=sink_adv)
    b, s = _summary(base, family), _summary(rows, family)
    print(f"\n=== rule firing, {label} vs cloned field ({family}, {s['n']} games) ===")
    print(f"  {'rule':26s}{'vs field':>12s}{'vs attack':>12s}")
    for key in sorted(set(sink_base) | set(sink_adv)):
        if key == "turns":
            continue
        print(f"  {key:26s}{sink_base[key] / max(1, sink_base['turns']):>12.3%}"
              f"{sink_adv[key] / max(1, sink_adv['turns']):>12.3%}")
    print(f"  {'(turns)':26s}{sink_base['turns']:>12d}{sink_adv['turns']:>12d}")
    print(f"\n  their percentile {b['them_pct']:.4f} -> {s['them_pct']:.4f}"
          f"   our percentile {b['us_pct']:.4f} -> {s['us_pct']:.4f}")
    return {"field": dict(sink_base), "attack": dict(sink_adv),
            "baseline": b, "attacked": s}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", choices=("catalogue", "evolve", "diagnose", "ablate"),
                    default="catalogue")
    ap.add_argument("--family", choices=("bargaining", "negotiation"),
                    default="bargaining")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--generations", type=int, default=12)
    ap.add_argument("--lam", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--stack", default=json.dumps(LIVE_STACK),
                    help="JSON flag dict, or a path to one, for the stack under "
                         "attack (default: the live composite arm). A flag "
                         "REMOVED from this dict is the cheapest way to ask "
                         "'is that rule what the attack is eating?'")
    ap.add_argument("--attack", default=None,
                    help="JSON genome, or a path to one, for --mode diagnose")
    ap.add_argument("--out", default=None, help="write the run's JSON here")
    args = ap.parse_args()

    field = Field()
    flags = json.loads(open(args.stack, encoding="utf-8").read()
                       if os.path.exists(args.stack) else args.stack)
    rng = random.Random(args.seed)
    print(f"stack under attack : {json.dumps(flags, sort_keys=True)}")
    print(f"family {args.family}  games {args.games}  seed {args.seed}\n")

    doc = {"_schema": "glee.redteam/v1", "family": args.family,
           "stack": flags, "games": args.games, "seed": args.seed,
           "mode": args.mode}

    if args.mode == "evolve":
        best, score, log = mode_evolve(field, flags, args.family, args.games,
                                       args.generations, args.lam, rng)
        print("\nheld-out confirmation on a fresh seed:")
        draws = _draw_games(field, [args.family], args.games, rng.randrange(2 ** 30))
        res = mode_catalogue(field, draws, flags, args.family,
                             extra={"EVOLVED": best})
        doc.update(generations=log, evolved={k: round(best[k], 4)
                                             for k in FAMILY_KNOBS[args.family]},
                   train_pct=score, holdout=res)
    elif args.mode in ("diagnose", "ablate"):
        genome = default_genome()
        if args.attack:
            raw = args.attack
            if os.path.exists(raw):
                with open(raw, encoding="utf-8") as fh:
                    raw = fh.read()
            loaded = json.loads(raw)
            if isinstance(loaded, str):
                loaded = ARCHETYPES[loaded]
            if isinstance(loaded, dict) and "evolved" in loaded:
                loaded = loaded["evolved"]          # a saved --mode evolve report
            elif isinstance(loaded, dict) and "attacks" in loaded:
                # models/redteam_attacks_v1.json: pick this family's attack
                loaded = next(a["genome"] for a in loaded["attacks"].values()
                              if a.get("search", {}).get("family") == args.family)
            genome = dict(default_genome(), **loaded)
        draws = _draw_games(field, [args.family], args.games, args.seed)
        runner = mode_diagnose if args.mode == "diagnose" else mode_ablate
        doc[args.mode] = runner(field, draws, flags, args.family,
                                genome, args.attack or "genome")
    else:
        draws = _draw_games(field, [args.family], args.games, args.seed)
        doc["catalogue"] = mode_catalogue(field, draws, flags, args.family)

    out = args.out or os.path.join(
        REPO, "logs", "redteam",
        f"redteam_{args.family}_{args.mode}_{time.strftime('%Y%m%dT%H%M%S')}.json")
    try:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
        print(f"\nsaved -> {out}")
    except OSError as exc:
        print(f"\n(could not save report: {exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
