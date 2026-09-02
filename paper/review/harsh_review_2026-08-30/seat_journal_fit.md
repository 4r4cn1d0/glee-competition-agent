# Journal-Fit and Award-Competitiveness Review

## Review identity and scope

**Role:** Venue-fit and Best Competition Paper reviewer for the NeurIPS 2026 IAB Workshop GLEE Competition Paper Track.

**Materials reviewed:** `paper/main.tex`, the exact candidate `paper/main_core.pdf`, `paper/README.md`, the locally retained public call text in `docs/reference/glee-docs.md:540-568`, and the authoritative live-call check supplied to this panel. I did not use the internal technical supplement to cure omissions in the submitted core. I did not read another report from this review panel before committing this one.

**Exact candidate receipt:** `paper/main_core.pdf`, SHA-256 `f64ac2be20db56c434204ddc715833ef0dd81cd744a4578ac29ad5bc5876ac7e`, created 2026-08-30 18:32 IST. It has 12 pages: four content pages, references on page 5, and the NeurIPS checklist on pages 6-12. All fonts are embedded. The main pages have no visible clipping, overlap, or illegible table text.

**Calibration status:** `NOT_CALIBRATED`.

**Recommendation:** **Major Revision**. The work is strongly in scope and has a credible acceptance case. The exact candidate is not ready to submit, and the current four-page narrative is not yet competitive for Best Competition Paper.

**Confidence:** 5/5. The venue criteria, exact rendered candidate, page-budget tradeoffs, and competition-paper positioning are directly reviewable. I do not use this confidence as a vote weight.

## Summary assessment

This is a technically serious and unusually candid account of a deterministic, LLM-free GLEE system that finished second in the agent track and third on the combined board. The rank-aware objective is relevant, the post-close result is prominent, the required Agent Behavior Analysis is substantive, and the authors are disciplined about distinguishing endpoint performance, live description, retrospective diagnostics, simulation, and causal evidence. Those are real strengths.

The central editorial weakness is severe: after four dense pages, a reviewer can describe the returned-action audit much more readily than the runner-up strategy. The bargaining paragraph gives one narrow Bob schedule but not the overall family policy. The negotiation paragraph spends substantial space defining a proxy without reporting the resulting operational policy, then compresses most other branches into one sentence. The persuasion paragraph names theory and components but not a reviewable decision map. The manuscript therefore reads as an audit-method case study with an agent attached, despite the call asking first for a clear and complete description of the agent, its motivation, technical approach, strategic choices, development, and evaluation.

This imbalance also weakens the award case. Best Competition Paper is judged on scholarly merit, originality, and clarity independently of leaderboard performance. The paper has award-worthy ingredients, especially the negative-result discipline and action-level audit, but its audit novelty is positioned against only two adjacent works in one sentence, its production-equivalent evidence is unavailable to reviewers, and its own main text disclaims component attribution. The appropriate decision is Major Revision, not Reject, because the core is honest and the needed narrative repair can be achieved by replacing lower-value material rather than inventing new evidence.

## Criterion-bound judgements

| Criterion | Source | Judgement | Evidence | Decision bearing |
|---|---|---|---|---|
| Relevance to GLEE and IAB | Live call criteria and `docs/reference/glee-docs.md:542-567` | EXCEEDS | `main_core.pdf` pp. 1-4 are entirely about GLEE strategy, returned behavior, failures, and evaluation | Strong positive |
| Clarity and completeness of agent description | Live call criteria | PARTLY_MEETS | `main.tex:123-208`; only selected branches are operationally described | Major revision needed |
| Motivation and insight | Live call criteria | EXCEEDS | Equation 1 and the terminal-rank expression at `main.tex:90-111`; negative findings at `main.tex:292-312` | Strong positive |
| Technical soundness within claimed scope | Live call criteria | MEETS | Claims are repeatedly bounded in `main.tex:90-121`, `240-258`, and `280-343` | Positive, subject to specialist review |
| Quality of evaluation and Agent Behavior Analysis | Live call criteria and required section | MEETS | Section 3 and Table 2 at `main_core.pdf` p. 3; `main.tex:210-258` | Positive, but not award-leading because census-wide conformance is unavailable |
| Reproducibility | Live call criteria | DOES_NOT_MEET | `main_core.pdf` p. 4, lines 131-136; `paper/README.md:60-78`; checklist pp. 7-8 | Acceptance and award risk |
| Originality | Best Competition Paper criteria | PARTLY_MEETS | Contribution contrast is limited to `main.tex:119-121`; no baseline, ablation, or second deployment validates the audit as a general method | Major award risk |
| Clarity | Best Competition Paper criteria | PARTLY_MEETS | Four dense pages, four tables, two equations, no at-a-glance policy map | Major award risk |
| Submission readiness | NeurIPS single-blind and ethics requirements | DOES_NOT_MEET | Placeholder author block at p. 1; unresolved ethics statement at checklist p. 9 | Current submission blocked |

