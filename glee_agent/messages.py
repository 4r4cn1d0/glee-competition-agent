"""Grounded message templates — the language channel without an LLM.

The channel is open in about a third of bargaining and negotiation turns and in
half of all persuasion turns, where in text mode the message IS the entire move.
Live data shows opponents using it well: they cite discount asymmetry, claim
reservation prices, and spend a round declining to recommend in order to buy
credibility for later ones.

Older reachable builders sent fixed templates. Bargaining's prior bank was not
reachable in the measured fleet, so no wording in it has evidence of rating
impact; the randomised arms below test the channel instead of assuming an
effect. Negotiation and persuasion may still use a configured wording provider.
The bargaining experiment is hand-written only: its silent and sentence-bank
arms never call, fall back to, or expose a hook for an LLM.

Nothing here changes a single number. The move is already decided; this only
chooses how to say it.
"""

from __future__ import annotations

from . import runtime_flags

import hashlib
import json
import random

from .actions import _num, coerce


def _pick(rng: random.Random, options: list[str]) -> str:
    """Vary the phrasing so a repeat opponent cannot key on a fixed string."""
    return rng.choice(options)


# --------------------------------------------------------------------------
# BARGAINING MESSAGE ARMS — the randomised bank behind GLEE_BARG_MSG.
#
# Reachability is measured, effect is not: Test 1 sent text on 0/1,851 offer
# turns in 493 message-enabled games while opponents sent it on 1,583/1,830.
# B0 therefore preserves fleet silence and B1-B3 measure the language channel;
# none is a default policy claim about rating impact.
#
# Every non-silent arm is assembled from the same FRAME, REQUEST and FILLER
# pools into the same length band. The composer reads the submitted split and
# public offer history only. It does not read discount factors, reservation or
# floor values, continuation estimates, planned concessions, or ``plan`` at all.
# --------------------------------------------------------------------------

BARG_MSG_FLAG = "GLEE_BARG_MSG"
BARG_ARM_GRAMMAR_VERSION = "barg-msg-grammar-1"
BARG_ARM_LEN_LO, BARG_ARM_LEN_HI = 292, 308
BARG_ARM_TARGET_LEN = 300
BARG_ARM_SALT = "barg_msg|"

BARG_ARM_SEMANTICS = {
    "B0": "silent control — no message is attached although the channel is "
          "open. This reproduces the fleet behaviour that the channel test is "
          "measured against.",
    "B1": "neutral split recap — states only the submitted allocations and "
          "returns the decision to the opponent. It is the length-matched text "
          "reference with no bargaining argument.",
    "B2": "no-agreement frame — pairs the submitted allocations with the public "
          "rule that an eventual no-agreement outcome pays both sides zero.",
    "B3": "public-movement frame — states a concession only when transmitted "
          "offer history proves it, otherwise it uses public allocation "
          "arithmetic. It makes no claim about a future move.",
}

BARG_ARMS = ("B0", "B1", "B2", "B3")


def bargaining_arm(game_id) -> str | None:
    """Stable per-game arm, matching ``_zopa_share``'s hash assignment shape."""
    gid = str(game_id or "")
    if not gid:
        return None
    digest = hashlib.sha256((BARG_ARM_SALT + gid).encode()).hexdigest()
    return BARG_ARMS[int(digest, 16) % len(BARG_ARMS)]


def _barg_fmt(value: float) -> str:
    return f"{value:,.2f}"


def _barg_public_facts(game: dict, action: dict) -> dict | None:
    """Public split/history facts used by every bargaining message arm."""
    if not isinstance(action, dict):
        return None
    state = game.get("game_state") or {}
    money = _num(state.get("money_to_divide"), 0.0)
    if money <= 0.0:
        return None
    me = game.get("your_player") or state.get("current_player") or "player_1"
    other = "player_2" if me == "player_1" else "player_1"
    mine_key = "alice_gain" if me == "player_1" else "bob_gain"
    theirs_key = "bob_gain" if me == "player_1" else "alice_gain"
    if action.get(mine_key) is None or action.get(theirs_key) is None:
        return None
    mine = _num(action[mine_key], -1.0)
    theirs = _num(action[theirs_key], -1.0)
    if mine < 0.0 or theirs < 0.0:
        return None

    previous_to_them = None
    for entry in state.get("history") or []:
        if not isinstance(entry, dict):
            continue
        offer = entry.get("offer") or {}
        if not isinstance(offer, dict):
            continue
        proposer = offer.get("proposer") or entry.get("proposer")
        if proposer != me:
            continue
        prior = offer.get(f"{other}_gain")
        if prior is not None:
            prior_gain = _num(prior, -1.0)
            if 0.0 <= prior_gain <= money:
                previous_to_them = prior_gain

    public_step = None
    # The retained "serious move" language follows a publicly visible move of
    # at least five percent of the pot; a one-cent change does not qualify.
    if (previous_to_them is not None
            and theirs - previous_to_them >= 0.05 * money):
        public_step = theirs - previous_to_them
    return {
        "money": money,
        "mine": mine,
        "theirs": theirs,
        "round": int(_num(state.get("round"), 1)),
        "public_step": public_step,
    }


