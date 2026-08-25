# Persuasion workstream handoff

Last updated: 2026-08-25 21:15 IST. This file is the deployment boundary for
the persuasion-owned workstream. Negotiation and bargaining owners may read it;
they must not edit persuasion strategy or flags. Persuasion work does not alter
their code, configuration, experiments, or fleet flags.

## 21:15 Test 4 strict-edge audit — mechanism clean, effect decision blocked

- The complete post-`Tcfg=1787656144.0263646` Test 4 cohort through
  `1787672720.3951201` contains 576 persuasion assignments: 286 seller and 290
  buyer. Five hundred seventy-three are terminal and three buyer games remain
  active at rounds 13, 3, and 2. There were no timeouts, strategy errors,
  abandoned games, or immediate terminals. The one carry-in game is retained.
- Exact replay covered all `11,477/11,477` turns. The 10,652 nonfires were
  byte-identical to control; all 825 changes had one legal strict-edge gate and
  no V1, legacy A/B, component, or multi-gate overlap. Truth is
  `278/278/278` eligible/fired/changed in 30 games; positive prose is
  `559/535/535` in 29 games, with 24 correct truth preemptions; buyer V2 is
  `12/12/12` in two games. Truth/prose have passed first-20 audit coverage;
  buyer V2 remains short at 12/20.
- Authenticated aggregate display movement is concerning but not causal:
  Test 4 moved from `2376.94/8,502` at the first post-boundary snapshot to
  `2302.40/9,072`, or -74.54 over 570 count advances, while the four unchanged
  slots averaged -16.10. Known roughly +/-125 identical-agent noise, differing
  game mix, zero authenticated per-game rating joins, and three unresolved
  games block a promotion or rejection. The account-best Agent 5 remains rank
  4 at 2424.25, 52.32 below third. Preserve the challenger pending valid joins;
  do not promote it to Agent 5 and do not infer harm from selected fires or raw
  payoff.

## 20:46 Test 2 replacement loaded — activation still waiting for zero persuasion games

- The concurrent bargaining owner completed the clean drain of PID `9695`,
  finalized its owned non-persuasion overlay, and re-enabled Test 2. The
  supervisor naturally launched replacement PID `15302` at 20:45:08 IST from
  pushed HEAD `a49f1bd`, which contains `cef2621`. The command is correct:
  `--probe champion`, LLM off, all three families, and a 3,600-second maximum
  shift. Persuasion did not start, stop, signal, restart, or configure it.
- This was not a safe persuasion Tcfg: within its first minute PID `15302`
  resumed at least six already-active persuasion games at rounds 9, 6, 4, 14,
  1, and later. V2/V3 therefore remain absent/off. V1 remains `1`, every
  persuasion `*_AB` key remains zero, and Agent 5 is unchanged.
- The 20:45 post-bargaining Test 2 non-persuasion overlay hash is
  `04ab6b129a47c5c2efb3a0504cf92114aa0afd3953721735319fd72752a10eb7`.
  This is a load checkpoint only. At the eventual persuasion Tcfg, refreeze the
  exact then-current stack and require that hash, `control.json`, and every
  other slot to remain byte-identical across the V2/V3-only fleet write. A safe
  opportunity is the natural post-max drain after PID `15302` stops acquiring
  games and every persuasion game it touched has a terminal record; never
  force or accelerate that boundary.

## 19:38 Test 2 wait checkpoint — concurrent bargaining drain owns the boundary

- Test 2 naturally launched PID `9695` at 19:25:30 IST from pushed HEAD
  `0146c3f`, which contains persuasion code commit `cef2621`. Its command is the
  required complete-agent command: `--probe champion`, LLM off, all three
  families, and a 3,600-second maximum shift. V1 is live; V2 and V3 remain
  absent/off, and every persuasion `*_AB` value remains zero.
- A separate bargaining owner used fleet tooling to disable Test 2 at 19:28 and
  now owns its natural drain and replacement launch. PID `9695` is still
  running normally with in-flight games; persuasion did not stop, signal,
  restart, start, or mutate it. Do not arm V2/V3 during this drain and do not
  override `control.json`.
- The then-current Test 2 non-persuasion overlay hash is
  `ff68acfa5609d37aec1ad3ad6efab687a851b2da3a9b73c094d72c6b8704a178`,
  legitimately superseding earlier hashes through concurrent owned changes.
  This is only a wait checkpoint: at the eventual persuasion Tcfg, freeze the
  exact current non-persuasion stack again and require it to stay byte-identical
  across the V2/V3-only fleet write. Agent 5 and all other slots remain outside
  the authorized persuasion change.

