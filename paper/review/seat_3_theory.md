# Reviewer Seat 3: Game Theory and Literature

## 1. Reconstructed theoretical contribution

The paper’s real theoretical contribution is not a new bargaining equilibrium or persuasion theorem. It is a hierarchy for reasoning about strategic agents under GLEE’s rank-based, nonstationary evaluation:

1. GLEE transforms payoff through a within-cell empirical percentile, so higher expected payoff need not imply higher expected rating.
2. Pointwise payoff guarantees can survive a monotone raw-rank transform, but equilibrium intuitions and mean-payoff comparisons generally do not.
3. Classic theory should therefore define narrowly scoped structural owners and invariants.
4. Field-derived heuristics, including strategies copied from leaders, require action-level and all-assignment evaluation.
5. A leaderboard result demonstrates competitiveness. It does not, by itself, identify the component that caused it.

That is coherent, useful, and substantially more original than any individual proposition in the appendix.

## 2. Strongest theoretical element

The strongest element is the separation among:

- structural theorem,
- software invariant,
- descriptive behavioral audit,
- retrospective comparison,
- randomized field effect.

The appendix applies this distinction unusually carefully. It does not pretend that Rubinstein bargaining, Myerson-Satterthwaite, Bayesian persuasion, or Boulware schedules directly solve the live competition. The paper repeatedly states what each model proves, which assumptions GLEE violates, and what behavior remained empirical. This is a genuine strength and could become the paper’s award-level intellectual signature.

## 3. Ranked concerns

1. **The central theorem-level idea is implicit rather than stated.**  
   Locations: abstract, lines 49–69; contributions, lines 90–101; conclusion, lines 292–295.

   The paper contains the ingredients for a clean principle but never names it: pointwise or stochastic payoff dominance survives a fixed monotone percentile map, while a higher mean alone does not. That distinction explains why terminal positive acceptance can be structural while concessions, persuasion schedules, and leader imitation must be tested.

   Minimal fix: add an appendix proposition:

   > For fixed nondecreasing \(Q\), if \(Y_a\geq Y_b\) almost surely, then \(\mathbb E[Q(Y_a)]\geq\mathbb E[Q(Y_b)]\). A larger expected payoff alone does not imply this ordering.

   Then use one main-text sentence to explain that this boundary determines which game-theoretic rules become structural owners.

2. **The retained leader fallback appears inconsistent with the falsification thesis.**  
   Locations: Table 1 negotiation row, line 195; competitor experiment, lines 215–223; final policy, lines 237–241; Appendix line 840.

   The randomized leader clone failed its promotion rule, yet an observed-leader buyer path remained in the bank. A skeptical reviewer can read this as selective falsification.

   Minimal fix: state explicitly that failure to promote was not evidence that removal would improve the full stack. The fallback remained inherited and unvalidated, while structural owners narrowed its scope. This distinction is scientifically defensible and actually strengthens the argument.

3. **The main-text persuasion equation is undefined and looks ornamental.**  
   Location: lines 128–139.

   The \(q^*\) equation appears without defining \(p,v,P,u\), and the main text does not say how it produced the final heuristic.

   Minimal fix: replace it with the direct bridge:

   > In the one-shot benchmark, recommending every item is obedient exactly when the buyer’s prior expected value is at least the price, equivalently \(q^*\geq1\).

   Then state that repeated noncommitment invalidates the inference that this remains dynamically optimal.

4. **There is a small but real mathematical wording error.**  
   Location: lines 121–123.

   \(Q(0)+A(x)\{Q(u(x))-Q(0)\}\) is the **expected** raw rank, not the realized raw rank.

   Minimal fix: change “raw rank equals” to “expected raw rank equals.”

5. **The abstract does not tell an unfamiliar reader what GLEE is.**  
   Location: lines 49–52.

   It starts with the scoring transform before expanding the acronym or describing the shared-pool strategic-language setting.

   Minimal fix: begin with:

   > GLEE, Games in Language-based Economic Environments, is a live competition in which autonomous agents and humans play multi-turn bargaining, bilateral negotiation, and persuasion games in a shared opponent pool.

6. **The conclusion is accurate but anticlimactic.**  
   Location: lines 272–295.

   Almost the entire section is limitations. The last three sentences stop at epistemic caution and do not explain why a competition win would matter scientifically.

   Minimal fix: move detailed ethics qualifications to the appendix, retain a compact limitations paragraph, and reserve a visually distinct final paragraph for the result. The ending should distinguish competitive success from causal understanding.

