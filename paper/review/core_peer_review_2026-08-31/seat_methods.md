# Comments to authors

## Adversarial methods, statistics, and evidence review of the four-page core

## Status, scope, and limits

This is an author-requested local review, not an official independent peer review and not an editorial decision. I reviewed only `paper/main.tex` through the first `\clearpage` at line 341 and the corresponding first four pages of `paper/main_core.pdf`. I did not review the appendix, supplement, checklist, or any earlier manuscript version. No network or external service was used.

The reviewed source SHA-256 was `51065b2c2045d1cecb59f54e402d14a100a5e1e61252077741b5800903d8c91d`. The reviewed PDF SHA-256 was `c9492db96cb12b60fbecf957e013b06b172b9f7c14810c71891ee4bee7b19a37`. Pages 1 through 4 were rendered and visually inspected. The core fits within four pages, has no clipping or overlap, and the lifecycle figure has a complete legend. My competence limits are that I do not have organizer-side row-level scoring records or the private scorer implementation, and I am not a competition organizer.

## Methods verdict

The main arithmetic for the official endpoint, lifetime local census, and bounded 245-assignment action receipt is internally consistent. The strongest part of the core is its separation of 46,316 local assignments from 46,564 official rated-game increments and its retention of zeros, walks, no-deals, timeouts, and role-specific rating changes.

The current core is not yet evidence-safe in five central places. First, the public result row is not bound in a release artifact to the focal Agent 5 identifier. Second, the two final windows are selected and strongly heterogeneous, especially in persuasion, yet are pooled into one mean and one iid game bootstrap. Third, legal action receipt is described as design alignment even though state-conditioned owner conformance is unavailable for most final actions. Fourth, several negative-result numbers lack reproducible denominators or do not belong to Agent 5. Fifth, the planned reproducibility bundle does not yet reproduce the private final-window audit or run the mathematical verifier against an isolated banked checkout.

I found no central arithmetic error in the endpoint or 245-game table, but the major issues below should be resolved before the four-page core is treated as submission-ready.

## Incorrect statements or rules

### Major comment I1

**Topic:** Randomization alone is not a sufficient rule for causal language

- Severity: Major
- Location: Page 1, lines 107 to 113, especially “only randomized comparisons receive causal language.”
- Observation: The stated rule makes randomization sound sufficient for causal interpretation.
- Evidence or criterion: A causal comparison also requires a valid and recoverable assignment rule, treatment isolation, all-assignment analysis, outcome completeness or a missingness strategy, interference assumptions, and an analysis that accounts for stopping and multiple looks. The 91-game clone had an earlier 45-game look, and the persuasion backload analysis initially grouped realized behavior rather than assigned arm and used the wrong activation window. These facts do not make every comparison unusable, but they show why randomization by itself is not the gate.
- Why it matters: This sentence is the paper's global evidence standard. A reviewer can use it to challenge every later use of “randomized,” “interval,” or “lost.”
- Requested action: Replace it with: “The unit of analysis is an assigned game. We use causal language only for prospectively assigned comparisons with recoverable assignment, treatment isolation, complete all-assignment accounting, and stopping-aware analysis; all other contrasts are descriptive or mechanistic.”

### Major comment I2

**Topic:** The score-floor challenger is not Agent 5 evidence

- Severity: Major
- Location: Page 2, line 179; page 4, lines 314 to 315.
- Observation: The core includes a later score-floor challenger that closed 7 of 27 resolved fires as part of the Agent 5 strategy lineage and negative results.
- Evidence or criterion: The Agent 5 scope record states that the score-floor challenger ran on Test 4, never became part of Agent 5, and should be removed from the Agent 5 paper. The 7 of 27 statistic is also a resolved-fire cohort, not an Agent 5 all-assignment denominator.
- Why it matters: A true result from another profile is still the wrong evidence object for an Agent 5-only paper. It makes the negative-result section look broader than the focal-agent record supports.
- Requested action: Remove the score-floor claim from both the lineage table and page 4. If space is needed, replace it with the Agent 5 same-overlay seesaw or the final 19-game negotiation non-agreement census.

