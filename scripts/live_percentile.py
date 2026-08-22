#!/usr/bin/env python3
"""Score our REAL completed games as percentiles. The meter the arena is not.

Why this exists. Two things were being used to judge a strategy change and both
are poor:

  * the ARENA, whose negotiation opponent clone cannot price aggression -- it
    bins on _price_bin (0.1 of base) while the moves we test are often smaller
    than one bin, consults a survivorship-selected value-keyed table first, and
    FALLS BACK to "profitable -> AcceptOffer" (sim/field_data.py:343), which
    grants any greedy ask it has never observed;
  * the LIVE RATING, which is a lagged, shrunk, opponent-adjusted transform of
    percentile. The measured cross-agent noise floor on IDENTICAL code is +/-125
    rating, so a +2-rating change is 62x below the noise and unobservable.

But the rating is a transform of a quantity we can compute ourselves for every
finished game: the percentile of our payoff within its exact configuration cell.
That is the RAW signal the rating is a noisy average of, and per-game it has far
more statistical power than watching a rating drift.

So: replay our own results.jsonl through the same fitted CDF the simulator uses
(models/percentile_cdf_v3.json), and report mean percentile per agent, family,
cell and era. No simulation, no cloned opponent, no assumption about how the
field responds -- these are the payoffs the field actually paid us.

    python scripts/live_percentile.py                      # last 24h, by agent
    python scripts/live_percentile.py --hours 6 --by cell
    python scripts/live_percentile.py --split 1787342160   # A/B across a deploy
    python scripts/live_percentile.py --ab rank-price      # terminal-price arm
    python scripts/live_percentile.py --ab open-claim --since T0 --until T1
                                                     # CI opening/floor arm + veto
    python scripts/live_percentile.py --ab barg-msg        # B0 silence vs B1-B3

CAVEAT, stated because it decides how far the numbers can be pushed: the cell
CDF is fitted from logged field payoffs, OUR OWN GAMES INCLUDED, so it is a
self-referential yardstick and drifts as the field drifts. It is reliable for
COMPARING two of our own arms measured in the same window against the same CDF,
which is what it is for. It is not an independent estimate of our true rank.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.percentile import percentile          # noqa: E402
from glee_agent.messages import BARG_ARMS, bargaining_arm  # noqa: E402
from scripts.orphan_watch import COLD_SECONDS as ORPHAN_COLD_SECONDS  # noqa: E402

NAMES = {"champion": "Test 1", "hardliner": "Test 2", "conceder": "Test 3",
         "randomized": "Test 4", "composite": "Agent 5"}


def mean_ci(xs):
    """Mean with a normal 95% interval. n<2 gives no interval, not a fake one."""
    n = len(xs)
    if n == 0:
        return None, 0.0, 0.0, 0
    m = sum(xs) / n
    if n < 2:
        return m, m, m, n
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    half = 1.96 * math.sqrt(var / n)
    return m, m - half, m + half, n


def _result_records(hours):
    """Yield (slot, timestamp, envelope, final) from results.jsonl files."""
    cut = time.time() - hours * 3600
    for path in sorted(glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl"))):
        slot = os.path.basename(os.path.dirname(path))
        if slot not in NAMES:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                ts = rec.get("ts", 0)
                if ts < cut:
                    continue
                fin = rec.get("final") or {}
                yield slot, ts, rec, fin


def games(hours):
    """Yield score and message eligibility fields for finished games."""
    for slot, ts, rec, fin in _result_records(hours):
        fam = fin.get("game_family")
        seat = fin.get("your_player")
        gs = fin.get("game_state") or {}
        res = fin.get("result") or {}
        if not fam or not seat:
            continue
        pay = res.get(f"{seat}_payoff")
        if pay is None:
            pay = res.get("your_payoff")
        if not isinstance(pay, (int, float)):
            continue
        params = dict(gs)
        pct = percentile(fam, params, seat, float(pay))
        if pct is None:            # unknown cell -- no opinion, skip
            continue
        yield (slot, ts, fam, pct, rec.get("game_id"),
               gs.get("messages_allowed"))


def open_claim_arm(gid) -> str | None:
    """Recover the complete-information opening/floor arm used on the wire."""
    gid = str(gid or "")
    if not gid:
        return None
    bit = int(hashlib.sha256(("open_claim|" + gid).encode()).hexdigest(), 16) & 1
    return "candidate" if bit else "control"


def _number(value) -> float | None:
    """Match the live action guard's finite numeric coercion."""
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip().replace("$", "").replace(",", "").replace("%", "")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _open_claim_static_eligible(seat: str, state: dict) -> bool:
    """Whether either seat has the positive visible ZOPA required by the arm."""
    if seat not in ("player_1", "player_2"):
        return False
    if state.get("complete_information") is not True:
        return False
    role = state.get(f"{seat}_role")
    if role not in ("seller", "buyer"):
        return False
    other = "player_2" if seat == "player_1" else "player_1"
    other_role = state.get(f"{other}_role")
    if (role, other_role) not in (("seller", "buyer"), ("buyer", "seller")):
        return False
    seller = seat if role == "seller" else other
    buyer = seat if role == "buyer" else other
    seller_value = _number(state.get(f"{seller}_value"))
    buyer_value = _number(state.get(f"{buyer}_value"))
    if seller_value is None or buyer_value is None or buyer_value <= seller_value:
        return False
    return True


