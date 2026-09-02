# Theory, economics, and code-alignment peer-review working draft

> Author-requested developmental review of the four-page core only. This is not an independent official review, does not cover any material after `main.tex:340`, and makes no editorial decision.

## Intake record

- Reviewer capacity: author-authorized local developmental reviewer
- Review scope: `paper/main.tex:42-340` and pages 1-4 of `paper/main_core.pdf`
- Competence focus: game theory, mechanism claims, economic objective, mathematical notation, assumptions, and consistency with Agent 5 code and frozen local aggregates
- Processing boundary: local repository only; no network, external service, appendix, supplement, checklist, or confidential replay text used in the assessment
- Verification performed: the supplied theory verifier passed all five groups; the derived-table verifier passed all four groups; the deidentified clone analyzer reproduced the reported 91-game arithmetic

# Comments to authors

## Evidence-bounded summary and verdict

The four-page core is mathematically much stronger than its earlier framing suggests. I found no critical error in the rating algebra, the finite bargaining recursion, the silent-Bob commitment inequality, the 24-cell hidden-seller rank proxy, or the persuasion obedience threshold. Those constructions match the implementation and the stated support grid. The final outcome table now reports official rating increments and zero rates, so the core no longer evaluates the closing policy only through agreement counts.

The remaining risk is interpretation rather than algebra. The title is defensible only if "rank aware" denotes the objective and a scoped subset of owners, not a claim that every final family policy directly optimized official percentile or that rank-aware components caused second place. The paper mostly observes this distinction, but it does not yet make it explicit enough. The other serious issues are that a hidden seller offer is called a reservation bound without stating the individual-rationality assumption, wire-level replay agreement is treated as design alignment, and the exact LLM conversion percentages have no reconstructable evidence object in the local record. No additional theory figure is needed. The current lifecycle figure earns its space; the fixes below are better made through sharper text and one compact policy annotation.

## Claim-status ledger

| Status | Core claims |
|---|---|
| Correct and defensible | Normal-game scoring map and conditional one-step objective; finite empirical rank reversal; terminal-offer raw-rank expression; finite bargaining recursion; silent-Bob floor; 24-cell hidden-seller proxy as a pooled heuristic; persuasion threshold as a commitment benchmark; final counts, official deltas, and the 85-game negotiation diagnostic |
| Incompletely reported | Scope of "rank aware" across final owners; behavioral assumption behind hidden seller bounds; distinction between wire conformance and owner conformance; backload assignment and estimand details; assumptions behind the displayed benchmark equations and bootstrap intervals |
| Unsupported in the retained local evidence | Exact 46.3% versus 55.3% LLM/template conversion comparison |
| Incorrect or misleading terminology | Calling the inferred hidden-seller cost ceiling a reservation bound without naming the individual-rationality condition; calling the candidate multiplier `\pi` a "scale"; calling `s<p<b` the trade interval without saying it is the strict positive-surplus interior |

## Strengths

- The objective section is unusually disciplined. Equation 1 matches the documented normal-game update, explicitly conditions the equivalence result on a fixed reference pool and adjustment, positive learning rate, and inactive clipping, and does not pretend to know the official opponent adjustment.
- The payoff-versus-rank example is exact under the implemented empirical midrank convention. The terminal objective also correctly retains `Q(0)` instead of treating rejection as a neutral zero.
- The bargaining math is code-faithful. `glee_agent/strategies/bargaining.py:60-80` implements the displayed recursion, and `glee_agent/bargaining_p2_commitment.py` implements the six-share schedule and Equation 2.
- Equation 3 is not decorative theory. `paper/analysis/verify_theory_code.py:355-425` checks the same four buyer multipliers, two message modes, three monetary bases, and the exact banked asks selected by `glee_agent/first_principles.py`.
- The persuasion threshold is algebraically correct for the one-shot committed benchmark, and the paper immediately states that the repeated noncommitted game violates the commitment assumption.
- The paper does not assign causal credit to the final placement. Figure 1 also labels operational boundaries as descriptive rather than treatment effects.
- The final-policy table reports the evidence object reviewers need most: official per-game rating changes with uncertainty, zero rates, role counts, and explicit disclosure of the absent close-window negotiation sample.