def _barg_arm_frames(facts: dict) -> list[str]:
    mine, theirs, money = facts["mine"], facts["theirs"], facts["money"]
    return [
        f"You take {_barg_fmt(theirs)} of the {_barg_fmt(money)} nominal pot.",
        f"My submitted split assigns {_barg_fmt(theirs)} to you and "
        f"{_barg_fmt(mine)} to me.",
        f"The proposal is {_barg_fmt(theirs)} to you and {_barg_fmt(mine)} to me.",
    ]


def _barg_arm_claim(arm: str, facts: dict,
                    rng: random.Random) -> tuple[str, str | None]:
    if arm == "B1":
        return "", None
    if arm == "B2":
        return ("If this bargaining ends without an accepted agreement, both "
                "sides receive zero; the submitted split is the agreement "
                "available on this turn.", "b2_no_agreement")
    if arm == "B3":
        step = facts.get("public_step")
        if step is not None:
            # These closers used to fire only below a 45% own-share gate. They
            # now follow a concession proved by public offer history, so either
            # closer can be emitted above or below that former share threshold.
            closer = _pick(rng, [
                "That is a serious move toward you. I would like to close here.",
                "I have come a long way to you on this. Let us finish it.",
            ])
            return (f"Relative to my previous submitted split, this assigns "
                    f"{_barg_fmt(step)} more of the nominal pot to you. {closer}",
                    "b3_public_move")
        return ("The two submitted allocations add to the full nominal pot, and "
                "no side condition changes either number.", "b3_public_allocation")
    return "", None


def _barg_arm_requests() -> list[str]:
    return [
        "Please decide on the split as submitted.",
        "The decision on this submitted split is yours.",
        "Please evaluate the two submitted amounts and decide.",
        "You can accept or reject the allocation as written.",
    ]


def _barg_arm_fillers(facts: dict) -> list[str]:
    return [
        f"This is the complete allocation submitted for round {facts['round']}.",
        f"The two submitted amounts sum to {_barg_fmt(facts['money'])}.",
        "No side payment or additional condition is attached.",
        "Only the two allocations shown are part of this proposal.",
        "The offer stands with exactly the amounts written above.",
        "Nothing else is bundled into the division of the pot.",
        "The amounts are explicit.",
        "Those are the full terms.",
        "The split is fully stated.",
        "The proposal has no add-ons.",
        "Both amounts are shown.",
        "That is the entire split.",
        "As written.",
        "No extras.",
        "This is exact.",
        "Nothing is implied.",
    ]


