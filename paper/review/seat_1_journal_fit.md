# Reviewer Seat 1: Competition-Track Fit and Best-Paper Case

## 1. Thesis as understood

In a live rank-based agent competition, the most durable source of competitive advantage was not one fixed game-theoretic heuristic, but a falsification discipline that separated structural guarantees from field-dependent guesses and audited the action actually transmitted.

## 2. Strongest feature

The paper's strongest feature is its unusual evidentiary honesty. Most competition papers retrospectively present a winning system as a coherent sequence of improvements. This paper instead documents selection bias, non-firing gates, treatment leakage, a sign-reversing replay, an inconclusive competitor clone, parser failure, and rating reversals. Combined with the required Agent Behavior Analysis, this gives the paper a real scientific identity beyond "we won." The title, "Percentiles, Not Payoffs," is memorable and expresses the central strategic puzzle well.

## 3. Ranked concerns

### 1. Submission blocker: unresolved human-participant and ethics status

**Location:** Section "Limitations and conclusion"; NeurIPS checklist, Code of Ethics, human subjects, and IRB items.

**Evidence:** The checklist answers "No" to conformity with the Code of Ethics and explicitly says the draft "must not be submitted" until review is resolved. The shared pool may contain human opponents who received persuasive or strategically misleading text.

**Why it matters:** This can override every scientific strength. An award-caliber paper first has to be reviewable.

**Minimal fix:** Obtain and document the applicable institutional or organizer determination before submission. Then revise the main limitation and checklist to state the actual determination without breaking anonymity. Do not solve this only by changing the checklist answer.

### 2. Conditional on winning, the paper still does not clearly tell the reader what won

**Location:** Title, Abstract, Introduction, end of "Competitors, ratings, and failed theories."

**Evidence:** The draft reports three banked ratings and a displayed-family mean, but it does not state placement, the comparison population, or the competition outcome. It also foregrounds the audit process so strongly that the final agent architecture is hard to summarize in one sentence.

**Why it matters:** A Best Competition Paper should connect the scientific contribution to the competition result. Readers should know both what the system did and why its result is noteworthy.

**Minimal fix:** Once officially verified, add one restrained result sentence to the abstract and results, such as "The resulting deterministic agent placed first in the GLEE competition." Follow it immediately with the caveat that placement validates full-stack competitiveness, not the causal value of each retained component. Consider the camera-ready subtitle "Building and Auditing a First-Place Agent in GLEE," but only if this does not violate double-blind policy.

### 3. The proposed audit process is compelling, but its own value is not causally evaluated

**Location:** Abstract contribution sentence; Introduction contributions; "Falsification under a moving field"; Conclusion.

**Evidence:** The manuscript demonstrates that the process rejected or corrected several bad claims, but it does not compare development with and without the process, nor show that the audit discipline itself caused the final rank.

**Why it matters:** "Falsification as strategy" can sound like a performance claim that the evidence cannot identify. The paper currently has a strong case-study contribution, not an experiment on scientific workflow.

**Minimal fix:** State the contribution as an instantiated, action-level evidence contract and a documented case study. Replace broad suggestions that the process produced the rating with the narrower claim that it made the path to the result auditable and prevented specific unsupported deployments.

### 4. The abstract assumes familiarity with GLEE and overwhelms the reader with forensic detail

**Location:** Abstract, especially its opening and the sequence of 352, 375, 11,737, 91, 44, and 47.

**Evidence:** "GLEE" is never expanded there. The reader is not told that it is Games in Language-based Economic Environments, that it involves multi-turn bargaining, negotiation, and persuasion, or that agents and humans share a changing opponent pool.

**Why it matters:** The abstract's conceptual hook is buried beneath numbers whose denominators and estimands require the paper to understand. Workshop reviewers may know GLEE, but award readers should not need that context.

**Minimal fix:** Define GLEE in the first sentence. Keep one vivid reversal and, at most, the randomized-clone result. Move the reader bug count and secondary denominators to the body. End with the competitive outcome and the portable methodological claim.

### 5. One retained behavior appears inconsistent with the falsification narrative

**Location:** Agent Behavior Analysis, negotiation row; "Competitors, ratings, and failed theories"; Appendix "Dated Agent 5 configuration."

