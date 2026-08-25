# GLEE competition paper: framing brief

Status: proposed framing for author confirmation, 25 August 2026.

Target: IAB Workshop at NeurIPS 2026, GLEE competition-paper track. The track
allows four pages in NeurIPS format (references excluded) and requires an
Agent Behavior Analysis section.

## Recommended contribution

> We present a deterministic, LLM-free GLEE agent that combines
> game-theoretic structure with rank-aware online experimentation, and show
> through live behavior analysis that many apparently successful strategy
> changes disappear when evaluation retains all outcomes, defines cohorts
> before treatment, and verifies that each mechanism actually changes actions.

This framing makes the agent itself the contribution while giving the paper a
specific technical lesson. It is stronger than a leaderboard narrative because
the final rank is not yet known, and stronger than a catalogue of heuristics
because the repository contains unusually clear evidence about why plausible
strategy conclusions failed.

## Working title

**Winning the Percentile, Not the Payoff: A Deterministic,
Experiment-Driven Agent for GLEE**

Alternatives:

1. **A Deterministic Agent for GLEE: Game Theory, Rank-Aware Objectives, and
   Live Causal Auditing**
2. **What Survives Contact with the Leaderboard? Building and Auditing a GLEE
   Agent**

## Narrative

The GLEE competition does not reward raw expected payoff. It converts each
game payoff to a same-configuration, same-role percentile, adjusts that value
for opponent strength, and updates a moving rating. We therefore built a
low-latency deterministic agent whose three family policies use economic
structure, empirical response regularities, and a final legality layer. The
same scoring rule also makes naive development analysis unreliable: zeros are
costly in cells where competitors close, agreements are a selected sample,
unplayed asks have unidentified continuation values, and a configuration flag
can produce a perfect-looking null while never reaching its intended branch.
Our development process consequently became as important as the policies:
per-game randomized arms when permitted, pre-treatment cohorting, all-outcome
intent-to-treat reads, exact action-wire auditing, gate-reachability checks,
and explicit unresolved-outcome bounds.

## Claims that the current evidence supports

### 1. The scoring objective changes the optimal strategy

- A payoff is ranked within the exact configuration and role before the rating
  update; maximizing expected money is therefore not generally equivalent to
  maximizing competition score.
- Negotiation contains a large zero-payoff atom. In one-round,
  complete-information games, every observed offer that left the responder a
  positive amount closed (384/384), whereas offers at or beyond the feasible
  span did not (0/78). This supports taking almost the full surplus in that
  terminal structure, but does not identify behavior in multi-round games.
- Forty-five percent of the negotiation value grid is structurally infeasible:
  6/16 hidden-information value pairs have a positive bargaining range, while
  all six complete-information configurations do.

### 2. A deterministic agent can be reliable across heterogeneous games

- The decision path contains no LLM and uses a dispatcher plus a final action
  coercion layer.
- The agent combines backward-induction structure in bargaining, bounded
  concession and terminal rules in negotiation, and Bayesian persuasion
  thresholds with empirical belief tracking in persuasion.
- The live system reports zero strategy errors and zero invalid actions across
  more than 24,000 scored turns in the repository README snapshot. Refresh this
  count before submission.

### 3. Naive observational and replay analyses repeatedly produce false wins

- Conditioning on completed deals created the false conclusion that taking
  90--95% of negotiation surplus should help; controlled arena measurements
  were negative and reduced close rate.
- A response-model offer engine changed sign across two continuation-value
  fits because the causal value of an unplayed ask was not identifiable from
  logged play.
- A negotiation replay clone auto-accepted unobserved profitable asks and used
  a coarse price bin in place of the intended surplus-share bin. Its apparent
  gain for aggressive pricing was therefore rejected.
- A randomized surplus probe leaked treatment assignment into the agent's
  acceptance threshold and its analyzer joined the wrong response turn. The
  experiment was invalidated rather than interpreted.
- Missing local finals were once imputed as bad outcomes even though an outcome
  collector had stopped. The corrected readers retain them as unresolved and
  block promotion.

### 4. Behavior alignment is enforced as an executable contract

- Every behavioral mechanism is default-off and activates through a runtime
  flag.
- A mechanism must demonstrate eligible states, gate firings, and changed
  final actions before evaluation.
- Randomized arms use stable per-game hashes and keep treatment variables out
  of unrelated decisions.
- Readers include every pre-treatment assignment, including agreements,
  no-deals, walks, zeros, invalids, and unresolved outcomes; unresolved records
  block promotion when they can change the verdict.