def _assemble_barg_arm(facts: dict, claim: str,
                       rng: random.Random) -> str:
    """Assemble every non-silent arm around one common character target."""
    def joined(parts):
        return " ".join(p.strip() for p in parts if p and p.strip())

    frames = _barg_arm_frames(facts)
    requests = _barg_arm_requests()
    rng.shuffle(frames)
    rng.shuffle(requests)
    frame = min(frames, key=len)
    request = min(requests, key=len)
    for candidate in frames:
        if len(joined([candidate, claim, request])) <= BARG_ARM_LEN_HI:
            frame = candidate
            break
    parts = [frame, claim, request]
    if len(joined(parts)) > BARG_ARM_LEN_HI:
        parts = [min(frames, key=len), claim]
    text = joined(parts)

    # A broad shared ceiling still leaves register confounded with mean
    # verbosity. Track one reachable sentence-bank rendering per length and
    # choose the length nearest 300 characters, so every arm actually occupies
    # the same narrow realised band without truncating a truth qualifier.
    candidates = {len(text): text}
    fillers = _barg_arm_fillers(facts)
    rng.shuffle(fillers)
    for filler in fillers:
        additions = {}
        for candidate in list(candidates.values()):
            extended = joined([candidate, filler])
            if len(extended) <= BARG_ARM_LEN_HI:
                additions.setdefault(len(extended), extended)
        for length, candidate in additions.items():
            candidates.setdefault(length, candidate)
    in_band = [candidate for candidate in candidates.values()
               if BARG_ARM_LEN_LO <= len(candidate) <= BARG_ARM_LEN_HI]
    if not in_band:
        return text.strip()
    distance = min(abs(len(candidate) - BARG_ARM_TARGET_LEN)
                   for candidate in in_band)
    closest = [candidate for candidate in in_band
               if abs(len(candidate) - BARG_ARM_TARGET_LEN) == distance]
    return rng.choice(closest).strip()


def bargaining_arm_message(arm: str, game: dict, action: dict,
                           plan: dict | None = None,
                           rng: random.Random | None = None) -> dict:
    """Compose one hand-written arm; ``plan`` is accepted and never inspected."""
    out = {"arm": arm, "grammar_version": BARG_ARM_GRAMMAR_VERSION,
           "text": None, "claim_id": None, "claim_kind": None, "reason": None}
    try:
        if arm not in BARG_ARMS:
            out["reason"] = "unknown-arm"
            return out
        if arm == "B0":
            out["reason"] = "silent-arm"
            return out
        facts = _barg_public_facts(game, action)
        if facts is None:
            out["reason"] = "facts-unavailable"
            return out
        if rng is None:
            state = game.get("game_state") or {}
            rng = random.Random(f"barg-msg:{game.get('game_id')}:{state.get('round')}")
        claim, claim_id = _barg_arm_claim(arm, facts, rng)
        text = _assemble_barg_arm(facts, claim, rng)
        if not text or not BARG_ARM_LEN_LO <= len(text) <= BARG_ARM_LEN_HI:
            out["reason"] = "length-band-failure"
            return out
        out.update(text=text, claim_id=claim_id,
                   claim_kind="fact" if claim_id else None, reason="ok")
        return out
    except Exception:
        out["reason"] = "exception"
        out["text"] = None
        return out


def bargaining_numeric_fingerprint(action: dict) -> str:
    payload = {k: v for k, v in action.items()
               if k != "message" and not str(k).startswith("_")}
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def attach_bargaining_arm(game: dict, action: dict) -> dict | None:
    """Attach the per-game hand-written arm without changing any numeric field."""
    try:
        if not runtime_flags.enabled(BARG_MSG_FLAG):
            return None
        if game.get("game_family") != "bargaining":
            return None
        if (game.get("valid_actions") or {}).get("type") != "offer":
            return None
        if (game.get("game_state") or {}).get("messages_allowed") is not True:
            return None
        arm = bargaining_arm(game.get("game_id"))
        if arm is None:
            return None

        plan = action.get("_plan")
        before_action = dict(action)
        before = bargaining_numeric_fingerprint(action)
        # Dispatch coerces integer-pot bargaining gains to whole units. Compose
        # from that same wire action so a sentence never quotes 432.87 while the
        # submitted split says 433; attachment still changes only ``message``.
        wire_action = coerce(action, game)
        try:
            composed = bargaining_arm_message(arm, game, wire_action)
        except Exception:
            composed = {"text": None, "reason": "exception"}
        record = {
            "experiment_id": "barg-msg-1",
            "arm": arm,
            "assignment": f"sha256({BARG_ARM_SALT}<game_id>) mod {len(BARG_ARMS)}",
            "p_assign": 1.0 / len(BARG_ARMS),
            "game_id": game.get("game_id"),
            "round": (game.get("game_state") or {}).get("round"),
            "grammar_version": BARG_ARM_GRAMMAR_VERSION,
            "numeric_sha256_before": before,
        }
        text = composed.get("text") if isinstance(composed, dict) else None
        if arm == "B0":
            action.pop("message", None)
            record.update(outcome="silent", message_len=0,
                          claim_id=None, claim_kind=None)
        elif isinstance(text, str) and text.strip():
            action["message"] = text.strip()
            record.update(outcome="sent", message_len=len(action["message"]),
                          claim_id=composed.get("claim_id"),
                          claim_kind=composed.get("claim_kind"))
        else:
            failure_reason = (composed.get("reason")
                              if isinstance(composed, dict)
                              else "invalid-composer-result")
            record.update(outcome="compose_failed",
                          reason=failure_reason,
                          message_len=0, claim_id=None, claim_kind=None)

        after = bargaining_numeric_fingerprint(action)
        if after != before:
            action.clear()
            action.update(before_action)
            record.update(outcome="invariance_violation",
                          numeric_sha256_after=after,
                          numeric_invariant_ok=False)
        else:
            record.update(numeric_sha256_after=after, numeric_invariant_ok=True)
        if isinstance(plan, dict):
            plan["barg_msg_arm"] = record
        return record
    except Exception:
        return None


