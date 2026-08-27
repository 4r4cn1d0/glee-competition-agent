# EXPERIMENTS — hypothesis, design, verdict

## AUTHORIZED / PENDING CLEAN TEST 4 BOUNDARY — `seller-positive-pass-streak-truth-v1` (27 Aug)

- **Operator supersession and null**: the operator now authorizes this first
  credibility-recovery stage on physical Test 4 / slot `randomized`, replacing
  the earlier proposed Test 2 allocation.  The never-exposed cumulative-rate candidate
  `GLEE_PERS_SELLER_DEMAND_COLLAPSE_TRUTH_V1` is abandoned because its own
  truthful NO/pass rounds lower its denominator and can self-lock the policy.
  Its historical flag is inert, not redefined.  The replacement is the separate
  default-OFF `GLEE_PERS_SELLER_POSITIVE_PASS_STREAK_TRUTH_V1`.  The null is no
  improvement in authenticated same-configuration, seller-role rating over the
  complete all-assignment cohort.  The flag remains absent/OFF on the live
  fleet at this record; authorization does not permit an in-flight overlay
  write, process restart, signal, force-cycle, or change outside persuasion.
- **Mechanism contract**: first compute the complete ordinary seller plan.
  Eligibility requires persuasion seller/player 1 at its exact legal seller
  action, nonterminal integral round `2..19` of 20, known finite values, LOW with
  `u < price`, prior EV at least price, and the exact ordinary all-push control
  plan (`YES`, reason `prior alone justifies purchase`, lie rate 1).  History
  must contain every preceding round exactly once and in order, with exact bool
  outcomes consistent with buyer decisions.  Token-text accepts only literal
  `yes`/`no`; binary uses the strict binary signal.  Fire only when the three
  most recent explicit positive recommendations were all passed.  Explicit
  declines are ignored and any more recent purchased positive resets the
  streak.  Role/phase/knowledge contradictions, malformed history or values,
  harmless LOW (`u>=price`), terminal/HIGH turns, LLM/prose/wire recomposition,
  any optional seller flag/gate/marker, and nonfires all fail closed.
- **Allowed delta**: submitted wire `YES -> NO`; plan `recommend True->False`,
  reason and `lie_rate 1->0`; add only marker
  `seller_positive_pass_streak_truth_v1=true` and sole gate
  `pers_seller_positive_pass_streak_truth_v1`.  It never reads game ID,
  opponent, cell allowlists, or buyer-private information.
- **Motivation, not efficacy**: corrected both-mode all-assignment logs contain
  1,432 Agent 5 seller assignments and 644 Test 2 seller assignments.  The
  trigger reached 668 LOW turns/109 games on Agent 5 (`8/664` observed target
  LOWs sold) and 359/59 on Test 2 (`3/359` sold).  These outcomes were generated
  under continued all-push behavior and are action-selected.  They cannot
  identify buyer recovery after the new truthful decline.
- **Current Test 4 shadow, not efficacy**: the stable V2/V3-era log through the
  authorization contains 3,078 persuasion assignments, including 1,617 seller
  assignments (1,594 joined and 23 unresolved).  The exact stage-1 predicate
  reaches 113 seller games / 644 LOW turns; only `14/644` control LOW
  recommendations sold.  After first reach, only 11/113 games later sold a
  HIGH (`28/598` later HIGH turns).  This establishes substantial reach and low
  observed control conversion, not the counterfactual effect of truthful NOs.
- **Preflight**: focused seller safety/interaction tests pass `172/172`; the
  current persuasion-wide suite passes `930/930`.  Exact Test 4 `randomized`
  overlay with the effective `hardliner` wrapper over 800 games passes
  `eligible=fired=action_changed=371/371/371` on seed 270827, with legal
  isolated `YES -> NO` wires.  An independent seed produced `326/326/326`.
  The complete suite is `2,787 passed / 3 failed`, with exactly the
  declared bargaining horizon-floor and bargaining/negotiation live-grid drift
  failures.  An independent adversarial reviewer returned PASS after literal
  text-token and contradictory-metadata leaks were reproduced and closed.
- **Allocation and identification**: run this addition alone on physical Test
  4; protect Agent 5 and every other slot, preserve Test 4's complete B+P
  topology, V1/V2/V3 buyer safety background, and non-persuasion overlay, and
  keep all persuasion A/B keys zero.  Do not add terminal push, seller truth/
  prose, the abandoned cumulative-rate flag, or another seller addition.
  Because the operator requires a deterministic named one-slot
  challenger rather than randomized per-game allocation, the result is
  observational and cannot establish a causal treatment effect.  Retain every
  post-boundary persuasion assignment and report the seller-role primary over
  all seller assignments, both modes, fires/nonfires, buys/passes,
  zeros/losses/timeouts/unresolved/immediate terminals, and compare official
  same-role/configuration evidence to a frozen Test 4 pre-period and unchanged
  contemporaneous agents.  Agent 5 is currently bargaining-only and therefore
  is a protected historical benchmark, not a contemporaneous persuasion
  control.  The game—not the turn—is the analysis unit.
- **Clean deployment boundary owned outside Codex**: the present Test 4 PID
  launched from the dirty workspace with the code likely loaded but the flag
  absent, and it held active persuasion games during this audit.  First commit
  and push the inert implementation, then require a later natural Test 4
  process containing that commit and exact `--probe hardliner --llm-mode off
  --families bargaining,persuasion --max-time 3600`.  After it stops acquiring
  naturally, require terminal proof for every persuasion game it touched and
  authenticated `active=0,pending=0`.  Freeze its PID/load boundary, Test 4
  full/persuasion/non-persuasion overlays and hashes, every other slot,
  `control.json`, arms mtime, authenticated persuasion rating/count, and the
  preceding 2,000 authenticated seller assignments.  Only the deployment owner
  may then use one `scripts/fleet.py set randomized` write to set
  `GLEE_PERS_SELLER_POSITIVE_PASS_STREAK_TRUTH_V1=1`.  Verify that sole Test 4
  persuasion-key delta, all persuasion A/B values zero, and byte-identical
  Agent 5/other-slot/non-persuasion/control state.  Never edit fleet JSON by
  hand or restart/signal/force-cycle a process.
- **Mechanism audit and immediate rollback**: exact OFF/ON replay every state
  until 20 clean firings.  Require seller/player 1, known-loss LOW, rounds
  2..19/20, exact baseline YES, three passed explicit positives since the last
  purchased positive, live NO, heuristic source, legal wire, sole adjacent
  marker/gate, and only the documented plan delta.  Nonfires must be full-object
  identical.  Any scope/history/quality/role/mode/round error, HIGH decline,
  overlap, illegal wire, unexplained delta, strategy error, or attributable
  timeout rejects the mechanism and requires the deployment owner to set only
  this flag explicitly to `0`; never clear the key.
- **Precommitted looks**: continuous reads may inspect only mechanism scope,
  legality, errors, timeouts, assignment counts, join recovery, and reach;
  outcome/rating reads occur only at the fixed looks below.  Primary endpoint
  is authenticated official seller-role, same-configuration rating difference-
  in-differences against the frozen Test 4 pre-period and unchanged live slots.
  Secondary all-assignment endpoints are seller payoff/price, zero-payoff rate,
  low-sale rate, mode/prior slices, affected-game later-HIGH recovery, and
  later-HIGH turn purchase rate.  No completed-only or firing-only filter is
  permitted.
  - Harm: `N_seller>=500`, `N_affected>=40`, and zero missing joins.  Roll back
    for any mechanism failure, a 99% CI for official seller DiD wholly below
    zero, or a zero-payoff deterioration of at least 10 percentage points whose
    99% CI is wholly above zero.
  - Futility: `N_seller>=1,000`, `N_affected>=70`.  Stop only when the point
    estimates for official seller DiD, normalized payoff, and affected-game
    later-HIGH recovery versus frozen `11/113 = 9.7%` are all nonpositive.
  - Final: `N_seller>=2,000`, `N_affected>=100`, and zero missing joins.  Retain
    on Test 4 only if the official seller DiD lower 95% bound is above zero,
    normalized-payoff point delta is positive, zero- and low-sale-rate deltas
    are nonpositive, binary and text official points are nonnegative, no
    `n>=100` mode/prior slice loses at least `.5` rating/game, and mechanism
    audit remains clean.  An inconclusive result may remain Test-4-only but
    cannot advance.  Declare reach futility at 4,000 seller assignments if 100
    affected games have not accrued.  If authenticated joins remain
    unavailable, the policy cannot be promoted.
- **Frozen sequential advancement rule**: do not inspect arbitrary interim
  slices or alter the treatment between fixed looks.  Stage 2 and stage 3 are
  separate future flags and cohorts, never silent changes to V1.  Stage 1 must
  first pass its final and improve both recovery diagnostics to affected-game
  later-HIGH recovery `>=20%` (frozen control `9.7%`) and later-HIGH turn
  purchase `>=10%` (frozen control `28/598 = 4.68%`).
  - Stage 2 may then encode the earlier two-pass/burn-confirmed state as a
    separate incremental gate.  Precommitted looks are `750 seller/30
    incremental games` harm, `1,500/60` futility, `3,000/120` final, and a
    6,000-seller reach ceiling.  Apply the same CI harm and final criteria
    incrementally versus stage 1.
  - Stage 3 remains unimplemented until at least 2,000 prospective stage-2
    seller assignments show incremental reach `>=1.5%` and at least 30 games,
    plus at least 30 would-change LOW turns with control sale rate `<=10%`.
    Its frozen mechanism would require two consecutive purchased HIGH/YES
    recommendations to leave recovery, with any passed positive resetting the
    success count.  If qualified, looks are `1,000/15` harm, `3,000/40`
    futility, `6,000/80` final, and a 12,000-seller reach ceiling.
  Current fixed-history shadows do not qualify: stage 2 creates only five
  wholly new games in 1,617 seller assignments, while stage 3 reaches nine
  games (`0.56%`) and `9/25` affected LOW opportunities sold under control
  (`36%`).  Therefore neither later stage is built or authorized now.

## OPERATOR-TERMINATED, NO EFFICACY VERDICT — `seller-terminal-push-v1` (27 Aug)

- **Rollback boundary**: the operator ended this challenger before its frozen
  efficacy read.  At `T1=1787776198.0249655`, one
  `scripts/fleet.py set hardliner` write changed only
  `GLEE_PERS_SELLER_TERMINAL_PUSH_V1` from `1` to explicit `0`; the key must
  remain explicit zero because clearing it could expose the launch value.
  Test 2's non-persuasion overlay, `control.json`, Agent 5, and every other
  slot remained byte-identical, and every persuasion `*_AB` key remained zero.
  The completed local pre-T1 cohort contains 121 assignments (55 seller, 66
  buyer) and 19 clean seller-terminal firings, with zero source errors or
  timeout records.  That is underpowered relative to the precommitted
  500-seller harm and 2,000-seller final reads, so this is neither a promotion
  nor a rejection of the mechanism.  Do not reactivate it without fresh
  operator authorization and a new clean cohort.

- **Operator decision and allocation**: the operator explicitly authorized the
  terminal seller repair on physical Test 2 / slot `hardliner`.  It may add only
  `GLEE_PERS_SELLER_TERMINAL_PUSH_V1=1` to the exact then-current Test 2 stack.
  Agent 5, Test 1/3/4, every buyer rule, every bargaining key, `control.json`,
  the process/family topology, and all persuasion `*_AB` keys remain unchanged.
  Test 2 continues bargaining + persuasion with negotiation disabled and LLM
  off.  This is a deterministic named challenger, not a randomized policy or
  game-ID arm.
- **Mechanism contract**: first compute the complete existing seller plan.  The
  addition is eligible only on persuasion seller/player 1 at its own legal
  seller action, exact numeric round `20/20`, private quality LOW, and a
  baseline `recommend=false`.  It changes only the wire `no -> yes`, the plan's
  `recommend: false -> true`, and adds marker `seller_terminal_push_v1` plus
  sole gate `pers_seller_terminal_push_v1`.  HIGH, earlier/non-20 terminals,
  baseline YES, every buyer turn, malformed rounds, wrong roles/families, and
  all nonfires are byte-identical.  It accepts omission of the redundant
  `player_1_role` field because persuasion structurally fixes player 1 as
  seller, but rejects a contradictory role.  Any optional seller policy,
  existing seller gate/marker, or nonzero/nonfinite backload value makes it fail
  closed.  No opponent identity, game ID, buyer hidden value, or configuration
  allowlist is consulted.
- **Rationale and objection**: backward induction removes the reputation cost
  of a LOW recommendation only on the final round; there is no round 21 whose
  trust can be damaged.  In the current-era `p=1/3` seller logs, HIGH terminal
  units were already YES `543/543`, while LOW terminal units were YES
  `382/1,061` and NO `679/1,061`; resolved terminal NO sold `0/625`.  Those
  actions are selected by the current policy and do not identify the
  counterfactual buy rate or official-rating effect.  This does not revive the
  measured-negative broad backload arm: no earlier sale is withheld and no
  baseline YES is changed.
- **Implementation evidence**: the change is default OFF.  Focused tests pass
  `52/52`; persuasion-wide tests pass `663/663`.  Exact physical Test 2
  `hardliner` stack / effective `champion` reachability over 800 paired games
  passes `eligible=fired=action_changed=117/117/117`, in both binary and text
  modes.  Full verification is `2742 passed` plus exactly the three declared
  non-persuasion failures: the stale bargaining horizon-floor assertion and
  bargaining/negotiation live-grid drift alarms.  These results prove scope,
  isolation, and reach—not efficacy.
- **Supersession boundary**: Test 2's live `tight-credibility-reset-v1` cohort
  was precommitted with every seller rule frozen and was only 910/2,000 at the
  latest complete checkpoint.  Do not mix the new seller treatment into that
  cohort.  At the eventual clean activation boundary, record the reset-only
  cohort as **operator-superseded without an efficacy verdict** at its exact
  authenticated assignment count.  Keep its already-live buyer flag and all
  other Test 2 values unchanged as frozen background; begin a new incremental
  seller-terminal cohort only after the new Tcfg.
- **Claude-owned clean activation**: Codex must not edit live fleet documents or
  processes.  The deployment owner must first review, commit, and push the inert
  code, then wait for a code-loaded Test 2 process and use the SDK-native bank /
  natural zero-game drain—never a signal, restart, force-cycle, or abandonment.
  Freeze the old PID/load time, full Test 2 overlay and non-persuasion hash,
  every other slot, `control.json`, arms mtime, authenticated persuasion
  rating/count, and terminal proof for every touched game.  At `active=0` and
  `pending=0`, one `scripts/fleet.py set hardliner` write may set only
  `GLEE_PERS_SELLER_TERMINAL_PUSH_V1=1`.  Verify that single persuasion-key
  delta, explicit-zero A/B flags, unchanged Agent 5/other slots/non-persuasion
  hash/control, then allow the normal Test 2 B+P process to load it.
- **Audit and immediate rollback**: retain every post-Tcfg persuasion
  assignment and outcome/nonoutcome, both roles and modes, all scales/priors,
  fires/nonfires, buys/passes, zeros, negatives, timeouts, unresolved games and
  immediate terminals.  Exact OFF/ON replay the first 20 firings; each must be
  seller/player 1, LOW, round 20/20, heuristic, legal, sole-gate NO-to-YES with
  no unexplained plan delta.  Any scope/role/round/quality error, HIGH change,
  overlap, illegal wire, nonfire delta, strategy error, or attributable timeout
  rejects the mechanism and requires explicitly setting only this Test 2 flag
  to `0` through fleet tooling; never clear the key or alter the process stack.
- **Frozen efficacy reads**: one harm look after 500 fully authenticated
  post-Tcfg **seller assignments** with zero missing joins and at least 20
  affected games; reject on a wholly negative official Test2-seller trend or a
  zero/negative-payoff rate at least 10 points worse with a wholly positive
  interval.  No early efficacy promotion.  Final read after 2,000 fully
  authenticated seller assignments with zero unresolved joins and at least 80
  affected games.  Retain Test2-only only if official seller trend and
  normalized-payoff deltas are positive, zero/negative/severe-rate deltas are
  nonpositive, both message-mode point estimates are nonnegative, no `n>=100`
  seller mode x prior slice loses at least `.5` rating/game, and mechanism
  checks remain clean.  Agent 5 requires separate future authorization.

## LIVE ON TEST 2 — `tight-credibility-reset-v1` (26 Aug)

- **Activation boundary**: code/test commit `985ead2` is pushed. Test 2 PID
  `12216` was losslessly banked at `Tbank=1787745279.855`; it acquired no new
  game after that instant, all seven post-bank holdings authenticated terminal,
  server state reached `active=0,pending=0` at 17:30:21 IST, and the PID exited
  cleanly. Frozen pre-Tcfg persuasion was `2304.49/17632`. One fleet write set
  only `GLEE_PERS_BUYER_TIGHT_CREDIBILITY_RESET_V1=1` at
  `Tcfg=1787745792` (17:33:12). Test 2's non-persuasion hash and every other
  slot remained byte-identical; all persuasion `*_AB` flags stayed zero.
  Replacement PID `20124` launched at 17:33:53 from pushed HEAD with exact
  `--probe champion --llm-mode off --families bargaining,persuasion --max-time
  3600`. Its first 101 turns covered seven bargaining and six persuasion game
  IDs, all heuristic with zero errors/timeouts and no negotiation assignment.
  No controller firing had occurred at this initial health check; continue the
  first-20-per-direction exact audit below.

- **Allocation and null**: physical Test 2 / slot `hardliner` alone may
  prospectively add `GLEE_PERS_BUYER_TIGHT_CREDIBILITY_RESET_V1=1` to its
  otherwise frozen persuasion stack. Agent 5, every other slot, every seller
  rule, non-persuasion key, and all persuasion `*_AB` flags remain unchanged.
  This is a deterministic named one-slot challenger, not a randomized causal
  A/B test. The null is no improvement in authenticated same-configuration,
  same-role persuasion rating over the complete all-assignment cohort.
