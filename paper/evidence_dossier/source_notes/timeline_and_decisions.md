# GLEE project chronology and decision ledger

Status: private internal evidence dossier. This file is not manuscript prose and
should not be copied into the paper without claim-level review. It retains some
competitor handles for internal traceability and must be redacted before any
Git, Overleaf, artifact, reviewer, or public release.

Cutoff: 2026-08-30, after the official competition close and the latest local
paper review.

Manuscript scope boundary: this file preserves broader development archaeology,
but the paper is about Agent 5 only. Other profiles may be promoted into the
manuscript only when a test directly explains an Agent 5 component decision.
See `../AGENT5_ONLY_PAPER_SCOPE.md` for the binding inclusion rules.

## 1. Scope and the two clocks

This note deliberately keeps two histories separate:

1. The **competition-development timeline** records strategy design, tests,
   deployment, reversals, ratings, banking, and the official close. Its causal
   unit is a game or a policy decision, not a paper revision.
2. The **paper-review timeline** records how the manuscript framing, evidence
   boundaries, submission package, and reviewer objections changed after the
   competition work. A review finding is not evidence that a strategy worked,
   and a paper edit is not a competition event.

The development history is unusually dense. The repository contains 301
commits reachable from current `HEAD`, 317 unique commits across all refs, 15
local heads, and no tags. The visible history begins at commit `1298b9e` on
2026-08-20 and current `HEAD` is
`ead108352449089a32c0f6805479940052c99be1` from 2026-08-30. Sixteen commits
are retained only by historical worktree heads. The paper path appears in four
commits in this history: `3434ed5`, `fb07a0f`, `b8a5a87`, and `ead1083`.
Most current review artifacts are later working-tree records, not a clean
commit-by-commit manuscript history. Evidence: commit hashes above; the latest
frozen harsh-review receipt records exact source and PDF hashes at
`paper/review/harsh_review_2026-08-30/editorial_decision.md:11-24`.

Reproduction commands for the history counts:

```sh
git rev-list --count HEAD
git rev-list --count --all
git for-each-ref --format='%(refname)' refs/heads
git tag
git log --all --reverse --format='%H|%cI|%s'
git log --all --format='%H|%cI|%s' -- paper
```

### Evidence classes

| Code | Evidence class | Meaning |
|---|---|---|
| `STRUCT` | Structural or mathematical | Generator, protocol, support, or proved identity under stated assumptions. |
| `GIT` | Version-control record | Code or documentation existed at the named commit. It does not prove live exposure. |
| `OPS` | Operational record | Authenticated deployment, process, configuration, rating, bank, or close boundary. |
| `MECH` | Mechanism verification | Eligibility, firing, action change, exact replay, or wire-path check. It does not prove reward value. |
| `RCT` | Prospective randomized comparison | Stable per-game assignment and all-assignment outcome analysis. Sequential looks and power limits still apply. |
| `OBS` | Live observational cohort | Real games without randomized identification. Useful for behavior and localization, not component causality. |
| `RETRO` | Retrospective replay or shadow | Fixed-history alternative. Opponent response after a changed action is generally not identified. |
| `INVALID` | Invalidated instrument or selected analysis | A prior numerical result that must not support a claim. |
| `REVIEW` | Manuscript review evidence | What a panel or audit found about the paper, not what the agent achieved. |

### Causal-status codes

| Code | Permitted inference |
|---|---|
| `C0` | Record of implementation, deployment, or chronology only. |
| `C1` | Intended mechanism reached and changed the returned action. |
| `C2` | Descriptive association or behavior count. |
| `C3` | Randomized estimate, with the stated sample and analysis limitations. |
| `C4` | Pointwise or structural comparison identified under explicit assumptions. |
| `C5` | Invalidated, superseded, or contradicted. Do not reuse as positive evidence. |

## 2. Identity map: physical slots were not stable policies

The names Test 1, Agent 5, Test 2, Test 3, and Test 4 identify physical slots.
They do not identify one immutable strategy. The most consequential bookkeeping
error was reasoning from Test 4's historical slot name `randomized` even when
its actual process ran `champion`. The correction established that zero of five
agents then used the whole-policy randomizer
(`.ai/HANDOFF.md:3432-3439`; `.ai/FINDINGS.md:567-578`).

| Period | Test 1 / `champion` | Agent 5 / `composite` | Test 2 / `hardliner` | Test 3 / `conceder` | Test 4 / `randomized` | Evidence and status |
|---|---|---|---|---|---|---|
| Aug 20 early | Champion and revert point | Composite assembled from family winners | Hardliner development profile | Conceder and persuasion instrument | Specialist slot, later deleted and recreated | `GIT/C0`: `3f08a4b`, `c0b03e0`, `4ff569b`, `f031ca4`, `3e0fa5a`. Names denote slots and development roles only. |
| Aug 22 16:24 | Champion | Champion-equivalent | Champion-equivalent | Champion-equivalent | Configured equivalent but inactive | `OPS+MECH/C1`: byte-identical 39-flag baseline at `.ai/BASELINE.md:3-17` and `DIARY.md:237-241`. |
| Aug 25 01:35 | Champion | Composite | Hardliner | Conceder | Composite despite slot label | `OPS/C0`: max-of-five plan at `.ai/HANDOFF.md:3494-3515`. It was a selection portfolio, not a randomized trial. |
| Aug 25 01:55 onward | Champion | Hardliner challenger | Champion protected leader | Conceder | Composite, later hardliner in specific eras | `OPS/C0`: leader-protection correction at `.ai/HANDOFF.md:3517-3531`. |
| Final submitted profile | Separate account development profile | Focal `hardliner`, LLM off, with a deterministic family-specific overlay | Source of the final persuasion overlay | Development profile | Development and late challenger profile | `OPS/C0`: final bank manifest at `paper/data/submitted_agent_bank_manifest.csv:1-80`; Agent 5 persuasion copy at `.ai/HANDOFF.md:144-183`. |
| 2026-08-30 11:39Z snapshot | Champion, all families | Hardliner, bargaining only at that instant | Champion, all families | Conceder, all families | Hardliner, all families | `OPS/C2`: `.ai/CURRENT_STATE.md:3-42`. This snapshot predates the closing family changes and is superseded for final-state claims by `.ai/HANDOFF.md:6-24`. |

The safest paper terminology is therefore **physical profile**, **effective
policy**, **family topology**, and **dated overlay**. Do not use a slot name as a
strategy label without a process or manifest citation.

## 3. Competition-development timeline

### Era A: system bootstrap and rapid policy search, 20 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 20, 01:52 | The repository began with closed-form family solvers and total error containment. | `GIT/C0`: `1298b9e`. | Establishes the initial implementation boundary only. |
| Aug 20, 04:56 to 05:06 | Runtime flags and the separation of slot identity, policy, families, keys, and logs were added. | `GIT/C0`: `0d7fa88`, `4d2d985`. | This separation later enabled safe overlays, but also made slot-name reasoning unsafe. |
| Aug 20, 05:49 to 06:28 | A champion revert point was frozen, Agent 5's composite was rebuilt from per-family winners, three costly flags were removed, and bargaining was moved away from the field's exact half-pot atom. | `GIT/C0`: `3f08a4b`, `c0b03e0`, `78d46a8`. | These commits record intended changes, not isolated effects. |
| Aug 20 afternoon | Negotiation shifted toward close rate and curve-priced final offers; an offline arena, percentile-aware scoring, and evolutionary tuning were introduced. | `GIT/C0`: `43b35a4`, `d047f43`, `d5bc96d`, `9eb6b1d`, `ad2fa9c`, `2a7c80b`. | Later clone and replay defects mean early arena numbers cannot be treated uniformly as valid. |
| Aug 20, 16:46 to 18:47 | Endgame v3, lie-shading instrumentation, stall policy v2, evolved acceptance, and hardliner-style bargaining were added. | `GIT/C0`: `a13d9de`, `36ee441`, `bf95bff`, `141061f`, `191f3ef`, `10bfbde`. | Mechanisms were changing faster than the rating could equilibrate. |
| Aug 20, 19:15 to 19:40 | A persuasion hybrid was promoted and then removed 25 minutes later on fresh evidence. | `GIT/C5`: `2ea635a`, `8f1f6c4`. | Earliest clear example that promotion and reversal were part of development, not a clean ablation. |
| Aug 20, 19:43 to 22:49 | Persuasion moved to a dynamic-programming policy, then to LLM-assisted wording, buyer-v2 on Agent 5, and finally back to token templates after measurement. | `GIT+C2/C5`: `7a0ed3b`, `42e5e5f`, `80d4b95`, `fd05278`, `4b0f45e`, `7c893d1`; measured LLM conversion was 46.3% versus 55.3% for templates at `.ai/FINDINGS.md:165-170`. | The final system was LLM-free. LLM wording is a measured negative, not part of the winning narrative. |

