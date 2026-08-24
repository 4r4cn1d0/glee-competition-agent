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
    python scripts/live_percentile.py --ab hi-buyer-curve --since T0 \
        --official-json FILE
                         # hidden cap-10 buyer-1.2 terminal-counter ITT + wire audit
    python scripts/live_percentile.py --ab hidden-min-share-veto --since T0 \
        --official-json FILE
                         # support-aware low-share acceptance veto + wire audit
    python scripts/live_percentile.py --ab table-vcont-precedence --since T0 \
        --official-json FILE
                         # direct-TABLE accept vs observed continuation + audit
    python scripts/live_percentile.py --ab fp-complete --since T0 --until T1
                         # exact official-CDF first-principles promotion cells
    python scripts/live_percentile.py --ab pers-selectivity --since T0 --until T1
                                  # buyer selectivity arm, first eligible decision
    python scripts/live_percentile.py --ab pers-prose --since T0 --official-json FILE
                       # exact seller wording ITT + official dashboard deltas
    python scripts/live_percentile.py --ab pers-truth --since T0 --official-json FILE
                       # exact binary seller credibility ITT + official deltas
    python scripts/live_percentile.py --ab pers-decline-veto --since T0 \
        --official-json FILE
                       # exact buyer/text explicit-decline veto ITT + wire audit
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
from glee_agent.actions import hi_cap10_buyer_curve_arm as _hi_buyer_curve_bit  # noqa: E402
from glee_agent.actions import hi_cap10_buyer12_terminal_arm as _hi_terminal_bit  # noqa: E402
from glee_agent.messages import BARG_ARMS, bargaining_arm  # noqa: E402
from glee_agent.pricing import infer_base       # noqa: E402
from glee_agent.strategies.persuasion import (  # noqa: E402
    _recommendation_signal as _pers_recommendation_signal,
    buyer_selectivity_assignment,
    p08_r125_binary_truth_assignment,
    p08_r125_prose_assignment,
    p08_r125_text_decline_veto_assignment,
)
from glee_agent.text import (  # noqa: E402
    reads_as_recommendation_expanded,
    reads_as_recommendation_legacy,
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


def hi_extreme_open_arm(gid) -> str | None:
    """Recover the production direct-leader opening assignment."""
    from glee_agent.actions import hi_uncapped_extreme_open_arm

    treatment = hi_uncapped_extreme_open_arm(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def hi_terminal_arm(gid) -> str | None:
    """Recover the production terminal-counter assignment without duplicating its salt."""
    treatment = _hi_terminal_bit(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def hi_buyer_curve_arm(gid) -> str | None:
    """Recover the production broad cap-10 buyer-curve assignment."""
    treatment = _hi_buyer_curve_bit(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def stall_current_break_arm(gid) -> str | None:
    """Recover the production stale-stall assignment without copying its salt."""
    from glee_agent.strategies.negotiation import stall_current_break_assignment

    treatment = stall_current_break_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def hidden_min_share_veto_arm(gid) -> str | None:
    """Recover the production support-aware acceptance-veto assignment."""
    from glee_agent.strategies.negotiation import hidden_min_share_veto_assignment

    treatment = hidden_min_share_veto_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def table_vcont_precedence_arm(gid) -> str | None:
    """Recover the production TABLE-versus-continuation assignment."""
    from glee_agent.strategies.negotiation import table_vcont_precedence_assignment

    treatment = table_vcont_precedence_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def pers_selectivity_arm(gid) -> str | None:
    """Recover the buyer-selectivity arm from the action path's pure helper."""
    treatment = buyer_selectivity_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def pers_prose_arm(gid) -> str | None:
    """Recover the exact-cell seller prose assignment from production code."""
    treatment = p08_r125_prose_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def pers_truth_arm(gid) -> str | None:
    """Recover the exact-cell binary truth assignment from production code."""
    treatment = p08_r125_binary_truth_assignment(gid)
    if treatment is None:
        return None
    return "candidate" if treatment else "control"


def pers_decline_veto_arm(gid) -> str | None:
    """Recover the exact buyer/text decline-veto production assignment."""
    treatment = p08_r125_text_decline_veto_assignment(gid)
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


def _hi_buyer_curve_signal(seat: str, state: dict) -> dict | None:
    """Pre-treatment public cell for the broad cap-10 buyer curve."""
    if seat not in ("player_1", "player_2"):
        return None
    if (state.get("complete_information") is not False
            or state.get("horizon_known") is not True
            or _number(state.get("max_rounds")) != 10.0
            or state.get(f"{seat}_role") != "buyer"):
        return None
    own_value = _number(state.get(f"{seat}_value"))
    base = infer_base(own_value) if own_value is not None else None
    if base is None:
        return None
    own_mult = next(
        (mult for mult in (1.0, 1.2, 1.5)
         if abs(own_value / base - mult) <= 1e-6),
        None,
    )
    if own_mult is None:
        return None
    return {
        "base": base,
        "own_value": own_value,
        "own_mult": own_mult,
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


def _pers_prose_signal(seat: str, state: dict) -> dict | None:
    """Pre-action exact seller cell for the token-versus-prose experiment."""
    if seat != "player_1" or state.get("seller_message_type") != "text":
        return None
    # Live seller turns omit this configuration key and reveal the cell by
    # exposing v/u. Collector finals carry the full config, where an explicit
    # false must not be allowed back into the known-CV cohort.
    if ("is_seller_know_cv" in state
            and state.get("is_seller_know_cv") is not True):
        return None
    price = _number(state.get("product_price"))
    prior = _number(state.get("p"))
    high_value = _number(state.get("v"))
    low_value = _number(state.get("u"))
    rounds = _number(state.get("total_rounds"))
    if None in (price, prior, high_value, low_value, rounds) or price <= 0.0:
        return None
    if (abs(prior - 0.8) > 1e-9
            or abs(high_value / price - 1.25) > 1e-9
            or int(rounds) != 20):
        return None
    return {
        "price": price,
        "p": prior,
        "v": high_value,
        "u": low_value,
        "ratio": high_value / price,
        "seller_message_type": "text",
        "total_rounds": int(rounds),
    }


def _pers_truth_signal(seat: str, state: dict) -> dict | None:
    """Pre-action exact seller cell for the binary credibility experiment."""
    if seat != "player_1" or state.get("seller_message_type") != "binary":
        return None
    if ("is_seller_know_cv" in state
            and state.get("is_seller_know_cv") is not True):
        return None
    price = _number(state.get("product_price"))
    prior = _number(state.get("p"))
    high_value = _number(state.get("v"))
    low_value = _number(state.get("u"))
    rounds = _number(state.get("total_rounds"))
    if None in (price, prior, high_value, low_value, rounds) or price <= 0.0:
        return None
    if (abs(prior - 0.8) > 1e-9
            or abs(high_value / price - 1.25) > 1e-9
            or abs(low_value) > 1e-9
            or int(rounds) != 20):
        return None
    return {
        "price": price,
        "p": prior,
        "v": high_value,
        "u": low_value,
        "ratio": high_value / price,
        "seller_message_type": "binary",
        "total_rounds": int(rounds),
    }


def _pers_decline_veto_signal(seat: str, state: dict) -> dict | None:
    """Pre-action exact buyer cell for the text explicit-decline veto."""
    if seat != "player_2" or state.get("seller_message_type") != "text":
        return None
    price = _number(state.get("product_price"))
    prior = _number(state.get("p"))
    high_value = _number(state.get("v"))
    low_value = _number(state.get("u"))
    rounds = _number(state.get("total_rounds"))
    if None in (price, prior, high_value, low_value, rounds) or price <= 0.0:
        return None
    if (abs(prior - 0.8) > 1e-9
            or abs(high_value / price - 1.25) > 1e-9
            or abs(low_value) > 1e-9
            or int(rounds) != 20):
        return None
    return {
        "price": price,
        "p": prior,
        "v": high_value,
        "u": low_value,
        "ratio": high_value / price,
        "seller_message_type": "text",
        # Absent on active documented state; present in collector finals.  The
        # official delta is already same-configuration normalized, and the
        # reader reports this as a predeclared subgroup rather than letting an
        # unobservable config bit enter assignment.
        "is_seller_know_cv": state.get("is_seller_know_cv"),
        "total_rounds": int(rounds),
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


def _hi_extreme_open_signal(seat: str, state: dict) -> dict | None:
    """Public pre-action signal for the four direct-leader copy cells."""
    signal = _hidden_policy_signal(seat, state)
    if (signal is None or signal.get("horizon") != "inf"
            or state.get("horizon_known") is not False):
        return None
    role, own_mult = signal.get("role"), signal.get("own_mult")
    if not ((role == "seller" and own_mult in (0.8, 1.0))
            or (role == "buyer" and own_mult in (1.2, 1.5))):
        return None
    return signal


def _hi_extreme_open_exposure_turn(slot: str, rec: dict):
    """Cohort the disjoint leader-copy arm before its first action."""
    from glee_agent.actions import _hidden_own_price_count

    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _hi_extreme_open_signal(seat, state)
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
    arm = hi_extreme_open_arm(gid)
    expected = None
    if arm == "candidate" and actual is not None:
        expected = round(signal["base"] *
                         (1.485 if signal["role"] == "seller" else 0.81), 2)
    return (slot, gid), ts, {
        **signal,
        "first_action": action.get("decision") or rec.get("action_type"),
        "first_price": actual,
        "expected_price": expected,
        "wire_ok": expected is None or abs(actual - expected) <= 1e-9,
    }


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


def _hi_buyer_curve_exposure_turn(slot: str, rec: dict):
    """Cohort at the first eligible buyer decision, before its action."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _hi_buyer_curve_signal(seat, state)
    if not gid or signal is None:
        return None
    if (rec.get("action_type") != "decision"
            or (state.get("current_player") or seat) != seat):
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    action = rec.get("action") or {}
    return (slot, gid), ts, {
        **signal,
        "first_decision": action.get("decision"),
        "first_price": _number(action.get("product_price")),
    }


def _stall_current_break_signal(seat: str, state: dict) -> dict | None:
    """Observable first-trigger state for the stale-stall target experiment."""
    from glee_agent.strategies import negotiation

    if seat not in ("player_1", "player_2"):
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    role = state.get(f"{seat}_role")
    if role not in ("seller", "buyer"):
        return None
    stale = negotiation._their_stall_price(state, seat)
    if stale is None:
        return None
    current = negotiation._current_concession_break(state, seat, stale)
    if current is None:
        return None
    own_value = _number(state.get(f"{seat}_value"))
    if own_value is None:
        return None
    base = infer_base(own_value)
    max_rounds = _number(state.get("max_rounds"))
    horizon = ("inf" if state.get("horizon_known") is False
               or max_rounds is None else str(int(max_rounds)))
    return {
        "role": role,
        "own_value": own_value,
        "base": base,
        "scale": base,
        "complete": state.get("complete_information") is True,
        "horizon": horizon,
        "messages": state.get("messages_allowed") is True,
        "round": int(_number(state.get("round")) or 0),
        "stale_price": stale,
        "current_price": current,
    }


def _stall_current_break_exposure_turn(slot: str, rec: dict):
    """Cohort a game at its first favorable current break, before action."""
    if rec.get("game_family") != "negotiation":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _stall_current_break_signal(seat, state)
    if not gid or signal is None or rec.get("action_type") != "decision":
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None

    arm = stall_current_break_arm(gid)
    action = rec.get("action") or {}
    plan = rec.get("plan") or {}
    logged = (plan.get("stall_current_break")
              if isinstance(plan, dict) else None)
    if isinstance(logged, dict) and logged.get("eligible") is False:
        return None
    gates = plan.get("gates_fired") if isinstance(plan, dict) else []
    gates = gates if isinstance(gates, list) else []
    pre_target = (_number(logged.get("pre_stall_target"))
                  if isinstance(logged, dict) else None)
    control_target = (_number(logged.get("control_target"))
                      if isinstance(logged, dict) else None)
    writer_changed = (pre_target is not None and control_target is not None
                      and abs(pre_target - control_target) > 1e-9)
    plan_arm = logged.get("arm") if isinstance(logged, dict) else None
    mechanism_ok = (isinstance(logged, dict)
                    and logged.get("eligible") is True
                    and plan_arm == arm)
    if arm == "candidate":
        mechanism_ok = mechanism_ok and (
            ("stall_current_break" in gates) == writer_changed)
    else:
        mechanism_ok = mechanism_ok and "stall_current_break" not in gates
    signal.update({
        "action_decision": action.get("decision") if isinstance(action, dict) else None,
        "wire_price": (_number(action.get("product_price"))
                       if isinstance(action, dict) else None),
        "plan_arm": plan_arm,
        "pre_stall_target": pre_target,
        "control_target": control_target,
        "final_target": (_number(logged.get("final_target"))
                         if isinstance(logged, dict) else None),
        "writer_changed": writer_changed,
        "gate_fired": "stall_current_break" in gates,
        "mechanism_ok": mechanism_ok,
    })
    return (slot, gid), ts, signal


def _hidden_min_share_veto_exposure_turn(slot: str, rec: dict):
    """Cohort the first low-share offer the untreated stack would accept."""
    if (rec.get("game_family") != "negotiation"
            or rec.get("action_type") != "decision"):
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    plan = rec.get("plan") or {}
    logged = (plan.get("hidden_min_share_veto")
              if isinstance(plan, dict) else None)
    if not gid or not isinstance(logged, dict) or logged.get("eligible") is not True:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None

    from glee_agent.strategies import negotiation
    signal = negotiation.hidden_min_share_signal(state, seat)
    arm = hidden_min_share_veto_arm(gid)
    action = rec.get("action") or {}
    gates = plan.get("gates_fired") if isinstance(plan, dict) else []
    gates = gates if isinstance(gates, list) else []
    source = logged.get("control_acceptor")
    source_ok = source in ("table_accept", "stall_accept", "continuation_accept")
    mechanism_ok = signal is not None and arm is not None and source_ok
    mechanism_ok = mechanism_ok and logged.get("arm") == arm
    for key in ("base", "own_value", "offer_price", "surplus",
                "min_positive_zone", "veto_fraction", "veto_floor",
                "positive_zone_share_upper"):
        actual = _number(logged.get(key))
        expected = _number((signal or {}).get(key))
        mechanism_ok = mechanism_ok and actual is not None and expected is not None
        if actual is not None and expected is not None:
            mechanism_ok = mechanism_ok and abs(actual - expected) <= max(
                1e-8, abs(expected) * 1e-9)
    wire_price = (_number(action.get("product_price"))
                  if isinstance(action, dict) else None)
    logged_counter = _number(logged.get("counter_price"))
    if arm == "candidate":
        mechanism_ok = mechanism_ok and (
            action.get("decision") == "RejectOffer"
            and wire_price is not None
            and logged_counter is not None
            and abs(wire_price - logged_counter) <= 1e-9
            and "hidden_min_share_veto" in gates)
    else:
        mechanism_ok = mechanism_ok and (
            action.get("decision") == "AcceptOffer"
            and wire_price is None
            and logged_counter is None
            and "hidden_min_share_veto" not in gates)

    max_rounds = _number(state.get("max_rounds"))
    horizon = ("inf" if state.get("horizon_known") is False
               or max_rounds is None else str(int(max_rounds)))
    diagnostic = {
        **(signal or {}),
        "role": (signal or logged).get("role"),
        "own_multiplier": (signal or logged).get("own_multiplier"),
        "scale": (signal or logged).get("base"),
        "complete": False,
        "horizon": horizon,
        "messages": state.get("messages_allowed") is True,
        "round": int(_number(state.get("round")) or 0),
        "control_acceptor": source,
        "plan_arm": logged.get("arm"),
        "action_decision": action.get("decision"),
        "wire_price": wire_price,
        "counter_price": logged_counter,
        "mechanism_ok": bool(mechanism_ok),
    }
    return (slot, gid), ts, diagnostic


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


def _table_vcont_precedence_exposure_turn(slot: str, rec: dict):
    """Cohort the first direct TABLE accept contradicted by observed momentum."""
    if (rec.get("game_family") != "negotiation"
            or rec.get("action_type") != "decision"):
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    plan = rec.get("plan") or {}
    logged = (plan.get("table_vcont_precedence")
              if isinstance(plan, dict) else None)
    if not gid or not isinstance(logged, dict) or logged.get("eligible") is not True:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None

    from glee_agent import table_policy
    from glee_agent.strategies import negotiation

    role = state.get(f"{seat}_role")
    own_value = _number(state.get(f"{seat}_value"))
    offer_price = _number((state.get("last_offer") or {}).get("price"))
    continuation = _number(plan.get("continuation_value"))
    evidence = plan.get("continuation_evidence")
    elapsed = _number(plan.get("elapsed"))
    threshold = None
    surplus_now = None
    if (role in ("seller", "buyer") and own_value is not None
            and offer_price is not None and elapsed is not None):
        surplus_now = (offer_price - own_value if role == "seller"
                       else own_value - offer_price)
        threshold = table_policy.accept_threshold(
            own_value, role == "seller", elapsed)
    expected = None
    if (offer_price is not None and surplus_now is not None
            and continuation is not None and threshold is not None):
        expected = negotiation.table_vcont_precedence_signal(
            state, plan, offer_price, surplus_now, continuation, evidence,
            threshold)

    arm = table_vcont_precedence_arm(gid)
    action = rec.get("action") or {}
    gates = plan.get("gates_fired") if isinstance(plan, dict) else []
    gates = gates if isinstance(gates, list) else []
    mechanism_ok = expected is not None and arm is not None
    mechanism_ok = mechanism_ok and logged.get("arm") == arm
    for key in ("offer_price", "surplus_now", "table_threshold",
                "continuation_value", "continuation_rate"):
        actual = _number(logged.get(key))
        wanted = _number((expected or {}).get(key))
        mechanism_ok = mechanism_ok and actual is not None and wanted is not None
        if actual is not None and wanted is not None:
            mechanism_ok = mechanism_ok and abs(actual - wanted) <= max(
                1e-8, abs(wanted) * 1e-9)
    mechanism_ok = mechanism_ok and logged.get("role") == (expected or {}).get("role")
    mechanism_ok = mechanism_ok and logged.get("distinct_opponent_prices") == \
        (expected or {}).get("distinct_opponent_prices")

    wire_price = (_number(action.get("product_price"))
                  if isinstance(action, dict) else None)
    counter_price = _number(logged.get("counter_price"))
    if arm == "candidate":
        mechanism_ok = mechanism_ok and (
            action.get("decision") == "RejectOffer"
            and wire_price is not None and counter_price is not None
            and abs(wire_price - counter_price) <= max(
                1e-8, abs(counter_price) * 1e-12)
            and plan.get("table_accept_vetoed") is True
            and "table_vcont_precedence" in gates
            and "table_accept" not in gates)
    else:
        mechanism_ok = mechanism_ok and (
            action.get("decision") == "AcceptOffer"
            and wire_price is None and counter_price is None
            and "table_accept" in gates
            and "table_vcont_precedence" not in gates)

    base = infer_base(own_value) if own_value is not None else None
    max_rounds = _number(state.get("max_rounds"))
    horizon = ("inf" if state.get("horizon_known") is False
               or max_rounds is None else str(int(max_rounds)))
    diagnostic = dict(logged)
    diagnostic.update({
        "role": role,
        "complete": state.get("complete_information") is True,
        "horizon": horizon,
        "own_value": own_value,
        "scale": base,
        "own_multiplier": (own_value / base
                           if own_value is not None and base else None),
        "messages": state.get("messages_allowed") is True,
        "round": int(_number(state.get("round")) or 0),
        "plan_arm": logged.get("arm"),
        "action_decision": (action.get("decision")
                            if isinstance(action, dict) else None),
        "wire_price": wire_price,
        "counter_price": counter_price,
        "gate_fired": "table_vcont_precedence" in gates,
        "mechanism_ok": mechanism_ok,
    })
    return (slot, gid), ts, diagnostic


def _pers_prose_exposure_turn(slot: str, rec: dict):
    """Cohort an exact-cell seller game before its first outgoing message."""
    if rec.get("game_family") != "persuasion":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _pers_prose_signal(seat, state)
    if not gid or signal is None:
        return None
    if rec.get("action_type") != "seller_message":
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    opponent = rec.get("opponent") or {}
    if isinstance(opponent, dict):
        signal["opponent_type"] = opponent.get("type")
        signal["opponent_name"] = opponent.get("name")
    action = rec.get("action") or {}
    plan = rec.get("plan") or {}
    signal.update({
        "first_message": action.get("message") if isinstance(action, dict) else None,
        "first_recommend": plan.get("recommend") if isinstance(plan, dict) else None,
    })
    return (slot, gid), ts, signal


def _pers_truth_exposure_turn(slot: str, rec: dict):
    """Cohort an exact binary seller game before its first recommendation."""
    if rec.get("game_family") != "persuasion":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _pers_truth_signal(seat, state)
    if not gid or signal is None:
        return None
    if rec.get("action_type") != "seller_recommendation":
        return None
    if (state.get("current_player") or seat) != seat:
        return None
    ts = _number(rec.get("ts"))
    if ts is None:
        return None
    opponent = rec.get("opponent") or {}
    if isinstance(opponent, dict):
        signal["opponent_type"] = opponent.get("type")
        signal["opponent_name"] = opponent.get("name")
    action = rec.get("action") or {}
    plan = rec.get("plan") or {}
    signal.update({
        "first_decision": (action.get("decision")
                           if isinstance(action, dict) else None),
        "first_recommend": (plan.get("recommend")
                            if isinstance(plan, dict) else None),
        "first_quality": state.get("current_quality"),
    })
    return (slot, gid), ts, signal


def _pers_decline_veto_exposure_turn(slot: str, rec: dict):
    """Cohort every exact buyer game at its globally first decision."""
    if rec.get("game_family") != "persuasion":
        return None
    gid = str(rec.get("game_id") or "")
    seat = rec.get("your_player")
    state = rec.get("state") or {}
    signal = _pers_decline_veto_signal(seat, state)
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
    opponent = rec.get("opponent") or {}
    if isinstance(opponent, dict):
        signal["opponent_type"] = opponent.get("type")
        signal["opponent_name"] = opponent.get("name")
    signal.update({
        "first_message": state.get("seller_message"),
        "first_decision": decision,
    })
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


def _hi_extreme_open_row(slot: str, rec: dict, fin: dict):
    """Build one direct-leader opening outcome and zone diagnostic."""
    state = fin.get("game_state") or {}
    seat = fin.get("your_player")
    if _hi_extreme_open_signal(seat, state) is None:
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


def _hi_buyer_curve_row(slot: str, rec: dict, fin: dict):
    """Build the broad buyer ITT outcome and audit every emitted counter."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _hi_buyer_curve_signal(seat, state)
    if not gid or signal is None:
        return None
    closed = _terminal_close(fin)
    if closed is None:
        return None
    result = fin.get("result") or {}
    payoff = _result_payoff(result, seat, seat)
    pct = (percentile("negotiation", dict(state), seat, payoff)
           if payoff is not None else None)

    from glee_agent.actions import _HI_CAP10_BUYER_CURVE

    wire_rounds = []
    wire_prices = []
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        if (entry.get("decided_by") != seat
                or entry.get("decision") != "RejectOffer"):
            continue
        price = _counter_price(entry)
        if price is None:
            continue
        wire_rounds.append(_number(entry.get("round")))
        wire_prices.append(price)
    curve_count = min(len(wire_prices), len(_HI_CAP10_BUYER_CURVE))
    curve_wire_prices = wire_prices[:curve_count]
    expected = [
        round(signal["own_value"] * _HI_CAP10_BUYER_CURVE[index], 2)
        for index in range(curve_count)
    ]
    wire_ok = all(abs(actual - target)
                  <= max(1e-7, abs(target) * 1e-12)
                  for actual, target in zip(curve_wire_prices, expected))
    diagnostic = {
        **signal,
        "wire_rounds": wire_rounds,
        "wire_prices": wire_prices,
        "curve_wire_prices": curve_wire_prices,
        "expected_wire_prices": expected,
        "wire_ok": wire_ok,
        "outgoing_counters": len(wire_prices),
        "curve_counters": curve_count,
        "terminal_control_price": (
            wire_prices[len(_HI_CAP10_BUYER_CURVE)]
            if len(wire_prices) > len(_HI_CAP10_BUYER_CURVE) else None),
        "no_deal": not closed,
    }
    return slot, pct, str(gid), closed, diagnostic


def _stall_current_break_row(slot: str, rec: dict, fin: dict):
    """Build a terminal stale-stall outcome; exposure metadata carries scope."""
    if fin.get("game_family") != "negotiation":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    if not gid or seat not in ("player_1", "player_2"):
        return None
    closed = _terminal_close(fin)
    if closed is None:
        return None
    state = fin.get("game_state") or {}
    payoff = _result_payoff(fin.get("result") or {}, seat, seat)
    pct = (percentile("negotiation", dict(state), seat, payoff)
           if payoff is not None else None)
    return slot, pct, str(gid), closed


def _hidden_min_share_veto_row(slot: str, rec: dict, fin: dict):
    """Build one terminal outcome for the first-accepted-low-share ITT cohort."""
    return _stall_current_break_row(slot, rec, fin)


def _table_vcont_precedence_row(slot: str, rec: dict, fin: dict):
    """Build one terminal outcome for the triggered precedence ITT cohort."""
    return _stall_current_break_row(slot, rec, fin)


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


def _pers_prose_row(slot: str, rec: dict, fin: dict):
    """Build one exact-cell seller outcome without conditioning on purchases."""
    if fin.get("game_family") != "persuasion":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _pers_prose_signal(seat, state)
    if not gid or signal is None:
        return None
    completed = _terminal_close(fin)
    if completed is None:
        return None
    result = fin.get("result") or {}
    payoff = _result_payoff(result, seat, seat)
    pct = (percentile("persuasion", dict(state), seat, payoff)
           if payoff is not None else None)
    history = [entry for entry in state.get("history") or []
               if isinstance(entry, dict)]
    purchases = sum(bool(entry.get("bought")) for entry in history)
    diagnostic = {
        **signal,
        "payoff": payoff,
        "payoff_per_price": (
            payoff / signal["price"]
            if payoff is not None and signal["price"] else None),
        "rounds": len(history),
        "seller_messages": [entry.get("seller_message") for entry in history],
        "purchases": purchases,
        "purchase_rate": purchases / len(history) if history else None,
        "zero_outcome": payoff == 0.0 if payoff is not None else None,
        "bought_highs": sum(
            bool(entry.get("bought"))
            and str(entry.get("quality") or "").lower() == "high"
            for entry in history),
        "bought_lows": sum(
            bool(entry.get("bought"))
            and str(entry.get("quality") or "").lower() == "low"
            for entry in history),
    }
    return slot, pct, str(gid), completed, diagnostic


def _pers_truth_row(slot: str, rec: dict, fin: dict):
    """Build one exact binary seller outcome without purchase selection."""
    if fin.get("game_family") != "persuasion":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _pers_truth_signal(seat, state)
    if not gid or signal is None:
        return None
    completed = _terminal_close(fin)
    if completed is None:
        return None
    payoff = _result_payoff(fin.get("result") or {}, seat, seat)
    pct = (percentile("persuasion", dict(state), seat, payoff)
           if payoff is not None else None)
    history = [entry for entry in state.get("history") or []
               if isinstance(entry, dict)]
    purchases = sum(bool(entry.get("bought")) for entry in history)
    diagnostic = {
        **signal,
        "payoff": payoff,
        "payoff_per_price": (
            payoff / signal["price"]
            if payoff is not None and signal["price"] else None),
        "rounds": len(history),
        "seller_messages": [entry.get("seller_message") for entry in history],
        "qualities": [entry.get("quality") for entry in history],
        "purchases": purchases,
        "purchase_rate": purchases / len(history) if history else None,
        "zero_outcome": payoff == 0.0 if payoff is not None else None,
        "bought_highs": sum(
            bool(entry.get("bought"))
            and str(entry.get("quality") or "").lower() == "high"
            for entry in history),
        "bought_lows": sum(
            bool(entry.get("bought"))
            and str(entry.get("quality") or "").lower() == "low"
            for entry in history),
    }
    return slot, pct, str(gid), completed, diagnostic


def _pers_decline_veto_history_metrics(history) -> dict:
    """All-round buyer diagnostics without selecting games on a decline."""
    entries = [entry for entry in history or [] if isinstance(entry, dict)]
    decline_mask = [
        reads_as_recommendation_expanded(entry.get("seller_message")) is False
        for entry in entries
    ]
    purchases = sum(bool(entry.get("bought")) for entry in entries)
    first_decline = next(
        (index + 1 for index, decline in enumerate(decline_mask) if decline),
        None,
    )
    return {
        "rounds": len(entries),
        "seller_messages": [entry.get("seller_message") for entry in entries],
        "buyer_decisions": [entry.get("buyer_decision") for entry in entries],
        "qualities": [entry.get("quality") for entry in entries],
        "purchases": purchases,
        "purchase_rate": purchases / len(entries) if entries else None,
        "explicit_declines": sum(decline_mask),
        "bought_explicit_declines": sum(
            decline and bool(entry.get("bought"))
            for decline, entry in zip(decline_mask, entries)),
        "first_decline_round": first_decline,
    }


def _pers_decline_veto_row(slot: str, rec: dict, fin: dict):
    """Build one exact buyer outcome while retaining no-decline games."""
    if fin.get("game_family") != "persuasion":
        return None
    gid = rec.get("game_id") or fin.get("game_id")
    seat = fin.get("your_player")
    state = fin.get("game_state") or {}
    signal = _pers_decline_veto_signal(seat, state)
    if not gid or signal is None:
        return None
    completed = _terminal_close(fin)
    if completed is None:
        return None
    payoff = _result_payoff(fin.get("result") or {}, seat, seat)
    pct = (percentile("persuasion", dict(state), seat, payoff)
           if payoff is not None else None)
    diagnostic = {
        **signal,
        **_pers_decline_veto_history_metrics(state.get("history")),
        "payoff": payoff,
        "payoff_per_price": (
            payoff / signal["price"]
            if payoff is not None and signal["price"] else None),
        "zero_outcome": payoff == 0.0 if payoff is not None else None,
        "negative_outcome": payoff < 0.0 if payoff is not None else None,
    }
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


def hi_extreme_open_games(hours, since=None, until=None):
    """Yield every assigned disjoint direct-leader opening game."""
    yield from _price_arm_games(
        hours, _hi_extreme_open_exposure_turn, _hi_extreme_open_row,
        since=since, until=until)


def hi_terminal_games(hours, since=None, until=None):
    """Yield every assigned buyer-1.2 cap-10 game, not only terminal reaches."""
    yield from _price_arm_games(
        hours, _hi_terminal_exposure_turn, _hi_terminal_row,
        since=since, until=until)


def hi_buyer_curve_games(hours, since=None, until=None):
    """Yield every assigned viable hidden cap-10 buyer game."""
    yield from _price_arm_games(
        hours, _hi_buyer_curve_exposure_turn, _hi_buyer_curve_row,
        since=since, until=until)


def stall_current_break_games(hours, since=None, until=None):
    """Yield every game from its first pre-action favorable current break."""
    yield from _price_arm_games(
        hours, _stall_current_break_exposure_turn, _stall_current_break_row,
        since=since, until=until)


def hidden_min_share_veto_games(hours, since=None, until=None):
    """Yield games from the first low-share control acceptance opportunity."""
    yield from _price_arm_games(
        hours, _hidden_min_share_veto_exposure_turn,
        _hidden_min_share_veto_row, since=since, until=until)


def table_vcont_precedence_games(hours, since=None, until=None):
    """Yield games from the first contradicted direct-TABLE acceptance."""
    yield from _price_arm_games(
        hours, _table_vcont_precedence_exposure_turn,
        _table_vcont_precedence_row, since=since, until=until)


def pers_selectivity_games(hours, since=None, until=None):
    """Yield the first-eligible-decision buyer-selectivity ITT cohort."""
    yield from _price_arm_games(
        hours, _pers_selectivity_exposure_turn, _pers_selectivity_row,
        since=since, until=until)


def pers_prose_games(hours, since=None, until=None):
    """Yield every assigned exact-cell seller wording outcome."""
    yield from _price_arm_games(
        hours, _pers_prose_exposure_turn, _pers_prose_row,
        since=since, until=until)


def pers_truth_games(hours, since=None, until=None):
    """Yield every assigned exact-cell binary seller truth outcome."""
    yield from _price_arm_games(
        hours, _pers_truth_exposure_turn, _pers_truth_row,
        since=since, until=until)


def _pers_decline_veto_trace_audit(rows):
    """Attach emitted-gate evidence for every exact buyer turn in the cohort."""
    wanted = {(row[0], row[2]) for row in rows}
    audits = defaultdict(lambda: {
        "eligible_turns": 0,
        "veto_traces": 0,
        "trace_failures": 0,
    })
    by_slot = defaultdict(set)
    for slot, gid in wanted:
        by_slot[slot].add(gid)
    for slot, gids in by_slot.items():
        path = os.path.join(REPO, "logs", slot, "turns.jsonl")
        try:
            handle = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = str(rec.get("game_id") or "")
                if gid not in gids:
                    continue
                state = rec.get("state") or {}
                if (_pers_decline_veto_signal(
                        rec.get("your_player"), state) is None
                        or rec.get("action_type") != "buyer_decision"):
                    continue
                audit = audits[(slot, gid)]
                audit["eligible_turns"] += 1
                arm = pers_decline_veto_arm(gid)
                decline = (reads_as_recommendation_expanded(
                    state.get("seller_message")) is False)
                action = rec.get("action") or {}
                decision = str(action.get("decision") or "").strip().lower()
                plan = rec.get("plan") or {}
                gates = plan.get("gates_fired") if isinstance(plan, dict) else []
                traced = (isinstance(gates, list)
                          and "p08_r125_text_decline_veto" in gates)
                marked = (isinstance(plan, dict)
                          and plan.get("p08_r125_text_decline_veto") is True)
                audit["veto_traces"] += int(traced)
                mechanism_ok = (
                    (not traced or
                     (arm == "candidate" and decline and decision == "no"
                      and marked))
                    and (not marked or traced)
                    and not (arm == "candidate" and decline and decision == "yes")
                    and not (arm == "control" and (traced or marked))
                )
                audit["trace_failures"] += int(not mechanism_ok)

    enriched = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        attached = False
        output_metadata = []
        for item in metadata:
            if isinstance(item, dict) and not attached:
                output_metadata.append({**item, **audits[(slot, gid)]})
                attached = True
            else:
                output_metadata.append(item)
        if not attached:
            output_metadata.insert(0, dict(audits[(slot, gid)]))
        enriched.append((slot, pct, gid, completed, *output_metadata))
    return enriched


def pers_decline_veto_games(hours, since=None, until=None):
    """Yield all assigned exact buyer games with emitted-veto trace audits."""
    rows = list(_price_arm_games(
        hours, _pers_decline_veto_exposure_turn, _pers_decline_veto_row,
        since=since, until=until))
    yield from _pers_decline_veto_trace_audit(rows)


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


def report_hi_extreme_open(rows, hours, since=None, until=None):
    """Report the disjoint two-arm direct-leader opening experiment."""
    observations = _hidden_policy_observations(rows, hi_extreme_open_arm)
    print("GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB, direct-leader hidden "
          "no-limit first turns")
    print("LOCAL DIAGNOSTIC ONLY: pct below pools the hidden counterpart value. "
          "This report never authorizes promotion; join official per-game score "
          "before any rollout.")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first-turn cohort window: [{lower}, {upper})")
    if not observations:
        print("no eligible direct-leader opening assignments in the window")
        return 1

    gid_slots = defaultdict(set)
    for observation in observations:
        slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    pooled_obs = [item for item in observations if item["gid"] not in duplicates]

    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [item for item in pooled_obs if item["arm"] == arm]
        if not assigned:
            continue
        pooled[arm] = _summarize_hidden_policy(assigned)
        _print_hidden_policy_line("POOLED", arm, pooled[arm])
    print(f"pooled dependence guard: excluded {len(duplicates)} cross-fleet "
          "game id(s)")

    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("candidate-control (diagnostic, not promotion-grade):")
        _print_delta("hidden-pooled percentile", candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)
        _print_delta("reconstructed-zone capture ITT", candidate["capture"],
                     control["capture"])

    wire_failures = [
        item for item in pooled_obs
        if item["arm"] == "candidate"
        and item["diagnostic"].get("expected_price") is not None
        and item["diagnostic"].get("wire_ok") is not True
    ]
    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    print(f"wire failures={len(wire_failures)}; unresolved outcomes={unresolved}")
    print("PROMOTION BLOCKED BY DESIGN: require official-score 95% CI above "
          "zero, close-rate lower bound above -2pp, zero wire failures, and no "
          "role/type/scale/message reversal.")
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


_PERS_PROSE_OPENERS = (
    "This one is worth taking.",
    "Strong unit this round — I would buy it.",
    "This is one of the better ones.",
)
_PERS_PROSE_CLOSERS = (
    "My record on these is the reason to take this one seriously.",
    "You can check that against the calls I have made so far.",
)


def _is_current_positive_prose(message) -> bool:
    text = str(message or "").strip()
    return (any(text.startswith(opener + " ") for opener in _PERS_PROSE_OPENERS)
            and any(text.endswith(closer) for closer in _PERS_PROSE_CLOSERS))


def _load_official_deltas(path):
    """Load dashboard-exported per-game deltas keyed by (slot, game id)."""
    if not path:
        return {}
    with open(path, encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        records = parsed if isinstance(parsed, list) else parsed.get("games", [])
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    output = {}
    for record in records:
        slot = str(record.get("slot") or "")
        gid = str(record.get("game_id") or "")
        delta = _number(record.get("rating_delta"))
        if not slot or not gid or delta is None:
            raise ValueError("each official record needs slot, game_id, rating_delta")
        key = (slot, gid)
        if key in output:
            raise ValueError(f"duplicate official record for {slot}/{gid}")
        output[key] = delta
    return output


def _load_pers_official_records(path):
    """Load audited persuasion transcript records without changing other ABs.

    The generic official join intentionally consumes only rating deltas.  A
    persuasion game can nevertheless be complete on the authenticated
    dashboard while the local collector has only its turn stream.  Preserve
    the complete record here so the persuasion readers can recover such a
    terminal outcome only when all 20 transcript rounds are supplied and pass
    the exact-cell/wire checks below.
    """
    deltas = _load_official_deltas(path)
    if not path:
        return {}
    with open(path, encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        records = parsed if isinstance(parsed, list) else parsed.get("games", [])
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    output = {}
    for record in records:
        slot = str(record.get("slot") or "")
        gid = str(record.get("game_id") or "")
        key = (slot, gid)
        if key not in deltas:
            raise ValueError("persuasion official record failed delta validation")
        output[key] = {**record, "rating_delta": deltas[key]}
    return output


def _pers_official_terminal(record, diagnostic, *, mode):
    """Validate and reconstruct one missing local persuasion final.

    A rating row alone is never enough: the authenticated export must contain
    the complete 20-round transcript, exact setup, and terminal seller payoff.
    This keeps unresolved games in the ITT denominator unless the server-side
    evidence can also audit the emitted action on every round.
    """
    if not isinstance(record, dict) or record.get("terminal") is not True:
        return None
    transcript = record.get("persuasion")
    if (record.get("source") != "authenticated-dashboard-transcript"
            or str(record.get("family") or "").lower() != "persuasion"
            or str(record.get("role") or "").lower() != "seller"
            or not isinstance(transcript, dict)):
        return False

    expected = {
        "price": diagnostic.get("price"),
        "p": diagnostic.get("p"),
        "v": diagnostic.get("v"),
        "u": diagnostic.get("u"),
        "rounds": 20.0,
    }
    for field, wanted in expected.items():
        observed = _number(transcript.get(field))
        wanted_number = _number(wanted)
        if (observed is None or wanted_number is None
                or not math.isclose(observed, wanted_number,
                                    rel_tol=1e-9, abs_tol=1e-9)):
            return False
    if str(transcript.get("mode") or "").strip().lower() != mode:
        return False

    messages = transcript.get("seller_messages")
    qualities = transcript.get("qualities")
    decisions = transcript.get("buyer_decisions")
    if not all(isinstance(values, list) and len(values) == 20
               for values in (messages, qualities, decisions)):
        return False
    normalized_qualities = [str(value or "").strip().lower()
                            for value in qualities]
    normalized_decisions = [str(value or "").strip().lower()
                            for value in decisions]
    if (any(value not in {"high", "low"} for value in normalized_qualities)
            or any(value not in {"buy", "pass"}
                   for value in normalized_decisions)):
        return False
    payoff = _number(transcript.get("seller_payoff"))
    price = _number(diagnostic.get("price"))
    if payoff is None or price is None or price <= 0:
        return False
    purchases = sum(value == "buy" for value in normalized_decisions)
    # Persuasion sellers receive exactly price for each purchase.  Requiring
    # this identity catches a wrong-role or wrong-modal dashboard join.
    if not math.isclose(payoff, purchases * price,
                        rel_tol=1e-9, abs_tol=1e-9):
        return False

    merged = {
        **diagnostic,
        "rounds": 20,
        "seller_messages": list(messages),
        "qualities": normalized_qualities,
        "buyer_decisions": normalized_decisions,
        "purchases": purchases,
        "purchase_rate": purchases / 20.0,
        "payoff": payoff,
        "payoff_per_price": payoff / price,
        "zero_outcome": payoff == 0.0,
        "bought_highs": sum(
            decision == "buy" and quality == "high"
            for decision, quality in zip(normalized_decisions,
                                         normalized_qualities)),
        "bought_lows": sum(
            decision == "buy" and quality == "low"
            for decision, quality in zip(normalized_decisions,
                                         normalized_qualities)),
        "official_terminal_recovery": True,
    }
    return merged


def _pers_buyer_official_terminal(record, diagnostic):
    """Validate and reconstruct one authenticated exact-cell buyer final."""
    if not isinstance(record, dict) or record.get("terminal") is not True:
        return None
    transcript = record.get("persuasion")
    if (record.get("source") != "authenticated-dashboard-transcript"
            or str(record.get("family") or "").lower() != "persuasion"
            or str(record.get("role") or "").lower() != "buyer"
            or not isinstance(transcript, dict)):
        return False
    expected = {
        "price": diagnostic.get("price"),
        "p": diagnostic.get("p"),
        "v": diagnostic.get("v"),
        "u": diagnostic.get("u"),
        "rounds": 20.0,
    }
    for field, wanted in expected.items():
        observed = _number(transcript.get(field))
        wanted_number = _number(wanted)
        if (observed is None or wanted_number is None
                or not math.isclose(observed, wanted_number,
                                    rel_tol=1e-9, abs_tol=1e-9)):
            return False
    if str(transcript.get("mode") or "").strip().lower() != "text":
        return False
    seller_knows = transcript.get("is_seller_know_cv")
    if not isinstance(seller_knows, bool):
        return False
    messages = transcript.get("seller_messages")
    qualities = transcript.get("qualities")
    decisions = transcript.get("buyer_decisions")
    if not all(isinstance(values, list) and len(values) == 20
               for values in (messages, qualities, decisions)):
        return False
    normalized_qualities = [str(value or "").strip().lower()
                            for value in qualities]
    normalized_decisions = [str(value or "").strip().lower()
                            for value in decisions]
    if (any(value not in {"high", "low"} for value in normalized_qualities)
            or any(value not in {"buy", "pass"}
                   for value in normalized_decisions)):
        return False
    price = _number(diagnostic.get("price"))
    high_value = _number(diagnostic.get("v"))
    low_value = _number(diagnostic.get("u"))
    payoff = _number(transcript.get("buyer_payoff"))
    if None in (price, high_value, low_value, payoff) or price <= 0.0:
        return False
    expected_payoff = sum(
        (high_value - price if quality == "high" else low_value - price)
        for decision, quality in zip(normalized_decisions,
                                     normalized_qualities)
        if decision == "buy"
    )
    if not math.isclose(payoff, expected_payoff,
                        rel_tol=1e-9, abs_tol=1e-9):
        return False
    history = [
        {
            "seller_message": message,
            "buyer_decision": decision,
            "bought": decision == "buy",
            "quality": quality,
        }
        for message, decision, quality in zip(
            messages, normalized_decisions, normalized_qualities)
    ]
    return {
        **diagnostic,
        **_pers_decline_veto_history_metrics(history),
        "is_seller_know_cv": seller_knows,
        "payoff": payoff,
        "payoff_per_price": payoff / price,
        "zero_outcome": payoff == 0.0,
        "negative_outcome": payoff < 0.0,
        "official_terminal_recovery": True,
    }


def _pers_prose_observations(rows, official):
    observations = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        arm = pers_prose_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if completed is None else "terminal")
        official_record = official.get((slot, gid))
        if completed is None:
            recovered = _pers_official_terminal(
                official_record, diagnostic, mode="text")
            if recovered is False:
                resolution = "invalid-final"
            elif isinstance(recovered, dict):
                diagnostic = recovered
                completed = True
                resolution = "official-terminal"
        messages = diagnostic.get("seller_messages")
        if not isinstance(messages, list) or not messages:
            messages = [diagnostic.get("first_message")]
        expected = ((lambda message: str(message or "").strip() == "yes")
                    if arm == "control" else _is_current_positive_prose)
        wire_failures = sum(not expected(message) for message in messages)
        recommend_failure = diagnostic.get("first_recommend") is not True
        observations.append({
            "slot": slot, "gid": gid, "arm": arm, "pct": pct,
            "completed": completed, "resolution": resolution,
            "diagnostic": diagnostic,
            "official": (None if official_record is None else
                         official_record.get("rating_delta")),
            "wire_failures": wire_failures,
            "recommend_failure": recommend_failure,
        })
    return observations


def _pers_truth_observations(rows, official):
    """Join exact binary assignments and validate every emitted recommendation."""
    observations = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        arm = pers_truth_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if completed is None else "terminal")
        official_record = official.get((slot, gid))
        if completed is None:
            recovered = _pers_official_terminal(
                official_record, diagnostic, mode="binary")
            if recovered is False:
                resolution = "invalid-final"
            elif isinstance(recovered, dict):
                diagnostic = recovered
                completed = True
                resolution = "official-terminal"
        messages = diagnostic.get("seller_messages")
        qualities = diagnostic.get("qualities")
        if not isinstance(messages, list) or not messages:
            messages = [diagnostic.get("first_decision")]
            qualities = [diagnostic.get("first_quality")]
        if not isinstance(qualities, list) or len(qualities) != len(messages):
            qualities = [None] * len(messages)
        wire_failures = 0
        for message, quality in zip(messages, qualities):
            observed = str(message or "").strip().lower()
            if arm == "control":
                expected = "yes"
            else:
                normalized_quality = str(quality or "").strip().lower()
                expected = ("yes" if normalized_quality == "high" else
                            "no" if normalized_quality == "low" else None)
            wire_failures += int(expected is None or observed != expected)
        first_quality = str(diagnostic.get("first_quality") or "").lower()
        expected_first = (True if arm == "control" else
                          True if first_quality == "high" else
                          False if first_quality == "low" else None)
        recommend_failure = (
            expected_first is None
            or diagnostic.get("first_recommend") is not expected_first)
        observations.append({
            "slot": slot, "gid": gid, "arm": arm, "pct": pct,
            "completed": completed, "resolution": resolution,
            "diagnostic": diagnostic,
            "official": (None if official_record is None else
                         official_record.get("rating_delta")),
            "wire_failures": wire_failures,
            "recommend_failure": recommend_failure,
        })
    return observations


def _pers_decline_veto_observations(rows, official):
    """Join exact buyer assignments and audit the decline-only action path."""
    observations = []
    for row in rows:
        slot, pct, gid, completed, *metadata = row
        arm = pers_decline_veto_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if completed is None else "terminal")
        official_record = official.get((slot, gid))
        if completed is None:
            recovered = _pers_buyer_official_terminal(
                official_record, diagnostic)
            if recovered is False:
                resolution = "invalid-final"
            elif isinstance(recovered, dict):
                diagnostic = recovered
                completed = True
                resolution = "official-terminal"
        bought_declines = int(_number(
            diagnostic.get("bought_explicit_declines")) or 0)
        trace_failures = int(_number(
            diagnostic.get("trace_failures")) or 0)
        # The final overlay makes a candidate purchase on any expanded-parser
        # decline impossible. Controls are unrestricted because byte identity,
        # rather than a newly asserted wire, is their mechanism contract.
        wire_failures = trace_failures
        if arm == "candidate":
            wire_failures += bought_declines
        observations.append({
            "slot": slot,
            "gid": gid,
            "arm": arm,
            "pct": pct,
            "completed": completed,
            "resolution": resolution,
            "diagnostic": diagnostic,
            "official": (None if official_record is None else
                         official_record.get("rating_delta")),
            "wire_failures": wire_failures,
        })
    return observations


def _summarize_pers_prose(observations):
    stats = {
        "pct": [], "official": [], "purchase_rate": [],
        "purchases": [], "payoff_per_price": [], "zero": [], "terminal": 0,
        "pending": 0, "invalid": 0, "wire_failures": 0,
        "recommend_failures": 0, "official_missing": 0,
    }
    for observation in observations:
        stats["wire_failures"] += observation["wire_failures"]
        stats["recommend_failures"] += int(observation["recommend_failure"])
        if observation["completed"] is None:
            field = ("invalid" if observation["resolution"] == "invalid-final"
                     else "pending")
            stats[field] += 1
            continue
        stats["terminal"] += 1
        if observation["pct"] is not None:
            stats["pct"].append(observation["pct"])
        if observation["official"] is not None:
            stats["official"].append(observation["official"])
        else:
            stats["official_missing"] += 1
        diagnostic = observation["diagnostic"]
        for source, target in (("purchase_rate", "purchase_rate"),
                               ("purchases", "purchases"),
                               ("payoff_per_price", "payoff_per_price")):
            value = _number(diagnostic.get(source))
            if value is not None:
                stats[target].append(value)
        zero = diagnostic.get("zero_outcome")
        if isinstance(zero, bool):
            stats["zero"].append(float(zero))
    return stats


def _summarize_pers_decline_veto(observations):
    stats = {
        "pct": [], "official": [], "purchase_rate": [], "purchases": [],
        "payoff_per_price": [], "zero": [], "negative": [],
        "explicit_declines": [], "bought_declines": [],
        "veto_traces": 0, "eligible_turns": 0, "terminal": 0,
        "pending": 0, "invalid": 0, "wire_failures": 0,
        "official_missing": 0,
    }
    for observation in observations:
        stats["wire_failures"] += observation["wire_failures"]
        diagnostic = observation["diagnostic"]
        stats["veto_traces"] += int(_number(
            diagnostic.get("veto_traces")) or 0)
        stats["eligible_turns"] += int(_number(
            diagnostic.get("eligible_turns")) or 0)
        if observation["completed"] is None:
            field = ("invalid" if observation["resolution"] == "invalid-final"
                     else "pending")
            stats[field] += 1
            continue
        stats["terminal"] += 1
        if observation["pct"] is not None:
            stats["pct"].append(observation["pct"])
        if observation["official"] is None:
            stats["official_missing"] += 1
        else:
            stats["official"].append(observation["official"])
        for source, target in (
                ("purchase_rate", "purchase_rate"),
                ("purchases", "purchases"),
                ("payoff_per_price", "payoff_per_price"),
                ("explicit_declines", "explicit_declines"),
                ("bought_explicit_declines", "bought_declines")):
            value = _number(diagnostic.get(source))
            if value is not None:
                stats[target].append(value)
        for source, target in (("zero_outcome", "zero"),
                               ("negative_outcome", "negative")):
            value = diagnostic.get(source)
            if isinstance(value, bool):
                stats[target].append(float(value))
    return stats


def _print_pers_prose_line(label, arm, stats):
    official, n_official = _mean_ci_text(stats["official"])
    pct, n_pct = _mean_ci_text(stats["pct"])
    buy, n_buy = _mean_ci_text(stats["purchase_rate"], percent=True)
    zero, n_zero = _mean_ci_text(stats["zero"], percent=True)
    print(f"{label:9} {arm:9} official-dR={official} n={n_official}; "
          f"local-pct={pct} n={n_pct}; buy={buy} n={n_buy}; "
          f"zero={zero} n={n_zero}; terminal={stats['terminal']} "
          f"pending={stats['pending']} badfin={stats['invalid']} "
          f"official-missing={stats['official_missing']} "
          f"wire-fail={stats['wire_failures']} "
          f"recommend-fail={stats['recommend_failures']}")


def report_pers_prose(rows, hours, since=None, until=None, official_path=None):
    """Report the exact-cell seller wording arm with official delta joins."""
    try:
        official = _load_pers_official_records(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2
    observations = _pers_prose_observations(rows, official)
    print("GLEE_PERS_P08_R125_PROSE_AB, seller/text/p=.8/known-CV/"
          "v=1.25P/20 rounds")
    print("primary: official dashboard per-game rating delta, intent-to-treat; "
          "local percentile is diagnostic only")
    lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
    upper = f"{float(until):g}" if until is not None else "now"
    print(f"first seller-message cohort window: [{lower}, {upper})")
    if not observations:
        print("no assigned exact-cell seller games in the window")
        return 1

    gid_slots = defaultdict(set)
    for observation in observations:
        slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    contaminated = {gid for gid, slots in gid_slots.items() if len(slots) > 1}

    by_slot_arm = defaultdict(list)
    for observation in observations:
        by_slot_arm[(observation["slot"], observation["arm"])].append(observation)
    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        _print_pers_prose_line(
            NAMES.get(slot, slot), arm, _summarize_pers_prose(assigned))

    pooled_obs = [observation for observation in observations
                  if observation["gid"] not in contaminated]
    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [observation for observation in pooled_obs
                    if observation["arm"] == arm]
        if assigned:
            pooled[arm] = _summarize_pers_prose(assigned)
            _print_pers_prose_line("POOLED", arm, pooled[arm])
    print(f"self-play guard: excluded {len(contaminated)} game id(s) observed "
          "in multiple fleet slots; hidden opponents remain a declared risk")

    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("OFFICIAL per-game rating delta",
                     candidate["official"], control["official"])
        _print_delta("local same-cell percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("purchase rate", candidate["purchase_rate"],
                     control["purchase_rate"], percent=True)
        _print_delta("zero-outcome rate", candidate["zero"],
                     control["zero"], percent=True)

    print("predeclared scale diagnostics:")
    for price in (100.0, 10000.0, 1000000.0):
        grouped = {}
        for arm in ("control", "candidate"):
            grouped[arm] = [observation["official"] for observation in pooled_obs
                            if observation["arm"] == arm
                            and _number(observation["diagnostic"].get("price")) == price
                            and observation["official"] is not None]
        if grouped["control"] or grouped["candidate"]:
            delta, lo, hi = _delta_ci(grouped["candidate"], grouped["control"])
            rendered = ("insufficient" if delta is None else
                        f"{delta:+.4f} [{lo:+.4f}, {hi:+.4f}]"
                        if lo is not None else f"{delta:+.4f}")
            print(f"  price={price:g}: official candidate-control {rendered}")

    wire_failures = sum(stats["wire_failures"] + stats["recommend_failures"]
                        for stats in pooled.values())
    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    missing_official = sum(stats["official_missing"] for stats in pooled.values())
    print(f"mechanism failures={wire_failures}; unresolved={unresolved}; "
          f"terminal outcomes missing official delta={missing_official}")
    print("DECISION RULE: first read at 120 resolved official games/arm; promote "
          "only if official-delta 95% CI >0, purchase-rate point >=0 with "
          "lower bound >-2pp, every scale point >=0, and zero mechanism, "
          "self-play, unresolved, invalid, or official-join failures. Reject "
          "on any mechanism failure or an official CI <0 after 50/arm.")
    if wire_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or missing_official or contaminated:
        print("PROMOTION BLOCKED: incomplete or contaminated intent-to-treat cohort")
    return 0


def _print_pers_truth_line(label, arm, stats):
    official, n_official = _mean_ci_text(stats["official"])
    pct, n_pct = _mean_ci_text(stats["pct"])
    purchases, n_purchases = _mean_ci_text(stats["purchases"])
    zero, n_zero = _mean_ci_text(stats["zero"], percent=True)
    print(f"{label:9} {arm:9} official-dR={official} n={n_official}; "
          f"local-pct={pct} n={n_pct}; purchases={purchases} "
          f"n={n_purchases}; zero={zero} n={n_zero}; "
          f"terminal={stats['terminal']} pending={stats['pending']} "
          f"badfin={stats['invalid']} official-missing={stats['official_missing']} "
          f"wire-fail={stats['wire_failures']} "
          f"recommend-fail={stats['recommend_failures']}")


def report_pers_truth(rows, hours, since=None, until=None, official_path=None):
    """Report the exact binary credibility arm using official per-game deltas."""
    try:
        official = _load_pers_official_records(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2
    observations = _pers_truth_observations(rows, official)
    print("GLEE_PERS_P08_R125_BINARY_TRUTH_AB, seller/binary/p=.8/"
          "known-CV/v=1.25P/u=0/20 rounds")
    print("primary: official dashboard per-game rating delta, intent-to-treat; "
          "local percentile is diagnostic only")
    lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
    upper = f"{float(until):g}" if until is not None else "now"
    print(f"first seller-recommendation cohort window: [{lower}, {upper})")
    if not observations:
        print("no assigned exact-cell binary seller games in the window")
        return 1

    gid_slots = defaultdict(set)
    for observation in observations:
        slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    contaminated = {gid for gid, slots in gid_slots.items() if len(slots) > 1}

    by_slot_arm = defaultdict(list)
    for observation in observations:
        by_slot_arm[(observation["slot"], observation["arm"])].append(observation)
    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        _print_pers_truth_line(
            NAMES.get(slot, slot), arm, _summarize_pers_prose(assigned))

    pooled_obs = [observation for observation in observations
                  if observation["gid"] not in contaminated]
    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [observation for observation in pooled_obs
                    if observation["arm"] == arm]
        if assigned:
            pooled[arm] = _summarize_pers_prose(assigned)
            _print_pers_truth_line("POOLED", arm, pooled[arm])
    print(f"self-play guard: excluded {len(contaminated)} game id(s) observed "
          "in multiple fleet slots; hidden opponents remain a declared risk")

    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("OFFICIAL per-game rating delta",
                     candidate["official"], control["official"])
        _print_delta("local same-cell percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("purchase count", candidate["purchases"],
                     control["purchases"])
        _print_delta("zero-outcome rate", candidate["zero"],
                     control["zero"], percent=True)

    print("predeclared scale diagnostics (minimum 8 official/arm at final read):")
    scale_ready = True
    for price in (100.0, 10000.0, 1000000.0):
        grouped = {}
        for arm in ("control", "candidate"):
            grouped[arm] = [observation["official"] for observation in pooled_obs
                            if observation["arm"] == arm
                            and _number(observation["diagnostic"].get("price")) == price
                            and observation["official"] is not None]
        scale_ready &= all(len(grouped[arm]) >= 8
                           for arm in ("control", "candidate"))
        delta, lo, hi = _delta_ci(grouped["candidate"], grouped["control"])
        rendered = ("insufficient" if delta is None else
                    f"{delta:+.4f} [{lo:+.4f}, {hi:+.4f}]"
                    if lo is not None else f"{delta:+.4f}")
        print(f"  price={price:g}: official candidate-control {rendered}; "
              f"n={len(grouped['candidate'])}/{len(grouped['control'])}")

    wire_failures = sum(stats["wire_failures"] + stats["recommend_failures"]
                        for stats in pooled.values())
    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    missing_official = sum(stats["official_missing"] for stats in pooled.values())
    print(f"mechanism failures={wire_failures}; unresolved={unresolved}; "
          f"terminal outcomes missing official delta={missing_official}")
    print("DECISION RULE: one harm look at 20 resolved official games/arm; "
          "reject if the official 95% CI is wholly negative. Fixed final read "
          "at 40/arm and >=8/arm/price; promote only if the official CI is "
          "wholly positive, purchase-count point delta is positive, zero-rate "
          "point delta is nonpositive, all scale points are nonnegative, and "
          "mechanism, self-play, unresolved, invalid, and official joins are clean.")
    if wire_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or missing_official or contaminated or not scale_ready:
        print("PROMOTION BLOCKED: incomplete or contaminated intent-to-treat cohort")
    return 0


def _print_pers_decline_veto_line(label, arm, stats):
    official, n_official = _mean_ci_text(stats["official"])
    pct, n_pct = _mean_ci_text(stats["pct"])
    payoff, n_payoff = _mean_ci_text(stats["payoff_per_price"])
    zero, n_zero = _mean_ci_text(stats["zero"], percent=True)
    negative, n_negative = _mean_ci_text(stats["negative"], percent=True)
    bought_declines, n_declines = _mean_ci_text(stats["bought_declines"])
    print(f"{label:9} {arm:9} official-dR={official} n={n_official}; "
          f"local-pct={pct} n={n_pct}; payoff/P={payoff} n={n_payoff}; "
          f"zero={zero} n={n_zero}; negative={negative} n={n_negative}; "
          f"bought-declines={bought_declines} n={n_declines}; "
          f"terminal={stats['terminal']} pending={stats['pending']} "
          f"badfin={stats['invalid']} official-missing={stats['official_missing']} "
          f"eligible-turns={stats['eligible_turns']} "
          f"veto-traces={stats['veto_traces']} "
          f"wire-fail={stats['wire_failures']}")


def report_pers_decline_veto(rows, hours, since=None, until=None,
                             official_path=None):
    """Report the exact buyer/text explicit-decline veto experiment."""
    try:
        official = _load_pers_official_records(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2
    observations = _pers_decline_veto_observations(rows, official)
    print("GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB, buyer/text/p=.8/"
          "v=1.25P/u=0/20 rounds, union of seller-known and seller-blind "
          "official configurations")
    print("primary: official dashboard per-game rating delta, all-assigned "
          "intent-to-treat; local percentile and fixed message diagnostics "
          "cannot promote")
    lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
    upper = f"{float(until):g}" if until is not None else "now"
    print(f"globally first buyer-decision cohort window: [{lower}, {upper})")
    if not observations:
        print("no assigned exact-cell buyer games in the window")
        return 1

    gid_slots = defaultdict(set)
    for observation in observations:
        slots = observation["diagnostic"].get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[observation["gid"]].update(slots)
        else:
            gid_slots[observation["gid"]].add(observation["slot"])
    contaminated = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    independent = [observation for observation in observations
                   if observation["gid"] not in contaminated]

    by_slot_arm = defaultdict(list)
    for observation in observations:
        by_slot_arm[(observation["slot"], observation["arm"])].append(
            observation)
    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        _print_pers_decline_veto_line(
            NAMES.get(slot, slot), arm,
            _summarize_pers_decline_veto(assigned))

    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [observation for observation in independent
                    if observation["arm"] == arm]
        if assigned:
            pooled[arm] = _summarize_pers_decline_veto(assigned)
            _print_pers_decline_veto_line("POOLED", arm, pooled[arm])
    print(f"self-play guard: excluded {len(contaminated)} game id(s) observed "
          "in multiple fleet slots; hidden opponents remain a declared risk")

    control, candidate = pooled.get("control"), pooled.get("candidate")
    official_delta = official_low = official_high = None
    payoff_delta = zero_delta = negative_delta = None
    if control and candidate:
        print("pooled candidate-control (all-assigned intent-to-treat):")
        _print_delta("OFFICIAL per-game rating delta",
                     candidate["official"], control["official"])
        _print_delta("local same-cell percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("payoff / price", candidate["payoff_per_price"],
                     control["payoff_per_price"])
        _print_delta("zero-outcome rate", candidate["zero"],
                     control["zero"], percent=True)
        _print_delta("negative-outcome rate", candidate["negative"],
                     control["negative"], percent=True)
        _print_delta("purchase rate", candidate["purchase_rate"],
                     control["purchase_rate"], percent=True)
        official_delta, official_low, official_high = _delta_ci(
            candidate["official"], control["official"])
        payoff_delta, _lo, _hi = _delta_ci(
            candidate["payoff_per_price"], control["payoff_per_price"])
        zero_delta, _lo, _hi = _delta_ci(candidate["zero"], control["zero"])
        negative_delta, _lo, _hi = _delta_ci(
            candidate["negative"], control["negative"])

    print("predeclared scale diagnostics (minimum 20 official/arm at final read):")
    scale_ready = True
    scale_nonnegative = True
    for price in (100.0, 10000.0, 1000000.0):
        grouped = {
            arm: [observation["official"] for observation in independent
                  if observation["arm"] == arm
                  and _number(observation["diagnostic"].get("price")) == price
                  and observation["official"] is not None]
            for arm in ("control", "candidate")
        }
        scale_ready &= all(len(grouped[arm]) >= 20
                           for arm in ("control", "candidate"))
        delta, lo, hi = _delta_ci(grouped["candidate"], grouped["control"])
        scale_nonnegative &= delta is not None and delta >= 0.0
        rendered = ("insufficient" if delta is None else
                    f"{delta:+.4f} [{lo:+.4f}, {hi:+.4f}]"
                    if lo is not None else f"{delta:+.4f}")
        print(f"  price={price:g}: official candidate-control {rendered}; "
              f"n={len(grouped['candidate'])}/{len(grouped['control'])}")

    print("predeclared seller-knowledge official-cell diagnostics:")
    knowledge_ready = True
    knowledge_nonnegative = True
    for knows in (True, False):
        grouped = {
            arm: [observation["official"] for observation in independent
                  if observation["arm"] == arm
                  and observation["diagnostic"].get(
                      "is_seller_know_cv") is knows
                  and observation["official"] is not None]
            for arm in ("control", "candidate")
        }
        knowledge_ready &= bool(grouped["control"] and grouped["candidate"])
        delta, lo, hi = _delta_ci(grouped["candidate"], grouped["control"])
        knowledge_nonnegative &= delta is not None and delta >= 0.0
        rendered = ("unavailable" if delta is None else
                    f"{delta:+.4f} [{lo:+.4f}, {hi:+.4f}]"
                    if lo is not None else f"{delta:+.4f}")
        print(f"  is_seller_know_cv={str(knows).lower()}: {rendered}; "
              f"n={len(grouped['candidate'])}/{len(grouped['control'])}")
    unavailable_knowledge = sum(
        observation["diagnostic"].get("is_seller_know_cv") not in (True, False)
        for observation in independent)
    print(f"  unavailable configuration labels={unavailable_knowledge}; never "
          "infer this subgroup from messages or outcomes")

    phrase_counts = Counter()
    for observation in independent:
        for message in observation["diagnostic"].get("seller_messages") or []:
            if reads_as_recommendation_expanded(message) is not False:
                continue
            family = ("legacy-recognized"
                      if reads_as_recommendation_legacy(message) is False
                      else "v2-only")
            phrase_counts[(observation["arm"], family)] += 1
    print("predeclared decline-phrase diagnostics: "
          + ", ".join(
              f"{arm}/{family}={phrase_counts[(arm, family)]}"
              for arm in ("control", "candidate")
              for family in ("legacy-recognized", "v2-only")))

    wire_failures = sum(stats["wire_failures"] for stats in pooled.values())
    veto_traces = sum(stats["veto_traces"] for stats in pooled.values())
    unresolved = sum(stats["pending"] + stats["invalid"]
                     for stats in pooled.values())
    missing_official = sum(stats["official_missing"] for stats in pooled.values())
    print(f"mechanism failures={wire_failures}; veto traces={veto_traces}; "
          f"unresolved={unresolved}; terminal outcomes missing official "
          f"delta={missing_official}")
    print("DECISION RULE: one harm look at 50 resolved official games/arm; "
          "reject if the official 95% CI is wholly negative. Fixed final read "
          "at 120/arm and >=20/arm/price; promote only if official CI >0, "
          "payoff/P point >0, zero and negative-outcome points are nonpositive, "
          "all scale and both seller-knowledge-cell points are nonnegative, "
          "veto-traces>0, and mechanism, "
          "self-play, unresolved, invalid, and official joins are clean.")
    if wire_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if control and candidate:
        harm_ready = all(len(pooled[arm]["official"]) >= 50
                         for arm in ("control", "candidate"))
        if harm_ready and official_high is not None and official_high < 0.0:
            print("OFFICIAL REJECTION: >=50/arm and official-dR CI is below zero")
            return 2
    if (not control or not candidate or unresolved or missing_official
            or contaminated or veto_traces <= 0):
        print("PROMOTION BLOCKED: incomplete, contaminated, or inert "
              "intent-to-treat cohort")
        return 1
    sample_ready = all(len(pooled[arm]["official"]) >= 120
                       for arm in ("control", "candidate"))
    promotable = (
        sample_ready and scale_ready and scale_nonnegative
        and knowledge_ready and knowledge_nonnegative
        and official_delta is not None and official_low is not None
        and official_low > 0.0
        and payoff_delta is not None and payoff_delta > 0.0
        and zero_delta is not None and zero_delta <= 0.0
        and negative_delta is not None and negative_delta <= 0.0
    )
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: sample/official-CI/payoff/bottom-tail/scale "
          "gates are not all satisfied")
    return 1


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


def report_hi_terminal(rows, hours, since=None, until=None,
                       official_path=None):
    """Report the terminal-counter ITT with official rating and wire audits."""
    try:
        official = _load_official_deltas(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2

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
            "official": official.get((slot, gid)),
        })

    title = "GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("ITT eligibility: hidden cap-10 negotiation, our role buyer, own value "
          "1.2*base; cohort begins at the first buyer decision, before terminal "
          "reach or outcome is known")
    print("primary: authenticated dashboard per-game rating delta. Local pct "
          "uses the hidden-value-pooled CDF and is diagnostic only, not the "
          "official full-configuration score")
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
        official_scores = [item["official"] for item in terminal
                           if item["official"] is not None]
        reached = [item for item in terminal
                   if item["diagnostic"].get("reached_terminal_counter")]
        unresolved = len(assigned) - len(terminal)
        official_missing = sum(item["official"] is None for item in terminal)
        stats[arm] = {
            "pct": pcts, "closed": closes, "official": official_scores,
            "reached": reached, "unresolved": unresolved,
            "official_missing": official_missing,
        }
        official_text, _ = _mean_ci_text(official_scores)
        pct_text, _ = _mean_ci_text(pcts)
        close_text, _ = _mean_ci_text(closes, percent=True)
        print(f"POOLED    {arm:9} official-dR={official_text} "
              f"n={len(official_scores)}; local-pct={pct_text} n={len(pcts)}; "
              f"close={close_text} n={len(closes)}; "
              f"terminal-counter={len(reached)}; unresolved={unresolved}; "
              f"official-missing={official_missing}")

    control, candidate = stats.get("control"), stats.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("official rating delta", candidate["official"],
                     control["official"])
        _print_delta("local pooled-CDF percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)

    stratum_deltas = {}
    print("predeclared official point estimates by scale and message setting:")
    for field, values in (("base", (100.0, 10000.0, 1000000.0)),
                          ("messages_allowed", (False, True))):
        for value in values:
            grouped = {
                arm: [item["official"] for item in pooled
                      if item["arm"] == arm
                      and item["diagnostic"].get(field) == value
                      and item["official"] is not None]
                for arm in ("control", "candidate")
            }
            delta, low, high = _delta_ci(
                grouped["candidate"], grouped["control"])
            stratum_deltas[(field, value)] = (delta, grouped)
            rendered = ("official unavailable" if delta is None else
                        f"{delta:+.4f} (CI unavailable)" if low is None else
                        f"{delta:+.4f} [{low:+.4f},{high:+.4f}]")
            print(f"  {field}={value}: {rendered}; "
                  f"n={len(grouped['control'])}/{len(grouped['candidate'])}")

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
    official_missing = sum(value["official_missing"] for value in stats.values())
    print("DECISION RULE: fixed final read at >=100 resolved official games/arm "
          "and >=10/arm in every scale x message cell. Promote only if "
          "official-dR CI >0, close-rate point delta >0 with lower CI >-2pp, "
          "every scale/message point is nonnegative, and all wires/joins/"
          "outcomes are clean. One harm look at >=30 official games/arm rejects "
          "if the official CI is wholly negative.")
    if wire_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or official_missing:
        print(f"PROMOTION BLOCKED: unresolved={unresolved}, terminal outcomes "
              f"missing official delta={official_missing}")
        return 1
    if not control or not candidate:
        print("PROMOTION BLOCKED: both randomized arms need resolved outcomes")
        return 1

    official_delta, official_low, official_high = _delta_ci(
        candidate["official"], control["official"])
    close_delta, close_low, _close_high = _delta_ci(
        candidate["closed"], control["closed"])
    harm_ready = all(len(stats[arm]["official"]) >= 30
                     for arm in ("control", "candidate"))
    if harm_ready and official_high is not None and official_high < 0:
        print("OFFICIAL REJECTION: >=30/arm and official-dR CI is below zero")
        return 2

    sample_ready = all(len(stats[arm]["official"]) >= 100
                       for arm in ("control", "candidate"))
    cells_ready = True
    for base in (100.0, 10000.0, 1000000.0):
        for messages in (False, True):
            cell_counts = {
                arm: sum(
                    item["arm"] == arm
                    and item["diagnostic"].get("base") == base
                    and item["diagnostic"].get("messages_allowed") is messages
                    and item["official"] is not None
                    for item in pooled)
                for arm in ("control", "candidate")
            }
            cells_ready &= all(cell_counts[arm] >= 10
                               for arm in ("control", "candidate"))
    strata_nonnegative = all(
        delta is not None and delta >= 0
        for delta, _grouped in stratum_deltas.values())
    promotable = (
        sample_ready and cells_ready and strata_nonnegative
        and official_delta is not None and official_low is not None
        and official_low > 0 and close_delta is not None and close_delta > 0
        and close_low is not None and close_low > -0.02)
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: sample/official-CI/close/stratum gates are not "
          "all satisfied")
    return 1


def report_hi_buyer_curve(rows, hours, since=None, until=None,
                          official_path=None):
    """Report the broad leader-curve ITT with official and wire gates."""
    try:
        official = _load_official_deltas(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2

    observations = []
    gid_slots = defaultdict(set)
    for slot, pct, gid, closed, *metadata in rows:
        arm = hi_buyer_curve_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal")
        fleet_slots = diagnostic.get("fleet_slots")
        if isinstance(fleet_slots, (list, tuple, set)):
            gid_slots[gid].update(fleet_slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "pct": pct, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic, "resolution": resolution,
            "official": official.get((slot, gid)),
        })

    title = "GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB"
    if since is None and until is None:
        title += f", last {hours:g}h"
    print(title)
    print("ITT eligibility: hidden cap-10 negotiation, our role buyer, own "
          "value in {1.0,1.2,1.5}*base; cohort begins at the first buyer "
          "decision before accept/reject or any candidate price")
    print("candidate: the first four outgoing prices equal the frozen Clod "
          "midpoint curve times our own value; terminal price is current "
          "control in both arms. Primary outcome is authenticated "
          "dashboard rating delta. Local pooled-CDF percentile is diagnostic")
    if since is not None or until is not None:
        lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
        upper = f"{float(until):g}" if until is not None else "now"
        print(f"first buyer-decision exposure window: [{lower}, {upper})")
    if not observations:
        print("no assigned broad hidden cap-10 buyer games in the window")
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
        official_scores = [item["official"] for item in terminal
                           if item["official"] is not None]
        unresolved = len(assigned) - len(terminal)
        official_missing = sum(item["official"] is None for item in terminal)
        counters = sum(
            int(item["diagnostic"].get("curve_counters") or 0)
            for item in terminal)
        stats[arm] = {
            "pct": pcts, "closed": closes, "official": official_scores,
            "unresolved": unresolved, "official_missing": official_missing,
            "curve_counters": counters,
        }
        official_text, _ = _mean_ci_text(official_scores)
        pct_text, _ = _mean_ci_text(pcts)
        close_text, _ = _mean_ci_text(closes, percent=True)
        print(f"POOLED    {arm:9} official-dR={official_text} "
              f"n={len(official_scores)}; local-pct={pct_text} n={len(pcts)}; "
              f"close={close_text} n={len(closes)}; curve-counters={counters}; "
              f"unresolved={unresolved}; official-missing={official_missing}")

    control, candidate = stats.get("control"), stats.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("official rating delta", candidate["official"],
                     control["official"])
        _print_delta("local pooled-CDF percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)

    stratum_deltas = {}
    print("predeclared official point estimates by own type, scale, and messages:")
    for field, values in (
            ("own_mult", (1.0, 1.2, 1.5)),
            ("base", (100.0, 10000.0, 1000000.0)),
            ("messages_allowed", (False, True))):
        for value in values:
            grouped = {
                arm: [item["official"] for item in pooled
                      if item["arm"] == arm
                      and item["diagnostic"].get(field) == value
                      and item["official"] is not None]
                for arm in ("control", "candidate")
            }
            delta, low, high = _delta_ci(
                grouped["candidate"], grouped["control"])
            stratum_deltas[(field, value)] = (delta, grouped)
            rendered = ("official unavailable" if delta is None else
                        f"{delta:+.4f} (CI unavailable)" if low is None else
                        f"{delta:+.4f} [{low:+.4f},{high:+.4f}]")
            print(f"  {field}={value}: {rendered}; "
                  f"n={len(grouped['control'])}/{len(grouped['candidate'])}")

    wire_failures = []
    candidate_counter_count = 0
    for item in pooled:
        if item["arm"] != "candidate" or item["closed"] is None:
            continue
        diagnostic = item["diagnostic"]
        candidate_counter_count += int(diagnostic.get("curve_counters") or 0)
        if diagnostic.get("wire_ok") is not True:
            wire_failures.append((
                item["gid"], diagnostic.get("curve_wire_prices"),
                diagnostic.get("expected_wire_prices")))
    if wire_failures:
        print(f"FALSIFICATION: {len(wire_failures)} candidate game(s) emitted "
              f"a non-curve counter; first={wire_failures[0]}")
    else:
        print(f"wire mechanism: {candidate_counter_count} candidate counter(s), "
              "all on the frozen four-point value-scaled early curve")

    unresolved = sum(value["unresolved"] for value in stats.values())
    official_missing = sum(value["official_missing"] for value in stats.values())
    print("DECISION RULE: one harm look at >=30 official games/arm; reject if "
          "the official-score or close-rate CI is wholly negative. Fixed final "
          "read at >=100 official games/arm and >=15/arm for each own type. "
          "Promote only if official-dR CI >0, close lower CI >-2pp, each own-"
          "type point is nonnegative, no scale/message point is <=-1 rating/"
          "game, and all wires/joins/outcomes are clean.")
    if wire_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or official_missing:
        print(f"PROMOTION BLOCKED: unresolved={unresolved}, terminal outcomes "
              f"missing official delta={official_missing}")
        return 1
    if not control or not candidate:
        print("PROMOTION BLOCKED: both randomized arms need resolved outcomes")
        return 1

    official_delta, official_low, official_high = _delta_ci(
        candidate["official"], control["official"])
    close_delta, close_low, close_high = _delta_ci(
        candidate["closed"], control["closed"])
    harm_ready = all(len(stats[arm]["official"]) >= 30
                     for arm in ("control", "candidate"))
    if harm_ready and ((official_high is not None and official_high < 0)
                       or (close_high is not None and close_high < 0)):
        print("HARM REJECTION: >=30/arm and an official-score/close CI is "
              "wholly negative")
        return 2

    sample_ready = all(len(stats[arm]["official"]) >= 100
                       for arm in ("control", "candidate"))
    types_ready = all(
        len(grouped[arm]) >= 15
        for (field, _value), (_delta, grouped) in stratum_deltas.items()
        if field == "own_mult"
        for arm in ("control", "candidate"))
    type_points_ok = all(
        delta is not None and delta >= 0
        for (field, _value), (delta, _grouped) in stratum_deltas.items()
        if field == "own_mult")
    nuisance_points_ok = all(
        delta is not None and delta > -1.0
        for (field, _value), (delta, _grouped) in stratum_deltas.items()
        if field in ("base", "messages_allowed"))
    promotable = (
        sample_ready and types_ready and type_points_ok and nuisance_points_ok
        and official_delta is not None and official_low is not None
        and official_low > 0 and close_delta is not None
        and close_low is not None and close_low > -0.02)
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: sample/official-CI/close/type/nuisance gates are "
          "not all satisfied")
    return 1


def report_stall_current_break(rows, hours, since=None, until=None,
                               official_path=None):
    """Report the triggered stale-stall A/B over every first-break outcome."""
    try:
        official = _load_official_deltas(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2

    observations = []
    gid_slots = defaultdict(set)
    for slot, pct, gid, closed, *metadata in rows:
        arm = stall_current_break_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal")
        slots = diagnostic.get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[gid].update(slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "pct": pct, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic,
            "resolution": resolution, "official": official.get((slot, gid)),
        })

    print("GLEE_NEGO_STALL_CURRENT_BREAK_AB")
    print("triggered ITT: first decision where three completed opponent offers "
          "look stalled but the standing current offer improves for us by >1%; "
          "accepts, counters, walks, no-deals, and unresolved games all remain")
    print("primary: official dashboard per-game rating delta; local pooled-CDF "
          "percentile is diagnostic only")
    lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
    upper = f"{float(until):g}" if until is not None else "now"
    print(f"first-trigger exposure window: [{lower}, {upper})")
    if not observations:
        print("no assigned favorable current-break games in the window")
        return 1

    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    independent = [item for item in observations if item["gid"] not in duplicates]
    print(f"pooled dependence guard: excluded {len(duplicates)} cross-fleet "
          "game id(s)")

    def summarize(population):
        stats = {
            "official": [], "pct": [], "closed": [], "terminal": 0,
            "pending": 0, "invalid": 0, "official_missing": 0,
            "mechanism_fail": 0, "writer_changed": 0, "countered": 0,
        }
        for item in population:
            diagnostic = item["diagnostic"]
            stats["mechanism_fail"] += int(
                diagnostic.get("mechanism_ok") is not True)
            stats["writer_changed"] += int(
                diagnostic.get("writer_changed") is True)
            stats["countered"] += int(
                diagnostic.get("wire_price") is not None)
            if item["closed"] is None:
                field = ("invalid" if item["resolution"] == "invalid-final"
                         else "pending")
                stats[field] += 1
                continue
            stats["terminal"] += 1
            stats["closed"].append(float(bool(item["closed"])))
            if item["pct"] is not None:
                stats["pct"].append(item["pct"])
            if item["official"] is not None:
                stats["official"].append(item["official"])
            else:
                stats["official_missing"] += 1
        return stats

    def print_line(label, arm, stats):
        official_text, _ = _mean_ci_text(stats["official"])
        pct_text, _ = _mean_ci_text(stats["pct"])
        close_text, _ = _mean_ci_text(stats["closed"], percent=True)
        print(f"{label:18} {arm:9} official-dR={official_text} "
              f"n={len(stats['official'])}; local-pct={pct_text} "
              f"n={len(stats['pct'])}; close={close_text} "
              f"n={len(stats['closed'])}; terminal={stats['terminal']} "
              f"pending={stats['pending']} badfin={stats['invalid']} "
              f"official-missing={stats['official_missing']} "
              f"writer-changed={stats['writer_changed']} "
              f"countered={stats['countered']} "
              f"mechanism-fail={stats['mechanism_fail']}")

    by_slot_arm = defaultdict(list)
    for item in observations:
        by_slot_arm[(item["slot"], item["arm"])].append(item)
    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        print_line(NAMES.get(slot, slot), arm, summarize(assigned))

    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [item for item in independent if item["arm"] == arm]
        if assigned:
            pooled[arm] = summarize(assigned)
            print_line("POOLED", arm, pooled[arm])
    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("official rating delta", candidate["official"],
                     control["official"])
        _print_delta("local pooled-CDF percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)

    def stratum_key(item, field):
        value = item["diagnostic"].get(field)
        if field == "complete":
            return "complete" if value is True else "hidden"
        if field == "messages":
            return "text" if value is True else "silent"
        return str(value)

    print("pre-treatment stratum point estimates (official candidate-control):")
    for field in ("role", "complete", "horizon", "scale", "messages"):
        values = sorted({stratum_key(item, field) for item in independent})
        for value in values:
            population = [item for item in independent
                          if stratum_key(item, field) == value]
            grouped = {
                arm: [item["official"] for item in population
                      if item["arm"] == arm and item["official"] is not None]
                for arm in ("control", "candidate")
            }
            delta, low, high = _delta_ci(
                grouped["candidate"], grouped["control"])
            if delta is None:
                rendered = "official unavailable"
            elif low is None:
                rendered = f"{delta:+.4f} (CI unavailable)"
            else:
                rendered = f"{delta:+.4f} [{low:+.4f},{high:+.4f}]"
            print(f"  {field}={value}: {rendered}; "
                  f"n={len(grouped['control'])}/{len(grouped['candidate'])}")

    # Dependence exclusion protects the causal CI, not mechanism safety. A
    # malformed wire in a cross-fleet duplicate is still a deployment failure.
    mechanism_failures = sum(
        item["diagnostic"].get("mechanism_ok") is not True
        for item in observations)
    unresolved = sum(
        stats["pending"] + stats["invalid"] for stats in pooled.values())
    official_missing = sum(
        stats["official_missing"] for stats in pooled.values())
    print("DECISION RULE: do not decide before 100 resolved official games/arm "
          "and 20/arm in each role. Promote only if official-dR 95% CI >0, "
          "close-rate lower CI >-2pp, every role/information/horizon/scale/"
          "message point estimate is nonnegative, and mechanism failures=0. "
          "Reject on a negative official CI or any mechanism failure.")
    if mechanism_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or official_missing:
        print(f"PROMOTION BLOCKED: unresolved={unresolved}, terminal outcomes "
              f"missing official delta={official_missing}")
        return 1

    if not control or not candidate:
        print("PROMOTION BLOCKED: both randomized arms need resolved outcomes")
        return 1
    official_delta, official_low, official_high = _delta_ci(
        candidate["official"], control["official"])
    _close_delta, close_low, _close_high = _delta_ci(
        candidate["closed"], control["closed"])
    if official_high is not None and official_high < 0:
        print("OFFICIAL REJECTION: official-dR 95% CI is below zero")
        return 2

    arm_minimum_met = all(
        len(pooled[arm]["official"]) >= 100
        for arm in ("control", "candidate"))
    role_minimum_met = True
    stratum_nonnegative = True
    strata_complete = True
    for field in ("role", "complete", "horizon", "scale", "messages"):
        values = {stratum_key(item, field) for item in independent}
        for value in values:
            population = [item for item in independent
                          if stratum_key(item, field) == value]
            grouped = {
                arm: [item["official"] for item in population
                      if item["arm"] == arm and item["official"] is not None]
                for arm in ("control", "candidate")
            }
            delta, _low, _high = _delta_ci(
                grouped["candidate"], grouped["control"])
            strata_complete &= bool(grouped["control"] and grouped["candidate"])
            stratum_nonnegative &= delta is not None and delta >= 0
            if field == "role":
                role_minimum_met &= all(
                    len(grouped[arm]) >= 20
                    for arm in ("control", "candidate"))

    promotable = (
        arm_minimum_met
        and role_minimum_met
        and official_delta is not None
        and official_low is not None
        and official_low > 0
        and close_low is not None
        and close_low > -0.02
        and strata_complete
        and stratum_nonnegative
    )
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: sample/CI/noninferiority/stratum gates are not "
          "all satisfied")
    return 1


def report_hidden_min_share_veto(rows, hours, since=None, until=None,
                                 official_path=None):
    """Report the support-aware low-share acceptance-veto experiment."""
    try:
        official = _load_official_deltas(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2

    observations = []
    gid_slots = defaultdict(set)
    for slot, pct, gid, closed, *metadata in rows:
        arm = hidden_min_share_veto_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal")
        slots = diagnostic.get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[gid].update(slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "pct": pct, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic, "resolution": resolution,
            "official": official.get((slot, gid)),
        })

    print("GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB")
    print("triggered ITT: first nonfinal hidden offer that the current accept stack "
          "would close while paying us <40% of the smallest positive ZOPA allowed "
          "by the validated competition value support")
    print("primary: official dashboard per-game rating delta; local pooled-CDF "
          "percentile is diagnostic only; every agreement/no-deal/walk/pending "
          "outcome remains in its assigned arm")
    lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
    upper = f"{float(until):g}" if until is not None else "now"
    print(f"first-trigger exposure window: [{lower}, {upper})")
    if not observations:
        print("no assigned low-share control-accept opportunities in the window")
        return 1

    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    independent = [item for item in observations if item["gid"] not in duplicates]
    print(f"pooled dependence guard: excluded {len(duplicates)} cross-fleet "
          "game id(s)")

    def summarize(population):
        stats = {
            "official": [], "pct": [], "closed": [], "terminal": 0,
            "pending": 0, "invalid": 0, "official_missing": 0,
            "mechanism_fail": 0, "sources": Counter(),
        }
        for item in population:
            diagnostic = item["diagnostic"]
            stats["mechanism_fail"] += int(
                diagnostic.get("mechanism_ok") is not True)
            stats["sources"][str(diagnostic.get("control_acceptor"))] += 1
            if item["closed"] is None:
                field = ("invalid" if item["resolution"] == "invalid-final"
                         else "pending")
                stats[field] += 1
                continue
            stats["terminal"] += 1
            stats["closed"].append(float(bool(item["closed"])))
            if item["pct"] is not None:
                stats["pct"].append(item["pct"])
            if item["official"] is None:
                stats["official_missing"] += 1
            else:
                stats["official"].append(item["official"])
        return stats

    def print_line(label, arm, stats):
        official_text, _ = _mean_ci_text(stats["official"])
        pct_text, _ = _mean_ci_text(stats["pct"])
        close_text, _ = _mean_ci_text(stats["closed"], percent=True)
        sources = ",".join(f"{key}:{value}" for key, value
                           in sorted(stats["sources"].items()))
        print(f"{label:18} {arm:9} official-dR={official_text} "
              f"n={len(stats['official'])}; local-pct={pct_text} "
              f"n={len(stats['pct'])}; close={close_text} "
              f"n={len(stats['closed'])}; terminal={stats['terminal']} "
              f"pending={stats['pending']} badfin={stats['invalid']} "
              f"official-missing={stats['official_missing']} "
              f"mechanism-fail={stats['mechanism_fail']} sources={sources}")

    by_slot_arm = defaultdict(list)
    for item in observations:
        by_slot_arm[(item["slot"], item["arm"])].append(item)
    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        print_line(NAMES.get(slot, slot), arm, summarize(assigned))

    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [item for item in independent if item["arm"] == arm]
        if assigned:
            pooled[arm] = summarize(assigned)
            print_line("POOLED", arm, pooled[arm])
    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("official rating delta", candidate["official"],
                     control["official"])
        _print_delta("local pooled-CDF percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)

    def stratum_value(item, field):
        value = item["diagnostic"].get(field)
        if field == "messages":
            return "text" if value is True else "silent"
        return str(value)

    print("pre-treatment stratum point estimates (official candidate-control):")
    stratum_deltas = {}
    for field in ("role", "horizon", "own_multiplier", "scale", "messages",
                  "control_acceptor"):
        values = sorted({stratum_value(item, field) for item in independent})
        for value in values:
            population = [item for item in independent
                          if stratum_value(item, field) == value]
            grouped = {
                arm: [item["official"] for item in population
                      if item["arm"] == arm and item["official"] is not None]
                for arm in ("control", "candidate")
            }
            delta, low, high = _delta_ci(
                grouped["candidate"], grouped["control"])
            stratum_deltas[(field, value)] = (delta, grouped)
            if delta is None:
                rendered = "official unavailable"
            elif low is None:
                rendered = f"{delta:+.4f} (CI unavailable)"
            else:
                rendered = f"{delta:+.4f} [{low:+.4f},{high:+.4f}]"
            print(f"  {field}={value}: {rendered}; "
                  f"n={len(grouped['control'])}/{len(grouped['candidate'])}")

    mechanism_failures = sum(
        item["diagnostic"].get("mechanism_ok") is not True
        for item in observations)
    unresolved = sum(
        stats["pending"] + stats["invalid"] for stats in pooled.values())
    official_missing = sum(
        stats["official_missing"] for stats in pooled.values())
    print("DECISION RULE: efficacy only at >=100 resolved official games/arm and "
          ">=20/arm in each role. Promote if official-dR 95% CI >0, close-rate "
          "point delta >=-5pp, both role point estimates are nonnegative, and "
          "mechanism failures=0. At >=30/arm reject for official-dR 95% CI <0; "
          "reject immediately for any mechanism failure.")
    if mechanism_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or official_missing:
        print(f"PROMOTION BLOCKED: unresolved={unresolved}, terminal outcomes "
              f"missing official delta={official_missing}")
        return 1
    if not control or not candidate:
        print("PROMOTION BLOCKED: both randomized arms need resolved outcomes")
        return 1

    official_delta, official_low, official_high = _delta_ci(
        candidate["official"], control["official"])
    close_delta, _close_low, _close_high = _delta_ci(
        candidate["closed"], control["closed"])
    reached_harm_look = all(len(pooled[arm]["official"]) >= 30
                            for arm in ("control", "candidate"))
    if reached_harm_look and official_high is not None and official_high < 0:
        print("OFFICIAL REJECTION: >=30/arm and official-dR 95% CI is below zero")
        return 2

    arm_minimum_met = all(len(pooled[arm]["official"]) >= 100
                          for arm in ("control", "candidate"))
    role_minimum_met = True
    role_nonnegative = True
    for value in ("buyer", "seller"):
        delta, grouped = stratum_deltas.get(("role", value), (None, {}))
        role_nonnegative &= delta is not None and delta >= 0
        role_minimum_met &= bool(grouped) and all(
            len(grouped[arm]) >= 20 for arm in ("control", "candidate"))
    promotable = (
        arm_minimum_met and role_minimum_met and role_nonnegative
        and official_delta is not None and official_low is not None
        and official_low > 0 and close_delta is not None and close_delta >= -0.05)
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: sample/official-CI/close/role gates are not all "
          "satisfied")
    return 1


def report_table_vcont_precedence(rows, hours, since=None, until=None,
                                  official_path=None):
    """Report direct TABLE acceptance versus observed continuation value."""
    try:
        official = _load_official_deltas(official_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot load official delta export: {exc}")
        return 2

    observations = []
    gid_slots = defaultdict(set)
    for slot, pct, gid, closed, *metadata in rows:
        arm = table_vcont_precedence_arm(gid)
        if arm is None:
            continue
        diagnostic = next(
            (item for item in metadata if isinstance(item, dict)), {})
        resolution = next(
            (item for item in metadata if isinstance(item, str)),
            "unresolved" if closed is None else "terminal")
        slots = diagnostic.get("fleet_slots")
        if isinstance(slots, (list, tuple, set)):
            gid_slots[gid].update(slots)
        else:
            gid_slots[gid].add(slot)
        observations.append({
            "slot": slot, "pct": pct, "gid": gid, "closed": closed,
            "arm": arm, "diagnostic": diagnostic, "resolution": resolution,
            "official": official.get((slot, gid)),
        })

    print("GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB")
    print("triggered ITT: first nonfinal hidden offer that directly clears TABLE "
          "while three distinct improving opponent prices imply continuation "
          "value above accept-now surplus; low-share and next-stall accepts "
          "remain outside the cohort")
    print("primary: official dashboard per-game rating delta; local pooled-CDF "
          "percentile is diagnostic only; every agreement/no-deal/walk/pending "
          "outcome remains in its assigned arm")
    lower = f"{float(since):g}" if since is not None else f"now-{hours:g}h"
    upper = f"{float(until):g}" if until is not None else "now"
    print(f"first-trigger exposure window: [{lower}, {upper})")
    if not observations:
        print("no assigned TABLE-versus-continuation opportunities in the window")
        return 1

    duplicates = {gid for gid, slots in gid_slots.items() if len(slots) > 1}
    independent = [item for item in observations if item["gid"] not in duplicates]
    print(f"pooled dependence guard: excluded {len(duplicates)} cross-fleet "
          "game id(s)")

    def summarize(population):
        stats = {
            "official": [], "pct": [], "closed": [], "terminal": 0,
            "pending": 0, "invalid": 0, "official_missing": 0,
            "mechanism_fail": 0, "countered": 0,
        }
        for item in population:
            diagnostic = item["diagnostic"]
            stats["mechanism_fail"] += int(
                diagnostic.get("mechanism_ok") is not True)
            stats["countered"] += int(
                diagnostic.get("action_decision") == "RejectOffer")
            if item["closed"] is None:
                field = ("invalid" if item["resolution"] == "invalid-final"
                         else "pending")
                stats[field] += 1
                continue
            stats["terminal"] += 1
            stats["closed"].append(float(bool(item["closed"])))
            if item["pct"] is not None:
                stats["pct"].append(item["pct"])
            if item["official"] is None:
                stats["official_missing"] += 1
            else:
                stats["official"].append(item["official"])
        return stats

    def print_line(label, arm, stats):
        official_text, _ = _mean_ci_text(stats["official"])
        pct_text, _ = _mean_ci_text(stats["pct"])
        close_text, _ = _mean_ci_text(stats["closed"], percent=True)
        print(f"{label:18} {arm:9} official-dR={official_text} "
              f"n={len(stats['official'])}; local-pct={pct_text} "
              f"n={len(stats['pct'])}; close={close_text} "
              f"n={len(stats['closed'])}; terminal={stats['terminal']} "
              f"pending={stats['pending']} badfin={stats['invalid']} "
              f"official-missing={stats['official_missing']} "
              f"countered={stats['countered']} "
              f"mechanism-fail={stats['mechanism_fail']}")

    by_slot_arm = defaultdict(list)
    for item in observations:
        by_slot_arm[(item["slot"], item["arm"])].append(item)
    for (slot, arm), assigned in sorted(by_slot_arm.items()):
        print_line(NAMES.get(slot, slot), arm, summarize(assigned))

    pooled = {}
    for arm in ("control", "candidate"):
        assigned = [item for item in independent if item["arm"] == arm]
        if assigned:
            pooled[arm] = summarize(assigned)
            print_line("POOLED", arm, pooled[arm])
    control, candidate = pooled.get("control"), pooled.get("candidate")
    if control and candidate:
        print("pooled candidate-control (intent-to-treat):")
        _print_delta("official rating delta", candidate["official"],
                     control["official"])
        _print_delta("local pooled-CDF percentile (diagnostic)",
                     candidate["pct"], control["pct"])
        _print_delta("close rate", candidate["closed"], control["closed"],
                     percent=True)

    def stratum_value(item, field):
        value = item["diagnostic"].get(field)
        if field == "messages":
            return "text" if value is True else "silent"
        return str(value)

    print("pre-treatment stratum point estimates (official candidate-control):")
    stratum_deltas = {}
    for field in ("role", "horizon", "own_multiplier", "scale", "messages"):
        values = sorted({stratum_value(item, field) for item in independent})
        for value in values:
            population = [item for item in independent
                          if stratum_value(item, field) == value]
            grouped = {
                arm: [item["official"] for item in population
                      if item["arm"] == arm and item["official"] is not None]
                for arm in ("control", "candidate")
            }
            delta, low, high = _delta_ci(
                grouped["candidate"], grouped["control"])
            stratum_deltas[(field, value)] = (delta, grouped)
            if delta is None:
                rendered = "official unavailable"
            elif low is None:
                rendered = f"{delta:+.4f} (CI unavailable)"
            else:
                rendered = f"{delta:+.4f} [{low:+.4f},{high:+.4f}]"
            print(f"  {field}={value}: {rendered}; "
                  f"n={len(grouped['control'])}/{len(grouped['candidate'])}")

    mechanism_failures = sum(
        item["diagnostic"].get("mechanism_ok") is not True
        for item in observations)
    unresolved = sum(
        stats["pending"] + stats["invalid"] for stats in pooled.values())
    official_missing = sum(
        stats["official_missing"] for stats in pooled.values())
    print("DECISION RULE: efficacy only at >=100 resolved official games/arm "
          "and >=20/arm in each role. Promote if official-dR 95% CI >0, "
          "close-rate lower 95% bound >-2pp, every role/horizon/own-type point "
          "estimate is nonnegative, and mechanism failures=0. At >=30/arm "
          "reject for official-dR 95% CI <0; reject immediately for any "
          "mechanism failure.")
    if mechanism_failures:
        print("MECHANISM REJECTION: disarm immediately")
        return 2
    if unresolved or official_missing:
        print(f"PROMOTION BLOCKED: unresolved={unresolved}, terminal outcomes "
              f"missing official delta={official_missing}")
        return 1
    if not control or not candidate:
        print("PROMOTION BLOCKED: both randomized arms need resolved outcomes")
        return 1

    official_delta, official_low, official_high = _delta_ci(
        candidate["official"], control["official"])
    _close_delta, close_low, _close_high = _delta_ci(
        candidate["closed"], control["closed"])
    reached_harm_look = all(len(pooled[arm]["official"]) >= 30
                            for arm in ("control", "candidate"))
    if reached_harm_look and official_high is not None and official_high < 0:
        print("OFFICIAL REJECTION: >=30/arm and official-dR 95% CI is below zero")
        return 2

    arm_minimum_met = all(len(pooled[arm]["official"]) >= 100
                          for arm in ("control", "candidate"))
    role_minimum_met = True
    for value in ("buyer", "seller"):
        _delta, grouped = stratum_deltas.get(("role", value), (None, {}))
        role_minimum_met &= bool(grouped) and all(
            len(grouped[arm]) >= 20 for arm in ("control", "candidate"))
    protected_strata = ("role", "horizon", "own_multiplier")
    stratum_nonnegative = all(
        delta is not None and delta >= 0
        for (field, _value), (delta, _grouped) in stratum_deltas.items()
        if field in protected_strata)
    promotable = (
        arm_minimum_met and role_minimum_met and stratum_nonnegative
        and official_delta is not None and official_low is not None
        and official_low > 0 and close_low is not None and close_low > -0.02)
    if promotable:
        print("PROMOTION GATE PASSED")
        return 0
    print("PROMOTION BLOCKED: sample/official-CI/close/stratum gates are not "
          "all satisfied")
    return 1


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
    ap.add_argument("--official-json", default=None,
                    help="dashboard export containing slot, game_id, and "
                         "rating_delta records for an official-join A/B")
    ap.add_argument("--ab", nargs="?", const="zopa",
                    choices=("zopa", "rank-price", "open-claim",
                             "open-claim-official", "hidden-floor",
                             "hidden-policy", "hi-first-offer", "hi-extreme-open",
                             "hi-terminal", "hi-buyer-curve",
                             "stall-current-break",
                             "hidden-min-share-veto", "table-vcont-precedence",
                             "fp-complete", "pers-selectivity", "pers-prose",
                             "pers-truth", "pers-decline-veto",
                             "barg-msg"),
                    help="split games by a recoverable hash arm; bare --ab "
                         "keeps the legacy GLEE_NEGO_ZOPA_AB report")
    args = ap.parse_args()
    keep = {s.strip() for s in args.slots.split(",") if s.strip()}

    if args.ab in ("open-claim", "open-claim-official", "hidden-floor",
                   "hidden-policy", "hi-first-offer", "hi-extreme-open",
                   "hi-terminal", "hi-buyer-curve", "stall-current-break",
                   "hidden-min-share-veto",
                   "table-vcont-precedence",
                   "fp-complete",
                   "pers-selectivity", "pers-prose", "pers-truth",
                   "pers-decline-veto"):
        if (args.since is not None and args.until is not None
                and args.until <= args.since):
            ap.error("--until must be greater than --since")
        cohort = {
            "open-claim": open_claim_games,
            "open-claim-official": open_claim_official_games,
            "hidden-floor": hidden_floor_games,
            "hidden-policy": hidden_policy_games,
            "hi-first-offer": hi_first_offer_games,
            "hi-extreme-open": hi_extreme_open_games,
            "hi-terminal": hi_terminal_games,
            "hi-buyer-curve": hi_buyer_curve_games,
            "stall-current-break": stall_current_break_games,
            "hidden-min-share-veto": hidden_min_share_veto_games,
            "table-vcont-precedence": table_vcont_precedence_games,
            "fp-complete": fp_complete_games,
            "pers-selectivity": pers_selectivity_games,
            "pers-prose": pers_prose_games,
            "pers-truth": pers_truth_games,
            "pers-decline-veto": pers_decline_veto_games,
        }[args.ab]
        reporter = {
            "open-claim": report_open_claim,
            "open-claim-official": report_open_claim_official,
            "hidden-floor": report_hidden_floor,
            "hidden-policy": report_hidden_policy,
            "hi-first-offer": report_hi_first_offer,
            "hi-extreme-open": report_hi_extreme_open,
            "hi-terminal": report_hi_terminal,
            "hi-buyer-curve": report_hi_buyer_curve,
            "stall-current-break": report_stall_current_break,
            "hidden-min-share-veto": report_hidden_min_share_veto,
            "table-vcont-precedence": report_table_vcont_precedence,
            "fp-complete": report_fp_complete,
            "pers-selectivity": report_pers_selectivity,
            "pers-prose": report_pers_prose,
            "pers-truth": report_pers_truth,
            "pers-decline-veto": report_pers_decline_veto,
        }[args.ab]
        price_rows = [r for r in cohort(
            args.hours, since=args.since, until=args.until)
            if not keep or r[0] in keep]
        extra = ({"official_path": args.official_json}
                 if args.ab in ("pers-prose", "pers-truth",
                                "pers-decline-veto", "stall-current-break",
                                "hidden-min-share-veto", "hi-terminal",
                                "hi-buyer-curve",
                                "table-vcont-precedence") else {})
        return reporter(price_rows, args.hours, since=args.since,
                        until=args.until, **extra)

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