### Minor comment I3

**Topic:** The hidden-seller notation calls a multiplier a monetary scale

- Severity: Minor
- Location: Page 2, lines 147 to 156.
- Observation: The text says the seller selects a supported “scale” `\pi`, while the equation uses `B` as the monetary scale and `\pi` as a normalized ask multiplier.
- Evidence or criterion: In the banked implementation, the supported bases are 100, 10,000, and 1,000,000, while the selected targets are grid multipliers such as 1.2 or 1.5.
- Why it matters: The current wording makes dimensional interpretation of the equation unnecessarily difficult.
- Requested action: Change “supported scale `\pi`” to “supported normalized ask multiplier `\pi`,” and define `B` as the monetary base.

## Unsupported claims

### Major comment U1

**Topic:** The public endpoint is not yet bound to Agent 5 in the release evidence

- Severity: Major
- Location: Abstract, lines 57 to 65; page 4, lines 290 to 292.
- Observation: The core attributes the second-place row, 2590.02 rating, 46,564 increments, and family endpoints to the focal submitted agent.
- Evidence or criterion: The frozen public leaderboard CSV contains the numerical row but no public profile identifier or name. The private final-window manifest identifies player UUID `87df5f6b-64d6-437f-914d-23105d15e1bf`, but no release object binds that UUID to the public leaderboard row and to the user-facing name Agent 5. The Agent 5 scope note explicitly records this as a prerequisite for public use.
- Why it matters: The numbers themselves reconcile, but attribution is a provenance claim. Without the binding receipt, a reviewer cannot distinguish a focal-profile result from an account-level or another-profile result.
- Requested action: Add a sanitized binding receipt that records the focal profile identifier, Agent 5 label, public endpoint row, capture time, and hashes of the underlying authenticated responses. If the identifier cannot be released, state that the binding was verified privately by a named procedure and provide a salted or redacted stable identifier.

### Major comment U2

**Topic:** The census and rating polls do not by themselves “trace” strategy mechanisms

- Severity: Major
- Location: Abstract, lines 57 to 62; page 1, lines 107 to 110.
- Observation: The core calls this the agent's “full development” and says 46,316 assignments plus 1,348 polls trace solvers, randomized probes, failed imitation, stalling, rollbacks, and the final router.
- Evidence or criterion: The assignment census supplies games, actions, outcomes, timestamps, and imperfect internal plan fields. The rating polls supply aggregate family ratings. Mechanism chronology comes from separate deployment, source, and overlay records. The first retained rating poll is already after 3,545 cumulative family games, and the lifetime local records cannot be joined row by row to all 46,564 official increments.
- Why it matters: Combining distinct evidence objects into one “full development” claim obscures what is directly observed, reconstructed, or missing.
- Requested action: Use “retained local lifecycle” rather than “full development,” and write that the census and polls were paired with deployment and source records to reconstruct strategy chronology. Do not imply that a poll or every assignment contains a verified policy label.

### Major comment U3

**Topic:** Aggregate action diversity does not establish that behavior matched design

- Severity: Major
- Location: Page 3, lines 261 to 270.
- Observation: The statement “The behavior largely matched design” is supported by bargaining agreement, negotiation walk/trade, and persuasion action-diversity summaries.
- Evidence or criterion: Those summaries show valid returned behavior and outcomes, not whether the correct owner fired in the correct visible state. The manuscript itself reports a stable `plan.component` field for only 220 of 2,288 final actions and cannot reconstruct selected-owner conformance for every turn.
- Why it matters: Agent Behavior Analysis is required to compare designed and actual behavior. Legal action receipt and state-conditioned policy conformance are different claims.
- Requested action: Replace the alignment sentence with: “The receipt verifies that 2,288 local returned actions were valid and reproduced in authenticated service replay. It does not establish state-conditioned owner conformance for all turns. Descriptively, bargaining always agreed, negotiation included both trades and exits, and persuasion used both messages and buyer actions.”

### Major comment U4

**Topic:** The intermediate negotiation “owner” census is not reproducible from a frozen artifact

