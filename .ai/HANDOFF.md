# HANDOFF — Claude ↔ Codex

Append-only. Newest at the top. Each entry: what changed, what was measured,
what is contested.

## 2026-08-27 18:49 IST — Agent 5 activity defense complete; banked after exact bargaining cushion

The operator authorized whatever lossless play was needed to keep Agent 5 clear
of the official activity penalties.  The authenticated pre-defense boundary was
`16:45 IST`: bargaining `2637.44/15,348`, negotiation `2823.94/15,272`, and
persuasion `2314.94/15,343`.  The first all-family defense cohort used physical
slot `composite`, hardliner, LLM off, and its locked deterministic overlay.  It
was drained through `scripts/fleet.py` only.  A later supervisor relaunch briefly
used the then-configured bargaining+persuasion next topology and added 15
persuasion games before a lossless bank; this was not treated as bargaining
evidence.  The remainder ran bargaining-only through clean zero-game watchdog
replacements.  No strategy flag, `.env`, manual JSON edit, Test 4 state, or
other slot was changed.  The Agent 5 overlay stayed exactly
`759831b1fffae74225d5a6acf1e88493ba6d0d9dfa22db4afbf66d21f3852a7a`.

All 79 games assigned after the boundary were retained and have terminal files:
bargaining was 20/20 agreements (8 P1, 12 P2); negotiation was 9 agreements,
8 no-deals, and 5 walk-aways (8 P1, 14 P2); persuasion was 37 completed games
(18 P1, 19 P2).  There are zero missing finals, timeouts, invalids,
abandonments, or unresolved games in this cohort.  The exact authenticated
post-defense state is bargaining `2658.47/15,368`, negotiation
`2790.16/15,294`, and persuasion `2285.52/15,380`: rating changes of `+21.03`,
`-33.78`, and `-29.42`, respectively.  Overall therefore moved from about
`2592.11` to `2578.05`; this cost is retained rather than hidden by conditioning
on bargaining or agreements.

At `18:46:13 IST`, finalized bargaining plus the sole in-flight bargaining game
first covered the exact `15,368` target.  One `scripts/fleet.py bank composite`
request stopped new acquisition and let that game finish.  It agreed, raised
bargaining to `2658.47`, and PID `8693` exited; the supervisor recorded the slot
down at `18:46:32`.  Authenticated active games are zero, `fleet.py status`
reports `composite BANKED`, and there is no composite runner.  Only the NEXT
launch topology was restored to `bargaining,persuasion`; negotiation remains
excluded and the slot remains disabled/banked.  Do not start it merely because
the next-family string is restored.

Conservative first-sample-after-cutoff activity is now B/N/P `20/22/37` over
24h and `869/836/923` over 48h.  That clears the official 10/day rule by
`+10/+12/+27`, the project 15/day safety buffer by `+5/+7/+22`, the official
100/48h rule by `+769/+736/+823`, and the 115/48h safety buffer by
`+754/+721/+808`.  The earliest projected next crossing is negotiation around
`2026-08-28 16:40:37 IST` (48h stepping to 98), followed by its 24h count near
`16:42:49` (stepping to 9).  Ratings-history cadence adds up to about ten
minutes of uncertainty, so begin the next defense materially before `16:30 IST`.

Queue diagnosis is observational but concrete.  Between `17:33:12` and
`17:46:52`, Test 4 acquired 15 bargaining games while Agent 5 acquired one;
Agent 5 nevertheless had the exact bargaining-only command, successful API
polling, no cooldown, 403, 429, 5xx, transport error, or fleet fence.  The SDK
re-posts its idempotent queue entry every 15 seconds, yet the documented
30-second baseline fallback was not observed.  There is no read-only queue
membership endpoint, so a stale/low-priority backend entry cannot be separated
from undocumented suitability/rating scheduling.  Strategy cannot cause this
because it runs only after assignment.  Do not alter Test 4 or add another
Agent 5 family as a speculative bargaining fix; another active family can
suppress baseline fallback.  Preserve these timestamps for a platform-support
escalation if the next Agent 5 defense is similarly sparse.

## 2026-08-27 03:05 IST — current-stack bargaining veto; recoverable seller repair implemented inert

The apparent bargaining high-share hole is now **rejected**, not implemented.
The permitted P2 / disclosed-H12 / `delta_2=.95` / messages-off cell is already
owned before generic bargaining by `bargaining_p2_commitment.action()`.  In the
current component stack there were 46 exact first triggers: 45 joined plus one
unresolved, all 45 joined games later agreed, and accepting the `.45-.50`
standing offer early was worse in all `45/45` by a mean `21.47` pot points.
Test 2 was `12/12` worse and Agent 5 `14/14` worse.  This directly supersedes
the older pre-component `35/0` post-hoc signal.  Do not create a standalone V2
or revive the broad parent.  At a future deployment-owned clean boundary, the
misleading but unreachable `GLEE_BARG_HIGH_SHARE_DELAY_GUARD=1` should be set
explicit zero; Codex made no fleet write here.

The original default-OFF persuasion candidate
`GLEE_PERS_SELLER_DEMAND_COLLAPSE_TRUTH_V1` is also abandoned before exposure.
Its cumulative all-round buy rate counted the repair's own LOW/NO passes, so it
could reinforce itself and permanently suppress LOW recommendations.  The
historical flag is now deliberately inert and only fences newer seller work.
It was not silently redefined.

The working tree instead contains the new default-OFF deterministic
`GLEE_PERS_SELLER_POSITIVE_PASS_STREAK_TRUTH_V1`.  It runs the complete seller
baseline first and can change only an ordinary known-value all-push LOW
`YES -> NO` before round 20 when the three most recent explicit positive
recommendations were all passed.  Exact NO/pass rows are ignored; the first
later purchased YES immediately resets the streak and restores the original
all-push policy.  Binary history uses the strict binary parser; token-text
history requires literal `yes`/`no`.  Ordered completed history, buyer-decision
consistency, role/phase/knowledge metadata, finite values, `u < price`, prior
EV at least price, token/KEEP/LLM-off wire settings, and every seller-policy
conflict all fail closed.  A firing changes only the wire, `recommend`,
`reason`, `lie_rate`, and adds one marker plus sole gate
`pers_seller_positive_pass_streak_truth_v1`; nonfires are byte-identical.

Corrected both-mode all-assignment audit: Agent 5 had 1,432 seller assignments
(1,253 joined, 179 unresolved); the streak reached 668 LOW turns in 109 games,
with `8/664` observed target LOWs selling.  Test 2 had 644 assignments (625
joined, 19 unresolved); it reached 359 turns in 59 games, with `3/359` selling.
This is action-selected mechanism motivation only.  It cannot identify restored
future conversion or official rating lift.  Focused safety/interaction tests
pass `172/172`; persuasion-wide tests pass `708/708`; the full suite is `2,787
passed / 3 failed`, with exactly the declared bargaining horizon-floor and
bargaining/negotiation live-grid drift failures.  Exact Test 2 stack
reachability over 800 games is
`eligible=fired=action_changed=365/365/365`.  An independent adversarial review
returned PASS after malformed text/metadata leaks were closed.  Agent 5 and all
live fleet state remain untouched; fresh explicit authorization and a clean
deployment-owner boundary are required for any Test 2 challenger.

## 2026-08-27 02:10 IST — terminal push rolled back; next B/P holes audited

The operator ended Test 2's persuasion `seller-terminal-push-v1` challenger.
At `T1=1787776198.0249655`, one supported `scripts/fleet.py set hardliner`
write changed only `GLEE_PERS_SELLER_TERMINAL_PUSH_V1` from `1` to explicit
`0`.  Test 2's non-persuasion hash, `control.json`, Agent 5 and every other
slot remained byte-identical; every persuasion `*_AB` key remains zero.  The
121-assignment pre-T1 cohort contained 19 clean firings but was far below the
precommitted efficacy boundary, so it is operator-terminated without a
promotion or rejection verdict.

The strongest current bargaining code/configuration hole is that
`GLEE_BARG_HIGH_SHARE_DELAY_GUARD=1` on Test 2 and Agent 5 is unreachable:
the code also requires `GLEE_BARG_DISCOUNT_NO_REGRESS=1`, while that broad
parent is correctly `0` after the human scope correction.  Do not revive the
parent.  A future default-OFF standalone V2 should preserve only the existing
discounted `.45-.50` current-high-water predicate, three provenance-checked
opponent offers, and all conflict fences.  Frozen evidence was 35 wins/zero
losses with a maximally adverse unresolved bound still positive; fresh
current-stack replay reached 24 Test 2 games (22 joined, 18 better/4 worse,
`+.0617` pot per joined trigger) and 45 Agent 5 games (44 joined, 40/4,
`+.0855`).  The cutoff is post-hoc and accept-now is compared with a trajectory
generated under rejection, so this is a prospective challenger hypothesis,
not a causal promotion.  The higher-risk secondary hole is Bob's unknown-
horizon fitted-offer exit cliff: `best_ask()` returning `None` abruptly hands
control to the much lower quadratic glide.  It appeared in 34/1,200 Test 2 and
25/1,200 Agent 5 assignments, but the observed low accepted offers are heavily
selected; holding the prior ask may turn them into zeros.

The strongest next persuasion hypothesis is the existing default-OFF
`GLEE_PERS_SELLER_DEMAND_COLLAPSE_TRUTH_V1`.  Agent 5's complete joined cohort
has 1,432 seller assignments.  In 94 games its exact predicate reached 660
known-LOW all-push recommendations after cumulative demand fell below 50%; only
15/660 sold.  In 38 games a buyer stopped entirely after buying a recommended
LOW, leaving 378 later HIGH items unsold.  The fresh Test 2 reset-era seller
stream reproduced the pattern: 264 exact turns in 42 games, only 4/264 sold,
and 233 later HIGH items missed after 21 buyers stopped.  This supports a broad
trust-preservation test—LOW becomes `no` only after collapse, HIGH stays
`yes`—but cannot prove restored future conversion because the trigger and
purchases are action-selected and the opponent may never resume.  Test it
alone, prospectively, over every assigned seller game using official
same-role/configuration evidence.

The lower-risk, lower-reach persuasion hole is strict warning prose that the
legacy fallback still treats as positive.  Agent 5 bought 40 such V1-missed
warnings across 21 games; all 40 revealed LOW and zero HIGH.  Existing
default-OFF V2/V3 only convert those direct-warning BUYs to PASS.  This is a
semantic repair, not yet an efficacy result, and its roughly 2.3% assignment
reach cannot plausibly supply the full rating target alone.  Do not add another
buyer-unlock layer: Test 2's current reset had 27/42 affected PASS-to-BUY games
negative.  Also keep retired broad bargaining floor releases, persuasion
backloading, LLM prose, blanket selectivity/LCB, and rank gates off.

## 2026-08-26 23:17 IST — Test 4 negotiation frozen at 2914.38

The operator directed `test 4 stop negotiation`. At the authenticated boundary,
Test 4 / physical slot `randomized` was PID `52607`, hardliner policy, LLM off,
all three families, with eight active games. Negotiation was `2914.38/10,421`.
Codex set only the next-launch family list to `bargaining,persuasion` and used
the SDK-native manual bank at `ts=1787766144.420578`. The runner stopped queue
acquisition, drained active games `8 -> 3 -> 2 -> 1 -> 0`, and negotiation
remained exactly `2914.38/10,421` throughout. PID `52607` exited naturally and
the supervisor left the banked slot down at 23:16:34; no process was signaled
and no game was abandoned.

After authenticated zero and process exit, Codex re-enabled only Test 4.
Replacement PID `53923` launched at 23:17:05 with the verified command
`--probe hardliner --families bargaining,persuasion --llm-mode off`, concurrency
eight and a 3,600-second bound. Its first seven logged turns comprise five
bargaining and two persuasion turns, with zero negotiation turns. A subsequent
authenticated read still showed negotiation `2914.38/10,421`. Test 4's strategy
flags were preserved but are dormant for negotiation because that family is no
longer queued. No other slot or strategy configuration was changed.

## 2026-08-26 18:49 IST — Test 4 V3/one-cent negotiation successor ready

The new default-OFF whole-policy selector is
`GLEE_NEGO_TEST4_HOTFIX_V1`. It is a strict successor to Test 2 support V3:
hidden unknown- and cap-10 seller asks stay inside the official four-value
support; hidden cap-10 terminal buyers retain the absolute `seller+$0.01`
support bid; all V1 first-principles cent cells and the observed-leader buyer
matrix remain. The selector additionally folds in only two pointwise-dominant
repairs: a copied hidden/unknown buyer `WalkAway` becomes `AcceptOffer` when the
standing offer leaves at least one cent, and a buyer Reject/Walk becomes Accept
at the observed round-99 terminal node when it leaves at least one cent. The
measured-negative broad hidden accept-all-profitable policy is not revived.

Evidence retained all outcomes. V3's cap-10 repricing was motivated by seven
fresh seller games whose opening asks all exceeded the largest possible buyer;
four agreed, two no-dealed, and one walked, with two crumb agreements scoring
`-5.7/-6.3`. Exact cent offers were accepted `39/40` in retained terminal
records, so an initially proposed deterministic round-9 fallback from one
exceptional failure was rejected by the red team and removed. The hidden
Walk-to-Accept repair is payoff-dominant because Walk pays zero. Round 99 is
terminal in `1,225/1,225` observed games reaching it, making profitable Accept
payoff-dominant there. The post-hoc round-97 guard remains its own independent
flag and is not implied by the selector.

Two independent post-diff red-team reviewers returned PASS after the round-9
rule was removed and round 97 was decoupled. Focused negotiation tests pass
`919/919`; the complete suite is `2,690 passed / 3 failed`, with exactly the
pre-existing bargaining horizon-floor expectation and bargaining/negotiation
live-grid drift alarms. Exact Test 4 physical-stack reachability using its live
`hardliner` wrapper passes `7,004 eligible / 7,004 fired / 1,520 submitted
actions changed` over 600 games; representative seller asks move
`317.65 -> 119.99` and `47,647.20 -> 14,999.99`.

Commit `cd5b6ee0f433cbe96e519e6a7993b7d240288b41` is pushed to
`origin/main` and the successor is live only on Test 4. The new selector was
armed at 18:50:01 IST while old PID `22195` continued on V1; it stopped taking
new work at its normal one-hour boundary, completed every held game, and exited
cleanly at 19:06:46 after a 4,083-second shift. Replacement PID `39161` launched
at 19:06:57 as the same `hardliner` wrapper, all three families, LLM off,
concurrency eight. A live negotiation at `ts=1787751425.8028271` recorded
`plan.source=test4_hotfix_v1` and gate `test4_hotfix_v1`. Only then was Test 4's
superseded `GLEE_NEGO_AGENT5_DEFAULT_V1` set to zero; a later negotiation at
`ts=1787751458.433494` still recorded and fired `test4_hotfix_v1`, proving the
live overlay transition. The independent round-97 flag remains one. The launch
baseline read was negotiation `2738.20/9,917`, bargaining `2648.85/10,265`, and
persuasion `2348.04/10,913`. No other slot was promoted, and Test 4's bargaining
or persuasion configuration was not changed.

The first three successor negotiation completions moved the live rating to
`2729.38/9,920`, but they do not identify a policy regression. Two were duplicate
hidden one-round buyer/P2 cells with own value `1,000,000` and a sole incoming
ask of `1,196,000`; both correctly rejected because no profitable action or
counterturn existed. The third was hidden one-round seller/P1 with own value
`100`; the corrected support ask was exactly `119.99` and the hidden buyer walked.
Thus the first two zeros were action-forced and the third used the human-supplied
one-cent/support rule. Keep all three in subsequent all-outcome rollout analysis.

## 2026-08-26 16:39 IST — Test 4 round-97 low-share negotiation guard live

Commit `9dab12127dab33e3eeca6c38826901cd11a187b2` is pushed to
`origin/main`. It adds default-OFF deterministic flag
`GLEE_NEGO_COMPLETE_UNKNOWN_R97_LOW_SHARE_ACCEPT_V1`. The server labels the
seller/P1 offer as round 97; rejecting it emits buyer/P2's round-98 counter and
leaves seller/P1 the final response on round 99. When armed, the guard changes
only a canonical complete-information, explicitly unknown-horizon buyer/P2
`RejectOffer` at exactly round 97 to `AcceptOffer`. It requires ten fully
completed exact mutual-stasis cycles, a provenance-valid standing seller offer,
a buyer gain of at least $0.01, and a buyer gain no greater than 20% of the
visible ZOPA. Hidden games, known horizons, sellers, other rounds, changing
prices, accepts, walks, malformed actions, and the older broad stasis flag are
fail-closed. Its cycle constant is independent from the older guard's constant.

The all-outcome audit covered 3,572 unknown-horizon negotiations reaching round
98/99. Seller opponents rejected our buyer/P2 round-98 counter in 1,555/1,607
games (96.8%); under complete information with a strictly profitable counter,
they still rejected 136/186 (73.1%). In the post-hoc ten-cycle subset where the
standing offer gave the buyer at most 20% of visible ZOPA, accepting at the
round-97 decision beat observed continuation in 86/88 games, lost in 1, and tied
in 1. The diagnostic exact-percentile delta was `+.06709`, normal 95% CI
`[.04738, .08679]`. This is a retrospective reached-state comparison across
policy eras, not a randomized causal estimate; no official rating lift should
be claimed until live fires and terminal outcomes accumulate. The supplied
631-game value matrix mixes complete and hidden information and must not be used
as a hidden-value prior; the official hidden generator remains independent
uniform support over `{.8, 1.0, 1.2, 1.5}`.

Focused guard tests pass 42/42; the four adjacent endgame-guard files pass
133/133. Exact Test 4 hardliner-stack reachability at n=256, seed 97020 is
10 eligible / 10 fired / 10 submitted actions changed, all at round 97. The
final full suite is 2,595 passed with exactly the same three pre-existing
failures: the stale bargaining horizon-floor assertion and the bargaining and
negotiation live-log grid drift alarms. Compilation and `git diff --check`
pass. No replay-eval, arena, or red-team job ran.

The operator explicitly unfroze Test 4 negotiation for this rollout while
retaining the bargaining freeze. Test 4's predeployment state was bargaining
`2684.18/10186`, negotiation `2724.71/9738`, and persuasion `2347.04/10740`.
Codex used `fleet.py bank randomized`; old persuasion-only PID `10380` stopped
queue acquisition, drained authenticated active games `6 -> 0`, and exited
without a signal or abandonment. Only at the zero-process boundary did fleet
tooling set the new flag to `1` and set next-launch families to
`negotiation,persuasion`. The prior Agent-5 V1 negotiation component and live
persuasion V2+V3 flags were preserved; the older broad complete-unknown stasis
flag remains absent. The resulting 83-key Test 4 overlay SHA-256 is
`f1073619a8c00a304fc26b6721459f4f22c9d9064cb18bcbff4c184a6a402f77`.

Replacement PID `12959` launched at 16:37:06 IST from the pushed workspace as
`--probe hardliner --families negotiation,persuasion --llm-mode off`, concurrency
8, max time 3,600 seconds. Runtime inspection confirms the new flag `1`, Agent
5 V1 `1`, persuasion V2/V3 `1`, and no old broad stasis flag. The first 31 live
turns include six negotiation turns across three games, all `source=heuristic`,
with zero malformed actions or strategy errors. The rare round-97 gate has not
yet fired. Bargaining remained exactly frozen at 10,186 games while negotiation
advanced to 9,740. No other slot, agent, bargaining behavior, or persuasion
flag was changed by this negotiation rollout.

## 2026-08-26 16:16 IST — Test 4 V2+V3 live after clean restart

The operator explicitly authorized restarting Test 4. Codex used the supported
SDK-native bank so PID `5532` stopped acquisition, finished all seven held
persuasion games, reached authenticated zero/zero, and exited without any
abandonment or signal. At the stable no-process boundary, one fleet write set
only Test 4 persuasion V2=1 and V3=1 at `Tcfg=1787741035`; exact reversal
reproduces the full pre-write arms hash. Replacement PID `10380` launched at
16:14:42 as hardliner, persuasion-only, LLM off. Agent 5, other slots, every
non-persuasion key, prose/truth, unlock/seller repair, and every A/B flag stayed
unchanged. The first post-launch turns are clean; first-20-per-gate exact replay
is now active under `.ai/EXPERIMENTS.md`.

## 2026-08-26 15:42 IST — Test 4 direct-decline repair authorized, not yet live

The operator authorized a Test-4-only deterministic V2+V3 buyer direct-decline
repair after the log review. Existing code is already pushed/default OFF and
passes focused tests and exact Test 4 hardliner-stack reachability. Agent 5 and
all non-persuasion behavior remain outside scope. Test 4 PID `1184` still had
live persuasion games at the predeployment audit, so no flag or process action
was taken. The complete frozen experiment rule and clean-boundary instructions
are at the top of `.ai/EXPERIMENTS.md` and `.ai/PERSUASION_HANDOFF.md`.
PID `1184` later drained cleanly to zero at 15:47:58 and exited, but no fleet
write occurred before successor PID `5532` acquired games at 15:49:57. V2/V3
therefore remain OFF; wait for PID `5532`'s next natural zero-game boundary.
The bounded PID-1184 terminal join is complete: 173/173 unique persuasion games
(79 seller, 94 buyer, 55 exact-zero own outcomes), 3,460 turns, and zero missing,
nonterminal, wrong-family, or malformed records. Its sorted-newline game-ID
SHA-256 is
`0f276b43c625a04134a0ffc4bc67fb0e6557ec541a95fc2e52becf7b7d0f42bd`.

## 2026-08-26 12:54 IST — Test 4 bargaining and negotiation frozen

The operator directed: "freeze test 4 bargaining and negotiation." At the
authenticated pre-change boundary, physical slot `randomized` / Test 4 was PID
`95548`, policy `hardliner`, LLM off, and already excluded negotiation; it was
still playing bargaining and persuasion with six active games. The exact
family state was bargaining `2680.04/10184`, negotiation `2724.71/9738`, and
persuasion `2350.49/10178`.

Codex used only repository fleet tooling to set the next-launch families to
`persuasion`, then requested the runner's SDK-native lossless bank. PID `95548`
stopped queueing new games, completed all six in-flight outcomes, reached
authenticated `active_games=0`, and exited naturally at `12:53:24 IST`. No
process was killed or interrupted and no game was abandoned. The exact frozen
post-drain ratings/counts are bargaining **`2684.18/10186`** and negotiation
**`2724.71/9738`**; persuasion was `2355.84/10184`.

Only after PID `95548` disappeared from the process table did Codex re-enable
the slot. Replacement PID `97052` launched at `12:54:04 IST` with the verified
command `--families persuasion`, the same hardliner policy, LLM off,
concurrency eight, and a 3,600-second bound. The first post-launch read had two
active games while bargaining and negotiation counts remained exactly
`10186`/`9738`. Test 4 must remain persuasion-only unless the operator
explicitly unfreezes a family. No strategy flags, Agent 5 controls, or other
slots were changed. Agent 5 had independently already completed its previously
armed negotiation-2720 bank before this request.

## 2026-08-26 11:28 IST — Agent 5 family-only 2720 negotiation bank is live

Codex implemented, reviewed, committed, pushed, and deployed authenticated
per-family peak banking in commit
`00cf4a5027e84a0b5a8f0ef2b84a786cec8ecdb1`. The focused control/watcher suite
passed `48/48`; the full suite passed `2553` tests with only the three known
pre-existing failures (the bargaining horizon-floor assertion and the
bargaining/negotiation live-grid drift alarms). Two review findings were fixed
before deployment: clean watcher shutdown can no longer be swallowed by the
poll loop, and a wrong trigger-removal command now refuses instead of falsely
claiming success.

With no eligible rating trigger armed, repository tooling reloaded only the
minute watcher from old PID `63596` to PID `94819`; the replacement singleton
advertises `family-peak-v1`. All five competition-agent PIDs remained unchanged,
including Agent 5 PID `93204`, so no game process, supervisor, queue, or strategy
was interrupted. Fleet tooling then armed exactly
`bank_family_thresholds.composite={"family":"negotiation","threshold":2720.0}`.
There is no Agent 5 overall threshold, disabled request, drain request, or bank
latch. The watcher recorded `poll ok (armed=1)` at `11:28:09 IST`.

The post-arm authenticated read kept Agent 5 live on all three families with
seven active games: bargaining `2460.07/15106`, negotiation `2672.03/15064`,
and persuasion `2392.22/15065`. The exact strategy overlay remains unchanged at
SHA-256 `94bb689c645ec743406c64c3570b1b8e10e7d2778050ec0ca98950a3201e38b6`.
The sole automatic stop condition is now the first fresh authenticated Agent 5
**negotiation rating >=2720.00**. Overall rating, rank, bargaining, persuasion,
and the historical 2505 crossing must never substitute for it. On a qualifying
sample the watcher atomically requests the existing SDK-native lossless drain;
the runner stops queueing new games, finishes every in-flight game, and stays
down.

## 2026-08-26 11:06 IST — operator resumed Agent 5; only negotiation 2720 may bank it

The operator explicitly superseded the overall-2505 peak lock: "let agent 5
take games again, dont stop it from taking games unless the negotiation reaches
2720+." The prior lossless drain had completed server-side with
`active_games=0`; PID `86125` then exited naturally at `11:05:56` and the
supervisor left physical slot `composite` down. No process was signalled and no
game was abandoned.

Only after the old PID was fully down, Codex used safe fleet tooling to remove
the obsolete authenticated-overall threshold (`fleet.py peak-off composite`)
and re-enable the slot (`fleet.py start composite`). Control now contains no
Agent 5 overall threshold, no Agent 5 bank latch, and no Agent 5 drain/disabled
request. Replacement PID `93204` launched at `11:06:56` on the unchanged
78-key overlay SHA-256
`94bb689c645ec743406c64c3570b1b8e10e7d2778050ec0ca98950a3201e38b6`, policy
`hardliner`, all three families, LLM off, concurrency eight, and a 3,600-second
shift. It immediately resumed play; the first verified read had four active
games. Authenticated family state was bargaining `2468.47/15057`, negotiation
`2663.29/15015`, and persuasion `2406.19/15017`, so the new trigger had not
fired.

Effective immediately, **do not bank Agent 5 for overall rating, rank,
bargaining, persuasion, or the historical 2505 observation.** Its sole
rating-triggered bank condition is the first fresh authenticated
**negotiation-family rating >=2720.00**. A family-specific one-minute watcher
extension is being implemented and tested; until it is armed, monitoring must
apply the same exact family-only condition and must never substitute overall.
When it fires, preserve the exact authenticated negotiation observation and use
only the repository's lossless bank path.

## 2026-08-26 10:43 IST — Agent 5 crossed 2505; lossless peak bank requested

The first fresh authenticated overall-board observation in this monitoring run
put physical slot `composite` / Agent 5 at **2513.66 overall** at
`2026-08-26 10:43:29 IST` (`ts=1787721209.085619`, overall rank 1). This is an
overall rating, not the bargaining-family substitute. The same authenticated
observation reported bargaining `2471.96/15052`, negotiation `2668.82/15009`,
and persuasion `2400.19/15012`. It therefore satisfied the operator's exact
`>=2505.00` peak-lock trigger on the first qualifying sample; no second sample
was awaited.

Codex immediately used `scripts/fleet.py bank composite`. The fleet tool
atomically requested the runner's SDK-native lossless drain: it stops queueing
on its next normal poll, completes every in-flight game, and stays down. No
process was signalled, killed, interrupted, or force-cycled, and no game was
abandoned. At observation/request time the live process was PID `86125`
(started `2026-08-26 09:43:49 IST`), workspace HEAD
`3434ed555fe4ea57f4ac7e28e01b7951bfd1fb8e`, and the locked 78-key overlay's
canonical SHA-256 was
`94bb689c645ec743406c64c3570b1b8e10e7d2778050ec0ca98950a3201e38b6`.

Authenticated activity at the trigger was bargaining/negotiation/persuasion
`+1586/+1551/+1584` over the trailing 24-hour baseline and
`+4302/+4269/+4301` over the trailing 48-hour baseline, far above the
`15`/`115` defense buffers. Agent 5 is now peak-locked: deploy no further
experimental strategy to it. Verify PID `86125` continues normally while it
drains, then verify it is fully down and absent from all queues. Preserve and
report every terminal result from this final cohort before making any
performance claim.

## 2026-08-26 09:43 IST — operator explicitly restarted Agent 5

The operator twice directed "restart Agent 5", superseding its stopped state.
The physical `composite` slot was already fully down with zero local process,
so `scripts/fleet.py start composite` safely removed only its disabled/drain
controls. The supervisor launched PID `86125` at `09:43:49` on workspace HEAD
`3434ed555fe4ea57f4ac7e28e01b7951bfd1fb8e` with policy `hardliner`, all three
families, LLM off, concurrency eight, and a bounded 3,600-second shift. No
running process was signalled or interrupted and no game was abandoned.

The locked 78-key strategy overlay is unchanged at canonical SHA-256
`94bb689c645ec743406c64c3570b1b8e10e7d2778050ec0ca98950a3201e38b6`.
The previous one-shot `bank_latched` audit record and 2505 threshold remain in
control, as `fleet.py start` intentionally preserves them; the old crossing
will not immediately bank the replacement or count as a newly armed trigger.
Server verification after launch reported all three rating families and seven
active games. At that read, bargaining was `2495.94/14919`, negotiation
`2616.98/14876`, persuasion `2372.56/14878`, and overall `2495.16`. No strategy
flag, family topology, LLM setting, or other slot was changed.

## 2026-08-26 09:05 IST — AC recovery verified; first usable shift still pending

The host has remained on AC power with the lid open since 08:43:49. `pmset`
records zero Sleep and zero DarkWake events after that boundary, and the
watcher, collector, and rating snapshot daemons have recovered their normal
cadence. All four challenger accounts resumed matchmaking after their common
queue bans expired. Test 2 drained without abandonment at 08:48:41 and launched
PID `82326`; Test 3 drained without abandonment at 08:57:46 and launched PID
`82601`. Test 1 PID `78356` and Test 4 PID `78267` still have matched games and
must finish their lossless drains naturally. No process was signalled and no
fleet configuration changed.

The two finalized pre-recovery shifts retain 665 outcomes: bargaining 220
agreements and two timeouts; negotiation 105 agreements, 63 no-deals, 49 walks,
and five timeouts; persuasion 211 completions and ten timeouts. They contain
169 exact-zero payoffs and zero invalids. The weakest adequately sampled cell
is Test 2 bargaining P1, complete information, known H12 at fitted percentile
`.2854` (`n=21`, all agreements). Test 2 persuasion is the weakest finalized
profile-family at `.4605` over 76 scoreable outcomes; 35 hidden-value seller
records are retained but cannot be assigned a percentile. These are outage-
spanning diagnostics, not deployment evidence.

The next falsifiable read is one full natural shift that begins after the ban,
runs continuously on AC with zero sleep, and finishes with zero unresolved
games. Retain all zeros, timeouts, invalids, roles, and cells. If Test 2 P1
complete/H12 bargaining remains below `.40` with at least 20 all-outcome games
in that clean shift, inspect its exact offer/accept path and propose a new
default-OFF deterministic hypothesis. Do not revive broad observed-gain or the
discount-no-regress parent: both are already measured negative or out of the
human-corrected scope. Agent 5 remains banked and unchanged.

