# Reviewer Seat 2: Methodology and Statistical Validity

## Central claims and evidence grade

| Claim | Evidence type | Grade | Assessment |
|---|---|---:|---|
| Expected payoff and expected raw percentile can rank actions differently; adjusted percentile determines one-step rating under stated conditions. | Structural | A | The theorem, assumptions, counterexample, tie caveat, inactive-clamp condition, and unknown opponent-adjustment boundary are unusually careful and mathematically correct. |
| Action-level auditing can expose false strategic conclusions. | Retrospective and forensic | A- | The selected replay reversal, invalid surplus probe, unresolved-outcome reader, and non-firing gates establish that these failure modes occurred. They do not establish that the audit process caused the final rating or competition result. |
| The final agent behaved as designed. | Software invariant plus sampled descriptive evidence | B | Returned-action auditing is the right behavioral unit, but the paper explicitly lacks a common final-bank cohort, a complete PID-to-commit manifest, and a bank-wide action-join denominator. |
| The competitor-derived clone was beneficial. | Randomized ITT point estimate under assumptions, inferentially inconclusive | B- | The reproducible point contrast is \(+0.869\) rating/game, but the overlapping early look, stopped read, ordinary normal interval, host heterogeneity, possible interference, and one negative host preclude a positive-effect claim. The paper mostly respects this. |
| Displayed rating movements reveal strategy effects. | Descriptive chronology | A for the negative conclusion | The paper correctly argues that they do not. It retains configuration, exposure, opponent, field-drift, and rating-dynamics caveats. |
| The final ratings document a strong agent. | Descriptive endpoint | A | The three dated values reproduce from the local ledger. They are not component effects. An official win, once verified, would be stronger and easier to interpret than these raw rating values. |
| The falsification contract generalizes to other live fields. | Design argument | B | Plausible and well motivated, but not empirically tested as a treatment. It should remain an argument, not a demonstrated performance explanation. |

The clone analysis script reproduces the manuscript exactly: unstratified \(+0.8691\), normal interval \([-0.7304,2.4686]\); host-standardized \(+0.9908\), interval \([-0.6306,2.6122]\); and no-deals \(13/44\) versus \(11/47\).

## Strongest feature

The paper's strongest contribution is its refusal to confuse a configured policy, an intended mechanism, a changed internal variable, and the legal action actually returned to the SDK. The eligibility, firing, post-coercion action-change, all-assignment outcome, and frozen-decision-rule contract is both technically sound and directly motivated by documented failures. This is more scientifically interesting than another account of a leaderboard climb.

## Ranked concerns

1. **Submission-blocking ethics status**

   - **Location:** Main Section 8, lines 284-289; Appendix governance; checklist items "Code of ethics" and "IRB approvals."
   - **Basis:** The checklist currently answers "No" to compliance and states that an institutional or organizer determination is still required because the shared pool may contain humans.
   - **Impact:** This can prevent submission regardless of scientific merit or competition placement.
   - **Minimal fix:** Obtain the applicable institutional or organizer determination before submission, document it without breaking anonymity, and update the checklist and limitations. This is not a stylistic issue.

2. **The required behavior analysis does not yet measure one common final-agent cohort**

   - **Location:** Agent Behavior Analysis, especially the table caption at lines 185-187 and qualification at lines 201-205.
   - **Basis:** Bargaining uses an early 4,001-game audit and retrospective cases, negotiation uses pooled August 22 data plus simulated states, and persuasion uses selected historical turns. The paper explicitly lacks bank-wide conformance evidence.
   - **Impact:** The section is intellectually honest but only partially answers how the submitted agent actually behaved across its games. This is likely the biggest scientific weakness for the required competition-track section.
   - **Minimal fix:** From existing logs, add a final-era audit with games and actions by family and role, policy-owner frequencies, fallback/error frequency, returned-action to official-history join coverage, and the matched fraction. No new live experiment is required. If this cannot be recovered, foreground "sampled alignment" in the table title rather than implying final-bank coverage.

3. **The abstract implies a causal path from audit process to final performance**

   - **Location:** Abstract, especially "The resulting deterministic..." at line 66.
   - **Basis:** The final ratings are a full-stack endpoint. There is no experiment comparing development with and without the falsification process.
   - **Impact:** A skeptical reviewer can characterize the paper as post hoc process attribution around a successful agent.
   - **Minimal fix:** Replace "The resulting" with "The final." State the competition outcome separately from the methodological contribution. If the agent officially wins, say so only after verification and give the dated official placement.

4. **The abstract does not explain what GLEE is and compresses unlike retrospective estimands**

   - **Location:** Abstract, lines 50-65.
   - **Basis:** "GLEE maps..." assumes prior knowledge. The 352-case \(+0.071\) and 375-exposure \(-0.066\) estimates use different retrospective estimands and denominators, which the appendix explains but the abstract makes sound like a simple corrected reanalysis.
   - **Impact:** External readers cannot understand the setting quickly, and the reversal can look rhetorically stronger than its identification warrants.
   - **Minimal fix:** Open with the full name and game setting. Explicitly call the two numbers "different retrospective estimands," or retain only the corrected estimate and cohort ITT. The abstract should also call the clone result an inconclusive candidate-control contrast, not a "lift."