## Genuine strengths

### S1. The required Agent Behavior Analysis is real rather than ceremonial

Section 3 reports returned actions, outcomes, missing conformance denominators, separate branch-reach checks, and the procedures used to detect unreachable gates and treatment leakage. It directly addresses whether behavior aligned with design and how alignment was checked, while stating where alignment cannot be established.

**Evidence anchor:** text: `main_core.pdf` p. 3, lines 87-106; `main.tex:210-258`, "execution alignment is sampled and bounded."

### S2. The competition result is prominent and responsibly qualified

The second-place agent-track result appears in the abstract and in a dedicated post-close table. The paper correctly says that this establishes competitiveness of the adaptive account/profile system, not a causal effect of one component.

**Evidence anchor:** table: `main_core.pdf` Table 3, p. 4, "Agent 2nd; combined 3rd" with overall rating 2590.02.

### S3. The rank objective gives the paper a genuine technical hook

The safe-versus-lottery example and the terminal proposal expression explain why expected payoff and expected competition rank can differ. This is the most memorable strategic motivation in the paper and is accessible without private logs.

**Evidence anchor:** equation: `main_core.pdf` Equation 1, p. 1, and the terminal raw-rank expression continued on p. 2; `main.tex:90-111`.

### S4. Negative evidence is handled with unusual discipline

The manuscript reports the stopped clone at both looks, the higher no-deal rate, the negative focal-profile stratum, the sign-reversing replay, and the missing replay recipe. It does not rescue these results with post hoc subgrouping.

**Evidence anchor:** text: `main_core.pdf` p. 4, lines 116-130; `main.tex:292-312`, "It failed its frozen promotion rule."

### S5. The rendered four-page core is clean and compliant in length

The main content ends exactly on page 4, references begin on page 5, and the mandatory checklist follows. Typography is dense but still legible, and the four main pages are self-contained in the narrow sense that they do not cite an appendix for an essential proof.

**Evidence anchor:** dataset: `paper/main_core.pdf` page structure and font inspection, pages 1-12; `paper/README.md:18-40`.

## Decision-bearing weaknesses

### W1. The core does not adequately explain the runner-up strategy

**Severity:** Major

**Evidence anchor:** text: `main_core.pdf` pp. 2-3, lines 58-86; `main.tex:157-208`, "Other hidden buyers used reservation-bound inference or observed-leader price paths."

**Evidence:** Bargaining describes one silent-Bob, disclosed-12-round schedule and a coarsened Bob offer proxy, but not the general Alice policy, generic acceptance logic, or full family routing. Negotiation gives a dense hidden-seller construction but not the selected multipliers or a compact account of acceptance, walking, buyer paths, and fallbacks. Persuasion names an obedience benchmark, a conservative `q=0` choice, a credibility posterior, a reset, and a veto, but not the actual decision thresholds or precedence. Table 2 reduces the three families to phrases such as "structural owners then fallbacks" and "posterior, reset, and final veto." A reader cannot reconstruct the final policy at the level expected of a competition paper.

**Why it matters:** The live call explicitly evaluates clarity and completeness of the agent description, technical approach, and strategic design choices. The excluded technical supplement cannot repair this. More importantly, the paper's second-place result creates a reasonable expectation that the core will tell readers what the agent did and why those choices were sensible.

**Bounded remedy:** Replace Table 1 with one compact final-policy map. Give one row per family and, within each row, the public-state split, decision owner, representative outgoing action or acceptance rule, last postguard, and rationale/evidence class. For Equation 2, either report the actual selected multiplier for each supported seller type or replace the equation with the operational choices. Use four short sentences per family: trigger, action, fallback, and reason. Do not attempt to enumerate all 81 flags.

