"""Randomiser and logging contract for the message-framing experiment.

The estimand is ``P(accept | offer x, framing m) - P(accept | offer x, neutral)``.
It is only identified if the framing is drawn *after* the numbers are final and
if the draw is independent of everything the numbers depend on. This module is
the part of the design that makes both true, and the part that records enough
that the analysis never has to guess what the design was.

Four properties it is built to guarantee
----------------------------------------

1. **Downstream of the number.** Nothing here reads or returns a numeric field.
   ``attach()`` is handed an action that is already ``coerce``-d and sets exactly
   one key on it, ``"message"``. It fingerprints the numeric fields before and
   after and refuses to proceed — permanently, for the whole process — if they
   ever differ. See ``numeric_fingerprint`` and ``HARD_STOP``.

2. **Reproducible.** The arm at a decision point is a pure function of

       (experiment_id, arm_set_version, block_key, arrival_index)

   with the block permutation seeded by those first three. ``arrival_index`` is
   the only state, and ``replay()`` rebuilds it exactly from the log, so a
   restarted fleet continues the same sequence rather than starting a fresh one.
   A decision point that is presented twice (an SDK retry after a rejected move)
   returns the memoised arm and does *not* consume a second block slot — burning
   slots on retries is a silent route to imbalance.

   Order-dependence is intrinsic to blocking and is not hidden here: balance
   within a block *is* a constraint across arrivals, so the arm cannot be a
   function of the decision point alone. What is guaranteed is that the same
   arrival stream always yields the same assignment stream, and that the same
   decision point yields the same arm on replay of that stream.

3. **Balanced within blocks, not globally.** Intake is sequential, per-stratum n
   is small, and the fleet restarts constantly; simple randomisation drifts out
   of balance exactly in the thin strata that carry the effect. Each block key
   holds its own permuted block of ``reps`` copies of each eligible arm, and the
   block refills only when exhausted.

4. **Revertible in one flag.** The experiment is **off unless explicitly turned
   on**, and an operator can turn it off again without a restart by touching
   ``experiments/KILL``. Any exception anywhere returns "not handled" and the
   caller keeps its current template behaviour.

Balance is per assignment stream, not global across the fleet
-------------------------------------------------------------
Each agent process runs its own Assigner over its own log directory
(``supervise.py`` sets ``GLEE_LOG_DIR=logs/<probe>`` per agent), so five agents
are five independent streams. Sharing one counter across processes would need
cross-process locking on every turn and would buy nothing: with permuted blocks
each stream's imbalance is bounded by a single partial block, so fleet-wide
imbalance is bounded by (agents x one partial block) — a handful of offers
against thousands, and the analysis blocks on stratum regardless. Set
``GLEE_EXPERIMENT_ID`` per agent if you want the streams labelled distinctly in
the log rather than merely being distinct in fact.

The arm pool is part of the block key
-------------------------------------
Several arms are only defined in some states (F4 needs a prior offer of ours,
F6 needs ``complete_information=False``, F3 needs our own schedule to be nearly
out of concessions). If those arms sat in every block and were skipped when
ineligible, the block would never balance. So blocks are keyed by
``(stratum, arm_pool)``: a block is only ever formed over arms that are all
eligible for the states in it, and ``pool_id`` is logged so the analysis
compares like with like.

**The estimation stratum is therefore ``block_key`` = stratum x pool, NOT
``stratum_id``.** This is not a stylistic preference, it is measured. Replaying
the fleet's 62,786 logged turns through this randomiser and regressing the
realised offer share on the arm (the design's own 5(f) balance proof, run as a
permutation test):

    conditioning on stratum_id only    imbalance 0.0439 vs null 0.0225, p = 0.000
    conditioning on block_key          imbalance 0.0180 vs null 0.0172, p = 0.377

The leak is not in the randomisation — it is that the *pool* is state-dependent
(F3 needs a near-terminal round, F6 needs incomplete information), so two pools
inside one share bucket can carry very different offers: within
``bargaining|s0|opp:hidden|r2+`` one pool averages a 0.000 share and another
0.207. Pool is a pre-treatment variable and conditioning on it is legitimate;
failing to condition on it manufactures an arm/share correlation out of nothing.
``analyse.py`` must group by ``block_key``.

Integration (specification — no file under ``glee_agent/`` is edited here)
-------------------------------------------------------------------------
See ``SPEC`` at the bottom of this module for the exact two insertions.
The call site is one line::

    if not experiment.attach(game, action, plan, probe=name, log=log,
                             compose=framings.compose, coerce=coerce):
        action["message"] = messages.compose(game, action, plan, _rng(game))

``attach`` returns True when the experiment took control of the channel —
*including* the SILENT arm, where taking control means deliberately sending
nothing. Returning False means "not in the experiment, do what you already do".
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import threading
import time
from dataclasses import dataclass, replace

__all__ = [
    "Arm", "Assignment", "Assigner", "Context",
    "ARM_SETS", "DEFAULT_ARMS", "SILENT", "NEUTRAL",
    "attach", "assign", "default_assigner", "reset_default_assigner",
    "framing_hooks",
    "context_of", "eligible", "stratum_of", "arm_pool",
    "numeric_fingerprint", "hard_stop", "hard_stopped", "clear_hard_stop",
    "SPEC",
]

# --------------------------------------------------------------------------
# Versions. Anything that changes the meaning of a record bumps a version, and
# the version travels in the record, so data from before and after a change is
# never silently pooled.
# --------------------------------------------------------------------------

#: Bump when the stratifier changes: buckets, round classes, or the opponent
#: roster. Per the design the roster is re-levelled from a frozen snapshot,
#: never mid-stage.
STRATIFIER_VERSION = "strat-1"

#: Named opponents with enough accumulated offers to carry their own stratum
#: level (>=30 in the snapshot behind ``STRATIFIER_VERSION``). Everything else
#: pools to ``other-agent``; ``hidden`` is its own level and is the largest.
OPPONENT_ROSTER: tuple[str, ...] = ("Quantile", "pas-2", "champion")

#: Share-to-responder bucket edges. The middle buckets are the analysis
#: population.
#:
#: DEVIATION FROM THE WRITTEN DESIGN, deliberate. The design's edges were
#: (.33, .38, .42, .47), which puts the measured acceptance cliff *inside* the
#: [.38, .42) bucket: P(accept) is .13 at .38 and .60 at .41, so that one
#: stratum would carry a 47-point internal spread — precisely the variance
#: blocking exists to remove, left in the block. 0.40 is added as an edge so the
#: cliff is a bucket boundary rather than a bucket interior. Cost: one more
#: level, i.e. thinner strata; benefit: the largest single source of
#: within-block outcome variance in the whole design is eliminated.
SHARE_EDGES: tuple[float, ...] = (0.33, 0.38, 0.40, 0.42, 0.47)

MAX_MESSAGE_CHARS = 320          # design 5(e); an eighth of the rules' 2,000
MIN_MESSAGE_CHARS = 180          # band floor, recorded not enforced

LOG_FILENAME = "experiment.jsonl"
KILL_FILENAME = "KILL"


# --------------------------------------------------------------------------
# Small local helpers. This module imports nothing from glee_agent on purpose:
# it must be impossible for an edit here to change what the fleet decides.
# --------------------------------------------------------------------------

def _num(value, default=None):
    """Coerce to a finite float, or ``default``. Mirrors actions._num loosely."""
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        value = float(value)
        return value if value == value and value not in (float("inf"), float("-inf")) else default
    if isinstance(value, str):
        try:
            value = float(value.strip().replace("$", "").replace(",", "").replace("%", ""))
        except ValueError:
            return default
        return value if value == value else default
    return default


def _sha(payload) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def numeric_fingerprint(action) -> str:
    """Hash of everything in an action that is NOT the message channel.

    This is the object the experiment is forbidden to move. ``message`` and the
    private ``_``-prefixed keys are excluded; every other key is included,
    including ones this module has never heard of, so a future numeric field is
    protected by default rather than by remembering to add it here.
    """
    if not isinstance(action, dict):
        return _sha(["<non-dict>", repr(action)])
    return _sha({k: v for k, v in action.items()
                 if k != "message" and not str(k).startswith("_")})


# --------------------------------------------------------------------------
# Hard stop. Process-wide, one-way (except in tests). Tripped by a numeric
# invariance violation, which is the one failure that would invalidate every
# record collected so far rather than just the current turn.
# --------------------------------------------------------------------------

_HARD_STOP: list = []
_HARD_STOP_LOCK = threading.Lock()


def hard_stop(reason: str) -> None:
    with _HARD_STOP_LOCK:
        if not _HARD_STOP:
            _HARD_STOP.append(reason)


def hard_stopped():
    return _HARD_STOP[0] if _HARD_STOP else None


def clear_hard_stop() -> None:
    """Test-only. Live code has no reason to un-stop a stopped experiment."""
    with _HARD_STOP_LOCK:
        _HARD_STOP.clear()


# --------------------------------------------------------------------------
# Arms
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Arm:
    """One cell.

    ``predicate`` decides whether this arm is *defined* at a decision point. It
    reads only the Context — never the arm draw, never anything downstream — so
    the eligible pool is a deterministic function of the state, which is what
    lets the pool be part of the block key.
    """
    name: str
    venues: frozenset          # {"bargaining"} / {"negotiation"} / both
    label: str = ""            # human-readable, for the log and the write-up
    is_control: bool = False
    sends_message: bool = True
    predicate: object = None   # Callable[[Context], bool] | None

    def defined_at(self, ctx: "Context") -> bool:
        if ctx.venue not in self.venues:
            return False
        if self.predicate is None:
            return True
        try:
            return bool(self.predicate(ctx))
        except Exception:
            return False


BOTH = frozenset({"bargaining", "negotiation"})
BARG = frozenset({"bargaining"})
NEGO = frozenset({"negotiation"})

#: Arm codes are the short ones (A0, A1, F1..F6) so that this module and
#: ``experiments/framing.py`` — which composes the text — name the same cells
#: the same way and no translation table can drift between them.
SILENT = "A0"
NEUTRAL = "A1"


def _f3_defined(ctx: "Context") -> bool:
    """Commitment language only where the commitment is close to true.

    The solver's own schedule must imply at most one further concession. If the
    plan states that directly we use it; otherwise we fall back to the
    conservative proxy of being near the end of the horizon. A commitment
    falsified next round is worse than no commitment, so 'unknown' means 'no'.
    """
    if ctx.concessions_left is not None:
        return ctx.concessions_left <= 1
    return ctx.rounds_left is not None and ctx.rounds_left <= 2


def _f4_defined(ctx: "Context") -> bool:
    # Reciprocal concession accounting needs a prior offer of ours to reference.
    return ctx.round is not None and ctx.round >= 2


def _f5_defined(ctx: "Context") -> bool:
    # Solver authority quotes a derived number; there has to be one in the plan.
    if ctx.venue == "bargaining":
        return ctx.spe_share is not None
    return ctx.plan_target is not None


def _f6_defined(ctx: "Context") -> bool:
    # A patience claim is cheap talk only where it cannot be checked.
    return ctx.complete_information is False


#: Every arm the design defines. An ArmSet is a subset of these names.
ALL_ARMS: tuple[Arm, ...] = (
    Arm(SILENT,  BOTH, "silent", is_control=True, sends_message=False),
    Arm(NEUTRAL, BOTH, "neutral, length-matched", is_control=True),
    Arm("F1", BOTH, "reference re-basing"),
    Arm("F2", BOTH, "delay arithmetic"),
    Arm("F3", BOTH, "commitment / final number", predicate=_f3_defined),
    Arm("F4", NEGO, "reciprocal concession accounting", predicate=_f4_defined),
    Arm("F5", BOTH, "solver authority", predicate=_f5_defined),
    Arm("F6", NEGO, "patience bluff", predicate=_f6_defined),
)

ARMS_BY_NAME = {a.name: a for a in ALL_ARMS}

#: Stage arm sets. ``stage2`` is a placeholder: the two surviving framings are
#: chosen from Stage-1 negotiation data and this tuple is edited then, which
#: bumps ``arm_set_version`` automatically.
ARM_SETS: dict = {
    "stage1": tuple(a.name for a in ALL_ARMS),
    "stage2": (SILENT, NEUTRAL, "F2", "F5"),
    "controls_only": (SILENT, NEUTRAL),
}

DEFAULT_ARMS: tuple[str, ...] = ARM_SETS["stage1"]


# --------------------------------------------------------------------------
# Context: everything the design blocks on, adjusts for, or wants in the record
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Context:
    venue: str | None
    action_type: str | None
    game_id: str
    round: int | None
    your_player: str | None
    opponent_type: str | None
    opponent_name: str | None
    messages_allowed: object          # True / False / None (absent)
    is_proposer: bool
    carries_offer: bool
    share_to_responder: float | None
    money_to_divide: float | None
    horizon_known: object
    complete_information: object
    delta_me: float | None
    delta_opp: float | None
    rounds_left: float | None
    spe_share: float | None
    plan_target: float | None
    concessions_left: float | None
    probe: str | None = None

    @property
    def opponent_class(self) -> str:
        if self.opponent_type == "hidden" or not self.opponent_name:
            return "hidden"
        return self.opponent_name if self.opponent_name in OPPONENT_ROSTER else "other-agent"

    @property
    def share_bucket(self) -> str:
        if self.share_to_responder is None:
            return "na"
        share = self.share_to_responder
        for i, edge in enumerate(SHARE_EDGES):
            if share < edge:
                return f"s{i}"
        return f"s{len(SHARE_EDGES)}"

    @property
    def round_class(self) -> str:
        return "r1" if self.round == 1 else "r2+"


def context_of(game, action, plan, probe=None) -> Context:
    """Read the blocking variables and covariates out of the live structures."""
    game = game if isinstance(game, dict) else {}
    action = action if isinstance(action, dict) else {}
    plan = plan if isinstance(plan, dict) else {}
    state = game.get("game_state") or {}
    opponent = game.get("opponent") or {}
    family = game.get("game_family")
    me = game.get("your_player")

    money = _num(state.get("money_to_divide"))
    share_to_responder = None
    if family == "bargaining" and money:
        mine = _num(action.get("alice_gain" if me == "player_1" else "bob_gain"))
        if mine is not None:
            share_to_responder = max(0.0, min(1.0, (money - mine) / money))

    # In bargaining the proposer is whoever the server says; only the proposer
    # may attach text, which is why this is an eligibility condition and not a
    # covariate. In negotiation both sides may speak on their own turn.
    proposer = state.get("proposer") or state.get("current_player")
    if family == "bargaining":
        is_proposer = (game.get("valid_actions") or {}).get("type") == "offer"
    else:
        is_proposer = proposer == me or proposer is None

    delta_me = _num(plan.get("delta_me"))
    delta_opp = _num(plan.get("delta_opp"))
    if delta_me is None and me:
        delta_me = _num(state.get("delta_1" if me == "player_1" else "delta_2"))
    if delta_opp is None and me:
        delta_opp = _num(state.get("delta_2" if me == "player_1" else "delta_1"))

    # A negotiation counteroffer is submitted as a *decision* that carries a
    # price, not as an "offer" (see randomized_strategy and dispatch's own
    # _wants_message, which already treats negotiation decisions as messageable).
    #
    # DEVIATION FROM THE WRITTEN DESIGN, deliberate. The design's eligibility
    # rule is `valid_actions.type == "offer"`. Applied literally it admits only
    # round 1 of a negotiation and drops every counteroffer — which would delete
    # the whole Stage-1 screening venue, the ~10-offers-per-game endpoint, and
    # F4_RECIPROCITY (defined only from round 2) along with it. Measured over the
    # 61k logged turns: the literal rule yields 0 eligible F4 turns.
    action_type = (game.get("valid_actions") or {}).get("type")
    if family == "bargaining":
        carries_offer = action_type == "offer"
    elif family == "negotiation":
        carries_offer = (action_type == "offer"
                         or (action_type == "decision"
                             and _num(action.get("product_price")) is not None))
    else:
        carries_offer = False

    return Context(
        venue=family,
        action_type=action_type,
        game_id=str(game.get("game_id", "?")),
        round=int(_num(state.get("round"), 0) or 0) or None,
        your_player=me,
        opponent_type=opponent.get("type"),
        opponent_name=opponent.get("name"),
        messages_allowed=state.get("messages_allowed"),
        is_proposer=bool(is_proposer),
        carries_offer=bool(carries_offer),
        share_to_responder=share_to_responder,
        money_to_divide=money,
        horizon_known=state.get("horizon_known"),
        complete_information=state.get("complete_information"),
        delta_me=delta_me,
        delta_opp=delta_opp,
        rounds_left=_num(plan.get("rounds_left")),
        spe_share=_num(plan.get("spe_share")),
        plan_target=_num(plan.get("target")),
        concessions_left=_num(plan.get("concessions_left")),
        probe=probe,
    )


def eligible(ctx: Context) -> tuple[bool, dict]:
    """Evaluated and recorded BEFORE assignment, per the design's §2.3.

    Returns ``(ok, flags)``; ``flags`` goes in the record whether or not the
    turn is assigned, so the denominator is auditable rather than inferred.
    """
    flags = {
        "venue_ok": ctx.venue in BOTH,
        "messages_allowed": ctx.messages_allowed is not False,
        # An accept or a walkaway ends the exchange and has nothing to persuade
        # about; only a turn that puts a number on the table is a design point.
        "carries_offer": ctx.carries_offer,
        "we_propose": ctx.is_proposer,
    }
    return all(flags.values()), flags


def stratum_of(ctx: Context) -> str:
    """Coarse stratum: share bucket x opponent class x round class.

    Deeper stratifications measured in-sample overfit (blocks of size 2 with
    zero within-block variance by construction); everything else in the design
    is adjusted for in the model instead of blocked on.
    """
    return "|".join((str(ctx.venue), ctx.share_bucket, f"opp:{ctx.opponent_class}",
                     ctx.round_class))


def arm_pool(ctx: Context, arms: tuple[str, ...]) -> tuple[str, ...]:
    """The arms *defined* at this decision point, in the arm set's own order."""
    return tuple(name for name in arms
                 if name in ARMS_BY_NAME and ARMS_BY_NAME[name].defined_at(ctx))


