"""Randomised message arms for NEGOTIATION offers — the number never moves.

Since the LLM persuasion fence (commit 4b0f45e) ``dispatch._play`` only composes
text for the family named in ``GLEE_LLM_FAMILIES`` (persuasion), so negotiation
offers have gone out with **no message at all**: 34,729 negotiation turns in the
logs carry text, and the most recent of them is from before the fence. The
channel is open on roughly half of our negotiation turns and we are silent on
every one of them. That is either free rating or a non-effect, and nobody knows
which, because the observational record cannot separate "we sent nothing" from
"nothing would have helped".

This module is the randomiser that answers it. It is the negotiation twin of
``experiments/assign.py`` (the bargaining framing-1 harness) and deliberately
copies its four load-bearing properties rather than inventing new ones:

1. **Downstream of the number.** ``attach()`` is handed an action whose numeric
   fields are already final. It sets exactly one key, ``"message"``, and it
   sha256-fingerprints every non-message, non-private field before and after.
   A mismatch reverts the message, trips a process-wide hard stop, and the turn
   proceeds exactly as it would have without this module. The fingerprint is
   byte-compatible with ``experiments.assign.numeric_fingerprint`` (asserted in
   ``tests/test_nego_arms.py``), so records from the two harnesses are directly
   comparable.

2. **Reproducible.** The arm at a decision point is a pure function of
   ``(EXPERIMENT_ID, arm_set_version, block_key, arrival_index)`` with the block
   permutation seeded from those alone. It is emphatically NOT the strategy's
   own generator: that stream sets prices, and sharing it would correlate the
   arm with the number and the experiment would measure nothing.

3. **Balanced within blocks, not globally.** Each ``(configuration cell x
   opponent class x arm pool)`` keeps its own permuted block, so per-cell
   imbalance is bounded by one partial block no matter how often the fleet
   restarts. The pool is part of the block key because it is state-dependent
   (N3 only exists where its claim is near-true), and a state-dependent pool is
   a pre-treatment confounder if you do not condition on it — measured, on the
   bargaining harness, at p=0.000 by stratum alone versus p=0.377 by block key.

4. **Revertible in one flag.** ``GLEE_NEGO_MSG_ARMS`` is read through
   ``runtime_flags`` at decision time, so ``fleet.py set`` reaches a running
   agent without a restart. Unset (the default) means this module is a single
   dict lookup and a ``return``: the action is byte-identical to today's.

The unit of randomisation is the DECISION POINT, not the game
-------------------------------------------------------------
An offer is the thing whose acceptance we are trying to move, so the estimand is
``P(their next move is AcceptOffer | our price x, arm m) - P(... | arm N1)``,
which is identified turn by turn. A game therefore mixes arms across its rounds,
exactly as framing-1 does in bargaining. The cost is that a game-level read is
intention-to-treat over a mixture; the benefit is ~10 design points per game
instead of one, and an outcome that is measured on the same turn as the
treatment. ``game_id`` is recorded so a modal-arm game-level analysis stays
possible.

There is no LLM anywhere in this path. The wording experiment retired today
measured LLM-worded persuasion at 46.3% conversion against 55.3% for plain
templates; these arms are template-only and cost nothing to run.

WHAT IS AND IS NOT VARIED
-------------------------
Varied: the CLAIM slot, and only the claim slot. Frame, request and filler pools
are shared across every messaged arm, so realised length is matched by
construction and the only systematic difference between N1 and a treatment arm
is the argument.

Never varied: the number. ``product_price`` and ``decision`` are chosen before
this module is called and are fingerprinted across the call.
"""

from __future__ import annotations

import hashlib
import json
import random
import threading

from . import messages, runtime_flags
from .actions import _num

__all__ = [
    "FLAG", "EXPERIMENT_ID", "STRATIFIER_VERSION", "ARMS", "DEFAULT_ARMS",
    "SILENT", "NEUTRAL", "PRECISE", "MANDATE",
    "enabled", "attach", "assign", "arm_pool", "stratum_of",
    "numeric_fingerprint", "hard_stopped", "reset",
]

#: The one flag. Off unless explicitly set; see ``_arm_set`` for the grammar.
FLAG = "GLEE_NEGO_MSG_ARMS"

EXPERIMENT_ID = "nego-msg-1"

#: Bump when the strata change: cells, round classes, or the opponent roster.
STRATIFIER_VERSION = "nego-strat-1"

SILENT, NEUTRAL, PRECISE, MANDATE = "N0", "N1", "N2", "N3"

#: Arm codes are shared with ``messages.negotiation_arm_message`` so the two
#: halves of the design cannot drift apart under a rename.
ARMS: tuple[str, ...] = (SILENT, NEUTRAL, PRECISE, MANDATE)
DEFAULT_ARMS = ARMS