## 18:50 Test 2 wait checkpoint — external non-persuasion stack advanced

- Test 2 remains PID `6085`, launched at 18:11:51 IST, so it still predates the
  final V3 code and V2/V3 remain absent/off. HEAD and origin are both
  `115e02e`, which contains code commit `cef2621`. Do not activate on this PID.
- A separate owner added the already-pushed Test-2 bargaining overlay
  `GLEE_BARG_P1_UNKNOWN_DISCOUNT_DOMINANCE_V1=1` plus explicit safety zeros
  after the persuasion preflight. Persuasion did not make or revert that
  change. The old non-persuasion hash `a1d1cfc...` is therefore superseded; the
  current canonical non-persuasion overlay hash is
  `2b7fd4338b4208994b70e7cf0ceea072e3ab8dc15c08780a8f2971d596824262`.
  At the future persuasion T0, freeze whatever non-persuasion stack is then
  current and require its hash to remain byte-identical across the V2/V3 fleet
  write. Never restore the old hash or change those external keys.
- Process command, all-family queue, LLM-off state, fleet-wide persuasion A/B
  zeros, and Agent 5 persuasion stack remain valid. No persuasion flag, live
  process, bargaining setting, or negotiation setting changed in this check.

## 18:29 Test 2 V1+V2+V3 challenger — code pushed, activation waiting

- Commit `cef2621` is pushed and adds default-OFF deterministic
  `GLEE_PERS_BUYER_EXPLICIT_DECLINE_V3`, its reachability registration, and
  dedicated invariants. It is a final buyer-action semantic tail: buyer-v2,
  player 2, text only, control BUY only, and BUY-to-PASS only. It has no game-ID
  hash, random arm, cell targeting, history/posterior mutation, seller change,
  or non-persuasion path.
- Frozen all-assigned evidence is 49,802 buyer/text turns / 2,498 games. On the
  exact Test 2 stack, V2 adds 62 changed turns / 25 games (61 LOW, zero HIGH,
  one unresolved quality); V3 above V1+V2 adds exact
  `eligible=fired=action_changed=66/66/66` / 39 games, all 66 LOW and zero HIGH.
  Combined V2+V3 versus V1-only is 128 changes / 62 games: 127 LOW, zero HIGH,
  one unresolved. V3 had zero V1/V2 overlap, 66/66 exact sole-gate plan diffs,
  and no semantic positive false positive in the frozen corpus. This remains
  action-selected mechanism evidence, not causal official-rating proof.
- Verification: focused `164 passed`; exact Test 2 V2 and incremental V3
  reachability each pass `1142/1142/1142`; full suite is `2354 passed, 3 failed`
  with only the declared bargaining assertion and bargaining/negotiation grid
  drift alarms. No replay_eval, arena, or redteam command was run.
- User-authorized deployment boundary is physical slot `hardliner` / Test 2
  only, with V1=1, V2=1, V3=1 and every persuasion `*_AB` key zero. Agent 5 is
  protected and must remain byte-identical; Test 1, Test 3, and Test 4 also get
  no flag change. Do not copy Test 4's unproved seller truth/prose switches.
- Test 2 PID `6085` launched at 18:11:51 IST before the final code commit and
  cannot safely load the final V3 implementation. V2/V3 remain unarmed. Wait for
  a later natural launch on `cef2621`; never restart, signal, stop, drain, or
  force-cycle it. Freeze the exact pre-arm overlay and authenticated
  rating/game-count at that future T0, then use fleet tooling to set only V2=1
  and V3=1. The prospective sample, harm/final rules, full-cohort inclusion, and
  first-20 exact replay contract are frozen in `.ai/EXPERIMENTS.md`.

## 17:00 Test 4 strict-edge challenger — first live firings verified

- The main deployment owner authorized and deployed commit `67b684b` on Test 4
  only. PID `92980` launched cleanly at 16:38:53 IST with deterministic
  `hardliner`, LLM off, and all three families. Its immutable persuasion
  boundary is `Tcfg=1787656144.0263646` (16:39:04 IST), with the first
  post-overlay action at `1787656145.214844`. Test 4 alone has
  `GLEE_PERS_ZERO_MARGIN_TRUTH_V1=1`,
  `GLEE_PERS_P08_POSITIVE_PROSE_V1=1`, and
  `GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2=1`; the other four slots lack all three.
  Fleet-wide V1 remains `1`, and all ten persuasion `*_AB` keys remain explicit
  `0` everywhere. These Test-4-only values are the authorized deterministic
  challenger, not configuration drift.