# --------------------------------------------------------------------------
# Assignment
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Assignment:
    arm: str
    stratum_id: str
    pool: tuple
    pool_id: str
    block_key: str
    block_index: int
    block_position: int
    block_length: int
    arrival_index: int
    p_assign: float                  # marginal, weight_a / block_length
    p_assign_conditional: float      # realised, given how much of the block is spent
    propensities: dict               # arm -> conditional propensity at this draw
    arm_rng_seed: str
    repeat: bool = False


def _block_sequence(seed: str, pool: tuple, reps: int, weights=None) -> tuple:
    """One permuted block: ``reps * weight[arm]`` copies of each arm, shuffled
    by a dedicated generator.

    Weights exist because the design over-allocates the neutral control by
    sqrt(k): A1 is the reference for every framing contrast, so its variance
    enters every comparison and it should carry more sample than any single
    treatment arm.

    The generator is seeded from a string that contains the experiment id, the
    arm-set version, the block key and the block index — and from nothing else.
    It is emphatically NOT the ``random.Random(seed)`` stream inside
    ``randomized_strategy``: that stream is consumed in call order to draw the
    offer share, so sharing it would make the arm and the offer deterministically
    correlated and the experiment would measure nothing.
    """
    weights = weights or {}
    slots = []
    for name in pool:
        slots.extend([name] * (reps * max(1, int(weights.get(name, 1)))))
    random.Random(seed).shuffle(slots)
    return tuple(slots)


