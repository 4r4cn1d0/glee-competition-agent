# LIVE EXPERIMENTS — pre-registered, 2026-08-22

Written BEFORE reading any result, so the decision rule cannot be rewritten to
fit whatever comes back. Both are randomised per GAME by a hash of its id, so
`scripts/live_percentile.py --ab` recovers the arm with the same pure function
and nothing logged can drift out of sync.

Read with:
    .venv/bin/python scripts/live_percentile.py --hours 24 --ab
    .venv/bin/python scripts/orphan_watch.py --hours 12      # sanity first

---

## 1. GLEE_NEGO_CLOSE_AB = 1.2  — the main event

**Hypothesis.** 72% of the remaining negotiation prize is hidden-information
games we fail to close, concentrated where our OWN factor says a deal probably
exists (0.8: close 64.5% against a 75% ceiling; 1.0: 41.4% against 50%). We
already know that at round one, and today we ignore it. Conceding faster ONLY in
those games should convert part of that gap without paying the price cost
everywhere else — which is why the unconditional test (-0.0166/-0.0182) does not
apply.

**Eligibility, measured:** 36% of negotiation games (hidden info + favourable
own draw). Fleet ~2,182/day → **~1,091 per arm per day**. Agent 5 alone
~344 per arm per day, so the fleet-wide read is the one that matters.

**Primary endpoint: CLOSE RATE in eligible games.** Binary, so it has far more
power than percentile, and it is the mechanism under test.
**Secondary endpoint: PERCENTILE in eligible games.** This is what actually
pays, and it is the one that can veto: closing more deals at ruinous prices is a
loss, not a win.

**Sample needed (80% power, 5% two-sided):**
| effect | games/arm | fleet time |
|---|---|---|
| close rate +7.5pp (64.5→72.0) | 604 | **~13 hours** |
| close rate +5.5pp (64.5→70.0) | 1,142 | ~25 hours |
| percentile +0.04 | 882 | ~19 hours |
| percentile +0.02 | 3,528 | ~3.2 days |

**RUN FOR 24 HOURS**, i.e. read at ~2026-08-22 21:00Z. That covers the
+7.5pp and +0.04 cases with room, and a full day averages over the diurnal
change in who is online — the opponent pool at 03:00Z is not the one at 15:00Z,
and a half-day read would confound the arm with the field.

**Decision rule, fixed in advance:**
- PROMOTE if close rate is up with its CI excluding zero AND percentile is not
  significantly negative.
- REJECT if percentile is significantly negative, whatever the close rate does.
  Closing more at worse prices is the failure mode this is most likely to have.
- STOP EARLY only if percentile in eligible games is worse by more than 0.05
  with n>400/arm — a real harm, not noise.
- If close rate moves and percentile does not, that is INFORMATIVE, not a win:
  it means the deals we gained were worth about what we paid for them.

---

## 2. GLEE_NEGO_ZOPA_AB = 0.10 — the smaller half

**Hypothesis.** Keep 90% of the visible zone instead of 61%. Measured +0.0121 in
the arena, then refuted, because the arena cannot price aggression: it bins on
`_price_bin` (0.1 of base) when the move is often smaller than one bin, consults
a survivorship-selected table first, and falls back at field_data.py:343 to
"profitable -> AcceptOffer", GRANTING any greedy ask it never observed. Live is
the only way to settle it.

**Endpoint: percentile in NEGOTIATION games.** Applies mostly where the zone is
visible, so it is diluted across all negotiation games rather than targeted.
**Sample:** the claimed +0.0121 needs ~2,400/arm; the fleet produces ~3,000/arm
per day. **Read at 24h with the same decision rule.**

**Prior:** genuinely uncertain. The mechanism evidence (384/384 closes below 90%
of span) came from one-round complete-info games where rejection pays the
opponent zero, which is the ultimatum payoff structure rather than a property of
the opponent, and it does not obviously generalise.

---

## What must be true for either read to mean anything

`orphan_watch.py` must be quiet. An abandoned game is scored at the 5th
percentile and never writes a result line, so a restart that strands games
silently poisons BOTH arms — and if it strands them unevenly it poisons the
comparison. Check abandonment before trusting any number here.

---

## 3. GLEE_PERS_KEEP_MSG = 1 — the persuasion message fix

**Defect (not a hypothesis).** dispatch.py recomposed `action["message"]` from
the template bank every turn, so in persuasion TEXT mode — where the message IS
the recommendation — the strategy's chosen wording was discarded and
`GLEE_PERS_MSG_STYLE` was inert. Armed on three agents, 0% of their messages
were the token form, 100% were prose.

**Baseline, seller p=0.8, 24h before the fix:**
| cell | mean | sd | n |
|---|---|---|---|
| TEXT (treated) | **0.3657** ±0.0293 | 0.2649 | 313 |
| BINARY (control, untouched by the flag) | 0.5368 ±0.0249 | 0.2374 | 348 |

Per agent in the text cell: Test 3 0.3228, Test 2 0.3860, **Test 1 0.3610**,
Agent 5 0.4310. Test 1 is second-worst, which is part of why its persuasion fell
2179 -> 1968, i.e. 211 below its own high.

**Design: difference-in-differences.** Binary-mode games in the same block are
untouched by the flag, so they measure field drift directly. A rise in text that
is really the whole field moving cannot be mistaken for the fix working.

**Read with:** `.venv/bin/python scripts/pers_cell.py --split <deploy_ts>`

**Success requires BOTH, per the operator's bar:**
1. **Mean up** — diff-in-diff positive with its CI excluding zero. The binary
   cell at 0.5368 is the natural target, since it is the same decision in a
   channel the buyers parse cleanly; that would be about +0.17 in this cell.
2. **Variance down** — sd in the treated cell must not RISE. A change that lifts
   the average while widening the spread is not a win: the rating is an average
   over games and a fat lower tail is exactly what produces the -80 swings.

**REJECT if** the diff-in-diff is negative, or the mean rises while sd rises
materially — that would mean we bought the average with a heavier tail.

**Then promote to Test 1**, which it already carries; the instruction is that if
it proves out, Test 1 is where it matters most. Expected there: persuasion 1968
-> the 2100s, which with barg 2240 and nego 2017 puts Test 1's overall near 2145
and makes it the fleet's strongest agent.

**Timing.** The seller p=0.8 text cell yields ~313 games/24h fleet-wide. To
resolve +0.17 needs only ~50/arm, so this is readable in HOURS, not a day —
much faster than either negotiation experiment. First read once ~100 post-fix
games exist in the cell.