### Era B: Agent 5 accumulation, safety gates, and early reversals, 20 to 21 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 20 late | Span-floor acceptance, horizon-aware language, and a combined stall-plus-span stack were built, then span plus stall was placed on Agent 5. | `GIT/C0`: `587ac30`, `a0c35f9`, `8d61ea6`, `0942009`. | Live deployment is not an isolated estimate because multiple gates changed together. |
| Aug 20 to 21 | Agent 5 received a 0.50 bargaining acceptance floor, dead-game harvesting, Bob offer logic, and discount-aware acceptance. | `GIT+MECH/C1`: `da7660c`, `9e3d0f9`, `48df9cd`, `1c69447`, `3eabd09`, `8689f49`; Bob-seat deficit and later reversal are summarized at `.ai/FINDINGS.md:112-115`. | Dead-game harvesting remained, but faster fishing later measured negative at `.ai/FINDINGS.md:254-260`. |
| Aug 21, 13:24 to 14:06 | Agent 5 received ultimatum share 0.80, a stonewall release, and margin weight 0.40. | `GIT/C0`: `7786b67`, `742f4c5`, `1b988d7`. | The apparent live-positive stonewall story did not survive. |
| Aug 21, 19:21 to 19:39 | Span invariant, economic-stall release, and Bob offers were deployed to Agent 5; the stonewall release was then reverted after about a 200-point divergence, with an explicit zero required for a real rollback. | `OPS/C5`: `ab6a226`, `8c77de2`, `8ad6703`; negative ledger at `.ai/FINDINGS.md:165-178`. | Clearing a key was not sufficient because launch values could reappear. Explicit zero became an operational invariant. |
| Aug 21, 19:12 | Gate tracing and a reachability checker were added. | `GIT+MECH/C1`: `6890e3f`; required deploy rule at `.ai/CURRENT_STATE.md:44-52`. | This did not prove efficacy. It proved that a proposed treatment could actually alter a returned action. |

### Era C: evidence reset and invalidated meters, 22 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 21 23:59 to Aug 22 00:05 | The shared evidence ledgers were created and an independent reviewer was added. | `GIT/C0`: `714825b`, `6ccc34d`; ledger rule at `.ai/FINDINGS.md:1-4`. | Hypotheses and validated findings were separated explicitly. |
| Aug 22 early | A randomized surplus-response probe was found to leak assignment into acceptance behavior and its analyzer joined the wrong turn. | `INVALID/C5`: `.ai/FINDINGS.md:202-217`; commits `c29a992`, `3a1bac7`, `22587ab`, `d20d2e4`. | The probe cannot identify acceptance probability for an offered share and must not appear as positive evidence. |
| Aug 22, 01:10 to 01:21 | A local arena initially made leaving only 10% of the visible span look best, then an adversarial audit showed that the clone granted unobserved greed, binned the wrong quantity, and selected on agreements. | `INVALID/C5`: initial result at `.ai/FINDINGS.md:355-419`; refutation at `.ai/FINDINGS.md:460-516`; commits `145d76f`, `c194beb`. | The heading "largest measured gain" is historical and explicitly superseded. The valid lesson is instrument failure. |
| Aug 22, 01:19 to 01:27 | Economic-stall behavior was reproduced as exploitable and its removal was positive in three arena seeds; the live flag was disabled. | `MECH+diagnostic/C1`: `.ai/FINDINGS.md:421-447`; commits `de6d6f7`, `d20d2e4`. | The adversarial worst case was larger than ordinary field damage, so do not report the attack as an average effect. |
| Aug 22, 02:08 onward | Per-game live percentile readers and within-agent game-hash A/B assignment were added. | `GIT/C0`: `c113255`, `dfe5b75`, `01c1af1`. | Later experiments still had sequential looks and join defects, so randomization alone did not guarantee a clean result. |
| Aug 22, 05:10 to 13:53 | Persuasion parser repairs and a fleet-wide backload arm were deployed; all-push beat backload by +0.391 percentile in strict profitable cells and the arm was killed. | `RCT/C3`: commits `04c78d5`, `2d5e920`, `9d5e86e`; result at `DIARY.md:249-253`. | Grouping by realized behavior rather than assigned arm had been a method failure; the corrected assignment supported rejection. |
| Aug 22, 15:44 to 16:25 | After no tested A/B won, all slots were reset to one behaviorally identical 39-flag champion baseline for a cross-agent noise measurement. | `OPS+MECH/C1`: `3f6b652`, `5dc2ef2`, `1079cdf`, `85e51c9`; `.ai/BASELINE.md:3-17`; `DIARY.md:237-241`. | Identical agents differed by about +/-125 rating, so many earlier cross-slot movements were below the noise floor. |
| Aug 22, 18:05 to 19:41 | A faulty safe restart and watchdog caused about 31 timeouts, four queue bans, and about 90 minutes of lost play. | `OPS/C5`: `DIARY.md:231-235`; fixes `a512ae3`, `628fe37`. | This is infrastructure damage, not policy evidence. |
| Aug 22, 22:30 onward | Constant simulated game IDs and a poor opponent clone were repaired; a local +82 parameter-search result was then withdrawn because it searched only inside the already-played concession regime. | `INVALID/C5`: `b765240`, `2247727`; `DIARY.md:219-229`. | A simulator fit only on the agent's support cannot discover an unplayed strategy regime. |

### Era D: rank-aware negotiation pivot, 23 to early 24 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 23, 00:24 | Test 4 received complete-information open claim 0.95 and claim floor 0.80 as a challenger. | `OPS/C0`: commits `1b40025`, `9d05761`, `9c58753`; deploy record at `DIARY.md:213-217`. | The hypothesis was higher share with possible close-rate cost, not an established win. |
| Aug 23, 01:22 | Hidden opponent values were algebraically reconstructed from completed deals, leading attention from close rate to surplus share. | `OBS/C2`: `DIARY.md:207-211`; `.ai/RIVAL_ANALYSIS.md:232-281`. | This sample conditions on agreement. It can describe closed deals, not hidden no-deal types or the value of refusing an offer. |
| Aug 23, 02:45 | A grid-aware hidden policy was rejected because its boundaries would have refused many deals and lowered retrospective percentiles in all six cells. | `RETRO/C5`: `DIARY.md:189-193`. | Its useful contribution was diagnosis, not deployment. |
| Aug 23, 03:33 to 04:15 | Hidden anchors and an observed-gain bargaining change were run on Test 4. Later analysis found the opening mechanism reached, but outcome evidence was underpowered; anchor gains were time-selection artifacts; the bargaining change could not affect the early rounds motivating it. | `OBS/C2`: `DIARY.md:159-181`. | Cutting on collection time rather than play time produced false positives. |
| Aug 23, 04:30 to 05:35 | A 30-hour Test 4 ratings blackout was fixed; a competing collector then exhausted request budget and briefly stopped moves. | `OPS/C5`: `DIARY.md:131-157`. | Missing snapshots and collector interference are not strategy results. |
| Aug 23, 06:55 | An uncapped concession creep was implemented but blocked before activation after review found the stall writer, not the concession schedule, owned most late prices; the relevant population was hidden-only and the alleged safety guard was unreachable. | `MECH/C5`: `DIARY.md:100-129`; commit `442f75e` records the block. | A NaN flag could also fail open into a zero-dollar offer and was fixed. The candidate was never a live result. |
| Aug 22 to 23 competitor audit | The first story was that top agents won by never conceding. A same-night seven-opponent comparison corrected this: opening and floor level tracked rating, while concession amount did not. | `OBS/C5 then C2`: initial claim at `.ai/RIVAL_ANALYSIS.md:8-71`; correction at `.ai/RIVAL_ANALYSIS.md:76-108`. | Use the corrected "level, not stonewalling" account. Opponent ratings plus direct games do not identify the tactic's causal value. |
| Aug 23 field drift | Opponent opening claims rose across recency windows, and a pooled persuasion pattern disappeared when cut by time. | `OBS/C2`: `.ai/RIVAL_ANALYSIS.md:181-228`. | Nonstationarity is a direct reason not to treat pooled historical comparisons as current causal effects. |
| Aug 24, 02:40 | A first-principles negotiation arm was deployed to Test 4, based on different complete and hidden generators, terminal proposer parity, and a large zero atom. | `STRUCT+MECH/C1`: `DIARY.md:17-79`; `ceef75f`, `767518d`. | The structural facts survived, but the full-policy promotion did not. |

