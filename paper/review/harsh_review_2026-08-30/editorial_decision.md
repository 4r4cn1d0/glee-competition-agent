# Harsh Editorial Review of the Current GLEE Paper

## Decision

**HOLD: MAJOR REVISION. The current paper is not submission-ready, and it is not yet Best Competition Paper competitive.**

This is not a verdict that the project is weak. The project has three unusually strong assets: an externally validated second-place finish, a technically interesting rank-sensitive objective, and an unusually candid record of failures and inferential limits. The problem is that the four-page paper currently explains its audit vocabulary more completely than it explains the runner-up strategy, while the audit itself stops before the most important alignment quantity.

If the administrative blockers are cleared and the central evidence chain is rebuilt, I would view the paper as a plausible accept and a possible award contender. If the evidence chain cannot be rebuilt, the paper should be repositioned as a rigorous adaptive-agent case study rather than a validated returned-action audit method.

## Review receipt

The panel reviewed the following frozen materials:

| Object | Receipt |
|---|---|
| Main source | `paper/main.tex`, SHA-256 `997b4680808beef2a4ced875baf377262efbfca65117c4dfa6cc397761ee8646` |
| Technical appendix | `paper/appendix.tex`, SHA-256 `b8af569ddf535074f0f1193bb744734fa0b8696ec50c98658aca194a6cbd60b3` |
| Exact core candidate | `paper/main_core.pdf`, 12 pages, SHA-256 `f64ac2be20db56c434204ddc715833ef0dd81cd744a4578ac29ad5bc5876ac7e` |
| Full internal build | `paper/main.pdf`, 43 pages, SHA-256 `dbd53c11f188a55b0ad42a346a16409776235aaa8f2aecba96323801d6f2622e` |
| Core page structure | Main text pages 1 to 4, references page 5, checklist pages 6 to 12 |
| Visual inspection | All 43 pages of the full build, plus both vector figure PDFs |

The theory/code checker, derived-table checker, artifact-manifest checker, and the artifact's aggregate verifier all passed. Those passes establish internal arithmetic and selected synthetic-policy checks. They do not establish that the banked competition process executed the cited policy end to end.

The panel consisted of separate methodology, game-theory, venue-fit, visual/reproducibility/ethics, and Devil's Advocate reviews. Role separation improved coverage but does not create independent statistical evidence.

## Provisional scorecard

These are author-facing diagnostic scores, not predicted official reviewer scores.

| Criterion | Score | Current assessment |
|---|---:|---|
| Clarity and completeness of agent description | 5/10 | Selected mechanisms are clear, but the full runner-up action policy is not reconstructible from the core. |
| Motivation and insight | 7/10 | The percentile objective and adaptive-system framing are meaningful. The positive insight is buried under audit caveats. |
| Technical soundness | 7/10 | Core equations are sound. Implementation provenance, proxy validity, and one appendix negative-result statement need correction. |
| Agent Behavior Analysis | 5/10 | The 245-game census is real and honest, but it does not measure focal final-policy conformance. |
| Reproducibility | 4/10 | Aggregate arithmetic is reproducible locally. Production equivalence and live action-to-outcome provenance are not. |
| Originality | 6/10 | The integration is interesting, but the audit method lacks a baseline, ablation, or second-system validation. |
| Visual communication | 5/10 | The core is legible but dense and table-heavy. The long appendix has float drift and unreadable tables. |
| Best Paper readiness | 4/10 | Strong ingredients, but no single decisive evidence-backed contribution is yet visible on one pass. |

## What should be preserved

1. **The scoring insight is correct and useful.** The safe-versus-lottery counterexample correctly shows that expected payoff and expected empirical rank can reverse. The paper appropriately limits this to the stated same-cell and fixed-score assumptions.

2. **The core game theory is substantially sound.** The finite alternating-offer recursion, hidden-seller pooled objective, negotiation support bounds, and persuasion obedience threshold survive direct algebraic and code checks under their stated assumptions.

3. **The result is prominent and properly bounded.** Second place is in the abstract and main results. The manuscript does not falsely convert the endpoint into a component ablation.

4. **The negative evidence is unusually valuable.** The failed clone, rating reversals, selected-replay reversal, unreachable gate, treatment leakage, and parser coverage failure are exactly the kinds of lessons that can distinguish this paper from an ordinary competition report.