## Title assessment

Qualified yes. The title's rank-aware claim is earned as a design descriptor because the paper derives the percentile objective, implements a Bob expected-percentile search, implements a hidden one-round seller seed-rank proxy, and evaluates the final windows with official rating increments. It is not earned as an all-family optimizer or causal performance explanation. The final manifest has `BARG_BOB_OFFER=1`, but the explicit negotiation and persuasion rank flags are off; negotiation mixes a rank-derived one-round seller rule with structural and copied-leader rules, while persuasion is driven mainly by monetary obedience, posterior credibility, and safety vetoes. The final audit does not link a rank-aware owner's firing to its realized rating increment. The title can remain if the core defines this limited meaning once and makes the owner scope visible in Table 1.

## Major comments

### Major comment M1

- Location: Title; Abstract, lines 57-69; Section 1, lines 84-113; Table 1; conclusion, lines 336-339.
- Observation: **Incompletely reported.** The paper contains genuine rank-aware design, but it currently allows a broader reading in which the final system across all three families optimizes rank. Code and manifest evidence show a narrower system: bargaining's Bob search uses a rank proxy, hidden one-round negotiation has a seed-rank construction, but many retained owners optimize equilibrium continuation, money, support consistency, imitation, credibility, or legal safety. The explicit negotiation rank-hybrid/rank-price flags and persuasion rank-buy/rank-gate flags were off. Aggregate family rating increments do not identify which owner generated them.
- Evidence or criterion: `glee_agent/barg_offer.py:113-200` is a coarsened expected-percentile floor; `glee_agent/first_principles.py:280-399` contains the hidden-seller rank proxy; `paper/data/submitted_agent_bank_manifest.csv` records the final flags; `paper/data/final_window_outcome_summary.csv` reports family outcomes but no component-level estimand. A design title must match the implemented scope and must not imply component efficacy that the paper explicitly says is unidentified.
- Why it matters: This is the paper's central promise. Without a scope definition, a reader can reasonably infer that rank optimization is the common policy principle across all owners and that the second-place endpoint validates it. The paper proves neither claim, even though it does support the more interesting and defensible claim that rank awareness changed selected decisions within an adaptive multi-owner system.
- Requested action: Define "rank aware" as an objective and scoped design principle, then mark in Table 1 which retained owners directly use a rank proxy and which are theory, payoff, behavioral, or safety owners. State in the abstract or conclusion that the title does not mean every action optimized an official cell percentile. No new figure is necessary.

### Major comment M2

- Location: Theory-guided owners, lines 144-147; Table 1 negotiation row, line 179.
- Observation: **Conceptually misleading unless qualified.** The phrase "hidden offers supplied only conditional reservation bounds" does not state the condition and uses the wrong economic object. The implementation infers an upper bound on hidden seller cost from the lowest observed seller ask. That implication holds only if a binding seller offer is individually rational, so the seller never offers below cost. It does not generally identify the seller's dynamic reservation price or continuation value.
- Evidence or criterion: `glee_agent/nego_hidden_terminal_inference.py:1-18` states the omitted assumption explicitly: an individually rational seller with cost `c` does not offer below `c`. Lines 109-138 then take the lowest ask and choose the greatest support cost no larger than it. In a dynamic bargaining game, a reservation price can include continuation value and beliefs, so "cost ceiling under an IR support assumption" is the accurate description. The cited incomplete-information bargaining papers establish limitations, not this behavioral inference.
- Why it matters: The current wording makes a heuristic behavioral assumption sound like an implication of incomplete-information theory. Language agents can make dominated, deceptive, mistaken, or intentionally loss-making offers, precisely the setting in which an observed ask ceases to bound type. This also affects how readers interpret the zero-fire terminal-inference branch.
- Requested action: Replace "reservation bounds" with "support-consistent upper bounds on seller cost under the assumption that binding seller offers are individually rational." State that the branch fails through to another owner when no such bound exists and that the assumption is behavioral, not a theorem of incomplete-information bargaining.

