# Editorial Decision

## Manuscript information

- **Title**: *Percentiles, Not Payoffs: Strategy and Behavior of a Deterministic GLEE Agent*
- **Manuscript ID**: Not available
- **Decision date**: 2026-08-30
- **Review round**: Round 1 author-requested panel
- **Calibration**: NOT_CALIBRATED
- **Criteria binding**: criteria_binding_unavailable

This is an advisory model panel, not an official IAB or NeurIPS decision and not a contract-bound venue-alignment determination.

## Panel provenance

See [panel_provenance.md](panel_provenance.md). Five role-separated seats committed reports in separate fork_turns="none" contexts without peer-output access. Model family and provider receipts were unavailable, no human reviewer participated, and correlated model errors cannot be ruled out. The canonical provenance schemas and builder referenced by the skill were absent, so no replay-valid typed artifact was produced.

The manuscript was edited while the panel ran. Seat reports remain immutable assessments of the versions each seat saw. The current-source repair audit below identifies changes already present after those reports; it is not a formal re-review.

## Decision

### Major Revision

All four scoring seats independently recommended Major Revision with confidence 4/5. The Devil's Advocate identified one Critical issue, unresolved human-opponent research ethics, that is corroborated by EIC and R3 and by the manuscript's own checklist. It blocks Accept until resolved. The remaining weaknesses are substantial but repairable, so Reject is not warranted.

Advisory Best Competition Paper assessment: **not award-ready in the reviewed state, but plausibly award-competitive after the blockers below are resolved**. The strongest award case is the returned-action evidence contract, the exact multi-family policy ownership map, and the unusually candid negative-result account, not the provisional rank alone.

## Blocking issues

| Ref | Blocking issue | Source seats | Evidence anchor | Resolving item |
|---|---|---|---|---|
| B1 | No completed institutional, exemption, or organizer determination for analyses that may include human opponents | EIC W1; R3 W1; DA Critical | text: paper/checklist.tex, Code of ethics, "This draft must not be submitted until that review is resolved" | REV-1 |
| B2 | The exact submission package is not finalized: author placeholders remain and inline-supplement permission is unconfirmed | EIC W2/W5; DA submission-package Major | text: paper/main.tex author block, "Author Name", "Affiliation", "email@example.com" | REV-2 |
| B3 | Central execution and randomized-study claims are not independently auditable at review time | EIC W4; R1 W2/W3; R3 W5; DA audit Major | text: Appendix Reproducibility, "cannot replay private live interactions or re-audit every source-to-server join" | REV-3 and REV-4 |

## Reviewer summary

| Seat | Role | Recommendation | Confidence |
|---|---|---|---|
| EIC | Competition-track fit and Best Paper competitiveness | Major Revision | 4/5 |
| R1 | Online experimentation, statistics, reproducibility | Major Revision | 4/5 |
| R2 | Game theory, automated negotiation, GLEE | Major Revision | 4/5 |
| R3 | Agent behavior, HCI, reproducibility, ethics | Major Revision | 4/5 |
| DA | Fixed Devil's Advocate | Findings only | Per finding |

## Consensus analysis

### Points of agreement

**[CONSENSUS-4]** All four scoring seats found a defensible contribution in auditing the post-routing, post-coercion returned action rather than treating a configured branch as behavior.

**[CONSENSUS-4]** All four found the negative-result discipline and separation of theorem, implementation, observation, and causal effect unusually strong.

**[CONSENSUS-4]** All four concluded that current evidence is insufficient for an unqualified final-policy or component-effect claim and recommended Major Revision rather than Reject.

**[CONSENSUS-3]** EIC, R1, and R3 found submission-time verification materially incomplete; R2 reached the parallel domain conclusion that the full banked action function is not reconstructible. These are different formulations of one reproducibility boundary, not independent evidence.

### Points of disagreement or emphasis

1. **Primary scholarly contribution.** EIC and R3 viewed the returned-action evidence contract as the strongest contribution. R2 emphasized that the exact policy remains under-specified and that the rank objective is not the objective of every owner. The editor accepts both: the paper is strongest when it presents an exact strategy and uses the evidence contract to interpret it, while explicitly labeling money, agreement, rank, and safety objectives branch by branch.

2. **Endpoint wording.** R1 and DA treated final-policy competitiveness language as Major because 46,383 games span an adaptive trajectory and the fixed final era has only 63 games. The later current source now says “competitive adaptive trajectory,” quantifies the final-era family counts, and disclaims isolation of the fixed policy. This finding is materially repaired in the current source, subject to re-review after rebuild.

3. **Rank-aware framing.** R2 found the title-to-policy link incomplete. The later current source now states that only two subcomponents directly optimized a local raw-rank surrogate and that other owners targeted money, agreement, or safety. This narrows the claim appropriately, but a versioned branch-objective manifest is still needed for full reproducibility.

4. **Ethics severity.** EIC, R3, and DA classified the unresolved determination as Critical; R1 and R2 were silent rather than disputing it. Because the checklist explicitly says not to submit until resolved, the Critical finding is validated and blocks Accept.

## Decision rationale

