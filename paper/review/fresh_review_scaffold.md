# Fresh author-side peer review: GLEE competition paper

> Private working document. This is an author-requested scientific assessment, not an official venue review or award prediction. Human factual verification and a qualified human-participant determination remain necessary before submission.

## Review scope and materials

- Reviewer capacity: author-requested reader under the competition call's lightweight single-blind review model.
- Materials reviewed: the four-page main paper, technical appendix, NeurIPS checklist, bibliography, deidentified clone checkpoint, clone analysis script, 35-record experiment-registry crosswalk, claim-evidence matrix, and the frozen project state, findings, and experiment records.
- Local checks performed: manuscript structure and PDF layout inspection; registry denominator and disposition validation; claim-evidence validation; and reproduction of the reported 91-game clone summaries from the supplied deidentified table.
- Processing boundary: local-only review. No manuscript material was sent to an external service.

# Comments to authors

## Evidence-bounded summary

The paper asks how a deterministic agent should be developed and interpreted in GLEE, a live competition spanning bargaining, bilateral negotiation, and persuasion. GLEE transforms payoff into a same-configuration, same-role percentile before an undocumented opponent adjustment and rating update. The paper therefore treats field performance as a moving rank objective rather than ordinary expected-payoff maximization.

The agent combines narrow game-theoretic policy owners with empirical fallbacks. The central methodological contribution is an evidence contract requiring a candidate to be eligible, fire, alter the legal returned action, retain every assigned outcome, and satisfy a frozen promotion rule. Evidence consists of formal results, historical and selected-state audits, replay, observational rating chronology, and one game-level hash-assigned leader-clone comparison. The paper explicitly limits its conclusions to audited execution states and dated full-stack outcomes. It does not establish component causality, universal final-bank conformance, or an official competition placement.

The supplied clone analysis reproduces the reported candidate-control contrast of 0.869 rating points per game at 91 games, its normal interval of [-0.730, 2.469], the 13/44 versus 11/47 no-deal counts, and the host-standardized estimate. The registry crosswalk contains 35 unique records, of which 33 reached a policy path, 25 were live, one was staged, and none passed a precommitted efficacy-promotion rule. Those facts support a failure-centered case study of disciplined falsification. They do not by themselves show that the audit process caused the final rating or competition result.

## Strengths

1. **The scientific object is unusually clear.** Sections 2 and 3 distinguish payoff, raw percentile, adjusted percentile, and one-step rating. The monotonicity claims are explicitly conditional on a fixed adjustment, positive update rate, and inactive clamp. The appendix supplies proofs and a tie-handling caveat instead of presenting the undocumented scorer as known.

2. **The theory is broad without being converted into field-effect claims.** The midrank jump, one-step rating equivalence, payoff-dominance boundary, payoff/rank reversal, terminal proposal identity, finite-horizon bargaining recursion, gains-from-trade bounds, support floor, and persuasion-obedience results are internally coherent under their stated assumptions. The manuscript consistently describes theory as a source of hypotheses.

3. **The paper makes negative evidence informative.** The accept-all replay reversal, treatment leakage, unresolved-outcome error, unreachable nested gate, and failed broad clone are not hidden as development debris. Together they demonstrate why flag presence, completed deals, replayed asks, and rating movement are inadequate evidence.

4. **The required Agent Behavior Analysis is present and conceptually mature.** Section 4 separates execution alignment from objective alignment and distinguishes designed action, transmitted action, observed outcome, and unresolved reward value. Appendix G reconstructs concrete failures at the parser, fallback, treatment, replay, and reachability layers.

5. **Competitor evidence is handled carefully.** Section 5 anonymizes the accounts, describes their visible action pattern without inferring why they ranked highly, and treats the broad leader clone as a bounded policy test rather than a causal explanation of competitor quality.

6. **The limitations are candid and scientifically material.** The paper reports nonstationarity, hidden outcomes, post-inspection uncertainty, private transcripts, incomplete process provenance, and possible human opponents. The conclusion also keeps any first-place statement conditional and stack-level.

7. **The paper fits the four-page constraint cleanly.** The abstract defines GLEE, the main text ends on page 4, references begin on page 5, the required section title is exact, and the appendix carries derivations and audit detail without crowding the central narrative.

## Major comments

### Major comment M1

**The manuscript is built for the wrong review model.**