- Exact replay covered all `966/966` post-boundary persuasion turns from 50
  observed game IDs (`419` seller, `547` buyer), with all actions sourced from
  the heuristic. The truth switch is live-verified at
  `eligible/fired/action_changed=1/1/1`. The prose switch had 39 isolated
  eligible turns and changed 38 live turns; the remaining eligible low-quality
  equality turn was correctly preempted by the truth switch. Buyer V2 remains
  `0/0/0` because no strict missed-decline state has appeared yet.
- All 39 emitted changes occurred in two games and passed scope, wire, gate,
  marker, legality, overlap, and full-plan replay checks. The 38 prose changes
  were seller/player-1, text, p=.8 positive recommendations and changed literal
  `yes` only to exact `I recommend this one.` The one truth change was a
  seller/player-1, known-value, low-quality, p=.8/v=1.25P/u=0 equality turn and
  changed the control recommendation `yes` to decline `no`. There was no V1 or
  legacy A/B overlap, multi-gate wire, illegal action, error, timeout, traceback,
  fatal line, or process incident. The 927 nonfiring turns were byte-identical.
- This is mechanism evidence only. The local results collector has not flushed
  a single post-boundary persuasion final, so all 50 assignments remain
  unresolved for outcome analysis even though 47 had visibly reached round 20;
  the other three were at rounds 19, 12, and 6. One game opened 4.33 seconds
  before `Tcfg` and had no challenger firing; 49 are clean-start assignments.
  Do not condition on the two firing games or impute any unresolved final.
- The latest authenticated snapshot at `1787656881.8295639` keeps the account at
  persuasion rank `4`: Agent 5 is best at `2395.58`, `51.42` below the unchanged
  third-place threshold `2447.00`. The gap improved from `67.42`, while Test 4's
  early rating movement occurred before any strict-edge action change and cannot
  identify challenger harm or benefit.
- Decision: keep the authorized Test 4 challenger unchanged, with no promotion
  or rollback. Continue the first-20 exact audit for truth and buyer V2, retain
  every post-`Tcfg` assignment and nonfiring, and wait for complete local plus
  authenticated official joins before any performance decision. Codex made no
  live fleet/configuration/process change in this monitoring pass; the recurring
  monitor was updated to recognize the authorized boundary and these mechanism
  invariants.

## 16:36 elevated follow-up — decline did not persist; result joins stalled

- Rank remains `4`. Test 2 is best at `2379.58`; the third-place threshold is
  still `2447.00`, so the current podium gap is `67.42`.
- The follow-up cohort `[1787654464.868853, 1787655673.768141]` retained 212
  assigned games. Rating movement split three down/two up with mean `+0.70`
  and descriptive 95% interval `[-19.27, +20.66]`. The preceding synchronized
  drop therefore did not persist; this window reverted to ordinary
  identical-policy noise. No stable buyer cell or opponent cluster repeated.
- Mechanism and live-state checks remain clean. Thirteen new V1 turns in four
  games passed exact OFF/ON replay, scope, action, source, marker, and sole-gate
  checks. Every persuasion `*_AB` flag is zero, V1 is `1`, V2 is absent, and
  there are no errors, timeouts, crashes, or abandoned games.
- The material evidence-pipeline issue has broadened: none of the five current
  processes has emitted a post-boundary local final-result row. In the latest
  incremental audit, 198/214 games reached round 20 but 0/214 joined a result.
  Authenticated per-game rating joins also remain zero. This does not explain
  official rating movement—the server aggregate counts continue to advance—but
  it prevents reliable outcome/cell diagnosis.
- Decision remains no deployment or rollback. Preserve V1, keep V2 OFF, and do
  not revive measured-negative selectivity or prose. Continue fixed
  all-assignment monitoring while the result and authenticated join pipelines
  recover.

## 16:18 monitoring alert — podium lost, no reversible mechanism fault

- The authenticated 16:10 snapshot moved our account-best persuasion marker
  from rank `3` to rank `4`. Test 2/hardliner is now best at `2389.64`; the
  displayed third-place threshold remained exactly `2447.00`, leaving a `57.36`
  gap. The podium loss came from our ratings falling, not a rising threshold.
