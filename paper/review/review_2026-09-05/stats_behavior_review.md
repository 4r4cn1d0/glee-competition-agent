# Empirical evidence and Agent Behavior Analysis: author-side working draft

This is an authorized, local author-side review of the September 5 revised manuscript, not an official venue review or editorial decision. The author remains accountable for checking and submitting the work. I used the peer-review skill after validating the existing intake as `READY_FOR_LOCAL_REVIEW`; scope and confidentiality declarations are in `scope.md`. My remit was statistics, denominators, all three families' behavior analysis, experiment flow, lifecycle evidence, and reproducibility. The coordinator and other readers cover page layout, mathematical correctness, production-code semantics, and citations. Separate AI passes do not supply independent human corroboration. Human-data governance remains outside this reviewer's determination.

# Comments to authors

## Overall assessment

The revised manuscript supports a useful descriptive competition report. It now distinguishes the evolving account's result from the final policy, separates the 46,316 local assignments from the 46,564 official rated games, and places the 245-game execution audit in two explicitly selected windows. The final-policy census is 0.529% of local lifetime assignments, so that separation is consequential. The explicit distinction between owner selection, plan-to-action semantics, and replay receipt is unusually helpful: the 2,288/2,288 transmission result is real evidence, but its scope is narrower than a complete policy audit.

The empirical claims generally avoid giving policy components causal credit. A new randomized experiment is not necessary to support the report's descriptive claims. Likewise, confidence intervals on every count in a fixed census would add little. The improvements most needed are accurate reconstruction of the historical promotion rule, consistent outcome populations, and precise descriptions of what the available implementation and provenance artifacts reproduce.

One substantive error found during this pass has already been corrected by the coordinator: Appendix F queried normalized seed payoffs at .01 while calling the probe one currency cent. The old table therefore measured 1% of the base. The corrected table queries .01/B, changes every row's derived gains, narrows the title and caption to pooled reference distributions, and passes the new read-only verifier. This is a resolved finding, not an outstanding objection.

## Evidence actually checked

I read the current core, empirical appendices, relevant policy/audit specifications, project state/findings, and the relevant experiment and evidence records. I inspected the lifecycle, clone, final-window join, parser, and derived-table analysis scripts. I did not regenerate the entire lifetime archive, rerun field experiments, use live APIs, or reconstruct all source-to-process provenance.

The following checks were actually executed locally:

- `python3 paper/analysis/verify_derived_tables.py` passed the separate lifetime/official totals, 63-game preclose subset, 245-game union, 244 rated outcomes, one timeout, 2,288 actions, and frozen parser denominators.
- `python3 paper/analysis/analyze_clone_checkpoint.py` reproduced candidate 44/control 47, displayed rating difference +0.869101, SE .816054, normal 95% interval [-.730366, 2.468567], no-deals 13/44 versus 11/47, and profile-standardized difference +.990780. This is arithmetic reproduction, not independent recovery of game-hash assignment or stopping validity.
- I invoked the existing final-window verifier's read-only `load_rows` on the authorized private export and canonical local game files. The export's SHA-256 matched `b777bfc314adb7ec4a522641118a39bebe0fb9153ce98030f8eaa49c8f06ca98`. All 245 one-to-one result joins and all 2,288 valid, normalized replay-action matches passed. The family totals were B/N/P = 1,001/190/1,097 actions. This reuses the provided verifier; it is not an independent implementation of replay actor attribution.
- Recomputed rated family means were B +1.260819, N -.052632, and P +.757407. The preclose/close means in the core also reproduced: B +.768421/+1.322368, P +1.632000/+.003448. Persuasion has 12 zeros among 54 rated games and 13 local zero payoffs among 55 assignments; the latter includes its timeout.
- An additional direct payload count over the 19 negotiation games found 10 initial offers, 170 price-bearing counters, seven accepts, one rejection without a price, and two own walks.
- `python3 paper/analysis/verify_environment_rank_ladder.py --check-manuscript` passed after the coordinator's correction. The script checks the frozen seed SHA-256 `f828dc51501b7473b016b1d9ecc844ba7792128d2a9bcff757265c5404f61505`, 32,403 games, 64,806 role samples, and 1,152 role-keyed reference cells, and recomputes all six pooled table rows using exact midranks. Only this authorized verifier and the present report were added by this reviewer.