- Location: `paper/main.tex`, lines 3-5 and 40-44; `paper/README.md`, lines 16-18; locally archived competition call, `docs/reference/glee-docs.md`, lines 540-568.
- Observation: The competition call specifies lightweight single-blind review, but the draft uses the `dblblindworkshop` option, renders anonymous authors, and retains placeholder author information. The intake record was corrected to single-anonymized after this discrepancy was verified.
- Evidence or criterion: The track-specific call controls the review model. It also requires all authors to have OpenReview profiles and the agent's public ID in the submission form.
- Why it matters: This is a submission-format blocker. It may also produce the wrong workshop footer or author treatment even though the PDF otherwise follows the NeurIPS 2026 style.
- Requested action: Change the build to `sglblindworkshop`, replace all author placeholders with the real author list, affiliations, and contact details, and rebuild. Recheck the four-page boundary, footer, metadata, and author block after the change. Keep competitor identities anonymized. Confirm each author profile and provide the agent's public ID in the submission form.

### Major comment M2

**The behavior section needs a denominator-defined final-policy audit.**

- Location: Main paper, Section 4 and Table 1, especially lines 184-205; Appendix G, especially lines 883-893 and 927-931; contribution 3 at lines 98-100.
- Observation: Table 1 deliberately mixes a 4,001-game historical bargaining audit, a pooled three-agent negotiation sample, simulated activation states, selected persuasion turns, and selected action reconstructions. The closest final-era cohort contains 63 games, but the paper states that roles, owner frequencies, action frequencies, join totals, and match totals are unavailable. The appendix also lacks a final process-to-commit manifest and a bank-wide joined-action denominator.
- Evidence or criterion: The competition requirement asks what the agent actually did across its games, whether that matched its design, and how alignment was checked. The paper explains the checking mechanism well, but its coverage cannot be calculated. The claim-evidence matrix also marks the behavior claim as only partly supported.
- Why it matters: This is the most important scholarly gap for the competition track. A reader can learn how selected failures were diagnosed, but cannot tell how often the final policy used each owner or fallback, what it transmitted by family and role, how often coercion or fallback occurred, or what fraction of actions was matched to official history. It also makes contribution 3, which promises the behavior that reached the final bank, broader than the evidence delivered.
- Requested action: Recover one bounded final-policy or nearest-frozen-policy census from existing logs. Report the cohort boundary, games and decisions by family and role, intended owner or fallback frequency, major returned-action categories, fallback or exception frequency, official-history join coverage, exact matches, mismatches, and unresolved records. A compact main-text summary plus an appendix CSV is sufficient and requires no new live experiment. If these counts cannot be recovered, narrow contribution 3 to "selected forensic reconstruction of behavior near the final bank" and state in the first sentence of Section 4 that the section is not an across-games behavior census.

### Major comment M3

**Distinguish the evidence contract from the rule for retaining components.**

- Location: Abstract, lines 56-64; contributions, lines 89-100; Section 3; Section 4, lines 207-212; Appendix E and its registry table.
- Observation: The abstract says a candidate "had to" satisfy reach, changed-action, all-assignment, and frozen-rule conditions. Yet the bounded registry reports no candidate passing an efficacy-promotion rule, and the final bank retained structural owners and inherited fallbacks whose standalone causal value was not established. The later text discloses this, but the opening can still imply that every final-policy inclusion passed the experimental contract.
- Evidence or criterion: A policy can be retained for a theorem, a software invariant, operational continuity, observational evidence, or a randomized efficacy result. These evidence classes support different claims and should not share one promotion verb.
- Why it matters: The contract is most credible when it governs causal or efficacy claims, not when it is presented as a universal component-selection rule that the final stack did not follow. The current ambiguity also makes the failed broad clone and retained narrow leader-derived fallback appear contradictory.
- Requested action: State explicitly that the contract governs efficacy claims and experimental promotion, not every bank inclusion. Add a compact component-lineage table with each final component, evidence class, whether it passed an efficacy rule, why it remained, and its unresolved claim boundary. Explain that the four-account buyer-only clone tested a materially broader policy than the narrower retained fallback, whose standalone value remains unknown.

### Major comment M4

**Make the clone cohort auditable and reconcile its two intervals.**

