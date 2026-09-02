# Methodology review: cohorts, identification, behavior alignment, and reproducibility

Working draft for author revision. This is a deliberately strict, evidence-bounded review of the current manuscript. It is not an editorial decision. I did not read the other new reviewer reports.

## Scope and materials checked

I reviewed the complete source and the rendered four-page core in `paper/main.tex`, the technical supplement in `paper/appendix.tex`, the NeurIPS checklist in `paper/checklist.tex`, and all 43 pages of `paper/main.pdf`. I also checked the official competition description frozen in `docs/reference/glee-docs.md`, the released aggregate CSVs, the policy and configuration manifests, the isolated review artifact, the relevant strategy source, and the local state, findings, experiment, and handoff ledgers.

The rendered core has no obvious clipping, overlap, broken glyphs, or illegible table text. The methodological problems below are not typesetting artifacts.

## Overall assessment

**Methodological readiness: major revision.**

The manuscript is unusually candid about adaptation, failed experiments, selection bias, and incomplete provenance. The arithmetic I could recompute is correct, and the main text mostly avoids claiming that observational results identify component effects. Those are substantial strengths.

The central weakness is more fundamental. The paper's stated methodological contribution is a returned-action audit, yet the required Agent Behavior Analysis does not measure returned-action conformance for the 2,288-action focal census. It reports action and outcome counts, then explicitly says exact conformance is unknown for bargaining and negotiation. The separate 25-game bargaining audit uses three pooled profiles, the negotiation evidence is simulation, and the persuasion failure audit covers only four pre-close text-buyer games. These are useful diagnostics, but they do not establish whether the submitted focal policy behaved as designed across the reported live window.

The second central weakness is population separation. The paper combines an ex post best-profile endpoint accumulated over 46,564 games by an adaptive system, a deliberately selected 245-game final-window census, several separate branch audits, and one small stopped randomized checkpoint. It labels these evidence classes, but the abstract and narrative still make it too easy to read the competition endpoint as validation of the final policy or its audit method. The current evidence supports a strong competition case study and a useful auditing proposal. It does not support a frozen-policy evaluation or a causal account of why the account placed second.

## Method and evidence map

| Evidence object | Actual population | What it can establish | Principal limitation |
|---|---:|---|---|
| Official endpoint | Focal profile, 46,564 rated games | Final displayed ratings, game counts, and account placement | Adaptive history, moving field, ex post best-profile selection |
| Two-window census | 245 joined games, 2,288 local actions | Complete local counts within the two named windows | Selected late windows, 69.8% bargaining, only 19 negotiation games, no census-wide owner conformance |
| Bargaining reach audit | 25 finalized games pooled across three profiles | Branch reach and action change in that audit | Not the focal census and not a policy-effect estimate |
| Negotiation reach audit | 800 simulated games | Software reach under simulation | Not live execution or server receipt |
| Persuasion parser audit | Four pre-close text-buyer games, 80 decisions | A concrete semantic coverage failure | One clustered failure game and narrow state slice |
| Clone checkpoint | 91 hash-assigned games | A descriptive, inconclusive randomized checkpoint if assignment and joins are trusted | Two looks, unverifiable assignment, 14 recovered joins at an earlier read, simple normal interval |
| Selected replay | 352 versus 375 reached decisions | Historical reason for rejecting an argument | Different estimands, missing derived rows, missing resampling recipe, not causal |

This map should be made explicit in the paper. At present, the reader must reconstruct it across four pages and a long supplement.

## Strengths that should be preserved

1. **The core distinguishes outcome from causality.** At `paper/main.tex:280-312`, the close window is labeled unrandomized, the moving field is acknowledged, the clone is called inconclusive, and the replay is called unreproduced. This is appropriately cautious.

2. **Selection and collider bias are treated seriously.** The discussion at `paper/appendix.tex:1095-1119` correctly warns against conditioning on completed agreements and against assigning a zero to an unplayed action without modeling continuation. This is one of the strongest methodological parts of the manuscript.

