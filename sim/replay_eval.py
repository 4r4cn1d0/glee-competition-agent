#!/usr/bin/env python3
"""Screen a candidate strategy offline against the cloned field.

Live measurement costs ~7 hours per change at ~50 games/hr per family, every
deploy risks real rating, and the platform bans an agent whose clock slips.
This screens a candidate in minutes with none of that: the real strategy code
plays full games inside the local engines against opponents cloned from their
own logged behaviour, on the exact configuration mix we face live.

A candidate is an env-flag dict -- the same shape as an arms.json entry -- so
whatever wins here can be deployed verbatim with ``fleet.py set``:

    python -m sim.replay_eval --games 2000 \
        --candidate '{"GLEE_NEGO_MIN_MARGIN": "0.02"}' \
        --control   '{"GLEE_NEGO_MIN_MARGIN": "0.04"}'

Both arms play the SAME drawn games -- same config, same opponent, same seeds --
so the comparison is paired and the noise that dominates live A/Bs cancels.
Deltas come with bootstrap CIs; the verification-discipline rule applies here
too: a CI spanning zero reads "cannot distinguish", never "better".

What this cannot see (say it before trusting a result):
  * message-channel effects -- clones don't read text;
  * opponents' adaptation to a NEW price region we never probed live -- clones
    fall back to pooled-field behaviour outside their observed bins;
  * persuasion -- excluded from v1 (sim/field_data.py explains why);
  * percentile against the true field distribution -- we report payoff, close
    rate, and zero rate; the zero-rate column is the percentile-relevant one,
    since 51% of live negotiation outcomes sit on the $0 atom and any positive
    close beats that entire pile.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

FLAG_PREFIXES = ("GLEE_NEGO", "GLEE_BARG", "GLEE_PERS", "GLEE_OPP", "GLEE_SIM")

#: The flag set composite ran live before today's changes -- the natural control.
#: The live champion/composite stack. This MUST track what the fleet actually
#: runs: a candidate nested inside a gate the control omits is dead code, and
#: the harness reports that as a clean +0.0000 null rather than as "never
#: executed". That trap cost a real screen -- GLEE_BARG_STONEWALL sits inside
#: `if accept_floor > 0`, the old default omitted GLEE_BARG_ACCEPT_FLOOR, and
#: the A/B returned exact zeros on every metric while the code never ran.
#: Anything added to the fleet's arms belongs here the same day.
DEFAULT_CONTROL = {"GLEE_NEGO_BOUND_AS_FLOOR": "1",
                   "GLEE_BARG_OPPONENT_FLOOR": "0.39",
                   "GLEE_BARG_OFFER_FLOOR": "0.57",
                   "GLEE_BARG_ACCEPT_FLOOR": "0.50",
                   "GLEE_BARG_FLOOR_GAIN": "0.05",
                   "GLEE_NEGO_MIN_MARGIN": "0.02",
                   "GLEE_NEGO_CURVE_PRICING": "1",
                   "GLEE_NEGO_MARGIN_WEIGHT": "0.25",
                   "GLEE_NEGO_CONTINUATION_ACCEPT": "1",
                   "GLEE_NEGO_HORIZON_V2": "1",
                   "GLEE_NEGO_ENDGAME_V3": "1",
                   "GLEE_NEGO_ACCEPT_SPAN": "0.48",
                   "GLEE_NEGO_STALL_POLICY": "1",
                   "GLEE_NEGO_DEADGAME_V1": "1",
                   "GLEE_NEGO_TABLE": "1"}


def _set_flags(flags: dict) -> None:
    for k in list(os.environ):
        if k.startswith(FLAG_PREFIXES) or k == "GLEE_PROBE":
            del os.environ[k]
    os.environ.update({k: str(v) for k, v in flags.items()})
    os.environ["GLEE_LLM_MODE"] = "off"
    # runtime_flags caches arms.json lookups; with GLEE_PROBE unset it reads the
    # env directly, but reset the cache anyway so no stale arm leaks between arms.
    from glee_agent import runtime_flags
    runtime_flags._STATE.update(checked=0.0, mtime=None, arms=None)


def _build_strategy(flags: dict):
    """The real live strategy (composite policy) under this flag set."""
    _set_flags(flags)
    from glee_agent.config import Config
    from glee_agent.probes import make_probe
    strategy, _cfg = make_probe("composite", Config.from_env())
    return strategy


def _draw_games(field, families, n, seed):
    """The shared game list both arms will play: (family, params, seat, game_seed)."""
    rng = random.Random(seed)
    draws = []
    for i in range(n):
        family = families[i % len(families)]
        params, seat = field.sample_config(family, rng)
        draws.append((family, params, seat, rng.randrange(2 ** 31)))
    return draws


def _play_arm(field, draws, flags):
    from sim import Config as SimConfig
    from sim.arena import play
    strategy = _build_strategy(flags)
    rows = []
    for family, params, seat, game_seed in draws:
        grng = random.Random(game_seed)
        opponent = field.sample_opponent(random.Random(game_seed + 1))
        params = dict(params)
        if opponent.name != "__field__":
            # disclose the clone's real name to the strategy half the time,
            # exactly as the live server would; paired across arms by seed
            params["opponent_name"] = opponent.name
            params["disclose_opponent"] = random.Random(game_seed + 2).random() < 0.5
        s1, s2 = (strategy, opponent) if seat == "player_1" else (opponent, strategy)
        # A DISTINCT game id per draw, stable across arms. Every randomised arm we
        # ship assigns by sha256("<salt>|" + game_id), and sim/arena.play defaults
        # game_id to the literal "local" -- so before this, EVERY simulated game
        # hashed to the same bit and an arm was 100% control or 100% treatment,
        # never a comparison. Arms whose salt happens to hash to 0 (open_claim,
        # rank_price_ab, barg_msg) therefore returned a byte-identical FALSE NULL
        # with a zero-width CI, while arms hashing to 1 (zopa, close_ab, backload)
        # ran treatment-everywhere and looked fine. That asymmetry is worse than a
        # uniform break because it is invisible in exactly half of cases.
        # Deriving the id from the draw seed keeps the two arms paired: the same
        # game carries the same id, so it lands in the same arm in both runs and
        # the comparison stays like-for-like.
        gid = f"sim-{game_seed:08x}"
        result = play(SimConfig(family, dict(params)), s1, s2, grng, game_id=gid)
        mine = result.payoff(seat)
        scale = params.get("money_to_divide") or params.get("player_1_value") or 1.0
        from sim.percentile import percentile as _pct
        rows.append({"family": family, "mine": mine, "norm": mine / scale,
                     "closed": result.outcome == "agreement",
                     "zero": mine <= 0.0, "opponent": opponent.name,
                     "pct": _pct(family, params, seat, mine)})
    return rows


def _boot_ci(deltas, B=4000, seed=7):
    if not deltas:
        return None
    rng = random.Random(seed)
    n = len(deltas)
    means = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n
                   for _ in range(B))
    return means[int(0.025 * B)], means[int(0.975 * B)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--candidate", required=True, help="JSON flag dict for the candidate")
    ap.add_argument("--control", default=json.dumps(DEFAULT_CONTROL),
                    help="JSON flag dict for the control (default: live composite)")
    ap.add_argument("--games", type=int, default=2000)
    ap.add_argument("--families", default="bargaining,negotiation")
    ap.add_argument("--seed", type=int, default=20260820)
    args = ap.parse_args()

    from sim.field_data import Field
    field = Field()
    families = [f.strip() for f in args.families.split(",") if f.strip()]
    draws = _draw_games(field, families, args.games, args.seed)

    control = json.loads(args.control)
    # The candidate is an OVERLAY on the control, not a replacement. _set_flags
    # clears every GLEE_ key before applying an arm, so a bare
    # --candidate '{"GLEE_NEGO_BOULWARE": "1.2"}' used to play an arm with that
    # one flag and NOTHING else -- the whole live stack silently stripped. Every
    # such run measured "strategy with no flags vs strategy with fifteen", which
    # swamps the flag under test and reads as a large, entirely spurious
    # negative. It also silently disarms gates the candidate depends on: a
    # harvest-margin sweep whose rule sits inside GLEE_NEGO_ENDGAME_V3 produced
    # BIT-IDENTICAL numbers for 0.02, 0.05 and 0.02+buyer, because the gate was
    # off in all three and none of them ever executed the rule.
    # Merging makes --candidate mean what every caller has assumed it means:
    # the live stack, plus these overrides. Pass --control '{}' for a bare arm.
    overrides = json.loads(args.candidate)
    candidate = {**control, **overrides}
    print(f"control   : {json.dumps(control, sort_keys=True)}")
    print(f"overrides : {json.dumps(overrides, sort_keys=True)}")
    print(f"candidate : {json.dumps(candidate, sort_keys=True)}")
    if not overrides:
        print("WARNING: empty override set -- both arms are identical.")
    _noop = [k for k, v in overrides.items() if str(control.get(k)) == str(v)]
    if _noop:
        print(f"WARNING: override(s) equal to the control, so they change "
              f"nothing: {sorted(_noop)}")
    print(f"playing {len(draws)} paired games "
          f"({', '.join(families)}) against the cloned field...\n")

    rows_ctl = _play_arm(field, draws, control)
    rows_cnd = _play_arm(field, draws, candidate)

    verdicts = []
    for family in families:
        pairs = [(a, b) for a, b in zip(rows_ctl, rows_cnd) if a["family"] == family]
        if not pairs:
            continue
        n = len(pairs)
        def mean(rows, key):
            return sum(float(r[key]) for r in rows) / n
        ctl = [a for a, _ in pairs]
        cnd = [b for _, b in pairs]
        d_norm = [b["norm"] - a["norm"] for a, b in pairs]
        d_close = [b["closed"] - a["closed"] for a, b in pairs]
        d_pct = [b["pct"] - a["pct"] for a, b in pairs
                 if a.get("pct") is not None and b.get("pct") is not None]
        ci_n = _boot_ci(d_norm)
        ci_c = _boot_ci(d_close)
        ci_p = _boot_ci(d_pct)
        verdict = ("cannot distinguish" if ci_n and ci_n[0] <= 0.0 <= ci_n[1]
                   else ("CANDIDATE BETTER" if sum(d_norm) > 0 else "CANDIDATE WORSE"))
        verdicts.append((family, verdict))
        print(f"=== {family} (n={n} paired) ===")
        print(f"  {'':14s}{'payoff/scale':>13s}{'close rate':>12s}{'zero rate':>11s}")
        print(f"  {'control':14s}{mean(ctl,'norm'):>13.4f}{mean(ctl,'closed'):>12.1%}"
              f"{mean(ctl,'zero'):>11.1%}")
        print(f"  {'candidate':14s}{mean(cnd,'norm'):>13.4f}{mean(cnd,'closed'):>12.1%}"
              f"{mean(cnd,'zero'):>11.1%}")
        print(f"  payoff delta {sum(d_norm)/n:+.4f}  95% CI [{ci_n[0]:+.4f}, {ci_n[1]:+.4f}]")
        print(f"  close  delta {sum(d_close)/n:+.3f}   95% CI [{ci_c[0]:+.3f}, {ci_c[1]:+.3f}]")
        if d_pct:
            print(f"  EST. PERCENTILE delta {sum(d_pct)/len(d_pct):+.4f}  "
                  f"95% CI [{ci_p[0]:+.4f}, {ci_p[1]:+.4f}]  "
                  f"(n={len(d_pct)} scoreable — the rating-relevant number)")
        print(f"  -> {verdict}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
