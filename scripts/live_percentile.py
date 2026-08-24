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
    python scripts/live_percentile.py --ab open-claim-official --since T0
                         # exact official-seed complete-cell claim-arm strata
    python scripts/live_percentile.py --ab hidden-floor --since T0 --until T1
                                                     # hidden price floor + veto
    python scripts/live_percentile.py --ab hidden-policy --since T0 --until T1
                                       # hidden policy + zone-capture diagnostics
    python scripts/live_percentile.py --ab hi-terminal --since T0 --until T1
                         # hidden cap-10 buyer-1.2 terminal-counter ITT + wire audit
    python scripts/live_percentile.py --ab fp-complete --since T0 --until T1
                         # exact official-CDF first-principles promotion cells
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
from sim import official_negotiation_seed      # noqa: E402
from glee_agent import first_principles         # noqa: E402
from glee_agent.actions import hi_cap10_buyer12_terminal_arm as _hi_terminal_bit  # noqa: E402
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


def fp_complete_arm(gid) -> str | None:
    """Recover the first-principles Test 4 assignment from its pure helper."""
    treatment = first_principles.treatment_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


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


def hi_first_offer_arm(gid) -> str | None:
    """Recover the production unknown-horizon first-offer assignment."""
    from glee_agent.actions import hi_uncapped_first_offer_arm

    return hi_uncapped_first_offer_arm(gid)


