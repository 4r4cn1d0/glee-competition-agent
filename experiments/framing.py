"""Compositional message grammar for the randomised framing experiment.

The decision core stays LLM-free. This module is a pure string builder over
``(game, action, plan)``: no I/O, no network, no model call, and therefore no
arm-dependent latency for an opponent to condition on (``response_time_ms`` is
visible in the history, so a per-arm latency difference would confound the whole
experiment).

WHAT THIS IS
------------
``compose(arm, game, action, plan, rng)`` returns the message for one
experimental arm, or ``None`` when that arm sends nothing. It mirrors
``glee_agent.messages.compose`` in every convention that matters:

* it never raises — a message is never worth risking the move over;
* it returns ``None`` when the phase carries no legal text, when
  ``messages_allowed`` is false, or when ``plan`` is missing;
* output is capped well under the 2,000-character server limit.

The numbers are already fixed by the time this is called. Nothing here reads,
writes, or influences a numeric field.

THE GRAMMAR
-----------
Four slots, assembled in order::

    [FRAME] + [ECONOMIC CLAIM] + [COMMITMENT] + [REQUESTED ACTION]   (+ filler)

* **FRAME** — states the position plainly. Filled by every arm from the *same*
  pool, so it carries no treatment.
* **CLAIM** — the treatment. Each arm owns an ordered list of claim builders;
  the *first* whose precondition holds is used, so claim selection is a
  deterministic function of the state and only the surface wording is random.
  This is what keeps the semantics of an arm constant while its surface varies.
* **COMMITMENT** — filled only by F3, F5 and F6, and only under the truth gate
  described below. Empty for A1/F1/F2/F4, constantly so, which is what makes
  the emptiness harmless rather than confounding.
* **REQUESTED ACTION** — a close. ``A1`` uses a neutral hand-back; treatment
  arms use a push. Both pools are fixed and arm-constant.
* **FILLER** — argument-free, factually true, on-topic padding drawn from one
  shared pool, used only to bring every messaged arm into the same 180–320
  character band. The band is narrow on purpose: message length is a
treatment-correlated feature the opponent can see, so per-arm realised
length is a balance table in the analysis, not an afterthought. Because the pool is shared, the only systematic difference
  between A1-neutral and any treatment arm is the CLAIM (and, for F3/F5/F6, the
  COMMITMENT).

TRUTH DISCIPLINE — the part that matters more than variety
----------------------------------------------------------
Every claim this module can emit is tagged ``fact`` or ``bluff``.

* ``fact`` — arithmetic or a rule of the game, computed from the state or the
  plan we were handed. If the precondition for a fact is absent (an opponent
  discount factor we were never told, a history we do not have), the claim is
  not emitted and the arm falls through to its next claim, or becomes
  ineligible. We never assert a number we assumed as though we knew it; where
  the plan used an assumed opponent discount factor, the claim says so.
* ``bluff`` — an unverifiable statement about *our own* position. Legal under
  the rules ("bluffing, misrepresentation"). Only F6 can emit one, only where
  the opponent structurally cannot check it (``complete_information`` is false
  in bargaining; private valuations in negotiation), and only where our own
  deterministic schedule is not about to contradict it next round.

**No arm ever emits a falsifiable promise about our own future moves.** We
learned that the expensive way: a persuasion template promised candour while
pushing a known-low unit, and the buyer verifies that on the next reveal. So:

* F3's "commitment" is not a promise. It is a *fact* — either "there is no
  round after this one" / "you make the last offer of this game, not me", or
  "below this number refusing pays me more than agreeing". Neither can be
  broken by anything we do next round.
* No arm claims candour, honesty, or a track record in persuasion when the
  plan says we are recommending a unit we know to be low quality
  (``plan['quality_is_high'] is False``). Those arms go quiet instead.

SCOPE
-----
Ordinary strategic persuasion only: fairness re-basing, delay arithmetic,
structural commitment, reciprocity, equilibrium authority, and a patience
bluff. Nothing here attempts to move the opponent out of the game frame, quote
history they never sent, imitate a system or tool channel, extract a prompt, or
induce a malformed action. Messages are capped at 320 characters, an eighth of
what the rules permit, so nothing here is cap-filling either.

Persuasion support exists so the composer is *total*, not because the
experiment runs there: in text-mode persuasion the message IS the move, so a
silent arm would be an invalid action. ``in_experiment_scope()`` excludes
persuasion for exactly that reason.

INTEGRATION (spec — no file outside experiments/ is edited here)
----------------------------------------------------------------
In ``dispatch._play``, strictly after ``coerce`` has finalised the numbers::

    if _wants_message(game):
        arm = assign(game, action, plan)          # None => not in the experiment
        if arm is None:
            message = messages.compose(game, action, plan, _rng(game))
        else:
            message = framing.compose(arm, game, action, plan, _arm_rng(game))
        if message:
            action["message"] = message
            action = coerce(action, game)

``arm`` must be drawn from a generator seeded independently of the one inside
``randomized_strategy`` — sharing that stream would correlate arm assignment
with offer share and the experiment would measure nothing. ``compose``
returning ``None`` means "send nothing", which is the A0 arm and is a result,
not a failure; it must NOT be back-filled from ``messages.compose``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

__all__ = [
    "ARMS", "CONTROL_ARMS", "FRAMING_ARMS", "ARM_SEMANTICS",
    "MAX_MESSAGE_LEN", "LEN_LO", "LEN_HI", "GRAMMAR_VERSION",
    "compose", "describe", "eligible", "phase_carries_message",
    "in_experiment_scope",
]

#: Bump whenever a pool or a claim precondition changes. Recorded alongside
#: ``arm_set_version`` in the propensity log so a mid-flight edit is visible in
#: the analysis rather than silently pooled.
GRAMMAR_VERSION = "framing-grammar-1"

MAX_MESSAGE_LEN = 2000          # server limit; exceeding it is an invalid move
LEN_LO, LEN_HI = 220, 300       # every messaged arm targets this band

#: A0 sends nothing; A1 sends length-matched text with no argument in it.
CONTROL_ARMS = ("A0", "A1")
FRAMING_ARMS = ("F1", "F2", "F3", "F4", "F5", "F6")
ARMS = CONTROL_ARMS + FRAMING_ARMS

ARM_SEMANTICS = {
    "A0": "silent — no message attached, though the channel is open",
    "A1": "neutral, length-matched — states the position, makes no argument",
    "F1": "reference re-basing — the same offer measured against a different "
          "true quantity",
    "F2": "delay arithmetic — what one more round actually costs",
    "F3": "commitment — a structural fact that removes belief in further "
          "concession (never a promise)",
    "F4": "reciprocal concession accounting — our movement made legible",
    "F5": "solver authority — the derived equilibrium stated as a result",
    "F6": "patience bluff — an unverifiable claim about our own position",
}

#: Arms that fill the COMMITMENT slot. Constant per arm by construction.
_COMMITMENT_ARMS = ("F3", "F5", "F6")


# --------------------------------------------------------------------------
# numeric helpers (local, so this module has no import-time coupling to the
# live agent package)
# --------------------------------------------------------------------------

def _num(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        v = float(value)
        return v if math.isfinite(v) else default
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "").replace("%", "")
        try:
            parsed = float(cleaned)
        except ValueError:
            return default
        return parsed if math.isfinite(parsed) else default
    return default


def _money(x: float, pot: float) -> str:
    """Format a money amount the way the pot is denominated."""
    if pot and float(pot).is_integer():
        return f"{x:,.0f}"
    return f"{x:,.2f}"


def _price(x: float) -> str:
    return f"{x:,.2f}"


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _rounds(n: int) -> str:
    return f"{n} round" if n == 1 else f"{n} rounds"


def _there_are(n: int) -> str:
    return f"There is {_rounds(n)}" if n == 1 else f"There are {_rounds(n)}"


def _pts(x: float) -> str:
    """Share difference expressed in points of the pot."""
    return f"{x * 100:.1f}".rstrip("0").rstrip(".") or "0"


# --------------------------------------------------------------------------
# claims
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Claim:
    """One economic assertion, with provenance.

    ``kind`` is ``"fact"`` (arithmetic or a rule of the game, computed from
    state/plan) or ``"bluff"`` (an unverifiable statement about our own
    position, legal under the rules). Nothing else is permitted, and no claim
    is ever a promise about our own future moves.
    """
    id: str
    kind: str
    text: str


@dataclass
class Facts:
    """Everything a claim builder is allowed to read, computed once."""
    family: str = ""
    phase: str = ""
    state: dict = field(default_factory=dict)
    plan: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.extra[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.extra.get(key, default)


# --------------------------------------------------------------------------
# fact extraction
# --------------------------------------------------------------------------

def _bargaining_history(state: dict, me: str) -> tuple[list, list]:
    """(our own gains we proposed, gains they proposed for us), oldest first."""
    ours: list[tuple[int, float]] = []
    theirs: list[tuple[int, float]] = []
    entries = list(state.get("history") or [])
    last = state.get("last_offer")
    if isinstance(last, dict):
        entries = entries + [{"round": last.get("round"), "offer": last,
                              "proposer": last.get("proposer")}]
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        offer = entry.get("offer")
        if not isinstance(offer, dict):
            continue
        proposer = offer.get("proposer") or entry.get("proposer")
        rnd = int(_num(entry.get("round") or offer.get("round"), 0))
        gain = offer.get(f"{me}_gain")
        if gain is None:
            continue
        key = (proposer, rnd, _num(gain))
        if key in seen:
            continue
        seen.add(key)
        (ours if proposer == me else theirs).append((rnd, _num(gain)))
    ours.sort()
    theirs.sort()
    return ours, theirs


def _negotiation_history(state: dict, me: str) -> tuple[list, list]:
    """(prices we named, prices they named), oldest first."""
    ours: list[tuple[int, float]] = []
    theirs: list[tuple[int, float]] = []
    entries = list(state.get("history") or [])
    last = state.get("last_offer")
    if isinstance(last, dict):
        entries = entries + [{"round": last.get("round"), "offer": last}]
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if not isinstance(offer, dict) or offer.get("price") is None:
                continue
            who = offer.get("from_player")
            rnd = int(_num(entry.get("round") or offer.get("round"), 0))
            sig = (who, rnd, _num(offer["price"]))
            if sig in seen:
                continue
            seen.add(sig)
            (ours if who == me else theirs).append((rnd, _num(offer["price"])))
    ours.sort()
    theirs.sort()
    return ours, theirs


def _bargaining_facts(game: dict, action: dict, plan: dict) -> Facts | None:
    state = game.get("game_state") or {}
    money = _num(state.get("money_to_divide"), 0.0)
    if money <= 0:
        return None
    me_is_alice = game.get("your_player") == "player_1"
    mine = _num(action.get("alice_gain" if me_is_alice else "bob_gain"), -1.0)
    if mine < 0:
        return None
    mine = min(max(mine, 0.0), money)
    theirs = money - mine

    me = game.get("your_player") or ("player_1" if me_is_alice else "player_2")
    opp_key = "delta_2" if me_is_alice else "delta_1"
    my_key = "delta_1" if me_is_alice else "delta_2"
    complete = state.get("complete_information")
    delta_me = _num(plan.get("delta_me"), 1.0)
    delta_opp = _num(plan.get("delta_opp"), 1.0)
    # Their discount factor counts as KNOWN only when the server disclosed it.
    # Under incomplete information the plan carries cfg.barg_unknown_delta, an
    # assumption; asserting it as fact would be a false claim about the state.
    delta_opp_known = state.get(opp_key) is not None and complete is not False
    delta_me_known = state.get(my_key) is not None

    round_no = int(_num(state.get("round"), 1))
    rounds_left = plan.get("rounds_left")
    rounds_left = None if rounds_left is None else int(_num(rounds_left, 1))
    last_round = None if rounds_left is None else round_no + rounds_left - 1
    # Proposals alternate, always. With an even number of rounds remaining the
    # final proposal of the game belongs to the opponent.
    they_propose_last = None if rounds_left is None else (rounds_left % 2 == 0)

    ours, from_them = _bargaining_history(state, me)
    # Our own earlier proposals only; the offer being composed is not history.
    ours = [(r, g) for r, g in ours if r < round_no]

    return Facts(
        family="bargaining", phase="offer", state=state, plan=plan,
        extra={
            "money": money, "mine": mine, "theirs": theirs,
            "share_me": mine / money, "share_them": theirs / money,
            "me": me, "me_is_alice": me_is_alice,
            "delta_me": delta_me, "delta_opp": delta_opp,
            "delta_me_known": delta_me_known,
            "delta_opp_known": delta_opp_known,
            "complete_information": complete,
            "round": round_no, "rounds_left": rounds_left,
            "last_round": last_round, "they_propose_last": they_propose_last,
            "horizon_known": state.get("horizon_known"),
            "spe_share": _num(plan.get("spe_share"), 0.5),
            "continuation_if_refused": _num(plan.get("continuation_if_refused"), 0.0),
            "realistic_continuation": _num(plan.get("realistic_continuation"), 0.0),
            "effective_horizon": plan.get("effective_horizon"),
            "our_offers": ours, "their_offers": from_them,
        },
    )


def _negotiation_facts(game: dict, action: dict, plan: dict) -> Facts | None:
    state = game.get("game_state") or {}
    price_raw = action.get("product_price", action.get("price"))
    if price_raw is None:
        return None                       # an acceptance carries no framing
    price = _num(price_raw, -1.0)
    if price < 0:
        return None
    me = state.get("current_player") or game.get("your_player") or "player_1"
    i_am_seller = bool(plan.get("i_am_seller"))
    ours, from_them = _negotiation_history(state, me)
    ours = ours[:-1] if ours and abs(ours[-1][1] - price) < 1e-9 else ours

    rounds_left = int(_num(plan.get("rounds_left"), 1))
    capped = bool(plan.get("capped"))
    round_no = int(_num(state.get("round"), 1))
    return Facts(
        family="negotiation",
        phase=(game.get("valid_actions") or {}).get("type") or "offer",
        state=state, plan=plan,
        extra={
            "price": price, "me": me, "i_am_seller": i_am_seller,
            "my_value": _num(plan.get("my_value"), 0.0),
            "floor": _num(plan.get("floor"), 0.0),
            "anchor": _num(plan.get("anchor"), 0.0),
            "reservation": _num(plan.get("reservation"), 0.0),
            "target": _num(plan.get("target"), price),
            "rounds_left": rounds_left, "capped": capped,
            "elapsed": _num(plan.get("elapsed"), 0.0),
            "opponent_bound": plan.get("opponent_bound"),
            "round": round_no,
            "our_offers": ours, "their_offers": from_them,
            "their_last": from_them[-1][1] if from_them else None,
        },
    )


def _persuasion_facts(game: dict, action: dict, plan: dict) -> Facts | None:
    state = game.get("game_state") or {}
    if "recommend" not in plan:
        return None                       # buyer side: no seller message to send
    history = [h for h in (state.get("history") or []) if isinstance(h, dict)]
    bought = sum(1 for h in history if h.get("bought"))
    round_no = int(_num(plan.get("round"), _num(state.get("round"), 1)))
    total = int(_num(plan.get("total_rounds"), max(round_no, 1)))
    return Facts(
        family="persuasion", phase="seller_message", state=state, plan=plan,
        extra={
            "recommend": bool(plan.get("recommend", True)),
            # None means "we were never told"; False means "we know it is low".
            "quality_is_high": plan.get("quality_is_high", None),
            "round": round_no, "total_rounds": max(total, round_no),
            "rounds_after": max(0, max(total, round_no) - round_no),
            "price": _num(state.get("product_price"), 0.0),
            "history_len": len(history), "bought": bought,
        },
    )


def _may_claim_credit(facts: Facts) -> bool:
    """Whether a persuasion arm may invoke honesty, candour or a track record.

    Never while recommending a unit the plan knows to be low quality: the buyer
    verifies quality the moment they purchase, and a broken claim of candour
    costs more than the round it bought.
    """
    return not (facts.get("quality_is_high") is False and facts.get("recommend"))


# --------------------------------------------------------------------------
# CLAIM builders — one per (arm, family). Each self-guards and returns None
# when its precondition does not hold, so the arm falls through or goes quiet.
# --------------------------------------------------------------------------

# ---- F1: reference re-basing --------------------------------------------

def _f1_barg_pv(f: Facts, rng) -> Claim | None:
    """Re-base their share onto next round's pot, which inflation has shrunk."""
    if not f["delta_opp_known"] or f["delta_opp"] >= 1.0:
        return None
    if f["rounds_left"] == 1:
        return None                       # there is no next round to re-base onto
    money, theirs, d = f["money"], f["theirs"], f["delta_opp"]
    pot_next = d * money
    if pot_next <= 0:
        return None
    rebased = theirs / pot_next
    if rebased <= f["share_them"]:
        return None
    txt = rng.choice([
        f"Measure it against the right pot. One round from now the whole "
        f"{_money(money, money)} is worth {_money(pot_next, money)} to you, and "
        f"{_money(theirs, money)} of that is {_pct(rebased)}, not {_pct(f['share_them'])}.",
        f"The {_pct(f['share_them'])} is against today's pot. Against the "
        f"{_money(pot_next, money)} the same pot is worth to you next round, "
        f"{_money(theirs, money)} is {_pct(rebased)}.",
        f"Your reference should be what is actually reachable: next round the pot "
        f"is {_money(pot_next, money)} in your money, so this offer is "
        f"{_pct(rebased)} of it.",
        f"Rebase it. {_money(theirs, money)} is {_pct(rebased)} of the "
        f"{_money(pot_next, money)} you would be splitting a round from now, not "
        f"{_pct(f['share_them'])} of something you can still have.",
    ])
    return Claim("f1_pv_next_round", "fact", txt)


