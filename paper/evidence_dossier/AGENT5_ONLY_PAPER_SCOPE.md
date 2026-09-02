# Agent 5 Only Paper Scope

Status: binding internal editorial plan, not manuscript prose, not approved for
public release

Evidence cutoff: 2026-08-30

Update, 2026-08-31: the authenticated dashboard export in
`OFFICIAL_FINAL_WINDOW_EXPORT.md` supersedes this file wherever it says that
server receipt or official final-window rating deltas were unavailable. It
establishes exact valid replay receipt for 2,288 of 2,288 returned actions and
adds official displayed rating-change aggregates. It does not resolve selected
owner, pre-coercion action, process provenance, or component causality.

## Binding decision

The paper is about Agent 5. Agent 5 is the sole system being described,
evaluated, and interpreted. The other four profiles are not co-equal systems,
not additional submissions to compare, and not part of the paper's central
claim.

Other profiles may enter only as development apparatus when one of their tests
directly explains why a component was copied into Agent 5, withheld from Agent
5, or rejected before it could enter Agent 5. Even then, the paper should report
the candidate rule, evidence, and decision rather than narrating the other
profile's full strategy, rating history, or identity.

The broader files in this directory remain a private evidence warehouse. They
are intentionally more expansive than the intended manuscript. This file
controls which facts may be promoted into the four-page paper and appendix.

## Naming and result discipline

The user-facing name is **Agent 5**. Internal labels such as `composite` for the
execution slot and `hardliner` for a policy wrapper are provenance fields, not
alternative paper names. They belong in a reproducibility receipt, not the
title, abstract, or main narrative.

The current internal provenance identifies Agent 5 as the participant's
best-performing submitted profile at official close. Before public use, the
artifact must bind the focal public profile identifier to Agent 5. The
post-close snapshot reports:

| Measure | Official value |
|---|---:|
| Agent-track rank | 2 |
| Combined human-agent rank | 3 |
| Overall rating | 2590.02 |
| Rated games | 46,564 |
| Bargaining | 2804.82 over 15,639 games |
| Negotiation | 2620.36 over 15,415 games |
| Persuasion | 2344.87 over 15,510 games |

The manuscript may call Agent 5 our best-performing agent, focal agent, or
runner-up agent. It must not call Agent 5 the competition winner. The last
pre-close snapshot briefly showed first place, but the official post-close
snapshot shows second place in the agent track. "Winning agent" is acceptable
only as an informal internal description meaning our strongest agent, not as a
public result claim.

## Central paper question

How did Agent 5 turn heterogeneous bargaining, negotiation, and persuasion
states into legal economic actions, how did it actually behave in live play,
where did that behavior fail, and what evidence supports each part of the
design?

This question keeps the paper centered on the submitted agent. The development
process matters only when it explains Agent 5's final design or a documented
failure in that design.

## One-sentence contribution

We present Agent 5, a deterministic and LLM-off GLEE agent that routes visible
game states between structural game-theoretic owners, empirically motivated
rank-aware heuristics, and legal fallbacks, and we compare that intended design
with a complete local census of its final live windows while reporting the
failures and evidence limits that remained.

This is the preferred contribution posture. It leads with the agent and its
strategy. Returned-action auditing is supporting methodology, not a second
paper competing for attention.

## What counts as Agent 5 evidence

### Direct evidence

- The official post-close record used for the focal Agent 5 profile, together
  with the still-required public-profile identity binding.
- Agent 5's `logs/composite` assignment, turn, result, and per-game archives.
- The frozen Agent 5 bank manifest, policy asset hashes, final overlay, and
  source-equivalence checks.
- Agent 5 rating checkpoints and bank boundaries.
- The 63-game pre-close Agent 5 census and the 182-assignment closing window.
- The combined 245-assignment, 2,288-action Agent 5 census.
- Agent 5-specific reachability, returned-action, parser, and failure audits.

### Supporting development evidence

Evidence from another profile is admissible only if all four conditions hold:

1. the tested rule was a candidate for Agent 5 or became part of Agent 5;
2. the evidence changed a documented Agent 5 selection decision;
3. the paper states whether the evidence is structural, mechanistic,
   observational, retrospective, simulated, randomized, or operational;
4. the text does not use the other profile's rating as a proxy for Agent 5's
   counterfactual result.