def bargaining_message(game: dict, action: dict, plan: dict | None,
                       rng: random.Random) -> str | None:
    """Legacy builder: the neutral arm, using the same leak-audited pools."""
    composed = bargaining_arm_message("B1", game, action, plan, rng)
    return composed.get("text") if isinstance(composed, dict) else None


def negotiation_message(game: dict, action: dict, plan: dict | None,
                        rng: random.Random) -> str | None:
    if not plan:
        return None
    price = _num(action.get("product_price"), 0.0)
    seller = plan.get("i_am_seller")
    reservation = plan.get("reservation", 0.0)
    rounds_left = plan.get("rounds_left")
    decision = action.get("decision")

    if decision == "AcceptOffer":
        return _pick(rng, ["Agreed — done at that price.", "That works. Closing here."])

    parts = []
    if price:
        parts.append(_pick(rng, [
            f"{price:,.2f}.",
            f"I can do {price:,.2f}.",
            f"My number is {price:,.2f}.",
        ]))
    # THE SAME LEAK, IN NEGOTIATION. These two lines fired only when the price
    # was within 10% of our PRIVATE reservation -- 4,926 and 4,994 historical
    # emissions, every one of them inside that band. An opponent correlating the
    # phrase with our subsequent behaviour learns exactly when we have no room
    # left, which is the one thing about us they cannot otherwise observe, and
    # the moment to stop conceding.
    #
    # The claim itself is a legitimate tactic; being perfectly honest about WHEN
    # we make it is what hands over the information. So the line stays in the
    # general pool and is no longer conditioned on proximity to the limit.
    if seller:
        parts.append(_pick(rng, [
            "I would rather trade than not, but not at any number.",
            "Priced to close, not to start a haggle.",
            "There is no meaningful room left on my side of this.",
        ]))
    else:
        parts.append(_pick(rng, [
            "That leaves you a clear gain over walking away.",
            "This is a real offer, and it beats no deal for both of us.",
            "There is no meaningful room left on my side of this.",
        ]))
    # Deadline talk only when the deadline is REAL. In uncapped games
    # rounds_left is the synthetic planning clock, and the transcript export
    # showed "nearly out of rounds" repeated from round 11 to round 99 of a
    # hidden-horizon game -- a claim any patient opponent can falsify by
    # simply waiting, which converts the message from leverage into a leak.
    if (rounds_left is not None and rounds_left <= 2
            and plan.get("capped", False)):
        parts.append("We are nearly out of rounds, and no deal pays us both zero.")
    return " ".join(parts)[:1800]


