# Narrative and literature review: working draft

Author-side review of the corrected `paper/main.tex`, full `paper/appendix.tex`, their current diff, and `paper/references.bib`, on 2026-09-05. Manuscript text was reviewed locally. Public-source verification used only published citation titles and URLs; no unpublished manuscript text was sent to search. Intake validation returned `READY_FOR_LOCAL_REVIEW`. The author remains accountable for the final submission. This is one specialist pass within the coordinating review, not an independent human panel or an editorial recommendation.

Scope: contribution clarity, accessibility to a first-time GLEE reader, core/appendix balance, related-work claim fit, lessons, and inferential usefulness of figures. Formula/code correctness, data reconstruction, statistical analysis, and PDF rendering are covered by the other passes. I have not independently reproduced those results or verified every one of the 47 bibliography records. Venue criteria are those in the coordinator's current CFP check. The current dated study profile has no matching clinical reporting guideline; no clinical checklist or invented award probability is used.

# Comments to authors

## Overall assessment and strengths

The manuscript has a credible and useful case-study contribution: a competitive deterministic agent deployed in an evolving, heterogeneous competition, a clear explanation of why monetary payoff and the scoring target differ, and unusually candid separation of observed actions, their transmission, and causal attribution. It is strongest when it reports concrete mismatches between success proxies: all 15 CDF-triggered bargaining games agreed, yet 14 lost displayed rating; a fully matched action stream still leaves policy-selection and process provenance unresolved; and a registry of 35 candidates produced no promotion under a precommitted efficacy rule.

The revised statements about fixed fitted models and priors, the distinction between zero-payoff frequency and the scoring objective, and the limited meaning of pooled seed ranks are improvements. The full appendix supplies substantial implementation detail rather than hiding the policy behind its name. The sampled recent references are real and correctly identified. The principal remaining problem is explanation and emphasis: the core sometimes sounds like a paper introducing a general rank-optimization method, while its most convincing evidence supports an audited competition engineering case study. Several statements in related work also attach stronger theoretical meaning to the implementation than the cited models justify.

## Major revision priorities

### Major comment N1

Explain in the core that the failed clone's buyer behavior survived assembly

- Location: Main Table 1, line 193; main lines 278–292; Appendix B, lines 420–438.

- Observation: The core lists “leader clone” under “Excluded after development” and says its trial was stopped. Appendix B then explains that this exclusion refers to the randomized whole-policy arm, while the final buyer coverage equals the clone's buyer coverage, includes the adverse hidden unknown-horizon slice, and shipped while a narrower assembly was off. A careful core-only reader can reasonably conclude that the failed clone's behavior was removed, which is materially different from the disclosed appendix account.

- Evidence or criterion: The paper's own explicit lineage statement in Appendix B; the CFP's agent-description, motivation, and evaluation criteria. This is a reporting inconsistency, not a claim that the trial proved the retained buyer component harmful.

- Why it matters: This is one of the paper's most instructive development lessons. It shows the gap between rejecting an experimental package and retaining some of its content during deterministic assembly. Leaving that distinction outside the four-page paper can make the negative-result story sound cleaner than the actual process.

- Requested action: Rename the excluded item to “randomized whole-policy clone arm” and add one core sentence explaining that observed-leader buyer paths nevertheless remained in the final assembly without a passing efficacy read. State the recorded selection rationale if one exists; otherwise say that the retained choice lacks a documented evidence-based promotion rationale. Do not infer a component effect from the failed package contrast.

### Major comment N2

Make the route and game vocabulary usable before the main tables

- Location: Main lines 124–178 and Tables 1–2; Appendix B, lines 149–162 and 198–212.

- Observation: The core introduces Bob, Alice, pot size M, discounts, a payoff CDF, owner labels, gates, protected wires, and plan semantics without defining several of them there. In the persuasion formula, p, u, P, and v are not identified as prior HIGH probability, LOW value, price, and HIGH value. The negotiation price p has just used the same letter differently. Equation 3 also uses B and m before a clear symbol definition. “Owner” and “wire” are defined only in the appendix, although they are necessary to interpret the core's audit coverage. Table 1's arrows combine mutually exclusive fall-through with subsequent modifications: a Bob CDF raise modifies a generic plan rather than simply being another first-eligible owner.

- Evidence or criterion: Appendix B says the core can be read without the appendix (lines 149–151). CFP agent-description and technical-soundness criteria require readers to understand what the rules choose and what the audit verifies.

- Why it matters: The reader may understand the equations individually yet fail to understand the deployed action path or the practical difference between a matched action, a labeled owner, and a gate firing. That distinction is central to the contribution.

