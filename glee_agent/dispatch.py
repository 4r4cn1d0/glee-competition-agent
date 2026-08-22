"""The single entry point handed to ``client.run`` — one function per family
behind a dispatcher, with the safety net around it.

Two SDK behaviours make that net necessary. A strategy that raises causes the
SDK to log the traceback and submit *nothing*, so the game stalls until the
120-second turn timeout closes it as a no-deal — scored at the 5th percentile.
And an action the server rejects is not retried: it burns one of five attempts
and the turn clock keeps running.

So this layer is total. Every path returns a legal action, and any exception
anywhere below it degrades to the conservative fallback rather than escaping.
"""

from __future__ import annotations

import logging
import math
import os
import random

from . import llm, messages
from .actions import coerce, safe_action
from .strategies import bargaining, negotiation, persuasion

logger = logging.getLogger("glee.dispatch")

STRATEGIES = {
    "bargaining": bargaining.decide,
    "negotiation": negotiation.decide,
    "persuasion": persuasion.decide,
}


def make_strategy(cfg, log=None):
    """Build the ``strategy(game) -> action`` callable for this configuration."""

    def strategy(game: dict) -> dict:
        try:
            return _play(game, cfg, log)
        except Exception as exc:           # nothing may escape into the SDK
            logger.exception("Strategy failed for game %s", game.get("game_id"))
            if log is not None:
                try:
                    log.error(game, exc, stage="strategy")
                except Exception:
                    logger.exception("Could not record strategy error")
            try:
                # The fallback uses the same final postconditions as every
                # ordinary action, including flagged complete-info price guards.
                action = coerce(safe_action(game), game)
            except Exception:
                # safe_action is written not to fail; if it somehow does, still
                # submit something shaped like the phase rather than nothing.
                logger.exception("Fallback failed for game %s", game.get("game_id"))
                action = _last_resort(game)
            # Record the action actually returned after an exception.  Outcome
            # analyzers cohort from ordinary turn records, so omitting fallback
            # turns would select failures out of per-game close-rate estimates.
            if log is not None:
                try:
                    log.turn(game, action, None, source="fallback:strategy-error")
                except Exception:
                    logger.exception("Could not record strategy fallback")
            return action

    return strategy