### Era E: first-principles audit, leader imitation, and randomized clones, 24 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 24, 04:01 | A live wire-ownership bug was fixed after a bare rejection surrendered the zone; a property test was added so policy intent had to reach the wire. | `GIT+MECH/C1`: `f32c334`, `e0ca910`. | This is the origin of the returned-action framing. An internal plan was not accepted as behavior. |
| Aug 24 audit | The broad first-principles promotion was withdrawn after a first-turn intent-to-treat survivorship audit. Cold missing finals were also reclassified as collector backlog rather than abandoned losses. | `INVALID/C5`: `.ai/HANDOFF.md:1897-1992`; instrument correction at `.ai/FINDINGS.md:232-252`. | Strong cell-local structural logic did not justify a whole-policy effect claim. |
| Aug 24 hidden accept audit | A historical accept-all-profitable read changed from apparently positive to `-0.06628` exact percentile after actual later agreements were retained. | `RETRO/C5`: `.ai/FINDINGS.md:165-177`; `.ai/HANDOFF.md:1874-1895`. | The two estimates used different outcome handling. Only the corrected negative result may be cited. |
| Aug 24 afternoon | Hidden terminal counters, direct-leader openings, prose and truth probes, stale-stall, support-aware veto, and table-precedence experiments were built or staged behind exact scopes. | `GIT+MECH/C1`: commits `c1dec4d`, `8a21e8e`, `2f4989d`, `34a4367`, `6f7e79b`, `d1c5cb4`; scope examples at `.ai/HANDOFF.md:2997-3126`. | Most established reachability, not efficacy. Several stayed off to avoid overlapping treatments. |
| Aug 24, 20:47 | A broad hidden cap-10 buyer curve was briefly enabled on four profiles and stopped before a meaningful sample. | `OPS/C0`: `.ai/EXPERIMENTS.md:1023-1070`; commit `e007a90`. | Explicitly no causal verdict. |
| Aug 24, 20:47 | The supposed safe restart interrupted runners, caused held-game timeouts, and triggered a 30-minute queue suspension. | `OPS/C5`: `.ai/HANDOFF.md:3206-3214`. | Deployment outage, not evidence against the curve. |
| Aug 24, 22:28 to 23:14 | A game-hash randomized buyer clone copied directly observed behavior from four leading profiles. At the fixed 91-game checkpoint, candidate was +1.116 rating/game versus +0.247 control, but the nominal interval crossed zero, no-deals were 6.14 percentage points worse, and Agent 5's stratum was negative. The arm stopped. | `RCT/C3, no promotion`: `.ai/EXPERIMENTS.md:1072-1184`; commits `c755ec9`, `11e1af8`, `0261557`. | The failed broad clone does not prove that every narrower observed-leader fallback was harmful, but it cannot be called a win. |
| Aug 24 late | A fresh hidden cap-10 scoped clone retained a positive early point estimate, but at 9 candidate and 16 control games it was below the frozen harm look and failed the every-host condition on Agent 5. | `RCT/C3, underpowered`: `.ai/EXPERIMENTS.md:1186-1260`. | This was hypothesis generation, not promotion evidence. |

### Era F: deterministic portfolio and Agent 5 final strategy lineage, 25 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 25, 00:16 | An exact Athena transcript sidecar matched none of 2,638 recent buyer states and was kept undeployed. | `MECH/C5`: `.ai/HANDOFF.md:3353-3364`. | Literal transcript copying would have been a zero-reach placebo. |
| Aug 25, 01:24 to 01:55 | The fleet moved from scoped experiments to deterministic specialists, briefly restored two negotiation trials by mistake, then adopted a max-of-five all-family portfolio and protected Test 2 while making Agent 5 the hardliner challenger. | `OPS/C0`: `.ai/HANDOFF.md:3453-3531`. | The single-family map was superseded before landing because the account was ranked by its best complete profile. |
| Aug 25, 05:54 | A deterministic first-principles component owned three negotiation cells: complete one-round seller, complete cap-10 buyer, and hidden one-round seller. | `STRUCT+MECH/C1`: `.ai/HANDOFF.md:3533-3578`; commit `9a23ed8`. | Historical positive-cent acceptance was selected mechanism evidence, not live effect identification. |
| Aug 25, 06:08 | Agent 5's negotiation became a whole deterministic dispatcher: first-principles precedence in three cells, observed-leader buyer policy elsewhere, and current seller fallback where no replacement was identified. Wire coercion recomputed and protected owned actions. | `GIT+MECH/C1`: `.ai/HANDOFF.md:3580-3609`; commit `f9edc20`. | This is the central final negotiation strategy description. It is an ordered portfolio, not a universal theorem. |
| Aug 25, 06:21 | Hidden seller asks were used as conditional upper bounds on reservation value for cap-10 terminal buyer bids; Agent 5 activated the whole policy at a clean boundary. | `STRUCT+OPS+MECH/C1`: `.ai/HANDOFF.md:3611-3652`; commit `b29f7a5`. | The inference is conditional on individually rational offers and does not reveal the hidden type exactly. |
| Aug 25, 06:34 to 07:29 | Three Bob/H12 commitment components were built. Only the message-off, own-discount .95 six-offer ladder was judged defensible and then activated on Agent 5. | `STRUCT+MECH+OPS/C1`: `.ai/HANDOFF.md:3654-3718`, `.ai/HANDOFF.md:3737-3760`; commit `ca79aa7`. | A terminal-cent demand was not guaranteed: later pooled audit found 8 accepts in 10 reached games at `.ai/HANDOFF.md:4006-4036`. |
| Aug 25, 07:04 to 09:58 | Agent 5's negotiation overlay was mirrored to Test 2, and Test 3 and Test 4 were temporarily cloned from Agent 5 for a common-policy observation. | `OPS/C0`: `.ai/HANDOFF.md:3720-3790`. | Transition-era games cannot estimate an effect because overlays and launch profiles changed at different times. |
| Aug 25, 11:31 | The common hardliner observation retained 1,028 terminal games across Test 3, Agent 5, and Test 4. It described family outcomes but could not assign differences to the cloned policy. | `OBS/C2`: `.ai/HANDOFF.md:3792-3837`. | Host and composition differences remained observational. |
| Aug 25, 12:48 | A percentile fitter was found to retain only the top 2,000 values in saturated cells, deleting zero atoms and reversing apparent weak cells. It was fixed without rewriting the live model. | `INVALID then GIT/C5`: `.ai/HANDOFF.md:3839-3881`; commit `d0a9ada`. | Any earlier fitted-percentile claim using the dirty model is invalid, although raw enrollment and outcomes remain usable. |
| Aug 25, 15:52 | Under the same code, Test 3 rebounded across all three families; Agent 5 bargaining and persuasion improved while negotiation fell. | `OBS/C2`: `.ai/HANDOFF.md:4006-4019`. | Direct evidence of composition-sensitive seesawing, not a policy regression. |
| Aug 25 high-share chain | A post hoc 35-to-0 bargaining replay motivated a high-share delay guard, which was deployed to Agent 5 but initially proved unreachable. A later current-stack audit showed accepting early was worse in all 45 joined triggers because the P2 commitment owner already secured better later agreements. | `RETRO+MECH/C5`: initial signal at `.ai/FINDINGS.md:68-93`; deployment at `.ai/HANDOFF.md:1212-1287`; unreachable finding at `.ai/HANDOFF.md:846-866`; final supersession at `.ai/FINDINGS.md:6-18`. | Do not report the 35-to-0 result without the 45-to-45 reversal. The enabled-looking flag did not own the action path. |
| Aug 25 to 26 Test 2 | Test 2 received support V2 and then V3, an exact round-99 acceptance, and persuasion credibility components. | `GIT+MECH/C1`: `ddb26d2`, `2e2a0e7`, `6ebd057`, `f7188ac`, `96671bb`; deploy lineage at `.ai/HANDOFF.md:868-1064`. | V3 versus V2 was not a randomized promotion and several efficacy reads remained incomplete. |
| Aug 25, 19:49 to 23:01 | Agent 5's overall 2505 peak lock was armed. It crossed 2506.72, but 15-minute monitoring missed the exact peak and the eventual bank was 2490.75. Minute-level banking was then implemented fleet-wide. | `OPS/C2`: `.ai/HANDOFF.md:4269-4323`; commits `457cc91`, `a530dd6`. | Banking protects a displayed state but cannot freeze it exactly because in-flight games settle after the observation. |

