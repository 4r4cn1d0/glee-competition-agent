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
    python scripts/live_percentile.py --ab hidden-floor --since T0 --until T1
                                                     # hidden price floor + veto
    python scripts/live_percentile.py --ab hidden-policy --since T0 --until T1
                                       # hidden policy + zone-capture diagnostics
    python scripts/live_percentile.py --ab pers-selectivity --since T0 --until T1
                                  # buyer selectivity arm, first eligible decision
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
import statistics
import sys
import time
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from sim.percentile import percentile          # noqa: E402
from glee_agent.messages import BARG_ARMS, bargaining_arm  # noqa: E402
from glee_agent.pricing import infer_base       # noqa: E402
from glee_agent.strategies.persuasion import (  # noqa: E402
    _recommendation_signal as _pers_recommendation_signal,
    buyer_selectivity_assignment,
)
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


def hidden_floor_arm(gid) -> str | None:
    """Recover the hidden-information concession-floor arm used on the wire."""
    gid = str(gid or "")
    if not gid:
        return None
    bit = int(hashlib.sha256(("hidden_floor|" + gid).encode()).hexdigest(), 16) & 1
    return "candidate" if bit else "control"


def hidden_policy_arm(gid) -> str | None:
    """Recover the hidden-policy arm used by actions.py."""
    gid = str(gid or "")
    if not gid:
        return None
    bit = int(hashlib.sha256(("hidden_policy_v1|" + gid).encode()).hexdigest(), 16) & 1
    return "candidate" if bit else "control"


def pers_selectivity_arm(gid) -> str | None:
    """Recover the buyer-selectivity arm from the action path's pure helper."""
    treatment = buyer_selectivity_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


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


def _hidden_floor_static_eligible(seat: str, state: dict) -> bool:
    """Whether the wire guard can infer B from our value in a hidden game."""
    if seat not in ("player_1", "player_2"):
        return False
    if state.get("complete_information") is not False:
        return False
    if state.get(f"{seat}_role") not in ("seller", "buyer"):
        return False
    own_value = _number(state.get(f"{seat}_value"))
    return own_value is not None and infer_base(own_value) is not None


def _hidden_policy_signal(seat: str, state: dict) -> dict | None:
    """Return the arm's public own-type signal, or None when ineligible."""
    if not _hidden_floor_static_eligible(seat, state):
        return None
    max_rounds = state.get("max_rounds")
    horizon_number = _number(max_rounds)
    if max_rounds is not None and horizon_number == 1.0:
        return None
    role = state.get(f"{seat}_role")
    own_value = _number(state.get(f"{seat}_value"))
    base = infer_base(own_value)
    if own_value is None or base is None:
        return None
    own_mult = next(
        (m for m in (0.8, 1.0, 1.2, 1.5)
         if abs(own_value / base - m) <= 1e-6),
        None,
    )
    if own_mult is None:
        return None
    # Hidden opponent types are uniform on four points in the reconstructed
    # live grid.  Keep the literal mapping visible rather than disguising this
    # local empirical assumption as a formula from official documentation.
    seller_probability = {0.8: 0.75, 1.0: 0.50, 1.2: 0.25, 1.5: 0.0}
    buyer_probability = {0.8: 0.0, 1.0: 0.25, 1.2: 0.50, 1.5: 0.75}
    p_zopa = (seller_probability if role == "seller" else buyer_probability)[own_mult]
    if p_zopa <= 0.0:
        return None
    return {
        "role": role,
        "own_mult": own_mult,
        "p_zopa": p_zopa,
        "horizon": ("inf" if max_rounds is None else
                    str(int(horizon_number)) if horizon_number is not None else
                    "invalid"),
        "base": base,
        "own_value": own_value,
    }


def _pers_selectivity_signal(seat: str, state: dict) -> dict | None:
    """Return the pre-treatment buyer cell, or None outside the arm's scope.

    Eligibility is fixed from the first buyer decision and uses the low-quality
    value ``u`` explicitly: E[prior] = p*v + (1-p)*u.  It deliberately does not
    inspect history, recommendations, purchases, or eventual declines; doing so
    would turn the experiment's intent-to-treat cohort into a post-treatment
    subset.
    """
    if seat != "player_2":
        return None
    price = _number(state.get("product_price"))
    p = _number(state.get("p"))
    v = _number(state.get("v"))
    u = _number(state.get("u"))
    if None in (price, p, v, u):
        return None
    prior_value = p * v + (1.0 - p) * u
    value_scale = max(1.0, abs(price), abs(prior_value))
    prior_not_profitable = prior_value <= price + 1e-9 * value_scale
    if not (v > u and price > u and prior_not_profitable):
        return None
    return {
        "price": price,
        "p": p,
        "v": v,
        "u": u,
        "prior_value": prior_value,
        "seller_message_type": state.get("seller_message_type"),
        "total_rounds": _number(state.get("total_rounds")),
    }


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


def _hidden_floor_exposure_turn(slot: str, rec: dict):
    """Return a hidden-game outgoing-price exposure key and timestamp."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    if not gid or not _hidden_floor_static_eligible(seat, state):
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


def _hidden_policy_exposure_turn(slot: str, rec: dict):
    """Return a multi-round hidden-policy outgoing-price exposure."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _hidden_policy_signal(seat, state)
    if not gid or signal is None:
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    action = rec.get("action") or {}
    if not isinstance(action, dict) or "product_price" not in action:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    return (slot, gid), ts, signal


