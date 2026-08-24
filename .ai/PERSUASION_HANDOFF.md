# Persuasion workstream handoff

Last updated: 2026-08-25 01:44 IST. This file is the deployment boundary for
the persuasion-owned workstream. Negotiation and bargaining owners may read it;
they must not edit persuasion strategy or flags. Persuasion work does not alter
their code, configuration, experiments, or fleet flags.

## Live persuasion boundary

- All five slots use buyer-v2, tight-prior `.65`, honest rounds `99`, lie
  shading `0`, backload off, KEEP_MSG on, token message style, and LLM off.
- Test 2's invalid `GLEE_PERS_RANK_GATE_AB` arm was explicitly set to `0` with
  `scripts/fleet.py` at unix `1787570799` (2026-08-24 16:56:39 IST). Test 3 was
  not changed. The disarm is a mechanism rejection, not a causal effect result.
- Authenticated board at 21:29: account-best Test 2 is persuasion rank 5 at
  `2358.3`, `60.6` behind rank 3 expert, `136.7` behind rank 2 Tiberius, and
  `197.5` behind leader gill bates. Overall Test 2 is rank 5 at `2298.9`,
  `58.2` behind rank 3 Athena. This movement is not truth-arm evidence: the
  all-assigned readers still find no exact eligible game on any activated host.
  Holding Test 2's displayed bargaining `2519.5` and negotiation `2018.8`
  fixed, matching Athena's `2357.1` overall requires persuasion about `2533.0`,
  a `+174.7` gain from `2358.3`; reaching persuasion rank 3 alone is not enough
  for the overall podium.
- The prose arm remains live only on Test 1, Test 4, and Agent 5 from
  `T0=1787575521`. It is absent on Test 2 and Test 3.
- The binary truth arm is live on Test 2 from clean arms mtime `T0=1787582397`
  (2026-08-24 20:09:57 IST), on Agent 5 from `T0=1787584351` (20:42:31 IST),
  and on Test 4 from `T0=1787584425` (20:43:45 IST). Test 2 naturally drained
  PID 71871 and loaded pushed code `d79ca92` as PID 76676 at 20:08:48 IST;
  Agent 5 loaded PID 79006 at 20:42:18 and Test 4 loaded PID 79064 at 20:42:58
  before fleet tooling set only the truth flag at each clean boundary. Prose is
  absent on Test 2 and text-only on Agent 5/Test 4, so it cannot overlap this
  binary arm. Buyer-parser flags remain absent, rank gate/backload are zero, and
  Test 3 is untouched.
- The exact text explicit-decline buyer veto was implemented default OFF and is
  now live on research slots Test 1 from `T0=1787588203`, Agent 5 from
  `T0=1787588220`, and Test 4 from `T0=1787588236`. Before any veto activation
  or outcome, its sequential
  Test-2-after-truth boundary was prospectively amended to a parallel,
  behaviorally disjoint research window on Test 1, Agent 5, and Test 4 only.
  Test 2 and Test 3 remain unarmed. The hypothesis and every sample, harm,
  success, stop, all-outcome, and subgroup rule remain unchanged; full details
  were frozen in `.ai/EXPERIMENTS.md` before activation. Fleet tooling changed
  only this persuasion flag, no target game was in flight at each boundary,
  and no process was restarted or signalled. Immediate host-specific readers
  found zero assignments and no live veto trace, so changed-action verification
  remains pending the first candidate explicit decline.
- Before any binary-truth assignment or outcome existed, the research boundary
  was prospectively expanded to Agent 5 and Test 4. Exact-stack preflight on
  both reported `eligible=32/fired=18/action_changed=18` over 800 games. At the
  21:30 read, host-specific all-assigned readers reported zero exact eligible
  games since each clean T0, so the live mechanism is not yet behavior-verified
  and no rating movement may be attributed to it. Test 3 remains protected.