### Era G: peak protection, Test 4 specialization, and activity constraints, 26 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 26, 09:43 to 10:43 | At operator direction Agent 5 restarted on all three families and reached a fresh authenticated overall 2513.66, rank 1 at that instant, then entered lossless bank. | `OPS/C2`: `.ai/HANDOFF.md:737-778`. | This was a transient authenticated peak, not the final rank and not a component effect. |
| Aug 26, 11:06 to 11:28 | The operator superseded the overall lock, resumed Agent 5, and armed a negotiation-only bank at 2720. | `OPS/C0`: `.ai/HANDOFF.md:674-735`; commit `00cf4a5`. | Overall, bargaining, and persuasion could no longer trigger the bank. |
| Aug 26, 12:54 | Test 4 bargaining and negotiation were frozen at 2684.18 and 2724.71 after a clean lossless drain; Test 4 continued persuasion only. | `OPS/C2`: `.ai/HANDOFF.md:647-672`. | Frozen ratings are operational checkpoints, not proof of the last policy's effect. |
| Aug 26 afternoon | Test 4 received deterministic direct-decline persuasion repairs, a round-97 low-share negotiation guard, and a V3 successor; its negotiation was later frozen at 2914.38. | `GIT+OPS+MECH/C1`: `.ai/HANDOFF.md:479-645`; commits `9dab121`, `b3f1615`, `cd5b6ee`. | The persuasion repair established parser/action consistency in selected warnings, not a causal rating lift. |
| Aug 26, 17:33 | Test 2's tight-credibility-reset controller launched as a deterministic one-slot challenger. | `OPS+MECH/C1`: `.ai/EXPERIMENTS.md:435-525`; commits `985ead2`, `b9a7275`. | Its final efficacy gate required 2,000 assignments and was never completed cleanly before later crossover. |

### Era H: activity-defense seesaw and late negative results, 27 to 28 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 27, 16:45 to 18:49 | Agent 5 played 79 all-outcome activity-defense games with its locked overlay. Bargaining gained 21.03 rating, negotiation lost 33.78, and persuasion lost 29.42, moving overall from about 2592.11 to 2578.05. | `OBS/C2`: `.ai/HANDOFF.md:318-342`. | This is the clearest single dated seesaw. Retaining the negative families prevents selection on the good bargaining slice. |
| Aug 27 | The current-stack bargaining audit rejected the high-share override, and a persuasion seller repair remained a fixed-history shadow. | `RETRO/C5`: `.ai/HANDOFF.md:376-424`; `.ai/FINDINGS.md:6-51`. | Reach and low conversion among selected actions do not identify a future repair effect. |
| Aug 27 | Test 2 seller-terminal push was implemented, briefly run, and operator-terminated without an efficacy verdict. | `OPS/C0`: `.ai/EXPERIMENTS.md:341-434`; `.ai/HANDOFF.md:426-477`; commit `24250a6`. | Do not revive it as a win because the experiment ended before its frozen final read. |
| Aug 28, 04:26 | A fixed-boundary opponent archive was added for disclosed priority opponents, retaining all outcomes and refusing weak anonymous matches. | `GIT+OBS/C1`: `.ai/HANDOFF.md:4463-4501`; commit `4131e5d`. | It is behavior intelligence, not proof that copied tactics caused leader ratings. |
| Aug 28, 04:50 | A deterministic one-round seller-cent owner was standardized across the fleet. On Test 2 and Agent 5 it changed zero wires because their whole policies already emitted the same prices. | `STRUCT+MECH/C1`: `.ai/HANDOFF.md:4503-4540`; commit `cd94171`. | Standardized ownership is useful even when incremental behavior change is zero. |
| Aug 28, 07:18 | Test 4's complete-information unknown-horizon buyer score floor went live and fired correctly. | `OPS+MECH/C1`: `.ai/HANDOFF.md:4643-4664`; commit `bf85c73`. | Mechanism proof did not imply outcome efficacy. |
| Aug 28 later | The score-floor challenger was rejected after 27 resolved fires produced seven agreements and 20 no-deals versus a prior cohort's 23 agreements and five no-deals. The 82.1% to 25.9% close collapse was era-confounded but large enough to prohibit promotion and authorize explicit-zero rollback. | `OBS/C5`: `.ai/HANDOFF.md:4666-4700`. | The proposed broad round-95 acceptance repair also reversed sign on the preperiod and was not bundled. |
| Aug 28, 21:42 onward | A dynamic stopping guard accepted a profitable standing offer after ten exact mutual-stasis cycles only if its seed-CDF midrank was at least .50. Retrospectively, 21 of 389 pooled games would change with positive descriptive lift. | `RETRO+MECH/C1`: `.ai/HANDOFF.md:255-316`; commits `fe7e435`, `b54cb33`. | The retrospective estimate was not randomized. In live production, the first four ten-cycle offers all ranked below .50, so zero fires were correct and the gate was not lowered (`.ai/HANDOFF.md:185-216`). |

### Era I: final bank, final profile, and official close, 29 to 30 August

| Date and event | What happened | Evidence class and causal status | Contradiction, supersession, or lesson |
|---|---|---|---|
| Aug 29, 10:57 IST | Agent 5 copied Test 2's exact persuasion overlay and launched all three families from commit `b54cb33`. The Test 2 reset study was short of its frozen final read and later contaminated, so this was an operator-directed prospective boundary, not an evidence-based causal promotion. | `OPS/C0`: `.ai/HANDOFF.md:144-183`; final source receipt at `paper/data/submitted_agent_bank_manifest.csv:1-7`. | The final persuasion choice was operationally exact but empirically unresolved as an isolated component. |
| Aug 29 pre-close focal window | The first complete bounded final-profile window contains exactly 63 games: 19 bargaining, 19 negotiation, and 25 persuasion, with 787 own actions and zero logged errors. | `OBS/C2`: `paper/data/final_policy_era_census.csv:1-4`. | This was the denominator available to the first paper review. It is not the complete closing-window census. |
| Aug 29, 18:18 IST | Agent 5 completed minimum final-day family quotas and banked. Persuasion played 16 games and ended 2344.79/15,481; bargaining played 11 and ended 2603.81/15,487; negotiation played 10 and ended 2620.36/15,415. | `OPS/C2`: `.ai/HANDOFF.md:4702-4727`. | The extra bargaining and persuasion games came from queue races, not deliberate cherry-picking. |
| Aug 29, 18:26 and Aug 30, 02:49 | A separate profile, `The One & Only`, launched with Agent 5 bargaining and negotiation plus Test 2 persuasion, first bounded and then continuous. | `OPS/C0`: `.ai/HANDOFF.md:76-140`. | The assembly was explicitly observational and had a fresh low-rating account. It did not produce Agent 5's submitted endpoint. |
| Aug 29 23:58 UTC | The last pre-close public snapshot had the participant account first in the agent track, second on the combined board, at 2522.99. | `OPS/C2`: `paper/data/submitted_agent_leaderboard_snapshot.csv:1-2`. | This was not final. Winner language based on it became false after close. |
| Aug 30 closing window | A second complete window added 152 bargaining assignments and 30 persuasion assignments, one of which timed out. Combined with the earlier 63, the two-window census is 245 assignments, 244 rated games, one timeout, and 2,288 own actions. | `OBS/C2`: `paper/data/final_policy_two_window_census.csv:1-6`; summary at `paper/README.md:41-48`. | The added window had no negotiation assignments. It expands behavior coverage but does not convert the selected windows into a held-out efficacy study. |
| Aug 30, 12:28 UTC post-close snapshot | The account finished second in the agent track and third on the combined board. The focal profile endpoint was 2590.02 after 46,564 rated games, with family ratings/counts 2804.82/15,639 bargaining, 2620.36/15,415 negotiation, and 2344.87/15,510 persuasion. | `OPS/C2`: `paper/data/submitted_agent_leaderboard_snapshot.csv:1-3`; `paper/README.md:41-48`. | This validates the adaptive account trajectory, not any single component or the last 245 selected assignments. |
| Aug 30, 16:38 to 17:33 IST | After close-window play, Agent 5 was changed from bargaining-only to bargaining plus persuasion and then all three families. The all-three runner loaded, but the platform rejected new games because the competition had closed at 11:59:59 UTC. Final authenticated family readings were 2804.8/15,639, 2620.4/15,415, and 2344.9/15,510. | `OPS/C2`: `.ai/HANDOFF.md:6-74`. | `.ai/CURRENT_STATE.md:19-24` is an earlier bargaining-only snapshot and must not be cited as the final topology or exact final ratings. |