def _play(game: dict, cfg, log) -> dict:
    family = game.get("game_family")
    decide = STRATEGIES.get(family)
    if decide is None:
        logger.warning("Unknown game family %r", family)
        action = safe_action(game)
        if log is not None:
            log.turn(game, action, None, source="fallback:unknown-family")
        return action

    # 1. The heuristic decides. This is always computed, even in "full" mode,
    #    because it is what the model's reply is checked against.
    raw = decide(game, cfg)
    plan = raw.pop("_plan", None)
    source = "heuristic"

    # 2. In "full" mode the model may override, but only through the same
    #    repair path — a bad override degrades to the heuristic, never to an
    #    invalid move.
    # Bargaining is sentence-bank only. Even a stale custom allowlist cannot
    # route its action or message through an LLM; GLEE_BARG_MSG owns that channel
    # downstream of the already-final numeric split.
    if (family != "bargaining" and cfg.llm_mode == "full" and family in
            set((os.environ.get("GLEE_LLM_FAMILIES") or "persuasion").split(","))):
        proposed = llm.propose_action(game, raw, plan, cfg)
        if proposed:
            repaired = coerce(proposed, game)
            if repaired:
                raw, source = repaired, "llm"

    action = coerce(raw, game)

    # Persuasion TEXT mode: the message IS the action. In messages/full mode the
    # LLM rewords the policy's recommendation persuasively; the recommendation
    # itself is never the model's to change, and any failure falls back to the
    # template (a lost call costs wording, never a game).
    if (game.get("game_family") == "persuasion" and "persuasion" in
            set((os.environ.get("GLEE_LLM_FAMILIES") or "persuasion").split(","))
            and cfg.llm_mode in ("messages", "full")
            and isinstance(action, dict) and "message" in action
            and (game.get("game_state") or {}).get("seller_message_type") == "text"):
        rec = bool(plan.get("recommend")) if isinstance(plan, dict) else \
            ("recommend" in str(action.get("message", "")).lower())
        better = llm.pers_seller_message(game, rec, cfg)
        if better:
            action = dict(action, message=better)
            source = source + "+llm-pers"


    # 3. Attach a message. The numbers are already fixed at this point, so a
    #    slow or failed call costs nothing but the message itself.
    # Default-DENY outside persuasion: a process launched without the env var
    # must fence itself rather than inherit an open door. Bargaining is excluded
    # from this branch entirely; its GLEE_BARG_MSG arm was already attached by
    # the hand-written bank and B0 must remain silent rather than be back-filled.
    llm_fams = set((os.environ.get("GLEE_LLM_FAMILIES") or "persuasion").split(","))
    # A message the randomised negotiation arms already attached is the
    # treatment; recomposing over it would replace it with the un-randomised
    # template and silently destroy the experiment. The marker only exists when
    # GLEE_NEGO_MSG_ARMS is set, so with the flag unset this condition is
    # exactly the one that was here before.
    armed = isinstance(plan, dict) and bool(plan.get("msg_arm"))
    barg_armed = isinstance(plan, dict) and bool(plan.get("barg_msg_arm"))
    # In persuasion TEXT mode the message IS the recommendation -- it is the
    # whole action, not decoration on a number. Recomposing over it replaced the
    # strategy's chosen wording with a generic template and made
    # GLEE_PERS_MSG_STYLE completely inert: the flag was armed on three agents
    # and 0% of their messages were the token form, 100% were prose.
    # That is expensive. persuasion.py's own note records a 20pp conversion gap
    # between a binary "yes" (71.5% buy at high prior) and the prose template
    # (51.2%), and the live cells agree -- at p=0.8 we push in 96% of text
    # rounds and 97% of binary rounds, yet sell 65% against 74%. The seller
    # p=0.8 text cell scores at the 0.366 percentile against 0.537 for the same
    # configuration in binary, which is ~926 rating-equivalent in that cell.
    # Same intent, different tokens, and the buyers are parsers.
    #
    # Gated so the fix itself is measurable rather than assumed: with
    # GLEE_PERS_KEEP_MSG unset, behaviour is exactly what it was.
    from . import runtime_flags as _rf
    # `style_downgraded` means persuasion.decide DELIBERATELY declined the token
    # at a high prior and wants the full template bank instead -- which is the
    # path that measured 69.3% conversion at p=0.8, against 60.8% for the bare
    # token. Preserving the strategy's fallback string here would send
    # "I recommend this one." instead, a third thing that was never measured.
    # So a downgrade is explicitly NOT final: let compose() build the message.
    _downgraded = isinstance(plan, dict) and bool(plan.get("style_downgraded"))
    pers_final = (game.get("game_family") == "persuasion"
                  and (game.get("game_state") or {}).get("seller_message_type") == "text"
                  and isinstance(action, dict)
                  and isinstance(action.get("message"), str)
                  and action["message"].strip()
                  and not _downgraded
                  and _rf.enabled("GLEE_PERS_KEEP_MSG"))
    if _wants_message(game) and family != "bargaining" and family in llm_fams \
            and not armed and not pers_final:
        message = None
        if cfg.llm_mode in ("messages", "full"):
            message = llm.write_message(game, action, plan, cfg)
        tag = "+llm-msg"
        if not message:
            # No provider configured, or the call failed. Grounded templates are
            # the floor — far better than silence on a channel that is open in
            # a third of turns.
            message = messages.compose(game, action, plan, _rng(game))
            tag = "+tmpl-msg"
        if message:
            action["message"] = message
            action = coerce(action, game)   # re-check the 2,000-char cap
            source += tag
    elif armed:
        # Name the arm in the turn's source so the assignment is visible in a
        # grep of turns.jsonl, not only inside the plan record.
        source += f"+arm-{(plan.get('msg_arm') or {}).get('arm')}"
    elif barg_armed:
        source += f"+barg-arm-{(plan.get('barg_msg_arm') or {}).get('arm')}"

    if log is not None:
        log.turn(game, action, plan, source=source)
    logger.info("[%s] %s r%s -> %s (%s)", family,
                (game.get("valid_actions") or {}).get("type"),
                (game.get("game_state") or {}).get("round"), action, source)
    return action


def _rng(game: dict) -> random.Random:
    """Per-game phrasing variation that stays reproducible for a replay."""
    return random.Random(f"{game.get('game_id')}:{(game.get('game_state') or {}).get('round')}")


def _last_resort(game: dict) -> dict:
    """Phase-shaped action of last resort. Submitting the wrong shape is an
    invalid move, so match the action type even with no usable state."""
    action_type = (game.get("valid_actions") or {}).get("type")
    if action_type == "seller_message":
        return {"message": "I recommend this product."}
    if action_type == "offer":
        if game.get("game_family") == "bargaining":
            money = ((game.get("game_state") or {}).get("money_to_divide")) or 0
            return {"alice_gain": money / 2, "bob_gain": money / 2}
        if game.get("game_family") == "negotiation":
            # This branch is reached only after coerce itself failed, so it does
            # not re-enter coerce. Our own finite valuation is already on the
            # visible ZOPA boundary in either seat.
            state = game.get("game_state") or {}
            me = state.get("current_player") or game.get("your_player") or ""
            try:
                price = float(state.get(f"{me}_value"))
            except (TypeError, ValueError):
                price = 1.0
            if not math.isfinite(price):
                price = 1.0
            return {"product_price": max(0.0, price)}
        return {"product_price": 1}
    if game.get("game_family") == "negotiation":
        return {"decision": "AcceptOffer"}
    if game.get("game_family") == "bargaining":
        return {"decision": "accept"}
    return {"decision": "yes"}


def _wants_message(game: dict) -> bool:
    """Whether this phase carries free text worth spending a model call on."""
    action_type = (game.get("valid_actions") or {}).get("type")
    if action_type == "seller_message":
        return True                        # the message *is* the move
    if (game.get("game_state") or {}).get("messages_allowed") is False:
        return False
    # Offers and counteroffers persuade; a bare accept/reject does not.
    if action_type == "offer":
        return True
    if action_type == "decision":
        return game.get("game_family") == "negotiation"
    return False