5. **The paper is candid about causal status.** It repeatedly separates live descriptions, simulations, retrospective diagnostics, randomized probes, and official outcomes. That discipline should remain after the paper is shortened.

6. **The privacy boundary is responsible.** Withholding raw messages, opponent identities, credentials, and operational controls is sensible. The unresolved issue is authorization and ethics classification, not an observed leak in the inspected artifact.

## Strongest rejection case

The strongest rejection is not that the equations are wrong or that the second-place result is unimpressive. The strongest rejection is that the claimed methodological contribution is a returned-action audit, yet the focal final-era evidence does not report whether the returned actions matched the frozen policy that supposedly owned each state.

The main behavior table covers 245 games and 2,288 own actions. It reports action categories and outcomes, but it explicitly lacks owner eligibility and exact conformance for bargaining and negotiation. The separate bargaining result covers 25 pooled games across three profiles. The negotiation result is an 800-game simulation. The persuasion failure covers 80 decisions in four games, with all four misses clustered in one game. These are useful bounded audits, but they are not an end-to-end audit of the focal 2,288 actions.

That gap is decisive because the required Agent Behavior Analysis asks whether actual behavior matched the design and how that alignment was ensured. At present the paper can say:

- what local actions were logged;
- what outcomes were joined;
- that selected branches were reachable in other cohorts;
- that some instrumentation defects were found.

It cannot yet say, for the focal census:

- which owner was eligible on each turn;
- which owner actually won precedence;
- what action an independent specification predicted;
- whether the final post-coercion action matched that prediction;
- whether a fallback or downstream override changed it;
- whether the service received and executed that action.

The paper must either recover that chain or narrow the contribution.

## Submission blockers

### B1. Author metadata is still a placeholder

`paper/main.tex:44-48` and page 1 of the exact PDF still show `Author Name`, `Affiliation`, and `email@example.com`. The track is single-blind, so this is incomplete rather than anonymous metadata.

**Required action:** insert the actual author, affiliation, and contact information, then rebuild and inspect the PDF and its metadata.

### B2. Human-opponent ethics and data-use status is explicitly unresolved

The paper and checklist state that human and agent interactions cannot be separated in the available aggregates and that the applicable determination remains outstanding. Because humans and agents shared the pool, aggregate-only release does not by itself settle the authorization or human-subjects question.

**Required action:** obtain the applicable organizer and institutional determination. Record what data were available, whether opponent type was known, what analysis and release were authorized, what review classification applied, and which privacy controls remain necessary. Do not turn the checklist answer into Yes until that determination exists.

### B3. The Overleaf project can compile the wrong document

The current local core candidate is safe at 12 pages, but the supplied Overleaf bundle contains `main.tex` as the root and omits `main_core.tex`. Its default root can compile the 43-page internal report. The workshop call explicitly exempts references from the four-page limit but does not clearly authorize a 29-page technical appendix.

**Required action:** make the Overleaf default `main.tex` produce the exact submission-safe package. Move the long build behind a clearly named `full_report.tex` or separate project. If a technical supplement is intended, obtain written venue guidance first.

### B4. Review-time artifact status is not settled

The narrow artifact is engineered well but remains local, non-production-equivalent, and unable to verify private joins or service receipt. A camera-ready promise does not support review-time claims.

**Required action:** use an organizer-approved anonymous artifact channel if one exists. Provide a stable version, checksum, exact command, expected output, and claim-to-check map. If no channel exists, narrow every claim that depends on production-source equivalence.

## Major scientific findings

### M1. The core does not explain the actual runner-up strategy completely

The strategy section presents representative mechanisms, not the complete returned-action function.

- Bargaining omits the generic discount-dependent acceptance floor, unknown-horizon quadratic glide, fitted Bob expected-percentile offer optimizer, its precedence after the 61 percent cap, integer rounding, the exact-cent exception, and the legal fallback.
- Negotiation gives the hidden-seller pooled objective in detail but does not compactly state the selected operational multipliers and the full precedence of structural owners and fallbacks.
- Persuasion omits the buyer's exact ordered policy: posterior money gate, 0.75 tight-cell threshold, 0.65 prior fence, reversible credibility reset, then the final decline veto.

This imbalance makes a secondary hidden-seller derivation more reproducible than the agent that earned the result.