class Assigner:
    """Stratified permuted-block randomiser with a durable arrival counter.

    Thread-safe: the SDK runs a worker pool and two turns in the same stratum
    can be drawn concurrently.
    """

    def __init__(self, experiment_id: str = "framing-1",
                 arms: tuple = DEFAULT_ARMS,
                 reps: int = 2,
                 weights=None,
                 log_dir: str = "logs",
                 enabled: bool | None = None,
                 disabled_arms=(),
                 max_message_chars: int = MAX_MESSAGE_CHARS,
                 min_pool_size: int = 2,
                 log_ineligible: bool = False,
                 kill_file: str | None = None):
        self.experiment_id = experiment_id
        self.arms = tuple(a for a in arms if a in ARMS_BY_NAME)
        self.reps = max(1, int(reps))
        #: Relative allocation per arm. Default over-allocates the neutral
        #: reference 2:1, the design's sqrt(4) for the four-cell confirmatory
        #: stage. Blocks stay exactly balanced at these ratios.
        self.weights = dict(weights) if weights else {NEUTRAL: 2}
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, LOG_FILENAME)
        self.disabled_arms = set(disabled_arms)
        self.max_message_chars = max_message_chars
        #: A pool of one is not a randomisation: the propensity is 1.0 and the
        #: block carries no contrast. Measured over the fleet's logged turns,
        #: 2,698 of 8,740 eligible turns fall in strata where only A0 has a true
        #: claim available; assigning there would inflate the silent arm with
        #: turns that can never be compared to anything. Those turns are left to
        #: the existing template path instead.
        self.min_pool_size = max(1, int(min_pool_size))
        self.log_ineligible = log_ineligible
        self.kill_file = (kill_file if kill_file is not None
                          else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            KILL_FILENAME))
        self._explicit_enabled = enabled
        self._counters: dict = {}
        self._memo: dict = {}
        self._lock = threading.RLock()
        self._kill_checked = 0.0
        self._kill_present = False

    # -- versioning --------------------------------------------------------

    @property
    def live_arms(self) -> tuple:
        return tuple(a for a in self.arms if a not in self.disabled_arms)

    @property
    def arm_set_version(self) -> str:
        """Derived, not declared, so killing an arm cannot fail to bump it.

        Data collected under different arm sets, different block sizes or a
        different stratifier carries a different version tag and is never
        silently pooled.
        """
        digest = _sha([self.live_arms, self.reps, sorted(self.weights.items()),
                       STRATIFIER_VERSION, OPPONENT_ROSTER, SHARE_EDGES])[:10]
        return f"{STRATIFIER_VERSION}/r{self.reps}/{digest}"

    # -- the one flag ------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Off unless explicitly on, and killable without a restart.

        Precedence: a tripped hard stop, then the KILL file, then the explicit
        constructor flag, then ``GLEE_EXPERIMENT``. The default is OFF: a fleet
        that has not opted in behaves exactly as it does today.
        """
        if hard_stopped():
            return False
        if self._kill_file_present():
            return False
        if not self.live_arms:
            return False
        if self._explicit_enabled is not None:
            return bool(self._explicit_enabled)
        return os.environ.get("GLEE_EXPERIMENT", "").strip().lower() in (
            "1", "on", "true", "yes")

    def _kill_file_present(self) -> bool:
        # Stat at most once a second: an operator gets sub-second revert without
        # putting a syscall on every turn.
        now = time.time()
        if now - self._kill_checked > 1.0:
            self._kill_checked = now
            try:
                self._kill_present = os.path.exists(self.kill_file)
            except OSError:
                self._kill_present = False
        return self._kill_present

    def kill(self, reason: str = "manual") -> None:
        """Write the kill file. Instant, process-independent revert."""
        try:
            os.makedirs(os.path.dirname(self.kill_file) or ".", exist_ok=True)
            with open(self.kill_file, "w", encoding="utf-8") as handle:
                handle.write(f"{time.time()} {reason}\n")
        except OSError:
            pass
        self._kill_checked = 0.0

    def revive(self) -> None:
        try:
            os.remove(self.kill_file)
        except OSError:
            pass
        self._kill_checked = 0.0

    def kill_arm(self, name: str) -> None:
        """Drop one arm (design §6.2). Blocks re-form over the remainder at the
        next refill and ``arm_set_version`` changes, so the killed arm's data
        stays in the analysis under its own tag."""
        with self._lock:
            self.disabled_arms.add(name)

    # -- the draw ----------------------------------------------------------

    def decision_key(self, ctx: Context) -> str:
        return f"{ctx.game_id}:{ctx.round}:{ctx.action_type}"

    def draw(self, ctx: Context, pool: tuple | None = None) -> Assignment | None:
        """Assign an arm. Pure with respect to the action: reads no number and
        returns no number. ``None`` when no arm is defined here.

        ``pool`` narrows the eligible set further — used to consult the
        composer's own per-arm eligibility, so a block never spends a slot on an
        arm that would have gone quiet. The pool is part of the block key, so
        narrowing forms a different block rather than corrupting an existing one.
        """
        if pool is None:
            pool = arm_pool(ctx, self.arms)
        pool = tuple(n for n in pool if n not in self.disabled_arms)
        if len(pool) < self.min_pool_size:
            return None
        stratum_id = stratum_of(ctx)
        pool_id = _sha(pool)[:8]
        block_key = f"{stratum_id}||{pool_id}"
        key = self.decision_key(ctx)

        with self._lock:
            memo = self._memo.get(key)
            if memo is not None:
                # A repeat presentation of the same decision point (SDK retry
                # after a rejected move). Same arm, and NO new block slot.
                return replace(memo, repeat=True)

            index = self._counters.get(block_key, 0)
            length = sum(self.reps * max(1, int(self.weights.get(n, 1))) for n in pool)
            block_index, position = divmod(index, length)
            seed = (f"arm:{self.experiment_id}:{self.arm_set_version}:"
                    f"{block_key}:{block_index}")
            sequence = _block_sequence(seed, pool, self.reps, self.weights)

            remaining = sequence[position:]
            total = len(remaining)
            propensities = {name: remaining.count(name) / total for name in pool}
            arm = sequence[position]

            assignment = Assignment(
                arm=arm, stratum_id=stratum_id, pool=pool, pool_id=pool_id,
                block_key=block_key, block_index=block_index,
                block_position=position, block_length=length,
                arrival_index=index,
                p_assign=(self.reps * max(1, int(self.weights.get(arm, 1)))) / length,
                p_assign_conditional=propensities[arm],
                propensities=propensities, arm_rng_seed=seed,
            )
            self._counters[block_key] = index + 1
            self._memo[key] = assignment
            return assignment

    # -- record ------------------------------------------------------------

    def record(self, game, action, plan, ctx: Context,
               assignment: Assignment | None, flags: dict,
               outcome: str, before: str, after: str | None = None,
               message: str | None = None, log=None, provenance=None) -> dict:
        """Write one JSONL line in the envelope ``gamelog.turn`` already uses.

        The envelope keys are byte-identical to a turns.jsonl record — including
        the ones ``scripts/transcript.py`` reads back ("ts", "round", "phase",
        "action_type", "action", "plan", "source", "error", "stage") — with the
        design fields hung off an extra ``"experiment"`` key. It is written to
        ``<log_dir>/experiment.jsonl``, NOT to turns.jsonl: appending our own
        lines to turns.jsonl would make ``GameLog.write_game_record`` emit each
        of our moves twice and quietly corrupt every transcript.
        """
        design = {
            "experiment_id": self.experiment_id,
            "arm_set_version": self.arm_set_version,
            "stratifier_version": STRATIFIER_VERSION,
            "probe": ctx.probe,
            "outcome": outcome,
            "eligibility_flags": flags,
            # blocking variables
            "stratum_id": assignment.stratum_id if assignment else stratum_of(ctx),
            "share_bucket": ctx.share_bucket,
            "opponent_class": ctx.opponent_class,
            "round_class": ctx.round_class,
            # assignment
            "arm": assignment.arm if assignment else None,
            "arm_label": (ARMS_BY_NAME[assignment.arm].label
                          if assignment and assignment.arm in ARMS_BY_NAME else None),
            "arm_pool": list(assignment.pool) if assignment else [],
            "pool_id": assignment.pool_id if assignment else None,
            # The analysis stratum. stratum_id alone is NOT sufficient — see
            # the module docstring: the eligible pool is state-dependent, so
            # grouping by stratum_id manufactures an arm/share correlation.
            "block_key": assignment.block_key if assignment else None,
            "block_index": assignment.block_index if assignment else None,
            "block_position": assignment.block_position if assignment else None,
            "block_length": assignment.block_length if assignment else None,
            "arrival_index": assignment.arrival_index if assignment else None,
            "p_assign": assignment.p_assign if assignment else None,
            "p_assign_conditional": (assignment.p_assign_conditional
                                     if assignment else None),
            "propensities": assignment.propensities if assignment else None,
            "arm_rng_seed": assignment.arm_rng_seed if assignment else None,
            "repeat": bool(assignment.repeat) if assignment else False,
            "decision_key": self.decision_key(ctx),
            # the numeric action, hashed either side of the message hook
            "numeric_action_sha256_before": before,
            "numeric_action_sha256_after": after,
            "numeric_invariant_ok": (after is None or after == before),
            # message
            "message_len": len(message) if message else 0,
            "message_sha256": _sha(message) if message else None,
            "length_band_ok": (message is None or
                               MIN_MESSAGE_CHARS <= len(message) <= self.max_message_chars),
            # covariates adjusted for in the model
            "opponent_type": ctx.opponent_type,
            "opponent_name": ctx.opponent_name,
            "share_to_responder": ctx.share_to_responder,
            "money_to_divide": ctx.money_to_divide,
            "horizon_known": ctx.horizon_known,
            "complete_information": ctx.complete_information,
            "delta_me": ctx.delta_me,
            "delta_opp": ctx.delta_opp,
            "rounds_left": ctx.rounds_left,
            "spe_share": ctx.spe_share,
            "messages_allowed": ctx.messages_allowed,
            # Whatever the composer chose to report about the claim it built:
            # which one fired, fact or bluff, its own grammar version.
            "composer": provenance,
        }
        state = (game or {}).get("game_state") or {}
        record = {
            "ts": time.time(),
            "game_id": ctx.game_id,
            "game_family": (game or {}).get("game_family"),
            "your_player": ctx.your_player,
            "phase": (game or {}).get("phase") or state.get("phase"),
            "round": ctx.round,
            "opponent": (game or {}).get("opponent"),
            "action_type": ctx.action_type,
            "state": state,
            "plan": plan,
            "action": {k: v for k, v in (action or {}).items()
                       if not str(k).startswith("_")},
            "source": f"experiment:{assignment.arm}" if assignment else "experiment:none",
            "error": None,
            "stage": None,
            "experiment": design,
        }
        self._append(record, self._dir_for(log))
        return record

    def _dir_for(self, log) -> str:
        """The fleet runs five agents with five log directories. If the caller
        hands us its GameLog we write beside its turns.jsonl, so an agent's
        experiment records live with that agent's games and the join in
        analyse.py is a directory listing rather than a guess."""
        directory = getattr(log, "dir", None)
        return directory if isinstance(directory, str) and directory else self.log_dir

    def _append(self, record: dict, directory: str | None = None) -> None:
        directory = directory or self.log_dir
        try:
            os.makedirs(directory, exist_ok=True)
            line = json.dumps(record, default=str) + "\n"
            with self._lock:
                with open(os.path.join(directory, LOG_FILENAME), "a",
                          encoding="utf-8") as handle:
                    handle.write(line)
        except OSError:
            pass          # a lost record is never worth a lost turn

    # -- replay ------------------------------------------------------------

    def replay(self, path: str | None = None) -> int:
        """Rebuild the arrival counters and the memo from an experiment log.

        Called once at startup so a restarted fleet continues the same
        assignment sequence instead of restarting every block. Records are
        re-walked in file order and the (block_index, block_position) are
        re-derived rather than trusted, so a truncated or interleaved file
        degrades to a shorter-but-consistent history rather than to a corrupt
        counter.
        """
        path = path or self.log_path
        counters: dict = {}
        memo: dict = {}
        try:
            handle = open(path, encoding="utf-8")
        except OSError:
            return 0
        seen = 0
        with handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                design = record.get("experiment") or {}
                if design.get("experiment_id") != self.experiment_id:
                    continue
                if design.get("arm_set_version") != self.arm_set_version:
                    continue
                arm, block_key = design.get("arm"), design.get("block_key")
                if not arm or not block_key or design.get("repeat"):
                    continue
                key = design.get("decision_key")
                if key in memo:
                    continue
                index = counters.get(block_key, 0)
                pool = tuple(design.get("arm_pool") or ())
                length = design.get("block_length") or (
                    sum(self.reps * max(1, int(self.weights.get(n, 1))) for n in pool)) or 1
                block_index, position = divmod(index, length)
                memo[key] = Assignment(
                    arm=arm, stratum_id=design.get("stratum_id", ""), pool=pool,
                    pool_id=design.get("pool_id", ""), block_key=block_key,
                    block_index=block_index, block_position=position,
                    block_length=length, arrival_index=index,
                    p_assign=design.get("p_assign") or 0.0,
                    p_assign_conditional=design.get("p_assign_conditional") or 0.0,
                    propensities=design.get("propensities") or {},
                    arm_rng_seed=design.get("arm_rng_seed", ""),
                )
                counters[block_key] = index + 1
                seen += 1
        with self._lock:
            self._counters = counters
            self._memo = memo
        return seen

    # -- the call site -----------------------------------------------------

    def attach(self, game, action, plan, probe=None, log=None,
               compose=None, coerce=None, arm_eligible=None) -> bool:
        """Draw an arm and put its message on ``action``, in place.

        Returns True when the experiment took control of the message channel —
        including the SILENT arm, where control means deliberately attaching
        nothing. False means "not handled": the caller should do whatever it
        does today. Total: any exception returns False.

        ``compose(game, action, plan, arm) -> str | None`` is injected rather
        than imported so this module has no dependency on the composer, and so a
        broken composer degrades to today's templates rather than to silence
        (silent-by-accident treatment turns would contaminate the SILENT arm,
        which is the one contrast this design cannot afford to lose).

        ``compose`` may return a plain string, or a dict with a ``"text"`` key
        and any provenance it wants recorded (``experiments.framing.describe``
        returns exactly that: which claim fired, whether it was fact or bluff,
        the grammar version). The provenance lands in the record under
        ``experiment.composer`` and is never read back into the assignment.

        ``arm_eligible(arm, game, action, plan) -> bool`` is consulted BEFORE the
        draw, so a block never spends a slot on an arm that has no true claim
        available and would therefore go quiet. Narrowing the pool forms a
        different block key rather than corrupting an existing block.

        ``coerce(action, game) -> dict`` is injected so the after-fingerprint is
        taken on the action as it will actually be submitted, not on the action
        before the caller's own re-coerce.
        """
        try:
            return self._attach(game, action, plan, probe, log, compose, coerce,
                                arm_eligible)
        except Exception:
            return False

    def _attach(self, game, action, plan, probe, log, compose, coerce,
                arm_eligible=None) -> bool:
        if not self.enabled:
            return False
        ctx = context_of(game, action, plan, probe=probe)
        ok, flags = eligible(ctx)
        before = numeric_fingerprint(action)
        if not ok:
            if self.log_ineligible:
                self.record(game, action, plan, ctx, None, flags,
                            "ineligible", before, log=log)
            return False

        pool = arm_pool(ctx, self.arms)
        if arm_eligible is not None:
            narrowed = []
            for name in pool:
                try:
                    if arm_eligible(name, game, action, plan):
                        narrowed.append(name)
                except Exception:
                    pass
            pool = tuple(narrowed)

        assignment = self.draw(ctx, pool=pool)
        if assignment is None:
            self.record(game, action, plan, ctx, None, flags,
                        "no_arm_defined", before, log=log)
            return False

        arm = ARMS_BY_NAME[assignment.arm]

        if not arm.sends_message:
            # SILENT. Recorded exactly like every other arm: logging only the
            # messaged turns would make this arm invisible and the denominator
            # wrong, which is precisely how the earlier observational reading
            # confused "chose silence" with "was not allowed to speak".
            self.record(game, action, plan, ctx, assignment, flags,
                        "silent", before, after=before, log=log)
            return True

        message, provenance = None, None
        if compose is not None:
            try:
                composed = compose(game, action, plan, assignment.arm)
            except Exception:
                composed = None
            if isinstance(composed, dict):
                provenance = {k: v for k, v in composed.items() if k != "text"}
                message = composed.get("text")
            else:
                message = composed
        if not message or not isinstance(message, str):
            self.record(game, action, plan, ctx, assignment, flags,
                        "compose_failed", before, after=before, log=log,
                        provenance=provenance)
            return False

        message = message.strip()
        if len(message) > self.max_message_chars:
            message = message[: self.max_message_chars].rstrip()

        action["message"] = message
        after = numeric_fingerprint(action)

        if coerce is not None:
            coerced = coerce(action, game)
            if isinstance(coerced, dict):
                after = numeric_fingerprint(coerced)
                action.clear()
                action.update(coerced)
                message = action.get("message") or message

        if after != before:
            # The message hook moved a number. Every record collected under this
            # arm set is now suspect, so this stops the whole experiment rather
            # than the turn: revert the message and let the caller proceed.
            hard_stop(f"numeric invariance violated at {self.decision_key(ctx)}")
            self.record(game, action, plan, ctx, assignment, flags,
                        "invariance_violation", before, after=after,
                        message=message, log=log, provenance=provenance)
            action.pop("message", None)
            return False

        self.record(game, action, plan, ctx, assignment, flags,
                    "sent", before, after=after, message=message, log=log,
                    provenance=provenance)
        return True


# --------------------------------------------------------------------------
# Module-level default, so the call site is one line and one import
# --------------------------------------------------------------------------

_DEFAULT: list = []
_DEFAULT_LOCK = threading.Lock()


def _parse_weights(spec: str):
    out = {}
    for item in spec.split(","):
        if ":" not in item:
            continue
        name, _, value = item.partition(":")
        try:
            out[name.strip()] = max(1, int(value))
        except ValueError:
            continue
    return out or None


def default_assigner() -> Assigner:
    """Built once, from the environment, on first use.

    ``GLEE_EXPERIMENT``            "1"/"on"/"true"/"yes" turns it on. Anything
                                   else, including unset, leaves it OFF.
    ``GLEE_EXPERIMENT_ID``         experiment id, default "framing-1".
    ``GLEE_EXPERIMENT_ARMS``       an ARM_SETS name, or a comma-separated list.
    ``GLEE_EXPERIMENT_REPS``       copies of each arm per block, default 2.
    ``GLEE_EXPERIMENT_WEIGHTS``    "A1_NEUTRAL:2,..." relative allocation.
    ``GLEE_EXPERIMENT_KILL_ARMS``  comma-separated arms to drop (design 6.2).
    ``GLEE_LOG_DIR``               log directory, default "logs".
    """
    with _DEFAULT_LOCK:
        if _DEFAULT:
            return _DEFAULT[0]
        spec = os.environ.get("GLEE_EXPERIMENT_ARMS", "stage1").strip()
        arms = ARM_SETS.get(spec)
        if arms is None:
            arms = tuple(a.strip() for a in spec.split(",") if a.strip()) or DEFAULT_ARMS
        try:
            reps = int(os.environ.get("GLEE_EXPERIMENT_REPS", "2"))
        except ValueError:
            reps = 2
        assigner = Assigner(
            experiment_id=os.environ.get("GLEE_EXPERIMENT_ID", "framing-1"),
            arms=arms,
            reps=reps,
            weights=_parse_weights(os.environ.get("GLEE_EXPERIMENT_WEIGHTS", "")),
            log_dir=os.environ.get("GLEE_LOG_DIR", "logs"),
            disabled_arms=[a.strip() for a in
                           os.environ.get("GLEE_EXPERIMENT_KILL_ARMS", "").split(",")
                           if a.strip()],
        )
        try:
            assigner.replay()
        except Exception:
            pass
        _DEFAULT.append(assigner)
        return assigner


def reset_default_assigner() -> None:
    """Test-only."""
    with _DEFAULT_LOCK:
        _DEFAULT.clear()


def framing_hooks():
    """Bind to ``experiments/framing.py``: ``(compose, arm_eligible)``.

    Imported lazily and adapted here rather than in the call site, so that this
    module has no import-time dependency on the composer and a missing or broken
    framing module degrades to "not handled" — today's templates — instead of
    taking a turn down with it.

    Note the argument orders differ (``framing`` puts the arm first, mirroring
    ``glee_agent.messages.compose`` with the arm prepended); the adapter is the
    only place that fact lives.
    """
    try:
        from experiments import framing
    except Exception:
        return None, None

    def compose(game, action, plan, arm):
        try:
            # describe() returns the text plus the provenance the analysis
            # wants: which claim fired, fact or bluff, grammar version.
            return framing.describe(arm, game, action, plan)
        except Exception:
            try:
                return framing.compose(arm, game, action, plan)
            except Exception:
                return None

    def arm_eligible(arm, game, action, plan):
        try:
            return bool(framing.eligible(arm, game, action, plan))
        except Exception:
            return False

    return compose, arm_eligible


def attach(game, action, plan, probe=None, log=None, compose=None, coerce=None,
           arm_eligible=None) -> bool:
    """One-line call site. See ``Assigner.attach``.

    With no composer supplied it binds to ``experiments/framing.py`` itself, so
    the integration in dispatch is genuinely one line and one import.
    """
    try:
        if compose is None and arm_eligible is None:
            compose, arm_eligible = framing_hooks()
        return default_assigner().attach(game, action, plan, probe=probe, log=log,
                                         compose=compose, coerce=coerce,
                                         arm_eligible=arm_eligible)
    except Exception:
        return False


def assign(game, action, plan, probe=None) -> Assignment | None:
    """Draw without side effects on the action and without logging. For tests,
    for ``analyse.py``, and for anything that wants to know the arm without
    committing to it."""
    try:
        ctx = context_of(game, action, plan, probe=probe)
        ok, _ = eligible(ctx)
        if not ok:
            return None
        return default_assigner().draw(ctx)
    except Exception:
        return None


# --------------------------------------------------------------------------
# Handover
# --------------------------------------------------------------------------

SPEC = """\
SPECIFICATION — three insertions, to be applied by the fleet owner between
restarts. Nothing under glee_agent/, sim/, scripts/ or tests/ is edited by the
experiment code itself.