def _pers_selectivity_exposure_turn(slot: str, rec: dict):
    """Return the first eligible persuasion buyer-decision exposure."""
    if rec.get("game_family") != "persuasion":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _pers_selectivity_signal(seat, state)
    if not gid or signal is None:
        return None
    if rec.get("action_type") != "buyer_decision":
        return None
    if rec.get("phase") not in (None, "buyer_decision"):
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    action = rec.get("action") or {}
    decision = (str(action.get("decision") or "").strip().lower()
                if isinstance(action, dict) else "")
    if decision not in ("yes", "no"):
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    plan = rec.get("plan") or {}
    strike_arm = (plan.get("buyer_selectivity_strike_arm")
                  if isinstance(plan, dict) else None)
    if strike_arm in ("off", "no-strike", "strike"):
        # This is assigned before any seller behavior and is copied from the
        # action path instead of inferred from outcomes.  The reader can thus
        # estimate the main gate separately with and without the optional stop.
        signal["buyer_selectivity_strike_arm"] = strike_arm
    return (slot, gid), ts, signal


def _terminal_close(fin: dict) -> bool | None:
    """Return agreement/completion status, or None without a terminal outcome."""
    result = fin.get("result") or {}
    status = str(fin.get("status") or "").strip().lower()
    outcome = str(result.get("outcome") or "").strip().lower()
    if status == "active" or outcome == "active":
        return None
    if outcome in ("agreement", "completed"):
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


def _hidden_floor_row(slot: str, rec: dict, fin: dict):
    """Build one hidden-floor outcome, retaining unknown-CDF close results."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    if not gid or not _hidden_floor_static_eligible(seat, state):
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


def _result_payoff(result: dict, player: str, our_seat: str) -> float | None:
    """Return one seat's payoff from either server result schema."""
    value = _number(result.get(f"{player}_payoff"))
    if value is not None:
        return value
    fallback = "your_payoff" if player == our_seat else "opponent_payoff"
    return _number(result.get(fallback))


def _snap_hidden_mult(value: float, base: float) -> float | None:
    """Snap a reconstructed value to the four-point hidden grid."""
    ratio = value / base
    return next(
        (m for m in (0.8, 1.0, 1.2, 1.5)
         if abs(ratio - m) <= 1e-4),
        None,
    )


def _hidden_zone_diagnostics(seat: str, result: dict, closed: bool,
                             signal: dict) -> dict:
    """Reconstruct closed-deal zone share and its ITT contribution.

    In an agreement, seller payoff plus buyer payoff equals buyer value minus
    seller value regardless of closing price.  Positive-zone agreements expose
    our captured fraction of that span.  A non-close contributes zero to the
    intent-to-treat capture mean but has no conditional closed-deal share.  A
    zero- or negative-zone agreement also contributes zero and leaves the ratio
    undefined rather than manufacturing a division-by-zero score.
    """
    diagnostic = {
        "role": signal["role"],
        "own_mult": signal["own_mult"],
        "p_zopa": signal["p_zopa"],
        "horizon": signal["horizon"],
        "zone_share": None,
        "realized_capture": 0.0,
        "pair": None,
        "reconstruction_missing": False,
        "reconstruction_invalid": False,
        "nonpositive_zone": False,
    }
    if not closed:
        return diagnostic

    player_1 = _result_payoff(result, "player_1", seat)
    player_2 = _result_payoff(result, "player_2", seat)
    if player_1 is None or player_2 is None:
        diagnostic["realized_capture"] = None
        diagnostic["reconstruction_missing"] = True
        return diagnostic

    own_payoff = player_1 if seat == "player_1" else player_2
    span = player_1 + player_2
    base = signal["base"]
    own_value = signal["own_value"]
    if signal["role"] == "seller":
        seller_value, buyer_value = own_value, own_value + span
    else:
        seller_value, buyer_value = own_value - span, own_value
    seller_mult = _snap_hidden_mult(seller_value, base)
    buyer_mult = _snap_hidden_mult(buyer_value, base)
    if seller_mult is None or buyer_mult is None:
        diagnostic["realized_capture"] = None
        diagnostic["reconstruction_invalid"] = True
        return diagnostic
    diagnostic["pair"] = f"S{seller_mult:g}-B{buyer_mult:g}"

    if span > max(abs(base) * 1e-9, 1e-9):
        share = own_payoff / span
        diagnostic["zone_share"] = share
        diagnostic["realized_capture"] = share
    else:
        diagnostic["nonpositive_zone"] = True
    return diagnostic