3. **The experimental unit is correctly defined as the game.** The argument at `paper/appendix.tex:1049-1072` correctly rejects turn-level pseudo-replication and notes possible interference from adaptive and repeated opponents.

4. **The two-window descriptive totals are internally consistent.** The family, role, outcome, and action counts in `paper/main.tex:213-238` agree with the frozen CSV. The prose also correctly refuses to turn zero logged errors into proof of zero errors.

5. **The score argument is scoped.** The assumptions at `paper/main.tex:90-111` are explicit, and the paper says the raw-rank result is not a theorem about the hidden opponent adjustment or the final leaderboard.

## Major findings

### M1. The required Agent Behavior Analysis only partially answers whether live behavior matched the design

**Exact anchors:** `paper/main.tex:210-258`, especially Table 2 at `paper/main.tex:221-238` and the conformance discussion at `paper/main.tex:240-249`; `paper/appendix.tex:1494-1509` and `paper/appendix.tex:1541-1546`. The official requirement is recorded at `docs/reference/glee-docs.md:540-549`.

**Finding:** Table 2 reports coarse returned-action categories and terminal outcomes, but it says bargaining ladder/floor conformance is unknown, negotiation conformance is unknown, and the census lacks the denominator needed for the defined conformance rate (C). The evidence substituted afterward comes from different populations: a pooled three-profile live bargaining audit and a negotiation simulation. Persuasion has a valuable failure case, but no full comparison of designed versus returned behavior across its 1,097 focal-window actions.

The manuscript literally tells the reader that alignment is unknown, which is honest. However, the competition requirement asks both whether behavior aligned and how that alignment was ensured. A protocol description plus unrelated reach cohorts is not the same as a result for the submitted agent. The current section therefore satisfies the disclosure aspect but not the evidentiary substance of the requirement.

**Why it matters:** Returned-action auditing is one of the three claimed contributions at `paper/main.tex:113-121`. A paper cannot make that its central empirical contribution and then omit the focal audit's principal denominator.

**Minimum remedy:** For every one of the 2,288 recorded focal-window states, run the frozen effective policy against the recorded visible state and report, by family and owner:

- eligible actions;
- selected-owner actions;
- exact planned-action matches;
- exact postguarded returned-action matches;
- legal-fallback or coercion overrides;
- joined terminal outcomes;
- records that cannot be evaluated because required state or provenance is missing.

Keep local conformance separate from server receipt. A missing server acknowledgement does not prevent reporting a reproducible local (a^{\mathrm{spec}}) versus (a^{\mathrm{returned}}) comparison.

**If reconstruction is impossible:** Retitle the contribution as a proposed audit contract with sampled diagnostic evidence. In the abstract, replace language that the audits “establish bounded execution evidence” with language that they reveal what could and could not be verified. In the behavior section, state directly that exact alignment of the submitted focal policy remains undetermined.

### M2. Four different populations are separated verbally but still blended rhetorically

**Exact anchors:** abstract at `paper/main.tex:53-76`; adaptive-profile qualification at `paper/main.tex:126-130`; census definition at `paper/main.tex:213-219`; result interpretation at `paper/main.tex:280-290`; claim table at `paper/main.tex:314-331`; focal-profile qualification at `paper/appendix.tex:1427-1435`.

**Finding:** The 46,564-game endpoint is a lifetime result from an adaptive focal profile selected because it supplied the account maximum at close. The 245-game census is two late, chosen exposure windows under a recorded final overlay. The reach audits use other profiles or simulation. The clone checkpoint is a separate experiment. These answer different questions.

The selected census is also highly unbalanced: bargaining is 171/245, or 69.8%; negotiation is 19/245, or 7.8%; persuasion is 55/245, or 22.4%. The closing window itself contains only bargaining and persuasion. It was chosen operationally to raise the displayed rating, not sampled to estimate final-policy behavior over the competition grid. Thus 171/171 bargaining agreements cannot be generalized to the lifetime trajectory, to all 960 configurations, or even to the final policy under a representative family mix.