(1) glee_agent/dispatch.py, inside _play(), in the existing `if _wants_message`
    block. The arm is drawn AFTER coerce(), so it is causally downstream of the
    number by construction:

        if _wants_message(game):
            message = None
            from experiments import assign as experiment
            if experiment.attach(game, action, plan, probe="champion", log=log,
                                 coerce=coerce):
                source += "+exp-msg"
            else:
                ... existing llm / messages.compose path, unchanged ...

    attach() mutates action["message"] in place and re-runs the caller's own
    coerce, so the line that follows the existing path (`action = coerce(...)`)
    stays correct and idempotent.

(2) glee_agent/probes.py, make_probe()'s custom-strategy wrapper. Today it
    returns coerce(inner(game), game) directly and never reaches the message
    hook, which is why `randomized` — the one agent with exogenous offer shares,
    the only one that identifies the response surface — has sent 0 messages in
    every messages_allowed game. Insert the SAME hook after that coerce and
    before log.turn:

        action = coerce(inner(game), game)
        ...
        if _wants_message(game):
            experiment.attach(game, action, plan=None, probe=name, log=log,
                              coerce=coerce)
        if log is not None:
            log.turn(game, action, None, source=f"probe:{name}")

    inner(game) is untouched, so randomized's numeric draw stays bit-identical.
    Note plan=None here: the F5 and F3 predicates read the
    plan, so both are simply never eligible on probes that do not produce one,
    and the arm pool (and therefore the block) reflects that rather than
    silently unbalancing.

