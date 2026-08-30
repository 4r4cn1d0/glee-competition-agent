# Peer Review Report

## Manuscript Information

- **Title**: *Percentiles, Not Payoffs: Strategy and Behavior of a Deterministic GLEE Agent*
- **Manuscript ID**: Not available
- **Review Date**: 2026-08-30
- **Review Round**: Round 1
- **Criteria status**: `criteria_binding_unavailable`
- **Calibration status**: `NOT_CALIBRATED`

No formal `ReviewCriteriaBindingManifest` was supplied. Venue-fit and submission-compliance observations below are therefore advisory readings of the archived GLEE call, not claims of formal venue alignment. This is a role-separated Journal-Fit Reviewer card; no peer reports were consulted.

---

## Reviewer Information

### Reviewer Role

Journal-Fit Reviewer

### Reviewer Identity

Senior NeurIPS workshop competition-track editor experienced in concise agent-system reports, empirical case studies, and Best Competition Paper assessment.

### Review Focus

Whether the four-page paper clearly identifies the agent, strategy, scholarly contribution, and observed behavior; whether the required Agent Behavior Analysis is substantively satisfied; whether the audited draft is submission-ready; and whether its merit, originality, and clarity support an award case independently of leaderboard performance.

---

## Overall Assessment

### Recommendation

- [ ] **Accept**
- [ ] **Minor Revision**
- [x] **Major Revision**
- [ ] **Reject**

### Confidence Score

**4/5 — high confidence in competition-paper positioning and systems-paper assessment; uncertainty remains about the unpublished submission interface, exact appendix policy, official final leaderboard state, and rendered layout.**

### Summary Assessment

This paper presents a deterministic, LLM-free agent spanning GLEE bargaining, negotiation, and persuasion, together with a rank-aware account of the competition objective and an audit framework separating configured policy, returned action, outcome, and causal attribution. The four-page narrative is unusually complete for the format: it explains the objective, the ordered strategy, observed behavior, negative findings, outcomes, and limitations, while the Agent Behavior Analysis directly compares designed and returned behavior. Its strongest scholarly contribution is not the provisional leaderboard lead or the elementary observation that expected payoff and expected percentile can diverge; it is the disciplined action-level evidence contract and the forensic demonstration of how routing, coercion, selection, and non-firing gates defeat naïve evaluation.

The manuscript is nevertheless not submission-ready. Its own checklist says the ethics determination remains unresolved and that the draft must not be submitted; the build includes a large inline appendix despite a four-page call that expressly exempts only references; the anonymous-looking author block is still a placeholder; and the verification artifact is deferred until camera-ready. On merit independent of performance, the paper has Best Competition Paper-caliber ingredients, especially its negative-result discipline and returned-action audit, but the four-page story currently diffuses that contribution among many tactical details. These defects are substantial but repairable, supporting Major Revision rather than rejection.

---

## Strengths

### S1: A defensible contribution exists beyond leaderboard performance

The paper identifies a useful three-part contribution—rank-aware decision framing, an implementable cross-family policy, and an evidence contract—and generally avoids turning tactical success into a scientific claim.

**Evidence Anchor**: `text: paper/main.tex lines 111–116 "We contribute a rank-aware decision account, an implementable three-family policy organized by GLEE's market dimensions, and an evidence contract"`

### S2: The Agent Behavior Analysis operationalizes behavior at the correct interface

The distinction between a configured policy and the legal post-coercion action returned to the SDK is precise, memorable, and broadly useful for evaluating modular agents.

**Evidence Anchor**: `text: paper/main.tex lines 182–187 "A configured flag is not behavior." "The local behavioral object was the legal post-coercion action returned to the SDK"`

### S3: Designed and observed behavior are compared across all three families

The required behavior section is not a perfunctory self-description. It gives family-specific intended behavior, counts or simulations of actual execution, and bounded alignment verdicts.

**Evidence Anchor**: `table: paper/main.tex Table \ref{tab:behavior} — all three family rows distinguish designed behavior, observed behavior, and an alignment verdict`