The abstract compounds this by describing a “deterministic, LLM-free agent whose focal profile played 46,564 games.” The evidence only establishes that the two audited final windows used an LLM-off wrapper. The lifetime rating summarizes changing policies, and the supplement records an earlier LLM-generated wording comparison. The wording can therefore be read as assigning the final implementation to the entire lifetime history.

**Why it matters:** A strong result can be reported as a fact without turning it into validation of a method. Here, the adaptive endpoint is an externally scored competition outcome, but it is not an out-of-sample estimate of the final policy.

**Minimum remedy:** Add a short “populations and estimands” paragraph in the core with three explicit targets:

1. the account/profile endpoint, which is a placement fact for an adaptive, ex post selected trajectory;
2. the bounded final-window census, which is descriptive only for those named windows;
3. component studies, which have their own eligibility rules and causal status.

Report the pre-close and close windows separately in the main table, or at least state the 63 versus 182 game split and that negotiation had no closing-window exposure. Change the abstract to: “The focal profile accumulated 46,564 rated games under adaptive development; its final two audited windows used a deterministic, LLM-free policy.” Do not use the endpoint as evidence that the final router or audit method caused competitiveness.

### M3. The lifetime archive's missingness flow is obscured by the 99.44% summary

**Exact anchors:** archive table and prose at `paper/appendix.tex:1437-1464`; summary at `paper/appendix.tex:1663`; evidence manifest at `paper/appendix.tex:1738-1746`.

**Finding:** The submitted profile has 46,564 public rated games, 46,316 local per-game records, 46,301 canonical terminal joins, and 15 unresolved local records. Therefore:

- 248 public games have no local per-game record;
- 15 additional local per-game records are unresolved;
- 263 public games lack a canonical local terminal join.

The stated 46,301/46,564 = 99.44% is correct, but the table's “15 unresolved” column can leave the impression that only 15 games are missing. The manuscript does not characterize the 248 absent records by time, family, role, configuration, process, or failure mode. Missingness is therefore not shown to be random.

**Why it matters:** The lifetime archive underpins the development history and several selected diagnostics. Even a small missing fraction can matter if it clusters around process crashes, difficult configurations, or failed policies. The manuscript appropriately avoids using the lifetime archive as a complete behavior census, but its current coverage presentation is still too compressed.

**Minimum remedy:** Replace the single percentage with an explicit denominator flow:

`46,564 public rated -> 46,316 local per-game records (248 absent) -> 46,301 canonical finals (15 unresolved)`.

Where possible, stratify the 263 missing finals by family and time block and compare observed versus missing process states. If only public aggregate totals are available, state that the missingness mechanism is unidentifiable and do not use complete-case lifetime analyses without adverse bounds. The two-window census can remain the complete descriptive cohort because all 245 assignments are locally joined.

### M4. The clone checkpoint's interval is arithmetically correct but methodologically too weak to carry inferential weight

**Exact anchors:** `paper/main.tex:292-299`; hash-assignment assumptions at `paper/appendix.tex:1049-1072`; sequential-inference caveat at `paper/appendix.tex:1121-1139`; assignment description at `paper/appendix.tex:1280-1284`; join recovery at `paper/appendix.tex:1761-1768`.

**Finding:** The released 91-row table reproduces candidate (n=44), control (n=47), mean difference (+0.8691), standard error (0.8161), and nominal normal interval ([-0.7304, 2.4686]). It also reproduces a 6.141 percentage-point no-deal increase. Those calculations are correct.

The inferential chain is not independently auditable. Game IDs and the salt are withheld, so assignment cannot be re-derived. At an earlier read, 14 of 36 added rows failed the strict live-turn join and were retained through a deterministic multi-key match; their inclusion materially reduced the apparent interim lift. No sensitivity analysis reports the result with those rows excluded or bounded as possible linkage errors. The normal interval also ignores the two-look stopping process, possible repeated-opponent dependence, temporal drift, and interference in a moving pool. The appendix correctly states these limitations, but the main text still gives a confidence-interval-shaped object that readers may overinterpret.

**Why it matters:** This is the manuscript's only live randomized comparison. If it is included, it should demonstrate the audit standard the paper advocates.