(3) glee_agent/strategies/bargaining.py, ONE optional plan field. F3 is
    specified to fire only where our own concession schedule implies at most one
    further concession, and the plan does not currently expose that. Without it
    this module falls back to the conservative proxy `rounds_left <= 2`, which
    over the fleet's 61k logged turns leaves F3 eligible on 358 negotiation
    turns but only 2 bargaining turns — i.e. F3 is effectively undefined in the
    confirmatory venue. Adding

        plan["concessions_left"] = <steps remaining in the schedule>

    to bargaining.decide's _plan makes F3 eligible where the design intends.
    Until it exists, F3 should be treated as a negotiation-only screening arm.

THREE DEVIATIONS FROM THE WRITTEN DESIGN, all deliberate, each marked at its
definition above:

  * SHARE_EDGES gains 0.40. The design's buckets put the measured acceptance
    cliff inside [0.38, 0.42), leaving a 47-point outcome spread inside a single
    block — the exact variance blocking exists to remove.
  * Eligibility is "this turn puts a number on the table", not
    `valid_actions.type == "offer"`. Negotiation counteroffers are submitted as
    decisions carrying a price; the literal rule admits only round 1 of a
    negotiation, deleting the Stage-1 screening venue and F4 with
    it. Measured: 1,740 eligible turns under the literal rule, 8,460 under this
    one, with F4 going from 0 to 784.
  * A pool of one is not assigned (min_pool_size=2). A0 is eligible wherever the
    channel is open, so in strata where no framing has a true claim available it
    would otherwise take every slot at propensity 1.0 — 2,698 of 8,740 otherwise
    eligible turns in the replay, all of them uncomparable to anything. Those
    turns are left to the existing template path.

ANALYSIS CONTRACT (the part that is easiest to get wrong):
  * Group by `block_key`, not by `stratum_id`. The eligible pool is
    state-dependent and is therefore a confounder; see the module docstring for
    the measured permutation test, p=0.000 by stratum_id versus p=0.377 by
    block_key on the same replay.
  * Weight by `p_assign_conditional`, not by `p_assign`. Under permuted blocks
    the realised per-draw probability is not the marginal one.
  * Split on `arm_set_version`. Killing an arm changes it automatically.
  * Drop `outcome != "sent"` and `outcome != "silent"` records from the effect
    estimate; keep them for the CONSORT-style intake table.

REVERT: touch experiments/KILL, or unset GLEE_EXPERIMENT. Either takes effect
within a second, with no restart and no code change; attach() then returns
False everywhere and the existing template path runs unmodified.
"""