## 4. Reconciliation of the 63-game and 245-assignment cohorts

These numbers answer different questions and are nested rather than
contradictory.

| Object | Selection boundary | Family composition | Games or assignments | Own actions | What it supports | What it does not support | Source |
|---|---|---:|---:|---:|---|---|---|
| Pre-close final-profile cohort | 2026-08-29 05:27:36Z to 12:48:08Z | B 19, N 19, P 25 | 63 | 787 | A complete bounded census of the first final overlay exposure, including family actions, roles, outcomes, and zero logged errors. | Lifetime behavior, official-close behavior, or component efficacy. | `paper/data/final_policy_era_census.csv:1-4` |
| Official-close added window | 2026-08-30 11:08:31Z to 11:59:57Z | B 152, P 30, N 0 | 182 | 1,501 | A complete local closing-window action and outcome census. | Complete process-to-commit provenance, negotiation behavior in the closing hour, or a representative sample of the lifetime trajectory. | `paper/data/final_policy_two_window_census.csv:5-6` |
| Combined two-window census | Union of the two declared windows | B 171, N 19, P 55 | 245 | 2,288 | Returned behavior and outcomes for both complete bounded windows; 244 public rated increments and one timeout. | All-owner conformance, server receipt for every action, or a frozen-policy effect estimate. | `paper/data/final_policy_two_window_census.csv:1-6`; `paper/review/harsh_review_2026-08-30/panel_adjudication.md:16-24` |
| Lifetime focal endpoint | Public cumulative counts at official close | B 15,639, N 15,415, P 15,510 | 46,564 rated games | Not fully retained at action level | Adaptive trajectory scale and official endpoint. | Behavior of one fixed policy or causal credit for the final overlay. | `paper/data/submitted_agent_leaderboard_snapshot.csv:1-3` |

Arithmetic check: 63 + 182 = 245 assignments; 787 + 1,501 = 2,288
own actions; 245 - 1 timeout = 244 rated public increments. The 63-game
denominator should remain when discussing the original pre-close final overlay.
The 245 denominator should be used only for the named union of the two complete
windows. Neither should be called the 46,564-game history.

## 5. Agent 5 rating and bank chronology

Displayed ratings are stateful, opponent-adjusted, and nonstationary. The table
is therefore a descriptive chronology only.

| Timestamp | Bargaining | Negotiation | Persuasion | Boundary | Evidence and causal status |
|---|---:|---:|---:|---|---|
| 2026-08-25 04:07 | 2122.69 | 2060.42 | 2471.17 | Pre-transition snapshot | `OBS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:1-2`. |
| 2026-08-25 05:17 | 2204.31 | not recorded | not recorded | High-share checkpoint | `OBS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:3`. The later current-stack audit reversed the motivating high-share claim. |
| 2026-08-25 05:39 | 2222.34 | not recorded | not recorded | High-share checkpoint | `OBS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:4`. Do not attribute the rise to an unreachable guard. |
| 2026-08-26 09:43 | 2495.94 | 2616.98 | 2372.56 | Post-transition restart | `OPS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:5`. |
| 2026-08-26 10:43 | 2471.96 | 2668.82 | 2400.19 | Overall 2513.66, transient rank 1, bank request | `OPS/C2`: `.ai/HANDOFF.md:737-765`; `paper/data/submitted_agent_rating_checkpoints.csv:6`. |
| 2026-08-26 11:06 | 2468.47 | 2663.29 | 2406.19 | Operator resume | `OPS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:7`; `.ai/HANDOFF.md:706-735`. |
| 2026-08-26 11:28 | 2460.07 | 2672.03 | 2392.22 | Negotiation-only 2720 bank armed | `OPS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:8`; `.ai/HANDOFF.md:674-704`. |
| 2026-08-27 16:45 | 2637.44 | 2823.94 | 2314.94 | Activity-defense start | `OBS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:9`; `.ai/HANDOFF.md:318-342`. |
| 2026-08-27 18:46 | 2658.47 | 2790.16 | 2285.52 | Activity-defense end | `OBS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:10`. Same overlay, B +21.03, N -33.78, P -29.42. |
| 2026-08-29 10:57 | 2589.21 | 2621.38 | 2304.67 | Final persuasion-copy boundary | `OPS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:11`; `.ai/HANDOFF.md:144-183`. |
| 2026-08-29 18:18 | 2603.81 | 2620.36 | 2344.79 | Pre-close family-quota bank | `OPS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:12`; `.ai/HANDOFF.md:4702-4727`. |
| Official close | 2804.82 | 2620.36 | 2344.87 | Second agent track, third combined | `OPS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:13`; `paper/data/submitted_agent_leaderboard_snapshot.csv:3`. |

The chronology directly supports the claim that ratings seesawed. It does not
show that a given policy caused a rise or fall. The strongest same-code example
is Test 2 bargaining moving from fitted .5668 to .5038 across consecutive
six-hour windows with 99.6% agreement under an unchanged stack
(`.ai/FINDINGS.md:548-565`).

## 6. Strategy lineage by family

### 6.1 Bargaining

| Layer or decision | How it entered the final lineage | Evidence | Claim boundary |
|---|---|---|---|
| Finite bargaining benchmark | Closed-form alternating-offer recursion was present from the initial commit and later restricted in the paper to the finite complete-information domain. | `GIT+STRUCT/C4`: `1298b9e`; `paper/review/theory_code_audit.md:19-28`. | The public no-limit branch uses a synthetic boundary and is a heuristic, not a finite-horizon equilibrium. |
| Generic acceptance and Bob offers | The 0.50 acceptance floor, discount-aware refinements, and a Bob offer optimizer came from the early Bob-seat deficit. | `OBS+GIT/C1`: `.ai/FINDINGS.md:112-115`; `da7660c`, `1c69447`, `3eabd09`, `16258ea`. | Cross-era role improvement does not isolate any one subcomponent. |
| Economic-stall and stonewall removals | Both were disabled after exploit or negative evidence. | `MECH/C5`: `.ai/FINDINGS.md:165-178`, `.ai/FINDINGS.md:421-447`. | They are failures that shaped the final policy, not active winning heuristics. |
| P2/H12/.95 silent commitment owner | Six scheduled Bob shares culminate in an exact terminal-cent demand; decisions use a discounted common floor. | `STRUCT+MECH/C1`: `.ai/HANDOFF.md:3654-3707`; theory audit at `paper/review/theory_code_audit.md:27-28`. | Reached terminal-cent offers closed 8 of 10 pooled audited games, selected by reach. Not a causal success rate or guarantee. |
| High-share delay guard | Remained configured-looking in some states but was unreachable under the active commitment owner and later contradicted by 45 of 45 worse accept-now comparisons. | `MECH+RETRO/C5`: `.ai/HANDOFF.md:846-866`; `.ai/FINDINGS.md:6-18`. | Must not be described as an active evidence-backed improvement. |
| Final behavior | The two-window census contains 171 bargaining games, all agreements, with 1,001 bargaining actions and zero logged errors. | `OBS/C2`: `paper/data/final_policy_two_window_census.csv:2,5`. | Outcome census, not owner-level conformance or component efficacy. |

### 6.2 Negotiation

| Layer or decision | How it entered the final lineage | Evidence | Claim boundary |
|---|---|---|---|
| Structural feasibility | Reconstructed support has all six complete cells feasible and six of 16 hidden type pairs feasible under the independent-uniform model. | `STRUCT/C4`: `.ai/FINDINGS.md:95-109`; theory qualification at `paper/review/theory_code_audit.md:29-31`. | The earlier 12% infeasibility line in `.ai/NEGO_FRESH_START_PROMPT.md:77-92` is superseded. Live hidden joint frequencies are not identified. |
| First-principles terminal owners | Complete one-round seller, complete cap-10 buyer, and hidden one-round seller received explicit precedence. | `STRUCT+MECH/C1`: `.ai/HANDOFF.md:3533-3578`. | Cell-local structure did not validate the earlier broad first-principles promotion. |
| Hidden seller bound inference | Opponent seller asks provide conditional upper bounds used for terminal bids. | `STRUCT+MECH/C1`: `.ai/HANDOFF.md:3611-3632`. | Requires individually rational observed asks; corpus violations make it conditional evidence. |
| Observed-leader buyer behavior | Directly observed buyer paths filled supported non-structural buyer cells; current seller behavior remained fallback. | `OBS+MECH/C1`: `.ai/HANDOFF.md:3580-3609`; theory/code trace at `paper/review/theory_code_audit.md:40-49`. | Broad randomized imitation failed promotion. The retained narrower fallback's standalone value was not tested. |
| One-round seller cent standardization | A fleet-wide owner formalized complete visible-buyer minus one cent and hidden support asks. | `STRUCT+MECH/C1`: `.ai/HANDOFF.md:4503-4540`. | On Agent 5 it changed no wires because the active whole policy already matched it. |
| Final behavior | The pre-close final-profile cohort contains 19 negotiation games: 13 agreements, three walks, three no-deals, 190 own actions, zero logged errors. | `OBS/C2`: `paper/data/final_policy_era_census.csv:3`. | There were no negotiation assignments in the added official-close window. N=19 is a behavior census, not efficacy evidence. |

