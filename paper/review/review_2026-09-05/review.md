# Detailed peer review: corrected September 5 draft

Working draft for the author. This is an AI-assisted, author-requested assessment,
not an official review decision or an award prediction. Three separate specialist
passes informed this synthesis, but they are not independent human reviewers.
The coordinating assistant also edited the manuscript, which limits independence.

Scope: the four-page core, references, and Appendices A through F. The reviewed
full build has 22 pages; the core-only build has four main-text pages and one
reference page. The separate technical supplement has 18 pages. No build
includes the removed checklist. Scientific recommendations below remain
unapplied unless explicitly listed as completed corrections.

## Completed corrections

1. Replaced the false claim that the final policy has no learned parameters.
   It now distinguishes absence of an inference-time language model/prompt from
   fixed fitted models and priors, and from within-game history updates.
2. Corrected Appendix D's description of zero-payoff frequency. It is a
   descriptive outcome diagnostic, not the competition's scoring objective.
3. Removed Appendix F's unsupported inference that a large positive-payoff rank
   span makes rank maximization equivalent to money maximization or proves that
   conceding is inferior. The table now describes pooled seed distributions.
4. Found and corrected a further Appendix F unit error during review. The
   source stores payoff divided by base B. The old probe .01 was 1% of B, not
   one currency cent. All six rows, derived spans, and ranges now use .01/B.
   A new hash-pinned, read-only verifier checks the printed table directly.
5. Replaced related work's preliminary-draft and unfinished-work notices with
   an introduction and substantive scope-of-comparison limitations. This is
   not a claim that every literature analogy has been repaired; see M7.
6. Updated the core's A-to-D reference to A-to-F, reconciled the meaning of
   banked/inactive versus intended policy configuration, and refreshed build
   documentation and the separate supplement's title and workshop footer.
7. Removed `paper/checklist.tex` and its inclusion logic. The deletion is
   recoverable from Git history. The official template was not modified.

# Comments to authors

## Overall assessment

The paper has a defensible contribution as a competition system report:
an externally competitive agent, an explicit connection between the scoring
rule and strategic choices, detailed policy specification, and an unusually
careful record of behavior and failure. The inspected central mathematics is
sound under its stated assumptions. The 245-game, 2,288-action replay match
also reproduces under the existing verifier. These are substantive strengths.

It is not yet an award-ready presentation. The obstacle is no longer simply
that the paper lacks rating evidence: the core now reports displayed rating
changes, including unfavorable ones. The obstacle is that several descriptions
of the development process are inaccurate or ambiguous, and the core explains
its evidence machinery more clearly than it explains its strategic agent.
The appendix has enough detail to support a strong report, but contains
smaller specification errors and literature connections that exceed what the
implementation or cited model actually establishes.

I would keep the title if rank awareness remains explicitly scoped to the
competition objective and selected decisions. A new randomized experiment is
not a prerequisite for this descriptive paper. Nor should every fixed census
count receive a confidence interval. The priorities are faithful reporting,
understandable strategy, a useful behavioral lesson in each family, and a
reproducibility route that a reader can actually use.

## Major comments

### Major comment M1

The core makes the removal of imitation sound more complete than it was.

- Location: Core Table 1 and Section 4; Appendix B.3, especially the retained buyer-path lineage paragraph (`main.tex:193`, `appendix.tex:420`).
- Observation: Table 1 lists the leader clone as excluded, and the results say its trial stopped. Appendix B says the stopped randomized package's broad buyer coverage nevertheless remained in the final policy, including its negatively directed hidden unknown-horizon slice. A narrower variant existed but was off.
- Evidence or criterion: All three specialist readers independently noticed the core/appendix distinction. Frozen `b54cb33` routing confirms retained buyer imitation. The issue is not that a failed package experiment identifies the buyer component's causal effect; it does not.
- Why it matters: The paper promises an accurate account of failed strategies and final assembly. Stopping an experiment and removing its policy content are different events. This is also an important lesson about how the submitted system was assembled under imperfect evidence.
- Requested action: Label the excluded item as the randomized whole-policy clone arm, explicitly noting retained buyer imitation. Add one core sentence that the buyer paths survived without a qualifying efficacy result. State the documented rationale if available, but do not invent one or describe the retained component as proven harmful.

### Major comment M2

Appendix C substitutes the wrong outcome into a precommitted gate.