### Major comment M3

- Location: Agent Behavior Analysis, lines 261-285, especially "The behavior largely matched design" at line 264.
- Observation: **Incompletely supported.** The audit establishes excellent wire conformance, not comprehensive policy-design alignment. Matching 2,288 normalized local returned actions to 2,288 valid replay moves proves that the server received the same legal actions the local system returned. Agreement in every bargaining game and the use of both action types in other families are surface outcome or support checks. They do not show that the intended owner fired, that its thresholds were satisfied, or that its candidate survived postguards as designed. The paper itself reports component labels for only 220 actions and gate traces for 1,207.
- Evidence or criterion: `paper/data/final_window_official_export_manifest.csv` supports the 2,288 wire matches. The core's own lines 282-285 disclose sparse owner traces. A behavioral-alignment claim needs a stated design contract and evidence at the same level: transmission conformance, legality, action-distribution conformance, owner selection, and threshold/action conformance are distinct tests.
- Why it matters: Agent Behavior Analysis is a required contribution, and the paper presents traceability as a key strength. Conflating execution receipt with strategic conformance weakens that strength and makes "largely matched" non-falsifiable. It also blurs the role of numeric postguards, which can legally alter an owner's candidate.
- Requested action: Split the claim into three explicit levels: 2,288/2,288 wire conformance; surface behavior and outcome checks by family; and owner or gate auditability limited to the corresponding trace-covered actions. Either remove "largely matched design" or define a short, pre-specified set of invariants and report pass counts for each. Keep the unverified remainder explicit and do not treat a gate trace alone as proof of owner conformance.

### Major comment M4

- Location: Agent design, lines 127-129; Results, lines 315-318.
- Observation: **Unsupported in the retained local evidence.** The directional claim that generated wording was removed after underperforming templates is repeated in operational ledgers, but the exact 46.3% versus 55.3% comparison has no frozen denominator, row-level aggregate, allocation definition, model/provider/version, prompt procedure, time window, uncertainty, or reconstructable analysis artifact located in the local evidence used for this review.
- Evidence or criterion: The exact values appear in `.ai/FINDINGS.md:166`, `.ai/HANDOFF.md`, and source comments, but those are repeated assertions rather than independent evidence objects. A precise comparative result requires at minimum numerator/denominator by condition, unit of analysis, assignment or exposure rule, and enough provenance to distinguish a randomized comparison from a temporally confounded deployment comparison.
- Why it matters: This is the only exact numerical result in the core that cannot be audited from a bounded artifact. It conflicts with the paper's otherwise strong claim-evidence discipline and invites reviewers to question whether other negative results are also ledger-only.
- Requested action: Either remove the exact percentages and retain only the bounded historical statement that LLM wording was tried and retired, or add a frozen aggregate with counts, window, assignment/exposure definition, model and prompt provenance, uncertainty, and causal status. Do not call the comparison causal unless assignment integrity can be reconstructed.

### Major comment M5

- Location: Section 1, line 113; Results, lines 312-318, especially the backload result.
- Observation: **Incompletely reported.** The 91-game clone is described carefully as a stopped randomized comparison with an interval crossing zero. The backload sentence is much stronger: "lost by .391 raw-percentile points" reads as a causal effect, but the core gives no arm counts, analysis unit, assignment rule, interval, stopping rule, or statement that all assigned games rather than realized policy behavior defined the comparison. The local diary specifically records that an earlier analysis grouped on realized `q` rather than assigned arm before the assignment was recovered.
- Evidence or criterion: `DIARY.md:251-253` records the 0.391 estimate, interval `[0.326,0.455]`, and the realized-behavior grouping failure. Randomized intent-to-treat analysis requires recovery by assigned arm, inclusion of all assignments under the stated estimand, and qualification for repeated looks or interference. The sentence "only randomized comparisons receive causal language" is a defensible necessary gate, but randomization alone is not the entire identification argument.
- Why it matters: The backload estimate is one of the largest numerical effects in the core and supports a claimed reversal. Without the corrected assignment provenance and denominators, a reader cannot tell whether 0.391 is a valid ITT contrast, an as-treated contrast, or a selected-cell post hoc result.
- Requested action: Report the candidate/control game counts, game-level assignment function, strict profitable-cell inclusion rule, corrected ITT definition, interval, and whether the read was fixed or repeated. If those details cannot fit or be reconstructed, narrow the main-text statement to "a randomized backload test favored all-push and the arm was retired" without the exact magnitude.