def persuasion_message(game: dict, action: dict, plan: dict | None,
                       rng: random.Random) -> str | None:
    """Text mode: the message IS the move, so it must carry the recommendation.

    A seller's only asset is credibility across rounds, so an honest round is
    said plainly — that is what makes the recommending rounds worth anything.
    """
    if not plan:
        return None
    recommend = plan.get("recommend", True)
    round_no = int(_num(plan.get("round"), 1))
    total = int(_num(plan.get("total_rounds"), 1))
    reason = str(plan.get("reason", ""))
    # Whether THIS recommendation is truthful. A promise of candour made while
    # pushing a known-low unit is falsifiable the moment the buyer purchases,
    # and a broken promise costs more credibility than saying nothing.
    truthful = plan.get("quality_is_high", None)

    if not recommend:
        # Declining to sell is the credibility purchase. Say so explicitly.
        return _pick(rng, [
            "Not this one. It is below the standard I want to put my name to — "
            "wait for the next.",
            "I would pass on this unit. I would rather tell you that than sell it "
            "to you and lose your trust for the rest of these rounds.",
            "Honestly, this one is weak. Skip it.",
        ])

    parts = [_pick(rng, [
        "This one is worth taking.",
        "Strong unit this round — I would buy it.",
        "This is one of the better ones.",
    ])]
    # THE CLOSER MUST NOT DEPEND ON THE QUALITY ONLY WE CAN SEE.
    #
    # The branch below picked the closer from `truthful`, and the two
    # price-framing lines it used for a weak unit appear NOWHERE ELSE. Measured
    # over 24h of live seller rounds, that made them a perfect oracle:
    #
    #   "Priced the same as every other round"  3,008 bought, 100% LOW
    #   "Same price as always"                  3,041 bought, 100% LOW
    #   "My record on these is the reason"      4,695 bought,   0% LOW
    #   "You can check that against the calls"  4,636 bought,   0% LOW
    #
    # 6,049 low units all carrying one of two phrases, 11,079 high units
    # carrying neither. The intent was sound -- do not make a falsifiable
    # promise about a bad unit -- but because those lines were reserved for that
    # case, "generic" became DISTINCTIVE, and we shipped a code word for
    # "this one is worthless" six thousand times. Any opponent correlating
    # phrasing with outcome gets our private signal for free, and against a
    # repeated buyer that is the whole game.
    #
    # It shows up exactly where it should: those closers convert at 2-5% when
    # the buyer has been passing, against 12% for the best one -- and they are
    # attached to the units where a sale is pure profit to us.
    #
    # So: one pool, chosen independently of quality. Both survivors are
    # backward-looking references to our record rather than promises about THIS
    # unit, so neither is falsifiable on the round it is sent, and both are the
    # best-converting lines we have. Gated so the change is measurable.
    # NOT gated. A leak is a defect, not an experiment: there is no configuration
    # in which broadcasting the quality is the behaviour we want, so the leaking
    # branches are deleted rather than kept behind a flag. `truthful` is now
    # unused here by design -- the closer must not be able to depend on it.
    parts.append(_pick(rng, [
        "My record on these is the reason to take this one seriously.",
        "You can check that against the calls I have made so far.",
    ]))
    return " ".join(parts)[:1800]


# --------------------------------------------------------------------------
# NEGOTIATION MESSAGE ARMS — the randomised bank behind GLEE_NEGO_MSG_ARMS.
#
# ``negotiation_message`` above is the single un-randomised template: it picks
# the strongest available line and sends it, which is fine for playing and
# useless for measuring, because every offer gets the treatment its own state
# selected. The arms below hold the NUMBER fixed and vary only the argument, so
# the difference between two arms is attributable to the words.
#
# Four slots, assembled in this order:
#
#     [FRAME] + [CLAIM] + [REQUEST]  (+ FILLER to reach the length band)
#
# FRAME, REQUEST and FILLER are drawn from pools shared by every messaged arm,
# from one rng seeded per turn (not per arm), so length is matched by
# construction and the only systematic difference between N1 and a treatment is
# the CLAIM. The claim itself is chosen DETERMINISTICALLY — first available in
# an ordered ladder, no rng — so "which arms are eligible here" and "what this
# arm would say here" are the same question, and the randomiser can drop an arm
# that would go quiet before it spends a block slot on it.
#
# Truth discipline, inherited from experiments/framing.py and from the
# persuasion post-mortem that produced it:
#   * every claim tagged ``fact`` is arithmetic over public objects — a price
#     the opponent themselves named, a price we ourselves named, a valuation the
#     server disclosed to both sides, or a rule of the game;
#   * the one claim tagged ``bluff`` (N3's mandate language) is an unverifiable
#     statement about our OWN position, legal under the rules, and it is gated
#     to states where our own schedule is not about to contradict it next round;
#   * no arm ever makes a falsifiable promise about our own future moves, and
#     no arm reveals our private valuation.
# --------------------------------------------------------------------------

#: Bump when a pool or a claim precondition changes; it feeds the arm-set
#: version, so a mid-flight edit shows up in the analysis instead of pooling
#: silently with data collected under the old grammar.
NEGO_ARM_GRAMMAR_VERSION = "nego-msg-grammar-1"