def _f1_barg_last_word(f: Facts, rng) -> Claim | None:
    """Re-base from the split onto positional control of the final round."""
    if not f["they_propose_last"] or (f["rounds_left"] or 0) < 2:
        return None
    txt = rng.choice([
        f"Look at the position, not just the split: the last offer of this game, "
        f"in round {f['last_round']}, is yours to make and not mine. Weigh "
        f"{_money(f['theirs'], f['money'])} now against what that is worth "
        f"{f['rounds_left'] - 1} rounds from here.",
        f"The final proposal in this game belongs to you — round "
        f"{f['last_round']}, not mine. That is the thing to price this against, "
        f"and it is {f['rounds_left'] - 1} rounds of decay away.",
        f"You hold the last word here: round {f['last_round']} is your proposal. "
        f"Compare {_money(f['theirs'], f['money'])} today with what that position "
        f"pays after {f['rounds_left'] - 1} more rounds.",
    ])
    return Claim("f1_last_word", "fact", txt)


def _f1_barg_remaining(f: Facts, rng) -> Claim | None:
    """Re-base onto what is left rather than what there was in round one."""
    d = f["delta_me"] if f["delta_me_known"] else None
    if d is None or d >= 1.0 or f["round"] < 2:
        return None
    lost = 1.0 - d ** (f["round"] - 1)
    if lost < 0.02:
        return None
    txt = rng.choice([
        f"This is a share of what is left, not of what there was. By round "
        f"{f['round']} my side of the pot has already lost {_pct(lost)} of its "
        f"round-one value, and {_pct(f['share_them'])} of what remains is the "
        f"only thing either of us can still take.",
        f"The round-one pot is gone. On my ledger {_pct(lost)} of it has "
        f"evaporated by round {f['round']}, so the number to judge is "
        f"{_pct(f['share_them'])} of what is still on the table.",
        f"Judge it against what survives to round {f['round']}, not against the "
        f"opening pot — {_pct(lost)} of that has already gone on my side. Against "
        f"what is left, this is {_pct(f['share_them'])} to you.",
    ])
    return Claim("f1_remaining_pot", "fact", txt)


