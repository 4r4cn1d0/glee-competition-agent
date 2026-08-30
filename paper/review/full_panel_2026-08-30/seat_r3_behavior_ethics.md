# Peer Review Report

## Manuscript Information

- **Title:** *Percentiles, Not Payoffs: Strategy and Behavior of a Deterministic GLEE Agent*
- **Review date:** 2026-08-30
- **Review round:** Round 1
- **Criteria binding:** `criteria_binding_unavailable`
- **Calibration status:** `NOT_CALIBRATED`

## Reviewer Information

**Role:** Peer Reviewer 3 — Perspective

**Identity:** Researcher in agent-behavior evaluation and human-agent interaction, specializing in behavior traceability, qualitative failure analysis, privacy, research ethics, and responsible artifact release.

**Focus:** Design-to-action alignment across coherent cohorts; language and parser failures; account/profile integrity; possible human opponents; privacy, dual use, ethics, and artifact-release safeguards. No contract-bound venue-alignment claim is made.

## Overall Assessment

### Recommendation: **Major Revision**

### Confidence: **4/5**

The paper presents a deterministic, LLM-free GLEE agent and an unusually candid account of its deployed behavior, negative experiments, and software failures. Its strongest contribution from this reviewer’s perspective is the separation of configured intent, post-coercion returned action, observed outcome, and causal value. The complete 63-game final-era census, reachability conditions, and parser-failure forensics are valuable foundations for an Agent Behavior Analysis.

The present draft nevertheless does not establish design-to-action alignment across one coherent cohort. Its complete final-era cohort contains mostly aggregate actions, whereas its strongest alignment claims mix 25 live games from three profiles, 800 simulations, 877 replayed games, and a selected 21-game language-failure corpus. More importantly, possible human opponents were present in the shared pool, but the manuscript records no completed institutional or organizer ethics determination and cannot identify opponent type in hidden-identity games. That is an acceptance blocker as written. Five-profile use is disclosed, but “four-account” terminology and possible slot-label contamination leave account and self-play integrity insufficiently resolved. The release plan is privacy-conscious, yet remains promissory, cannot independently verify source-to-server joins, and provides few concrete dual-use controls. These deficiencies are substantial but repairable, supporting Major Revision rather than rejection.

## Strengths

### S1: A behaviorally meaningful execution unit

The paper evaluates the post-routing, post-coercion action rather than treating an enabled flag or intermediate plan as behavior. This is a strong and transferable traceability principle.

**Evidence Anchor:** `text: main.tex §Agent Behavior Analysis "A configured flag is not behavior."`

### S2: A coherent final-era process census exists

The appendix reports all three families, both roles, terminal outcomes, and action totals for a bounded 63-game final-policy era, with complete local records and result joins.

**Evidence Anchor:** `table: appendix.tex Table “Complete census of the final 63-game policy era” — family, role, outcome, and recorded-action totals`

### S3: Failures are localized rather than hidden

The parser analysis identifies the exact interface failure between tri-state parsing and a binary fallback, reports adverse outcomes, and appropriately avoids claiming a rating effect.

**Evidence Anchor:** `text: appendix.tex §Language and credibility state "every purchased quality revealed LOW"`

### S4: Five-profile use is explicitly disclosed

The manuscript states that all five permitted profile slots were used under one participant account and distinguishes the submitted profile from development profiles in pooled analyses.

**Evidence Anchor:** `text: appendix.tex §Archive coverage and the complete final era "We used those five profile slots under one account."`

### S5: The artifact plan practices meaningful data minimization

The proposed release withholds transcripts, game IDs, opponent identities, credentials, operational controls, and quasi-identifying timestamps, while retaining derived reproducibility assets.

**Evidence Anchor:** `text: ARTIFACT_RELEASE_PLAN.md §Material withheld "Raw logs and competition transcripts."`

## Weaknesses

### Critical

#### W1: Human-opponent research lacks the required ethics determination

**Problem:** The shared matchmaking pool can contain humans, including games whose opponent type remains hidden. The authors analyzed interaction histories and strategically deceptive behavior but have not obtained or reported an institutional exemption/review determination or an organizer determination covering secondary research use. Withholding transcripts and avoiding individual-level claims reduces risk but does not determine whether the activity constitutes human-subjects research or whether participants were adequately informed about research reuse.

