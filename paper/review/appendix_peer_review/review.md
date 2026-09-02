# Peer-review working draft — REVIEW-GLEE-APPENDIX-001

> Private working document. Human review, policy checks, and factual verification are required. Do not submit this scaffold with unresolved placeholders. Do not make or announce an editorial decision.

## Intake record

- Reviewer capacity: `author_requested_reader`
- Peer-review model: `single_anonymized`
- Declared processing plan: `local_deterministic_tools`
- Scope: Appendices A, B, C only. Main text and the ethics determination are out of scope.
- Conflict disclosed: this reviewer drafted the Appendix B revisions and all of Appendix C. Findings on that material are self-review and are marked SELF.

# Comments to authors

## Evidence-bounded summary

The appendix supports a competition case study whose objective is a per-configuration, per-role payoff percentile rather than payoff. Appendix A states that objective, its assumptions, and a six-class evidence taxonomy used to grade downstream claims. Appendix B specifies the frozen policy that produced the audited windows: recorded inputs, an owner-precedence model, per-family rules for bargaining, negotiation and persuasion, and a coverage-and-verification boundary. Appendix C reports the flow of 35 named development candidates to a terminal disposition. The principal appendix claims are that the specification reproduces the returned action on the audited window, and that no named candidate was promoted by a rule fixed before its read.

Eighteen claims were mapped to evidence and checked against the repository and frozen commit `b54cb33`. Fifteen were supported, one partly supported, and two unsupported on first pass; all three problem claims were located in Appendix C and were corrected before this draft was finalised.

## Strengths

- Appendix B, coverage boundary: the section enumerates what its own verifiers cannot establish, including that no verifier executes banked dispatch end to end and that the manifest omits the launcher, supervisor, overlays and inherited environment. Self-limiting statements of this specificity are uncommon.
- Appendix B, receipt table: the ordered asset checksum reproduces from the shipped manifest under the verifier's exact concatenation format, so the PDF commits to a verifiable artifact rather than pointing at an unopenable one.
- Appendix B, bargaining: the float-equality disclosure, that binary representation makes the nominal .20 and .45 acceptance floors slightly strict so exact offers can fail the comparison, documents a live defect that no reader would otherwise find.
- Appendix C, denominator: every registry count reproduces exactly from the shipped CSV, and the headline finding is a negative one about the authors' own process.
- Appendices A and C together: the evidence taxonomy is applied rather than declared, and Appendix C closes by refusing component attribution, endpoint attribution, and any claim that stopped candidates were harmful.

## Major comments

### Major comment M1

- Location: Appendix C, adverse-records table, rows REG-010 and REG-022 (claim IDs CLAIM-C-004, CLAIM-C-005). SELF.
- Observation: the draft described development-time screening counts as live exposure. REG-010 was written as "historical reach 130 turns with a 38-turn live preflight" and REG-022 as "shadow reach 316 turns across 159 games".
- Evidence or criterion: the source records `130 eligible / 130 fired / 130 action_changed` over 2,400 paired games and `38/38/38` over 800 paired games; REG-022 records `316/159/159` on the same eligible, fired and action-changed convention. These are paired-simulation reachability screens, not live turns or games.
- Why it matters: the manuscript elsewhere separates reach, live, and fired with care, and this wording collapsed that distinction in the one section whose purpose is to report the development process honestly.
- Requested action: restate both rows on the eligible, fired and action-changed convention and remove the word live. Completed in this revision; verify the rendered table.

### Major comment M2

- Location: Appendix C, denominator subsection; audit item `analysis.multiplicity`.
- Observation: 35 candidates were screened and the single quantified contrast, REG-023, is reported with a nominal interval.
- Evidence or criterion: no multiplicity control, alpha allocation, or family-wise statement appears anywhere in the appendix.
- Why it matters: a reader can reasonably ask whether the one interval that excludes zero survived a search over 35 candidates. The point estimate is large and the direction is adverse, so the conclusion is unlikely to reverse, but the interval as printed is not the interval a multiplicity-aware reader would use.
- Requested action: add one sentence stating that the interval is nominal and unadjusted for the number of candidates screened, or report an adjusted interval. No reanalysis is required.

### Major comment M3

- Location: Appendix C, denominator subsection; audit item `analysis.prespecification`.
- Observation: the section reports that no candidate passed a precommitted efficacy rule, but no precommitted rule text is shown for any row.
- Evidence or criterion: the registry records dispositions and evidence references; the promotion rules themselves live in the development log and are not reproduced.
- Why it matters: the headline negative claim is stronger if a reader can see what a promotion rule looked like. Without one example the claim rests entirely on the authors' characterisation.
- Requested action: quote one representative promotion rule verbatim, for instance the stopped clone's interval, no-deal and every-host gates, so the standard the candidates failed is visible.

### Major comment M4