- **Controller contract**: compute the complete ordinary buyer-v2 plan first.
  Eligibility is persuasion buyer/player 2 at `buyer_decision`, current player
  2, text or binary mode, `tight=true`, breakeven probability at least `.75`,
  prior money EV no greater than price, a strict current direct positive, and
  unchanged posterior EV strictly above price. Text signals use a full-string
  anchored whitelist; ambiguous, historical, and future prose fails closed.
  Seller knowledge, current private quality, opponent, and game ID are never
  read. Credit is ordered public history: `last_strict_decline >
  last_purchased_LOW`. Invalid credit changes an ordinary BUY to PASS. Valid
  credit changes only a PASS proven to be the static tight-prior block
  (`blocked=true`, prior below the configured threshold) to BUY. All other
  states are byte-identical. Only a changed action adds the adjacent
  `buyer_tight_credibility_reset_v1` metadata and sole gate. Current-decline
  V1/V2/V3 retain final precedence; optional rank/selectivity/LCB/parser/audit/
  unlock/pulse conflicts fail closed.
- **Preflight and fixed-stream evidence**: the flag is default OFF. Focused
  tests pass `78/78`; exact current Test 2-stack reachability passes
  `eligible/fired/action_changed=460/460/460`; the full suite is `2673 passed`
  with exactly the three declared non-persuasion failures. Fixed-stream replay
  changes `6,718` turns in `877` games: `4,122` BUY->PASS and `2,596` PASS->BUY.
  These counts prove reach and precedence only. They are not payoff evidence:
  purchased quality is action-selected, passed quality is hidden, and the first
  changed action alters later posterior state and seller behavior.
- **Risk and objections**: the controller bundles reversible trust revocation
  and restoration, so a live read identifies only the whole controller.
  BUY->PASS can turn profitable highs into costly zeros; PASS->BUY can buy lows
  because neighboring buyer-v2 posteriors were optimistic by roughly 4-7
  points. A decline can be strategic bait. The measured-negative broad
  selectivity/strike and LCB ideas, mechanism-rejected rank gate, canceled broad
  selective-signal unlock, and underperforming LLM prose are not revived. The
  large shadow surface is an exposure warning, not evidence of likely lift.
  Display rating, raw payoff, and local percentile remain diagnostic only.
- **Clean T0 and cohort**: first push the inert code. Then use SDK-native
  `scripts/fleet.py bank hardliner` and wait without forcing until the old
  process has stopped acquiring, every touched game is terminal, authenticated
  active/pending are zero, and the PID exits. Freeze the exact process/load
  boundary, Test 2 full and non-persuasion overlays, every other slot, control
  hash, arms mtime, and authenticated persuasion rating/count. One atomic fleet
  write may set only this Test 2 flag; start Test 2 with exactly `--llm-mode off
  --families bargaining,persuasion`, leaving negotiation disabled. Enroll every
  post-Tcfg Test 2 persuasion assignment: both roles and modes, all scales,
  priors, knowledge states, fires/nonfires, buys/passes, zeros, losses,
  timeouts, unresolved games, and immediate terminals. Never condition the
  primary read on firing, direction, purchase, revealed quality, completion, or
  success. Agent 5 and all other slots remain untouched.
- **Mechanism audit and immediate rollback**: exact OFF/ON replay every turn
  until at least 20 clean BUY->PASS and 20 clean PASS->BUY firings; nonfires
  must be full-object identical. Any scope/signal error, malformed-history
  fail-open, wrong credit order, non-tight PASS revival, prior-profitable
  change, direct-decline overlap, multi-gate collision, illegal wire,
  unexplained delta, strategy error, or attributable timeout rejects the
  mechanism. Explicitly set only this Test 2 flag to `0` with fleet tooling;
  never clear the key or alter the process/family stack.
- **Frozen efficacy gates**: one harm look at `500` fully authenticated
  post-Tcfg assignments with zero missing joins and at least `20` affected
  games, including at least `5` per direction. Reject on a wholly negative
  official Test2-minus-frozen-pre/contemporaneous-control 95% interval, or a
  negative-payoff rate at least 10 points worse with a wholly positive interval;
  no early efficacy promotion. Final read is `2,000` fully authenticated
  assignments with zero missing/unresolved joins and at least `80` affected
  games, including at least `20` per direction. Retain Test2-only only if the
  overall official trend and tight-buyer point estimate are positive,
  normalized-payoff delta is positive, zero/negative/severe-rate deltas are
  nonpositive, every direction/mode/knowledge/scale point estimate is
  nonnegative, no `n>=100` role x mode x prior slice loses at least `.5`
  rating/game, and all mechanism/join checks remain clean. Agent 5 may not
  receive the controller without separate explicit future authorization.

## LIVE ON TEST 4 — `direct-decline-safety-v1` (26 Aug)

- **Activation**: after explicit operator authorization to restart Test 4, the
  SDK-native bank stopped acquisition and PID `5532` drained `7 -> 0` without
  abandonment. Its final game completed round 20, authenticated state reached
  `active=0,pending=0` at 16:13:12 IST, and the PID exited at 16:13:29. At the
  stable no-process boundary, one `scripts/fleet.py` write set only Test 4 V2
  and V3 to `1` at `Tcfg=1787741035` (16:13:55). Replacement PID `10380`
  launched naturally at 16:14:42 with `--probe hardliner --llm-mode off
  --families persuasion --max-time 3600`. The authenticated pre-Tcfg persuasion
  baseline was `2291.55/10701`.
- **Post-write isolation**: reversing only V2 `1 -> 0` and removing V3 from the
  post-write arms document reproduces the exact pre-write whole-file SHA-256
  `d72153b476d2bbd17cde8f0be227f860e0028d08cf98562a41b205e6c783c07e`.
  Test 4's non-persuasion hash, every other slot, and all persuasion `*_AB`
  values remained unchanged; Agent 5 stayed banked. The first 31 post-launch
  turns covered four fresh round-1 seller games, all heuristic with no error,
  timeout, or V2/V3 firing. Continue the frozen mechanism and efficacy rules
  below from this immutable Tcfg.

- **Operator authorization and isolation**: after reviewing Test 4's complete
  persuasion logs, the operator authorized the first, lowest-risk repair only:
  physical Test 4 / slot `randomized` keeps its Agent-5-equivalent persuasion
  baseline with V1=1 and adds only
  `GLEE_PERS_BUYER_EXPLICIT_DECLINE_V2=1` and
  `GLEE_PERS_BUYER_EXPLICIT_DECLINE_V3=1`. Test 4's prose/truth additions stay
  explicit zero; buyer unlock and seller demand-collapse truth remain absent/OFF;
  all ten persuasion `*_AB` keys stay explicit zero. Agent 5, Test 1, Test 2,
  Test 3, every non-persuasion key, `control.json`, and all processes are outside
  this experiment and must remain unchanged.
- **Falsifiable hypothesis**: direct current-round text warnings that V1 misses
  should never cause an existing buyer-v2 BUY. V2/V3 must improve Test 4's
  authenticated same-configuration, same-role persuasion outcome without a
  material losing buyer/text subgroup. This is a deterministic named one-slot
  challenger, not a randomized or causal A/B experiment; no component consults
  game id, opponent identity, or a configuration-cell allowlist.
- **Frozen evidence and objection**: the five-slot exact-log replay changes 128
  buyer/text turns in 62 games relative to V1-only: 127 purchased qualities were
  LOW, zero HIGH, and one unresolved. The newest complete Test 4 audit found
  eight additional missed direct warnings; all eight control purchases revealed
  LOW. These qualities are purchase-selected and seller adaptation is
  counterfactual, so they prove a parser/action-consistency defect and
  one-directional mechanism safety, not an identified official-rating lift.
  Reach is only about 1% of Test 4 assignments, so this repair is not expected
  to close the full gap to 2500 by itself.
- **Mechanism contract**: V1 runs first, then V2, then V3. Each new gate is
  limited to buyer/player 2, `buyer_decision`, current player 2, text mode,
  buyer-v2, and a complete control plan with `buy=true`. Live must be
  PASS/`no`, heuristic, legal, with exactly one adjacent marker/sole gate:
  `buyer_explicit_decline_v2` or `buyer_explicit_decline_v3`. The only plan
  delta may be `buy: true -> false`, its marker, and its gate. V1-owned, positive,
  ambiguous, history-only, binary, seller, legacy-buyer, and existing-PASS turns
  must remain byte-identical. A V1/V2 fire makes later gates unreachable.
- **Preflight**: current HEAD `00cf4a5` contains V2 commit `6d3aec4` and V3
  commit `cef2621`; both are default OFF. Focused V1/V2/V3 tests pass `164/164`.
  Exact current Test 4 hardliner-stack reachability over 800 games passes
  `630/630/630` independently for V2 and V3; separate stacked checks also pass.
  Full suite passes `2553` with only the three declared non-persuasion failures
  (bargaining horizon assertion and bargaining/negotiation live-grid drift).
- **Clean activation boundary**: do not arm while any Test 4 persuasion game is
  in flight. After the current PID stops acquiring naturally, require terminal
  proof for every persuasion game it touched and authenticated `active_games=0`.
  Freeze Test 4's exact PID/end time, HEAD/origin, full overlay, non-persuasion
  hash, all other slot overlays, `control.json` hash, arms mtime, authenticated
  persuasion rating/count, and Agent 5 bank state. Then the deployment owner may
  use one atomic `scripts/fleet.py set randomized` write for V2=1 and V3=1.
  Never restart, stop, signal, force-cycle, clear a key, or alter a queue.
- **Cohort and evidence rule**: enroll every Test 4 persuasion assignment whose
  first turn is post-Tcfg, including both roles, all nonfires, buys, passes,
  positives, zeros, negative/severe outcomes, timeouts, unresolved games, and
  immediate terminals. The primary endpoint is authenticated official
  same-configuration, same-role rating delta. Display rating, raw payoff, and
  local fitted percentile are diagnostic only. Compare the full Test 4 cohort
  to its frozen pre-period and contemporaneous unchanged agents; never condition
  on firing, purchase, completion, or a successful outcome.
- **Audit and immediate rejection**: exact OFF/ON replay every firing until 20
  clean V2 and 20 clean V3 events; nonfires must remain byte-identical. Any scope
  drift, positive/history-only veto, multi-gate overlap, PASS-to-BUY, illegal
  wire, nonheuristic source, unexplained plan delta, strategy error, or
  attributable timeout immediately rejects the mechanism and requires setting
  only Test 4 V2=0 and V3=0 explicitly through fleet tooling. If isolation is
  uncertain, set both explicit zero and report the incident.
- **Precommitted efficacy reads**: harm look at 500 fully authenticated Test 4
  games with zero missing joins and at least five combined V2/V3-affected games;
  reject if the official Test4-minus-frozen-pre/contemporaneous-unchanged trend
  interval is wholly negative or on any mechanism failure. Final read at 2,000
  fully authenticated games with zero missing joins and at least 20 combined
  affected games. Retain only with a positive overall official trend, positive
  buyer/text point estimate, no `n>=100` role x mode x prior slice losing at
  least `.5` rating/game, and zero mechanism/join failures. Anything short stays
  Test-4-only; Agent 5 may not receive it without a fresh explicit decision.

## CANCELED BEFORE EXPOSURE — Test 2 `adaptive-credibility-v1` (25 Aug)

- **Operator supersession at 23:29 IST**: the operator directed physical Test 2
  and Test 4 to use Agent 5's exact effective persuasion behavior. Test 2
  already matched Agent 5, so no Test 2 fleet write occurred and this profile
  received zero prospective assignments. V2, V3, buyer unlock, and seller
  demand-collapse truth remain absent/OFF on Test 2. Commits `cef2621` and
  `96671bb` remain inert/default OFF and are not efficacy evidence.
- **Verdict**: operator-canceled before exposure, neither promoted nor rejected.
  Preserve the frozen mechanism evidence below as historical design work, but
  do not arm the profile or execute its former pending deployment instructions.

- **Falsifiable hypothesis**: the broad deterministic credibility profile will
  improve Test 2's official same-configuration, same-role persuasion rating by
  (a) respecting direct current-round declines, (b) allowing a strict positive
  signal to overcome the static tight-prior block only after the seller has
  demonstrated selectivity and buyer-v2's existing posterior clears price, and
  (c) stopping known-low all-push recommendations only after observed demand
  has collapsed. It must improve the complete all-assignment profile without a
  material losing buyer, seller, or configuration subgroup. This is a named
  one-slot observational challenger, not a randomized or causal A/B test.
- **Exact deterministic profile and allocation**: pushed code commits `cef2621`
  and `96671bb` contain the default-OFF components. Physical slot `hardliner` /
  Test 2 alone is authorized for live V1=1, V2=1, V3=1,
  `GLEE_PERS_BUYER_SELECTIVE_SIGNAL_UNLOCK_V1=1`, and
  `GLEE_PERS_SELLER_DEMAND_COLLAPSE_TRUTH_V1=1`. V2/V3 only change BUY to PASS
  on strict current text declines. The unlock only changes a tight-prior PASS to
  BUY on a strict current positive after at least one prior strict decline and
  strict posterior EV above price. The seller repair only changes a known-low
  all-push YES to NO after nonempty cumulative buy rate falls below `.5`. None
  consult a game ID, randomized arm, opponent allowlist, or configuration-cell
  allowlist. Agent 5 is protected and remains byte-identical; Test 1/Test 3 are
  unchanged, Test 4 keeps its separate challenger, Test 4 truth/prose flags are
  not copied, and every persuasion `*_AB` key remains explicit zero.
- **Frozen buyer-decline evidence**: `[1787607608,1787661128.8]` contains 49,802
  buyer/text turns in 2,498 all-assigned games. On exact Test 2 control, V2 adds
  62 BUY-to-PASS changes in 25 games (61 observed LOW, zero HIGH, one unresolved
  quality). Incremental V3 is `eligible=fired=action_changed=66/66/66` in 39
  games, all 66 observed LOW and zero HIGH. Combined V2+V3 is 128 changes in 62
  games: 127 LOW, zero HIGH, one unresolved. Every V3 plan diff is an exact sole
  gate/marker BUY-to-PASS. This is action-selected mechanism evidence, not an
  official effect estimate.
- **Frozen buyer-unlock evidence**: Agent 5's complete buyer cohort
  `[1787607315,1787673787.5)` has 1,167 assignments and 23,340 contiguous turns.
  The exact unlock predicate reaches 1,120 turns in 216 assigned games. Exactly
  188 of those games have a result join and all 188 ended at zero; 28 lack a
  result join and remain unresolved even though their complete local traces are
  20/20 passes. The scope spans both message modes, both seller-knowledge states,
  every scale, priors `1/3` and `.5`, and ratios `1.2/1.25`; passed quality is
  never revealed, so prospective Test 2 play is required to learn the effect.
  The 1,120 control-path turns are not 1,120 identified live purchases: the
  first new purchase changes both revealed-quality history and seller response.
  Neighboring bought states show buyer-v2 probability optimism of roughly four
  to seven points, with the `p=1/3,r=1.2` diagnostic below breakeven. This is the
  principal harm risk and why the unlock cannot reach Agent 5 without the
  prospective official rule.
- **Frozen seller-repair evidence**: the Agent 5 seller cohort
  `[1787656144.0263646,1787673658.0]` retains all 287 assignments: 275 completed
  and 12 unresolved. The exact `<.5` rule reaches 150 known-low all-push turns
  in 21 games; 149 adjacent outcomes are observed, only 2/149 control low
  recommendations sold, and one remains unresolved. After first trigger the
  control also made 130 high recommendations with zero buys. Threshold checks
  at `.4/.5/.6` are stable, but whether a truthful low signal restores future
  trust is still unobserved; this is a prospective mechanism, not a fitted
  payoff claim.
- **Prospective cohort**: immediately before a clean future T0, freeze Test 2's
  authenticated persuasion rating/count, preceding 2,000 authenticated games,
  full overlay, non-persuasion overlay hash, every other slot overlay,
  `control.json`, arms mtime, PID/launch timestamp, and terminal proof for every
  persuasion game touched before T0. Enroll every Test 2 persuasion assignment
  whose first local turn is at or after T0, including both roles, buys, passes,
  positives, zeros, negative/severe outcomes, timeouts, unresolved games,
  immediate terminals, and all nonfires. Compare to the fixed Test 2 pre-period
  and contemporaneous unchanged Test 1/Test 3/Agent 5 streams; Test 4's distinct
  challenger is not a control. Aggregate movement alone is not component-causal.
- **Mechanism audit / immediate stop**: exact replay every firing until each new
  gate has 20 clean events. V2/V3 require buyer/player-2 text, control BUY, live
  PASS, and exactly one V2/V3 gate. The unlock requires buyer/player-2,
  buyer-v2, strict current positive, a prior strict decline, control tight-prior
  PASS, posterior EV strictly above price, live BUY, and the unlock as sole new
  gate. Seller repair requires seller/player-1, known LOW, prior EV at least
  price, nonempty history, buy rate `<.5`, control YES, live NO, and its sole
  gate. Every wire must be legal/heuristic and every nonfire byte-identical.
  Scope drift, game-ID dependence, history-only/positive decline veto, negative
  unlock, PASS-to-BUY outside the exact proof, HIGH seller decline, multi-gate
  overlap, illegal wire, unexplained plan delta, strategy error, or attributable
  timeout is immediate rejection. Set the failing addition explicitly zero on
  Test 2 with fleet tooling; reject/disarm all four additions if isolation is
  lost. Never clear, restart, signal, or force-cycle a process.