**Minimum remedy:** Either present it only as a failed decision checkpoint without a nominal interval, or upgrade the analysis by providing:

- a frozen commitment that permits assignment verification without revealing raw IDs, such as keyed hashes or signed deidentified assignment receipts;
- a sensitivity analysis excluding the 14 recovered joins and conservative bounds for potential mislinks;
- arm balance by pre-treatment profile, time block, visible configuration, and role;
- an analysis consistent with the two planned looks, or a clearly descriptive estimate with no coverage claim;
- opponent-clustered or time-blocked sensitivity estimates where identity is observed;
- both pooled and predeclared profile-standardized estimates with the target stratum weights stated in advance.

Until then, keep the language “inconclusive operational checkpoint” and avoid presenting it as evidence for or against the winning strategy.

### M5. “Rank-aware” is a construct claim that is not empirically validated against the official target

**Exact anchors:** objective at `paper/main.tex:90-111`; contribution at `paper/main.tex:113-121`; bargaining proxy at `paper/main.tex:165-170`; hidden-seller construction at `paper/main.tex:176-194`; result conclusion at `paper/main.tex:334-343`.

**Finding:** The theoretical point that expected payoff and expected empirical rank can disagree is sound under the stated fixed-score assumptions. The implementation, however, uses local raw midrank proxies while the competition target is opponent-adjusted, time-varying, same-configuration, same-role percentile. The bargaining model further pools seats and omits discount factors and message mode. The hidden-seller table averages across 24 cells even though message mode and scale are observed. The paper acknowledges every one of these approximations, but it never validates how well the proxies track the official per-game target in the final era.

The title and contribution can therefore suggest that rank optimization governed the full policy, while much of the actual system consists of structural rules, fitted heuristics, fallbacks, and safety guards. The theoretical example establishes that rank sensitivity can matter. It does not establish that the retained proxy improved official rating or even ranked candidate actions correctly in the relevant live cells.

**Why it matters:** This is a construct-validity problem, not a demand for a causal ablation. A proxy should be shown to measure the target it claims to approximate.

**Minimum remedy:** On a held-out, frozen set of scoring cells or joined final-era games, report proxy calibration against recoverable official raw or adjusted outcomes. At minimum show coverage, rank correlation, calibration error, and failure strata by family. If the official adjustment cannot be recovered, validate only against the raw same-cell percentile and say so. Otherwise narrow the framing to “rank-motivated routing” and state that only specific offer-selection components use local rank proxies.

### M6. The review artifact verifies arithmetic and synthetic behavior, not the central implementation-linked claim

**Exact anchors:** `paper/main.tex:334-338`; reproducibility boundary at `paper/appendix.tex:1680-1699`; manifest at `paper/appendix.tex:1701-1758`; unresolved source-to-process provenance at `paper/appendix.tex:1761-1784`; checklist answers at `paper/checklist.tex:47-98`.

**Finding:** The anonymous artifact is well organized and passes its own closed-allowlist, checksum, privacy, dependency, table, math, synthetic-policy, and figure checks. It deliberately excludes production source, fitted production models, deployment switches, private joins, raw messages, identifiers, and source-to-server receipts. Therefore a reviewer can reproduce aggregate arithmetic and selected reference behavior, but cannot verify that the described owner order is complete, that the focal process loaded the reviewed source, that the returned actions came from that source, or that the clone assignment and joins were correct.

This limitation strikes the paper's first two claimed contributions: an “implementation-linked account” and returned-action evidence. A promised camera-ready release is valuable, but it does not give reviewers a current path to test the central claim.

**Why it matters:** Reproducibility is not merely a checklist concern here. Execution provenance is the proposed research method.

**Minimum remedy:** Provide an anonymized, non-operational, production-equivalent snapshot for review containing the exact relevant source at the frozen commit, the 81-key effective overlay, fitted tables needed by the policy, a dependency lock, source hashes, a read-only replay harness, and synthetic plus deidentified real-state conformance vectors. Keep credentials, fleet controls, raw messages, and opponent identities excluded. If licensing prevents this, provide a complete executable specification that covers every final route, not only selected rules, and narrow “implementation-linked” accordingly.