5. **The clone interval is descriptive, not confirmatory**

   - **Location:** Competitors section, lines 215-223; Appendix identification and competitor table.
   - **Basis:** The \(n=91\) read followed an overlapping \(n=45\) look. The manuscript uses ordinary normal intervals, games may share opponents, game-ID exogeneity is assumed, and adaptive agents weaken no-interference.
   - **Impact:** "Randomized lift" can be read as a statistically validated effect even though the arm failed every promotion gate.
   - **Minimal fix:** Use "randomized candidate-control point contrast." State in the main text that the interval is descriptive after repeated inspection. Keep the stopped design and failure outcome, which are valuable negative evidence.

6. **Reproducibility is too weak for a paper whose contribution is auditability**

   - **Location:** Appendix reproducibility; checklist items on reproducibility, open access, experimental detail, and statistical significance.
   - **Basis:** The clone result is reproducible from a deidentified table, but the central 352/375/4,050 reversal, 45/45 stack reversal, final alignment, historical bootstrap settings, and process-to-commit history are not independently recoverable.
   - **Impact:** This creates a mismatch between the paper's scientific message and its artifact support. It is a substantial best-paper obstacle even if ordinary acceptance remains possible.
   - **Minimal fix:** Release deidentified row-level or sufficient aggregate data and scripts for every numerical claim in the abstract and main figure, plus a frozen code snapshot, environment lock, exact commands, and a data-access statement. Raw transcripts need not be released.

7. **The archived LLM-wording comparison lacks sufficient provenance**

   - **Location:** Appendix theory-evolution, findings, and reproducibility sections; checklist LLM-use item.
   - **Basis:** The paper reports 46.3% versus 55.3%, but the denominator, model/provider, prompt, version, and selection procedure were not preserved.
   - **Impact:** This is an avoidable weak claim that reviewers can use to question the evidence ledger.
   - **Minimal fix:** Recover and disclose the provenance or remove the numerical comparison. An unquantified statement that LLM wording was tested and not retained would not carry the same evidentiary burden.

## Claims that are unusually well bounded

- The raw-rank reversal is not silently converted into an adjusted-rating theorem under an undocumented nonlinear adjustment.
- The rating result is explicitly one-step and assumes a fixed adjustment, positive step size, current rating, and inactive clamp.
- The 6/16 hidden feasibility count is labeled as conditional on the independent-uniform joint model.
- The paper distinguishes structural guarantees, software invariants, retrospective comparisons, randomized ITT, and before/after chronology.
- The 89/14,732 negotiation statistic is correctly described as dependent turns in selected no-deal histories.
- The rating chronology is never presented as an interrupted time-series effect.
- The clone reports both arm denominators, host heterogeneity, no-deals, interval crossing zero, and failed decision gates.
- The paper explicitly limits alignment to sampled actions and declines to estimate failure prevalence.

## Abstract recommendation

Yes, the first sentence should define GLEE. A statistically cleaner opening would be:

> GLEE, Games in Language-based Economic Environments, is a live shared-pool competition in which agents and humans play multi-turn bargaining, bilateral negotiation, and persuasion games. Payoffs are converted to configuration- and role-specific percentiles before rating updates, so optimizing money need not optimize rank.

Then describe this as a documented case study. Keep one retrospective reversal, the invalid response-model example, and the inconclusive randomized clone. Separate the dated final performance from the audit contribution. If an official win is confirmed, report the verified placement instead of expecting readers to interpret three raw ratings.

## Conclusion recommendation

The current conclusion is mostly a limitations paragraph and ends by shrinking the contribution. It needs a distinct synthesis:

> Conditional on official first place, the win establishes system-level competitiveness, not the causal value of any individual component. GLEE's moving reference field made ratings useful for ranking agents but unreliable for explaining why a policy succeeded. The broader lesson is that a competition result becomes scientific only when the submitted action, eligible cohort, failures, and stopping rule remain auditable. A leaderboard can identify a winner. It cannot identify the winning idea without that evidence.

This conclusion accurately cashes out the paper's theory, behavior analysis, and negative results without claiming that the development process caused the win.

## Conditional scores

Assuming an officially verified competition win:

- Rigor: **8.0/10**
- Transparency: **9.2/10**
- Reproducibility: **5.5/10**
- Statistical validity: **7.5/10**
- Award competitiveness now: **7.4/10**
- Award competitiveness after ethics resolution, final-era behavior audit, reproducibility package, and abstract/conclusion revision: **8.8/10**

## Verdict

**Strong competition-track paper, but not yet best-paper ready.** A win would make the case study important, but it would not repair the missing final-era behavior denominator, ethics determination, or reproducibility gap. No additional live strategy experiment is essential for the claims currently made. The necessary work is a final-log alignment audit, artifact packaging, and sharper separation of competition success from causal explanation.
