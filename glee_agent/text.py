"""Reading the opponent's words.

GLEE hands you natural language as part of the game state. In persuasion text
mode the seller's message IS the observation a buyer's Bayesian update runs on,
so an agent that cannot read it is not "numbers only" — it is running its belief
update on corrupted input.

The previous approach was a flat blacklist of eight phrases. Measured against
1,530 real messages from live play it read **88% of honest warnings as
recommendations**, including our own template ("I would hold off on this one",
274 occurrences) — the blacklist knew "skip this" but the field writes "skip it".
Every such error tells the buyer a truthful seller lied.

This is still a heuristic and still loses to novel phrasing eventually; the
corpus already holds 108 distinct messages from ~900 games. It is built so an
LLM classifier can replace ``reads_as_recommendation`` without touching callers.

Two things make it work where the blacklist failed:

* **Concession structure.** "I wouldn't blame you for being skeptical, BUT this
  product is genuinely high quality" is a recommendation. The clause after the
  last contrastive conjunction carries the intent, so it is weighted far higher
  than what precedes it.
* **Negation scope.** "recommend" and "not recommend" are opposites, and
  "without reservation" is not a reservation. Polarity is matched on phrases,
  never on bare words.
"""

from __future__ import annotations

import re

# Phrases that decline the sale. Weight reflects how unambiguous each is.
_NEGATIVE = (
    (3.0, ("do not buy", "don't buy", "dont buy", "do not recommend", "don't recommend",
           "not recommending", "cannot recommend", "can't recommend", "would not recommend",
           "wouldn't recommend")),
    (2.5, ("hold off", "hold out for", "pass on this", "pass on it", "i'd pass", "i would pass",
           "skip it", "skip this", "skip a sale", "sit this round out", "sit this one out",
           "not this round", "not this one", "wait for the next", "wait for a better",
           "better to wait", "not worth the price", "would not prioritize",
           "wouldn't prioritize", "wouldn't push it", "you may want to pass")),
    (2.0, ("low quality", "below our usual", "below the standard", "below my usual",
           "isn't my best", "is not my best", "not my strongest", "isn't up to",
           "is not up to", "not up to my usual", "not up to the standard",
           "isn't what you hoped", "not a strong one", "lukewarm",
           "don't think this one is worth", "not worth it for you")),
    (1.2, ("ordinary unit", "nothing special", "unremarkable", "mediocre")),
)

# Phrases that push the sale.
_POSITIVE = (
    (3.0, ("i recommend", "recommending it", "recommending this", "recommended",
           "strong recommendation", "i can recommend", "clear buy", "high confidence buy",
           "yes on this round")),
    (2.5, ("worth it", "worth the price", "worth taking", "worth buying", "worth your money",
           "i'd buy it", "i would buy it", "i'd take it", "i would take", "i'd take this",
           "take it", "buy it myself", "buying is the right call", "definitely a good buy",
           "buying still beats", "a solid purchase", "good deal",
           "better deal", "much better", "you'll be very happy", "consider it")),
    (2.0, ("high quality", "highest quality", "genuinely strong", "genuinely good",
           "genuinely high quality", "one of the strongest", "one of the better",
           "the real thing", "strong unit", "strong pick", "solid pick", "good one",
           "good unit", "clear value", "stand behind")),
)

# Contrastive conjunctions: what follows them is the speaker's actual position.
_CONTRAST = re.compile(r"\b(?:but|however|that said|even so|still,)\b")

#: Weight applied to clauses BEFORE the final contrast. Deliberately small —
#: "I know it's been a rough streak ... but this one is genuinely high quality"
#: is a recommendation, and the concession before the pivot is not the point.
_PRE_CONTRAST_WEIGHT = 0.25


#: Words that invert the phrase following them, and how far ahead they reach.
#: "not every unit is worth the price" must not score as "worth the price".
_NEGATORS = ("not ", "n't ", "never ", "hardly ", "rarely ", "no ")
_NEGATION_REACH = 24


def _negated(text: str, at: int) -> bool:
    """Whether a negator sits close enough before position ``at`` to invert it."""
    window = text[max(0, at - _NEGATION_REACH):at]
    return any(word in window for word in _NEGATORS)


def _score(text: str) -> float:
    total = 0.0
    for weight, phrases in _NEGATIVE:
        for phrase in phrases:
            if phrase in text:
                total -= weight
    for weight, phrases in _POSITIVE:
        for phrase in phrases:
            at = text.find(phrase)
            while at != -1:
                # A negated positive is not evidence of a recommendation, and
                # counting it cancels a genuine decline out to neutral.
                if not _negated(text, at):
                    total += weight
                    break
                at = text.find(phrase, at + 1)
    return total


def reads_as_recommendation(message: str) -> bool | None:
    """Does this seller message advocate buying?

    Returns True (buy), False (do not), or None when the text carries no usable
    signal — the caller decides what a silent message means rather than having a
    default smuggled in here.
    """
    if not isinstance(message, str):
        return None
    text = message.strip().lower()
    if not text:
        return None
    if text in ("yes", "y", "buy"):
        return True
    if text in ("no", "n", "pass"):
        return False

    parts = _CONTRAST.split(text)
    if len(parts) > 1:
        # Everything up to the final pivot is a concession; the last clause is
        # the position being argued for.
        score = _score(parts[-1]) + _PRE_CONTRAST_WEIGHT * sum(_score(p) for p in parts[:-1])
    else:
        score = _score(text)

    if score > 0.5:
        return True
    if score < -0.5:
        return False
    return None
