# Devil's Advocate Review: Rank-Aware Routing and Returned-Action Audits in GLEE

## Review scope and calibration

- Role: fresh Devil's Advocate reviewer
- Calibration: NOT_CALIBRATED
- Candidate reviewed: `paper/main_core.pdf`, SHA-256 `f64ac2be20db56c434204ddc715833ef0dd81cd744a4578ac29ad5bc5876ac7e`
- Source reviewed: `paper/main.tex`, SHA-256 `997b4680808beef2a4ced875baf377262efbfca65117c4dfa6cc397761ee8646`
- Submission package represented by the repository: one 12-page PDF containing four main-text pages, references, and the NeurIPS checklist. The internal technical appendix and local review bundle are not part of that package (`paper/README.md:18-22,30-40,60-89`).
- External standard: the [GLEE call for competition papers](https://glee-competition.com/call-for-papers), especially its requirements for technical approach, strategic choices, development process, evaluation including Agent Behavior Analysis, limitations, and reproducibility. The call states that acceptance is independent of leaderboard position and that the Best Paper Award is based on scholarly merit, originality, and clarity, independently of agent performance.
- Independence safeguard: I did not read any other output in `paper/review/harsh_review_2026-08-30` or any prior `final_audit` file.

## Bottom line

This is an unusually candid and technically literate competition report. Its rank-objective algebra is carefully bounded, the frozen arithmetic checks pass, and the paper understands several failure modes that many strategic-agent papers miss: selected-deal bias, non-firing gates, post-coercion action changes, treatment leakage, and unidentifiable counterfactual asks. Those are genuine strengths.

The strongest rejection case is nevertheless substantial. The paper presents a high-performing adaptive endpoint and a proposed audit discipline, but it does not establish full behavior-to-design conformance, production equivalence, server receipt, the validity or field value of its rank proxies, or the causal value of any retained component. The 245-game behavior cohort is a post hoc final-policy slice covering 0.53% of the focal profile's 46,564 rated games, and the final result is selected through a best-active-profile account rule after extensive adaptive development. The manuscript says most of this correctly. Candor prevents overclaiming, but candor does not create the missing scientific evidence. Once leaderboard placement is excluded as proof, the positive empirical validation of the proposed method is thin.

There is also an explicit submission blocker: the checklist says the work does not yet conform to the NeurIPS Code of Ethics and must not be submitted until the human-opponent data-use determination is resolved. That cannot be repaired by softer prose.

## Strongest case for acceptance, then rebuttal

The best defense is that this track asks for a competition-agent account, not a conventional causal-method paper. On that reading, a second-place agent is relevant evidence that the system functioned competitively, while the paper's main scholarly contribution is methodological honesty: it separates policy intent, branch eligibility, selected authority, returned action, joined outcome, and causal status. The paper discloses failed probes, includes all no-deals and timeouts in its bounded census, states that none of 35 development records passed a precommitted efficacy-promotion rule, and refuses to convert an adaptive leaderboard endpoint into a component claim. In four pages, that is disciplined and useful.

My rebuttal is that the call still evaluates technical soundness, quality of behavior analysis, completeness of the agent description, and reproducibility. The proposed audit contract is central, yet the submitted evidence cannot calculate its own stated conformance quantity across the final census and cannot establish that reviewed code produced each served action. The rank-aware strategy is central in the title, yet no held-out calibration or prospective comparison establishes that either direct proxy tracks the official adjusted objective or improves decisions. The exact candidate also omits most of the active owner order and fallback logic. These deficiencies do not become harmless merely because they are accurately labeled. For Best Competition Paper, the call expressly removes leaderboard performance from the award criterion, leaving insufficient evidence of originality or validated general insight.

## Critical finding

### C1. The manuscript documents an unresolved ethics and data-use condition that forbids submission

- Anchor: `main_core.pdf`, p. 4, lines 131-136; p. 9, checklist item 9, lines 365-372; p. 12, checklist item 15, lines 484-493. Source anchors: `paper/main.tex:334-340`; `paper/checklist.tex:124-127,190-204`; `paper/appendix.tex:1786-1795`.
- Confidence: high.
- Evidence: the main text says opponent type is absent and a human-data determination remains required. The checklist answers "No" to Code of Ethics conformance and states, verbatim, that the draft must not be submitted until review is resolved. It also reports no institutional or exemption determination and unresolved organizer authorization for a pool that may contain human opponents. The internal appendix adds unresolved account/profile identity and no-self-play attestation.
- Why it matters: this is not a disclosure-quality complaint. It is an unresolved external authorization and research-governance question involving potentially human-generated interactions, strategic persuasion, and private logs. NeurIPS ethics compliance is a submission condition. Wording can narrow claims and protect privacy, but it cannot retroactively supply a required determination or permission.
- Bounded remedy: before submission, obtain the applicable written institutional determination or exemption and written organizer confirmation covering analysis and publication of the competition interactions. Document what data were used, the legal or ethical basis, retention and release restrictions, and safeguards. If the determination requires consent, waiver, or further review, complete it. If authorization cannot be obtained, remove all affected human-opponent records and recompute every result on a demonstrably agent-only cohort, if such a cohort can be established.
- Evidence that would change my mind: a dated institutional determination or exemption from the competent body, organizer authorization for the analysis and proposed aggregate release, and a corrected checklist that accurately reflects those documents. A verified proof that no analyzed game involved a human would also materially alter the human-subjects branch, but would not by itself resolve platform data-use permission.
- Severity rationale: fatal as submitted. This remains fatal after any wording change because the missing fact is external authorization, not phrasing.

## Major findings

### M1. The required Agent Behavior Analysis cannot answer whether the final agent aligned with its own design

- Anchor: `main_core.pdf`, p. 3, lines 83-101, and p. 4, lines 102-106; `paper/main.tex:210-258`, especially `224-258`; `paper/appendix.tex:1409-1425,1497-1507,1541-1548`.
- Confidence: high.
- Evidence: Table 2 says exact owner eligibility and conformance are unknown for bargaining and negotiation. The paper defines conformance as an exact-action numerator over eligible audited actions, then says the aggregate census lacks that denominator for all 2,288 actions. The 153/153 bargaining result pools three profiles and only proves that a branch changed eligible returned actions. The 6,188/6,188 negotiation result is simulation, and only 3,274 actions changed. Neither result measures exact conformance of the submitted 245-game census. Logging is optional, local returns are not server acknowledgements, and there is no complete process-to-commit-to-server manifest.
- Why it matters: the call specifically requires Agent Behavior Analysis, including whether behavior aligns with design and how alignment is ensured. The paper explains an intended mechanism for ensuring alignment, but its headline audit cannot quantify alignment for the final agent. Action-type totals and terminal outcomes are not substitutes. This also weakens the central "implementation-linked" and "returned-action audit" contributions.
- Bounded remedy: freeze an independent executable specification of every active owner and postguard, recover eligibility and selected-owner labels for every action in a predeclared final-policy exposure cohort, compare exact returned actions against that specification, and report coverage, conformance, deviations, and missingness by family and owner. Bind each process to commit and effective configuration, then join a sampled or complete set of local returns to server-visible history. If complete server receipts are unavailable, report a predeclared receipt sample and its selection procedure rather than implying global execution alignment.
- Evidence that would change my mind: a full action-level conformance table with auditable denominators for the frozen submitted policy, an independent policy specification, explicit treatment of uncovered actions, and process/configuration receipts. A representative, predeclared receipt-validation sample could suffice for server equivalence if complete receipt is impossible and the resulting uncertainty is quantified.
- Severity rationale: major for track acceptance and fatal to a Best Paper case under the present framing. It requires new evidence, not softer wording. If the claim is softened further, the central audit contribution becomes a design proposal plus selected forensic anecdotes.

### M2. The scientific evidence is selected through adaptive development, best-profile selection, and a post hoc endpoint cohort

- Anchor: `main_core.pdf`, p. 2, lines 48-54; p. 3, lines 83-101; p. 4, lines 118-132. Source anchors: `paper/main.tex:126-130,213-249,280-304`; `paper/data/final_policy_two_window_census.csv:2-6`; `paper/appendix.tex:1286-1335,1427-1475`.
- Confidence: high.
- Evidence: the official account is ranked by its best active profile, and the focal profile supplied that maximum after an adaptive trajectory. The 245-game census is complete inside two selected windows, but it is only 0.53% of 46,564 rated games. Its family mix is 171 bargaining, 19 negotiation, and 55 persuasion, unlike the nearly balanced lifetime totals. The close window contains 152 bargaining games, 30 persuasion assignments, and no negotiation; bargaining alone moved +201.01 while persuasion moved +0.08. The paper's 35-record ledger is explicitly not the full exploratory universe, excludes handoff-only candidates and threshold sweeps, and has zero candidates promoted by a precommitted efficacy rule.
- Why it matters: completeness within a chosen window does not remove selection into the final profile, selected policy, or reporting window. The endpoint is a valid competition outcome, but it is not a held-out evaluation of a fixed agent. Alternative explanations include best-of-five profile selection, exposure mix, opponent mix, time-varying reference pools, rating path dependence, and field adaptation. The paper acknowledges these confounds, which means the rank cannot fill the resulting evidentiary gap.
- Bounded remedy: define policy identity prospectively by commit plus effective overlay, enumerate every activation period of that identity across every profile, and report all subsequent assignments until a fixed stopping point. Better, run a pre-registered held-out deployment or game-level randomized comparison after the policy freeze, retaining all assigned, timed-out, unresolved, and no-deal games. Report all profiles and all candidate families, with selection rules and exploratory multiplicity visible. Do not use display-rating movement as the sole outcome when the underlying per-game adjusted target can be retained.
- Evidence that would change my mind: a timestamped precommitment and complete post-freeze exposure census, or a prospective randomized frozen-policy evaluation with recoverable assignments and all-outcome analysis; a complete profile/account inventory; and a normalized registry of the full candidate and threshold-search universe.
- Severity rationale: major. The manuscript does not make a false causal claim, but without a held-out or prospective evaluation it cannot provide positive scientific validation of the selected strategy. This is fatal to using second place as evidence for Best Paper merit.

### M3. The rank-aware components are not validated against the official objective or shown to improve the agent

- Anchor: `main_core.pdf`, p. 1, lines 26-36; p. 2, lines 62-71; p. 3, lines 72-77. Source anchors: `paper/main.tex:90-111,157-196`; `paper/appendix.tex:264-280,301-329,560-603`; private calibration record `.ai/FINDINGS.md:157-163`.
- Confidence: high.
- Evidence: the paper correctly says the official tie rule and opponent adjustment are undocumented. The bargaining CDF pools roles, discount factors, and message mode. The hidden one-round seller averages equally over 24 latent-value, message, and scale cells even though message mode and scale are visible and actual exposure weights are not established. The internal technical report says only two retained subcomponents directly optimize local raw-rank models. It also says these proxies omit the official opponent adjustment and time-varying reference pool. The only private calibration summary reports bargaining R-squared 0.667; that evidence is neither in the candidate nor linked to a held-out decision-quality test. No prospective ablation shows that either proxy improves official per-game score.
- Why it matters: the algebraic counterexample establishes that expected payoff and expected rank can disagree. It does not establish that the implemented proxies estimate the relevant official rank well enough, that their equal-weighting matches deployment, or that rank-aware routing caused competitive performance. The title and main motivation therefore outrun the validation. Most active behavior appears to remain monetary, structural, or heuristic rather than directly rank-optimized.
- Bounded remedy: report held-out calibration of each proxy against the closest observable official same-configuration, same-role target, stratified by every dimension the proxy pools. Include calibration error, ranking regret, sensitivity to tie rules, reference-time drift, and opponent adjustment. Then evaluate each rank-aware branch prospectively against its monetary or pre-proxy control with game-level randomization and all outcomes. If the official adjusted target is unavailable, narrow the claim to a local raw-rank heuristic and remove any implication that it optimizes the competition score.
- Evidence that would change my mind: out-of-sample proxy calibration on a frozen period, a sensitivity analysis showing policy choices are stable to plausible official-scoring variants, and a predeclared randomized or otherwise identified comparison demonstrating improved official scoring or decision regret.
- Severity rationale: major and not repairable by wording if rank awareness remains the principal novelty. Softer wording can make the claims accurate, but then the paper needs another validated contribution.

### M4. The exact submission does not describe the active strategy completely enough to reproduce or critically assess it

- Anchor: `main_core.pdf`, p. 2, lines 55-71, and p. 3, lines 73-81; `paper/main.tex:157-208`; `paper/README.md:18-22,30-40`; omitted technical detail is visible at `paper/appendix.tex:250-295,635-705`.
- Confidence: high.
- Evidence: the four-page candidate gives one narrow bargaining ladder, one hidden seller table, and high-level persuasion rules. It describes the remaining negotiation behavior as reservation-bound inference, observed-leader price paths, and a Boulware-style fallback. The non-submitted appendix shows that the actual policy includes a long precedence order, learned thresholds, stall/deadgame/endgame writers, visible-span vetoes, postguards, fitted tables, and safe fallbacks that materially determine actions. The exact candidate has no owner-by-cell map, no complete precedence, no feature definitions for fitted policies, and no way for a reviewer to reconstruct the policy from the paper.
- Why it matters: completeness of the agent description and technical soundness are explicit review criteria. The omitted logic is not implementation trivia. It determines which branch owns a state and whether the purported rank-aware or theory-guided rule ever reaches the returned action. This omission also makes novelty and strategic reasoning difficult to judge.
- Bounded remedy: replace lower-value narrative or one result table with a compact owner-by-family/state table showing precedence, objective, fitted artifacts, and postguards. Supply concise pseudocode for complete routing and returned-action coercion. If the organizers permit an artifact channel, provide an anonymous production-equivalent frozen policy and configuration; otherwise the core must contain enough detail to implement the agent without the private repository.
- Evidence that would change my mind: an exact candidate or approved supplement containing the full owner map, ordered precedence, fitted-artifact definitions, effective configuration, and deterministic pseudocode sufficient for an independent implementation.
- Severity rationale: major. This is a content gap in the exact submission, not a request to expose credentials or live fleet controls.

### M5. Reproducibility is inadequate precisely where the claimed contribution is implementation-linked

- Anchor: `main_core.pdf`, p. 4, lines 131-137; p. 7, checklist item 4, lines 237-245; p. 8, checklist items 5-6, lines 278-313. Source anchors: `paper/main.tex:306-340`; `paper/checklist.tex:47-98`; `paper/README.md:49-78,115-147`; `paper/review_artifact/REPRODUCIBILITY_BOUNDARY.md:15-31`.
- Confidence: high.
- Evidence: the checklist answers "No" for experimental reproducibility, open data/code, experimental details, and statistical significance. The local bundle is not uploaded or part of the PDF. Even if reviewers somehow received it, its own boundary says it cannot re-audit action-outcome joins, reconstruct random assignment, prove reference-policy equivalence to production, independently verify service receipt or placement, or identify component effects. The reported retrospective sign reversal lacks derived rows and its resampling recipe. The clone release omits IDs and salt, so assignment cannot be re-derived.
- Why it matters: this is not generic insistence on open source. The paper's central methodological claim is that exact implementation evidence matters. A synthetic excerpt and aggregate arithmetic cannot validate that very claim. Planned camera-ready release does not help review-time assessment and remains conditional on unresolved permissions and licensing.
- Bounded remedy: provide, through an approved anonymous channel at review time, a frozen production-equivalent policy snapshot, exact dependency and configuration lock, source and model hashes, a deidentified action-level final cohort with eligibility/owner/return/outcome fields, assignment commitments or verifiable salted hashes, and scripts that reproduce every quantitative claim. Privacy-preserving commitments and limited organizer-mediated access are acceptable alternatives to releasing raw dialogue or identities.
- Evidence that would change my mind: a review-accessible artifact that independently reproduces the main behavior and experiment tables, proves equivalence of tested rules to the frozen production code, and permits audit of assignment and join integrity without exposing participant identities.
- Severity rationale: major. Because implementation linkage is the stated contribution, the limitation is central rather than ancillary.

### M6. Originality and Best Paper merit are not established independently of leaderboard performance

- Anchor: `main_core.pdf`, p. 2, lines 41-47, and p. 4, lines 107-138; `paper/main.tex:113-121,260-343`; the broader related-work positioning exists only outside the submission at `paper/appendix.tex:1550-1643`.
- Confidence: medium-high.
- Evidence: the core differentiates its contract from AgentBoard and causal trajectory analysis in two sentences. Eligibility traces, precedence logging, post-coercion action comparison, configuration receipts, and outcome joins are valuable engineering discipline, but the candidate neither formalizes what is novel relative to runtime observability and intervention auditing nor compares failure-detection coverage against prior approaches. The empirical cases show that the authors found several bugs, not that the proposed contract is necessary, sufficient, portable, or more reliable than existing trace validation. No component passed the paper's own promotion rule. The official call says Best Paper is judged independently of agent performance.
- Why it matters: after correctly removing second place as causal evidence, the paper needs a stand-alone scholarly contribution. The rank transformation is elementary, the strategy is benchmark-specific and only partially disclosed, and the audit method has no comparative validation. This may still be a useful competition experience report, but it is not yet a compelling originality case for the award.
- Bounded remedy: state a precise novelty claim, compare the contract feature-by-feature with the closest agent evaluation and observability methods, and evaluate it on a blinded suite of seeded and naturally occurring failures. Report detection rate, false alarms, uncovered actions, localization accuracy, and portability across all three game families. Show which failures a trace-only or intermediate-plan audit would miss and why.
- Evidence that would change my mind: a convincing related-work comparison plus an independently specified audit benchmark showing that returned-action receipts detect consequential failures missed by reasonable baselines, with reproducible results across multiple families or agents.
- Severity rationale: major for Best Competition Paper and moderate-to-major for ordinary track acceptance. This is a scientific-merit gap, not a prose gap.

## Minor findings

1. The exact single-blind PDF still contains `Author Name`, `Affiliation`, and `email@example.com` on p. 1 (`paper/main.tex:43-48`; `paper/README.md:49`). Replace these before submission.
2. The checklist answers "No" on LLM-use disclosure because an archived development comparison used LLM-generated persuasion wording without provider, version, prompt, or output-selection provenance (`main_core.pdf`, p. 12, lines 505-514; `paper/checklist.tex:213-217`). Either remove that comparison from the scientific record or disclose it adequately.
3. The candidate says all 245 games have joined local records and repeatedly uses "complete," while the paper also says exact owner conformance and server receipt are unknown. The qualifiers are present, but a reviewer can still confuse cohort completeness with execution completeness. Rename it consistently as a complete local assignment census with incomplete owner and receipt coverage.
4. The public result is internally consistent with the frozen snapshot, and the frozen arithmetic and selected theory verifiers pass. However, the candidate still needs organizer-verifiable profile/account identity and the final public ID. The internal appendix says that attestation remains unresolved (`paper/appendix.tex:1786-1793`).
5. The PDF is visually clean and fits the required four main pages, but density is high. If space is recovered, it should go to the owner map and conformance denominator, not another leaderboard graphic.

## Alternative explanations the current evidence cannot exclude

1. The second-place account result reflects best-active-profile selection across an adaptive portfolio rather than the reported focal design in isolation.
2. The late endpoint is dominated by a favorable bargaining exposure burst, with no late negotiation exposure, rather than cross-family rank-aware routing.
3. Rating changes reflect field drift, reference-pool updates, opponent-strength adjustment, path dependence, or opponent/configuration mix rather than policy quality.
4. Conventional monetary heuristics, structural visible-value rules, and fallbacks account for most performance; the two direct rank proxies contribute little, nothing, or harm.
5. Audit cases were selected because they were found and narratively useful. Without the full exploration and failure universe, their apparent prevalence and method advantage are unknown.
6. Ambiguous profile/opponent identities, including possible same-account interactions, distort selected observational comparisons unless the organizer resolves identity and no-self-play rules.

## Evidence that would most change the verdict

In priority order:

1. The ethics, human-data, organizer-permission, and profile-identity determinations described under C1.
2. A review-time production-equivalent artifact with verifiable commit, overlay, assignment, action, join, and result provenance.
3. A complete, independently specified final-policy conformance analysis across all active owners, with explicit missingness and a server-receipt validation design.
4. A prospective frozen-policy evaluation or recoverable game-level randomization that handles all profiles, assignments, no-deals, timeouts, and unresolved games.
5. Held-out calibration and decision-value evidence for both direct rank proxies against the closest available official scoring target.
6. A complete strategy owner map and full candidate-development registry, including threshold sweeps and unpromoted variants.
7. Comparative evidence that the returned-action audit contract catches important failures missed by strong trace or intermediate-plan baselines.

## Figures worth adding only if the underlying evidence exists

1. A selection-and-conformance flow figure showing every account profile and activation period, the exact policy hash, assigned games, joined games, audited eligible actions, exact conformance, and server-receipt coverage. This would close the denominator and post hoc selection gap; a decorative architecture diagram would not.
2. A held-out rank-proxy validation figure with predicted local rank versus official adjusted outcome, calibration error by omitted configuration dimension, and a predeclared treatment-control effect panel including no-deals and unresolved assignments. This would address proxy validity and policy value; a rating trajectory would not.

## Fatality after claim softening

- C1 remains fatal to submission after any wording change. Only an external determination or a cleanly rebuilt authorized cohort can resolve it.
- M1, M3, and M6 together remain fatal to a Best Competition Paper case under the current evidence. Further softening would make the manuscript more accurate but would reduce it to a careful benchmark-specific experience report. New conformance, proxy-validation, and comparative-novelty evidence is required.
- The remaining major findings are potentially repairable through a bounded artifact, a complete strategy map, and a prospectively frozen evaluation. None is repaired by emphasizing second place.

VERDICT: REJECT for the competition-paper track as submitted; STRONG REJECT for Best Competition Paper.