def _open_claim_exposure_turn(slot: str, rec: dict):
    """Return an eligible outgoing-price exposure key and timestamp."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    if not gid or not _open_claim_static_eligible(seat, state):
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    action = rec.get("action") or {}
    if not isinstance(action, dict) or "product_price" not in action:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    return (slot, gid), ts


def _terminal_close(fin: dict) -> bool | None:
    """Return agreement status, or None while/no terminal outcome is recorded."""
    result = fin.get("result") or {}
    status = str(fin.get("status") or "").strip().lower()
    outcome = str(result.get("outcome") or "").strip().lower()
    if status == "active" or outcome == "active":
        return None
    if outcome == "agreement":
        return True
    if status == "no_deal" or outcome in ("no_deal", "timeout", "walked_away"):
        return False
    return None


def _open_claim_row(slot: str, rec: dict, fin: dict):
    """Build one eligible arm outcome, retaining unknown-CDF close results."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    if not gid or not _open_claim_static_eligible(seat, state):
        return None

    closed = _terminal_close(fin)
    if closed is None:
        return None
    result = fin.get("result") or {}
    payoff = result.get(f"{seat}_payoff")
    if payoff is None:
        payoff = result.get("your_payoff")
    pct = None
    payoff_number = _number(payoff)
    if payoff_number is not None:
        pct = percentile("negotiation", dict(state), seat, payoff_number)
    return slot, pct, str(gid), closed


def _game_record_final(record: dict) -> dict:
    """Rebuild the final envelope stored by the continuous outcome collector."""
    state = dict(record.get("config") or {})
    state.pop("result", None)
    state["history"] = record.get("history") or []
    return {
        "game_id": record.get("game_id"),
        "game_family": record.get("game_family"),
        "your_player": record.get("your_player"),
        "status": record.get("status"),
        "game_state": state,
        "result": record.get("result") or {},
    }


def _prefer_final(latest: dict, key: tuple[str, str], stamp: float,
                  rec: dict, fin: dict) -> None:
    """Keep a terminal final ahead of an active snapshot, then the newest copy."""
    rank = (_terminal_close(fin) is not None, stamp)
    previous = latest.get(key)
    if previous is None or rank >= previous[0]:
        latest[key] = (rank, rec, fin)