**Evidence Anchor:** `text: checklist.tex §§Code of ethics/IRB "This draft must not be submitted until that review is resolved"; "No author-side institutional or exemption determination has yet been recorded."`

**Why it matters:** This is a prerequisite for responsible publication, not a post-acceptance formatting issue. Hidden opponent identity also prevents the authors from simply asserting that the analyzed cohorts contain no humans.

**Suggestion:** Before submission or acceptance, obtain and document the applicable institutional or equivalent determination and organizer authorization. Add an ethics statement covering the data source, participant notice or consent basis, likely human inclusion and its identifiable bounds, treatment of hidden-identity games, risks from deception and behavioral profiling, data retention/access, and privacy protections. If the determination requires exclusion of human games, rerun all affected analyses with a defensible exclusion or bounding procedure.

**Severity:** Critical  
**Confidence:** 5/5 — core expertise in human-agent research ethics.

### Major

#### W2: The required behavior analysis does not close design-to-action alignment on one coherent cohort

**Problem:** The paper’s complete 63-game cohort establishes process and outcome coverage, but its strongest family-level alignment claims use different populations and evidence modes: live games across three profiles for bargaining, simulation for negotiation, and replay plus a selected live failure corpus for persuasion. The final-era table supplies coarse actions rather than owner eligibility, firing, conformity, semantic validity, and server receipt for every relevant turn.

**Evidence Anchor:** `table: main.tex Table “Required behavior analysis” — family rows respectively use 25 live games, 800 simulated games, and 877 replayed games plus 21 live games`

**Why it matters:** Design-to-action alignment is a central contribution and a required section of the competition paper. Readers cannot infer whole-agent alignment by composing heterogeneous samples with different profiles, eras, and observation mechanisms.

**Suggestion:** Present a cohort inventory before reporting alignment. For the complete 63-game final era, report deidentified counts by family, role, owner, and profile for: eligible turns, owner fired, returned action changed, action satisfying the stated behavioral invariant, successful server join, semantic failures, and terminal outcomes. Keep simulations and older live audits in separate explicitly supplementary cohorts.

**Severity:** Major  
**Confidence:** 5/5 — directly observable reporting mismatch.

#### W3: The language-failure analysis lacks a semantic-coverage denominator

**Problem:** The 40 missed direct warnings are important, but the manuscript does not report how messages were selected or labeled, the total number of warning and non-warning messages examined, ambiguous cases, false positives, phrase or language coverage, annotation reliability, or performance by disclosed opponent type.

**Evidence Anchor:** `absence: Persuasion behavior reporting — expected a full-cohort message denominator, annotation protocol, phrase taxonomy, and confusion matrix; checked main §Agent Behavior Analysis and appendix §§Language and credibility state/Forensic cases/Expanded Agent Behavior Analysis`

**Why it matters:** “Semantic coverage failed” is justified for the observed cases, but neither prevalence nor parser reliability is estimable. This is particularly consequential when text may originate from humans and the agent converts language into economically harmful purchases.

**Suggestion:** Annotate the complete final-era text-message cohort or a prespecified random sample. Report the sampling rule, annotation categories, annotator procedure and agreement, confusion matrix, abstention behavior, negation/direct-warning subclasses, and human/agent/hidden identity strata where observable. Derived counts can be released without transcripts.

**Severity:** Major  
**Confidence:** 5/5 — core expertise in language-mediated agent behavior.

#### W4: Account, profile, and possible self-play provenance remain ambiguous

**Problem:** The appendix says five profiles were used under one account, but elsewhere calls an experiment a “four-account” clone and reports possible slot-label contamination despite the platform’s no-self-play rule. The manuscript does not explain whether “account” there means profile, host, opponent account, or a separately controlled participant account, nor how suspect records were handled. This is an ambiguity, not evidence that a rule was violated.

**Evidence Anchor:** `text: appendix.tex §§Archive coverage/Competitors and docs/reference/glee-docs.md §§Matchmaking/Fair play "We used those five profile slots under one account."; "Four-account trajectory clone"; "possible slot-label contamination despite the public no-self-play rule"; "One account per participant/team; no multi-accounting or collusion."`

**Why it matters:** Literal author control of multiple participant accounts would raise competition-integrity concerns; imprecise terminology also obscures clustering and dependence across development profiles.