- Location: Abstract, lines 62-64; Section 5, lines 223-231; Appendix F and Appendix H, especially lines 1052-1059; `.ai/EXPERIMENTS.md`, lines 1169-1177.
- Observation: The clone summary reproduces from the deidentified table. However, the release removes game IDs and timestamps, so hash assignment and source-to-wire joins cannot be re-audited. Fourteen of 36 added rows at an earlier read required deterministic matching after a strict join failed. The paper describes an earlier look and a stopped 91-game read. It reports a normal interval of [-0.73, 2.47], while the frozen experiment record reports an approximate Welch interval of [-0.78, 2.52]. Host was a predeclared stratum, but the main text foregrounds the unstratified contrast.
- Evidence or criterion: A randomized estimate depends on auditable assignment, a defined analysis cohort, outcome completeness, a named primary estimator, and a stopping rule. Different interval estimators can legitimately produce different values, but the manuscript must identify which estimator is authoritative and why.
- Why it matters: The 0.869 contrast is in the abstract and is the paper's strongest empirical comparison. Readers therefore need to know exactly what was frozen, why the read stopped, which assigned games entered the table, how failed joins were handled, which estimator was primary, and which promotion criteria failed.
- Requested action: Add one compact cohort-and-rule table giving assignment unit, treatment counts, eligibility definition, analysis boundary, earlier and final look timing, missing or unmatched rows, deterministic-match rule, all-assignment outcome handling, primary estimator, frozen promotion criteria, and criterion-level results. Reconcile the two intervals by naming their methods and selecting one primary descriptive summary. State that assignment cannot be independently reconstructed from the released table. If privacy permits, release salted or committed game-ID digests, host/time blocks, assignment, inclusion status, and join method. A randomization-based or permutation sensitivity analysis matching the hash design would be useful, but a narrower descriptive claim is an adequate alternative.

### Major comment M5

**Sharpen what is new about the evidence contract.**

- Location: Introduction, lines 82-100; Section 3; Appendix E; Appendix I, Related Work.
- Observation: Eligibility checks, implementation fidelity, all-assignment analysis, offline-policy limitations, and frozen sequential rules each have established antecedents. The manuscript combines them effectively for live strategic agents, but the main text does not yet isolate whether the claimed contribution is a new formal method, a reusable engineering protocol, or a uniquely documented competition case study.
- Evidence or criterion: A methods contribution needs a precise object and a clear distinction from adjacent practice. The appendix discusses offline policy evaluation and sequential testing, but gives less direct comparison with software or agent-behavior verification, potential-outcomes and randomization-inference practice, adaptive leaderboard evaluation, and benchmark overfitting.
- Why it matters: Without a sharper novelty statement, a sympathetic reader may view the evidence contract as excellent research hygiene rather than a research contribution. The strongest available evidence is not that the contract improved rating, but that it changed the evidentiary status of concrete policy claims.
- Requested action: Define the contract as a tuple or state-transition test with explicit inputs, outputs, and failure states. Map each audited claim to its first failed condition and resulting action, such as retain, narrow, disable, or mark unresolved. Use the 35-record crosswalk for this mapping without implying causality. State whether the novelty is the post-coercion action join, the combined contract, its application to a moving percentile field, or the forensic evidence that results when all three are combined.

### Major comment M6

**Align every headline number with a recoverable artifact.**

- Location: Abstract; Figure 1; Table 1; Sections 5 and 6; Appendix E to H; NeurIPS checklist.
- Observation: The clone result, figure scripts, rating checkpoints, and registry denominator have concrete companion artifacts. Several other numerical claims rely on private transcripts, mutable historical ledgers, selected-state reconstruction, or incomplete process provenance. These include the 4,001-game role audit, 6,188/3,274 reachability counts, 45/45 bargaining reversal, 40-warning result, 8/664 selected persuasion turns, and 14,732-turn audit. The 6,188/3,274 and 40-warning values are not currently represented by a frozen claim-specific artifact in the manifest.
- Evidence or criterion: Reproducibility does not require releasing private opponent text, but each headline quantitative claim should have a stable evidence path or a clearly marked archival status. Reporting a private path alone does not make the claim independently checkable.
- Why it matters: The paper's thesis is auditability. Provenance gaps therefore weigh more heavily here than they would in an ordinary competition report. The claim-evidence validation also identifies unresolved scope, population, timepoint, uncertainty, and causal-language gaps.
- Requested action: Add a claim-to-artifact manifest for every number in the abstract, Figure 1, Table 1, and Sections 5 and 6. For each claim, give source artifact, immutable digest or commit, unit, cohort boundary, inclusion rule, unresolved count, transformation command, and status: independently reproducible, verifiable from a deidentified aggregate, or archival and unavailable. Release non-identifying rows or sufficient statistics where permissions allow. Remove or qualify exact numbers that cannot be tied to a frozen artifact.

### Major comment M7

**Resolve human-participant and asset governance before submission.**