## Major comments

### Major comment M1

The registry's claimed failed interval gate is not the interval gate in the recorded protocol

- Location: Appendix C, paragraph beginning “The standard those candidates failed was not nominal” (`appendix.tex:706`); compare the precommitted REG-018 rule in `.ai/EXPERIMENTS.md:1112` and the reproduced clone analysis.
- Observation: Appendix C treats the displayed-rating interval [-.78,+2.52] as evidence that the clone failed its precommitted interval gate. The archived promotion rule requires a positive displayed-rating **point** difference, separately requiring a contemporaneous local same-cell percentile difference of at least +.03 with its 95% interval above -.01. The rating point +.869 meets the first condition. A rating interval spanning zero is not the specified percentile interval test. The later ledger verdict makes the same conflation, so quoting that verdict does not resolve it.
- Evidence or criterion: `.ai/EXPERIMENTS.md:1112–1118` specifies the different endpoints and thresholds. The 91-row released checkpoint and `analyze_clone_checkpoint.py` contain rating changes, but do not reproduce the requisite percentile contrast and interval. The no-deal increase of 6.14 percentage points exceeds the protocol's five-point limit, and the negative focal-profile contrast also fails a separately recorded condition, so promotion can still be ruled out without inventing an interval failure.
- Why it matters: The registry's central contribution is faithful reconstruction of precommitted decisions. Substituting one outcome's interval for another defeats that claim even when the ultimate non-promotion decision remains unchanged. “Three gates failed” is stronger than the supplied record can currently establish.
- Requested action: Print the actual prespecified local-percentile estimate and interval, with their input and selection boundary, if recoverable. Otherwise say that the no-deal and profile conditions failed and that the recorded interval-gate verdict cannot be independently reconstructed from the released checkpoint. Keep the rating CI as a descriptive result. Do not alter the protocol retrospectively to make it match the result.

### Major comment M2

Outcome denominators change silently between the behavior table and the lifecycle table

- Location: Core Table 2, persuasion row (`main.tex:248`); Appendix D Table “Locally recorded assignments and own actions” (`appendix.tex:806–856`), especially the final persuasion zero rate; `analyze_final_window_outcomes.py:225–269` and `analyze_agent5_lifecycle.py:211–286`.
- Observation: The core says 12 persuasion games returned zero, using the 54 rated outcomes. Appendix D says 23.6%, using 13/55 local payoff records, including the timeout's local zero. Both calculations are reproducible, but the paper does not disclose that they answer different questions. Across the lifetime table, the zero-rate denominator is also observed local payoffs, not assignments; 15 assignments lack observed payoffs.
- Evidence or criterion: `final_window_outcome_summary.csv` gives 12/54 = 22.22%; `agent5_lifecycle_era_census.csv` gives 13/55 = 23.636%. The joined export confirms that the unmatched rating outcome is the same persuasion timeout. The lifecycle totals are 46,079 completed records, 222 failed terminals, and 15 active/unresolved records. The code computes `zero_payoff / payoff_observed`, while the displayed table supplies only assignment counts.
- Why it matters: Including failures in an operational census is sensible, and excluding an unavailable rating from a rating mean is sensible. Calling both “zero payoff” without distinguishing populations makes them appear contradictory and conceals how failures and missing outcomes enter the evidence. It also weakens the claim of all-assignment accounting.
- Requested action: State the denominator beside each zero count/rate. For example, report “12/54 rated zeros; one additional timeout recorded locally as zero” in the core, and define the lifecycle rate as zero among observed local payoffs, with failures retained and missing counts stated. Alternatively harmonize both tables on the same well-defined operational outcome while keeping the rating mean explicitly conditional on observed official rating deltas. Do not impute an official rating for the timeout.

### Major comment M3

The reproducibility boundary is honest, but does not yet deliver a runnable frozen final policy