## 20:47 fleet-restart incident — not persuasion behavior

At 20:47:08 IST (`1787584628`) the supervisor and all five agent processes were
restarted together; the live process table shows the common start second. The
authenticated persuasion dashboard records 14 games timing out at 20:47 while
in progress: Test 2 had six (`5 * -7.9`, `1 * -8.0`, total `-47.5`), Agent 5
had three (`-7.8`, `-7.9`, `-7.8`, total `-23.5`), and Test 4 had five
(`-7.6`, `4 * -7.7`, total `-38.4`). Total official persuasion loss was
`-109.4`. A Test 2 transcript confirms the seller successfully played 15 rounds
and earned `15P` before timing out on round 16; the official delta was still
`-7.9`. This is an operational deployment failure, not evidence about the
persuasion policy.

The restart occurred after the declared truth-host T0s, but host-specific truth
readers report zero exact assignments through the incident and the prose reader
reports no new exact assignments. Therefore none of the 14 timeouts enters
either arm comparison, the original cohorts remain intact, and `1787584628` is
recorded as a mandatory activation-era split. Future fleet deployments must use
natural per-slot drains; a simultaneous supervisor restart destroys live games
and can erase roughly eight rating points per affected game.

The restart also triggered the competition's crash-loop protection on every
slot. Each new agent process received HTTP 403 because its last three games had
timed out on its turn; queue joins were suspended until the server-provided
per-slot deadlines between 21:17:02 and 21:17:08 IST. No experiment exposure
could accrue during `[1787584628, 1787586428)`. The processes retried in place
without another restart. Fresh error-free turns appeared on champion and
randomized at `1787586470.929` and `1787586471.399`, and on hardliner,
conceder, and composite by `1787586508.658`; subsequent traffic reached at
least 24--42 new games per slot. This verifies natural queue recovery on all
five slots. Do not restart again: the delay was server-enforced recovery, not
passive experiment waiting.

## Binary-truth live-reach audit

The absence of a live truth assignment is not currently a gate failure. Through
21:30 there were 381 all-family first-turn starts since the host-specific T0s:
291 on Test 2, 43 on Agent 5, and 47 on Test 4. They yielded 127 persuasion
games and 25 binary-seller first exposures, but no exact target.
Outcome-independent live arrival evidence over the prior 6h was 18 exact
targets / 5,976 starts (`0.301%`), closely matching the configuration-grid rate
`0.278%`; zero targets in 381 starts therefore still has probability about
`31.7%`.

Production, reader, and reachability predicates were independently replayed and
match on seller/player 1, binary mode, known CV, p=.8, v/P=1.25, u=0, 20 rounds,
and the stable salt. The checker and reader counts must not be compared raw:
checker `eligible` counts target low-quality turns, while the reader cohorts
target games at the first recommendation. Escalate a reach failure only if
there are still zero targets after 1,077 activated all-family starts (below 5%
under live support), or below 1% after 1,656. Once exact games arrive, zero
candidate-low traces after five exact assignments is separately suspicious and
requires a wire audit. Until either threshold, change no code or reader.

## Rejected rank-gate mechanism

The rank gate did not implement its stated scope. It reached p=.8 cells, flipped
both buy-to-pass and pass-to-buy, used a local CDF that pooled six official
configurations, and applied a recommendation-only threshold to explicit seller
declines. Across 267 treatment games it changed 828 turns; 539 were unintended
p=.8 buy-to-pass changes. A verified threshold-zero case bought a low unit after
an explicit “I do not recommend this one” message and lost 1,000,000. No result
conditioned on changed turns, purchases, or the 83/495 locally recovered finals
is admissible. The remaining 412 unresolved outcomes also block any ITT read.

## Next safe causal experiment

