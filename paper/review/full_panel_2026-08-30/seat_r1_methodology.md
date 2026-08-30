# Peer Review Report

## Manuscript Information

- **Title**: *Percentiles, Not Payoffs: Strategy and Behavior of a Deterministic GLEE Agent*
- **Manuscript ID**: Not provided
- **Review Date**: 2026-08-30
- **Review Round**: Initial review
- **Criteria Binding**: `criteria_binding_unavailable`. No formal venue-alignment determination is made.

## Reviewer Information

### Reviewer Role

Peer Reviewer 1 (Methodology)

### Reviewer Identity

Methodologist specializing in adaptive online experiments, logged-policy evaluation, sequential analysis, missing outcomes, and reproducible ML systems.

### Review Focus

I assessed denominator coherence, causal identification, repeated inspection, hash assignment, stratification, uncertainty, missing joins, action-to-outcome provenance, local versus official score models, endpoint interpretation, and empirical reproducibility.

## Overall Assessment

### Recommendation

- [ ] Accept
- [ ] Minor Revision
- [x] **Major Revision**
- [ ] Reject

### Confidence Score

**4/5** — Core expertise matches the study, but private provenance, official endpoint evidence, and several promised artifacts are unavailable for verification.

### Summary Assessment

The manuscript presents a deterministic three-family GLEE agent, formalizes consequences of percentile-based scoring, and combines a complete 63-game final-era census with selected live audits, simulations, replays, a small hash-assigned comparison, and lifetime leaderboard endpoints. Its methodological self-awareness is unusually strong: it separates eligibility, firing, returned-action change, server joins, observed outcomes, and causal attribution; it also identifies selection bias, unsupported replay, missing-outcome, and repeated-look failures in its own development history.

The principal weakness is that the manuscript nevertheless treats a lifetime, path-dependent rating endpoint as evidence of the final banked portfolio’s competitiveness, although only 63 games—19 per bargaining and negotiation family and 25 in persuasion—belong to the fixed final era. The randomized clone comparison is arithmetically reproducible, but its randomization, eligibility, action-change, join, stopping, and stratum contract cannot be independently audited from the released table. More broadly, the empirical artifact that would verify the central systems claims is promised only for camera-ready release. These are substantial but repairable limitations. I recommend major revision centered on reframing the endpoint claim, closing the randomized-study analysis contract, and shipping the frozen verification artifact.

## Strengths

### S1: Denominators are unusually well separated

The manuscript distinguishes the complete final-era census, 99.43% lifetime joined-final coverage, and selected live/replay/simulation cohorts rather than pooling them into a universal denominator. The reported arithmetic is internally coherent: \(46{,}119/46{,}383=99.43\%\), and the family action counts \(97+190+500\) reconcile to 787.

**Evidence Anchor**: `table: Appendix Tables tab:archive_coverage and tab:final_era_census — submitted finals 46,119/46,383 and final-era totals of 63 games and 787 actions`

### S2: Identification boundaries are stated with exceptional clarity

The manuscript correctly identifies deal completion as downstream selection, games rather than turns as the experimental unit, unresolved outcomes as requiring explicit assumptions or bounds, and repeated looks as invalidating ordinary fixed-horizon coverage.

**Evidence Anchor**: `text: Appendix §§Selection and Sequential decisions, "Agreement is downstream of both strategy and opponent response" and "Ordinary fixed-horizon intervals do not preserve their nominal coverage"`

### S3: Local and official score models are not conflated

The paper carefully distinguishes the local midrank diagnostic from the undocumented official opponent-strength adjustment and identifies the dimensions pooled or omitted by the local CDF.

**Evidence Anchor**: `text: Appendix §Reproducibility, "Neither diagnostic should be described as the official opponent-adjusted scorer"`

### S4: The released clone summary is exactly reproducible

Running the supplied script over the 91-row table reproduces the candidate and control means, \(+0.869101\) difference, normal interval \([-0.730366,2.468567]\), host-weighted difference \(+0.990780\), and 6.141-point no-deal difference.

**Evidence Anchor**: `dataset: clone_checkpoint_deidentified.csv with analyze_clone_checkpoint.py — 91 rows reproduce all published pooled, realized-stratum-weighted, and no-deal summaries`