#: N1 is the reference for every framing contrast, so its variance enters every
#: comparison and it carries twice the allocation of a single treatment arm.
WEIGHTS = {NEUTRAL: 2}

#: Copies of each arm per permuted block. One rep at these weights gives a
#: block of five (N0, N1, N1, N2, N3) — short enough that a restart-truncated
#: block costs little, long enough to permute meaningfully.
REPS = 1

#: A pool of one is not a randomisation. Where fewer than two arms are defined
#: the turn is left to the existing (silent) path rather than assigned.
MIN_POOL = 2

MIN_MESSAGE_CHARS = messages.NEGO_ARM_LEN_LO
MAX_MESSAGE_CHARS = messages.NEGO_ARM_LEN_HI

#: Opponents with enough logged negotiation offers to carry their own stratum
#: level; everything else pools to ``other-agent``. ``hidden`` (the server did
#: not disclose a name) is its own level and is the largest.
OPPONENT_ROSTER: tuple[str, ...] = ("Quantile", "pas-2", "champion")


# --------------------------------------------------------------------------
# numeric invariant
# --------------------------------------------------------------------------

def _sha(payload) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def numeric_fingerprint(action) -> str:
    """Hash of everything in an action that is NOT the message channel.

    Byte-compatible with ``experiments.assign.numeric_fingerprint``: same key
    filter, same canonicalisation, same digest. Unknown future keys are included
    by default, so a numeric field added later is protected without anyone
    having to remember this function exists.
    """
    if not isinstance(action, dict):
        return _sha(["<non-dict>", repr(action)])
    return _sha({k: v for k, v in action.items()
                 if k != "message" and not str(k).startswith("_")})


_HARD_STOP: list = []
_LOCK = threading.RLock()


def hard_stop(reason: str) -> None:
    with _LOCK:
        if not _HARD_STOP:
            _HARD_STOP.append(reason)


def hard_stopped():
    return _HARD_STOP[0] if _HARD_STOP else None


# --------------------------------------------------------------------------
# the flag
# --------------------------------------------------------------------------

_OFF = ("", "0", "off", "false", "no", "none")


def _raw_flag() -> str:
    try:
        return (runtime_flags.get(FLAG) or "").strip()
    except Exception:
        return ""


def _arm_set() -> tuple[tuple[str, ...], str | None]:
    """``(arms, pinned)`` for this agent, from the flag's small grammar.

    ================  ==================================================
    unset / 0 / off   OFF. This module does nothing at all.
    1 / on / true     all four arms, stratified assignment.
    ``N0,N1,N2``      that subset, stratified assignment.
    ``pin:N2``        always N2 where its claim exists. Single-arm mode,
                      for diagnostics and for the decide()-level tests;
                      it is a treatment with no concurrent control and
                      must not be used to measure anything.
    ================  ==================================================
    """
    raw = _raw_flag()
    low = raw.lower()
    if low in _OFF:
        return (), None
    if low in ("1", "on", "true", "yes"):
        return DEFAULT_ARMS, None
    if low.startswith("pin:"):
        name = raw.split(":", 1)[1].strip()
        return ((name,), name) if name in ARMS else ((), None)
    chosen = tuple(a.strip() for a in raw.split(",") if a.strip() in ARMS)
    return (chosen if len(chosen) >= 1 else (), None)


def enabled() -> bool:
    """Whether this agent is running the experiment at all."""
    if hard_stopped():
        return False
    try:
        return bool(_arm_set()[0])
    except Exception:
        return False


def arm_set_version(arms: tuple[str, ...]) -> str:
    """Derived, never declared, so an arm change cannot fail to bump it."""
    digest = _sha([arms, REPS, sorted(WEIGHTS.items()), STRATIFIER_VERSION,
                   OPPONENT_ROSTER, messages.NEGO_ARM_GRAMMAR_VERSION])[:10]
    return f"{STRATIFIER_VERSION}/r{REPS}/{digest}"


# --------------------------------------------------------------------------
# eligibility and strata
# --------------------------------------------------------------------------

def carries_offer(game: dict, action: dict) -> bool:
    """Whether this turn puts a price on the table with text allowed on it.

    A bare AcceptOffer or WalkAway ends the exchange and has nothing left to
    persuade about, so it is not a design point. A RejectOffer carrying a
    counter-price is: it is submitted as a ``decision``, which is why the rule
    is "there is a price in the action" rather than ``valid_actions.type ==
    "offer"`` — the literal rule would admit only round 1 and delete every
    counteroffer from the experiment.
    """
    try:
        if game.get("game_family") != "negotiation":
            return False
        state = game.get("game_state") or {}
        if state.get("messages_allowed") is False:
            return False
        action_type = (game.get("valid_actions") or {}).get("type")
        if action_type not in ("offer", "decision"):
            return False
        return action.get("product_price") is not None
    except Exception:
        return False