### Excluded evidence

- Full descriptions of Test 1, Test 2, Test 3, or Test 4.
- Cross-profile leaderboard tables or rating trajectories.
- The five-profile topology as a scientific contribution.
- Unrelated experiments that neither entered Agent 5 nor caused an Agent 5
  design decision.
- Competitor catalogs, handles, or profile-by-profile imitation stories.
- The late `The One & Only` profile, which did not produce Agent 5's endpoint.
- A max-of-five or account-selection narrative as the organizing frame.

## Agent 5 as the complete system

Agent 5 is one three-family strategy, not three unrelated specialists. Its
common architecture is an ordered dispatcher. A visible state determines the
game family, role, horizon, information regime, communication regime, and
public history. The highest-priority eligible owner proposes an action. Later
postguards and schema coercion may replace that proposal before the legal action
is returned. This order matters because an enabled-looking lower branch may
never own a turn.

The final Agent 5 configuration was deterministic and LLM-off. A bounded LLM
wording experiment occurred earlier in development and was retired. The safe
claim is therefore that Agent 5's final competition policy was LLM-free, not
that the project never used an LLM.

## Strategy that belongs in the main paper

### Bargaining

The main text should explain the narrow highest-priority owner and the generic
fallback, not every historical flag.

- In the silent Bob, disclosed horizon 12, own discount 0.95 cell, Agent 5 used
  a six-offer commitment ladder. The scheduled Bob shares were 0.61, 0.68,
  0.74, 0.82, 0.91, and a terminal action that left Alice one cent.
- Its acceptance rule compared the standing offer with the discounted value of
  the scheduled continuation.
- Other finite known-horizon states used alternating-offer recursion.
- Public unlimited-horizon states used a synthetic boundary and concession
  clock. They must be called heuristics, not a finite-horizon equilibrium.
- The generic branch also used a coarsened empirical percentile model, integer
  rounding, postguards, legal coercion, and a safe fallback.

The central theoretical distinction is between the exact finite-horizon
benchmark and the heuristic treatment of no-limit games. The paper should not
blur them.

### Negotiation

The main text should show the ordered state decomposition.

- Complete one-round seller, complete cap-10 buyer, and hidden one-round seller
  received explicit structural ownership.
- Complete-information rules used the visible positive-trade interval.
- Hidden-information rules used support restrictions, public offers, finite
  priors, and conditional bounds. They did not observe the hidden opponent
  value and must not be described as knowing the exact ZOPA.
- The hidden one-round seller selected a supported ask from a seed-CDF raw-rank
  proxy averaged over latent buyer types, message modes, and price scales.
- In cap-10 hidden buyer states, observed seller asks could provide a
  conditional upper bound on reservation value when those asks were
  individually rational.
- Remaining buyer cells used scoped observed-behavior paths, while seller cells
  used continuation, stall, endgame, and Boulware-style fallbacks.

The structural support audit found all six complete-information type pairs
feasible and six of 16 hidden type pairs feasible. Overall, 12 of 22 type pairs
admitted trade under the reconstructed support. Per-game hidden feasibility is
not identified from Agent 5's visible state.

### Persuasion

The main text should distinguish the one-shot benchmark from the deployed
repeated-game heuristic.

- The seller used the one-shot obedience calculation as a benchmark.
- When the benchmark permitted all-push, Agent 5 used it. In partial-persuasion
  cases, the bank conservatively avoided claiming an optimal committed scheme.
- When buyer value was hidden, the exact obedience threshold was unavailable
  and a historical buy-rate heuristic was used.
- The buyer path ordered a posterior money gate, a 0.75 tight-cell threshold, a
  0.65 prior fence, a reversible credibility reset, and a final BUY-to-PASS
  explicit-decline veto.

Repeated GLEE communication is noncommitted cheap talk. The safe theoretical
claim is theory-guided routing, not optimal Bayesian persuasion.

## Agent Behavior Analysis

The required section must be an analysis of Agent 5, not a generic audit
framework and not a fleet report.

### Primary behavior population

Use the union of the two complete bounded Agent 5 windows:

| Family | Assignments | Own actions | Returned behavior | Joined outcomes |
|---|---:|---:|---|---|
| Bargaining | 171 | 1,001 | 503 offers, 414 rejects, 84 accepts | 171 agreements |
| Negotiation | 19 | 190 | 10 initial offers, 171 rejects or counters, 7 accepts, 2 own walks | 13 agreements, 3 walks, 3 no-deals |
| Persuasion | 55 | 1,097 | Buyer BUY/PASS 456/201; seller positive/negative 316/124 | 54 completions, 1 timeout |
| Total | 245 | 2,288 | Complete local returned-action census in the declared windows | 244 rated outcomes, 1 timeout |

This population describes behavior. It is selected by operational final-window
boundaries, contains no closing-window negotiation games, and is not a held-out
or representative sample of the 46,564-game lifetime trajectory.

### Designed behavior versus actual behavior

The section should answer four questions for Agent 5:

1. Which owner was designed to control each state class?
2. Which legal action was actually returned?
3. What outcome followed, including zeros, walks, no-deals, and timeouts?
4. What part of that chain is verified, reconstructed, or unavailable?

All 2,288 local action rows contain visible state, plan, returned action,
source, and timestamp, and none contains a logged strategy error. That does not
establish zero errors. The logs do not contain an exhaustive stable selected-
owner field or an independent server receipt. Exact owner-to-return conformance
therefore remains a reconstruction task, not a completed result.

### Agent 5 failings that belong in the paper

- In the August 27 activity-defense window, the same Agent 5 overlay gained
  21.03 bargaining rating points while losing 33.78 in negotiation and 29.42 in
  persuasion, moving overall from about 2592.11 to 2578.05. This is the clearest
  Agent 5-specific seesaw. It is descriptive and does not identify field drift
  or a policy effect.
- In the final 19-game negotiation census, six games did not end in agreement:
  three walks and three no-deals. These outcomes prevent a sanitized story in
  which hard bargaining always succeeded.
- A stricter frozen selector found four persuasion buyer warning turns outside
  the deployed decline layer in one pre-close game. Agent 5 bought on all four,
  and all four revealed LOW quality. This is a concrete alignment miss under
  the selector's definition.
- In an Agent 5 seller localization, after three consecutive passed positive
  recommendations, only 8 of 664 subsequent targeted LOW recommendations sold
  across 109 games. The statistic is action-selected and does not prove that a
  different message would improve rating, but it documents a credibility
  failure mode.
- The final tight-credibility reset was copied into Agent 5 by an explicit
  operator decision before its source experiment reached the planned final
  efficacy read. The paper must report this as a deployment choice, not a
  causally validated promotion.
- A high-share bargaining guard looked enabled but was unreachable under the
  active owner. In the later Agent 5-specific current-stack audit, waiting beat
  accepting the standing offer in 14 of 14 joined triggers by a mean 21.77 pot
  points. This is both a reachability lesson and evidence that the active
  commitment owner already dominated the proposed override in those played
  trajectories.

### Alignment assurance

The paper should describe the actual assurance chain used for Agent 5:

1. log the visible state, plan, returned action, and joined outcome;
2. freeze policy source, overlay values, fitted assets, and window boundaries;
3. test that a branch is eligible, selected, and action-changing before reading
   outcomes;
4. compare flag-off and flag-on returned wires for scoped changes;
5. retain no-deals, walks, zeros, timeouts, and unresolved assignments;
6. separate mechanical conformance from efficacy;
7. state where process-load or server-receipt evidence is absent.

This assurance process supports bounded execution claims about Agent 5. It does
not prove that every lifetime action matched the intended owner or that any one
component caused the final rank.

## Permitted use of other-agent development evidence

Only two categories currently have a strong reason to survive into the paper.

### Component-source disclosure

The credibility-reset controller entered Agent 5 from a development challenger.
The appendix may state the source experiment's sample and incompleteness because
that limitation is necessary to interpret the final Agent 5 component. The main
text does not need the challenger's name, rating, or full strategy.

### Rejection evidence that changed Agent 5

A broad observed-leader buyer clone failed its frozen promotion rule at 91
games, increased no-deals by 6.14 percentage points, and was negative in the
Agent 5 stratum. This can explain why Agent 5 did not adopt a broad imitation
policy. It must not be presented as a comparison among five agents. If space is
tight, place it in the appendix and retain only the design lesson in the core.

### Audit-origin evidence

An unnamed pre-integration challenger exposed a case in which intermediate
policy intent and the final wire action diverged after coercion. It may be used
briefly because it motivated the returned-action assurance later applied to
Agent 5. The other profile's identity, rating, and unrelated strategy remain
out of scope.