def open_claim_games(hours, since=None, until=None):
    """Yield the first-price exposure cohort with its terminal outcomes.

    ``results.jsonl`` timestamps say when a result was fetched, not when the arm
    first affected an outgoing price. Cohorting on that turn prevents a delayed
    backfill from importing pre-experiment games. The presence of product_price
    is fixed before this postcondition changes its number, so the cohort does not
    select on the assigned arm. Fresh or malformed outcomes stay unresolved,
    while calibrated aged omissions count as abandonments, so collector lag
    cannot make the close-rate veto look better.
    """
    now = time.time()
    cut = float(since) if since is not None else now - hours * 3600
    end = float(until) if until is not None else now
    exposures = {}
    last_turn = {}
    turns_pattern = os.path.join(REPO, "logs", "*", "turns.jsonl")
    for path in sorted(glob.glob(turns_pattern)):
        slot = os.path.basename(os.path.dirname(path))
        if slot not in NAMES:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = str(rec.get("game_id") or "")
                ts = _number(rec.get("ts"))
                if gid and ts is not None:
                    key = (slot, gid)
                    last_turn[key] = max(last_turn.get(key, -math.inf), ts)
                exposure = _open_claim_exposure_turn(slot, rec)
                if exposure is None:
                    continue
                key, ts = exposure
                if key not in exposures or ts < exposures[key]:
                    exposures[key] = ts

    # A game can emit many counteroffers. Select its first exposure globally,
    # then apply the arm window, so a pre-window game cannot leak in through a
    # later in-window counteroffer.
    cohort = {key: ts for key, ts in exposures.items() if cut <= ts < end}

    latest = {}
    watermark = defaultdict(float)
    wanted_by_slot = defaultdict(set)
    for slot, gid in cohort:
        wanted_by_slot[slot].add(gid)

    # Process-exit finalisation appends results.jsonl. Read the complete file:
    # an eligible price exposure inside the window may have been backfilled with
    # an older collection timestamp, and exposure is already fixed by cohort.
    for slot, wanted in wanted_by_slot.items():
        path = os.path.join(REPO, "logs", slot, "results.jsonl")
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                fin = rec.get("final") or {}
                stamp = _number(rec.get("ts")) or 0.0
                watermark[slot] = max(watermark[slot], stamp)
                gid = str(rec.get("game_id") or fin.get("game_id") or "")
                if gid not in wanted:
                    continue
                _prefer_final(latest, (slot, gid), stamp, rec, fin)

    # The continuous collector writes games/<id>.json without appending the
    # legacy result stream.  Joining it is necessary for the close-rate veto;
    # otherwise collector-only no-deals would be selected out of the analysis.
    for slot in wanted_by_slot:
        games_dir = os.path.join(REPO, "logs", slot, "games")
        try:
            watermark[slot] = max(watermark[slot], os.path.getmtime(games_dir))
        except OSError:
            pass
    for (slot, gid), _exposure_ts in cohort.items():
        if os.path.basename(gid) != gid:
            continue
        path = os.path.join(REPO, "logs", slot, "games", f"{gid}.json")
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                record = json.load(fh)
        except (OSError, ValueError):
            continue
        fin = _game_record_final(record)
        try:
            stamp = os.path.getmtime(path)
        except OSError:
            stamp = 0.0
        _prefer_final(latest, (slot, gid), stamp, {"game_id": gid}, fin)

    for (slot, gid), exposure_ts in sorted(cohort.items()):
        key = (slot, gid)
        selected = latest.get(key)
        if selected is not None:
            _rank, rec, fin = selected
            row = _open_claim_row(slot, rec, fin)
            if row is not None:
                yield (*row, "terminal")
                continue
            status = str(fin.get("status") or "").strip().lower()
            outcome = str((fin.get("result") or {}).get("outcome") or "").strip().lower()
            awaiting_terminal = status in ("", "active") and outcome in ("", "active")
        else:
            awaiting_terminal = True

        # Missing results become abandonments only after the same calibrated
        # test used by orphan_watch: our last move is >6000s old (past the
        # measured 5700s maximum healthy gap) and this slot collected a later
        # outcome. The competition assigns such an abandonment percentile .05,
        # and it is a non-close. Fresh or schema-invalid outcomes stay explicit
        # and block promotion instead of being guessed away.
        last = last_turn.get(key, exposure_ts)
        aged = now - last > ORPHAN_COLD_SECONDS and last < watermark[slot]
        if awaiting_terminal and aged:
            yield slot, 0.05, gid, False, "abandoned"
        else:
            reason = "pending" if awaiting_terminal else "invalid-final"
            yield slot, None, gid, None, reason