The paper already does several things at an unusually high level. It gives a coherent cross-family strategy, uses GLEE's market dimensions rather than a universal tactic, distinguishes local rank proxies from the undisclosed scorer, and reports adverse, invalid, unreachable, and inconclusive development results. Its required Agent Behavior Analysis has a strong conceptual unit, the returned action after routing and coercion, and now includes a complete 63-game final-era process census. These strengths justify continued consideration and a credible Best Paper path.

Major Revision is nevertheless required. The ethics question is explicitly unresolved and independently blocks responsible submission. The exact review package still has placeholder authors and uncertain supplement handling. Reviewers also cannot verify the central provenance chain, and the future artifact cannot fully reproduce private assignment or source-to-server joins. The final-era census does not yet give owner-level eligibility, firing, conformity, semantic validity, and receipt counts, while the language failure lacks a coverage denominator. Account, profile, host, and “four-account” terminology also need reconciliation against the one-account rule.

The later source repaired two important overclaims during review: endpoint ratings now describe the adaptive trajectory, and the text now states which branches optimize rank versus other objectives. Those repairs reduce, but do not eliminate, the need for an exact policy manifest and submission-time artifact. Because all remaining defects have bounded remedies and no reviewer found a fatal mathematical error, Major Revision is appropriate.

## Devil's Advocate Critical adjudication

**DA Critical: unresolved possible-human-opponent research ethics**

- **Status**: Validated and unresolved.
- **Corroboration**: EIC W1 and R3 W1 independently identified the same defect; the checklist answers No and says not to submit until the review is resolved.
- **Decision effect**: Accept is unavailable while this remains unresolved.
- **Why not Reject**: An institutional or organizer determination, plus any required cohort exclusions or disclosure changes, can resolve the issue without necessarily invalidating the technical contribution.

## Critical and Major finding crosswalk

| Source finding | Editorial disposition |
|---|---|
| EIC W1, R3 W1, DA Critical: human-opponent ethics | Must fix in REV-1; blocks Accept. |
| EIC W2 and DA packaging Major: four-page and inline appendix risk | Partly repaired by the corepaper build route; finalize and verify in REV-2. |
| EIC W3 and DA originality Major: award contribution not sufficiently centered or differentiated | Improved by the strategy-origin paragraph and evidence-contract framing; complete REV-7. |
| EIC W4, R1 W3, R3 W5, DA audit Major: review-time artifact and provenance incomplete | Must fix in REV-3. |
| R1 W1 and DA endpoint Major: lifetime rating does not isolate final policy | Materially repaired in current source by adaptive-trajectory wording; verify in re-review. |
| R1 W2: randomized clone lacks a closed auditable analysis contract | Must fix or further downgrade in REV-4. |
| R2 W1: final policy not fully reconstructible | Must fix in REV-3 through a versioned policy manifest and exact tables or hashes. |
| R2 W2: rank objective not mapped to retained owners | Materially narrowed in current source; finish branch mapping in REV-7. |
| R3 W2 and DA behavior Major: heterogeneous cohorts do not close final-era design-to-action alignment | Must fix or narrow in REV-5. |
| R3 W3: persuasion warning failures lack a semantic-coverage denominator | Must fix or narrow in REV-5. |
| R3 W4 and DA profile/account Major: account, profile, host, and possible self-play provenance ambiguous | Must fix in REV-6. |
| R3 W6: dual-use and privacy safeguards inconsistent with acknowledged risk | Must fix in REV-1 and REV-6. |
| DA selection Major: candidate universe and retention story remain incomplete | Add the released registry and clearly separate efficacy, safety, and operational retention in REV-3. |

## Organizer-feedback audit of the current source

| Organizer concern | Current status | Editorial assessment |
|---|---|---|
| Explain where the strategy came from and what inspired it | **Satisfied in current source** | The new strategy-origin paragraph explicitly links GLEE dimensions, economic theory, live logs, public leader trajectories, and negative trials. Preserve it. |
| Put reproducibility detail in the appendix while keeping the main paper readable | **Partly satisfied** | The main paper has strategy and evidence summaries; the appendix has derivations, policy ownership, registry, coverage, and governance. Missing exact policy tables or hashes and a submission-time artifact prevent full satisfaction. |
| Put the prominent competition result in the abstract | **Satisfied, conditionally** | The abstract reports the dated ratings and provisional lead, correctly labeled as an adaptive-trajectory endpoint. Flip to first-place language only from an archived official post-close record. |
| Discuss failed strategies and rating reversals | **Satisfied strongly** | Main Table 2 reports four decisions, including rejected broadening, faster concession, failed leader imitation, and parser failure; the results text reports a rating seesaw and moving-field caveat. |

## Required revisions

### REV-1: Resolve ethics, privacy, and release-governance authority

- **Sources**: EIC W1; R3 W1/W6; DA Critical.
- **Requirement**: Obtain the applicable institutional, exemption, or equivalent determination and organizer authorization. State the data source, possible human inclusion, notice or consent basis, deception and profiling risk, retention and access controls, transcript handling, and whether any analyses must exclude or bound human games. Reconcile the safeguards checklist answer with the acknowledged dual-use policy release and add a proportionate release threat model.
- **Acceptance criterion**: The checklist no longer says the draft must not be submitted; the determination and any resulting data or release restrictions are documented consistently without exposing identifying information.