### S5: Returned actions are treated as the behavioral object

The audit contract correctly recognizes that configured flags and intermediate plans are not behavior when routing, coercion, or postguards can overwrite them. Server receipt is also explicitly distinguished from a local return record.

**Evidence Anchor**: `text: Main §Agent Behavior Analysis, "A configured flag is not behavior" and "server receipt claimed only for successfully joined histories"`

## Weaknesses

### W1: The lifetime endpoint does not identify the competitiveness of the final banked portfolio

**Problem**: The manuscript says the dated endpoint supports “full-stack competitiveness” and that the endpoint ratings “evaluate the complete stack.” However, those ratings are accumulated across 46,383 games under changing strategies, whereas the fixed final era contains only 63 games. With the documented late-game step size near 0.2%, 19 new games in a family replace only a small portion of the pre-existing raw-rating state. Thus the endpoint primarily evaluates an adaptive development trajectory, not the final policy in isolation.

**Evidence Anchor**: `text: Abstract and §Competition outcomes, "The dated snapshot supports full-stack competitiveness and sampled execution alignment" and "These numbers evaluate the complete stack"`

**Why it matters**: This is the main empirical bridge from strategy description to competitive effectiveness. The current wording exceeds what the temporal design can establish, even though the manuscript correctly refuses component-level causal attribution.

**Suggestion**: Reframe the leaderboard result as an endpoint of the lifetime adaptive agent-development process. Quantify the rating weight attributable to the fixed final era under the documented update rule. If final-policy competitiveness is retained as a claim, provide a prospective fixed-policy evaluation or another design that separates inherited rating state from final-policy performance.

**Severity**: Major  
**Confidence**: 5/5 — core expertise in sequential and path-dependent evaluation

### W2: The randomized clone comparison lacks a closed, independently auditable analysis contract

**Problem**: The manuscript gives a hash formula and reports the arm table, but the public evidence cannot re-derive assignment or verify the assignment-to-eligible-action-to-wire-to-outcome chain. The exact encoding and bit extraction, analysis-set flow, definition of `rating_change`, per-arm reach/action-change counts, submitted-profile stratum mapping, target stratum weights, complete stopping rule, and match multiplicity are unavailable. This is especially important because 14 of 36 added rows failed the strict live-turn join and entered through a composite deterministic match.

**Evidence Anchor**: `absence: clone comparison Methods and artifact — expected a closed analysis contract covering assignment serialization, eligibility flow, action-change receipt, rating-change definition, prespecified stratum weights, stopping schedule, and join validation; checked Appendix §§Identification, Strategy evolution, and Reproducibility, Table tab:competitors, clone_checkpoint_deidentified.csv, and analyze_clone_checkpoint.py`

**Why it matters**: The numerical summaries are reproducible, but the causal label “Randomized ITT” depends on provenance that the released table cannot test. The realized-stratum-weighted estimator also does not identify a target population unless those weights and the host/profile estimand are specified.

**Suggestion**: Release privacy-preserving row-level receipts containing a commitment to the original game identifier, exact hash input/encoding and assigned bit, pre-action eligibility, host stratum, returned-action change, join method, match uniqueness, and terminal inclusion status. State the estimand, raw-versus-displayed rating outcome, prespecified weights, all planned looks, and promotion/stopping rule. Report stratum-specific estimates and sequence-aware uncertainty; otherwise retain only a bounded descriptive randomized-comparison label.

**Severity**: Major  
**Confidence**: 5/5 — core expertise in randomized online experiments and logged-policy provenance

### W3: The central systems and behavior claims are not yet independently reproducible

**Problem**: The manuscript’s formal arithmetic and clone-summary calculation can be checked, but the empirical artifact needed to verify policy ownership, effective configuration, the 63-game census, lifetime coverage, official endpoint, and source-to-wire joins is deferred to camera-ready release. The checklist appropriately answers “No” for experimental-result reproducibility and open access.

**Evidence Anchor**: `text: Appendix §Reproducibility, "With the camera-ready paper, we will release a frozen, sanitized artifact"`