def _f1_nego_gap(f: Facts, rng) -> Claim | None:
    """Re-base from price-versus-price onto the gap that is actually left."""
    their = f["their_last"]
    if their is None or their <= 0:
        return None
    gap = abs(f["price"] - their)
    if gap <= 0:
        return None
    txt = rng.choice([
        f"The number to look at is not {_price(f['price'])} against "
        f"{_price(their)}. It is the {_price(gap)} between them, which is "
        f"{_pct(gap / their)} of your own figure. That is the whole distance left "
        f"in this.",
        f"Reframe it as the gap: {_price(gap)} separates us, "
        f"{_pct(gap / their)} of the number you named. That is the whole of what "
        f"is left to settle.",
        f"Two prices, one distance: {_price(gap)}. Set against the "
        f"{_price(their)} you put up, that is {_pct(gap / their)} — and it is all "
        f"that is still in dispute.",
    ])
    return Claim("f1_gap_rebase", "fact", txt)


def _f1_nego_zero(f: Facts, rng) -> Claim | None:
    """Re-base onto the outside option, which is zero for both of us."""
    txt = rng.choice([
        "The comparison that decides this is not my price against yours. It is "
        "either price against the zero we both book if this closes with no deal.",
        "Set my number against no deal rather than against your number. No deal "
        "is the alternative on the table, and it pays each of us nothing.",
        "The reference point here is zero, not your last figure — that is what "
        "either of us walks away with if we do not close.",
    ])
    return Claim("f1_zero_rebase", "fact", txt)