`GLEE_PERS_P08_R125_PROSE_AB` is implemented default OFF. It targets only
persuasion seller/text/p=.8/seller-knows-CV/v=1.25P/20-round games. A stable
per-game SHA-256 bit leaves control messages byte-identical `yes`; treatment
uses the current six quality-neutral prose combinations. Recommendation choices,
negative messages, seller-blind cells, binary mode, buyers, bargaining, and
negotiation are unchanged.

Preflight after all three hosts loaded commit `2f4989d` used 800 seeded
persuasion games per exact live stack. Test 1 reported
`eligible=320/fired=160/action_changed=160`; Test 4 reported `220/100/100`;
Agent 5 reported `160/60/60`. Focused implementation and reader tests pass. The
full allowed suite finished with 1,061 passes and only the two pre-existing
bargaining failures.

Deployment boundary: only Test 1 (`champion`), Agent 5 (`composite`), and Test 4
(`randomized`) are research hosts. They naturally loaded commit `2f4989d` as
PIDs 68351, 68203, and 67641 respectively, with no restart or signal. Fleet
tooling then set `GLEE_PERS_P08_R125_PROSE_AB=1` and the explicit inert
`GLEE_PERS_TOKEN_MAX_P=0` on those three only. Clean common T0 is arms mtime
`1787575521` (2026-08-24 18:15:21 IST). Test 2 and Test 3 remain unarmed.

## Official transcript diagnosis at activation

The authenticated dashboard's latest 20 Test 2 persuasion games were read in
full, including every positive, negative, zero, refusal, and all-round outcome.
Buyer games contributed -13.3 official rating over 8 games (mean -1.66; 6/8
negative), while seller games contributed +7.2 over 12 (mean +0.60; 5/12
negative). This is a diagnostic window, not a treatment result.

Two mechanisms were directly visible. In the exact prose-arm cell (seller,
text, p=.8, known CV, v=1.25P, 20 rounds), the buyer bought four literal `yes`
messages, observed one low product, then passed the remaining 16 `yes` messages;
our +4P payoff still lost 5.2 official rating. Dashboard transcript setup does
not show text versus binary mode, so this classification is joined to local game
`e03c909a-2fb4-4922-bd59-9b609c042e42`; an adjacent -6.2 binary game is not in
the arm's target cohort. Separately, the legacy buyer
parser bought three seller messages saying `Not recommended.`; all three were
low, the game ended at zero, and it lost 4.0 official rating. The latter agrees
with the existing default-off `GLEE_PERS_PARSE_V2` evidence (historically 373
such purchases, 373 low, 0 high), but it is not co-armed here: any buyer-parser
trial needs its own stable per-game randomisation and official precommit.

Decision boundary: first official read at 120 resolved dashboard rating deltas
per arm, using every assigned game. Unresolved, invalid, official-join, wire, or
self-play contamination blocks promotion. Full rules and subgroups are
precommitted in `.ai/EXPERIMENTS.md`. The local percentile reader is diagnostic
only; official per-game dashboard deltas control promotion/rejection.

## First live mechanism observations

Candidate game `202cb810-c1a7-4d36-b98b-7d394842d258` on Test 1 is the first
post-T0 target draw. Its hash was candidate on all 20 rounds; all 20 plan records
carried `p08_r125_prose`, recommendation stayed `true`, and the wire contained
only five members of the approved six-message bank. The game completed normally
with 4/20 purchases (3 high, 1 low), seller payoff `4P`, no invalid/timeout, and
official dashboard rating delta `-4.3`. The buyer passed all 16 rounds after the
first bought low. This is a clean but adverse first treatment observation, not a
decision; the precommitted sample and stop rules remain unchanged.

Candidate game `36053a1f-16a3-4fb3-94cb-2d580cc1764d` on Agent 5 is the
second post-T0 target draw and was played against named opponent `expert`. The
stable candidate hash and approved prose held for all 20 rounds. The buyer
purchased 13/20 (7 high, 6 low), producing seller payoff `13P` and buyer payoff
`-4.25P`; the authenticated official delta was `-1.4`. The two candidate games
therefore have mean official delta `-2.85` and mean purchase rate `42.5%`, with
no zeros or wire failures. There are still no official controls and n=2 is far
below every decision boundary, so this is monitoring evidence only.

