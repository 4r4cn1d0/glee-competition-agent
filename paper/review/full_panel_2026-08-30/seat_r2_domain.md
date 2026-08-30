# Peer Review Report

## Manuscript Information

- **Title**: *Percentiles, Not Payoffs: Strategy and Behavior of a Deterministic GLEE Agent*
- **Manuscript ID**: Not provided
- **Review Date**: 2026-08-30
- **Review Round**: Round 1
- **Criteria binding**: `criteria_binding_unavailable`. Venue-fit observations are advisory only.

## Reviewer Information

### Reviewer Role

Peer Reviewer 2 (Domain)

### Reviewer Identity

Researcher in bargaining theory, bilateral trade under incomplete information, cheap talk and persuasion, automated negotiation agents, and benchmark design.

### Review Focus

I assess mathematical soundness and scope, theory-to-policy fidelity, use of the GLEE taxonomy, domain contribution, and whether the banked three-family policy is reconstructible and strategically coherent. I distinguish equilibrium results, software invariants, heuristics, selected evidence, and field effects.

## Overall Assessment

### Recommendation

- [ ] Accept
- [ ] Minor Revision
- [x] **Major Revision**
- [ ] Reject

### Confidence Score

**4/5** — Core domain expertise; confidence is limited only because the permitted review record excludes source-code inspection, so actual code correspondence cannot be independently verified.

### Summary Assessment

The manuscript presents a deterministic, LLM-free GLEE agent, an elementary formal account of percentile-based scoring, a precedence-ordered three-family strategy, and unusually disciplined behavior auditing. The mathematical propositions are largely correct within their stated assumptions, and the paper consistently avoids turning finite-horizon equilibrium results, individual-rationality bounds, or committed-persuasion benchmarks into claims about unrestricted GLEE play. Its use of GLEE’s horizon, information, and communication taxonomy is faithful, and its separation of returned-action alignment from component causality is excellent.

Two central issues nevertheless require major revision. First, the advertised final policy is not reconstructible from the manuscript: essential fitted tables, fallback paths, reset predicates, prior weights, lexicons, and postguard details remain unspecified. Second, the percentile objective is not connected owner-by-owner to most retained decisions; much of the bank remains monetary, safety-driven, or empirically heuristic. Thus “Percentiles, Not Payoffs” currently describes the evaluation insight more clearly than the implemented policy. These issues are repairable without new field data through an exact state-machine specification and a branch-level objective/evidence map.

**Finding census**: Critical 0; Major 2; Minor 2.

## Strengths

### S1: Exceptional separation of evidential claim types

The manuscript explicitly distinguishes structural theorems, software invariants, descriptive audits, reached-state comparisons, randomized ITT estimates, chronology, and invalid studies. This prevents equilibrium reasoning or action-change counts from being mistaken for field effects.

**Evidence Anchor**: `table: Appendix Table \ref{tab:evidence_labels} — rows Structural theorem through Invalid or refuted study`

### S2: Formal claims are sound and carefully scoped

I found no Critical mathematical error. The midrank identities, rating equivalence under inactive clamping, payoff-rank reversal, finite-horizon recursion, conditional offer bounds, terminal extraction, and persuasion obedience inequality follow from their stated premises. Importantly, the manuscript disclaims unknown adjustment monotonicity, hidden-information equilibrium status, seller individual rationality, opponent acceptance, and signaling commitment where appropriate.

**Evidence Anchor**: `equation: Appendix propositions Midrank jump, Rating equivalence, Finite-horizon recursion, Conditional bounds from offers, and Recommendation obedience`

### S3: Faithful use of the GLEE taxonomy

