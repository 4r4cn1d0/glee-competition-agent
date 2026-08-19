"""Pre-specified analysis of the randomised message-framing experiment.

This file is written BEFORE any experimental record exists. That is the whole
point of it: the estimator, the outcomes, the clustering, the multiplicity
correction and the thresholds that turn a number into a verdict are all fixed
here, in code, so that none of them can be chosen after seeing a result. The
frozen text of that commitment is the ``PREREGISTRATION`` string below; its
SHA-256 is recomputed at import and printed at the top of every report, so a
later edit to any part of the commitment is visible in the output of every run
that follows it.

    $ .venv/bin/python -m experiments.analyse_framing prereg      # the commitment + its hash
    $ .venv/bin/python -m experiments.analyse_framing report      # analyse logs/
    $ .venv/bin/python -m experiments.analyse_framing validate    # simulation study

What it estimates
-----------------
    Delta P_accept(m) = P(accept | offer x, framing m) - P(accept | offer x, A1-neutral)

held at a fixed numeric action, because ``experiments/assign.py`` draws the arm
strictly downstream of ``coerce()`` and fingerprints the numeric fields either
side of the message hook. This module never re-derives that guarantee, it
*checks* it (balance check B0) and refuses to report anything if it failed.

Three design facts drive every choice below
-------------------------------------------
1. **Randomisation is a stratified permuted block over ``block_key`` = stratum x
   arm-pool, per assignment stream.** So the estimator is a within-block one:
   a Mantel-Haenszel stratified risk difference over the *realised randomisation
   blocks*, not a pooled two-by-two. Pooling across blocks is confounded by the
   pool, which is state-dependent (assign.py measured this: an arm/share
   correlation with p=0.000 conditioning on ``stratum_id`` versus p=0.377
   conditioning on ``block_key``, on the same replay).

2. **Observations are not independent.** Offers within a game share an
   opponent, an opponent recurs across games, and a configuration (horizon,
   information, discount factors, pot) recurs across both. Variance is therefore
   two-way cluster-robust on (opponent identity) x (configuration), computed
   from the estimator's own influence function, with a small-cluster t
   reference distribution.

3. **``opponent_class`` is inside the block key.** So a within-block
   re-randomisation is automatically a within-opponent-class re-randomisation:
   the randomisation-inference p-value below is exact under the sharp null and
   respects the opponent structure without assuming anything about it. It is
   the arbiter when the cluster count is small, which it will be.

The verdict lattice, which is the part the brief cares about most
-----------------------------------------------------------------
A noisy point estimate is not a finding. Every contrast is resolved to exactly
one of:

    HARD_FAIL           balance or numeric invariance broke; nothing is reported
    INSUFFICIENT_POWER  realised precision cannot see the effect the design was
                        built for; the estimate is printed but is NOT a finding
    EFFECT_POSITIVE     adjusted interval excludes 0 and the conservative
    EFFECT_NEGATIVE     p-value clears the Holm-adjusted level
    NULL_RULED_OUT      powered, and the interval excludes everything worth
                        shipping (|effect| < 3 points) -- a real negative result
    INCONCLUSIVE        powered enough to pass the MDE gate, interval still
                        spans both 0 and a shippable effect

``NULL_RULED_OUT`` and ``INSUFFICIENT_POWER`` are different findings and are
never printed with the same words.
"""

from __future__ import annotations

import glob
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict

__all__ = [
    "PREREGISTRATION", "PREREG_SHA256", "THRESHOLDS",
    "Unit", "Estimate", "BalanceItem", "BalanceReport", "AnalysisReport",
    "load_records", "load_games", "build_units", "dedupe_records",
    "balance_check", "estimate_contrast", "run_analysis", "format_report",
    "simulate_units", "simulate_to_disk", "validate",
    "mh_risk_difference", "cluster_variance", "block_variance",
    "holm", "randomisation_p",
]


# ==========================================================================
# 1. THE COMMITMENT
# ==========================================================================

PREREGISTRATION = """\
PRE-REGISTERED ANALYSIS -- message-framing experiment (framing-1)
=================================================================
Written before the first record exists. Frozen by the SHA-256 of this text.

P0. POPULATION AND UNIT
  Unit: one assigned decision point -- an offer of ours that carried (or, for
  arm A0, deliberately did not carry) an experimental message, recorded in
  <log_dir>/experiment.jsonl by experiments/assign.py.
  Included: records with experiment.outcome in {"sent","silent"} and a non-null
  experiment.arm.
  Excluded, and counted in the intake table rather than dropped silently:
  outcome in {"ineligible","no_arm_defined","compose_failed"} (never assigned or
  never delivered), duplicate presentations of one decision_key (SDK retry --
  the earliest record is kept), and assigned offers that never received an
  opponent response because the game ended (censored; reported as a rate per
  arm, and a differential censoring rate is itself a balance failure).

P1. PRIMARY OUTCOME  (one, named, binary)
  accepted -- 1 if the opponent accepted the very offer this message was
  attached to, 0 if they rejected it or walked away from it.
    bargaining: the history entry at our round r whose proposer is us; its
      "decision" field is the opponent's response. accept -> 1, reject -> 0,
      walkaway -> 0.
    negotiation: the first history entry with offer.from_player == us and round
      >= r (our counteroffer at round r is submitted as a decision carrying
      product_price and surfaces as the offer at round r+1); its "decision" is
      the opponent's. AcceptOffer -> 1, RejectOffer -> 0, WalkAway -> 0.
  The join is verified against the submitted number (gains in bargaining, price
  in negotiation); a mismatch marks the unit unjoined rather than guessing.

P2. PRIMARY CONTRASTS  (two families, declared separately on purpose)
  FAMILY M ("does opening our mouth help"): A0-silent vs A1-neutral. One
    contrast, tested at alpha=0.05 with no correction, because it is one
    pre-specified question and correcting it against the framing family would
    penalise it for questions it does not ask.
  FAMILY F ("does the argument help"): each framing arm F1..F6 vs A1-neutral.
    Holm-Bonferroni across the framing contrasts actually present in the data,
    family-wise alpha=0.05. Confirmatory intervals use the Bonferroni level
    alpha/k_F; unadjusted intervals are printed beside them and are descriptive.
  A0 is NEVER the reference for a framing contrast. A framing measured against
  silence is confounded with the presence of text; a framing measured against an
  unpadded neutral is confounded with length. A1 is length-matched for exactly
  this reason and is the only admissible reference.

P3. PRIMARY ESTIMATOR  (within-block, matching the randomisation)
  Mantel-Haenszel stratified risk difference over the realised randomisation
  blocks. The analysis stratum is
      (arm_set_version, experiment_id, probe, block_key, block_index)
  i.e. one permuted block of one assignment stream -- the finest stratum at
  which the assignment was actually randomised. block_key already carries
  venue x share bucket x opponent class x round class x arm pool.
      Delta_hat = sum_b w_b (ybar_{b,arm} - ybar_{b,A1}) / sum_b w_b,
      w_b = n_{b,arm} n_{b,A1} / (n_{b,arm} + n_{b,A1}).
  Blocks containing only one of the two arms get weight 0 and are reported as
  non-informative rather than pooled in.
  Pre-specified sensitivities, reported always, never substituted for the
  primary: (a) coarse stratum (arm_set_version, block_key), (b) Hajek IPW
  weighted by 1/p_assign_conditional within stratum -- the recorded conditional
  propensity, not the marginal p_assign, because under permuted blocks the
  realised per-draw probability is not 1/k.

P4. VARIANCE AND INTERVALS  (clustered)
  A full block holds 2 units of a framing arm and 4 of the neutral control, so
  there is no usable within-block variance. The variance is therefore the
  standard one for a finely stratified (essentially paired) design: the spread
  of the block-level differences about the estimate,
      c_b = (w_b / W) (d_b - Delta_hat),   V = B/(B-1) sum_b c_b^2,
  which is valid whatever the dependence WITHIN a block. Clustering extends it
  to dependence ACROSS blocks by splitting each block's contribution over the
  clusters its units belong to and leaving the unattributable part independent
  (the formula is in cluster_variance's docstring and collapses to the line
  above when blocks nest inside clusters). Clusterings, all pre-specified:
    cluster_opponent = opponent_name when the opponent is named; for a hidden
      opponent the identity is not observable and each hidden game is treated as
      one draw ("hidden::<probe>::<game_id>"), which nests offers within a game.
    cluster_config  = (venue, horizon_known, complete_information,
      money_to_divide, delta_me, delta_opp, max_rounds).
    cluster_game    = one game.
    two-way opponent x config, Cameron-Gelbach-Miller, floored at
      max(V_opp, V_cfg) if the correction drives it non-positive.
  PRIMARY INTERVAL = the WIDEST of those four. A fixed rule, fixed here, that
  always resolves the same way; every component is printed so the choice is
  auditable. It is the honest response to clusterings that do not nest and
  therefore disagree. Reference distribution t, df = min(G_selected, B) - 1.
  Also printed, never substituted: the block-only variance and the conservative
  clustering that pools every hidden game into one "hidden" cluster.
  P-value used for the verdict = max(cluster-robust p, randomisation p). The
  randomisation p re-randomises arm labels within analysis block, 20000 draws,
  seed 20260819; because opponent_class is inside block_key this is exact under
  the sharp null AND within-opponent by construction, and it is exact under
  arbitrary dependence between units because the assignment really was made per
  decision point. Taking the max is deliberate: the analytic interval can be
  anti-conservative and the randomisation test is the one that cannot lie.

P5. SECONDARY OUTCOMES  (four, named, in this order, gatekept)
  S1 opp_concession_next  continuous. Bargaining: share-of-pot the opponent's
     next proposal gives us, minus the share their previous proposal gave us
     (undefined at round 1). Negotiation: their next price minus their previous
     price, signed toward us and normalised by our valuation. Defined only on
     rejected offers with an opponent offer on both sides.
  S2 settle_round        integer, censored, defined for every game:
     agreed_round if agreement, else rounds_played + 1. The agreement-only
     version is printed beside it and is explicitly NOT causal (conditioning on
     a post-treatment outcome); the agreement rate is printed with it.
  S3 realised_share      our realised payoff normalised (bargaining: by the pot;
     negotiation: by our valuation), no-deal and walk-away coded 0.
  S4 walked_away         1 if the game ended in a walk-away.
  S2-S4 are game-level. The game's arm is the arm of its FIRST assigned unit
  (first-exposure intention-to-treat, which is randomised); the pure-arm subset
  is a reported sensitivity, not the primary, because purity is post-treatment.
  Multiplicity: Holm within the secondary family (arms x outcomes), and
  GATEKEPT -- a secondary contrast is reported as confirmatory only if that
  arm's primary contrast reached EFFECT_*. Otherwise it is labelled supportive.

P6. BALANCE  (the first thing to look at, and the first thing to break)
  B0 numeric invariance: any record with numeric_invariant_ok false, or any
     outcome == "invariance_violation" -> HARD_FAIL, no effect is reported.
  B1 share-on-arm: within-block mean difference of share_to_responder for each
     arm vs A1, with a within-block permutation p on the max |difference|.
     p < 0.01 -> HARD_FAIL. p < 0.05 -> WARN. This is the design's own 5(f)
     proof run on the real data.
  B2 blocked variables constant within block (structural; a violation means the
     log is corrupt) and non-blocked covariates balanced across arms by
     within-block permutation.
  B3 allocation: realised arm counts against sum of recorded
     p_assign_conditional. |z| > 4 -> HARD_FAIL, > 3 -> WARN.
  B4 length: |median(len_arm) - median(len_A1)| > 40 chars -> that contrast is
     reported CONFOUNDED WITH VERBOSITY and cannot reach EFFECT_*.
  B5 differential censoring: unjoined rate differs across arms, permutation
     p < 0.01 -> HARD_FAIL.

P7. POWER GATE  (an explicit refusal, not a small p)
  Realised MDE = (t_{1-a/2,df} + t_{0.8,df}) * SE_primary at the Bonferroni
  level for that family. A contrast is INSUFFICIENT_POWER, and reports NO
  finding, if any of:
      n_arm < 60, or n_A1 < 60
      informative blocks < 5
      effective clusters (min of the two dimensions) < 5
      realised MDE > 0.10   (the design is honest that it is powered for a
                             10-point shift and not for a 5-point one)
  SHIP_THRESHOLD = 0.03. Powered and interval inside +-0.03 -> NULL_RULED_OUT.
  Powered, interval spans 0 and something >= 0.03 -> INCONCLUSIVE.

P8. NO OPTIONAL STOPPING, NO OPTIONAL ANALYSIS
  Safety monitoring (assign.py 6.2 / experiments/monitor.py) is not inference
  and spends no alpha. This module runs at the end of a stage. Interim runs are
  permitted for balance and safety only and must be invoked with --interim,
  which suppresses every effect estimate.
"""

PREREG_SHA256 = hashlib.sha256(PREREGISTRATION.encode("utf-8")).hexdigest()

#: Every threshold that turns a number into a verdict. Frozen with the prereg.
THRESHOLDS = {
    "alpha": 0.05,
    "power_target": 0.80,
    "mde_ceiling": 0.10,          # P7: realised MDE above this -> no finding
    "ship_threshold": 0.03,       # P7: smallest effect worth deploying
    "min_n_per_arm": 60,
    "min_informative_blocks": 5,
    "min_clusters": 5,
    "length_tolerance_chars": 40,  # P6/B4, design 5(e)
    "balance_fail_p": 0.01,
    "balance_warn_p": 0.05,
    "allocation_fail_z": 4.0,
    "allocation_warn_z": 3.0,
    "ri_draws": 20000,
    "ri_seed": 20260819,
    "balance_ri_draws": 4000,
}

CONTROL_SILENT = "A0"
CONTROL_NEUTRAL = "A1"
FRAMING_ARMS = ("F1", "F2", "F3", "F4", "F5", "F6")
PRIMARY_OUTCOME = "accepted"
SECONDARY_OUTCOMES = ("opp_concession_next", "settle_round", "realised_share",
                      "walked_away")
GAME_LEVEL_OUTCOMES = frozenset({"settle_round", "realised_share", "walked_away"})
BINARY_OUTCOMES = frozenset({"accepted", "walked_away"})