**Suggestion:** Define *participant account*, *agent profile*, *host*, and *opponent account* once and use them consistently. State who controlled every treatment-bearing profile, confirm that all author-controlled profiles belonged to the permitted single account, explain the apparent four-account wording, and report the exclusion or sensitivity rule for suspected slot-label contamination. Obtain organizer confirmation if server-side no-self-play enforcement is part of the evidential argument.

**Severity:** Major  
**Confidence:** 4/5 — the textual inconsistency is clear, but underlying ownership is unavailable.

#### W5: The planned artifact cannot independently verify the paper’s central traceability claim

**Problem:** The artifact is scheduled only for camera-ready release and will reproduce derived calculations, not private live interactions or every source-to-server join. Thus the proposed evidence-contract contribution cannot presently be independently audited at its most consequential boundary.

**Evidence Anchor:** `text: appendix.tex §Reproducibility, assets, and governance "cannot replay private live interactions or re-audit every source-to-server join"`

**Why it matters:** The paper appropriately discloses this limitation, but external verification of returned-action and server-receipt claims remains substantially dependent on the authors’ private ledgers.

**Suggestion:** Release a privacy-preserving trace manifest containing cohort definitions, stable sanitized source IDs, commit and effective-configuration hashes, per-owner reachability and conformity aggregates, join-status counts, and expected verifier outputs. For claims that cannot be publicly checked, obtain organizer or independent escrowed verification and clearly identify which claims it covers. An anonymized review-time snapshot would be stronger than a future-only plan.

**Severity:** Major  
**Confidence:** 4/5 — the limitation is explicit; the adequacy of unreleased assets cannot be assessed.

#### W6: Dual-use and privacy safeguards are not yet commensurate with the stated risk

**Problem:** The manuscript acknowledges clear dual-use potential and plans to publish the complete strategic policy, but the stated mitigation is principally that external deployment is “not authorized.” The checklist nevertheless marks safeguards not applicable. The plan lacks a documented threat model, release-risk decision, misuse cases, enforceable or technical boundaries, aggregate disclosure thresholds, and a reidentification assessment.

**Evidence Anchor:** `text: appendix.tex §Governance and checklist.tex §Safeguards "Strategic persuasion and bargaining policies also have clear dual-use potential."; "The paper does not release a high-risk pretrained model or scraped dataset."`

**Why it matters:** A deterministic policy is not a pretrained model, but that distinction does not eliminate acknowledged risks from manipulating human bargaining or persuasion. Framing alone does not prevent repurposing, while combinations of deidentified host, rating, time, and behavior fields may still support linkage.

**Suggestion:** Add a proportionate release threat model. State foreseeable misuse, risk tier, why open or gated release is justified, excluded operational capabilities, license and acceptable-use terms, abuse-reporting contact, and conditions for withholding high-risk modules. Apply a documented disclosure review to released rows and checksums, including linkage testing, minimum-cell rules where needed, and avoidance of hashes derived from guessable human text.

**Severity:** Major  
**Confidence:** 4/5 — risk magnitude is context-dependent, but the current safeguard inconsistency is explicit.

### Minor

#### W7: Core terminology is difficult for readers outside the codebase

**Problem:** Terms such as “owner,” “bank,” “wire,” “fired,” “overlay,” and V1/V2/V3 are central but not consistently defined at first use.

**Evidence Anchor:** `absence: main and appendix behavior exposition — expected first-use definitions for “owner,” “bank,” “wire,” “fired,” and V1/V2/V3; checked main §§Final submitted strategy/Agent Behavior Analysis and appendix §§Final submitted policy specification/Expanded Agent Behavior Analysis`

**Why it matters:** The argument is decipherable, but readers unfamiliar with the implementation must reconstruct the state machine and version labels.

**Suggestion:** Add a compact glossary or one schematic mapping configuration → eligible owner → plan → coercion/postguard → returned action → server receipt → outcome.

**Severity:** Minor  
**Confidence:** 5/5 — presentation issue directly visible in the manuscript.

#### W8: Human-agent and responsible-agent literature is absent

**Problem:** The related-work section covers game theory, negotiation agents, and logged-policy evaluation, but not behavior traceability, human-agent trust and deception, privacy, or responsible artifact release.

**Evidence Anchor:** `absence: Related Work and references — expected human-agent interaction, trust/deception, behavior-traceability, privacy, or responsible-release scholarship; checked appendix §Related work and references.bib`

**Why it matters:** This limits the paper’s ability to position its evidence contract and governance discussion for readers interested in interpreting agent behavior rather than only economic strategy.

