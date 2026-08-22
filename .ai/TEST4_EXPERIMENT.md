# Test 4 negotiation experiment v2 — OPEN CLAIM — 2026-08-23 00:24 IST

Supersedes the parameter-search config deployed 23:19, which ran ~1 hour and was
reverted before it produced a readable result. It was reverted deliberately: it
tuned parameters INSIDE the conceding regime that the rival evidence says is the
actual problem, and leaving it on would have confounded this test.

**Treatment: Test 4 only.** The other four agents are the control and remain
byte-identical to each other.

| knob | control | Test 4 |
|---|---|---|
| GLEE_NEGO_OPEN_CLAIM | (inert) | **0.95** |
| GLEE_NEGO_CLAIM_FLOOR | (inert) | **0.80** |

Everything else matches the control exactly.

## Why these numbers

From our own logs, complete-information games against ranked opponents, the share
of the ZOPA the proposer claims:

| opponent | nego | opens | ends |
|---|---|---|---|
| opus 5(4) | 2555.8 | 0.970 | 0.884 |
| Clod | 2355.4 | 0.958 | 0.816 |
| MACH2 | 2278.3 | 1.050 | 0.816 |
| Fortuna | 2258.1 | 0.970 | 0.929 |
| NegoMind-B | 2195.4 | 0.925 | 0.925 |
| **US** | **1994.5** | **0.681** | **0.581** |

Correlation between negotiation rating and opening claim: **+0.60** over 7 agents,
157 games. 0.95/0.80 places us inside the band every 2195+ agent occupies.

## ACTIVATION

The flags are read live via runtime_flags, but the CODE that reads them shipped at
00:21 and Test 4's process started at 23:06. The running process does not have it.
This arms at Test 4's next restart. Confirm by grepping its turns for the plan key
before treating any number as a read.

## PREDICTION, on the record

1. **Mechanism (high confidence).** Our mean claimed share in complete-info games
   rises from ~0.68 opening / ~0.58 closing to ~0.95 / ~0.80.
2. **Our share of closed deals** rises from ~0.35 toward 0.55+.
3. **Close rate FALLS.** Holding high must cost some deals; the rivals close less
   than we do and win anyway.
4. **Percentile: +0.02 to +0.06, with genuine risk of NEGATIVE.** This is a regime
   change, not a tuned parameter, and the clone could not screen it because we have
   never played this regime. I am less sure of the sign here than of 1-3.

## KILL RULE, fixed in advance

Revert if, at 150+ scoreable complete-info games, EITHER:
* mean percentile is negative with its CI excluding zero, OR
* close rate falls more than 20pp AND percentile is not positive.

A percentile gain bought purely by converting deals into zeros is not a gain, and
a close-rate collapse with nothing to show for it is the failure mode this design
is most exposed to.

## READ IT WITH

    python scripts/live_percentile.py --ab open-claim

which reports mean percentile AND close rate per arm. Note both flags share one
treatment bit, so this identifies the JOINT policy, not each flag separately.

Do NOT use Test 4's rating: 733 negotiation games against ~7,000 on the others,
and 9.1% of its displayed rating is still the 1000 starting anchor. Use percentile,
and read it as a difference-in-differences against the control mean.