### 6.3 Persuasion

| Layer or decision | How it entered the final lineage | Evidence | Claim boundary |
|---|---|---|---|
| LLM-free templates | LLM wording was retired after lower conversion than templates. | `OBS/C5`: `.ai/FINDINGS.md:165-170`; `7c893d1`. | Development used LLM assistance, but the closing configuration was deterministic and LLM-off. |
| Costly-cell restraint and buyer posterior | DP and buyer-v2 introduced belief tracking; low lying in punished cells was an observed edge. | `OBS+GIT/C2`: `.ai/RIVAL_ANALYSIS.md:139-166`; `7a0ed3b`, `42e5e5f`, `4b0f45e`. | The one-shot obedience threshold is not a theorem for repeated noncommitted cheap talk (`paper/review/theory_code_audit.md:34-38`). |
| Explicit-decline veto | A final one-directional BUY-to-PASS safety layer was retained. | `MECH/C1`: `paper/review/theory_code_audit.md:37-49`. | Coverage and official rating value were not established. V2 and V3 were not banked on Agent 5. |
| Tight credibility reset | Test 2's buyer controller was copied exactly onto Agent 5 for the final overlay. | `OPS/C0`: `.ai/HANDOFF.md:144-180`; `paper/data/submitted_agent_bank_manifest.csv:72-80`. | Test 2 had only 1,086 assignments and 79 affected games before contamination, short of its final rule. The copy was operator-directed, not a causal promotion. |
| Final behavior | Across both windows, persuasion had 55 assignments, 54 rated outcomes, one timeout, 1,097 own actions, and zero logged errors. | `OBS/C2`: `paper/data/final_policy_two_window_census.csv:4,6`. | Action categories describe returned behavior but do not establish correct seller truthfulness, buyer optimality, or all-owner conformance. |

## 7. Competitor evidence and how it changed the strategy

| Competitor-derived observation | Development use | Evidence and causal status | Restriction |
|---|---|---|---|
| High-rated negotiators opened around 0.92 to 1.05 of visible surplus while our opening was about 0.681. | Motivated the 0.95 open-claim regime and later observed-leader buyer paths. | `OBS/C2`: `.ai/RIVAL_ANALYSIS.md:76-108`; `DIARY.md:213-217`. | Rating-opening correlation does not establish that opening caused rating. |
| The initial Opus-only story claimed never conceding was the key. | Triggered a regime-change search. | `OBS/C5`: `.ai/RIVAL_ANALYSIS.md:8-71`. | Superseded by the multi-opponent conclusion that level, not concession amount, tracked rating. |
| Direct paths from 7aidara, Alpha, Beta, and Gamma shared buyer patterns. | Supplied the randomized broad clone and later scoped hypotheses. | `OBS+RCT/C3`: `.ai/EXPERIMENTS.md:1074-1107`. | Direct behavior was observed, private source and hidden types were not. Broad clone failed promotion. |
| Two Clod cap-10 paths closed at the same terminal price and implied buyer type from payoff identity. | Motivated an early-curve experiment. | `OBS/C2`: `.ai/HANDOFF.md:3140-3152`, `.ai/HANDOFF.md:3160-3186`. | Two paths do not identify a universal timing exponent or cross-type policy. |
| Exact Athena transcript table had zero live reach. | Rejected literal transcript wiring. | `MECH/C5`: `.ai/HANDOFF.md:3353-3364`. | Copying observed states without a reachable state abstraction is not a strategy. |
| Late fixed-boundary archive retained disclosed Athena, Grok 4.6, and gill bates encounters. | Created a future observational intelligence base. | `OBS/C2`: `.ai/HANDOFF.md:4463-4501`. | Anonymous matches were deliberately not claimed; sparse direct data limited inference. |

## 8. Reversal and negative-result ledger

| Candidate or claim | Why it looked promising | Corrected verdict | Evidence class and exact source |
|---|---|---|---|
| Persuasion hybrid and LLM prose | Model-generated wording seemed more adaptive. | Hybrid was reversed quickly; templates converted 55.3% versus 46.3% for LLM wording. | `OBS/C5`: `2ea635a`, `8f1f6c4`; `.ai/FINDINGS.md:165-170`. |
| Stonewall release | Early arena-neutral and live-positive reading. | About 200-point divergence, reverted with explicit zero. | `OPS/C5`: `742f4c5`, `8c77de2`, `8ad6703`. |
| Economic-stall release | Intended to avoid endless bargaining. | Exploitable and modestly harmful; disabling it was positive on three arena seeds. | `MECH/C5`: `.ai/FINDINGS.md:421-447`. |
| Faster negotiation concession | Expected to raise close rate. | Corrected live-stack arena result remained negative at -0.0166 and -0.0182 and close rate fell. | `diagnostic/C5`: `.ai/FINDINGS.md:188-200`. The earlier magnitude was inflated by an overlay bug, but direction was not reversed. |
| ZOPA share 0.10 | Four arena runs looked positive. | Clone granted unseen greedy asks and selected on agreements; do not deploy. | `INVALID/C5`: `.ai/FINDINGS.md:380-419`, `.ai/FINDINGS.md:460-516`. |
| Backloaded persuasion | Appeared to manage trust. | All-push beat it by +0.391 in strict profitable cells; killed. | `RCT/C3, rejected`: `DIARY.md:249-253`. |
| Hidden accept-all-profitable | Old fixed-history reader gave +0.07138. | Corrected estimate was -0.06628 because later agreements after rejection were retained. | `RETRO/C5`: `.ai/FINDINGS.md:174-177`. |
| First-principles whole-policy promotion | Strong structural terminal cells. | Promotion withdrawn after first-turn ITT survivorship audit; keep only owned-cell claims. | `INVALID/C5`: `.ai/HANDOFF.md:1944-1992`. |
| Broad leader buyer clone | Candidate point estimate was positive. | Failed interval, no-deal, and every-host gates at 91 games; stopped. | `RCT/C3, no promotion`: `.ai/EXPERIMENTS.md:1169-1184`. |
| High-share delay guard | Post hoc 35 wins and zero losses among an earlier replay. | Unreachable under current owner; current stack showed accept-now worse in 45 of 45. | `RETRO+MECH/C5`: `.ai/FINDINGS.md:68-93`, `.ai/FINDINGS.md:6-18`. |
| Dirty saturated CDF | Suggested sudden weak bargaining cells. | Fitter retained only top tails and deleted zeros; prior fitted values invalidated. | `INVALID/C5`: `.ai/HANDOFF.md:3839-3860`. |
| Test 4 score floor | Mechanism could guarantee a seed-CDF floor for played counters. | Close rate collapsed in the live challenger; explicit-zero rollback authorized. | `OBS/C5`: `.ai/HANDOFF.md:4643-4700`. |
| Test 4 dynamic stop | Retrospective all-outcome census was positive. | Live offers did not meet the .50 rank gate, so zero fires were correct; no efficacy result. | `RETRO+MECH/C1`: `.ai/HANDOFF.md:185-216`, `.ai/HANDOFF.md:255-316`. |
| Final credibility reset copy | Mechanism was exact and Test 2 was the selected persuasion source. | Copied to Agent 5 despite the source experiment missing its final efficacy read. | `OPS/C0`: `.ai/HANDOFF.md:144-183`. |

## 9. Contradiction and supersession ledger