**Why it matters**: Reproducible action provenance is itself one of the paper’s claimed contributions. A future-release promise cannot presently substantiate that contribution, particularly when the private archive cannot later reconstruct every process-to-commit or source-to-server join.

**Suggestion**: Attach an anonymized frozen submission artifact now, with checksums, dependency lock, exact commands, effective-configuration receipt, derived census/coverage/leaderboard tables, verifier outputs, and an explicit matrix of reproducible versus irrecoverable claims. Raw transcripts and identities need not be released.

**Severity**: Major  
**Confidence**: 4/5 — direct assessment of the supplied artifact boundary, with private materials unavailable

### W4: Final placement remains unresolved in the reviewed manuscript state

**Problem**: The title switch remains false and the only leaderboard evidence described is a pre-close snapshot. The prose is appropriately conditional, but the final paper cannot convert this into a first-place claim without a post-close official record.

**Evidence Anchor**: `text: Main §Competition outcomes, "the AoE close had not yet occurred"`

**Why it matters**: This is currently a submission-readiness issue rather than an invalid result because the manuscript does not yet assert final victory.

**Suggestion**: Preserve the provisional wording unless an archived official post-grace-window endpoint is supplied. If verified, record retrieval time, close status, ranking population, eligibility fields, and checksum alongside the final title change.

**Severity**: Minor  
**Confidence**: 5/5 — directly stated in the manuscript

### Severity Summary

- **Critical issues**: None
- **Major issues**: W1–W3
- **Minor issues**: W4

## Detailed Comments

### Title & Abstract

The title accurately foregrounds the rank objective and avoids an unverified first-place claim. The abstract clearly labels behavior audits as sampled and component value as noncausal. Its “full-stack competitiveness” sentence should nevertheless be revised because the endpoint is inherited from a long sequence of changing policies.

### Introduction

The distinction between expected payoff, raw percentile, adjusted percentile, and rating is careful and mathematically appropriate. The qualification that the opponent adjustment is undocumented is essential. The one-step ordering result should remain explicitly separate from claims about final leaderboard position.

### Literature Review / Theoretical Framework

The methodological literature on collider selection, contextual-bandit evaluation, sequential off-policy evaluation, A/B peeking, group-sequential analysis, and confidence sequences is relevant and used accurately. I did not assess comprehensive game-theory coverage. No formal criteria binding was provided.

### Methodology / Research Design

The game-level ITT definition and identification assumptions are sound. The manuscript also correctly rejects turn-level pseudoreplication. The strongest weakness is operational: the clone study does not expose the complete analysis set, eligibility/action-change counts, exact assignment receipt, outcome definition, or target stratum distribution.

The 63-game final-era census is a census of a bounded time period and therefore requires no sampling interval for its counts. It should not be used as an effectiveness sample or a conformance census across 960 configurations. The manuscript mostly respects that boundary.

Missingness is handled better than in most systems papers: lifetime coverage, unresolved records, and selected outcomes are distinguished. Still, overall 99.43% coverage does not establish claim-specific missingness. The release should provide family-, era-, and claim-level flow tables for every empirical result.

### Results / Findings

The endpoint count and rating arithmetic, lifetime coverage percentage, final-era action totals, and clone estimates reconcile. The clone normal and Wald intervals are correctly described as nominal/descriptive after repeated inspection. To avoid accidental inferential reading, call them “unadjusted fixed-\(z\) intervals after two looks” wherever first presented.

The local diagnostic percentile results are generally labeled correctly and are not presented as official opponent-adjusted scores. Selected terminal-offer and completed-deal analyses are also appropriately described as selected rather than population causal estimates.

### Discussion

The limitations section is unusually candid. It identifies nonstationarity, unknown ties, local-CDF misspecification, hidden values, unplayed actions, repeated inspection, single-host evidence, and incomplete owner-to-wire provenance. These disclosures improve the paper, but they cannot substitute for reframing the endpoint claim or shipping the promised artifact.

### Conclusion

The three general lessons are supported at the level stated. The conditional sentence that first place would establish the complete portfolio’s competitiveness should instead say that the adaptive agent-development trajectory reached a competitive endpoint. Final-policy competitiveness requires separate evidence.

### References