def _f1_pers(f: Facts, rng) -> Claim | None:
    if f["total_rounds"] <= 1:
        return None
    txt = rng.choice([
        f"Judge this against the run of all {f['total_rounds']} rounds rather "
        f"than this one on its own.",
        f"The unit of account here is the {f['total_rounds']} rounds together, "
        f"not round {f['round']} in isolation.",
        f"Round {f['round']} is one draw out of {f['total_rounds']}; that is the "
        f"frame to price it in.",
    ])
    return Claim("f1_horizon_rebase", "fact", txt)


# ---- F2: delay arithmetic ------------------------------------------------

def _f2_barg_pv(f: Facts, rng) -> Claim | None:
    if not f["delta_opp_known"] or f["delta_opp"] >= 1.0:
        return None
    if f["rounds_left"] == 1:
        return None                       # a rejection here pays zero, not less
    theirs, d = f["theirs"], f["delta_opp"]
    later, lost = theirs * d, theirs * (1.0 - d)
    m = f["money"]
    txt = rng.choice([
        f"Run the arithmetic on rejecting. This same {_money(theirs, m)} one round "
        f"later is worth {_money(later, m)} to you — {_money(lost, m)} gone to buy "
        f"one more exchange.",
        f"Delay is priced, not free: at your discount factor of {d:g}, "
        f"{_money(theirs, m)} next round is {_money(later, m)}. One round of "
        f"argument costs you {_money(lost, m)}.",
        f"A round costs you {_pct(1.0 - d)} of whatever you end up with. On "
        f"{_money(theirs, m)} that is {_money(lost, m)} spent before we even "
        f"discuss a better split.",
        f"If you reject and we land on exactly this again next round, you take "
        f"{_money(later, m)} instead of {_money(theirs, m)}. The difference, "
        f"{_money(lost, m)}, is the price of the round.",
    ])
    return Claim("f2_pv_delay", "fact", txt)


def _f2_barg_own_decay(f: Facts, rng) -> Claim | None:
    """Their discount factor is undisclosed; state ours, which we do know."""
    if not f["delta_me_known"] or f["delta_me"] >= 1.0:
        return None
    if f["rounds_left"] == 1:
        return None
    d, m = f["delta_me"], f["money"]
    mine_later = f["mine"] * d
    txt = rng.choice([
        f"Delay is not free in this game. My own factor is {d:g}: the "
        f"{_money(f['mine'], m)} I am asking is {_money(mine_later, m)} to me one "
        f"round later, and a pot that shrinks for one of us is a smaller pot to "
        f"argue over.",
        f"Each round costs me {_pct(1.0 - d)} of my side. That is real money "
        f"leaving the table every time we exchange offers, whatever your own "
        f"factor turns out to be.",
        f"On my side a round of delay is worth {_pct(1.0 - d)} — "
        f"{_money(f['mine'] * (1.0 - d), m)} at this split. Whatever we settle "
        f"on, settling later is settling on less.",
    ])
    return Claim("f2_own_decay", "fact", txt)


def _f2_barg_budget(f: Facts, rng) -> Claim | None:
    rl = f["rounds_left"]
    if rl is None or rl < 1:
        return None
    txt = rng.choice([
        f"{_there_are(rl)} left including this one, and round "
        f"{f['last_round']} is the end of it — after that we both take nothing. "
        f"Every exchange spends one of them.",
        f"Count the rounds: {_rounds(rl)} left, and the game pays us both zero "
        f"if round {f['last_round']} closes without an agreement.",
        f"The budget is {_rounds(rl)}, not unlimited. Each rejection spends one, "
        f"and there is nothing after round {f['last_round']}.",
    ])
    return Claim("f2_round_budget", "fact", txt)


def _f2_nego_budget(f: Facts, rng) -> Claim | None:
    if not f["capped"] or f["rounds_left"] < 1:
        return None
    rl = f["rounds_left"]
    gap = None
    if f["their_last"] is not None:
        gap = abs(f["price"] - f["their_last"])
    if gap:
        txt = rng.choice([
            f"{_rounds(rl).capitalize()} left, and {_price(gap)} between us. "
            f"Each exchange spends one of them and closes none of the gap by "
            f"itself; if they run out we both book zero.",
            f"{_there_are(rl)} left to cover {_price(gap)}. Running out costs "
            f"each of us the whole deal, not the difference.",
        ])
    else:
        txt = rng.choice([
            f"{_rounds(rl).capitalize()} left, and a negotiation that runs out "
            f"of them pays us both nothing at all.",
            f"The round budget is {_rounds(rl)}. Spending it without a deal is "
            f"the one outcome here that is worse for us both than any price.",
        ])
    return Claim("f2_nego_budget", "fact", txt)


def _f2_nego_nodeal(f: Facts, rng) -> Claim | None:
    txt = rng.choice([
        "This does not run forever, and an exchange that ends without a deal "
        "pays each of us nothing. Rounds spent are the one cost here neither of "
        "us recovers.",
        "Every round we spend disagreeing is a round closer to the outcome that "
        "pays us both zero. That cost is real even though it is not in the price.",
    ])
    return Claim("f2_nego_nodeal", "fact", txt)


def _f2_pers(f: Facts, rng) -> Claim | None:
    if f["rounds_after"] < 1:
        return None
    txt = rng.choice([
        f"{_there_are(f['rounds_after'])} after this one, and a round you sit "
        f"out is a round neither of us gets back.",
        f"{_rounds(f['rounds_after']).capitalize()} follow this one. A skipped "
        f"round is not stored anywhere; it is simply gone.",
    ])
    return Claim("f2_pers_budget", "fact", txt)


