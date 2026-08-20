"""Optional LLM layer, provider-agnostic through litellm.

Three modes, set by ``GLEE_LLM_MODE``:

* ``off``      — pure heuristics. No cost, no latency, no provider key needed.
* ``messages`` — the heuristics decide every number; the model only writes the
  free text that accompanies them. This is the default: it is where the model
  earns its keep (a message is what moves an LLM or human opponent) at one cheap
  call per turn instead of a decision-critical one.
* ``full``     — the model proposes the whole action; the heuristic result is
  passed in as a recommendation and used whenever the model's reply is unusable.

Every call is capped by a timeout well inside the 120-second turn clock, and no
failure here can ever produce an illegal move: the caller keeps the heuristic
action as its fallback.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading

logger = logging.getLogger("glee.llm")

_lock = threading.Lock()
_calls = 0
_failures = 0

SYSTEM_PROMPT = """\
You are a strategic player in an economic game, playing to maximise YOUR OWN
payoff over the whole game. You are given the situation, the state visible to
you (including the history of past rounds), and a recommendation computed by a
game-theoretic solver.

The solver's numbers are usually right — it knows the equilibrium of this game.
Deviate only when the history gives you a concrete reason to.

Reply with ONLY a JSON object. No explanation, no markdown fences.
"""

MESSAGE_PROMPT = """\
You are a strategic player in an economic game. Your move has already been
decided; write the short message that goes with it.

The message is the only thing your opponent reads. Make it work for you: give
the offer a reason to be accepted, anchor expectations, signal firmness or
flexibility as the situation warrants. Any strategic content is legal here,
including bluffing.

Keep it under 60 words, plain text, no markdown, no quotes around it. Reply with
the message text only — nothing else.
"""


def _budget_exhausted(cfg) -> bool:
    if cfg.llm_max_calls <= 0:
        return False
    with _lock:
        return _calls >= cfg.llm_max_calls


def _count_call() -> None:
    global _calls
    with _lock:
        _calls += 1


def _count_failure() -> None:
    global _failures
    with _lock:
        _failures += 1


def stats() -> dict:
    with _lock:
        return {"llm_calls": _calls, "llm_failures": _failures}


def _complete(cfg, messages: list[dict], model: str | None = None) -> str | None:
    if _budget_exhausted(cfg):
        return None
    try:
        from litellm import completion
    except ImportError:
        logger.warning("litellm is not installed; falling back to heuristics")
        return None
    _count_call()
    try:
        response = completion(model=model or cfg.llm_model, messages=messages,
                              timeout=cfg.llm_timeout)
        return response.choices[0].message.content or ""
    except Exception as exc:               # provider error, timeout, bad key
        _count_failure()
        logger.warning("LLM call failed (%s): %s", type(exc).__name__, exc)
        return None


def parse_json(text: str) -> dict | None:
    """Pull a JSON object out of a model reply that may be fenced or chatty."""
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


def _situation(game: dict, plan: dict | None) -> str:
    parts = [
        game.get("prompt", ""),
        "",
        "State visible to you (includes `history` of past rounds):",
        json.dumps(game.get("game_state") or {}, indent=2, default=str),
    ]
    opponent = game.get("opponent") or {}
    if opponent.get("type") and opponent["type"] != "hidden":
        parts += ["", f"Your opponent is a {opponent['type']}"
                      f"{' named ' + str(opponent.get('name')) if opponent.get('name') else ''}."]
    if plan:
        readable = {k: v for k, v in plan.items() if not k.startswith("_")}
        parts += ["", "Solver recommendation and reasoning:",
                  json.dumps(readable, indent=2, default=str)]
    return "\n".join(parts)


def write_message(game: dict, action: dict, plan: dict | None, cfg) -> str | None:
    """Compose the free-text message accompanying an already-decided move."""
    if (game.get("game_state") or {}).get("messages_allowed") is False:
        return None
    decided = {k: v for k, v in action.items() if not k.startswith("_")}
    prompt = (
        f"{_situation(game, plan)}\n\n"
        f"The move you are about to make: {json.dumps(decided, default=str)}\n\n"
        f"Write the message that goes with it."
    )
    text = _complete(cfg, [{"role": "system", "content": MESSAGE_PROMPT},
                           {"role": "user", "content": prompt}])
    if not text:
        return None
    message = text.strip().strip('"').strip()
    return message or None


def propose_action(game: dict, fallback: dict, plan: dict | None, cfg) -> dict | None:
    """Ask the model for a complete action. Returns None if it gives nothing usable."""
    recommended = {k: v for k, v in fallback.items() if not k.startswith("_")}
    prompt = (
        f"{_situation(game, plan)}\n\n"
        f"Your action must follow this format:\n"
        f"{json.dumps(game.get('valid_actions') or {}, indent=2, default=str)}\n\n"
        f"The solver recommends: {json.dumps(recommended, default=str)}\n\n"
        f"Reply with the JSON action only."
    )
    text = _complete(cfg, [{"role": "system", "content": SYSTEM_PROMPT},
                           {"role": "user", "content": prompt}])
    if text is None:
        return None
    action = parse_json(text)
    if action is None:
        _count_failure()
        logger.warning("Unparseable LLM reply: %r", text[:200])
    return action


PERS_SELLER_PROMPT = """You are a seller in a repeated trust game. Fixed price: {price}. \
The buyer knows P(high quality)={p:.2f} and remembers everything. Round {rnd}/{total}. \
Your recommendation this round is: {rec}. \
Write ONE persuasive message (max 160 chars) that clearly conveys that recommendation \
({rec_word}). Be credible, specific, human. Message only, no quotes."""


def pers_seller_message(game: dict, recommend: bool, cfg) -> str | None:
    """LLM-worded seller message for persuasion TEXT mode. The recommendation
    itself comes from the policy and is NOT the model's to change: a reply that
    fails to convey it is discarded for the template. Prompt is deliberately
    tiny (~250 tokens) -- the operator's $15 must stretch to thousands of
    messages, and the experiment is about wording, not context."""
    st = game.get("game_state") or {}
    prompt = PERS_SELLER_PROMPT.format(
        price=st.get("product_price"), p=float(st.get("p") or 0),
        rnd=st.get("round"), total=st.get("total_rounds"),
        rec="RECOMMEND BUYING" if recommend else "ADVISE AGAINST BUYING",
        rec_word="a clear yes" if recommend else "a clear no")
    # Model mix per operator: Sonnet 5 for the bulk, Opus 5 (4x cost) reserved
    # for the two moments wording matters most -- the opening impression
    # (rounds 1-2, nothing else to judge us by) and trust repair right after
    # the buyer caught a lie. ~15% of calls at premium keeps the blend cheap.
    model = None
    hist = st.get("history") or []
    caught_recent = any(r.get("bought") and str(r.get("quality")).lower() == "low"
                        for r in hist[-2:])
    if (st.get("round") or 99) <= 2 or caught_recent:
        model = os.environ.get("GLEE_LLM_MODEL_PREMIUM", "anthropic/claude-opus-5")
    text = _complete(cfg, [{"role": "user", "content": prompt}], model=model)
    if not text:
        return None
    msg = text.strip().strip('"')[:300]
    low = msg.lower()
    positive = not ("don't" in low or "do not" in low or "skip" in low or "pass" in low
                    or "avoid" in low or "hold off" in low or low.startswith("no"))
    if positive != recommend:
        return None                      # model flipped the signal: use template
    return msg or None
