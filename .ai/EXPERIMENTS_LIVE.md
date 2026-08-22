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

## GLEE_BARG_NO_REGRESS  (Test 1/2/3, deployed 2026-08-22)

Guard, not a policy retune: before a reject, project the actual next-turn offer
through bargaining.decide() and accept the standing offer instead if the
projected counter is no better than it. Measured basis: 9 games rejected an
offer then countered with the same or less and were accepted, -44.9 rating
strictly forfeited.

WINDOW. The analysis window opens at the FIRST turn whose plan carries the
`no_regress` key, NOT at the arms.json write. Flag-gated code lands inert and
only becomes live when the agent next loads it, so the two differ by up to one
rotation. Recovered arm assignment intersected with the wrong window is what
made GLEE_PERS_BACKLOAD_AB read as null for nine hours while it was losing
0.391 percentile per game.

REVISED 2026-08-22, after measuring the base rate. The regression this guard
catches occurs in 0.45% of bargaining games (47 of 10,529 over 48h, 4 agents).
On Test 2 + Test 3 that is ~12 fires a day, so the original 400-fire decision
point needs 33 days and is unreachable before the Aug 29 close.

It does not need a powered A/B. Accepting an offer at least as good as the
counter you were about to make -- one round earlier and undiscounted --
DOMINATES making that counter. That is a theorem, not a hypothesis, and the
measured 47 cases give up a mean 5.26 pot-points with the opponent accepting
the weaker ask 85% of the time; the worst rejects an offer worth 0.950 of the
pot and then asks 0.610.

What must be checked instead is PROJECTION FIDELITY: does the offer the guard
projects equal the offer actually made next turn? Verify by replaying logged
games where the guard evaluated and comparing its `planned_counter_share`
against our real next offer. Any mismatch is a correctness bug, not a result.
KILL only on a projection mismatch or a latency regression.

SUPERSEDED rule (kept for the record) -- DECISION at 400 fired games:
  * SHIP to Agent 5 if mean percentile delta CI excludes zero and is positive.
  * KILL if the CI excludes zero and is negative.
  * KILL if fires < 40, i.e. the guard is too rare to pay for its risk.
  * Otherwise extend once to 800, then kill if still unresolved.
This flag cannot be judged on rating drift; use scripts/live_percentile.py.

## GLEE_BARG_MSG  (Test 1/2/3, deployed 2026-08-22)

Four arms by sha256("barg_msg|"+game_id) mod 4. B0 is SILENT and is the control,
because silence is what the fleet does today -- 0 messages sent across 1,851
offer turns while opponents sent text on 1,583 of 1,830. B1-B3 are length-matched
at 299-301 chars so register is not confounded with verbosity.

Rating impact is UNMEASURED. Only reachability was measured. This ships as an
experiment and must never be defaulted on without clearing the rule below.

DECISION at 600 message-enabled games per arm:
  * PRIMARY: B0 vs pooled B1/B2/B3 mean percentile. Ship text only if the CI
    excludes zero and is positive.
  * The B1/B2/B3 contrasts are EXPLORATORY. A winning register among them is a
    hypothesis for a fresh randomisation, never a deployment -- picking the best
    of three post hoc is the same error that made the persuasion closer-phrase
    table meaningless.
  * KILL on any evidence of timeout or latency regression; the bank is local and
    must cost nothing.

## GLEE_NEGO_RANK_PRICE_AB  (Test 1/2/3, deployed 2026-08-22)

Terminal price chosen to maximise A(P)*F(payoff) + (1-A(P))*F(0) over acceptance
-curve bin midpoints, rather than to maximise expected money. Rationale: the
score is a percentile, 51% of live negotiation outcomes sit on the $0 atom, and
E[F(X)] != F(E[X]) -- so the money-maximising price is not the rank-maximising
price. Thin cells below 30 observations fall back to the existing pricing.

DECISION at 1,000 games per arm:
  * SHIP to Agent 5 if the percentile CI excludes zero and is positive.
  * KILL if negative, or if close rate drops more than 3pp with no percentile
    gain -- a rank gain bought purely by abandoning deals is the failure mode
    this design is most exposed to.
  * Report zero-rate alongside; it is the percentile-relevant column.