def hi_terminal_arm(gid) -> str | None:
    """Recover the production terminal-counter assignment without duplicating its salt."""
    treatment = _hi_terminal_bit(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


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


def _open_claim_official_signal(seat: str, state: dict) -> dict | None:
    """Pre-action complete-cell strata for the exact claim-arm reader."""
    if not _open_claim_static_eligible(seat, state):
        return None
    role = state.get(f"{seat}_role")
    seller_value = _number(state.get("player_1_value"))
    buyer_value = _number(state.get("player_2_value"))
    base = infer_base(seller_value) if seller_value is not None else None
    if base is None and buyer_value is not None:
        base = infer_base(buyer_value)
    if state.get("horizon_known") is True:
        horizon_number = _number(state.get("max_rounds"))
        horizon = (str(int(horizon_number))
                   if horizon_number in (1.0, 10.0) else "invalid")
    else:
        horizon = "unknown"
    return {
        "cell": f"{horizon}/{role}",
        "role": role,
        "horizon": horizon,
        "seller_mult": seller_value / base if base else None,
        "buyer_mult": buyer_value / base if base else None,
        "messages_allowed": state.get("messages_allowed") is True,
    }


def _fp_complete_signal(seat: str, state: dict) -> dict | None:
    """Return one of the two measured-positive promotion cells.

    Eligibility uses only the configuration visible before our first action.
    The single-round hidden seller cell is intentionally absent: its corrected
    Test 4 confidence interval crossed zero and ``FP_COMPLETE_ONLY`` excludes it.
    """
    game = {
        "game_family": "negotiation",
        "your_player": seat,
        "game_state": state,
    }
    parsed = first_principles.cell(game)
    if parsed is None:
        return None
    horizon, complete, i_am_seller, my_value, _their_value = parsed
    if not complete or first_principles.scale_of(my_value) is None:
        return None
    if (horizon, i_am_seller) == ("single", True):
        return {"cell": "single/seller", "role": "seller"}
    if (horizon, i_am_seller) == ("cap10", False):
        return {"cell": "cap10/buyer", "role": "buyer"}
    return None


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


def _hi_terminal_signal(seat: str, state: dict) -> dict | None:
    """Pre-treatment public configuration for the narrow terminal arm."""
    if seat not in ("player_1", "player_2"):
        return None
    if (state.get("complete_information") is not False
            or state.get("horizon_known") is not True
            or _number(state.get("max_rounds")) != 10.0
            or state.get(f"{seat}_role") != "buyer"):
        return None
    own_value = _number(state.get(f"{seat}_value"))
    base = infer_base(own_value) if own_value is not None else None
    if base is None or abs(own_value / base - 1.2) > 1e-6:
        return None
    return {
        "base": base,
        "own_value": own_value,
        "messages_allowed": state.get("messages_allowed") is True,
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


def _open_claim_official_exposure_turn(slot: str, rec: dict):
    """Exact-reader exposure with pre-action cell metadata for omissions."""
    exposure = _open_claim_exposure_turn(slot, rec)
    if exposure is None:
        return None
    signal = _open_claim_official_signal(
        rec.get("your_player"), rec.get("state") or {})
    if signal is None:
        return None
    key, ts = exposure
    return key, ts, signal


def _fp_complete_exposure_turn(slot: str, rec: dict):
    """Cohort at the first own turn in a promotable cell, before its action."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _fp_complete_signal(seat, state)
    if not gid or signal is None:
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    expected_type = "offer" if signal["role"] == "seller" else "decision"
    if rec.get("action_type") != expected_type:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    return (slot, gid), ts, signal


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


def _hi_first_offer_signal(seat: str, state: dict) -> dict | None:
    """Public pre-action signal for the two identified no-limit cells."""
    signal = _hidden_policy_signal(seat, state)
    if (signal is None or signal.get("horizon") != "inf"
            or state.get("horizon_known") is not False):
        return None
    role, own_mult = signal.get("role"), signal.get("own_mult")
    counterpart_mult = (1.5 if (role, own_mult) == ("seller", 1.2) else
                        0.8 if (role, own_mult) == ("buyer", 1.0) else None)
    if counterpart_mult is None:
        return None
    return {**signal, "counterpart_mult": counterpart_mult}


def _hi_first_offer_exposure_turn(slot: str, rec: dict):
    """Cohort before the first price, including buyers that accept immediately."""
    from glee_agent.actions import _hidden_own_price_count

    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _hi_first_offer_signal(seat, state)
    if not gid or signal is None:
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    if _hidden_own_price_count(state, seat) != 0:
        return None
    expected_action = "offer" if signal["role"] == "seller" else "decision"
    if rec.get("action_type") != expected_action:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None

    action = rec.get("action") or {}
    actual = (_number(action.get("product_price"))
              if isinstance(action, dict) else None)
    arm = hi_first_offer_arm(gid)
    expected = None
    if arm in ("share80", "share95") and actual is not None:
        share = 0.80 if arm == "share80" else 0.95
        own, counterpart = signal["own_value"], \
            signal["counterpart_mult"] * signal["base"]
        expected = (own + share * (counterpart - own)
                    if signal["role"] == "seller" else
                    own - share * (own - counterpart))
        expected = round(expected, 2)
    signal = {
        **signal,
        "first_action": action.get("decision") or rec.get("action_type"),
        "first_price": actual,
        "expected_price": expected,
        "wire_ok": expected is None or abs(actual - expected) <= 1e-9,
    }
    return (slot, gid), ts, signal


def _hi_terminal_exposure_turn(slot: str, rec: dict):
    """Cohort on the buyer's first decision, before terminal reach is known."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _hi_terminal_signal(seat, state)
    if not gid or signal is None:
        return None
    if rec.get("action_type") != "decision":
        return None
    if (state.get("current_player") or seat) != seat:
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


def _open_claim_official_row(slot: str, rec: dict, fin: dict):
    """Build one claim-arm outcome against the literal official seed cell."""
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
    payoff = _result_payoff(fin.get("result") or {}, seat, seat)
    score = (official_negotiation_seed.percentile(state, seat, payoff)
             if payoff is not None else None)
    diagnostic = _open_claim_official_signal(seat, state)
    if diagnostic is None:
        return None
    return slot, score, str(gid), closed, diagnostic


def _fp_complete_row(slot: str, rec: dict, fin: dict):
    """Build an exact full-configuration outcome for the promotion cohort."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _fp_complete_signal(seat, state)
    if not gid or signal is None:
        return None
    closed = _terminal_close(fin)
    if closed is None:
        return None
    payoff = _result_payoff(fin.get("result") or {}, seat, seat)
    score = (official_negotiation_seed.percentile(state, seat, payoff)
             if payoff is not None else None)
    return slot, score, str(gid), closed, signal


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


def _hi_first_offer_row(slot: str, rec: dict, fin: dict):
    """Build one identified first-offer outcome and zone diagnostic."""
    state = fin.get("game_state") or {}
    seat = fin.get("your_player")
    if _hi_first_offer_signal(seat, state) is None:
        return None
    return _hidden_policy_row(slot, rec, fin)


def _counter_price(entry: dict) -> float | None:
    counter = entry.get("counteroffer")
    if isinstance(counter, dict):
        return _number(counter.get("price"))
    return _number(counter)


def _hi_terminal_row(slot: str, rec: dict, fin: dict):
    """Build an all-assigned outcome and terminal-wire mechanism diagnostic."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _hi_terminal_signal(seat, state)
    if not gid or signal is None:
        return None
    closed = _terminal_close(fin)
    if closed is None:
        return None
    result = fin.get("result") or {}
    payoff = _result_payoff(result, seat, seat)
    pct = (percentile("negotiation", dict(state), seat, payoff)
           if payoff is not None else None)

    reached = False
    wire_price = None
    history = [entry for entry in state.get("history") or []
               if isinstance(entry, dict)]
    for entry in history:
        if (_number(entry.get("round")) == 9.0
                and entry.get("decided_by") == seat
                and entry.get("decision") == "RejectOffer"):
            reached = True
            wire_price = _counter_price(entry)
            break
    last_decision = history[-1].get("decision") if history else None
    diagnostic = {
        **signal,
        "reached_terminal_counter": reached,
        "wire_price": wire_price,
        "expected_wire_price": signal["base"] + 0.01,
        "walked_away": last_decision == "WalkAway",
        "no_deal": not closed,
    }
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
    while missing outcomes remain unresolved, so collector lag cannot make the
    close-rate veto look better or manufacture a fifth-percentile loss.
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

        # A cold missing FINAL IS NOT an identified abandonment.  The 2026-08-24
        # audit found the supervisor SIGKILLing processes only after the server
        # reported active_games=0, while those processes were still fetching
        # final states.  The separate collector then stopped with 11,737 games
        # outstanding.  Those games completed on the server but have no local
        # result, so assigning them .05 would invent both an outcome and an arm
        # effect.  Distinguish cold backlog from fresh pending, but keep both
        # unresolved and block promotion until the collector recovers them.
        last = last_turn.get(key, exposure_ts)
        aged = now - last > ORPHAN_COLD_SECONDS and last < watermark[slot]
        if awaiting_terminal and aged:
            if metadata:
                yield slot, None, gid, None, metadata, "cold-missing"
            else:
                yield slot, None, gid, None, "cold-missing"
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


def open_claim_official_games(hours, since=None, until=None):
    """Yield complete claim-arm games with exact public-seed scores."""
    yield from _price_arm_games(
        hours, _open_claim_official_exposure_turn, _open_claim_official_row,
        since=since, until=until)


def fp_complete_games(hours, since=None, until=None):
    """Yield the two exact-CDF first-principles promotion cells."""
    yield from _price_arm_games(
        hours, _fp_complete_exposure_turn, _fp_complete_row,
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


def hi_first_offer_games(hours, since=None, until=None):
    """Yield every assigned identified hidden unknown-horizon game."""
    yield from _price_arm_games(
        hours, _hi_first_offer_exposure_turn, _hi_first_offer_row,
        since=since, until=until)


def hi_terminal_games(hours, since=None, until=None):
    """Yield every assigned buyer-1.2 cap-10 game, not only terminal reaches."""
    yield from _price_arm_games(
        hours, _hi_terminal_exposure_turn, _hi_terminal_row,
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


def _hidden_policy_observations(rows, arm_function=hidden_policy_arm):
    """Normalize terminal, abandoned, and unresolved price-cohort rows."""
    observations = []
    for row in rows:
        slot, pct, gid, closed, *metadata = row
        arm = arm_function(gid)
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


def report_hidden_policy(rows, hours, since=None, until=None, *,
                         arm_function=hidden_policy_arm,
                         experiment_name="GLEE_NEGO_HIDDEN_POLICY_V1",
                         eligibility="hidden multi-round negotiation only"):
    """Report the hidden-policy ITT experiment and mechanism diagnostics."""
    observations = _hidden_policy_observations(rows, arm_function)
    title = f"{experiment_name}, {eligibility}"
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


def report_hi_first_offer(rows, hours, since=None, until=None):
    """Report the three-arm identified first-offer greed experiment."""
    observations = _hidden_policy_observations(rows, hi_first_offer_arm)
    print("GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB, identified hidden no-limit "
          "first turns")
    print("LOCAL DIAGNOSTIC ONLY: pct below pools the hidden counterpart value. "
          "This report never authorizes promotion; join official per-game score "
          "before any rollout.")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-turn cohort window: [{lower}, {upper})")
    if not observations:
        print("no eligible first-offer assignments in the window")
        return 1

    gid_slots = defaultdict(set)
    for observation in observations:
        slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    pooled_obs = [o for o in observations if o["gid"] not in duplicates]

    pooled = {}
    for arm in ("control", "share80", "share95"):
        assigned = [o for o in pooled_obs if o["arm"] == arm]
        if not assigned:
            continue
        pooled[arm] = _summarize_hidden_policy(assigned)
        _print_hidden_policy_line("POOLED", arm, pooled[arm])
    print(f"pooled dependence guard: excluded {len(duplicates)} cross-fleet "
          "game id(s)")

    control = pooled.get("control")
    if control:
        for arm in ("share80", "share95"):
            candidate = pooled.get(arm)
            if not candidate:
                continue
            print(f"{arm}-control (diagnostic, not promotion-grade):")
            _print_delta("hidden-pooled percentile",
                         candidate["pct"], control["pct"])
            _print_delta("close rate", candidate["closed"],
                         control["closed"], percent=True)
            _print_delta("reconstructed-zone capture ITT",
                         candidate["capture"], control["capture"])
    if pooled.get("share80") and pooled.get("share95"):
        print("share95-share80 greed contrast (diagnostic):")
        _print_delta("hidden-pooled percentile", pooled["share95"]["pct"],
                     pooled["share80"]["pct"])
        _print_delta("close rate", pooled["share95"]["closed"],
                     pooled["share80"]["closed"], percent=True)

    wire_failures = [
        o for o in pooled_obs
        if o["diagnostic"].get("expected_price") is not None
        and o["diagnostic"].get("wire_ok") is not True
    ]
    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    print(f"wire failures={len(wire_failures)}; unresolved outcomes={unresolved}")
    print("PROMOTION BLOCKED BY DESIGN: require official-score 95% CI above "
          "zero, close-rate lower bound above -2pp, zero wire failures, and no "
          "role/scale sign reversal. Conditional deal share is never sufficient.")
    return 2 if wire_failures else 0


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


def report_open_claim_official(rows, hours, since=None, until=None):
    """Report the claim experiment on literal complete configuration cells."""
    observations = []
    gid_slots = defaultdict(set)
    for slot, score, gid, closed, *metadata in rows:
        arm = open_claim_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal",
        )
        fleet_slots = diagnostic.get("fleet_slots")
        if isinstance(fleet_slots, (list, tuple, set)):
            gid_slots[gid].update(fleet_slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "score": score, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic, "resolution": resolution,
        })

    title = "GLEE_NEGO_OPEN_CLAIM + CLAIM_FLOOR, exact official-seed read"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("eligibility: complete information, positive visible ZOPA, first "
          "outgoing price before action; use only an era/slot where the hash "
          "arm—not OPEN_CLAIM_ALWAYS—determined behavior")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-price exposure window: [{lower}, {upper})")
    if not observations:
        print("no exact claim-arm exposures in the window")
        return 1

    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    independent = [item for item in observations
                   if item["gid"] not in duplicates]
    print(f"pooled dependence guard: excluded {len(duplicates)} game id(s) "
          "observed in multiple fleet slots")

    def group_key(item):
        return item["diagnostic"].get("cell")

    groups = [("ALL", independent)]
    for cell in sorted({group_key(item) for item in independent}
                       - {None}):
        groups.append((cell, [item for item in independent
                              if group_key(item) == cell]))
    # The old unknown-buyer aggregate hid a strong visible-type interaction.
    # Keep these strata predeclared in the reader: the 2026-08-24 Test 4 read
    # estimated floor effects +.198/- .005/-.033 for seller types .8/1.0/1.2.
    unknown_buyers = [item for item in independent
                      if group_key(item) == "unknown/buyer"]
    for seller_mult in (0.8, 1.0, 1.2):
        groups.append((f"unknown/buyer S{seller_mult:g}", [
            item for item in unknown_buyers
            if abs((_number(item["diagnostic"].get("seller_mult")) or -99)
                   - seller_mult) <= 1e-6]))

    all_unresolved = 0
    for label, population in groups:
        if not population:
            continue
        stats = {}
        for arm in ("control", "candidate"):
            assigned = [item for item in population if item["arm"] == arm]
            terminal = [item for item in assigned if item["closed"] is not None]
            scores = [item["score"] for item in terminal
                      if item["score"] is not None]
            closes = [float(bool(item["closed"])) for item in terminal]
            abandoned = sum(item["resolution"] == "abandoned"
                            for item in terminal)
            unresolved = len(assigned) - len(terminal)
            stats[arm] = (scores, closes, unresolved)
            if label == "ALL":
                all_unresolved += unresolved
            score_text, _ = _mean_ci_text(scores)
            close_text, _ = _mean_ci_text(closes, percent=True)
            print(f"{label:22} {arm:9} official={score_text} n={len(scores)}; "
                  f"close={close_text} n={len(closes)}; abnd={abandoned}; "
                  f"unresolved={unresolved}")
        control, candidate = stats["control"], stats["candidate"]
        if control[0] and candidate[0]:
            print(f"  {label} candidate-control:")
            _print_delta("official-seed percentile", candidate[0], control[0])
            _print_delta("close rate", candidate[1], control[1], percent=True)

    if all_unresolved:
        print(f"INCOMPLETE OUTCOMES: {all_unresolved}; promotion is blocked")
    print("Primary outcome is exact percentile ITT. Close rate is a mechanism "
          "diagnostic already reflected through zero/abandonment scores; never "
          "condition the score comparison on agreement.")
    return 0


def report_fp_complete(rows, hours, since=None, until=None):
    """Read the corrected first-principles promotion cohort reproducibly."""
    observations = []
    gid_slots = defaultdict(set)
    for slot, score, gid, closed, *metadata in rows:
        arm = fp_complete_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal",
        )
        fleet_slots = diagnostic.get("fleet_slots")
        if isinstance(fleet_slots, (list, tuple, set)):
            gid_slots[gid].update(fleet_slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "score": score, "gid": gid, "closed": closed,
            "arm": arm, "cell": diagnostic.get("cell"),
            "resolution": resolution,
        })

    title = "GLEE_NEGO_FIRST_PRINCIPLES + FP_COMPLETE_ONLY"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("ITT eligibility: complete-information single-round seller or cap-10 "
          "buyer; cohort begins at our first turn, before treatment action")
    print("score: exact horizon/information/messages/scale/value-pair/role "
          "midrank against the checked-in 32,403-game official public seed; "
          "never the hidden-value-pooled local model")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-turn exposure window: [{lower}, {upper})")
    if not observations:
        print("no assigned first-principles promotion-cell games in the window")
        return 1

    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    independent = [item for item in observations
                   if item["gid"] not in duplicates]
    print(f"pooled dependence guard: excluded {len(duplicates)} game id(s) "
          "observed in multiple fleet slots")

    summaries = {}
    for cell in ("single/seller", "cap10/buyer", "ALL"):
        population = independent if cell == "ALL" else [
            item for item in independent if item["cell"] == cell]
        for arm in ("control", "candidate"):
            assigned = [item for item in population if item["arm"] == arm]
            terminal = [item for item in assigned if item["closed"] is not None]
            scores = [item["score"] for item in terminal
                      if item["score"] is not None]
            closes = [float(bool(item["closed"])) for item in terminal]
            unresolved = len(assigned) - len(terminal)
            abandoned = sum(item["resolution"] == "abandoned"
                            for item in terminal)
            summaries[(cell, arm)] = (
                scores, closes, unresolved, abandoned)
            score_text, _ = _mean_ci_text(scores)
            close_text, _ = _mean_ci_text(closes, percent=True)
            print(f"{cell:13} {arm:9} official={score_text} n={len(scores)}; "
                  f"close={close_text} n={len(closes)}; "
                  f"abandoned={abandoned}; unresolved={unresolved}")
        control = summaries[(cell, "control")]
        candidate = summaries[(cell, "candidate")]
        if control[0] and candidate[0]:
            print(f"  {cell} candidate-control:")
            _print_delta("official-seed percentile", candidate[0], control[0])
            _print_delta("close rate", candidate[1], control[1], percent=True)

    unresolved = sum(
        item[2] for (cell, _arm), item in summaries.items() if cell == "ALL")
    if unresolved:
        print(f"INCOMPLETE OUTCOMES: {unresolved}; promotion is blocked")
    return 0


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