- Severity: Major
- Location: Page 3, lines 252 to 259.
- Observation: The core reports exact owner counts for 2,499 assignments and 18,033 actions and says these establish which rules owned recorded behavior.
- Evidence or criterion: A read-only recomputation from the local archive reproduces the four assignment and action totals, but the paper bundle contains no frozen CSV, analysis script, boundary manifest, or checksum for this census. The counts are based on internal component labels, not an independent branch-to-wire conformance test.
- Why it matters: This is the core's only large mechanism-level behavior census. Without a reproducible derivation, it is stronger in wording than the final action receipt.
- Requested action: Freeze a script and aggregate CSV with the August 25 activation timestamp, all label mappings, zero missing component labels, and hashes of source inputs. Change “owned” to “was attributed by the logged component label” unless an independent state-to-owner verifier is supplied.

### Major comment U5

**Topic:** The exact LLM conversion percentages lack a complete evidence object

- Severity: Major
- Location: Page 2, lines 127 to 129; page 4, lines 315 to 318.
- Observation: The core reports 46.3 percent conversion for LLM wording versus 55.3 percent for templates and says both were removed.
- Evidence or criterion: The local evidence ledger repeats these percentages but supplies no arm counts, assignment unit, activation window, family cells, model and prompt version, missing outcomes, uncertainty, or frozen reproduction script. Conversation chronology supports that the LLM path ran and was stopped, not the statistical completeness of this exact contrast.
- Why it matters: Exact percentages invite quantitative interpretation that the retained evidence cannot currently support.
- Requested action: Either recover and release the full comparison denominator and derivation, or remove the percentages and say only that a bounded internal comparison favored deterministic templates and the final policy ran LLM-off.

### Major comment U6

**Topic:** The official endpoint does not support the effect of “measured revision”

- Severity: Major
- Location: Page 4, lines 336 to 339.
- Observation: The conclusion says the second-place result “supports the competitiveness of measured revision.”
- Evidence or criterion: The endpoint supports the competitiveness of the resulting adaptive system. It does not identify whether measurement discipline, any specific revision, banking, field drift, matchup composition, or another process caused the placement. The next sentence correctly withholds owner-level causal credit, but the first sentence still credits the revision process.
- Why it matters: This is the paper's final causal impression.
- Requested action: Replace it with: “The second-place result establishes that the resulting adaptive three-family system was competitive in this competition. It does not identify the effect of the revision process or any retained component.”

## Incompletely reported claims

### Major comment C1

**Topic:** The pooled final-window means hide strong temporal heterogeneity

- Severity: Major
- Location: Abstract, lines 65 to 67; page 3, lines 207 to 224 and Table 2(b); page 4, lines 336 to 339.
- Observation: The two operational windows are pooled into one family mean. Persuasion is especially heterogeneous: the mean displayed delta is `+1.632` over 25 rated preclose games but only `+0.00345` over 29 rated closing-window games. The closing window has 30 persuasion assignments, with one timeout. Within role, seller means move from `+2.182` over 11 games to `+0.400` over 11, while buyer means move from `+1.200` over 14 to `-0.239` over 18 rated games. Bargaining also changes from `+0.768` over 19 preclose games to `+1.322` over 152 closing games. Negotiation appears only in the 19-game preclose window.
- Evidence or criterion: These values recompute exactly from the same 245-game authenticated export and local first-action window rule used by the manuscript. The two windows are separated by banking, have different family and role mixtures, and occur in a nonstationary reference pool.
- Why it matters: The pooled persuasion mean of `+0.757` can be read as stable final-policy performance even though essentially all of its net displayed gain comes from the first window. The asymmetry also weakens the conclusion that the final evidence is equally informative across all three families.
- Requested action: Report window-specific rated denominators and means, at minimum for persuasion. Add: “These are selected operational censuses, not a held-out or representative sample; closing play contained no negotiation and the pooled means conceal window heterogeneity.” If space is tight, replace the bootstrap intervals with preclose and close means.

### Major comment C2

**Topic:** The game bootstrap is presented without its dependence and coverage limits