Also freeze a separate receipt for each of the two audited windows. I independently confirmed that `git diff b54cb33..b8a5a87 -- glee_agent models` is empty, which supports the supplement's byte-equivalence statement, but the paper should record the two window commits and the exact path-scoped digest rather than rely on a retrospective repository check.

### M7. The 35-record development denominator is a post hoc ledger cohort, not a prospective registry

**Exact anchors:** `paper/main.tex:286-290`; `paper/appendix.tex:1286-1335`.

**Finding:** The appendix carefully says that the 35 records are reconstructed by collapsing updates and deployment epochs, exclude handoff-only candidates and threshold sweeps, and are not a census of the exploratory universe. The core compresses this into “Of 35 bounded development records ... none passed a precommitted efficacy-promotion rule.” That wording risks presenting zero promotions as evidence of a systematically preregistered development process.

There are at least three different concepts here: a retrospectively defined record cohort, prospective decision rules attached to some individual records, and final operational retention for structural or safety reasons. The denominator does not estimate the rate of successful ideas, and zero promotions does not mean the final policy was selected independently of observed performance.

**Why it matters:** The manuscript rightly criticizes denominator errors elsewhere. Its development-process denominator should meet the same standard.

**Minimum remedy:** In the core, call this a “post hoc audit of 35 named ledger records through the August 29 bank.” State that it excludes undocumented exploration and threshold sweeps. Preserve the 7 adverse, 17 stopped/superseded, and 11 no-terminal-disposition partition if space permits. Do not use the zero-promotion count as evidence of confirmatory rigor.

## Blocking compliance issue with methodological consequences

### C1. Human-opponent data governance is unresolved

**Exact anchors:** `paper/main.tex:334-340`; `paper/appendix.tex:1786-1796`; `paper/checklist.tex:124-127`, `paper/checklist.tex:190-204`.

**Finding:** The checklist answers “No” to Code of Ethics, human-subjects handling, and IRB or equivalent review, and explicitly says the draft must not be submitted until the applicable determination is obtained. The shared competition pool can contain human opponents, while opponent type is missing for some analyzed records.

**Remedy:** Obtain and document the organizer's data-use authorization and the applicable institutional determination before submission. State whether this is secondary analysis of competition interactions, what data were available to participants, what was retained, how identities and messages are protected, and whether any human-only strata are analyzed. Update the main text and checklist to the resulting determination. If authorization is not obtained, remove human-derived private evidence from the research claims or limit analyses to organizer-confirmed agent/baseline interactions.

## Minor findings

### m1. Action categories are too coarse to diagnose designed behavior

**Exact anchor:** Table 2 at `paper/main.tex:229-236`, especially negotiation's “171 rejects or counters” and persuasion's pooled BUY/PASS and positive/negative totals.

**Finding:** These categories merge decisions made at different turns, under different roles, owners, information states, horizons, and message modes. They describe traffic volume but do not reveal whether the policy reacted correctly to the state variables that supposedly govern routing.

**Remedy:** Disaggregate by intended owner and the minimum state strata needed to interpret the design. For negotiation, separate counteroffers from rejects and show initial, response, terminal, visible-value, and hidden-value owners. For persuasion, report buyer decisions by prior/posterior gate, reset eligibility, direct-decline eligibility, and quality outcome where observed.

### m2. “Complete census” should be qualified as complete local assignment/action records, not complete execution receipt

**Exact anchors:** `paper/main.tex:65-74`, `paper/main.tex:213-219`, and `paper/appendix.tex:1411-1425`.

**Finding:** Every assignment has a local join, but local logging is best-effort and is not a server acknowledgement. The manuscript knows this, yet “complete two-window census” can be read as a complete execution trace.

**Remedy:** Use “complete local census of recorded assignments and actions within two windows” everywhere, and state what independent count proves action-record completeness. If action rows were not reconciled against server histories, call the action total locally complete according to the logger, not wire-complete.