## Minor comments

### Minor comment m1

- Location: Theory-guided owners, line 144.
- Observation: **Terminologically imprecise.** `s<p<b` is the strict positive-surplus interior, not the entire individually rational trade set. Weak individual rationality permits `s\leq p\leq b`, and feasible trade exists when `s\leq b`. The symbol `s` also collides with the state symbol defined at line 122.
- Evidence or criterion: In bilateral trade, seller utility is `p-s` and buyer utility is `b-p`; strict inequalities give both agents strictly positive surplus, while weak inequalities allow indifference.
- Why it matters: The current wording can be read as excluding valid boundary trades and makes later one-cent boundary policies look theoretically required rather than tie-breaking or empirical choices.
- Requested action: Call it the "strict positive-surplus interval" and use distinct symbols such as `v_S<p<v_B`.

### Minor comment m2

- Location: Equation 3 and surrounding text, lines 148-157.
- Observation: **Incorrect terminology and incomplete notation.** `\pi` is called a "supported scale," but the implementation treats it as an ask multiplier or support point; `B` is the monetary scale. The roles of `\sigma`, `\beta`, `m`, `B`, `S`, and the equal weighting are not defined locally.
- Evidence or criterion: `paper/analysis/verify_theory_code.py:355-399` defines seller-cost multiplier, candidate ask multiplier, buyer-value multiplier, message mode, and three monetary bases. The factor `1/24` is an equal-weight prior over `4 x 2 x 3` cells.
- Why it matters: Readers cannot reconstruct the expression without reverse engineering the notation, and "scale" currently names two different quantities.
- Requested action: Rename `\pi` an ask multiplier and define every summation index plus `S` in one sentence. State that the 24 cells receive equal heuristic weight.

### Minor comment m3

- Location: Persuasion benchmark, lines 158-164.
- Observation: **Defensible but incompletely stated.** The displayed threshold is correct under `u<P<v`, a committed sender who recommends every HIGH item and independently recommends a fraction `q` of LOW items, and a Bayesian buyer who buys when posterior expected value weakly exceeds price. The core defines none of `p,v,u,P` immediately around the formula.
- Evidence or criterion: Bayes' rule gives posterior purchase value `[pv+(1-p)qu]/[p+(1-p)q]`; imposing it at least `P` yields the displayed threshold. `sim/grid.py` and the implementation satisfy `u=0<P<v` on the GLEE support.
- Why it matters: Without the assumptions, clipping can conceal corner cases and the formula can look like a repeated-game solution despite the next sentence's commitment caveat.
- Requested action: Add a compact symbol definition and explicitly call it a one-shot obedience ceiling, not a repeated-game equilibrium.

### Minor comment m4

- Location: Bargaining benchmark, lines 131-136.
- Observation: **Defensible with omitted benchmark assumptions.** The recursion is exact for a divisible unit surplus, common knowledge, zero disagreement payoffs, alternating offers, and acceptance at indifference. GLEE uses currency rounding and empirical agents need not accept a zero or indifferent share. Rubinstein 1982 is primarily the infinite-horizon benchmark, while the displayed formula is finite backward induction.
- Evidence or criterion: The code computes the recursion exactly and then combines it with empirical floors and clocks, so the manuscript already treats it as a benchmark rather than a complete behavioral model.
- Why it matters: Calling the owner "exact game-theoretic" without the tie-breaking and divisibility qualifications can overstate its status in the implemented game.
- Requested action: Add "divisible-pot, zero-disagreement benchmark with acceptance at indifference" or equivalent, and retain the current statement that empirical floors modify it.