- Location: Appendix C.1, paragraph beginning “The standard those candidates failed was not nominal” (`appendix.tex:706`); archived protocol `.ai/EXPERIMENTS.md:1112`.
- Observation: The paper says the clone's rating interval crossing zero failed its precommitted interval gate. The recorded rule instead requires a positive displayed-rating point difference, plus a separate local-percentile contrast of at least .03 with its 95% interval above -.01. The rating point difference +.869 satisfies the rating-point condition. Its interval cannot substitute for the percentile interval.
- Evidence or criterion: The frozen 91-row checkpoint reproduces +.869 and the reported nominal rating interval, but not the required local-percentile interval. The no-deal increase, 6.14 percentage points against a five-point ceiling, and the negative profile contrast independently violate recorded conditions.
- Why it matters: This is a definite reporting error in the appendix whose purpose is to document the actual decision process. The non-promotion conclusion can remain correct while the stated reasons are wrong. A later ledger repeating the error does not validate it.
- Requested action: Recover the specified percentile estimate and interval, if available. Otherwise report the documented no-deal/profile failures and state that the percentile gate cannot be reconstructed from the released checkpoint. Keep the rating interval descriptive. Remove “failed all three” unless all three correct endpoints are supplied.

### Major comment M3

Reconcile the outcome populations, not just their totals.

- Location: Core Table 2 and Section 4; Appendix D's lifecycle table and rating narrative; `main.tex:248`, `main.tex:275`, `appendix.tex:806`.
- Observation: The core's persuasion zeros are 12/54 rated games, whereas the lifecycle final-era percentage is 13/55 local payoff records, including a timeout recorded locally as zero. The lifetime zero-rate denominator is observed payoffs, not assignments. The core also incorrectly says every era has at least 3,028 assignments per family, although the final era has 171/19/55. Appendix D's final bargaining snapshot is 2,831.94 before close, not the settled 2,804.82 used in the full trajectory.
- Evidence or criterion: The provided aggregate scripts and the bounded 245-game join reproduce these distinctions. They are not unexplained numerical noise. The two zero rates describe different populations, and the era snapshot excludes the final settled poll by construction.
- Why it matters: Precise cohort accounting is central to the paper's credibility. A timeout can appropriately belong in an operational failure census while lacking a rated outcome, but that distinction must be visible. Snapshot changes should not be read as complete game-level rating contributions.
- Requested action: Label zeros as rated versus observed local payoff outcomes, state missingness and failure conventions, and never impute an official rating for the timeout. Change “every era” to “each of the three development eras.” Label era endpoints as first/last polls strictly within the boundary, or harmonize the final segment with the settled endpoint. Also change 171 negotiation “counters” to 171 rejects/counters, or distinguish 170 counters and one plain rejection.

### Major comment M4

The core needs enough vocabulary to explain its own equations and audit table.

- Location: Core Section 2, equations 2–3, and Tables 1–2; Appendix B's definitions.
- Observation: Alice/Bob, M, the persuasion symbols p/u/P/v, owner, gate, and wire are not all explained before they are needed. The core reuses p for different quantities across families. Table 1 uses the same arrow for mutually exclusive rule selection and subsequent transformations, although those have different execution semantics.
- Evidence or criterion: Appendix B defines much of this vocabulary and claims the core is independently readable. The competition evaluates clarity and completeness of the agent description, not just completeness of an attached specification.
- Why it matters: A reader cannot assess alignment between design and observed behavior without understanding which rule selects an action, which component modifies it, and which check establishes only transmission. This is a central comprehension gap rather than cosmetic terminology.
- Requested action: Define each bargaining seat and monetary symbol at first use. Define owner as the selecting rule, gate as a recorded condition, and wire as the final submitted action, or replace these terms with plain language. In Table 1, distinguish “else” selection from “then” modification. Use local notation clearly for persuasion. Recover space by deleting repeated evidence-boundary sentences rather than shrinking the type further.

### Major comment M5

Put the reached strategic mechanism and its lesson ahead of the inventory of evidence.

- Location: Abstract, contribution paragraph, Section 2's two proxy descriptions, and Agent Behavior Analysis.
- Observation: The paper says it contributes a rank-sensitive objective, although that objective is imposed by the competition. The hidden seller proxy gets a full equation in the core but no live state in the final audit. The Bob proxy that actually changed 57 decisions across 15 games is less clearly explained in the method. The abstract enumerates several corpus sizes but omits the most concrete behavioral finding: agreement did not imply positive rating in that selected proxy subset.
- Evidence or criterion: The final audit contains 15 CDF-triggered bargaining games, all agreements, 14 negative displayed changes, mean -4.67. This is a descriptive selected-subset finding, not the effect of activating the gate. The hidden seller proxy has no final-audit exposure. All these restrictions are already in the manuscript.
- Why it matters: The reader needs to leave with an understanding of what was tried, what actually happened, and what that teaches. A long evidence inventory is not a substitute for that insight. Rank-aware design remains a defensible framing if presented as motivation and implementation, not demonstrated superiority.
- Requested action: Change the contribution to formalizing the supplied scoring objective and instantiating two local proxies. Explain the Bob decision in one plain-language sentence: compare predicted acceptance rank and continuation rank, and raise the offer only when the estimated criterion passes its margin. State observed versus unobserved proxy coverage. Consider moving the hidden seller grid sum to Appendix B, retaining its assumptions in the core. Use the freed space for one concrete abstract result and a small amount of substantive behavior analysis across all three families.