- Severity: Major
- Location: Table 2 caption, lines 221 to 224; all bracketed intervals in Table 2(b).
- Observation: The caption calls the intervals descriptive 95 percent game-bootstrap intervals but does not give the resampling count, seed, exchangeability assumption, or the effect of sequential rating dependence and selected windows.
- Evidence or criterion: The script uses 20,000 iid game resamples with seed 20260831. Displayed rating deltas are sequential state updates in a drifting field, and games across each operational burst can share opponents, configurations, and reference-pool conditions. The two-window mixture is visibly heterogeneous.
- Why it matters: A percentile bootstrap over individual games does not automatically provide 95 percent repeated-sampling coverage under dependence or window selection. The brackets can be mistaken for inferential confidence intervals.
- Requested action: Call them “iid game-resampling summaries,” report 20,000 resamples and the seed in the artifact, and explicitly state that they are not confidence intervals for a stationary population or a policy effect. Prefer window-stratified means or a block/window sensitivity analysis.

### Major comment C3

**Topic:** The final action audit lacks contemporaneous process-to-source provenance

- Severity: Major
- Location: Page 3, lines 278 to 285; page 4, lines 330 to 334.
- Observation: The paper says alignment assurance combined a frozen source revision and overlay with replay receipt, but acknowledges only missing owner conformance.
- Evidence or criterion: The final receipt verifies local returned wires against 2,288 service replay moves and the bank manifests hash 23 source assets and 81 flags. It does not bind every final action to a contemporaneous process image, PID, loaded commit, or pre-coercion candidate. The private receipt explicitly lists process-to-commit and selected-owner provenance as unavailable.
- Why it matters: Exact replay matching proves what left the client and reached the service. It does not prove that all actions were produced by the claimed banked source and overlay.
- Requested action: State this additional boundary in the core. If stronger conformance is desired, provide launch records for both windows, bind PID to commit and overlay, and replay sanitized visible states through an isolated banked checkout to compare returned wires.

### Major comment C4

**Topic:** The hidden one-round seller proxy omits its behavioral acceptance assumption

- Severity: Major
- Location: Page 2, lines 147 to 157, Equation 3.
- Observation: The indicator assigns the seller its ask margin whenever the latent buyer value exceeds the ask and zero otherwise.
- Evidence or criterion: This assumes the buyer accepts every strictly profitable one-round offer. The implementation verifier confirms that this assumption is built into the proxy. Live human and agent behavior has included rejections of positive-surplus offers, so it is not a game rule or universal empirical law.
- Why it matters: Without the assumption, readers can mistake the finite proxy for an exact expected-rank objective or an official cell optimum. The text only disclaims the latter.
- Requested action: Add: “The proxy assumes acceptance iff the buyer's payoff is strictly positive and averages uniformly over the four supported latent buyer values, two message modes, and three monetary bases. It is a design heuristic, not an identified response model.”

### Minor comment C5

**Topic:** The persuasion threshold omits the parameter and behavior regime

- Severity: Moderate
- Location: Page 2, lines 158 to 164.
- Observation: The formula for `q_max` is given as a general one-shot obedience threshold.
- Evidence or criterion: The derivation requires `0 < p < 1`, `u < P < v`, a risk-neutral buyer, recommendation-contingent purchase, all HIGH products recommended, and a fraction `q` of LOW products recommended. The core mentions lack of repeated-game commitment but not these one-shot assumptions.
- Why it matters: Outside the stated regime the denominator may change sign and the clipped expression is not the same obedience characterization.
- Requested action: State the parameter regime and obedient-buying assumption in the sentence introducing the formula. Continue to call it a benchmark, not an optimal repeated-game policy.

### Major comment C6

**Topic:** The clone checkpoint needs its repeated-look and assignment limitations

