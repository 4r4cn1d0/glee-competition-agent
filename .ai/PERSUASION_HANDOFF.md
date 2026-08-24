# Persuasion workstream handoff

Last updated: 2026-08-24 21:08 IST. This file is the deployment boundary for
the persuasion-owned workstream. Negotiation and bargaining owners may read it;
they must not edit persuasion strategy or flags. Persuasion work does not alter
their code, configuration, experiments, or fleet flags.

## Live persuasion boundary

- All five slots use buyer-v2, tight-prior `.65`, honest rounds `99`, lie
  shading `0`, backload off, KEEP_MSG on, token message style, and LLM off.
- Test 2's invalid `GLEE_PERS_RANK_GATE_AB` arm was explicitly set to `0` with
  `scripts/fleet.py` at unix `1787570799` (2026-08-24 16:56:39 IST). Test 3 was
  not changed. The disarm is a mechanism rejection, not a causal effect result.
- Official board after the 20:47 fleet restart incident: account-best Test 2 is
  persuasion rank 5 at `2333.6`, `102.4` behind rank 3 expert, `144.6` behind
  rank 2 Tiberius, and `222.2` behind leader gill bates. Overall Test 2 is rank
  5 at `2305.4`, `50.0` behind rank 3 Athena. This movement is not truth-arm
  evidence: the all-assigned readers still find no eligible games on any
  activated host.
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
- The exact text explicit-decline buyer veto is implemented default OFF and is
  not live on any slot. It must not be armed until the binary-truth experiment
  is decided and disarmed.
- Before any binary-truth assignment or outcome existed, the research boundary
  was prospectively expanded to Agent 5 and Test 4. Exact-stack preflight on
  both reported `eligible=32/fired=18/action_changed=18` over 800 games. At the
  20:50 read, host-specific all-assigned readers reported zero exact eligible
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
timed out on its turn; queue joins are suspended until the server-provided
per-slot deadlines between 21:17:02 and 21:17:08 IST. The processes remain up
and retry in place every 60 seconds. Consequently there are no post-restart
game starts on any slot and no experiment exposure can accrue during
`[1787584628, approximately 1787586428)`. Do not restart again: waiting for this
specific deadline is server-enforced recovery, not passive experiment waiting.

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

The follow-on `GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB` is pushed default OFF.
Its original seller-knowledge gate was rejected at preflight because that
official configuration is hidden from the buyer during play and yielded an
unreachable production policy. The corrected observable union gate covers both
seller-knowledge configurations and stratifies only when authenticated terminal
evidence exposes the label; it never infers the label from purchases or outcomes.
Focused persuasion tests passed, and exact Test 2 reachability over 800 seeded
games reported `eligible=180/fired=15/action_changed=15`. It remains inert until
the binary-truth arm concludes and is explicitly disarmed.