- The submitted action, not merely an internal plan, is audited because later
  price writers and wire coercion can overwrite intended behavior.

## Claims to defer or state only as provisional

- Final leaderboard rank, final family ratings, and final game counts.
- Any benefit attributed to the currently running deterministic bargaining
  guards or negotiation leader replica.
- Any fleet-wide causal effect inferred from deterministic, cross-profile
  deployment.
- Any policy effect estimated only among agreements, gate firings, or locally
  recovered outcomes.
- Any assertion that natural-language messages improve performance. Only about
  7.1% of recent negotiation offers contain text, and earlier LLM-written
  persuasion messages converted worse than templates (46.3% versus 55.3%).

## Four-page structure

### 1. Introduction (about 0.6 page)

- Define the unusual percentile objective and why ordinary payoff
  maximization is insufficient.
- Introduce the deterministic three-family agent.
- State the core lesson: trustworthy improvement required causal and
  mechanism-level auditing, not leaderboard watching.
- List three contributions: agent architecture, rank-aware strategic design,
  and an evidence-backed evaluation protocol with negative results.

### 2. Competition and agent design (about 1.0 page)

- Summarize bargaining, negotiation, and persuasion.
- Give the percentile-to-rating objective and explain the effect of zero atoms.
- Show one architecture figure: game state -> family solver -> flagged policy
  overlay -> action coercion -> submitted wire; logs feed offline analysis and
  stable per-game experiments.
- Give one compact paragraph per family; put detailed thresholds in an
  appendix or artifact rather than the four-page body.

### 3. Rank-aware development methodology (about 0.8 page)

- Pre-treatment eligibility and stable hash assignment.
- All-outcome intent-to-treat analysis.
- Reachability and final-wire checks.
- Same-configuration/role empirical CDFs and unresolved-outcome bounds.
- Separate mechanism evidence, observational hypotheses, and causal effects.

### 4. Results and negative findings (about 1.0 page)

- Table with structural negotiation facts and the strongest validated
  bargaining/persuasion findings.
- A failure-analysis table: tempting conclusion, hidden bias/bug, corrected
  verdict.
- Reserve one row for final competition performance and reliability statistics
  to be refreshed at the submission boundary.

### 5. Agent Behavior Analysis (about 0.4 page)

- Compare intended plan source, final submitted wire, and terminal behavior.
- Report invalid-action/strategy-error counts, gate reachability, and examples
  where downstream rewriting violated intended behavior before fixes.
- Explain how default-off flags, exact-stack replay, and frozen decision rules
  kept behavior aligned with the design.

### 6. Limitations and conclusion (about 0.2 page)

- The opponent pool is nonstationary and repeated cross-agent comparisons are
  observational.
- Hidden opponent values make some counterfactuals unidentified.
- Some findings are competition-specific and may not transfer to other payoff
  distributions or scoring rules.
- Conclude that robust strategic-agent development depends as much on
  evaluation design as on the strategy itself.

## Figure 1 concept

A two-lane vector diagram:

1. **Online decision lane:** public game state -> family solver -> default-off
   behavioral flag -> legality/coercion -> submitted action.
2. **Evidence lane:** pre-action assignment -> full outcome join -> exact-cell
   percentile -> precommitted promote/reject rule.

Red callouts mark the failure points observed in this project: unreachable
gate, downstream action overwrite, agreement-only selection, wrong response
join, and unresolved-outcome imputation.

The caption should make the paper's thesis legible without the main text:
strategy and evaluation are coupled, and an internal policy change is not a
valid treatment until it changes the submitted wire for a pre-treatment cohort
whose full outcomes are retained.

## Citation plan

The initial related-work anchor is the verified GLEE benchmark paper:

- Eilam Shapira, Omer Madmon, Itamar Reinman, Samuel Joseph Amouyal, Roi
  Reichart, and Moshe Tennenholtz. *GLEE: A Unified Framework and Benchmark for
  Language-based Economic Environments*. arXiv:2410.05254.

Before adding any other citation, retrieve and verify its metadata and the
claim it supports. Do not generate bibliography entries from memory.

## Author inputs needed before drafting the body

1. Confirm or revise the one-sentence contribution above.
2. Supply the author list and affiliations when convenient; the draft can stay
   anonymized meanwhile.
3. Supply the public ID of the submitted agent for the submission form. It
   does not need to appear in the paper unless the organizers require it.