def report_open_claim(rows, hours, since=None, until=None):
    """Report percentile and the close-rate veto for each recoverable hash arm."""
    arms = defaultdict(
        lambda: defaultdict(lambda: {
            "pct": [], "closed": [], "abandoned": 0, "pending": 0,
            "invalid": 0,
        }))
    for row in rows:
        slot, pct, gid, closed, *metadata = row
        resolution = (metadata[0] if metadata else
                      ("unresolved" if closed is None else "terminal"))
        arm = open_claim_arm(gid)
        if arm is None:
            continue
        if closed is None:
            field = "invalid" if resolution == "invalid-final" else "pending"
            arms[slot][arm][field] += 1
            continue
        if resolution == "abandoned":
            arms[slot][arm]["abandoned"] += 1
        if pct is not None:
            arms[slot][arm]["pct"].append(pct)
        arms[slot][arm]["closed"].append(float(bool(closed)))

    title = ("GLEE_NEGO_OPEN_CLAIM + GLEE_NEGO_CLAIM_FLOOR, "
             "complete-information negotiation only")
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("eligibility: complete_information=true, positive visible ZOPA, either "
          "seat/horizon, and at least one outgoing price")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-price exposure window: [{lower}, {upper})")
    else:
        print("scope --hours/--slots to an era where OPEN_CLAIM and/or CLAIM_FLOOR "
              "was armed; for a finished arm, use exact first-price "
              "--since/--until bounds")
    if not arms:
        print("no eligible complete-information price exposures in the window")
        return 1
    print(f"{'agent':9} {'arm':9} {'mean pct':>9} {'n pct':>7} "
          f"{'close rate':>11} {'n outcome':>9} {'abnd':>6} {'pend':>6} "
          f"{'badfin':>6}")

    pooled = defaultdict(lambda: {
        "pct": [], "closed": [], "abandoned": 0, "pending": 0, "invalid": 0,
    })
    for slot, assigned in sorted(arms.items()):
        for arm in ("control", "candidate"):
            stats = assigned.get(arm)
            if not stats:
                continue
            pooled[arm]["pct"].extend(stats["pct"])
            pooled[arm]["closed"].extend(stats["closed"])
            pooled[arm]["abandoned"] += stats["abandoned"]
            pooled[arm]["pending"] += stats["pending"]
            pooled[arm]["invalid"] += stats["invalid"]
            mean_pct = (sum(stats["pct"]) / len(stats["pct"])
                        if stats["pct"] else None)
            close_rate = (sum(stats["closed"]) / len(stats["closed"])
                          if stats["closed"] else None)
            pct_text = f"{mean_pct:.4f}" if mean_pct is not None else "n/a"
            close_text = f"{close_rate:.1%}" if close_rate is not None else "n/a"
            print(f"{NAMES.get(slot, slot):9} {arm:9} {pct_text:>9} "
                  f"{len(stats['pct']):7d} {close_text:>11} "
                  f"{len(stats['closed']):9d} {stats['abandoned']:6d} "
                  f"{stats['pending']:6d} {stats['invalid']:6d}")

    for arm in ("control", "candidate"):
        stats = pooled.get(arm)
        if not stats:
            continue
        mean_pct = (sum(stats["pct"]) / len(stats["pct"])
                    if stats["pct"] else None)
        close_rate = (sum(stats["closed"]) / len(stats["closed"])
                      if stats["closed"] else None)
        pct_text = f"{mean_pct:.4f}" if mean_pct is not None else "n/a"
        close_text = f"{close_rate:.1%}" if close_rate is not None else "n/a"
        print(f"{'POOLED':9} {arm:9} {pct_text:>9} {len(stats['pct']):7d} "
              f"{close_text:>11} {len(stats['closed']):9d} "
              f"{stats['abandoned']:6d} {stats['pending']:6d} "
              f"{stats['invalid']:6d}")

    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    if unresolved:
        bounds = []
        for arm in ("control", "candidate"):
            stats = pooled.get(arm)
            if not stats:
                continue
            arm_unresolved = stats["pending"] + stats["invalid"]
            observed = len(stats["closed"])
            total = observed + arm_unresolved
            successes = sum(stats["closed"])
            bounds.append(
                f"{arm} [{successes / total:.1%}, "
                f"{(successes + arm_unresolved) / total:.1%}]")
        pending = sum(stats["pending"] for stats in pooled.values())
        invalid = sum(stats["invalid"] for stats in pooled.values())
        print(f"INCOMPLETE OUTCOMES: pending={pending}, invalid-final={invalid}; "
              "close-rate bounds "
              f"{'; '.join(bounds)}")
        print("the close-rate veto is not promotion-grade until unresolved=0")

    control = pooled.get("control")
    candidate = pooled.get("candidate")
    if control and candidate and control["closed"] and candidate["closed"]:
        close_control = sum(control["closed"]) / len(control["closed"])
        close_candidate = sum(candidate["closed"]) / len(candidate["closed"])
        close_delta = close_candidate - close_control
        if control["pct"] and candidate["pct"]:
            pct_delta = (sum(candidate["pct"]) / len(candidate["pct"])
                         - sum(control["pct"]) / len(control["pct"]))
            print(f"pooled candidate-control: mean percentile {pct_delta:+.4f}; "
                  f"close rate {close_delta:+.1%}")
        else:
            print(f"pooled candidate-control close rate: {close_delta:+.1%}")
        if close_delta < 0.0:
            print("CLOSE-RATE VETO (terminal point estimate): candidate closes "
                  "fewer eligible games; do not promote it on percentile alone")
    return 0