Everything else remains in the private archaeology unless a direct Agent 5
decision link is demonstrated.

## Four-page main-paper map

### Page 1: GLEE, result, and design problem

- Define GLEE and its three game families in two or three sentences.
- State Agent 5's official second-place agent-track result in the abstract and
  introduction.
- Explain the percentile-based objective and the zero atom compactly.
- State the single contribution: Agent 5's observable-state routing design,
  live behavior, failures, and bounded action-alignment evidence.
- Give the inspiration in one paragraph: exact structure where available,
  empirical fallbacks where it was not, and hard lessons from misleading live
  statistics.

Do not introduce the five-profile account architecture on this page.

### Page 2: Agent 5 strategy and theory

- Use one compact Agent 5 policy table with columns for family, visible state,
  owner, theoretical basis, returned rule, and fallback.
- Give only the equations needed to understand the percentile objective,
  hidden one-round seller proxy, and persuasion obedience benchmark.
- State assumptions beside the equations.
- Explain owner precedence and final legal coercion in prose or the table.

Do not use a decorative architecture image.

### Page 3: Agent Behavior Analysis

- Use the 245-assignment Agent 5 behavior table.
- Compare intended behavior with returned actions and joined outcomes.
- Report the missing exhaustive owner field and process receipt directly.
- Include the most concrete Agent 5 failures: negotiation non-agreements and
  the four persuasion warning misses.
- If a figure earns the space, use only the Agent 5 family-rating trajectory to
  show seesawing. Label it descriptive and noncausal.

### Page 4: What failed, reproducibility, and conclusion

- Report the Agent 5 activity-defense seesaw and at most two development
  reversals that directly shaped Agent 5.
- Distinguish structural justification, mechanism verification, observational
  evidence, and causal evidence.
- State that no retained component completed a precommitted efficacy-promotion
  rule.
- Give the reproducibility boundary: sanitized Agent 5 policy, policy receipt,
  derived tables, and exact checks, with private messages and controls removed.
- Conclude with what Agent 5 establishes and what it does not establish.

The official result should be stated once in the abstract and once in the main
text. A separate one-row result table is unnecessary if space is tight.

## Appendix map

The appendix should deepen Agent 5, not reintroduce the fleet as a second paper.

1. **GLEE scoring and assumptions**: official formula, fixed-reference
   qualification, tie uncertainty, and payoff-versus-rank example.
2. **Exact Agent 5 policy specification**: ordered owners, visible triggers,
   constants, table hashes, postguards, schema coercion, and fallbacks for all
   three families.
3. **Game-theory derivations**: finite bargaining recursion, hidden negotiation
   support and objective, terminal bounds, and persuasion obedience benchmark.
4. **Agent 5 behavior details**: role, horizon, information, message, action,
   outcome, and failure breakdowns for the 63-game and 245-assignment windows.
5. **Agent 5 alignment audit**: bank receipt, isolated source verifier,
   owner-reconstruction method, conformance results if completed, and all
   unresolved cases.
6. **Agent 5 development lineage**: only components retained by, rejected from,
   or copied into Agent 5, each with evidence class and decision status.
7. **Negative results and reversals**: Agent 5-specific seesaw, unreachable
   guard, persuasion misses, negotiation failures, and the limited supporting
   development tests that changed Agent 5.
8. **Reproducibility and release boundary**: exact source receipt, environment,
   data dictionary, privacy exclusions, licensing, compute accounting, and
   artifact commands.
9. **Ethics and limitations**: mixed human-agent pool, persuasion risks,
   deidentification, selection, nonstationarity, missing official row IDs, and
   absence of component-level causal attribution.

Standalone Test 1 through Test 4 strategy descriptions, ratings, and timelines
do not belong in this appendix.

## Figure and table policy

Every visual must answer a question about Agent 5 that prose cannot answer as
clearly.

### Main text

- At most one empirical figure: Agent 5's bargaining, negotiation, persuasion,
  and optional overall rating trajectory across exact dated checkpoints.
- Required labels: `Agent 5 rating` on the y-axis, timezone-explicit date/time
  on the x-axis, a complete family legend, visible point markers, and a caption
  stating that the path is descriptive and noncausal.