- Requested action: Add short inline definitions at first use: Alice/Bob as the two bargaining seats, M as the pot, the persuasion symbols, CDF as cumulative payoff distribution, owner as the rule selecting a candidate, gate as a recorded condition, and wire as the final submitted action. Define B as monetary scale and m as communication mode. In Table 1, distinguish “else” owner fall-through from “then” transformations/coercion, or separate those into two cells. These changes need not add a separate glossary or figure.

### Major comment N3

Focus the contribution and core space on what the evidence actually demonstrates

- Location: Abstract, lines 61–78; main lines 114–119, 139–178, 262–269, and 324–327; Appendix B, lines 314–345.

- Observation: “We contribute a rank-sensitive objective” can imply that the paper introduces an objective that the competition already imposes. The hidden seller proxy receives a full core equation, while Table 2 reports no audited hidden rank-proxy state. The Bob proxy that did change 57 turns receives only a short description in the design section. The abstract spends many words on corpus counts and evidence qualifications but does not state one of the specific substantive findings those records reveal.

- Evidence or criterion: The evidence supports formalizing the supplied score, implementing scoped proxies, reconstructing an adaptive system, and documenting behavior and failure. It does not establish a general new optimizer or a performance benefit from either proxy. The existing qualification of “rank aware” is good and should remain.

- Why it matters: A reader attracted by the title should be able to identify the implemented score-aware choice and its observed behavior. The paper's strongest scientific value is currently less visible than its administrative evidence inventory.

- Requested action: Frame the first contribution as “formalize the competition objective and instantiate two local proxies.” Add one plain-language description of the Bob choice: predicted rank after acceptance versus a fitted continuation percentile, with an offer raised only when the estimated comparison passes its margin. State that the audited gate reached 15 games while the hidden seller proxy was unobserved in the final census. If space is tight, move Equation 3's full grid sum to Appendix B and keep its assumptions in one core sentence. Give the abstract one concrete finding, such as agreement failing to imply positive rating. No additional experiment is necessary if the case-study claim remains bounded.

### Minor comment N4

Correct the final-era exposure sentence

- Location: Main lines 274–276; Appendix D, Table 7, lines 818–832.

- Observation: The core claims at least 3,028 assignments per family “in every era.” The final era contains 171 bargaining, 19 negotiation, and 55 persuasion assignments.

- Evidence or criterion: Direct contradiction with the lifecycle table and the main behavior census.

- Why it matters: As written, this overstates the exposure behind the final policy and undermines the careful distinction between lifecycle evidence and the 245-game audit.

- Requested action: Replace “every era” with “each of the three development eras,” or state the development and final exposure separately.

## Related-work findings

### Major comment L1

Separate conceptual inspiration from the mechanisms established by the bargaining literature

- Location: Appendix E, lines 894–908; Appendix B, lines 270–312.

- Observation: The literature paragraph calls Admati–Perry's strategic delay “the theoretical content” of the empirical discount-dependent clock. Their model makes time between offers an endogenous signal of private bargaining strength. The deployed clock instead computes a patience horizon from own discount and applies a concession schedule. The paragraph also moves from hidden bargaining information into hidden-value bilateral trade without clearly saying that the discussion has crossed from the bargaining family to negotiation. The finite/infinite-horizon qualification correctly appears in Appendix B but is not carried into this renewed Rubinstein attribution.