- Location: Limitations, lines 280-284; Appendix H, lines 1020-1023 and 1077-1084; NeurIPS checklist items on ethics, human subjects, institutional review, safeguards, assets, and LLM usage.
- Observation: The shared opponent pool may contain humans. The draft has no documented institutional or organizer determination, and the checklist currently answers No for ethics conformity and institutional review. Exact behavioral summaries may also require a re-identification assessment even when account names are replaced. The draft lacks a complete license inventory for competition-side assets. One historical LLM-generated persuasion-wording comparison lacks provider, version, prompt, and selection provenance. The safeguards answer is N/A even though the appendix describes dual-use risk and proposes controlled release.
- Evidence or criterion: These are process and reporting questions that require qualified human and venue-specific determinations. An automated review cannot classify the work as exempt, determine consent requirements, assess re-identification risk, or resolve asset terms.
- Why it matters: This is a submission-readiness constraint, not merely a limitation paragraph. Deidentification and transcript withholding reduce risk but do not themselves settle whether analysis of human interactions required review. An unresolved No on code-of-ethics conformity is especially consequential.
- Requested action: Obtain and document the applicable institutional determination and organizer authorization before submission, using anonymized wording only where the review model requires it. Document inclusion rules for human games, retention and security, and re-identification controls. Complete a version-and-license inventory. For the historical LLM comparison, either reconstruct and disclose the minimum provenance or remove it from the scientific evidence chain. Reconsider the safeguards answer in light of the stated dual-use release risk. Update the checklist only to reflect verified facts.

### Major comment M8

**Describe the retained agent before expanding the audit narrative.**

- Location: Objective and hypothesis generation, lines 103-138; Agent Behavior Analysis; Section 6, lines 246-270.
- Observation: The reader encounters the score derivation, theoretical catalogue, and falsification protocol before receiving one coherent architecture paragraph and a plain account of the retained policy across all three families.
- Evidence or criterion: The competition call asks for the agent's technical approach and strategic design choices as well as its development and evaluation. A reader should be able to reconstruct the top-level action path without synthesizing the table and appendix.
- Why it matters: The audit is the paper's scientific identity, but it currently crowds the artifact being audited. This can make the paper read like a methodology report with an agent attached rather than a competition paper whose agent motivates the methodology.
- Requested action: Reclaim a few lines from the theory catalogue or repeated rating chronology and add a compact architecture paragraph: visible state, family solver, ordered structural owner, bounded empirical fallback, legality/coercion, transmitted action. Follow it with one plain sentence for the retained bargaining, negotiation, and persuasion behavior. Keep the detailed theory in the appendix.

## Minor comments

### Minor comment m1

**Correct two overbroad abstract statements.**

- Location: Abstract, lines 61-64.
- Observation: The 11,737 value was a stopped-collector snapshot, while a later direct remeasurement found that it was not a reliable fleet-total estimate. The clone did not fail literally every gate; it met some administrative criteria but failed the precommitted promotion rule through its interval, no-deal, and every-host conditions.
- Evidence or criterion: Quantitative scope and criterion-level outcomes should match the frozen findings and experiment records.
- Why it matters: Both phrases are vivid and appear in the abstract, so readers may carry a stronger claim than the archive supports.
- Requested action: Describe the outcome bug as a stopped collector snapshot with 11,737 outstanding records that the reader misclassified, without presenting it as a fleet total. Replace "failed every promotion gate" with "failed the precommitted promotion rule, including its interval, no-deal, and every-host criteria."

### Minor comment m2

**Define competition-specific jargon at first use.**

- Location: Abstract and Introduction, including "bank," "owner," "gate," and "post-coercion action."
- Observation: These terms are meaningful inside the project but are not standard across agent research.
- Evidence or criterion: A four-page competition paper should remain legible to readers who know game theory but not the GLEE implementation vocabulary.
- Why it matters: The abstract is already information-dense, so unexplained operational terms make the core contribution harder to parse.
- Requested action: Define "bank" as the frozen final snapshot, "owner" as the highest-precedence policy responsible for a state, and "post-coercion action" as the legal action returned to the SDK. Use "gate" only after defining the condition it represents.

### Minor comment m3

**Clarify units, populations, and selection in Table 1.**