**Evidence:** The broader leader-trajectory clone failed every promotion gate, yet an observed-leader action function remained a buyer fallback in the final agent and inherited seller rules also remained operational. The distinction between the failed treatment and the narrower retained fallback is present, but easy to miss.

**Why it matters:** A skeptical reviewer can say the paper celebrates falsification while retaining an unvalidated competitor-derived policy. That would weaken its central thesis.

**Minimal fix:** Add one direct sentence explaining that the failed experiment tested a broader trajectory clone, not the already-deployed fallback in isolation; structural owners took precedence; and the residual fallback is reported as operational but not causally validated. If there is no stronger justification, call this an unresolved inconsistency rather than obscuring it.

### 6. The conclusion is a limitations paragraph followed by an underpowered ending

**Location:** "Limitations and conclusion," final three sentences.

**Evidence:** The section accumulates nonstationarity, identification, reproducibility, ethics, and dual-use limitations, then ends with "the most valuable update was the decision not to believe an apparent improvement." That is a good line, but it does not synthesize what the agent, result, and audit establish together.

**Why it matters:** The last paragraph should leave reviewers with the paper's positive scientific result and why it changes how competition agents should be evaluated. At present it feels like the manuscript retreats from its own contribution.

**Minimal fix:** Separate the limitations from a short conclusion. State what won, what winning does not prove, and the portable evidence standard. End on the distinction between leaderboard success and behavioral understanding.

## 4. Abstract rewrite guidance

Use a five-part abstract:

1. Define the setting: "GLEE, Games in Language-based Economic Environments, is a live shared-pool competition in which agents and humans play multi-turn bargaining, negotiation, and persuasion games."
2. State the scoring problem: payoffs are mapped to same-configuration, same-role percentiles before rating, so payoff-maximizing heuristics can be rank-suboptimal.
3. State the system: a deterministic, LLM-free agent combining structural game-theoretic owners with bounded empirical fallbacks.
4. State the method and one decisive failure: action-level reachability, all-assignment outcomes, frozen rules, and the accept-all replay reversing from positive to negative after realized continuation was retained. Optionally retain the inconclusive randomized clone as the second example.
5. State the verified outcome and contribution: first place, only after confirmation, plus the claim that the evidence contract makes a changing competition policy scientifically interpretable.

The current abstract should lose several forensic counts. The 11,737-outcome reader bug is valuable, but it is not the abstract's most important fact. The abstract should make a new reader understand GLEE, the agent, the result, and the contribution without needing to decode the experiment ledger.

## 5. Conclusion rewrite guidance

Keep the current limitations, but end with a separate constructive paragraph along these lines:

> GLEE was not solved by a single equilibrium rule. The final agent combined structural reasoning where the information state supported it with deliberately bounded empirical fallbacks where it did not. If the final result is confirmed, first place establishes that this full stack was competitive in the live field; it does not identify every retained component as optimal or attribute the result to the audit process. The broader contribution is an evidence contract for live strategic agents: verify the action that actually reached the interface, retain every assigned outcome, and judge hypotheses at declared checkpoints. A leaderboard can establish who won. This discipline makes it possible to understand what survived on the way there.

That ending preserves the paper's caution while giving it a stronger intellectual payoff.

## 6. Conditional scores, assuming an officially verified first-place finish

- Competition-track fit: 9/10
- Scientific contribution: 7/10
- Clarity: 6/10
- Evidence discipline: 8/10
- Memorability: 7/10
- Award competitiveness in its current form: 6.5/10
- Award competitiveness after the narrative and ethics issues are resolved: approximately 8.5/10

## 7. Verdict

**Competitive but Not Yet Distinctive.**

The substance is stronger than the current presentation. With the abstract contextualized, the conclusion rebuilt, the retained-clone inconsistency confronted, and the ethics gate resolved, this could become a Strong Award Contender.

## 8. What first place would and would not add

A first-place result would provide meaningful external validation that the complete deterministic system was highly competitive against the live shared field. It would also make the paper's failure-centered account unusually credible, because the authors would be disclosing negative results from a position of success rather than explaining away a weak score. It would not show that falsification caused the win, that every retained heuristic was beneficial, that the agent was optimal in any game-theoretic sense, or that the reported rating chronology identifies component effects. The best award case is therefore not "our method won, so it is correct." It is "the full system won, and our evidence discipline lets us state much more precisely than usual which behavioral claims that result does and does not support."