- Evidence or criterion: The primary [Admati–Perry article abstract](https://academic.oup.com/restud/article-abstract/54/3/345/1558303) identifies endogenous timing and signaling as its mechanism. The manuscript's clock is specified in Appendix B. This supports a connection to delay and private information, not a derivation of that clock from the cited equilibrium.

- Why it matters: An economic-theory reader will distinguish a patience heuristic from a signaling equilibrium. The current wording can suggest a stronger theoretical justification than the implementation claims elsewhere.

- Requested action: Say that strategic-delay theory motivates attention to patience and information, while the actual clock is an empirical heuristic that does not implement the cited signaling model. Name which family and hidden quantity each comparison concerns. Reuse the accurate “finite-horizon benchmark in the alternating-offer tradition” qualification instead of suggesting that Rubinstein's infinite-horizon result directly supplies the finite recursion.

### Major comment L2

Do not equate equal surplus splits with splitting the previous offer difference

- Location: Appendix E, lines 904–908, including its cross-reference to Appendix C.

- Observation: The Keniston et al. citation concerns offers that split the difference between the previous two offers. The text claims the paper's recorded field behavior is consistent with this pattern, but the cited destination is the experiment registry, which does not present the required consecutive-offer statistic. An approximately equal final surplus split alone would not establish the cited offer-level pattern.

- Evidence or criterion: The [published article abstract](https://onlinelibrary.wiley.com/doi/abs/10.1111/iere.12719) defines the empirical behavior in terms of the prior two offers and separately discusses why it can sometimes represent an equal inferred surplus split.

- Why it matters: This currently supplies apparent external corroboration without a matching observed quantity or an accurate internal pointer.

- Requested action: Keep the citation as a potential explanation to examine, remove the claim of observed consistency unless a relevant offer-level diagnostic already exists, and repair the internal reference. A new empirical test is unnecessary for a contextual literature paragraph.

### Major comment L3

Qualify the persuasion analogy and correct the reset description

- Location: Appendix E, lines 927–937; main lines 171–178; Appendix B, lines 582–595.

- Observation: “Repeated play removes commitment” treats repetition as the reason commitment is unavailable. The relevant fact is that this environment provides no enforceable commitment to a recommendation policy. Calling Best–Quigley the “closest of all” also skips an important difference: their long-run sender meets a sequence of short-run receivers with public accuracy records; this submission's buyer updates within a game using its own history. Finally, the reset is described as a “fixed counter,” whereas the policy checks the ordering of the latest strict decline and latest purchased LOW.

- Evidence or criterion: The [published Best–Quigley record and abstract](https://ora.ox.ac.uk/objects/uuid%3Aaec04840-9969-4bf0-af0e-0f93fbaf9ed7) describe the sender/receiver population and public records. Appendix B states the implemented history-order test.

- Why it matters: The literature motivates credibility, but a reader should not infer the paper inherits a public-reputation equilibrium or that the mechanism is a simple count threshold.

- Requested action: Write that GLEE's repeated persuasion setting lacks enforceable commitment. Describe Best–Quigley as a related reputation-based model with different receiver and information structure, and replace “fixed counter” with “fixed history-order rule.” Keep the existing statement that no equilibrium analysis was performed.

### Major comment L4

EGTA and alpha-Rank require different positioning from percentile optimization

- Location: Appendix E, lines 939–949.

- Observation: EGTA is grouped among methods that take relative standing as a primitive and “choose a ranking criterion.” The survey instead concerns constructing and analyzing empirical game models from simulations or procedural environments; ranking is one possible application. Alpha-Rank does provide a population ranking, but its evolutionary stationary-distribution ranking is not a same-cell payoff percentile or a result about maximizing that percentile.

- Evidence or criterion: [Wellman, Tuyls, and Greenwald](https://arxiv.org/abs/2403.04018) characterize EGTA as empirical game-model construction and strategic analysis. [Alpha-Rank](https://www.nature.com/articles/s41598-019-45619-9) ranks strategy profiles through evolutionary dynamics. Both sources exist, and the survey's 2025 JAIR metadata matches the bibliography.

- Why it matters: A broad shared concern with strategic evaluation is valid; presenting these methods as evidence for the manuscript's precise transformed-payoff objective creates a category mismatch.

- Requested action: Retain EGTA as context for empirical opponent-population analysis and alpha-Rank as an alternative population-evaluation approach. Explicitly state that neither is used here and neither supplies GLEE's percentile objective. The objective follows from the competition rule; the core toy example is sufficient for the mathematical distinction.

### Major comment L5

The recent citations are valid, but the paper should distinguish verification from attribution without claiming a new distinction

- Location: Main lines 253–260; Appendix E, lines 975–983; recent entries in `references.bib`.

- Observation: The four recent records are real and support the broad topic connection. They are methodologically different from the submission's replay match: CTA compares paired with/without-skill traces; AgenTracer uses counterfactual replay and fault injection; the observability work instruments executions and supports injected failures; and the trajectory-attribution benchmark evaluates attribution localization and chain recovery. The statement that the paper “adds” the distinction between transmission and correct policy selection risks presenting an established limitation of logging as a methodological novelty.

- Evidence or criterion: Direct metadata and abstract checks, listed below. No citation in this group should be removed as a presumed hallucination, and their dates do not postdate this review.

- Why it matters: The manuscript has a useful domain application and unusually explicit evidence boundary, but it does not introduce or run those attribution methods. Readers should understand what is compared and what is merely adjacent literature.

- Requested action: Say that the paper “documents this distinction in a competition deployment” and briefly contrast deterministic replay conformity with intervention-based attribution. Place the core citations after a sentence about tracing/auditing methods rather than after the submission's own statement of missing reconstruction, which those sources cannot substantiate. Do not add more recent citations just to enlarge the bibliography.

| Verified source | Metadata verified on 2026-09-05 | Relevant method, in brief |
|---|---|---|
| [Counterfactual Trace Auditing of LLM Agent Skills](https://arxiv.org/abs/2605.11946v2) | Zhou et al.; submitted 12 May 2026, cited v2 revised 28 May 2026; title/authors match | Paired with/without-skill trace analysis |
| [Observability and Fault Injection for LLM-Based Multi-Agent Systems in Software Engineering](https://arxiv.org/abs/2608.24271v1) | Seyedghorban et al.; submitted 25 August 2026; author list/title match; arXiv links the bibliography's ICST DOI | Instrumented tracing and controlled fault injection |
| [AgenTracer: Who Is Inducing Failure in the LLM Agentic Systems?](https://arxiv.org/abs/2509.03312v2) | Zhang et al.; submitted 3 September 2025, cited v2 revised 4 September 2025; title/authors match | Failure attribution using counterfactual replay and fault injection |
| [Long-Horizon Agent Trajectory Attribution: A Unified Benchmark and Fine-Grained Annotation Framework](https://arxiv.org/abs/2608.06909v1) | Chen et al.; submitted 7 August 2026; title/authors match | Attribution localization and chain-recovery benchmark |

The cited [GLEE v3](https://arxiv.org/abs/2410.05254v3) also matches the bibliography's title, six-author list, original 2024 submission, and 2 March 2026 revision. These checks establish identity and broad claim relevance, not independent replication of the cited papers' empirical results.

## Minor clarity issue

### Minor comment N5

Keep the broader-impact assertions within the measured evidence

- Location: Main lines 316–322.

- Observation: The 668-recommendation shadow is said to show “how cheaply” manipulation is built, but the reported analysis counts selected recommendations and purchases; it supplies no cost measurement. The paragraph also asserts that rank objectives can license exploitation that payoff maximization would not, while the formal example only demonstrates an ordering reversal, not an exploitation comparison.

- Evidence or criterion: The defined shadow measures action frequencies and observed purchases. The score proposition compares expected monetary and percentile outcomes. Neither quantifies implementation cost or a change in manipulative behavior between the objectives.

- Why it matters: A candid broader-impact section should retain the same evidence discipline as the technical sections.

- Requested action: Describe the demonstrated concern directly: a simple deterministic policy can repeatedly recommend known-LOW products, including in an environment that permits human opponents. Frame changed exploitation incentives as a possible risk rather than a demonstrated comparison, and remove the unmeasured cost assertion.

## Core/appendix and figure decisions

Keep the lifecycle figure in the core. It carries an important inference boundary that prose alone makes harder to assess: the endpoint belongs to an evolving account, and much of the rating movement predates the final audited configuration. Its caption appropriately says the events are not isolated effects. The coordinator's PDF pass should assess legibility; this review does not claim a visual inspection.

Keep the route table and the behavior table, but simplify their vocabulary and distinguish owner fall-through from later transforms. They answer different questions: what should choose the action, and what evidence exists that it did. A new architecture figure is optional only if it replaces the current ambiguous arrow notation; adding a third representation of the same route would be redundant.

The three-panel toy payoff/rank figure is mathematically illustrative but optional. The core's two-action example and Appendix A's pair of expected values already explain it completely. Do not promote this figure to the four-page core at the expense of agent behavior or failure analysis. There is no need for a leaderboard screenshot, radar plot, or another rating curve.

Retain the precise schedules, coefficients, parser semantics, defaults, and override precedence in Appendix B; they belong in a reimplementation specification. Retain experiment flow and lifecycle exposure tables in C–D. Condense the repeated prose on what every table does not establish; one evidence-status table plus a short local qualification is often enough. Related work should connect a small number of models to the implemented choices and evidence boundaries, rather than repeatedly reciting methods that were not run.

The core should gain: the retained-clone clarification; a minimal vocabulary for the game and action path; one clear explanation of the reached Bob proxy; and one concrete abstract finding. It can give up: the hidden seller's full summation, some repeated placement/count/causality sentences, and unnecessary operational jargon. These are redistribution choices within the existing study, not requests for a larger experimental program.

## Handoff boundary

No manuscript, code, live configuration, process, or raw participant artifact was modified in this pass. The only authored file is this private review. Suggested revisions should be checked against the final current source before editing because the coordinator is concurrently completing the explicitly requested limited fixes.

# Confidential comments to editor

Not applicable: this is an author-requested working review, and the documented venue intake provides no editor-only channel. All substantive findings are in the author comments above.
