"""Regression tests for the seller-message parser (glee_agent/text.py).

Every string here is drawn from LIVE logged seller messages. The declines were
all being read as recommendations before 2026-08-21: the phrase table had
"not recommending" but not "not recommended", so the bare past participle
scored neutral, resolved to None, and the buyer's None-means-yes fallback
bought it. Measured across 20h of logs: 373 purchases of messages that
explicitly declined the sale, 373 of them low quality, 0 high.
"""
import sys, os
os.environ.setdefault('GLEE_PERS_PARSE_V2','1')  # the fix under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from glee_agent.text import reads_as_recommendation

DECLINES = [
    "Not recommended.", "not recommended",
    "I do not recommend buying this product.",
    "I'd skip this one. I only push units that are worth it.",
    "Straight answer: this one is not worth what I am asking.",
    "Skip this one. Yes, I lose a sale by saying that.",
    "recommend skipping this one", "recommend passing on this",
    "I am advising you to skip", "not asking you to buy",
    "save your cash", "save your money", "sit this round out",
    "I would hold off on this one",
]
BUYS = [
    "Recommended.", "I recommend it.", "BUY - strong unit",
    "This is one of the strongest products I've offered you.",
    "Strong unit this round - I would buy it.",
    "This one is worth taking.", "yes",
]

def main() -> int:
    bad = 0
    for m in DECLINES:
        if reads_as_recommendation(m) is not False:
            print(f"FAIL decline read as {reads_as_recommendation(m)}: {m!r}"); bad += 1
    for m in BUYS:
        if reads_as_recommendation(m) is not True:
            print(f"FAIL buy read as {reads_as_recommendation(m)}: {m!r}"); bad += 1
    print(f"parser regression: {len(DECLINES)} declines + {len(BUYS)} buys, {bad} failures")
    return 1 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main())