- Location: Appendix B, coverage boundary; audit item `reproducibility.data_materials_access`.
- Observation: the appendix designates the frozen source phrase tables as normative for arbitrary text replay, while the main text records that raw replays and source remain withheld pending approval.
- Evidence or criterion: the two statements are jointly consistent only if the reader is expected not to reproduce the parser.
- Why it matters: the specification's reproducibility promise is bounded by an artifact the reader cannot open, and the appendix does not say which of its numbers suffice on their own and which require the withheld material.
- Requested action: state explicitly which rules are reimplementable from the printed text alone and which are not, so the boundary is a property of the document rather than a discovery the reader makes.

## Minor comments

### Minor comment m1

- Location: Appendix C, adverse-records table, row REG-031 (claim ID CLAIM-C-007). SELF.
- Observation: the draft said "828 action flips"; the source says turn flips.
- Evidence or criterion: development log, REG-031 block.
- Why it matters: the appendix distinguishes turns from actions elsewhere, so the substitution is locally inconsistent.
- Requested action: use the source term. Completed in this revision.

### Minor comment m2

- Location: Appendix C, adverse-records table; audit item `design.allocation_randomization`.
- Observation: the table mixes randomized arms and deterministic candidates without marking which is which per row.
- Evidence or criterion: REG-023 and REG-024 are hash-assigned; REG-010 and REG-035 are deterministic guards.
- Why it matters: a reader cannot tell which rows could in principle have yielded a causal estimate.
- Requested action: add a one-character column marking assignment type.

### Minor comment m3

- Location: Appendix B, negotiation, learned acceptance thresholds.
- Observation: four thresholds are printed to nine decimals with no fit metadata, and the third quartile value is an order of magnitude below its neighbours.
- Evidence or criterion: the source model file carries no sample size or fitting record, unlike the persuasion prior, which carries a corpus count.
- Why it matters: printed precision implies a confidence the artifact does not support.
- Requested action: the non-monotonicity is now flagged as an unvetted fitted artifact; consider also reducing the printed precision to decision-relevant digits.

## Methods, statistics, and reproducibility

A 22-item structured audit returned seven items verified present, eight partly documented, four missing, two not applicable and one not assessed. The gaps cluster, and the cluster is informative rather than incidental: `analysis.prespecification`, `analysis.multiplicity`, `design.sample_size_precision`, and `reproducibility.data_materials_access` are all missing, while denominators, provenance, and claim-evidence discipline are verified present.

That pattern is consistent with what Appendix C itself reports. This was an opportunistic development program in which exposure was not planned, no promotion rule was met, and the evidence that survives is descriptive. The appendix should not be asked to supply a design it did not have; it should be asked to say so, which it largely does. The remaining gap is that the absent design elements are visible only by their absence, and M2 and M3 request the two sentences that would make them explicit.

Reproducibility is the weakest dimension and the boundary section is candid about why: the frozen commit, 23-file manifest and ordered checksum are verified present, while launcher, supervisor, effective overlays and inherited environment are declared missing, and no verifier executes the banked dispatch over the audited states. The specification is therefore auditable in parts and executable in none.

## Ethics, transparency, figures, tables, and citations

Ethics was recorded as not assessed and is out of scope for this review; it remains an unresolved external gate that the manuscript itself flags as submission-blocking.

On transparency, Appendix B publishes verbatim message strings and price coefficients copied from an observed competitor's play. The appendix now states the position that these are constants of the submitted policy and are reported as such while transcripts and identities remain withheld. That position is defensible and, importantly, it is stated rather than left implicit.

Tables were checked for denominator and total consistency. The experiment-flow table reconciles to 35 across both margins, and the adverse-records table contains seven rows matching the seven adverse dispositions.

## Limitations of this review

This is a model-generated working draft, not an independent human review, and it must be verified before use. The reviewer drafted the Appendix B revisions and all of Appendix C, so every finding on that material is self-review; three of the four claim-level defects found were in that self-authored text, which is evidence that the check was not vacuous but not evidence that it was complete. No analysis was independently reproduced beyond recomputing counts from shipped CSVs and the frozen commit. The reviewer has no access to the competition platform, opponent transcripts, or any ethics determination, and could not verify the withheld artifacts on which several reproducibility statements depend.

# Confidential comments to editor

> Keep this channel separate from comments to authors. Follow the venue policy. Do not place ordinary scientific criticism only here.

## Reviewer disclosures

- Conflicts and editor clearance: reviewer authored part of the material under review; disclosed, and affected findings are marked SELF in the author comments.
- Competence limits or specialist review needed: no platform access, no access to ethics determinations; no specialist referral requested.
- Assistance or tools used and required disclosure: local deterministic checkers only, no external service, no manuscript text transmitted.
- Confidentiality or retention issue: none. Material is the requesting author's own and is retained with the project.

## Editorial-process or integrity concerns

None. The unresolved human-participant determination is recorded in the manuscript's own checklist as submission-blocking and is a process gate rather than an integrity concern.