### Minor comment m5

- Location: Lines 135-136; Table 1 bargaining row; title assessment.
- Observation: **Defensible but easy to overread.** The Bob offer search is rank-aware, yet its CDF key includes money, cap, horizon visibility, and information visibility, omitting role, discounts, message mode, and potentially falling back to a pooled CDF. It is also shipped as a floor on the baseline ask, not as the sole offer policy.
- Evidence or criterion: `glee_agent/barg_offer.py:113-139` defines the coarsened key and pooled fallback; lines 158-200 optimize its diagnostic expected percentile; the module header and caller document floor semantics. Official scoring uses the full same-configuration, same-role cell.
- Why it matters: "Rank-aware Bob offer search" is true, while "official-cell rank optimizer" would be false. The difference is central to the title.
- Requested action: Retain "coarsened" wherever the component is named and call its output a diagnostic rank proxy or offer floor, not an official percentile optimum.

### Minor comment m6

- Location: Table 2 caption and rows, lines 221-248.
- Observation: **Incompletely reported uncertainty.** The intervals are correctly labeled descriptive, but a game bootstrap implicitly resamples games as exchangeable while the window contains repeated opponents, heterogeneous roles/configurations, irregular exposure, changing ratings, and reference-pool drift. The negotiation interval has only 19 games.
- Evidence or criterion: Bootstrap percentile intervals do not obtain ordinary coverage from arbitrary dependent, nonstationary observations. The manuscript already avoids an inferential treatment-effect claim, which substantially reduces the problem.
- Why it matters: Readers may still read "95%" as a confidence guarantee, especially because the bargaining interval excludes zero.
- Requested action: Call them "descriptive game-resampling intervals" and state that they do not account for temporal, opponent, or configuration dependence. Do not use interval exclusion as evidence of a component effect.

### Minor comment m7

- Location: Agent Behavior Analysis, lines 264-270; Table 2.
- Observation: **Defensible but sample-limited.** The role means are useful diagnostics, but negotiation seller/buyer means use 10 and 9 games, and the final two-window audit has no negotiation games in the closing run. Persuasion includes one timeout and only 54 rated games.
- Evidence or criterion: `paper/data/final_policy_two_window_census.csv` and `paper/data/final_window_outcome_summary.csv` provide these denominators.
- Why it matters: The means should not be interpreted as stable role rankings or evidence that the structural router fixed or failed a role.
- Requested action: Keep the role means but attach the role sample sizes in prose or make explicit that they are window-specific diagnostics.

### Minor comment m8

- Location: Results, lines 299-306.
- Observation: **Defensible observational motivation.** The three leading-profile opening ratios and the focal agent's 0.681 opening are presented as motivation, not proof, and the text acknowledges field drift and agreement-conditioned samples. However, "three then-leading profiles" is a selected comparison and `1.05` of visible surplus needs a clear definition of the normalization and eligible cell set.
- Evidence or criterion: Competitor selection, time of observation, role, information regime, and normalization determine whether opening ratios are comparable.
- Why it matters: The observation is strategically interesting, but without the denominator definition it can look like a general field statistic.
- Requested action: Define visible-surplus normalization and label the three profiles as a purposive, time-stamped sample. Retain the current noncausal language.

### Minor comment m9