**Required action:** replace generic audit machinery with a compact final-policy table. For each family, report observable trigger, owner precedence, exact action rule or path, retained state, postguard, fallback, and evidence class. Put full constants and pseudocode in an authorized artifact or appendix.

### M2. The Agent Behavior Analysis does not estimate focal-policy conformance

The manuscript defines

`C = number of returned actions equal to the independent specification / number of eligible audited actions`,

then states that the aggregate census does not supply the denominator. This is an honest admission, but it leaves the required alignment question only partly answered.

**Required action:** for the complete 63-game close cohort at minimum, and preferably all 245 final-window games, reconstruct per owner:

1. eligible states;
2. selected-owner states;
3. independently recomputed intended actions;
4. exact post-coercion matches;
5. downstream overrides;
6. legal fallbacks;
7. local errors;
8. unresolved records;
9. joined outcomes.

Every proportion must print its raw denominator. If recovery is impossible, call Table 2 a returned-behavior census and describe the audit as sampled reachability evidence, not final-policy alignment.

### M3. Four distinct evidence populations are rhetorically too close

The paper moves among:

- the 46,564-game adaptive endpoint;
- the selected 245-game final-profile windows;
- auxiliary reachability and parser audits;
- the 91-game randomized clone checkpoint.

These populations answer different questions. The 245-game census is about 0.53 percent of the 46,564-game focal-profile history and is intentionally selected around final windows. It is not a representative sample of the adaptive trajectory. The 25-game bargaining audit is pooled across profiles. The negotiation audit is simulated. The four-game persuasion result is a bounded clustered failure case.

**Required action:** name each cohort once, give its selection rule, denominator, unit of analysis, and permitted inference, then keep those labels unchanged. Do not let the abstract imply that one deterministic frozen policy played all 46,564 games.

### M4. The implementation verifier checks a mutable working tree, not the named banked commit

`paper/analysis/verify_theory_code.py` places the repository root on `sys.path` and imports the current `glee_agent` modules. The manuscript names banked commit `b54cb33ad9f4fe7da4c667262eee00ffaeac3ab6`, but the current working tree differs from that commit in seven strategy-related files, with 374 insertions and 8 deletions. A green check can therefore validate code that was not banked.

**Required action:** make the verifier import from an isolated checkout or extracted blobs of the banked commit. Assert file hashes before import. Test the selected policy through dispatch and final legal coercion, not only helper functions.

### M5. The endpoint validates the adaptive account, not the final frozen policy

Second place is strong external evidence for the participant trajectory. It is weak evidence that the final profile or any named component caused that endpoint. The paper says this correctly in places, but the abstract's phrase `deterministic, LLM-free agent whose focal profile played 46,564 games` can still sound like one fixed policy generated the whole record.

**Required action:** scope deterministic and LLM-free to the audited closing configuration. Describe the 46,564 games as an adaptive multi-era trajectory. Use the final windows for behavior description, not efficacy attribution.

### M6. `Rank-aware` is more strongly validated as motivation than as an empirical construct

The paper establishes that rank can reverse payoff ordering. It does not establish that each local proxy tracks the official adjusted target well enough to call the full policy rank-optimizing. The bargaining proxy pools seats and omits discounts and message mode. The official opponent adjustment and tie handling are undisclosed.

**Required action:** either validate predicted local-rank gain against recoverable official game targets by exact configuration and role, with held-out data, or narrow the wording to `rank-motivated` and `coarsened raw-rank proxy` wherever appropriate. The title currently overstates how much of the system is empirically shown to optimize rank.

### M7. The 91-game clone checkpoint should carry almost no inferential weight

The point estimate and nominal interval are arithmetically correct. The experiment had two looks, missing assignment receipts in the release, 14 recovered joins, a moving comparison pool, possible repeated opponents, and sequential rating-state carryover. Rating change is not a clean independent outcome because the current rating enters the next update.

**Required action:** keep the clone as a failed operational checkpoint in one or two sentences. Do not give it a figure. If reanalyzed, prefer the closest recoverable per-game adjusted target or percentile, use the actual randomized assignment, account for repeated opponents or series where possible, and describe any interval after repeated looks as nominal and descriptive.

### M8. Lifetime missingness is hidden by a summary percentage

The evidence flow is:

- 46,564 public rated games;
- 46,316 local per-game records, so 248 are absent locally;
- 46,301 canonical terminal joins, so another 15 are unresolved;
- 263 public games therefore lack a canonical local final.