## 2026-08-25 23:30 IST — Test 2 and Test 4 now use Agent 5 persuasion

The operator superseded the pending persuasion challengers and requested Agent
5's effective persuasion behavior on physical Test 2 (`hardliner`) and Test 4
(`randomized`). Test 2 already had the exact Agent 5 persuasion dictionary, so
it received no fleet write. Its proposed `adaptive-credibility-v1` additions
were canceled before exposure and remain absent/OFF.

Test 4 PID `60650` completed its natural 4,151-second shift and drained cleanly
at 23:29:46 IST. At `Tcfg=1787680787`, fleet tooling changed only
`GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2`,
`GLEE_PERS_P08_POSITIVE_PROSE_V1`, and
`GLEE_PERS_ZERO_MARGIN_TRUTH_V1` from `1` to explicit `0`. Replacement PID
`70598` launched naturally at 23:29:56 with the same hardliner probe, all three
families, LLM off, and a 3,600-second maximum shift. No process or queue was
forced, and Agent 5 remained banked and untouched.

The Test 4 non-persuasion overlay hash remained
`2e9104ab483ad11c48e64a3cd003d796891f5317d3956ca28df0f7971485679e`;
the respective Test 2 and Agent 5 full overlays remained byte-identical across
the write; `control.json`
remained `a55b9853f72d69f951d474a37137e71e7adb356d64f570d79193ef638ee34906`.
All ten persuasion `*_AB` keys are explicit zero on every slot. Test 4 retains
the three explicit-zero keys because clearing them can reactivate launch-env
values; its effective behavior is nevertheless Agent 5-identical. The Test 4
challenger is operator-terminated without a causal efficacy verdict, not
promoted or rejected.

## 2026-08-25 20:52 IST — high-share bargaining flag is configured but unreachable

Fresh exact-stack review found that `GLEE_BARG_HIGH_SHARE_DELAY_GUARD=1` on
Agent 5 and Test 4 is behaviorally inert.  The guard is deliberately nested
under `GLEE_BARG_DISCOUNT_NO_REGRESS=1`, but the 19:29 human scope correction
requires that broad comparator to remain `0` because it is valid only for
Bob/P2 with a disclosed twelve-round horizon.  Current Agent 5 reachability
over 600 games was `eligible=0`, `fired=0`, `action_changed=0`, and current-PID
traces likewise have zero fires.  It therefore cannot explain Agent 5's recent
rating movement and must not be described as live protection.  No flag or
process was changed: enabling the measured-negative broad parent merely to
reach this child would violate the human correction and revive known harm.

A falsifiable salvage test, not a deployment, is to retain every historical
outcome and measure the intersection of the high-share predicate with the only
permitted scope: P2, explicitly known H12, separately by message mode and
discount cell.  Only if that exact all-outcome slice is adequately sampled and
positive should a new default-OFF, conflict-free P2/H12-only flag be built and
proved reachable on a non-leading challenger.  The existing P2 commitment
dispatcher already owns part of this cell, so action-precedence and collision
tests are mandatory.  Agent 5 remains unchanged and protected.

## 2026-08-25 20:45 IST — Test 2 corrected P2/H12 bargaining stack launched at a clean boundary

The protected Test 2 process `9695`, launched at 19:25:30 with
`--max-time 3600`, completed its normal SDK drain and exited without being
signalled or interrupted.  At 20:34:00 the supervisor observed the slot down
and left it disabled; restart count remained zero.  This satisfied the clean
boundary queued in the 19:29 handoff.

Safe fleet tooling then made one atomic overlay update on physical slot
`hardliner`: `GLEE_BARG_P2_H12_D095_SILENT_V1=1`, while retaining
`GLEE_BARG_P2_H12_D095_MSG_COMMIT_V1=0`,
`GLEE_BARG_P2_H12_D100_COMMIT_V1=0`,
`GLEE_BARG_P1_UNKNOWN_DISCOUNT_DOMINANCE_V1=0`, and
`GLEE_BARG_DISCOUNT_NO_REGRESS=0`.  It also retained the already configured
`GLEE_NEGO_TEST2_UNKNOWN_R99_ACCEPT_V1=1`; no persuasion key was changed.
`fleet.py start hardliner` launched replacement PID `15302` at 20:45:08 from
workspace HEAD `a49f1bd086f0` (which contains pushed round-99 commit
`f7188ac`).  The exact command is `run_agent.py --probe champion --log-dir
logs/hardliner --llm-mode off --concurrency 8 --poll-interval 2.0 --families
bargaining,negotiation,persuasion --quiet --max-time 3600`.

The 83-entry runtime overlay has canonical SHA-256
`9e21cd564e6ffb7d12640e8c770dd6ccba71d87e1ed37a0eb25b0bf0dbef564a`.
Process-environment comparison found zero expected-value differences and
confirmed the five bargaining values above, round-99 acceptance `1`, Test 2
support V3 `1`, and negotiation default V2 `1`.  All three families and LLM-off
are present in the command.  The authenticated prelaunch T0 snapshot at
20:42:59 was overall `2438.33`, bargaining `2305.09/15836`, negotiation
`2658.83/15824`, and persuasion `2351.07/15798`.  The first 176 postlaunch turns
covered 25 games and all three families (22 bargaining, 35 negotiation, 119
persuasion turns), all heuristic with zero strategy-source errors; no terminal
result had yet landed, so no performance claim is made.  Preserve every
persuasion key until the persuasion workstream requests its own later clean
boundary.  Agent 5 was not changed.

## 2026-08-25 19:53 IST — Test 2 exact round-99 negotiation acceptance configured

Commit `f7188ac` (pushed to `origin/main`) adds the deterministic default-OFF
flag `GLEE_NEGO_TEST2_UNKNOWN_R99_ACCEPT_V1`. It is pinned to Test 2's selected
`test2_support_v3` whole negotiation policy and can change only buyer/P2's
decision on the seller/P1 offer at round 99 when the horizon is explicitly
unknown, the standing offer is provenance-valid, and it leaves the buyer at
least one cent. A V3 `RejectOffer` or `WalkAway` becomes `AcceptOffer`; rounds
1--98, known horizons, seller behavior, other whole policies, bargaining, and
persuasion are unchanged. Both complete and hidden information are covered
because 1,225/1,225 observed games reaching this nominally unknown horizon
terminated after the round-99 P1 offer, so there is no continuation to model.

The two motivating all-outcome failures were a buyer worth 12,000 rejecting
11,000 at round 99 and a buyer worth 100 rejecting 89 at round 99. They earned
zero instead of pointwise-known payoffs 1,000 and 11. Committed-CDF diagnostics
move from .0594 to .4196 and .0634 to .7254 respectively; those percentile
magnitudes are descriptive, not causal estimates. The earlier broad hidden
unknown-horizon accept-all-profitable policy remains excluded because it
measured -.06628 exact percentile over 375 exposed decisions.

Focused guard tests pass 32/32; deterministic/integration tests pass 151/151.
The full suite is 2,386 passed with exactly the same three pre-existing
failures: one stale bargaining horizon-floor expectation and the bargaining
and negotiation live-grid drift alarms. Exact physical `hardliner` reachability
at n=1,200 seed 2901 passes 4 eligible / 4 fired / 4 submitted-action changes,
all at round 99. No replay, arena, or red-team job was run.

