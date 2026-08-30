# Theory, Code, and Evidence Audit

Date: 2026-08-30

## Verdict

The paper's formal results are mathematically sound after the corrections in this audit, provided their stated assumptions are retained. The final text does not claim that a benchmark equilibrium describes every GLEE game, that a configured flag proves a transmitted server action, or that a rating movement identifies a component effect.

The most consequential corrections were about scope rather than algebra:

1. The generic bargaining recursion is an equilibrium result only for the stated finite, complete-information alternating-offer model. Production code also inserts a synthetic horizon in the public no-limit state. The manuscript now calls that branch a heuristic with an artificial terminal boundary.
2. The bank-enabled P2 bargaining owner is a fixed Bob-share ladder with a discounted acceptance floor. It does not accept every positive terminal share.
3. The submitted agent's negotiation policy is an ordered portfolio. Three first-principles cells have precedence, then hidden terminal inference, then the observed-leader buyer action function. Seller prices and decisions retain the current fallback, while a supported-cell table can rewrite messages.
4. The 668 persuasion turns were selected by a fixed-history shadow of an inactive predicate. They were not a submitted-agent intervention.
5. Historical ratings and selected replays are now labeled as observational, retrospective, archival, simulated, or randomized as appropriate.

## Formal claim ledger

| Claim | Status | Assumptions or boundary | Implementation trace |
| --- | --- | --- | --- |
| Empirical-midrank jump | Proved | Fixed reference multiset and exact-equality midrank. The local implementation uses a numerical tie tolerance, and the official tie rule is undocumented. | `sim/percentile.py`; executable check in `paper/analysis/verify_theory_code.py` |
| Expected payoff can reverse expected raw rank | Proved by finite counterexample | Orders raw rank only. It transfers to adjusted rank only when the fixed opponent adjustment preserves the relevant expectation ordering. | Exact reference multiset `D={5}` is checked exhaustively by the verifier and plotted by `paper/figures/gen_fig_rank_objective.py`. |
| Expected adjusted rank orders a one-step rating update | Proved | Current rating, positive update rate, opponent-adjustment map, and game count are fixed; rating clamp is inactive. This is not a final-leaderboard theorem. | Equation in `paper/main.tex`; executable monotonicity check in the verifier. |
| Finite bargaining recursion and patient-responder parity | Proved | Divisible pie, zero disagreement, finite known proposal count, complete information and common knowledge, alternating offers, discounting, and acceptance at indifference. | `glee_agent/strategies/bargaining.py:59`; all discount and horizon combinations in the verifier match the implementation. |
| Stationary Rubinstein share | Proved in its stated domain | Stationary limit with discount product below one. The equal-split return at the fully patient indeterminate corner is an implementation convention. | `glee_agent/strategies/bargaining.py:59` |
| Public no-limit bargaining behavior | Heuristic, not equilibrium | Production inserts a 99-opportunity recursion horizon and uses a separate concession clock. Neither converts a genuinely unlimited public game into a finite-horizon equilibrium. | `glee_agent/config.py:59`, `glee_agent/strategies/bargaining.py:304` |
| Limited discounted accept guard | Proved only against one stipulated continuation | The counter pays exactly `c`, is accepted exactly one discount period later, and no better later path is included. | Appendix proposition; broad deployment was off at bank. |
| P2/H12/delta=.95 owner | Code-verified policy, not optimality theorem | Bob only, messages off, disclosed 12 rounds, delta 0.95. Odd-round decisions compare with a common discounted terminal floor. Even offers use the fixed .61/.68/.74/.82/.91 ladder; round 12 gives Alice .01. | `glee_agent/bargaining_p2_commitment.py:49`, `:116`, `:172`, `:178`, `:264`; verified by executable state cases. |
| Strict gains from trade | Proved | Quasilinear bilateral trade with seller value `s`, buyer value `b`, and price `p`. | Appendix proposition. |
| Hidden 6/16 feasible-pair count | Structural only under a model | Conditional on the checked-in reconstructed support and an independent-uniform joint type model. Live logs do not identify the hidden joint distribution. | `sim/grid.py`; the full tests currently detect frequency drift between the frozen grid and live logs. |
| Offer-derived reservation bounds | Proved conditionally | Each observed offer must be individually rational for its proposer. The corpus contains violations, so code treats the bounds as conditional evidence. | `glee_agent/nego_hidden_terminal_inference.py:103` |
| Power concession path | Proved | `k>0`; the result is monotonicity and endpoints, not optimality. `k>1` is Boulware-like, `k=1` linear, and `k<1` conceder-like. | Negotiation policy and appendix proposition. |
| Generic profitable-offer clamp | Code property on its fallback only | Earlier deterministic owners can return before the generic clamp. On reached generic rejection states, the counter weakly improves own surplus if accepted, but can reduce agreement probability. | `glee_agent/strategies/negotiation.py` and ordered router in `glee_agent/deterministic_negotiation.py:256` |
| Persuasion obedience threshold | Proved | One-shot, risk-neutral buyer, correct values and prior, all high items recommended, low items recommended at stationary rate `q`, and commitment to that signal rule. GLEE's repeated noncommitted setting does not satisfy all of these assumptions. | `glee_agent/strategies/persuasion.py:412`; checked over boundary cases by the verifier. |
| Buyer break-even posterior | Proved | Myopic money objective. It need not be rank-optimal or dynamically optimal. | Persuasion appendix. |
| Discrete credibility posterior | Code-matched approximation | Stationary grid, conditional independence, parser correctness, error rate .02, and regularization floors. It is robustified Bayes, not exact unrestricted inference. | `glee_agent/strategies/persuasion.py:2133`; posterior weights checked by the verifier. |
| Banked persuasion seller policy | Code-verified cases | Known values use the earlier all-push branch when prior expected value weakly clears price and truth otherwise under the bank knobs. Unknown values use the observed buy-rate cutoff. Later buyer-side vetoes are separate. | `glee_agent/strategies/persuasion.py:430`; checked by the verifier. |
| V1 decline veto direction | Code property, incomplete coverage | It can change BUY to PASS and cannot force a purchase. V2 and V3 were off at bank. Coverage and rating value are not established. | `glee_agent/strategies/persuasion.py:44`, `:2808`; bank state in `.ai/CURRENT_STATE.md`. |