- Severity: Major
- Location: Page 4, lines 312 to 314.
- Observation: The core describes a randomized 91-game clone, an interval crossing zero, 6.14 percentage points more no-deals, and a negative focal-agent stratum.
- Evidence or criterion: The released deidentified table reproduces candidate `n=44`, mean `+1.1159`, control `n=47`, mean `+0.2468`, difference `+0.8691`, nominal normal interval `[-0.7304, 2.4686]`, and no-deal difference `+6.141` percentage points. There was an earlier 45-game look. The deidentified artifact removes game IDs, so the hash assignment cannot be independently rederived, and the focal stratum mapping is not recoverable from the released labels.
- Why it matters: “Randomized” plus an unqualified interval can imply a confirmatory causal estimate. The defensible claim is that the arm failed a precommitted operational promotion rule.
- Requested action: Say “At a stopped 91-game read after an earlier 45-game look, the hash-assigned clone failed its promotion rule; its nominal unadjusted interval crossed zero, no-deals were 6.14 percentage points higher, and the focal stratum was negative.” Do not call the interval confirmatory.

### Major comment C7

**Topic:** The backload statistic lacks unit, denominator, assignment, and correction details

- Severity: Major
- Location: Page 4, lines 316 to 318.
- Observation: The core says a randomized backload policy lost by `.391 raw-percentile points` in strict profitable cells.
- Evidence or criterion: The retained diary reports `+0.391` on the raw percentile scale for all-push over backload, with interval `[+0.326,+0.455]`, but records a method failure in which realized `q` was initially mistaken for assigned arm. No sample size, arm counts, recovery script, activation boundary, or multiplicity status is frozen in the paper data. The phrase `.391 percentile points` is also ambiguous by a factor of 100 unless the `[0,1]` scale is explicit.
- Why it matters: This is presented as one of the strongest randomized negative results, yet a reader cannot reconstruct the cohort or know whether the quoted estimate is the corrected intent-to-treat result.
- Requested action: Recover the assignment-level cohort and report `n` by arm, salt, T0/T1, all-assignment retention, correction from realized behavior to assigned arm, analysis scale, and stopping rule. Write either `0.391 on the [0,1] raw-percentile proxy scale` or `39.1 percentile points`. Otherwise remove the number from the core.

### Minor comment C8

**Topic:** The 14-trigger high-share audit is selected and retrospective

- Severity: Moderate
- Location: Page 4, lines 309 to 311.
- Observation: “Waiting beat immediate acceptance in all 14 joined triggers by 21.77 pot points” is numerically correct for the Agent 5 stratum but is not labeled as a selected current-stack replay audit.
- Evidence or criterion: The complete pooled audit had 46 exact first triggers, 45 joined, and one unresolved. Agent 5 contributed 14 of the 45 joined triggers. The cutoff was post hoc, and the audit compares a known accept-now payoff with the later observed agreement on trajectories generated under rejection.
- Why it matters: The result is useful mechanism evidence against an override, but it is not an all-assignment policy-effect estimate.
- Requested action: Add “in a retrospective selected-trigger audit” and, if retained, give the full denominator `14 Agent 5 triggers within 45 joined of 46 pooled triggers` or move the pooled details to the artifact.

### Minor comment C9

**Topic:** The four warning failures need their audit denominator and clustering

- Severity: Moderate
- Location: Page 4, lines 320 to 322.
- Observation: The core reports four warnings in one buyer game, all followed by buying LOW products.
- Evidence or criterion: The frozen selector covered four games and 80 buyer decisions; all four misses were clustered in one game. The four turns are not four independent games and do not estimate a population failure rate.
- Why it matters: The example is a strong concrete alignment failure, but its prevalence is uninterpretable without the audit denominator and clustering.
- Requested action: Write: “A frozen selector found four misses among 80 buyer decisions across four games; all four were clustered in one game, and all four purchases revealed LOW.” Keep it as a counterexample, not a rate estimate.

### Major comment C10

**Topic:** The seller credibility failure omits games, missing outcomes, and action selection

- Severity: Major
- Location: Page 4, lines 322 to 324.
- Observation: The core reports 8 conversions among 664 observed targeted LOW recommendations after three passed positives.
- Evidence or criterion: The selector reached 668 LOW recommendation turns across 109 Agent 5 games; 664 target outcomes were observed and 4 were unresolved or unavailable. The repeated turns are clustered by game and action-selected under the deployed all-push policy.
- Why it matters: `8/664` is a localization statistic, not an independent-turn experiment and not evidence that a decline or credibility reset improves later rating.
- Requested action: Report `668 turns in 109 games, 664 observed outcomes, 8 sales`, name the four missing outcomes, and retain the explicit action-selection caveat in the same sentence.