**Suggestion:** Add a short, claim-relevant discussion connecting returned-action auditing and parser-mediated deception to established human-agent evaluation and responsible-release work. Avoid expanding into generic AI-ethics citations.

**Severity:** Minor  
**Confidence:** 4/5 — adjacent literature expertise.

## Criterion-Bound Judgements

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale and scope limit | Decision bearing? |
|---|---|---|---|---|---|
| Originality | Universal originality criterion | MEETS | `text: main.tex §GLEE and the competition objective "an evidence contract that separates policy eligibility, returned-action change, field outcome, and causal attribution"` | The action-bound evidence contract is a defensible systems contribution; no formal venue comparison is available. | No |
| Methodological Rigor | Empirical/case-study design and triangulation criteria | PARTLY_MEETS | `table: main.tex Table “Required behavior analysis” — heterogeneous family-specific evidence cohorts` | Strong audit concepts and one complete process cohort, but no unified owner-to-wire conformance cohort. | Yes |
| Evidence Sufficiency | Universal evidence-coverage criterion | PARTLY_MEETS | `text: appendix.tex §Expanded Agent Behavior Analysis "no lifetime owner-to-wire conformance denominator is available"` | The limitations are candid, but central behavior and parser claims remain only partially externally verifiable. | Yes |
| Argument Coherence | Universal traceability criterion | MEETS | `text: main.tex §Agent Behavior Analysis "what an owner was meant to do, whether it changed the returned action, and whether the resulting policy improved rank"` | The conceptual distinction is clear and consistently limits causal claims; cohort composition weakens execution of the framework rather than its logic. | No |
| Writing Quality | Universal interpretability criterion | PARTLY_MEETS | `absence: behavior exposition — expected accessible definitions of implementation-specific terms; checked main §§Strategy/Behavior and appendix §§Policy/Behavior` | Dense internal terminology impedes non-codebase readers. | No |
| Literature Integration | Universal literature-integration criterion | PARTLY_MEETS | `absence: appendix §Related work and references.bib — expected HCI, trust/deception, traceability, privacy, and responsible-release grounding; checked both surfaces` | Economic and statistical literature is strong; the R3-facing scholarly context is thin. | No |
| Significance & Impact | Universal significance and impact criterion | PARTLY_MEETS | `text: main.tex §Limitations and conclusion "deployed behavior must be audited at the returned action, after routing and coercion"` | The principle is important, but human-facing implications and release risks are not yet sufficiently evaluated. | Yes |

## Detailed Comments

### Title and Abstract

The title accurately signals the scoring insight and deterministic-agent scope. The abstract responsibly calls the behavior evidence “sampled,” but readers could still miss that its highlighted family results come from different cohorts and evidence modes.

### Strategy and Behavior Analysis

The configured-intent → returned-action → outcome → causal-value separation is excellent. The analysis should be reorganized around explicit cohort definitions, with the complete final era used for the primary alignment claim and simulations/replays clearly secondary.

### Language and Human-Agent Interaction

The parser forensic case is one of the manuscript’s strongest qualitative results. It needs a corpus denominator and annotation protocol before it can support a broader semantic-coverage conclusion.

### Competition Outcomes

The authors are commendably cautious about leaderboard causality and moving-percentile effects. Development profiles should be treated as clustered, author-controlled experimental units rather than independent agents.

### Governance and Artifact Release

Data minimization is thoughtful, but the ethics determination and release-risk decision must be completed, not left as future checks. The promised `theory_code_audit.md` was outside this reviewer’s permitted evidence set and could not be evaluated.

### References

Coverage is strong for economic theory, automated negotiation, persuasion, and policy evaluation. Add narrowly selected HCI and responsible-agent references supporting the manuscript’s behavior-analysis and governance claims.

## Questions for Authors

1. What institutional or equivalent determination and organizer authorization cover analysis of games that may include human opponents, including hidden-identity games?
2. Can the authors report owner-level eligibility, firing, returned-action conformity, server-join, and semantic-failure counts for the complete 63-game final-policy cohort?
3. Does “four-account trajectory clone” refer to four profiles within the permitted participant account, four opponent accounts, or four author-controlled participant accounts? How were suspected slot-label contamination and possible self-matches audited?
4. What concrete privacy and dual-use review will determine whether each planned artifact component is released openly, modified, gated, or withheld?