def opponent_class(game: dict) -> str:
    opponent = game.get("opponent") or {}
    name = opponent.get("name")
    if opponent.get("type") == "hidden" or not name:
        return "hidden"
    return name if name in OPPONENT_ROSTER else "other-agent"


def stratum_of(game: dict, plan: dict) -> str:
    """Configuration cell x opponent class.

    The cell is the part of the configuration that changes what a message could
    plausibly do: which seat we hold, whether a real deadline exists, whether
    the opponent's valuation is on the table (so our arithmetic is checkable),
    and whether we are early or late. Everything finer is adjusted for in the
    analysis rather than blocked on — blocks of two have no within-block
    variance to remove.
    """
    state = game.get("game_state") or {}
    role = "seller" if plan.get("i_am_seller") else "buyer"
    cap = "capped" if plan.get("capped") else "uncapped"
    info = "open" if state.get("complete_information") is True else "private"
    elapsed = _num(plan.get("elapsed"), 0.0)
    phase = "early" if elapsed < 0.5 else "late"
    return f"nego|{role}|{cap}|{info}|{phase}|opp:{opponent_class(game)}"


def arm_pool(game: dict, action: dict, plan: dict,
             arms: tuple[str, ...] = DEFAULT_ARMS) -> tuple[str, ...]:
    """The arms whose claim actually exists here, in the arm set's own order.

    N0 (silence) and N1 (neutral) are defined wherever the channel is open. N2
    always has a true derivation to state. N3 is defined only where its mandate
    language is not about to be contradicted by our own next concession — see
    ``messages.negotiation_arm_claim``. Arms that would go quiet are dropped
    BEFORE the draw so a block never spends a slot on a silent treatment.
    """
    out = []
    for name in arms:
        if name not in ARMS:
            continue
        if name in (SILENT, NEUTRAL):
            out.append(name)
            continue
        try:
            if messages.negotiation_arm_claim(name, game, action, plan) is not None:
                out.append(name)
        except Exception:
            pass
    return tuple(out)


# --------------------------------------------------------------------------
# assignment
# --------------------------------------------------------------------------

_STATE: dict = {"counters": {}, "memo": {}}


def reset() -> None:
    """Test-only: forget the block counters and the per-decision memo."""
    with _LOCK:
        _STATE["counters"] = {}
        _STATE["memo"] = {}
        _HARD_STOP.clear()


def _block(seed: str, pool: tuple[str, ...]) -> tuple[str, ...]:
    slots: list[str] = []
    for name in pool:
        slots.extend([name] * (REPS * max(1, int(WEIGHTS.get(name, 1)))))
    random.Random(seed).shuffle(slots)
    return tuple(slots)


def _decision_key(game: dict, action: dict) -> str:
    state = game.get("game_state") or {}
    return (f"{game.get('game_id')}:{state.get('round')}:"
            f"{(game.get('valid_actions') or {}).get('type')}")


def assign(game: dict, action: dict, plan: dict) -> dict | None:
    """Draw an arm for this decision point, or ``None`` when it is not one.

    Reads no number and returns no number. A decision point presented twice (an
    SDK retry after a rejected move) returns the memoised arm and does not burn
    a second block slot — burning slots on retries is a silent route to
    imbalance.
    """
    arms, pinned = _arm_set()
    if not arms:
        return None
    pool = arm_pool(game, action, plan, arms)
    if pinned is not None:
        return ({"arm": pinned, "pinned": True, "stratum_id": stratum_of(game, plan),
                 "arm_pool": list(pool), "block_key": None, "p_assign": 1.0}
                if pinned in pool else None)
    if len(pool) < MIN_POOL:
        return None

    version = arm_set_version(arms)
    stratum = stratum_of(game, plan)
    pool_id = _sha(pool)[:8]
    block_key = f"{stratum}||{pool_id}"
    key = _decision_key(game, action)

    with _LOCK:
        memo = _STATE["memo"].get(key)
        if memo is not None:
            return dict(memo, repeat=True)
        index = _STATE["counters"].get(block_key, 0)
        length = sum(REPS * max(1, int(WEIGHTS.get(n, 1))) for n in pool)
        block_index, position = divmod(index, length)
        seed = f"arm:{EXPERIMENT_ID}:{version}:{block_key}:{block_index}"
        sequence = _block(seed, pool)
        remaining = sequence[position:]
        arm = sequence[position]
        out = {
            "experiment_id": EXPERIMENT_ID,
            "arm_set_version": version,
            "arm": arm,
            "arm_pool": list(pool),
            "pool_id": pool_id,
            "stratum_id": stratum,
            "opponent_class": opponent_class(game),
            "block_key": block_key,
            "block_index": block_index,
            "block_position": position,
            "block_length": length,
            "arrival_index": index,
            "p_assign": (REPS * max(1, int(WEIGHTS.get(arm, 1)))) / length,
            "p_assign_conditional": remaining.count(arm) / len(remaining),
            "arm_rng_seed": seed,
            "pinned": False,
            "repeat": False,
        }
        _STATE["counters"][block_key] = index + 1
        _STATE["memo"][key] = out
        return dict(out)