# ---- F3: commitment, expressed only as facts -----------------------------

def _f3_barg_terminal(f: Facts, rng) -> Claim | None:
    if f["rounds_left"] != 1:
        return None
    txt = rng.choice([
        "There is no round after this one. A rejection here is not a counteroffer, "
        "it is the end of the game at nothing for both of us.",
        "This is the final round of the game. Nothing follows it: if this does "
        "not close, we both score zero.",
        f"Round {f['round']} is the last one. There is no next offer from "
        f"either side — only this, or nothing.",
    ])
    return Claim("f3_terminal_round", "fact", txt)


def _f3_barg_last_offer(f: Facts, rng) -> Claim | None:
    """We do not propose again: the alternation gives them the final word."""
    if f["rounds_left"] != 2:
        return None
    txt = rng.choice([
        "This is the last number I get to name. The alternation gives you round "
        f"{f['last_round']}, and after your proposal the game is over — I have no "
        "further offer to make.",
        f"I do not propose again in this game. Round {f['last_round']} is yours "
        "and it is the last one, so this is my final number by the structure of "
        "the game, not by choice.",
        "There is no further offer from my side. You have the next and last "
        f"proposal, in round {f['last_round']}, and then this ends.",
    ])
    return Claim("f3_last_offer", "fact", txt)


def _f3_barg_reservation(f: Facts, rng) -> Claim | None:
    """Below this number refusing pays us more than agreeing. A fact, not a vow."""
    # For a PROPOSER the relevant floor is what a refusal of this offer is
    # worth to us, not the responder-side continuation value. And the claim is
    # only apt when our ask is actually sitting on that floor: asserting a floor
    # ABOVE our own ask contradicts the offer in the same message.
    floor = f["continuation_if_refused"]
    if floor <= 0 or not (floor * 0.90 <= f["mine"] <= floor * 1.05):
        return None
    m = f["money"]
    txt = rng.choice([
        f"I am at the point where the arithmetic decides it for me: below about "
        f"{_money(floor, m)} refusing is worth more to me than agreeing, so there "
        f"is nothing under this that I can rationally take.",
        f"This is not posture, it is the crossover. My continuation value here is "
        f"{_money(floor, m)}; a number below it makes rejection the better move "
        f"for me by construction.",
        f"Below {_money(floor, m)} I do better by refusing than by signing, so "
        f"that is the floor the arithmetic puts under this offer rather than one "
        f"I chose.",
    ])
    return Claim("f3_reservation", "fact", txt)


def _f3_nego_terminal(f: Facts, rng) -> Claim | None:
    if not f["capped"] or f["rounds_left"] > 2:
        return None
    if f["rounds_left"] <= 1:
        txt = rng.choice([
            "This is the final round. A rejection ends the negotiation at zero "
            "for both of us; there is no counteroffer after it.",
            "Nothing follows this round. Either this closes or we both book "
            "nothing — those are the only two outcomes left.",
        ])
        return Claim("f3_nego_terminal", "fact", txt)
    txt = rng.choice([
        "There is one exchange left after this. I do not get another number "
        "after that, so this is effectively where my side of it stops.",
        "The round budget leaves room for one more move, not for a negotiation. "
        "This is the last price I have room to name.",
    ])
    return Claim("f3_nego_last_offer", "fact", txt)


def _f3_nego_reservation(f: Facts, rng) -> Claim | None:
    if f["my_value"] <= 0:
        return None
    reservation = f["reservation"]
    if reservation <= 0:
        return None
    close = abs(f["price"] - reservation) <= 0.02 * max(abs(reservation), 1.0)
    if not close and f["elapsed"] < 0.95:
        return None
    side = "below" if f["i_am_seller"] else "above"
    txt = rng.choice([
        f"This sits on my reservation price. {side.capitalize()} it a trade is "
        f"worth less to me than no trade at all, which is a fact about my costs "
        f"rather than a bargaining position.",
        f"I am at my limit here — {side} this number the deal stops being better "
        f"than walking, so there is no version of me that signs it.",
        f"That is the end of my range. {side.capitalize()} it I am strictly worse "
        f"off than with no deal, so it is not a number I can move past.",
    ])
    return Claim("f3_nego_reservation", "fact", txt)


def _f3_pers(f: Facts, rng) -> Claim | None:
    if f["rounds_after"] > 0:
        return None
    txt = rng.choice([
        "This is the last round; there is no next one after it.",
        "No rounds follow this one, so the choice does not come round again.",
    ])
    return Claim("f3_pers_terminal", "fact", txt)


# ---- F4: reciprocal concession accounting --------------------------------

def _f4_barg(f: Facts, rng) -> Claim | None:
    ours = f["our_offers"]
    if not ours:
        return None
    money = f["money"]
    first_round, first_mine = ours[0]
    my_move = (first_mine - f["mine"]) / money
    if my_move <= 0.005:
        return None                       # we have not moved; do not claim we did
    theirs = f["their_offers"]
    if len(theirs) >= 2:
        their_move = (theirs[-1][1] - theirs[0][1]) / money
        if their_move > 0.005:
            tail = (f"Across the same stretch your offers have moved "
                    f"{_pts(their_move)} points toward me.")
        else:
            tail = ("Across the same stretch your own number has not moved "
                    "toward me at all.")
    elif theirs:
        tail = "You have put up one number and have not moved off it."
    else:
        tail = "I have not seen a number from your side yet."
    txt = rng.choice([
        f"Keep the ledger honest. In round {first_round} I asked "
        f"{_pct(first_mine / money)}; this offer is {_pct(f['share_me'])}. That is "
        f"{_pts(my_move)} points I have moved toward you. {tail}",
        f"Concessions so far: mine {_pts(my_move)} points, from "
        f"{_pct(first_mine / money)} in round {first_round} down to "
        f"{_pct(f['share_me'])} here. {tail}",
        f"I opened at {_pct(first_mine / money)} and I am at "
        f"{_pct(f['share_me'])} now — {_pts(my_move)} points of movement from my "
        f"side. {tail}",
    ])
    return Claim("f4_concession_ledger", "fact", txt)


