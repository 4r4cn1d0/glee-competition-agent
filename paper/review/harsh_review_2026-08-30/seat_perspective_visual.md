# Reviewer 3: Perspective, Reproducibility, Ethics, and Visual Communication

## Review status and scope

This is an author-facing working review, not an official venue decision. I reviewed the current `paper/main.tex`, `paper/appendix.tex`, `paper/checklist.tex`, the compiled 43-page `paper/main.pdf`, both figure-source PDFs, the Overleaf bundle, the local review artifact, and the current GLEE call and documentation. I visually inspected all 43 PDF pages after rasterizing them at publication resolution. I did not inspect or rely on any other reviewer report.

The relevant track requirements are unusually important here. The current GLEE call allows up to four paper pages with unlimited additional pages for references, specifies the NeurIPS 2026 format and lightweight single-blind review, requires an Agent Behavior Analysis section, and evaluates clarity, technical soundness, behavior and evaluation, reproducibility, and relevance. It does not expressly grant unlimited technical-appendix pages. The official documentation also says that humans and agents share a matchmaking pool, transcripts are private to the two participants, and organizers may release anonymized aggregate data. Those facts materially affect both the submission package and the release plan.

Constraint sources checked:

- [GLEE Call for Competition Papers](https://glee-competition.com/call-for-papers)
- [GLEE rules, games, and FAQ](https://glee-competition.com/docs)
- the retained official NeurIPS 2026 author kit and its local `neurips_2026.sty`

## Bottom line

The underlying project is far stronger than the current submission package. The manuscript is unusually honest about missing causal identification, has a real externally validated second-place result, and contains a well-engineered narrow verification bundle. However, if submitted exactly as the current Overleaf root and checklist, I would recommend rejection on readiness and compliance grounds before debating Best Paper merit.

There are four submission blockers:

1. **The supplied Overleaf root compiles a 43-page paper.** `main.tex:30-40,349-358` defaults the technical appendix on. The Overleaf archive contains no `main_core.tex`; its README explicitly instructs Overleaf to compile `main.tex`. The resulting PDF has 4 main pages, 3 reference pages, 29 appendix pages, and 7 checklist pages. The working archive is fine as an internal editing project, but unsafe as the project from which a submission PDF is exported. The track call only explicitly exempts references from the four-page limit.
2. **The paper is single-blind but still contains author placeholders.** `main.tex:44-48` says `Author Name`, `Affiliation`, and `email@example.com`. This is not an anonymity feature under the selected style. It is incomplete submission metadata.
3. **The ethics checklist says the manuscript should not be submitted.** `checklist.tex:124-127,190-204` answers No on ethics, human-subject handling, and institutional review, and says the classification remains unresolved. This must be resolved by the appropriate human specialist, organizer, and institution. It cannot be papered over by wording.
4. **The central implementation-linked audit claim is not reproducible to reviewers at submission.** The local artifact is good, but it is not available through a review channel, does not contain production-equivalent source, and cannot verify the private action-to-outcome joins or source equivalence. A camera-ready promise is not review-time evidence.

The Best Paper problem is separate. The paper currently reads as a forensic defense of why most conclusions cannot be drawn. That honesty is valuable, but the positive scientific contribution is buried. A reviewer finishes knowing that the authors avoided many inferential mistakes, but not yet carrying one crisp, memorable finding about how rank-aware strategy and action ownership changed a competitive agent. The award is based on scholarly merit, originality, and clarity independent of leaderboard placement. Second place is excellent external validation, but it cannot substitute for a clean scientific story.

### Provisional author-facing scores

| Dimension | Current score | Reason |
|---|---:|---|
| Perspective and contribution clarity | 5/10 | Real idea, but audit caveats dominate the strategic insight. |
| Main-paper visual communication | 5/10 | Legible, but four dense pages, four tables, and no figure. |
| Appendix communication | 3/10 | Valuable content, but 29 pages, severe float drift, and several unreadable tables. |
| Artifact engineering | 8/10 | The narrow bundle executes cleanly and states its boundary honestly. |
| Review-time reproducibility | 4/10 | The bundle is unavailable to reviewers and cannot verify the central production linkage. |
| Ethics and privacy readiness | 2/10 | Raw-data restraint is good, but the required determination is explicitly unresolved. |
| Best Competition Paper readiness | 4/10 | Strong ingredients, not yet a disciplined four-page award submission. |

## What is genuinely strong

1. **Template fidelity is correct.** `paper/neurips_2026.sty` is byte-identical to the retained official style, including SHA-256 `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a`. `main.tex:4` uses the single-blind workshop option required by the call.
2. **The four-page core really is four pages.** In the 43-page working PDF, references start on page 5. The required Agent Behavior Analysis is present on pages 3-4.
3. **The figures have been repaired well.** Figure 1 has panel labels, meaningful axes, a complete legend, direct numerical annotations, and shape and hatch redundancy. Figure 2 has a family legend plus distinct markers and line styles. Both are vector PDFs, all fonts are embedded, and neither depends on color alone.
4. **The paper is admirably explicit about causal status.** `main.tex:280-312` does not misrepresent a moving-field chronology, stopped experiment, or retrospective replay as a causal ablation.
5. **The local review artifact works.** I installed its two pinned direct dependencies in a fresh Python 3.9 environment and ran `verify_all.py`. It passed the 30-file allowlist, 29 manifest digests, a privacy scan over 27 text files, 14 policy vectors, 21 mathematical identities, 17 specification checks, 34 reported claims, three rendered tables, and two figure regenerations. The reported 91-game clone calculations also reproduced exactly.
6. **The privacy boundary is materially better than releasing raw logs.** The artifact excludes messages, opponent identities, game IDs, timestamps, credentials, and operational controls. This is consistent with the official statement that transcripts are private rather than automatically public research data.

## Major findings

### M1. The full Overleaf project and the submission project are dangerously conflated

**Evidence.** `output/overleaf/GLEE_NeurIPS_2026_Full_Paper/OVERLEAF_README.md:7-14` names `main.tex` as the root and says that it compiles the technical appendix. The zip contains only `main.tex`, not `main_core.tex`. `main.tex:34-40` activates the appendix unless `corepaper` is pre-defined. `paper/main.pdf` is 43 pages.

**Why this matters.** A reviewer should never have to infer which root the author meant. Nor should the author depend on remembering a local wrapper that is absent from Overleaf. The call grants unlimited references, not a clearly unlimited 29-page technical report. Generic NeurIPS guidance about supplementary material does not override a track-specific four-page call.

**Required change.** Make the default Overleaf root the actual submission. The safest naming is:

- `main.tex`: four-page core, references, and required checklist only.
- `full_report.tex`: internal long build with technical appendix.
- `technical_supplement.tex`: separate internal report if still useful.

If the organizers explicitly authorize a technical appendix or supplement, preserve that written confirmation and package it exactly as instructed. Until then, do not submit the current 43-page root. Rebuild and visually inspect the exact exported submission PDF after changing the root.

### M2. The required behavior section describes outcomes, but does not establish focal-policy conformance

**Evidence.** Table 2 and `main.tex:213-258` cover 245 games and 2,288 own actions. The table itself says exact owner conformance is unavailable. The separate live bargaining audit covers 25 pooled games and 153 eligible changed actions across three profiles. The negotiation owner audit is an 800-game simulation, not live behavior. The persuasion failure audit covers 80 decisions in four text-buyer games and finds four misses in one game.

**Why this matters.** The required section asks whether the agent behaved as designed and how the authors established alignment. The present answer is only partial:

- It establishes the distribution of returned action types and terminal outcomes in the focal live windows.
- It does not establish which intended owner controlled most of those 2,288 actions.
- It does not establish exact conformance of those returned actions to the declared policy.
- It uses separate cohorts to show that some branches can reach returned actions, but those cohorts do not close the focal-census gap.

This is the most important scientific weakness, not a minor reproducibility footnote. The paper's main methodological contribution is a returned-action audit, yet its central live cohort lacks the audit denominator required by its own contract.

**Required change.** Choose one of two honest paths:

1. Reconstruct a frozen action-level conformance audit for all 2,288 actions, or for a predeclared complete subset, from visible state, selected owner, returned action, and a versioned specification. Report every missing stage and preserve a reproducible aggregate.
2. If reconstruction is impossible, narrow the contribution. Call Table 2 a returned-behavior census, not evidence that the final router behaved as designed. State that the action-audit method was demonstrated in bounded auxiliary cohorts, while focal live conformance remains unknown.

The first path is substantially stronger for Best Paper consideration.

### M3. Review-time reproducibility is below what the central contribution requires

**Evidence.** `main.tex:334-338` and `appendix.tex:1679-1699` correctly state that the bundle does not reproduce private joins, server receipt, or production source. `ARTIFACT_RELEASE_PLAN.md:3-31` says the narrow archive is local and must not be implied to have reached reviewers. `review_artifact/REPRODUCIBILITY_BOUNDARY.md:15-31` says it cannot establish source equivalence, language labels, assignment, service receipt, official placement, or component causality. `LICENSES.md` grants no public redistribution license and lists unresolved data and dependency conditions.

**Why this matters.** The bundle's internal integrity is strong, but the paper's key novelty is not merely aggregate arithmetic. It is the claimed link from strategy intent, through branch ownership and postguards, to returned action. The artifact explicitly cannot verify that link. A future sanitized-source promise may improve the archival record, but it does not help a reviewer judge the present manuscript.

**Required change.** Before submission, ask the organizers which review channel is allowed. Then do the strongest permitted version of the following:

- Provide the current narrow bundle through the approved channel with a stable version, checksum, exact command, and explicit boundary.
- Prefer a sanitized production-equivalent policy snapshot now that the competition has closed, while still removing credentials, fleet controls, raw messages, identifiers, and operational deployment material.
- Include a frozen, non-operational effective-configuration snapshot and a check that the released policy produces the declared actions on synthetic fixtures.
- Provide stable public evidence for the official final board or an organizer-attested snapshot, rather than treating a placed CSV row as independent authentication.
- Freeze transitive dependencies or a container lock. Pinning only NumPy and Matplotlib is not a complete environment record.
- Fix the artifact contradiction: `REPRODUCIBILITY_BOUNDARY.md:13` promises four figures, while the README and verifier produce two.

If the organizers do not permit any artifact channel, the main text must carry more exact policy detail and must narrow every claim that depends on private source equivalence.

### M4. Human-opponent and ethics handling is a live submission blocker

**Evidence.** `main.tex:338-340`, `appendix.tex:1786-1796`, and `checklist.tex:190-204` acknowledge possible human opponents and an unresolved institutional or organizer determination. The official GLEE documentation states that humans and agents share the same pool and that transcripts are private to the participants. It does not promise that all trajectories become public. The checklist answers No on Code of Ethics and explicitly says review remains unresolved.

**Why this matters.** The authors did not recruit participants, but that fact alone does not decide whether analysis of competition interactions involving possible humans is outside human-subjects review, exempt, or subject to another institutional process. The manuscript also reports a one-game persuasion failure in enough temporal and behavioral detail that indirect linkage deserves explicit consideration. Strategic persuasion has a plausible dual-use dimension beyond this benchmark.

**Required change.** Obtain a written determination from the appropriate institutional specialist and organizer before submission. This review is not legal or ethics advice. Then write the result as a factual, past-tense disclosure:

- what data the authors accessed;
- whether opponent type was available;
- what participant terms governed secondary analysis and publication;
- whether the work was determined not to be human-subjects research, exempt, or reviewed, and by whom, to the extent disclosure is permitted;
- what individual-level information was excluded;
- whether the one-game subcohort is sufficiently aggregated to avoid reasonable re-identification;
- why raw messages, exact identifiers, and linkable timestamps remain withheld;
- what limits apply to release and real-world deployment of persuasion policies.

Do not convert an unresolved No into Yes without the actual determination. Do not release raw transcripts on the theory that they will eventually be public, because the current official documentation says otherwise.

### M5. The four-page paper spends space on audit meta-language instead of communicating the strategy and result

**Evidence.** The main paper uses four tables and no figures. Table 3 is a one-row result table. Tables 1 and 4 both map claims to evidence stages. The 244-word abstract contains many denominators, family outcomes, and caveats. The final paragraph at `main.tex:334-343` is almost entirely a reproducibility and ethics boundary. The strategy occupies three dense paragraphs containing many cell-specific mechanics but no concise visual or conceptual summary of the retained design.

**Why this matters.** The paper's defensiveness is now over-corrected. It is possible to be epistemically careful without making every paragraph read like a rebuttal. A Best Paper reader needs to retain three things after one pass:

1. Why rank percentiles changed the optimization problem.
2. What the final adaptive router did across the three game families.
3. What live evidence showed, including one clear success pattern and one clear failure.

The present paper gives the reader all of the caveats but makes those three answers laborious to reconstruct.

**Required change.** Reallocate the four pages:

- Page 1: a shorter abstract, the rank objective, one clear contribution paragraph.
- Page 2: the final strategy at the level of observable routing, with only one representative mechanism per family.
- Page 3: Agent Behavior Analysis, including the live census and audit-coverage boundary.
- Page 4: official result, the rating reversal figure, failed probes, and a conclusion with two concrete lessons.

Delete the one-row Table 3 and state the official rank and final ratings in text or the moved trajectory figure. Replace Tables 1 and 4 with one compact evidence-coverage visual described below. Keep Table 2, because it directly satisfies the required behavior section. Reduce the abstract to one main result, one behavior denominator, one failure, and one transferable conclusion.

The conclusion should not end on a compliance inventory. It should say what future strategic-agent builders should do differently: optimize the competition's rank transformation where supportable, assign decision authority from observable state, audit the postguarded returned action, and treat adaptive field performance as system evidence rather than component causality.

### M6. The technical appendix is not edited as a reader-facing supplement

**Evidence.** The appendix spans PDF pages 8-36 and contains 19 propositions, 16 appendix tables, two figures, long policy-order specifications, two full repository-path manifests, and repeated evidence caveats. Visual inspection found substantial float drift:

- Figure 2 and Tables 10-11 are separated from the prose and subsections that introduce them.
- Tables 14-15 float into the beginning of the Expanded Agent Behavior Analysis.
- Table 18 appears after later Related Work and Reproducibility prose.
- Tables 19-20 consume two dense pages of wrapped repository paths.

The TeX log has no overfull boxes, but it contains many severe underfull boxes and float-placement warnings. The visual result confirms the problem. Table 6 on PDF page 13, Table 10 on page 26, and Table 18 on page 34 have narrow columns that wrap into word-by-word rivers. Tables 19-20 on pages 35-36 are artifact README material, not useful paper tables.

**Why this matters.** A long appendix can demonstrate rigor, but only if readers can navigate it. Here length dilutes credibility because elementary propositions and implementation inventories are given the same visual weight as the strongest behavioral evidence. Float drift also makes cross-references feel broken even when LaTeX references resolve.

**Required change.** If an appendix is authorized at all, cut it to roughly 8-12 pages and order it by reviewer need:

1. exact score/rank assumptions and the one counterexample;
2. executable policy specification and precedence;
3. expanded Agent Behavior Analysis and forensic cases;
4. selected negative results and identification limits;
5. concise reproducibility, ethics, and release statement.

Move the policy and evidence path manifests to the artifact README. Collapse elementary propositions into lemmas or direct derivations. Keep only propositions that support a claim made in the four-page paper. Put `\FloatBarrier` or an equivalent section-level discipline after each major evidence group, and split any table that requires a narrow prose column. Add a one-paragraph appendix roadmap after `\appendix`. Do not solve the density by shrinking fonts.

### M7. The checklist and artifact documents contradict the manuscript in several places

**Evidence.** `checklist.tex:112-115` says host and memory information are absent, while `appendix.tex:1775-1784` reports a 10-core Apple M4 MacBook Air, 24 GB memory, macOS, arm64, Python, and no GPU. `REPRODUCIBILITY_BOUNDARY.md:13` says four figures, while only two are regenerated. `checklist.tex:213-217` says an LLM-generated persuasion-wording comparison affected development but lacks provider, model, prompt, and selection records. `checklist.tex:162-181` leaves asset licenses unresolved.

**Why this matters.** A checklist is part of the submission, not an internal issue tracker. Reviewers will treat these contradictions as evidence that the final audit was not actually run.

**Required change.** Re-answer the checklist only after the paper and artifact freeze. Every answer should be current, factual, and consistent with the exact submitted package. In particular:

- update the compute answer to acknowledge known hardware and list what remains unknown;
- resolve or remove the archived LLM wording comparison, and answer the LLM question according to its actual methodological importance;
- complete the license inventory for the template, code, generated figures, and competition-derived aggregates;
- distinguish honest N/A answers from No answers rather than using No as a placeholder;
- remove all language such as “the authors should” from the final disclosure.

## Visual audit of all 43 pages

| PDF pages | Content | Visual assessment |
|---|---|---|
| 1-4 | Main paper | Technically legible at normal zoom, but extremely dense. Four tables and no figure create a report-like rather than paper-like hierarchy. The section labels help, but the reader receives no visual summary of the adaptive trajectory or audit gap. |
| 5-7 | References | Clean and conventional. URLs and identifiers remain readable. No meaningful space concern because references are exempt. |
| 8-24 | Formal objective and family derivations | Figure 1 earns its space and is publication quality. Several long derivations and policy tables have equal visual weight despite unequal importance. Table 6 is especially difficult because its final column is too narrow. |
| 25-28 | Strategy evolution and selected evidence | Figure 2 is the strongest empirical visual and should not be buried here. It is readable and accessible, but lacks an explicit x-axis label and timezone. Table 10 is overly dense. Float ordering begins to separate tables from their introducing text. |
| 29-34 | Expanded behavior, forensics, related work, reproducibility | This should be the appendix's center of gravity, but it arrives late and is interrupted by floats from earlier sections. Table 18 appears far from its introduction and has an unreadably narrow evidence column. |
| 35-36 | Source and evidence manifests | Two pages of wrapped repository paths. The information is useful for an artifact, but almost none of it is visually usable in a paper. Move it out. |
| 37-43 | NeurIPS checklist | Render is clean and page 43's whitespace is harmless. The scientific and compliance content is not clean: multiple No answers and unresolved determinations are submission blockers. |

Additional production observations:

- Both figure PDFs are true vector outputs with embedded fonts.
- Figure 1 uses color plus markers and hatching. Figure 2 uses color plus distinct marker and line styles. Both survive grayscale reasonably well.
- Captions correctly warn that the examples and chronology are descriptive rather than causal.
- The main PDF is untagged. This is common in the template and not a workshop blocker by itself, but it means captions and surrounding prose must fully describe each visual for accessibility.
- Any revised figure should use at least the current effective text size, preserve vector text, define every abbreviation in the caption, and avoid color-only encodings.

## Figure decisions

I recommend exactly one new figure. I recommend moving and revising one existing figure. I do not recommend any other new visual. This is deliberately conservative because the previous decorative architecture graphic did not earn its space.

### New Figure: Returned-action audit coverage matrix

**Purpose.** Answer the paper's most important reviewer question: where does the evidence actually connect intended policy to returned action and outcome, and where is that link missing?

**Space rule.** This figure must replace Tables 1 and 4 plus their repeated prose. It should not be added on top. Target height is 0.42-0.50 page columns across the full width.

**Panel.** One annotated matrix, not a conceptual flowchart and not a score heat map.

**X-axis columns.** `Audit universe`, `Eligible state`, `Selected owner`, `Returned action`, `Joined outcome`.

**Y-axis rows and exact denominators.**

1. `Focal live two-window census`: universe `245 games / 2,288 own actions`; eligible state `not retained`; selected owner `not retained`; returned action `2,288 logged`; joined outcome `245/245 local joins, 244 rated + 1 timeout`.
2. `Pooled live bargaining owner audit`: universe `25 finalized games`; eligible state `153 eligible actions`; selected owner `not separately reported in released aggregate`; returned action `153/153 changed versus control`; joined outcome `25 finalized, descriptive only`.
3. `Negotiation paired simulation`: universe `800 simulated games`; eligible state `6,188 states`; selected owner `6,188/6,188`; returned action `3,274/6,188 changed`; joined outcome `simulation only, no live effect estimate`.
4. `Pre-close text-buyer selector audit`: universe `4 complete games / 80 decisions`; eligible state `4/80 warnings in 1/4 games`; selected owner `0/4 caught by deployed decline layer`; returned action `4/4 BUY`; joined outcome `4/4 LOW`.

**Encoding and legend.** Every cell contains text. Fill and pattern encode evidence class only: focal live census, pooled live auxiliary audit, paired simulation, fixed-history selector audit, and not retained. Use a colorblind-safe palette plus hatching or border styles. Gray with explicit `NR` should mean not retained. The legend must say that rows have different universes and are not numerically comparable. Do not compute or display a single “coverage percentage.”

**Caption.** Define `eligible`, `selected`, `returned`, `joined`, `NR`, and the causal status of each row. State that changed versus control is not the same as exact policy conformance.

**Data provenance.** Freeze a released `audit_coverage.csv` derived from:

- `paper/data/final_policy_two_window_census.csv`;
- the released aggregate underlying the 25-game bargaining reach audit;
- the negotiation reachability and paired-simulation report underlying the 6,188-state counts;
- `paper/data/persuasion_parser_coverage.csv`.

Add the generator and the CSV to the review artifact, then make `verify_all.py` recompute every cell. If these source counts cannot be frozen and released, do not publish the figure.

### Existing Figure 2: move it to the main paper and revise it

**Why it earns space.** The paper frames the submission as an adaptive endpoint, discusses rating reversals, and reports second place. Figure 2 directly shows that evidence. It is much more informative than the one-row official-result table and a paragraph of checkpoint prose.

**Placement and replacement.** Put it on page 4. Replace Table 3 and the most repetitive chronology sentences. Keep the final official standing in one sentence and label the final point directly.

**Axes.**

- X-axis: exact checkpoint timestamp in UTC, labeled `Checkpoint time (UTC)`.
- Y-axis: `Displayed family rating`.
- Series: Bargaining, Negotiation, Persuasion, using the existing distinct colors, marker shapes, and line styles.

**Annotations.** Mark only authenticated events: pre-close bank and official close. Lines must continue to be described as connections between irregular snapshots, not interpolation. If authenticated cumulative family game counts exist at every checkpoint, add a small bottom rug or segment labels for games played between checkpoints. If they do not exist, do not infer exposure from elapsed time and do not add the rug.

**Denominator and provenance.** The figure contains selected authenticated snapshots, not a complete time series. State that explicitly. Source every point from `paper/data/submitted_agent_rating_checkpoints.csv`; source the final rank and account endpoint from `submitted_agent_leaderboard_snapshot.csv` or an organizer-attested archival source.

### Existing Figure 1: keep it in the appendix

Figure 1 now has a correct legend, explicit axes, panel labels, direct values, and non-color encodings. It explains the payoff-versus-rank counterexample well. It does not need another redesign. In a four-page paper, the rating trajectory and audit matrix answer more consequential reviewer questions, so Figure 1 should remain supplemental.

### Figures that should not be added

- No architecture or router flowchart. The prior version was decorative and encouraged the reader to infer implementation structure without evidence.
- No bar chart of raw action counts across bargaining, negotiation, and persuasion. Those actions have different semantics and denominators.
- No forest plot for the 91-game clone. Its stopped two-look interval is descriptive and underpowered; elevating it visually would overstate it.
- No competitor comparison chart unless organizer-authenticated, same-time, same-metric profile data are available with a defensible denominator.
- No strategy “theory map” unless it replaces an equivalent amount of text and every arrow corresponds to a cited, implemented, and audited dependency. At present it would be another conceptual illustration rather than evidence.

## Reproducibility and release assessment

The artifact deserves credit, but the paper should distinguish four different levels more sharply:

| Level | Current status | What a reviewer can conclude |
|---|---|---|
| Arithmetic reproduction | Strong local PASS | Released aggregate claims and figures are internally reproducible. |
| Synthetic policy specification | Strong but partial | Selected disclosed rules behave as specified on synthetic fixtures. |
| Production-source equivalence | Not established | The reviewer cannot know that the synthetic reference functions equal the deployed source. |
| Live action-to-outcome provenance | Not established | The reviewer cannot re-audit private joins, server receipt, assignment, or language labels. |

This layered framing should replace generic statements such as “the artifact reproduces the paper.” It does not reproduce the live competition. It reproduces selected aggregate arithmetic and a synthetic executable specification. That is still useful if stated precisely.

The release plan should also be updated to reflect that the competition has ended. Keeping raw transcripts, opponent identities, secrets, and live controls private remains justified. Keeping all production-equivalent policy logic private until camera-ready is harder to defend scientifically once the paper makes implementation-linked strategy a central contribution. If source release is still delayed, explain the concrete licensing or governance blocker rather than invoking future competition secrecy.

## Ethics, privacy, and dual-use assessment

The manuscript currently makes three good choices:

1. It does not quote or release private opponent messages.
2. It does not claim to identify human-specific behavior when opponent type is absent.
3. It acknowledges that persuasion and bargaining policies may transfer poorly or harmfully outside the benchmark.

It still needs three concrete additions after specialist review:

1. **Data-governance basis.** Cite the competition terms or organizer authorization governing analysis of own-agent interaction records and publication of aggregates.
2. **Human-opponent handling.** State whether any analyses excluded known humans, whether known-human labels existed, or whether all claims deliberately pool unknown opponent types. State the consequence for interpretation.
3. **Release risk assessment.** Explain why the proposed aggregate thresholds, source release, and parser examples cannot reasonably identify an opponent or enable an operational persuasion system without substantial additional infrastructure.

For the one-game persuasion failure, report only the aggregate denominator and outcome needed to establish the failure. Do not add message text, a precise opponent label, game ID, or more granular timestamp. Consider whether even the exact time window plus unique pattern could be linkable by the other participant, and coarsen it if the organizer or institutional determination advises that.

## Ordered revision plan

### Priority 0: submission blockers

1. Obtain written guidance on appendix allowance and the artifact channel.
2. Make the Overleaf default root compile only the submission-safe PDF.
3. Replace author placeholders and verify all single-blind metadata.
4. Obtain and document the human-opponent data-use and ethics determination.
5. Resolve checklist No answers that reflect unfinished work, and reconcile all factual contradictions.
6. Freeze licenses and the permitted redistribution boundary.

### Priority 1: scientific credibility

1. Reconstruct focal returned-action conformance, or narrow the alignment claim.
2. Make the review artifact available through the approved channel with a checksum and stable version.
3. Release production-equivalent sanitized policy source if permitted, or state why not and reduce source-dependent claims.
4. Authenticate the final leaderboard snapshot through a durable source.
5. Freeze the proposed audit-coverage table as reproducible data.

### Priority 2: Best Paper communication

1. Rebuild the abstract around one objective, one system idea, the second-place result, one behavior denominator, one failure, and one lesson.
2. Move the revised rating trajectory into the main paper.
3. Replace Tables 1 and 4 with the data-driven audit coverage matrix.
4. Remove the one-row result table.
5. Rewrite the conclusion around concrete strategic and methodological lessons.
6. Cut and reorder the appendix, with the expanded Agent Behavior Analysis much earlier.

### Priority 3: final visual and package audit

1. Rebuild from a clean Overleaf import and from a clean local environment.
2. Inspect every page of the exact PDF to be uploaded, not only `main.pdf`.
3. Check figure labels at 100 percent zoom and in grayscale.
4. Confirm that every visual has a legend where encoding is nontrivial and that every caption defines its denominator.
5. Verify that no floats cross section boundaries and no table uses prose columns too narrow to read.
6. Run a final claim-by-claim, checklist, license, privacy, and metadata comparison against the frozen artifact.

## Final assessment

This can become a strong competition paper, but not by adding more material. The paper already contains more theory, forensic detail, and negative evidence than the four-page track can absorb. The route to award quality is subtraction, hierarchy, and one missing piece of evidence: a direct, bounded account of whether the focal final policy selected and returned the actions it was designed to return.

The strongest possible version would make a clean claim: rank-aware routing produced a competitive adaptive system; a complete returned-action audit shows where that system followed its declared policy and where it did not; and failed experiments demonstrate why live rating changes cannot be assigned causally to individual heuristics. The current draft has all three ideas, but only the third is fully visible.
