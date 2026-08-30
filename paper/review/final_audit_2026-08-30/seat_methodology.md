# Final methodology audit

## Scope and checks performed

I reviewed the five-page submission PDF and the corresponding source, including the technical appendix included by the full `main.tex` build. I also checked the current claim matrix, theory-code audit, released aggregate data, and analysis scripts. I did not inspect operational logs, controls, or running processes.

The arithmetic that is actually exposed is internally consistent. I reproduced the anonymous artifact with `python3 verify_all.py`, which passed its allowlist, manifest, privacy, dependency, mathematical, table, clone, and figure checks. The repository checks `paper/analysis/verify_derived_tables.py` and `paper/analysis/verify_theory_code.py` also passed. Visual inspection of all five PDF pages found no clipping or unreadable tables.

## Findings requiring revision

### 1. Major: the central replay reversal is neither mapped nor reproducible

The main paper gives a selected 352-decision estimate of `+.07138`, a corrected 375-exposure estimate of `-.06628`, and a nominal interval of `[-.08183,-.05096]` (`paper/main.tex:284-290`). The appendix adds 156 changed decisions, a 4,050-game cohort, and a cohort average of `-.00614` (`paper/appendix.tex:1370`). The private experiment ledger repeats the result and says the interval is a bootstrap interval (`.ai/EXPERIMENTS.md:1391-1401`).

No row in the 30-row `paper/review/claim_evidence_matrix.csv` covers this accept-all-profitable replay. The only released registry entry merely points back to the private ledger (`paper/data/experiment_registry_crosswalk.csv:24`). The anonymous artifact contains neither replay inputs nor an analysis script, and `data/reported_claims.csv` omits all of these numbers. Its stated boundary explicitly says it cannot replay opponent responses or estimate unobserved counterfactuals (`paper/review_artifact/REPRODUCIBILITY_BOUNDARY.md:14-28`). The appendix also acknowledges that resample count, seed, clustering, and selection correction were not preserved for every retrospective interval (`paper/appendix.tex:1127-1133`).

This does not show that the sign is wrong. It means the exact denominator, pairing rule, first-exposure rule, percentile construction, and interval cannot be independently audited from the evidence package, even though the reversal is a prominent methodological example in the four-page paper. Add a claim-matrix row and release a privacy-safe first-exposure or game-level derived table plus the exact analysis, including bootstrap unit, resample count, seed, and selection boundary. If that cannot be done, remove the interval and cohort-average precision and label the result as an unreproduced archival diagnostic.

### 2. Major: the concession-speed claim contradicts its own evidence adjudication

The claim matrix classifies the claim that exponent 1.2 was worse than 2.0 as unsupported because a later clone audit invalidated ask-moving measurements and later holdouts disagreed on the sign. It explicitly requests removal or wording as an invalidated, unproven development result (`paper/review/claim_evidence_matrix.csv:26`). The full manuscript instead states that exponent 1.2 "measured" `-.0166` and `-.0182` (`paper/appendix.tex:1202`) and concludes "Retain slower default" (`paper/appendix.tex:1372`). The review artifact reinforces the contradiction by publishing the two values as `negative_diagnostic` (`paper/review_artifact/data/outcome_summary.csv:11-12`) and checking only their presence, not their validity (`paper/review_artifact/analysis/verify_tables.py:177-182`).

The manuscript must follow the matrix here. Either remove the claim or say that two early diagnostics disfavored 1.2 but later audits invalidated the measurement and left the sign unresolved. "Retain slower default" may be reported as an operational choice, not as an empirically established ranking.

### 3. Major submission precondition: data-use and artifact-release authority remain unresolved

The paper itself says that possible human games cannot be separated in the released final-era aggregate and that an applicable data-use determination is required before submission (`paper/main.tex:313-321`). The artifact separately says that redistribution of the competition-derived aggregate tables has not been authorized and lists permission, licensing, and environment-freeze blockers (`paper/review_artifact/LICENSES.md:3-20`). This is candid reporting, but a declared pre-submission requirement is still unresolved.

Before submission, record the applicable human-participant or data-use determination and permission to distribute the aggregate artifact. Update the availability statement to say what determination was obtained, what material may be shared with reviewers, and what will remain private. If aggregate redistribution is not permitted, do not promise a review artifact that contains those tables.

### 4. Moderate: the claim-to-evidence table does not match two adjacent source claims

Table 3 maps the rating seesaw only to "Authenticated dated checkpoints" and calls it evidence of field drift (`paper/main.tex:295-308`). Checkpoints alone show chronology while both policy and field changed. The source claim also relies on an allegedly unchanged bargaining stack with consecutive fitted windows of `n=471` and `n=498` (`paper/appendix.tex:1229-1238`), and the claim matrix correctly names two evidence objects, `RATING-CHECKPOINTS;UNCHANGED-BARG-WINDOWS` (`paper/review/claim_evidence_matrix.csv:24`). The fitted-window input and calculation are absent from the anonymous artifact. Table 3 also omits the replay reversal immediately above it.