### S4: Negative evidence genuinely changes the reported strategy

The paper reports adverse, null, unreachable, and incomplete components rather than presenting only successful development episodes. This is unusually strong competition-paper practice.

**Evidence Anchor**: `table: paper/main.tex Table \ref{tab:selection} — broader bargaining, faster concession, leader cloning, and decline parsing are tied to measured evidence and explicit bank consequences`

### S5: Endpoint ratings are not misrepresented as component effects

The discussion correctly recognizes a moving reference population and refuses to divide rating chronology into unsupported causal stories.

**Evidence Anchor**: `text: paper/main.tex lines 274–278 "A live percentile compares against a moving field." "Rating chronology can describe the assembled agent, but it cannot identify which heuristic caused a rise."`

### S6: Provisional first-place wording is appropriately bounded

At the audited timestamp, the title remains performance-neutral and the abstract and results identify the public snapshot, eligible-account scope, and pending close. The source also requires an archived official check before activating first-place language.

**Evidence Anchor**: `text: paper/main.tex lines 227–232 "the public board ranked it first among eligible agent accounts, but the AoE close had not yet occurred"`

---

## Weaknesses

### W1: The manuscript’s own ethics assessment blocks submission

**Problem**: The shared pool may contain human opponents, but no institutional, exemption, or organizer determination has been obtained. The checklist answers “No” to ethics and human-subject review questions and explicitly says the draft must not be submitted.

**Evidence Anchor**: `text: paper/checklist.tex lines 124–127 "This draft must not be submitted until that review is resolved"`

**Why it matters**: The archived call requires compliance with NeurIPS research-ethics policy. This unresolved determination independently prevents acceptance or a responsible submission, regardless of the strength of the technical narrative.

**Suggestion**: Obtain and document the applicable institutional or exemption determination and organizer authorization before submission. Update the main limitations/governance text and checklist consistently. If the determination imposes conditions, describe data handling, consent applicability, privacy protections, and release restrictions precisely.

**Severity**: Critical  
**Confidence**: 5/5 — direct manuscript admission and explicit archived-call requirement

### W2: The inline appendix creates a serious four-page compliance risk

**Problem**: The final source enables `\technicalappendixtrue`, placing a very long appendix into the submitted PDF. The archived call grants up to four pages and unlimited references but does not grant an unlimited inline appendix.

**Evidence Anchor**: `text: paper/main.tex lines 29–32 and docs/reference/glee-docs.md lines 542–544 "The working build includes a technical appendix." "up to 4 pages, NeurIPS 2026 format, unlimited references"`

**Why it matters**: If appendices count toward the limit or are not accepted in the main PDF, the submission could be administratively rejected. Even if separate supplementary material is allowed, embedding it inline obscures what reviewers are meant to judge as the four-page paper.

**Suggestion**: Confirm the competition-track policy directly. Submit a clean four-page main paper plus unlimited references and checklist. Move the technical appendix to a separate supplement only if the submission interface explicitly permits it; otherwise provide a compact, sanitized artifact and retain only indispensable details in the main paper.

**Severity**: Major  
**Confidence**: 4/5 — high-risk advisory reading; exact OpenReview appendix policy was not available

### W3: The strongest award-worthy contribution is not yet the center of the four-page story

**Problem**: The main text distributes attention among three contributions and many exact tactical rules. The memorable title foregrounds percentile scoring, while the more original returned-action evidence contract competes with ladder values, conditional owners, and family-specific heuristics for limited space.

**Evidence Anchor**: `text: paper/main.tex lines 111–116 and 147–150 "We contribute a rank-aware decision account, an implementable three-family policy organized by GLEE's market dimensions, and an evidence contract" "It offered Bob shares $.61,.68,.74,.82,.91$, then left Alice one cent at round 12."`