Candidate game `6dc339a2-502a-437e-88ff-7747939cabcc` on Test 1 is the third
authenticated treatment outcome. It emitted approved prose on all 20 rounds,
sold 8/20 (all eight bought units were high), earned seller payoff `8P`, and
received official delta `-2.8`. The first completed control,
`3b47502f-2f42-478d-8215-d7ac21258bce` against named opponent `king`, emitted
literal `yes` on all 20 rounds, sold 19/20, earned `19P`, and received `+4.6`
official. Pooled candidate-only official mean is now `-2.8333` (n=3) versus
control `+4.6` (n=1), an unpowered raw difference of `-7.4333`; the 95% CI is
undefined because control n<2. The precommitted harm look is at 50 official
games per arm, so opponent/quality-draw variance in this first control cannot
support disarm. Mechanism failures, unresolved outcomes, and missing official
deltas are all zero in the four authenticated records.

Both server-completed games were initially absent from at least one local final
stream. Their complete authenticated 20-round transcripts, exact setup,
terminal payoffs, and manual join audit are frozen in
`.ai/PERSUASION_OFFICIAL.json`. The persuasion-only reader now accepts such a
recovery only when all 20 messages, qualities, buyer decisions, exact setup,
and the seller-payoff identity validate. A rating row alone remains unresolved.
The new recovery tests pass, and the full allowed suite after this reader change
has 1,204 passes with only the same two pre-existing bargaining failures.

## Expanded official failure diagnosis and next isolated arm

The authenticated dashboard was joined to the current Test 2 wire log for 37
deduplicated completed persuasion games from roughly 18:30-18:45 IST. This is
an all-outcome descriptive window, not an A/B result. The largest observed
cells were seller/binary/p=.8/known-CV/v=1.25P (`-7.6`, n=1),
buyer/p=.8/v=1.25P (`-6.9`, n=1), seller/p=.8/unknown-CV (mean `-3.70`, n=2),
buyer/p=.8/v=1.20P (mean `-2.50`, n=3), and seller/p=.33/unknown-CV (mean
`-1.12`, n=6; 4/6 negative). Small cell counts prohibit promotion, but they
localize the repeated mechanisms.

In exact seller game `6516c6b7-2a47-4919-b192-cd0484e21daa`, the current
all-yes policy sold round 1 high and round 2 low; the buyer then passed every
remaining round, including 14 highs, and the official delta was `-7.6`. Across
170 deduplicated completed comparable all-yes games, mean purchases were only
7.29 despite 16.04 high items, 35/170 sold nothing, and 42 buyers stopped
completely after a bought low. By contrast, opponents that beat us as sellers
often emit explicit negatives on bad items and make positive messages strongly
predictive; opponents that beat us as buyers stop or sharply tighten after the
first caught lie. The current stack sometimes does neither: it can recommend
every low at the p*v==price knife edge, and the legacy parser has bought literal
`Not recommended.` messages (373 historical purchases, all 373 low).

`GLEE_PERS_P08_R125_BINARY_TRUTH_AB` was implemented default OFF in pushed
commit `8372236` and is now live only on Test 2 from `T0=1787582397`. Test 2
naturally drained the pre-code PID 71871 and relaunched on pushed code
`d79ca92` as PID 76676 at 20:08:48 IST; fleet tooling activated the single
persuasion flag at 20:09:57 IST without a restart or signal. It targets
only the binary counterpart of the prose cell: seller, p=.8, visible v/u,
v=1.25P, u=0, 20 rounds. Hash controls are full-object identical; candidates
say `yes` on high and `no` on low. The post-load Test 2 exact-stack reachability
rerun over 800 seeded games reported `eligible=29/fired=14/action_changed=14`;
54 focused persuasion experiment tests passed. The latest full allowed suite
passed 1,230 tests with only the same two pre-existing bargaining failures. It
is Test 2 only with prose absent and rank-gate/backload explicit zero; Test 3
remains untouched. A real emitted low-quality candidate `no` is still required
before the live mechanism is considered behavior-verified.
The fixed read is 40 official outcomes per arm with a 20/arm harm look and at
least 8/arm at each price scale. Full precommit is in `.ai/EXPERIMENTS.md`.