The latest collector snapshot still identifies Test 2 / physical `hardliner`
as the second-best complete agent (overall 2415.72, behind Agent 5's 2467.17)
and our strongest negotiation component. Fleet tooling set only
`GLEE_NEGO_TEST2_UNKNOWN_R99_ACCEPT_V1=1` on `hardliner`; Agent 5's flag is
absent. This is configured but not yet behavior-live: PID 9695 launched before
`f7188ac` and is already disabled/draining for a separate protected launch
boundary. Do not interrupt or prematurely re-enable that process. The next
hardliner launch must load `f7188ac` or later and retain all three families;
verify the new PID and runtime flag before calling this live. This negotiation
work did not alter any bargaining or persuasion value.

## 2026-08-25 08:45 IST — Test 2 support V3 built default OFF

The human feedback contained two exact negotiation rules and several requests
for more evidence.  The first exact rule was already live in V2: a one-round
buyer accepts iff the incoming price leaves strictly positive payoff.  The
second was already live only for hidden unknown-horizon sellers: never carry an
ask outside the official `{80,100,120,150}*scale` buyer support.  No behavior
was invented for “move up a bit,” value-dependent thresholds, or the pending
inference answer.

Fresh authenticated Test 2 outcomes from 07:53--08:18 retained every result.
The hidden cap-10 seller slice was seven games: four agreements, two no-deals,
one walk, `-1.2` rating total.  All seven opening asks exceeded the largest
possible buyer value.  Two agreements left the seller only `0.40` and `0.85`
and scored `-5.7` and `-6.3`.  This identifies a literal support inconsistency,
not the causal value of an unplayed ask.

Default-OFF whole-policy selector `GLEE_NEGO_TEST2_SUPPORT_V3` keeps the entire
V2 matrix and additionally replaces only outgoing hidden cap-10 seller asks or
rejection counters with the existing support-grid prices: `119.99` for seller
types `80/100`, `149.99` for seller type `120`, scaled identically at every
price level.  Seller `150` stays on the dead-game policy.  Accept/reject/walk
decisions are unchanged; in particular, the previously negative broad hidden
accept-all-profitable policy is not revived.  The V2+V3 pair intentionally
selects V3 during an atomic migration; collisions with every unrelated whole
policy still fail closed.

Focused deterministic-policy tests pass 58/58 and the negotiation/isolation
suite passes 650/650.  The full suite is 2,098 passed with only the same three
pre-existing failures recorded by the preceding negotiation commits: stale
bargaining horizon-floor expectation plus bargaining and negotiation live-grid
drift.  Exact current Test 2 stack reachability over 1,200 games passes with
15,443 consulted states, 15,443 V3 trace changes, and 450 submitted wire
changes; examples move `3,970,600 -> 1,199,999.99` while preserving
`RejectOffer`.  Promotion configuration is Test 2 only:
`GLEE_NEGO_TEST2_SUPPORT_V3=1`; V2 may remain `1` during the atomic transition
or be explicitly set to `0`.  Keep Agent 5 on V1.  Do not change bargaining or
persuasion.  Codex did not edit live overlays, processes, `arms.json`, or
`control.json`; the deployment owner must arm the flag after the pushed code is
loaded.

## 2026-08-25 07:57 IST — V2 isolated to Test 2; Agent 5 retained on V1

Operator narrowed deployment after observing Agent 5 rising quickly: Test 2 is
the sole V2 challenger, and Agent 5 is the V1 comparison. Test 2 / slot
`hardliner` completed a zero-loss cycle at 07:51:22 and replacement PID `75251`
started at 07:51:32 from pushed commit `ddb26d2`, with `--probe champion`, LLM
off, and all three families unchanged. At `Tcfg=1787624505`, fleet tooling set
only the whole negotiation selectors: V1=0, V2=1, leader/rank/deterministic-FP
=0. Runtime overlay inspection resolves `mode=agent5_default_v2`.

Fresh post-boundary Test 2 traces immediately show V2 ownership on direct
first-principles wires and `deterministic_policy=agent5_default_v2` on retained
seller decisions. The first 33 negotiation turns comprised 26 current-seller,
six first-principles, and one observed-leader-buyer turn, with zero strategy
errors. Neither new rare support branch had appeared by this checkpoint, so no
live-effect claim is made. Test 2's non-negotiation overlay SHA-256 remained
exactly `b3dc118e29c9060fa05c3a3e8a336190c8872ffae7193dd3e36d7b28e3d973c4`.

Agent 5 remains PID `72600` with V1=1, V2 absent/off, and runtime
`mode=agent5_default_v1`; its non-negotiation overlay hash remains exactly
`13014b3950e594e328d1020d89fee32ec27c65461101051cc83106fc50825e16`.
Across every `GLEE_NEGO_*` key, the two overlays differ only on V1 (`1` versus
`0`) and V2 (absent versus `1`). A previously requested safe Agent 5 code-load
cycle was already resident in supervisor memory before the scope narrowed and
cannot be cancelled through the control surface; if it reaches a zero-game
boundary it may reload the same V1 configuration with zero games abandoned.
No Agent 5 flag or behavior was changed.

Compare future growth from the Test 2 boundary without conditioning on V2 gate
fires or agreements. Retain every negotiation result, including no-deals,
walks, exact zeros, invalid/timeouts, both roles, all information/horizon
cells, and unresolved joins. Roll V2 to Agent 5 only on the operator's later
decision after the all-outcome rate comparison.

## 2026-08-25 07:34 IST — Agent 5 negotiation V2 built default OFF

`GLEE_NEGO_AGENT5_DEFAULT_V2` is a mutually exclusive, deterministic whole
negotiation policy. It preserves V1's first-principles cells, seller-offer cost
inference, observed-leader buyer paths, seller messages, and labelled current
fallbacks. It adds two support-exact branches and no game hash or randomized
arm. The official hidden generator draws each value independently and uniformly
from `{80,100,120,150}*scale`: 6/16 pairs are feasible and 10/16 are not.

First, hidden unknown-horizon sellers with costs 80/100/120 now transmit fixed
rank-grid asks 119.99/119.99/149.99 on the unit scale (absolute one-cent
rounding at larger scales), replacing only the outgoing price. Seller cost 150
is structurally dead and retains the existing dead-game harvester. The
baseline Accept/Reject/WalkAway decision is preserved byte-for-byte. This
constraint is essential: the previous hidden-unknown accept-all-profitable
policy measured `-.06628` exact percentile over 375 exposed decisions (156
changed) and `-.00614` cohort ITT over 4,050 games. The live diagnosis that
motivated repricing is Test 2's latest-100 hidden-unknown slice at `-1.604`
rating/game (`n=27`) and the concrete seller-100 trace that remained at 187.59
while the hidden buyer climbed 55/63/71/78/86/98; 187.59 is above every legal
buyer type. That trace is mechanism evidence, not a causal effect estimate.

Second, a hidden cap-10 last-moving buyer still uses the strongest observed
seller-ask bound first. If no ask identifies a bound, V2 bids one cent above
the greatest supported seller type strictly below its own value:
80.01/100.01/120.01 for buyer values 100/120/150. These bids cover every
structurally feasible seller type under individual rationality. Buyer value 80
has no feasible seller and retains the existing fallback. This support rule
does not infer an unplayed offer's continuation value. Terminal-cent acceptance
is still response evidence rather than a guarantee; a spiteful or malformed
opponent can reject, and a low-payoff agreement can still rank poorly.

Verification: 75 focused component/wire tests pass; all 638 negotiation and
cross-family-isolation tests pass. Full suite is 1,965 passed with the same
three unrelated live-machine failures: stale bargaining horizon-floor 450 vs
468, bargaining live-grid drift, and negotiation max-round live-grid drift.
Exact prospective reachability passes on Agent 5's `composite` slot with its
actual `hardliner` wrapper at 9,847 eligible / 9,847 fired / 8,323 changed, and
on Test 2's `hardliner` slot with its actual `champion` wrapper at
9,429/9,429/7,483 (1,200 games each). These checks establish reachability and
wire ownership, not percentile lift.

At this checkpoint V2 is source-default OFF and not yet live. Promotion must
set V1=0 and V2=1 atomically while leaving every bargaining and persuasion key
unchanged, then cross a clean code-load boundary. Cohort every post-boundary
negotiation game, including agreements, no-deals, walks, exact zeros,
timeouts/invalids, both roles, all six public cells, and unresolved joins. Do
not condition the read on either new component firing.

## 2026-08-25 05:45 IST — bargaining rises; incomplete negotiation evidence blocks changes

Fleet topology and health remain clean.  Supervisor PID `93675` has zero
restart counts; all five current children started after pushed HEAD `4a15244`,
queue bargaining, negotiation, and persuasion, and produced fresh error-free
turns in all three families.  Every A/B, randomizer, router, allocator, and
cell-assignment flag is zero.  Test 2's exact bargaining stack is unchanged,
and the default-off late-stasis code is loaded but absent/off on every overlay.

The exact official snapshot at `1787616400` keeps Test 2 first overall at
`2278.66`, with Test 4 second at `2271.58`.  Movement since snapshot
`1787615191` was Test 1 `+5.52`, Test 2 `+15.55`, Test 3 `-4.10`, Test 4
`+19.04`, and Agent 5 `-17.74`.  Every slot gained bargaining over that same
interval; Agent 5 bargaining rose `+18.03`, while its negotiation fell
`-56.47` and persuasion `-33.05`.  Do not attribute its overall decline to the
bargaining guard.  Negotiation remains the fleet's weakest family: best ours
is `2062.40` versus field-third `2667.93`.

Agent 5's frozen high-share cohort now enrolls 195 bargaining games: 155
locally joined outcomes and 40 retained unresolved.  All joined outcomes are
agreements, with zero exact zeros, no-deals, parser, strategy, source, or wire
failures.  The full enrolled cohort is Alice/Bob `98/97` and covers every
coarse role x horizon x message cell.  Fifteen eligible game-turns all fired
and submitted exact deterministic accept wires.  Official bargaining moved
`2122.69/12619 -> 2222.34/12809` (`+99.65`) after activation, but fewer than
200 joined outcomes and 40 unresolved records block the frozen comparison.
The preceding-200 comparison was not inspected.

Test 4 PID `55554` has 82 current-shift negotiation games: 28 local finals and
54 unresolved.  The 28 finals retain 13 agreements, eight no-deals, seven
walks, 15 exact zeros, and both roles; all 2,563 post-boundary action turns are
heuristic with zero source/strategy errors or malformed wires.  Displayed
negotiation moved `2081.00/6987 -> 2058.36/7045` (`-22.64`), below the frozen
`-40` loss threshold.  A resolved-only percentile is selection-biased while
54 games are missing, so no rollback clause fires.  The last complete-shift
weakness remains complete-information / unknown-horizon seller at `.2339`,
`n=5`, too thin for a policy change.

All five frozen Agent 5 late-stasis outcomes remain unresolved and unimputed;
the sole predicate-reaching case still makes the maximally adverse evidence
bound negative.  No code, live flag, process, or deployment changed.  Continue
the Agent 5 cohort to 200 joined with zero unresolved, and finish Test 4's
natural shift before another decision.

## 2026-08-25 05:18 IST — Test 4 kept; Agent 5 high-share still below boundary

The fleet is healthy and unchanged in topology: all five agents still queue all
three families, supervisor restart counters are zero, every per-game A/B,
randomizer, router, and cell allocator remains off, and Test 2's bargaining
peak stack is untouched.  Test 3, Test 4, and Agent 5 completed natural drains
with zero abandoned games and relaunched as PIDs `55548`, `55554`, and `56033`.
The new Agent 5 process loaded pushed HEAD `4a15244`; the late-stasis flag is
absent/off and its bargaining high-share guard remains its sole unique live
bargaining overlay.

At exact official snapshot `1787615191`, Test 2 remains the overall leader at
`2263.11`; Agent 5 is second at `2260.38`, only `2.73` behind.  Since the prior
heartbeat snapshot, overall movement was Test 1 `+16.31`, Test 2 `-8.84`, Test
3 `+3.07`, Test 4 `+32.77`, and Agent 5 `+38.80`.  These cross-profile changes
are observational.  Negotiation remains the fleet's weakest family: the best
current internal mark is about `2077`, versus field-third `2675.62`.

Agent 5's frozen high-share cohort now has 142 enrolled bargaining games: 137
locally joined outcomes and five retained unresolved records.  The 137 joined
outcomes are agreements, with zero exact-zero, no-deal, strategy, wire, or
parser failures; both roles and every coarse role x horizon x message cell are
represented.  Eleven eligible game-turns fired and all eleven submitted exact
accept wires.  Official Agent 5 bargaining moved `2122.69/12619 ->
2204.31/12760` (`+81.62`) after activation, but this is not the frozen
same-cell/role comparison.  Do not inspect or act on that formal comparison
until 200 outcomes are joined and none in the enrolled cohort is unresolved.

Test 4's second clean leader-replica shift completed 132/132 negotiation games:
63 agreements, 44 no-deals, 24 walks, one opponent-side invalid-moves result,
and 69 exact zeros, retaining both roles and every cell.  There were no source,
wire, parser, fallback, or strategy failures.  All-outcome fitted same-cell
percentile was `.49568`, 95% CI `[.44904,.54233]`, while official negotiation
moved `2049.57/6858 -> 2081.00/6987` (`+31.43`).  The frozen rollback rule is
not met, so keep the profile.  Complete-information / unknown-horizon seller is
the weakest descriptive cell at `.23391`, but only `n=5`; named-opponent slices
are likewise too thin to justify policy.

All five frozen Agent 5 late-stasis outcomes remain unresolved, including the
sole observed game reaching the proposed predicate.  Its maximally adverse
bound remains negative, so `GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1` stays
OFF.  No code, flag, or deployment changed in this check.

## 2026-08-25 04:52 IST — late complete/unknown stasis guard built inert, not deployed

An all-outcome audit of 724 clean negotiation first-action games found 66 in
the complete-information / explicitly unknown-horizon cell.  Of the 61
terminal games, 44 agreed and 17 ended no-deal; five Agent 5 outcomes remain
unresolved and were not imputed or dropped.  Every one of the 17 terminal
no-deals repeatedly rejected a strictly profitable offer.  Broad repeat fences
remain prohibited: repeat-3 was `-.28173` diagnostic exact percentile and
repeat-10 was `-.04804`, reproducing the measured-negative accept-all failure.

The only post-hoc separator was much narrower: round at least 75 plus ten fully
completed, wire-exact mutual offer/counter/rejection cycles reached 17/17
terminal no-deals and 0/44 agreements.  On all 61 terminal outcomes its
diagnostic exact-percentile alternative was `+.03062`; one of the five
unresolved games also reaches, so the maximally adverse unresolved bound is
`-.01553`.  This is hypothesis evidence, not a promotion result.

Pushed commit `4a15244` implements
`GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1` default OFF and live nowhere.  It
is pinned to the current deterministic negotiation
stack, fails closed against randomized/overlapping flags or mixed policy
selectors, projects the baseline Reject through `actions.coerce`, and compares
the final submitted counter against ten completed two-row cycles.  It accepts
both the live scalar and simulator dict counter schemas, requiring provenance
when present.  Exact Test 4 and Test 3 stack reachability each passed
`4914/4914/4914` eligible/fired/action-changed over 800 games.  Focused tests
passed 38/38, all negotiation tests 585/585, and the full suite passed 1,861
with only the three already-observed live-machine failures (stale bargaining
horizon-floor expectation plus bargaining and negotiation grid drift).

Do not activate while the adverse unresolved bound is negative.  Once all five
outcomes finalize, any prospective test must be precommitted on one non-leading
deterministic challenger at a natural boundary and retain the whole enrolled
negotiation cohort, including non-fires, agreements, no-deals, zeros, both
roles, every cell, and unresolved joins.  Test 2 remains protected.

## 2026-08-25 04:17 IST — Test 4 negotiation drop is watch-grade, not rollback-grade

The exact clean PID 37202 leader-replica shift (`1787607037..1787610923`) is
fully joined: 155/155 negotiation games terminal, zero unresolved, 74
agreements, 53 no-deals, 28 walks, and 81 exact zeros, retaining buyer/seller
79/76 and all six information x horizon cells. Raw official negotiation moved
`2115.13/6709 -> 2049.57/6858`, a `-65.56` displayed-rating loss. Mechanism
reach was complete on the copied buyer path (586/586 turns across 79/79 buyer
games) and the seller-message gate fired 159 turns across 36 games; there were
zero source, wire, or strategy failures. All-outcome fitted same-cell
percentile was `.49710`, 95% CI `[.45704,.53715]`.

Do not roll back from that interval alone. The immediately preceding same-size
aggregate window gained `+62.11` under essentially the same intended replica,
93/155 of its local outcomes are unresolved, and the completed-shift interval
still spans `.50`. This is sign-flipping observational evidence, not an
identified fallback comparison. The precommitted next-shift rule is now: keep
every negotiation game and authenticated official delta; revert immediately on
any source/wire/strategy failure, otherwise only after zero unresolved outcomes
if official per-game mean 95% CI is wholly negative, or a second full shift
loses at least 40 rating and its all-outcome fitted-percentile upper 95% bound
is below `.50`. Test 2 remains untouched.

## 2026-08-25 04:08 IST — high-share bargaining challenger live on Agent 5 only

The staged guard crossed a verified code boundary without abandoning a game.
The supervisor recorded `composite cycled with zero games abandoned` at
04:06:28 and launched PID 48295 at 04:06:38 from current pushed HEAD `8a028dd`,
which contains implementation commit `aa6485a`. Its actual command is
`--probe hardliner`, LLM off, and
`--families bargaining,negotiation,persuasion`; no family eligibility changed.

Immediately before activation, the actual Agent 5 stack re-passed reachability
at `38 eligible / 38 fired / 38 action_changed` over 800 paired bargaining
games. Fleet tooling set only slot `composite` to
`GLEE_BARG_HIGH_SHARE_DELAY_GUARD=1` at arms mtime
`Tcfg=1787611031` (04:07:11). Runtime overlay lookup independently resolves the
candidate and required deterministic discount guard to true, while the hash
and nominal guards, legacy observed gain, econ-stall, stonewall, and opponent
exploit resolve false/zero. The other four slots remain explicit zero, every
`*_AB` remains zero, and Test 2's exact bargaining peak stack was not touched.

The last official snapshot before activation (`1787610964`) put Agent 5 at
`2220.76` overall and `2122.69` bargaining. The clean analysis cohort includes
only Agent 5 games whose first logged turn is at or after `1787611035`,
excluding three games opened in the 33 seconds between launch and the hot
overlay even though they completed later. Keep every enrolled non-trigger,
role, cell, zero, no-deal, and unresolved game. At 200 fully joined games, compare all-outcome same-cell and
role percentile with the immediately preceding 200; defer while any outcome is
unresolved. Any strategy, parser, or wire failure is an immediate explicit-zero
revert. Because allocation is deterministic by profile, rating and cross-agent
movement are observational, not causal; do not promote this to Test 2 or copy it
fleet-wide from a favourable selected-trigger read.

Live mechanism evidence arrived without waiting for a selected outcome. By
04:10:30, the all-turn post-cohort stream contained 302 turns / 35 game IDs
across all three families, with zero strategy-error sources. Five bargaining
states carried guard diagnostics and two changed Reject to Accept at standing
shares `.473700` and `.473684`; both had exactly three provenance-checked offers,
no retreat, and emitted `gates_fired=[accept_floor,high_share_delay_guard]`.
This proves the loaded production gate moves real wires; it says nothing yet
about payoff efficacy, and neither triggered game is being selected for the
outcome read.

## 2026-08-25 03:13 IST — high-share bargaining challenger pushed, staged at zero

The broad `GLEE_BARG_OBSERVED_GAIN` proposal was stopped before deployment. It
repeats a treatment already negative on all three arena seeds and its legacy
parser can misclassify own offers when proposer provenance lives at history-row
level. A frozen, all-first-trigger Test 2 replay instead isolated a materially
narrower band: among 39 standing offers from `.45` through `.499`, 35 recovered
finals were 35/0 immediate-accept wins (`+.10547` pot share and `+.09539`
diagnostic percentile), with four unresolved. Even giving every unresolved
baseline the full pot next round left `+.05857` pot share, 95% CI
`[+.00746,+.10968]`. The exact sub-`.35` rows were negative (combined n=51,
`-.02531` pot share), so a broad release remains prohibited.

Pushed commit `aa6485a` adds default-OFF deterministic
`GLEE_BARG_HIGH_SHARE_DELAY_GUARD`. It changes only a remaining Reject in the
`.45-.50` band, after three finite, genuine opponent offers including a
non-withdrawn current high-water, and only when both observed floor economics
and discounted continuation clear the offer. It is pinned to the exact peak
`.50/.05` stack, requires the deterministic discount guard, has no game hash,
and fails closed against every legacy/overlapping release or exploit flag.

Verification: 69 focused passes; 216 bargaining passes with only the declared
stale horizon assertion; full suite 1,837 passes with exactly the two declared
bargaining failures; Agent 5 exact-stack reachability `130/130/130` over 2,400
paired games. Independent review verdict: PASS for Agent 5 only, not Test 2 or
fleet-wide.

Deployment is deliberately two-stage. The new flag is explicit `0` on all five
slots. Agent 5 additionally has legacy observed gain, hash/nominal guards,
econ-stall, stonewall, and opponent exploit explicit zero. Its PID 37885 began
before the final source existed, so a safe named `composite` cycle was queued at
03:12; do not arm until its replacement starts from `aa6485a` or later. The
earlier `cc608f5` deterministic discounted guard did complete clean zero-loss
rotations and is live on Test 4 from 03:00:37 and Test 1/Agent 5 from
03:05:14/15; Test 2 and Test 3 remain protected at zero.

## 2026-08-25 03:01 IST — deterministic negotiation leader replica live on Test 4

Operator explicitly transferred deployment authority for this promotion.  The
default-OFF negotiation portfolio was pushed through commit `d615ac8` (the
behavioral implementation is `49b5901` plus the exact seller-message correction
`6942311`).  Only Test 4 / slot `randomized` was promoted, through fleet tooling,
with `GLEE_NEGO_LEADER_REPLICA_V1=1` and
`GLEE_NEGO_RANK_HYBRID_V1=0`.  Test 4 remains policy `composite`, LLM off, and
eligible for bargaining, negotiation, and persuasion.  Every negotiation
`*_AB` value on the slot was independently checked as zero.  No bargaining or
persuasion key was changed by this deployment, and the rank-hybrid backup was
not deployed.

The required exact-stack preflight used Test 4's actual overlay and composite
wrapper over 800 negotiation games.  It banked 6,253 decision points and
reported `eligible=6253`, `fired=2075`, `action_changed=3793`; focused clone and
deterministic-policy tests passed `72/72`.  The already-recorded full-suite run
on this source had 1,798 passes and only the two declared bargaining failures.
The implementation therefore changed real negotiation wires and did not rely
on a flag-presence claim.

The safe cycle was requested at 02:45:07 IST.  The supervisor retained old PID
17609 while its games drained from three to two to one, then recorded
`randomized cycled with zero games abandoned` at 03:00:26.  Replacement PID
37202 launched at the clean boundary `T0=1787607037` (03:00:37 IST) with
`--probe composite`, all three families, and `--max-time 3600`.  Post-boundary
wire evidence immediately confirmed both role paths: game
`3a88f17a-96b6-4aad-9660-2f68a2d96b6e` stamped buyer decisions with
`plan.source=leader_replica_v1` beginning at `1787607045.89682`, and game
`773cea3a-e53f-4f90-baf1-7067acb2d7b2` stamped its first seller offer with
`top_seller_message_clone.arm=leader_replica` at `1787607060.735022`.
The first post-launch official stats snapshot at `1787607173.801223`
(03:02:53 IST), before any observed post-boundary negotiation completion,
recorded negotiation rating `2115.13` after 6,709 games; use this as the first
available aggregate baseline while retaining the process launch as cohort T0.

This promotion preserves the whole Test 4 behavior whose preceding clean
77-game rating window implied opponent-adjusted percentile `.54881`; it does
not turn that observational estimate into a causal result.  Score all Test 4
negotiation games from `T0` without conditioning on agreements or local result
availability.  The sustained `.55-.56` target and third-place objective remain
unproven, and no other deterministic negotiation component currently has a
stronger deployment case.

## 2026-08-25 02:42 IST — Test 2's 2586 bargaining peak was the current stack

Operator asked to restore Test 2's approximately 2600 bargaining strategy after
its displayed rating fell to roughly 2283. The recorded maximum was `2586.20`
at `1787536616` (2026-08-24 07:26:56 IST, 11,325 bargaining games). The process
covering that peak launched at 07:03:32 after commit `7321de5`. At that commit,
`control.json` mapped slot `hardliner` / Test 2 to policy `champion`, all three
families, LLM off. Its bargaining overlay was exactly the current active stack:
accept floor `.50`, Bob offer on, econ stall off, floor gain `.05`, message arm
off, nominal no-regress off, offer floor `.57`, opponent floor `.39`, SPE weight
`1.0`, uncapped horizon `60`. Current Test 2 is still `champion` with those exact
values. New discount/no-regress, observed-gain, and hash flags are explicit
zero. Its current PID also predates commit `cc608f5`, so that deterministic
challenger cannot explain the decline.

There was no behavior-changing bargaining commit between the peak and Test 2's
current loaded process. The only bargaining diff adds default-off Test 4/hash
machinery; its Test 2 flags are zero. A git/config rollback would therefore be a
placebo and risks unrelated negotiation/persuasion work without changing a
Test 2 bargaining action. No flag, control map, process, or code was changed.

The decline is real outcome drift under the same strategy. Test 2's latest six
hours were `.5038` fitted same-cell percentile over 498 bargaining finals versus
`.5668` over 471 in the preceding six; payoff/pot fell `.4703 -> .4365`.
Agreement stayed `100.0% -> 99.6%`, so broad closing failure is not the cause.
The largest deterioration was own `delta=.9` (`.4917 -> .3758` percentile,
`.4291 -> .3644` payoff/pot), unknown horizon (`.5678 -> .4833`), Alice
(`.5395 -> .4837`), and hidden opponents (`.573 -> .504`). The same rating
also fell about 200 points by 13:29, recovered about 143 points by 20:12, then
fell again, all without a bargaining-policy change. Treat 2586 as a transient
high-water mark, not an archived superior policy. Next improvement should
target the identified impatient/unknown/Alice weakness on challenger profiles;
keep Test 2 frozen as the exact peak-stack control.

## 2026-08-25 02:32 IST — live whole replica is near target; exact flag preserved

This supersedes the recommendation ordering in the 02:13 entry below. Test 4's
actual deterministic whole negotiation profile from commit `93a449f` is now the
recommended component to preserve while evidence accumulates. It consists of
the full observed 7aidara buyer policy, the current seller decision/price
policy, and the exact message-only seller table. The rank hybrid remains the
distinct backup; do not replace the live Test 4 profile with that post-hoc
hybrid before obtaining a longer all-game read.

Clean rating-window accounting begins after the first stats snapshot following
Test 4's zero-game launch boundary `T0=1787602730`. At
`1787603104.747`, Test 4 negotiation was `2051.22` after 6,564 games;
at `1787604918.233`, it was `2098.84` after 6,641. Thus the 77-game
all-outcome interval gained `+47.62` displayed rating. Undoing the documented
`g/(g+30)` volume shrink and applying the mature `eta=0.002` update gives a
weighted mean game rating of `2390.47`, or opponent-adjusted percentile
`0.54881`. Concurrent champion was `0.54843` over 53 games. The first 52-game
subwindow had reached `0.56820`, but the following 25 games implied `0.51146`;
the required sustained `0.55-0.56` is therefore not yet established. Test 4 is
currently our negotiation leader at `2098.84`, displayed negotiation rank 13;
the third-place rating is `2675.62`. This comparison is observational, not a
causal policy estimate, and the Test 4/champion difference is noise-sized.

The complete post-`T0` local turn cohort now has 110 unique negotiation games.
Only 28 have locally recovered terminal files: 12 agreements, eight no-deals,
seven walk-aways, and one `invalid_moves_exceeded`; 82 remain local-missing and
must not be imputed. Within the copied-buyer path, the recovered accounting is
four agreements, three no-deals, five walks, and 39 local-missing. The seller
message path has three agreements, two walks, one invalid terminal, and 17
local-missing; baseline seller cells have five agreements, five no-deals, and
26 local-missing. The invalid terminal occurred in an always-feasible complete
cell, but the server artifact does not identify which side emitted the invalid
move; our recorded opening price/message is legal, so attribution is unresolved.

Commit `6942311` (local only, on top of `49b5901`) corrects
`GLEE_NEGO_LEADER_REPLICA_V1=1` so it reproduces the exact currently running
whole profile, including the seller message-only table. The default-OFF
`GLEE_NEGO_RANK_HYBRID_V1=1` remains the distinct alternative: copied buyer in
complete information and hidden cap-10, current buyer in hidden cap-1/unknown,
and current seller text. Both flags off preserve baseline; both on fail closed
to baseline. Deployment chat should preserve the current Test 4 behavior at
its next natural rotation by promoting only `GLEE_NEGO_LEADER_REPLICA_V1=1`
there, with every negotiation `*_AB` flag zero. If portfolio diversity is
desired, rank hybrid belongs on a separate challenger, not as an overwrite of
Test 4.

Verification: 72 focused deterministic/clone tests passed. The
negotiation-selected suite had 745 policy passes plus one live-data horizon-mix
drift failure (`n=29,846`, `p=7.86e-4`). Full suite: 1,797 passed and three
failures: the pre-existing bargaining continuation assertion, bargaining live
grid drift, and negotiation live horizon-grid drift. No deterministic policy
test failed. No bargaining or persuasion source/behavior was changed. No
`arms.json`, `control.json`, `.env`, log, process, supervisor, or deployment
configuration was edited; no agent was cycled or deployed, and neither local
commit was pushed.

## 2026-08-25 02:31 IST — deterministic persuasion component, default OFF

Persuasion source commit `e6ca9c6`, with evidence-comment correction `c085878`
(local only; not pushed or deployed), adds
`GLEE_PERS_BUYER_EXPLICIT_DECLINE_VETO_V1`.  It follows the current complete
policy and can make exactly one final change: buyer-v2's existing BUY becomes
PASS when the current text is an expanded-parser explicit decline or the
documented binary wire is strict `no`.  It is deterministic across games,
reads no game id, assigns no arm, targets no numeric cell, does not reinterpret
history, and never changes PASS to BUY.  The check is last, so an older optional
buyer overlay cannot revive the purchase.  Unset/`0` does not even consult the
expanded parser and is byte-identical to the pre-commit strategy.

Recommended complete persuasion component for the deployment owner:

- Retain the measured broad baseline: `GLEE_PERS_BUYER_V2=1`,
  `GLEE_PERS_BUYER_TIGHT_PRIOR=.65`, `GLEE_PERS_HONEST_ROUNDS=99`,
  `GLEE_PERS_LIE_SHADING=0`, `GLEE_PERS_KEEP_MSG=1`,
  `GLEE_PERS_MSG_STYLE=token`, `GLEE_PERS_TOKEN_MAX_P=0`, LLM off, and every
  historical persuasion `*_AB`, rank, backload, broad parser, selectivity, LCB,
  and DP flag at `0`.
- Add `GLEE_PERS_BUYER_EXPLICIT_DECLINE_VETO_V1=1`.  This is a buyer safety
  upgrade, not a seller-profile override.  Explicit `LIE_SHADING=0` and
  `HONEST_ROUNDS=99` keep all named profiles on the same recommended seller
  behavior: honesty when lying is punished and all-push when the prior makes a
  sale free.

Evidence and all-outcome accounting:

- The broad seller baseline remains the strongest measured deterministic
  policy.  Across 8,369 seller games against 70 opponents, punished-cell
  honesty scored diagnostic local percentile `.6485`; never-lie beat shading
  by `+.0457`, 95% CI `[+.0030,+.0883]`.  Buyer-v2's corrected fixed-stream
  replay retained 3,722 games and improved payoff by `+.481P/game`, 95% CI
  `[+.403,+.560]`, while negative games fell from 17.5% to 13.2%.  That replay
  had 3,982/4,000 control fidelity and found no adaptation among 68 checked
  sellers; it remains offline evidence, not an official causal estimate.
- Frozen all-five first-buyer-turn cohort
  `[1787570799,1787596351.4207911)` began with 1,958 assignments, excluded 15
  named self-play games and nine actually armed text-veto candidates, and
  retained 1,934 clean assignments: 1,925 completed, six active and three
  no-deal.  No cross-slot game/result duplicate was found.  In 981 completed
  text games (987 assigned: four active and two no-deal), the
  final text veto would remove 156 actual purchases in 65 games; revealed
  quality was 155 LOW and one HIGH.  The 129 changes requiring the expanded
  phrases were 129/129 LOW.  The all-text fixed-stream diagnostic was
  `+.156983P/game`, 95% CI `[+.103054,+.210912]`, and `+.009012` local
  percentile, CI `[+.005948,+.012076]`; nonpositive games moved 420 to 401,
  negatives 110 to 99, and severe outcomes at or below `-2P` 63 to 61.
- A separately decontaminated binary audit at the same frozen boundary began
  with 953 assigned buyer/binary games, removed six named self-play games, and
  retained all 947 clean assignments: 944 completed, two active and one
  no-deal.  Strict binary `no` would change 20 games / 20 turns, all 20 revealed
  LOW and zero HIGH, with every slot represented (champion/composite/conceder/
  hardliner/randomized `4/5/5/3/3`).  The
  completed-game fixed-stream diagnostic was `+.02119P/game`, CI
  `[+.01200,+.03038]`, and `+.000983` local percentile, CI
  `[+.000161,+.001806]`.  Most support was p=.33/r3 (13) and p=.5/r2 (6); the
  p=.8/r4 subgroup has only one observation.
- These changed-turn quality ratios are purchase-selected: passed quality and
  the seller's response to future refusals are not observed.  The local replay
  intervals are therefore diagnostic only.  The scoped official JSON has just
  five persuasion joins total, only one buyer join (text) and zero binary-buyer
  joins; there is no authenticated candidate-control official rating delta for
  this new deterministic policy.  Authenticated game `f2bed4f4-...` does prove
  the underlying defect occurred: three purchased `Not recommended` lows,
  zero payoff and `-4.0` official rating.  Persuasion's roughly `+/-125` rating
  noise across identical agents rules out cross-slot rating comparison as
  substitute causal evidence.
- A broader tri-state rewrite was rejected before commit or deployment.  On
  1,002 text games it changed 97 games / 550 turns, including 372 unsafe
  PASS-to-BUY moves whose qualities were unobserved.  The shipped guard is the
  one-directional subset only.

Mechanism verification: exact current champion-stack reachability over 800
seeded persuasion games was `eligible=763`, `fired=763`,
`action_changed=763`.  An independent 4,000-state property grid found 273
changes, all and only explicit-decline BUY-to-PASS, with zero violations.
Comparison across 26,236 synthesized messages found zero legacy/default parser
verdict changes; only the intended expanded decline overlaps changed.
Focused tests passed 142/142 and persuasion-wide review passed 380/380.  The
final full suite on the combined HEAD finished 1,798 passed with exactly the
two declared bargaining failures (stale 450-vs-468 horizon expectation and
live bargaining grid drift).  No persuasion or negotiation test failed.

Portfolio backup: existing deterministic seller `GLEE_PERS_DP_V3=1` with
`GLEE_PERS_DP_V3_MARGIN=.25` is the only meaningfully distinct broad candidate
with positive evidence: offline diagnostic percentile `+.0176`, CI
`[+.0162,+.0190]`, positive in 13/30 cells and negative in none.  Its policy
model and evaluation CDF are in-sample, seller adaptation is absent, and there
is no authenticated official causal result.  It is research-only lower-slot
diversity, not a promotion-grade replacement.  No independently supported
alternative buyer policy exists: backload, seller DP-v1, LCB, rank-buy, broad
selectivity and LLM wording all measured negative or failed identification.

Deployment boundary: this task changed only persuasion source, parser support,
reachability support, tests, and this handoff.  It did not edit `arms.json`,
`control.json`, `.env`, logs, supervisor/process state, bargaining behavior, or
negotiation behavior.  It did not cycle, deploy, arm, randomize, or push an
agent.  The main deployment chat owns any activation and must keep all five
agents eligible for all three families.

## 2026-08-25 02:13 IST — deterministic negotiation components, default OFF

This entry supersedes the automatic `composite -> leader_replica` source route
recorded below. The operator's newer boundary requires every new negotiation
behavior to land behind a default-OFF flag and reserves fleet configuration and
deployment for the main deployment chat. The automatic profile selector and
`Config.nego_policy` field were therefore removed; with both new flags off,
every named profile executes the pre-`93a449f` negotiation stack.

Two mutually exclusive, non-randomized complete components are implemented in
source commit `49b5901` (local only; not pushed or deployed).

- Recommended `GLEE_NEGO_RANK_HYBRID_V1=1`: current seller policy in every
  cell; observed 7aidara buyer policy in every complete-information cell and
  hidden cap-10; current buyer in hidden cap-1 and hidden unknown horizon. The
  cap-1 receiver already uses the measured any-positive terminal rule. The
  unknown-horizon exclusion removes the full clone's eight-price walk, its only
  coherent negative horizon slice.
- Backup `GLEE_NEGO_LEADER_REPLICA_V1=1`: current seller policy plus the full
  observed 7aidara buyer policy in every supported information/horizon cell.
  This is the deterministic equivalent of the frozen broad buyer treatment,
  without adding the unmeasured seller-message overlay.

If both flags are `1`, neither owns the game and the existing stack runs. A
deterministic buyer wire owns the final numeric output, so legacy price guards
cannot create an unlabelled hybrid. The legacy randomized negotiation message
bank is bypassed while either complete component is selected. Deployment must
still keep every negotiation `*_AB` flag at zero; the existing fallback stack
contains historical gates outside these two selectors.

Evidence and all-outcome accounting:

- Frozen broad official buyer checkpoint, 91/91 scored: candidate 44, `+49.1`
  total / `+1.116` per game, with 18 agreements, 13 no-deals, and 13 walks;
  control 47, `+11.6` / `+0.247`, with 31 agreements, 11 no-deals, and five
  walks. Point lift `+0.869/game`; the approximate 95% interval crosses zero
  (`[-0.78,+2.52]`), candidate no-deals are +6.14pp, and composite is
  `-0.648/game`. This supports the backup's identity but does not prove it.
- Within that checkpoint, hidden unknown was candidate `-0.227` (n=11, ten
  walks and one agreement) versus control `+0.093` (n=15, nine agreements,
  five walks, one no-deal). Hidden cap-10 was candidate `+1.573` (n=15) versus
  control `-0.236` (n=11). The latter was selected post hoc and cannot identify
  the recommended hybrid's counterfactual.
- The clean first prospective hidden-cap10 checkpoint was candidate
  `+2.467/game` (n=9) versus control `+1.100` (n=16), lift `+1.367`, exact
  one-sided host-stratified `p=.1056`. Across all three official scoped files,
  54 deduplicated scored games are candidate `+0.713` (n=24; 9 agreements,
  10 no-deals, 5 walks) versus control `+0.523` (n=30; 7 agreements, 16
  no-deals, 7 walks), lift `+0.189` with approximate interval
  `[-1.55,+1.93]`. The expanded read is descriptive only: its pooled mechanism
  audit spans disabled/old-code traces and previously reported 15 wire
  mismatches plus four missing traces.
- Fixed-boundary recent five-slot census from `1787559935`: 5,267 negotiation
  finals, including every status: 2,564 agreements, 1,872 no-deals, 814 walks,
  seven active snapshots, seven timeouts, and three invalid-move terminals.
  Complete information was 1,424 games (1,340 agreements, 80 no-deals, two
  active, two timeouts); hidden was 3,843 (1,224 agreements, 1,792 no-deals,
  814 walks, five active, five timeouts, three invalid). This is descriptive
  fleet context, not a candidate-control estimate. Complete cells are always
  feasible; hidden cells are only 37.5% feasible.
- The already-live Test 4 auto-profile exposure from the superseded commit had
  nine unique supported buyer games at the audit boundary, all nine locally
  unresolved. It supplies mechanism proof only and no score claim.

Identification objections remain explicit: the recommended hybrid is a
mechanism-driven post-hoc repair, not a prospectively identified winner; the
full backup failed its frozen promotion gates; hidden private types are not
recoverable in no-deals; no accepted-deal statistic is used to value an
unplayed offer; and seller-message imitation has direct wire support but no
policy-effect estimate, so it is excluded from both components.

Verification: 72 deterministic/clone policy tests passed; 706 negotiation-wide
tests passed; full suite finished with 1,751 passed and only the two declared
bargaining failures (`realistic_continuation` 468 versus stale 450 expectation,
and the live bargaining-grid drift alarm). No bargaining or persuasion source
was changed by this work. No `arms.json`, `control.json`, `.env`, log,
supervisor, agent process, or deployment configuration was edited; no agent was
cycled or deployed.

## 2026-08-25 02:11 IST — deterministic bargaining guard pushed and queued

Operator requested bargaining improvement across the max-of-five full-stack
portfolio while prohibiting per-game randomizers and rejecting five identical
agents. Pushed commit `cc608f5` adds default-off
`GLEE_BARG_DISCOUNT_NO_REGRESS`. After the baseline chooses Reject, it accepts
only a positive standing offer when our own discount is below one and the exact
next wire-coerced counter, discounted one round, is no better. It excludes the
harmful `delta_me=1` cell and fails closed if the old hash arm or broad nominal
no-regress flag is armed.

The evidence is retrospective: complete first triggers on the two bargaining
leaders were 49/49 favorable in discounted games, `+0.03326` mean pot share
(95% CI `[+0.02722,+0.03930]`) and `+0.02005` diagnostic percentile; the
excluded patient row lost `0.0505` pot share over 16 games. This is a
deterministic deployment under operator direction, not a prospective causal
claim. Exact-stack reachability passed Test 1 `11/11/11`, Agent 5 hardliner
`14/14/14`, and Test 4 `31/31/31` eligible/fired/action-changed. Focused tests
passed 32/32; the full suite passed 1,738 with exactly the two predeclared
bargaining failures.

At `Tcfg=1787604088`, the guard was set to `1` on Test 1, Agent 5, and Test 4,
and explicitly `0` on protected controls Test 2 and Test 3. Fleet-wide
`GLEE_BARG_DISCOUNT_NO_REGRESS_AB=0` and `GLEE_BARG_NO_REGRESS=0`; no game hash
or cell-specific assignment remains. Safe cycles were requested for the three
candidates at 02:11:35, without signalling a process. Their then-current PIDs
all predated the commit, so do not call the guard live until replacement PIDs
start after `cc608f5`. Evaluate from each clean PID boundary, keep every zero
and no-deal, and treat candidate-versus-control profile differences as
observational because the operator intentionally rejected randomization.

## 2026-08-25 01:44 IST — whole deterministic leader-replica policy pushed

Operator superseded every cell/A/B rollout with full three-family named
profiles and set all randomized/cell flags to zero.  Commit `93a449f` therefore
implements the negotiation change as the complete deterministic `composite`
profile, selected by `Config.nego_policy="leader_replica"`, not by a game hash
or runtime flag.  Every supported buyer turn executes the frozen full 7aidara
price/accept/walk/message policy; every seller turn retains the current seller
price/acceptance stack (the winning half in the motivating window) and adds the
57/57 exact observed seller-message table where supported.  Unsupported or
malformed states fall through to the total current policy.  The semantic buyer
wire owns downstream price repair, preventing a legacy postcondition from
silently creating a hybrid.

`composite` remains unchanged for bargaining and keeps its existing persuasion
configuration.  `champion`, `hardliner`, and `conceder` retain their existing
whole negotiation policies.  The operator's launch map sends both Agent 5 and
Test 4 to `composite`; no process was restarted or signalled, and no
`arms.json`, `control.json`, bargaining flag, or bargaining source was changed
by this commit.  Focused policy/invariance checks passed 59/59.  The broad
buyer-policy evidence motivating this whole-policy promotion was candidate
`+1.116/game` (n=44) versus control `+.247/game` (n=47), a `+.869/game` point
lift with an inconclusive interval and a negative historical Agent 5 stratum;
this is an urgent deterministic deployment under operator direction, not a
claim that the old randomized promotion gates passed.  Measure the clean
post-launch profile window without conditioning on deals.

Live follow-up: Test 4 / slot `randomized` drained with zero games abandoned and
started `--probe composite` at `T0=1787602730` (01:48:50 IST).  Its first
supported buyer action at `1787602751.936849` carried
`plan.source=leader_replica`: hidden unknown-horizon buyer type `1.0`, exact
7aidara rejection/counter `83.0`, and the exact buyer sentence.  This proves
whole-profile routing and wire ownership, not outcome value.  Agent 5 remained
on its pre-boundary process at this checkpoint.

## 2026-08-24 — direct-leader opening copy activated on research slots

Codex activated `GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB=1` on `champion`,
`hardliner`, `randomized`, and `composite` at the clean common first-action
boundary `T0=1787571320` (17:05:20 IST). Every target process had naturally
rotated onto pushed commit `8a21e8e`; no process was signalled, drained, or
restarted for deployment. The final overlay write was at `1787571316`, four
seconds before T0. `conceder` / Test 3 remains unarmed, and no bargaining flag
or bargaining code was changed.

This is the default-off per-game 50/50 direct-leader arm described below. It
changes only the first hidden unknown-horizon outgoing price in seller
.8B/1.0B and buyer 1.2B/1.5B cells, to 1.485B or .81B respectively. The running
seller-1.2/buyer-1.0 first-offer probe and cap-10 terminal probe are disjoint;
`HIDDEN_POLICY_V1` and `HIDDEN_FLOOR` were absent on all four slots at
activation. The first post-T0 assignment was a composite buyer-1.2 hash control
and retained its ordinary counter. The first emitted treatment wire was a
composite seller-.8 ask at exactly 1.485B; a Test 4 candidate buyer-1.5 accepted
immediately and correctly stayed in the ITT without emitting a treatment price.
Across the first eight assignments, every applicable wire reported
`wire_ok=true`. This verifies live mechanism and cohort semantics, not value.

Read with `scripts/live_percentile.py --ab hi-extreme-open --since 1787571320
--slots champion,composite,hardliner,randomized`. Do not decide before 100
resolved games per arm and 15 per own-type/arm, and never promote from its local
hidden-pooled diagnostic. Official per-game score CI, close-rate noninferiority,
all subgroup signs, unresolved outcomes, cross-fleet duplicate IDs, and exact
wire integrity remain the precommitted gates.

## 2026-08-24 — direct-leader opening copy built, default OFF

Codex reconstructed the current top negotiation agents from direct encounters,
without conditioning on deals. Clod/Athena/doodod are at
2918.75/2840.38/2649.25 and appear in 47/38/69 of our negotiation games. In
hidden cap-10 plus unknown-horizon games their seller opening medians are
1.488/1.490/1.485B (n=10/8/12) and buyer medians are
.8108/.8075/.810B (n=9/7/14). This validates the literal behavior to copy, not
the causal value of copying it.

`GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB=1` is a default-off 50/50 per-game arm
that copies 1.485B/.81B on the first outgoing hidden unknown-horizon price in
seller .8B/1.0B and buyer 1.2B/1.5B cells only. It changes no decision and
falls back to the full current policy after one rejection. These types exclude
the running first-offer probe's seller 1.2B/buyer 1.0B cells and the dead
seller 1.5B/buyer .8B cells, so all live negotiation measurements remain
disjoint. Broad hidden policy/floor flags make the arm inert rather than
contaminate its hash control.

Exact champion-stack reachability on 1,000 paired games (seed 1907) passed at
100 eligible / 49 fired / 49 changed final wires. Focused tests are 88 passed;
the full suite is 1,048 passed with only the two predeclared bargaining
failures. The reader cohorts at the first pre-action turn, verifies literal
wires, retains unresolved outcomes, guards cross-fleet duplicate IDs, and
labels its hidden-pooled score non-promotion-grade. The code must land inert and
load through natural rotations before any arm boundary is recorded. Test 3 is
not a research slot. No bargaining code or flag was changed.

## 2026-08-24 — hidden cap-10 terminal counter deployed on research slots

Codex activated `GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB=1` on `champion`,
`composite`, and `randomized` at the clean common cohort boundary
`T0=1787568551` (16:19:11 IST). `hardliner` and the overall contender
`conceder` remain unarmed. This is a negotiation-only, per-game 50/50 arm. It
changes exactly the round-9 counter attached to a hidden cap-10 buyer-1.2
rejection to `B+$0.01`; accept, walk, seller, earlier-round, complete-info, and
all bargaining actions remain unchanged.

The experiment is disjoint from the running hidden unknown-horizon first-offer
probe. Test 4's first-principles module owns only complete single seller,
complete cap-10 buyer, and hidden single seller cells, so it cannot shadow this
hidden cap-10 buyer arm. Champion's exact live-stack reachability preflight
(1,000 paired games, seed 1701) reported 19 eligible, 10 fired, and 10 changed
wire actions; representative changes were `.989676B -> B+$0.01` at three
scales. The earlier 3,000-game paired check reported 57/20/20.

The primary cohort begins at the first matching buyer decision, not at terminal
reach, and includes agreements, no-deals, walks, timeouts, and unresolved games.
Promotion still requires official per-game score candidate-control 95% CI above
zero, close-rate point estimate positive with lower bound above -2pp, exact wire
integrity, and no material scale/message reversal. Read with
`scripts/live_percentile.py --ab hi-terminal --since 1787568551 --slots
champion,composite,randomized`. Bargaining code and bargaining flags were not
changed.

## 2026-08-24 — support ladder rejected; clean first-offer probe replaces it

This entry explicitly supersedes the support-ladder entry immediately below.
Independent mechanism review found that the ladder bundled an unproved 95%
claim, a four-offer hold, and deterministic support ordering; several apparent
"strong opponent" landmarks also came from failed no-deal/walk trajectories.
The ladder implementation, reader, flag, and tests were removed before any live
deployment.

The replacement is `GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB=1`, assigned per game
as `sha256("nego_hi_uncapped_first_offer_v1|" + game_id) % 3` to `control`,
`share80`, or `share95`. It is eligible only in hidden, explicitly
unknown-horizon negotiation for seller 1.2B and buyer 1.0B—the two own types
with exactly one strictly feasible counterpart. It changes only the first
outgoing price (seller: 1.44B/1.485B; buyer: .84B/.81B) and falls back to the
current policy after a rejection. Buyers who accept before emitting a price
remain in the intent-to-treat cohort. Broad hidden-policy/floor flags make the
probe inert so its control cannot be silently contaminated.

Deployment is now live on `champion`, `composite`, and `randomized`, with the
clean common cohort boundary `T0=1787567218` (15:56:58 IST). `hardliner` remains
unarmed pending evidence and `conceder` remains untouched. Pre-boundary wire
confirmation observed exact share95 prices at 1.485B (seller) and .81B (buyer)
on Test 4 plus an unchanged hash-control buyer action on Agent 5; all three
reported `wire_ok=true`. Test 4 entered the negotiation top-50 at rating
2077.54 / displayed rank 24 before any eligible probe exposure, so that move is
baseline variance and must not be attributed to treatment.

The first common-boundary read had 7 assigned games, 4 resolved and 3 active.
All four resolved without agreement; hidden-pooled diagnostic percentile was
control .4028 (n=1), share80 .4028 (n=1), and share95 .3807 (n=2), with zero
wire failures. This is explicitly no decision. Structural feasibility is only
25% in both eligible own-type cells, and the observed opposing bids/asks were
far outside our reservation values, so an early all-zero draw is unsurprising.

Production-context shadowing over Test 2's latest 20,000 turns found 47 eligible
first-turn games: 12 control, 18 share80, and 17 share95, split 24 seller / 23
buyer. All 35 candidate price opportunities fired and changed the wire action;
examples reproduced .81B, 1.44B, and 1.485B exactly. Focused verification is
139 passed; the latest full suite is 1,016 passed with only the two predeclared
bargaining failures. No bargaining code or configuration was changed.

Promotion requires joined official per-game scores: candidate-control 95% CI
above zero, close-rate lower bound above -2pp, zero wire failures, and no
material role/scale reversal. The local hidden-value-pooled report is explicitly
diagnostic and cannot promote the arm. The operator transferred deployment
ownership to Codex on 2026-08-24. Deployment must use natural process rotation;
do not signal or drain live agents and do not arm Test 3, preserving its
rank-one bargaining configuration.

Direct `pending_ids` remeasurement found 93,336 locally missing outcome
artifacts across the five slots; the older collector line saying 11,737
"outstanding before pass" is therefore not a reliable fleet-total estimate.
The collector now recognizes both `results.jsonl` and `games/<id>.json`, and
splits each API budget evenly between the oldest and newest missing IDs. The
store deduplication is a correctness fix but barely changed the current count
because those stores overlap heavily; newest-first capacity is what prevents a
fresh experiment from waiting behind the historical queue.

The official outcome collector was relaunched in detached screen
`glee-collector` as PID 37837 at 10 requests/minute/agent, with 50-call passes
and a 30-second inter-pass interval. Newest IDs run before the historical half,
so fresh outcomes land after roughly a five-minute API phase rather than waiting
behind a 20-minute pass; hourly request capacity is unchanged. The older
supervisor process predates collector supervision, so collector health must be
monitored directly until a safe supervisor refresh is available.

## 2026-08-24 — hidden no-limit support ladder implemented, default OFF

`GLEE_NEGO_HI_UNCAPPED_LADDER_AB=1` now arms an independent per-game experiment
with assignment `sha256("nego_hi_uncapped_ladder_v1|" + game_id) & 1`. It is
eligible only for hidden-information, explicitly unknown-horizon negotiation
with a supported own grid value and at least one strictly feasible counterpart
type. Complete-information, cap-10, single-round, seller-1.5, buyer-.8, missing
id, and off-grid states are unchanged. When armed it owns both hash arms in this
scope, preventing `HIDDEN_POLICY_V1` or `HIDDEN_FLOOR` from contaminating its
control.

The localization is from Test 2's latest 100 official dashboard results: hidden
unknown-horizon n=27 averaged `-1.604` rating/game, while hidden cap-10 n=19 was
`-0.189`, hidden single n=27 was `+0.489`, complete cap-10 n=8 was `+2.588`, and
complete single n=8 was `+4.525`. The broad `HIDDEN_POLICY_V1` is therefore not
recommended: a 6,043-turn shadow shows it makes five of six own-type/role cells
harder and would unnecessarily touch the non-negative capped horizon.

The candidate is a support-screening ladder, not a smooth concession curve. It
starts with the feasible hidden type giving us the largest zone, offers that
type 5% of its zone for four of our outgoing price opportunities, then advances
one grid type inward. Examples in B units: seller .8 uses 1.465, 1.18, .99;
seller 1.2 holds 1.485; buyer 1.2 uses .82 then 1.01; buyer 1.5 uses .835, 1.025,
1.215. These numbers reproduce observable landmarks from disclosed strong
no-limit opponents (approximately 1.484-1.485, .8205, and 1.212) while leaving
both sides strictly profitable at every compatible rung. The code never reads a
hidden opponent value and never changes AcceptOffer/RejectOffer/WalkAway.

On a recent Test 2 turn shadow, the runtime predicate found 316 eligible games,
159 hash candidates, and 159 candidates with a changed wire price. Representative
first prices move seller-1.0 `3.9706B -> 1.475B`, buyer-1.0 `.15833B -> .81B`,
and seller-1.2 `4.76472B -> 1.485B`. This establishes mechanism reachability on
live states, not outcome value. `scripts/live_percentile.py --ab hi-ladder
--since T0 --until T1` cohorts at first outgoing price and reports all assigned
outcomes plus reconstructed-zone diagnostics. Its pooled hidden CDF is diagnostic
only; promotion requires official per-game score.

Claude must run the prescribed `check_reachability.py` against the exact intended
stack before arming; Codex did not run it because it imports and executes the
explicitly prohibited replay/arena machinery. Restore/backfill the collector
before measuring. Do not co-arm this with `HIDDEN_POLICY_V1` or the cap-10
terminal arm. The precommitted rule is official-score 95% CI above zero,
close-rate lower bound above -2pp, positive reconstructed capture ITT, no
mechanism failure, and no material role/type sign reversal. The 95% claim and
four-offer hold are judgments under test, not validated constants.

Focused support-ladder/reader/legacy-policy/terminal/bargaining-isolation tests:
118 passed. Full suite: 1,004 passed; only the two AGENTS.md-predeclared
bargaining failures remain (`test_bargaining_horizon_floor` and the bargaining
live-grid drift alarm). No bargaining behavior, live configuration, fleet
process, API key, deployment file, or log was changed.

## 2026-08-24 — hidden late-accept arm rejected and removed

This entry explicitly supersedes the hidden unknown-horizon late seller
acceptance section below. The original public-corpus calculation did not compare
accept-now with the control trajectory's actual continuation; in effect it
rewarded rescuing a rejected bid without charging the candidate for later deals
the control secured at a better price.

The corrected replay used the exact official full-configuration CDF over all
32,403 public trajectories. In the matching hidden unknown-horizon seller cohort
(4,050 games), 375 decisions were exposed and 156 would change. Accepting every
strictly profitable bid on an even round at or after round 4 changes exact
percentile by `-0.06628` per exposed decision, bootstrap 95% CI
`[-0.08183,-0.05096]`; cohort ITT is `-0.00614`, a total loss of `-24.85`
percentile points. Example: a 1.0B-cost seller accepting 1.1B gets a 0.218
percentile, while the observed continuation closes at 1.2B for 0.364.

`GLEE_NEGO_HI_UNKNOWN_ACCEPT_AB`, its assignment helper, live reader,
reachability hook, and dedicated tests have been removed before deployment.
The cap-10 buyer-1.2 terminal-counter arm remains intact and prospective. Do not
restore or arm broad profitable-bid acceptance. No bargaining behavior, live
configuration, fleet process, API key, deployment file, or log was touched.

## 2026-08-24 — cold finals are collector backlog, not identified abandonments

This corrects the immediately following ITT entry's `.05` imputation while
preserving its conclusion: first-principles promotion is blocked.

The separate outcome collector is not running.  `logs/collector.out` stops at
06:00 after three 2,000-record passes and reports 11,737 games still outstanding;
its stale singleton PID has no live process.  Meanwhile the supervisor log
shows the repeated sequence: server `active_games=0` for 365 seconds, then
SIGKILL.  At zero server games this does not strand play, but SIGKILL skips the
child's `finally: GameLog.finalize()`.  The process may in fact be spending those
365 seconds fetching hundreds of final states under the per-key rate limit.
Therefore “old turn + later results watermark + no local final” mixes actual
forfeits with completed server games whose local backfill was interrupted.

`scripts/live_percentile.py` no longer manufactures a `.05` score or non-close
for that state.  It emits `cold-missing` with score/outcome unresolved and blocks
promotion.  `scripts/orphan_watch.py` now includes collector-only
`games/<id>.json` records in its completed set and reports **cold missing local
outcomes**, not rating drag or known abandonments.  Explicit terminal timeouts
and server no-deals remain real outcomes.

`scripts/supervise.py` now owns `scripts/collect.py` as a read-only sidecar.  It
adopts an existing collector by PID, starts one at 10 requests/minute/key when
absent, records its PID in supervisor state, restarts it after exit, and stops it
gracefully with the supervisor.  This code is not live until Claude deploys the
new supervisor; Codex did not start, stop, or signal the current fleet or stale
collector.  A one-time authorized collector restart/backfill is still required
for the existing backlog.

For the first-principles complete cohort this means 18 locally recovered
outcomes and 64 unresolved, not 70 outcomes with 52 synthetic abandonments.
The result-only positive estimate and the synthetic-negative estimate are both
invalid for promotion.  Claude should restart/backfill `scripts/collect.py`
through the authorized operational workflow, let the 64 outcomes recover, then
rerun `--ab fp-complete --since 1787534215 --slots randomized`.  No fleet process,
log, restricted config, or key was touched by Codex.

The new exact open-claim reader is
`scripts/live_percentile.py --ab open-claim-official --since
1787425367.073369 --slots randomized`.  Before the backlog correction it exposed
996 synthetic/terminal observations and a candidate-control `+0.0662`, but that
number must also be rerun after backfill.  The locally recovered subset and the
ongoing randomization still point to the already-live policy's strongest cells
(cap-10 buyer and unknown seller); no new unknown-buyer floor promotion is
claimed.

## 2026-08-24 — first-principles promotion withdrawn after ITT survivorship audit

This entry supersedes the “corrected Test 4 promotes complete-information
cells” entry below.  That read still selected games with fetched terminal
artifacts.  A first-turn cohort reveals the omitted mass and does not support
promotion.

`scripts/fit_official_negotiation_seed.py` now builds
`models/negotiation_seed_cdf_full.json` from the official 32,403-game public
corpus.  The checked-in artifact has all 1,152 literal role cells:
3 horizons x 2 information conditions x 2 message modes x 3 scales x 16 value
pairs x 2 roles, with 53-58 observations per cell.  The corresponding
`sim/official_negotiation_seed.py` scorer requires both values and never pools
a hidden counterpart value.  This closes the old local-CDF error where “same
configuration” silently omitted the valuation pair.

`scripts/live_percentile.py --ab fp-complete --since 1787534215 --slots
randomized` is the reproducible corrected reader.  It cohorts at our first turn
before the randomized action, uses the action path's pure `nego_fp|` assignment,
joins both terminal stores, counts calibrated cold omissions as `.05`
abandonments, leaves fresh omissions unresolved, excludes fleet self-play from
the pooled estimate, and scores complete cells against the full official seed
key.

At about 14:00 IST the complete-information cohort contained 82 assigned games.
Seventy were scoreable under the existing cold-omission rule, including 52
aged missing finals classified as abandonments, and 12 remained unresolved:

- cap-10 buyer: control `0.2028` (n=20) vs candidate `0.2760` (n=7), delta
  `+0.0732`, normal 95% CI `[-0.2488,+0.3953]`; close `20.0% -> 28.6%`;
- single seller: control `0.3023` (n=18) vs candidate `0.2595` (n=25), delta
  `-0.0428`, CI `[-0.2701,+0.1844]`; close `33.3% -> 24.0%`;
- pooled complete: `0.2499 -> 0.2631`, delta `+0.0132`, CI
  `[-0.1574,+0.1838]`; close `26.3% -> 25.0%`.

The prior `+0.3221` / `+0.1018` promotion claim came from the minority of games
that had terminal records and therefore selected away the dominant failure
mode.  Whether a cold omission is ultimately an opponent stall, collector gap,
or competition abandonment remains operationally worth diagnosing, but it
cannot be dropped from an ITT policy comparison.  `GLEE_NEGO_FP_COMPLETE_ONLY`
remains default OFF and is no longer recommended for Test 2.  Continue the Test
4 randomization until unresolved outcomes settle; promotion again requires the
per-cell exact-score CI above zero with no close regression.

The two disjoint hidden-information arms in the next entry are unaffected and
remain prospective/default OFF.  Focused exact-CDF/reader/first-principles/
bargaining-isolation verification: 46 tests passed.  No bargaining behavior,
live flag/configuration, fleet process, API key, deployment file, or log was
changed.

## 2026-08-24 — two hidden-information negotiation arms ready, default OFF

Two independent, per-game randomized mechanisms are implemented.  Neither is
live, neither shares a salt with an existing experiment, and they must not be
co-armed with `GLEE_NEGO_HIDDEN_POLICY_V1` during their first measurement.

### Hidden cap-10 buyer 1.2B terminal counter

`GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB=1` assigns by
`sha256("nego_hi_cap10_buyer12_terminal_v1|" + game_id) & 1`.  It is eligible
only on a hidden-information, known cap-10, round-9 buyer `RejectOffer` carrying
a counter, with our value exactly `1.2*base`.  Treatment makes the final wire
counter exactly `base+$0.01` and returns before broader price guards; control is
byte-identical to the existing stack.  Accept/walk and every earlier action are
unchanged, and no hidden seller value is read.

Measured Aug 22-24: 234 matching games, 85 agreements, 118 no-deals, 31 walks.
Structural feasibility is 50% (about 117 games), but about 32 feasible games
were not closed.  Eighty-one no-deals carried a terminal bid below the `1.0B`
seller grid point; median terminal bid was `0.989676B`.  `base+$0.01` is
strictly profitable for both seller types that can trade with a `1.2B` buyer.
This response is not point-identified—current opponents can still reject—so it
is a randomized trial, not an immediate promotion.

`scripts/live_percentile.py --ab hi-terminal --since T0 --until T1` cohorts at
the buyer's first decision, before terminal reach or outcome, and therefore
keeps early agreements, walks, no-deals, timeouts, and unresolved results in
the ITT.  It verifies every candidate terminal counter equals `base+$0.01`.
Its local percentile is explicitly labeled a hidden-value-pooled diagnostic;
it is not the official full-configuration score.

Reachability on 3,000 paired negotiation games: eligible 57, fired 20, wire
action changed 20.  Examples moved `0.989676B -> 1.0B+$0.01` at all observed
scales.

Precommitted promotion: official candidate-control per-game score 95% CI above
zero; close-rate point estimate positive and lower 95% bound above -2pp; zero
wire failures; no material sign reversal by scale or message mode.  Negative
official-score CI or any wire/mechanism failure rejects.  Rough sample need is
205-280 games/arm (about four to six days at the observed rate).

### Hidden unknown-horizon late seller acceptance

`GLEE_NEGO_HI_UNKNOWN_ACCEPT_AB=1` assigns by
`sha256("nego_hi_unknown_accept_v1|" + game_id) & 1`.  In treatment only, a
hidden-information unknown-horizon seller with cost multiplier in
`{1.0,1.2,1.5}` accepts the first strictly profitable buyer bid on an even
round at or after round 4.  The override changes only the decision; offers,
targets, continuation values, and hidden values are untouched.

On all 32,403 official public negotiation games, the deterministic accept
counterfactual gained `+0.07138` exact percentile across 352 eligible games
(bootstrap 95% CI `[+0.04940,+0.09616]`), `+0.004654` ITT inside hidden
unknown-horizon games, and about `+0.000775` over negotiation (roughly +6.2
long-run rating points).  A chronological 70/30 design chose the rule on the
early corpus and reproduced `+0.09745` across 99 untouched later eligible games
(`+0.005955` hidden-cell ITT); signs were positive across message modes and all
three scales.

Reachability on 3,000 paired negotiation games: eligible 90, gate fired 48,
wire action changed 9.  The gap is expected because many eligible profitable
bids are already accepted in control.  Read with
`scripts/live_percentile.py --ab hi-accept --since T0 --until T1`, cohorting on
the first eligible incoming bid before our action.  Promote only if the
prospective official per-game score CI is above zero.  The local pooled-CDF
number is diagnostic only.

Focused verification for both mechanisms, their readers, production/analyzer
hash parity, and bargaining isolation: 75 tests passed.  No bargaining code,
live flag/configuration, API key, fleet process, or deployment file was touched.
Full suite: 980 passed; only the two AGENTS.md-predeclared bargaining failures
remain (`test_bargaining_horizon_floor` and the bargaining live-grid drift
alarm).  Scoped `git diff --check` passes.  Claude remains the only deployer.

## 2026-08-24 — corrected Test 4 promotes complete-information cells only

Test 4's first-principles A/B was re-read only after commit `f32c334`, using
timestamp `1787534215` as the cohort boundary.  The finished cohort has 157
eligible games (83 control, 74 treatment).  Complete-information outcomes use
the exact official seed CDF for the full value-pair configuration; the hidden
cell is reported as expectation across the four possible counterpart-value
CDFs because a hidden no-deal does not reveal that value.

- cap-10 complete-info buyer: n=27, percentile `0.5706 -> 0.8927`, delta
  `+0.3221` (bootstrap 95% CI `[+0.1825,+0.4677]`), close rate 100% in both;
- single-round complete-info seller: n=45, `0.8086 -> 0.9104`, delta `+0.1018`
  (`[+0.0254,+0.1618]`), with one treatment no-deal;
- single-round hidden seller: n=85, `0.5936 -> 0.5843`, delta `-0.0093`
  (`[-0.1005,+0.0823]`), unresolved;
- all eligible: `0.6373 -> 0.7280`, delta `+0.0907`
  (`[+0.0144,+0.1666]`).  Reweighting by observed eligible-cell frequency gives
  `+0.0795`, about +636 game-rating points inside eligible cells.

`GLEE_NEGO_FP_COMPLETE_ONLY` is now a default-OFF promotion gate in
`first_principles.owns`.  When explicitly enabled it lets hidden games fall
through to the existing strategy while retaining the two measured-positive
complete-information cells.  It does not change Test 4 or any current agent
while absent.  Intended Test 2 promotion configuration is
`GLEE_NEGO_FIRST_PRINCIPLES=1`, `GLEE_NEGO_FP_ALWAYS=1`, and
`GLEE_NEGO_FP_COMPLETE_ONLY=1`; Claude remains the only fleet deployer.

Focused verification: 31/31 first-principles, wire-integrity, and bargaining-
isolation tests pass.  No bargaining code, live flag/configuration, fleet
process, API key, or deployment file was touched.

**Objections / next falsifiable tests:**

1. The official docs say percentile is against the same configuration and role,
   and define the 960-cell grid as including valuations.  Therefore the local
   pooled hidden-value percentile model is not a promotion oracle.  Keep hidden
   randomized and score against the exact latent value-pair once recoverable.
2. Game `e6765abc-2cc5-4998-b5be-77a5695f204d` is a current counterexample to
   the old absolute crumb rule: Scarlett rejected a seller ask of 1,199,999.99
   with buyer value 1,200,000.  Do not increase `EPS` from one cent globally;
   test any larger crumb as a separate game-hashed arm.
3. Eligible cells were about 21% of recent negotiation games, so complete-only
   promotion is expected to add roughly 135-145 overall negotiation rating
   points, not enough by itself to reach the 0.55 target (rating 2400).  The
   already-implemented, default-off hidden-policy V1 should be the next disjoint
   randomized arm after its reachability and scoring reader are revalidated.

## 2026-08-23 — buyer-selectivity red team rejects the historical gain

The user's `q_rank=0.4987` calculation for text `p=.5,r=1.2,S=0` is correct,
but it is not a stable policy threshold.  The exact frozen shadow was reproduced
from the five active-slot `results.jsonl` files only: first-seen game-id
deduplication, completed persuasion buyer records, prior value no greater than
price, sorted by `(ts, game_id)`, oldest 5,181.  Window:
`2026-08-19T11:42:58.172361Z` through `2026-08-22T22:25:54.865690Z`.  Frozen
q-prior and CDF hashes still match the precommit.

At logged pre-decision accumulated-payoff quartiles, the one-step rank threshold
is below money breakeven at 35/54 displayed state points and above it at 17/54,
with two ties.  At the cell median the split is 8 lower / 9 higher / 1 tie.
Weighting the 27,493 actual purchase states reverses the S=0 intuition:
`q_rank>q_money` 16,973 times, `q_money>q_rank` 9,843, 664 ties, 13 flat.
Large empirical-CDF atoms make the sign move with S.  More importantly, raw
`F(S)` is a terminal/fixed-continuation identity; before the last round the
correct value includes future payoff, posterior transitions, and information
revealed by a purchase.  It is not valid to substitute the raw threshold into
all 20 rounds.

The old full candidate still reproduces exactly: 27,493 historical buys become
8,683; 12,720 highs and 6,090 lows are blocked.  Under the requested one-step
proxy and the candidate's counterfactual S, 8,572 blocked buys are rank-positive,
including 6,283 highs.  Reason precedence:

- bought-low strike: 5,816 blocked / 4,305 rank-positive;
- no prior decline: 11,974 / 4,208;
- current signal not explicit yes: 1,007 / 50;
- posterior below money cutoff: 13 / 9.

So the mass error is not caused by the money threshold.  A sequential shadow
also shows the cutoff is nearly inert: prior-decline-only `+.01337`, adding
explicit yes `+.01484`, adding money cutoff `+.01445`, adding strike `+.01209`.
The fitted gain comes almost entirely from text (`+.01248` overall contribution);
binary contributes `-.00039`.  Largest positive cells are text `.8/1.25`,
`.5/2`, and `1/3,3`; binary `.8/1.25`, `1/3,2`, and `.8/1.2` drag.

The overfit objection is decisive.  A chronological 70/30 artifact cross-fit at
`2026-08-21T16:52:32Z` fitted the q prior on 6,013 earlier buyer games and the
CDF on 9,048 earlier persuasion games, then scored 1,555 strictly later eligible
games with every CDF cell supported (n=270-351).  Early in-sample was `+.01442`
`[+.00890,+.01994]`; later full gate was `-.00131`
`[-.01111,+.00848]`, and no-strike was `+.00684`
`[-.00113,+.01482]`.  Neither survives.  This is artifact-disjoint but not a
pristine model-selection holdout because the policy itself was designed after
viewing the full corpus; that limitation makes the failure stronger, not weaker.

The no-look-ahead state is "has an explicit decline occurred before this
decision", never eventual seller type.  In explicit-current-yes purchases,
post-decline beats pre-decline after exact cell+round adjustment by +11.72pp
high rate, +.2355 price-units per buy, and +.01554 local fitted rank.  The
predictive gradient therefore reproduces.  But pre-decline explicit-yes buys
themselves earn +.1455P/buy and local rank +.00036 with a CI spanning zero.
This action-selected observation does not identify a benefit from vetoing them.

Implementation response: do NOT replace money breakeven with the myopic raw-rank
threshold, and do NOT run the main arm.  The one-low stop is no longer bundled.
`GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB` is a separate default-off, independent
per-game hash arm (`pers_buyer_selectivity_strike_v1|`).  When both experiments
are armed this creates strike/no-strike cells inside candidate and matching
behaviorally inert controls.  `scripts/live_percentile.py` records and reports
those pre-treatment variants separately; more than one bought low is a
falsification only in the strike-assigned cell.  Neither flag was armed and no
live fleet/process or restricted file was changed.

Verification: 24 focused selectivity/ITT tests pass.  The mandated full suite is
843 passed with only the two failures pre-declared by AGENTS.md: bargaining's
450-vs-468 horizon-floor expectation and the live `horizon_known` grid drift.
Scoped `git diff --check` and compilation pass.  No replay-eval, arena, red-team,
fleet, or reachability command was run.

## 2026-08-23 — persuasion buyer selectivity arm implemented, default OFF

`GLEE_PERS_BUYER_SELECTIVITY_AB=1` arms a per-game A/B only in persuasion buyer
games with `v>u`, `price>u`, and prior money value
`p*v+(1-p)*u <= price`. Assignment is
`sha256("pers_buyer_selectivity_v1|" + game_id) & 1`. The flag is absent/OFF by
default. Candidate is strictly an extra veto over the current buyer; it cannot
revive an existing rejection. Prior-positive games return before assignment,
so the protected `p*r>1` corpus (3,452 games, 84.08% of rounds bought, mean
payoff `21.429P`) is byte-identical with the arm armed.

The candidate requires all four conditions for a purchase:

1. at least one historical message is an explicit decline;
2. the current message is an explicit recommendation under the tri-state
   parser, independent of the fleet's legacy-parser flag;
3. the fitted posterior `P(high | current recommendation)` strictly exceeds
   `(price-u)/(v-u) + margin`;
4. no previously purchased unit in the game was low.

The permanent one-low strike is deliberate. A decline is not a costly or
directional signal under this gate: while the buyer waits, a pre-decline yes
would also make no sale, so the seller can decline a low at zero on-path cost
and unlock 19 later rounds. One decline only proves
`P(no|high)>0` or `P(no|low)>0`; it does not prove recommendations favor highs.
The strike caps direct post-unlock loss at one price. Hard never-buy is the only
zero-loss minimax rule, but it discards every selective-seller winner; the
strike is a bounded-loss hypothesis whose effect must be randomized.

The probability estimator is the existing six-point seller-type mixture over
low-quality recommendation rate `q={0,.125,.25,.5,.75,1}`, with a 2% high-unit
decline likelihood and mode/prior-bin weights fitted on 4,191 games. Candidate
recomputes it with parser abstentions preserved even when control uses the
legacy optimistic coercion. A single Beta/Laplace count model was rejected: the
fitted population is bimodal, and the declined unit's hidden quality supplies
no Bernoulli success/failure with which to bootstrap a Beta posterior. The
first-arm probability margin is `0.0` plus strict `>` because no measurement
identifies a positive margin and the blanket guard/LCB family is already
measured negative. `GLEE_PERS_BUYER_SELECTIVITY_MARGIN` exists only inside
candidate and must remain `0.0` in the first window.

The motivating money-EV algebra is valid with an important scope correction:
for posterior `q`, buyer payoff is
`q(v-price)+(1-q)(u-price)`, so buy iff
`q>(price-u)/(v-u)`; live `u=0` gives `q>1/r`. A genuinely always-recommend
seller has `P(high|yes)=p`. Therefore `p*r<1` is strictly negative money EV,
while `p*r=1` is zero EV, not negative. T2 and T3 are equality cells (`.8*1.25
= 1`, `(1/3)*3 = 1`). T6's stated 11 highs / 8 lows yields `+25P`, not `+13P`;
`+13P` corresponds to 8 highs / 11 lows. T3's five initial lows are not seller
front-loading if it said yes on every unit: nature draws iid and the event has
probability `(2/3)^5 = 13.17%`.

The universal claim is also false for the competition objective. Rank applies a
nonlinear same-cell CDF `F` to total payoff. In the fitted text `p=.5,r=1.2`
cell at zero accumulated payoff, `F(-P)=.0284`, `F(0)=.4498`, and
`F(+.2P)=.8734`; one blind buy has expected percentile
`.5*.0284+.5*.8734=.4509`, narrowly above passing, despite money EV `-.4P`.
This is a counterexample, not evidence to buy that cell.

Read-only shadow reconstruction of the oldest 5,181 eligible games found
27,493 historical buys. The full candidate retains 8,683, blocking 12,720 high
winners and 6,090 lows. Mean payoff falls `1.1555P -> .7774P`, while fitted
percentile changes `+0.01209`, normal 95% CI `[+.00718,+.01701]` over 5,170
scoreable paired games. The pure pre-decline veto alone blocks 11,974 buys
(8,605 highs, 3,369 lows) and forgoes a net 1,150.9 price-units of historical
payoff. The one-strike insurance removes 5,604 additional buys and reduces the
shadow percentile gain from `+.01445` to `+.01209`. This replay holds seller
messages fixed and observes no quality on skipped rounds, so it is screening
evidence only, not a causal estimate.

The supplied never/sometimes split is not exactly reproducible without its
semantic classifier. On the same 5,181 games, explicit tri-state parsing yields
1,443 never-decline / 3,738 eventual-decline games; alternate committed parsers
yield 1,174/4,007 or 1,266/3,915, not 1,058/4,123. More importantly, eventual
decline is future, post-treatment information and cannot define the primary
policy comparison.

**Pre-committed falsification:** arm only after recording exact T0 and hashes
`pers_buyer_prior_v1.json=173e00273db5b2d5121080be0e6192c4ab12e1ea553b61ab22896bfb4a31787a`
and
`percentile_cdf_v3.json=bd3b313792951465624543612b09fb0ca5cc1708aee08a7a3dfb85f269e58ff9`;
do not refit either mid-window. Use
`scripts/live_percentile.py --ab pers-selectivity --since T0 --until T1`.
Primary is candidate-control mean percentile over every assigned eligible game,
never the eventual-decline subgroup. Promote only if the 95% CI is wholly above
zero; reject if wholly below; unresolved outcomes block promotion. Any candidate
pre-decline purchase or second bought-low is a mechanism failure. Report exact
cell/equality strata and one-decline sellers as diagnostics. The one-decline
attack is decline a low, then recommend 19 indiscriminately: a permanent unlock
would cost `19P(p*r-1)` in expectation (`-.76P` at `.8*1.2`, `-6.333P` at
`(1/3)*2`); this candidate permits at most one low purchase.

The prescribed `check_reachability.py` was not run because its import path uses
the explicitly prohibited replay/arena modules and it has no persuasion family.
Focused decision tests instead require eligible>0, veto-fired>0, and
action-changed>0, alongside default-off/hash-control identity and protected-cell
identity. Claude still owns independent verification and any live deployment.

Verification: 173 focused persuasion tests and 95 live-percentile tests passed.
The mandated full suite produced 840 passed and only the two failures explicitly
pre-declared by AGENTS.md: the bargaining horizon-floor expectation is
450/current 468, and the live bargaining `horizon_known` grid drift remains
significant. Scoped `git diff --check` and `py_compile` pass. No replay-eval,
arena, red-team, fleet, or reachability command was run; no live flag was armed,
and no restricted file or running process was changed.

## 2026-08-23 — grid-aware hidden negotiation policy implemented, default OFF

`GLEE_NEGO_HIDDEN_POLICY_V1=1` arms a new offer-only experiment.  The default
is absent/OFF.  Eligible games require `complete_information=false`, a
multi-round horizon, a supported own value/base, a present game id, and an own
type with positive prior probability of a strict ZOPA.  Each eligible game is
assigned by `sha256("hidden_policy_v1|" + game_id) & 1`, an independent salt.
Complete-information games, one-round games, seller `1.5B`, and buyer `0.8B`
are unchanged.  When the new flag is armed, it owns both hash arms and
suppresses the older `GLEE_NEGO_HIDDEN_FLOOR` path, so an accidental second
flag cannot contaminate control.

The candidate is a grid-aware screening curve:

| Role / own type | assumed P(strict ZOPA) | opening | prior terminal boundary |
|---|---:|---:|---:|
| seller `0.8B` | 75% | `1.395B` | `0.950B` |
| seller `1.0B` | 50% | `1.425B` | `1.150B` |
| seller `1.2B` | 25% | `1.455B` | `1.425B` |
| seller `1.5B` | 0% | unchanged | existing dead-game path |
| buyer `1.0B` | 25% | `0.830B` | `0.850B` |
| buyer `1.2B` | 50% | `0.860B` | `1.050B` |
| buyer `1.5B` | 75% | `0.905B` | `1.275B` |
| buyer `0.8B` | 0% | unchanged | existing dead-game path |

The opening claims 85% of the largest support-compatible positive zone.  Its
purpose is screening: it is inside a possible opponent's support, unlike the
measured 3.97x-own-limit opening, so a favorable type can accept while paying
us a high share.  The terminal boundary claims 75% of the narrowest still
compatible positive zone.  This makes the answer to “higher or lower than flat
1.15?” type-dependent: seller `0.8B` must go lower (`0.95B`) to retain the
buyer-`1.0B` zone, while seller `1.2B` can hold higher (`1.425B`) because only
buyer `1.5B` is feasible.  The buyer side is the exact zone-share analogue.

For capped games, the five H=10 price opportunities follow a squared clock
with progress `0, .0625, .25, .5625, 1`; both seats reach their boundary on
their last price opportunity.  In an uncapped game the linear clock is capped
at `.85`, so its square traverses at most 72.25% of the opening-to-boundary
distance.  The uncapped cap, squared timing, `.85` opening share, and `.75`
boundary share are judgments, not identified constants.

The schedule never reads opponent concession speed.  A static price therefore
cannot make us concede faster.  It uses only the best price level as a rational
one-sided type bound (`buyer bid <= buyer value`, `seller ask >= seller cost`):
crossing a grid threshold can harden the terminal boundary, and a favorable
opponent price is never given back.  This is also a judgment: an irrational or
strategic loss-making offer invalidates the type inference, which the live arm
must test.

The implementation is a final `actions.coerce()` postcondition after strategy
and LLM planning.  It replaces an emitted candidate `product_price` but never
changes the selected decision or any plan/acceptance input.  Tests cover both
roles, every 75/50/25/0 own signal, the full H=10 wire sequence, uncapped cap,
history echo counting, static opponents, crossed type bounds, favorable offers,
hash parity, hidden-value sentinels, complete-info/one-round/dead exclusions,
default-off identity, and legacy-arm isolation.

`scripts/live_percentile.py --ab hidden-policy --since T0 --until T1` now
reports, per slot and pooled:

- mean same-cell percentile with 95% CI;
- close rate with 95% CI;
- median/IQR reconstructed-zone share among positive-zone agreements;
- mean zone-capture ITT, where every non-close/abandonment contributes zero;
- role, own type, P(ZOPA), and horizon strata plus reconstructed closed-pair
  composition.

For an agreement, the seller and buyer payoffs sum to the true zone, so own
share is `own_payoff / (p1_payoff + p2_payoff)`.  Missing payoffs, off-grid
reconstructions, and zero/negative zones are counted explicitly and cannot
silently enter that ratio.  Cross-slot fleet self-play ids are detected before
eligibility and `--slots` filtering and excluded from the pooled independent
estimate.  First-exposure signal metadata survives abandonment, keeping its
zero in the correct stratum.  Conditional share remains selected on closing;
the ITT capture metric exists specifically to expose a false “share gain” made
by deleting low-share deals.

**Evidence versus judgment:** the evidence supports replacing the off-support
journey, conditioning on our own feasibility signal, avoiding reciprocal
concession, and targeting more than the measured 0.520 median closed-zone
share.  The 319 no-deal opening comparison is selected on failure and does not
prove openings have no causal effect.  The four-value axis is official, but
uniform independent hidden draws and the current joint support are local
reconstructions.  The field's move from 0.776 to 0.830 says any fixed constants
must be tested in a short contemporaneous window; it does not identify 0.85 or
0.75 as optimal.

**Pre-committed falsification / promotion rule:**

1. Primary outcome is candidate-control mean percentile.  Promote only if its
   95% CI is above zero; reject if its 95% CI is below zero; otherwise continue
   or call the arm inconclusive.
2. Close-rate non-inferiority margin is -2 percentage points (judgment, chosen
   because close rate is near its structural ceiling).  Promotion requires the
   delta's lower 95% bound above -2pp; reject if its upper bound is below -2pp.
3. Mechanism requires positive zone-capture ITT and at least +0.05 conditional
   median closed-zone share.  A higher conditional share with lower ITT capture
   is survivorship, not success.  Treat a non-positive median-share delta as a
   mechanism rejection after at least 200 reconstructed positive-zone closes
   per arm; the +0.05 and n=200 thresholds are judgments.
4. Inspect pair composition and role/horizon strata before promotion.  A gain
   produced only by dropping narrow zones, a seller/buyer sign split, or an H=10
   gain paired with an uncapped loss falsifies the proposed mechanism even if a
   pooled descriptive metric looks good.

Verification: prescribed reachability at 200 negotiation draws against
`replay_eval.DEFAULT_CONTROL` reported eligible 1,168, fired 589,
action_changed 589, PASS; the checker warns that this is a simulator snapshot,
so Claude must repeat against the exact intended live stack.  Focused
policy/reporting/floor tests passed 104/104.  The mandated full suite produced
811 passed and only the two AGENTS.md-declared bargaining failures
(`test_bargaining_horizon_floor`, expected 450/current 468, and
`test_sim_grid[bargaining]`, live `horizon_known` drift).  No live flag, fleet
process, `arms.json`, `control.json`, `.env`, or file under `logs/` was changed.
No replay-eval, arena, or red-team command was run; only the prescribed
reachability checker was invoked.  Claude still owns verification and deploy.

## 2026-08-23 — hidden-information concession floor implemented, default OFF

`GLEE_NEGO_HIDDEN_FLOOR=<F>` is a float flag with inert default `0.0`.  It is
eligible only when `complete_information` is literally false, our public role
is seller/buyer, our own visible value maps to a supported base through
`pricing.infer_base`, the game id is present, and
`sha256("hidden_floor|" + game_id) & 1` assigns treatment.  Hash-control games,
missing/off-grid inputs, non-finite/non-positive settings, and `F > 2` retain
the existing wire price.

The implementation is a final `actions.coerce()` price postcondition, after
heuristic/full-LLM choice and action repair.  For every emitted treatment
`product_price`, a seller submits `max(price, F*B)` and a buyer submits
`min(price, (2-F)*B)`.  The buyer expression is the additive reflection of
`F*B` around `B`: `B-(F-1)B=(2-F)B`; using `max` there would silently reverse
the protection.  The boundary is reapplied after cent rounding.  An
`AcceptOffer` has no price and returns before the flag is read, so neither the
plan nor any accept/reject threshold changes.  Complete-information games
continue through OPEN_CLAIM/CLAIM_FLOOR and are tested identical with this flag
armed.  A sentinel test also proves no hidden opponent-value key is read.

`scripts/live_percentile.py --ab hidden-floor` recovers the same hash and
reports mean percentile AND close rate for each arm, per agent and pooled.  It
uses the existing robust first-outgoing-price exposure cohort rather than the
results-only A/B path: both seats/all horizons are eligible; the result join
covers `results.jsonl` plus collector `games/<id>.json`; unknown-CDF outcomes
remain in the close denominator; cold abandonments count as percentile `.05`
non-closes; pending/invalid finals block promotion; and any negative terminal
close-rate point estimate prints the veto.  `--since/--until` bound the first
price exposure, so Claude must record the exact activation/disarm timestamps.

The generic reachability checker had its own hash-arm defect: its control play
left every game id at the simulator literal `local`, assigning all banked
states to one bit.  It now supplies the stable per-draw `sim-<seed>` id already
used by the paired harness.  Required checker result at `F=1.15`, 200
negotiation draws against `replay_eval.DEFAULT_CONTROL`: eligible 1,354, fired
301, action_changed 301, PASS.  The checker warned that this control is a
simulator snapshot, so Claude must repeat it against the intended live stack
before deployment.

Read-only 30h calibration over five active result streams, deduplicated by
game id: 4,074 hidden negotiations, 1,300 closes.  Recommended first treatment
is **F=1.15** (seller `>=1.15B`, buyer `<=0.85B`), chosen from the observed
accepted-price support rather than a midpoint:

| F | buyer cap | games whose historical price would change | existing closes whose accepted own price would change |
|---:|---:|---:|---:|
| 1.10 | 0.90B | 553 / 4,074 | 168 / 1,300 |
| 1.15 | 0.85B | 713 / 4,074 | 183 / 1,300 |
| 1.175 | 0.825B | 894 / 4,074 | 257 / 1,300 |
| 1.20 | 0.80B | 944 / 4,074 | 262 / 1,300 |

Moving 1.10 -> 1.15 buys another `.05B` while exposing only 15 additional
historical closes; moving just above 1.15 crosses a large accepted-price atom
and exposes 74 more.  At 1.15, sellers expose 146/2,053 games and 52 accepted
own offers; buyers expose 567/2,021 and 131 accepted own offers.  The buyer arm
is the veto: 131/143 accepted buyer-originated offers would have been clipped,
and observational logs cannot say whether those unplayed prices would close.

**Objections / proposed validation:**
1. The supplied “field seller 1.449” row is actually counterparty buyer bids in
   games where we sell, and “field buyer 0.826” is counterparty seller asks in
   games where we buy; neither is a same-role policy path.  Round buckets also
   change type composition as games close.  Use them as price-support context,
   not causal proof that matching either endpoint wins.
2. Retrospective hash balance before treatment is control n=2,050, close 31.32%,
   percentile .4939 versus candidate n=2,024, close 32.51%, percentile .4960.
   Thirty hours leaves roughly +/-2.9pp uncertainty on the close-rate
   difference.  Use a clean activation boundary and do not call a sub-1pp close
   difference identified at that sample size.
3. Any credible candidate close-rate loss, especially in buyer games, rejects
   or lowers 1.15 regardless of mean percentile.  If percentile improves with
   no close-rate penalty, test 1.175 in a separate randomized window; do not
   extrapolate through the accepted-price cliff.

Verification: 88 focused hidden/open-claim tests passed; the mandated full
suite produced 741 passed and only the two AGENTS.md-declared bargaining
failures (`test_bargaining_horizon_floor`, expected 450/current 468, and
`test_sim_grid[bargaining]`, live `horizon_known` drift).  No live flag, fleet
process, `arms.json`, `control.json`, `.env`, or file under `logs/` was changed.
No replay-eval, arena, or red-team command was run; only the prescribed
reachability checker was invoked.  Claude still owns verification and deploy.

## 2026-08-23 — complete-info opening claim + concession floor implemented, default OFF

This supersedes the never-deployed `GLEE_NEGO_CI_ASK_AB` entry immediately
below; there is one mechanism, not two.  The old flag and `ci_ask|` assignment
were removed.  `GLEE_NEGO_OPEN_CLAIM=<share>` and
`GLEE_NEGO_CLAIM_FLOOR=<share>` are independent floats with inert `0.0`
defaults, but both use the same per-game treatment assignment:
`sha256("open_claim|" + game_id) & 1`.  Hash-control games retain the existing
wire price.  A non-finite/non-positive value is inert, and a missing game id is
inert.

On a treatment game, OPEN_CLAIM replaces our first outgoing price in either
seat: the seller's standalone round-1 offer or, on the live protocol, the
buyer's first `RejectOffer` counterprice.  It includes one-round games.  The
price is `seller_value + share * span` for a seller and
`buyer_value - share * span` for a buyer.  CLAIM_FLOOR is then a lower bound on
our claimed share for every emitted `product_price`, including late rejection
counters; an already more ambitious price is retained.  Every price affected
by either knob is clamped to `[seller_value, buyer_value]`, including shares
above 1 and fractional ZOPA endpoints.  The action postcondition runs after the
strategy/LLM and only when the normalized action contains `product_price`.
`AcceptOffer` has no price and returns before either flag is read, so neither
the flags nor their assignment can change an acceptance threshold.

The complete-information marker is checked before role/value mapping.  A test
uses a hidden-state dict that raises if the opponent-value key is read, arms
both flags, and verifies that the unchanged price returns without that read.
This keeps hidden-information games entirely outside the mechanism.

`scripts/live_percentile.py --ab open-claim` recovers the exact `open_claim|`
hash and reports mean percentile plus close rate for each arm, per agent and
pooled.  It cohorts on each game's globally earliest logged outgoing price,
then applies `--since/--until`; a later counter cannot pull a pre-window game
into the cohort.  This includes both seats, every horizon, and every round with
a positive visible ZOPA.  The result join still covers both `results.jsonl` and
collector-only `games/<id>.json`; unknown-CDF terminals stay in the close-rate
denominator, unresolved outcomes are bounded and block promotion, and cold
missing results count as .05-percentile non-closes.  A negative candidate close
delta prints the close-rate veto.

Reachability registers both flags as final-action postconditions.  Codex did
not run `scripts/check_reachability.py`, because it imports and executes the
explicitly prohibited replay/arena path; Claude should later require
eligible>0, fired>0, action_changed>0 against the intended control stack.

Verification: 67 focused open-claim/ZOPA tests passed.  The mandated full suite
produced 707 passed and only the two failures pre-declared in AGENTS.md:
`test_bargaining_horizon_floor` (expected 450, current 468) and
`test_sim_grid[bargaining]` (`horizon_known` live-grid drift).  No live flag,
fleet process, `arms.json`, `control.json`, `.env`, or file under `logs/` was
changed; replay evaluation, arena, red-team, and reachability scripts were not
run.

**Objections / proposed validation:**
1. With both floats armed in one interval, `--ab open-claim` identifies the
   joint opening-plus-floor policy, not the contribution of either component.
   Separate homogeneous windows (one nonzero float at a time) are needed for
   component attribution; the requested bundle is still the primary test.
2. Arm exposure is not persisted.  Record the exact per-slot arm/value `T0`
   and disarm/value-change `T1`, then analyze that first-price interval.  Games
   whose first outgoing price predates T0 are deliberately excluded even if a
   later floor would have changed them after a mid-game arm.
3. A hidden-information analogue cannot use ZOPA share.  If built, randomize it
   under an independent salt and key the schedule on role, own value normalized
   by the public money scale, round/horizon, and bounds or a posterior inferred
   from opponent offers; do not infer an opponent value that the payload hides.

## 2026-08-22 — complete-info seller opening-ask arm implemented, default OFF

`GLEE_NEGO_CI_ASK_AB=<share>` is a float flag with an inert `0.0` default.  It
is consulted only for a standalone opening offer when `complete_information` is
literally true, both role-mapped values are finite and form a positive visible
ZOPA, our current player is the seller, the action type is `offer`, round is 1,
history and `last_offer` are empty, the horizon is not 1, and the game id is
present.  Every eligible game is assigned by
`sha256("ci_ask|" + game_id) & 1`.  Hash control keeps the already-computed wire
opening unchanged.  Treatment replaces only that opening with
`seller_value + flag_share * (buyer_value - seller_value)`, rounds it, then
clamps the literal wire price to `[seller_value, buyer_value]`; a flag share
above 1 therefore cannot submit an ask above the visible buyer value.  The arm
runs as a final action postcondition after heuristic/full-LLM pricing.  Decision
turns, reject/counter prices, acceptance thresholds, and every offer after the
opening do not read it.

The motivating longer-horizon observations remain hypothesis-generating only:
horizon 10 had 94.1% closes at the existing 0.50-0.65-span opening (n=188,
mean percentile .5571), and unbounded had 97.7% (n=217, .5024).  Horizon and ask
band were perfectly confounded, so the implementation comment explicitly says
that these observations establish no ask effect and that the hash experiment is
the identifying variation.

`scripts/live_percentile.py --ab ci-ask` recovers the identical pure hash and
cohorts from the actual eligible round-1 turn timestamp, not a later result-fetch
timestamp.  Use `--since T0 --until T1` (opening-time bounds, upper exclusive)
and `--slots` to isolate the period in which a chosen value was armed.  It joins
both `results.jsonl` and the continuous collector's `games/<id>.json`, prefers a
recognized terminal record over an active snapshot, and reports mean percentile
and close rate separately for each arm and pooled.  Agreement is a close;
`no_deal`, `timeout`, and `walked_away` are non-closes.  Unknown-CDF games remain
in the close denominator.  Missing results older than the calibrated 6,000s
orphan threshold and behind a later collection watermark count as percentile
.05 abandonments and non-closes.  Fresh pending and malformed terminal records
are shown separately with arm-wise best/worst close-rate bounds and make the
read non-promotion-grade.  A zero-eligible window exits nonzero.  Strategy
exception fallbacks now write the actual returned action as an ordinary turn in
addition to the error record, so fallback openings cannot disappear from this
intent-to-treat cohort; this changes logging only, not the returned action.

Reachability knows `GLEE_NEGO_CI_ASK_AB` as a final-action postcondition and its
eligibility predicate reuses the live visible-ZOPA coercion.  Codex did not run
the checker because it imports `replay_eval`/`sim.arena`, which the operator
explicitly prohibited.  Claude should later run the registered check with the
real target control stack and require eligible>0, fired>0, action_changed>0.

Verification: 97 focused/interaction tests passed.  The exact mandated full
suite produced 702 passed and only the two pre-existing AGENTS.md failures:
`test_bargaining_horizon_floor` (expected 450, current 468) and
`test_sim_grid[bargaining]` (`horizon_known` live-grid drift).  Tests cover flag
absent/0 and hash-control identity, both horizon 10 and unbounded treatment,
64-game runtime/analyzer hash parity, horizon-1 and hidden-information
exclusions, missing visible value, buyer and later-turn exclusions, history-only
and `last_offer`-only opening guards, decision/accept/counter isolation, a share
1.5 fractional-boundary clamp, non-finite flag behavior, exception-fallback
cohorting, exact opening-time bounds, collector-only results, duplicate finals,
terminal labels, unknown CDFs, aged abandonment, unresolved bounds, and the
zero-eligible exit.  The stale current-state snapshot was regenerated before
review; no live flag or process was changed, and no file under `arms.json`,
`control.json`, `.env`, or `logs/` was modified.  Arena, replay evaluation, and
red-team scripts were not run.

**Objections / proposed validation:**
1. Arm exposure is not persisted by design.  The operator must record the exact
   per-slot code-deploy/flag-arm `T0`, disarm/value-change `T1`, and analyze each
   homogeneous interval with `--since T0 --until T1`; a broad `--hours` window
   can hash control-only games into a false treatment after disarm.
2. Promotion requires unresolved=0 and no treatment close-rate loss.  No sample
   size or uncertainty rule was supplied, so none was invented; pre-commit it
   before inspecting the live arm contrast.
3. A missing outcome becomes an abandonment only under the repository's
   measured 6,000s-plus-watermark rule.  Inspect the reported abandonment count
   per arm and backfill/fetch questionable outcomes before the final verdict.
4. Historical strategy-error records created before this patch lack the state
   needed for opening-time eligibility.  Start `T0` after this code is live so
   those records cannot enter the experiment cohort.

## 2026-08-22 — bargaining no-regression guard and message arms implemented, default OFF

`GLEE_BARG_NO_REGRESS=1` now changes only a decision that every existing rule
still leaves as `reject`. It deep-copies the deterministic post-rejection state
(records the live offer, advances the round, makes the rejecter proposer) and
runs that projected offer through the public bargaining `decide()` plus action
coercion. The comparison therefore uses the SAME endgame cap, opponent floor,
Bob fitted-offer writer and opponent-profile writer that will make the next real
offer; it is not a second derivation of aspiration. If the wire-coerced planned
own share is no greater than the live offered share plus
`GLEE_BARG_NO_REGRESS_EPS`, the move becomes `accept`. EPS is in share units,
defaults to 0.0 and is clamped to [0,1]. Projection errors keep the reject.

The measured defect was nine games, -44.9 rating and 17.36 pot-points strictly
forfeited. The regression reproduces Bob rejecting a 70% live share and then
asking for 61%; flag OFF rejects, flag ON accepts, and the projected 61% is
equal to the real next observation's offer after an actual simulator rejection.
Boundary tests cover 60%<61% remaining a reject, exact equality accepting, and
60.9% accepting only with EPS>=0.001. A later-writer test forces Bob pricing to
80% and proves the guard sees 80%, not the earlier aspiration.

`GLEE_BARG_MSG=1` now assigns every game by
`sha256("barg_msg|" + game_id) mod 4` to `BARG_ARMS` for its full lifetime:
`B0` silent fleet control; `B1` length-matched neutral split recap; `B2` the
public no-agreement-pays-zero rule; `B3` a movement statement only when public
offer history proves a concession, otherwise public allocation arithmetic.
`BARG_ARM_SEMANTICS` records those meanings. B1-B3 use the same frame, request
and filler pools and target 300 characters: a 30,000-composition fuzz across
arms, seats, public movement/no movement and pots from 1 to 123,456,789.12 had
zero composition failures, with B1/B2 exactly 300 characters and B3 299-301.
Messages quote the wire-coerced split, not a pre-rounding float. The numeric
action is fingerprinted before/after attachment; B0 and failed compositions are
logged as assigned arms and cannot be back-filled. Dispatch excludes bargaining
from both LLM action and LLM message hooks, even under a stale allowlist: every
bargaining message is from this hand-written bank.

Mandatory leak audit of the former bank found seven gated families: inferred
last-round text; discount-asymmetry text; generic inflation text; exact
rounds-left text; internal non-concession-classifier text; "priced off discount
rates"; and the share<0.45 concession closers. The first six were removed from
the bargaining arms because pooling them would be false or disclose discount,
synthetic horizon or solver state. The two concession closers now require a
publicly verifiable prior move. Over 1,000 deterministic seeds each emitted on
B3 at BOTH 40% and 60% current own share: "serious move" 503/503 and "come a
long way" 497/497. Plan-metamorphic tests vary private deltas, rounds-left,
aspiration, floor, continuation, planned counter and internal evidence while
holding public state fixed; a second side varies hidden/complete-information and
horizon fields. Every arm stays byte-identical because the composer never reads
`plan` or those game-state fields. Paired true/false old-gate tests emit every
retired phrase 0/0. Those six phrase families could not be moved across both
sides truthfully: doing so would make false deadline/discount claims, so they are
retired rather than pooled.

Message rating impact is **UNMEASURED**. The only measured result is reachability:
Test 1 sent 0/1,851 texts while opponents sent 1,583/1,830 in 493
message-enabled games. `GLEE_BARG_MSG` must therefore run as the per-game arm
experiment against B0 silence, never as a default-on template policy.
`scripts/live_percentile.py --ab barg-msg` recovers the same four-way hash,
filters to `messages_allowed=true`, reports the primary B0-versus-pooled-text
contrast and exploratory B1/B2/B3 contrasts, and warns that `--hours`/`--slots`
must be scoped to an era where the flag was armed because result records do not
carry flag exposure.

Verification: the 31 focused regressions pass. Full suite: 640 passed; only the
two pre-existing failures named in AGENTS.md remain
(`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`). Reachability now
registers both flags and treats message changes as action changes, but Codex did
not execute that replay/arena-backed checker because the operator explicitly
forbade replay and arena runs. No arena, replay evaluation, red-team script,
live flag, fleet process, `arms.json`, `control.json`, `.env` or `logs/` was
touched.

**Objections / proposed validation:**
1. Code-path reuse is exact for one policy snapshot. A live flag or hot-reloaded
   model changing between rejection and the next turn can change the later real
   offer; no pre-reject projection can freeze an external mutation.
2. Before deployment, Claude should run the registered reachability checks and
   require eligible>0, fired>0, action_changed>0. For messages, verify all four
   hash arms and analyze B0 versus pooled text before comparing registers.
3. Do not select B1/B2/B3 from observational phrase conversion. Arm assignment,
   including silence, is the identifying variation; promotion needs live
   game-level outcomes under a pre-committed decision rule.
4. The live `randomized`/Test 4 slot uses `probes.py`'s custom bargaining policy
   and bypasses `bargaining.decide`, so both flags are intentionally inert there.
   Do not arm that slot without a separate probe-policy design and test.

## 2026-08-22 — terminal rank-price arm implemented, default OFF

`GLEE_NEGO_RANK_PRICE_AB=1` now hash-assigns each game to control or treatment
with the independent `rank_price_ab|<game_id>` salt.  Only an outgoing offer on
a REAL final round (`capped and rounds_left <= 1`) can move.  The treatment is
the final target writer, after ultimatum/posterior/curve/stall logic, and bypasses
the later split transform; decision turns never read its price, so the arm cannot
contaminate acceptance as the surplus probe did.  Flag off and hash control keep
the previous path exactly.  `scripts/live_percentile.py --ab rank-price` recovers
the assignment; the reachability registry knows the `rank_price` trace gate.

The search grid is the midpoint of each pooled v5 final-role bin with `n>=20`,
then filtered to strictly profitable prices and, when the opponent value is
visible, the interior of the ZOPA.  Hidden A(P) is the structural uniform mixture
of the four responder-type curves, using a type row at `n>=8` and the pooled rate
otherwise; complete information uses the visible type with the same fallback.
For each candidate it computes exact-cell empirical midranks from CDF v3 and
maximises `A(P)F(payoff)+(1-A(P))F(0)`.  It separately computes the true money
argmax `A(P)*payoff`.  The returned plan records previous/chosen/money prices,
both acceptance probabilities and expected-rank values, F(0), CDF n, grid size,
cell, acceptance basis, arm, status and fallback reason.

CDF cells with fewer than 30 observations do not price: at n=30 one observation
already moves the empirical rank by 0.033 and worst-case pointwise SE is about
0.091.  Unknown/invalid/thin CDF cells, missing acceptance curves, and no covered
profitable bin all fall back to the complete pre-existing target.  Focused tests
cover a 74%-zero cell (`F(0)=0.37`) where treatment lowers a seller ask from the
fixed 0.80-span price 136 to 115 and exact expected-rank assertions require the
nonzero rejection term.  They also cover uniform hidden-type mixing,
observed-type complete-information pricing, flag-off/hash control, every
required fallback, offer-only real-final reachability, posterior precedence,
split-transform bypass, and buyer payoff symmetry.  Full suite: 609 passed;
only the two pre-existing bargaining failures named in AGENTS.md failed.  Codex
did not invoke replay evaluation, arena, or red-team, or touch a live flag, fleet
process, or deployment file.

**Objections / proposed validation:**
1. This is a fitted proxy, not an identified policy: CDF v3 contains our own
   games and omits opponent type/messages, while hidden v5 type labels are
   recovered mainly after agreements.  Uniform weights avoid v2's selected
   posterior weights but cannot remove selection inside the component curves.
2. Before any arena or deploy, Claude should run the registered reachability
   check and require eligible>0, fired>0, action_changed>0.  This implementation
   did not run it because the operator reserved replay-based validation for
   Claude.
3. If armed live, inspect plan fallback rates and direction by role/cell, then
   judge the pre-committed game-level hash arms with
   `scripts/live_percentile.py --ab rank-price`; model-predicted expected rank is
   diagnostic only and must not be the promotion criterion.

## 2026-08-22 — negotiation rank optimisation derived; no behaviour changed

The finite-horizon policy is a belief-state dynamic programme with terminal
utility equal to the exact-cell payoff midrank, not money.  At a terminal offer
the correct objective is `F(0) + P_accept(p) * (F(u(p)) - F(0))`; at continuing
states it also needs the full accept/counter/walk transition kernel and Bayesian
updates over the four opponent types.  The three shipped artifacts do not supply
that kernel, so a full backward-induction implementation is not yet identified.

**Exact correction in the one-round complete-information cell:** the seller is
the sole proposer and the buyer only decides.  The seller's rational price is
buyer value minus one cent; the buyer's exact best response is already shipped:
accept every strictly profitable offer.  The reported 0.7183 seller versus
0.3336 buyer percentile is proposer advantage, not a missing buyer ask policy.

**Terminal hidden-type benchmark (uniform four-point prior):** combining the
rational acceptance steps with the shipped CDF moves the actual one-round seller
policy away from the money optimum by up to 0.30B.  Seller own factors
0.8/1.0/1.2 choose money asks 1.20/1.50/1.50B versus rank asks
1.00/1.20/1.50B.  A separate v5 fitted-curve proxy over the actual terminal
proposer cells (one-round seller; round-10 buyer) shifts price by up to 0.275B
and estimated rank by up to +0.111.  Rank always weakly buys more acceptance on
the supported grid.  Structural argmaxes are exact conditional on the rational
response step and shipped CDF; their percentile levels and every v5 result are
fitted proxies.

**Visible-span correction:** current hidden games have `zopa=None`; the opponent
bid bound changes only the anchor, and the span veto is unreachable.  The cited
12,000/15,000 transcript was accepted by the absolute learned-table threshold,
not because a latest-bid span scored 100%.  If a share diagnostic is retained,
use the posterior distribution of `(P-c)/(v-c)` (seller) or `(b-P)/(b-c)`
(buyer), conditional on a ZOPA, never the ratio to a bid-created denominator.

**Objections / required tests before implementation:**
1. The CDF omits opponent type and messages, while hidden cells are heavily
   own-policy contaminated; verify that its key matches the server's scoring
   cell and refit complete-information cells by the full value pair if required.
2. The v2 posterior and v5 type curves label hidden types mainly after agreement,
   so they are selected-on-close.  Start from the exact uniform prior, fit offer
   likelihoods on uncensored complete-info data, and validate calibration by
   hidden first-offer bucket before using them for belief updates.
3. Fit an identified accept/counter/walk kernel (including counter-price
   distribution), then solve H=10 on a cent/breakpoint grid and test a default-OFF
   per-game randomised arm.  Until then, do not ship a rank-DP behavioural flag.

## 2026-08-22 — negotiation opponent clone V2 implemented, default OFF

`GLEE_SIM_NEGO_RESP_V2` now switches the simulator's negotiation clone from the
legacy value-first price lookup to a separately fitted V2 instrument.  When both
values are directly visible and the span is positive, V2 keys responses on the
candidate proposer's 4%-binned share of span.  Hidden/no-span games use the
coarser `price/base` observable, with buyer/seller directions normalized onto one
greed axis.  Terminal and continuing responses have separate keys so one-round
ultimata cannot contaminate round-one continuation play.  The tracked model was
refitted on 29,105 games and carries 701 pooled V2 response cells (528 share,
173 price; 588 continuing, 113 final) with zero private-value keys.

The hidden value-conditioned table is deliberately dropped, not reweighted:
the responder value is recoverable in hidden games only after agreements, and
the measured buyer m1.5 / round-4+ / price-bin-1.0 cell was 0.640 acceptance
(n=25) against 0.027 (n=2,793) without that selected label.  Weighted PAVA makes
acceptance non-increasing in proposer greed; interior gaps take the greedier
neighbor, the generous edge stays flat, and asks beyond greedy support get zero
acceptance.  There is no profitable-price auto-accept fallback.  Structural
no-loss checks prevent pooled hidden curves or counters from accepting/offering
through the clone's own reservation value.

The same flag selects unconditioned counter distributions represented by
equally weighted quantile midpoints.  This replaces the legacy
`sorted(values)[:400]` left-tail truncation under V2 only; the old algorithm is
still the default.  Final-round V2 rejection omits the otherwise-invalid
counteroffer.  `sim/replay_eval.py` now clears `GLEE_SIM*` between arms.

Verification: focused field-clone tests 18 passed.  Full suite: 599 passed and
only the two pre-existing bargaining failures named in AGENTS.md failed
(`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`).  No arena,
replay_eval, red-team run, live flag, fleet process, or deployment file was
touched.  The required regression pins the old clone accepting an unseen but
profitable 95%-of-span ask, then proves V2 rejects it rather than assigning
acceptance probability one.  A schema smoke test prevents committing a stale
four-part/reject-all model artifact.

**Objections / proposed validation:**
1. `scripts/check_reachability.py` replays our strategy, while this flag executes
   inside the opponent clone, so its standard eligible/fired/action_changed
   contract cannot observe this simulator gate.  The direct old/new clone test
   is the reachability proof; Claude should run the paired negotiation arena
   with V2 present in BOTH control and candidate before trusting a strategy A/B.
2. `Field._field_weight` computes `unnamed_games - named_games`; on this refit it
   is 40, making behavior draws almost entirely named clones before opponent-name
   redaction.  This may be an accidental weight bug or an undocumented way to
   model hidden identity separately from hidden behavior.  Do not change it
   without first deciding that estimand; test the intended named/pooled mixture.
3. Even after the terminal split, round buckets 2-3 and 4+ remain deliberately
   coarse.  Validate calibration by seat/terminal/round bucket before promoting
   any price-moving negotiation flag.  These are observational, shape-restricted
   response curves rather than identified off-policy effects, and conservative
   tails may create false negatives; arena evidence still beats this model.

## 2026-08-22 — persuasion: buyer parser tri-state correction implemented

`GLEE_PERS_PARSE_TRI` is implemented default OFF. When armed, buyer v1 and v2
preserve parser abstention as `None`: historical abstentions do not update the
seller-type posterior, and a current abstention leaves `P(high)` at the prior.
An explicit parser decline is a final hard veto. The shared legacy boolean
wrapper is unchanged for seller policy, so this flag cannot move seller play.

Focused regression coverage proves the flag-off path still makes the original
ambiguous-message purchase, while the armed path passes when the prior is below
`1/v`; a second case proves an explicit decline vetoes a purchase that the v2
posterior otherwise makes. Verification: focused parser tests 49 passed; full
suite 581 passed, with only the two pre-existing bargaining failures named in
AGENTS.md (`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`). No
live configuration, fleet process, or deployment file was touched. Claude still
owns verification and deployment.

## 2026-08-22 — negotiation: two theories tested, both moved

**Codex's first review paid for itself.** It found that the surplus probe is
invalid AND contaminates live accept/reject decisions (`target` is read at
negotiation.py:1046 and :760, not only on the offer path). Verified at both
call sites. ACTION PENDING: set `GLEE_NEGO_SURPLUS_PROBE=0` on `composite` and
`conceder` — blocked by the local permission classifier, needs the operator.

**The "we are too soft" theory (A) is refuted for the concession schedule.**
Arena says faster concession is worse on percentile AND closes fewer deals
(4 runs, all CIs excluding zero). See FINDINGS "Measured NEGATIVE".

**The "half the games are impossible" theory (B) is now exact, not folklore.**
Read off the generator: complete-info cells are 6/6 feasible, hidden-info cells
6/16, overall 45% infeasible. We close 91.8% of complete-info and 79% of
feasible hidden-info games. The remaining prize is ~8% of negotiation games.

**Contested / next:**
1. Codex's rank objective `F(0) + P(accept|x)[F(payoff(x)) - F(0)]` over the
   exact-cell empirical CDF. If the CDF really has a fat atom at the even
   split, pricing one tick above it is nearly free rank. Needs the per-cell CDF
   built first — that is the highest-value measurement now.
2. negotiation.py:319 floors no-ZOPA seller asks at 1.15x cost on a "39%
   positive" figure that fit_percentile.py calls a role-pooling phantom. If the
   figure is dead the rule should go. UNVERIFIED.
3. The probe, if rebuilt, must assign the arm INSIDE the offer branch only.

## 2026-08-22 — Codex connected as reviewer

Codex CLI 0.149.0 installed, authenticated via ChatGPT, registered as a
project-scoped MCP server (`.mcp.json`) and callable non-interactively with
`codex exec --sandbox read-only "<prompt>"`.

**Open questions where an independent review would be most valuable:**

1. `GLEE_NEGO_SURPLUS_PROBE` (live on Agent 5 + Test 3). Is the randomised
   design sound — assignment seeded on game id, stratified by seat/round-block/
   cap? Is `scripts/analyze_surplus_probe.py` computing P(accept|x) without
   re-introducing selection bias? Is the decision rule (peak of P(accept)*x plus
   continuation) the right objective given percentile scoring?
2. `GLEE_NEGO_FINAL_OPTION` — values our own final take-it-or-leave-it proposal
   as P(accept) x surplus off fitted curves, and refuses to accept below it.
   Arena +0.0004..+0.0012 across two seeds. Is the option value correctly
   specified, and does the buyer branch (pooled `buyer_final` curve) carry the
   same selection problem the response model died of?
3. Persuasion is stuck: no identified defect, play at the 0.548 percentile,
   ratings drifting with the field. Is there a measurement we have not made?

## 2026-08-22 — complete-information negotiation price guards implemented

Three default-inert flags now guard the final numeric action in
`glee_agent/actions.py`, after heuristic or full-LLM selection and after action
repair: `GLEE_NEGO_ZOPA_CLAMP` (boolean, default OFF),
`GLEE_NEGO_ULT_FLOOR` (float, default `0.0`), and `GLEE_NEGO_ULT_CAP` (float,
default `0.85`, read only while the floor gate is armed). The same postcondition
covers offers and reject/counter prices; hidden-information states return before
either visible opponent bound is read.

Diagnosis: `GLEE_BARG_OPPONENT_FLOOR=0.39` does not leak into negotiation. The
0.390 one-shot mode is negotiation's independent `nego_zopa_share=0.39` under
ENDGAME_V3. The 0.020 mode is `GLEE_NEGO_MIN_MARGIN=0.02` without that endgame
floor. The 1.440/1.800 modes are the HORIZON_V2-off hardliner branch: visible
opponent value is ignored, and a 4.0x anchor with 0.12 margin emits 1.36x cost.

Focused verification: `tests/test_nego_zopa_guards.py` passes 13 tests covering
default-off behavior, seller and buyer clamps, an impossible 14,000 seller ask
after a full-LLM replacement, reject/counter prices, a hidden-information
non-clamp, the 0.72 floor in both seats, the default 0.85 cap, and a live-tuned
0.80 cap, including fractional valuation boundaries after wire rounding. Full
suite: 653 passed; only the two AGENTS.md-documented bargaining failures remain
(`test_bargaining_horizon_floor`, `test_sim_grid[bargaining]`).

**Objections / proposed validation:**
1. `ULT_CAP` is deliberately nested under `ULT_FLOOR > 0`; applying its required
   0.85 default unconditionally would violate the default-off deployment rule.
2. The ZOPA clamp removes dominated, impossible proposals but does not identify
   the best interior share. Keep 0.72/0.85 as explicit runtime settings and use
   the supplied one-round evidence; do not generalize the cap to multi-round
   complete-information play.
3. `scripts/check_reachability.py` now coerces replayed decisions so it can see
   these post-plan wire guards. Before deployment, run it separately for
   `GLEE_NEGO_ZOPA_CLAMP=1` and `GLEE_NEGO_ULT_FLOOR=0.72`; the latter control
   must set the older `GLEE_NEGO_ULTIMATUM_SHARE=0`, or its existing 0.80 ask
   masks a 0.72 floor. Prove the cap knob separately with
   `GLEE_NEGO_ULT_CAP=0.80` and ULT_FLOOR armed in the control; an explicit 0.85
   candidate is identical to the code default and correctly changes nothing.
   Each meaningful run must show eligible, fired, and action_changed above zero.
   Claude remains the only fleet deployer.

## 2026-08-24 — persuasion workstream boundary and exact-cell prose probe

Persuasion deployment state, the rejected Test 2 rank-gate mechanism, and the
precommitted seller wording experiment are recorded in
`.ai/PERSUASION_HANDOFF.md`. Negotiation/bargaining owners should treat that file
as read-only; no persuasion change in this workstream alters their code or flags.

Objection resolved before deployment: the historical p=.8 token/prose purchase
contrast is observational, conditioned on positive recommendations, and crossed
multiple policy eras. It cannot promote prose. The resulting
`GLEE_PERS_P08_R125_PROSE_AB` code is therefore default OFF and randomized per
game in the exact known-CV seller/text/p=.8/v=1.25P cell. On Agent 5's exact live
stack its reachability check reports 340 eligible, 220 fired and 220 changed
wire actions. Official dashboard per-game deltas, all assigned outcomes, zero
mechanism failures, and the preregistered 120/arm rule are required; local CDF
percentiles remain diagnostic only. Test 2 and Test 3 are protected from the
research deployment.

## 2026-08-24 — negotiation stale-stall arm and paper review

Built, default OFF: `GLEE_NEGO_STALL_CURRENT_BREAK_AB`. The existing stall
detector reads only the last three completed `history[*].offer` prices. On a
decision turn, the standing `last_offer` is one opponent action newer. A live
seller-.8 game therefore classified historical 0/0/0 as a continuing stall
even though the current buyer bid had advanced to 440,779.69; `stall_park`
rewrote the scheduled ~1,400,527 counter to 900,000. Last-20k shadows found
52-120 favorable current breaks and 35-107 changed counters per major slot.

The treatment is a triggered 50/50 per-game hash. At the first state where the
current opponent offer improves for us by strictly more than 1% relative to the
historical stall price *and* suppressing the writer gives us a strictly stronger
counter, treatment suppresses only the offer-target stall writer; control is
byte-identical. Wrong-direction schedule states are logged as ineligible.
`_their_stall_price` itself is unchanged, so
dead-game walking and stall acceptance retain their old semantics. The arm
fails closed unless `CONTINUATION_ACCEPT=1`, and refuses mixed stacks carrying
the first-offer, extreme-open, terminal-counter, hidden-policy, hidden-floor, or
first-principles experiments. This prevents target assignment from leaking into
legacy decisions or becoming an unanalysed factorial.

Do not arm while the current opening/terminal probes are live. The old park was
accepted in the motivating transcript, so semantically correcting stale state
may still lower close rate; this is a randomized hypothesis, not a direct bug
fix. Read every first-trigger outcome with `scripts/live_percentile.py --ab
stall-current-break --since T0 --slots ... --official-json FILE`. Promotion
requires 100 resolved official games/arm, 20/arm in each role, official rating
delta CI above zero, close lower CI above -2pp, nonnegative role/information/
horizon/scale/message point estimates, and zero mechanism failures.

Paper review: arXiv:2502.16242 studies a different six-party HarborCo game, so
its deals and policies do not transfer. Its communication-free baseline is the
useful methodological result: once acceptability is structurally identifiable,
multi-agent dialogue adds little. The GLEE paper (arXiv:2410.05254v3, Section
4) is directly aligned with our localization: its negotiation efficiency is
17.3-17.4pp above baseline for complete-information unknown-horizon games, but
only 4.1-5.5pp for hidden unknown-horizon and 8.3-9.2pp for hidden cap-10. That
supports horizon-specific experiments and rejects a universal curve. Its
model-pair effects support a later named-opponent arm, but efficiency/fairness
are not our percentile objective, so neither paper authorizes a deployment.

## 2026-08-24 — negotiation hidden minimum-share acceptance arm

Built default OFF: `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB`. This is a prospective
decision experiment, not a retroactive claim that every low-share agreement
should have been rejected. The validated hidden support lets our own type identify
the smallest positive feasible ZOPA; the arm marks a nonfinal profitable offer
strictly below 40% of that minimum only when the current table/stall/continuation
stack is otherwise about to accept. Hash controls accept byte-for-byte as before.
Candidates reject and emit the existing profitable-side counter. Every first
assignment and every eventual zero/agreement/pending result stays in the ITT.

The broader all-acceptor estimand is deliberate. Historical current-slot turns
contain 1,243 below-table fallthrough accepts and 230 direct table accepts under
the same support floor. Restricting the arm to `table_accept_below` would leave a
known low-share region shadowed by the table's late 0.034B/0.076B thresholds.
Conversely, assigning every low-share state before knowing whether control rejects
would only dilute the effect. The hook therefore runs at each would-be acceptance
branch and records which control acceptor owned the decision.

Adversarial objections resolved before deployment:

1. The support bound is conditional on a positive-ZOPA latent cell. Three of 479
   recovered historical finals had negative opponent payoff, so the arm is not a
   dominance guard; the randomized official rating outcome must pay for that risk.
2. The pure shared signal now excludes real final rounds itself. The terminal
   any-positive rule remains untouched and is covered by a dedicated test.
3. First-principles is not a global conflict because its hidden scope is only a
   single-round seller cell and returns before this path. All genuinely overlapping
   opening/terminal/hidden/accept experiments still fail closed.
4. Exact Test 3 stack reachability at seed 2309 over 1,500 paired negotiations is
   55 eligible / 26 fired / 26 changed actions. Dedicated tests are 50/50 and the
   impacted negotiation/reader suite is 444/444.

Precommit: arm only `conceder` after inert code is pushed and that process naturally
rotates. Record T0 after the overlay is live. Read with `scripts/live_percentile.py
--ab hidden-min-share-veto --since T0 --slots conceder --official-json FILE`.
Promotion requires 100 resolved official games/arm, 20/role/arm, official-delta CI
above zero, close point delta >=-5pp, nonnegative role points, and zero mechanism
failures. One harm look is allowed at 30 official games/arm; reject if its official
CI is wholly negative. Never touch bargaining code or any bargaining flag.

## 2026-08-24 — Test 3 rotated; exact official join proven

Test 3 naturally rotated from PID 67640 to PID 73157 at 19:22:14 IST and the
refreshed state shows `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB=1`. The first new-code
negotiation action at `1787579568.528749` was an ineligible outgoing offer, so it
is not causal T0. Keep T0 pending until the first plan records
`hidden_min_share_veto` on a qualifying would-accept decision; hash controls and
candidates both record that metadata. Do not backdate to process start.

The first real dashboard/local smoke join now succeeds exactly. Dashboard record
`Aug 24, 2026 7:08 PM`, Buyer, Agreement, +5.1, hidden cap-10, full ten-round
offer/decision/counter transcript, and payoffs 20/10 maps uniquely to local game
`3da88013-1084-4c01-875d-2f7843a44d9f` with one candidate and zero ambiguity.
The authenticated UI's timestamp format, active snapshots, and timeout wire
events exposed three synthetic-only gaps; `scripts/join_official_history.py` now
parses the UI timestamp only with an explicit timezone, ignores known live
snapshots, and preserves timeout as a distinct event. Focused tests: 15 passed.
The latest 20 official Test 3 negotiation records from 19:00-19:12 (all pre-arm)
sum +24.9 rating: agreements +38.2 (n=10), no-deals -13.9 (n=7), walks +0.6
(n=3). This is a descriptive baseline, not the randomized estimate.

## 2026-08-24 — trend-confirmed TABLE precedence arm built inert

Built default OFF: `GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB`. This is the narrow
randomized test recommended by the latest Test 3 shadow: TABLE currently returns
before the state-dependent continuation comparator. Candidate suppresses that
return only when three distinct improving opponent prices identify a positive
trend, existing continuation exceeds accept-now surplus, the support-minimum
signal is absent, and STALL would not immediately accept. It then falls through
to the existing counter unchanged; control accepts byte-for-byte.

The trigger deliberately excludes the continuation model's no-trend basis,
because an extrapolation from our own unplayed target is not identified. It also
refuses every overlapping negotiation arm and requires the exact future stack
including FINAL_OPTION=0.60. Latest 100,000 Test 3 turns produced 76 first-
eligible games; future-stack reachability over 1,500 paired games (seed 2411)
reported 47 eligible / 19 fired / 19 changed. Do not arm it during the current
support-minimum experiment. Its clean deployment window is still pending;
historical completed outcomes cannot promote it.

Update: the official reader is now built as `--ab table-vcont-precedence`. It
recomputes the trigger from the logged state/plan, verifies hash parity and the
direct-TABLE control versus exact candidate counter wire, retains unresolved and
all terminal outcomes, excludes cross-fleet duplicates from causal estimates,
and enforces the precommitted official-score/close/stratum gates. Combined
precedence/veto focused verification is 83/83. The arm remains OFF; no behavior
changed.

## 2026-08-24 — hidden-veto causal T0 and direct-leader curve audit

The first qualifying support-minimum assignment arrived at
`T0=1787581117.643784` (19:48:37 IST), game
`99c476fc-5bce-44b0-af07-57382aec6160`. It was hash control, hidden cap-10
seller-.8, round 6, text enabled. The buyer's `.85666667B` offer paid us
`.05666667B`, below the `.08B` support-aware floor, and direct TABLE accepted.
The independent reader reconstructed the signal and returned
`mechanism_ok=true`. This exact first exposure, not the 19:22 process rotation,
is the lower bound for every causal read. At the time of freezing, its local
collector final had not yet appeared, so outcome status remains unresolved.

Independent review reconstructed Clod's private type in both observed cap-10
buyer trajectories: agreement at `1.008B` plus Clod payoff `.192B` implies
buyer value `1.2B`. The two full paths were approximately
`[.8108,.8112,.8196,.8648,1.008]B` and
`[.8179,.8180,.8217,.8553,1.008]B`. This identifies actions and type, not the
causal value of copying them; their fitted timing exponents also differ. Do not
build a literal five-price clone now: its fifth point directly overlaps the
running cap-10 buyer-1.2 terminal experiment. First finish that experiment. If
the terminal rule promotes, freeze it in both arms and test only the first four
Clod midpoint prices prospectively; otherwise redesign the terminal component
before any curve trial. Hardliner is the only currently clean host and would
need roughly 57 hours for 100/arm at its observed cell arrival rate, another
reason not to launch a bundled arm.

Authenticated/API state around 19:44-19:48 IST: Test 2 was sixth overall at
2315.51 versus third-place Mythos01 at 2383.21 (gap 67.70). Negotiation leaders
were Clod 2894.70, 7aidara_Gamma 2675.62, and opus 5(4) 2652.36; our best visible
negotiation rating was Test 4 at 2070.5. These are transient monitoring values,
not policy-effect estimates.

## 2026-08-24 — broad cap-10 buyer curve built for an hours-scale read

`GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB` is implemented default OFF. It replaces the
rare-cell-first optimization loop with a high-frequency, all-viable-type hidden
cap-10 buyer test. Candidate owns only the first four outgoing counter prices
and uses their pointwise midpoint across two completed, type-reconstructed Clod
buyer-1.2B paths, normalized by our visible buyer value:
`[.6786404167,.6788316667,.6838475,.71674625]`. Control keeps the current stack
exactly; the fifth/terminal price and accept/walk decisions are unchanged. The
two Clod paths both closed at `1.008B` with private value `1.2B`, but that
terminal is not part of this arm. Scaling to 1.0B/1.5B is an explicit randomized
extrapolation, not a claim that hidden no-deal types were observed.

The runtime refuses overlap with the old buyer-1.2 terminal arm, broad hidden
writers, hidden support-veto, TABLE precedence, stale-stall, CLOSE_AB, or
PROBE_V1. Do not arm until each overlapping flag is explicitly `0` on every
target. The official reader is
`--ab hi-buyer-curve`; it cohorts before the first action, retains immediate
accepts and all non-closes, audits every candidate counter, and uses dashboard
rating delta as primary. Harm/final rules are frozen in EXPERIMENTS.md.

Independent review correctly rejected the original five-price bundle: it
aliased early imitation with the unsettled terminal mechanism and overclaimed
the cross-type evidence. The implementation was changed before activation.
The remaining scaling is a randomized treatment whose official effect is
reported separately by own type; no causal or behavioral identification is
claimed in advance.

Exact intended champion stack with the old terminal flag disabled, 1,500 paired
games seed 2601 after terminal isolation: 549 eligible / 227 fired / 227 changed.
Focused tests 125 pass; the impacted negotiation/action/reader set is 530 pass.
Full suite: 1,269 passed with only the two predeclared bargaining failures. No
bargaining code, bargaining flag, live arm, process, key, or deployment file
was changed.

Deployment followed immediately after the verified commit because the operator
rejected another multi-day rare-cell wait. Commit `e007a90` was pushed to main,
then the interlocked safe deployment drained every in-flight game normally and
relaunched all five slots at 2026-08-24 20:47:08 IST (`T0=1787584628`). The
broad curve A/B was subsequently stopped on champion, conceder, randomized,
and composite at the operator's direction before a meaningful sample accrued;
all four flags are explicitly `0`, so there is no causal verdict. Test 2
hardliner stayed control. The old terminal arm is off on its three former slots
and Test 3's overlapping hidden-min-share-veto arm is off. No bargaining value
was changed.

### 2026-08-24: top-agent buyer clone and the 20:47 fleet outage

The 20:47 deployment used `fleet.py safe-restart`. Despite its drain wording,
the supervisor shutdown path interrupted every `run_agent.py`; each slot then
timed out its last three held games and the platform suspended queue joins for
30 minutes. All five agent processes remained healthy but had zero active games
until their recorded expiries at 21:17:02–21:17:08 IST. This was a deployment
error, not evidence about any negotiation policy. Do not use `safe-restart` for
behavior deployment; use a named zero-game cycle or a natural shift boundary.

At the operator's direction, the replacement experiment copies observable
top-agent behavior on Test 3 only. A 70-game reconstruction across 7aidara,
Alpha, Beta, and Gamma identified exact shared buyer paths rather than a fitted
median: complete cap-10 own-zone claims are
`[.960,.898,.836,.774,.774]`, and hidden paths are literal price/base tables by
own type (buyer 1.5 is `[.905,.905,1.075,1.075,1.245×4]`). Mapping the
payoff-hidden classes to monotone private types remains the randomized part.
The treatment is buyer-only because the contemporaneous official window had
seller `+47.9` and buyer `-24.4`, with buyer no-deals accounting for `-22.5`.
It is a single full-policy hash arm (`GLEE_NEGO_TOP_BUYER_CLONE_AB`) so offers,
acceptance, and stopping behavior travel together. Focused tests pass 11/11,
all negotiation tests pass 563/563, Test 3 reachability is 3,827 eligible /
1,575 fired / 1,575 changed, and the full suite is 1,280 pass plus only the two
known bargaining failures. Bargaining code and flags were not changed.

The subsequent exact-message and reader pass adds 7aidara's literal buyer
counter sentence in message-enabled treatment games and an all-turn official
reader (`--ab top-buyer-clone`). The reader independently reconstructs every
candidate wire from the pre-action state, requires the clone plan source,
detects any control contamination, keeps unresolved and every terminal outcome,
and enforces the frozen emergency stop. Combined clone/reader tests pass 22/22;
the full suite passes 1,291 with only the two predeclared bargaining failures.
The flag overlay was written at `1787586287`, but Test 3 PID 79383 predates the
clone code and remained busy. A safe named cycle is pending; no pre-launch game
is treatment exposure, and the future verified relaunch is the only valid T0.

### 2026-08-24: clone is live; prospective multi-host acceleration

Test 3 eventually drained every held game and the clone became genuinely live
from process launch `T0=1787590698` (22:28:18 IST). Its first buyer candidate
trace was game `66e4b705-9a53-415c-861b-ba9c1c4e858e` at
`1787590787.720265`, with exact `plan.source=top_buyer_clone`; the first local
reader found one control and one candidate assignment, both unresolved, with
zero wire or control-contamination failures.

Four buyer assignments in the first five minutes were too slow for an urgent
10/arm harm read. Before inspecting any treatment outcome, the same arm was
prospectively expanded to champion, randomized, and composite at common
`T0=1787591092.200761`; hardliner remains untouched. Their overlapping hidden
buyer probes and first-principles arm were explicitly set to zero, and all
three produced exact clone-source traces after post-T0 hash controls. Analyse
each host separately before pooling and require every host point estimate to be
nonnegative for promotion. Seller policy and all bargaining flags/behavior are
unchanged.

The first relaunch exposed a fleet infrastructure defect: the long-lived
supervisor inherited fd 0 from a terminal that later became `(revoked)`, so new
children died in Python's `init_sys_streams` before importing strategy code.
Commit `816cd31` gives children explicit `DEVNULL` stdin. After the affected
three slots had independently drained, only the broken supervisor process was
replaced; no child agent was signalled. The replacement adopted the still-
running conceder/randomized processes and outcome collector, then launched the
three already-down slots. All five turn streams were live by 22:32:09. This is
not policy evidence and no held game was interrupted.

### 2026-08-24 22:50 IST: first buyer-clone official checkpoint

The first change in this workstream to show a positive clean official A/B point
estimate is `GLEE_NEGO_TOP_BUYER_CLONE_AB`. After auditing every unmatched
dashboard row rather than conditioning on successful joins, treatment is
20 games / `+24.8` rating (`+1.240/game`) and control is 25 games / `-14.3`
(`-0.572/game`): lift `+1.812/game`, approximate Welch 95% interval
`[-0.39,+4.02]`. This clears the emergency harm gate but not promotion:
30/arm is unmet, the interval crosses zero, and Agent 5/composite is currently
negative (`-1.13/game`) while champion, Test 4, and Test 3 are positive. Keep
the arm randomized and collect the fixed checkpoint; do not claim a sustained
0.55 percentile or deploy it fleet-wide yet.

The strict join matched 22/36 new buyer rows. All 14 failures were recovered
by exact host/minute/setup/incoming-offer/submitted-action/source evidence; no
rating or payoff entered the key. Their inclusion lowered the naive matched-
only lift from `+2.51` to `+1.81`, so this is a material evaluator bug, not
bookkeeping. First incoming accept/reject records have empty `state.history`;
the live join currently omits `state.last_offer` in that case. A fail-closed
regression fix is in progress.

### 2026-08-24 23:14 IST: broad clone stopped; scoped prospective retest built

The broad buyer clone has not earned promotion. Its frozen 91-game official
checkpoint is candidate 44 / `+49.1` (`+1.116/game`) versus control 47 /
`+11.6` (`+.247/game`), a `+.869/game` point lift with approximate Welch 95%
interval `[-.78,+2.52]`. Candidate no-deals rose 6.14pp and composite's host
point is `-.648/game`, failing the precommitted interval, no-deal, and
every-host gates. Fleet tooling set only `GLEE_NEGO_TOP_BUYER_CLONE_AB=0` on
the four research hosts at `T1=1787593429`; live overlay polling makes this a
non-restart stop. Bargaining was untouched.

The sole coherent post-hoc cell was hidden-information known-cap-10 buyers:
candidate `+1.573/game` n=15 versus control `-.236/game` n=11, `+1.809/game`,
with fewer rather than more no-deals. Because it was selected after looking,
`GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB` uses a fresh hash salt and remains
default OFF until a clean prospective T0. It copies the already-frozen literal
leader path only in that exact buyer cell; every other negotiation action and
all bargaining behavior fall through. Champion-stack reachability is
335 eligible / 164 fired / 164 changed over 800 paired games, and focused
strategy tests are 37/37. EXPERIMENTS.md freezes the 20/arm harm and 40/arm
final rules before activation. Next: finish the all-outcome reader, full suite,
commit/push, wait for natural shifts, verify no eligible games in flight, then
arm champion/composite/conceder/randomized at host-specific clean T0s.

Follow-up: runtime/join/evidence commit `9f87a48` is pushed. Full suite passed
1,476 tests with only the two predeclared bargaining failures. The independent
reader is implemented as `--ab top-buyer-clone-hi-cap10`; unlike the first
draft, its executable gates now exactly match this experiment's frozen 20/arm
harm and 40/arm final rules. Combined scoped/broad/Opus clone reader tests are
43/43. Activation still waits for natural rotation onto `9f87a48` and a clean
no-eligible-game boundary; the flag remains absent/default OFF.

Follow-up 23:44 IST: prospective activation is complete on pushed commit
`64ec557`, without signals or abandoned games. Clean launch boundaries are
conceder `T0=1787594802`, randomized `1787594943`, champion `1787595144`, and
composite `1787595205`; every launch record has broad clone `0` and scoped
hidden-cap-10 clone `1`. Hardliner/Test 2 was not enrolled and no bargaining
flag or behavior changed. The first candidate wire appeared after conceder's
T0 in game `cdd59547-0b66-4416-94b0-8f2877159e90`; independent assignment is
candidate and the state is exactly hidden-information, known-horizon, cap-10,
buyer. That is mechanism proof only. Do not report a winner until the frozen
20/arm harm or 40/arm final reader gates are reached with official joins.

### 2026-08-25 00:05 IST: scoped clone remains positive, not yet proven

Authenticated dashboard capture now gives 25 unique prospective scoped games
with 25/25 exact, unique joins and no unresolved or ambiguous rows. Candidate
is 9 / `+22.2` / `+2.467 per game`; control is 16 / `+17.6` / `+1.100 per
game`. The point lift is `+1.367/game` unstratified and `+1.535/game` after the
frozen host adjustment. The exact host-stratified sharp-null test enumerates
50,400 assignments and gives one-sided `p=.1056` (two-sided `.2033`). Host
points are positive on Test 1, Test 3, and Test 4; Agent 5 is `-1.900/game` on
only one candidate versus three controls. Preserve the randomized arm: this is
the first persistent prospective official signal, but 9/16 is below the frozen
20/arm harm look, uncertainty crosses zero, and Agent 5 still blocks promotion.
The checkpoint artifacts are
`.ai/NEGOTIATION_OFFICIAL_{RAW_,}SCOPED_CLONE_2336_2353.json` and
`.ai/NEGOTIATION_OFFICIAL_{RAW_,}SCOPED_CLONE_2352_0005.json`; deduplicate the
single overlapping dashboard capture by exact joined game id. Bargaining and
Test 2 remain untouched.

### 2026-08-25 00:16 IST: do not wire the exact Athena transcript table

The untracked Athena sidecar is evidence-bounded but operationally inert. A
reachability scan over the latest 20 MB of each of the five live turn streams
(`1787591775..1787597181`, 22:46–00:16) contained 5,248 unique negotiation
decision states and 2,638 player-2 buyer states. Its 21 exact complete-history
counters plus four exact one-round accepts matched `0/2,638`. Wiring or arming
it would therefore create a zero-reach placebo A/B, not copy Athena at useful
coverage. Keep it untracked and undeployed. The next leader imitation must
copy a reachable state-conditioned rule/trajectory with `eligible>0`,
`fired>0`, and `action_changed>0`; do not weaken point observations merely to
make this table fire. No bargaining state or process changed.

### 2026-08-25 00:24 IST: discount-aware bargaining arm implemented, default OFF

Test 2 and Test 3 remain the best bargaining agents and are indistinguishable in
the complete latest-12h first-exposure cohort (`.5259`, n=980 vs `.5258`,
n=1,038 fitted percentile; both 99.7% agreements). The actionable defect is
narrower: after a baseline Reject, compare the standing share with the exact
wire-coerced counter the policy will send next, discounted one round by our own
delta. In 49/49 complete leader-log first triggers with `delta_me<1`, immediate
acceptance beat the realised final; mean identified lift was +.03326 pot share
and +.02005 diagnostic percentile. The `delta_me=1` row lost .0505 pot share on
average (n=16), so it is explicitly excluded.

`GLEE_BARG_DISCOUNT_NO_REGRESS_AB=1` now hash-assigns each game with
`barg_discount_no_regress_v1|<game_id>`. At the first eligible state both arms
have followed identical behavior and log the same pre-action signal; control
keeps Reject, candidate changes only that decision to Accept. The implementation
fails closed if the older nominal `GLEE_BARG_NO_REGRESS` is armed. Default OFF
does not add plan metadata or change an action. The production helper exposes
the pure assignment, and the live reader cohorts on the first trigger, retains
unresolved/no-deal/zero outcomes, removes cross-fleet duplicates, independently
recovers the hash, audits wires/traces, and optionally joins authenticated
official deltas:

`.venv/bin/python scripts/live_percentile.py --ab barg-discount-no-regress --since T0 --slots hardliner,conceder --official-json FILE`

Exact-stack reachability passes: hardliner 31 eligible / 22 fired / 22 changed
over 1,200 paired games; conceder 28 / 15 / 15. Focused tests pass 21/21,
including a zero-offer regression that proves the arm never accepts $0. The
precommitted harm/final rules are in `.ai/EXPERIMENTS.md`. Do not arm Test 4:
its custom randomized strategy bypasses `bargaining.decide`, which is also why
its current `BARG_OBSERVED_GAIN=1` display is inert. No live flag, fleet process,
`arms.json`, `control.json`, `.env`, or log was changed.

Final full suite after the zero-offer fence: 1,658 passed. Only the two
AGENTS.md-predeclared failures remain (`test_bargaining_horizon_floor`, current
468 vs expected 450, and `test_sim_grid[bargaining]`, live grid drift).

### 2026-08-25: Test 4 bargaining host prepared at operator direction

The earlier “do not arm Test 4” objection was a routing fact, not a permanent
host decision: its `randomized` custom policy intercepted bargaining before
`bargaining.decide`. `GLEE_PROBE_RANDOMIZED_BARG_BASE=1` now provides the
missing default-off route. It sends only Test 4 bargaining through normal
dispatch; its negotiation and persuasion policies remain byte-for-byte the
same seeded randomized policies. On Test 4's exact current stack, the route is
not a placebo: 4,465 eligible / 3,263 fired / 3,263 changed over 2,400 paired
games. With the route present in both arms, the nested
`GLEE_BARG_DISCOUNT_NO_REGRESS_AB=1` check passes 50 / 16 / 16 over 2,400 paired
games with the required OBSERVED_GAIN zero. Focused tests pass 26/26, including candidate/control decisions through
the actual `make_probe("randomized")` wrapper and isolation of both other
families.

Claude-only live action after this code has reached Test 4: at one clean Test 4
boundary set `GLEE_PROBE_RANDOMIZED_BARG_BASE=1`,
`GLEE_BARG_DISCOUNT_NO_REGRESS_AB=1`, and `GLEE_BARG_OBSERVED_GAIN=0`, then
record T0. The explicit zero matters: OBSERVED_GAIN is currently 1 but inert
under the random probe; opening the route would otherwise activate it as an
unplanned second bargaining treatment. Keep `GLEE_BARG_NO_REGRESS=0`. Read only
Test 4 with `scripts/live_percentile.py --ab barg-discount-no-regress --since
T0 --slots randomized --official-json FILE`. This prospectively replaces the
earlier Test 2/Test 3 host plan before any arm activation or outcome inspection.
No live flag, process, `arms.json`, `control.json`, `.env`, or log was changed by
Codex. Final allowed suite: 1,663 passed; only the two predeclared failures
remain (`test_bargaining_horizon_floor`, 468 versus stale 450 expectation, and
`test_sim_grid[bargaining]`, live grid drift).

### 2026-08-25: correction — Test 4's slot name is not its live policy

The preceding Test 4 entry reasoned from the slot name and is superseded here.
`control.json` maps every slot, including `randomized`, to policy `champion`;
Test 4's current process command and every recent launch marker confirm
`run_agent.py --probe champion`. Thus zero whole-policy randomizers are live,
not one. All five agents already play the champion family dispatch; before this
cleanup all five nevertheless carried at least one narrow hash-randomized A/B.

Operator transferred deployment authority to Codex. Commit `8a8c5c9` is pushed.
The Test 4 overlay now has `GLEE_BARG_DISCOUNT_NO_REGRESS_AB=1`,
`GLEE_BARG_OBSERVED_GAIN=0`, and
`GLEE_PROBE_RANDOMIZED_BARG_BASE=0`; a named zero-game cycle is queued so the
new bargaining code loads without abandoning a game. Exact actual-policy
preflight is 50 eligible / 16 fired / 16 changed over 2,400 paired bargaining
games. Test 2's sole active treatment,
`GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB`, was explicitly set to zero so the
current overall/bargaining leader is a deterministic champion control. Four
non-leading slots retain scoped experiments because only the account's best
agent determines placement.

### 2026-08-25: operator selected deterministic family specialists

The operator rejected both the research-host layout and a five-way identical
clone. At `T1=1787600396`, every `*_AB` flag was explicitly zero on all five
slots; the arm objects are byte-identical and contain no enabled randomizer,
cell-specific experiment, observed-gain trial, or randomized-probe router.

The configured launch topology is now Test 2 + Test 3 = `hardliner` bargaining,
Agent 5 = `hardliner` negotiation, Test 1 = `champion` negotiation, and Test 4 =
`conceder` persuasion. All use LLM off. Five named safe cycles are queued; do
not call a specialist live until its actual PID command and launch marker show
the configured policy/family. Pre-cutover processes remain on their earlier
all-family champion commands until they naturally drain. No game was abandoned.

### 2026-08-25 01:24 IST: negotiation trials restored after accidental disarm

The deterministic-specialist cutover above set every `*_AB` flag to zero and
therefore silently stopped both active negotiation experiments even though
`CURRENT_STATE.md` still described them as armed. At operator direction to
implement and keep testing negotiation, Codex restored only
`GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB=1` and
`GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB=1` on champion, composite,
conceder, and randomized at arms-file `T1=1787601236`. Runtime overlays expose
those values within three seconds; no process was interrupted and no bargaining
flag or policy was changed. After the queued specialist cutover, only Test 1
and Agent 5 will continue to queue negotiation, so Test 3/Test 4's negotiation
flags become inert rather than changing their assigned family.

The newest exact authenticated cap-10 join added 31 matches. Combined with the
earlier exact files and deduplicated by game ID, the observed arm read is
candidate official rating `+0.9053` (n=19) versus control `+0.3652` (n=23), an
ITT lift of `+0.5400` rating/game; local diagnostic percentile is `.5729`
versus `.5053` (`+.0676`) and close rate is 48.0% versus 25.7% (`+22.3pp`).
The intervals remain wide and this is one candidate short of the frozen 20-arm
harm read, so it is evidence to continue, not a promotion claim. The pooled
mechanism audit rejects because the earlier read spans disabled/old-code games
(15 candidate wire mismatches plus four missing traces); freeze a clean second
cohort from `T1=1787601236` and require exact scoped-source wires before using
it causally. The Opus unknown-horizon arm has only two exact official candidate
outcomes so far (`-4.5`, `+3.5`) and remains far below its harm-read sample.

### 2026-08-25 01:35 IST: max-of-five full-stack portfolio supersedes single-family map

The operator clarified the actual selection objective: competition placement
uses the single best complete agent. Restricting slots to one family therefore
throws away selection opportunities and cannot identify the best complete
agent. The pending single-family launch map was superseded before any queued
cycle landed.

All five configured launches now queue `bargaining,negotiation,persuasion` with
LLM off. Deterministic profiles are Test 1=`champion`, Agent 5=`composite`, Test
2=`hardliner`, Test 3=`conceder`, and Test 4=`composite`; Test 4's historical
slot/log name remains `randomized` but no randomized policy is configured.
Profile specialization supplies max-of-five diversity without making agents
family-ineligible.

Three narrow A/B flags had been restored on four slots at 01:24. They conflicted
with the operator's no-randomizer instruction and were explicitly set to zero
again at `T2=1787601952`. Every arm object is now byte-identical and every
`*_AB`, `GLEE_BARG_OBSERVED_GAIN`, and
`GLEE_PROBE_RANDOMIZED_BARG_BASE` value is zero. Five safe named cycles were
requested; verify actual replacement PID commands before calling the portfolio
live, and never signal a process holding competition games.

### 2026-08-25 01:55 IST: protect Test 2 during deterministic diversification

At the operator's request, the actual live/configured split and leader risk were
rechecked. Test 2 led at 2244 overall while still running `champion`; its pending
`hardliner` launch would leave bargaining and negotiation effectively unchanged
under the canonical overlay but replace honest persuasion with the historically
weaker lie-heavy transform. Before Test 2 or Agent 5 rotated, their configured
profiles were swapped: Test 2 stays `champion`, while lower-rated Agent 5 becomes
the deterministic `hardliner` challenger. Both continue to queue all three
families. Safe cycles were re-requested and no process was signalled.

Test 3 and Test 4 completed clean zero-abandonment cycles at 01:48:37/01:48:39
and launched at 01:48:50 as all-family `conceder` and `composite`, respectively.
Test 1, Agent 5, and Test 2 were still running all-family `champion` at the time
of this entry. Every randomized/cell-specific flag remained explicitly zero.

### 2026-08-25 05:54 IST: deterministic first-principles negotiation component implemented, default OFF

At operator direction, the existing first-principles negotiation policy now has
a non-randomized promotion path: `GLEE_NEGO_DETERMINISTIC_FP_V1=1`. It never
hashes a game ID. It owns all eligible games and precedes the broader
`rank_hybrid_v1` / `leader_replica_v1` buyer dispatch so a selected full policy
cannot shadow its terminal prices. All other negotiation cells retain the
selected complete policy.

Owned cells and exact behavior:

- complete-information, known one-round seller: ask visible buyer value minus
  `$0.01`;
- complete-information, known ten-round buyer: reject ordinary earlier offers,
  counter at visible seller value plus `$0.01`, accept an offer only at the
  existing 0.994-of-zone boundary, and bid seller value plus `$0.01` on the
  terminal buyer turn;
- hidden-information, known one-round seller: use the official four-point grid
  and per-configuration scoring ask already implemented by Test 4 (`80 ->
  119.99`, `100 -> 119.99`, `120 -> 149.99` at scale 1). A top-ranked human
  independently reported the exact `80 -> 119.99` move on 2026-08-25.

Evidence is mechanism-level, not a claimed live treatment effect. Across all
locally retained complete-information terminal offers, positive opponent gain
was accepted 1,489/1,493, exact `$0.01` was accepted 39/40, and non-positive
gain was accepted 0/159. Those records do not identify unplayed offers or the
full first-turn ITT because the historical outcome collector left many games
unresolved; arbitrary bots can also walk away or spite-reject a positive cent.
The hidden `119.99` rule uses the public support and the official
per-configuration score model, not an exact prediction of a hidden opponent
value and not an accepted-deal-only value sample. The human's claim that own
value reveals only the feasible opponent values remains selection-biased until
no-deals and unresolved games can be included, so no such point predictor was
added.

Exact champion-stack reachability over 800 sampled negotiation games / 6,188
banked decision states: 259 eligible, 259 fired, 255 wire actions changed. The
four unchanged actions already matched the component. Focused policy, wire,
precedence, flag-off, and family-isolation tests pass 49/49. The full suite is
1,879 passed / 3 failed; all three are state-data failures unrelated to this
diff: the predeclared bargaining horizon-floor expectation (468 live versus
450 stale), bargaining grid drift, and a newly tripped negotiation horizon-grid
drift alarm from accumulated logs. No live flag, fleet process, `arms.json`,
`control.json`, `.env`, bargaining behavior, or persuasion behavior was changed
for this negotiation implementation. Code-only commit `9a23ed8` is pushed to
`origin/main`; the deployment flag remains OFF.

### 2026-08-25 06:08 IST: Agent 5 whole negotiation replacement ready for deployment

Operator clarified that the new policy must replace Agent 5's negotiation
dispatcher rather than act as a layered three-cell flag. The new single
default-off selector is `GLEE_NEGO_AGENT5_DEFAULT_V1=1`. It is mutually
exclusive with `GLEE_NEGO_LEADER_REPLICA_V1` and
`GLEE_NEGO_RANK_HYBRID_V1`; more than one selected whole policy fails closed.

The complete deterministic matrix is:

- first-principles hard precedence in complete cap-1 sellers, complete cap-10
  buyers, and hidden cap-1 sellers;
- observed-leader buyer decisions/prices in every other supported buyer cell;
- the measured current seller stack as an explicitly labelled fallback only in
  seller cells where no replacement rule is identified, plus the 57/57 observed
  deterministic seller-message table where supported.

Direct first-principles and observed-leader moves return before the legacy
planner and randomized message attachment. `actions.coerce()` independently
recomputes the selected whole-policy wire and returns before every hidden floor,
opening claim, ultimatum cap/floor, TABLE, or ZOPA postcondition, so a legacy
guard cannot rewrite an owned price. Every negotiation A/B remains OFF.

Exact Agent 5 `hardliner`/`composite` reachability over 800 negotiation games
and 6,188 banked states: 6,188 eligible, 6,188 fired, 3,274 submitted actions
changed. Focused ownership and isolation tests pass 56/56. Full suite: 1,886
passed / the same three unrelated state-data failures (stale bargaining 450 vs
468 expectation and the bargaining/negotiation live-grid drift alarms). This
entry changes negotiation only; no bargaining or persuasion implementation is
part of the policy.

### 2026-08-25 06:21 IST: hidden-value terminal inference added and Agent 5 activated

The top-human clarification supplied an identified use of hidden seller asks in
known ten-round games where our buyer is player 2. Under the official discrete
value support, the lowest price the seller has offered is an upper bound on the
seller's reservation value. Agent 5 now uses that bound on its terminal buyer
turn: an observed seller ask at or below `97` implies a terminal `80.01`; at or
below `119` implies `100.01`; and at or below `149` implies `120.01`, with the
same mapping scaled for the larger currency grids. The inference uses only the
opponent seller's own asks, takes the minimum across their history, never treats
our own rejected bids as evidence, and falls back to the complete deterministic
buyer policy when the support does not identify a safe bound. This is commit
`b29f7a5`, pushed to `origin/main`.

Focused negotiation tests pass 63/63. The full suite reports 1,893 passed and
the same three unrelated live-data/stale-expectation failures: bargaining
horizon floor (468 actual versus 450 expected), bargaining grid drift, and
negotiation max-round grid drift. Exact Agent 5 reachability remains 6,188 /
6,188 eligible states fired, with 3,274 submitted actions changed over 800
sampled games. This evidence establishes wiring and mechanism behavior, not a
live percentile lift; the latter requires post-activation completed-game data
including no-deals, zeros, timeouts, and unresolved outcomes.

Agent 5 (`composite` slot, `hardliner` launch profile) was clean-cycled before
activation. The old process drained with zero games abandoned and PID `65057`
started at 06:21:01 with all three families still eligible. At configuration
boundary `Tcfg=1787619084`, only the negotiation whole-policy selectors were
updated: `GLEE_NEGO_AGENT5_DEFAULT_V1=1`, while
`GLEE_NEGO_LEADER_REPLICA_V1=0`, `GLEE_NEGO_RANK_HYBRID_V1=0`, and
`GLEE_NEGO_DETERMINISTIC_FP_V1=0`. The runtime overlay resolves the selected
mode as `agent5_default_v1`. Post-boundary turn traces show
`source=agent5_default_v1` / `component=observed_leader_buyer` on buyer turns
and `deterministic_policy=agent5_default_v1` / `component=current_seller` on
the deliberately retained seller fallback.

This is a whole negotiation dispatcher, not a tactic layered beneath the old
stack. First-principles, hidden-terminal-inference, and observed-leader buyer
moves return before the legacy planner; the wire coercion path recomputes and
protects those owned actions from downstream legacy price guards. The only old
negotiation behavior retained is the explicitly labelled seller fallback in
cells for which no evidence-backed replacement has been identified. Test 2 was
not changed. Bargaining and persuasion flags and behavior were not changed.

### 2026-08-25 06:34 IST: human Bob/H12 terminal-commitment policies implemented, default OFF

The reported Bob last-mover tactic exposed a real bargaining hole. In a
disclosed twelve-round game Bob proposes on every even round and owns round 12,
but the current generic stack sends a modal 61% Bob share at every even round,
including the terminal one. `GLEE_BARG_BOB_OFFER=1` is only an ask-raising
fitted floor and excludes the last two rounds; the generic opponent floor also
rewrites the nominal 75% ultimatum back to 61%. Integer-pot coercion rounded
away cents, so the old stack could not leave the opponent exactly `$0.01`.

Three independent, deterministic, default-OFF components now own their exact
Bob/H12 cells end to end:

- `GLEE_BARG_P2_H12_D095_SILENT_V1`: message-off, `delta_2=.95`, literal Bob
  shares `.61/.68/.74/.82/.91/(M-.01)` on rounds 2/4/6/8/10/12;
- `GLEE_BARG_P2_H12_D095_MSG_COMMIT_V1`: message-on, `delta_2=.95`, with
  `V=(M-.01)*.95**11`, Bob asking `V/.95**r-.01` on even round `r<12`, and a
  concise truthful explanation that Alice receives one cent more now than she
  can keep in her next offer while meeting Bob's coded discounted floor;
- `GLEE_BARG_P2_H12_D100_COMMIT_V1`: `delta_2=1`, Bob asks `M-.01` on every
  even round and discloses the unchanged floor only when messages are allowed.

All variants accept an odd-round Alice offer exactly when its discounted Bob
payoff meets the same terminal floor. More than one component flag fails
closed. A message-bearing component also fails closed if the old randomized
`GLEE_BARG_MSG` bank is armed. Exact-cent coercion is bypassed only after the
enabled component independently reproduces both submitted gains in the full
structural cell; generic integer-pot offers still round exactly as before.

The `.95` silent ladder's realised Bob shares are
`.57950/.58302/.57260/.57264/.57353/.56874`. This is a payoff floor only if an
agreement is accepted; it is not an outcome or rating guarantee because an
opponent can reject, walk, time out, or spite-reject the terminal cent. In the
complete-log audit, our positive terminal bargaining offers were accepted
150/154, but none left exactly one cent, so field cent acceptance remains
unmeasured. The message-on target has 1,848 enrolled games, 977 joined and 871
unresolved; observationally, text-bearing offers closed 25/107 versus
363/1,235 silent. The message policy changes 3,289/3,289 target offers and
861/4,159 decisions. `delta=1` is a separate, still more aggressive policy.
Only the silent `.95` component is a defensible first challenger; keep the
message and patient flags OFF until separately justified.

Exact Test 4 `randomized`-slot / `composite`-probe reachability over 1,200
sampled bargaining games passed for every flag:

- `.95` silent: 162 eligible / 162 fired / 53 submitted actions changed;
- `.95` message: 240 / 240 / 126;
- `delta=1`: 451 / 451 / 240.

Focused tests pass 53/53. Full suite: 1,946 passed / the same three unrelated
state-data failures (stale bargaining horizon-floor expectation plus
bargaining and negotiation live-grid drift). No live flag, process,
`arms.json`, `control.json`, `.env`, log, negotiation behavior, or persuasion
behavior was changed by this implementation.

Negotiation review objection retained for the deployment lane: complete-info
cap-10 buyer `seller_value+$0.01` has a strong terminal-only case (14/14 exact
cent responses; Wilson-lower expected lift still `+0.1449` across the
all-enrolled audit), but that does not identify a broader hold-out trajectory.
The hidden one-round seller `.8B -> 1.1999B` move is not supported over the
current `1.15B`: five of six exact score cells are tied, the sixth gains only
`.00219`, and exact-cent response uncertainty makes the conservative expected
lift negative. Hidden values remain independent over the four-point support;
agreement-only reconstruction is survivorship-selected and must not become a
point predictor.

### 2026-08-25 07:04 IST: Agent 5 negotiation policy mirrored to Test 2

At direct operator request, Test 2 / slot `hardliner` received the exact Agent
5 negotiation overlay at `Tcfg=1787621680`: `GLEE_NEGO_AGENT5_DEFAULT_V1=1`,
with `GLEE_NEGO_LEADER_REPLICA_V1=0`, `GLEE_NEGO_RANK_HYBRID_V1=0`, and
`GLEE_NEGO_DETERMINISTIC_FP_V1=0`. All `GLEE_NEGO_*` values now match Agent 5;
no bargaining or persuasion flag was copied or changed.

Test 2 PID `68625` began at 06:49:13 after commit `b29f7a5` was already in
HEAD, so no process cycle was required. Its exact live `champion` stack passed
prospective reachability over 800 games / 6,188 decision states: 6,188
eligible, 6,188 fired, and 3,274 submitted actions changed. Runtime overlay
inspection resolves `mode=agent5_default_v1`, and post-boundary live traces
show both `observed_leader_buyer` and `current_seller` branches labelled with
that policy. Test 2 remains eligible for all three families and retains its
existing bargaining and persuasion behavior.

### 2026-08-25 07:29 IST: Agent 5 Bob/H12/.95 silent policy live

At direct operator request, only
`GLEE_BARG_P2_H12_D095_SILENT_V1=1` was armed on Agent 5 / `composite`;
`GLEE_BARG_P2_H12_D095_MSG_COMMIT_V1=0` and
`GLEE_BARG_P2_H12_D100_COMMIT_V1=0` remain OFF. The process still launches
the `hardliner` profile with LLM OFF and all three families eligible. The
safe supervisor cycle drained PID `65057`, explicitly recorded zero games
abandoned at 07:28:04, and launched replacement PID `72600` at 07:28:15 from
commit `ca79aa7`. The launch header contains the exact 1/0/0 flag stack, and
fresh turns from all three families show no import or runtime error.

The deterministic runtime flag was already visible to the old process before
its natural shift boundary, so the first fully target-scoped game began at
07:14:50 on PID `65057`; it did not switch policy mid-game. Gate traces own
all twelve decisions/offers and show the exact Bob ladder
`61/68/74/82/91/99.99` on a `$100` pot. The hidden opponent rejected through
round 10, offered Bob `87` on round 11 (below the coded nominal requirement
`94.9905`), then accepted the round-12 `Alice=.01, Bob=99.99` split. The
complete game record reports agreement, Bob payoff `56.87`, Alice payoff
`.01`, and twelve rounds played. This proves live reachability and supplies
one successful terminal-cent observation; it does not establish a rating lift
or reliable field acceptance. Continue counting every enrolled target game,
including rejections, timeouts, walkaways, unresolved games, and zeros.

### 2026-08-25 09:58 IST: Test 3 and Test 4 cloned from Agent 5

At the operator's explicit one-time request, the complete deterministic Agent 5
strategy surface was copied to Test 3 / `conceder` and Test 4 / `randomized`
through `scripts/fleet.py`. The control writes landed at
`1787629249.9922638` and the live-overlay writes at `1787629250.0146475`.
Both targets now map to Agent 5's `hardliner` policy, retain LLM OFF, and remain
eligible for `bargaining,negotiation,persuasion`. Their 78-entry overlay maps
are byte-equivalent after canonicalisation to Agent 5 / `composite`, with
SHA-256 `f5781a1a2d8141294f808216a61bb6d3c889677d3f509772acbffd92e8a2b46c`.
All persuasion `*_AB` flags remain zero.

No slot was stopped, signalled, force-cycled, or disabled. The supervisor
allowed each old process to finish its held games and recorded clean natural
drains: Test 3 PID `79488` completed a 4,096-second shift at 09:37:25 and PID
`86555` launched at 09:37:36; Agent 5 PID `79678` completed a 4,179-second
shift at 09:44:37 and PID `87209` launched at 09:44:47; Test 4 PID `81396`
completed a 4,124-second shift at 09:57:54 and PID `88096` launched at
09:58:04. All three replacement processes run commit `e735ada`, `--probe
hardliner`, `--llm-mode off`, and the full three-family queue. The 10-11 second
handoffs show no boundary error or timeout.

Only behavioral configuration was copied. Test 3 and Test 4 retain their own
API identities, physical `GLEE_PROBE` overlay selectors, log directories,
ratings, histories, and dashboard attribution. No strategy code was changed,
and no test run was required for this configuration-only operation. Do not
infer a causal effect from the transition-era games: runtime overlays became
visible before the launch-fixed profiles changed, so use the clean PID/start
boundaries above for like-for-like evidence.

### 2026-08-25 11:31 IST: clone observation complete; restore diversity next

The exact common hardliner boundary `T0=1787632084` is now fully joined:
`1,028/1,028` terminal games and zero unresolved across Test 3 (`228`), Agent 5
(`307`), and Test 4 (`493`). Every outcome was retained. Bargaining contains
342 agreements and zero exact zeros; negotiation contains 156 agreements, 112
no-deals, 75 walks, and 187 exact zeros over 343 games; persuasion contains 77
zeros, 261 CDF-scoreable outcomes, and 82 retained CDF-unscoreable outcomes
over 343 games. Fitted all-outcome percentiles are bargaining `.32513`,
negotiation `.54655`, and persuasion `.54141`. The weakest bargaining cells
with at least ten observations are P1/public/unknown/message-on/delta-.8
`.14708` (`n=10`) and P1/hidden/H12/message-off/delta-.95 `.17975` (`n=11`).
Agent 5's next complete exact-stack shift rebounded from bargaining `.24840` to
`.36909`, so the clone does not identify its high-share or silent ladder as the
cause of the weak pooled bargaining result. Host and pre/post differences remain
observational.

Test 2's exact V3 process window `[1787632548,1787636699)` also finished
`391/391` terminal with zero unresolved: bargaining `130`, negotiation `131`,
and persuasion `130`. All 984 negotiation actions carried
`test2_support_v3`, proving live mechanism reachability. Negotiation's
all-outcome percentile was `.51773`, retaining 56 agreements, 34 no-deals, 41
walks, and 75 exact zeros. Its clearest sufficiently sampled misses were
seller/hidden/cap-10/message-on `.42196` (`n=11`) and
buyer/hidden/unknown/message-on `.42484` (`n=17`). Bargaining remained the
window's weakest family at `.34807`, but V3 cannot cause bargaining behavior.
The preceding exact-V2 process still has unresolved joins, so this is not a
V3-versus-V2 causal promotion result.

The completed clone cohort exposed only two rejected offers that the default-
off `GLEE_BARG_ACCEPT_FLOOR_EXACT_V1` would change. One immediate acceptance
beat the realised continuation by 6.12 pot points and one lost by 5.67, for a
mean alternative of only `+.225` pot points (`n=2`); neither was the
delta-.8/share-.20 atom. This new complete evidence does not invalidate the
separate historical six-win motivation, but it is too sparse to arm the flag.
Keep `e735ada` inert and OFF.

The one-time clone observation has therefore reached its natural stopping
point. The next falsifiable portfolio action is to restore Test 3's documented
conceder/control stack and Test 4's documented composite/leader-replica stack
at separate clean natural boundaries, leaving Agent 5 and Test 2 untouched.
Verify the actual replacement commands and exact overlays, then evaluate each
whole-process cohort with every outcome, role, and cell retained. Only after
restoration should the exact-floor flag receive fresh restored-stack
reachability and a new one-challenger decision rule; do not infer a treatment
effect from cross-host rating movement.

### 2026-08-25 12:48 IST: correct the saturated-CDF false regression before tuning

The dirty `models/percentile_cdf_v3.json` is not a valid scoring instrument.
Its 106,802-game refit hit `MAX_PER_CELL=2000`, while the fitter wrote
`sorted(values)[-2000:]`. That retained only each saturated cell's highest
payoffs, removed every zero from several bargaining cells, and moved their
minimum to `.47`. The same complete 636-game bargaining cohort scores `.53502`
against the checked-in 32,223-game CDF but only `.31171` against the dirty
top-tail CDF. The supposed P2/hidden/unknown/silent/delta-.95 weakness reverses
from `.35566` to `.61530` in the common clone cohort and is `.55308` across all
14 available games. All 636 bargaining outcomes were agreements, with zero
exact zeros or unresolved games; no parser, wire, or reachability defect was
found. Therefore the prior fitted-percentile values in this handoff are
invalidated wherever they used the dirty model; their raw enrollment and
outcome counts remain valid.

Commit `d0a9ada` fixes the fitter without rewriting the live model: saturated
cells now use deterministic evenly spaced order statistics, retaining the
whole distribution rather than its top tail. Focused tests pass 3/3; the full
suite is 2,102 passed with only the stale bargaining horizon-floor assertion
and the bargaining/negotiation live-grid drift alarms. No strategy, flag,
control, process, or model artifact was changed.

The two newest clean cohorts were rescored entirely in memory against the
committed model. Test 4 PID `91902` bargaining is `.59109` (`n=167`, all
agreements), `+.06780` versus its preceding exact hardliner cohort; P1/P2 are
`.60090/.58364`. Test 2 PID `92288` bargaining is `.51144` (`n=147`, all
agreements), only `-.03468` versus its preceding exact V3 cohort; P1/P2 are
`.48469/.53208`. The dirty-model `.360/.295` values must be discarded.
Negotiation is essentially stable on Test 2 (`-.00319`) and down `.03292` on
Test 4, localized to its seller role; persuasion is flat on both. These remain
observational whole-profile comparisons, not treatment estimates.

Before making another behavioral proposal, refit into a separate candidate
artifact, verify zero atoms and both tails against the uncapped source for every
saturated cell, then rerun every recent frozen cohort from its clean process
boundary. Also fit a research-only bargaining diagnostic stratified by seat and
own delta and calibrate it against official rating deltas; the current CDF pools
both, so its `.38339` reading for the 16 delta-.8 games does not identify a bad
accept rule. Those 16 games all accepted profitable incoming offers on round 1,
and raising their floor repeats a previously measured-harm direction. No
bargaining behavior change is justified; preserve Test 2, Agent 5, and the
known-12 P2 ladder.

### 2026-08-25 13:55 IST: pointwise copied-buyer walk repair landed inert

Four initial complete hardliner-profile buyer games selected the copied round-17
`WalkAway` while holding a canonical standing offer that left `.03B` or `.045B`
of strictly positive buyer payoff.  The played walk itself terminates at zero,
so accepting that same offer is pointwise identified rather than a fitted
continuation claim.  Against the committed pooled hidden-cell CDF, the four
diagnostic lifts over zero are `+.22917`, `+.33607`, `+.38889`, and `+.22917`;
they are not official-cell estimates.  Four subsequent clean cohorts added
eight matching cases, including both message modes and Test 2 V3, for twelve
complete identified examples in total.  This is not a
renamed version of the measured-negative broad hidden/unknown accept-all policy:
it cannot touch an earlier `RejectOffer`, counteroffer, or any non-walk action.

Local commit `42f21cb` adds default-OFF deterministic flag
`GLEE_NEGO_HI_UNKNOWN_BUYER_WALK_ACCEPT_V1`.  It is scoped to the measured Agent
5 V1 and Test 2 V3 `observed_leader_buyer` component in hidden-information,
explicitly unknown-horizon buyer decisions with an explicit boolean message
mode; it requires exact role/turn/standing-offer provenance and at least one
cent of finite positive buyer gain.  V2, sellers, capped horizons, malformed
states, and all earlier decisions are unchanged.  The flag is consulted only
after the exact structural predicate holds.

Focused tests pass `92/92`.  Exact Agent 5 V1 composite-stack and Test 2 V3
support-stack reachability each report `eligible=16`, `fired=16`,
`action_changed=16`, all at round 17 with `WalkAway -> AcceptOffer`.  The
reachability-only opponent holds the observed
`1.455B` ask and restores the live API's recorded-history echo shape that the
local engine omits; no payoff is synthesized.  The full suite is `2216 passed`
with only the three pre-existing failures: the stale bargaining horizon-floor
assertion and bargaining/negotiation live-grid drift alarms.

The commit is local and unpushed.  The flag is absent from every live slot, no
control or arms file was edited by this change, and no process was cycled or
signaled.  Claude should independently review, push if accepted, and only then
consider an OFF-by-default one-challenger activation at a clean natural
boundary.  Agent 5 (overall leader), Test 1's bargaining leader/peak stack, and
Test 2 remain protected.

### 2026-08-25 14:35 IST: fresh hardliner shifts isolate bargaining extraction, not closure

The completed Test 3 PID `97575`, Test 4 PID `99621`, and Agent 5 PID `99522`
cohorts retain all 1,353 games and have zero unresolved outcomes or local
errors.  Their bargaining means against the committed distribution are
`.49597` (`n=151`), `.46807` (`n=156`), and `.50830` (`n=144`), respectively,
down `.03778`, `.11594`, and `.04361` from each slot's preceding exact
hardliner shift.  Yet 450/451 bargaining games closed, so the repeated weakness
is rank/extraction rather than deal formation.  The clearest recurring slice is
complete-information P1: Test 4 known-12/message `.1999` (`n=7`),
unknown/message `.2091` (`n=8`), and known-12/silent `.2441` (`n=10`); Agent 5
known-12/message `.2226` (`n=12`); Test 3 known-12/silent `.3269` (`n=10`).
These are observational shift comparisons, not a causal estimate, and do not
justify changing the live offer or acceptance schedule.

The same Test 3 shift added a thirteenth point-identified profitable walk for
the existing negotiation repair: hidden/unknown/silent buyer game
`46c602a0-098d-44f9-89a7-f60917beaaa1` walked on round 17 while facing a
canonical ask `148.57` against value `150`.  Accepting yields `1.43` instead of
the played zero and moves the committed-CDF diagnostic from `.18182` to
`.38182`.  This independently reinforces `42f21cb`; it does not support any
earlier or broader profitable-offer acceptance rule.

The falsifiable next bargaining question is whether the current P1
complete-information outgoing path concedes rank too cheaply while already
closing almost every game.  Before building anything, enumerate the exact
round/discount/offer atoms in those weak cells, compare every game (not only
agreements) with the preceding exact-profile shifts, and verify the effect is
not an opponent or CDF-composition change.  Any candidate must be a narrow
default-OFF deterministic flag, leave P2's known-12 peak ladder and Test 2's
exact peak stack untouched, and prove exact-stack reachability before a single
non-leading challenger is considered.  Do not deploy a higher acceptance floor:
that repeats the already measured-harm direction.

Operationally, remote `main` is still `6d3aec4`; local `42f21cb` remains one
commit ahead and the profitable-walk flag is absent from all overlays.  Test 4
and Agent 5 naturally loaded final inert code, while current Test 3 loaded an
intermediate amend and must not be armed until a reviewed push and a verified
replacement PID.  All randomizer/A-B controls remain zero.  Agent 5 is still
overall #1 and Test 1 bargaining #1; neither should be touched.

### 2026-08-25 15:06 IST: leader cohorts clean; apparent P1 decline is mostly composition

The newly completed Test 2 PID `431` and Test 1 PID `1642` cohorts retain all
`899/899` terminal games, both roles, every outcome, and every configuration;
there are zero unresolved joins.  Across `9,864` turns, schema validation found
zero parser, source, wire, or action errors.  Test 2's family percentiles are
bargaining `.53875` (`n=149`, all agreements), negotiation `.51300` (`n=149`,
`80` zeros retained), and persuasion `.55223` (`111/149` scoreable, `34` zeros
retained).  Test 1's are `.52206` (`n=150`, all agreements), `.49715`
(`151/152` scoreable, `80` zeros retained), and `.61932` (`115/150` scoreable,
`27` zeros retained).  This leaves no crash/parser explanation for the current
cards.

The sharpest adequately sampled cells are Test 1 hidden/unknown/silent seller
negotiation `.37984` (`n=12`, `9` zeros) and P1 hidden/unknown/message
bargaining `.35132` (`n=9`, all agreements); Test 2 hidden/H10/silent seller
negotiation `.40224` (`n=10`, `7` zeros) and P1 hidden/H12/message bargaining
`.35743` (`n=8`, all agreements).  Every inspected Test 1 negotiation zero
lacked a strictly profitable incoming offer.  The bargaining misses therefore
remain extraction problems, while the negotiation misses need action-path
comparison rather than a blanket acceptance change.

Across the three newest hardliner shifts and their preceding exact-profile
shifts, all `236` complete-information P1 bargaining games agreed.  Raw pooled
percentile fell `.47022 -> .38496`, but opponent `delta=1` exposure rose
`28.1% -> 38.3%`; reweighting the `44` shared exact horizon x message x delta
pair strata leaves only `-.01509` within-stratum movement versus the raw
`-.08525`.  All `301` target rejected incoming offers had a next counter whose
discounted own value exceeded the standing offer, with zero pointwise-dominated
rejections.  Do not change the `.57/.61` P1 schedule from this observational
draw.  Pre-register the exact four-way strata and require two more clean shifts
plus official per-game deltas; reject the weakness hypothesis if the
within-stratum move remains within `+/- .02`.

The state generator itself had been stamping a fresh header over a preserved,
stale `Current experiments` tail, including obsolete policies, flags, and PIDs.
`scripts/refresh_state.py` is locally corrected to label the checkout as
`workspace HEAD`, regenerate only invariant deploy mechanics, and point dated
experiment claims to `EXPERIMENTS.md`; it now captures Test 1 replacement PID
`27573`.  This monitoring-only edit touches no strategy, overlay, log, or
process.  Full validation remains `2216 passed` plus the same three known
failures (one stale bargaining expectation and the two live-grid drift alarms).

### 2026-08-25 15:52 IST: clean-shift rebound; ladder guarantee disproved without a removal case

The completed Test 3 PID `23565`, Test 4 PID `24560`, and Agent 5 PID `25133`
cohorts retain all `1,404/1,404` terminal games and both roles, with zero
unresolved joins.  Their `14,358` turns are all heuristic and contain zero
schema, parser, wire, duplicate, or action errors.  Test 3's unchanged
hardliner stack rebounded across every family versus its preceding exact shift:
bargaining `.49597 -> .51924` (`n=165`), negotiation `.46166 -> .53967`
(`n=165`), and persuasion `.55701 -> .61110` (`159/165` scoreable).  Agent 5
also improved bargaining `.50830 -> .53655` (`n=141`) and persuasion
`.57490 -> .58582` (`106/140` scoreable), while negotiation moved
`.52617 -> .49563` (`n=131`).  This same-code reversal is direct evidence that
the recent card movement is too composition-sensitive to identify a policy
regression.

The exact live P2/known-12/own-discount-.95/silent ladder now has `25` complete
games across clean Test 3, Test 4, and Agent 5 cohorts, with every outcome
retained: `23` agreements and `2` no-deals/zeros.  All `153` eligible turns
fired and changed the wire action with no errors.  Of `10` games reaching the
terminal one-cent demand, opponents accepted `8` and rejected `2`; both rejects
were complete-information games against an undiscounted (`delta_opp=1`)
opponent.  The pooled committed-CDF mean is still strong at `.76508`, and every
successful terminal-cent agreement beat its game's earlier rejected offer.
Therefore the human claim that the cent demand is guaranteed is false, but a
broad ladder revert is not supported.  The two failures are a post-hoc thin
slice and do not justify changing Agent 5 or Test 2.  The falsifiable next
question is whether complete-information, `delta_opp=1` games that actually
reach the late ladder should accept a sufficiently strong round-11 standing
offer.  Accumulate a prospective all-outcome denominator before choosing any
threshold; if a guard is built, it must be default OFF, deterministic, and
decision-theoretically derived rather than fitted to these two losses.

Agent 5's weakest sampled negotiation cell was hidden-information,
unknown-horizon, message-on seller (`.36079`, `n=11`): `2` agreements,
`5` no-deals, `3` walks, `1` timeout, and `9` zeros.  None of those nine zeros
ever exposed a strictly profitable incoming bid.  The path instead opens
extremely high and then emits `235` `stall_park` actions around `.9B` or `1.4B`;
Clod was `0/3` while always bidding at or below reservation, and Opus variants
produced one tiny-margin agreement, one opponent walk, and one timeout.  This is
price-path compatibility/prolonged stasis, not an accept-parser miss.  A narrow
Clod/Opus convergence hypothesis would first need a legal profitable ZOPA in
the observed state; the current zeros do not establish one.

Operationally, all five agents are healthy with supervisor restart counts zero.
Test 2, Test 4, and Agent 5 rotated naturally to replacement PIDs `87826`,
`86582`, and `87495`; no agent was signalled or interrupted.  Every `_AB` and
router/randomizer control remains zero or absent.  There are only three unique
exact live stacks because Test 3, Test 4, and Agent 5 are byte-identical
hardliner overlays.  That violates the intended specialist diversity even
though it is not a per-game randomizer.  Do not touch overall-leading Agent 5
or Test 2's protected peak stack.  If Claude restores portfolio diversity, use
one clean non-leading natural boundary (prefer the weakest Test 3 slot), record
the exact pre-change stack and T0, and treat the comparison as observational,
not causal.

### 2026-08-25 16:27 IST: operator requests Test 3 specialist restoration

The operator explicitly selected Test 3 / physical slot `conceder` as the
specialist challenger.  The last exact pre-clone specialist is independently
recoverable from the identical 07:19:39 and 08:29:09 launch headers: policy
`conceder`, all three families, LLM off, and a deterministic 69-entry overlay
with every randomizer/A-B flag zero (canonical SHA-256
`df914eabdd6a0224db5f06331bb9fa090ff0ab003fc2cbf09d350a8f69590f53`).

Current PID `91069` launched at 16:19:14 as `hardliner` and held nine live games
at the 16:25 preflight, so it must not be interrupted.  Restore behavior at a
zero-game boundary by safely disabling the slot and letting this bounded shift
drain, then use `scripts/fleet.py policy conceder conceder` and explicitly set
`GLEE_BARG_DISCOUNT_NO_REGRESS=0`,
`GLEE_BARG_HIGH_SHARE_DELAY_GUARD=0`,
`GLEE_BARG_P2_H12_D095_SILENT_V1=0`, and
`GLEE_NEGO_AGENT5_DEFAULT_V1=0` before re-enabling it.  The seven other
clone-only keys are already explicit inert zeros.  Do not call
`fleet.py clear conceder`: that would remove the 69 shared measured controls.

Before calling the restoration live, require the old PID to be gone,
`logs/supervisor.json` to show the slot down, and the supervisor log to record a
clean drain.  Afterwards require a new PID whose command shows `--probe
conceder`, `--llm-mode off`, and all three families; verify the latest launch
header, the four explicit zeros above, and all A-B/router controls off, then
record that replacement start as T0.  Leave Agent 5 and Test 2 untouched and
treat the whole-process before/after comparison as observational.  Codex made
no live configuration or process change; repository policy reserves fleet
deployment to Claude.

### 2026-08-25 16:36 IST: deterministic strict-edge persuasion challenger for Test 4

Commit `67b684b` (pushed to `origin/main`) adds two deterministic, default-OFF
seller switches and composes them with the already-inert deterministic buyer
decline V2. No switch reads game ID, assigns an arm, or changes bargaining or
negotiation behavior.

- `GLEE_PERS_ZERO_MARGIN_TRUTH_V1=1` changes only known-value, low-quality
  seller turns where `p*v+(1-p)*u == price` within scale-safe tolerance from
  recommend to decline. High quality, strict-positive prior value, strict-
  negative prior value, and seller-blind cells remain byte-identical. The
  motivation retains all 170 comparable completed p=.8/r1.25 all-yes games:
  35 sold nothing, 123 exposed a bought low, and 42 of those buyers stopped
  completely while leaving a mean 12.38 later high-quality opportunities.
  This is mechanism evidence concentrated in one official cell, not an
  identified official-rating effect for every equality cell.
- `GLEE_PERS_P08_POSITIVE_PROSE_V1=1` changes only a positive p=.8 seller/text
  wire from literal `yes` to the fixed, quality-neutral sentence
  `I recommend this one.` Negative messages stay literal `no`; recommendation
  policy, binary mode, other priors, and buyers are unchanged. Historical
  within-text conversion was 69.3% prose versus 60.8% token at p=.8, but that
  contrast is observational and the earlier exact prose arm never reached its
  official decision boundary. No LLM wording is used; measured LLM copy was
  worse (46.3% versus 55.3% templates).
- `GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2=1` is the existing final BUY-to-PASS
  guard from `6d3aec4`. Its frozen exact replay changed 51 purchases in 16
  games and every one of the 51 observed purchased items was low quality;
  seller adaptation and action selection still prevent a causal rating claim.

Focused strict-edge/existing-component tests passed `116/116`. The full suite
passed `2231` tests with only the three pre-existing unrelated failures: the
stale 450-versus-468 bargaining horizon assertion and live bargaining/
negotiation grid drift alarms. Exact Test 4 `randomized`-slot / actual
`hardliner`-policy reachability over 1,200 paired persuasion games passed:
truth `644/644/644`, prose `2109/2109/2109`, and buyer V2
`1492/1492/1492` eligible/fired/action-changed.

The requested candidate host is Test 4 only. Preserve its entire existing
overlay and add exactly the three values above after a process has naturally
loaded `67b684b`; keep every persuasion `*_AB` flag at explicit zero. Record
the overlay timestamp and first post-activation turn as T0. Retain every
post-T0 persuasion game, both roles, all cells, zero/negative outcomes,
timeouts, and unresolved joins. This is a deterministic challenger comparison,
not a causal A/B; the prose and cross-equality extensions are the weakest
identified parts and should be first rollback candidates if adequately sampled
all-outcome role/cell performance deteriorates.

Deployment landed on Test 4 only. The old PID `86582` crossed its one-hour
cutoff, drained cleanly with zero games abandoned at 16:38:43 IST, and the
supervisor launched PID `92980` at 16:38:53 with policy `hardliner`, all three
families, LLM off, and workspace commit `67b684b` already checked out. Fleet
tooling atomically added the three deterministic values at
`Tcfg=1787656144.0263646` (16:39:04 IST). Runtime lookup on the `randomized`
slot resolves all three to `1`; the other four slots have none of them, and
the three old p=.8 persuasion A/B flags remain explicit `0`. The first
post-overlay persuasion action was at `1787656145.214844`. No new gate trace
appeared during the first roughly six post-activation minutes. That window
contained 354 persuasion turns across 19 games (174 seller, 180 buyer), but
zero p=.8 seller/text turns and zero known-value low-quality equality turns, so
the absent seller traces are expected non-eligibility rather than a reach
failure. No strict buyer-V2 decline appeared either. Live behavior is not yet
mechanism-verified; the exact-stack reachability above is the only action-change
evidence at this checkpoint.

### 2026-08-25 18:13 IST: Test 2 deterministic P1 unknown-horizon repair live

The operator explicitly overrode the earlier preference to protect Test 2 and
requested this candidate on physical slot `hardliner`. The old champion-policy
PID `94369` was disabled through `scripts/fleet.py`, finished every in-flight
game normally, and the supervisor recorded a clean drain at 17:58:11 IST. An
authenticated prelaunch check showed `active_games=0`; no process was signalled
and no game was abandoned. Its exact rollback overlay remains the 75-entry
stack with canonical SHA-256
`ad304a4510a456f7a0dda6e9802c84558dca568e24070c141470a86db0ee7ea6`.

Commits `f458a9c` and `12069ea` are pushed to `origin/main`. The first repairs
the corrupted percentile artifact: 131,413 games / 198 cells, all 12 saturated
bargaining cells again retain zero atoms, artifact SHA-256
`dd85dcde6ec5ce671786409c6458e469fe3a218558c09ff4ef00fcdef4ada55d`.
No live path currently consumes it because negotiation rank-price and
persuasion rank-gate remain explicit zero fleet-wide. The second adds
`GLEE_BARG_P1_UNKNOWN_DISCOUNT_DOMINANCE_V1`, deterministic and default OFF.

The candidate changes only a remaining Reject when P1 has an unknown horizon,
own delta exactly .95, round at least 10, a current high-water offer in
[.45,.50), and at least three provenance-checked opponent offers, and the exact
wire-coerced next counter discounted one round is strictly worse by more than
1e-12. It is pinned to Test 2's .50/.05/SPE1/.57/.39/60/99 numeric stack and
fails closed against every existing discount/no-regress/high-share/exact-floor
guard, OBSERVED_GAIN, economic stall, stonewall, and opponent exploitation.
It has no game hash, randomized arm, or cell assignment; P2 commitment dispatch
is untouched.

Evidence is deliberately limited. Across the clean Test 2 window
`[1787616328,1787656904)`, all 1,177 terminal bargaining outcomes were retained
(573 P1); the strict first-trigger subset was 8/8 retrospective wins, mean
+0.0328984 pot share, but is low-frequency and non-causal. One real example
rejected 45.20% at round 34, then sent 47.32%; `.95*.4732=.44954`, and the
eventual payoff was 230.73 versus 831.80 from immediate acceptance. Do not
generalize this into a broad early-accept policy: Agent 5's wider hindsight
miss set is not identified, and broad OBSERVED_GAIN already lost all three
arena seeds.

Focused tests passed 52/52; related bargaining interactions passed 296/296.
The full suite was 2,285 passed with exactly three pre-existing failures: the
stale bargaining horizon-floor assertion plus bargaining and negotiation live
grid drift alarms. Exact physical `hardliner` / effective `champion`
reachability at n=2,400 seed 2701 passed 1,653/1,653/1,653
eligible/fired/action-changed. Ordinary cloned-field draws close too early for
this rare late predicate, so the checker uses a documented reachability-only
hold-open opponent; eight actual historical Test 2 games separately prove live
state reach.

Safe fleet tooling added the candidate `=1` and explicit zeros for every
conflict while Test 2 was down. The resulting 79-entry treatment overlay hash
is `fcb6335f3a58015eaf614dd44277a2eee5664537d0561c832cb35d2edd5101e1`.
The supervisor launched replacement PID `6085` at 18:11:51 IST with policy
`champion`, all three families, LLM off, and pushed HEAD `12069ea`. Process
environment inspection confirms candidate=1, every conflict=0, both CDF
consumers=0, and all three families. T0 scores/counts were bargaining
2307.35/15,543, negotiation 2649.59/15,539, persuasion 2349.12/15,505. The
first authenticated postlaunch check showed nine active games and counts
15,545/15,541/15,505; bargaining was 2307.5. No candidate gate has fired yet,
which is expected at this frequency. Treat post-T0 comparison as observational
and roll back by setting the candidate to zero at a natural boundary if the
all-outcome P1 unknown-H/d=.95 target cell deteriorates after adequate exposure.

### 2026-08-25 19:29 IST: human scope correction; P1/broad comparator retired, correct Test 2 P2 ladder queued

The human source explicitly corrected the rule `current offer > .95 * next
counter`: it is intended only for Bob/P2 with a disclosed twelve-round horizon,
not P1 or an unknown horizon. Fleet tooling therefore set
`GLEE_BARG_P1_UNKNOWN_DISCOUNT_DOMINANCE_V1=0` on Test 2 and set the broader
`GLEE_BARG_DISCOUNT_NO_REGRESS=0` on Test 1, Agent 5, and Test 4. Test 2 and
Test 3 already had the broad flag at zero. Runtime overlays resolved all five
values to zero; no process was signalled and no game was abandoned by the
rollback. The P2 commitment dispatcher takes precedence in its owned cell, so
the broad flag had not contaminated Agent 5/Test 4's existing P2 ladder.

This was a real, contained Test 2 exposure rather than an inert mistake. The
P1 candidate appeared on 35 decision turns across three bargaining games,
became eligible once, fired once, and changed one Reject to Accept. In game
`7e5ee0a3-5df3-4bd2-aed1-ebb3e7ed8817`, P1 accepted 45.2% from gamma on round
42 in an unknown-horizon `.95` game; the agreement paid discounted P1 payoff
55,183.12 on a 1,000,000 pot. Gamma had offered the identical 45.2% since round
6, where acceptance would have paid 349,748.98. This proves that waiting was
nominal-payoff destructive in that game, but it does not identify the official
same-cell percentile/Elo counterfactual.

Do not silently replace the existing P2 acceptance floor with the newly worded
comparator. The implemented human P2 component already follows the source's
earlier explicit rule: accept when the current discounted payoff meets the
round-12 `(M-.01)*.95**11` floor. On a 100 pot its odd-round thresholds are
56.8743/63.0186/69.8267/77.3704/85.7289/94.9905, whereas `.95` times the next
silent-ladder counter is 57.95/64.60/70.30/77.90/86.45/94.9905. Adding the
new comparator as an OR is behaviorally dead; replacing/taking the max is a
strictly tighter policy and contradicts the earlier formula until the human
confirms that replacement. Keep the message-on component off: historical text
closure is materially weaker, while the silent component's complete live
sample retains 23 agreements and two no-deal zeros over 25 games.

At 19:28 IST, safe fleet tooling requested `stop hardliner`. Current Test 2 PID
`9695` had only started at 19:25:30 from workspace HEAD `0146c3f`, policy
`champion`, all three families, and LLM off, so it will continue normally until
its one-hour SDK boundary, drain all in-flight games, and stay down. Do not
signal or accelerate it. Once the supervisor records the old PID gone and a
zero-game clean drain, set only
`GLEE_BARG_P2_H12_D095_SILENT_V1=1`, retain
`GLEE_BARG_P2_H12_D095_MSG_COMMIT_V1=0`,
`GLEE_BARG_P2_H12_D100_COMMIT_V1=0`,
`GLEE_BARG_P1_UNKNOWN_DISCOUNT_DOMINANCE_V1=0`, and
`GLEE_BARG_DISCOUNT_NO_REGRESS=0`, then `fleet.py start hardliner`. Verify the
replacement PID, `--probe champion`, all three families, LLM off, loaded code,
and exact runtime values before calling the corrected Test 2 bargaining policy
live. Fresh exact Test 2 reachability for the silent component is 191 eligible,
191 fired, and 74 submitted actions changed over 1,200 games; focused P2 tests
pass 53/53.

### 2026-08-25 19:49 IST: Agent 5 overall-2505 peak lock armed

The operator directed that the next authenticated Agent 5 / physical
`composite` overall leaderboard snapshot at or above `2505.00` must latch a
bank-and-defend peak lock. The latest snapshot when armed was `2469.97`, so the
trigger has not fired. A 15-minute thread heartbeat now checks the authenticated
overall row and must trigger on the first fresh `>=2505.00` observation, record
the exact overall/family ratings and counts, PID, stack hash, and timestamp,
then request `fleet.py stop composite`. This is a safe-drain request only: never
signal, kill, crash, or abandon games. Because the current SDK process can stop
queueing only at its natural shift boundary, the eventual banked value may
differ from the trigger snapshot; report both.

Once latched, Agent 5 is no longer an experimental host. Keep its exact stack
unchanged and stopped except for activity-defense shifts. Use authenticated
total-count differences to maintain buffers of at least 15 games per family in
the trailing 24 hours and 115 per family in the trailing 48 hours. When any
buffer is reached, start exactly one normal all-three-family, LLM-off shift,
verify its PID and unchanged stack, and immediately queue a safe stop for its
next natural boundary so it cannot roll into a second shift. Record every
outcome and the pre/post ratings. Other agents continue improvement work. This
minimizes exposure but cannot freeze the rating exactly because GLEE applies
activity requirements and high-rating decay.

### 2026-08-25 23:01 IST: fleet-wide minute bank shipped; Agent 5 latch reconciled

The earlier 15-minute heartbeat was too slow for the requested peak lock. The
authenticated ten-minute history later proved that Agent 5 crossed the trigger
at 22:03 IST with overall `2506.72`; its family snapshot was bargaining
`2493.33/14890`, negotiation `2604.62/14849`, and persuasion `2418.72/14848`.
The next two overall observations were `2496.54` and `2490.75`, demonstrating
why an hourly process boundary could not bank the exact peak. The operator's
safe stop request left PID `23015` playing every in-flight game; the supervisor
recorded it down at 22:25:28 with no signal or abandonment. Latest authenticated
stopped state is overall `2490.75`, bargaining `2480.55/14916`, negotiation
`2619.14/14874`, and persuasion `2372.56/14878`.

Commits `457cc91` and `a530dd6` are pushed to `origin/main`. They add a distinct
`fleet.py bank SLOT` path for every physical slot. A code-loaded runner observes
the request in its normal roughly two-second poll, stops all queue top-ups,
uses the SDK's native drain for every already-matched game, and remains disabled.
Ordinary `stop` retains its natural-boundary semantics for one-shift activity
defence. A singleton `peak_watch.py` samples one authenticated overall board on
a monotonic 60-second cadence only while at least one unlatched threshold is
eligible. Each slot has an independent target; no strategy, randomizer, family
assignment, or gameplay flag was changed.

Safe tooling armed physical `composite` at `2505.00`, latched it, and verified
it BANKED/down with `drain_now`, `disabled`, and `bank_latched` all present.
The retained Agent 5 overlay SHA-256 is
`759831b1fffae74225d5a6acf1e88493ba6d0d9dfa22db4afbf66d21f3852a7a`.
Peak watcher PID `63596` is live. The manual reconciliation observation is in
control because the first minute watcher did not exist at the historical
22:03 crossing; the authenticated peak and exact family data above come from
the append-only rating history rather than being relabelled as a fresh trigger.
Conservative trailing activity deltas are approximately 24h
`B/N/P=2905/2872/2906` and 48h `5308/5279/5300`, far above the minimum buffers,
so no defence shift is due.

At this checkpoint champion replacement PID `62880` (22:50:39) has loaded the
cooperative bank code. Hardliner PID `58430`, conceder PID `59614`, and
randomized PID `60650` predate `457cc91`; do not force-cycle them. They gain the
same capability at their next clean SDK boundary. Agent 5 is already stopped
and will load it only when a future authorised defence shift starts. The old
supervisor predates watcher supervision, but `fleet.py peak` launched and
verified PID `63596`; a future safe supervisor replacement will adopt it.

Safety-focused tests pass 35/35. The immediately preceding full suite had
2,532 passes and exactly the same three documented pre-existing failures: the
stale bargaining horizon-floor assertion and the bargaining/negotiation live
grid drift alarms. Review found no remaining high-risk code issue. Exact rating
freeze remains impossible: an observation stops new matchmaking promptly, but
up to the slot's existing concurrency of already-matched games must settle.

**23:30 IST rollout completion.** The remaining pre-commit runners all exited
through their SDK boundaries and were never signalled. Verified live replacement
PIDs are champion `62880` (22:50:39), hardliner/Test 2 `63678` (23:01:36),
conceder/Test 3 `65015` (23:09:21), and randomized/Test 4 `70598` (23:29:56).
Every command retains all three families, concurrency 8, and LLM off; each start
postdates bank commit `457cc91`. Agent 5 remains down/BANKED, so it has no process
to replace until its next authorised defence shift. Watcher PID `63596` remained
live on exact 60-second ticks throughout the rollout. Fleet-wide minute-bank
capability is therefore live on every currently running slot and available on
the stopped Agent 5 code path at its next start.

### 2026-08-26 07:41 IST: post-outage cohorts finalized; host sleep remains the blocker

Agent 5 remains authenticated at overall `2490.75`, bargaining
`2480.55/14916`, negotiation `2619.14/14874`, and persuasion
`2372.56/14878`. It is down with `disabled`, `drain_now`, and `bank_latched`
still present, its locked overlay unchanged, and no observed decay. Conservative
activity lower bounds are B/N/P `1813/1780/1814` over 24 hours and
`4501/4473/4499` over 48 hours, so no defence shift is due.

Tests 1, 3, and 4 eventually completed clean zero-abandon drains at 07:38,
07:26, and 07:33 respectively and relaunched with current code, all three
families, LLM off, and deterministic overlays. Test 2 PID `77504` is also
current-code-loaded, but its preceding process was replaced only after an
authenticated zero-active stall and produced no natural finalized cohort.
Every randomizer, A/B, probe, and cell-assignment control remains off.

The three natural drains retained 984 outcomes: bargaining 324 agreements and
4 timeouts; negotiation 175 agreements, 94 no-deals, 52 walks, 5 timeouts, and
4 invalid-moves-exceeded; persuasion 305 completed and 21 timeouts. There were
245 exact-zero payoffs. The weakest adequately sampled completed cell was Test
4 bargaining P1, hidden information, unknown horizon, messaging off at fitted
percentile `.4012` (`n=10`, all agreements). Test 4 persuasion was the weakest
profile-family at `.4915` over 85 scoreable outcomes, with 18 additional
retained seller records lacking the value needed for a percentile. These are
not deployment evidence: all three cohorts span the synchronized transport
failure and the Test 4 cell is still small.

The operational confounder is now directly observed. macOS recorded 27
Maintenance Sleep/DarkWake cycles between 07:18 and 07:41 while on battery,
despite the live `caffeinate` assertion. The fleet was healthy at the last
check with 7--8 active games per challenger, but clamshell/battery sleep can
again reset connections and trigger synchronized timeout bans. Do not signal or
cycle the fleet. The falsifiable next check is one fully awake, AC-powered,
zero-timeout/zero-invalid natural shift; only then re-evaluate Test 4's hidden
unknown-horizon bargaining cell. If synchronized failures persist while the
host is continuously awake, investigate shared transport; if only one slot
fails, inspect that runner and its invalid-move wire before proposing strategy.

### 2026-08-27 00:41 IST: persuasion round-20 incentive audit (analysis only)

A human report that Tiberius passed a truthful HIGH/YES final round at `p=1/3`
is consistent with terminal cheap-talk discounting, but the missing `v/price`
ratio prevents calling it a mistake. In our clean truthful-history games,
Tiberius bought HIGH/YES on round 20 in `4/4` known `v=2P` cases, but `0/5` at
`v=1.2P`, `0/2` at `v=1.25P`, and `0/5` when value was unknown. It is
value-sensitive, not an unconditional terminal refuser.

The current seller has no special terminal override: HIGH is always YES; LOW is
YES only in prior-profitable/all-push or still-responsive unknown-value states.
Since equal-seller Tcfg `1787680787`, our `p=1/3` round-20 actions were 543/543
HIGH YES and 382/1,061 LOW YES, so 41.3% of all 925 YES messages were LOW. The
remaining 679 LOWs were NO. Among resolved actions, YES sold 390/837 while NO
sold 0/625; this is selected observational evidence, not the counterfactual
conversion rate. Opponent sellers said YES on 1,324/1,594 (83.1%) of our
`p=1/3` final buyer decisions, confirming that terminal recommendations are
heavily pooled.

Decision: reject an unconditional buyer round-20 PASS or BUY. Large-value
cells still profit from buying; low-value terminal positives are often dumps.
The appropriate buyer hypothesis is a value-aware terminal threshold, and it
must preserve truthful high-value histories. A separate seller hypothesis is
stronger: default-OFF `SELLER_TERMINAL_PUSH_V1`, changing only terminal LOW
control-NO to YES. It has no reputation continuation cost and current NOs never
sold, but efficacy remains prospective. This is not the measured-negative
broad backload arm: that arm withheld earlier sales in already prior-profitable
cells, whereas this proposed test changes only the final action where the
current complete control plan says NO. Do not stack it into an active Test 2
buyer cohort; if later authorized, isolate on Test 2, exact-replay first 20
firings, and judge all seller assignments under the existing 500/2,000 rules.

### 2026-08-27 01:00 IST: Test 2 terminal seller push implemented; deployment pending

The operator explicitly authorized the seller-only terminal hypothesis on Test
2. Codex implemented `GLEE_PERS_SELLER_TERMINAL_PUSH_V1` default OFF in
`glee_agent/strategies/persuasion.py`. The complete prior seller plan is now a
baseline function wrapped by a strict postcondition. Only seller/player 1,
persuasion, exact numeric round 20/20, private LOW, baseline-NO states may move
to YES. The plan retains its reason and every prior field; the only differences
are `recommend: false -> true`, marker `seller_terminal_push_v1`, and sole gate
`pers_seller_terminal_push_v1`. HIGH, earlier/non-20 rounds, existing YES,
buyers, malformed states, conflicting seller mechanisms, and nonfires are
byte-identical. The role key may be absent because the official persuasion
protocol structurally fixes P1 as seller; a contradictory key still fails
closed. This is deterministic and game-ID invariant.

Focused verification passed 52/52, the persuasion suite passed 663/663, and the
mandatory exact physical Test 2 `hardliner` / effective `champion` reachability
check passed 117 eligible, 117 fired, and 117 submitted NO-to-YES action changes
over 800 paired games, covering binary and text wire types. The full suite was
2742 passed with exactly the three known unrelated failures: the stale
bargaining horizon-floor expectation and bargaining/negotiation live-grid drift
alarms. `scripts/check_reachability.py` now recognizes the new gate with its
exact structural predicate. No live configuration, process, queue, `.env`,
`arms.json`, `control.json`, bargaining behavior, or Agent 5 state was changed.

Deployment objection: the current Test 2 tight-credibility-reset experiment
precommitted a frozen seller and was only 910/2,000 at its latest complete
checkpoint. Do not blend cohorts. Claude/deployment owner should review and
push the inert code, wait for a code-loaded SDK-native bank and lossless
zero-game drain, mark the reset-only cohort operator-superseded without an
efficacy verdict at its exact final count, retain its buyer flag as frozen
background, then set only
`GLEE_PERS_SELLER_TERMINAL_PUSH_V1=1` using `scripts/fleet.py`. Preserve Test
2's bargaining + persuasion / negotiation-disabled / LLM-off topology, every
other Test 2 key, Agent 5 and other slots, all A/B zeros, and control. First-20
exact replay, immediate explicit-zero rollback rules, and 500-seller harm /
2,000-seller final efficacy rules are frozen at the top of
`.ai/EXPERIMENTS.md`.