- One compact Agent 5 policy table.
- One Agent 5 behavior and outcome table.
- No architecture diagram, competitor chart, cross-profile bar chart, clone
  forest plot, or didactic payoff illustration if the equation and example fit
  in prose.

### Appendix

- An owner-by-state conformance matrix is useful only after the independent
  Agent 5 replay is complete.
- A cell-coverage matrix is useful only if it gives explicit denominators and
  distinguishes observed, eligible, selected, changed, returned, and joined.
- Every color, hatch, marker, and line style must be defined in a visible
  legend. Every panel must be independently labeled.

## Safe claim bank

- Agent 5 finished second in the agent track and third on the combined board at
  official close.
- Agent 5's official profile displayed 2590.02 after 46,564 rated games.
- Agent 5's final competition configuration was deterministic and LLM-off.
- Agent 5 used an observable-state ordered router with structural owners,
  empirical heuristics, postguards, legal coercion, and fallbacks.
- The complete two-window Agent 5 local census contains 245 assignments, 2,288
  own actions, 244 rated outcomes, and one timeout.
- Agent 5's family ratings seesawed during live play, including a same-overlay
  window in which bargaining rose while negotiation and persuasion fell.
- Several candidate claims were rejected after Agent 5-relevant reachability,
  denominator, response-model, or outcome-join audits.
- The final endpoint shows that Agent 5 was competitive. It does not identify
  the causal value of any one component.

## Claims prohibited without new evidence

- Agent 5 won the competition.
- The final frozen overlay caused second place.
- Agent 5 was evaluated as a fixed policy over all 46,564 games.
- Every Agent 5 action matched its intended owner.
- The 245-assignment census represents Agent 5's lifetime behavior.
- The final stack optimized the undisclosed opponent-adjusted official rank.
- Every retained Agent 5 component passed a completed causal experiment.
- Hidden-information negotiation observed the opponent's private value or exact
  ZOPA.
- Repeated GLEE persuasion implemented an optimal committed Bayesian
  persuasion scheme.
- Zero logged errors means zero execution or server errors.

## Required changes to the current draft, not yet applied

The LaTeX remains untouched. When manuscript editing begins, the following
changes are required:

1. Replace the abstract's multi-profile account framing with Agent 5's name,
   strategy, official result, live behavior population, and evidence boundary.
2. Remove account selection and five-profile portfolio design from the stated
   contribution.
3. Recast "Adaptive strategy and action audit" as "Agent 5 design" and make
   action auditing a subsection or implementation principle.
4. Replace generic or pooled conformance examples with Agent 5-specific checks,
   or place pooled mechanism evidence in the appendix with an explicit reason.
5. Remove Test 2's unchanged-stack example and use the August 27 Agent 5
   same-overlay seesaw instead.
6. Remove Test 4 score-floor and dynamic-stop material because neither became
   part of Agent 5.
7. Retain the credibility-reset source limitation because the component entered
   Agent 5, but describe the source as a development challenger in the core.
8. Retain the broad clone only if needed to explain rejection of broad imitation
   from Agent 5. Move its detailed statistics to the appendix.
9. Replace account-level conclusion language with Agent 5-specific competitive
   performance and the precise runner-up result.
10. Eliminate any figure or table whose subject is the fleet rather than Agent
    5.

## Next evidence tasks before manuscript editing

1. Build the private exact Agent 5 policy specification from the banked source
   and 81-key overlay.
2. Reconstruct owner selection and returned-action conformance first for the
   63-game pre-close window, then for all 245 assignments if provenance holds.
3. Produce Agent 5-only role, state-cell, action, outcome, and failure tables.
4. Repair the invalid lifetime coverage interpretation. Do not divide local
   terminal assignments by official rated games.
5. Fix the rating-checkpoint timezone and durable provenance before making the
   Agent 5 trajectory figure.
6. Audit every proposed sentence against an Agent 5 evidence object and causal
   status.
7. Decide the sanitized Agent 5 source release boundary before claiming full
   reproducibility.

## Editorial test

For every paragraph, table, equation, and figure, ask:

> Does this help a reader understand what Agent 5 was designed to do, what it
> actually did, why a final component was present or absent, or what its result
> establishes?

If the answer is no, remove it from the paper. The fact may remain in the
private evidence warehouse, but it is outside the manuscript's scope.