- Frozen cohort `[1787653255.820292, 1787654464.868853]` retained all 220
  assigned persuasion games, exactly matching the aggregate official game-count
  advance. Every slot fell: Test 1 `-62.43`, Test 2 `-39.43`, Test 3 `-46.34`,
  Test 4 `-3.92`, and Agent 5 `-42.78`. Mean movement was `-38.98`, with a
  descriptive cross-slot 95% interval `[-57.82, -20.14]`. Shared-field
  correlation prevents a causal policy claim, but this clears the fleet-level
  deterioration alert and warrants continued elevated monitoring.
- The available local finals are buyer-weak but incomplete: 82/220 joined
  completed outcomes, with sellers showing three zeros and zero negatives,
  versus buyers showing 22 zeros and all eight negatives. The eight losses span
  four slots, both message modes, every prior, several value ratios, and several
  opponents. Buyer `p=.5` is the broadest weak diagnostic slice, but 138/220
  outcomes remain unresolved and there are zero current authenticated per-game
  rating joins, so no cell or opponent supports a deterministic patch.
- No reversible mechanism or operational cause was found. All five agents are
  complete all-family/LLM-off processes on post-`6d3aec4` code; every persuasion
  `*_AB` flag is zero, V1 is `1`, and V2 is absent. There were zero strategy
  errors, timeouts, API incidents, crashes, forced cycles, or abandoned games.
  V1 fired only nine turns in five of the 220 games, too rarely to explain the
  synchronized decline; incremental exact OFF/ON replay and scope checks remain
  clean. V2 emitted zero live markers.
- Decision: do not reactivate measured-negative selectivity and do not deploy
  V2 on this non-identified batch. Preserve the deterministic live stack while
  recovering authenticated per-game deltas and terminal joins. Four newly
  cycled slot collectors have not yet emitted local final rows despite many
  round-20 games; only conceder is current. This is an evidence-pipeline gap,
  not a confirmed competition-game failure.

## 13:30 inert candidate — deterministic direct-decline V2

- The authenticated 13:29 snapshot still has our account-best Test 1/champion
  at official persuasion rank `3`, rating `2449.40`. This retains the podium;
  no live policy change was made while V2 was developed and validated.
- `GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2` is implemented as a broad deterministic
  buyer parser-safety extension and is default OFF. It is not a hash arm, an A/B
  policy, or a grid-cell probe. It applies across persuasion configurations but
  can only turn an existing buyer-v2 BUY into PASS when the current text directly
  instructs the buyer not to buy and the live V1 expanded parser missed it.
  Binary messages, seller actions, existing passes, history/reporting language,
  current positive claims, ambiguous contrast, and all flag-OFF responses remain
  unchanged. The new marker/gate is emitted only on an actual BUY-to-PASS change.
- Frozen all-outcome diagnostic cohort: 5,334 completed persuasion games,
  including 1,382 buyer/text games and 27,640 turns, from
  `[1787607608, 1787642008]`. The conservative selector found 181 direct current
  declines across 29 games. Exact recorded-state OFF/ON replay produced
  `eligible=fired=action_changed=51` in 16 games; every one of the 51 observed
  purchases revealed LOW and none HIGH. Coverage spans 14 configuration cells,
  every prior, ratios 1.25/2/3/4, both seller-knowledge states, all three scales,
  rounds 1-17, and visible plus hidden opponents. The selector reproduced the
  frozen 181-message set exactly: 181/181 recall, zero outside-set matches, zero
  current-positive/history/contrast ambiguities. OFF reproduced all 27,640
  recorded actions byte-identically, and non-firing ON states were also
  byte-identical.
- This is mechanism and corpus-precision evidence, not an identified official
  rating lift. The 51 qualities are action-selected and seller adaptation is
  unobserved. Therefore the live V1 stack remains the recommendation until a
  deterministic, prospective official-rating validation is authorized.
- Frozen prospective boundary for the deployment owner: enable V2 for every
  persuasion game on exactly one nonleading complete-agent challenger at a clean
  timestamp, leaving the other four complete agents byte-identical and every
  persuasion `*_AB` flag zero. Retain all assigned outcomes, including refusals,
  zeros, losses, timeouts, unresolved games, and immediate terminals. Any scope,
  parser, legality, source, wire, marker, or process-integrity failure is an
  immediate mechanism rejection. Review harm only after 500 authenticated joined
  games and at least five would-change events; reject only if the official
  challenger-minus-unchanged trend interval is wholly negative. The fixed final
  boundary is 2,000 authenticated joined games, at least 20 would-change events,
  zero unresolved/missing joins, positive official trend interval, positive
  buyer/text point estimate, and no official cell with `n>=100` losing at least
  0.5 rating/game. Crossing without those conditions remains challenger-only.