### REV-2: Freeze and verify the exact submission package

- **Sources**: EIC W2/W5; DA packaging Major.
- **Requirement**: Replace author placeholders, confirm all OpenReview profiles and the public agent ID submission field, rebuild the exact single-blind core PDF, verify that main text ends on page 4 and references begin after it, and obtain organizer confirmation before attaching the inline technical appendix. Keep the appendix as separate supplemental material if that is the permitted route.
- **Acceptance criterion**: One archived submission PDF and, if allowed, one supplement are identified by checksum; author and workshop metadata are final; no unverified first-place switch is active.

### REV-3: Ship a frozen submission-time verification artifact

- **Sources**: EIC W4; R1 W3; R2 W1; R3 W5; DA audit and selection Majors.
- **Requirement**: Include the exact banked policy source, non-operational effective configuration, dependency lock, exact commands, figure and table generators, a versioned policy manifest with every owner predicate, precedence, objective, parameter or table hash, and postguard, plus the final-era census derivation, coverage table, released experiment registry, and verifier outputs. Provide a claim-by-claim matrix of what is reproducible, independently verifiable, organizer-attested, or irrecoverable.
- **Acceptance criterion**: An external reviewer can rebuild the paper assets and reproduce every released aggregate and deterministic policy check from one documented command sequence; irreproducible private joins are explicitly scoped rather than implied verifiable.

### REV-4: Close or further narrow the clone-study analysis contract

- **Sources**: R1 W2; DA audit Major.
- **Requirement**: Document the exact assignment encoding and bit, pre-action eligibility, arm and stratum flow, owner firing, returned-action change, strict versus composite joins, match uniqueness, outcome definition, target stratum weights, both looks, stopping and promotion rule, and dependence or interference limitations. Release privacy-preserving commitments or receipts where possible. Otherwise call the estimate only a descriptive hash-assigned comparison and remove “ITT.”
- **Acceptance criterion**: Every analyzed row has an auditable inclusion path, or the causal label is narrowed to match the released evidence.

### REV-5: Make the behavior analysis cohort-complete or explicitly forensic

- **Sources**: R3 W2/W3; DA behavior Major; R1 denominator comments.
- **Requirement**: For the complete final 63-game era, report by family and role the owner-level eligible, fired, returned-action-changed, invariant-conforming, semantic-failure, successful-join, and terminal counts. Separately label older pooled profiles, simulations, and replays. For warning parsing, provide a defined denominator and annotation or confusion protocol, or restrict the claim to the 40 counterexamples.
- **Acceptance criterion**: No reader needs to combine simulations, pooled profiles, historical shadows, and the final-era census to infer the scope of an “actual behavior” claim.

### REV-6: Reconcile account, profile, host, opponent, and self-play provenance

- **Sources**: R3 W4; DA profile/account Major.
- **Requirement**: Define participant account, agent profile, host, and opponent account once. Replace ambiguous “four-account” wording if it means four profiles or hosts. State that all author-controlled profiles were within the permitted account, explain suspected slot-label contamination, and document exclusions or sensitivity checks for ambiguous identities. Obtain organizer confirmation if no-self-play enforcement is used as evidence.
- **Acceptance criterion**: Every treatment-bearing profile and field comparison has an unambiguous ownership and clustering description, with no unresolved suggestion of multi-accounting or self-play.

### REV-7: Sharpen the originality and branch-objective map

- **Sources**: EIC W3; R2 W2; R3 W8; DA originality Major.
- **Requirement**: Keep the new strategy-origin and objective-scope paragraphs. Add a compact branch-level map of money, local percentile, agreement, information, and safety objectives and their evidence class. Compare the returned-action audit with the closest execution tracing, agent observability, feature-flag experimentation, competition-agent analysis, and responsible-agent evaluation work. Treat elementary propositions as benchmarks, not novelty claims.
- **Acceptance criterion**: A reviewer can state the paper's scholarly delta without citing leaderboard placement or textbook identities, and every retained owner has a clear objective and evidential status.

## Suggested revisions

- Consolidate elementary bargaining, ZOPA, Boulware, and buyer-break-even identities into a compact benchmark table if appendix length or focus remains a concern.
- Keep Myerson-Satterthwaite separate from elementary ZOPA observability and Rubinstein separate from finite terminal backward induction; the later current source appears to have repaired this.
- Define owner, bank, wire, joined, fired, overlay, and V1/V2/V3 at first use or in a small schematic glossary.
- Label 8/10 terminal-cent closure and the 40 warning cases as selected descriptive or coverage evidence wherever they appear prominently.
- Add only claim-relevant HCI, human-agent trust or deception, traceability, privacy, and responsible-release literature.

## Revision roadmap

The immutable source-traceability checklist is in [revision_roadmap.md](revision_roadmap.md). Its order is source order, not a work ranking.