### Minor comment C11

**Topic:** The same-overlay seesaw needs per-family denominators

- Severity: Moderate
- Location: Page 4, lines 325 to 328.
- Observation: The core gives 79 total games and three family rating changes but not each family's exposure.
- Evidence or criterion: The complete cohort is 20 bargaining games, 22 negotiation games, and 37 persuasion games. Bargaining had 20 agreements; negotiation had 9 agreements, 8 no-deals, and 5 walks; persuasion had 37 completions. No terminal was missing.
- Why it matters: Rating changes cannot be compared across families without the number of increments. The unequal family counts also make the total movement an exposure-weighted operational episode.
- Requested action: Add `(n=20/22/37 for bargaining/negotiation/persuasion)` and retain the current noncausal caveat.

### Minor comment C12

**Topic:** The opponent-opening motivation lacks its sampling definition

- Severity: Moderate
- Location: Page 4, lines 299 to 306.
- Observation: The core says three leading profiles opened at `.92` to `1.05` of visible surplus while the focal opening was `.681`.
- Evidence or criterion: The retained rival analysis defines the broader comparison over 157 complete-information games against seven ranked opponents. The top three rows have openings `.970`, `.958`, and `1.050`, while the focal row is `.681`. Per-profile game counts, observation dates, weighting, and uncertainty are not reported in the core. “Visible surplus” should be restricted to complete-information ZOPA share.
- Why it matters: Opponent behavior is an inspiration claim, not causal evidence, but the unit and denominator still need to be reproducible. Without them, a range across profiles can be mistaken for a game-level estimate.
- Requested action: Say “In 157 retained complete-information encounters across seven ranked profiles, the three highest-rated observed profiles opened at .958 to 1.050 of the visible ZOPA, while our observed opening mean was .681.” Add per-profile counts in the artifact and keep the imitation caveat.

### Minor comment C13

**Topic:** The lifecycle eras are retrospective operational segments

- Severity: Moderate
- Location: Page 4, lines 293 to 297; Figure 1 caption, lines 193 to 200.
- Observation: The core reports exact phase endpoints and game counts and calls the figure markers verified runtime boundaries.
- Evidence or criterion: The lifecycle script assigns games retrospectively by first-own-action timestamp into half-open operational eras. It reports zero missing first-action timestamps in the current 46,316-file run, but the manifest hashes only the rating snapshot output, not the raw archive, era census, daily census, or boundary definition. The boundaries are not randomized intervention times.
- Why it matters: The phase counts are valid descriptive segmentation but cannot establish that exposure in a named phase caused rating movement.
- Requested action: Call them “retrospectively declared operational segments,” report zero missing or unparseable assignments, and hash every census output plus the boundary specification. Replace “verified runtime boundaries” with “recorded operational boundaries” unless process receipts are bundled.

### Minor comment C14

**Topic:** The 85-game negotiation snapshot is not independently reproducible

- Severity: Moderate
- Location: Page 3, lines 272 to 276.
- Observation: The core reports 44 negative changes in 85 games, including 21 agreements, and two payoff-versus-rating counterexamples.
- Evidence or criterion: The internal authenticated note records 44 of 44 exact joins for the negative subset, 20 buyer and 24 seller negatives, with 21 agreements, 20 no-deals, and 3 walks. The paper data do not include a deidentified 85-row table or a verifier for these claims.
- Why it matters: The examples are persuasive evidence that payoff and agreement are not rating proxies, but they currently depend on a private hand-curated report.
- Requested action: Release a deidentified all-85-game table with family role, terminal outcome, payoff band, displayed delta, and a frozen join verifier, or describe the examples as private audit cases and avoid implying independent reproducibility.

### Major comment C15

**Topic:** The reproducibility paragraph describes a future artifact, not the current executable boundary

