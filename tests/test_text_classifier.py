"""Regression tests for reading seller messages.

The corpus here is real: every string was played against us in live competition
games. The previous keyword blacklist scored 74% on it and, worse, misread 88%
of honest warnings as recommendations — which is the direction that hurts, since
each error teaches the buyer that a truthful seller lied.
"""

from __future__ import annotations

import pytest

from glee_agent.text import reads_as_recommendation

# (message, advocates_buying) — hand-labelled from live play.
DECLINES = [
    "I would hold off on this one.",
    "This unit is below our usual quality this round.",
    "I'll be straight with you — this one isn't my best unit. You may want to pass today.",
    "Ordinary unit this round. Still available at the same price.",
    "Honestly, today's product is not up to my usual standard. I'd understand if you sit this round out.",
    "I'd hold off this round, not a strong one.",
    "This one is low quality. It is not worth the price. Do not buy it.",
    "I'll be straight with you: I don't think this one is worth it for you. I'd rather skip a sale than lose your trust — pass on this round.",
    "Being straight with you: I'd pass on this one.",
    "Not this round. Better to wait for a better one.",
    "I do not recommend buying this product.",
    "I'll be straight with you — this one isn't up to the standard of my better stock. I'd hold out for the next one.",
    "Honestly, pass on this one. I would rather keep your trust than make one sale.",
    "Not this round. Wait for a better unit.",
    "I would not prioritize this product in this round.",
    "I do not recommend this one. I'd pass.",
    "Not this one — I don't recommend buying it.",
    "I would sit this round out if I were you. Not every unit is worth the price.",
    "Not my strongest item this round. Your call, but I wouldn't push it.",
    "Honestly, I'd pass on this particular unit. I'd rather keep your trust than push something I'm lukewarm about.",
    "Do not buy this one. Wait for the next.",
    "I would pass on this round. Not recommending it. (You have bought 2 on my say-so; 2 were high.)",
]

RECOMMENDS = [
    "I recommend this one.",
    "This is a good one. Take it. My record here speaks for itself.",
    "Strong unit this round. Recommending it without reservation. My record here speaks for itself.",
    "This unit is high quality -- recommended.",
    "This one is worth your money -- I would buy it myself at this price.",
    "Good unit this round. Worth taking at the asking price.",
    "Recommended.",
    "This one's genuinely strong this round, I'd buy it. Clear value here.",
    "Solid pick this round, honestly. Worth it.",
    "I can recommend this one without reservation: it's a high-quality unit and worth the price. I'd buy it.",
    "Today's unit is the real thing — high quality, and I'll stand behind that. At this price, buying is the right call.",
    "I recommend buying this product.",
    "Another high-quality unit this round, definitely a good buy at this price.",
    "Strong recommendation on this unit. It's exactly the sort of item that makes the price worth paying.",
    "THIS IS HIGHEST QUALITY",
    "clear buy at this price",
    "I recommend buying this round. Judge this signal by the realized outcomes of prior purchases.",
]

# The concession-then-pivot shape: a naive negative-word match reads these
# backwards, because the reassurance about the buyer's scepticism precedes the
# actual recommendation.
CONTRASTIVE_RECOMMENDS = [
    "I know last round's product wasn't what you hoped for, but this one is a much better deal, I promise!",
    "I know it's been a really rough streak for you, and I wouldn't blame you for being skeptical, "
    "but this product is genuinely high quality. I hope you'll consider it.",
    "I understand your hesitation after the last two rounds, but I assure you this product is a solid purchase.",
    "I know it's hard to believe given the history, but this product is a good deal for you today.",
    "It's been a tough game for both of us, but this product is genuinely high quality. "
    "Let's make this last high-quality one count!",
]


@pytest.mark.parametrize("message", DECLINES)
def test_declines_are_not_read_as_recommendations(message):
    assert reads_as_recommendation(message) is False, message


@pytest.mark.parametrize("message", RECOMMENDS + CONTRASTIVE_RECOMMENDS)
def test_recommendations_are_read_as_such(message):
    assert reads_as_recommendation(message) is True, message


def test_binary_mode_passes_through():
    assert reads_as_recommendation("yes") is True
    assert reads_as_recommendation("no") is False


def test_no_signal_is_reported_rather_than_guessed():
    # The caller decides what silence means; a default must not be smuggled in.
    assert reads_as_recommendation("") is None
    assert reads_as_recommendation("BOIIIII") is None
    assert reads_as_recommendation(None) is None


def test_our_own_templates_round_trip():
    """We generate these. Misreading our own output is how the old blacklist
    turned 274 honest warnings into recorded lies."""
    from glee_agent import messages
    import random
    rng = random.Random(0)
    for _ in range(40):
        decline = messages.persuasion_message(
            {"game_family": "persuasion", "game_state": {}},
            {}, {"recommend": False, "round": 3, "total_rounds": 10,
                 "reason": "lie budget", "quality_is_high": False}, rng)
        assert reads_as_recommendation(decline) is False, decline