- Location: Core reproducibility paragraph (`main.tex:304–314`); Appendix B “Coverage and verification boundary” (`appendix.tex:599–638`); `paper/README.md` and `paper/ARTIFACT_RELEASE_PLAN.md`.
- Observation: The manuscript correctly acknowledges that the formula verifier imports a later mutable worktree, the asset manifest omits launch/dispatch inputs, and no verifier executes the frozen router, owner selection, and coercion over every audited state. Consequently, the very detailed policy specification can be checked only in pieces; the intended configuration is not yet a reproducible executable artifact. The locally prepared review bundle is explicitly a selected-rule reference implementation, not production-equivalent source, and is not claimed to have reached reviewers.
- Evidence or criterion: Appendix B lists omitted `run_agent.py`, `glee_agent/probes.py`, overlays, inherited environment, and process receipts. The paper's contribution is a concrete routed adaptive agent, and reproducibility is a stated venue criterion. The private 245-game join verifies service correspondence, not the claimed runtime's complete deterministic action function.
- Why it matters: Honest limitation language prevents overclaiming but does not let another researcher implement or check the complete submitted policy. The remedy is an artifact/provenance improvement, not a new experiment or release of participant trajectories.
- Requested action: Provide a nonoperational, version-pinned entry point for the selected frozen policy and its effective configuration/model dependencies, with synthetic or approved sanitized fixtures demonstrating routing and coercion. At minimum run the existing formula checks against the specified frozen commit in isolation, document which branches are covered, and provide a concrete permitted access route for the bounded arithmetic artifact. If that cannot be completed, retain the present narrow claim and identify the unavailable full-policy reproduction as a material limitation; do not describe the planned release as present evidence.

## Minor comments and targeted corrections

### Minor comment m1

The minimum per-era exposure statement excludes the final era

- Location: `main.tex:275–276`.
- Observation: “At least 3,028 assignments per family in every era” conflicts with the final era's 171 bargaining, 19 negotiation, and 55 persuasion assignments.
- Evidence or criterion: Appendix D's four-era table and its input CSV agree on these counts; 3,028 is the minimum only across the three development eras.
- Why it matters: This otherwise concise sentence exaggerates the support of the fixed-policy audit.
- Requested action: Change “every era” to “each of the three development eras.”

### Minor comment m2

The negotiation action table counts a plain rejection as a counter

- Location: Core Table 2 negotiation row (`main.tex:247`).
- Observation: “Offers/counters/accepts/walks = 10/171/7/2” calls all 171 non-accept decisions counters. The actual payloads contain 170 price-bearing counters plus one rejection with no counterprice.
- Evidence or criterion: The direct bounded payload count above reproduces these categories. The existing `final_policy_two_window_census.csv` more accurately says “171 rejects or counters.” Also, the 102 independently recomputed negotiation wires are a subset of the 180 price-bearing actions, not the full set.
- Why it matters: The distinction is behavioral: rejecting without a counter communicates a different action and must not be folded silently into offer generation. It also affects how readers interpret the scope of the wire check.
- Requested action: Use “rejects/counters” for the 171 count or show 170 counters and one plain reject separately. Call the 102 checked wires “owned price wires” so the exact-price and seller-bound checks remain distinct.

### Minor comment m3

The final-era rating summary stops before the settled endpoint used elsewhere

- Location: Appendix D rating narrative (`appendix.tex:858–867`), Figure 1 caption, `agent5_lifecycle_rating_eras.csv`, and `agent5_lifecycle_rating_snapshots.csv`.
- Observation: The appendix ends final-era bargaining at 2,832, from the 11:51:28 preclose poll. The full trajectory and official result end at 2,804.82, from the 12:01:32 settled postclose poll. The era summary's code excludes that final poll because it is after the era's clock boundary. Its first final-era poll also occurs after initial final-policy games, so the first-to-last differences do not cover the whole audit cohort.
- Evidence or criterion: The CSVs reproduce 2,831.94 at 11:51:28 versus 2,804.82 at 12:01:32. Final negotiation is described as “flat at 2,633 to 2,620,” although the full audit's summed displayed deltas are only -1.0 because some initial games precede the era's first poll.
- Why it matters: The lifecycle appendix reads as a decomposition of the final result, but its snapshots omit within-boundary activity and the settled tail. The qualitative conclusion remains plausible; the numerical endpoint attribution is less complete than the prose suggests.
- Requested action: Label these explicitly as the first and last polls strictly inside each era, with timestamps and omitted boundary activity, or include the settled postclose result for the final segment. Do not equate snapshot differences with summed game-level outcome deltas.

### Minor comment m4

