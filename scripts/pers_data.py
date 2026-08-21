#!/usr/bin/env python3
"""Load every logged persuasion SELLER game as a flat round table.

Reads the LIVE logs of the main checkout by absolute path (read-only): the
per-game files carry the full history and config, results.jsonl carries the
timestamps.  Everything downstream in the v3 recalibration -- the selection
diagnosis, the credibility-state buyer fit, and the offline replay -- reads
its rounds through this one loader so they cannot disagree about what a
"round" is.

A round record is what the SELLER knew when it moved plus what happened:
  mode, p, ratio, round index, true quality, our recommendation,
  lies the buyer had CAUGHT so far, and -- the feature v1 omitted --
  the recommendation record the buyer had SEEN so far.
"""
from __future__ import annotations

import glob
import json
import os

LIVE = os.environ.get("GLEE_LIVE_REPO", "/Users/spiderishi/Coding/GLEE Competition")
RATIOS = (1.2, 1.25, 2.0, 3.0, 4.0)


def rec_of(msg):
    """True/False/None: did this seller message read as a recommendation?"""
    if msg is None:
        return None
    if isinstance(msg, bool):
        return msg
    s = str(msg).strip().lower()
    if s in ("yes", "true"):
        return True
    if s in ("no", "false"):
        return False
    if "hold off" in s or "skip" in s or "pass" in s or "not recommend" in s:
        return False
    if "recommend" in s:
        return True
    return True if s else None


def pbin(p):
    return "lo" if p < 0.45 else ("mid" if p < 0.65 else "hi")


def rbin(v, price):
    return min(RATIOS, key=lambda g: abs(g - (v / price if price else 0)))


def _game_ts():
    """game_id -> unix ts, from the results.jsonl streams that carry one."""
    ts = {}
    for path in glob.glob(os.path.join(LIVE, "logs", "*", "results.jsonl")):
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                gid = d.get("game_id")
                if gid and d.get("ts"):
                    ts[gid] = d["ts"]
    return ts


def iter_games():
    """Yield (meta, history) for every completed persuasion game in our seller seat."""
    ts = _game_ts()
    seen = set()
    for path in glob.glob(os.path.join(LIVE, "logs", "*", "games", "*.json")):
        try:
            d = json.load(open(path, encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        gid = d.get("game_id")
        if not gid or gid in seen:
            continue
        seen.add(gid)
        if d.get("game_family") != "persuasion":
            continue
        me = d.get("your_player")
        cfg = d.get("config") or {}
        if not me or cfg.get(f"{me}_role") != "seller":
            continue
        p = cfg.get("p")
        price = cfg.get("product_price")
        v = cfg.get("v")
        if p is None or not price or v is None:
            continue
        hist = [h for h in (d.get("history") or []) if isinstance(h, dict)]
        if not hist:
            continue
        opp = d.get("opponent") or {}
        yield ({
            "game_id": gid,
            "agent": os.path.basename(os.path.dirname(os.path.dirname(path))),
            "ts": ts.get(gid),
            "mode": cfg.get("seller_message_type") or "text",
            "p": float(p), "v": float(v), "u": float(cfg.get("u") or 0.0),
            "price": float(price),
            "pb": pbin(float(p)), "rb": rbin(float(v), float(price)),
            "total_rounds": int(cfg.get("total_rounds") or len(hist)),
            "opponent": opp.get("name") if isinstance(opp, dict) else None,
            "payoff": d.get("our_payoff"),
        }, hist)


def iter_rounds(games=None):
    """Flatten to per-round records carrying the buyer-visible seller record."""
    for meta, hist in (games if games is not None else iter_games()):
        caught = 0        # lies the buyer CAUGHT (bought a recommended low)
        recs = 0          # recommendations the buyer has SEEN
        nos = 0           # declines the buyer has SEEN
        for i, h in enumerate(hist):
            rec = rec_of(h.get("seller_message"))
            if rec is None:
                continue
            quality = str(h.get("quality") or "").lower()
            bought = bool(h.get("bought"))
            yield {
                **meta,
                "i": i, "round": i + 1,
                "quality": quality, "rec": rec, "bought": bought,
                "caught": caught, "recs_seen": recs, "nos_seen": nos,
                "seen": recs + nos,
                # yes-rate the buyer has observed BEFORE this round
                "yes_rate": (recs / (recs + nos)) if (recs + nos) else None,
            }
            recs += 1 if rec else 0
            nos += 0 if rec else 1
            if bought and rec and quality == "low":
                caught += 1


if __name__ == "__main__":
    rs = list(iter_rounds())
    gs = {r["game_id"] for r in rs}
    print(f"{len(gs):,} seller games, {len(rs):,} rounds")
    from collections import Counter
    print("by agent:", Counter(r["agent"] for r in rs).most_common())
    print("modes:", Counter(r["mode"] for r in rs).most_common())
    tsd = [r["ts"] for r in rs if r["ts"]]
    print(f"rounds with ts: {len(tsd):,}")
