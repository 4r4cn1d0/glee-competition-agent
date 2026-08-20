#!/usr/bin/env python3
"""Fit a behavioural profile per named opponent from our own game logs.

Half of GLEE games disclose the opponent's name, and the pool is concentrated:
121 distinct opponents across ~12k named games, with 83 of them seen 400+ rounds.
An LLM opponent sees one game at a time and cannot remember the previous twenty-
nine; we can. That asymmetry is the point of this file.

What it fits, per opponent, per family:

  bargaining   the acceptance threshold -- the smallest share of the pot they
               will take. Measured thresholds run from 0.130 to 0.500, and we
               currently offer every one of them the same ~0.50, so the spread is
               pure forgone value.

  negotiation  their opening anchor relative to their own value, and how fast
               they concede across rounds.

  persuasion   as buyer, how often they buy and how much a recommendation moves
               them; as seller, how honest their recommendations turn out to be.

Written to models/opponent_profiles.json for the live strategy to read. This is
an OFFLINE job -- it walks ~1.2GB of logs, which is far too slow to do inside a
120-second turn.

Every entry carries its own sample size, and the consumer is expected to refuse
to act on thin ones: a profile fitted on six observations is worse than no
profile, because it replaces a policy we have measured with a guess we have not.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "models", "opponent_profiles.json")

#: Below this many labelled observations a fitted value is not reported at all.
MIN_OBS = 12
#: An acceptance threshold is the lowest share at or above which this fraction of
#: offers were accepted. Set high: acting on the threshold means offering less,
#: and a wrong guess costs the deal.
ACCEPT_RATE = 0.70


def _iter_finals():
    """Every completed game we have a full final state for."""
    seen = set()
    for path in glob.glob(os.path.join(REPO, "logs", "*", "results.jsonl")):
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
                if final.get("game_state"):
                    yield final
    # The per-game files carry games that results.jsonl has since rotated past.
    for path in glob.glob(os.path.join(REPO, "logs", "*", "games", "*.json")):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                rec = json.load(fh)
        except (ValueError, OSError):
            continue
        gid = rec.get("game_id")
        if gid in seen:
            continue
        seen.add(gid)
        if rec.get("history"):
            yield {"game_family": rec.get("game_family"),
                   "your_player": rec.get("your_player"),
                   "opponent": rec.get("opponent"),
                   "result": rec.get("result") or {},
                   "game_state": {"history": rec.get("history"),
                                  **(rec.get("config") or {})}}


def _opponent_name(final: dict):
    opp = final.get("opponent")
    if isinstance(opp, dict):
        name = opp.get("name")
        return name if name else None
    return None


def _threshold(points):
    """Lowest share we have actually SEEN this opponent accept, above which they
    keep accepting at >=ACCEPT_RATE. Returns (threshold, highest_rejected_below).

    Two traps here, both of which produced a threshold of 0.000 -- i.e. "offer
    them nothing" -- for opponents that reject everything at zero.

    First, candidates must be distinct share VALUES, not list indices: slicing a
    sorted list splits ties and quietly drops offers at the candidate share from
    its own denominator.

    Second, and less obvious, the candidate must be a share we have observed them
    ACCEPT. Opponents are typically offered either near-nothing or near-half and
    little in between, so the true threshold sits in an unobserved gap. Scanning
    every float in the data lets a value inside that gap -- or, with float noise
    around zero, a value that merely looks like zero -- satisfy the test on the
    strength of the accepted offers far above it. Reporting the lowest ACCEPTED
    observation instead is conservative: it can understate how greedy we could be,
    but it never invents a threshold in a region we have never tested.

    The second return value is the highest share we have seen REJECTED below that
    threshold, so a consumer can see how wide the untested gap is.
    """
    if not points:
        return None, None
    points = sorted(points)
    accepted_shares = sorted({s for s, ok in points if ok})
    for share in accepted_shares:
        above = [ok for s, ok in points if s >= share - 1e-12]
        if len(above) >= 6 and sum(above) / len(above) >= ACCEPT_RATE:
            below = [s for s, ok in points if not ok and s < share - 1e-12]
            return round(share, 4), (round(max(below), 4) if below else None)
    return None, None


def build() -> dict:
    barg = defaultdict(list)      # name -> [(share_to_them, accepted)]
    nego_anchor = defaultdict(list)
    nego_close = defaultdict(lambda: [0, 0])
    pers_buy = defaultdict(lambda: [0, 0])
    pers_honest = defaultdict(lambda: [0, 0])
    games = defaultdict(int)

    for final in _iter_finals():
        name = _opponent_name(final)
        if not name:
            continue
        fam = final.get("game_family")
        gs = final.get("game_state") or {}
        me = final.get("your_player")
        if not me:
            continue
        them = "player_2" if me == "player_1" else "player_1"
        history = gs.get("history") or []
        games[name] += 1

        if fam == "bargaining":
            money = gs.get("money_to_divide")
            if not money:
                continue
            for rnd in history:
                offer = rnd.get("offer") or {}
                if offer.get("proposer") != me:
                    continue          # only offers WE made, labelled by THEIR reply
                share = offer.get(f"{them}_gain")
                decision = (rnd.get("decision") or "").lower()
                if share is None or decision not in ("accept", "reject", "walkaway"):
                    continue
                barg[name].append((share / money, decision == "accept"))

        elif fam == "negotiation":
            their_value = gs.get(f"{them}_value")
            for rnd in history:
                offer = rnd.get("offer") or {}
                if offer.get("from_player") != them:
                    continue
                price = offer.get("price")
                if price is None:
                    continue
                if their_value:
                    nego_anchor[name].append(price / their_value)
            counts = nego_close[name]
            counts[1] += 1
            if (final.get("result") or {}).get("outcome") == "agreement":
                counts[0] += 1

        elif fam == "persuasion":
            for rnd in history:
                msg = rnd.get("seller_message")
                decision = rnd.get("buyer_decision")
                quality = rnd.get("quality")
                if gs.get(f"{them}_role") == "buyer" and decision is not None:
                    counts = pers_buy[name]
                    counts[1] += 1
                    if str(decision).lower() in ("yes", "buy", "true"):
                        counts[0] += 1
                if gs.get(f"{them}_role") == "seller" and msg is not None and quality:
                    recommended = str(msg).lower() in ("yes", "true") or "recommend" in str(msg).lower()
                    if recommended:
                        counts = pers_honest[name]
                        counts[1] += 1
                        if str(quality).lower() == "high":
                            counts[0] += 1

    profiles = {}
    for name in sorted(games, key=lambda n: -games[n]):
        entry = {"games_observed": games[name]}
        pts = barg.get(name) or []
        if len(pts) >= MIN_OBS:
            thr, rejected_below = _threshold(pts)
            entry["bargaining"] = {
                "n": len(pts),
                "accept_rate": round(sum(1 for _, ok in pts if ok) / len(pts), 4),
                "accept_threshold": thr,
                "highest_rejected_below": rejected_below,
            }
        anchors = nego_anchor.get(name) or []
        closed = nego_close.get(name)
        if len(anchors) >= MIN_OBS or (closed and closed[1] >= MIN_OBS):
            entry["negotiation"] = {
                "n_offers": len(anchors),
                "median_price_over_their_value":
                    round(sorted(anchors)[len(anchors) // 2], 4) if anchors else None,
                "n_games": closed[1] if closed else 0,
                "close_rate": round(closed[0] / closed[1], 4) if closed and closed[1] else None,
            }
        buy = pers_buy.get(name)
        honest = pers_honest.get(name)
        block = {}
        if buy and buy[1] >= MIN_OBS:
            block["as_buyer_n"] = buy[1]
            block["as_buyer_buy_rate"] = round(buy[0] / buy[1], 4)
        if honest and honest[1] >= MIN_OBS:
            block["as_seller_n"] = honest[1]
            block["as_seller_truth_rate"] = round(honest[0] / honest[1], 4)
        if block:
            entry["persuasion"] = block
        if len(entry) > 1:
            profiles[name] = entry
    return profiles


def main() -> int:
    profiles = build()
    doc = {
        "_schema": "glee.opponent_profiles/v1",
        "_what": "Per-opponent behaviour fitted from our own logged games. Consumers "
                 "MUST check the per-field n before acting: a thin profile replaces a "
                 "measured policy with a guess.",
        "_min_obs": MIN_OBS,
        "_accept_rate": ACCEPT_RATE,
        "profiles": profiles,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    os.replace(tmp, OUT)

    withb = [n for n, p in profiles.items()
             if (p.get("bargaining") or {}).get("accept_threshold") is not None]
    print(f"{len(profiles)} opponents profiled -> {os.path.relpath(OUT, REPO)}")
    print(f"  with a fitted bargaining threshold: {len(withb)}")
    ts = sorted((profiles[n]["bargaining"]["accept_threshold"], n) for n in withb)
    print(f"    {'opponent':25s}{'threshold':>10s}{'rejected below':>16s}{'n':>6s}{'accepts':>9s}")
    for t, n in ts[:14]:
        b = profiles[n]["bargaining"]
        rb = b.get("highest_rejected_below")
        print(f"    {n[:24]:25s}{t:>10.3f}{(f'{rb:.3f}' if rb is not None else '-'):>16s}"
              f"{b['n']:>6d}{b['accept_rate']:>9.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