# ==========================================================================
# 2. STATISTICS PRIMITIVES
#
# Stdlib only, like assign.py and framing.py: numpy/scipy are not installed in
# the fleet's venv and adding a dependency to the analysis of a live experiment
# is a good way to have no analysis at all on the day it matters.
# ==========================================================================

_SQRT2 = math.sqrt(2.0)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


def norm_sf(x: float) -> float:
    return 0.5 * math.erfc(x / _SQRT2)


def norm_ppf(p: float) -> float:
    """Inverse standard normal. Acklam's rational approximation, one Halley
    refinement -- accurate to ~1e-15, which is more than any of this needs."""
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    elif p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    else:
        q, r = p - 0.5, (p - 0.5) ** 2
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    e = norm_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta (Lentz)."""
    tiny = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-16:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a,b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    front = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + b * math.log(1.0 - x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b


def t_sf(t: float, df: float) -> float:
    """Upper tail of Student's t."""
    if df <= 0:
        return float("nan")
    if df > 4000:                      # numerically indistinguishable
        return norm_sf(t)
    x = df / (df + t * t)
    p = 0.5 * betainc(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def t_two_sided_p(t: float, df: float) -> float:
    if df is None or df <= 0 or not math.isfinite(t):
        return float("nan")
    return min(1.0, 2.0 * t_sf(abs(t), df))


def t_ppf(p: float, df: float) -> float:
    """Quantile of Student's t by bisection on the CDF. df<=0 -> +inf, which
    makes every interval infinite, which is the honest answer when there is no
    residual degree of freedom left to estimate a variance with."""
    if df is None or df <= 0:
        return float("inf")
    if df > 4000:
        return norm_ppf(p)
    lo, hi = -400.0, 400.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 1.0 - t_sf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def chi2_sf(x: float, df: int) -> float:
    """Upper tail of chi-square via the regularised upper incomplete gamma."""
    if df <= 0 or x <= 0:
        return 1.0
    a, xx = df / 2.0, x / 2.0
    if xx < a + 1.0:                    # series for P(a,x)
        term = 1.0 / a
        total = term
        n = a
        for _ in range(2000):
            n += 1.0
            term *= xx / n
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        return max(0.0, 1.0 - total * math.exp(-xx + a * math.log(xx) - math.lgamma(a)))
    tiny = 1e-300                       # continued fraction for Q(a,x)
    b = xx + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-16:
            break
    return max(0.0, min(1.0, math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h))


def holm(pairs):
    """Holm-Bonferroni step-down. ``pairs`` is [(key, p), ...]; returns
    {key: adjusted_p}. Monotone-enforced, capped at 1."""
    items = [(k, (p if (p is not None and math.isfinite(p)) else 1.0)) for k, p in pairs]
    order = sorted(range(len(items)), key=lambda i: items[i][1])
    m = len(items)
    out, running = {}, 0.0
    for rank, i in enumerate(order):
        key, p = items[i]
        adj = min(1.0, (m - rank) * p)
        running = max(running, adj)
        out[key] = running
    return out


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _median(values):
    values = sorted(v for v in values if v is not None)
    return statistics.median(values) if values else None


# ==========================================================================
# 3. DATA LAYER
#
# One experiment record + the game it belongs to -> one Unit. Everything the
# estimator, the balance check and the intake table need is materialised here
# so that no downstream function has to re-parse a log or guess a schema.
# ==========================================================================

@dataclass
class Unit:
    # identity
    probe: str
    game_id: str
    round: int | None
    ts: float
    decision_key: str
    experiment_id: str
    arm_set_version: str
    # design
    arm: str
    block_key: str
    block_index: int | None
    stratum_id: str
    pool_id: str | None
    arm_pool: tuple
    p_assign: float | None
    p_assign_conditional: float | None
    # blocking / covariates
    venue: str | None
    share_to_responder: float | None
    share_bucket: str | None
    opponent_class: str | None
    opponent_name: str | None
    round_class: str | None
    horizon_known: object = None
    complete_information: object = None
    delta_me: float | None = None
    delta_opp: float | None = None
    rounds_left: float | None = None
    spe_share: float | None = None
    money_to_divide: float | None = None
    max_rounds: float | None = None
    your_player: str | None = None
    message_len: int = 0
    propensities: dict = field(default_factory=dict)
    claim_id: str | None = None
    claim_kind: str | None = None
    # integrity
    numeric_invariant_ok: bool = True
    length_band_ok: bool = True
    record_outcome: str = "sent"
    # outcomes
    accepted: int | None = None
    opp_concession_next: float | None = None
    settle_round: float | None = None
    settle_round_if_agreed: float | None = None
    agreed: int | None = None
    realised_share: float | None = None
    walked_away: int | None = None
    join_status: str = "unjoined"       # joined | no_game | no_response | mismatch
    is_first_in_game: bool = False
    game_pure_arm: bool = False

    # -- clusters ---------------------------------------------------------
    @property
    def joined_primary(self) -> int:
        """1 when the primary outcome was observed. Differential censoring
        across arms is itself a balance failure (B5), so it needs to be a
        first-class variable and not a footnote in the intake table."""
        return 1 if self.accepted is not None else 0

    @property
    def is_binary_treated(self) -> int:
        return 1

    @property
    def cluster_game(self) -> str:
        return f"{self.probe}::{self.game_id}"

    @property
    def cluster_opponent(self) -> str:
        """Finest identifiable opponent. A named agent recurs across games and
        is one cluster. A hidden opponent is not identifiable, and each hidden
        game is a fresh draw from a pool we cannot see -- so a hidden game is
        its own cluster, which also nests every offer inside that game."""
        if self.opponent_name:
            return f"name::{self.opponent_name}"
        return f"hidden::{self.cluster_game}"

    @property
    def cluster_opponent_strict(self) -> str:
        """Conservative alternative: every hidden game pooled into one cluster,
        as if the same opponent were behind all of them. Reported as a
        sensitivity, never as the primary, because with 3-5 levels the sandwich
        has no degrees of freedom left."""
        return self.opponent_class or "hidden"

    @property
    def cluster_config(self) -> str:
        return "|".join(str(x) for x in (
            self.venue, self.horizon_known, self.complete_information,
            self.money_to_divide, self.delta_me, self.delta_opp, self.max_rounds))

    def stratum(self, coarse: bool = False) -> str:
        """The analysis stratum. Fine = the actual permuted block of the actual
        assignment stream (P3). Coarse = pooled over block index and stream."""
        if coarse:
            return f"{self.arm_set_version}||{self.block_key}"
        return "||".join(str(x) for x in (
            self.arm_set_version, self.experiment_id, self.probe,
            self.block_key, self.block_index))


def _f(value, default=None):
    if isinstance(value, bool) or value is None:
        return default
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def load_records(roots=("logs",), filename="experiment.jsonl"):
    """Every experiment record under every agent's log directory.

    The fleet runs five agents with five log dirs; assign.py writes beside each
    agent's turns.jsonl. ``probe`` is taken from the record when present and
    from the directory name otherwise, so records written before the probe field
    existed still attribute correctly."""
    out = []
    seen_paths = set()
    for root in roots:
        patterns = [os.path.join(root, filename),
                    os.path.join(root, "*", filename),
                    os.path.join(root, "*", "*", filename)]
        for pattern in patterns:
            for path in sorted(glob.glob(pattern)):
                real = os.path.realpath(path)
                if real in seen_paths:
                    continue
                seen_paths.add(real)
                probe_dir = os.path.basename(os.path.dirname(path))
                with open(path, "r", encoding="utf-8") as handle:
                    for line_no, line in enumerate(handle, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except ValueError:
                            out.append({"_malformed": True, "_path": path,
                                        "_line": line_no})
                            continue
                        rec["_path"] = path
                        rec["_probe_dir"] = probe_dir
                        out.append(rec)
    return out


def load_games(roots=("logs",)):
    """Index every completed-game record by (probe, game_id).

    Keyed by probe as well as id because two agents can be handed the same
    game_id by different servers, and because the join must not silently reach
    across agents."""
    index = {}
    for root in roots:
        for pattern in (os.path.join(root, "*", "games", "*.json"),
                        os.path.join(root, "games", "*.json")):
            for path in sorted(glob.glob(pattern)):
                probe = os.path.basename(os.path.dirname(os.path.dirname(path)))
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        game = json.load(handle)
                except (OSError, ValueError):
                    continue
                gid = game.get("game_id") or os.path.splitext(os.path.basename(path))[0]
                index[(probe, str(gid))] = game
                index.setdefault((None, str(gid)), game)
    return index


def dedupe_records(records):
    """One record per decision point, earliest kept.

    assign.py memoises a repeated presentation (an SDK retry after a rejected
    move) and returns the same arm without consuming a block slot -- but it
    writes a second record. Counting both would double-count one offer and would
    do so differentially, because retries follow rejected moves."""
    best, dropped = {}, 0
    for rec in records:
        design = rec.get("experiment") or {}
        key = (design.get("experiment_id"), rec.get("_probe_dir"),
               design.get("decision_key") or f"{rec.get('game_id')}:{rec.get('round')}")
        prior = best.get(key)
        if prior is None:
            best[key] = rec
        else:
            dropped += 1
            if _f(rec.get("ts"), 0.0) < _f(prior.get("ts"), 0.0):
                best[key] = rec
    return list(best.values()), dropped


# -- outcome derivation ----------------------------------------------------

_ACCEPT_TOKENS = {"accept", "acceptoffer", "accepted"}
_WALK_TOKENS = {"walkaway", "walked_away", "walk_away"}
_GAIN_KEY = {"player_1": "alice_gain", "player_2": "bob_gain"}


def _opponent_of(me):
    return "player_2" if me == "player_1" else "player_1"


def _decision_token(entry):
    return str(entry.get("decision") or "").strip().lower()


def _our_bargaining_entry(game, me, round_no, submitted):
    """The history entry for OUR offer at ``round_no``, verified against the
    number we actually submitted. A mismatch is reported, never patched: if the
    join is wrong the outcome belongs to some other offer and the unit must
    leave the analysis rather than contribute a wrong label."""
    for entry in game.get("history") or []:
        if entry.get("round") != round_no:
            continue
        if entry.get("proposer") != me:
            continue
        offer = entry.get("offer") or {}
        mine = _f(offer.get(f"{me}_gain"))
        if submitted is not None and mine is not None and abs(mine - submitted) > 1e-6:
            return entry, "mismatch"
        return entry, "joined"
    return None, "no_response"


def _our_negotiation_entry(game, me, round_no, submitted):
    """Our counteroffer at round r is submitted as a decision carrying
    product_price and surfaces as the OFFER at round r+1; when we open the game
    it is the offer at round r. Take the first entry from us at or after r."""
    best = None
    for entry in game.get("history") or []:
        offer = entry.get("offer") or {}
        if offer.get("from_player") != me:
            continue
        rnd = entry.get("round")
        if rnd is None or (round_no is not None and rnd < round_no):
            continue
        if best is None or rnd < best.get("round", 10 ** 9):
            best = entry
    if best is None:
        return None, "no_response"
    price = _f((best.get("offer") or {}).get("price"))
    if submitted is not None and price is not None and abs(price - submitted) > 1e-4:
        return best, "mismatch"
    return best, "joined"


def _bargaining_concession(game, me, round_no, money):
    opp = _opponent_of(me)
    if not money:
        return None
    by_round = {}
    for entry in game.get("history") or []:
        by_round[entry.get("round")] = entry
    nxt, prev = by_round.get((round_no or 0) + 1), by_round.get((round_no or 0) - 1)
    if not nxt or not prev:
        return None
    if nxt.get("proposer") != opp or prev.get("proposer") != opp:
        return None
    new = _f((nxt.get("offer") or {}).get(f"{me}_gain"))
    old = _f((prev.get("offer") or {}).get(f"{me}_gain"))
    if new is None or old is None:
        return None
    return (new - old) / money


def _negotiation_concession(game, me, our_entry, scale, we_are_buyer):
    """Movement of the opponent's price between the offer we rejected and the
    offer they make after rejecting ours, signed so positive = toward us."""
    history = game.get("history") or []
    try:
        idx = history.index(our_entry)
    except ValueError:
        return None
    prev_price = next_price = None
    for entry in reversed(history[:idx]):
        if (entry.get("offer") or {}).get("from_player") != me:
            prev_price = _f((entry.get("offer") or {}).get("price"))
            break
    for entry in history[idx + 1:]:
        if (entry.get("offer") or {}).get("from_player") != me:
            next_price = _f((entry.get("offer") or {}).get("price"))
            break
    if prev_price is None or next_price is None or not scale:
        return None
    delta = (prev_price - next_price) if we_are_buyer else (next_price - prev_price)
    return delta / scale


def _game_level_outcomes(game, me, venue, money):
    """settle_round (censored, defined for every game), realised_share
    (no-deal = 0, so no selection on the outcome), agreement, walk-away."""
    config = game.get("config") or {}
    result = game.get("result") or config.get("result") or {}
    outcome = str(result.get("outcome") or "").strip().lower()
    rounds_played = _f(game.get("rounds_played"), 0.0) or 0.0
    agreed = 1 if outcome == "agreement" else 0
    agreed_round = _f(result.get("agreed_round"))
    settle = agreed_round if (agreed and agreed_round) else rounds_played + 1.0
    walked = 1 if outcome in _WALK_TOKENS else 0
    if not walked:
        for entry in game.get("history") or []:
            if _decision_token(entry).replace(" ", "") in _WALK_TOKENS:
                walked = 1
                break
    payoff = _f(game.get("our_payoff"), 0.0) or 0.0
    if venue == "bargaining":
        scale = money or _f(config.get("money_to_divide"))
    else:
        scale = _f(config.get(f"{me}_value"))
        if not scale:
            prices = [_f((e.get("offer") or {}).get("price")) for e in game.get("history") or []]
            prices = [p for p in prices if p]
            scale = max(prices) if prices else None
    realised = (payoff / scale) if scale else None
    return {"settle_round": settle,
            "settle_round_if_agreed": (agreed_round if agreed else None),
            "agreed": agreed, "realised_share": realised, "walked_away": walked}


def build_units(records, games, include_ineligible=False):
    """Join assignment records to game outcomes. Returns (units, intake)."""
    intake = Counter()
    units = []
    for rec in records:
        if rec.get("_malformed"):
            intake["malformed_record"] += 1
            continue
        design = rec.get("experiment") or {}
        outcome = design.get("outcome")
        intake[f"record:{outcome}"] += 1
        if outcome == "invariance_violation":
            intake["invariance_violation"] += 1
        if outcome not in ("sent", "silent"):
            continue
        arm = design.get("arm")
        if not arm:
            intake["assigned_without_arm"] += 1
            continue
        probe = design.get("probe") or rec.get("_probe_dir") or "?"
        gid = str(rec.get("game_id"))
        venue = rec.get("game_family") or design.get("venue")
        state = rec.get("state") or {}
        action = rec.get("action") or {}
        me = rec.get("your_player") or "player_1"
        money = _f(design.get("money_to_divide")) or _f(state.get("money_to_divide"))
        composer = design.get("composer") or {}

        unit = Unit(
            probe=probe, game_id=gid, round=rec.get("round"),
            ts=_f(rec.get("ts"), 0.0) or 0.0,
            decision_key=design.get("decision_key") or f"{gid}:{rec.get('round')}",
            experiment_id=design.get("experiment_id") or "?",
            arm_set_version=design.get("arm_set_version") or "?",
            arm=arm,
            block_key=design.get("block_key") or design.get("stratum_id") or "?",
            block_index=design.get("block_index"),
            stratum_id=design.get("stratum_id") or "?",
            pool_id=design.get("pool_id"),
            arm_pool=tuple(design.get("arm_pool") or ()),
            p_assign=_f(design.get("p_assign")),
            p_assign_conditional=_f(design.get("p_assign_conditional")),
            propensities=dict(design.get("propensities") or {}),
            venue=venue,
            share_to_responder=_f(design.get("share_to_responder")),
            share_bucket=design.get("share_bucket"),
            opponent_class=design.get("opponent_class"),
            opponent_name=design.get("opponent_name"),
            round_class=design.get("round_class"),
            horizon_known=design.get("horizon_known"),
            complete_information=design.get("complete_information"),
            delta_me=_f(design.get("delta_me")),
            delta_opp=_f(design.get("delta_opp")),
            rounds_left=_f(design.get("rounds_left")),
            spe_share=_f(design.get("spe_share")),
            money_to_divide=money,
            max_rounds=_f(state.get("max_rounds")),
            your_player=me,
            message_len=int(_f(design.get("message_len"), 0) or 0),
            claim_id=composer.get("claim_id"),
            claim_kind=composer.get("claim_kind"),
            numeric_invariant_ok=bool(design.get("numeric_invariant_ok", True)),
            length_band_ok=bool(design.get("length_band_ok", True)),
            record_outcome=outcome,
        )

        game = games.get((probe, gid)) or games.get((None, gid))
        if game is None:
            unit.join_status = "no_game"
            intake["no_game_record"] += 1
            units.append(unit)
            continue
        if unit.max_rounds is None:
            unit.max_rounds = _f((game.get("config") or {}).get("max_rounds"))

        if venue == "bargaining":
            submitted = _f(action.get(_GAIN_KEY.get(me, "alice_gain")))
            entry, status = _our_bargaining_entry(game, me, unit.round, submitted)
        elif venue == "negotiation":
            submitted = _f(action.get("product_price")) or _f(action.get("price"))
            entry, status = _our_negotiation_entry(game, me, unit.round, submitted)
        else:
            entry, status = None, "unsupported_venue"
        unit.join_status = status
        intake[f"join:{status}"] += 1

        gl = _game_level_outcomes(game, me, venue, money)
        unit.settle_round = gl["settle_round"]
        unit.settle_round_if_agreed = gl["settle_round_if_agreed"]
        unit.agreed = gl["agreed"]
        unit.realised_share = gl["realised_share"]
        unit.walked_away = gl["walked_away"]

        if status == "joined" and entry is not None:
            token = _decision_token(entry).replace(" ", "")
            unit.accepted = 1 if token in _ACCEPT_TOKENS else 0
            if venue == "bargaining":
                unit.opp_concession_next = _bargaining_concession(
                    game, me, unit.round, money)
            else:
                config = game.get("config") or {}
                role = str(config.get(f"{me}_role") or "").lower()
                scale = _f(config.get(f"{me}_value"))
                if not scale:
                    prices = [_f((e.get("offer") or {}).get("price"))
                              for e in game.get("history") or []]
                    prices = [p for p in prices if p]
                    scale = max(prices) if prices else None
                unit.opp_concession_next = _negotiation_concession(
                    game, me, entry, scale, role == "buyer")
        units.append(unit)

    # first-exposure ITT tag and arm purity, per game
    by_game = defaultdict(list)
    for unit in units:
        by_game[unit.cluster_game].append(unit)
    for group in by_game.values():
        group.sort(key=lambda u: ((u.round if u.round is not None else 10 ** 9), u.ts))
        pure = len({u.arm for u in group}) == 1
        for i, unit in enumerate(group):
            unit.is_first_in_game = (i == 0)
            unit.game_pure_arm = pure
    return units, intake


# ==========================================================================
# 4. ESTIMATION
# ==========================================================================

@dataclass
class BlockRow:
    stratum: str
    n_arm: int
    n_ctrl: int
    mean_arm: float
    mean_ctrl: float
    weight: float


def stratified_difference(units, arm, control, outcome, coarse=False):
    """Mantel-Haenszel / Cochran stratified difference over the randomisation
    blocks, with everything the variance needs carried out alongside it.

    Works for a binary outcome (where it is the stratified risk difference) and
    for a continuous one (where it is the stratified mean difference); the
    weights n1 n0/(n1+n0) are the same in both cases and, critically, are 0
    whenever a block holds only one of the two arms -- which is how a
    within-block estimator refuses to compare across blocks instead of quietly
    doing it.

    ``cells`` and ``rows`` are returned because the variance is a cluster
    JACKKNIFE, not an influence-function sandwich. That is not a stylistic
    choice, it is a correction forced by simulation: this estimator is the
    saturated block-by-arm model, so unit residuals taken about their own cell
    mean sum to exactly zero inside every cell. Any cluster that contains whole
    blocks -- which is every named opponent, because opponent_class is part of
    block_key -- then has a total influence of exactly zero and the sandwich
    reports roughly half the true standard error. Measured on 25 replications
    of the simulator: empirical SD 0.0189, sandwich clustered on opponent
    0.0112, sandwich iid 0.0204. The jackknife has no such degeneracy, is
    conservative with few clusters, and reproduces the exact unbiased variance
    in the delete-one-unit limit.
    """
    cells = {}
    rows = []
    for unit in units:
        if unit.arm not in (arm, control):
            continue
        value = getattr(unit, outcome, None)
        if value is None:
            continue
        stratum = unit.stratum(coarse)
        cell = cells.get(stratum)
        if cell is None:
            cell = cells[stratum] = [0, 0.0, 0, 0.0]     # n_a, sum_a, n_c, sum_c
        is_arm = unit.arm == arm
        if is_arm:
            cell[0] += 1
            cell[1] += float(value)
        else:
            cell[2] += 1
            cell[3] += float(value)
        rows.append((unit, stratum, is_arm, float(value)))

    summary = _delta_from_cells(cells)
    block_rows = []
    for stratum, (n_a, s_a, n_c, s_c) in sorted(cells.items()):
        if n_a and n_c:
            block_rows.append(BlockRow(stratum, n_a, n_c, s_a / n_a, s_c / n_c,
                                       (n_a * n_c) / (n_a + n_c)))
        else:
            block_rows.append(BlockRow(stratum, n_a, n_c, float("nan"),
                                       float("nan"), 0.0))
    informative = [r for r in block_rows if r.weight > 0]
    return {
        "point": summary["delta"],
        "baseline": summary["baseline"],
        "cells": cells,
        "rows": rows,
        "block_rows": block_rows,
        "informative": informative,
        "n_arm": sum(r.n_arm for r in informative),
        "n_ctrl": sum(r.n_ctrl for r in informative),
        "n_blocks": len(block_rows),
        "n_informative": len(informative),
    }


def _delta_from_cells(cells):
    """Weighted difference and weighted control level from per-block cells."""
    num = den = base = 0.0
    for n_a, s_a, n_c, s_c in cells.values():
        if not n_a or not n_c:
            continue
        w = (n_a * n_c) / (n_a + n_c)
        num += w * (s_a / n_a - s_c / n_c)
        base += w * (s_c / n_c)
        den += w
    if den <= 0:
        return {"delta": None, "baseline": None, "weight": 0.0}
    return {"delta": num / den, "baseline": base / den, "weight": den}


#: the primary estimator, named for what it is in the binary case
mh_risk_difference = stratified_difference


def hajek_ipw_difference(units, arm, control, outcome, coarse=False):
    """Design-based sensitivity: within stratum, weight each unit by the inverse
    of ``p_assign_conditional`` -- the realised probability the randomiser
    recorded at the moment of the draw, which under permuted blocks is NOT the
    marginal 1/k (assign.py's analysis contract insists on this and it is right
    to).  Hajek rather than Horvitz-Thompson so the weights normalise."""
    totals = {}
    counts = {}
    for unit in units:
        if unit.arm not in (arm, control):
            continue
        value = getattr(unit, outcome, None)
        if value is None:
            continue
        prob = unit.p_assign_conditional or unit.p_assign
        if not prob or prob <= 0:
            continue
        stratum = unit.stratum(coarse)
        cell = totals.setdefault(stratum, [0.0, 0.0, 0.0, 0.0])
        count = counts.setdefault(stratum, [0, 0])
        if unit.arm == arm:
            cell[0] += float(value) / prob
            cell[1] += 1.0 / prob
            count[0] += 1
        else:
            cell[2] += float(value) / prob
            cell[3] += 1.0 / prob
            count[1] += 1
    num = den = 0.0
    for stratum, (a_sum, a_w, c_sum, c_w) in totals.items():
        n_a, n_c = counts[stratum]
        if n_a == 0 or n_c == 0 or a_w <= 0 or c_w <= 0:
            continue
        w = (n_a * n_c) / (n_a + n_c)
        num += w * (a_sum / a_w - c_sum / c_w)
        den += w
    return (num / den) if den > 0 else None


def cluster_variance(cells, rows, key_fn):
    """Cluster-robust variance of the stratified difference. Returns (V, G).

    THE ESTIMATOR, and why it is this one. The design is finely stratified: a
    full block holds 2 units of a framing arm and 4 of the neutral control, so
    there is no usable within-block variance to estimate and any attempt to use
    one is a disaster in a specific, silent way. Two estimators were written and
    rejected against the simulator before this one:

      * influence-function sandwich, residuals about the cell mean. This
        estimator is the saturated block-by-arm model, so those residuals sum to
        exactly zero inside every cell; any cluster holding whole blocks -- which
        is every named opponent, since opponent_class is part of block_key --
        contributes exactly zero. Measured: empirical SD 0.0189, reported SE
        0.0112. Coverage 0.57 against a nominal 0.95.
      * delete-one-cluster jackknife. Deleting one of two treated units in a
        block changes that block's weight by 40%, and the jackknife charges that
        design-fixed quantity to sampling noise. Measured: SE 0.0307 against the
        same 0.0189. Coverage ~1.00, every contrast INSUFFICIENT_POWER for ever.

    What survives is the standard variance for a finely stratified (essentially
    paired) experiment: the estimator is a weighted mean of block-level
    differences, so its variance is estimated from the spread of those block
    differences, not from inside the blocks. With
        c_b = (w_b / W) (d_b - Delta_hat)      and     sum_b c_b = 0,
        V = B/(B-1) * sum_b c_b^2
    which is valid whatever the dependence WITHIN a block -- and blocks are
    where the within-game and within-opponent dependence mostly lives, because
    opponent_class and round class are part of the block key. It is conservative
    by exactly the between-block heterogeneity of the true effect, which is the
    right direction to be wrong in.

    Clustering then handles dependence ACROSS blocks -- the same opponent met in
    many games, the same configuration recurring, one negotiation game placing
    offers into several blocks. A cluster need not nest in a block, so each
    block's contribution is split across the clusters its units belong to,
    with the part that cannot be attributed to any single cluster left in the
    independent term:
        a_bg = (units of block b in cluster g) / (units of block b)
        V = B/(B-1) * [ sum_g (sum_b a_bg c_b)^2
                        + sum_b c_b^2 (1 - sum_g a_bg^2) ]
    which collapses to the block-level formula when every block sits inside one
    cluster, and to the same formula again when every unit is its own cluster.
    """
    summary = _delta_from_cells(cells)
    delta, weight = summary["delta"], summary["weight"]
    if delta is None or weight <= 0:
        return float("nan"), 0

    contribution, block_units = {}, defaultdict(int)
    for stratum, (n_a, s_a, n_c, s_c) in cells.items():
        if not n_a or not n_c:
            continue
        w = (n_a * n_c) / (n_a + n_c)
        contribution[stratum] = (w / weight) * (s_a / n_a - s_c / n_c - delta)
        block_units[stratum] = n_a + n_c

    blocks = len(contribution)
    if blocks < 2:
        return float("nan"), 0

    # key_fn None means "every block is its own cluster", i.e. the
    # independent-blocks variance that the whole family is built on.
    per_block_cluster = defaultdict(lambda: defaultdict(int))
    for unit, stratum, _is_arm, _value in rows:
        if stratum in contribution:
            key = stratum if key_fn is None else key_fn(unit)
            per_block_cluster[stratum][key] += 1

    cluster_sums = defaultdict(float)
    independent = 0.0
    for stratum, c_b in contribution.items():
        total = block_units[stratum]
        share_sq = 0.0
        for cluster, count in per_block_cluster[stratum].items():
            share = count / total
            cluster_sums[cluster] += share * c_b
            share_sq += share * share
        independent += c_b * c_b * max(0.0, 1.0 - share_sq)
    var = sum(v * v for v in cluster_sums.values()) + independent
    var *= blocks / (blocks - 1.0)
    return var, len(cluster_sums)


def block_variance(cells, rows):
    """The independent-blocks variance, i.e. cluster_variance with every block
    its own cluster. Reported as the floor of the clustered family."""
    return cluster_variance(cells, rows, lambda u: None)


def two_way_cluster_variance(cells, rows, key_a, key_b):
    """Cameron-Gelbach-Miller: V = V_a + V_b - V_{a&b}.

    Non-positive results are floored at max(V_a, V_b) -- the standard, and
    conservative, repair; it is flagged so the report can say it happened."""
    v_a, g_a = cluster_variance(cells, rows, key_a)
    v_b, g_b = cluster_variance(cells, rows, key_b)
    v_ab, g_ab = cluster_variance(cells, rows, lambda u: (key_a(u), key_b(u)))
    v = v_a + v_b - v_ab
    floored = False
    if not (v > 0) or not math.isfinite(v):
        v, floored = max(v_a, v_b), True
    return {"var": v, "g_a": g_a, "g_b": g_b, "g_ab": g_ab,
            "var_a": v_a, "var_b": v_b, "var_ab": v_ab, "floored": floored}


def randomisation_p(units, arm, control, outcome, coarse=False,
                    draws=None, seed=None):
    """Two-sided randomisation-inference p for the sharp null of no effect.

    Arm labels are re-drawn by permuting, within each analysis block, the arm
    labels that were actually realised there. This reproduces the design's own
    conditional randomisation distribution, so the test is EXACT under the sharp
    null -- and exact under arbitrary dependence between units, including
    several offers inside one negotiation game, because the thing being permuted
    is the assignment and the assignment really was made per decision point.

    Because ``opponent_class`` sits inside ``block_key``, a within-block
    permutation is also a within-opponent permutation. That is why this p-value
    is the arbiter when the cluster count is too small for the sandwich.
    """
    draws = int(draws if draws is not None else THRESHOLDS["ri_draws"])
    rng = random.Random(seed if seed is not None else THRESHOLDS["ri_seed"])
    blocks = defaultdict(list)
    for unit in units:
        if getattr(unit, outcome, None) is None:
            continue
        blocks[unit.stratum(coarse)].append(unit)

    # keep only blocks that can produce the contrast at all
    live = {}
    for stratum, group in blocks.items():
        arms = {u.arm for u in group}
        if arm in arms and control in arms:
            live[stratum] = group
    if not live:
        return {"p": float("nan"), "draws": 0, "observed": None, "n_blocks": 0}

    def statistic(labels_by_block):
        num = den = 0.0
        for stratum, group in live.items():
            labels = labels_by_block[stratum]
            a_vals = [float(getattr(u, outcome)) for u, lab in zip(group, labels) if lab == arm]
            c_vals = [float(getattr(u, outcome)) for u, lab in zip(group, labels) if lab == control]
            if not a_vals or not c_vals:
                continue
            w = (len(a_vals) * len(c_vals)) / (len(a_vals) + len(c_vals))
            num += w * (sum(a_vals) / len(a_vals) - sum(c_vals) / len(c_vals))
            den += w
        return (num / den) if den > 0 else None

    observed_labels = {s: [u.arm for u in g] for s, g in live.items()}
    observed = statistic(observed_labels)
    if observed is None:
        return {"p": float("nan"), "draws": 0, "observed": None, "n_blocks": len(live)}
    pools = {s: list(labels) for s, labels in observed_labels.items()}
    extreme = 0
    for _ in range(draws):
        shuffled = {}
        for stratum, labels in pools.items():
            copy = labels[:]
            rng.shuffle(copy)
            shuffled[stratum] = copy
        value = statistic(shuffled)
        if value is not None and abs(value) >= abs(observed) - 1e-12:
            extreme += 1
    return {"p": (1.0 + extreme) / (draws + 1.0), "draws": draws,
            "observed": observed, "n_blocks": len(live)}


@dataclass
class Estimate:
    arm: str
    control: str
    outcome: str
    family: str                       # "M" | "F" | "S"
    point: float | None = None
    baseline: float | None = None
    se: float | None = None
    df: float | None = None
    ci_low: float | None = None       # at the family's adjusted level
    ci_high: float | None = None
    ci_low_unadj: float | None = None
    ci_high_unadj: float | None = None
    alpha_ci: float = 0.05
    p_cluster: float | None = None
    p_randomisation: float | None = None
    p_combined: float | None = None
    p_adjusted: float | None = None   # Holm, filled in by run_analysis
    n_arm: int = 0
    n_ctrl: int = 0
    n_blocks: int = 0
    n_informative_blocks: int = 0
    g_opponent: int = 0
    g_config: int = 0
    g_game: int = 0
    mde: float | None = None
    verdict: str = "NOT_EVALUATED"
    verdict_reason: str = ""
    gates_failed: tuple = ()
    # sensitivities, reported never substituted
    point_coarse: float | None = None
    point_ipw: float | None = None
    point_pure_arm: float | None = None
    se_opponent: float | None = None
    se_opponent_strict: float | None = None
    se_config: float | None = None
    se_game: float | None = None
    se_iid: float | None = None
    se_source: str = ""
    var_floored: bool = False
    censoring_arm: float | None = None
    censoring_ctrl: float | None = None
    length_median_arm: float | None = None
    length_median_ctrl: float | None = None
    length_confounded: bool = False
    notes: tuple = ()


def _outcome_population(units, outcome):
    """Game-level outcomes are analysed one row per game, on the arm of the
    game's FIRST assigned decision point (first-exposure ITT, which is the
    randomised quantity). Per-offer outcomes use every joined unit."""
    if outcome in GAME_LEVEL_OUTCOMES:
        return [u for u in units if u.is_first_in_game]
    return list(units)


def estimate_contrast(units, arm, control, outcome, family="F", alpha_ci=0.05,
                      ri_draws=None, length_confounded=False,
                      thresholds=None, skip_ri=False):
    """One pre-specified contrast, resolved all the way to a verdict."""
    th = dict(THRESHOLDS)
    th.update(thresholds or {})
    population = _outcome_population(units, outcome)
    est = Estimate(arm=arm, control=control, outcome=outcome, family=family,
                   alpha_ci=alpha_ci, length_confounded=length_confounded)

    # censoring, computed on the whole assigned population before any drop
    for label, name in ((arm, "arm"), (control, "ctrl")):
        rows = [u for u in population if u.arm == label]
        if rows:
            missing = sum(1 for u in rows if getattr(u, outcome, None) is None)
            setattr(est, f"censoring_{name}", missing / len(rows))
        lengths = [u.message_len for u in rows if u.message_len]
        setattr(est, f"length_median_{name}", _median(lengths))

    fit = stratified_difference(population, arm, control, outcome, coarse=False)
    est.point = fit["point"]
    est.baseline = fit["baseline"]
    est.n_arm, est.n_ctrl = fit["n_arm"], fit["n_ctrl"]
    est.n_blocks, est.n_informative_blocks = fit["n_blocks"], fit["n_informative"]
    est.point_coarse = stratified_difference(
        population, arm, control, outcome, coarse=True)["point"]
    est.point_ipw = hajek_ipw_difference(population, arm, control, outcome)
    if outcome in GAME_LEVEL_OUTCOMES:
        pure = [u for u in population if u.game_pure_arm]
        est.point_pure_arm = stratified_difference(
            pure, arm, control, outcome)["point"]

    cells, rows = fit["cells"], fit["rows"]
    if est.point is None or not rows:
        est.verdict = "INSUFFICIENT_POWER"
        est.verdict_reason = "no informative block contains both arms"
        est.gates_failed = ("no_informative_blocks",)
        return est

    two_way = two_way_cluster_variance(
        cells, rows, lambda u: u.cluster_opponent, lambda u: u.cluster_config)
    est.g_opponent, est.g_config = two_way["g_a"], two_way["g_b"]
    est.var_floored = two_way["floored"]

    v_opp, g_opp = cluster_variance(cells, rows, lambda u: u.cluster_opponent)
    v_str, _ = cluster_variance(cells, rows, lambda u: u.cluster_opponent_strict)
    v_cfg, g_cfg = cluster_variance(cells, rows, lambda u: u.cluster_config)
    v_game, g_game = cluster_variance(cells, rows, lambda u: u.cluster_game)
    v_iid, _ = block_variance(cells, rows)
    est.se_opponent = math.sqrt(v_opp) if v_opp > 0 else None
    est.se_opponent_strict = math.sqrt(v_str) if v_str > 0 else None
    est.se_config = math.sqrt(v_cfg) if v_cfg > 0 else None
    est.se_game = math.sqrt(v_game) if v_game > 0 else None
    est.se_iid = math.sqrt(v_iid) if v_iid > 0 else None
    est.g_game = g_game

    # P4: the primary interval is the WIDEST of the pre-specified clusterings.
    # A fixed rule, decided here and not after seeing anything, and it always
    # resolves the same way. Justification is measured, not aesthetic: over 400
    # replications of the simulator the empirical SD of the estimate is 0.0265
    # to 0.0282 depending on arm, while two-way (opponent x config) reports
    # 0.0247 and config- or game-clustering reports 0.0277. Clusters that do not
    # nest give genuinely different answers and the honest response to that is to
    # take the widest, not to pick the one that reads best.
    candidates = [
        ("two-way opponent x config", two_way["var"],
         min(two_way["g_a"], two_way["g_b"])),
        ("opponent", v_opp, g_opp),
        ("config", v_cfg, g_cfg),
        ("game", v_game, g_game),
    ]
    candidates = [(name, var, groups) for name, var, groups in candidates
                  if var is not None and math.isfinite(var) and var > 0]
    if candidates:
        name, var, groups = max(candidates, key=lambda item: item[1])
        est.se, est.se_source = math.sqrt(var), name
        est.df = max(1.0, min(groups, fit["n_informative"]) - 1.0)
    else:
        est.se, est.se_source, est.df = None, "undefined", 1.0

    if est.se and est.se > 0:
        t_stat = est.point / est.se
        est.p_cluster = t_two_sided_p(t_stat, est.df)
        crit = t_ppf(1.0 - alpha_ci / 2.0, est.df)
        crit_unadj = t_ppf(1.0 - th["alpha"] / 2.0, est.df)
        est.ci_low, est.ci_high = est.point - crit * est.se, est.point + crit * est.se
        est.ci_low_unadj = est.point - crit_unadj * est.se
        est.ci_high_unadj = est.point + crit_unadj * est.se
        est.mde = (crit + t_ppf(th["power_target"], est.df)) * est.se

    if not skip_ri:
        ri = randomisation_p(population, arm, control, outcome, draws=ri_draws)
        est.p_randomisation = ri["p"]
    candidates = [p for p in (est.p_cluster, est.p_randomisation)
                  if p is not None and math.isfinite(p)]
    est.p_combined = max(candidates) if candidates else None
    return est


def apply_verdict(est, thresholds=None, alpha_decision=None, balance_hard_fail=False):
    """P7's power gate and the verdict lattice, applied last so that no verdict
    can be reached without passing through every gate."""
    th = dict(THRESHOLDS)
    th.update(thresholds or {})
    alpha = alpha_decision if alpha_decision is not None else est.alpha_ci
    ship = th["ship_threshold"]

    if balance_hard_fail:
        est.verdict = "HARD_FAIL"
        est.verdict_reason = "balance check failed; no effect is reportable"
        return est

    gates = []
    if est.n_arm < th["min_n_per_arm"]:
        gates.append(f"n_arm={est.n_arm}<{th['min_n_per_arm']}")
    if est.n_ctrl < th["min_n_per_arm"]:
        gates.append(f"n_ctrl={est.n_ctrl}<{th['min_n_per_arm']}")
    if est.n_informative_blocks < th["min_informative_blocks"]:
        gates.append(f"informative_blocks={est.n_informative_blocks}"
                     f"<{th['min_informative_blocks']}")
    eff_clusters = min(est.g_opponent or 0, est.g_config or 0)
    if eff_clusters < th["min_clusters"]:
        gates.append(f"effective_clusters={eff_clusters}<{th['min_clusters']}")
    if est.mde is None or not math.isfinite(est.mde):
        gates.append("mde=undefined")
    elif est.outcome in BINARY_OUTCOMES and est.mde > th["mde_ceiling"]:
        gates.append(f"realised_MDE={est.mde:.3f}>{th['mde_ceiling']:.2f}")
    est.gates_failed = tuple(gates)

    if gates:
        est.verdict = "INSUFFICIENT_POWER"
        est.verdict_reason = ("NOT A FINDING -- realised precision cannot see the "
                              "effect this design was built for: " + "; ".join(gates))
        return est

    p = est.p_adjusted if est.p_adjusted is not None else est.p_combined
    significant = (p is not None and p < th["alpha"]
                   and est.ci_low is not None
                   and (est.ci_low > 0 or est.ci_high < 0))
    if significant and est.length_confounded:
        est.verdict = "CONFOUNDED_WITH_VERBOSITY"
        est.verdict_reason = ("interval excludes 0 but this arm's message length "
                              "differs from the neutral control by more than "
                              f"{th['length_tolerance_chars']} characters (design 5e)")
        return est
    if significant:
        est.verdict = "EFFECT_POSITIVE" if est.point > 0 else "EFFECT_NEGATIVE"
        est.verdict_reason = (f"adjusted p={p:.4g} < {th['alpha']}, "
                              f"interval [{est.ci_low:+.3f},{est.ci_high:+.3f}] excludes 0")
        return est
    if (est.ci_low is not None and est.ci_low > -ship and est.ci_high < ship):
        est.verdict = "NULL_RULED_OUT"
        est.verdict_reason = (f"powered, and the interval lies inside "
                              f"+-{ship:.2f}: an effect worth shipping is ruled out")
        return est
    est.verdict = "INCONCLUSIVE"
    est.verdict_reason = ("powered past the MDE gate, but the interval still spans "
                          f"both 0 and +-{ship:.2f}")
    return est


# ==========================================================================
# 5. BALANCE -- the first thing to look at and the first thing to break
#
# If the arm moved the number, or the arms did not come out balanced on what
# they were blocked on, then every effect below is an artefact and the right
# output is a refusal. So this runs first, and a HARD_FAIL here suppresses the
# entire effect table rather than annotating it.
# ==========================================================================

_NUMERIC_COVARIATES = ("delta_me", "delta_opp", "rounds_left", "spe_share",
                       "money_to_divide", "share_to_responder")
_FLAG_COVARIATES = ("horizon_known", "complete_information")
_BLOCKED_VARIABLES = ("venue", "share_bucket", "opponent_class", "round_class",
                      "pool_id")


@dataclass
class BalanceItem:
    key: str
    status: str                       # PASS | WARN | FAIL
    statistic: float | None
    p_value: float | None
    detail: str
    table: dict = field(default_factory=dict)


@dataclass
class BalanceReport:
    items: list = field(default_factory=list)
    status: str = "PASS"
    hard_fail: bool = False
    length_confounded_arms: tuple = ()
    intake: dict = field(default_factory=dict)

    def add(self, item):
        self.items.append(item)
        order = {"PASS": 0, "WARN": 1, "FAIL": 2}
        if order[item.status] > order[self.status]:
            self.status = item.status
        if item.status == "FAIL":
            self.hard_fail = True
        return item


def _flag_value(value):
    if value is True:
        return 1.0
    if value is False:
        return 0.0
    return None


def _covariate_value(unit, name):
    if name in _FLAG_COVARIATES:
        return _flag_value(getattr(unit, name, None))
    value = getattr(unit, name, None)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _balance_permutation(units, arms, control, getters, draws, seed, coarse=False):
    """Within-block permutation test of arm balance on several variables at once.

    Statistic per variable = max over arms of |MH-weighted difference vs the
    neutral control|. One shuffle serves every variable, which is what makes it
    affordable to test every covariate rather than the two that look suspicious.
    """
    rows = []                              # (block, arm, {var: value})
    for unit in units:
        values = {name: fn(unit) for name, fn in getters.items()}
        if all(v is None for v in values.values()):
            continue
        rows.append((unit.stratum(coarse), unit.arm, values))
    blocks = defaultdict(list)
    for stratum, label, values in rows:
        blocks[stratum].append((label, values))
    if not blocks:
        return {name: {"stat": None, "p": float("nan"), "per_arm": {}}
                for name in getters}

    def stats(assignment):
        num = defaultdict(lambda: defaultdict(float))
        den = defaultdict(lambda: defaultdict(float))
        for stratum, group in blocks.items():
            labels = assignment[stratum]
            for name in getters:
                by_arm = defaultdict(list)
                for (_, values), label in zip(group, labels):
                    value = values.get(name)
                    if value is not None:
                        by_arm[label].append(value)
                ctrl = by_arm.get(control)
                if not ctrl:
                    continue
                mean_c = sum(ctrl) / len(ctrl)
                for arm in arms:
                    vals = by_arm.get(arm)
                    if not vals:
                        continue
                    w = (len(vals) * len(ctrl)) / (len(vals) + len(ctrl))
                    num[name][arm] += w * (sum(vals) / len(vals) - mean_c)
                    den[name][arm] += w
        out = {}
        for name in getters:
            per_arm = {arm: (num[name][arm] / den[name][arm])
                       for arm in arms if den[name][arm] > 0}
            out[name] = per_arm
        return out

    observed_labels = {s: [label for label, _ in g] for s, g in blocks.items()}
    observed = stats(observed_labels)
    observed_max = {name: (max((abs(v) for v in per_arm.values()), default=None))
                    for name, per_arm in observed.items()}
    rng = random.Random(seed)
    extreme = {name: 0 for name in getters}
    usable = {name: 0 for name in getters}
    for _ in range(draws):
        shuffled = {}
        for stratum, labels in observed_labels.items():
            copy = labels[:]
            rng.shuffle(copy)
            shuffled[stratum] = copy
        drawn = stats(shuffled)
        for name in getters:
            value = max((abs(v) for v in drawn[name].values()), default=None)
            if value is None or observed_max[name] is None:
                continue
            usable[name] += 1
            if value >= observed_max[name] - 1e-15:
                extreme[name] += 1
    return {name: {"stat": observed_max[name],
                   "p": ((1.0 + extreme[name]) / (usable[name] + 1.0)
                         if usable[name] else float("nan")),
                   "per_arm": observed[name]}
            for name in getters}


def balance_check(units, records, intake, arms=None, control=CONTROL_NEUTRAL,
                  thresholds=None, draws=None):
    th = dict(THRESHOLDS)
    th.update(thresholds or {})
    draws = int(draws if draws is not None else th["balance_ri_draws"])
    report = BalanceReport(intake=dict(intake))
    present = sorted({u.arm for u in units})
    arms = tuple(a for a in (arms or present) if a != control and a in present)

    # -- B0 numeric invariance ------------------------------------------
    violations = sum(1 for u in units if not u.numeric_invariant_ok)
    violations += int(intake.get("invariance_violation", 0))
    report.add(BalanceItem(
        "B0_numeric_invariance",
        "FAIL" if violations else "PASS", float(violations), None,
        ("the message hook moved a numeric field on %d turn(s); every record "
         "under this arm set is suspect" % violations) if violations else
        "no record shows the numeric action changing across the message hook",
        {"violations": violations}))

    if not units:
        report.add(BalanceItem("B_empty", "FAIL", 0.0, None,
                               "no assigned units in the log", {}))
        return report

    # -- B2a blocked variables must be constant inside a block ----------
    impurities = Counter()
    per_block_values = defaultdict(lambda: defaultdict(set))
    for unit in units:
        for name in _BLOCKED_VARIABLES:
            per_block_values[unit.stratum()][name].add(getattr(unit, name, None))
    for stratum, names in per_block_values.items():
        for name, values in names.items():
            if len(values) > 1:
                impurities[name] += 1
    report.add(BalanceItem(
        "B2a_block_purity",
        "FAIL" if impurities else "PASS",
        float(sum(impurities.values())), None,
        ("a variable that is part of block_key varies inside a block -- the log "
         "or the stratifier is inconsistent: %s" % dict(impurities)) if impurities
        else "every blocked variable is constant within its block, as it must be",
        dict(impurities)))

    # -- B1 + B2b covariate balance, one permutation for all -------------
    getters = {"share_to_responder": lambda u: _covariate_value(u, "share_to_responder")}
    for name in _NUMERIC_COVARIATES + _FLAG_COVARIATES:
        getters[name] = (lambda n: (lambda u: _covariate_value(u, n)))(name)
    getters["censoring"] = lambda u: float(u.joined_primary)
    getters["message_len"] = lambda u: (float(u.message_len) if u.message_len else None)
    balance = _balance_permutation(units, arms, control, getters, draws,
                                   th["ri_seed"] + 1)

    share = balance["share_to_responder"]
    status = "PASS"
    if share["p"] == share["p"]:
        if share["p"] < th["balance_fail_p"]:
            status = "FAIL"
        elif share["p"] < th["balance_warn_p"]:
            status = "WARN"
    report.add(BalanceItem(
        "B1_share_on_arm", status, share["stat"], share["p"],
        "design 5(f): the offer share must not depend on the arm. "
        "max |within-block difference vs %s| = %s" % (
            control, "n/a" if share["stat"] is None else f"{share['stat']:.4f}"),
        {"per_arm": share["per_arm"]}))

    covariates = [n for n in _NUMERIC_COVARIATES + _FLAG_COVARIATES
                  if n != "share_to_responder"]
    worst, worst_name = None, None
    for name in covariates:
        p = balance[name]["p"]
        if p == p and (worst is None or p < worst):
            worst, worst_name = p, name
    k = max(1, len(covariates))
    adjusted = min(1.0, worst * k) if worst is not None else float("nan")
    status = "PASS"
    if adjusted == adjusted:
        if adjusted < th["balance_fail_p"]:
            status = "FAIL"
        elif adjusted < th["balance_warn_p"]:
            status = "WARN"
    report.add(BalanceItem(
        "B2b_covariate_balance", status,
        (balance[worst_name]["stat"] if worst_name else None), adjusted,
        "covariates adjusted for but not blocked on; worst is %s "
        "(Bonferroni over %d covariates)" % (worst_name, k),
        {name: {"stat": balance[name]["stat"], "p": balance[name]["p"],
                "per_arm": balance[name]["per_arm"]} for name in covariates}))

    # -- B3 allocation against the recorded propensities -----------------
    observed = Counter(u.arm for u in units)
    expected = defaultdict(float)
    variance = defaultdict(float)
    have_propensities = 0
    for unit in units:
        props = unit.propensities or {}
        if not props:
            continue
        have_propensities += 1
        for name, p in props.items():
            p = _f(p, 0.0) or 0.0
            expected[name] += p
            variance[name] += p * (1.0 - p)
    table, worst_z = {}, 0.0
    for name in sorted(set(list(observed) + list(expected))):
        exp = expected.get(name)
        sd = math.sqrt(variance.get(name, 0.0)) if variance.get(name, 0.0) > 0 else None
        z = ((observed[name] - exp) / sd) if (exp is not None and sd) else None
        table[name] = {"observed": observed[name], "expected": exp, "z": z}
        if z is not None:
            worst_z = max(worst_z, abs(z))
    status = "PASS"
    if have_propensities == 0:
        status = "WARN"
    elif worst_z > th["allocation_fail_z"]:
        status = "FAIL"
    elif worst_z > th["allocation_warn_z"]:
        status = "WARN"
    report.add(BalanceItem(
        "B3_allocation", status, worst_z, None,
        "realised arm counts against the sum of the recorded conditional "
        "propensities (max |z| = %.2f over %d units carrying a propensity)"
        % (worst_z, have_propensities), table))

    # -- B4 message length, per arm, against the length-matched control --
    lengths = defaultdict(list)
    for unit in units:
        if unit.message_len:
            lengths[unit.arm].append(unit.message_len)
    ctrl_median = _median(lengths.get(control, []))
    confounded, table = [], {}
    for name in sorted(lengths):
        med = _median(lengths[name])
        gap = (abs(med - ctrl_median) if (med is not None and ctrl_median is not None)
               else None)
        out_of_band = sum(1 for L in lengths[name] if not (180 <= L <= 320))
        table[name] = {"median": med, "gap_vs_control": gap, "n": len(lengths[name]),
                       "outside_180_320": out_of_band}
        if name != control and gap is not None and gap > th["length_tolerance_chars"]:
            confounded.append(name)
    report.length_confounded_arms = tuple(confounded)
    report.add(BalanceItem(
        "B4_message_length",
        "WARN" if confounded else "PASS",
        (max((table[n]["gap_vs_control"] or 0.0) for n in table) if table else None),
        None,
        ("design 5(e): these arms differ from %s by more than %d characters and "
         "their framing contrast is reported as confounded with verbosity: %s"
         % (control, th["length_tolerance_chars"], ", ".join(confounded)))
        if confounded else
        "every messaged arm's median length is within %d characters of %s"
        % (th["length_tolerance_chars"], control),
        table))

    # -- B5 differential censoring ---------------------------------------
    censoring = balance["censoring"]
    status = "PASS"
    if censoring["p"] == censoring["p"]:
        if censoring["p"] < th["balance_fail_p"]:
            status = "FAIL"
        elif censoring["p"] < th["balance_warn_p"]:
            status = "WARN"
    rates = {}
    for name in sorted({u.arm for u in units}):
        rows = [u for u in units if u.arm == name]
        rates[name] = 1.0 - (sum(u.joined_primary for u in rows) / len(rows))
    report.add(BalanceItem(
        "B5_differential_censoring", status, censoring["stat"], censoring["p"],
        "rate at which an assigned offer never received an opponent response, "
        "by arm; a difference here would break the primary outcome",
        {"unjoined_rate": rates, "per_arm_diff": censoring["per_arm"]}))

    # -- B6 block structure ----------------------------------------------
    blocks = Counter(u.stratum() for u in units)
    sizes = sorted(blocks.values())
    versions = Counter(u.arm_set_version for u in units)
    report.add(BalanceItem(
        "B6_block_structure", "PASS", float(len(blocks)), None,
        "%d analysis blocks; median block size %s; %d arm-set version(s)"
        % (len(blocks), _median(sizes), len(versions)),
        {"n_blocks": len(blocks), "median_size": _median(sizes),
         "singleton_blocks": sum(1 for s in sizes if s == 1),
         "arm_set_versions": dict(versions),
         "streams": len({(u.experiment_id, u.probe) for u in units})}))

    # -- B7 composer provenance ------------------------------------------
    claims = defaultdict(Counter)
    kinds = defaultdict(Counter)
    for unit in units:
        if unit.claim_id:
            claims[unit.arm][unit.claim_id] += 1
        if unit.claim_kind:
            kinds[unit.arm][unit.claim_kind] += 1
    degenerate = [arm for arm, counter in claims.items()
                  if counter and max(counter.values()) / sum(counter.values()) > 0.95
                  and sum(counter.values()) >= 30]
    report.add(BalanceItem(
        "B7_composer_provenance",
        "WARN" if degenerate else "PASS", float(len(degenerate)), None,
        ("these arms collapsed onto a single claim (>95%% of their messages) and "
         "are no longer the framing family they are named after: %s"
         % ", ".join(degenerate)) if degenerate else
        "no arm collapsed onto a single claim builder",
        {"claims": {a: dict(c) for a, c in claims.items()},
         "kinds": {a: dict(c) for a, c in kinds.items()}}))
    return report


# ==========================================================================
# 6. THE ANALYSIS
# ==========================================================================

@dataclass
class AnalysisReport:
    generated_at: float
    prereg_sha256: str
    n_records: int
    n_units: int
    intake: dict
    balance: BalanceReport
    presence: object = None            # Estimate: A0 vs A1
    primary: list = field(default_factory=list)     # framing vs A1, primary outcome
    secondary: list = field(default_factory=list)
    interim: bool = False
    venue: str | None = None
    notes: list = field(default_factory=list)

    @property
    def headline(self):
        if self.balance.hard_fail:
            return "HARD_FAIL"
        if self.interim:
            return "INTERIM (balance and safety only; no effect reported)"
        verdicts = [e.verdict for e in self.primary]
        if any(v.startswith("EFFECT") for v in verdicts):
            return "EFFECT FOUND"
        if verdicts and all(v == "INSUFFICIENT_POWER" for v in verdicts):
            return "INSUFFICIENT POWER -- NO FINDING"
        if any(v == "NULL_RULED_OUT" for v in verdicts):
            return "NO SHIPPABLE EFFECT"
        return "INCONCLUSIVE"


def run_analysis(roots=("logs",), venue=None, interim=False, ri_draws=None,
                 balance_draws=None, thresholds=None, records=None, games=None,
                 units=None, skip_ri=False):
    """The whole pipeline, in the order the pre-registration fixes.

    Balance first, because a balance failure means there is nothing to report;
    then the message-presence contrast; then the framing family on the primary
    outcome with Holm across it; then the secondary family, gatekept on the
    primary."""
    th = dict(THRESHOLDS)
    th.update(thresholds or {})
    if units is None:
        records = records if records is not None else load_records(roots)
        games = games if games is not None else load_games(roots)
        deduped, dropped = dedupe_records(records)
        units, intake = build_units(deduped, games)
        intake["duplicate_records_dropped"] = dropped
        intake["records_read"] = len(records)
    else:
        intake = Counter()
        intake["records_read"] = len(units)
        dropped = 0
    if venue:
        units = [u for u in units if u.venue == venue]
    intake["units_assigned"] = len(units)

    balance = balance_check(units, records, intake, thresholds=th,
                            draws=balance_draws)
    report = AnalysisReport(
        generated_at=time.time(), prereg_sha256=PREREG_SHA256,
        n_records=int(intake.get("records_read", 0)), n_units=len(units),
        intake=dict(intake), balance=balance, interim=interim, venue=venue)

    if interim:
        report.notes.append(
            "--interim: effect estimates are suppressed by P8. Balance and "
            "safety only. Interim looks spend no alpha because they make no "
            "inference.")
        return report
    if balance.hard_fail:
        report.notes.append(
            "Balance HARD_FAIL. Per P6 no effect estimate is reported: with the "
            "randomisation in doubt, a point estimate is not an estimate of "
            "anything. Fix the cause and re-run; do not read the numbers below.")
        return report

    present = sorted({u.arm for u in units})
    framings = [a for a in FRAMING_ARMS if a in present]

    # -- family M: message presence -------------------------------------
    if CONTROL_SILENT in present and CONTROL_NEUTRAL in present:
        est = estimate_contrast(units, CONTROL_SILENT, CONTROL_NEUTRAL,
                                PRIMARY_OUTCOME, family="M",
                                alpha_ci=th["alpha"], ri_draws=ri_draws,
                                thresholds=th, skip_ri=skip_ri)
        est.p_adjusted = est.p_combined       # family of one, no correction
        apply_verdict(est, th, alpha_decision=th["alpha"])
        est.notes = ("Family M is a family of one and is not corrected: it asks "
                     "whether opening our mouth at all is worth anything, which "
                     "is a different question from which argument to make.",)
        report.presence = est

    # -- family F: framing vs the length-matched neutral -----------------
    k = max(1, len(framings))
    alpha_ci = th["alpha"] / k
    estimates = []
    for arm in framings:
        est = estimate_contrast(
            units, arm, CONTROL_NEUTRAL, PRIMARY_OUTCOME, family="F",
            alpha_ci=alpha_ci, ri_draws=ri_draws, thresholds=th,
            skip_ri=skip_ri,
            length_confounded=(arm in balance.length_confounded_arms))
        estimates.append(est)
    adjusted = holm([(e.arm, e.p_combined) for e in estimates])
    for est in estimates:
        est.p_adjusted = adjusted.get(est.arm)
        apply_verdict(est, th, alpha_decision=th["alpha"])
    report.primary = estimates

    # -- secondary family, gatekept -------------------------------------
    secondary = []
    for outcome in SECONDARY_OUTCOMES:
        for arm in framings + ([CONTROL_SILENT] if CONTROL_SILENT in present else []):
            est = estimate_contrast(
                units, arm, CONTROL_NEUTRAL, outcome, family="S",
                alpha_ci=alpha_ci, ri_draws=ri_draws, thresholds=th,
                skip_ri=skip_ri,
                length_confounded=(arm in balance.length_confounded_arms))
            secondary.append(est)
    adjusted = holm([((e.arm, e.outcome), e.p_combined) for e in secondary])
    passed = {e.arm for e in estimates if e.verdict.startswith("EFFECT")}
    for est in secondary:
        est.p_adjusted = adjusted.get((est.arm, est.outcome))
        apply_verdict(est, th, alpha_decision=th["alpha"])
        if est.verdict.startswith("EFFECT") and est.arm not in passed:
            est.notes = ("SUPPORTIVE ONLY: the gatekeeping rule in P5 requires "
                         "this arm's PRIMARY contrast to have reached EFFECT_* "
                         "before a secondary result counts as confirmatory.",)
            est.verdict = "SUPPORTIVE_" + est.verdict
    report.secondary = secondary
    return report


# ==========================================================================
# 7. REPORT RENDERING
# ==========================================================================

def _fmt(value, digits=3, pct=False):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "  n/a"
    if pct:
        return f"{100.0 * value:+.1f}"
    return f"{value:+.{digits}f}"


def _fmt_p(value):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "  n/a"
    if value < 1e-4:
        return "<1e-4"
    return f"{value:.4f}"


_VERDICT_GLOSS = {
    "EFFECT_POSITIVE": "framing RAISES acceptance",
    "EFFECT_NEGATIVE": "framing LOWERS acceptance",
    "NULL_RULED_OUT": "no shippable effect -- a real negative result",
    "INCONCLUSIVE": "powered, but the interval spans 0 and a shippable effect",
    "INSUFFICIENT_POWER": "NO FINDING -- too little data to say anything",
    "CONFOUNDED_WITH_VERBOSITY": "interval excludes 0 but length is not matched",
    "HARD_FAIL": "balance broke; nothing is reportable",
}


def _estimate_lines(est, indent="  "):
    out = []
    tag = _VERDICT_GLOSS.get(est.verdict.replace("SUPPORTIVE_", ""), "")
    out.append(f"{indent}{est.arm} vs {est.control}   [{est.outcome}]")
    out.append(f"{indent}  Delta        {_fmt(est.point)}"
               f"   (control level {_fmt(est.baseline)})")
    out.append(f"{indent}  {int(100*(1-est.alpha_ci))}% CI    "
               f"[{_fmt(est.ci_low)}, {_fmt(est.ci_high)}]"
               f"   widest pre-specified clustering: {est.se_source}, "
               f"t df={est.df:g}")
    out.append(f"{indent}  95% CI       [{_fmt(est.ci_low_unadj)}, "
               f"{_fmt(est.ci_high_unadj)}]   unadjusted, descriptive")
    out.append(f"{indent}  SE           {_fmt(est.se, 4)}"
               f"   [opp {_fmt(est.se_opponent, 4)} | cfg {_fmt(est.se_config, 4)}"
               f" | game {_fmt(est.se_game, 4)} | iid {_fmt(est.se_iid, 4)}"
               f" | strict-opp {_fmt(est.se_opponent_strict, 4)}]")
    out.append(f"{indent}  p            cluster {_fmt_p(est.p_cluster)} | "
               f"randomisation {_fmt_p(est.p_randomisation)} | "
               f"used {_fmt_p(est.p_combined)} | Holm {_fmt_p(est.p_adjusted)}")
    out.append(f"{indent}  n            arm {est.n_arm} / ctrl {est.n_ctrl}"
               f"   blocks {est.n_informative_blocks} informative of {est.n_blocks}"
               f"   clusters opp {est.g_opponent} cfg {est.g_config} game {est.g_game}")
    out.append(f"{indent}  realised MDE {_fmt(est.mde)}   at 80% power, this "
               f"family's adjusted level")
    out.append(f"{indent}  sensitivity  coarse {_fmt(est.point_coarse)} | "
               f"IPW {_fmt(est.point_ipw)}"
               + (f" | pure-arm {_fmt(est.point_pure_arm)}"
                  if est.point_pure_arm is not None else ""))
    if est.censoring_arm is not None or est.censoring_ctrl is not None:
        out.append(f"{indent}  censoring    arm {_fmt(est.censoring_arm)} / "
                   f"ctrl {_fmt(est.censoring_ctrl)}"
                   f"   msg length {est.length_median_arm} / {est.length_median_ctrl}")
    out.append(f"{indent}  VERDICT      {est.verdict}"
               + (f"  ({tag})" if tag else ""))
    out.append(f"{indent}               {est.verdict_reason}")
    if est.var_floored:
        out.append(f"{indent}               note: two-way variance was "
                   "non-positive and was floored at max(V_opp, V_cfg)")
    for note in est.notes:
        out.append(f"{indent}               note: {note}")
    return out


def format_report(report: AnalysisReport) -> str:
    lines = []
    add = lines.append
    add("=" * 78)
    add("MESSAGE-FRAMING EXPERIMENT -- PRE-SPECIFIED ANALYSIS")
    add("=" * 78)
    add(f"generated        {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.generated_at))}")
    add(f"prereg SHA-256   {report.prereg_sha256}")
    add(f"venue filter     {report.venue or 'all'}")
    add(f"records read     {report.n_records}")
    add(f"assigned units   {report.n_units}")
    add(f"HEADLINE         {report.headline}")
    add("")
    add("-" * 78)
    add("INTAKE (CONSORT-style; every eligible turn is accounted for)")
    add("-" * 78)
    for key in sorted(report.intake):
        add(f"  {key:<34} {report.intake[key]}")
    add("")
    add("-" * 78)
    add("BALANCE -- read this before anything else")
    add("-" * 78)
    add(f"  overall: {report.balance.status}"
        + ("   *** HARD FAIL: no effect is reportable ***"
           if report.balance.hard_fail else ""))
    for item in report.balance.items:
        stat = "" if item.statistic is None else f"  stat={item.statistic:.4f}"
        pval = "" if item.p_value is None else f"  p={_fmt_p(item.p_value)}"
        add(f"  [{item.status:<4}] {item.key}{stat}{pval}")
        add(f"          {item.detail}")
    if report.balance.hard_fail:
        add("")
        for note in report.notes:
            add("  " + note)
        return "\n".join(lines)
    if report.interim:
        add("")
        for note in report.notes:
            add("  " + note)
        return "\n".join(lines)

    add("")
    add("-" * 78)
    add("FAMILY M -- MESSAGE PRESENCE (A0 silent vs A1 neutral), alpha=0.05")
    add("-" * 78)
    if report.presence is None:
        add("  not estimable: one of the two control arms is absent from the log")
    else:
        lines.extend(_estimate_lines(report.presence))

    add("")
    add("-" * 78)
    add(f"FAMILY F -- FRAMING vs A1 NEUTRAL on {PRIMARY_OUTCOME} "
        f"(PRIMARY), Holm over {len(report.primary)} contrasts")
    add("-" * 78)
    if not report.primary:
        add("  no framing arm present in the log")
    for est in report.primary:
        lines.extend(_estimate_lines(est))
        add("")

    add("-" * 78)
    add("SECONDARY OUTCOMES -- Holm within the secondary family, GATEKEPT on")
    add("the primary contrast (P5). Compact table; full detail in --json.")
    add("-" * 78)
    add(f"  {'outcome':<22}{'arm':<5}{'Delta':>9}{'CI low':>9}{'CI high':>9}"
        f"{'Holm p':>9}{'n':>7}  verdict")
    for est in report.secondary:
        add(f"  {est.outcome:<22}{est.arm:<5}{_fmt(est.point):>9}"
            f"{_fmt(est.ci_low):>9}{_fmt(est.ci_high):>9}"
            f"{_fmt_p(est.p_adjusted):>9}{est.n_arm:>7}  {est.verdict}")
    add("")
    add("-" * 78)
    add("HOW TO READ THE VERDICTS")
    add("-" * 78)
    add("  INSUFFICIENT_POWER is not a null result. It means the realised")
    add("  precision is worse than the effect the design was built to see, so")
    add("  the point estimate is noise-dominated and is NOT a finding.")
    add("  NULL_RULED_OUT is a real negative result: powered, and everything")
    add("  worth shipping is outside the interval.")
    for note in report.notes:
        add("  " + note)
    return "\n".join(lines)


def report_to_dict(report: AnalysisReport) -> dict:
    def est_dict(est):
        if est is None:
            return None
        out = asdict(est)
        out["notes"] = list(est.notes)
        out["gates_failed"] = list(est.gates_failed)
        return out
    return {
        "generated_at": report.generated_at,
        "prereg_sha256": report.prereg_sha256,
        "headline": report.headline,
        "venue": report.venue,
        "interim": report.interim,
        "n_records": report.n_records,
        "n_units": report.n_units,
        "intake": report.intake,
        "balance": {"status": report.balance.status,
                    "hard_fail": report.balance.hard_fail,
                    "length_confounded_arms": list(report.balance.length_confounded_arms),
                    "items": [asdict(i) for i in report.balance.items]},
        "presence": est_dict(report.presence),
        "primary": [est_dict(e) for e in report.primary],
        "secondary": [est_dict(e) for e in report.secondary],
        "notes": report.notes,
    }


# ==========================================================================
# 8. SIMULATION -- validating the estimator before any real data exists
#
# The randomisation is NOT re-implemented here. The simulator drives the real
# experiments/assign.py Assigner over synthetic decision points, so what is
# validated is the estimator against the randomiser that will actually run, not
# against a tidy model of it. Only the OUTCOME is synthetic, and its truth is
# injected as a constant risk difference so the Mantel-Haenszel estimand is
# exactly the injected number and "recovers roughly that" is a checkable claim.
# ==========================================================================

_OPPONENTS = (("hidden", None, 0.00, 0.42),
              ("agent", "Quantile", -0.34, 0.14),
              ("agent", "pas-2", +0.06, 0.14),
              ("agent", "champion", +0.10, 0.10),
              ("agent", "theta", -0.05, 0.10),
              ("agent", "chotu", +0.18, 0.10))
_DELTAS = (0.8, 0.9, 0.95, 1.0)
_MONEY = (100.0, 10000.0, 1000000.0)


class _World:
    """The synthetic response surface.

    Shape taken from the measured corpus: a flat ~9% below the cliff, a step at
    a share-to-responder of 0.40, ~55-65% above it. Opponent and configuration
    random effects are real and shared, so units genuinely are correlated within
    opponent and within configuration -- otherwise a cluster-robust variance
    would have nothing to prove.
    """

    def __init__(self, seed=0, effect=0.0, effect_arm="F2",
                 concession_effect=0.0, share_leak=0.0, icc_sd=0.12):
        self.rng = random.Random(seed)
        self.effect = float(effect)
        self.effect_arm = effect_arm
        self.concession_effect = float(concession_effect)
        self.share_leak = float(share_leak)
        self.icc_sd = icc_sd
        self._opp_effect = {}
        self._cfg_effect = {}

    def opponent_effect(self, key, base):
        if key not in self._opp_effect:
            self._opp_effect[key] = base + self.rng.gauss(0.0, self.icc_sd)
        return self._opp_effect[key]

    def config_effect(self, key):
        if key not in self._cfg_effect:
            self._cfg_effect[key] = self.rng.gauss(0.0, self.icc_sd)
        return self._cfg_effect[key]

    def base_accept(self, share, opp_key, opp_base, cfg_key):
        cliff = 1.0 / (1.0 + math.exp(-(share - 0.40) / 0.028))
        p = 0.07 + 0.52 * cliff + 0.14 * max(0.0, share - 0.47)
        p += self.opponent_effect(opp_key, opp_base) * 0.5
        p += self.config_effect(cfg_key) * 0.5
        return min(0.90, max(0.02, p))

    def accept(self, share, opp_key, opp_base, cfg_key, arm):
        p = self.base_accept(share, opp_key, opp_base, cfg_key)
        if arm == self.effect_arm:
            p = min(0.98, max(0.0, p + self.effect))
        return 1 if self.rng.random() < p else 0

    def concession(self, arm):
        value = self.rng.gauss(0.02, 0.09)
        if arm == self.effect_arm:
            value += self.concession_effect
        return value


def _bargaining_turn(gid, me, round_no, share, opponent, config, history):
    """A live-shaped (game, action, plan) triple for one of our bargaining
    offers. Built as dicts and handed to assign.context_of rather than
    constructing a Context by hand, so the simulation exercises the same field
    reading the fleet does."""
    money = config["money"]
    mine = round(money * (1.0 - share), 2)
    theirs = round(money - mine, 2)
    delta_me, delta_opp = config["delta_me"], config["delta_opp"]
    game = {
        "game_id": gid, "game_family": "bargaining", "your_player": me,
        "opponent": {"type": opponent[0], "name": opponent[1]},
        "phase": "offer", "valid_actions": {"type": "offer"},
        "game_state": {
            "round": round_no, "max_rounds": config["max_rounds"],
            "horizon_known": config["horizon_known"],
            "money_to_divide": money,
            "complete_information": config["complete_information"],
            "messages_allowed": True, "current_player": me, "proposer": me,
            "delta_1": delta_me if me == "player_1" else delta_opp,
            "delta_2": delta_opp if me == "player_1" else delta_me,
            "history": list(history)},
    }
    action = ({"alice_gain": mine, "bob_gain": theirs} if me == "player_1"
              else {"alice_gain": theirs, "bob_gain": mine})
    rounds_left = max(1, config["max_rounds"] - round_no + 1)
    plan = {"money": money, "delta_me": delta_me, "delta_opp": delta_opp,
            "rounds_left": rounds_left,
            "spe_share": (1.0 - delta_opp) / max(1e-9, 1.0 - delta_me * delta_opp),
            "target": mine, "concessions_left": max(0, (rounds_left // 2) - 1),
            "continuation_if_refused": mine * delta_me}
    return game, action, plan


def _negotiation_turn(gid, me, round_no, price, opponent, config):
    game = {
        "game_id": gid, "game_family": "negotiation", "your_player": me,
        "opponent": {"type": opponent[0], "name": opponent[1]},
        "phase": "decision", "valid_actions": {"type": "decision"},
        "game_state": {
            "round": round_no, "max_rounds": config["max_rounds"],
            "horizon_known": True,
            "complete_information": config["complete_information"],
            "messages_allowed": True, "current_player": me},
    }
    action = {"decision": "RejectOffer", "product_price": round(price, 2)}
    plan = {"role": config["role"], "my_value": config["my_value"],
            "target": round(price, 2),
            "rounds_left": max(1, config["max_rounds"] - round_no + 1)}
    return game, action, plan


def _draw_share(rng, in_band=0.60):
    """Exogenous, arm-independent, and re-weighted the way design 3.3(1) asks:
    ~60% of the mass inside [0.33,0.47] where the response curve is steep."""
    if rng.random() < in_band:
        return rng.uniform(0.33, 0.47)
    return rng.uniform(0.05, 0.95)


def _make_assigner(arms=None, reps=2, weights=None, log_dir=None,
                   experiment_id="sim"):
    from experiments import assign as _assign
    return _assign.Assigner(
        experiment_id=experiment_id,
        arms=tuple(arms) if arms else ("A0", "A1", "F1", "F2", "F5"),
        reps=reps, weights=weights or {CONTROL_NEUTRAL: 2},
        log_dir=log_dir or ".", enabled=True,
        kill_file=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "__no_such_kill_file__"))


def simulate_units(n_games=900, effect=0.08, effect_arm="F2", seed=1,
                   arms=None, reps=2, weights=None, venue="bargaining",
                   in_band=0.60, share_leak=0.0, concession_effect=0.0,
                   icc_sd=0.12, experiment_id="sim"):
    """Fast in-memory simulation: real Assigner, synthetic outcomes, Units built
    directly. Returns ``(units, truth)`` where ``truth[arm]`` is the injected
    risk difference for that arm -- exactly, by construction."""
    from experiments import assign as _assign
    rng = random.Random(seed)
    world = _World(seed=seed + 7717, effect=effect, effect_arm=effect_arm,
                   concession_effect=concession_effect, share_leak=share_leak,
                   icc_sd=icc_sd)
    assigner = _make_assigner(arms, reps, weights, experiment_id=experiment_id)
    units = []
    for index in range(n_games):
        gid = f"sim-{seed}-{index}"
        opponent = _OPPONENTS[rng.randrange(len(_OPPONENTS))]
        me = "player_1" if rng.random() < 0.5 else "player_2"
        horizon_known = rng.random() < 0.5
        config = {
            "money": _MONEY[rng.randrange(len(_MONEY))],
            "delta_me": _DELTAS[rng.randrange(len(_DELTAS))],
            "delta_opp": _DELTAS[rng.randrange(len(_DELTAS))],
            "horizon_known": horizon_known,
            "max_rounds": 12 if horizon_known else 99,
            "complete_information": rng.random() < 0.5,
            "role": "buyer" if rng.random() < 0.5 else "seller",
            "my_value": 8000.0,
        }
        cfg_key = "|".join(str(config[k]) for k in
                           ("money", "delta_me", "delta_opp", "horizon_known",
                            "complete_information"))
        opp_key = opponent[1] or "hidden"
        first_round = 1 if me == "player_1" else 2
        history, game_units = [], []
        accepted_at, settle = None, None
        our_rounds = list(range(first_round, min(config["max_rounds"], 12) + 1, 2))
        for round_no in our_rounds:
            share = _draw_share(rng, in_band)
            game, action, plan = _bargaining_turn(
                gid, me, round_no, share, opponent, config, history)
            ctx = _assign.context_of(game, action, plan, probe="randomized")
            ok, _flags = _assign.eligible(ctx)
            if not ok:
                continue
            assignment = assigner.draw(ctx)
            if assignment is None:
                continue
            arm = assignment.arm
            # THE LEAK, used only by the adversarial validation scenario: an arm
            # that moves the number is exactly what balance check B1 exists to
            # catch, so the validation has to be able to produce one.
            effective_share = share + (share_leak if arm == effect_arm else 0.0)
            accepted = world.accept(effective_share, opp_key, opponent[2],
                                    cfg_key, arm)
            unit = Unit(
                probe="randomized", game_id=gid, round=round_no,
                ts=float(index * 100 + round_no),
                decision_key=f"{gid}:{round_no}:offer",
                experiment_id=assigner.experiment_id,
                arm_set_version=assigner.arm_set_version,
                arm=arm, block_key=assignment.block_key,
                block_index=assignment.block_index,
                stratum_id=assignment.stratum_id, pool_id=assignment.pool_id,
                arm_pool=assignment.pool, p_assign=assignment.p_assign,
                p_assign_conditional=assignment.p_assign_conditional,
                propensities=dict(assignment.propensities),
                venue="bargaining",
                share_to_responder=effective_share,
                share_bucket=ctx.share_bucket,
                opponent_class=ctx.opponent_class,
                opponent_name=opponent[1], round_class=ctx.round_class,
                horizon_known=config["horizon_known"],
                complete_information=config["complete_information"],
                delta_me=config["delta_me"], delta_opp=config["delta_opp"],
                rounds_left=plan["rounds_left"], spe_share=plan["spe_share"],
                money_to_divide=config["money"], max_rounds=config["max_rounds"],
                your_player=me,
                message_len=(0 if arm == CONTROL_SILENT
                             else 230 + rng.randrange(-20, 21)),
                claim_id=f"{arm}-claim", claim_kind="fact",
            )
            unit.accepted = accepted
            unit.opp_concession_next = (None if accepted
                                        else world.concession(arm))
            game_units.append(unit)
            history.append({"round": round_no, "proposer": me})
            if accepted:
                accepted_at = round_no
                break
        if not game_units:
            continue
        settle = accepted_at if accepted_at else (our_rounds[-1] + 1)
        realised = (1.0 - game_units[-1].share_to_responder) if accepted_at else 0.0
        walked = 0
        for unit in game_units:
            unit.settle_round = float(settle)
            unit.settle_round_if_agreed = float(settle) if accepted_at else None
            unit.agreed = 1 if accepted_at else 0
            unit.realised_share = realised
            unit.walked_away = walked
            unit.join_status = "joined"
        arms_here = {u.arm for u in game_units}
        for i, unit in enumerate(game_units):
            unit.is_first_in_game = (i == 0)
            unit.game_pure_arm = len(arms_here) == 1
        units.extend(game_units)
    truth = {a: (effect if a == effect_arm else 0.0)
             for a in (arms or ("A0", "A1", "F1", "F2", "F5"))}
    return units, truth


def simulate_to_disk(outdir, n_games=200, effect=0.08, effect_arm="F2", seed=5,
                     arms=None, reps=2, weights=None, probe="randomized",
                     experiment_id="sim-disk", venue_mix=0.5):
    """Full round-trip: real Assigner.attach writing real experiment.jsonl
    records, plus game JSONs in the live schema, so the loader, the join and the
    outcome derivation are validated on files rather than on objects."""
    from experiments import assign as _assign
    rng = random.Random(seed)
    world = _World(seed=seed + 4242, effect=effect, effect_arm=effect_arm)
    log_dir = os.path.join(outdir, probe)
    games_dir = os.path.join(log_dir, "games")
    os.makedirs(games_dir, exist_ok=True)
    for stale in glob.glob(os.path.join(games_dir, "*.json")):
        os.remove(stale)
    path = os.path.join(log_dir, "experiment.jsonl")
    if os.path.exists(path):
        os.remove(path)
    assigner = _make_assigner(arms, reps, weights, log_dir=log_dir,
                              experiment_id=experiment_id)

    def compose(game, action, plan, arm):
        filler = "Settling now beats another round of this for both of us. "
        text = f"[{arm}] " + filler * 4
        return {"text": text[:230 + (hash(arm) % 17)], "claim_id": f"{arm}-c1",
                "claim_kind": "fact", "grammar_version": "sim"}

    written = 0
    for index in range(n_games):
        gid = f"disk-{seed}-{index}"
        opponent = _OPPONENTS[rng.randrange(len(_OPPONENTS))]
        me = "player_1" if rng.random() < 0.5 else "player_2"
        is_negotiation = rng.random() < venue_mix
        horizon_known = rng.random() < 0.5
        config = {
            "money": _MONEY[rng.randrange(len(_MONEY))],
            "delta_me": _DELTAS[rng.randrange(len(_DELTAS))],
            "delta_opp": _DELTAS[rng.randrange(len(_DELTAS))],
            "horizon_known": horizon_known,
            "max_rounds": 10 if is_negotiation else (12 if horizon_known else 99),
            "complete_information": rng.random() < 0.5,
            "role": "buyer" if rng.random() < 0.5 else "seller",
            "my_value": 8000.0,
        }
        cfg_key = "|".join(str(config[k]) for k in sorted(config))
        opp_key = opponent[1] or "hidden"
        history = []
        accepted_at, agreed_gain = None, None
        first = 1 if me == "player_1" else 2
        opp = _opponent_of(me)
        if not is_negotiation:
            # Alice proposes odd rounds, Bob even, always -- so the history
            # starts at round 1 whether or not round 1 is ours.
            for round_no in range(1, min(config["max_rounds"], 12) + 1):
                if (round_no % 2 == 1) != (me == "player_1"):   # the opponent's turn
                    theirs = round(config["money"] * 0.7, 2)
                    history.append({
                        "round": round_no, "proposer": opp,
                        "offer": {f"{opp}_gain": theirs,
                                  f"{me}_gain": round(config["money"] - theirs, 2),
                                  "message": "", "proposer": opp, "round": round_no},
                        "decision": "reject", "response_time_ms": 1500})
                    continue
                share = _draw_share(rng)
                game, action, plan = _bargaining_turn(
                    gid, me, round_no, share, opponent, config, history)
                handled = assigner.attach(game, action, plan, probe=probe,
                                          compose=compose)
                if not handled:
                    continue
                written += 1
                accepted = world.accept(share, opp_key, opponent[2], cfg_key,
                                        _last_arm(assigner, gid, round_no))
                mine = action["alice_gain"] if me == "player_1" else action["bob_gain"]
                history.append({
                    "round": round_no, "proposer": me,
                    "offer": {"player_1_gain": action["alice_gain"],
                              "player_2_gain": action["bob_gain"],
                              "message": action.get("message", ""),
                              "proposer": me, "round": round_no},
                    "decision": "accept" if accepted else "reject",
                    "response_time_ms": 1700})
                if accepted:
                    accepted_at, agreed_gain = round_no, mine
                    break
            outcome = "agreement" if accepted_at else "no_deal"
            payoff = agreed_gain if accepted_at else 0.0
            record = {
                "game_id": gid, "game_family": "bargaining", "your_player": me,
                "opponent": {"type": opponent[0], "name": opponent[1]},
                "status": "completed",
                "config": {"game_family": "bargaining",
                           "horizon_known": config["horizon_known"],
                           "money_to_divide": config["money"],
                           "max_rounds": config["max_rounds"],
                           "complete_information": config["complete_information"],
                           "messages_allowed": True},
                "result": {"outcome": outcome, "agreed_round": accepted_at,
                           "player_1_payoff": 0.0, "player_2_payoff": 0.0},
                "our_payoff": payoff, "opponent_payoff": 0.0,
                "rounds_played": len(history), "history": history, "our_turns": []}
        else:
            price = 12000.0
            for round_no in range(1, config["max_rounds"] + 1):
                if (round_no % 2 == 1) != (me == "player_1"):    # their offer
                    price = price * (0.98 if config["role"] == "buyer" else 1.02)
                    history.append({
                        "round": round_no,
                        "offer": {"price": round(price, 2), "message": "x",
                                  "from_player": opp, "round": round_no},
                        "decision": "RejectOffer", "decided_by": me,
                        "response_time_ms": 900,
                        "counteroffer": None})
                    continue
                our_price = round(price * (0.85 if config["role"] == "buyer" else 1.15), 2)
                game, action, plan = _negotiation_turn(
                    gid, me, round_no, our_price, opponent, config)
                handled = assigner.attach(game, action, plan, probe=probe,
                                          compose=compose)
                if not handled:
                    continue
                written += 1
                share_proxy = 0.30 + 0.25 * rng.random()
                accepted = world.accept(share_proxy, opp_key, opponent[2], cfg_key,
                                        _last_arm(assigner, gid, round_no))
                history.append({
                    "round": round_no,
                    "offer": {"price": our_price, "message": action.get("message", ""),
                              "from_player": me, "round": round_no},
                    "decision": "AcceptOffer" if accepted else "RejectOffer",
                    "decided_by": opp, "response_time_ms": 1400,
                    "counteroffer": None})
                if accepted:
                    accepted_at = round_no
                    break
            outcome = "agreement" if accepted_at else "no_deal"
            record = {
                "game_id": gid, "game_family": "negotiation", "your_player": me,
                "opponent": {"type": opponent[0], "name": opponent[1]},
                "status": "completed",
                "config": {"game_family": "negotiation",
                           "max_rounds": config["max_rounds"],
                           "horizon_known": True,
                           f"{me}_role": config["role"],
                           f"{me}_value": config["my_value"],
                           "complete_information": config["complete_information"],
                           "messages_allowed": True},
                "result": {"outcome": outcome, "agreed_round": accepted_at},
                "our_payoff": (2000.0 if accepted_at else 0.0),
                "opponent_payoff": 0.0,
                "rounds_played": len(history), "history": history, "our_turns": []}
        with open(os.path.join(games_dir, f"{gid}.json"), "w", encoding="utf-8") as fh:
            json.dump(record, fh)
    return {"log_dir": log_dir, "records_written": written, "games": n_games}


def _last_arm(assigner, gid, round_no):
    """The arm the assigner just used for this decision point, read back from
    its own memo rather than re-drawn (a second draw would consume a slot)."""
    for key, assignment in assigner._memo.items():
        if key.startswith(f"{gid}:{round_no}:"):
            return assignment.arm
    return None


# -- the simulation study --------------------------------------------------

def validation_study(reps=200, n_games=900, effect=0.08, effect_arm="F2",
                     seed0=20260819, arms=("A0", "A1", "F1", "F2", "F5"),
                     alpha=0.05, outcome=PRIMARY_OUTCOME, share_leak=0.0,
                     in_band=0.60, contrast_arms=None, progress=None):
    """Repeat the whole (randomise -> observe -> estimate) loop and report what
    the estimator did, not what it was supposed to do.

    Reported per arm: mean estimate against the injected truth, the empirical
    standard deviation of the estimate against the mean standard error the
    pipeline believes in (they should agree -- if the cluster-robust SE is too
    small the intervals will under-cover and that is exactly what this catches),
    coverage of the 95% interval, and the rejection rate of H0: Delta=0."""
    contrast_arms = contrast_arms or [a for a in arms
                                      if a not in (CONTROL_NEUTRAL,)]
    acc = {arm: {"points": [], "ses": [], "covered": 0, "rejected": 0,
                 "n_arm": [], "verdicts": Counter(), "ipw": [], "coarse": []}
           for arm in contrast_arms}
    balance_status = Counter()
    truth = {}
    for rep in range(reps):
        units, truth = simulate_units(
            n_games=n_games, effect=effect, effect_arm=effect_arm,
            seed=seed0 + rep, arms=arms, share_leak=share_leak,
            in_band=in_band, experiment_id=f"sim{rep}")
        for arm in contrast_arms:
            est = estimate_contrast(units, arm, CONTROL_NEUTRAL, outcome,
                                    alpha_ci=alpha, skip_ri=True)
            apply_verdict(est)
            if est.point is None or est.se is None:
                continue
            true = truth.get(arm, 0.0)
            acc[arm]["points"].append(est.point)
            acc[arm]["ses"].append(est.se)
            acc[arm]["n_arm"].append(est.n_arm)
            acc[arm]["verdicts"][est.verdict] += 1
            if est.point_ipw is not None:
                acc[arm]["ipw"].append(est.point_ipw)
            if est.point_coarse is not None:
                acc[arm]["coarse"].append(est.point_coarse)
            if est.ci_low <= true <= est.ci_high:
                acc[arm]["covered"] += 1
            if not (est.ci_low <= 0.0 <= est.ci_high):
                acc[arm]["rejected"] += 1
        if progress and (rep + 1) % progress == 0:
            print(f"    ... {rep + 1}/{reps} replications", flush=True)

    out = {}
    for arm, data in acc.items():
        n = len(data["points"])
        if n == 0:
            out[arm] = {"reps": 0}
            continue
        mean = sum(data["points"]) / n
        sd = statistics.pstdev(data["points"]) if n > 1 else 0.0
        out[arm] = {
            "reps": n,
            "truth": truth.get(arm, 0.0),
            "mean_estimate": mean,
            "bias": mean - truth.get(arm, 0.0),
            "empirical_sd": sd,
            "mean_se": sum(data["ses"]) / n,
            "se_ratio": (sum(data["ses"]) / n / sd) if sd > 0 else float("nan"),
            "coverage_95": data["covered"] / n,
            "rejection_rate": data["rejected"] / n,
            "mean_n_arm": sum(data["n_arm"]) / n,
            "mean_ipw": (sum(data["ipw"]) / len(data["ipw"])) if data["ipw"] else None,
            "mean_coarse": (sum(data["coarse"]) / len(data["coarse"]))
                           if data["coarse"] else None,
            "verdicts": dict(data["verdicts"]),
        }
    out["_balance"] = dict(balance_status)
    return out


def _study_lines(title, result, effect_arm):
    lines = [f"  {title}",
             f"    {'arm':<5}{'truth':>8}{'mean est':>10}{'bias':>9}"
             f"{'emp SD':>9}{'mean SE':>9}{'SE/SD':>7}{'cover95':>9}"
             f"{'reject':>8}{'n/arm':>8}"]
    for arm, data in result.items():
        if arm.startswith("_") or not data.get("reps"):
            continue
        lines.append(
            f"    {arm:<5}{data['truth']:>8.3f}{data['mean_estimate']:>10.4f}"
            f"{data['bias']:>+9.4f}{data['empirical_sd']:>9.4f}"
            f"{data['mean_se']:>9.4f}{data['se_ratio']:>7.2f}"
            f"{data['coverage_95']:>9.3f}{data['rejection_rate']:>8.3f}"
            f"{data['mean_n_arm']:>8.0f}")
    return lines


def validate(reps=200, n_games=900, effect=0.08, seed0=20260819,
             quick=False, verbose=True):
    """The validation the brief asks for, run end to end.

    Four scenarios, each of which must come out a particular way for the
    pipeline to be trustworthy:
      A  an 8-point effect is injected  -> recovered, intervals cover the truth
      B  no effect is injected          -> recovered as null, ~nominal type I
      C  the arm is made to leak into the offer share -> balance B1 must FAIL,
         which is the check the whole design leans on
      D  too little data                -> INSUFFICIENT_POWER, not a point
         estimate dressed up as a finding
    """
    if quick:
        reps, n_games = 40, 500
    out = {"reps": reps, "n_games_per_rep": n_games, "effect": effect,
           "prereg_sha256": PREREG_SHA256}
    lines = ["=" * 78,
             "VALIDATION OF THE ANALYSIS PIPELINE ON SIMULATED DATA",
             "=" * 78,
             f"prereg SHA-256   {PREREG_SHA256}",
             f"replications     {reps}   games per replication {n_games}",
             "randomisation    real experiments/assign.py Assigner "
             "(arms A0,A1,F1,F2,F5; reps=2; A1 weighted x2)",
             "outcome model    measured acceptance cliff at share 0.40, plus "
             "opponent and configuration random effects",
             ""]

    if verbose:
        print("scenario A: injecting +8 points on F2 ...", flush=True)
    a = validation_study(reps=reps, n_games=n_games, effect=effect,
                         effect_arm="F2", seed0=seed0,
                         progress=(reps // 4 or None) if verbose else None)
    out["A_effect"] = a
    lines += _study_lines(
        f"SCENARIO A -- truth: F2 = {effect:+.3f}, every other arm = 0.000",
        a, "F2") + [""]

    if verbose:
        print("scenario B: injecting nothing ...", flush=True)
    b = validation_study(reps=reps, n_games=n_games, effect=0.0,
                         effect_arm="F2", seed0=seed0 + 100000,
                         progress=(reps // 4 or None) if verbose else None)
    out["B_null"] = b
    lines += _study_lines("SCENARIO B -- truth: every arm = 0.000", b, "F2") + [""]

    if verbose:
        print("scenario C: adversarial -- arm leaks into the offer share ...",
              flush=True)
    leak_units, _ = simulate_units(n_games=n_games * 3, effect=0.0,
                                   effect_arm="F2", seed=seed0 + 200000,
                                   share_leak=0.05)
    clean_units, _ = simulate_units(n_games=n_games * 3, effect=0.0,
                                    effect_arm="F2", seed=seed0 + 200000)
    leak_balance = balance_check(leak_units, [], Counter(), draws=2000)
    clean_balance = balance_check(clean_units, [], Counter(), draws=2000)
    leak_item = next(i for i in leak_balance.items if i.key == "B1_share_on_arm")
    clean_item = next(i for i in clean_balance.items if i.key == "B1_share_on_arm")
    out["C_leak"] = {
        "leaked": {"status": leak_item.status, "p": leak_item.p_value,
                   "stat": leak_item.statistic, "overall": leak_balance.status,
                   "hard_fail": leak_balance.hard_fail},
        "clean": {"status": clean_item.status, "p": clean_item.p_value,
                  "stat": clean_item.statistic, "overall": clean_balance.status,
                  "hard_fail": clean_balance.hard_fail}}
    lines += [
        "  SCENARIO C -- the balance check must break when the arm touches the number",
        f"    arm leaks +0.05 of share : B1 {leak_item.status}"
        f"  stat={leak_item.statistic:.4f}  p={_fmt_p(leak_item.p_value)}"
        f"  -> hard_fail={leak_balance.hard_fail}",
        f"    no leak                  : B1 {clean_item.status}"
        f"  stat={clean_item.statistic:.4f}  p={_fmt_p(clean_item.p_value)}"
        f"  -> hard_fail={clean_balance.hard_fail}",
        ""]

    if verbose:
        print("scenario D: too little data ...", flush=True)
    small_units, _ = simulate_units(n_games=30, effect=effect, effect_arm="F2",
                                    seed=seed0 + 300000)
    small = estimate_contrast(small_units, "F2", CONTROL_NEUTRAL,
                              PRIMARY_OUTCOME, skip_ri=True)
    apply_verdict(small)
    out["D_underpowered"] = {"verdict": small.verdict, "n_arm": small.n_arm,
                             "point": small.point, "mde": small.mde,
                             "gates_failed": list(small.gates_failed)}
    lines += [
        "  SCENARIO D -- too little data must produce a refusal, not a finding",
        f"    n per arm {small.n_arm}, point {_fmt(small.point)}, "
        f"realised MDE {_fmt(small.mde)}",
        f"    VERDICT {small.verdict}  ({'; '.join(small.gates_failed)})",
        ""]

    verdict_a = a.get("F2", {})
    checks = [
        ("A: effect recovered within 0.02 of truth",
         abs(verdict_a.get("bias", 9)) < 0.02),
        ("A: 95% interval covers the truth at >=0.90",
         verdict_a.get("coverage_95", 0) >= 0.90),
        ("A: SE agrees with the empirical SD within 20%",
         0.8 <= verdict_a.get("se_ratio", 0) <= 1.25),
        ("B: null arms unbiased within 0.01",
         all(abs(b[arm]["bias"]) < 0.01 for arm in b if not arm.startswith("_")
             and b[arm].get("reps"))),
        ("B: type-I rate at or below 0.10",
         all(b[arm]["rejection_rate"] <= 0.10 for arm in b
             if not arm.startswith("_") and b[arm].get("reps"))),
        ("B: 95% coverage at >=0.90 for every arm",
         all(b[arm]["coverage_95"] >= 0.90 for arm in b
             if not arm.startswith("_") and b[arm].get("reps"))),
        ("C: balance FAILS when the arm leaks into the share",
         leak_balance.hard_fail),
        ("C: balance PASSES when it does not",
         not clean_balance.hard_fail),
        ("D: an underpowered contrast returns INSUFFICIENT_POWER",
         small.verdict == "INSUFFICIENT_POWER"),
    ]
    lines += ["-" * 78, "PASS/FAIL", "-" * 78]
    for label, ok in checks:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}]  {label}")
    out["checks"] = {label: bool(ok) for label, ok in checks}
    out["all_passed"] = all(ok for _, ok in checks)
    lines += ["", f"  ALL CHECKS: {'PASS' if out['all_passed'] else 'FAIL'}"]
    out["text"] = "\n".join(lines)
    return out
