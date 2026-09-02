# Peer review working draft: four page core

> Author requested, local pre submission critique. This is not an official venue review or an editorial decision. It covers only pages 1 through 4 of `paper/main_core.pdf`. References, appendix, checklist, logs, code, and prior reviews were not used to rescue claims that are incomplete in the core.

# Comments to authors

## Overall assessment

The core is a strong competition system report with unusually careful causal language, real external validation, explicit negative results, and a clean required Agent Behavior Analysis section. It is not yet at Best Competition Paper level. The central gap is simple: the title and motivation promise rank aware strategic design, but the audited final policy is evaluated mainly through action counts and agreement outcomes, not same cell percentiles or rating increments. The paper therefore establishes that an adaptive account was competitive and that a final policy was traceable, but it does not yet show that the described rank aware choices explain, or even coincide with, strong final window rank performance.

Current author side scores:

| Dimension | Score | Reason |
|---|---:|---|
| Quality | 3/4 | Careful and technically serious, but the key strategy to performance link is missing. |
| Clarity | 2/4 | Clean rendering, but dense internal vocabulary and mixed evidence populations obscure the story. |
| Significance | 3/4 | Second place and tens of thousands of live games are substantial external validation. |
| Originality | 2/4 | The audit is distinctive, but the policy architecture is not yet differentiated clearly from familiar rule routing and negotiation heuristics. |
| Reviewer confidence | 4/5 | High on manuscript logic, game theory, statistics, and presentation; no independent reproduction was attempted. |

## Evidence bounded summary

The paper describes a deterministic agent that made no runtime LLM calls in two audited final era windows. It routed observable game states through priority ordered policy modules, game theoretic benchmarks, empirical rank proxies, validity checks, and legal fallbacks. The associated competition account finished second in the agent track and third on the combined leaderboard, with a displayed rating of 2590.02 after 46,564 rated game increments. The core separately audits 245 locally joined games and 2,288 returned actions from two final era windows, reports behavior by family, and presents failures and limits on causal attribution.

## Strengths

- The official result is prominent and provides external validation that most system papers cannot claim.
- The abstract is self contained at about 190 words. It defines GLEE, gives the method, reports the result, names the audit population, and states a bounded conclusion.
- The paper repeatedly distinguishes descriptive evidence from treatment effects. This restraint is a major strength.
- The theory sections state their assumptions and correctly label synthetic horizons, pooled rank models, and cheap talk adaptations as heuristics rather than equilibria.
- Negative evidence is retained: no deals, walks, a timeout, rating reversals, missed warnings, seller credibility failure, and an abandoned positive interpretation.
- The required Agent Behavior Analysis is visibly present and includes exact family, role, game, action, and outcome counts.
- The four pages render cleanly. Tables, equations, and the figure are legible, the figure has a legend, and there are no visible clipping or overflow defects.

## Major comments

### Major comment M1

- Location: Abstract; Section 1; Table 2; Section 4.
- Observation: The paper argues that expected payoff and expected percentile can favor different actions, but the final policy census reports agreements, action types, and completion outcomes rather than achieved same cell percentiles or rating increments.
- Evidence or criterion: A 171 of 171 bargaining agreement rate can still be poor under the paper's own objective if the accepted splits rank near the field median. The same issue applies to negotiation agreement counts and persuasion BUY or PASS counts.
- Why it matters: The second place endpoint shows competitiveness of the evolving account. It does not show that the audited final policy was successful because it was rank aware.
- Requested action: Report a compact final window outcome summary by family and role, preferably game level mean or median raw percentile, zero rate, and rating increment with uncertainty. If official adjusted increments are unavailable, label raw percentile as a proxy. If neither can be defended, narrow the title and contribution to an adaptive competition system and action audit.

### Major comment M2