#: Realised length band. The floor is what makes N1 a length-matched control
#: rather than a terser one; the ceiling is an eighth of the server's 2,000.
NEGO_ARM_LEN_LO, NEGO_ARM_LEN_HI = 180, 320

NEGO_ARM_SEMANTICS = {
    "N0": "silent — no message attached, though the channel is open. This is "
          "exactly what the fleet does today, so it is the control that makes "
          "the whole experiment a measurement of the channel itself.",
    "N1": "neutral, length-matched — states the price and hands the turn back. "
          "Text with no argument in it; the reference for every contrast.",
    "N2": "precise anchor — the price to the cent, plus a concrete derivation "
          "over public numbers (their bid, our previous ask, the disclosed "
          "band). A round number reads as an opening gesture; a worked one "
          "reads as a constraint.",
    "N3": "mandate freeze — this is the limit of my mandate, and the "
          "alternative is no deal, which pays us both zero. Unverifiable about "
          "our own side, so gated to states where our own schedule will not "
          "refute it next round.",
}

NEGO_ARMS = ("N0", "N1", "N2", "N3")


def _fmt(x: float) -> str:
    return f"{x:,.2f}"


def _nego_prices(state: dict, me: str) -> tuple[list[float], list[float]]:
    """(prices we named, prices they named), oldest first.

    Local to this module on purpose: importing the negotiation strategy here
    would make the message bank a dependency of the decision core rather than
    the other way round.
    """
    ours: list[float] = []
    theirs: list[float] = []
    entries = list(state.get("history") or [])
    last = state.get("last_offer")
    if isinstance(last, dict):
        entries = entries + [{"offer": last}]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("offer", "counteroffer"):
            offer = entry.get(key)
            if not isinstance(offer, dict) or offer.get("price") is None:
                continue
            price = _num(offer["price"])
            bucket = ours if offer.get("from_player") == me else theirs
            if not bucket or bucket[-1] != price:
                bucket.append(price)          # collapse the record echo
    return ours, theirs


def _nego_arm_facts(game: dict, action: dict, plan: dict) -> dict | None:
    """Everything a claim may read, computed once. Numbers in, no numbers out."""
    price = action.get("product_price")
    if price is None:
        return None
    price = _num(price, -1.0)
    if price < 0:
        return None
    state = game.get("game_state") or {}
    me = state.get("current_player") or game.get("your_player") or "player_1"
    ours, theirs = _nego_prices(state, me)
    if ours and abs(ours[-1] - price) < 0.005:
        ours = ours[:-1]                      # this very offer, already recorded
    zopa = plan.get("zopa")
    return {
        "price": price,
        "i_am_seller": bool(plan.get("i_am_seller")),
        "round": int(_num(state.get("round"), 1)),
        "rounds_left": int(_num(plan.get("rounds_left"), 1)),
        "capped": bool(plan.get("capped")),
        "reservation": _num(plan.get("reservation"), 0.0),
        "our_prev": ours[-1] if ours else None,
        "their_last": theirs[-1] if theirs else None,
        "zopa": zopa if isinstance(zopa, (tuple, list)) and len(zopa) == 2 else None,
        # Any of these means the concession schedule is frozen for now, so
        # "this is where I stop" is not about to be refuted by our own next move.
        "frozen": bool(plan.get("ultimatum") or plan.get("deadgame")
                       or plan.get("probe_hold") or plan.get("recip_damped")
                       or plan.get("time_driven") or plan.get("span_veto")),
    }