### W2. The audit framing eclipses the agent contribution

**Severity:** Major

**Evidence anchor:** table: `main_core.pdf` Table 1 on p. 2 and Table 4 on p. 4; source at `main.tex:138-155` and `314-331`.

**Evidence:** The title foregrounds returned-action audits. The contribution paragraph assigns two of three contributions to execution evidence and failure reporting. A generic four-stage audit contract occupies substantial space on page 2, the mandatory behavior section occupies most of page 3, and a second claim-status table occupies page 4. By contrast, the final strategy has no overview table or figure and is explained through three dense paragraphs. The conclusion again ends on the audit proposal rather than the strategic lessons of the runner-up agent.

**Why it matters:** The manuscript currently has two competing identities: a competition-system paper and a general action-audit paper. The evidence supports the first more strongly. The audit is valuable as the means by which the strategy is interpreted, but the paper does not validate it as a general method across systems, baselines, or deployments. Making the less-validated contribution dominant lowers both clarity and originality.

**Bounded remedy:** Choose the competition agent as the primary subject and the audit as the evidence discipline. Rewrite the contribution paragraph in that order: final strategy, rank-aware insight, then returned-action audit and negative lessons. Keep the audit stages in one sentence or in the caption of the replacement policy map. End with the strategic lessons that survived, not only a reporting prescription.

### W3. The four-page budget is spent on caveats and machinery more than inference

**Severity:** Major

**Evidence anchor:** dataset: `paper/main_core.pdf` pp. 1-4 contain approximately 2,372 extracted words, four tables, two equations, and no figure; the abstract alone is approximately 242 words.

**Evidence:** The abstract carries the result, profile size, census size, rated count, timeout count, per-family outcome inventory, and a four-turn failure before stating the general lesson. Page 2 gives a generic audit table. Page 4 gives both a result table and a claim-limit table, plus two long failure narratives. The final conclusion is only two sentences. The main pages are visually clean, but every page after the first is near 600 extracted words and the dominant experience is compression rather than hierarchy.

**Why it matters:** Clarity is an explicit review and award criterion. A four-page reviewer needs to identify the agent's three memorable strategic choices, the strongest evidence, and the main limitation in one pass. This draft asks the reviewer to decode implementation vocabulary and evidence taxonomies before obtaining that summary.

**Bounded remedy:** Cut Table 4 and convert its six rows into one sentence that points to existing qualifiers. Compress the clone and replay failures into a two-row negative-results table or five sentences total. Reduce the abstract to the objective, agent, exact result, one behavior finding, and bounded conclusion. Spend the recovered space on the final-policy map and a three-sentence conclusion that answers what the system did, what was learned, and what remains unknown.

### W4. The result is prominent, but the result-to-strategy story is intentionally unresolved and not replaced by a strong alternative

**Severity:** Major

**Evidence anchor:** text: `main_core.pdf` p. 4, lines 108-115; `main.tex:280-290`, "none passed a precommitted efficacy-promotion rule."

**Evidence:** The manuscript properly refuses to attribute second place to a single component. It also says the rating is an adaptive trajectory, not a frozen policy, and that none of 35 bounded development records passed a precommitted efficacy-promotion rule. Those disclaimers are scientifically correct. The remaining positive story, however, is mostly that retained rules had structural or operational rationales. The paper does not clearly identify which strategic insights were mathematically justified, which were safety fixes, which were copied behaviors, and which merely survived without a causal verdict.

**Why it matters:** A competition paper need not provide a clean ablation for an online adaptive system, but it must give readers a useful account of why the final design took its form. Without that account, the second-place result and the strategy section sit beside each other rather than forming a coherent contribution.

**Bounded remedy:** Do not manufacture component causality. Instead, label the final strategy components in the policy map as mathematical construction, structural dominance, behavior imitation, safety correction, or unresolved heuristic. Select one high-value lesson per family and state why it remained in the final profile. Keep the statement that no component passed the promotion rule, but make the noncausal design logic explicit.

### W5. The audit contribution is under-positioned for an originality award

**Severity:** Major