- Verification after the final parser fixes: focused V1/V2 tests `131 passed`;
  persuasion audit `390 passed`; full allowed suite `2182 passed, 3 failed`.
  The failures are pre-existing/non-persuasion: the bargaining horizon-floor
  assertion plus live-grid drift alarms for bargaining and negotiation. Python
  compilation and `git diff --check` passed. No replay_eval, arena, or redteam
  command was run.
- No live process was restarted, signalled, cycled, stopped, or drained. No live
  fleet configuration, `arms.json`, `control.json`, `.env`, bargaining behavior,
  or negotiation behavior was edited by this work. V2 remains OFF everywhere.

## 12:01 monitoring checkpoint — podium and deterministic stack stable

- The authenticated persuasion board reports account-best Test 2 at official
  rank `3`, rating `2447.19`, 110.56 behind rank-2 HAWK (`2557.75`) and 113.82
  behind rank-1 gill bates (`2561.01`). The account-best slot has rotated among
  byte-identical persuasion policies and remains inside the measured roughly
  `+/-125` dispersion, so this is monitoring evidence rather than a profile
  comparison or identified veto effect.
- The current clean-process streams now contain 64 post-boundary veto firings
  in 26 games. Scope, role, expanded-decline parsing, action, source and
  sole-gate checks pass `64/64`; exact recorded-state OFF/ON replay also passes
  `64/64`, with only BUY/yes changing to PASS/no plus marker/gate metadata.
  No post-boundary process error, traceback, fatal or timeout line was found.
- Every persuasion `*_AB` overlay remains zero and the deterministic veto
  remains `1` on all five complete agents. No live change is justified.

## 10:56 monitoring checkpoint — podium retained, mechanism clean

- The authenticated persuasion board reports account-best Agent 5 at official
  rank `3`, rating `2432.81`, 114.75 behind rank-2 HAWK (`2547.56`) and 128.20
  behind rank-1 gill bates (`2561.01`). The `-27.60` movement from the 10:18
  snapshot remains small relative to the measured roughly `+/-125` dispersion
  across identical persuasion policies; it is not evidence for a policy change.
- The five current clean-process streams now contain 32 post-boundary
  explicit-decline veto firings in 15 games. Fourteen firings in four games were
  new since the previous audit. Scope, role, parser, source, action and sole-gate
  checks passed for all 32, and exact recorded-state replay again showed only
  BUY/yes with the veto OFF versus PASS/no live and ON, plus the marker/gate
  metadata. No new process error, traceback, fatal or timeout line was found.
- Every persuasion `*_AB` overlay remains zero on all five slots and the
  deterministic veto remains `1`. No live persuasion change is justified.

## 10:18 monitoring checkpoint — rank 3 sustained after portfolio clone

- The authenticated persuasion board reports account-best Agent 5 at official
  rank `3`, rating `2460.41`, 65.18 behind rank-2 HAWK (`2525.59`) and 100.60
  behind rank-1 gill bates (`2561.01`). This sustains the podium objective but
  remains a time-stamped monitoring result inside the measured cross-agent
  noise range, not a causal estimate of the deterministic veto.
- At the operator's explicit one-time direction, the whole-agent deployment
  owner copied Agent 5's complete stack to Test 3 and Test 4 at epoch
  `1787629250`. No persuasion flag changed: all five still have the deterministic
  explicit-decline veto `1`, the same persuasion policy, and every persuasion
  `*_AB` flag `0`. Clean current boundaries are Test 3 PID `86555` at
  `1787630856`, Agent 5 PID `87209` at `1787631287`, and Test 4 PID `88096` at
  `1787632084`, all deterministic `hardliner`, LLM off, and queued for all three
  families. The clean boundary and identity-preservation details are in
  `.ai/HANDOFF.md`.