Add a replay row. For the seesaw row, cite both evidence objects and either release the two-window derived calculation or weaken the inference to descriptive rating chronology under joint strategy and field change. Also regenerate the matrix validation: the current CSV contains 30 claims, while `claim_evidence_validation.json` reports only nine (`paper/review/claim_evidence_validation.json:10-29`), so it is stale and does not validate the current matrix.

### 5. Moderate: account, profile, and game-count units are ambiguous in the abstract and result table

The abstract says the system was developed "across 46,383 games and five permitted profiles" and then says the selected profile ranked first among agent accounts (`paper/main.tex:67-74`). In fact, 46,383 is the public count of the focal profile, while placement is for the participant account selected by its best of five profiles. The appendix states this correctly (`paper/appendix.tex:1427-1433`), and the three family counts in Table 2 sum exactly to 46,383 (`paper/main.tex:248-260`).

Use separate units throughout: "46,383 games on the focal profile within a five-profile participant account." State that the account ranked first among eligible agent accounts, while the displayed rating and game counts belong to the focal profile supplying the account maximum. This is a selection-unit correction, not merely stylistic wording.

### 6. Moderate: the 153/153 bargaining denominator omits its required pooled-profile scope

The main paper says only "a pooled 25-game bargaining audit" (`paper/main.tex:223-231`). The claim matrix states that the 153 eligible turns came from 25 finalized games across three in-account profiles sharing a copied stack and specifically requires that scope to be explicit (`paper/review/claim_evidence_matrix.csv:14`). Placed directly after the final-era census, the current wording can be read as a focal-profile or final-era result.

Change the sentence to "a pooled three-profile live audit of 25 finalized games found that the owner changed 153 of 153 eligible returned actions." Keep it separate from the 63-game final-era census and from the 800-game simulation.

## Items that pass the methodology audit

- Final-era denominators reconcile: 19 + 19 + 25 = 63 games and 97 + 190 + 500 = 787 actions. Every negotiation terminal outcome is retained, including three walks and three no-deals. The manuscript correctly calls these live descriptions, not effects, and correctly distinguishes zero logged errors from zero errors (`paper/main.tex:197-231`; `paper/data/final_policy_era_census.csv:2-4`).
- The final-era warning claim uses the full four-game, 80-decision text-buyer slice and limits inference to four counterexamples in one game. It does not turn a post-hoc semantic selector into recall or a causal effect.
- The rating kernel is correct. With `eta=.002`, `1-(1-.002)^19 = 3.73%` and `1-(1-.002)^25 = 4.88%`. The appendix states the necessary no-penalty and inactive-clamp conditions and distinguishes raw from displayed rating (`paper/appendix.tex:58-93`).
- The clone arithmetic reproduces exactly: candidate `n=44`, control `n=47`, difference `+.869101`, fixed-normal interval `[-.730366,2.468567]`, and no-deal difference `+6.141` percentage points. The text discloses the earlier look, the failed frozen promotion rule, one negative stratum, and the lack of assignment re-derivation (`paper/appendix.tex:1272-1282`). Because repeated looks defeat nominal fixed-horizon coverage, "nominal unadjusted normal interval" would be the most precise label, but the current caveat is substantively adequate.
- Randomized and observational language is otherwise disciplined. The appendix makes hash assignment conditional on exogenous game IDs and random-oracle behavior, identifies games rather than turns as the experimental unit, and states consistency and interference assumptions (`paper/appendix.tex:1044-1067`). Replay is explicitly not ITT, rating chronology is descriptive, final-era outcomes are not causal, and best-of-five adaptation is disclosed.
- Selection and survivorship risks are handled well where data are exposed. No-deals, walks, zeros, unresolved assignments, and all exposed replay decisions are retained; agreement-conditioned observations are explicitly rejected as policy-value evidence (`paper/main.tex:233-240`; `paper/appendix.tex:1090-1114`).
- The reproducibility boundary is accurately narrow. The anonymous bundle successfully verifies aggregate arithmetic, the 91-row clone checkpoint, figures, and synthetic policy fixtures, while clearly declining production equivalence, private join verification, assignment re-derivation, and server receipt. The problem is the unmapped central replay result, not overstatement of what the existing bundle runs.

Major Revision. Exact blockers: add an auditable evidence path or materially demote the exact replay-reversal estimates; resolve the concession-speed claim in favor of the matrix's unsupported classification; obtain and document the required data-use and aggregate-redistribution determinations; repair Table 3 and regenerate validation against the current claim matrix; correct the account/profile denominator language; and state the three-profile scope of the 153/153 bargaining audit.