### m3. The competition-result table omits provenance details needed for a stable external result

**Exact anchor:** Table 3 at `paper/main.tex:263-278` and the account-selection sentence at `paper/main.tex:280-290`.

**Finding:** The table reports rank and ratings but not the snapshot timestamp, board scope, first-place rating/gap, focal public ID, or whether displayed ratings include shrinkage. The supplement contains more provenance, but the core result should be independently interpretable.

**Remedy:** Add the official close timestamp and source, state that ratings are displayed values, and state the best-profile account ranking rule in the caption. If anonymity permits, give the submitted public agent ID in the submission metadata and camera-ready paper. The one-row table can be replaced by prose if space is needed for a more informative behavior figure.

### m4. The main clone interval does not name the variance estimator

**Exact anchor:** `paper/main.tex:292-299`; checklist caveat at `paper/checklist.tex:95-109`.

**Finding:** “Nominal descriptive normal interval” is appropriately cautious, but the core does not say it is an unpooled difference-in-means standard error, what variability it represents, or that it is unadjusted for two looks.

**Remedy:** Add “unpooled game-level normal interval, unadjusted for two looks and clustering,” or remove the interval from the four-page core and leave the full calculation in the supplement.

### m5. The close-window outcome emphasis needs configuration support information

**Exact anchors:** `paper/main.tex:280-285`; Table 2 at `paper/main.tex:221-238`; the 960-configuration scope at `paper/main.tex:82-88`.

**Finding:** The paper gives family and role counts but not the number or distribution of configurations represented in the 245 games. An agreement rate without horizon, information, language, discount, or feasibility mix cannot be compared with other agents or with the lifetime field.

**Remedy:** Report distinct configuration count and a compact support summary by family. At minimum give horizon/information/language proportions and the negotiation feasible-trade fraction under visible values. Do not add inferential intervals unless the target population is defined.

### m6. The final-window source receipt needs two explicit process records

**Exact anchors:** `paper/main.tex:126-130`; `paper/appendix.tex:1466-1475`; `paper/appendix.tex:1770-1775`.

**Finding:** The paper says the overlay was the same and relevant source was byte-equivalent, but only one bank commit is prominently frozen and there is no complete process-to-commit receipt. This leaves a gap between repository equivalence and the code actually loaded by each live process.

**Remedy:** Add a two-row provenance table with window, process start, commit, path-scoped source digest, overlay digest, wrapper mode, first/last fresh turn, and joined-game count. Mark any field that is retrospective rather than contemporaneously logged.

### m7. The persuasion failure is clustered and should not be summarized as a turn-level failure rate

**Exact anchors:** abstract at `paper/main.tex:69-72`; Table 2 at `paper/main.tex:235`; forensic explanation at `paper/appendix.tex:1512-1522`.

**Finding:** All four warning misses occurred in one of four games. The manuscript does not currently compute a misleading 4/80 “rate,” which is good. Any future figure or revision must preserve the game-level clustering and the fact that quality is observed only after purchase.

**Remedy:** Report “one of four audited games contained four missed warning turns; all four purchased outcomes were LOW.” If a rate is shown, make the game the unit and retain the decision count only as a within-game diagnostic.

### m8. “LLM-free” should be temporally scoped

**Exact anchors:** `paper/main.tex:59-65`; `paper/main.tex:126-130`; `paper/appendix.tex:1775-1781`; `paper/checklist.tex:213-217`.

**Finding:** The final audited wrapper was LLM-off, but the lifetime adaptive profile and development process are broader. The abstract's current modifier can be read as applying to all 46,564 games.

**Remedy:** Say “the final audited policy was deterministic and LLM-free” and separately describe the adaptive lifetime profile. Disclose the unpreserved LLM wording comparison as a development limitation without implying it was part of the submitted final policy.

## Arithmetic and source verification

I reran the checked-in verification scripts. The following quantities reproduce:

- 46,301 / 46,564 = 99.44% canonical-terminal coverage;
- 63 pre-close games and 787 own actions;
- 245 two-window assignments, 244 rated games, one timeout, 2,288 own actions, and zero logged local errors;
- bargaining actions 503 + 414 + 84 = 1,001;
- negotiation actions 10 + 171 + 7 + 2 = 190;
- persuasion actions 456 + 201 + 316 + 124 = 1,097;
- total actions 1,001 + 190 + 1,097 = 2,288;
- family game counts 15,639 + 15,415 + 15,510 = 46,564;
- displayed overall rating (2,804.82 + 2,620.36 + 2,344.87) / 3 = 2,590.02 after rounding;
- close display change (201.01 + 0 + 0.08) / 3 = 67.03;
- clone candidate (n=44), mean 1.115909; control (n=47), mean 0.246809; difference 0.869101; standard error 0.816054; nominal interval [-0.730366, 2.468567];
- profile-standardized clone difference 0.990780 with nominal interval [-0.630623, 2.612184];
- clone no-deal difference 6.141 percentage points;
- 23 policy assets, the ordered checksum, 81 overlay flags, selected theory/code checks, all released tables, and both artifact figures pass the bundled verifiers.

The relevant commands were:

```text
python3 paper/analysis/verify_derived_tables.py
python3 paper/analysis/analyze_clone_checkpoint.py
python3 paper/analysis/verify_artifact_manifest.py
python3 paper/analysis/verify_theory_code.py
python3 paper/review_artifact/verify_all.py
```

These passes establish arithmetic consistency and selected source/specification checks. They do not establish source-to-process provenance, server receipt, full policy equivalence, independent assignment verification, or causal validity.

## Figures and tables worth adding

Do not add a decorative system diagram. The paper's limited figure budget should be used only for unresolved methodological relationships.

1. **Highest priority: evidence-population and denominator flow.** Show the nesting and separation of 46,564 public rated games, 46,316 local records, 46,301 canonical finals, 245 final-window assignments, and 2,288 focal actions. Put the 25-game bargaining audit, 800-game negotiation simulation, 91-game clone checkpoint, and four-game parser audit in separate non-nested boxes. Label every arrow with the selection rule. This would prevent the paper's most serious interpretive error.

2. **Highest priority if the data can be reconstructed: conformance matrix.** Use a compact table or heatmap with rows for family/owner and columns for eligible, selected, planned-action match, returned-action match, postguard override, fallback, unresolved, and joined outcome. This directly answers the required Agent Behavior Analysis. It is more valuable than the current one-row competition-result table.

3. **Useful supplement figure: configuration coverage.** Show which of the 960 configurations appear in the 245-game census, grouped by family and major observability dimensions. A sparse matrix or grouped support bars would make external validity visible.

4. **Only after the analysis is upgraded: clone checkpoint plot.** Show interim and final estimates, profile-stratified estimates, and no-deal contrast with explicitly descriptive or sequentially valid uncertainty. Do not plot the current nominal interval as if it were confirmatory.

The illustrative rank-reversal figure is mathematically correct but not necessary in the four-page core because the example is already short. A generic routing schematic would consume space without fixing an evidence gap.

## Priority order for revision

1. Produce focal-window owner and returned-action conformance denominators, or explicitly narrow the main contribution.
2. Separate the lifetime adaptive endpoint, selected final windows, reach audits, and component experiments in the abstract and core.
3. Replace the 99.44% shorthand with the full archive missingness flow and characterize the 263 games without canonical finals.
4. Scope “deterministic, LLM-free” to the final audited windows.
5. Upgrade or de-emphasize the 91-game clone inference, especially the unverifiable assignment and 14 recovered joins.
6. Validate the local rank proxies against recoverable official targets, or narrow “rank-aware” to “rank-motivated.”
7. Make a production-equivalent, non-operational policy artifact available for review, or narrow “implementation-linked.”
8. Recast the 35-record ledger as a post hoc named-record audit.
9. Resolve the human-opponent ethics and data-use determination before submission.

With those changes, the paper could become a rigorous and unusually transparent competition case study. Without the first two changes, the central audit contribution is asserted more strongly than it is demonstrated.