- Across the five current clean processes, the post-boundary turn streams
  contain 6,509 persuasion actions from 338 assigned games: 169 buyer and 169
  seller. Ten additional vetoes fired in six games. Scope/source/parser/gate
  checks passed `10/10`, and exact recorded-state OFF/ON replay passed `10/10`:
  OFF was BUY/yes, ON and live were PASS/no, and only `plan.buy`, the marker,
  and its sole appended gate changed. All five process outputs have zero new
  error, traceback, fatal, or timeout lines.
- The local results collector has not yet emitted terminal records for this
  newest 338-game cohort. They remain unresolved/backlog in local accounting;
  do not impute them as timeouts or condition a result on the six affected
  games. No policy change is justified at this checkpoint.

## 04:39 monitoring checkpoint — top-three sustained

- Test 4 remains official persuasion rank `3` at `2489.61`, `38.20` behind
  rank-2 HAWK and `71.40` behind rank-1 gill bates. Its like-for-like movement
  is `+68.41` over 198 added persuasion games. This remains inside the measured
  cross-agent noise range and is monitoring evidence, not a causal veto effect.
- The last two old processes completed natural clean drains: Test 2 launched
  PID `50751` at 04:26:34 after 4,577 seconds, and Test 1 launched PID `50781`
  at 04:26:55 after 4,890 seconds. Neither abandoned a game. All five current
  processes now retain their intended deterministic profiles, full three-family
  queues, LLM off, persuasion veto `1`, and all ten persuasion A/B flags `0`.
- The extended mechanism audit is clean through `41/41/41`
  eligible/fired/action-changed events in 26 games across 21,106 post-boundary
  turns / 1,068 assigned games. All 26 affected games are authenticated
  completed; exact replay and scope/parser/source/gate checks pass, with zero
  persuasion errors or affected-game timeouts. No deterministic policy change
  is justified by this checkpoint.

## 04:19 monitoring checkpoint — authenticated persuasion rank 3

- The authenticated persuasion board reports Test 4 at official rank `3` with
  rating `2474.35`. HAWK is rank 2 at `2500.97` (gap `26.62`) and gill bates is
  rank 1 at `2561.01` (gap `86.66`). Agent 5 is immediately behind our account
  leader at `2460.23`. Test 4's row position is lower than three because the
  board also displays higher-rated agents that are unranked/non-account-best;
  the API rank field itself is `3`.
- Like-for-like Test 4 movement from the rollout baseline is `+53.15` over 157
  added persuasion games. Agent 5 is `+57.83` over 154 games. This achieves the
  current persuasion top-three snapshot, but remains observational and inside
  the measured roughly `+/-125` cross-agent noise range; it is not an isolated
  causal estimate of the veto and does not justify another policy change.
- Natural all-family replacements were clean: Test 3 launched PID `48229` at
  04:05:23 after a completed drain, Test 4 launched PID `48235` at 04:05:34
  after a completed drain, and Agent 5 launched PID `48295` at 04:06:38 with
  zero games abandoned. Their deterministic profiles, all-three-family queues,
  LLM-off mode, persuasion veto `1`, and all ten persuasion A/B flags `0` were
  preserved. Test 1 PID `37884` and Test 2 PID `38947` remained healthy and
  were each naturally draining one active game.
- The mechanism extension is clean through `35/35/35`
  eligible/fired/action-changed events in 20 affected games across 17,176
  post-boundary persuasion turns / 866 assigned games. Exact OFF/ON replay,
  scope, parser, action, source, and sole-gate checks all passed. Every affected
  game is authenticated completed; no persuasion error, affected-game timeout,
  legacy gate, or unexplained plan delta was observed. Local collector evidence
  covers 580 games; locally missing records remain backlog, not imputed losses.

## 03:10 deterministic whole-policy rollout — live on all five complete agents

- Commit `e6ca9c6` added the default-OFF deterministic
  `GLEE_PERS_BUYER_EXPLICIT_DECLINE_VETO_V1`. It is a buyer-v2 final veto only:
  an existing BUY becomes PASS when the current seller signal is a strict binary
  decline or an explicit text decline recognized by the expanded parser. It
  never creates a purchase, never reinterprets history, and never changes the
  seller policy. Commits `c085878`, `acd2453`, and `d615ac8` corrected and
  recorded the evidence; `HEAD == origin/main == d615ac8` at deployment.