- Location: Figure 1, lines 185-200, and pages 2-3 of the rendered core.
- Observation: **Defensible and visually clear.** The lifecycle figure has readable family labels, axes, event markers, and a caption that explicitly denies isolated treatment effects. It materially supports the adaptive-system claim. A second conceptual or architecture figure would duplicate Table 1 and consume evidence space.
- Evidence or criterion: A figure should reveal a relationship that prose or a compact table cannot. Here the nonmonotone family trajectories and timing boundaries satisfy that criterion; an owner-flow diagram would not add outcome evidence.
- Why it matters: Additional visuals would likely force removal of denominators or assumptions that the theory currently needs more urgently.
- Requested action: Keep Figure 1 as the sole core figure. If space is reallocated, improve Table 1 with a rank-proxy versus theory/behavior/safety annotation rather than adding another image.

## Methods, statistics, and reproducibility

The local mathematical verifier reports passes for all five groups: objective algebra and rank reversal, bargaining recursion and parity, banked P2 owner, negotiation structural owners, and persuasion threshold/posterior/seller policy. The derived-data verifier separately confirms 46,316 local assignments, the 245-game two-window audit, 244 rated games plus one timeout, 2,288 own actions, and zero logged action errors. The deidentified clone analyzer reproduces candidate `n=44`, control `n=47`, difference `+0.869101`, normal interval `[-0.730366,2.468567]`, profile-standardized difference `+0.990780`, and a `+6.141` percentage-point no-deal difference.

These checks support arithmetic and code correspondence, not causal interpretation. The final rating increments are direct official outcomes, but their game-bootstrap intervals are descriptive. The 91-game clone point estimate is also not a promotion-grade effect because its interval crosses zero, it was examined repeatedly, and profile interference or common-pool effects remain possible. The paper handles most of this correctly. The backload and LLM wording comparisons are the exceptions requiring stronger evidence descriptions.

## Ethics, transparency, figures, tables, and citations

No integrity concern was found. The core is candid about failed strategies, incomplete owner traces, nonstationarity, private replay constraints, and absence of causal component credit. No private transcript content needs to be added to resolve any comment above; counts, hashes, assignment definitions, and deidentified aggregates are sufficient.

The theory citations are directionally appropriate, but citations should not carry assumptions the paper itself omits. In particular, incomplete-information bargaining references do not prove that a language agent's offer is individually rational, and the persuasion citation does not convert the repeated noncommitted game into a commitment model. The prose already acknowledges the persuasion limitation and should do the same for hidden seller inference.

The PDF's first four pages are visually coherent. Equations, Table 1, Table 2, and Figure 1 are readable at normal zoom, with no clipping or missing legend. The tables are dense but justified by the four-page limit. There is no evidence-based reason to add another figure.

## Prioritized revision order

1. Scope the title and define exactly which final owners are rank-aware.
2. Correct the hidden cost-bound assumption and terminology.
3. Separate wire conformance from owner and threshold conformance.
4. Remove or reconstruct the exact LLM conversion comparison.
5. Supply corrected ITT provenance and denominators for the backload result, or narrow it.
6. Clean up the local notation and benchmark assumptions in the three theory paragraphs.

## Limitations of this review

This review is intentionally restricted to the main four pages and local evidence objects. It does not assess the material after `main.tex:340`, submission compliance outside the visible core, external literature beyond the manuscript's use of it, or the official opponent-adjustment algorithm, which is undocumented. Raw private replays were not reprinted or independently released. The review verifies correspondence to the current frozen assets and supplied local analyzers, not that every historical process loaded a particular commit on every turn. No editorial outcome is offered.

# Confidential comments to editor

No editor-only channel was supplied for this author-requested developmental review. There are no separate integrity or process concerns to report, and no editorial decision is offered.

## Reviewer disclosures

- Conflicts and editor clearance: This is an author-authorized local review, not an assigned independent review. No external editor clearance was requested.
- Competence limits or specialist review needed: A competition organizer would be needed to verify the undocumented opponent adjustment and any official-data-use constraints.
- Assistance or tools used and required disclosure: Local PDF rendering, deterministic repository verifiers, a structured claim-evidence matrix, and direct source/aggregate inspection were used. No network or external model service was used.
- Confidentiality or retention issue: Review artifacts remain in the local repository workspace. No private replay text is reproduced in this report.

## Editorial-process or integrity concerns

None identified.