## Code ownership trace

The paper now follows the returned-action path rather than treating a flag or intermediate plan as behavior:

1. Family routing and final local coercion occur in `glee_agent/dispatch.py` and `glee_agent/actions.py:965`.
2. Bargaining first allows the exact narrow P2 owner, then uses the generic planner and later transforms. The P2 component validates role, phase, parity, horizon, discount, and message scope before returning an owned action.
3. Negotiation owner order is explicit in `glee_agent/deterministic_negotiation.py:256`: first-principles cells, hidden terminal inference, later support owners when selected, observed-leader buyer behavior, and current seller fallback.
4. Persuasion combines the seller policy, buyer posterior, tight credibility reset, and a final V1 one-directional decline veto. The paper does not call inactive V2/V3 or A/B branches banked behavior.

Local post-coercion return is not the same as server receipt. The manuscript claims exact transmission only for successfully joined subsets and makes no bank-wide conformance claim.

## Empirical provenance ledger

| Evidence | Manuscript status | What it can support | What it cannot support |
| --- | --- | --- | --- |
| August 29 ratings and lifetime counts | Dated full-stack snapshot | Observed stack-level field outcome | Component causality, official final placement, or a stationary field |
| 91-game leader clone table | Game-hash randomized candidate-control comparison, stopped after an earlier look | Reproducible point contrast, host strata, no-deal counts, descriptive normal intervals | Promotion, a clean sequential confidence statement, or the isolated value of narrower inherited rules |
| 45 joined bargaining histories | Selected retrospective hindsight comparison, with one selected case unresolved | Accept-now versus the realized continuation in those joined histories | A policy treatment effect or an arbitrary-continuation dominance theorem |
| 6,188 decision states from 800 simulated games | Simulation reachability study | Eligibility, firing, and changed submitted actions in the simulated grid | Live reward value or live-state frequency |
| 668 persuasion turns | Fixed-history shadow of an inactive predicate | Existence of a narrow behavior state and experiment motivation | A submitted-agent intervention, independent sample size, or promotion evidence |
| 4,001 bargaining games | Historical local diagnostic | Role asymmetry in that local diagnostic | Official role percentile or a causal effect |
| 11,737 stopped-collector backlog | Fault-forensics snapshot | Evidence that a reader mishandled old omissions | Fleet total or justification for imputing every omission as a loss |
| 6/16 hidden type pairs | Reconstructed support plus independent-uniform model | Conditional structural feasibility arithmetic | The live hidden-type frequency distribution |