- Pre-deployment verification passed on every exact named stack over 800 games:
  `eligible=763`, `fired=763`, and `action_changed=763` for Test 1/champion,
  Test 2/champion, Test 3/conceder, Test 4/composite, and Agent 5/hardliner.
  Focused tests passed 142, the persuasion audit passed 380, and the full suite
  passed 1,798 with only the two known bargaining failures. A 4,000-state
  property audit produced 273 changes, all legal BUY-to-PASS; 26,236 synthesized
  parser messages produced zero default-OFF/legacy changes.
- Deployment used `scripts/fleet.py` only. The final overlay boundary is
  `1787606572.088` (2026-08-25 02:52:52 IST): the deterministic flag is `1` and
  all ten persuasion `*_AB` flags are explicit `0` on all five slots. No
  bargaining or negotiation key was changed, `control.json` was not edited by
  this workstream, and no process was restarted or signalled.
- Clean post-code/post-overlay process boundaries are:

  | Complete agent | Slot | PID | T0 | deterministic profile |
  |---|---|---:|---:|---|
  | Test 1 | champion | 37884 | 1787607314 | champion |
  | Test 2 | hardliner | 38947 | 1787607608 | champion |
  | Test 3 | conceder | 36614 | 1787606834 | conceder |
  | Test 4 | randomized (legacy slot name) | 37202 | 1787607037 | composite |
  | Agent 5 | composite | 37885 | 1787607315 | hardliner |

  Every command retains `--families bargaining,negotiation,persuasion` and
  `--llm-mode off`. Test 3 and Test 2 completed natural clean max-time drains.
  Test 4, Test 1, and Agent 5 crossed previously queued authoritative-idle
  boundaries; the supervisor recorded zero games abandoned for each. The Test 4
  slot name does not imply random behavior: its loaded profile is deterministic
  `composite`.
- The frozen first-20 audit is complete, and the later monitoring extension is
  clean through 32 emitted vetoes in 17 games: Test 1/champion `7`, Test
  2/hardliner `5`, Test 3/conceder `7`, Test 4/randomized `12`, and Agent
  5/composite `1`. Exact recorded-state replay passed `32/32`; every event was
  buyer/player 2 on a strict binary or expanded-parser explicit current decline,
  with heuristic PASS/`no` live versus BUY/`yes` flag-off. Only `decision`,
  `plan.buy`, the marker, and its sole appended gate changed. Across 13,823
  post-boundary persuasion turns / 700 assigned games there were zero scope,
  parser, legality, legacy-gate, action, persuasion-error, or affected-game
  timeout failures. All 17 affected games were authenticated completed. Local
  outcomes existed for 270/700 assigned games; the other 430 are collector
  backlog or active and must not be imputed as server abandonment. Thus live
  `eligible=fired=action_changed=32` is verified without selecting on outcomes.
- Frozen fixed-stream evidence is diagnostic rather than causal: 1,934 assigned
  buyer games (1,925 completed, six active, three no-deal) contained 85 games
  and 176 turns that this veto would change; 175 of 176 changed turns were low
  quality. Text had 987 assigned / 981 completed / 156 changed turns (155 low,
  one high; local diagnostic `+0.009012` percentile). Binary had 947 assigned /
  944 completed / 20 changed turns (20 low, zero high; local `+0.000983`). The
  authenticated export did not contain enough buyer joins for an official
  causal estimate, so official post-cutover rating movement remains monitoring
  evidence, not a causal A/B estimate.
- Authenticated rollout baseline immediately after the five-host cutover:
  Test 1 `2266.2` persuasion / 12,924 games; Test 2 `2393.8` / 13,581; Test 3
  `2098.4` / 14,466; Test 4 `2421.2` / 6,716; Agent 5 `2402.4` / 12,464. The
  persuasion leaderboard snapshot showed account-best Test 4 rank 4 at
  `2431.8`, 70.0 behind rank 3 HAWK, 74.2 behind rank 2 king, and 124.0 behind
  leader gill bates. The per-agent stats and board are separately timed official
  snapshots; compare each source like-for-like on later reads.
- Automation `monitor-glee-persuasion-experiment` now runs every 15 minutes. It
  checks all five complete agents, every persuasion outcome, live mechanism
  integrity, official rating/rank movement, and broad deterministic improvement
  opportunities. New ideas must remain broad, deterministic, and default OFF;
  no randomized policy, hash arm, A/B probe, or narrow-cell deployment may be
  introduced.

Everything below this point is historical pre-rollout evidence. It remains
useful for measured negatives and incident boundaries, but its old live-arm
statements are superseded by the all-zero A/B boundary above.

## Historical live persuasion boundary

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