**Evidence anchor:** text: `main_core.pdf` p. 2, lines 41-47; `main.tex:113-121`, "our narrower contract checks eligibility, selection, and post-coercion return before joining an economic outcome."

**Evidence:** The paper cites AgentBoard and Counterfactual Trace Auditing and gives one sentence of differentiation. It does not explain whether eligibility-authority-return-outcome auditing is new as a method, new only in economic-agent competitions, or a careful integration of familiar tracing and causal-design practices. The three caught failures demonstrate utility in this case, but no baseline, audit-element ablation, or second system demonstrates a general advance.

**Why it matters:** Best Competition Paper is independent of rank and explicitly values originality. The current audit claim is the manuscript's most prominent scholarly claim, yet its novelty basis is thinner than the space allocated to it.

**Bounded remedy:** Add a short related-work contrast, using the unlimited reference allowance, that distinguishes trace-quality evaluation, counterfactual action comparison, experimentation infrastructure, and this paper's economic outcome join. Under the available evidence, call the contribution an integrated competition case-study protocol, not a generally validated audit method. A stronger general-method claim would require evidence not currently available and should not be forced into this submission.

### W6. Review-time reproducibility does not satisfy the call

**Severity:** Major

**Evidence anchor:** text: `main_core.pdf` p. 4, lines 131-136; `main.tex:334-340`, "but not private joins, server receipt, or production source."

**Evidence:** The paper says the bundle reproduces aggregate arithmetic, mathematical checks, synthetic fixtures, and two figures, but not the private joins, receipt, or source needed for the central returned-action claims. The README says the anonymous bundle has not been uploaded and is not part of the one-PDF submission (`paper/README.md:60-78`). The checklist answers No for experimental reproducibility and open access. The excluded supplement cannot help a reviewer.

**Why it matters:** Reproducibility is an explicit call criterion. This is especially consequential because the paper's main novelty claim is an audit protocol. A protocol that reviewers cannot execute against production-equivalent evidence is hard to rank above a strong descriptive case study.

**Bounded remedy:** If the organizers permit an anonymous artifact link, make the narrow bundle accessible at review time and state exactly which claims each command verifies. If no artifact channel is allowed, narrow the audit claim in the abstract, contribution paragraph, and conclusion to a documented internal practice, and put the finite verifier inputs and commands in a stable anonymous URL cited from the core. Do not imply that a conditional camera-ready release supports review-time reproducibility.

### W7. The title is accurate but undersells the competition contribution

**Severity:** Minor

**Evidence anchor:** text: `main_core.pdf` p. 1 title; `main.tex:42`, "Rank-Aware Routing and Returned-Action Audits in GLEE."

**Evidence:** The title is precise and professional, but it is audit-first and does not tell a workshop reader that this is the runner-up agent case study. "Routing" is also abstract until late in the paper.

**Why it matters:** For an award candidate, the title should surface the most distinctive combination: runner-up performance, rank-aware strategy, and disciplined audit. The current title could describe an instrumentation paper without a competition result.

**Bounded remedy:** Consider a title such as "Building the Runner-Up GLEE Agent: Rank-Aware Strategy and Returned-Action Audits." If the authors prefer not to lead with rank, use "A Rank-Aware GLEE Agent: Strategy, Failures, and Returned-Action Audits." Avoid "winning" because the documented result is second place.

## Exact-candidate submission blockers

### W8. The single-blind author block is still a placeholder

**Severity:** Critical for submission, trivial to repair

**Evidence anchor:** text: `main_core.pdf` p. 1 author block; `main.tex:44-48`, "Author Name" and "email@example.com."

**Why it matters:** The call uses lightweight single-blind review. The exact PDF cannot be submitted with dummy author metadata.

**Bounded remedy:** Replace name, affiliation, and email, rebuild `main_core.pdf`, and visually verify page 1 and PDF metadata before upload.

### W9. The checklist states that the ethics and human-opponent determination is unresolved

**Severity:** Critical for submission

**Evidence anchor:** text: `main_core.pdf` p. 9; `paper/checklist.tex:124-127`, "This draft must not be submitted until that review is resolved."

**Why it matters:** The call requires NeurIPS ethics compliance. The checklist also records unresolved human-subjects and institutional classification at `paper/checklist.tex:190-204`. This is not a narrative weakness that can be cured by softer wording.