The follow-on `GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB` was pushed default OFF.
Its original seller-knowledge gate was rejected at preflight because that
official configuration is hidden from the buyer during play and yielded an
unreachable production policy. The corrected observable union gate covers both
seller-knowledge configurations and stratifies only when authenticated terminal
evidence exposes the label; it never infers the label from purchases or outcomes.
Focused persuasion tests passed, and exact Test 2 reachability over 800 seeded
games reported `eligible=180/fired=15/action_changed=15`. That original
sequential deployment sentence was superseded prospectively before any veto
activation or outcome. The arm is now live only on Test 1, Agent 5, and Test 4
at their recorded T0s; Test 2 and Test 3 remain unarmed. Exact live-stack
reachability independently passed twice on every host (`340/25/25` and
`380/30/30` eligible/fired/action_changed). Focused tests passed 20; the full
allowed suite passed 1,291 with only the two known bargaining failures. The
fixed 50/arm harm and 120/arm final rules are unchanged.

The next broader persuasion design target is buyer `p=.5`, `v=1.2P`, `u=0`,
20 rounds. Since rank-gate disarm, 68 structurally exact seller-known games
ended at zero and our buyer passed all 900 rounds in the 45 directly audited
binary/text games; opponent buyers facing our selective sellers bought 114
high and zero low units across the corresponding 37-game mirror. This is
all-assigned descriptive mechanism evidence, not a causal estimate. A proposed
one-directional tight-prior unlock is recorded in `.ai/EXPERIMENTS.md` but is
not implemented or live.

## 23:41 buyer p=1/3, v=4P bait-pattern response — built inert

The Test 3 buyer transcript `7896ee73-7dc1-4517-8922-15e2f8d713d2` exposed a
specific model miss. Three early binary `no`s sharply reduced buyer-v2's
stationary-spammer posterior; the seller then emitted only `yes`, including 12
bought lows, but the posterior still placed round-20 `P(high|yes)=.401` above
the cell's `.25` money break-even. Control bought through a `+6P` peak, reached
zero after round 19, bought the final low, and finished `-1P`. This was baseline
buyer-v2 on protected Test 3; no persuasion experiment fired.

The proposed response is now implemented but default OFF as
`GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB`. It targets only buyer/player 2,
binary, `p=1/3`, `v=4P`, `u=0`, 20 rounds, across all scales and both hidden
seller-knowledge configurations. After the first strict `no`, it counts only
bought strict-`yes` outcomes. At `L>=3` and `3H-L<=0`, a hash-candidate changes
one current baseline buy to pass, resumes, and cannot pulse again until a newly
bought `yes` reveals low. It is a circuit breaker, not an absorbing stop; the
absorbing alternative was rejected because its all-assigned shadow replay could
double zeros and produced up to `-8P` fixed-stream harm.

The frozen motivating sequence would pulse rounds 9, 11, 13, 16, 18, and 20
and finish `+1P` rather than `-1P`. That is not causal evidence. Across 58
all-assigned exact historical games, the pulse was reachable in seven and
changed 27 frozen turns; diagnostic payoff moved `-0.0556P` while local
percentile moved `+0.00382`, with both intervals crossing zero. The sign
conflict is the reason for stable per-game randomization and research-only
deployment.

Implementation and independent reader files are:

- `glee_agent/strategies/persuasion.py`
- `scripts/check_reachability.py`
- `scripts/read_pers_p033_r4_binary_postdecline_pulse.py`
- `tests/test_pers_p033_r4_binary_postdecline_pulse.py`
- `tests/test_read_pers_p033_r4_binary_postdecline_pulse.py`

Focused implementation/reader tests pass 125. The first checker read incorrectly
reported reach on randomized because its replay hard-coded the composite probe.
The corrected probe-aware replay shows randomized/Test 4's custom policy bypasses
`persuasion.py` and correctly fails at `fired=0/action_changed=0`; it must not be
armed. Corrected exact-stack reachability passes on champion and composite at
`eligible=7/fired=3/action_changed=3` over 800 games each. The complete suite
passes 1,615 tests with only the two documented
pre-existing bargaining failures. The inert strategy commit is pushed. Natural
code load, immutable stack snapshots, and clean host-specific activation are
recorded in the live sections below. Test 2, Test 3, and Test 4 remain unarmed;
no bargaining or negotiation behavior, configuration, or flag was changed by
this workstream.

The final reader audit also fails closed unless `frozen_at <= HOST_T0`, every
terminal transcript round has one contiguous logged buyer turn with an exact
OFF/ON action-and-plan replay, every resolved official row has all payoff/tail
fields, and every would-pulse count corresponds to a control buy that would
actually change. Any exact candidate trace on Test 2, Test 3, or Test 4 is now
an unauthorized-host mechanism rejection.

The complete prospective hypothesis, all-assigned cohort, harm/final sample,
subgroups, failure rules, official promotion boundary, and expected ~180-hour
two-research-host duration are frozen in `.ai/EXPERIMENTS.md`. Deployment may
use only champion/Test 1 and composite/Agent 5, each with an immutable pre-arm
stack snapshot, separate clean T0, and no restart or signal. Read each host
separately; later-host pre-activation games must never enter an earlier boundary.

## 00:50–01:06 buyer pulse deployment — live research-only

Champion naturally relaunched on the pushed code as PID 11357 at 00:50:52 IST;
composite naturally relaunched as PID 11293 at 00:50:02. Neither process was
restarted or signalled. The final exact live-stack preflight, after those loads,
reported `eligible=12/fired=7/action_changed=7` over 800 paired persuasion games
on each host. The only exact target buyer games visible immediately before the
boundary had already emitted their round-20 decisions, so no target game could
receive a mid-game treatment.

The full pre-arm stacks were frozen at `1787599546.549658` in
`.ai/PERS_P033_R4_BINARY_POSTDECLINE_PULSE_T0_STACKS.json` and committed as
`35ff05e`; the captured `arms.json` mtime was unchanged through the snapshot.
Fleet tooling then armed only `GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB` on
champion at `T0=1787599611.224363327` and composite at
`T0=1787599624.328448057`. Runtime-overlay verification shows `1` on those two
hosts and the flag absent on hardliner/Test 2, conceder/Test 3, and
randomized/Test 4. No bargaining or negotiation setting was changed by this
deployment.

The first separate host-specific reader runs through approximately
`1787600226` found zero post-T0 structural assignments on both hosts. That is a
clean all-assigned baseline, not behavior verification: live `eligible>0`,
`fired>0`, and `action_changed>0` still require the first exact assignments and
traces. Continue the frozen first-20-round audit; any unauthorized host fire or
mechanism mismatch requires immediate research-host disarm.

## 01:09 external reset and 01:25 clean re-arm

An external fleet write at `T1=1787600396.5521495` explicitly set every
persuasion experiment flag to `0` on all five hosts. This ended the original
pulse eras at that exact boundary: champion
`[1787599611.224363327, 1787600396.5521495)` and composite
`[1787599624.328448057, 1787600396.5521495)`. It was not a persuasion decision
and did not restart or signal a process. The stopped prose, binary-truth, and
text-decline-veto arms were not silently folded into the pulse control.