The owner hierarchy genuinely conditions on family, role, horizon, information, communication, and history. The manuscript also correctly distinguishes the benchmark grid from the reconstructed live competition grid and notes that the live persuasion state exposed no myopic-buyer flag. This agrees with the [official GLEE paper](https://arxiv.org/pdf/2410.05254).

**Evidence Anchor**: `table: Appendix Table \ref{tab:policy_ownership} — all family-and-role ownership rows`

### S4: Negative evidence materially constrains the narrative

Failed or unidentified interventions are not silently converted into winning-strategy explanations. The broad bargaining guard, faster concession, broad trajectory clone, response-model engine, and parser failures remain negative, invalid, or explicitly noncausal evidence.

**Evidence Anchor**: `table: Main Table \ref{tab:selection} and Appendix Table \ref{tab:negative} — candidate, result, and disposition columns`

## Weaknesses

### W1: The final three-family policy is not reconstructible

**Problem**: The appendix calls its precedence pseudocode exact, but the full returned policy still depends on omitted content: generic bargaining floors and transforms; the hidden one-round seller support/rank table; observed-leader buyer paths; seller stall/endgame thresholds and message table; persuasion prior weights; the tight-reset predicate; and the V1 decline lexicon. The manuscript therefore permits reconstruction of the architecture, but not of the banked action function.

**Evidence Anchor**: `absence: Appendix §2 Final submitted policy specification and family §§3–5 — expected complete branch predicates, fitted tables, state-update parameters, and postguard order; checked pseudocode, policy-ownership table, and all three family derivations`

**Why it matters**: The central contribution is the actual competitive strategy and its theory-to-code relationship. Without a complete specification, readers cannot determine whether two implementations would return the same action, whether the cited theory governs the wire action, or exactly how the retained fallback differs from rejected variants.

**Suggestion**: Add a versioned policy manifest with one row per owner: full eligibility predicate, precedence, state inputs, exact output rule, all parameters/table hashes, subsequent coercions or overwrites, and evidential status. Provide complete pseudocode for history-dependent state updates and the final returned-action path.

**Severity**: Major  
**Confidence**: 5 — core expertise in automated-negotiation policy specification

### W2: The percentile objective is not connected to most retained actions

**Problem**: The score propositions establish that expected adjusted percentile governs a scoped rating update and that expected payoff can reverse raw rank. Yet most retained owners are explained through discounted money, visible surplus extraction, individual-rationality bounds, buy-rate thresholds, or observed trajectories. Only the hidden one-round seller is said to maximize a local rank model, and that model is itself unspecified.

**Evidence Anchor**: `absence: Main §2 and Appendix §§2–5 — expected owner-level mapping from payoff rules to raw percentile Q or adjusted percentile; checked bargaining, negotiation, persuasion, and theory-evolution specifications`

**Why it matters**: This leaves the title and claimed “rank-aware” policy stronger than the demonstrated strategic connection. The portfolio is structurally coherent—specialized owners precede generic ones and safety guards act last—but its objective coherence is not yet shown.

**Suggestion**: Add a branch-level table identifying whether each owner targets money, raw local percentile, adjusted-rank proxy, agreement probability, information acquisition, or safety. State the theorem, empirical surrogate, or heuristic warrant for each choice. Where no rank link exists, narrow the claim from “rank-aware policy” to “policy evaluated under a rank-aware evidence framework.”

**Severity**: Major  
**Confidence**: 5 — core expertise in rank incentives and bargaining strategy

### W3: Elementary textbook propositions crowd out agent-specific content

**Problem**: Several formal results—strict gains from trade, power-path monotonicity, ultimatum accounting, and the buyer break-even threshold—are correct but elementary. Their proposition-level treatment contributes less than the omitted exact policy state and parameterization.

**Evidence Anchor**: `equation: Appendix propositions Strict gains from trade, Power concession path, Ultimatum accounting, and Buyer break-even threshold`

**Why it matters**: Readers may mistake standard identities for the theoretical contribution, while the genuinely distinctive contribution—the audited, precedence-ordered policy—remains underspecified.

**Suggestion**: Consolidate these results into a compact “benchmark and invariant” table, explicitly mark them as standard or elementary, and use the recovered space for exact policy mechanics and branch-objective mapping.

**Severity**: Minor  
**Confidence**: 5 — core expertise in bargaining and persuasion theory

### W4: Two citations blur elementary observability with stronger equilibrium results

**Problem**: The main text attaches Myerson–Satterthwaite to the statement that visible values reveal the positive-trade interval whereas hidden values do not. The appendix correctly notes that its support calculation is not an application of the impossibility theorem. Likewise, Rubinstein (1982) is chiefly the infinite-horizon benchmark, while the finite recursion is a direct backward-induction result under an explicit terminal rule.

**Evidence Anchor**: `text: Main §2 “hidden values do not”; Appendix §4 “Neither result is an application of the Myerson--Satterthwaite impossibility theorem.”`

**Why it matters**: The present citation placement risks conflating lack of state observability with impossibility under Bayesian incentive compatibility, individual rationality, budget balance, and overlapping supports.

**Suggestion**: Separate the elementary ZOPA/observability statement from the Myerson–Satterthwaite discussion, and describe the finite recursion as backward induction with Rubinstein reserved for the stationary alternating-offer benchmark.

**Severity**: Minor  
**Confidence**: 5 — core expertise in bilateral trade and bargaining theory

## Detailed Comments

### Title and Abstract

The title is memorable but currently overstates how extensively percentile optimization enters the policy. The abstract should also say that the 153-turn bargaining audit and terminal-offer outcomes are pooled across three profiles within one account, rather than leaving readers to infer that they are a submitted-profile census.

### Literature Review and Theoretical Framework

The bargaining, bilateral-trade, automated-negotiation, cheap-talk, reputation, and Bayesian-persuasion literatures are broad and generally well integrated. The especially important distinction—GLEE persuasion is repeated noncommitted cheap talk, not committed Bayesian persuasion—is handled correctly.

### Strategy and Claim-Type Audit

| Claim type | Manuscript example | Domain judgement |
|---|---|---|
| Equilibrium theorem | Finite alternating-offer recursion | Correct only under finite horizon, complete/common-knowledge assumptions, and indifference acceptance; not a theorem about the synthetic horizon or narrow P2 owner. |
| Software invariant | Owner precedence, coercion, price postguards, BUY-to-PASS direction | Economically interpretable, but actual code fidelity cannot be established from the incomplete manuscript specification. |
| Heuristic | Synthetic 99-step boundary, P2 ladder, leader paths, Boulware fallback, buy-rate cutoff, credibility reset | Usually labeled honestly; none is thereby rank-optimal or an equilibrium. |
| Selected evidence | 8/10 terminal-cent acceptance, terminal response records, warning misses | Describes reached states or selected cohorts, not treatment effects. |
| Field effect | Endpoint ratings and provisional placement | Evidence for the complete stack only. The randomized clone comparison is arm-specific ITT under stated assumptions and does not validate retained components. |

### Agent Behavior Analysis and Results

The returned-action audit is a strong contribution. However, action-changing reach establishes execution alignment only for the audited scope. The manuscript correctly acknowledges that neither effective configuration nor a complete process-to-server manifest exists for the lifetime bank. The final 63-game census should report branch-level reach, not merely family/router totals, if it is intended to connect the banked submitted profile to the strategy specification.

### Conclusion

The conclusion is appropriately conservative about component causality and optimality. It should be equally conservative about the extent to which the three-family policy itself is rank-derived.

### References

Coverage is strong. The main improvement needed is sharper assignment of citations to elementary identities, equilibrium results, impossibility theorems, and empirical analogies.

## Questions for Authors

1. Can you supply a complete versioned policy manifest sufficient for an independent implementation to reproduce every banked returned action?
2. For each retained owner, what exact objective is optimized or proxied: money, raw percentile, adjusted rank, deal probability, information, or safety?
3. What action-level difference separates the rejected broad leader clone from the retained narrower observed-leader buyer fallback?
4. Which specialized owners and guards were actually reached by the submitted profile during the complete 63-game final era?

## Minor Issues

### Language and Scope

- Qualify the abstract’s 153-turn and 8/10 bargaining claims as pooled three-profile evidence.
- Replace or qualify “Bayesian credibility tracking” with “regularized Bayesian-style inference under a stationary misreport grid.”
- Define the exact dimensions pooled by each “same-cell” local rank model at first mention.

### Figures and Tables

- Figure quality was not separately assessed under the permitted review materials.
- Add branch-level owner counts to the final-era census.

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | Universal criterion; hybrid case-study/theoretical contribution | PARTLY_MEETS | `text: Main §1 “a rank-aware decision account, an implementable three-family policy”` | The returned-action audit and negative-result account are distinctive; the formal theory is mostly standard and the rank-to-policy delta is incomplete. | No formal target binding. | Yes; W2 is unresolved. |
| Methodological Rigor | Theoretical precision and case-study triangulation | PARTLY_MEETS | `table: Appendix Table \ref{tab:evidence_labels} — all evidence categories` | Formal assumptions and causal limits are strong, but code-to-bank verification remains incomplete. | Detailed statistical inference belongs principally to R1; code was outside this review scope. | Yes; W1 is unresolved. |
| Evidence Sufficiency | Universal evidence criterion | PARTLY_MEETS | `absence: Appendix policy specification — expected reproducible parameters and state transitions; checked all family sections` | Whole-stack and selected behavioral evidence are substantial, but insufficient to reconstruct the policy or validate most retained branches causally. | Private artifact release is promised but not presently reviewable. | Yes. |
| Argument Coherence | Universal and theoretical-paper criteria | PARTLY_MEETS | `absence: Main strategy and Appendix theory evolution — expected explicit link from rank objective to each retained owner; checked all three families` | The evidence taxonomy is coherent; the title-to-policy objective chain is incomplete. | Could be repaired by narrowing the claim rather than adding experiments. | Yes. |
| Writing Quality | Universal criterion | MEETS | `table: Main Tables \ref{tab:behavior} and \ref{tab:selection} — designed behavior, observed behavior, and status columns` | The main narrative is concise and unusually precise about inferential scope. | Dense appendix and unavailable figure inspection. | No independent negative bearing. |
| Literature Integration | Universal and theoretical-paper criteria | MEETS | `text: Appendix Related work “GLEE combines repetition, endogenous credibility, and parser-mediated language”` | Relevant bargaining, trade, negotiation, cheap-talk, reputation, persuasion, and evaluation work is integrated accurately. | Minor citation-role corrections remain. | No. |
| Significance & Impact | Universal criterion; competition-system case study | MEETS | `table: Main Table \ref{tab:behavior} and Appendix Table \ref{tab:negative} — alignment and rejected-study evidence` | The evidence contract and forensic failures are useful beyond this single agent, provided the policy claims are narrowed and made reproducible. | Transferability beyond this competition remains conceptual. | Positively supports publication but does not offset W1–W2. |

The Major Revision recommendation follows from the repairable but decision-bearing failures in reconstructibility, evidence sufficiency, and objective-to-policy coherence.