The disclosure fraction does not estimate self-play contamination

- Location: Appendix F final paragraph (`appendix.tex:1115–1120`, after the rank-table correction).
- Observation: The paragraph correctly says name matching cannot prove self-play, then says cross-identity comparisons are exposed to contamination “at roughly this rate” (1.9%). That percentage is 565/29,044 among named records, not an estimated self-play rate in all records or in any evaluated cohort. Hidden identities and name collisions prevent that inference. The final sentence, “No analysis in this paper compares development identities,” may mean that there is no direct between-profile performance comparison. That reading is consistent with the clone analysis, but should be distinguished from its use of profile-specific treatment contrasts.
- Evidence or criterion: About half the 57,793 records have undisclosed type/name, and the denominator is the separate archived fleet store rather than the 91-game clone cohort. `analyze_clone_checkpoint.py` reports within-profile candidate-control contrasts and their standardization; this is not evidence that a direct head-to-head comparison of profile performance was performed. Nevertheless, shared opponent histories and own-account games could affect a within-profile randomized comparison too, so the absence of direct between-profile comparison does not settle interference.
- Why it matters: Interference is a cohort- and network-specific concern. A matching-name fraction from another corpus neither quantifies nor dismisses it.
- Requested action: Call 1.9% a matching-name fraction among disclosed records only; say self-play/interference in the analyzed cohorts was not quantified. Clarify that the paper makes no direct between-profile performance comparison, while the clone checkpoint estimates treatment contrasts within profile strata. This is a precision and interference-reporting request, not an allegation that the paper performed an undisclosed head-to-head comparison.

### Minor comment m5

“Seven explicit adverse findings” and “35 failed rules” need to stay separate

- Location: Appendix C (`appendix.tex:647–715`, `746–777`).
- Observation: The disposition table itself appropriately separates A/S/N and totals 7/17/11. Some prose nevertheless describes the program as candidates failing a common standard, even though most were stopped, superseded, or had no terminal efficacy disposition. “The estimate is large and adverse, so its direction is unlikely to reverse under adjustment” also adds an unsupported multiplicity reassurance to the selected REG-023 replay diagnostic.
- Evidence or criterion: The crosswalk's 35-record inclusion convention is explicit, and only seven rows have A disposition. Statistical adjustment does not change the point estimate's sign by itself; it changes uncertainty or evidentiary conclusions. Neither the 35-row count nor a nominal selected-replay CI establishes a family-wise inferential statement.
- Why it matters: The paper's strength is reporting incomplete and invalid evidence without pretending every mechanism received a decisive test. The more emphatic prose obscures that distinction.
- Requested action: Say that no row had a documented successful precommitted promotion, rather than that all rows failed an efficacy standard. Remove the directional reassurance about multiplicity unless an actual defined adjusted analysis is supplied. Retain the descriptive adverse replay estimate and the explicit statement that it is not a component rating effect.

### Minor comment m6

Clarify the reference-cell count and release provenance in Appendix F

- Location: Appendix F (`appendix.tex:1006–1018`, `1060–1067`), `verify_environment_rank_ladder.py`, and the seed artifact.
- Observation: The 1,152 JSON keys include the seller/buyer role in addition to the economic configuration. The core's 960 environment configurations and this seed's 1,152 “configuration cells” therefore use different universes and indexing conventions. The corrected table is a pooled seed diagnostic; it is not a measurement of the live official ranking rule in a specific cell.
- Evidence or criterion: The JSON key format is `negotiation-seed|horizon|information|messages|base|seller_multiplier|buyer_multiplier|role`. There are 576 distinct non-role keys and 1,152 role-keyed distributions. The new table verifier pins this exact artifact but does not independently authenticate the public release or its relation to competition-time pools.
- Why it matters: Precise units and provenance matter particularly in a paper whose motivation is same-configuration, same-role ranking.
- Requested action: Call these “1,152 configuration-role reference cells” and identify the frozen source/version used to construct the seed. Keep the present pooled-distribution caveat; do not present the corrected table as evidence of seller-rule optimality.

## Family-specific behavior assessment and useful optional additions

The Agent Behavior Analysis requirement is addressed, but the depth differs substantially by family. This is an evaluation limitation rather than a request to manufacture causal evidence.