**Bounded remedy:** Obtain the applicable organizer and institutional determination, then update the checklist and core statement to report the resolved basis accurately. If the determination cannot be obtained, do not submit this candidate.

## Direct answers to the assigned questions

### Does the paper explain the runner-up strategy?

**Not adequately.** It explains the scoring incentive, the routing philosophy, one narrow bargaining schedule, one hidden-seller construction, and the theoretical basis of the persuasion branch. It does not provide a compact operational map of the final policy across roles and observable cells. The most important missing information is not another threshold list; it is decision hierarchy: which public states select which owner, what that owner actually returns, what fallback follows, and what postguard can replace it.

### Does the audit framing eclipse the agent contribution?

**Yes.** The audit is the better-explained object and receives the title, two tables, most of the contribution statement, the mandatory behavior section, and the final sentence. The agent itself receives three dense paragraphs without a synthesis artifact. This is the wrong hierarchy for the evidence currently available.

### Is the competition result prominent enough?

**Yes.** It appears in the abstract and in Table 3, with appropriate account/profile qualifications. The problem is not prominence. The problem is that the manuscript cannot tell an equally crisp story about the design that achieved it.

### Is the balance among strategy, theory, evidence, and failures effective?

**No.** Theory and evidence discipline are strong. Failures are unusually informative. Strategy is compressed and fragmented. The manuscript should retain the honest failure evidence but replace generic audit machinery and duplicated caveat tables with final-policy explanation.

### Is the paper competitive for Best Competition Paper?

**Not as submitted.** It is likely more competitive for acceptance than for the award. The strongest award case is the combination of a runner-up deterministic agent, a nonstandard rank objective, and unusually disciplined negative evidence. The current draft diffuses that case by making an incompletely validated audit protocol the lead contribution, providing only a thin novelty contrast, and offering no reviewer-accessible production-equivalent artifact. A focused revision could make it a serious award candidate, but leaderboard rank alone cannot carry that case under the call.

## Figure recommendation

Recommend **one replacement figure at most**, not an additional figure. Replace Table 1 with a three-lane final-policy routing diagram. Each lane should show public state and role, selected family owner, representative action rule, last postguard, and returned wire. A thin shared footer can show the four audit receipts. This materially improves inference because a reviewer can see both what the agent does and where alignment is checked. Do not add a second figure. Delete Table 4 and use its space for concise prose and the conclusion.

## Questions for the authors

1. What are the three strategic decisions, one per family, that a reviewer should remember as constituting the final runner-up policy?
2. Is the primary scholarly claim a competition-agent case study or a generally reusable audit method? The current evidence supports the former more strongly.
3. What anonymous artifact, if any, will a reviewer actually be able to access during review, and which exact core claims can it verify?
4. What organizer or institutional determination resolves the possible human-opponent data use, and will it be in hand before submission?

## Ranked revision list

1. **Clear both submission blockers:** replace the author placeholder and obtain the required ethics/data-use determination. Rebuild and recheck the exact PDF.
2. **Make the runner-up agent reconstructible from the core:** replace Table 1 with the final-policy map and state trigger, action, fallback, and rationale for each family.
3. **Recenter the story:** present agent strategy first, rank-aware insight second, and returned-action audit as the evidence discipline. Retitle accordingly.
4. **Reclaim the page budget:** remove Table 4, compress the abstract and two failure narratives, and give the conclusion enough space to state the strategic lessons.
5. **Clarify evidence status component by component:** label final rules as mathematical, structural, safety, imitation, or unresolved heuristic without implying causal promotion.
6. **Strengthen originality positioning:** add a concise related-work contrast and narrow the audit claim to what this one case establishes.
7. **Provide review-time reproducibility or narrow the claim:** expose the anonymous verifier if permitted; otherwise stop presenting a conditional camera-ready artifact as support for the review submission.

## Final recommendation

**Major Revision.** Strong venue fit and a plausible eventual accept, but reject the exact candidate for submission until the author and ethics blockers are cleared. On scholarly merit, the paper has real strengths, yet it is not Best Competition Paper competitive until the four-page core explains the runner-up strategy at least as clearly as it explains the audit.