### Major comment M6

The reproducibility statements are honest, but the current access route is not enough.

- Location: Core reproducibility paragraph; Appendix B.5; README and artifact-release plan; the GitHub link in the core.
- Observation: The 23-file hash receipt checks intended frozen assets, while the formula verifier imports a later mutable checkout. Effective overlays, inherited environment, launcher/dispatcher inputs, and full source-to-process binding are incomplete. The core's linked repository is private, as confirmed with authenticated repository metadata during this review. The planned sanitized release is not present reviewer-accessible evidence.
- Evidence or criterion: Appendix B explicitly lists the missing inputs. The provided replay verifier reproduces recorded action/server correspondence, not an independently runnable frozen action function. Reproducibility is one of the competition's stated review criteria.
- Why it matters: Detailed prose and a private hash receipt help an authorized local audit but do not give a reader a runnable system. Releasing raw messages or participant identities is neither necessary nor appropriate as the default remedy.
- Requested action: Supply a nonoperational pinned policy entry point, sanitized effective configuration and fitted assets, dependency versions, and approved synthetic fixtures. At minimum, run formula checks against the specified frozen commit in isolation and expose a permitted bounded arithmetic artifact. If full reproduction cannot be provided, preserve the narrower claim and state the access restriction explicitly. Do not imply that a private URL is a reader-accessible supplement, and do not publish private materials without authorization.

### Major comment M7

Related work now reads as finished prose, but several connections remain technically too strong.

- Location: Appendix E.1, E.3, E.4, and E.6.
- Observation: Admati–Perry's delay-signaling model is called the theoretical content of an empirical patience clock; repeated play is said to remove commitment; the reset is called a fixed counter rather than a history-order rule; EGTA is characterized as taking ranking as its primitive. The split-the-difference discussion points to a registry rather than an offer-level diagnostic. The distinction between transmission and correct policy selection is presented as something the paper adds, although it is a known limitation of tracing.
- Evidence or criterion: The specialist source checks confirmed the recent citations exist and match their metadata. The problem is claim relevance and scope, not fabricated references. Admati–Perry concerns endogenous delay as a signal; EGTA concerns empirical game construction/analysis; alpha-Rank supplies a different population ranking. The fixed persuasion reset compares the latest decline with the latest purchased LOW. See the linked literature review for primary-source URLs and precise locations.
- Why it matters: The theory should illuminate the actual implementation. Associating a heuristic with a more elaborate equilibrium or attribution method can imply guarantees or mechanisms the agent does not have, even when nearby caveats are cautious.
- Requested action: Distinguish inspiration, structural analogy, and implemented derivation. Say the GLEE setting lacks enforceable commitment to a signal policy, rather than that repetition removes it. Describe the reset as a fixed history-order rule. Keep EGTA and alpha-Rank as related approaches not used here. Remove the unmeasured offer-pattern corroboration or supply the matching existing statistic. Say the paper documents the tracing distinction in a competition deployment, not that it invents the distinction. More citations are not needed.

## Smaller corrections with concrete evidence

### Minor comment m1

- Location: Appendix B.4 binary veto specification (`appendix.tex:591`).
- Observation: The description omits the stripped, case-insensitive string `no`, which the frozen binary helper also recognizes as false.
- Evidence or criterion: Frozen `persuasion.py::_strict_binary_signal` and its V1 caller; direct frozen-function probes. The exclusions of aliases `n` and `pass` are correct.
- Why it matters: The exact parser semantics are part of the promised reimplementation specification.
- Requested action: Add the literal `no` case, retaining the absent-message Boolean recommendation fallback as a separate condition.

### Minor comment m2

- Location: Appendix B.2 implemented CDF description (`appendix.tex:323`).
- Observation: The fitted knots pool logged own-payoff shares across both roles, rather than Bob-only shares, and the implementation uses 1e-9 numerical tolerance for the CDF and near-tie offer selection.
- Evidence or criterion: Frozen `fit_barg_bob_offer.py` and `barg_offer.py`; the formal Appendix A diagnostic uses exact equality.
- Why it matters: The formal midrank and deployed numerical/coarsened approximation should not silently become the same object.
- Requested action: Describe the mixed-role 51-knot CDF and tolerance explicitly, without altering the exact mathematical proposition. No material live outcome difference from this tolerance was demonstrated.