The only exact assignment found in the original live window was composite
candidate `86d71fde-0bcc-4d7d-80f3-470b3bb3cdcc`, beginning at
`1787600113.949715`. All 20 buyer turns are present. The seller's strict binary
stream produced four bought highs and one bought low, so the frozen pulse
predicate never became true; there were zero pulse traces and zero changed
actions. The game remains in the all-assigned ITT cohort. Its absence of a
trace verifies only that this nontriggering candidate stayed control-identical,
not that the live pulse wire has fired.

Snapshot `ae7b913` captured the first post-reset stacks, but a concurrent
negotiation-owned fleet restore changed those stacks before activation. The
hash interlock refused deployment; that snapshot is an aborted boundary and
must never be used for a causal replay. After the external restore settled, the
complete current champion/composite stacks were refrozen before treatment at
`1787601285.818645` in
`.ai/PERS_P033_R4_BINARY_POSTDECLINE_PULSE_T2_STACKS.json`, commit `16161f6`.
The exact current-stack checker again returned
`eligible=12/fired=7/action_changed=7` over 800 paired games on each host, and
no exact target game was in flight.

Fleet tooling then re-armed only the pulse flag on champion at
`T0=1787601319.884793282` and composite at
`T0=1787601338.633884907`. Runtime overlay inspection shows `1` only on those
two research hosts and explicit `0` on hardliner/Test 2, conceder/Test 3, and
randomized/Test 4. The live PIDs stayed champion `11357` and composite `11293`;
no process was restarted or signalled. Immediate post-T0 scans found zero new
exact assignments, so emitted treatment behavior is still awaiting its first
would-change candidate.

Readers must keep the original and re-arm eras separate. Use the original
snapshot and original host boundary only through external `T1`; use the T2
snapshot with each new host T0 for current evidence. Never replay a host with a
snapshot frozen after that host's boundary or combine later-host pre-activation
games into the earlier host.

## 01:35 operator supersession — deterministic full-stack portfolio

The operator superseded all live experiments with a deterministic portfolio:
all five slots queue all three families, LLM is off, and every cell/A/B flag is
explicitly zero. The pulse overlay was set to `0` in the fleet write at
`1787601931.688070774` and the all-zero state was verified by
`T2=1787601952`. This ends the brief re-arm eras. The pulse is **stopped**, not
promoted or effect-rejected, and must not be automatically re-armed.

The brief champion era contains one additional all-assigned candidate,
`c0e26e93-685b-4a86-8fe8-54f6d7e57c17`, beginning at
`1787601553.841179`. All 20 local buyer turns are contiguous; the pulse never
became reachable, emitted no trace, and changed no action. Its terminal/official
record is still unresolved, so it remains in ITT and independently blocks any
effect decision. Composite had no exact assignment in its brief re-arm era.

The pending natural launch map is Test 1=`champion`, Agent 5=`composite`, Test
2=`hardliner`, Test 3=`conceder`, and the historically named Test 4
`randomized` slot=`composite`. Every slot keeps the full
`bargaining,negotiation,persuasion` queue. At the time of this record, the old
PIDs were still running `champion` on all five slots; no cycle was forced.
Record each replacement PID/profile only after its natural drain and launch.

For persuasion specifically, the five current overlays are byte-identical:
buyer-v2 `1`, tight prior `.65`, lie shading `0`, honest rounds `99`, KEEP_MSG
`1`, token style, backload/token-max/rank-gate `0`, and every persuasion A/B
flag `0`. Runtime lie/honest overlays override the nominal hardliner/champion
profile transforms, and the buyer path does not read probe configuration.
Therefore all pending profile labels currently collapse to one deterministic
persuasion policy. The portfolio is diverse overall, but it does not create a
persuasion comparison or causal experiment. Do not infer persuasion differences
from profile labels; verify emitted plans and official all-outcome evidence.