| Family | What is convincingly established | What remains behaviorally unresolved | Proportionate strengthening using existing records |
|---|---|---|---|
| Bargaining | Both roles, all 171 outcomes, complete gate traces, a narrow 30-action/eight-game silent-Bob schedule check, and the 15-game CDF-trigger failure diagnostic. | Generic owner selection, which economic states caused success or failure, and the relation between early demands, discounting, concession, and final allocation. All agreements do not establish good rank. | Add a compact role-by-discount/horizon aggregate or one normalized outcome-complete trajectory showing offer, threshold, accept/reject, continuation, and outcome. Keep the eight-game schedule match and 15-game CDF subset labeled as distinct selected analyses. |
| Negotiation | Complete replay linkage for 19 games, instrumented owners on 190 actions, and bounded exact-price/message/bound checks. The hidden rank-proxy branch is explicitly unobserved. | Only a small preclose sample, no closing exposure, no direct audit of one of the two headline rank-proxy decisions, and 19 hidden generic-seller price wires outside the printed independent checks. | Show the 19-game mix by information and horizon, then a normalized path illustrating one strategy success and one no-deal/walk. Keep claimed findings local to these states; synthetic fixtures can show the unobserved branch without being labeled live evidence. |
| Persuasion | All 55 assignments are retained in the audit, plan/action semantics agree, and four preclose warning-counterexamples are localized to one game. The 668-target shadow is labeled action-selected with 664 observed outcomes. | Plan/action agreement does not independently validate the parser, posterior, credibility reset, or owner. Seller positive/negative totals alone do not reveal whether recommendations were truthful, why LOW was recommended, or how buyer history affected subsequent behavior. The closing text-buyer window was not reclassified. | Add an aggregate seller quality-by-recommendation breakdown and buyer mode/prior-by-buy breakdown, or one normalized interaction demonstrating credibility updates and their limitation. If running the same retrospective parser on closing records, retain its status as a post hoc classifier disagreement, not independent precision/recall or an effect estimate. |

These additions would turn more of the section from execution bookkeeping into explanation of economic behavior. They are optional improvements to an explicitly descriptive report; the absence of randomized component effects is already accurately disclosed. Within a four-page core, one compact substantive behavioral example or small aggregate replacing repeated limitation prose may be more useful than more counts of instrumentation fields.

## Resolved finding: one-cent normalization

The old Appendix F values were reproduced exactly by querying the normalized seed at .01. Correcting to .01/B gives the following true monetary-cent calculations; the coordinator has applied them and the dedicated verifier passes:

| Information | Base | n | Q(0) | Q(.01 currency) | Q(max reference) | Near-zero jump | Remaining span |
|---|---:|---:|---:|---:|---:|---:|---:|
| Complete | 100 | 898 | .381960 | .688196 | .996102 | .306236 | .307906 |
| Complete | 10,000 | 904 | .375000 | .652655 | .999447 | .277655 | .346792 |
| Complete | 1,000,000 | 906 | .356512 | .596026 | .997241 | .239514 | .401214 |
| Hidden | 100 | 904 | .120022 | .240044 | .999447 | .120022 | .759403 |
| Hidden | 10,000 | 900 | .113333 | .226667 | .999444 | .113333 | .772778 |
| Hidden | 1,000,000 | 901 | .110988 | .221976 | .999445 | .110988 | .777469 |

The correction preserves the stated ordering between these pooled information-condition distributions. It does not establish within-cell scale invariance, acceptance probabilities, attainability, or improvement over the implemented seller policy.

## Limits of this working review

The official leaderboard endpoint is reviewed as a frozen recorded claim, not reauthenticated through a live service. The lifetime corpus, historical mechanism firings, 57,793-record disclosure census, all 35 archived dispositions, and 668-target persuasion shadow were not independently re-extracted in this pass. I statically checked their available definitions and provenance and explicitly reran only the bounded checks listed above. I did not assess raw human conversations, publish any artifacts, or decide the applicable consent/ethics status. Ordinary scientific comments are all in this author-facing report; there is no separate editor channel or invented editorial recommendation.

# Confidential comments to editor

Not applicable. The recorded scope is an author-side review with no editor channel. This heading is retained only to make that absence explicit to the review linter; it contains no additional criticism or confidential editorial communication.