def _hidden_policy_row(slot: str, rec: dict, fin: dict):
    """Build one policy outcome with own-signal and zone diagnostics."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _hidden_policy_signal(seat, state)
    if not gid or signal is None:
        return None

    closed = _terminal_close(fin)
    if closed is None:
        return None
    result = fin.get("result") or {}
    payoff_number = _result_payoff(result, seat, seat)
    pct = None
    if payoff_number is not None:
        pct = percentile("negotiation", dict(state), seat, payoff_number)
    diagnostic = _hidden_zone_diagnostics(seat, result, closed, signal)
    return slot, pct, str(gid), closed, diagnostic


def _pers_selectivity_history_metrics(history) -> dict:
    """Summarize realized buyer behavior without selecting on a decline."""
    entries = [entry for entry in history or [] if isinstance(entry, dict)]
    signals = [_pers_recommendation_signal(entry) for entry in entries]
    first_decline = next(
        (index for index, signal in enumerate(signals) if signal is False),
        len(entries),
    )
    purchases = sum(bool(entry.get("bought")) for entry in entries)
    return {
        "rounds": len(entries),
        "purchases": purchases,
        "purchase_rate": purchases / len(entries) if entries else None,
        "pre_decline_buys": sum(
            bool(entry.get("bought")) for entry in entries[:first_decline]),
        "bought_lows": sum(
            bool(entry.get("bought"))
            and str(entry.get("quality") or "").strip().lower() == "low"
            for entry in entries
        ),
        "bought_highs": sum(
            bool(entry.get("bought"))
            and str(entry.get("quality") or "").strip().lower() == "high"
            for entry in entries
        ),
        "decline_count": sum(signal is False for signal in signals),
    }


def _pers_selectivity_row(slot: str, rec: dict, fin: dict):
    """Build one terminal persuasion buyer outcome and mechanism diagnostics."""
    if fin.get("game_family") != "persuasion":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    if not gid or seat != "player_2":
        return None

    completed = _terminal_close(fin)
    if completed is None:
        return None
    result = fin.get("result") or {}
    payoff_number = _result_payoff(result, seat, seat)
    pct = None
    if payoff_number is not None:
        pct = percentile("persuasion", dict(state), seat, payoff_number)

    diagnostic = _pers_selectivity_history_metrics(state.get("history"))
    price = _number(state.get("product_price"))
    diagnostic.update({
        "payoff": payoff_number,
        "payoff_per_price": (
            payoff_number / price
            if payoff_number is not None and price not in (None, 0.0)
            else None
        ),
    })
    if price is not None:
        diagnostic["price"] = price
    return slot, pct, str(gid), completed, diagnostic


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


def _price_arm_games(hours, exposure_turn, outcome_row, since=None, until=None):
    """Yield a first-price exposure cohort with its terminal outcomes.

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
    gid_slots = defaultdict(set)
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
                # Record fleet participation before arm eligibility or CLI slot
                # filtering.  The marker survives into yielded policy rows, so
                # selecting one slot cannot disguise a fleet-vs-fleet game as
                # an independent observation.
                if gid:
                    gid_slots[gid].add(slot)
                if gid and ts is not None:
                    key = (slot, gid)
                    last_turn[key] = max(last_turn.get(key, -math.inf), ts)
                exposure = exposure_turn(slot, rec)
                if exposure is None:
                    continue
                key, ts, *details = exposure
                metadata = (details[0]
                            if details and isinstance(details[0], dict) else {})
                if key not in exposures or ts < exposures[key][0]:
                    exposures[key] = (ts, metadata)

    # A game can emit many counteroffers. Select its first exposure globally,
    # then apply the arm window, so a pre-window game cannot leak in through a
    # later in-window counteroffer.
    cohort = {key: exposure for key, exposure in exposures.items()
              if cut <= exposure[0] < end}

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
    for (slot, gid), (_exposure_ts, _metadata) in cohort.items():
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

    for (slot, gid), (exposure_ts, exposure_metadata) in sorted(cohort.items()):
        key = (slot, gid)
        metadata = dict(exposure_metadata)
        if metadata:
            metadata["fleet_slots"] = tuple(sorted(gid_slots.get(gid, {slot})))
        selected = latest.get(key)
        if selected is not None:
            _rank, rec, fin = selected
            row = outcome_row(slot, rec, fin)
            if row is not None:
                if metadata:
                    if isinstance(row[-1], dict):
                        row = (*row[:-1], {**metadata, **row[-1]})
                    else:
                        row = (*row, metadata)
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
            if metadata:
                yield slot, 0.05, gid, False, metadata, "abandoned"
            else:
                yield slot, 0.05, gid, False, "abandoned"
        else:
            reason = "pending" if awaiting_terminal else "invalid-final"
            if metadata:
                yield slot, None, gid, None, metadata, reason
            else:
                yield slot, None, gid, None, reason


def open_claim_games(hours, since=None, until=None):
    """Yield exposed complete-information claim-arm games and outcomes."""
    yield from _price_arm_games(
        hours, _open_claim_exposure_turn, _open_claim_row,
        since=since, until=until)


def hidden_floor_games(hours, since=None, until=None):
    """Yield exposed hidden-information floor-arm games and outcomes."""
    yield from _price_arm_games(
        hours, _hidden_floor_exposure_turn, _hidden_floor_row,
        since=since, until=until)


def hidden_policy_games(hours, since=None, until=None):
    """Yield exposed hidden-policy games with reconstructed-zone diagnostics."""
    yield from _price_arm_games(
        hours, _hidden_policy_exposure_turn, _hidden_policy_row,
        since=since, until=until)