| Apparent contradiction | Reconciliation | Authoritative source |
|---|---|---|
| `.ai/CURRENT_STATE.md` says Agent 5 was bargaining-only at 11:39Z, while the close record says all-three configured. | Both are time-stamped. The state snapshot is pre-close-family-change; the later all-three launch occurred after the platform had closed and acquired no games. | `.ai/CURRENT_STATE.md:3-24`; `.ai/HANDOFF.md:6-74`. |
| The fresh-start prompt says roughly 12% of negotiation games are infeasible. | Superseded generator audit found 10 of 22 overall configurations, or 45%, structurally infeasible, with six of 16 hidden pairs feasible. | `.ai/NEGO_FRESH_START_PROMPT.md:77-92`; `.ai/FINDINGS.md:95-109`. |
| Rival analysis says stonewalling wins, then says it is the level. | The first claim generalized from one family. The seven-opponent analysis found opening level correlated with rating, while concession amount did not. | `.ai/RIVAL_ANALYSIS.md:8-71`, `.ai/RIVAL_ANALYSIS.md:76-108`. |
| ZOPA 0.10 is called the largest measured gain, then forbidden. | The first result used a biased negotiation clone. The adversarial audit invalidated the meter in the action region the candidate entered. | `.ai/FINDINGS.md:380-419`, `.ai/FINDINGS.md:460-516`. |
| First-principles terminal logic looked strongly positive, but promotion was withdrawn. | Structural or pointwise terminal ownership can be sound while whole-policy first-turn ITT evidence is selected or incomplete. | `DIARY.md:17-79`; `.ai/HANDOFF.md:1944-1992`. |
| Bargaining high-share replay was 35-to-0 positive, while the final audit was 45-to-45 negative. | The later P2 commitment owner changed the continuation. Under the current stack, waiting produced better agreements in every joined trigger. | `.ai/FINDINGS.md:68-93`; `.ai/FINDINGS.md:6-18`. |
| Test 4's slot is named randomized, but review states zero whole-policy randomizers were live. | Physical slot names persist across policy changes. The process command and control mapping determine the effective policy. | `.ai/HANDOFF.md:3432-3451`; `.ai/FINDINGS.md:567-578`. |
| The first paper review used 63 final-era games, while later material uses 245. | The 63-game pre-close cohort is a subset. A complete 182-assignment close window was later added, producing 245 total assignments. | `paper/data/final_policy_era_census.csv:1-4`; `paper/data/final_policy_two_window_census.csv:1-6`. |
| The account was first just before close but finished second. | The 23:58 UTC snapshot was pre-close. The post-close official snapshot changed the agent-track rank from 1 to 2 and combined rank from 2 to 3. | `paper/data/submitted_agent_leaderboard_snapshot.csv:1-3`. |
| Score-floor mechanism worked on its first fire but the policy was rejected. | Reachability and exact action change were correct; live outcomes were poor. Mechanism validity and efficacy are separate. | `.ai/HANDOFF.md:4643-4700`. |
| Agent 5 crossed 2506.72 but was banked at 2490.75. | The original monitor sampled every 15 minutes and in-flight games continued. Minute banking was created afterward. | `.ai/HANDOFF.md:4293-4323`. |
| Final family ratings appear as rounded 2804.8/2620.4/2344.9 and precise 2804.82/2620.36/2344.87. | They are the same official-close values at different display precision. | `.ai/HANDOFF.md:21-24`; `paper/data/submitted_agent_leaderboard_snapshot.csv:3`. |

## 10. Paper-review timeline, kept separate from competition events

The manuscript history is not a clean Git series. Current paper files and review
directories were edited in the working tree after the last strategy commits.
The rows below therefore cite frozen review receipts and review documents, not
strategy commits.

| Paper-review stage | What the manuscript or reviewers believed | What changed next | Evidence class and source |
|---|---|---|---|
| Aug 25 framing brief | Proposed a deterministic, LLM-free, rank-aware competition-agent story with an Agent Behavior Analysis and a figure showing online and evidence lanes. Final rank was still deferred. | Later reviews demoted architecture diagrams and required direct behavior denominators. | `REVIEW/C0`: `paper/FRAMING.md:1-26`, `paper/FRAMING.md:115-201`. |
| First local five-seat review, Aug 30 early | Praised returned-action auditing and negative-result discipline, but the result was still conditional on first place. It identified the clean 63-game window and asked for a denominator-defined final-policy behavior cohort. | GLEE was defined in the abstract, causal language was narrowed, and the 63-game process census was added. | `REVIEW/C0`: `paper/review/panel_review.md:1-13`, `paper/review/panel_review.md:15-63`, `paper/review/panel_review.md:95-112`. |
| Full panel round 1 | Advisory decision was Major Revision. The strongest contribution was the returned-action evidence contract, but ethics, author/package metadata, artifact access, policy completeness, and all-owner behavior conformance blocked award readiness. | A branch-objective map, 63-game census, policy manifest work, and stricter evidence labels were added or requested. | `REVIEW/C0`: `paper/review/full_panel_2026-08-30/editorial_decision.md:20-35`, `:46-74`, `:112-154`. |
| Theory and code audit | After corrections, the formal results were judged mathematically sound under stated assumptions. The audit corrected bargaining scope, exact P2 behavior, negotiation owner order, selected persuasion evidence, and causal labels. | Manuscript retained structural assumptions and distinguished local post-coercion return from server receipt. | `REVIEW/C0`: `paper/review/theory_code_audit.md:1-16`, `:17-49`, `:64-117`. |
| Final submission audit, afternoon | The rebuilt core was structurally compliant as a 12-page PDF with four main-text pages, references, and checklist. It remained on hold because author metadata and human-opponent ethics/data-use determination were unresolved. Scientifically, it was defensible only as a bounded one-system case study. | Final result and expanded census were incorporated, but production-equivalent review access and conformance were still missing. | `REVIEW/C0`: `paper/review/final_audit_2026-08-30/editorial_decision.md:1-20`, `:80-99`. |
| Post-close result update | The paper recorded second in the agent track, third combined, 2590.02 after 46,564 games, and a 245-assignment two-window census. | Endpoint language shifted from conditional winner framing to runner-up adaptive-trajectory framing. | `REVIEW+OPS/C2`: `paper/README.md:30-55`; `paper/data/submitted_agent_leaderboard_snapshot.csv:1-3`. |
| Harsh review, evening | Decision remained Hold, Major Revision. The review found the core explained audit vocabulary better than the runner-up strategy, and that the 245-game census did not supply owner eligibility or exact conformance for all 2,288 actions. | Ordered roadmap prioritizes submission blockers, banked-source verification, behavior reconstruction, a complete final-policy table, simplified claims, and only evidence-bearing visuals. | `REVIEW/C0`: `paper/review/harsh_review_2026-08-30/editorial_decision.md:1-79`, `:81-224`; `paper/review/harsh_review_2026-08-30/revision_roadmap.md:1-82`. |
| Harsh visual adjudication | One new evidence-bearing visual at most; prefer conformance or audit coverage, then the descriptive rating trajectory. Reject architecture, decorative game tree, raw cross-family action bars, clone forest plot, and competitor chart. | Any retained visual must have explicit denominators, causal status, defined encodings, complete legend, and frozen source data. | `REVIEW/C0`: `paper/review/harsh_review_2026-08-30/figure_recommendations.md:1-81`, `:83-159`; panel arbitration at `paper/review/harsh_review_2026-08-30/panel_adjudication.md:26-64`. |

### Paper-review progress that is real

1. The result changed from a conditional expected win to the verified runner-up
   endpoint (`paper/data/submitted_agent_leaderboard_snapshot.csv:1-3`).
2. The behavior denominator expanded from the complete 63-game pre-close window
   to a named 245-assignment two-window census
   (`paper/data/final_policy_two_window_census.csv:1-6`).
3. The theory was corrected to match the finite model, conditional hidden bounds,
   actual owner precedence, and one-shot persuasion assumptions
   (`paper/review/theory_code_audit.md:17-38`).
4. The package became structurally compliant at the audited build, with four
   main-text pages, references, and the mandatory checklist
   (`paper/review/final_audit_2026-08-30/editorial_decision.md:13-20`).
5. The claim hierarchy moved toward the adaptive-agent case study and away from
   implying that the audit or last policy caused second place
   (`paper/review/harsh_review_2026-08-30/panel_adjudication.md:16-24`, `:42-64`).

### Paper-review blockers that remain

1. Author metadata is still a placeholder in the exact reviewed source
   (`paper/review/harsh_review_2026-08-30/editorial_decision.md:81-87`).
2. Human-opponent ethics and data-use authority remains an external precondition
   (`paper/review/harsh_review_2026-08-30/editorial_decision.md:89-93`).