# --------------------------------------------------------------------------
# the call site
# --------------------------------------------------------------------------

def _rng(game: dict) -> random.Random:
    """Wording variation, reproducible for a replay, and NOT the strategy's own
    stream — sharing that would couple the phrasing to the price draw. It is
    also independent of the arm, so frame and filler choices are drawn from the
    same stream in every arm and only the claim differs."""
    state = game.get("game_state") or {}
    return random.Random(f"nego-msg:{game.get('game_id')}:{state.get('round')}")


def attach(game: dict, action: dict, plan: dict | None = None) -> dict | None:
    """Draw an arm and put its message on ``action``, in place.

    Returns the provenance dict when the experiment took control of the channel
    — including the silent arm, where taking control means deliberately sending
    nothing — and ``None`` when it did not, in which case the caller's existing
    behaviour is untouched. Never raises: a message is never worth a turn.
    """
    try:
        return _attach(game, action, plan)
    except Exception:
        return None


def _attach(game: dict, action: dict, plan: dict | None) -> dict | None:
    if not enabled() or not isinstance(action, dict):
        return None
    if plan is None:
        plan = action.get("_plan")
    if not isinstance(plan, dict):
        return None
    if not carries_offer(game, action):
        return None

    before = numeric_fingerprint(action)
    drawn = assign(game, action, plan)
    if drawn is None:
        return None

    record = dict(drawn)
    record.update(game_id=game.get("game_id"),
                  round=(game.get("game_state") or {}).get("round"),
                  action_type=(game.get("valid_actions") or {}).get("type"),
                  numeric_sha256_before=before)

    if drawn["arm"] == SILENT:
        # Recorded exactly like every other arm. Logging only the messaged turns
        # would make silence invisible and the denominator wrong, which is the
        # exact confusion ("chose silence" vs "was not allowed to speak") that
        # makes the observational record unreadable.
        record.update(outcome="silent", message_len=0, message_sha256=None,
                      numeric_sha256_after=before, numeric_invariant_ok=True)
        _stamp(plan, record)
        return record

    composed = messages.negotiation_arm_message(drawn["arm"], game, action, plan,
                                                _rng(game))
    if not composed or not isinstance(composed.get("text"), str):
        record.update(outcome="compose_failed",
                      reason=(composed or {}).get("reason"),
                      numeric_sha256_after=before, numeric_invariant_ok=True)
        _stamp(plan, record)
        return None                    # not handled: caller keeps its behaviour

    text = composed["text"].strip()[:MAX_MESSAGE_CHARS].rstrip()
    action["message"] = text
    after = numeric_fingerprint(action)
    if after != before:
        # The message hook moved a number. Every record collected so far is now
        # suspect, so this stops the experiment rather than the turn.
        hard_stop(f"numeric invariance violated at {_decision_key(game, action)}")
        action.pop("message", None)
        record.update(outcome="invariance_violation", numeric_sha256_after=after,
                      numeric_invariant_ok=False)
        _stamp(plan, record)
        return None

    record.update(outcome="sent", message_len=len(text),
                  message_sha256=_sha(text),
                  claim_id=composed.get("claim_id"),
                  claim_kind=composed.get("claim_kind"),
                  grammar_version=composed.get("grammar_version"),
                  length_band_ok=MIN_MESSAGE_CHARS <= len(text) <= MAX_MESSAGE_CHARS,
                  numeric_sha256_after=after, numeric_invariant_ok=True)
    _stamp(plan, record)
    return record


def _stamp(plan: dict, record: dict) -> None:
    """Hang the design record off the plan.

    ``gamelog.turn`` already writes the plan verbatim beside the state, the
    action and the opponent, so this is the whole logging story: no second file,
    no second writer, and the join in the analysis is the turn record itself.
    """
    try:
        plan["msg_arm"] = record
    except Exception:
        pass