- Severity: Major
- Location: Page 4, lines 330 to 334.
- Observation: The core says receipts preserve source, overlay, aggregates, rating snapshots, final replays, and mathematical checks, then promises production-equivalent sanitized source and verifiers.
- Evidence or criterion: The bank verifier currently passes for 23 banked source blobs and 81 overlay flags. However, the mathematical verifier imports the mutable working tree, which currently differs from bank commit `b54cb33` in seven `glee_agent` files, rather than executing an isolated banked checkout. The final-window verifier requires a 1.65 MB private JSON outside the repository. The lifecycle manifest hashes only one of its outputs. The final-window script succeeds under `.venv/bin/python` but fails under the system `python3` because `zip(strict=True)` requires a newer runtime. No released artifact yet demonstrates production equivalence on the 2,288 audited actions.
- Why it matters: A future release plan is not present reproducibility. “Production-equivalent” is a testable conformance claim, not a synonym for sanitized.
- Requested action: State the current boundary precisely. Pin Python and package versions; run verification in an isolated checkout of the bank commit; hash all aggregate inputs and outputs; provide a sanitized state-action conformance set or signed aggregate receipt; and reserve “production-equivalent” until the sanitized implementation matches every releasable audited action.

### Major comment C16

**Topic:** The replay release plan needs an explicit human-participant governance boundary

- Severity: Major
- Location: Page 4, lines 330 to 334.
- Observation: The core says private replays await data-use approval but does not disclose that the final audit contains human-opponent data.
- Evidence or criterion: The authenticated 245-game export contains 244 agent opponents and 1 human opponent. The human game is a closing-window persuasion game. Raw replays contain transcripts, game IDs, opponent-linked records, private values, and actions. The local `opponent.type` identity-disclosure flag is not a substitute for the authenticated `opponent_type` field.
- Why it matters: Human interaction data can require organizer terms review, institutional review, consent analysis, and stricter deidentification than agent-only traces. A reproducibility release can unintentionally expose a participant even if names are removed.
- Requested action: Add a governance sentence such as: “One of the 245 audited games involved a human opponent. We will not release raw messages, game IDs, opponent-linked records, or private values without organizer and institutional approval; the default public artifact will use aggregates or approved deidentified state-action records.”

## Defensible claims and practices

### D1. The official endpoint arithmetic reconciles

- Severity: Defensible
- Location: Abstract, lines 62 to 66; Table 2(a); page 4, lines 290 to 292.
- Observation: Second in the agent track, third combined, 2590.02 overall, 46,564 official increments, and family values `2804.82/15,639`, `2620.36/15,415`, and `2344.87/15,510` match the frozen post-close row.
- Evidence or criterion: The family game counts sum to 46,564 and the three family ratings average to 2590.0167, displayed as 2590.02.
- Why it matters: The central competition result is numerically coherent.
- Requested action: Retain the values after adding the Agent 5 identity binding described in U1.

### D2. The paper correctly separates local assignments from official increments

- Severity: Defensible
- Location: Page 3, lines 207 to 216 and Table 2(a).
- Observation: The core explicitly states that 46,316 local assignment records and 46,564 official rated-game increments have different units and are not a coverage ratio.
- Evidence or criterion: The local total is 46,079 completed statuses plus 222 failed terminals plus 15 active records. The manuscript does not repeat the stale 99.44 percent coverage calculation.
- Why it matters: This avoids a serious denominator error present in older evidence objects.
- Requested action: Retain this distinction and label the local archive's exact missingness checks as requested in C13.

### D3. The final-window action and outcome totals reconcile exactly

- Severity: Defensible
- Location: Table 2(b), lines 242 to 249; page 3, lines 261 to 270.
- Observation: The table's family assignments, rated counts, zero counts, action totals, and outcomes match the authenticated export and local census.
- Evidence or criterion: There are 245 unique games, 244 rated outcomes, 1 timeout, and 2,288 matched valid focal moves. The family action totals are 1,001 bargaining, 190 negotiation, and 1,097 persuasion. All 245 game IDs and result objects join exactly.
- Why it matters: This is a strong bounded execution receipt.
- Requested action: Retain the receipt but separate it from owner conformance as requested in U3 and C3.