### Minor comment m3

- Location: Core hidden seller proxy and Appendix B.3 (`main.tex:159`, `appendix.tex:368`).
- Observation: The finite candidate set for the claimed maximization is missing.
- Evidence or criterion: The frozen code and verifier compare support multipliers in {.8,1,1.2,1.5} strictly above own cost multiplier; the dead-cell case is separate.
- Why it matters: An argmax over four declared candidates is narrower than unrestricted price optimality.
- Requested action: State the candidate set and separate the empty-set convention at cost multiplier 1.5.

### Minor comment m4

- Location: Appendix B.2's explanation of the continuation term (`appendix.tex:284`).
- Observation: The supported-discount-grid inequality is correct, but the claim that the term binds only for opponent discount above one is not correct outside the grid, where the code mixes clipped recursion inputs and a raw own discount.
- Evidence or criterion: A frozen-source counterexample has own discount 1.1, opponent discount .9, and k=3, giving continuation 1.1M versus recursive share M. This is outside the actual supported grid.
- Why it matters: This is a small false explanatory claim, not a demonstrated live policy failure.
- Requested action: Retain the supported-grid inequality and remove the unnecessary out-of-grid explanation.

### Minor comment m5

- Location: Appendix C's REG-023 discussion and Appendix F's final disclosure paragraph.
- Observation: The prose reassures readers that an adverse estimate's direction is unlikely to reverse under multiplicity adjustment without performing an adjusted analysis. It also turns a 1.9% matching-name fraction among disclosed records into an approximate interference rate.
- Evidence or criterion: Adjustment changes inferential uncertainty, not the unadjusted point estimate by itself. Matching names can collide, half the fleet records are undisclosed, and the exposure corpus differs from the experiment cohort.
- Why it matters: Both sentences exceed otherwise sound descriptive evidence boundaries.
- Requested action: Remove the uncomputed adjustment reassurance. Label 1.9% as a matching-name fraction only, and say cohort-specific self-play/interference was not quantified. Distinguish within-profile randomized contrasts from unadjusted between-profile comparisons rather than broadly denying all profile analysis.

### Minor comment m6

- Location: Core broader impacts and human-data statement; Appendix F reference-cell description.
- Observation: The recommendation shadow is used to claim how cheaply manipulation can be built, although cost was not measured. The rank-versus-payoff example is also not an experiment comparing exploitation. One known human game should not imply complete human-exposure ascertainment when undisclosed opponent types remain. Separately, the 1,152 seed keys are configuration-role keys, not directly comparable with the core's 960 environment configurations.
- Evidence or criterion: The shadow counts decisions and observed purchases, not implementation cost; the formal example only reverses an ordering. The paper itself reports withheld opponent types. The seed JSON includes role in each key.
- Why it matters: Ethical discussion and environment descriptions need the same measurement precision as the main results.
- Requested action: Remove the cost assertion, frame changed exploitation incentives as a possible risk, identify known human exposure as a lower bound where appropriate, and obtain the still-required human governance determination from the organizer/institution. Call the seed keys configuration-role reference cells and identify their source/version. This review does not decide the legal or institutional status of the data.

## Does Agent Behavior Analysis satisfy the requirement?

Yes at the structural level: it describes intended behavior, observed behavior,
and the evidence for their alignment. It is not merely missing the required
section. It is also appropriately explicit that transmission is not complete
strategic conformance. But it could be more informative about economic behavior.

| Family | What the present evidence establishes | Best bounded improvement |
|---|---|---|
| Bargaining | All 171 outcomes; eight-game silent-Bob schedule check; the 15-game CDF-selected failure diagnostic. | Explain how offers, discounting, acceptance thresholds, and final allocations interacted in one normalized outcome-complete example or a compact role/cell aggregate. |
| Negotiation | 19 preclose games; owner traces and subsets of independently checked prices, bounds, and messages. No final-audit hidden-seller proxy state. | Show the small cohort's information/horizon mix and why a trade closed or failed. Clearly distinguish retained buyer paths from the stopped experimental arm. |
| Persuasion | 55 assignments; plan/action agreement; four preclose warning misses in one game; the action-selected LOW-recommendation shadow. | Show seller quality versus recommendation and buyer signal/history versus BUY/PASS, using aggregates or one approved normalized trace. State that closing-window text was not independently reclassified. |