def _f4_nego(f: Facts, rng) -> Claim | None:
    ours = f["our_offers"]
    if not ours:
        return None
    first_round, first_price = ours[0]
    my_move = (first_price - f["price"]) if f["i_am_seller"] else (f["price"] - first_price)
    if my_move <= 0 or first_price <= 0:
        return None
    theirs = f["their_offers"]
    if len(theirs) >= 2:
        their_move = ((theirs[-1][1] - theirs[0][1]) if f["i_am_seller"]
                      else (theirs[0][1] - theirs[-1][1]))
        tail = (f"You have come {_price(their_move)} over the same rounds."
                if their_move > 0 else
                "Your own number has not moved toward me over the same rounds.")
    elif theirs:
        tail = "You have named one price and stayed on it."
    else:
        tail = "I have not seen a number from you yet."
    txt = rng.choice([
        f"The ledger: I opened at {_price(first_price)} in round {first_round} "
        f"and I am at {_price(f['price'])} now — {_price(my_move)} of movement "
        f"from my side. {tail}",
        f"I have moved {_price(my_move)}, from {_price(first_price)} to "
        f"{_price(f['price'])}. {tail}",
        f"Counting concessions rather than arguing about fairness: mine is "
        f"{_price(my_move)} since round {first_round}. {tail}",
    ])
    return Claim("f4_nego_ledger", "fact", txt)


def _f4_pers(f: Facts, rng) -> Claim | None:
    if f["history_len"] < 1:
        return None
    txt = rng.choice([
        f"You have bought on {f['bought']} of the {f['history_len']} rounds so "
        f"far; I have put a call on every one of them.",
        f"{f['bought']} purchases out of {f['history_len']} rounds so far, and a "
        f"call from me on each.",
    ])
    return Claim("f4_pers_ledger", "fact", txt)


# ---- F5: solver authority ------------------------------------------------

def _f5_barg(f: Facts, rng) -> Claim | None:
    spe = f["spe_share"]
    if not (0.0 < spe <= 1.0):
        return None
    if f["share_me"] > spe + 0.005:
        return None                       # never state a result that undercuts us
    horizon = (f"with {_rounds(f['rounds_left'])} left" if f["rounds_left"] is not None
               else "on an open horizon")
    # The plan substitutes an assumed discount factor when theirs is hidden.
    # Saying so keeps the claim true; asserting it flat would not be.
    hedge = ("" if f["delta_opp_known"] else
             " That assumes a middling discount on your side, since yours is not "
             "disclosed.")
    rel = "under it" if f["share_me"] < spe - 0.005 else "exactly it"
    txt = rng.choice([
        f"I ran the backward induction rather than guessed: {horizon}, the "
        f"proposer's equilibrium share here is {_pct(spe)}. I am asking "
        f"{_pct(f['share_me'])}, which is {rel}.{hedge}",
        f"A derived number, not an opening demand. The alternating-offers "
        f"solution {horizon} puts the proposer at {_pct(spe)}; my ask is "
        f"{_pct(f['share_me'])}, {rel}.{hedge}",
        f"Solved rather than argued: equilibrium for the proposer in this "
        f"position is {_pct(spe)}, and I am on {_pct(f['share_me'])} — "
        f"{rel}.{hedge}",
    ])
    return Claim("f5_induction", "fact", txt)


def _f5_nego(f: Facts, rng) -> Claim | None:
    if f["my_value"] <= 0:
        return None
    txt = rng.choice([
        "This number is generated, not chosen. It comes off my own valuation and "
        "the rounds remaining on a schedule I fixed before we started, which is "
        "why it moves the way it does and not further.",
        "I price this off my valuation and the round count, on a schedule set at "
        "the opening. The number is an output of that, not a position I picked to "
        "leave room in.",
        "There is a rule behind this figure: my own cost, the rounds left, and a "
        "fixed concession path between them. What you are seeing is where that "
        "path is today.",
    ])
    return Claim("f5_schedule", "fact", txt)


def _f5_pers(f: Facts, rng) -> Claim | None:
    if not _may_claim_credit(f) or f["history_len"] < 1:
        return None
    txt = rng.choice([
        "You can check this call against the ones I have made so far this game.",
        "My record this game is in front of you; weigh this call against it.",
    ])
    return Claim("f5_pers_record", "fact", txt)


# ---- F6: patience bluff (unverifiable, about our own position only) ------

def _f6_barg(f: Facts, rng) -> Claim | None:
    # Only where the opponent structurally cannot check our discount factor.
    if f["complete_information"] is not False:
        return None
    # And only where our own schedule will not contradict it next round.
    rl = f["rounds_left"]
    if rl is not None and rl < 4:
        return None
    horizon = f["effective_horizon"]
    if rl is None and horizon and f["round"] > 0.5 * _num(horizon, 1e9):
        return None
    txt = rng.choice([
        "You cannot see my discount factor in this game, so take this for what it "
        "is worth: waiting is cheap on my side. I am content to keep proposing "
        "until the numbers come to me.",
        "My side of this is not on a clock. I would rather close now, but a long "
        "game costs me less than it is likely to cost you, and I am set up to "
        "play one.",
        "Time is the one thing I am not short of here. I will keep making offers "
        "for as long as this runs; the question is what the pot is worth by then.",
        "Patience is cheap for me in this game, and nothing on my side is "
        "pushing me to move first.",
    ])
    return Claim("f6_patience", "bluff", txt)


def _f6_nego(f: Facts, rng) -> Claim | None:
    # Valuations are private in negotiation, so this is unverifiable by design.
    if f["elapsed"] >= 0.6 or f["rounds_left"] < 3:
        return None
    txt = rng.choice([
        "My valuation is mine and you cannot see it. What I will tell you is that "
        "no deal is a good deal less painful for me than it probably is for you, "
        "and I am comfortable letting this run.",
        "You are guessing at my costs, so here is my side of it: I am not under "
        "pressure to close this round, or the one after.",
        "I have a comfortable margin behind this number and no particular need to "
        "trade today. That is worth knowing before you decide how hard to push.",
        "The number I am holding is not close to my limit, and I am in no hurry "
        "to find out where yours is.",
    ])
    return Claim("f6_patience", "bluff", txt)


# --------------------------------------------------------------------------
# claim tables — ordered; the first builder that fires wins, so claim choice
# is a deterministic function of the state and only the wording is random.
# --------------------------------------------------------------------------

_ClaimBuilder = Callable[[Facts, Any], "Claim | None"]

_CLAIMS: dict[str, dict[str, tuple[_ClaimBuilder, ...]]] = {
    "A0": {},
    "A1": {},
    "F1": {
        "bargaining": (_f1_barg_pv, _f1_barg_last_word, _f1_barg_remaining),
        "negotiation": (_f1_nego_gap, _f1_nego_zero),
        "persuasion": (_f1_pers,),
    },
    "F2": {
        "bargaining": (_f2_barg_pv, _f2_barg_own_decay, _f2_barg_budget),
        "negotiation": (_f2_nego_budget, _f2_nego_nodeal),
        "persuasion": (_f2_pers,),
    },
    "F3": {
        "bargaining": (_f3_barg_terminal, _f3_barg_last_offer, _f3_barg_reservation),
        "negotiation": (_f3_nego_terminal, _f3_nego_reservation),
        "persuasion": (_f3_pers,),
    },
    "F4": {
        "bargaining": (_f4_barg,),
        "negotiation": (_f4_nego,),
        "persuasion": (_f4_pers,),
    },
    "F5": {
        "bargaining": (_f5_barg,),
        "negotiation": (_f5_nego,),
        "persuasion": (_f5_pers,),
    },
    "F6": {
        "bargaining": (_f6_barg,),
        "negotiation": (_f6_nego,),
        "persuasion": (),                 # no safe unverifiable own-position claim
    },
}