def report_barg_msg(rows, hours):
    """Report the primary silence/text contrast and each assigned text register."""
    arms = defaultdict(lambda: defaultdict(list))
    for slot, _ts, fam, pct, gid, messages_allowed in rows:
        if fam != "bargaining" or messages_allowed is not True or not gid:
            continue
        arm = bargaining_arm(gid)
        if arm is not None:
            arms[slot][arm].append(pct)

    print(f"GLEE_BARG_MSG, bargaining only, last {hours:g}h")
    print("eligibility: messages_allowed=true; scope --hours/--slots to an era "
          "where GLEE_BARG_MSG was armed")
    print("primary contrast: B0 assigned silence vs pooled B1-B3 assigned text")
    print(f"{'agent':9} {'silence':>20} {'text':>20} {'delta':>20}")
    pooled = defaultdict(list)
    for slot, assigned in sorted(arms.items()):
        for arm, values in assigned.items():
            pooled[arm].extend(values)
        silent = assigned.get("B0", [])
        text_arms = [pct for arm in BARG_ARMS[1:] for pct in assigned.get(arm, [])]
        c, _clo, chi, cn = mean_ci(silent)
        d, _dlo, dhi, dn = mean_ci(text_arms)
        if c is None or d is None or cn < 30 or dn < 30:
            continue
        se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
        print(f"{NAMES[slot]:9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
              f"{d - c:+.4f} +/-{1.96*se:.4f}")

    silent = pooled.get("B0", [])
    text_arms = [pct for arm in BARG_ARMS[1:] for pct in pooled.get(arm, [])]
    c, _clo, chi, cn = mean_ci(silent)
    d, _dlo, dhi, dn = mean_ci(text_arms)
    if c is not None and d is not None and cn and dn:
        se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
        delta = d - c
        verdict = ("TEXT BETTER" if delta > 1.96 * se else
                   "TEXT WORSE" if delta < -1.96 * se else
                   "cannot distinguish yet")
        print(f"{'POOLED':9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
              f"{delta:+.4f} +/-{1.96*se:.4f}   -> {verdict}")

    print("\nexploratory register contrasts against B0 silence")
    print(f"{'arm':9} {'silence':>20} {'register':>20} {'delta':>20}")
    for arm in BARG_ARMS[1:]:
        d, _dlo, dhi, dn = mean_ci(pooled.get(arm, []))
        if c is None or d is None or not cn or not dn:
            continue
        se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
        print(f"{arm:9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
              f"{d - c:+.4f} +/-{1.96*se:.4f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--split", type=float, default=None,
                    help="unix ts; compare games before vs after it")
    ap.add_argument("--since", type=float, default=None,
                    help="inclusive first-price unix timestamp for --ab open-claim; "
                         "overrides --hours as its lower bound")
    ap.add_argument("--until", type=float, default=None,
                    help="exclusive first-price unix timestamp for --ab open-claim")
    ap.add_argument("--slots", default="")
    ap.add_argument("--ab", nargs="?", const="zopa",
                    choices=("zopa", "rank-price", "open-claim", "barg-msg"),
                    help="split games by a recoverable hash arm; bare --ab "
                         "keeps the legacy GLEE_NEGO_ZOPA_AB report")
    args = ap.parse_args()
    keep = {s.strip() for s in args.slots.split(",") if s.strip()}

    if args.ab == "open-claim":
        if (args.since is not None and args.until is not None
                and args.until <= args.since):
            ap.error("--until must be greater than --since")
        claim_rows = [r for r in open_claim_games(
            args.hours, since=args.since, until=args.until)
            if not keep or r[0] in keep]
        return report_open_claim(
            claim_rows, args.hours, since=args.since, until=args.until)

    rows = [r for r in games(args.hours) if not keep or r[0] in keep]

    if args.ab:
        if args.ab == "barg-msg":
            report_barg_msg(rows, args.hours)
            return 0
        # Recompute the arm from the game id -- the SAME pure function the agent
        # used. Nothing is logged and nothing can drift out of sync.
        if args.ab == "rank-price":
            label, salt = "GLEE_NEGO_RANK_PRICE_AB", "rank_price_ab|"
        else:
            label, salt = "GLEE_NEGO_ZOPA_AB", "zopa_ab|"
        arms = defaultdict(lambda: defaultdict(list))
        for slot, ts, fam, pct, gid, _messages_allowed in rows:
            if fam != "negotiation" or not gid:
                continue
            bit = int(hashlib.sha256((salt + str(gid)).encode()).hexdigest(), 16) & 1
            arms[slot]["candidate" if bit else "control"].append(pct)
        print(f"{label}, negotiation only, last {args.hours:g}h")
        print(f"{'agent':9} {'control':>20} {'candidate':>20} {'delta':>20}")
        pooled = defaultdict(list)
        for slot, a in sorted(arms.items()):
            for k, v in a.items():
                pooled[k].extend(v)
            c, clo, chi, cn = mean_ci(a.get("control", []))
            d, dlo, dhi, dn = mean_ci(a.get("candidate", []))
            if c is None or d is None or cn < 30 or dn < 30:
                continue
            se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
            print(f"{NAMES[slot]:9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
                  f"{d - c:+.4f} +/-{1.96*se:.4f}")
        c, clo, chi, cn = mean_ci(pooled.get("control", []))
        d, dlo, dhi, dn = mean_ci(pooled.get("candidate", []))
        if c is not None and d is not None and cn and dn:
            se = math.sqrt(((chi - c) / 1.96) ** 2 + ((dhi - d) / 1.96) ** 2)
            delta = d - c
            verdict = ("CANDIDATE BETTER" if delta > 1.96 * se else
                       "CANDIDATE WORSE" if delta < -1.96 * se else
                       "cannot distinguish yet")
            print(f"{'POOLED':9} {c:.4f} (n={cn:>5}) {d:.4f} (n={dn:>5}) "
                  f"{delta:+.4f} +/-{1.96*se:.4f}   -> {verdict}")
            need = (1.96 * 0.30 / max(abs(delta), 0.004)) ** 2 * 2
            print(f"  games/arm for a decisive read at this effect size: ~{need:.0f}")
        return 0
    if not rows:
        print("no scoreable games in window")
        return 1

    if args.split:
        buckets = defaultdict(lambda: defaultdict(list))
        for slot, ts, fam, pct, _gid, _messages_allowed in rows:
            arm = "after" if ts >= args.split else "before"
            buckets[(slot, fam)][arm].append(pct)
        print(f"{'agent':9} {'family':12} {'before':>22} {'after':>22} {'delta':>18}")
        for (slot, fam), arms in sorted(buckets.items()):
            b, blo, bhi, bn = mean_ci(arms.get("before", []))
            a, alo, ahi, an = mean_ci(arms.get("after", []))
            if b is None or a is None or bn < 30 or an < 30:
                continue
            # difference of independent means
            d = a - b
            se = math.sqrt(((bhi - b) / 1.96) ** 2 + ((ahi - a) / 1.96) ** 2)
            mark = "  *" if abs(d) > 1.96 * se else ""
            print(f"{NAMES[slot]:9} {fam:12} {b:.4f} (n={bn:>5}) {a:.4f} (n={an:>5}) "
                  f"{d:+.4f} +/-{1.96*se:.4f}{mark}")
        return 0

    agg = defaultdict(list)
    for slot, ts, fam, pct, _gid, _messages_allowed in rows:
        agg[(slot, fam)].append(pct)
        agg[(slot, "ALL")].append(pct)
    print(f"our REALISED percentile, last {args.hours:g}h "
          f"(0.5 = the field's median; the rating tracks this)")
    print(f"{'agent':9} {'family':12} {'mean pct':>9} {'95% CI':>18} {'n':>7} {'~rating':>9}")
    for (slot, fam), xs in sorted(agg.items()):
        m, lo, hi, n = mean_ci(xs)
        if n < 20:
            continue
        rating = 2000 + 8000 * (m - 0.5)
        print(f"{NAMES[slot]:9} {fam:12} {m:>9.4f} [{lo:.4f},{hi:.4f}] {n:>7} {rating:>9.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