- **Precommitted reads**: the harm look is 500 fully authenticated post-T0 games
  with zero missing/unresolved joins, at least five V2/V3-affected games, 20
  independently unlock-affected games, and five independently seller-repair
  games. Reject for a wholly negative official Test2-minus-pre trend interval,
  any mechanism failure, or either role below zero together with at least a
  `.5` rating/game loss. The final read is 2,000 authenticated games with zero
  missing/unresolved joins, at least 20 V2/V3, 100 unlock, and 20 seller-repair
  affected games, a positive official overall trend interval, nonnegative buyer
  and seller point estimates, and no `n>=100` role x message-mode x prior slice
  losing `.5` rating/game or more. Current authenticated per-game joins are
  unavailable, so display movement, raw payoff, and local percentile cannot
  trigger promotion. Anything short remains Test-2-only; Agent 5 promotion
  requires the full official final rule and a fresh protected-agent boundary.
- **Verification / current load boundary**: focused new-mechanism tests pass
  `112/112`; all persuasion tests pass `533/533`. Exact Test 2 reachability over
  800 paired games is buyer unlock `272/272/272` and seller repair `346/346/346`.
  The full suite is `2498 passed, 3 failed`; the three failures are the declared
  bargaining horizon assertion plus bargaining/negotiation live-grid drift
  alarms. Test 2 naturally replaced PID `15302` with PID `58430` at 21:54:23
  IST, but that launch preceded code commit `96671bb` by about two minutes and
  cannot contain the new repairs. Do not arm it. Wait for a later natural
  successor containing both commits and for zero in-flight persuasion games;
  never force or accelerate the boundary.

## OPERATOR-TERMINATED, NO EFFICACY VERDICT — Test 4 strict-edge challenger (25 Aug)

- Test 4's V2, zero-margin truth, and p=.8 positive-prose additions were set
  from `1` to explicit `0` through `scripts/fleet.py` at
  `Tcfg=1787680787`, immediately after PID `60650` naturally drained cleanly
  and before replacement PID `70598` launched. Test 4 now has Agent 5-identical
  effective persuasion behavior; Test 2 was already identical and Agent 5
  remained banked and untouched.
- The prior complete Test 4 cohort and clean mechanism audit remain retained.
  Authenticated per-game joins were unavailable and the observed display
  movement was inside the measured roughly +/-125 identical-agent noise band.
  This operator topology change therefore supplies no causal promotion or
  rejection verdict for any of the three components.

## BUILT DEFAULT OFF — complete-info unknown-horizon late stasis (25 Aug)

- **Flag / state**: pushed commit `4a15244` contains
  `GLEE_NEGO_COMPLETE_UNKNOWN_LATE_STASIS_V1`, deterministic, default OFF, live
  nowhere. There is no hash, randomizer, or cell allocation.
- **All-outcome motivation**: 66 eligible clean games comprise 61 terminal
  outcomes (44 agreements, 17 no-deals) and five unresolved. The post-hoc
  round-75 / ten-completed-mutual-cycle fence reached 17/17 terminal no-deals,
  0/44 agreements, and one unresolved game. Terminal diagnostic lift is
  `+.03062` exact percentile; the maximally adverse unresolved bound is
  `-.01553`. Repeat-3 and repeat-10 alternatives were negative and remain off.
- **Mechanism**: only a baseline wire-coerced `RejectOffer` can become
  `AcceptOffer`; the visible offer must be strictly profitable in a feasible
  complete-information game with an explicitly unknown horizon, at round 75 or
  later, following ten complete and consecutive P→Reject/C, C→Reject/P cycles.
  The current provisional counter does not count as a cycle.
- **Verification**: exact Test 4/composite and Test 3/conceder stacks each pass
  reachability `4914/4914/4914` over 800 paired games. Focused 38/38 and all
  negotiation 585/585 tests pass. Full suite is 1,861 passed with only the
  three pre-existing live-machine failures.
- **Decision rule**: do not deploy while any unresolved outcome can reverse the
  sign. If those outcomes finalize and the complete all-outcome evidence stays
  positive, freeze a prospective one-challenger deterministic design before a
  natural boundary; retain every enrolled negotiation game, not only guard
  fires. Any source/wire/parser error is an immediate explicit-zero revert. No
  change is authorized for Test 2.

## RUNNING — deterministic bargaining high-share delay guard (25 Aug)

- **Flag / allocation**: `GLEE_BARG_HIGH_SHARE_DELAY_GUARD`, deterministic and
  default OFF in source. It is live on Agent 5 / slot `composite` only, stacked on
  `GLEE_BARG_DISCOUNT_NO_REGRESS=1`. Test 1, Test 2, Test 3, and Test 4 are
  explicit zero. There is no game-id hash, A/B arm, or configuration-cell
  assignment. Test 2 remains the exact 2586 high-water stack.
- **Action**: after every earlier policy still says Reject, accept only a
  positive standing offer in `[.45,.50)` when our delta is below one, more than
  two rounds remain, three finite provenance-checked opponent offers include
  the standing offer, it has not retreated from their prior high-water, the
  trail concession rate is below the pinned `.05` prior, and both the measured
  observed-gain floor and ordinary discounted continuation clear the offer.
  The gate is pinned to `ACCEPT_FLOOR=.50/FLOOR_GAIN=.05` and fails closed if
  legacy observed gain, a hash/nominal reject guard, stonewall, econ-stall, or
  opponent exploitation is armed.
- **Evidence / caveat**: frozen first-trigger replay is `35/0` exact wins plus
  four unresolved; mean exact payoff-share alternative `+.10547`, maximally
  adverse all-missing bound `+.05857` with 95% CI `[+.00746,+.10968]`.
  The broad parent treatment remains three-seed arena-negative and its
  sub-`.35` live subset is negative. The cutoff is post-hoc, so this is a
  deterministic single-profile challenger, not a proven promotion.
- **Verification**: pushed commit `aa6485a`; focused guard/no-regress tests
  `69/69`; bargaining suite `216` passes plus only the declared stale
  450-vs-468 assertion; full suite `1,837` passes with exactly the two declared
  bargaining failures. Agent 5 exact-stack reachability is
  `130 eligible / 130 fired / 130 action_changed` over 2,400 paired games. A
  fresh pre-deployment replay on the actual 04:06 Agent 5 overlay and hardliner
  wrapper passed `38/38/38` over 800 paired games on current HEAD `8a028dd`.
- **Deployment boundary**: the supervisor recorded `composite cycled with zero
  games abandoned` at 04:06:28 IST and launched replacement PID `48295` at
  04:06:38 with `--probe hardliner`, all three families, LLM off, and code newer
  than `aa6485a`. Fleet tooling then set the single deterministic overlay at
  `Tcfg=1787611031` (04:07:11); runtime lookup resolves the flag to `1` and all
  overlapping release/exploit flags to zero. The other four slots remain
  explicit zero. The last official snapshot before activation was
  `1787610964`: Agent 5 overall `2220.76`, bargaining `2122.69`, negotiation
  `2060.42`, and persuasion `2471.17`.
- **Cohort / falsifiable safety rule**: include only Agent 5 games whose first
  logged turn is at or after `1787611035`, so games opened during the 33-second
  launch-to-overlay interval cannot leak into the read. Three observed
  cross-boundary game IDs (one bargaining, two persuasion) are therefore
  excluded even though they completed after Tcfg. Retain every enrolled game,
  including non-triggers, both roles, all configuration cells, zeros, no-deals,
  and unresolved outcomes; defer the formal read while any cohort outcome is
  unresolved. At 200 fully joined post-boundary bargaining games, compare the
  all-outcome same-cell/role percentile with the immediately preceding 200
  Agent 5 games. Revert on any strategy/wire/parser failure. Otherwise this is
  an observational profile safety read, not causal evidence: do not copy it to
  another agent or alter protected Test 2 unless the overall point estimate is
  nonnegative and no role/cell with at least 20 games falls by `.05` percentile
  or more.
- **05:17 checkpoint — no decision**: 142 bargaining games are enrolled, with
  137 locally joined outcomes and five retained unresolved.  The joined set has
  zero no-deals, exact zeros, or strategy/wire/parser failures, and covers both
  roles and every coarse role x horizon x message cell.  Eleven eligible
  game-turns fired, all eleven changed to exact accept wires, and no malformed
  source/action record appeared.  Official bargaining moved
  `2122.69/12619 -> 2204.31/12760` after activation, but that movement is an
  observational safety signal, not the frozen comparison.  Do not read the
  preceding-200 control or make a live change before 200 joined outcomes and
  zero unresolved enrolled games.
- **05:39 checkpoint — still blocked**: 195 bargaining games are enrolled,
  with 155 locally joined outcomes and 40 retained unresolved.  The joined set
  remains all agreements with zero exact zeros, no-deals, or mechanism errors;
  the full enrolled cohort is Alice/Bob `98/97` and covers every coarse role x
  horizon x message cell.  Fifteen eligible game-turns all fired and submitted
  exact accept wires.  Official bargaining is `+99.65` after activation, but
  this is still observational and the frozen 200-joined/zero-unresolved gate is
  not met.  The preceding-200 comparison was deliberately not inspected.

## WATCH — deterministic negotiation leader replica on Test 4 (25 Aug)

- **Completed clean shift**: PID `37202`, `T0=1787607037` through natural drain
  `T1=1787610923`, had 155/155 negotiation games terminal and zero unresolved,
  strategy, or wire failures. Every outcome is retained: 74 agreements, 53
  no-deals, 28 walks, and 81 exact zeros; buyer/seller are 79/76 and all six
  information x horizon cells are represented.
- **Movement / mechanism**: raw official negotiation rating/count moved
  `2115.13/6709 -> 2049.57/6858` (`-65.56`). The replica stamped all 586 buyer
  turns across all 79 buyer games; its seller-message gate fired 159 turns in
  36 seller games, with no source miss. All-outcome fitted same-cell percentile
  was `.49710`, 95% CI `[.45704,.53715]`; complete-information unknown horizon
  was the weakest observed cell at `.3755` on only 14 games.
- **Why no rollback yet**: the immediately preceding same-size aggregate window
  gained `+62.11` while running essentially the same intended behavior, and 93
  of its 155 local outcomes remain unresolved. That sign flip plus the current
  cohort interval spanning `.50` makes an explicit-zero revert observationally
  underidentified. Test 4 remains a non-leading deterministic challenger and
  keeps the portfolio diverse.
- **Frozen next-shift rule**: join every next-shift negotiation game and its
  authenticated official delta by game ID, retaining zeros, no-deals, walks,
  both roles, all cells, and unresolved records. Revert immediately on any
  source/wire/strategy failure. Otherwise revert only if zero outcomes remain
  unresolved and either official per-game mean 95% CI is wholly negative, or a
  second full shift loses at least 40 displayed negotiation rating while its
  all-outcome fitted-percentile upper 95% bound is below `.50`. Do not select
  agreements or gate-fired games.
- **Second-shift verdict — KEEP (05:10 drain)**: PID `48235` completed 132/132
  negotiation games with zero unresolved or source/wire/strategy failures: 63
  agreements, 44 no-deals, 24 walks, one opponent-side invalid-moves result,
  and 69 exact zeros.  All-outcome fitted same-cell percentile was `.49568`,
  95% CI `[.44904,.54233]`, and authenticated displayed negotiation moved
  `2049.57/6858 -> 2081.00/6987` (`+31.43`) over the 129 posted games.  Neither
  frozen rollback clause fires.  The weakest descriptive slice is
  complete-information / unknown-horizon seller at `.23391`, `n=5`; preserve
  it as a hypothesis target rather than changing policy from a thin slice.
- **Current-shift watch (05:44)**: PID `55554` has 82 negotiation enrollments,
  only 28 local finals, and 54 retained unresolved.  The 28 finals include 13
  agreements, eight no-deals, seven walks, and 15 exact zeros; buyer/seller are
  both represented.  All 2,563 post-boundary action turns use the intended
  heuristic source with zero source/strategy errors or malformed wires.
  Displayed negotiation moved `2081.00/6987 -> 2058.36/7045` (`-22.64`), so it
  has not reached the frozen `-40` threshold.  Do not use the resolved-only
  `.44982` fitted percentile while 54 outcomes are unresolved; no rollback
  clause currently fires.

## RUNNING

### First-principles terminal cells (negotiation, Test 4)
- **Hypothesis**: in cells where our seat owns the final offer, bypassing every
  downstream price rewriter and leaving the counterparty one positive cent
  improves same-cell percentile.
- **Design**: 50/50 per-game hash arm, `sha256("nego_fp|" + game_id) & 1`, on
  Test 4.  Corrected cohort starts at timestamp `1787534215` after commit
  `f32c334`; do not mix earlier games into this read.
- **Corrected ITT status (2026-08-24 ~14:15 IST)**: the earlier result-only
  analysis is not promotion-grade because the separate outcome collector
  stopped at 06:00 with 11,737 games outstanding.  The supervisor kills a
  process only after the server reports `active_games=0`, but may do so while
  `GameLog.finalize()` is still fetching results; a missing local final is
  therefore not an identified server abandonment.  The complete first-turn
  cohort has only 18 locally recovered outcomes and 64 unresolved.  Do not
  impute the 64 as `.05`, and do not select the 18 as if complete.
- **Read with**: `scripts/live_percentile.py --ab fp-complete --since
  1787534215 --slots randomized`.  It cohorts before action, leaves cold/fresh
  missing finals unresolved, and uses the checked-in exact 1,152-cell official
  seed CDF rather than the hidden-value-pooled local model.
- **Decision rule**: do not promote while any outcome is unresolved or either
  cell's official-score CI crosses zero. `GLEE_NEGO_FP_COMPLETE_ONLY` remains a
  default-off mechanism switch, not a deployment recommendation. Any larger
  terminal crumb is a separate experiment.
- **Verdict**: promotion withdrawn; complete-info and hidden both pending.

## DISABLED / INVALID — NOT LIVE

### Surplus-share response probe (negotiation, complete-info)
- **Hypothesis**: our complete-info closes sit at the 49.4% attractor; the
  causal frontier P(accept | surplus share x) may peak above it.
- **Design**: randomise x over {0.50,0.55,0.60,0.65,0.70,0.75} in complete-info
  offer turns, seeded on game id, stratified by seat/round-block/cap.
- **Live on**: nowhere; `GLEE_NEGO_SURPLUS_PROBE=0` on all five slots.
- **Read with**: `scripts/analyze_surplus_probe.py`
- **Decision rule**: pick the x maximising P(accept)*x plus continuation, NOT
  the highest observed rating-by-band (that conditions on deals happening).
- **Verdict**: invalid as run. Assignment leaked into the accept/reject target,
  and its analyzer joined the wrong response turn. Do not restore this design.

### Seller-message parser v2 (persuasion)
- **Hypothesis**: the decline table missed "not recommended" and friends, so we
  bought messages that explicitly declined. 373 such purchases in 20h of logs,
  373 low quality, 0 high.