- Location: Abstract lines 8 through 10; Section 3 opening; Table 3; conclusion.
- Observation: The displayed rating and 46,564 increments belong to an adaptive lifetime, while the behavior analysis covers 245 games in two final era windows. The windows are called bounded but their dates, revision boundaries, inclusion rule, and reason for selection are not given.
- Evidence or criterion: The negotiation behavior claim rests on only 19 final window games, whereas the final negotiation rating reflects 15,415 lifetime increments.
- Why it matters: A reviewer can easily misread the lifetime rating as evaluation of the frozen policy described in Section 2.
- Requested action: Add one explicit evidence hierarchy: official lifetime result for competitiveness; complete final window census for behavior; selected retrospective diagnostics for failure localization. Define both final windows in one sentence and replace “validate the assembled system” with “demonstrate competitive performance of the adaptive system.”

### Major comment M3

- Location: Section 3, especially lines 101 through 111.
- Observation: “Agreement oriented,” “allowed trade and walk outcomes,” and “mixed positive and negative messages” are too broad to establish that the central designed branches executed as intended. Exact agreement between flat and nested returned action records validates logging consistency. It does not establish branch level policy conformance. The core also reports `plan.component` for only 220 of 2,288 actions.
- Evidence or criterion: The competition requirement asks what the agent actually did, whether it matched the design, and how that alignment was ensured.
- Why it matters: This is the required section and likely the most important award criterion specific to the track.
- Requested action: Replace the broad matching sentence and internal inventory counts with a compact table containing, for each central branch: intended behavior, eligible games or actions, fired count, action changed count, observed outcome, mismatch, and audit limitation. Quantify the unauditable remainder. Move the 81 key and 23 file inventory details out of the core.

### Major comment M4

- Location: Section 1 Equation 1; Section 2 state definition; bargaining Equation 2.
- Observation: First, `eta_g` is not defined. Second, `g` denotes game count in the rating equations but game family in the visible state tuple. Third, `s` denotes the complete visible state and later the seller value in negotiation. Fourth, Equation 2 calls `b_r` a share but compares it with `(M - .01)`, an amount in pot units.
- Evidence or criterion: Mathematical notation must preserve meaning and units across the four page core.
- Why it matters: The underlying bargaining threshold may be correct, but the current definition is dimensionally ambiguous and the symbol collisions make the method harder to verify.
- Requested action: Define the rating step size and cite the exact official rule; use `n` for game count and `f` for family; use `v_s` and `v_b` for seller and buyer values; define `B_r` as Bob's absolute allocation or normalize the right side of Equation 2 by `M`.

### Major comment M5

- Location: Section 4, lines 128 through 131.
- Observation: The paper reports an exact contrast of `-0.06628` and immediately says the full derived artifact was not preserved.
- Evidence or criterion: A precise empirical result must have an auditable evidence object, particularly in a paper that presents reproducibility and action auditing as contributions.
- Why it matters: This single sentence undermines confidence in the otherwise careful evidence discipline.
- Requested action: Regenerate, preserve, and expose the derivation before retaining the number. Otherwise remove the result from the core. Similar but lesser issues apply to the 14 of 14 trigger statistic and 8 of 664 seller statistic, which need eligible and game level denominators plus uncertainty.

### Major comment M6

- Location: End of Section 1; Section 2; Table 3.
- Observation: Priority routing, bargaining recursion, Boulware concession, persuasion obedience bounds, and legal fallbacks are familiar ingredients. The paper does not clearly say what is new about their combination or how this agent differs from other GLEE entries.
- Evidence or criterion: The official second place result establishes significance, but not originality.
- Why it matters: Without sharper positioning, a reviewer may see a strong implementation of known heuristics rather than a research contribution.
- Requested action: State three precise contributions: decision design under rank based evaluation, traceable priority routing across heterogeneous economic games, and a complete bounded action audit with negative results. Add the number of eligible agent entries and gap to first place if officially available. Briefly contrast the method with payoff optimizing or runtime LLM agents without naming competitors unless evidence is public and appropriate.

### Major comment M7