The methodology references are appropriate and sufficiently integrated for the claims made. I do not recommend mechanically adding unrelated significance-testing citations. If the randomized result remains an ITT claim, literature on cluster/sequence dependence or randomization inference would be useful only insofar as the revised analysis actually uses those methods.

## Questions for Authors

1. What is the complete clone-study flow by arm and stratum: assigned games, pre-action eligible games, owner-fired games, returned-action changes, strict joins, composite joins, unresolved games, and analyzed terminal outcomes?
2. Is `rating_change` a raw-rating increment, displayed-rating increment, or reconstructed quantity? How do prior treatment assignments affect later ratings, matchmaking, or outcomes within each host?
3. What exact promotion and stopping rule governed the \(n=45\) and \(n=91\) looks, and were the stratum weights fixed before outcomes were inspected?
4. What evidence can distinguish the competitiveness of the 63-game fixed final policy from the inherited rating produced by the preceding 46,320 games?

## Minor Issues

### Language / Grammar

- Define “joined” operationally on first use: game-level terminal-result join versus action-by-action official-history equality.
- Use “host stratum” and “profile stratum” consistently.

### Figures and Tables

- Put the absolute lifetime gap—264 public games without joined finals—beside 99.43%.
- Label the clone interval consistently as unadjusted after repeated looks.

### Layout

- In the behavior table, visually separate live games, simulations, and fixed-history replays to prevent cross-row denominator comparison.

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | Quality rubric Dimension 1; empirical case-study contribution | MEETS | `text: Main §Introduction, "an evidence contract that separates policy eligibility, returned-action change, field outcome, and causal attribution"` | The returned-action evidence contract is a defensible systems-method contribution. | No formal venue criteria binding; domain novelty assessed only from the supplied literature. | No |
| Methodological Rigor | Quality rubric Dimension 2; empirical internal validity and statistical reporting | PARTLY_MEETS | `absence: clone comparison Methods and artifact — expected a closed assignment, analysis-set, sequential, and join contract; checked Appendix §§Identification, Strategy evolution, Reproducibility, dataset, and analysis script` | Identification principles are strong, but the only randomized study cannot be independently audited and the endpoint is path-confounded. | Private assignment and provenance records unavailable. | **Yes** |
| Evidence Sufficiency | Quality rubric Dimension 3; case-study triangulation | PARTLY_MEETS | `table: Appendix Tables tab:archive_coverage and tab:final_era_census — coherent lifetime and final-era denominators` | The final census and negative-result ledger are valuable, but core system, endpoint, and join evidence remains private or future. | Formal claims and clone summaries are verifiable; most live provenance is not. | **Yes** |
| Argument Coherence | Quality rubric Dimension 4 | MEETS | `text: Main §Agent Behavior Analysis, "what an owner was meant to do, whether it changed the returned action, and whether the resulting policy improved rank"` | The design–execution–objective distinction organizes the paper coherently. | The endpoint wording is one material exception. | Yes, through W1 |
| Writing Quality | Quality rubric Dimension 5 | MEETS | `text: Appendix Table tab:evidence_labels, "What it establishes" and "What it does not establish"` | Dense but precise prose makes inferential status unusually inspectable. | Main-text compression occasionally obscures cohort boundaries. | No |
| Literature Integration | Quality rubric Dimension 6; methodology-review scope | MEETS | `text: Appendix §Empirical evaluation, "history-dependent off-policy evaluation needs stronger trajectory assumptions"` | Relevant selection, OPE, and sequential-analysis literature is tied to concrete failures. | Comprehensive bargaining and persuasion literature assessment belongs to the domain reviewer. | No |
| Significance & Impact | Quality rubric Dimension 7; case-study transferability | PARTLY_MEETS | `text: Main §Conclusion, "deployed behavior must be audited at the returned action, after routing and coercion"` | The audit lesson is important and transferable, but its empirical implementation is not yet independently reproducible. | Broader impact depends on artifact release and clearer endpoint scope. | Secondary |

The recommendation follows from two unresolved decision-bearing criteria: **Methodological Rigor** and **Evidence Sufficiency**. Both are repairable through claim reframing, a closed randomized-study contract, and a frozen verification artifact; therefore major revision, rather than rejection, is appropriate.