def pers_selectivity_games(hours, since=None, until=None):
    """Yield the first-eligible-decision buyer-selectivity ITT cohort."""
    yield from _price_arm_games(
        hours, _pers_selectivity_exposure_turn, _pers_selectivity_row,
        since=since, until=until)


def _quantile(values, probability):
    """Linear-interpolated quantile for a non-empty finite sequence."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _delta_ci(candidate, control):
    """Difference of independent means with a normal 95% interval."""
    if not candidate or not control:
        return None, None, None
    difference = statistics.mean(candidate) - statistics.mean(control)
    if len(candidate) < 2 or len(control) < 2:
        return difference, None, None
    candidate_var = statistics.variance(candidate)
    control_var = statistics.variance(control)
    half = 1.96 * math.sqrt(
        candidate_var / len(candidate) + control_var / len(control))
    return difference, difference - half, difference + half


def _empty_hidden_policy_stats():
    return {
        "pct": [], "closed": [], "share": [], "capture": [],
        "pairs": Counter(), "missing": 0, "abandoned": 0,
        "offgrid": 0, "nonpositive": 0, "pending": 0, "invalid": 0,
    }


def _hidden_policy_observations(rows):
    """Normalize terminal, abandoned, and unresolved price-cohort rows."""
    observations = []
    for row in rows:
        slot, pct, gid, closed, *metadata = row
        arm = hidden_policy_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal",
        )
        observations.append({
            "slot": slot, "pct": pct, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic,
            "resolution": resolution,
        })
    return observations


def _summarize_hidden_policy(observations):
    stats = _empty_hidden_policy_stats()
    for observation in observations:
        closed = observation["closed"]
        resolution = observation["resolution"]
        if closed is None:
            field = "invalid" if resolution == "invalid-final" else "pending"
            stats[field] += 1
            continue
        if resolution == "abandoned":
            stats["abandoned"] += 1
        if observation["pct"] is not None:
            stats["pct"].append(observation["pct"])
        stats["closed"].append(float(bool(closed)))

        diagnostic = observation["diagnostic"]
        capture = diagnostic.get("realized_capture")
        if resolution == "abandoned":
            capture = 0.0
        if capture is not None:
            stats["capture"].append(capture)
        share = diagnostic.get("zone_share")
        if share is not None:
            stats["share"].append(share)
        pair = diagnostic.get("pair")
        if pair:
            stats["pairs"][pair] += 1
        if diagnostic.get("reconstruction_missing"):
            stats["missing"] += 1
        if diagnostic.get("reconstruction_invalid"):
            stats["offgrid"] += 1
        if diagnostic.get("nonpositive_zone"):
            stats["nonpositive"] += 1
    return stats


def _mean_ci_text(values, *, percent=False):
    mean, low, high, count = mean_ci(values)
    if mean is None:
        return "n/a", count
    if percent:
        low, high = max(0.0, low), min(1.0, high)
        return f"{mean:.1%} [{low:.1%},{high:.1%}]", count
    return f"{mean:.4f} [{low:.4f},{high:.4f}]", count


def _share_text(values):
    if not values:
        return "n/a", 0
    median = statistics.median(values)
    q1, q3 = _quantile(values, 0.25), _quantile(values, 0.75)
    return f"{median:.3f} [{q1:.3f},{q3:.3f}]", len(values)


def _print_hidden_policy_line(label, arm, stats):
    pct, n_pct = _mean_ci_text(stats["pct"])
    close, n_outcome = _mean_ci_text(stats["closed"], percent=True)
    share, n_share = _share_text(stats["share"])
    capture, n_capture = _mean_ci_text(stats["capture"])
    print(
        f"{label:9} {arm:9} pct={pct} n={n_pct}; "
        f"close={close} n={n_outcome}; closed-zone-share median[IQR]="
        f"{share} n={n_share}; zone-capture-ITT={capture} n={n_capture}; "
        f"missing={stats['missing']} offgrid={stats['offgrid']} "
        f"nonpos={stats['nonpositive']} abnd={stats['abandoned']} "
        f"pend={stats['pending']} badfin={stats['invalid']}"
    )


def _print_delta(label, candidate, control, *, percent=False):
    delta, low, high = _delta_ci(candidate, control)
    if delta is None:
        print(f"  {label}: n/a")
        return
    if low is None:
        suffix = "95% CI unavailable (n<2 in an arm)"
    elif percent:
        suffix = f"95% CI [{low:+.1%},{high:+.1%}]"
    else:
        suffix = f"95% CI [{low:+.4f},{high:+.4f}]"
    value = f"{delta:+.1%}" if percent else f"{delta:+.4f}"
    print(f"  {label}: {value}; {suffix}")


def report_hidden_policy(rows, hours, since=None, until=None):
    """Report the hidden-policy ITT experiment and mechanism diagnostics."""
    observations = _hidden_policy_observations(rows)
    title = "GLEE_NEGO_HIDDEN_POLICY_V1, hidden multi-round negotiation only"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("eligibility: complete_information=false, multi-round, supported own "
          "grid value, positive prior P(ZOPA), and at least one outgoing price")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-price exposure window: [{lower}, {upper})")
    else:
        print("scope --hours/--slots to the exact armed era; for a finished arm, "
              "use exact first-price --since/--until bounds")
    if not observations:
        print("no eligible hidden-policy price exposures in the window")
        return 1

    by_slot_arm = defaultdict(list)
    gid_slots = defaultdict(set)
    for observation in observations:
        by_slot_arm[(observation["slot"], observation["arm"])].append(observation)
        recorded_slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(recorded_slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(recorded_slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    duplicate_gids = {gid for gid, slots in gid_slots.items() if len(slots) > 1}

    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        _print_hidden_policy_line(
            NAMES.get(slot, slot), arm, _summarize_hidden_policy(assigned))

    # Two fleet seats in the same game have coupled outcomes and, if both are
    # armed, coupled behavior.  Keep them visible per agent but remove them from
    # the pooled independent-arm estimate instead of double-counting self-play.
    pooled_observations = [
        observation for observation in observations
        if observation["gid"] not in duplicate_gids
    ]
    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [observation for observation in pooled_observations
                    if observation["arm"] == arm]
        if assigned:
            pooled[arm] = _summarize_hidden_policy(assigned)
            _print_hidden_policy_line("POOLED", arm, pooled[arm])
    print(f"pooled dependence guard: excluded {len(duplicate_gids)} game id(s) "
          "observed in multiple fleet slots")

    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("mean percentile", candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)
        _print_delta("mean reconstructed-zone capture",
                     candidate["capture"], control["capture"])
        if candidate["share"] and control["share"]:
            share_delta = (statistics.median(candidate["share"])
                           - statistics.median(control["share"]))
            print(f"  conditional median closed-zone share: {share_delta:+.3f} "
                  "(descriptive; selected on closing)")

    print("closed-zone share is conditional on agreement and cannot justify "
          "promotion without percentile, close rate, and zone-capture-ITT")

    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    missing = sum(stats["missing"] for stats in pooled.values())
    offgrid = sum(stats["offgrid"] for stats in pooled.values())
    nonpositive = sum(stats["nonpositive"] for stats in pooled.values())
    if unresolved:
        print(f"INCOMPLETE OUTCOMES: {unresolved}; promotion is blocked until "
              "pending and invalid-final outcomes resolve")
    if missing:
        print(f"MISSING RECONSTRUCTION: {missing} closed outcome(s) lack both "
              "seat payoffs; zone metrics are not promotion-grade")
    if offgrid:
        print(f"OFF-GRID RECONSTRUCTION: {offgrid} closed outcome(s) imply a "
              "value outside the reconstructed support; zone metrics are not "
              "promotion-grade")
    if nonpositive:
        print(f"UNDEFINED CLOSED SHARE: {nonpositive} agreement(s) reconstruct "
              "a zero/negative zone; each contributes zero to capture-ITT and "
              "is excluded from the conditional share ratio")

    pair_counts = {arm: stats["pairs"] for arm, stats in pooled.items()}
    if any(pair_counts.values()):
        print("reconstructed closed-pair composition (selection diagnostic):")
        for arm in ("control", "candidate"):
            pairs = pair_counts.get(arm)
            if pairs:
                rendered = ", ".join(f"{pair}={count}"
                                     for pair, count in sorted(pairs.items()))
                print(f"  {arm}: {rendered}")

    strata = defaultdict(list)
    for observation in pooled_observations:
        diagnostic = observation["diagnostic"]
        if not all(key in diagnostic for key in
                   ("role", "own_mult", "p_zopa", "horizon")):
            continue
        key = (diagnostic["role"], diagnostic["own_mult"],
               diagnostic["p_zopa"], diagnostic["horizon"],
               observation["arm"])
        strata[key].append(observation)
    if strata:
        print("pooled own-signal strata:")
        print("  role   own  P(ZOPA) horizon arm       n  close  med-share  capture")
        for (role, own_mult, p_zopa, horizon, arm), assigned in sorted(strata.items()):
            stats = _summarize_hidden_policy(assigned)
            close = (statistics.mean(stats["closed"])
                     if stats["closed"] else math.nan)
            share = (statistics.median(stats["share"])
                     if stats["share"] else math.nan)
            capture = (statistics.mean(stats["capture"])
                       if stats["capture"] else math.nan)
            print(f"  {role:6} {own_mult:>3g} {p_zopa:>8.0%} {horizon:>7} "
                  f"{arm:9} {len(stats['closed']):3d} {close:7.1%} "
                  f"{share:10.3f} {capture:8.3f}")
    return 0


def _empty_pers_selectivity_stats():
    return {
        "pct": [], "payoff": [], "payoff_per_price": [],
        "purchase_rate": [], "pre_decline_buys": [], "bought_lows": [],
        "bought_highs": [], "decline_count": [], "purchases": 0, "rounds": 0,
        "terminal": 0, "abandoned": 0, "pending": 0, "invalid": 0,
        "behavior_missing": 0, "payoff_missing": 0,
    }


def _pers_selectivity_observations(rows):
    """Normalize all assigned outcomes without conditioning on seller behavior."""
    observations = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        arm = pers_selectivity_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if completed is None else "terminal",
        )
        observations.append({
            "slot": slot,
            "pct": pct,
            "gid": gid,
            "completed": completed,
            "arm": arm,
            "diagnostic": diagnostic,
            "resolution": resolution,
        })
    return observations


def _summarize_pers_selectivity(observations):
    stats = _empty_pers_selectivity_stats()
    for observation in observations:
        completed = observation["completed"]
        resolution = observation["resolution"]
        if completed is None:
            field = "invalid" if resolution == "invalid-final" else "pending"
            stats[field] += 1
            continue

        stats["terminal"] += 1
        if observation["pct"] is not None:
            stats["pct"].append(observation["pct"])
        diagnostic = observation["diagnostic"]
        if resolution == "abandoned":
            # The competition's abandonment outcome discards prior earnings.
            # Keep it in ITT performance with payoff 0 and percentile .05, but
            # do not invent behavior that is absent from a terminal history.
            stats["abandoned"] += 1
            stats["payoff"].append(0.0)
            stats["payoff_per_price"].append(0.0)
            stats["behavior_missing"] += 1
            continue

        payoff = _number(diagnostic.get("payoff"))
        payoff_per_price = _number(diagnostic.get("payoff_per_price"))
        if payoff_per_price is None:
            price = _number(diagnostic.get("price"))
            if payoff is not None and price not in (None, 0.0):
                payoff_per_price = payoff / price
        if payoff is not None:
            stats["payoff"].append(payoff)
        if payoff_per_price is not None:
            stats["payoff_per_price"].append(payoff_per_price)
        if payoff is None or payoff_per_price is None:
            stats["payoff_missing"] += 1

        rounds = _number(diagnostic.get("rounds"))
        purchases = _number(diagnostic.get("purchases"))
        purchase_rate = _number(diagnostic.get("purchase_rate"))
        if rounds is None or purchases is None:
            stats["behavior_missing"] += 1
            continue
        stats["rounds"] += int(rounds)
        stats["purchases"] += int(purchases)
        if purchase_rate is not None:
            stats["purchase_rate"].append(purchase_rate)
        for field in ("pre_decline_buys", "bought_lows", "bought_highs",
                      "decline_count"):
            value = _number(diagnostic.get(field))
            if value is not None:
                stats[field].append(value)
    return stats


def _print_pers_selectivity_line(label, arm, stats):
    pct, n_pct = _mean_ci_text(stats["pct"])
    normalized, n_normalized = _mean_ci_text(stats["payoff_per_price"])
    purchase, n_purchase = _mean_ci_text(stats["purchase_rate"], percent=True)
    pre_decline, n_pre_decline = _mean_ci_text(stats["pre_decline_buys"])
    bought_lows, n_lows = _mean_ci_text(stats["bought_lows"])
    bought_highs, n_highs = _mean_ci_text(stats["bought_highs"])
    declines, n_declines = _mean_ci_text(stats["decline_count"])
    print(
        f"{label:9} {arm:9} pct={pct} n={n_pct}; "
        f"payoff/price={normalized} n={n_normalized}; "
        f"buy-rate={purchase} n={n_purchase} "
        f"({stats['purchases']}/{stats['rounds']} rounds); "
        f"pre-first-decline-buys={pre_decline} n={n_pre_decline}; "
        f"bought-lows={bought_lows} n={n_lows}; "
        f"bought-highs={bought_highs} n={n_highs}; "
        f"declines={declines} n={n_declines}; terminal={stats['terminal']} "
        f"abnd={stats['abandoned']} pend={stats['pending']} "
        f"badfin={stats['invalid']} behavior-missing={stats['behavior_missing']} "
        f"payoff-missing={stats['payoff_missing']}"
    )


def _pers_selectivity_cell(diagnostic: dict):
    """Return the pre-treatment exact-cell diagnostic key when available."""
    price = _number(diagnostic.get("price"))
    p = _number(diagnostic.get("p"))
    v = _number(diagnostic.get("v"))
    u = _number(diagnostic.get("u"))
    prior_value = _number(diagnostic.get("prior_value"))
    total_rounds = _number(diagnostic.get("total_rounds"))
    if None in (price, p, v, u, prior_value) or price == 0.0:
        return None
    value_scale = max(1.0, abs(price), abs(prior_value))
    prior_class = ("equality" if abs(prior_value - price) <= 1e-9 * value_scale
                   else "strict-negative")
    return (
        price, p, v / price, u, diagnostic.get("seller_message_type") or "?",
        int(total_rounds) if total_rounds is not None else "?", prior_class,
    )


def report_pers_selectivity(rows, hours, since=None, until=None):
    """Report the persuasion buyer-selectivity randomized intent-to-treat arm."""
    observations = _pers_selectivity_observations(rows)
    title = "GLEE_PERS_BUYER_SELECTIVITY_AB, persuasion buyer only"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("eligibility at first buyer decision: p*v+(1-p)*u <= price "
          "(with the live 1e-9 scale guard), v > u, and price > u")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first eligible buyer-decision exposure window: [{lower}, {upper})")
    else:
        print("scope --hours/--slots to the exact armed era; for a finished arm, "
              "use exact first-decision --since/--until bounds")
    print("primary estimates are intent-to-treat over every assigned eligible "
          "terminal game; they are not conditioned on an eventual decline")
    if not observations:
        print("no eligible persuasion buyer-decision exposures in the window")
        return 1

    by_slot_arm = defaultdict(list)
    gid_slots = defaultdict(set)
    for observation in observations:
        by_slot_arm[(observation["slot"], observation["arm"])].append(observation)
        recorded_slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(recorded_slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(recorded_slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    duplicate_gids = {gid for gid, slots in gid_slots.items() if len(slots) > 1}

    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        _print_pers_selectivity_line(
            NAMES.get(slot, slot), arm,
            _summarize_pers_selectivity(assigned),
        )

    pooled_observations = [
        observation for observation in observations
        if observation["gid"] not in duplicate_gids
    ]
    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [observation for observation in pooled_observations
                    if observation["arm"] == arm]
        if assigned:
            pooled[arm] = _summarize_pers_selectivity(assigned)
            _print_pers_selectivity_line("POOLED", arm, pooled[arm])
    print(f"pooled dependence guard: excluded {len(duplicate_gids)} game id(s) "
          "observed in multiple fleet slots")

    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("mean same-cell percentile", candidate["pct"], control["pct"])
        _print_delta("mean payoff/price", candidate["payoff_per_price"],
                     control["payoff_per_price"])
        _print_delta("purchase rate", candidate["purchase_rate"],
                     control["purchase_rate"], percent=True)
        _print_delta("pre-first-explicit-decline buys",
                     candidate["pre_decline_buys"], control["pre_decline_buys"])
        _print_delta("bought lows", candidate["bought_lows"],
                     control["bought_lows"])
        _print_delta("bought highs", candidate["bought_highs"],
                     control["bought_highs"])
        _print_delta("decline count", candidate["decline_count"],
                     control["decline_count"])

    strike_variants = defaultdict(list)
    for observation in pooled_observations:
        variant = observation["diagnostic"].get(
            "buyer_selectivity_strike_arm")
        if variant in ("off", "no-strike", "strike"):
            strike_variants[variant].append(observation)
    if strike_variants:
        print("pooled pre-treatment strike variants:")
        for variant in ("off", "no-strike", "strike"):
            variant_observations = strike_variants.get(variant)
            if not variant_observations:
                continue
            variant_stats = {}
            for arm in ("control", "candidate"):
                assigned = [observation for observation in variant_observations
                            if observation["arm"] == arm]
                if assigned:
                    variant_stats[arm] = _summarize_pers_selectivity(assigned)
                    _print_pers_selectivity_line(
                        variant.upper(), arm, variant_stats[arm])
            variant_control = variant_stats.get("control")
            variant_candidate = variant_stats.get("candidate")
            if variant_control and variant_candidate:
                print(f"{variant} candidate-control (intent-to-treat):")
                _print_delta("mean same-cell percentile",
                             variant_candidate["pct"], variant_control["pct"])
                _print_delta("mean payoff/price",
                             variant_candidate["payoff_per_price"],
                             variant_control["payoff_per_price"])
                _print_delta("purchase rate",
                             variant_candidate["purchase_rate"],
                             variant_control["purchase_rate"], percent=True)

    print("pooled exactly-one-decline diagnostic "
          "(descriptive/post-treatment; never a promotion criterion):")
    one_decline = {}
    for arm in ("control", "candidate"):
        assigned = [
            observation for observation in pooled_observations
            if observation["arm"] == arm
            and observation["completed"] is not None
            and observation["resolution"] == "terminal"
            and _number(observation["diagnostic"].get("decline_count")) == 1.0
        ]
        if assigned:
            one_decline[arm] = _summarize_pers_selectivity(assigned)
            _print_pers_selectivity_line("ONE-NO", arm, one_decline[arm])
    one_control, one_candidate = (one_decline.get("control"),
                                  one_decline.get("candidate"))
    if one_control and one_candidate:
        print("exactly-one-decline candidate-control (descriptive/post-treatment):")
        _print_delta("mean same-cell percentile", one_candidate["pct"],
                     one_control["pct"])
        _print_delta("mean payoff/price", one_candidate["payoff_per_price"],
                     one_control["payoff_per_price"])
        _print_delta("purchase rate", one_candidate["purchase_rate"],
                     one_control["purchase_rate"], percent=True)
        _print_delta("bought lows", one_candidate["bought_lows"],
                     one_control["bought_lows"])

    strata = defaultdict(list)
    for observation in pooled_observations:
        cell = _pers_selectivity_cell(observation["diagnostic"])
        if cell is not None:
            strata[(*cell, observation["arm"])].append(observation)
    if strata:
        print("pooled pre-treatment exact-cell diagnostics:")
        print("  price p r u mode rounds prior arm n pct payoff/price buy-rate")
        for (*cell, arm), assigned in sorted(
                strata.items(), key=lambda item: tuple(str(x) for x in item[0])):
            price, p, ratio, u, mode, total_rounds, prior_class = cell
            stats = _summarize_pers_selectivity(assigned)
            mean_pct = (statistics.mean(stats["pct"])
                        if stats["pct"] else math.nan)
            normalized = (statistics.mean(stats["payoff_per_price"])
                          if stats["payoff_per_price"] else math.nan)
            buy_rate = (stats["purchases"] / stats["rounds"]
                        if stats["rounds"] else math.nan)
            print(f"  {price:g} {p:g} {ratio:g} {u:g} {mode} {total_rounds} "
                  f"{prior_class} {arm} {len(stats['pct'])} {mean_pct:.4f} "
                  f"{normalized:.4f} {buy_rate:.1%}")

    candidate_terminal = [
        observation for observation in observations
        if observation["arm"] == "candidate"
        and observation["completed"] is not None
        and observation["resolution"] == "terminal"
    ]
    pre_decline_failures = sum(
        (_number(observation["diagnostic"].get("pre_decline_buys")) or 0.0) > 0.0
        for observation in candidate_terminal
    )
    strike_failures = sum(
        (_number(observation["diagnostic"].get("bought_lows")) or 0.0) > 1.0
        for observation in candidate_terminal
        if observation["diagnostic"].get(
            "buyer_selectivity_strike_arm") == "strike"
    )
    if pre_decline_failures or strike_failures:
        print("FALSIFICATION WARNING: terminal candidate games violate the "
              "precommitted mechanism: "
              f"pre-decline purchase games={pre_decline_failures}, "
              f">1 bought-low games={strike_failures}")

    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    if unresolved:
        pending = sum(stats["pending"] for stats in pooled.values())
        invalid = sum(stats["invalid"] for stats in pooled.values())
        print(f"INCOMPLETE OUTCOMES: pending={pending}, invalid-final={invalid}; "
              "promotion is blocked until every assigned outcome resolves")
    return 0


def _report_price_arm(rows, hours, arm_for_gid, title, eligibility,
                      scope_message, empty_message, since=None, until=None):
    """Report percentile and the close-rate veto for a price-only hash arm."""
    arms = defaultdict(
        lambda: defaultdict(lambda: {
            "pct": [], "closed": [], "abandoned": 0, "pending": 0,
            "invalid": 0,
        }))
    for row in rows:
        slot, pct, gid, closed, *metadata = row
        resolution = (metadata[0] if metadata else
                      ("unresolved" if closed is None else "terminal"))
        arm = arm_for_gid(gid)
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

    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print(eligibility)
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-price exposure window: [{lower}, {upper})")
    else:
        print(scope_message)
    if not arms:
        print(empty_message)
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


def report_open_claim(rows, hours, since=None, until=None):
    """Report the complete-information claim arm and close-rate veto."""
    return _report_price_arm(
        rows, hours, open_claim_arm,
        "GLEE_NEGO_OPEN_CLAIM + GLEE_NEGO_CLAIM_FLOOR, "
        "complete-information negotiation only",
        "eligibility: complete_information=true, positive visible ZOPA, either "
        "seat/horizon, and at least one outgoing price",
        "scope --hours/--slots to an era where OPEN_CLAIM and/or CLAIM_FLOOR "
        "was armed; for a finished arm, use exact first-price --since/--until "
        "bounds",
        "no eligible complete-information price exposures in the window",
        since=since, until=until)


def report_hidden_floor(rows, hours, since=None, until=None):
    """Report the hidden-information floor arm and close-rate veto."""
    return _report_price_arm(
        rows, hours, hidden_floor_arm,
        "GLEE_NEGO_HIDDEN_FLOOR, hidden-information negotiation only",
        "eligibility: complete_information=false, supported own-value base, "
        "either seat/horizon, and at least one outgoing price",
        "scope --hours/--slots to an era where HIDDEN_FLOOR was armed; for a "
        "finished arm, use exact first-price --since/--until bounds",
        "no eligible hidden-information price exposures in the window",
        since=since, until=until)


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
                    help="inclusive first-exposure unix timestamp for robust "
                         "--ab reports; overrides --hours as its lower bound")
    ap.add_argument("--until", type=float, default=None,
                    help="exclusive first-exposure unix timestamp for robust "
                         "--ab reports")
    ap.add_argument("--slots", default="")
    ap.add_argument("--ab", nargs="?", const="zopa",
                    choices=("zopa", "rank-price", "open-claim", "hidden-floor",
                             "hidden-policy", "pers-selectivity", "barg-msg"),
                    help="split games by a recoverable hash arm; bare --ab "
                         "keeps the legacy GLEE_NEGO_ZOPA_AB report")
    args = ap.parse_args()
    keep = {s.strip() for s in args.slots.split(",") if s.strip()}

    if args.ab in ("open-claim", "hidden-floor", "hidden-policy",
                   "pers-selectivity"):
        if (args.since is not None and args.until is not None
                and args.until <= args.since):
            ap.error("--until must be greater than --since")
        cohort = {
            "open-claim": open_claim_games,
            "hidden-floor": hidden_floor_games,
            "hidden-policy": hidden_policy_games,
            "pers-selectivity": pers_selectivity_games,
        }[args.ab]
        reporter = {
            "open-claim": report_open_claim,
            "hidden-floor": report_hidden_floor,
            "hidden-policy": report_hidden_policy,
            "pers-selectivity": report_pers_selectivity,
        }[args.ab]
        price_rows = [r for r in cohort(
            args.hours, since=args.since, until=args.until)
            if not keep or r[0] in keep]
        return reporter(
            price_rows, args.hours, since=args.since, until=args.until)

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