### D4. Failures and zero outcomes are not selected away

- Severity: Defensible
- Location: Table 2 and lines 265 to 276.
- Observation: The core reports six negotiation zeros, three walks, three no-deals, one persuasion timeout, and negative displayed changes despite positive payoffs and agreements.
- Evidence or criterion: These outcomes are present in the complete declared windows and are not conditioned on successful deals.
- Why it matters: This directly addresses the competition's rank-based objective and avoids survivorship bias.
- Requested action: Retain these examples and add window selection caveats rather than weakening the negative evidence.

### D5. The objective algebra is sound within its stated normal-completion scope

- Severity: Defensible
- Location: Page 1, lines 84 to 105.
- Observation: The one-step rating target, empirical-rank reversal, and terminal-offer percentile objective are algebraically correct under fixed adjustment and reference pool, positive learning rate, inactive clipping, and zero rejection payoff.
- Evidence or criterion: The local verifier reproduces the finite rank reversal and rating algebra. The paper already disclaims knowledge of the official opponent adjustment and begins from normal game completion.
- Why it matters: This is an appropriate theoretical motivation for percentile-aware design, not a claim of full official optimality.
- Requested action: Retain it. If space permits, mention fixed game count/display shrink and absence of timeout, inactivity, or missing-game penalties in the one-step equivalence.

### D6. The bargaining recursion and finite policy verification are bounded appropriately

- Severity: Defensible
- Location: Page 2, lines 131 to 143.
- Observation: The finite alternating-offer recursion, parity, and silent Bob acceptance floor match the banked component's finite domain.
- Evidence or criterion: The local theory verifier passes the recursion, parity, and banked P2 owner checks.
- Why it matters: The manuscript does not overclaim a universal equilibrium implementation.
- Requested action: Retain the finite-domain wording.

### D7. The rating trajectory is explicitly descriptive and visually legible

- Severity: Defensible
- Location: Figure 1 and caption, lines 185 to 200.
- Observation: The figure identifies family ratings, UTC time, competition close, and numbered operational events with a complete legend. It states that no marker is an isolated treatment effect and discloses that the first poll follows 3,545 cumulative family games.
- Evidence or criterion: Direct PDF inspection found no clipping, illegible legend, decorative imagery, or unexplained encoding.
- Why it matters: The figure earns its space by showing nonmonotonic family trajectories and limiting causal interpretation.
- Requested action: Retain the figure, subject to the boundary wording and artifact hashing requested in C13.

### D8. The core explicitly withholds component credit for placement

- Severity: Defensible
- Location: Abstract, lines 67 to 69; page 4, line 339.
- Observation: The paper says the evidence gives no component causal credit for placement.
- Evidence or criterion: The adaptive, nonstationary, selected-window evidence cannot identify any one component's effect on final rank.
- Why it matters: This is the correct global causal conclusion.
- Requested action: Retain it and revise the neighboring “measured revision” sentence as requested in U6.

## Priority repair order for the core

1. Bind Agent 5 to the official result row with a sanitized provenance receipt.
2. Replace the pooled final-window performance presentation with window-stratified denominators, especially the `+1.632` versus `+0.00345` persuasion split.
3. Rewrite the alignment claim so that 2,288-action replay receipt is not confused with owner conformance.
4. Remove the non-Agent 5 score-floor result and either document or remove the exact LLM and backload numbers.
5. Replace the randomization-only causal rule and qualify the clone's repeated-look interval.
6. Add the hidden-seller acceptance assumption and persuasion threshold regime.
7. State the process-to-source, private-data, and human-opponent governance boundaries.
8. Make the release artifact executable against the banked checkout and hash every reported aggregate.

These repairs would preserve the paper's strongest contribution: a bounded, failure-inclusive account of how a competitive adaptive agent actually behaved. They would also stop operational receipts, descriptive time series, retrospective diagnostics, and randomized comparisons from being blended into one undifferentiated evidence class.

# Confidential comments to editor

None. This was an author-requested local methods audit, not an official review, and no editorial assessment was requested or made.