# --------------------------------------------------------------------------
# COMMITMENT slot — filled only by F3, F5, F6, and only where already earned
# by the claim that fired. Never a promise about our own future moves.
# --------------------------------------------------------------------------

def _commitments(arm: str, facts: Facts, claim: Claim | None) -> list[str]:
    """The COMMITMENT slot. Filled only by F3, F5 and F6, and never a promise.

    F3's lines are entailed by the fact its claim just stated, so nothing we do
    next round can falsify them. F5's assert provenance. F6's flag its own
    unverifiability rather than dressing a bluff as a fact.
    """
    if arm not in _COMMITMENT_ARMS or claim is None:
        return []
    if arm == "F3":
        if claim.id in ("f3_terminal_round", "f3_nego_terminal"):
            return ["So this is the whole of it.",
                    "That is the entire decision in front of you."]
        if claim.id in ("f3_last_offer", "f3_nego_last_offer"):
            return ["So treat this as final, because the structure makes it final.",
                    "Final by arithmetic rather than by stubbornness."]
        if claim.id == "f3_pers_terminal":
            return ["So there is nothing to gain by waiting this one out.",
                    "That is simply where the game ends."]
        return ["That is the boundary, and it is not one I set.",
                "The number is where it is for that reason alone."]
    if arm == "F5":
        return ["That is the provenance of the figure.",
                "Derived first, offered second.",
                "The derivation is the argument."]
    if arm == "F6":
        return ["Discount it if you like; I cannot prove it to you.",
                "Take that for what an unverifiable claim is worth.",
                "You have only my word on that."]
    return []


# --------------------------------------------------------------------------
# FRAME, REQUEST and FILLER — shared pools, so the only systematic difference
# between A1-neutral and any treatment arm is the CLAIM slot.
# --------------------------------------------------------------------------

def _frames(facts: Facts) -> list[str]:
    if facts.family == "bargaining":
        m = facts["money"]
        return [
            f"You take {_money(facts['theirs'], m)} of {_money(m, m)}.",
            f"My proposal leaves you {_money(facts['theirs'], m)}.",
            f"{_money(facts['theirs'], m)} to you, {_money(facts['mine'], m)} to me.",
            f"Round {facts['round']}: {_money(facts['mine'], m)} to me, "
            f"{_money(facts['theirs'], m)} to you.",
            f"The split on the table is {_pct(facts['share_them'])} to you.",
        ]
    if facts.family == "negotiation":
        return [
            f"{_price(facts['price'])}.",
            f"My number is {_price(facts['price'])}.",
            f"I can do {_price(facts['price'])}.",
            f"Round {facts['round']}: {_price(facts['price'])}.",
            f"The price I am naming is {_price(facts['price'])}.",
        ]
    # persuasion: the frame IS the recommendation carrier, and must survive
    # glee_agent.text.reads_as_recommendation unchanged.
    if facts["recommend"]:
        return ["I recommend this one.",
                "I recommend this unit.",
                "I recommend buying this round."]
    return ["I would hold off on this one.",
            "I would pass on this one.",
            "Skip this one."]


def _requests(arm: str, facts: Facts) -> list[str]:
    if arm == "A1":
        return ["It is your call.", "Over to you.", "Your move.",
                "Respond as you see fit.", "The decision is yours."]
    if facts.family == "persuasion":
        return ["That is my call for this round.",
                "Decide on that basis.",
                "That is how I would play it."]
    return ["Accept and we are done.",
            "Take it and this closes here.",
            "Say yes and neither of us spends another round on it.",
            "Accept, and we both book this now.",
            "Close it here."]


def _fillers(facts: Facts) -> list[str]:
    """Argument-free, true, on-topic padding. Shared across every messaged arm."""
    if facts.family == "bargaining":
        m = facts["money"]
        out = [
            f"This is round {facts['round']}.",
            f"The pot is {_money(m, m)}.",
            f"Stated in full: {_money(facts['mine'], m)} to me, "
            f"{_money(facts['theirs'], m)} to you.",
            "No conditions are attached to the split.",
            "That is the offer as submitted.",
            f"I am {'Alice' if facts['me_is_alice'] else 'Bob'} in this one.",
            "The numbers above are the whole of the proposal.",
            "The proposal is exactly as written.",
            "Nothing else is bundled into this one.",
            "That is the entirety of what I am putting forward.",
        ]
        return out
    if facts.family == "negotiation":
        return [
            f"This is round {facts['round']}.",
            f"The price named is {_price(facts['price'])}.",
            f"I am the {'seller' if facts['i_am_seller'] else 'buyer'} here.",
            "No conditions are attached to the price.",
            "That is the number as submitted.",
            "One price, one product, nothing else in the package.",
            "The offer stands exactly as written.",
            "Nothing else is bundled with it.",
            "That is the whole of my proposal for this round.",
        ]
    return [
        f"Round {facts['round']} of {facts['total_rounds']}.",
        f"The price this round is {_price(facts['price'])}.",
        "That is the position as I see it.",
        "No other terms are attached to the unit.",
        "One unit, one price, one call from me.",
        f"We are {facts['round']} rounds into this game.",
    ]


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def _pick(rng, options: list[str], budget: int) -> str:
    """A random option that fits the budget; the shortest one if none does.

    Choosing to fit, rather than choosing then trimming, is what lets the CLAIM
    be inviolable. A trimmer that shortens a claim can amputate a truth-
    preserving qualifier — the "their discount factor was not disclosed" hedge
    in F5 is exactly such a clause — and turn a true statement into a false one.
    """
    pool = [o for o in options if o]
    if not pool:
        return ""
    order = list(pool)
    rng.shuffle(order)
    for option in order:
        if len(option) <= budget:
            return option
    return min(pool, key=len)