The 99.44 percent shorthand obscures the two different missingness stages and their possible selection mechanisms.

**Required action:** report the full flow and characterize the 263 missing or unresolved games by family, era, and any observable reason. Do not assume they are ignorable.

### M9. The audit contribution is not yet validated as a general method

Eligibility, ownership, post-coercion logging, frozen manifests, and claim-evidence bookkeeping are useful. The paper has no conventional observability baseline, audit-element ablation, second competition, or independent deployment check showing what this contract catches beyond a standard experiment pipeline.

**Required action:** choose a defensible claim level. Either add a compact baseline or concrete error-catch ablation, or say that the novelty is the documented integration and lessons from one competitive system. Transfer should remain a hypothesis.

### M10. The appendix contradicts the authoritative negative-result record

`paper/appendix.tex:1374` says faster concession had an invalidated measurement and holdouts disagreed on direction. `.ai/FINDINGS.md:188-200` says the corrected two-seed result remained negative at -0.0166 and -0.0182, with lower close rate; only the earlier magnitude was overstated.

**Required action:** correct the appendix before any release. State the corrected negative result and the overlay-bug history precisely. This is a factual inconsistency, not a style preference.

### M11. The paper's narrative hierarchy is backwards for an award submission

The current core contains four tables and no figures. Tables 1 and 4 repeat evidence-status concepts. Table 3 is a one-row result table. The abstract is 247 words and devotes substantial space to denominators and caveats. The conclusion ends as a compliance inventory.

**Required action:** make the hierarchy:

1. what the runner-up agent did;
2. why the rank-transformed objective changed its design;
3. what the returned-action evidence establishes;
4. what failed and what was learned.

The audit should discipline the evidence, not become the protagonist.

### M12. The claim-evidence matrix does not currently pass its own validator

The current matrix has 31 claim rows. The peer-review validator stops at CSV line 32 because `CLAIM-HIDDEN-REPLAY-001` uses `alignment_issue=reproducibility`, which is not in the permitted schema. The allowed labels are causal language, direction, magnitude, none, other, outcome, population, scope, selective reporting, timepoint, and uncertainty.

This does not show that the hidden-replay statement is false. It shows that the internal QA object presented as a safeguard is not currently machine-valid.

**Required action:** choose the intended permitted category, probably `scope` or `other`, rerun the validator, regenerate the validation receipt, and confirm that the receipt covers all 31 current claims rather than an earlier subset.

## Section-by-section review

### Title

`Rank-Aware Routing and Returned-Action Audits in GLEE` accurately names two ideas but hides the strongest external fact and overstates the empirical validation of both `rank-aware` and `audits`.

A better direction is `Building the Runner-Up GLEE Agent: Rank-Motivated Strategy and Returned-Action Evidence`. If complete conformance is recovered, `audit` can return to the title. Do not use `winning` because the result was second place.

### Abstract

The abstract is self-contained and correctly defines GLEE, but it is overloaded. It needs one problem, one strategy idea, one official result, one behavior denominator, one failure, and one lesson. It does not need family-by-family outcome counts, both board placements, and the full persuasion failure chronology.

Mandatory corrections:

- scope deterministic and LLM-free to the audited closing configuration;
- distinguish the 46,564-game adaptive account history from the 245-game focal census;
- replace `establish bounded execution evidence` with the exact scope, since final-era conformance is unavailable;
- give the reader a memorable strategy statement, not only router and audit language.

Target 170 to 200 words.

### Objective and contribution

Keep the rank-reversal example, but compress it. The equation and finite example already carry the point. The contribution paragraph should not lead with an implementation-linked claim until the implementation verifier is banked-commit safe.

State explicitly whether the paper is primarily:

- a competition-agent case study with a novel evidence discipline; or
- a generally reusable audit method.

The present evidence supports the first more strongly.

### Adaptive strategy

This section needs a final-policy map in table form, not a decorative architecture diagram. Each row should answer: when does this owner act, what exact action does it return, what can replace it, and what evidence supports it? The hidden-seller equation should move to the appendix if space is needed for the generic bargaining and persuasion paths that actually complete the policy.

### Agent Behavior Analysis

This should remain the empirical center of the paper. Its strongest feature is that it keeps no-deals, walks, zeros, timeouts, and unresolved records. Its largest weakness is that action categories are too coarse to diagnose designed behavior and its conformance denominator is missing.