3. The Overleaf root can compile the internal long report rather than the exact
   submission-safe package (`paper/review/harsh_review_2026-08-30/editorial_decision.md:95-105`).
4. The core still under-specifies the returned-action function, especially the
   generic bargaining path, negotiation precedence, and ordered persuasion buyer
   path (`paper/review/harsh_review_2026-08-30/editorial_decision.md:107-120`).
5. The 245-game census lacks owner eligibility, independent intended action,
   exact post-coercion match, override, fallback, and service-receipt denominators
   (`paper/review/harsh_review_2026-08-30/editorial_decision.md:121-141`).
6. The current theory verifier imports mutable working-tree modules rather than
   an isolated checkout of banked commit `b54cb33`
   (`paper/review/harsh_review_2026-08-30/editorial_decision.md:156-160`).
7. The returned-action discipline lacks a standard baseline, ablation, second
   system, or independent deployment check, so it is not yet validated as a
   general method (`paper/review/harsh_review_2026-08-30/editorial_decision.md:193-197`).
8. The appendix must preserve the corrected negative faster-concession result,
   not imply that its direction became unknown
   (`paper/review/harsh_review_2026-08-30/editorial_decision.md:199-203`).

## 11. Claims that the paper can and cannot make

### Supported with careful wording

| Claim | Evidence class | Required qualifier |
|---|---|---|
| The participant account finished second in the agent track and third on the combined board. | `OPS/C2`: `paper/data/submitted_agent_leaderboard_snapshot.csv:3`. | Account-level official endpoint. |
| The focal profile's closing family ratings and counts were 2804.82/15,639, 2620.36/15,415, and 2344.87/15,510. | `OPS/C2`: `paper/data/submitted_agent_leaderboard_snapshot.csv:3`. | Profile ratings, not account placement mechanism. |
| The development trajectory was adaptive and ratings seesawed. | `OBS/C2`: `paper/data/submitted_agent_rating_checkpoints.csv:1-13`; `.ai/HANDOFF.md:318-342`. | Descriptive, selected checkpoints, no policy-effect attribution. |
| The closing configuration was deterministic and LLM-free. | `OPS/C0`: `.ai/HANDOFF.md:144-175`; bank manifest `paper/data/submitted_agent_bank_manifest.csv:1-7`. | Scope this to the audited closing configuration, not the entire 46,564-game history. |
| The agent used ordered structural owners and empirical fallbacks. | `MECH/C1`: `.ai/HANDOFF.md:3580-3652`; `paper/review/theory_code_audit.md:40-49`. | Some fallbacks have no standalone efficacy estimate. |
| The two declared final-profile windows contain 245 assignments and 2,288 own actions with one timeout and zero logged errors. | `OBS/C2`: `paper/data/final_policy_two_window_census.csv:1-6`. | Returned-behavior census, not all-owner conformance. |
| Many plausible development conclusions reversed after all outcomes, reachability, or instrument defects were considered. | Mixed, mostly `C5`: representative authoritative reversals at `.ai/FINDINGS.md:165-178`, `.ai/FINDINGS.md:202-252`, and `.ai/FINDINGS.md:460-516`. | Name each evidence object and corrected verdict. Do not imply the audit process caused second place. |

### Not supported without new evidence

| Prohibited claim | Why it is unsupported | Source boundary |
|---|---|---|
| The final policy caused second place. | The account endpoint reflects an adaptive best-profile trajectory; the final windows are selected and small relative to lifetime history. | `paper/review/harsh_review_2026-08-30/panel_adjudication.md:16-24`. |
| Every final action matched the designed owner. | Owner eligibility and exact independent conformance were not retained for all 2,288 focal actions. | `paper/review/harsh_review_2026-08-30/editorial_decision.md:57-79`. |
| The full agent optimized the official rank objective. | Only selected components used local raw-rank proxies; official tie and opponent adjustment are undisclosed. | `paper/review/theory_code_audit.md:19-38`; `paper/review/harsh_review_2026-08-30/editorial_decision.md:168-172`. |
| The broad leader clone improved performance. | Fixed checkpoint failed its own promotion gates. | `.ai/EXPERIMENTS.md:1169-1184`. |
| A competitor tactic caused that competitor's high rating. | Only direct games against the focal account were visible, with partial type information and nonstationary field composition. | `.ai/RIVAL_ANALYSIS.md:57-71`. |
| Hidden values are generally recoverable. | Payoff inversion works after agreements; unclosed hidden games remain unidentified. | `.ai/FINDINGS.md:95-109`; `.ai/RIVAL_ANALYSIS.md:232-281`. |
| The audit method is generally validated. | There is one system, no baseline or audit-element ablation, and incomplete final conformance. | `paper/review/harsh_review_2026-08-30/panel_adjudication.md:19-24`. |

## 12. Source hierarchy and unresolved evidence gaps

When sources disagree, use this order:

1. Post-close public leaderboard snapshot for placement and exact close counts:
   `paper/data/submitted_agent_leaderboard_snapshot.csv:1-3`.
2. Dated authenticated deployment and bank records for live topology and ratings:
   `.ai/HANDOFF.md`, with the newest relevant entry taking precedence.
3. Frozen bank manifest for the closing configuration:
   `paper/data/submitted_agent_bank_manifest.csv`.
4. `.ai/FINDINGS.md` for validated findings and explicit negatives.
5. `.ai/EXPERIMENTS.md` for precommits, pending studies, and verdict boundaries.
6. `DIARY.md` and planning notes for contemporaneous rationale, with later
   corrections taking precedence.
7. Git commits for code existence and intended change, never for proof of live
   exposure by themselves.
8. Paper reviews for manuscript quality and claim scope, never for gameplay
   efficacy.

Unresolved gaps:

- The official opponent-strength adjustment and tie rule are not available for
  independent reproduction (`paper/review/theory_code_audit.md:108-115`).
- There is no lifetime process-to-commit-to-overlay-to-server-action manifest and
  no complete all-owner conformance denominator (`paper/review/theory_code_audit.md:108-115`).
- The current review's 99.44 percent lifetime-coverage calculation is invalid.
  It compares 46,301 local terminal assignments, including 221 timeouts and one
  invalid-move ending, with 46,564 official rated games. The local archive has
  46,079 completed records, 222 failed terminal assignments, and 15 active
  records. If every completed record maps one-to-one to a rated increment, the
  conditional count gap is 485, but the official aggregate has no row-level IDs
  to verify membership or missingness (`paper/evidence_dossier/source_notes/data_logs_and_conformance.md:187-248`).
- Several historical results lack frozen row-level artifacts and must remain
  archival diagnostics (`paper/review/theory_code_audit.md:108-117`).
- The final persuasion reset was copied before its source experiment completed
  the frozen efficacy rule (`.ai/HANDOFF.md:177-183`).
- Paper edits after the four paper-touching commits are mostly working-tree
  artifacts, so their review receipts are stronger revision evidence than the
  main Git history.
- Raw messages, credentials, private identifiers, and operational controls are
  intentionally excluded from this dossier. Their exclusion prevents independent
  replay of some semantic and service-receipt claims but avoids unnecessary
  privacy and security disclosure (`paper/README.md:50-78`).

## 13. Bottom-line reconstruction

The project did not progress through one monotone sequence of better parameter
values. It moved through four substantive epistemic pivots:

1. **From solver construction to live adaptation.** The first two days produced
   many family heuristics, rapid promotions, and rapid reversals.
2. **From cross-slot rating watching to instrument discipline.** Identical-agent
   noise, invalid probes, biased clones, stale collection timestamps, and
   unreachable gates forced the use of exact action change and all-outcome
   cohorts.
3. **From universal knobs to ordered policy ownership.** Structural terminal
   owners, conditional hidden bounds, opponent-derived buyer behavior, and
   explicit seller fallback became a deterministic Agent 5 dispatcher.
4. **From provisional first-place framing to a runner-up adaptive-system case
   study.** The official result is strong external validation of the participant
   trajectory, while the 63-game and 245-assignment censuses bound what can be
   said about the closing profile.

The strongest scientifically defensible story is therefore not that every
retained heuristic was proved optimal. It is that a second-place adaptive agent
was built under a rank-transformed, moving-field objective, and that its history
contains unusually concrete examples of why implementation reachability,
returned-action verification, all-outcome accounting, and causal-status labels
matter. The paper becomes award-competitive only if it makes the actual
runner-up action policy reconstructible and either recovers final-owner
conformance or states clearly that its audit evidence is partial.