def _n2_claim(f: dict) -> dict | None:
    """PRECISE. Ordered ladder; the first that fires wins. Always fires.

    The claims refer back to the price rather than restating it: the FRAME slot
    already names it to the cent in every arm, so re-quoting it here would put
    the number twice in the treatment arms and once in the control — a length
    and salience difference that is not the treatment.
    """
    price, seller = f["price"], f["i_am_seller"]
    their = f["their_last"]
    if their is not None:
        gap = (price - their) if seller else (their - price)
        if gap >= 0.01:
            return {"claim_id": "n2_gap_vs_their_bid", "claim_kind": "fact",
                    "text": (f"That is {_fmt(gap)} "
                             f"{'above' if seller else 'below'} the {_fmt(their)} "
                             f"you named, and that gap is the whole of what is "
                             f"still open between us.")}
    prev = f["our_prev"]
    if prev is not None and abs(prev - price) >= 0.01:
        step = abs(prev - price)
        return {"claim_id": "n2_step_from_our_last", "claim_kind": "fact",
                "text": (f"That is {_fmt(step)} "
                         f"{'down from' if (prev > price) else 'up from'} the "
                         f"{_fmt(prev)} I named before — a worked step, not a "
                         f"round number chosen to look like one.")}
    if f["zopa"]:
        lo, hi = _num(f["zopa"][0]), _num(f["zopa"][1])
        span = hi - lo
        if span > 0 and lo - 0.01 <= price <= hi + 0.01:
            share = (price - lo) / span
            return {"claim_id": "n2_zopa_share", "claim_kind": "fact",
                    "text": (f"That sits {share * 100:.1f}% of the way across the "
                             f"{_fmt(span)} between our two disclosed valuations, "
                             f"which is exactly where the number comes from.")}
    return {"claim_id": "n2_exact", "claim_kind": "fact",
            "text": ("That figure is exact to the cent: it is worked out from "
                     "what this trade is worth to me and how many rounds are "
                     "left in it, not rounded off into an opening position.")}


def _n3_claim(f: dict) -> dict | None:
    """MANDATE FREEZE. Defined only where our own schedule will not refute it.

    The mandate sentence is a bluff — unverifiable, about our own side, legal.
    The sentence beside it is a fact: a no-deal pays both sides zero. What the
    gate buys is that nothing WE do next round contradicts the bluff, which is
    the failure mode that makes a bluff cost more than silence.
    """
    if f["capped"] and f["rounds_left"] <= 1:
        return {"claim_id": "n3_terminal", "claim_kind": "bluff",
                "text": ("There is no round after this one: if that does not "
                         "close, we both book zero. It is also the limit of my "
                         "mandate, so it is the whole decision in front of you.")}
    reservation = f["reservation"]
    if reservation and abs(f["price"] - reservation) <= 0.10 * abs(reservation):
        return {"claim_id": "n3_at_limit", "claim_kind": "bluff",
                "text": ("That is the limit of my mandate on this one. The "
                         "alternative is no deal, and no deal pays us both "
                         "exactly zero.")}
    if f["frozen"]:
        return {"claim_id": "n3_frozen", "claim_kind": "bluff",
                "text": ("I have taken this as far as my mandate allows, and "
                         "that is where it stops. If we do not close, we both "
                         "take zero out of it.")}
    return None


_NEGO_ARM_CLAIMS = {"N2": _n2_claim, "N3": _n3_claim}


def negotiation_arm_claim(arm: str, game: dict, action: dict,
                          plan: dict | None) -> dict | None:
    """The claim ``arm`` would make here, or ``None`` when it has none.

    Deterministic: no rng, so the randomiser can ask this question before it
    draws. N0 and N1 carry no claim by definition and are not asked.
    """
    try:
        builder = _NEGO_ARM_CLAIMS.get(arm)
        if builder is None or not isinstance(plan, dict):
            return None
        facts = _nego_arm_facts(game, action, plan)
        if facts is None:
            return None
        return builder(facts)
    except Exception:
        return None


def _nego_arm_frames(f: dict) -> list[str]:
    p = _fmt(f["price"])
    return [f"{p}.", f"My number is {p}.", f"I can do {p}.",
            f"Round {f['round']}: {p}.", f"The price I am naming is {p}."]


def _nego_arm_requests(arm: str) -> list[str]:
    if arm == "N1":
        return ["It is your call.", "Over to you.", "Your move.",
                "Respond as you see fit.", "The decision is yours."]
    return ["Accept and we are done.", "Take it and this closes here.",
            "Say yes and neither of us spends another round on it.",
            "Close it here.", "Accept, and we both book this now."]


def _nego_arm_fillers(f: dict) -> list[str]:
    """Argument-free, true, on-topic padding, shared across every messaged arm."""
    return [
        f"This is round {f['round']}.",
        f"The price named is {_fmt(f['price'])}.",
        f"I am the {'seller' if f['i_am_seller'] else 'buyer'} here.",
        "No conditions are attached to the price.",
        "That is the number as submitted.",
        "One price, one product, nothing else in the package.",
        "The offer stands exactly as written.",
        "Nothing else is bundled with it.",
        "That is the whole of my proposal for this round.",
    ]