7. **The theoretical novelty is slightly overstated in the contribution list.**  
   Location: lines 90–96.

   The expected-payoff reversal is mathematically correct but elementary. “We formalize why” risks sounding like a new rank-utility theorem.

   Minimal fix: say “We derive the decision implications of GLEE’s empirical-percentile objective,” and foreground the zero atom, pointwise-dominance boundary, and opponent adjustment assumptions.

8. **The logged-policy literature is mostly contextual-bandit literature applied to a sequential game.**  
   Locations: lines 151–154; Appendix lines 574–580.

   Li et al. and Dudík et al. correctly motivate support and counterfactual-response concerns, but GLEE interactions are sequential, history-dependent, and potentially interfering.

   Minimal fix: either qualify those citations as analogies for support failure or add a sequential off-policy evaluation reference such as Jiang and Li’s doubly robust evaluation for reinforcement learning.

## 4. Missing or weak bridges to prior work

- Connect the rank-reversal example to first-order stochastic dominance. This yields a precise line between safe structural reasoning and empirical policy evaluation.
- Connect \(q^*\geq1\) directly to the final known-value all-push persuasion branch.
- Explain why failure to promote a leader clone does not identify the effect of removing an inherited fallback.
- Use empirical game-theoretic analysis more centrally. The competition is a changing empirical strategic environment, not merely a conventional benchmark.
- Clarify that Lazear and Rosen provide an analogy, while GLEE’s direct objective is expected empirical-CDF-transformed payoff.
- Add sequential off-policy evaluation literature or narrow the claims attached to contextual-bandit citations.

The amount of theory is already appropriate for four pages plus appendix. More citations in the main text would make it feel like name-checking. The better move is to make the few existing bridges sharper.

## 5. Abstract recommendation

A stronger shape would be:

> GLEE, Games in Language-based Economic Environments, is a live competition in which autonomous agents and humans play multi-turn bargaining, bilateral negotiation, and persuasion games in a shared opponent pool. Because GLEE converts each payoff into a same-configuration, same-role percentile, adjusts it for opponent strength, and only then updates rating, maximizing expected money need not maximize expected rating. We study the development and banked behavior of a deterministic, LLM-free agent [that placed first, only after official verification]. Its architecture gave priority to game-theoretic invariants and treated field-derived heuristics, including tactics copied from leading competitors, as falsifiable hypotheses. An action-level audit required treatment eligibility, actual firing, a changed legal action, frozen decision rules, and outcomes for every assigned game. That process reversed a positive-looking accept-all estimate, invalidated a surplus experiment with unsupported counterfactual responses, corrected 11,737 unresolved games misread as losses, and stopped a randomized leader clone whose interval crossed zero and whose no-deal rate increased. The broader lesson is that in a nonstationary rank-scored field, competitive performance becomes scientifically interpretable only when mathematical guarantees, transmitted behavior, and field effects are kept distinct.

Use “first place” only after official verification. Also replace “The resulting agent” in the current abstract with “At the dated bank, the audited agent” to avoid implying that the audit causally produced the ratings.

## 6. Conclusion recommendation

For the working draft:

> If the final leaderboard confirms first place, that result will establish that this stack was competitive in GLEE. It will not identify which unrandomized component caused the result, nor make the policy optimal outside the dated field. That distinction is the paper’s central result. Structural game-theoretic guarantees retained only their stated scope; equilibrium intuitions and leader traces became hypotheses whose value depended on opponent response, configuration, and a moving comparison population. The agent changed repeatedly, while one contract remained fixed: verify the action that actually reached the game, retain the full assignment cohort, and freeze the rule by which evidence changes policy. A leaderboard identifies a winner. Falsification is what turns that outcome into a scientific result.

After an official win, replace the conditional first sentence with the verified placement and date.

## 7. Conditional scores

| Dimension | Score |
|---|---:|
| Correctness | 8.5/10 |
| Theoretical depth | 8.3/10 |
| Novelty | 7.5/10 |
| Theory-behavior integration | 7.2/10 |
| Clarity | 7.1/10 |
| Award competitiveness, conditional on winning | 8.2/10 |
| Award competitiveness after the fixes above | 9.0/10 |

## 8. Verdict

**Strong workshop accept and plausible Best Competition Paper finalist, conditional on a verified competition win. Not yet an obvious award winner in its current form.**

The unusually honest failure analysis, behavior audit, and distinction between mathematical guarantee and field effect are award-caliber. The remaining problem is presentation: the abstract assumes GLEE knowledge, the main theory has two weak bridges, the retained failed-clone fallback needs explanation, and the conclusion does not yet convert a potential first-place result into a memorable scientific claim.

One separate submission risk should be checked immediately: `main.tex` says and uses `sglblindworkshop`, while the official competition call reportedly requires double-blind review. The venue-fit reviewer should verify the exact NeurIPS 2026 style option before submission.
