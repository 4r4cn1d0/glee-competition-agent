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
                log.error(game, exc, stage="strategy")
            try:
                return safe_action(game)
            except Exception:
                # safe_action is written not to fail; if it somehow does, still
                # submit something shaped like the phase rather than nothing.
                logger.exception("Fallback failed for game %s", game.get("game_id"))
                return _last_resort(game)

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
    if cfg.llm_mode == "full":
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
    llm_fams = set((os.environ.get("GLEE_LLM_FAMILIES") or
                    "bargaining,negotiation,persuasion").split(","))
    if _wants_message(game) and game.get("game_family") in llm_fams:
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