def report_hi_terminal(rows, hours, since=None, until=None):
    """Report the terminal-counter arm without conditioning on reaching round 9."""
    observations = []
    gid_slots = defaultdict(set)
    for slot, pct, gid, closed, *metadata in rows:
        arm = hi_terminal_arm(gid)
        if arm is None:
            continue
        diagnostic = next((item for item in metadata if isinstance(item, dict)), {})
        resolution = next((item for item in metadata if isinstance(item, str)),
                          "unresolved" if closed is None else "terminal")
        fleet_slots = diagnostic.get("fleet_slots")
        if isinstance(fleet_slots, (list, tuple, set)):
            gid_slots[gid].update(fleet_slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "pct": pct, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic, "resolution": resolution,
        })

    title = "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("ITT eligibility: hidden cap-10 negotiation, our role buyer, own value "
          "1.2*base; cohort begins at the first buyer decision, before terminal "
          "reach or outcome is known")
    print("IMPORTANT: pct below uses the local hidden-value-pooled CDF and is a "
          "same-window diagnostic, not the official full-configuration score. "
          "Promotion requires official per-game score evidence.")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first buyer-decision exposure window: [{lower}, {upper})")
    if not observations:
        print("no assigned hidden cap-10 buyer-1.2 games in the window")
        return 1

    duplicate_gids = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    pooled = [item for item in observations if item["gid"] not in duplicate_gids]
    print(f"pooled dependence guard: excluded {len(duplicate_gids)} game id(s) "
          "observed in multiple fleet slots")

    stats = {}
    for arm in ("control", "candidate"):
        assigned = [item for item in pooled if item["arm"] == arm]
        terminal = [item for item in assigned if item["closed"] is not None]
        pcts = [item["pct"] for item in terminal if item["pct"] is not None]
        closes = [float(bool(item["closed"])) for item in terminal]
        reached = [item for item in terminal
                   if item["diagnostic"].get("reached_terminal_counter")]
        unresolved = len(assigned) - len(terminal)
        stats[arm] = {"pct": pcts, "closed": closes, "reached": reached,
                      "unresolved": unresolved}
        pct_text, _ = _mean_ci_text(pcts)
        close_text, _ = _mean_ci_text(closes, percent=True)
        print(f"POOLED    {arm:9} pct={pct_text} n={len(pcts)}; "
              f"close={close_text} n={len(closes)}; "
              f"terminal-counter={len(reached)}; unresolved={unresolved}")

    control, candidate = stats.get("control"), stats.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("local pooled-CDF percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)
        _delta, low, _high = _delta_ci(candidate["closed"], control["closed"])
        if low is not None and low <= -0.02:
            print("CLOSE NONINFERIORITY NOT MET: lower 95% bound is not above -2pp")

    wire_failures = []
    for item in pooled:
        if item["arm"] != "candidate":
            continue
        diagnostic = item["diagnostic"]
        if not diagnostic.get("reached_terminal_counter"):
            continue
        actual = _number(diagnostic.get("wire_price"))
        expected = _number(diagnostic.get("expected_wire_price"))
        if (actual is None or expected is None
                or abs(actual - expected) > max(1e-7, abs(expected) * 1e-12)):
            wire_failures.append((item["gid"], actual, expected))
    if wire_failures:
        print(f"FALSIFICATION: {len(wire_failures)} candidate terminal counter(s) "
              f"were not base+$0.01; first={wire_failures[0]}")
    else:
        candidate_reaches = len(candidate["reached"]) if candidate else 0
        print(f"wire mechanism: {candidate_reaches} candidate terminal counter(s), "
              "all exactly base+$0.01")

    unresolved = sum(value["unresolved"] for value in stats.values())
    if unresolved:
        print(f"INCOMPLETE OUTCOMES: {unresolved}; promotion is blocked")
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
                    help="inclusive first-exposure unix timestamp for robust "
                         "--ab reports; overrides --hours as its lower bound")
    ap.add_argument("--until", type=float, default=None,
                    help="exclusive first-exposure unix timestamp for robust "
                         "--ab reports")
    ap.add_argument("--slots", default="")
    ap.add_argument("--ab", nargs="?", const="zopa",
                    choices=("zopa", "rank-price", "open-claim",
                             "open-claim-official", "hidden-floor",
                             "hidden-policy", "hi-first-offer", "hi-terminal",
                             "fp-complete", "pers-selectivity", "barg-msg"),
                    help="split games by a recoverable hash arm; bare --ab "
                         "keeps the legacy GLEE_NEGO_ZOPA_AB report")
    args = ap.parse_args()
    keep = {s.strip() for s in args.slots.split(",") if s.strip()}

    if args.ab in ("open-claim", "open-claim-official", "hidden-floor",
                   "hidden-policy", "hi-first-offer", "hi-terminal", "fp-complete",
                   "pers-selectivity"):
        if (args.since is not None and args.until is not None
                and args.until <= args.since):
            ap.error("--until must be greater than --since")
        cohort = {
            "open-claim": open_claim_games,
            "open-claim-official": open_claim_official_games,
            "hidden-floor": hidden_floor_games,
            "hidden-policy": hidden_policy_games,
            "hi-first-offer": hi_first_offer_games,
            "hi-terminal": hi_terminal_games,
            "fp-complete": fp_complete_games,
            "pers-selectivity": pers_selectivity_games,
        }[args.ab]
        reporter = {
            "open-claim": report_open_claim,
            "open-claim-official": report_open_claim_official,
            "hidden-floor": report_hidden_floor,
            "hidden-policy": report_hidden_policy,
            "hi-first-offer": report_hi_first_offer,
            "hi-terminal": report_hi_terminal,
            "fp-complete": report_fp_complete,
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