def _assemble(frames: list[str], claim: str, commitments: list[str],
              requests: list[str], fillers: list[str], rng) -> str:
    """Fill the slots around the claim, then pad toward LEN_LO.

    Priority is fixed and arm-independent. The CLAIM is the treatment and is
    never shortened or dropped. The REQUEST is a slot every arm fills, so it is
    chosen next — dropping it for some arms would make slot presence itself
    correlate with the arm. The FRAME comes third, the COMMITMENT is fitted only
    if there is room left, and filler is added last and only to reach LEN_LO.
    """
    def join(parts):
        return " ".join(p.strip() for p in parts if p and p.strip())

    claim = claim.strip()
    # Reserve room for the shortest available frame before choosing a request,
    # so a long request can never crowd the frame out of the message.
    min_frame = min((len(f) for f in frames if f), default=0)
    request = _pick(rng, requests, max(0, LEN_HI - len(claim) - min_frame - 2))
    frame = _pick(rng, frames, max(0, LEN_HI - len(claim) - len(request) - 2))
    parts = [frame, claim, request]
    if len(join(parts)) > LEN_HI:         # claim alone leaves no room for a frame
        parts = [claim, request]
    text = join(parts)

    commitment = _pick(rng, commitments, max(0, LEN_HI - len(text) - 1))
    if commitment and len(text) + len(commitment) + 1 <= LEN_HI:
        parts = parts[:-1] + [commitment, parts[-1]]
        text = join(parts)

    pool = [f for f in fillers if f]
    rng.shuffle(pool)
    for filler in pool:
        if len(text) >= LEN_LO:
            break
        candidate = f"{text} {filler}"
        if len(candidate) <= LEN_HI:
            text = candidate
    return text[:MAX_MESSAGE_LEN].strip()


_FACT_BUILDERS = {
    "bargaining": _bargaining_facts,
    "negotiation": _negotiation_facts,
    "persuasion": _persuasion_facts,
}


# --------------------------------------------------------------------------
# eligibility
# --------------------------------------------------------------------------

def phase_carries_message(game: dict) -> bool:
    """Whether the server will accept free text on this turn.

    Mirrors ``glee_agent.dispatch._wants_message`` plus the ``messages_allowed``
    check that ``actions._clean_message`` enforces. In bargaining only the
    proposer may attach text, so a decision turn carries none.
    """
    try:
        state = game.get("game_state") or {}
        action_type = (game.get("valid_actions") or {}).get("type")
        if action_type == "seller_message":
            return True                    # the message IS the move
        if state.get("messages_allowed") is False:
            return False
        if action_type == "offer":
            return True
        if action_type == "decision":
            return game.get("game_family") == "negotiation"
        return False
    except Exception:
        return False


def in_experiment_scope(game: dict) -> bool:
    """Whether this turn may be randomised into an arm at all.

    Bargaining and negotiation offers only. Persuasion is excluded because in
    text mode the message is the move, so the silent arm would be an invalid
    action rather than a treatment.
    """
    try:
        if not phase_carries_message(game):
            return False
        if game.get("game_family") not in ("bargaining", "negotiation"):
            return False
        return (game.get("valid_actions") or {}).get("type") == "offer"
    except Exception:
        return False


def eligible(arm: str, game: dict, action: dict, plan: dict | None) -> bool:
    """Whether ``arm`` has a true claim available on this turn.

    The assigner must consult this BEFORE drawing, so that a stratum's permuted
    block never spends a slot on an arm that would go quiet. A0 is eligible
    wherever the phase carries text at all — its treatment is the silence.
    """
    try:
        if arm not in ARMS:
            return False
        if not phase_carries_message(game):
            return False
        if arm == "A0":
            return True
        return describe(arm, game, action, plan)["text"] is not None
    except Exception:
        return False


# --------------------------------------------------------------------------
# public entry points
# --------------------------------------------------------------------------

def describe(arm: str, game: dict, action: dict, plan: dict | None,
             rng=None) -> dict:
    """Compose, and return the message together with its provenance.

    The returned dict is what the propensity log records: which claim fired,
    whether it was a fact or a bluff, and the realised length (per-arm length
    distribution is a mandatory balance table in the analysis).
    """
    out = {
        "arm": arm,
        "grammar_version": GRAMMAR_VERSION,
        "family": game.get("game_family") if isinstance(game, dict) else None,
        "phase": None,
        "text": None,
        "length": 0,
        "claim_id": None,
        "claim_kind": None,
        "claim_text": None,
        "commitment": False,
        "reason": None,
    }
    try:
        if arm not in ARMS:
            out["reason"] = "unknown-arm"
            return out
        if not isinstance(game, dict) or not isinstance(action, dict):
            out["reason"] = "malformed-turn"
            return out
        out["phase"] = (game.get("valid_actions") or {}).get("type")
        if not phase_carries_message(game):
            out["reason"] = "phase-carries-no-message"
            return out
        if arm == "A0":
            out["reason"] = "silent-arm"
            return out
        if not plan:
            out["reason"] = "no-plan"
            return out

        family = game.get("game_family")
        build_facts = _FACT_BUILDERS.get(family)
        if build_facts is None:
            out["reason"] = "unknown-family"
            return out
        facts = build_facts(game, action, plan)
        if facts is None:
            out["reason"] = "facts-unavailable"
            return out

        if rng is None:
            rng = _default_rng(game)

        claim: Claim | None = None
        if arm != "A1":
            for builder in _CLAIMS.get(arm, {}).get(family, ()):
                try:
                    claim = builder(facts, rng)
                except Exception:
                    claim = None
                if claim is not None:
                    break
            if claim is None:
                # No true claim of this arm's family is available on this state.
                # Going quiet is correct: the alternative is either inventing
                # one or emitting a different arm's semantics under this label.
                out["reason"] = "no-true-claim-available"
                return out

        commitments = _commitments(arm, facts, claim)
        text = _assemble(_frames(facts), claim.text if claim else "",
                         commitments, _requests(arm, facts),
                         _fillers(facts), rng)
        if not text:
            out["reason"] = "empty"
            return out

        out.update(text=text, length=len(text),
                   claim_id=claim.id if claim else None,
                   claim_kind=claim.kind if claim else None,
                   claim_text=claim.text if claim else None,
                   commitment=any(c in text for c in commitments),
                   reason="ok")
        return out
    except Exception:                      # never risk the move over a message
        out["reason"] = "exception"
        out["text"] = None
        return out


def compose(arm: str, game: dict, action: dict, plan: dict | None,
            rng=None) -> str | None:
    """Message for ``arm``, or ``None`` when this arm sends nothing.

    Signature mirrors ``glee_agent.messages.compose`` with the arm prepended, so
    integration is a one-line change in ``dispatch._play`` (see module docstring).
    ``None`` is a legitimate outcome — it is the A0 arm, and an ineligible arm —
    and must not be back-filled from the default template composer, which would
    destroy the silent control.

    Never raises.
    """
    try:
        return describe(arm, game, action, plan, rng)["text"]
    except Exception:
        return None


def _default_rng(game: dict):
    """Per-turn phrasing variation, reproducible for a replay.

    Deliberately *not* the strategy's own generator: sharing that stream would
    couple wording to the numeric draw. It is also not the arm-assignment
    stream, for the same reason in reverse.
    """
    import random
    state = game.get("game_state") or {}
    return random.Random(f"framing:{game.get('game_id')}:{state.get('round')}")