- Location: Main Table 1, all three family rows.
- Observation: The bargaining 71.5th/28.8th values are local fitted diagnostic percentiles, not official role-specific scores. The 6,188 and 3,274 negotiation counts do not identify whether a state is a turn, game, replay row, or policy decision. "All 40 revealed low quality" can be misread as a population rate rather than the outcome among the 40 purchased warning cases.
- Evidence or criterion: Denominators, analysis units, and score definitions are required to interpret behavioral frequencies and selection.
- Why it matters: Ambiguous units work against the paper's own warning about conditioning and mixed evidence sources.
- Requested action: Label the bargaining values as local fitted diagnostics, name the unit and replay corpus for the negotiation counts, and write "among the 40 purchased direct-warning cases, all later revealed low quality" or equivalent wording that makes selection explicit.

### Minor comment m4

**Narrow the final causal-sounding sentences.**

- Location: Conclusion, lines 286-291; contribution 3, lines 98-100.
- Observation: "Our audit separates what executed from what worked" and "the audit identifies which explanations survive" are broader than the bounded registry, incomplete final-bank census, and unresolved component effects support.
- Evidence or criterion: The strongest established result is that selected audited explanations remain consistent with, fail under, or are unresolved by the retained evidence.
- Why it matters: The last two sentences are memorable and will shape the reviewer's interpretation of the paper's epistemic standard.
- Requested action: Use "separates what executed from what the evidence can and cannot attribute" and "identifies which audited explanations remain consistent with the retained evidence," or equivalently bounded language. Preserve the leaderboard/audit contrast.

### Minor comment m5

**Repair theory and source-level clarity issues.**

- Location: `paper/main.tex`, lines 30-33; Appendix Proposition 2 around line 72; Proposition 4 around line 89; Proposition 7 around lines 221-225; Proposition 10 around lines 410-421.
- Observation: The source comment incorrectly says appendix permission is unconfirmed. The display-shrinkage caveat can be read as destroying action ordering even when a fixed positive affine transform would preserve it. The payoff/rank reversal uses a smooth logistic CDF rather than a finite empirical multiset. The discounted-guard proposition calls `c` a counter rather than the player's payoff from that counter. The persuasion proposition resumes with "and strictly optimal" after a displayed equation.
- Evidence or criterion: Internal submission comments should match the verified call, and proposition statements should align tightly with their formal object and the empirical-percentile setting.
- Why it matters: No theorem-level error was found, but these local issues invite unnecessary objections.
- Requested action: Update the appendix-permission comment; clarify when fixed display shrinkage preserves within-game ordering; optionally add a finite empirical-multiset reversal; define `c` as the player's payoff/share if the counter is accepted; and repair the grammar after the obedience inequality.

### Minor comment m6

**Make the abstract less ledger-dense.**

- Location: Abstract, lines 50-68.
- Observation: Three forensic episodes, a clone estimate, three absolute family ratings, and several undefined implementation terms compete for attention. The ratings lack a leaderboard reference point and do not carry the paper's most general lesson.
- Evidence or criterion: The abstract should prioritize problem, method, strongest evidence, scope, and contribution.
- Why it matters: The current abstract defines GLEE correctly but asks the reader to decode too much internal history before understanding the reusable idea.
- Requested action: Keep one strongest failure example, the bounded clone result, and the execution-versus-causality boundary. Move the raw family ratings to Section 5 unless an official placement later provides the necessary context.

### Minor comment m7

**Keep the required behavior section visually coherent.**

- Location: Main pages 2 and 3, Figure 1, Table 1, and lines 207-212.
- Observation: Figure 1 and Table 1 create a page break that separates part of the behavior interpretation from the required section's opening material.
- Evidence or criterion: Visual hierarchy should make the required section easy for competition reviewers to identify and read as a unit.
- Why it matters: The PDF is clean and readable, but the most track-specific narrative has less continuity than the general falsification narrative.
- Requested action: If possible without disturbing the four-page limit, keep lines 207-212 with Table 1 or reduce/reposition the figure. Otherwise retain the current layout, since there is no overflow or legibility failure.

### Minor comment m8

**Archive or identify mutable public sources.**

- Location: Bibliography and Appendix I.
- Observation: The competition-rules page is mutable, and the randomization/hash-assignment discussion lacks a direct foundational citation. Two bibliography entries, `gleecall2026` and `riley1983selling`, are unused.
- Evidence or criterion: Rules that define the target outcome and review requirements should remain retrievable at the cited version; methodological positioning should cite the practice it invokes.
- Why it matters: Later readers need to distinguish the 2026 rules from subsequent platform changes.
- Requested action: Cite a dated, publicly retrievable archive of the competition call if available; add a foundational randomization or potential-outcomes citation appropriate to the design; and remove or use the two unused entries.