**Why it matters**: The archived award standard emphasizes scholarly merit, originality, and clarity independent of performance. The percentile propositions are useful but mathematically elementary; the reusable scholarly delta is the audit contract and the evidence-bounded account of failure. The current density makes that delta harder to recognize.

**Suggestion**: Rebuild the four-page hierarchy around one thesis: agent behavior must be evaluated at the returned-action interface, with eligibility, action change, outcome, and causal value kept separate. Present percentile scoring as motivation, summarize the heterogeneous policy in one schematic, and move most numeric tactics to the supplement. State explicitly how this audit contract differs from standard competition postmortems or logged-policy evaluation.

**Severity**: Major  
**Confidence**: 4/5 — core competition-paper editorial expertise

### W4: Core verification assets are unavailable to reviewers at submission

**Problem**: The repository is private at submission, while the sanitized artifact is promised only for camera-ready. The checklist also records incomplete reproducibility, experimental details, uncertainty reporting, and compute accounting.

**Evidence Anchor**: `text: paper/checklist.tex lines 47–70 "The working repository is private at submission." "A frozen, sanitized camera-ready artifact will reproduce the reported calculations and deterministic policy checks"`

**Why it matters**: The paper’s scholarly contribution depends heavily on exact routing, action-change audits, archive joins, and negative-study reconstruction. Deferring the artifact prevents reviewers from checking the very evidence contract being proposed. This does not automatically violate a code-release requirement, but it materially weakens the award case and evidence sufficiency.

**Suggestion**: Provide an anonymous sanitized submission-time artifact containing the banked deterministic policy, effective non-operational configuration, dependency lock, exact reproduction commands, figure/table scripts, deidentified derived tables, and checksums. Clearly enumerate which live-interaction claims remain inherently non-reproducible.

**Severity**: Major  
**Confidence**: 4/5 — systems-paper and reproducibility assessment

### W5: The author block is still a placeholder

**Problem**: The final source contains generic author, affiliation, and email fields despite using a single-blind workshop configuration.

**Evidence Anchor**: `text: paper/main.tex lines 46–50 "Author Name" "Affiliation" "email@example.com"`

**Why it matters**: This does not weaken the academic claims, but it is not a credible final single-blind submission and could create an administrative failure or attribution problem.

**Suggestion**: Replace all placeholders with the exact author metadata required by the workshop and verify that every author has the required active OpenReview profile.

**Severity**: Minor  
**Confidence**: 5/5 — directly visible in source

---

## Detailed Comments

### Title & Abstract

The title is attractive and accurately motivates the scoring mismatch, but it makes the least novel part of the contribution appear primary. Consider whether the returned-action audit should receive equal prominence. The current non-winner title is appropriate. The provisional placement sentence is carefully scoped and should remain so unless the official close, eligibility, and exact placement are archived.

The abstract is information-rich but overloaded with exact ratings, one bargaining sample, and one persuasion failure. For an award-facing four-page paper, one sentence could instead articulate the general audit contribution and why it changes how competition-agent evidence should be interpreted.

### Introduction

The objective-to-contribution chain is clear, and the distinction between expected money and expected rank is correctly bounded. The introduction would be stronger if it stated, in one sentence, what readers knew before and what they know after this paper. At present, the rank observation, policy portfolio, and evidence contract appear co-equal even though only the last two plausibly constitute the distinctive systems contribution.

### Final Submitted Strategy

The no-LLM inference claim and owner-precedence architecture are clear. Figure 1 appears to provide the right organizing abstraction. The prose then spends scarce main-text space on detailed thresholds and exact ladders. Retain enough detail to make the agent identifiable, but move values that do not bear on the scholarly claim to the supplement.

### Agent Behavior Analysis

This is the strongest section. It satisfies the archived call’s substantive request to assess whether behavior aligned with design and how alignment was ensured. The local behavioral unit is well chosen; the family table reports both success and failure; and the paper avoids calling configuration presence execution evidence.

The section could more explicitly distinguish three denominators in the main text: the complete 63-game final-era process census, selected owner-specific execution audits, and simulations. Those are already labeled, but the narrative remains dense enough that a hurried reader could merge them.