- Location: Figure 1 and lines 113 through 119.
- Observation: The plot connects selected checkpoints even though horizontal spacing is ordinal, omits the overall rating series discussed in the text, and does not state how checkpoints were selected. Its close annotation visually points most strongly to bargaining although all families have final values.
- Evidence or criterion: A four page paper should devote visual space to evidence that answers its central question.
- Why it matters: The figure demonstrates volatility but does not connect the final policy to rank performance or alignment.
- Requested action: Do not add another figure. Replace this plot with either a complete and correctly timed trajectory with intervention markers, or preferably one compact table that combines final window rank performance and branch level design alignment.

### Major comment M8

- Location: Reproducibility and conclusion paragraph.
- Observation: The core promises a future sanitized production equivalent release but gives no artifact link, release condition, license, or exact reproducibility boundary. It also says human data review remains unresolved.
- Evidence or criterion: NeurIPS requires authors to remain responsible for data governance and encourages concrete code and data access paths. GLEE mixed agents and humans in the competition pool.
- Why it matters: An unresolved human data statement can become an ethics concern, and a planned release cannot support review of current reproducibility.
- Requested action: Resolve the organizer data use question before submission. State exactly which data enter the paper, whether messages or identities are analyzed, what is excluded, and what the sanitized artifact reproduces. Provide an artifact location if the track permits it.

## Minor comments

1. “LLM off” is less clear than “without runtime LLM calls.”
2. “Structural owner,” “postguard,” “wire action,” “current stack subset,” “activity defense window,” and “frozen stricter selector” read like internal engineering vocabulary. Define or replace them with ordinary terms.
3. In Table 1, write `delta_2 = .95` rather than `delta = .95` for consistency with the bargaining paragraph.
4. Define seller value and buyer value before writing `s < p < b`.
5. Explain why every source field is labeled `heuristic` even though the paper distinguishes structural, theoretical, empirical, and guard components.
6. The title promises a general design method, but the paper is a single agent case study. Either narrow the title or make the general design principles explicit.
7. The unhyphenated compound modifiers in the title are grammatically awkward beside “Language-based” in the abstract. If punctuation is intentionally excluded, recast rather than simply deleting punctuation. One option is “Strategic Policy Design for Ranking Objectives in GLEE.”
8. “Result, failures, and lessons” should be “Competition Result and Failure Analysis” or “Results, Failures, and Lessons.”
9. The conclusion is too short. End with the specific transferable lesson: rank based objectives changed which deals were attractive, priority routing made a heterogeneous policy deployable, and action auditing exposed failures that the final rating concealed.
10. Replace placeholder author metadata before submission and verify the track's single blind formatting requirement.

## Structured audit summary

The local claim evidence matrix covered 14 central claims. Three were supported within the four page core, nine were partly supported, one was unsupported because its derivation was not preserved, and one was a future release plan that could not yet be assessed. This is a claim alignment audit, not verification that the underlying data are true.

The statistics and reproducibility checklist contained 22 items: one verified present, 15 partly documented, three missing, and three not applicable. The main gaps were window selection, game level denominators, uncertainty, artifact availability, and human data governance. Reporting gaps are not themselves a paper score.

## Best revision sequence within four pages

1. Replace Figure 1 and the unauditable replay paragraph with one final window performance and conformance table.
2. Define the lifetime and final window evidence populations, including exact window boundaries.
3. Rebuild Agent Behavior Analysis around intended behavior, observed behavior, mismatch, and audit coverage for each central branch.
4. Fix the notation and dimensional ambiguity, then remove internal implementation language.
5. Rewrite the contribution paragraph, abstract ending, and conclusion around three precise contributions and three lessons.
6. Resolve the artifact and human data statement before final submission.

## Review limitations and disclosure

This assessment used only the rendered four page core and its corresponding core source for location checking. The appendix, references beyond citation resolution, checklist, logs, code, evidence dossier, prior reviews, and independent reproduction were outside scope. The PDF was processed locally. Public venue pages were consulted only for policy and track requirements; no manuscript text was sent to an external service. The author remains responsible for verifying every claim, calculation, citation, and policy interpretation.

# Confidential comments to editor

No editor channel exists for this author requested pre submission review. No conflicts were identified. The review used local AI assistance under the author's direction, and the manuscript remained in the shared local workspace. No integrity allegation or separate process concern is raised here.