## Methods, statistics, and reproducibility

The formal results checked in the objective appendix are internally coherent under their stated assumptions. Pointwise dominance under a fixed nondecreasing empirical CDF does not imply ordering by expected money, and the one-step rating equivalence requires a fixed adjustment map, a positive update rate, and an inactive clamp. The theory is appropriately presented as hypothesis generation rather than evidence of field performance.

The clone comparison uses the game as the assignment and analysis unit, which matches the randomization description. Its supplied summary can be reproduced from the deidentified table. The released normal and Wald intervals are suitable only as descriptive calculations because the paper records an earlier look, post-inspection stopping, unverified hash assignment in the released artifact, possible cross-agent interference, and matching-based inclusion of some rows. The no-deal Wald interval is especially fragile at these sample sizes; a score, Newcombe, or design-based interval would be more appropriate if an interval remains. No confirmatory error rate should be attached to either summary.

Most other empirical comparisons are retrospective, selected-state, era-confounded, or based on repeated turns. They are useful for falsifying reachability, software behavior, or broad policy claims, but not for estimating causal reward effects. Rates that support interpretation should be reported as numerator/denominator, with the unit and uncertainty method stated. "Host-standardized" should specify that it uses the realized host-frequency mix and whether those weights were fixed before outcome inspection.

The 35-record registry is a bounded reconstruction, not a preregistration. Its denominator depends on a stated inclusion convention, and some dispositions are inferred from archived state. Add a data dictionary, evidence class, promotion-rule status, terminal status, inclusion rationale, and source digest or commit. A deterministic validator or extraction script would make the denominator more than an arithmetically reproducible hand-constructed table.

For reporting guidance, the automated study classifier selected CONSORT because the materials contain a randomized comparison. This classification concerns reporting completeness only and is not a quality score or a natural full-study label for a computational competition case study. The useful principles here are transparent allocation, cohort flow, outcome completeness, stopping, analysis unit, and harms reporting, together with the NeurIPS checklist and track requirements.

## Ethics, transparency, figures, tables, and citations

No integrity allegation is raised. Competitor accounts are anonymized, individual human claims are avoided, and raw transcripts are withheld. The unresolved human-opponent classification should be handled through the applicable institutional and organizer process, with specialist human review. Strategic persuasion and bargaining methods have clear dual-use potential; the paper identifies this, but the release and safeguards answers should be made consistent.

The main figure is legible and honest about irregular observation times and descriptive interpretation. Authentication establishes the displayed values and dates, not exchangeability of adjacent windows. Table 1 is information-rich, but its mixed evidence sources make a final-policy census more important. The related-work appendix covers rank incentives, bargaining, bilateral trade, persuasion, offline evaluation, sequential testing, and empirical competition reporting. The novelty comparison should be pulled into the main contribution language rather than expanded through citation volume alone.

## Limitations of this review

This assessment is local and author-side. It is not an official venue review, an award prediction, or a substitute for organizer guidance. Raw competition transcripts, server-side scoring logic, opponent-adjustment code, final process-to-commit provenance, official placement evidence, and institutional determinations were not available for independent verification. Only the supplied deidentified clone summaries and local registry structure were computationally checked. The role-separated readers share the same supplied record and should not be treated as statistically independent reviewers. Human-participant compliance, asset licensing, and final venue-policy interpretation require qualified human review.

# Confidential comments to editor

> This section is retained only to preserve channel separation. The intake record states that a separate confidential editor-note channel is not currently supported, so these notes are not intended for submission as editor-only communication.

## Reviewer disclosures

- Conflicts and editor clearance: No conflict was identified from the author-provided scope. This was an author-requested review, not an assigned venue review.
- Competence limits or specialist review needed: A qualified institutional or venue specialist is needed for the human-opponent classification and any approval, consent, or exemption determination. Asset licensing also requires owner or organizer confirmation.
- Assistance or tools used and required disclosure: The review used approved local AI assistance, three role-separated local reads, deterministic validation scripts, PDF inspection, and local reproduction of the deidentified clone summary. This assistance should be disclosed if the venue requires it.
- Confidentiality or retention issue: Processing remained local. The working review and derived validation reports remain in the authorized project workspace under the recorded retention rule.

## Editorial-process or integrity concerns

No misconduct or duplicate-publication concern was identified. The unresolved human-participant determination is a process issue already disclosed to the authors and should be resolved before submission. No ordinary scientific criticism is withheld from the author-facing section.