- **Live on**: nowhere; the flag is absent from all five live arm stacks.
- **Verdict**: historical candidate only, not a running experiment. The newer
  tri-state parser is a separate default-off mechanism.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden unknown-horizon first-offer greed probe (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HI_UNCAPPED_FIRST_OFFER_AB=1`;
  `sha256("nego_hi_uncapped_first_offer_v1|" + game_id) % 3`, yielding
  `control`, `share80`, or `share95`.
- **Why this cell**: Test 2's latest 100 official dashboard results put hidden
  unknown-horizon games at `-1.604` rating/game (n=27), versus `-0.189` in
  hidden cap-10 and `+0.489` in hidden single-round. This is the only horizon
  the arm can change.
- **Candidate**: only the two own types with exactly one feasible counterpart
  are eligible: seller 1.2B (only buyer 1.5B can trade) and buyer 1.0B (only
  seller .8B can trade). On the first outgoing price, share80 uses 1.44B/.84B
  and share95 uses 1.485B/.81B respectively. Every later price and every
  accept/reject/walk decision is current control.
- **Why narrower**: the rejected ladder bundled greed, support ordering, and a
  four-offer hold. This trial isolates multi-round greed elasticity without
  assuming a rejected crumb reveals type or causes the opponent to wait through
  a deterministic concession schedule.
- **Primary cohort / rule**: every matching first turn before action, including
  buyers that immediately accept and never emit a price; retain all no-deals,
  walks, timeouts, and unresolved outcomes. Compare each greed arm with control
  and share95 with share80. Promotion requires official per-game score 95% CI
  above zero, close-rate lower bound above -2pp, zero wire failures, and no
  material role/scale sign reversal. Conditional deal share is diagnostic only.
- **Live on / boundary**: Test 1 (`champion`), Agent 5 (`composite`), and Test 4
  (`randomized`), all cleanly on pushed code by `T0=1787567218` (2026-08-24
  15:56:58 IST). Test 2 is protected pending evidence; Test 3 is untouched.
- **Read with**: `scripts/live_percentile.py --ab hi-first-offer --since
  1787567218 --slots champion,composite,randomized`. It labels its
  hidden-value-pooled metric diagnostic and never emits a promotion verdict.
- **Reachability / first wire evidence**: Test 2's latest 20,000-turn shadow had
  47 eligible, 35 candidate-fired, and 35 changed actions. Before the common
  boundary, Test 4 emitted exact share95 wires at 1.485B and .81B and Agent 5
  emitted a hash control, all with `wire_ok=true`. The runtime refuses to
  activate if `HIDDEN_POLICY_V1` or `HIDDEN_FLOOR` is armed.
- **Early common-cohort read (2026-08-24 ~16:17 IST)**: 12 assigned, 7 resolved,
  5 unresolved, zero agreements among the seven resolved, zero wire failures.
  Local diagnostic percentile: control .4028 (n=1), share80 .4028 (n=1),
  share95 .3852 (n=5). No inference: each eligible own type has only 25% structural
  feasibility, and the first counteroffers sat far outside our reservation
  values. Continue to the precommitted sample/rule; do not react to this draw.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden cap-10 buyer-1.2 terminal counter (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HI_CAP10_BUYER12_TERMINAL_AB=1`;
  `sha256("nego_hi_cap10_buyer12_terminal_v1|" + game_id) & 1`.
- **Candidate**: on the round-9 buyer rejection/counter only, replace the
  terminal counter with `base+$0.01`.  Control and every noneligible action are
  unchanged.
- **Primary cohort**: every matching game from its first buyer decision, not
  only games that reach round 9.  Include all terminal outcomes and block while
  any assigned outcome is unresolved.
- **Decision rule, frozen before the first official outcome join**: fixed final
  read at 100 resolved official games per arm and at least 10 per arm in every
  scale x message cell. Promote only if official per-game score delta 95% CI is
  above zero; close-rate point estimate is positive with lower 95% bound above
  -2pp; scale and message point estimates are all nonnegative; every fired wire
  is exactly `base+$0.01`; and mechanism/join/outcome failures are zero. One
  harm look at 30 official games per arm rejects if the official CI is wholly
  negative. Reject immediately on any mechanism failure. This prospective
  clarification was made after local diagnostic outcomes were visible but
  before harvesting any official terminal-arm records; it prevents repeated
  official-score peeking.
- **Read with**: `scripts/live_percentile.py --ab hi-terminal --since T0
  --until T1 --official-json FILE`. The reader now joins authenticated official
  rating deltas, retains the all-assigned ITT and unresolved outcomes, audits
  exact terminal wires, excludes cross-fleet duplicates, and enforces the fixed
  rule above. Its local hidden-value-pooled percentile remains diagnostic.
- **Reachability**: 57 eligible / 20 fired / 20 changed on 3,000 paired games.
- **Live on / boundary**: Test 1 (`champion`), Agent 5 (`composite`), and Test 4
  (`randomized`) from the clean common boundary `T0=1787568551` (2026-08-24
  16:19:11 IST). Test 2 and Test 3 are unarmed. The first-offer probe is
  disjoint because it requires an unknown horizon; Test 4's first-principles
  module does not own hidden cap-10 buyer cells.
- **Exact-stack preflight**: champion's live stack produced 19 eligible, 10
  fired, and 10 changed wires in 1,000 paired games (seed 1701), including
  literal `B+$0.01` at 100, 10,000, and 1,000,000 scales. The existing 3,000
  paired check remains the higher-sample reachability result above.

Do not co-arm this experiment with `GLEE_NEGO_HIDDEN_POLICY_V1` in its first
measurement. Codex owns deployment under the operator's 2026-08-24 directive.

## STOPPED BY OPERATOR — NO CAUSAL VERDICT

### Broad direct-leader hidden cap-10 buyer trajectory
- **Flag / assignment**: `GLEE_NEGO_HI_CAP10_BUYER_CURVE_AB=1`;
  `sha256("nego_hi_cap10_buyer_curve_v1|" + game_id) & 1`.
- **Why this replaces the slow loop**: the posted 63-game official window was
  `-24.4` on the buyer side and `+47.9` on the seller side; buyer no-deals alone
  contributed `-22.5`. The old terminal-only arm reaches one own type on one
  counter. This arm covers every hidden cap-10 buyer with own type
  `1.0B/1.2B/1.5B`, approximately 9% of negotiation games, and changes the first
  four price opportunities while leaving terminal price, AcceptOffer, and
  WalkAway byte-identical.
- **Candidate**: the frozen fraction-of-own-value early curve
  `[.6786404167,.6788316667,.6838475000,.7167462500]`. It is the first-four
  pointwise midpoint of two completed, type-identified Clod buyer-`1.2B` paths;
  both later ended at exactly `1.008B`, but that terminal is not copied. Scaling
  the early curve to buyer `1.0B/1.5B` is part of the treatment: matching
  `.677B/1.015B` literal opening families exist in direct top-agent traces, but
  their hidden private types are not identified in no-deals.
- **Isolation**: the mechanism fails closed if the old buyer-1.2 terminal arm,
  HIDDEN_POLICY, HIDDEN_FLOOR, HIDDEN_MIN_SHARE_VETO, TABLE_VCONT_PRECEDENCE,
  STALL_CURRENT_BREAK, CLOSE_AB, or PROBE_V1 is armed. Unknown-horizon opening
  probes are disjoint. Hash controls return before any later hidden-price writer
  and keep the current wire byte-for-byte.
- **Cohort / reader**: every matching game from its first buyer decision before
  action, including immediate accepts and games that never emit a candidate
  price. Read with `scripts/live_percentile.py --ab hi-buyer-curve --since T0
  --slots SLOTS --official-json FILE`. It audits every candidate counter against
  the frozen four-point early curve, retains unresolved/all outcomes, and removes
  cross-fleet duplicate IDs.
- **Frozen decision rule before deployment**: one harm look at 30 official
  games/arm rejects if either official-score or close-rate CI is wholly
  negative. Final read at 100 official games/arm and at least 15/arm per own
  type. Promote only if official-delta 95% CI is above zero, close lower CI is
  above -2pp, every own-type point is nonnegative, no scale/message point is
  `<=-1` rating/game, and wire/join/outcome failures are zero.
- **Verification**: exact intended-stack reachability over 1,500 paired games,
  seed 2601, produced 549 eligible states / 227 fired / 227 changed wire
  actions. Focused arm/terminal/opening tests are 125/125;
  negotiation/action/reader tests are 530/530. Before deployment the default-OFF
  flag left behavior unchanged. Full suite: 1,269 passed with only the two
  predeclared bargaining failures; no bargaining behavior or configuration
  changed.
- **Live boundary / stop**: briefly enabled on Test 1 (`champion`), Test 3
  (`conceder`), Test 4 (`randomized`), and Agent 5 (`composite`) at
  `T0=1787584628` (2026-08-24 20:47:08 IST), then explicitly set back to `0`
  on all four at the operator's direction before a meaningful sample arrived.
  Do not interpret this as a positive or negative result.

## STOPPED — FIXED CHECKPOINT FAILED PROMOTION

### Top-four/five observable negotiation behavior, buyer only
- **Flag / assignment**: `GLEE_NEGO_TOP_BUYER_CLONE_AB=1`; SHA-256 of
  `nego_top_buyer_clone_v1|<game_id>`, low bit 1 = candidate. Default OFF.
- **Target / prospective host amendment**: Test 3 (`conceder`) began alone.
  Before inspecting any treatment outcome, the slow arrival rate (four buyer
  assignments in five minutes) prospectively expanded the same arm to Test 1
  (`champion`), Test 4 (`randomized`), and Agent 5 (`composite`). Test 2 remains
  untouched. The added hosts explicitly disabled the four older hidden-buyer
  imitation probes and `NEGO_FIRST_PRINCIPLES` before their clean common T0;
  analyse host-specific randomisation first, then pool. Seller behavior and
  every bargaining action/configuration remain byte-for-byte control.
- **Why buyer only**: the operator's 63-game official window had sellers
  `+47.9` but buyers `-24.4`; buyer no-deals were `-22.5`. Replacing the winning
  seller half would add risk with no diagnosis supporting it.
- **Candidate**: copy the wire behavior identified across 70 games from
  7aidara, Alpha, Beta, and Gamma. All four labels share the same exact complete
  buyer zone path: claim `[.960,.898,.836,.774,.774]` in cap-10 and end at
  `.712` in unknown horizons. Hidden buyer paths are literal price/base tables
  by own type, including buyer 1.5
  `[.905,.905,1.075,1.075,1.245×4]`. Mapping the three hidden path classes
  whose private payoff was not revealed to monotone own types is the explicit
  randomized hypothesis. Any-positive terminal acceptance and Athena's
  observed ninth-decision hidden-uncapped walk remain state-specific. Gill
  bates and Mythos01 do not yet have enough complete local buyer transcripts to
  identify a competing path. This is an exact behavioral clone where wire
  moves are observed; it is not a claim to possess competitors' private source.
  In message-enabled games every rejected buyer counter copies 7aidara's exact
  observed sentence, `Above what I can justify. Here is where I can go.`; it is
  quality-neutral and does not reveal the private type or final hold.
- **Control**: each host's entire frozen current stack at its T0, selected by
  the opposite hash bit. The treatment owns both offer and acceptance policy so
  downstream gates cannot silently rewrite half the mechanism. Host is a
  predeclared stratum and each host point estimate must be nonnegative before
  promotion.
- **Primary outcome**: official per-game negotiation percentile/rating change,
  candidate minus contemporaneous hash control, buyer games only. Report hidden
  type, complete-information status, horizon status, terminal outcome, and
  opponent separately; never condition the estimate on agreement.
- **Emergency stop**: after at least 10 scored buyer games per arm, stop if the
  candidate is at least `-1.0 rating/game` below control or candidate live-game
  no-deal rate is 15 percentage points higher. Three consecutive candidate
  losses of `-6` or worse also stop immediately.
- **Promote**: at least 30 scored buyer games per arm; authenticated dashboard
  rating-delta point difference positive; contemporaneous same-cell percentile
  difference at least `+0.03` with its 95% interval above `-0.01`; no-deal rate
  no more than 5 percentage points worse; every assigned outcome/official join
  resolved; and zero wire, source, control-contamination, or duplicate failures.
  The local percentile is only a concurrent arm comparison, never an estimate
  of leaderboard rank. A 30-game harm read is not proof of the 0.55 target.
- **Reader**: run `scripts/live_percentile.py --ab top-buyer-clone --since T0
  --slots SLOT --official-json FILE` separately for each host at its boundary;
  the prospective pooled added-host read may use
  `--since 1787591092.200761 --slots champion,randomized,composite`. It cohorts
  before the first buyer
  action, audits every candidate wire and exact message against the production
  table, requires `plan.source=top_buyer_clone`, detects clone source in hash
  controls, keeps all unresolved/no-deal/walk outcomes, excludes duplicate game
  ids, and enforces the emergency and promotion gates by exit status.
- **Verification**: combined clone/reader tests 22/22; all negotiation/reader
  tests 574/574 after the exact-message extension;
  intended Test 3 stack reachability over 1,000 simulated games yielded 3,827
  eligible / 1,575 fired / 1,575 changed wire actions. Full suite 1,291 passed
  with only the two predeclared bargaining failures.
- **Deployment state / causal boundaries**: Test 3 drained cleanly and launched
  the final clone build at `T0=1787590698` (22:28:18 IST); its first exact
  `plan.source=top_buyer_clone` buyer trace was game
  `66e4b705-9a53-415c-861b-ba9c1c4e858e` at `1787590787.720265`. Before any
  treatment outcome was inspected, Test 1, Test 4, and Agent 5 were armed at the
  clean common `T0=1787591092.200761` (22:34:52 IST). Exact source traces then
  appeared on all three hosts at `1787591160.391535`, `1787591149.522183`, and
  `1787591136.825958`, respectively; their preceding post-T0 buyer games were
  verified hash controls. An inherited revoked stdin descriptor initially made
  supervised relaunches fail before Python imported strategy code; commit
  `816cd31` fixes future launches with explicit `DEVNULL`, and the replacement
  supervisor adopted every still-running game process without disturbing it.
- **First official ITT checkpoint (22:40--22:49 capture plus the immediately
  preceding joined slice)**: 20 candidate buyer games scored `+24.8` in total
  (`+1.240/game`, median `+0.55`) versus 25 hash controls scoring `-14.3`
  (`-0.572/game`, median `-0.70`), an official-rating point lift of
  `+1.812/game`. The approximate Welch 95% interval is `[-0.39,+4.02]`, so
  this is encouraging evidence, not a promotion verdict. Host point lifts are
  champion `+4.55` (4 candidate / 1 control), randomized `+6.87` (6/6),
  conceder `+0.85` (4/11), and composite `-1.13` (6/7). The precommitted
  emergency harm rule does not fire, but the every-host promotion condition
  currently fails on composite and neither arm has 30 scored games. Keep the
  randomized arm running; do not deploy the candidate fleet-wide yet.
- **Join-selection audit**: the strict live-turn join initially matched 22 of
  36 new buyer dashboard rows. The other 14 were not discarded: each was
  mapped to a unique local game by exact host, dashboard minute, public setup,
  incoming price, submitted decision/counter, and clone/control source. Adding
  them reduced the apparent lift from `+2.51` to `+1.81/game`, demonstrating why
  resolved/matched-only reporting is forbidden. The evaluator omitted
  `state.last_offer` when `history` was empty on first incoming decisions; that
  fail-closed join bug is being repaired with a regression test. Rating and
  payoff were never used as join keys.
- **Fixed 91-game official checkpoint / verdict (through 23:06 IST)**: all 91
  scored buyer rows have unique game ids and are retained. Candidate is 44
  games / `+49.1` total / `+1.116/game`; control is 47 / `+11.6` /
  `+0.247/game`, for a point lift of `+0.869/game`. The approximate Welch 95%
  interval is `[-0.78,+2.52]`. Candidate no-deals are 29.55% versus 23.40%
  (`+6.14pp`), and Agent 5/composite is negative (`-0.648/game`) while the
  other three host points are positive. The broad arm therefore fails its
  precommitted interval, no-deal, and every-host promotion gates. It is not a
  proven percentile winner and must not be promoted fleet-wide.
- **Stop boundary**: fleet tooling set only
  `GLEE_NEGO_TOP_BUYER_CLONE_AB=0` on champion, composite, conceder, and
  randomized at `T1=1787593429` (23:13:49 IST). The running processes re-read
  this overlay within three seconds; no process, active game, seller policy,
  bargaining action, or bargaining flag was changed. Any later-resolving game
  remains part of archival ITT completeness but cannot reverse this frozen
  decision or justify reviving the broad arm.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden-information cap-10 buyer leader clone
- **Why this is a new experiment**: the broad checkpoint's hidden cap-10 slice
  was candidate `+1.573/game` (n=15) versus control `-0.236/game` (n=11), a
  `+1.809/game` point lift, with no-deals 46.7% versus 54.5%. All four observed
  own-type points were nonnegative. This cell was selected after inspecting
  the broad result, so it is only a hypothesis generator and cannot be called a
  win. A new salt and fresh T0 are mandatory.
- **Flag / assignment**:
  `GLEE_NEGO_TOP_BUYER_CLONE_HI_CAP10_AB`, default OFF;
  `sha256("nego_top_buyer_clone_hi_cap10_v1|" + game_id)` low bit assigns the
  candidate. Missing ids fail closed. If the broad, Opus, or Athena clone is
  armed, both overlapping mechanisms fail closed.
- **Eligibility / action**: negotiation buyer seat only,
  `complete_information=false`, `horizon_known=true`, and exactly ten rounds,
  from the first buyer action before outcome or opponent identity is known.
  Candidate executes the already-frozen literal 7aidara hidden buyer path,
  acceptance boundary, terminal any-positive rule, and exact generic counter
  message. Hash control executes the complete current stack byte-for-byte.
  Seller, complete-information, one-round, unknown-horizon, and bargaining
  actions are ineligible.
- **Cohort / primary outcome**: retain every assigned game, including immediate
  accepts, agreements, no-deals, walks, timeouts, invalids, abandoned games,
  unresolved outcomes, and games whose candidate never emits a counter.
  Primary is authenticated official per-game rating delta, candidate minus
  contemporaneous hash control, stratified by host before pooling. Concurrent
  exact-cell percentile is a required diagnostic, not a substitute for the
  official score.
- **Frozen decision rule before activation**: one harm look at 20 scored games
  per arm stops if candidate is at least `-1.0 rating/game` below control, its
  official 95% interval is wholly negative, or no-deals are at least 10pp worse.
  Final read at 40 scored official games per arm, at least 5/arm on every
  deployed host and every own type, and at least 8/arm in each message mode.
  Promote only if the official-score 95% interval is wholly positive; exact-cell
  percentile point lift is at least `+0.03` with lower 95% bound above `-0.01`;
  candidate no-deal rate is no more than 5pp worse; every host, own-type,
  message, and scale point estimate is nonnegative; and source, wire, assignment,
  duplicate, outcome, and official-join failures are all zero. Otherwise leave
  it research-only. No optional or post-trigger subset can promote it.
- **Deployment boundary / verification so far**: live on conceder from
  `T0=1787594802` (23:36:42 IST), randomized from `T0=1787594943` (23:39:03),
  champion from `T0=1787595144` (23:42:24), and composite from
  `T0=1787595205` (23:43:25). Each T0 is the natural-shift replacement launch
  on pushed commit `64ec557`, with the broad flag explicitly zero and this
  scoped flag one in the launch record. Hardliner remains protected and
  unarmed. The first prospective candidate wire fired on conceder game
  `cdd59547-0b66-4416-94b0-8f2877159e90` at `1787594922.983`; its independent
  hash assignment is candidate and its exact scope is hidden/known/cap-10
  buyer. This proves deployment and reachability, not outcome superiority.
  Exact champion-stack reachability over 800 paired games produced 335 eligible
  states, 164 firings, and 164 changed wires. Focused strategy tests pass 37/37;
  the prospective reader encodes the 20/arm harm and complete 40/arm promotion
  rules, preserves every unresolved/non-close, audits all candidate/control
  wires and collisions, and reports host/type/message/scale strata; combined
  clone-reader tests pass 43/43. Full suite: 1,476 passed with only the same two
  pre-existing bargaining failures. Never restart or alter bargaining to
  accelerate deployment.
- **Prospective official checkpoint / continue (00:05 IST)**: two independently
  captured dashboard windows join 25/25 exact scoped games to unique local game
  ids, with zero unresolved or ambiguous rows. Candidate is 9 games / `+22.2`
  total / `+2.467/game`; control is 16 / `+17.6` / `+1.100/game`, for an
  unstratified lift of `+1.367/game` and host-fixed-effect lift of
  `+1.535/game`. The exact host-stratified sharp-null randomization test is
  one-sided `p=.1056` (50,400 assignments). Conceder, randomized, and champion
  host points are positive; composite remains `-1.900/game` on only one
  candidate versus three controls. This is the first positive prospective
  official signal, but it is not promotion evidence: neither arm has reached
  the frozen 20/arm harm look, the interval still crosses zero, and the
  every-host condition fails. Keep the arm randomized without policy changes.
  Frozen raw/join artifacts are
  `.ai/NEGOTIATION_OFFICIAL_{RAW_,}SCOPED_CLONE_2336_2353.json` and
  `.ai/NEGOTIATION_OFFICIAL_{RAW_,}SCOPED_CLONE_2352_0005.json`; the latter
  intentionally overlaps one previously captured game, and all analysis
  deduplicates by the exact joined game id.

### Opus hidden unknown-horizon buyer trajectory clone — BUILT DEFAULT OFF
- **New falsifiable experiment**: copy Opus's directly observed hidden
  unknown-horizon buyer trajectory for live buyer types `1.0B`, `1.2B`, and
  `1.5B`. The null is official candidate-control rating delta `<=0`. This is
  not a retry of the broad 7aidara hidden-unknown slice (`-0.321/game`, n=11/15):
  Opus holds near `0.6767 * own_value` and follows 43 literal observed
  coefficients, whereas 7aidara used four different piecewise price/base paths.
- **Flag / independent assignment**:
  `GLEE_NEGO_TOP_OPUS_BUYER_CLONE_HI_UNKNOWN_AB`, default OFF;
  `sha256("nego_top_opus_buyer_clone_hi_unknown_v1|" + game_id)` low bit gives
  candidate. Missing ids fail closed. This salt has never been armed or used to
  select an outcome.
- **Static ITT scope**: negotiation buyer only, hidden information,
  `horizon_known=false`, `max_rounds` absent, and own type in
  `{1.0B,1.2B,1.5B}`, from the first eligible pre-action turn. The structurally
  dead `.8B` buyer type is excluded before assignment because no individually
  rational seller can leave it positive surplus. Known-cap-10, one-round,
  complete-information, seller, malformed, and bargaining states are ineligible.
- **Candidate action**: replay only the existing Opus reconstruction's 43
  point-observed hidden-unknown price coefficients, exact counter message, and
  its history/round-conditioned late acceptance. An incoming price at or below
  the copied bid and every unsupported tail branch returns to the complete
  current control policy. No coefficient is fitted, interpolated, or extended.
  Hash controls always execute the complete current stack.
- **Reachability before activation**: the latest 20 MB of each intended host
  stream over `1787592547..1787597591` contained 1,057 supported actions in 103
  games; all 1,057 reconstructed wires differed semantically from control. An
  800-game champion-stack paired preflight (seed 2671) produced 241 changed
  submitted actions and passed the generic reachability gate. These are
  mechanism counts, not an effect estimate. Focused strategy/integration tests
  pass 35/35 before the independent reader is added.
- **Isolation**: the running hidden known-cap-10 7aidara arm is statically
  disjoint and may coexist. The new arm fails closed against the broad 7aidara,
  full Opus, Athena, both hidden-unknown opening arms, hidden-policy/floor, and
  hidden-min-share, table-continuation, stall-break, close, and probe
  experiments. Hardliner/Test 2 is excluded because its live extreme-opening
  arm overlaps the first Opus wire. No bargaining flag, configuration, import,
  or behavior may change.
- **Primary / retention**: authenticated official dashboard rating delta over
  every assignment, including immediate accepts, unsupported candidate
  fallbacks, agreements, no-deals, walks, timeouts, invalids, unresolved games,
  and games that never emit a copied counter. Stratify by host before pooling.
  Exact-cell percentile is diagnostic; hidden counterpart values may not be
  inferred from selected deals.
- **Mechanism gate**: audit every turn in the first 20 assignments. Candidate
  point-supported turns must carry the scoped source and exact reconstructed
  wire; unsupported candidate turns must have no scoped source and run control;
  controls must never carry the source. Any scope/hash drift, collision,
  untraced changed wire, invalid action, duplicate, self-play contamination, or
  official join ambiguity causes immediate disarm and rejection.
- **Frozen decision rule**: one harm look at 20 scored official games per arm;
  stop if candidate is at least `-1.0 rating/game` below control, its official
  95% interval is wholly negative, or no-deals are at least 10pp worse. Final at
  40 scored games per arm, at least 5/arm on every deployed host and own type,
  and at least 8/arm in each message mode. Promote only if the official 95% CI
  is wholly positive; exact-cell percentile point lift is at least `+.03` with
  lower bound above `-.01`; candidate no-deals are no more than 5pp worse;
  every host/type/message/scale point is nonnegative; and mechanism, source,
  wire, assignment, duplicate, outcome, and official-join failures are zero.
  Otherwise remain research-only.
- **Prospective deployment boundary**: after inert code/reader/full-suite
  verification is committed and pushed, allow only champion, composite,
  conceder, and randomized to acquire it through natural clean rotations.
  Record separate host T0s before reading outcomes; never restart, signal, or
  abandon a game. The flag is currently OFF everywhere and no live outcome
  exists.

### Direct-leader hidden unknown-horizon opening copy (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HI_UNCAPPED_EXTREME_OPEN_AB=1`;
  `sha256("nego_hi_uncapped_extreme_open_v1|" + game_id) & 1` gives control or
  candidate per game.
- **Behavior evidence**: across all direct hidden multi-round encounters, not
  only agreements, Clod/Athena/doodod opened as sellers at median
  1.488/1.490/1.485B (n=10/8/12) and as buyers at .8108/.8075/.810B
  (n=9/7/14). Their current negotiation ratings were
  2918.75/2840.38/2649.25.
- **Candidate**: in explicitly unknown-horizon hidden games, copy the literal
  1.485B seller ask or .81B buyer bid on the first outgoing price only, then
  return to the complete current policy. Eligibility is restricted to seller
  own types .8B/1.0B and buyer own types 1.2B/1.5B. The running identified-cell
  probe owns seller 1.2B/buyer 1.0B, while DEADGAME_V1 already owns seller
  1.5B/buyer .8B; all scopes are disjoint.
- **Why one wire**: the direct evidence identifies the opening boundary but not
  whether the leaders' later holds cause their rating. A persistent copy is a
  separate mechanism. This arm tests imitation without bundling a concession
  schedule or changing accept/reject/walk decisions.
- **Cohort**: every matching first action before treatment, including buyers
  that accept without emitting a counter. Keep every agreement, no-deal, walk,
  timeout, and unresolved game; exclude cross-fleet duplicate game IDs from the
  pooled estimate.
- **Decision rule**: do not decide before 100 resolved games per arm and at
  least 15 per arm in each own-type cell. Promote only if official per-game
  score candidate-control 95% CI is above zero, close-rate lower 95% bound is
  above -2pp, every role/type/scale/message point estimate is nonnegative, and
  wire failures are zero. Reject on an official-score CI below zero or any
  mechanism failure. Conditional agreement share is diagnostic only.
- **Read with**: `scripts/live_percentile.py --ab hi-extreme-open --since T0
  --until T1 --slots champion,composite,hardliner,randomized`. The local
  hidden-value-pooled percentile never authorizes promotion.
- **Live on / boundary**: Test 1 (`champion`), Test 2 (`hardliner`), Test 4
  (`randomized`), and Agent 5 (`composite`) from the clean common boundary
  `T0=1787571320` (2026-08-24 17:05:20 IST). All four processes naturally
  rotated onto pushed commit `8a21e8e` before the flag was set; the overlay
  mtime was `1787571316`, four seconds before T0. Test 3 remains unarmed.
- **Preflight**: champion's exact live stack, 1,000 paired negotiation games,
  seed 1907: 100 eligible / 49 fired / 49 changed final wire actions. Focused
  suite 88 passed; full suite 1,048 passed with only the two predeclared
  bargaining failures.

The first post-boundary assignment was a composite hash control in buyer-1.2;
its ordinary first counter remained unchanged. The first emitted treatment wire
was composite seller-.8 at exactly 1.485B, and a Test 4 candidate buyer-1.5
immediately accepted before emitting a price while remaining in the ITT. All
eight initial assignments reported `wire_ok=true`. This verifies live control,
treatment, and immediate-accept cohort semantics, not outcome value. Do not arm
Test 3 before causal promotion evidence.

## REJECTED — DEFAULT OFF, DO NOT RUN

### Hidden unknown-horizon 95%-share support ladder (negotiation)
- **Rejected before deployment**: the proposed three-rung/four-hold schedule
  bundled unproved greed and timing constants. Several transcript landmarks
  used as imitation evidence came from no-deal/walk trajectories, and a rational
  opponent can reject the 5% first rung knowing a deterministic concession is
  coming. The mechanism also initially disabled broader hidden guards in
  ineligible states; independent review caught that control contamination.
- **Verdict**: implementation and reader removed. Replaced by the one-price,
  three-arm identified-cell probe above.

### Hidden unknown-horizon accept-all-profitable (negotiation)
- **Corrected counterfactual**: exact replay of all 32,403 public trajectories
  compared accept-now with each game's actual continuation after rejection,
  rather than treating a rejected bid as a zero. In the matching cohort
  (4,050 games), 375 decisions were exposed and 156 would change.
- **Result**: exposed exact-percentile delta `-0.06628`, bootstrap 95% CI
  `[-0.08183,-0.05096]`; cohort ITT `-0.00614` (sum `-24.85` percentile).
- **Why the old estimate was wrong**: it ignored later agreements at better
  prices. The prior `+0.07138` result was not the policy counterfactual.
- **Verdict**: implementation, reader, and reachability hook removed before
  deployment. Never arm this mechanism.

### Buyer selectivity safety arm (persuasion, prior EV <= price)
- **Hypothesis**: in cells where the prior does not beat price, the existing
  buyer's early and repeated purchases from sellers with no demonstrated
  selectivity create enough bottom-tail outcomes that a conservative veto
  improves same-cell percentile despite giving up substantial raw payoff.
- **Design**: `GLEE_PERS_BUYER_SELECTIVITY_AB=1` assigns each eligible game by
  `sha256("pers_buyer_selectivity_v1|" + game_id) & 1`. Control is the current
  buyer. Candidate is veto-only: wait for a historical explicit decline,
  require a current explicit recommendation, require the existing fitted
  q-grid posterior mean to strictly exceed money breakeven. The one-bought-low
  stop is no longer bundled: `GLEE_PERS_BUYER_SELECTIVITY_STRIKE_AB=1` assigns
  it independently per game with salt `pers_buyer_selectivity_strike_v1|`, so
  the ITT reader can score the gate with and without that insurance. Both flags
  are absent/default OFF. The first-arm margin is exactly `0.0`; a positive
  `GLEE_PERS_BUYER_SELECTIVITY_MARGIN` is a separate, unmeasured parameter and
  must not be changed during the window.
- **Eligibility**: buyer persuasion games with `v>u`, `price>u`, and
  `p*v+(1-p)*u <= price`. Prior-positive games are not assigned and cannot be
  changed. Cohort on the globally first eligible buyer decision and record exact
  activation/disarm timestamps; exclude games whose first exposure predates T0.
- **Primary outcome**: candidate-control mean same-cell percentile over ALL
  assigned eligible games, including no-decline games, terminal zeros and cold
  abandonments. Never condition the primary analysis on an eventual decline.
- **Decision rule**: promote only if the candidate-control percentile 95% CI is
  entirely above zero; reject if entirely below zero; otherwise continue or call
  inconclusive. Pending/invalid outcomes block promotion. A mechanism failure
  (any candidate buy before a prior explicit decline, or any second bought low
  in the independently strike-assigned cell) rejects regardless of percentile.
  Stratify, without changing the primary
  rule, by exact `(p, v/price, message mode)`, equality versus strict-negative
  prior EV, and one-decline sellers. Freeze and record hashes of both the q prior
  and percentile CDF for the whole window.
- **Cost diagnostics**: report payoff/price, purchase rate, pre-first-decline
  buys, bought highs/lows, and the one-decline subgroup. These are secondary:
  the competition scores percentile, while a seller may adapt its messages to
  treatment.
- **Rank-threshold red team**: the proposed one-step `q_rank` is not uniformly
  below money breakeven once accumulated payoff moves across CDF atoms. At the
  empirical cell medians it is lower in 8/18 cells, higher in 9/18, and tied in
  one; over the 27,493 actual purchase states it is stricter 16,973 times versus
  money's 9,843. The full candidate blocks 8,572 one-step-rank-positive buys,
  including 6,283 highs, but only 13 blocks are caused by the money cutoff after
  earlier gates. Raw `F(S)` is also a terminal/fixed-continuation calculation,
  not the dynamic threshold in a 20-round game where buying changes later payoff
  and information. Do not replace money breakeven with that myopic threshold.
- **Historical shadow, not causal evidence**: on the frozen oldest 5,181
  eligible results, full gate changes buys `27,493 -> 8,683`, payoff
  `1.1555P -> 0.7774P`, and fitted percentile `+0.01209` (normal 95% CI
  `[+0.00718,+0.01701]`). Without strike it retains 14,287 buys, payoff is
  `0.9123P`, and the proxy is `+0.01445`; the strike removes 5,604 more buys and
  costs `0.00236` percentile. The money cutoff itself removes only 56 buys in
  the sequential reconstruction and changes the proxy `+0.01484 -> +0.01445`.
  Text framing supplies `+0.01248` of the full overall delta while binary
  framing contributes `-0.00039`.
- **Held-out failure**: deterministic chronological 70/30 cross-fit, cutoff
  `2026-08-21 16:52:32Z`. The q prior uses 6,013 earlier buyer games and the CDF
  9,048 earlier persuasion games; all later cells have CDF n=270-351. On 1,555
  strictly later eligible games, full gate is `-0.00131` with 95% CI
  `[-0.01111,+0.00848]`; no-strike is `+0.00684`
  `[-0.00113,+0.01482]`. The early in-sample estimate is `+0.01442`
  `[+0.00890,+0.01994]`. The gain does not survive.
- **No-look-ahead motivation**: the observable state is "any explicit decline
  before this decision", not eventual seller type. Explicit-yes purchases after
  a prior decline outperform those before one after exact cell+round adjustment
  (`+11.72pp` high, `+0.2355P` per buy, local rank `+0.01554`), so the predictive
  gradient reproduces. But pre-decline explicit-yes buys themselves are
  money-positive (`+0.1455P/buy`) and locally rank-neutral (`+0.00036`, CI spans
  zero). This observational, action-selected contrast does not establish that
  vetoing them helps final rank.
- **Verdict**: reject the historical performance claim and do not arm either
  flag. The implementation remains inert for auditability; any reconsideration
  needs a new prospective design, not another fit to this corpus.

## BUILT — DEFAULT OFF, WAITING FOR AN UNCONTAMINATED WINDOW

### Current-offer stale-stall break (negotiation)
- **Flag / assignment**: `GLEE_NEGO_STALL_CURRENT_BREAK_AB=1`;
  `sha256("nego_stall_current_break_v1|" + game_id) & 1`.
- **Trigger**: the existing historical helper reports a three-offer <=1% stall,
  the current standing opponent offer has improved for our seat by strictly
  more than 1% of `max(abs(stale), abs(current), 1)`, and suppressing the stale
  writer would make our counter strictly more favorable (seller asks more;
  buyer bids less). Wrong-direction schedule states are shadowed but ineligible.
- **Candidate**: suppress only `stall_park`'s target rewrite on that turn.
  Control retains the exact existing target. Dead-game walk, stall acceptance,
  and every non-triggered state keep the original helper and behavior.
- **Identification**: cohort on the globally first qualifying pre-action turn;
  the arm has no earlier behavioral path, so trigger reach is pre-treatment.
  Keep immediate accepts, emitted counters, walks, no-deals, cold missing
  finals, and all later outcomes. Exclude cross-fleet duplicate game IDs.
- **Safety**: fail closed unless `CONTINUATION_ACCEPT=1`; refuse co-arming with
  either first-offer probe, the terminal-counter probe, hidden-policy,
  hidden-floor, or either first-principles switch. Close the cohort if the
  accept stack or anchors change.
- **Decision rule**: first decision at 100 resolved official games/arm and
  20/arm per role. Promote only if official per-game rating-delta CI >0,
  close-rate lower CI >-2pp, all role/information/horizon/scale/message point
  estimates >=0, and mechanism failures=0. Reject on official CI <0 or any
  mechanism failure. Local pooled-CDF percentile is diagnostic only.
- **Read with**: `scripts/live_percentile.py --ab stall-current-break --since
  T0 --until T1 --slots SLOTS --official-json FILE`.
- **Live on**: nowhere. Do not arm until the overlapping opening/terminal
  experiments are closed or an uncontaminated slot is deliberately selected.

### Hidden support minimum-share acceptance veto (negotiation)
- **Flag / assignment**: `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB=1`, default OFF;
  `sha256("nego_hidden_min_share_veto_v1|" + game_id) & 1` assigns control or
  candidate once per game. Missing ids fail closed.
- **Structural signal**: validated hidden values are
  `{.8,1.0,1.2,1.5}*B`. From our observed own type, the smallest strictly
  positive ZOPA is `.2B` for seller-.8/1.0 and buyer-1.0/1.2, `.3B` for
  seller-1.2 and buyer-1.5, and nonexistent for seller-1.5/buyer-.8. On a real
  nonfinal hidden decision, mark an offer only when it is profitable and our
  surplus is strictly below 40% of that minimum, with a scale tolerance that
  excludes exact-boundary float artefacts. The share bound is conditional on a
  positive-ZOPA latent cell; irrational loss-making opponent offers are legal
  and remain part of the randomized outcome.
- **Pre-treatment eligibility**: the globally first marked offer that the exact
  current stack is otherwise about to accept through direct table acceptance,
  stall acceptance, or continuation acceptance. States the control already
  rejects are never assigned, so the estimand is the decision-level effect of
  holding instead of accepting—not a diluted universal state cohort. Control
  remains byte-identical. Candidate returns `RejectOffer` through the existing
  profitable-side counter construction; no concession parameter is bundled.
- **Scope / safety**: requires `HORIZON_V2=1`, `CONTINUATION_ACCEPT=1`, and
  `TABLE=1`; refuses the live first-offer, extreme-open, terminal-counter,
  hidden-policy/floor, stale-current-break, rank-price, close, uncapped, and
  surplus probes. First-principles is not a flag-level conflict: its only hidden
  cell is single-round and its owner returns before this nonfinal path. The real
  final-round any-positive rule is dominant and unreachable by the veto.
- **Historical motivation, not effect evidence**: five-slot turn streams contain
  1,473 matching accepted offers (1,243 below-table fallthroughs and 230 direct
  table accepts). Of 479 locally recovered finals, 474 captured <40% of realised
  positive surplus; two were exact-boundary float cases and three were irrational
  negative-opponent-payoff deals. Conditioning on accepted deals cannot identify
  what rejection would have earned.
- **Primary cohort/outcome**: include every first assignment and every eventual
  agreement, no-deal, walk, invalid, cold-missing, and pending outcome. Exclude
  cross-fleet duplicate game ids from the pooled causal estimate but retain them
  for mechanism auditing. Primary is official dashboard per-game `rating_delta`;
  local hidden-value-pooled percentile is diagnostic only. Freeze the exact
  accept stack and activation boundary for the whole window.
- **Decision rule**: efficacy only at 100 resolved official games per arm and 20
  per arm in each role. Promote only if candidate-control official-rating 95% CI
  is wholly above zero, close-rate point delta is at least -5pp, both role point
  estimates are nonnegative, and mechanism failures are zero. At the single
  preplanned harm look after 30 official games per arm, reject if the official
  95% CI is wholly below zero. Reject immediately for any scope/hash/wire failure;
  unresolved or official-missing outcomes block promotion.
- **Reader**: `scripts/live_percentile.py --ab hidden-min-share-veto --since T0
  --until T1 --slots conceder --official-json FILE`. It recomputes the production
  signal and assignment, verifies control `AcceptOffer` and candidate
  `RejectOffer`/counter wires, and enforces the decision rule by exit status.
- **Exact-stack reachability**: Test 3 (`conceder`) control stack, 1,500 paired
  negotiation games, seed 2309: 55 eligible, 26 fired, 26 changed submitted
  actions. Focused impacted suite: 444 passed; dedicated mechanism/reader suite:
  50 passed.
- **Live on**: nowhere pending inert commit/push and a natural Test 3 rotation.
  Test 3 is the only current uncontaminated slot; never alter its bargaining flags.

## NEXT (not built)
1. General accept/counter/walk response model (item 5 of the operator plan).
2. State-dependent price discrimination / shallow DP over the frontier.
3. Full-sequence opponent-type inference.
4. Partially pooled per-opponent profiles.
5. Message framing arms (orthogonal; only 7.1% of offers carry text).

## RUNNING — LIVE CAUSAL MEASUREMENT

### Exact weak-cell token versus non-leaking prose (persuasion seller)
- **Falsifiable hypothesis**: in the official persuasion seller cell
  `seller_message_type=text`, `p=.8`, seller knows `v/u`, `v=1.25*price`, and
  `total_rounds=20`, replacing the current literal positive token `yes` with
  the current quality-neutral prose template raises mean official per-game
  rating delta. The recommendation policy and negative token `no` do not
  change. A non-positive official result falsifies the hypothesis; conversion
  alone cannot promote it.
- **Why this cell**: in the clean common token window
  `[1787402777.668, 1787484376.458)`, this was the largest scoreable seller/text
  weakness: 118 games assigned, 30 locally recovered finals, local diagnostic
  percentile `.4847`, 47.5% purchase rate, and 16.7% zero outcomes. The wider
  historical positive-message contrast (token 60.8% versus prose 69.3%) is
  observational and post-action-selected; it motivates randomisation only.
  The authenticated dashboard immediately before activation also contained an
  exact text-cell game: after one observed low, the hidden buyer stopped at
  4/20 purchases and the official delta was -5.2. A superficially matching
  5/20, -6.2 transcript was binary when joined to the wire log and is excluded;
  the dashboard does not display message mode. This is pre-treatment mechanism
  evidence, not a causal estimate.
- **Flag / assignment**: `GLEE_PERS_P08_R125_PROSE_AB=1`, default OFF.
  `int(sha256("pers_p08_r125_prose_v1|" + game_id).hexdigest(), 16) & 1` assigns the
  game. No game id fails closed. The bit is read only after `seller_plan`, so it
  cannot enter any recommendation decision or another arm.
- **Pre-treatment cohort**: every target game's globally first seller-message
  turn, before inspecting the outgoing message or any purchase. The untreated
  baseline begins at the rank-gate disarm boundary `1787570799`; it ends at the
  prospective clean common activation T0. The experimental cohort begins at T0
  and includes every assignment: purchases, refusals, zero payoffs, timeouts,
  invalid/abandoned games, unresolved outcomes, and any immediate terminal
  result. Result-fetch timestamps never define the cohort.
- **Control / candidate**: hash control remains byte-identical to the live
  `yes`/`no` stack. Candidate changes only positive text to one of the six
  combinations in the current non-leaking template bank, selected by a stable
  game-id/round RNG independent of private quality. No LLM. Binary persuasion,
  buyers, other priors/ratios, seller-blind cells, and all bargaining and
  negotiation actions are unreachable.
- **Hosts / boundary**: commit `2f4989d` naturally loaded as Test 1 PID 68351,
  Agent 5 PID 68203, and Test 4 PID 67641. Fleet tooling armed those three with
  `PERS_TOKEN_MAX_P=0`; clean common `T0=1787575521` (2026-08-24 18:15:21
  IST). Test 2 and Test 3 stay unarmed. The rest of each exact live stack,
  including LLM off, KEEP_MSG=1 and MSG_STYLE=token, was preserved.
- **Reachability contract**: after process load, 800 seeded persuasion games on
  each exact live stack reported Test 1 `eligible=320/fired=160/changed=160`,
  Test 4 `220/100/100`, and Agent 5 `160/60/60`. During the first 20 games per
  arm require a stable game bit on all 20 rounds, literal `yes` for every
  control message, only current-bank prose for every candidate message, no
  recommendation mismatch, no third wording, and no invalid/timeout. Any
  failure is an immediate disarm and mechanism rejection.
- **Primary / diagnostics**: join every resolved assignment to the official
  dashboard's per-game `rating_delta`; the local same-cell percentile is
  diagnostic only. Report purchase rate, zero rate, payoff/price and bought
  high/low counts without conditioning the primary analysis on purchases or
  recommendations. Exclude detected cross-fleet game ids and reject any
  self-play-contaminated read; hidden-opponent contamination remains explicit.
- **Sample and rules**: no outcome decision before 120 resolved official games
  per arm. At the observed three-host arrival rate this is about 3.2 days.
  Extend once to 200/arm only if the official CI crosses zero and competition
  time permits. Promote only if the official candidate-control 95% CI is wholly
  above zero, the purchase-rate point estimate is nonnegative with lower bound
  above -2pp, all three price-scale point estimates are nonnegative, and there
  are zero unresolved, invalid, duplicate/self-play, official-join, or wire
  failures. Reject immediately for any mechanism/scope failure; after at least
  50 official games/arm reject if the official-score CI is wholly below zero or
  the purchase-rate CI is wholly negative. Otherwise remain research-only.
- **Subgroups**: predeclared price scale `{100, 10_000, 1_000_000}`, named
  versus hidden opponent, host slot, and activation era. Exact-cell scale rows
  are diagnostic unless powered; no subgroup cherry-picking can override the
  pooled official rule.
- **Read with**: `scripts/live_percentile.py --ab pers-prose --since T0
  --until T1 --slots champion,composite,randomized --official-json FILE` where
  FILE contains dashboard-exported `slot`, `game_id`, `rating_delta` records.
- **First live observations (no decision)**: Test 1 candidate game
  `202cb810-c1a7-4d36-b98b-7d394842d258` fired on all 20 rounds with stable hash,
  unchanged recommendations, approved prose only, and no terminal failure. It
  closed 4/20 purchases (3 high, 1 low), payoff `4P`, official delta `-4.3`;
  the buyer passed all 16 rounds after the low purchase. This clean adverse
  observation does not alter the precommitted sample or stop boundary. Agent 5
  candidate game `36053a1f-16a3-4fb3-94cb-2d580cc1764d`, against named opponent
  `expert`, fired approved prose for all 20 rounds, sold 13/20 (7 high, 6 low),
  earned `13P`, and received official delta `-1.4`. Pooled candidate-only n=2
  is official mean `-2.85`, purchase rate `42.5%`, zero rate 0%, with no wire
  failure. No control has resolved, so neither the point nor its tiny-sample CI
  may trigger a decision. Complete dashboard transcripts are frozen in
  `.ai/PERSUASION_OFFICIAL.json`; the reader requires all 20 messages,
  qualities, decisions, exact setup, and seller-payoff identity before an
  authenticated transcript may recover a locally missing final.

### Exact zero-margin binary seller truthfulness (LIVE on Test 2)
- **Falsifiable hypothesis**: in persuasion seller/binary games with `p=.8`,
  seller-visible `v/u`, `v=1.25*price`, `u=0`, and 20 rounds, recommending only
  high-quality items raises mean official per-game rating delta versus the live
  all-`yes` control. A non-positive official intent-to-treat result falsifies
  the hypothesis. Purchase conversion or selected post-lie games cannot promote
  it.
- **Exact official cells**: seller role, binary protocol,
  seller-knows-consumer-values, p=.8, v=1.25P, u=0, 20 rounds, at each price
  scale `{100, 10_000, 1_000_000}`. Text mode is excluded, making this arm
  behaviorally disjoint from the running prose experiment.
- **Why this is not the rejected broad backload idea**: the published
  all-push advantage `+.391` was measured only in strict `p*r>1` cells. This
  experiment targets only the equality `p*r=1` branch, which never reached the
  live never-lie/shading path. A tiny recovered subset of the old backload arm
  favored its mostly truthful candidate (14.17 versus 5.29 purchases, n=6/7)
  in this exact cell, but result-time selection, missing official deltas, and
  the terminal push make that diagnostic non-causal.
- **Mechanism evidence, not an effect estimate**: 170 deduplicated completed
  all-yes exact-cell games averaged 7.29 purchases despite 16.04 high items;
  35/170 sold nothing. Of 123 games with a bought low, 42 buyers stopped
  completely and left a mean 12.38 later high opportunities. Official game
  `6516c6b7-2a47-4919-b192-cd0484e21daa` sold a round-1 high and round-2 low,
  then lost 14 later high opportunities and scored `-7.6`. The first text-prose
  candidate showed the same stop-after-low mechanism and scored `-4.3`, so
  stronger positive wording alone did not repair credibility in that draw.
- **Flag / assignment**: `GLEE_PERS_P08_R125_BINARY_TRUTH_AB=1`, default OFF.
  `int(sha256("pers_p08_r125_binary_truth_v1|" + game_id).hexdigest(), 16) & 1`
  assigns treatment. Missing game ids fail closed. Eligibility is fixed at the
  globally first seller recommendation and never conditions cohort membership
  on private quality, buyer response, purchase, payoff, or completion.
- **Control / candidate**: hash control returns the complete current plan and
  submitted `yes` action byte-identically. Candidate returns `yes` on high and
  `no` on low in every round. Candidate-high actions remain unchanged and only
  candidate-low turns append `p08_r125_binary_truth` to `gates_fired`. There is
  no adaptive trigger, terminal exception, prose, LLM, buyer change, or reach
  into any other seller cell.
- **Pre-treatment cohort**: Test 2 exact-cell games whose first seller turn is
  in `[1787570799, 1787582397)`, beginning at the rank-gate disarm. The
  experimental cohort begins at clean `T0=1787582397` (2026-08-24 20:09:57
  IST) and includes every assignment: purchases, refusals, zero outcomes,
  timeouts, invalid/abandoned, unresolved, and immediate terminal outcomes.
  Result-fetch time never defines the cohort.
- **Preflight**: Test 2's exact hardliner stack, 800 seeded persuasion games,
  seed 2417, reported `eligible=31`, `fired=21`, and `action_changed=21`.
  Focused mechanism/reader suite: 31 passed. The full allowed suite passed 1,167
  tests with only the same two pre-existing bargaining failures
  (`test_bargaining_horizon_floor` and `test_sim_grid[bargaining]`).
- **First-20 mechanism contract**: verify all 20 rounds of each of the first 20
  assigned games. The game bit must be stable; controls must emit `yes` every
  round; candidate action must equal private quality (`high -> yes`, `low ->
  no`); no third action, non-target fire, invalid action, timeout, or prose/rank/
  backload interaction is permitted. Any failure causes immediate disarm and
  mechanism rejection.
- **Primary / sample / rules**: authenticated dashboard per-game rating delta,
  full-game ITT, fixed final read at 40 resolved official games per arm and at
  least 8 per arm per price scale. One harm look at 20 official games per arm;
  reject if the official 95% CI is wholly negative. Promote only if the final
  official CI is wholly positive, purchase-count point delta is positive,
  zero-outcome point delta is nonpositive, all three scale point estimates are
  nonnegative, every deployed host point estimate is nonnegative, and mechanism,
  scope, wire, self-play/duplicate, unresolved, invalid, and official-join
  failures are zero. A final CI crossing zero remains research-only.
- **Subgroups**: price scale, named versus hidden opponent, host slot, and
  activation era. No subgroup can override the pooled official rule. Local
  percentile and post-lie continuation counts remain diagnostic only.
- **Deployment boundary**: Test 2 (`hardliner`) naturally drained PID 71871 and
  loaded pushed code `d79ca92` as PID 76676 at 20:08:48 IST. Fleet tooling set
  only `GLEE_PERS_P08_R125_BINARY_TRUTH_AB=1` at clean arms mtime
  `T0=1787582397`, without a restart or signal. The post-load exact-stack rerun
  reported `eligible=29/fired=14/action_changed=14`. Test 3 stays untouched;
  prose and buyer-parser flags are absent on Test 2; rank gate and backload are
  explicit zero. A real candidate low-quality `no` remains required before the
  live mechanism is behavior-verified.
- **Prospective research-host expansion (frozen before any truth assignment or
  outcome)**: the first 14 post-T0 minutes on Test 2 produced zero eligible
  games. To reach the unchanged fixed 40/arm official boundary without peeking
  at any treatment outcome, Agent 5 (`composite`) and Test 4 (`randomized`) may
  be armed after each naturally loads `d79ca92` or later. Their live prose arm
  is text-only, while truth is binary-only, so the eligibility sets are
  disjoint. Exact-stack preflight at seed 2431 reported
  `eligible=32/fired=18/action_changed=18` on each host over 800 games. Record a
  host-specific clean T0; pool all declared hosts by stable game hash, retain
  host/activation-era diagnostics, require every host point estimate
  nonnegative for promotion, and reject detected cross-fleet duplicates. Test 3
  remains untouched.
- **Research-host activation**: Agent 5 (`composite`) naturally loaded pushed
  code as PID 79006 at 20:42:18 IST and fleet tooling set only the truth flag at
  `T0=1787584351` (20:42:31). Test 4 (`randomized`) naturally loaded as PID
  79064 at 20:42:58 and was armed at `T0=1787584425` (20:43:45). At the 20:50
  read, all three host-specific readers reported zero exact assigned games.
  Therefore no observed rating movement is treatment evidence and the required
  first candidate low-quality `no` remains outstanding.
- **Operational era split**: an external whole-fleet supervisor restart at
  `1787584628` (20:47:08 IST) timed out 14 persuasion games across Test 2,
  Agent 5, and Test 4 for `-109.4` official rating in total. Host-specific truth
  readers and the prose reader show that none was an exact assigned experiment
  game, so they do not enter either arm. Preserve the original cohorts, record
  `1787584628` as a deployment-era subgroup boundary, and never attribute this
  rating discontinuity to persuasion behavior. The timeouts also caused a
  server-enforced crash-loop queue suspension on every slot until approximately
  `1787586428` (21:17 IST); no experiment exposure can accrue during that
  interval. The live processes retry in place every 60 seconds and must not be
  restarted again.
- **Read with**: run `scripts/live_percentile.py --ab pers-truth` separately for
  `hardliner --since 1787582397`, `composite --since 1787584351`, and
  `randomized --since 1787584425`, always with `--official-json FILE`. Do not
  pool from a common earlier timestamp: that would admit pre-activation games
  from the later research hosts.

### Exact buyer/text explicit-decline veto (built default OFF)
- **Falsifiable hypothesis**: in persuasion buyer/text games with `p=.8`,
  `v=1.25*price`, `u=0`, and 20 rounds, treating every
  expanded-parser explicit decline as a final pass raises mean authenticated
  official per-game rating delta versus the complete live buyer-v2 control.
  A non-positive all-assigned official result falsifies the hypothesis;
  decline-conditioned payoff or local percentile cannot promote it.
- **Why this is isolated**: `GLEE_PERS_PARSE_V2` only expands phrases, while
  `GLEE_PERS_PARSE_TRI` changes abstentions and posterior updates broadly; TRI
  alone still reads `Not recommended.` as abstention when V2 is absent.  This
  arm uses the expanded decline table only for its final candidate veto and
  changes neither current nor historical parsing anywhere else.  It leaves all
  positive-message and pre-decline purchases intact, so it does not retry the
  rejected buyer-selectivity/strike/LCB arms.
- **Mechanism evidence, not effect evidence**: among 395 deduplicated completed
  exact games across both official seller-knowledge configurations, 196
  contained an expanded-parser decline and 199 did not.  The live buyer
  purchased such declines in 22 games / 44 turns; all 44 revealed low.
  Frozen-stream savings averaged `.1114P` and the within-configuration local
  diagnostic percentile changed `+.0172` over all 395.  In the known-CV cell
  alone the corresponding figures were `.1456P` and `+.0228` (bootstrap 95%
  interval `[+.0109,+.0374]`).  Passed-item quality is unobserved and seller adaptation
  invalidates that counterfactual.  Authenticated game `f2bed4f4-b9f2-47d3-
  b397-7dc41c919673` bought three `Not recommended.` lows, finished at zero,
  and scored `-4.0`; its fixed sequence would save `3P`, but is not causal.
- **Flag / assignment**:
  `GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB=1`, default OFF;
  `int(sha256("pers_p08_r125_text_decline_veto_v1|" + game_id).hexdigest(),
  16) & 1` assigns the game.  Missing ids fail closed.  Eligibility is fixed at
  the globally first buyer decision from structural buyer seat, text mode,
  exact numeric cell, and horizon only—never message, decline, purchase,
  payoff, or completion.
- **Two official configuration cells**: the production-observable gate is the
  union of `is_seller_know_cv=true` and `is_seller_know_cv=false`.  The
  documented active state withholds that configuration flag (and the simulator
  enforces the omission), so conditioning assignment on it would be an
  unreachable hidden-state policy.  Official rating deltas are already scored
  within their own configuration.  The reader reports both final/config labels
  separately and never infers a missing label from messages, purchases, or
  outcomes; unavailable labels block promotion.
- **Control / candidate**: hash control returns the entire flag-off buyer plan
  and action byte-identically, without arm metadata.  Candidate first computes
  that same complete plan, including optional rank-buy, then final-overlays
  `yes -> no` only when the current message is an expanded-parser explicit
  decline.  Positive messages, abstentions, already-refused actions, history,
  posterior, sellers, binary mode, other cells, bargaining, and negotiation are
  unreachable.  Only a real changed action appends
  `p08_r125_text_decline_veto` to `gates_fired`.
- **Pre-treatment / ITT cohort**: Test 2 first exact buyer turns in
  `[1787570799, prospective T0)`, beginning at rank-gate disarm.  The
  experimental cohort begins at a clean future T0 and includes every assigned
  game: no-decline paths, purchases, refusals, zero and negative outcomes,
  timeouts, invalid/abandoned, unresolved, and immediate terminal outcomes.
  First-turn time, never result-fetch time, defines membership.
- **Preflight and live mechanism contract**: on Test 2's exact stack require
  `eligible>0`, `fired>0`, and `action_changed>0`.  Audit all rounds of the
  first 20 assignments for a stable bit, byte-identical controls, no change on
  positive/abstaining messages, and candidate pass on every target decline.
  Any control difference, non-target fire, candidate decline purchase, hash
  drift, invalid wire, or trace/action mismatch is immediate mechanism
  rejection.  Activation is not behavior-verified until a real changed-action
  trace appears; no trace by 50 exact assignments is a reach failure.
- **Primary / sample / rules**: authenticated dashboard per-game rating delta,
  full-game ITT.  One harm look at 50 resolved official games per arm rejects
  if the official 95% CI is wholly negative.  Fixed final read at 120/arm and
  at least 20/arm per price scale.  Promote only if the official CI is wholly
  positive, normalized-payoff point delta is positive, zero- and negative-
  outcome point deltas are nonpositive, all scale and both seller-knowledge-
  cell points are nonnegative, and
  mechanism, scope, wire, duplicate/self-play, unresolved, invalid, and
  official-join failures are zero.  A final CI crossing zero stays research-
  only.
- **Subgroups / boundary**: seller-knowledge configuration (when present in
  final/config evidence), price scale, named versus hidden opponent, legacy-
  recognized versus V2-only decline phrase, and first-decline round are
  diagnostic only.  Build/push inert code now; arm Test 2 only after the binary
  truth decision/disarm at a clean timestamp, with prose/parser/selectivity
  absent and rank/backload explicit zero.  Test 3 remains untouched.  Exclude
  observed cross-fleet duplicates; hidden self-play risk blocks promotion.
- **Prospective research-host amendment, frozen before any activation or
  decline-veto outcome**: replace only the preceding sequential host/timing
  boundary.  Arm Test 1 (`champion`), Agent 5 (`composite`), and Test 4
  (`randomized`) at separate clean T0s; Test 2 and Test 3 remain unarmed.  This
  amendment uses only pre-treatment reachability, arrival rate, behavioral
  scope, and the competition deadline: the flag was absent everywhere and `rg`
  found zero live decline-veto traces.  Prose is seller/text, truth is
  seller/binary, and this arm is buyer/text, so no action can enter two arms.
  The complete current persuasion stack on each host is frozen at its T0 and
  the hash control remains the full buyer-v2 control object byte-identically.
  Preserve the original 50/arm harm look, 120/arm final, 20/arm/scale minimum,
  success/stop rules, and all-outcome ITT; add deployed host as a predeclared
  subgroup and require every host point estimate to be nonnegative for
  promotion.  Use a host-specific reader T0 so no pre-activation game on a
  later host can enter.  Verify no exact target is already in flight at each
  activation and replay every state in the first 20 assignments both flag-OFF
  and flag-ON; a changed candidate `no` without the adjacent trace is an
  immediate mechanism rejection.  Underpowered deadline results cannot
  promote.
- **Amendment preflight**: on each exact live research stack, 800 persuasion
  games at seed 2441 reported `eligible=340/fired=25/action_changed=25`; an
  independent seed 2461 reported `380/30/30`.  The focused mechanism/reader
  suite passed 20 tests.  The full allowed suite passed 1,291 tests with only
  the same two pre-existing bargaining failures
  (`test_bargaining_horizon_floor` and `test_sim_grid[bargaining]`).  All three
  current processes launched after commit `d79ca92`, so activation requires no
  restart.  The pre-treatment reader found 27 exact games across the proposed
  hosts in roughly 4.7 hours (24 terminal, 3 unresolved), implying about 38--42
  hours to the unchanged 120/arm boundary.
- **Research-host activation**: after verifying no exact target game was in
  flight, fleet tooling set only
  `GLEE_PERS_P08_R125_TEXT_DECLINE_VETO_AB=1` on Test 1 at
  `T0=1787588203` (21:46:43 IST), Agent 5 at `T0=1787588220` (21:47:00), and
  Test 4 at `T0=1787588236` (21:47:16).  All three processes had loaded
  `d79ca92` or later before activation; no restart, signal, bargaining flag, or
  negotiation flag changed.  Test 2 and Test 3 remain unarmed.  Immediate
  host-specific readers found zero assigned target games and `rg` found zero
  decline-veto traces, so live changed-action verification remains pending the
  first eligible candidate decline.
- **Read with**: `scripts/live_percentile.py --ab pers-decline-veto --since T0
  --slots hardliner --official-json FILE`.
  For the amended research window run this separately for `champion`,
  `composite`, and `randomized` using each host's own T0, then pool only the
  declared host-specific cohorts.

### Exact p=.5/r=1.2 buyer selectivity unlock (design audit; not built)
- **Observed weak cell, diagnostic only**: since the rank-gate disarm, 68
  structurally exact seller-known buyer games across binary/text produced 68
  zeros; in 45 of those games our buyer passed all 900 rounds.  In the directly
  observed seller-known mirror, opponent buyers bought 114 high and zero low
  units from our selective sellers across 37 games, with local diagnostic
  percentiles `.7914` binary and `.7774` text.  A post-recovery all-outcome
  cohort contained 9/86 games in this cell family, all zero.  These comparisons
  motivate randomization; they do not identify a causal action value and local
  percentile cannot promote.
- **Falsifiable candidate**: in buyer games with `p=.5`, `v=1.2P`, `u=0`, and
  20 rounds, after computing the full current buyer-v2 plan, a stable per-game
  candidate may change only `pass -> buy` when the plan is tight-prior blocked,
  the strict current signal is positive, at least one prior strict decline was
  observed, and posterior expected value strictly exceeds price.  Enroll both
  message modes and both seller-knowledge configurations; the latter is hidden
  during play and can only be a terminal subgroup.  A nonpositive all-assigned
  official candidate-control result falsifies the hypothesis.
- **Scope relative to rejected ideas**: this is not the rejected broad rank
  gate (which reached `.8` cells, flipped both directions, and used a pooled
  local CDF) or the negative selectivity/strike/LCB arms (which removed
  purchases).  The proposed arm is exact-cell, money-posterior gated, and
  one-directional `no -> yes`; it is also disjoint from prose, truth, and the
  live `.8/1.25` decline veto.  It remains unimplemented and default OFF until
  independent code, reader, tests, reachability, and a full prospective sample
  rule are committed.
- **Flag / assignment precommit**:
  `GLEE_PERS_P05_R12_SELECTIVITY_UNLOCK_AB`, default OFF, with candidate bit
  `int(sha256("pers_p05_r12_selectivity_unlock_v1|" + game_id).hexdigest(),
  16) & 1`.  Missing game ids fail closed.  Eligibility is fixed at the
  globally first buyer decision from structural public state, before inspecting
  any message, purchase, quality, payoff, completion, or result.
- **Exact official cells**: buyer/player 2, `p=.5`, `v=1.2P`, `u=0`, 20 rounds,
  price scale `{100, 10_000, 1_000_000}`, both text and binary modes, and both
  seller-knowledge configurations.  Seller knowledge is hidden from the buyer
  and cannot enter the production gate; it is recovered only from authenticated
  terminal configuration evidence and missing labels block promotion.
- **Control / candidate**: first compute the complete current buyer-v2 plan.
  Hash control and every non-triggering candidate return that action and plan
  byte-identically and without arm metadata.  Candidate may change only
  `pass -> buy` when buyer-v2 reports `tight=true` and `blocked=true`, the
  current strict tri-state recommendation is `true`, at least one earlier
  strict decline exists, and posterior expected value exceeds price by a
  scale-relative tolerance.  Legacy ambiguous-text coercion cannot trigger.
  Only an actual changed action appends `p05_r12_selectivity_unlock` to
  `gates_fired`.  Fail closed if guard, strike, LCB, rank-buy/rank-gate,
  selectivity, or parser experiments can alter the frozen buyer path.
- **Pre-treatment / ITT cohort**: for each future host, all structurally exact
  games whose first buyer turn lies in `[1787570799, host T0)` are
  pre-treatment; the experimental cohort begins at that host's clean T0.
  Retain every assignment, including games with no qualifying message path,
  all passes, purchases, zero and negative payoffs, timeouts, invalid/abandoned,
  unresolved, and immediate terminal outcomes.  First-turn time, never
  result-fetch time or first changed action, defines membership.
- **Prospective sample / rules**: primary is authenticated official per-game
  rating delta over all assigned games.  One harm look at 30 resolved official
  games per arm rejects if the official candidate-control 95% CI is wholly
  negative, or if candidate negative-outcome rate is at least 10 percentage
  points worse with a wholly positive CI.  Fixed final read is 100 official
  games per arm, with at least 20/arm per message mode, 15/arm per
  seller-knowledge configuration, 15/arm per price scale, and 10/arm in every
  mode x seller-knowledge intersection.  Promote only if the official CI is
  wholly positive, normalized-payoff point delta is positive, zero- and
  negative-outcome point deltas are nonpositive, every mode, knowledge, scale,
  and deployed-host point estimate is nonnegative, and mechanism, scope, wire,
  duplicate/self-play, invalid, unresolved, and official-join failures are
  zero.  A final CI crossing zero or an underpowered deadline read remains
  research-only.
- **Mechanism contract / diagnostics**: replay every state in the first 20
  assigned games with the flag OFF and ON.  Any control difference, hash drift,
  non-target fire, candidate purchase without a strict prior decline and
  current strict positive, changed direction other than `no -> yes`, or changed
  action without its adjacent trace is immediate mechanism rejection.  Report
  purchase count, normalized payoff, zero/negative outcomes, first-decline
  round, mode, knowledge, scale, host, and named/hidden opponent without
  conditioning the primary analysis on triggers or purchases.  Local
  percentile and fixed-stream payoff are diagnostic only.
- **Frozen stack / deployment boundary**: initial research hosts may be Test 1,
  Agent 5, and Test 4 only after each naturally loads the pushed implementation
  and its exact current-stack checker reports
  `eligible>0/fired>0/action_changed>0`.  Test 2 and Test 3 remain unarmed.
  Freeze buyer-v2 on, tight prior `.65`, guard/strike/LCB/rank/selectivity/parser
  experiments off, and model/parser/CDF hashes
  `173e00273db5b2d5121080be0e6192c4ab12e1ea553b61ab22896bfb4a31787a`,
  `74971723391a35c5d30f44b98749c6d85e7aa60e6d83c7e8b61e641096bd7356`,
  and `bd3b313792951465624543612b09fb0ca5cc1708aee08a7a3dfb85f269e58ff9`.
  The observed pre-treatment structural cohort had 88 games / 1,760 turns;
  65 games / 406 turns reached the proposed predicate, and the frozen salt
  assigned 55 candidates of which 40 games changed 246 actions.  These are
  reach measurements only, not outcome evidence.  Record host-specific clean
  T0s before examining any official treatment outcome and never add Test 2
  after peeking without a separate prospective expansion rule.

## MECHANISM REJECTED — DISARMED

### Continuation-aware persuasion rank gate (Test 2)
- **Live window**: first observed fire `1787484376.458`; explicitly disarmed
  through `scripts/fleet.py` at `T1=1787570799` by setting
  `GLEE_PERS_RANK_GATE_AB=0`. Clearing the key was not a safe disarm because a
  launch environment could retain it. Test 3 was untouched.
- **Failure**: the arm reached all 12 tight buyer cells rather than the claimed
  eight, including every p=.8 treatment game; it could flip both directions,
  applied a recommendation-only DP to explicit declines, and pooled six
  official configurations per local CDF key. Live census: 267 treatment games,
  828 turn flips; 539 were unintended p=.8 buy-to-pass changes. One verified
  threshold-zero flip bought a low unit after “I do not recommend this one” and
  lost the full 1,000,000 unit price.
- **Decision**: mechanism rejection, not an effect estimate. Only 83/495 first-
  round eligible games have local finals and 412 remain unresolved. Do not use
  resolved-only local percentile or Test 2's aggregate rating to promote or
  salvage this arm.

## RUNNING — LIVE CAUSAL MEASUREMENT

### Hidden support-minimum share veto (negotiation, Test 3)
- **Flag / assignment**: `GLEE_NEGO_HIDDEN_MIN_SHARE_VETO_AB=1` on Test 3 only;
  `sha256("nego_hidden_min_share_veto_v1|" + game_id) & 1` gives control or
  candidate per game.
- **Eligible decision**: hidden, nonfinal, profitable offers below 40% of the
  minimum positive feasible ZOPA implied by our own type, and only when the
  frozen table/stall/continuation stack would otherwise accept. Control accepts
  byte-for-byte. Candidate rejects and uses the existing profitable-side
  counter. The terminal any-positive-cent rule is outside scope.
- **Deployment state / causal boundary**: pushed inert mechanism commit
  `6f7e79b`; Test 3 process naturally rotated onto it at 2026-08-24 19:22:14 IST
  (PID 73157). The first qualifying pre-action assignment is therefore the clean
  `T0=1787581117.643784` (2026-08-24 19:48:37 IST), not process start or overlay
  mtime. Game `99c476fc-5bce-44b0-af07-57382aec6160` was hash control, hidden
  cap-10 seller-.8, round 6: buyer offered `.85666667B`, paying `.05666667B`
  against the `.08B` support floor; direct TABLE accepted. The production/reader
  parity audit reports `mechanism_ok=true`.
- **Primary cohort / outcome**: every game from its first qualifying pre-action
  decision, with all agreements, zeros, walks, timeouts, invalid and unresolved
  outcomes retained. Primary outcome is authenticated-dashboard per-game rating
  delta joined by exact modal fingerprint and minute; local pooled percentiles
  are diagnostic only.
- **Decision rule**: final read at 100 resolved official games per arm and at
  least 20 per role per arm. Promote only if official-delta 95% CI is above zero,
  close-rate point delta is at least -5pp, both role point estimates are
  nonnegative, and mechanism/join failures are zero. One harm look at 30 official
  games per arm rejects if the official CI is wholly negative.
- **Read with**: `scripts/live_percentile.py --ab hidden-min-share-veto --since
  T0 --slots conceder --official-json FILE`.

## BUILT — DEFAULT OFF, WAITING FOR AN UNCONTAMINATED WINDOW

### Trend-confirmed TABLE versus continuation precedence (negotiation)
- **Flag / assignment**: `GLEE_NEGO_TABLE_VCONT_PRECEDENCE_AB=1`, default OFF;
  `sha256("nego_table_vcont_precedence_v1|" + game_id) & 1` gives direct-TABLE
  control or continuation candidate per game.
- **Identified trigger**: a hidden, profitable, nonfinal offer directly clears
  TABLE; at least three distinct echo-collapsed opponent prices show a positive
  concession trend; the existing continuation value exceeds accept-now surplus;
  the support-minimum signal is absent; and the next stall branch would not
  accept anyway. No-trend extrapolations from our own unplayed target are
  excluded.
- **Candidate**: suppress only TABLE's early return, then use the existing
  continuation rejection and existing profitable-side counter. Control remains
  byte-identical. The arm freezes HORIZON_V2, CONTINUATION_ACCEPT, TABLE,
  STALL_POLICY, and FINAL_OPTION=0.60, and fails closed against every overlapping
  negotiation experiment, including the running Test 3 arm.
- **Reachability / evidence**: latest 100,000 Test 3 turns contained 76 first-
  eligible games (about 25.5 per 1,000 negotiation games). Test 3's future
  control stack with the running veto explicitly absent produced 47 eligible,
  19 fired, and 19 changed actions over 1,500 paired games (seed 2411). Focused
  and all negotiation tests passed (79 and 363 respectively). The prospective
  official reader is now implemented as `--ab table-vcont-precedence`; it
  independently recomputes the trigger from state/plan, verifies direct-TABLE
  control and exact candidate counter wires, retains unresolved and every
  terminal outcome, rejects cross-fleet duplicates, and enforces the frozen
  official/close/stratum decision rule. Combined precedence/veto focused suite:
  83 passed.
- **Precommitted future rule**: do not co-arm with the support-minimum trial.
  After a clean window, final read at 100 resolved official games per arm and
  20 per role; one harm look at 30/arm. Promotion requires official-delta CI
  above zero, close-rate lower bound above -2pp, nonnegative role/horizon/type
  point estimates, and zero mechanism/join failures. Completed historical deals
  do not identify whether rejecting the guaranteed offer is beneficial.

## RUNNING RESEARCH-ONLY — PERSUASION BUYER BINARY POST-DECLINE PULSE

Frozen prospectively at 2026-08-24 23:41 IST, before inert commit, fleet
activation, assignment, or outcome.

- **Flag / assignment**:
  `GLEE_PERS_P033_R4_BINARY_POSTDECLINE_PULSE_AB`, default OFF;
  `sha256("pers_p033_r4_binary_postdecline_pulse_v1|" + game_id) & 1`
  assigns control/candidate once per game. A missing game ID fails closed.
- **Falsifiable hypothesis**: in buyer/player-2, binary, `p=1/3`, `v=4P`,
  `u=0`, 20-round games, a one-positive-message pause after post-decline
  positive-message precision reaches the exact 25% break-even boundary raises
  authenticated official per-game rating delta relative to the complete current
  buyer-v2 stack. The null is candidate-control official delta `<= 0`.
- **Pre-treatment cohort**: every structurally exact game is enrolled at its
  globally first buyer decision, before any recommendation, decline, purchase,
  pulse, quality, termination, or outcome can select it. All three price scales
  and both seller-knowledge configurations are included. Seller knowledge is
  not observable to the buyer and is never a production gate; authenticated
  terminal evidence supplies that frozen subgroup label.
- **Candidate action**: compute the full control plan first. After the first
  strict binary `no`, count only bought strict-`yes` outcomes. If `L>=3` and
  `3H-L<=0`, change only a current strict-`yes` control purchase to a pass. That
  consumes the pulse. Control resumes immediately, and the same evidence cannot
  pulse again; only a newly bought strict-`yes` low can arm another future pulse.
  Passed/current qualities never enter. Metadata and the
  `p033_r4_binary_postdecline_pulse` gate appear only beside a real `yes -> no`
  action change. Hash controls and every nontriggering candidate are byte-
  identical to the complete current persuasion stack.
- **Isolation**: fail closed against every optional buyer guard, strike, LCB,
  audit, rank, selectivity, parser, and uninformed-veto path or corresponding
  plan metadata. The live p=.8 seller prose/truth arms, p=.8 text decline veto,
  and p=.5 unlock are structurally disjoint. Bargaining and negotiation are
  outside scope and must not change.
- **Pre-treatment evidence only**: the all-assigned shadow cohort contains 58
  exact games / 1,151 buyer decisions, with 54 local finals and four unresolved.
  The pulse was reachable in 7/58 games and changed 27 frozen-stream turns. Its
  diagnostic mean effect was `-0.0556P` payoff and `+0.00382` local percentile;
  both intervals crossed zero. The absorbing alternative was rejected before
  implementation because it could double the zero rate and had observed
  fixed-stream harm as large as `-8P`. These are noncausal diagnostics and can
  neither promote nor reject the prospective arm.
- **Motivating case, not an allowlist**: in game
  `7896ee73-7dc1-4517-8922-15e2f8d713d2`, the seller first emitted three `no`s,
  then its bought `yes` stream reached post-decline `H=1,L=3` before round 9.
  The candidate would pulse on rounds 9, 11, 13, 16, 18, and 20 in the frozen
  sequence and finish `+1P` versus control `-1P`. Seller adaptation and the
  unresolved local final make this mechanism motivation only.
- **Mechanism gate**: before activation, each exact research stack must report
  `eligible>0`, `fired>0`, and `action_changed>0`. For each of the first 20
  assignments, replay every buyer turn with the exact host stack flag OFF and
  ON. Controls must be full-object identical; candidates may only change
  baseline `yes` to `no` on the independent pulse predicate with a complete
  adjacent trace. Any scope/hash drift, non-target/control fire, bought
  reconstructed pulse, missing trace, changed action without trace, invalid
  wire, overlapping buyer path, timeout caused by the mechanism, duplicate, or
  self-play contamination means immediate disarm and mechanism rejection.
- **Primary and retained outcomes**: authenticated official dashboard per-game
  rating delta, full-game intent-to-treat over every assignment. Purchases,
  refusals, positive/zero/negative/severe payoffs, timeouts, unresolved games,
  invalid finals, and immediate terminal actions all remain. Local same-cell
  percentile and fixed-stream payoff are diagnostic only. Unresolved or invalid
  official joins block promotion; no analysis may condition on a decline,
  pulse, action change, purchase, completion, or success.
- **Harm look**: once, at 50 resolved official games per arm and at least four
  independently would-pulse games per arm. Reject if the official-delta 95% CI
  is wholly negative, or candidate negative-payoff rate is at least 10pp worse
  and its 95% CI is wholly above zero. No early efficacy promotion.
- **Fixed final**: 325 resolved official games per arm, at least 12 would-pulse
  games per arm, at least 30/arm/price scale, and at least 50/arm in each
  seller-knowledge configuration, plus at least 30/arm on each of the two
  research hosts. The conservative target gives about 80%
  power for a 1.0 official-rating/game effect at planning SD 4.55. At the recent
  two-research-host arrival rate it requires roughly 180 hours; deadline-
  truncated evidence is underpowered and cannot promote.
- **Promotion**: official candidate-control 95% CI wholly above zero; normalized
  payoff point nonnegative; zero, negative, and severe (`payoff/P <= -2`) rate
  points nonpositive; every price, knowledge, and research-host official point
  nonnegative; assignment/official joins fully resolved; and all mechanism,
  replay, contamination, duplicate, and self-play checks clean. Otherwise keep
  research-only or reject under the frozen rules.
- **Deployment boundary**: after inert code is pushed and naturally loaded,
  arm only `champion` (Test 1) and `composite` (Agent 5) at separate clean host
  timestamps using fleet tooling. `randomized` (Test 4) runs a custom policy
  that bypasses `persuasion.py`; the corrected probe-aware checker reports
  `fired=0/action_changed=0`, so a present flag there would be inert. Test 2,
  Test 3, and Test 4 stay unarmed. Never restart or signal a process. Freeze an
  immutable pre-activation stack snapshot, then read each host separately with
  `scripts/read_pers_p033_r4_binary_postdecline_pulse.py --slots HOST --since
  HOST_T0 --control-slot HOST --stack-snapshot SNAPSHOT --official-json FILE`.
- **Live research boundary (25 Aug)**: pushed code loaded naturally on composite
  PID 11293 at 00:50:02 IST and champion PID 11357 at 00:50:52; no process was
  restarted or signalled. Post-load exact-stack preflight returned
  `12 eligible / 7 fired / 7 action_changed` over 800 paired games on each.
  Snapshot commit `35ff05e` froze both complete stacks at
  `1787599546.549658`. Fleet tooling armed only champion from
  `T0=1787599611.224363327` and composite from
  `T0=1787599624.328448057`; Test 2, Test 3, and Test 4 remain unarmed. Separate
  readers through approximately `1787600226` found no post-T0 structural
  assignments yet, so live emitted behavior is still awaiting its first exact
  game and the first-20 assignment audit remains mandatory.
- **External reset and re-arm era (25 Aug)**: an external fleet write at
  `T1=1787600396.5521495` set all persuasion experiment flags to zero and ended
  both original host eras. The original window contains one exact assignment:
  composite candidate `86d71fde-0bcc-4d7d-80f3-470b3bb3cdcc`, with all 20
  turns present, no reachable pulse, no trace, and no action change. It remains
  in ITT. Snapshot `ae7b913` was invalidated before activation when a concurrent
  negotiation-owned restore changed the complete stacks; the hash interlock
  refused deployment, so that snapshot defines no treatment era. The restored
  stacks were refrozen prospectively at `1787601285.818645` in snapshot commit
  `16161f6`. Fresh exact-stack reachability was `12/7/7` on each host and no
  target game was in flight. Fleet tooling re-armed only champion from
  `T0=1787601319.884793282` and composite from
  `T0=1787601338.633884907`; Test 2, Test 3, and Test 4 remain explicit zero.
  PIDs did not change and immediate post-T0 scans found zero current-era
  assignments. Original and current eras must be read separately with their
  own immutable snapshots and upper/lower boundaries; the frozen harm/final,
  subgroup, mechanism, and promotion rules are unchanged.

## READY, DEFAULT OFF — bargaining discounted reject/counter consistency

- **Prospective Test 4 host amendment (25 Aug, before activation/outcomes)**:
  per operator direction, host this arm on Test 4 (`randomized`) only, not Test
  2 or Test 3. Live launch records and `control.json` show that the slot label
  is historical: Test 4, like every slot, is already overridden to effective
  policy `champion` across all three families. At the same clean boundary set
  `GLEE_BARG_DISCOUNT_NO_REGRESS_AB=1`,
  `GLEE_BARG_OBSERVED_GAIN=0`, and
  `GLEE_PROBE_RANDOMIZED_BARG_BASE=0`. The explicit OBSERVED_GAIN zero removes
  an unproved second bargaining treatment; the explicit router zero prevents a
  future policy-override removal from silently changing Test 4's behavior.
- **Flag / assignment**: `GLEE_BARG_DISCOUNT_NO_REGRESS_AB=1`; SHA-256 of
  `barg_discount_no_regress_v1|<game_id>`, low bit 1 = candidate. Assignment is
  per game and recoverable through the production pure helper. The older
  `GLEE_BARG_NO_REGRESS` must remain `0`; the new arm fails closed if it is on,
  so a nominal guard cannot contaminate hash controls.
- **Pre-treatment trigger**: the current full policy has decided `Reject`, our
  standing offer is strictly positive, our discount is strictly below 1, a
  nonfinal round remains, and the exact
  wire-coerced offer that the same policy would send after rejection satisfies
  `next_counter_share * delta_me <= offered_share`. Both hash arms compute and
  log this signal before the candidate changes the decision. The first such turn
  is therefore assignment-independent: controls retain the baseline reject;
  candidates accept the standing offer. `delta_me=1` is deliberately excluded.
- **Measured motivation**: complete latest-12h Test 2 + Test 3 logs contain 49
  first triggers with `delta_me<1`; immediate acceptance beats the realised
  final in 49/49, by mean `+0.03326` pot share (95% CI
  `[+0.02722,+0.03930]`) and diagnostic `+0.02005` fitted percentile
  (`[+0.00752,+0.03259]`). The excluded `delta_me=1` row averaged `-0.0505`
  pot share (n=16), so broad nominal no-regression is not justified.
- **Primary cohort / outcome**: every game's globally first eligible turn,
  including later agreements, no-deals, zeros, unresolved outcomes, and both
  roles/horizons. Primary is authenticated dashboard per-game rating delta;
  payoff share and the checked-in pooled bargaining-CDF percentile are
  diagnostics because CDF v3 omits discount factors. Never condition on an
  agreement, an action change, or a candidate accept.
- **Reader**: `scripts/live_percentile.py --ab barg-discount-no-regress --since
  T0 --slots randomized --official-json FILE`. It cohorts on the logged pre-action
  trigger rather than result-fetch time, keeps cold missing finals unresolved,
  removes cross-fleet duplicate game ids from the pooled estimate, recovers the
  hash independently, and audits candidate `accept` / control `reject` wires
  plus adjacent trace gates.
- **Harm look**: once at 30 resolved official games per arm. Reject immediately
  on any assignment, wire, trace, duplicate/self-play, or official-join failure.
  Otherwise reject for harm only if the official-delta 95% CI is wholly negative
  or the candidate zero-rate difference is at least +5pp with its 95% CI wholly
  above zero. No early efficacy promotion.
- **Fixed final**: 100 resolved official Test 4 games per arm and at least 15
  per arm for both `delta_me=.90` and `.95` (the `.80` trigger is too rare for a
  feasible quota). Promote only if
  official candidate-control 95% CI is above zero; payoff-share and local-
  percentile points are positive; close-rate lower 95% bound is above -2pp;
  Alice, Bob, known-horizon, unknown-horizon, `.90`, and `.95` point estimates
  are all nonnegative; every assigned outcome and official join
  is resolved; and mechanism/duplicate/self-play failures are zero.
- **Reachability**: under Test 4's actual `champion` launch policy, with the
  prospectively required OBSERVED_GAIN zero and router zero, the discount A/B
  produced `50 eligible / 16 fired / 16 changed` over 2,400 paired Test 4
  games. The gap between eligible and changed is the expected per-game hash
  control assignment.
- **Verification / deployment state**: focused mechanism, assignment, reader,
  overlap, zero-offer, patient-cell, Test 4 route, and cross-family isolation
  tests pass 26/26. Live nowhere; no flag, fleet process, `arms.json`, or
  `control.json` was changed by implementation. Deployment authority was later
  transferred to Codex: commit `8a8c5c9` was pushed and the three explicit Test
  4 values above were written to its live overlay; activation waits for the
  named zero-game cycle to load that commit. Test 1, Test 2, Test 3, and Agent 5
  remain unarmed for this bargaining experiment.

## DEPLOYING — deterministic discounted-counter guard (25 Aug)

- **Operator constraint / design**: no per-game hash, cell assignment, or
  randomized arm is active. `GLEE_BARG_DISCOUNT_NO_REGRESS=1` deterministically
  changes every reachable bargaining decision on its enrolled profile. The
  legacy `GLEE_BARG_DISCOUNT_NO_REGRESS_AB` and broad
  `GLEE_BARG_NO_REGRESS` flags are explicitly `0`; the deterministic guard
  fails closed if either is armed, preventing accidental overlap.
- **Behavior**: only after the baseline policy has chosen `Reject`, accept a
  strictly positive standing offer when a round remains, our discount is
  strictly below one, and the exact next wire-coerced counter multiplied by our
  one-round discount is no larger than the standing offer. Patient
  `delta_me=1` games are excluded.
- **Retrospective basis, not a prospective causal result**: in the complete
  latest-12h first-trigger cohort on the two bargaining leaders, the discounted
  subset had `49/49` realised finals below immediate acceptance, mean
  `+0.03326` pot-share alternative (95% CI `[+0.02722,+0.03930]`) and
  `+0.02005` diagnostic percentile. The excluded patient subset was harmful:
  `-0.0505` pot share over 16 games. This motivates deployment but does not
  prove its future field effect.
- **Deterministic profile allocation**: candidate on Test 1 (`champion`), Agent
  5 (`hardliner`), and Test 4 (`composite`); protected controls on Test 2
  (`champion`) and Test 3 (`conceder`). All five still queue all three families.
  The cross-profile comparison is observational and noisier than a randomized
  experiment, but preserves the operator's no-randomizer rule and the
  max-of-five selection objective.
- **Verification**: commit `cc608f5` is pushed. Focused tests passed `32/32`;
  the bargaining-focused suite passed `165` with only the predeclared stale
  horizon-floor failure. Full suite: `1,738 passed`, with exactly the two
  predeclared failures (468 versus stale 450 horizon expectation, and live
  bargaining grid drift). Exact-stack reachability passed Test 1
  `11/11/11`, Agent 5 hardliner `14/14/14`, and Test 4 `31/31/31`
  eligible/fired/action-changed.
- **Clean evaluation boundary**: overlays were written at `Tcfg=1787604088`
  (02:11:28 IST), and safe cycles were requested at 02:11:35 for the three
  candidate slots. The old processes predate commit `cc608f5`, so the flag is
  inert until each replacement PID launches after the commit. Measure all
  bargaining games beginning at each verified replacement start; retain zeros,
  no-deals, both roles, and every discount/horizon cell. Compare realised
  same-cell percentiles and rating movement against both protected controls;
  do not condition on a deal or a guard firing. No efficacy claim exists before
  those post-boundary outcomes arrive.

## STOPPED — fleet-wide deterministic full-stack portfolio cutover (25 Aug)

- **Operator decision / stop boundaries**: every randomized and cell-specific
  experiment was first explicitly set to zero fleet-wide at
  `T1=1787600396` (2026-08-25 01:09:56 IST). Three narrow arms were subsequently
  restored on four slots, contrary to the later full-stack portfolio decision,
  and were explicitly disabled again at `T2=1787601952` (2026-08-25 01:35:52
  IST). Prospective readers must exclude new assignments after T1 and may not
  treat the brief restored interval as a promoted deployment. No stopped
  experiment may be interpreted as promoted.
- **Deterministic topology**: because competition placement selects the best
  complete agent, all five slots continue to queue bargaining, negotiation, and
  persuasion. The configured profiles are Test 1=`champion`, Agent 5=`hardliner`,
  Test 2=`champion`, Test 3=`conceder`, and Test 4=`composite`. The historical
  `randomized` name for Test 4 is only a slot/log label. LLM mode is off. Every
  arm overlay is byte-identical, with every `*_AB`, probe router, and
  observed-gain trial explicitly zero. Test 2 retains the winner stack because
  the hardliner transform would only replace its honest persuasion component
  with the historically weaker lie-heavy component under the canonical overlay;
  the hardliner challenger was moved to lower-rated Agent 5 before rotation.
- **Deployment safety**: all five named cycles were requested. Existing
  processes continue their pre-cutover launch shape until a zero-game/natural
  shift boundary; each replacement must be verified from its actual process
  command and launch record before the topology is called live. No process may
  be signalled while holding a game.