def _fit(rng: random.Random, options: list[str], budget: int) -> str:
    """A random option that fits the budget; the shortest one if none does.

    Choosing to fit rather than choosing then trimming is what keeps the claim
    inviolable: a trimmer can amputate the qualifier that made a sentence true.
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


def _assemble_nego_arm(frames: list[str], claim: str, requests: list[str],
                       fillers: list[str], rng: random.Random) -> str:
    """Fill the slots around the claim, then pad toward the band floor.

    Priority is fixed and arm-independent. The CLAIM is the treatment and is
    never shortened or dropped. The REQUEST is a slot every arm fills, so
    dropping it for some arms would make slot presence itself correlate with the
    arm. The FRAME comes third; filler is added last and only to reach LEN_LO.
    """
    def join(parts):
        return " ".join(p.strip() for p in parts if p and p.strip())

    claim = (claim or "").strip()
    min_frame = min((len(x) for x in frames if x), default=0)
    request = _fit(rng, requests, max(0, NEGO_ARM_LEN_HI - len(claim) - min_frame - 2))
    frame = _fit(rng, frames, max(0, NEGO_ARM_LEN_HI - len(claim) - len(request) - 2))
    parts = [frame, claim, request]
    if len(join(parts)) > NEGO_ARM_LEN_HI:
        # Keep the shortest frame rather than dropping it: the claims refer back
        # to "that", and a claim with no frame in front of it has no referent.
        parts = [min((x for x in frames if x), key=len, default=""), claim]
    text = join(parts)

    pool = [x for x in fillers if x]
    rng.shuffle(pool)
    for filler in pool:
        if len(text) >= NEGO_ARM_LEN_LO:
            break
        candidate = f"{text} {filler}"
        if len(candidate) <= NEGO_ARM_LEN_HI:
            text = candidate
    return text.strip()


def negotiation_arm_message(arm: str, game: dict, action: dict,
                            plan: dict | None,
                            rng: random.Random | None = None) -> dict:
    """The message for one arm, with its provenance. Never raises.

    Returns ``{"text": str|None, "claim_id", "claim_kind", "reason", ...}``.
    ``text is None`` means this arm sends nothing here — which is a result for
    N0 and a "do not assign me" for a treatment arm, and must never be
    back-filled from ``negotiation_message`` above: that would destroy the
    silent control and mix the un-randomised template into a treatment cell.
    """
    out = {"arm": arm, "grammar_version": NEGO_ARM_GRAMMAR_VERSION,
           "text": None, "claim_id": None, "claim_kind": None, "reason": None}
    try:
        if arm not in NEGO_ARMS:
            out["reason"] = "unknown-arm"
            return out
        if arm == "N0":
            out["reason"] = "silent-arm"
            return out
        if not isinstance(plan, dict) or not isinstance(action, dict):
            out["reason"] = "no-plan"
            return out
        facts = _nego_arm_facts(game, action, plan)
        if facts is None:
            out["reason"] = "facts-unavailable"
            return out
        claim = None
        if arm != "N1":
            claim = negotiation_arm_claim(arm, game, action, plan)
            if claim is None:
                out["reason"] = "no-true-claim-available"
                return out
        if rng is None:
            state = game.get("game_state") or {}
            rng = random.Random(f"nego-msg:{game.get('game_id')}:{state.get('round')}")
        text = _assemble_nego_arm(_nego_arm_frames(facts),
                                  claim["text"] if claim else "",
                                  _nego_arm_requests(arm),
                                  _nego_arm_fillers(facts), rng)
        if not text:
            out["reason"] = "empty"
            return out
        out.update(text=text, reason="ok",
                   claim_id=claim["claim_id"] if claim else None,
                   claim_kind=claim["claim_kind"] if claim else None)
        return out
    except Exception:
        out["text"] = None
        out["reason"] = "exception"
        return out


BUILDERS = {
    "bargaining": bargaining_message,
    "negotiation": negotiation_message,
    "persuasion": persuasion_message,
}


def compose(game: dict, action: dict, plan: dict | None,
            rng: random.Random) -> str | None:
    builder = BUILDERS.get(game.get("game_family"))
    if builder is None:
        return None
    try:
        return builder(game, action, plan, rng)
    except Exception:
        return None          # a message is never worth risking the move over