### Results and Findings

The negative evidence table is excellent. The provisional leaderboard statement is responsible and should not be upgraded from a public snapshot alone. If an official close result is available, report the archived timestamp, account eligibility, and final placement exactly. If not, keep placement out of the title and retain the provisional wording.

The full-stack ratings support competitiveness of the assembled agent, not the independent merit of its components. The manuscript states this boundary correctly. For award assessment, however, performance should be treated as context only; the paper’s case must survive if every rating and placement sentence is removed.

### Discussion and Conclusion

The three closing lessons are strong, particularly the requirement to audit after routing and coercion. The broader significance would be clearer if the paper named two or three settings beyond GLEE where the same evidence contract applies—for example, modular agents with safety postguards, tool routers, or schema repair—without claiming empirical generalization beyond this case.

### References

The appendix integrates relevant foundations in bargaining, bilateral trade, persuasion, negotiation agents, rank objectives, logged-policy evaluation, and sequential experimentation. The four-page main paper necessarily carries little comparative positioning, but the contribution sentence should still explain more directly how this report differs from prior negotiating-agent competition analyses. The `gleecall2026` entry should be cited where the manuscript discusses page limits, behavior-analysis requirements, or award criteria.

### Submission Compliance — Advisory Only

| Surface | Advisory assessment |
|---|---|
| Four-page main narrative | Substantively complete according to the Phase 0 audit; rendered pagination was not inspected. |
| Required Agent Behavior Analysis | Satisfied in substance and unusually strong. |
| NeurIPS workshop format | The source selects the 2026 single-blind workshop style; formal conformance is not claimed. |
| Author information | Not ready: placeholders remain. |
| Public agent ID | Required in the submission form; not assessable from the authorized manuscript surfaces. |
| Inline appendix | High compliance risk; confirm whether a separate supplement is permitted. |
| Ethics/human-opponent determination | Submission blocker in the manuscript’s own checklist. |
| LLM and asset-policy disclosures | Incomplete. Either remove the weak historical LLM comparison or disclose the best available provenance; complete the asset version/license inventory. |
| First-place wording | Appropriate and provisional at the audited timestamp. Upgrade only from archived official-close evidence. |

### Advisory Award-Competitiveness Assessment

Independent of leaderboard performance, I would **not recommend the paper for Best Competition Paper in its present form**. It does, however, contain award-caliber ingredients:

- a memorable action-level evidence contract;
- unusually honest treatment of null, adverse, unreachable, and non-identifiable results;
- a coherent cross-family strategy indexed by the environment’s structural dimensions; and
- a genuinely substantive behavior-analysis section.

The current award case is weakened by unresolved ethics, uncertain submission packaging, unavailable submission-time artifacts, and a four-page narrative that foregrounds tactical breadth more than its durable scientific contribution. If those issues are repaired and the evidence contract becomes the unmistakable center of the paper, the manuscript could merit award reconsideration on scholarly grounds alone.

---

## Questions for Authors

1. What archived official source establishes the final leaderboard placement, account eligibility, and competition-close status? If no such source exists before submission, will all first-place language remain disabled?
2. What institutional, exemption, or organizer determination governs the analysis of games that may involve human opponents, and will that determination be documented before submission?
3. Does the competition-paper OpenReview form explicitly permit a separate technical supplement or appendix beyond the four-page paper and unlimited references?
4. Can a sanitized anonymous artifact be released at submission rather than camera-ready, and which reported results would it reproduce exactly?

---

## Minor Issues

### Language / Grammar

- The prose is generally excellent but exceptionally compressed. Several sentences combine method, finding, caveat, and interpretation; selective splitting would improve clarity.
- Define “bank,” “banked,” and “owner” at first use for readers outside the project.

### Citation Format

- Cite `gleecall2026` explicitly when discussing the paper-track requirements and award standard.
- Check whether all bibliography entries are cited in the final four-page and supplement package.