These are improvements using existing evidence, not demands to invent new
experiments or release private dialogue. A compact core lesson for each family
can point to richer appendix details. If approval prevents trace release,
aggregate counts or clearly labeled synthetic rule fixtures remain alternatives.

## Figures, tables, and page budget

Keep the three-family lifecycle figure in the core. It shows a relationship
that matters: much rating movement predates the final audited configuration,
and policy events are not isolated interventions. Its legend uses distinct
line styles as well as color. The render has no clipping or overlapping text.

Do not add a decorative architecture diagram, leaderboard screenshot, radar
plot, or another version of the same rating trajectory. Table 1 can resolve
its routing ambiguity with clearer else/then semantics. Table 2 should spend
less space on unexplained labels and more on the meaning of the observed actions.

The appendix's toy three-panel payoff/rank illustration is optional. It is
properly labeled now, but repeats a very small example already explained in
prose. It should not displace behavioral evidence in the core. If any new
figure is added later, a normalized, outcome-complete behavioral trace or a
family/role outcome distribution would need to answer a question the current
table cannot. It should replace existing material rather than simply add length.

The full PDF's page layout was inspected throughout, with individual-page
checks for the dense policy specification and changed Appendix F. All three
builds compile without unresolved references/citations or overfull boxes.
Two underfull-box notices remain in appendix prose and show no clipping.
The main text ends on page four. The separate supplement now uses the same
IAB workshop footer. Small table text is dense but not broken; simplify content
rather than reducing it further.

## Recommended revision order

1. Fix the clone lineage and exact promotion-rule account (M1–M2).
2. Reconcile denominator/action/era-snapshot definitions (M3).
3. Add the missing core vocabulary and distinguish selection from transforms (M4).
4. Refocus the abstract and method explanation on concrete reached behavior (M5).
5. Correct the bounded specification and literature claims (M7, m1–m6).
6. Establish an actually accessible, permission-compliant artifact route (M6).
7. Confirm appendix eligibility and human-data governance before submission.

The [official competition call](https://glee-competition.com/call-for-papers)
currently specifies four pages plus unlimited references, lightweight
single-blind review, and Agent Behavior Analysis. It does not explicitly grant
unlimited appendices or explicitly require a checklist. Keep the full working
paper, but do not assume its 22 pages are an authorized one-PDF submission.
The core-plus-references build is five pages. This review records the policy
ambiguity rather than resolving it on the organizer's behalf.

## Verification and review limits

Passed in this working session:

- `verify_artifact_manifest.py`: 23 frozen asset hashes, ordered checksum,
  81 flag rows, and recorded defaults. This does not reconstruct full overlays.
- `verify_derived_tables.py`: separate local/official totals and bounded audit
  denominators.
- `verify_theory_code.py`: five algebra and selected-code groups. It imports
  the working checkout, so it is not a full frozen-process reproduction.
- `verify_environment_rank_ladder.py --check-manuscript`: every corrected
  monetary-cent row against the hash-pinned source.
- Specialist bounded reruns: the 91-game clone arithmetic and the 245-game
  join with 2,288 valid action matches using the existing verifier.
- All three PDF builds and visual inspection of the complete full paper.
- Review intake, appropriate no-clinical-guideline selection, structured
  claim/evidence matrix, and specialist report lint.

The full project test suite completed with **2,886 passed and four failed**
in 570.32 seconds. The failures are the bargaining degenerate-corner
acceptance-threshold test and the live-server grid checks for bargaining,
negotiation, and persuasion. These are distinct from the passing manuscript
verification scripts. No strategy, test, simulation, model, or live-control
files were changed in this task; the suite is not reported as fully passing.

Not established: complete lifetime policy conformance; causal effects of
components, revisions, or the audit; calibration of fitted opponent models;
every historical experiment's raw evidence; every bibliography claim; a
reviewer-accessible production-equivalent release; organizer/institutional
approval for human-game data. No live policy, control, secret, or log file was
edited. No paper files were pushed to GitHub by this task.

Specialist reports, with exact code/source anchors and literature URLs:

- [Theory and frozen code](</Users/spiderishi/Coding/GLEE Competition/paper/review/review_2026-09-05/math_code_review.md>)
- [Statistics and behavior](</Users/spiderishi/Coding/GLEE Competition/paper/review/review_2026-09-05/stats_behavior_review.md>)
- [Narrative and literature](</Users/spiderishi/Coding/GLEE Competition/paper/review/review_2026-09-05/narrative_literature_review.md>)

# Confidential comments to editor

Not applicable. This is a private author-side working review, not a review
submitted to an editor. All substantive findings and competence limitations
are presented to the author above.