Report the persuasion failure at the game level as well as the turn level: one of four games contained all four misses. Do not imply 80 independent decisions. Qualify `complete census` as complete local assignment/action records, not complete execution receipt.

### Competition result and failures

State the final placement and ratings in text or on the rating-trajectory figure. Delete the one-row result table. Keep the rating seesaw because it demonstrates why adaptive chronology is not attribution. Keep only the most diagnostic negative results in the core:

1. the clone failed its promotion rule;
2. the selected hidden-offer replay reversed after fixing the denominator;
3. the parser missed an obvious warning pattern.

Move other failures to the appendix or artifact. The clone should be shorter than the denominator reversal because the latter is the clearer scientific lesson.

### Conclusion

The conclusion should not finish with licensing, privacy, and checklist language. End with three concrete lessons:

1. percentile scoring changes the relevant risk tradeoff;
2. observable state determines where structural rules are trustworthy;
3. adaptive competition agents need evidence at the returned-action boundary before outcome stories are believed.

Then give one sentence on the central limitation: final-era conformance and component causality remain unresolved.

### Appendix and checklist

The 29-page appendix is not reader-edited. It contains 19 propositions, dense policy and evidence tables, two pages of repository paths, and serious float drift. If an appendix is authorized, cut it to about 8 to 12 pages and order it by reviewer need:

1. score assumptions and the rank reversal;
2. complete final-policy specification and precedence;
3. expanded behavior evidence and forensic cases;
4. selected negative studies and identification limits;
5. reproducibility, ethics, and release boundary.

Move file manifests to the artifact README. Collapse elementary propositions into direct derivations. Keep only formal statements that support claims in the four-page paper.

The checklist is part of the submission. Reconcile its compute, asset-license, ethics, human-opponent, and development-time LLM answers with the manuscript before upload.

## Claim audit

| Claim | Current status | What would strengthen it |
|---|---|---|
| Expected payoff can rank policies differently from expected empirical percentile | Supported under stated assumptions | Keep exact assumptions adjacent to the example. |
| The core bargaining, negotiation, and persuasion equations are mathematically correct | Supported under stated models | Preserve model boundaries and avoid presenting heuristics as equilibrium. |
| The participant account was competitive and finished second | Supported by the post-close board snapshot | Archive a durable organizer-authenticated source. |
| The final frozen profile caused second place | Not supported, and mostly disclaimed | Requires a frozen-policy evaluation or valid ablation. |
| The 245-game census describes local returned behavior | Supported for the retained local windows | Preserve the local-record and timeout boundary. |
| The final policy behaved as designed across those 2,288 actions | Not established | Recover owner/action conformance and deployment provenance. |
| The full agent is rank-aware | Partly supported as motivation and for selected proxies | Calibrate proxies against recoverable official targets or narrow wording. |
| The returned-action audit is a generally validated method | Not established | Add a baseline, ablation, second system, or narrower case-study claim. |
| The clone improved performance | Not supported | It failed promotion; retain only as a negative experiment. |
| Faster concession had unresolved sign | Contradicted by the authoritative findings ledger | Correct the appendix to the retained negative result. |
| The artifact reproduces the live competition evidence | Not supported | It reproduces aggregates and selected fixtures, not private provenance or production equivalence. |

## Best Competition Paper test

To become a credible award candidate, the revised paper should let a reviewer answer five questions after one read:

1. What did the runner-up agent actually do in each family?
2. What is the one technical insight beyond ordinary competition engineering?
3. What live evidence shows that the intended policy reached the returned action?
4. Which conclusions are causal, descriptive, simulated, or unresolved?
5. What can another researcher reproduce at review time?

The current paper answers questions 2 and 4 best, question 1 partially, and questions 3 and 5 incompletely. Adding more theory will not fix that. The highest-value work is reconstructing conformance, publishing the strongest permitted policy artifact, and rewriting the core around the agent rather than the audit vocabulary.

## Final recommendation

Do not submit the current PDF. Clear the author and ethics/data-use blockers, make the Overleaf root safe, and decide whether final-era conformance can be reconstructed. If it can, the paper has a credible path to a strong accept and a serious award case. If it cannot, narrow the title and claims, present the work as a rigorous runner-up case study, and make the missing link explicit rather than implying a complete audit.