### Figures and Tables

- The two main tables use `\scriptsize` and carry many clauses per cell. Verify legibility at the final PDF scale.
- Keep captions self-contained about sample type, denominator, and causal status.

### Layout and Finalization

- Resolve `\winnerverifiedfalse` deliberately in the archived final build; do not let the branch change without matching official evidence.
- Reconcile the checklist’s LLM, license, safeguards, and broader-impact answers with the appendix’s admitted historical LLM comparison and planned strategic-code release.

---

## Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | Review Criteria Framework §1; Phase 0 EIC card | **MEETS** | `text: paper/main.tex lines 111–116 "We contribute a rank-aware decision account, an implementable three-family policy organized by GLEE's market dimensions, and an evidence contract"` | The returned-action audit and evidence separation are defensible contributions; the rank result itself is elementary and comparative novelty is not sharply established in the main text. | No formal target binding; no comparison with other 2026 competition submissions. | **Yes** — central to the award assessment. |
| Methodological Rigor | Review Criteria Framework §§1, 2.1, 2.4 | **PARTLY_MEETS** | `text: paper/appendix.tex lines 708–715 "They therefore do not carry unconditional 95% coverage."` | Identification threats are recognized unusually well, but many analyses remain retrospective, selected, repeatedly inspected, or incompletely preserved. | This EIC card does not substitute for the methodology reviewer. | **Yes** — supports Major Revision, not rejection, because claims are mostly bounded. |
| Evidence Sufficiency | Review Criteria Framework §1 | **PARTLY_MEETS** | `text: paper/appendix.tex lines 1270–1275 "cannot replay private live interactions or re-audit every source-to-server join"` | The final-era census and selected audits are useful, but submission-time independent verification and universal owner-to-wire evidence are unavailable. | Private live data may be irreducibly unreleasable. | **Yes** — material to acceptance readiness and award competitiveness. |
| Argument Coherence | Review Criteria Framework §1 | **MEETS** | `text: paper/main.tex lines 182–184 "what an owner was meant to do, whether it changed the returned action, and whether the resulting policy improved rank"` | Objective, policy, behavior, and evidence status form a traceable chain. The primary scholarly thesis nevertheless competes with tactical detail. | Rendered pacing was not inspected. | **Yes** — the remaining issue is repairable through restructuring. |
| Writing Quality | Review Criteria Framework §1; archived call clarity criterion, advisory only | **PARTLY_MEETS** | `text: paper/main.tex lines 147–150 "It offered Bob shares $.61,.68,.74,.82,.91$, then left Alice one cent at round 12."` | The prose is precise, but the main narrative is overcompressed and gives exact strategy values space needed for contribution framing. | Source review only; no rendered PDF inspection. | **Yes** — clarity is explicitly relevant to the advisory award assessment. |
| Literature Integration | Review Criteria Framework §1 | **MEETS** | `text: paper/appendix.tex lines 1113–1122 "We instead study the design, returned behavior, and field outcome of one deterministic competition agent"` | The supplement covers the appropriate economic, negotiation-agent, persuasion, ranking, and evaluation literatures. | Most positioning is outside the four-page main story. | **No for basic acceptance; yes at the margin for originality positioning.** |
| Significance & Impact | Review Criteria Framework §1; Phase 0 award-facing standard | **MEETS** | `text: paper/main.tex lines 290–299 "deployed behavior must be audited at the returned action, after routing and coercion"` | This lesson matters beyond one leaderboard and can improve evaluation of modular strategic agents. Its transferability is argued rather than demonstrated. | No empirical validation outside this agent and competition. | **Yes** — the paper’s award case should rest here, not on placement. |

### Recommendation Rationale

The positive criteria are originality, argument coherence, literature integration, and a meaningful audit contribution. Acceptance is presently blocked by a repairable Critical ethics defect, while submission packaging, submission-time verification, and contribution hierarchy require substantial revision. No unfixable scientific failure is evident, so **Major Revision** is more appropriate than Reject.