## Corrections made in the manuscript

- Replaced the false claim that the P2 owner accepts any positive terminal share with the exact ladder and discounted-floor rule.
- Restricted the bargaining equilibrium language to the finite complete-information model and labeled the 99-round production boundary synthetic.
- Added the missing `delta=1` boundary to the one-period gain threshold.
- Replaced broad claims about an aspiration floor and concession projection with the exact pre-transform and history-dependent scopes.
- Rewrote the negotiation owner order to match production code, including seller message rewriting.
- Replaced the generic bargaining "60-round clock" shorthand with the exact
  discount-dependent clock, whose supported values are 14, 29, 59, and 60 and
  whose value 60 is only a cap.
- Separated global negotiation ownership from the internal generic-seller
  decision order, and marked the configured final-option and ultimatum writers
  as shadowed on supported returned paths.
- Labeled the 6/16 support result as conditional on the reconstructed generator and an independent-uniform model.
- Recast the 45/45 result as selected hindsight, not a losing treatment.
- Recast the 668-turn persuasion result as a fixed-history shadow, not banked submitted-agent behavior.
- Separated local post-coercion return from server receipt.
- Recast the clone interval as descriptive after repeated inspection and retained all failed promotion criteria.
- Labeled archival diagnostics, unresolved outcomes, stopped collectors, and era-confounded comparisons explicitly.
- Kept first-place language conditional on organizer verification.

## Verification results

`paper/analysis/verify_theory_code.py` passed all five groups:

- objective algebra and finite empirical rank reversal
- bargaining recursion and parity
- banked P2 bargaining owner
- negotiation structural owners
- persuasion threshold, posterior, and seller policy

`paper/analysis/analyze_clone_checkpoint.py` reproduced the 91-game values used in the paper, including the unstratified difference `0.869101`, normal interval `[-0.730366, 2.468567]`, profile-stratum-standardized difference `0.990780`, and no-deal difference `6.141` percentage points.

The full repository suite completed with `2861 passed, 4 failed`. No strategy code was changed by this audit. The failures were:

1. `tests/test_bargaining_horizon_floor.py:195`, the documented bargaining floor expectation mismatch.
2. `tests/test_sim_grid.py:599` for bargaining.
3. `tests/test_sim_grid.py:599` for negotiation.
4. `tests/test_sim_grid.py:599` for persuasion.

The three grid failures compare a frozen reconstructed distribution with the much larger current live-log corpus. They reinforce the paper's decision to describe the simulator as reconstructed and to avoid treating its sampling weights as current official frequencies.

The LaTeX build succeeds. Main text ends on page 4, references begin on page 5, and the technical appendix follows the references.

## Residual limits that must remain in the paper

- The official tie rule and opponent-strength adjustment are undocumented.
- Hidden type frequencies and responses to unplayed actions are not identified from the available logs.
- No complete final-process manifest links every banked process to commit, overlay, and joined server action.
- There is no bank-wide denominator for action conformance.
- Many historical measurements lack a frozen row-level artifact and are usable only as labeled archival diagnostics.
- The official final competition placement is not yet verified in the manuscript workspace.

Within those limits, the draft now distinguishes mathematical proof, implementation fact, selected behavior evidence, randomized evidence, and full-stack rating chronology. It does not fill an evidentiary gap with an invented mechanism or result.
