# GLEE Project Evidence and Revision Dossier

Status: internal working record, not manuscript text, not approved for public release

Evidence cutoff: 2026-08-30

Update, 2026-08-31: see `OFFICIAL_FINAL_WINDOW_EXPORT.md` for the newer
authenticated dashboard receipt. Its 245 replays establish exact valid
local-to-service action agreement for all 2,288 submitted-agent moves and add
official final-window displayed rating-change aggregates. Earlier statements
in this dossier that service receipt was unavailable are superseded. Missing
owner selection, pre-coercion action, process provenance, and causal efficacy
remain unresolved.

Controlling manuscript scope: Agent 5 only. See
`paper/evidence_dossier/AGENT5_ONLY_PAPER_SCOPE.md`.

## Purpose

This dossier reconstructs how Agent 5 developed, what the available evidence
actually supports, and how each current peer-review finding should be handled.
It retains broader fleet history as private development evidence, but that
history is not the paper's subject. It is intentionally separate from
`paper/main.tex` and `paper/appendix.tex`. No manuscript claim should be copied
from this file until its Agent 5 relevance, evidence status, and release
boundary have been checked.

The immediate goals are:

1. preserve the full development story without turning conversations into facts;
2. separate official outcomes, live behavior, simulations, retrospective
   diagnostics, and proposed explanations;
3. identify which review findings can be resolved from existing records;
4. identify which findings require new analysis, user input, organizer guidance,
   or an institutional determination;
5. establish a safe order for revising the paper one issue at a time.

## Binding manuscript scope

The manuscript will describe and evaluate Agent 5 as one complete
three-family system. Other profiles may appear only as unnamed development
apparatus when a test directly explains why a component was copied into Agent
5, rejected from Agent 5, or retained in Agent 5 with an explicit limitation.
Their full policies, ratings, timelines, and topology are outside the paper.

The official result must be stated as second in the agent track and third on
the combined board. Agent 5 may be called the participant's best-performing
agent or focal runner-up. It may not be called the competition winner. The
exact page plan, appendix plan, claim bank, and inclusion rules are frozen in
`AGENT5_ONLY_PAPER_SCOPE.md`.

## Privacy boundary

This file summarizes private evidence but does not reproduce raw messages,
credentials, game identifiers, opponent identifiers, assignment salts, or
operational controls. Conversation text is used only to recover decisions,
hypotheses, and chronology. A statement made by an assistant or reviewer is not
treated as empirical evidence unless it is corroborated by code, a frozen
record, a database query, or an official snapshot.

This dossier should remain private until every cited source and excerpt has been
reviewed for permission, licensing, and participant privacy.

## Executive finding

Agent 5 progressed from a compact solver and safety wrapper on August 20 to a
complete deterministic three-family system with a frozen final policy receipt,
hundreds of thousands of local records, and an official second-place
agent-track result after 46,564 rated games. Development profiles supplied
candidate tests, but they are experimental apparatus rather than the paper's
subject. The strongest scientific story is not that one heuristic was proved
to win. It is how Agent 5 combined structural and empirical decision owners,
how it actually behaved, where it failed, and how repeated corrections to
selection bias, non-identification, unreachable gates, treatment leakage, and
missing outcomes changed its final design.

The main unresolved scientific issue is narrower and more concrete. The final
archive contains state, plan, returned action, and outcome data for the complete
245-game two-window census, but it does not contain a stable top-level policy
owner identifier or a complete process-to-commit receipt. Exact conformance can
therefore only be attempted by building an independent specification against
the frozen source and replaying owner precedence through final coercion. Whether
the required dependencies and state are fully recoverable is not yet known. It
cannot be read directly from an existing aggregate column.

## Current paper snapshot

The controlling review snapshot is the current source and PDF assessed by the
harsh review, not the earlier final-audit snapshot.

| Object | Current receipt |
|---|---|
| Main source | `paper/main.tex`, SHA-256 `997b4680808beef2a4ced875baf377262efbfca65117c4dfa6cc397761ee8646` |
| Technical appendix | `paper/appendix.tex`, SHA-256 `b8af569ddf535074f0f1193bb744734fa0b8696ec50c98658aca194a6cbd60b3` |
| Exact core candidate | `paper/main_core.pdf`, 12 pages, SHA-256 `f64ac2be20db56c434204ddc715833ef0dd81cd744a4578ac29ad5bc5876ac7e` |
| Full internal build | `paper/main.pdf`, 43 pages, SHA-256 `dbd53c11f188a55b0ad42a346a16409776235aaa8f2aecba96323801d6f2622e` |
| Main-page structure | Four main-text pages, references on page 5, checklist on pages 6 to 12 |

The earlier `paper/review/final_audit_2026-08-30/` report assessed a different
source/PDF state with core PDF hash
`5307127be9feb35cfb784d049a6503e8b698e1c69480c18cff60941485a5a71d`.
It is useful as review history, but it is not a receipt for the current files.

## What was examined

### Primary operational and empirical sources

- `.ai/CURRENT_STATE.md`, read as a dated snapshot rather than a post-close live
  truth.
- `.ai/FINDINGS.md`, the repository's designated ledger of measured facts and
  negative results.
- `.ai/EXPERIMENTS.md`, including hypotheses, assignment rules, stopping rules,
  and dispositions.
- `.ai/HANDOFF.md`, an append-only deployment and decision history.
- `DIARY.md`, for early development chronology.
- Git history, including 301 commits reachable from current `HEAD` and 317
  commits across all refs from August 20 through August 30.
- The focal profile's turn stream, flat result stream, canonical per-game
  records, rating history, and final official snapshot.
- `opponent_intelligence/opponent_intelligence.sqlite3`, used as a structured
  behavior store, subject to the same selection and privacy limits as the logs.
- Frozen paper data under `paper/data/` and the review artifact under
  `paper/review_artifact/`.

### Conversation and decision-history sources

- Two related Claude JSONL archives, 20,668 records in total.
- The Codex Bargaining task, 10 turns.
- The Codex Negotiation task, 184 turns.
- The Codex Persuasion task, 150 turns.
- The current Paper task, whose requests and review decisions are already part
  of the present working context.

The conversation archive is a decision-history source, not a measurement
source. It can establish what was proposed, questioned, authorized, or rejected.
It cannot establish that code ran or that a strategy worked.

### Review and verification sources

- The initial five-seat paper review and its revision roadmap.
- The later final audit, retained as a superseded snapshot.
- The current harsh review package in
  `paper/review/harsh_review_2026-08-30/`.
- The current claim-evidence matrix and its validator.
- The theory/code audit and local executable checks.

## Evidence hierarchy

When sources disagree, use this order:

1. official post-close snapshots and immutable service receipts;
2. raw local state, action, result, and canonical game records;
3. frozen banked Git blobs, overlay hashes, and deterministic verifiers;
4. reproducible derived tables whose inputs and transformation are present;
5. the repository's measured-fact and experiment ledgers;
6. deployment handoffs and dated operator records;
7. manuscript text and review reports;
8. conversations, assistant analyses, and unverified red-team suggestions.

This order matters. A model-generated correction in `.ai/REDTEAM_LOG.md` does
not override the designated measured-fact ledger without a supporting artifact
or valid citation to the underlying evidence.

## Coverage receipt

### Focal raw archive

The bounded scan of the focal profile found:

| Source | Reconciled count |
|---|---:|
| `logs/composite/turns.jsonl` valid JSON rows | 517,261 |
| Unique flat result IDs | 24,803 |
| Canonical per-game records | 46,316 |
| Canonical records marked completed | 46,079 |
| Canonical records marked `no_deal`: 221 timeouts, one invalid move | 222 |
| Canonical records still active or unresolved | 15 |
| Official rated-game total | 46,564 |

These counts do not form one nested flow. The official total counts rated games,
while the local archive counts assignments and includes 221 timeouts, one
invalid-move ending, and 15 active records. The 46,079 records marked
`completed` contain 22,999 agreements, 15,306 persuasion completions, 5,597
rated no-deal outcomes, and 2,177 walks. If, and only if, every completed local
record maps one-to-one to an official rated increment, the count-level rated
gap is 485 and the upper-bound local rated coverage is 98.96 percent. The
official aggregate supplies no row-level IDs with which to verify that mapping.

The previously reported `46,301 / 46,564 = 99.44%` coverage mixes local terminal
assignments with official rated games and is invalid. The 248 and 263 deficits
derived from that comparison are also invalid. Existing paper data, appendix,
README, and review text that use this flow are stale and must be repaired later.

### Final policy windows

Direct raw-window scans reproduce both frozen census files:

| Window | Games | Own actions | Key scope |
|---|---:|---:|---|
| Pre-close, August 29 | 63 | 787 | Bargaining 19, negotiation 19, persuasion 25 |
| Close, August 30 | 182 | 1,501 | Bargaining 152, persuasion 30 |
| Combined | 245 | 2,288 | 244 rated, one persuasion timeout |

Every scanned final-window action contains the agent-visible serialized state,
a plan object, the returned action, a source label, and a timestamp. Every
action has source `heuristic` under the logger's deterministic-path convention,
and no logged strategy error appears in the census. That source label does not
identify the selected internal policy owner. Gate instrumentation is incomplete:
`plan.gates_fired` exists on 1,207
of 2,288 actions and is nonempty on 905. The archive does not contain a stable
top-level owner field, and no complete process commit receipt is attached to
every action. Agent-visible state can include private values and interaction
text, so it is not a public-data object.

### Conversation coverage

The two Claude archives contain 20,668 JSONL records and 504 human-origin user
messages. The three non-paper Codex tasks contributed 344 turns in total. These
records were scanned for strategy decisions, reversals, objections, operator
instructions, and paper-framing changes. This controlling synthesis does not
reproduce raw conversation records. The private conversation source note retains
absolute locators, opaque IDs, and short quoted directives for auditability and
must not enter a Git, Overleaf, reviewer, or public bundle without redaction.

The current Paper task was reconstructed from the active task context rather
than an immutable exported turn archive. Its editorial decisions are therefore
covered, but not yet backed by a stable external task receipt.

### Other stores audited

The repository-wide inventory covered approximately 21 GiB under `logs`,
including 27 JSONL streams and 352,933 JSON files, plus 12 historical transcript
exports, 39 model artifacts, 23 operational JSON records under `.ai`, and the
opponent-intelligence SQLite store. The database contains 57,793 game rows,
9,143 target moves, 6,435 tactic matches, and 6,414 live target-turn rows, but
its time span ends on August 29 and its purpose is opponent behavior analysis.
It cannot fill the final-window owner-conformance gap. The 12 transcript exports
cover historical batches from August 20 through August 22 and likewise do not
cover the final two windows.

Repository-local Claude worktree snapshots, approximately 115 MiB and 597 JSON
files, were inventoried but excluded from every denominator because they are
duplicate repository copies rather than new observations. Model corpus sizes,
simulation rows, replay exposures, live assignments, and official games are
kept as separate evidence populations throughout the source notes.

## How far the system came

### Starting point

The first repository commit, on August 20, described closed-form solvers with
total error containment. The initial architecture already recognized that a
strategy exception could become a timeout or illegal action, so legal coercion
and fallback behavior were part of the system from the beginning.

### Major development stages

| Period | Main change | What was learned |
|---|---|---|
| August 20 | Runtime flags, fleet separation, safe draining, early arena, percentile scoring | Strategy had to be changeable without arbitrary restarts, and the evaluation objective was rank-like rather than raw payoff. |
| August 21 to 22 | Cell-specific analysis, live-log fitting, structural feasibility, adversarial review | Many intuitive conclusions were artifacts of accepted-deal selection, pooled roles, or invalid counterfactual response models. |
| August 22 to 24 | Explicit negative-result ledger, bounded randomized arms, competitor behavior observation | Observing a leader's action did not show that copying it caused success. Assignment, reachability, and all-outcome cohorts had to be retained. |
| August 24 to 25 | Final-outcome collector repair, deterministic specialist policies, exact owner precedence | Missing finals were not automatically losses, slot names were not policies, and an enabled flag could be inert or unreachable. |
| August 25 to 28 | Family specialists, lossless banking, live mechanism checks, persuasion and negotiation repairs | Mechanism verification and efficacy were separate. Several live changes were stopped, rolled back, or retained only for safety or structure. |
| August 29 | Final Agent 5 bank and family-best assembly | Agent 5 was an ordered router of observable-state owners and fallbacks, not one equilibrium solver. |
| August 30 | Controlled final activity and official close | Agent 5 finished second in the agent track and third on the combined board. The endpoint belonged to Agent 5's adaptive trajectory, not one isolated component or only the final overlay. |

The conversation record adds five decision-history inflection points to that
artifact chronology. First, the initial heterogeneous fleet was intentionally
used to expose failures before assembling the fifth agent. Second, the objective
shifted from intuitive payoff and agreement metrics to exact-cell percentile and
rating. Third, a bounded LLM wording trial was run during development, measured
worse than templates, and retired; only the closing configuration is accurately
described as deterministic and LLM-off. Fourth, a planned single-family
competitive-profile layout was superseded before landing once the team
recognized that placement depended on the best complete three-family agent;
later operational queues were still sometimes family-restricted for measurement,
quotas, or peak protection. Fifth, at least one final persuasion component was copied to
the focal profile by explicit operator choice before its planned efficacy read
was complete. These are design and authorization facts, not component-effect
estimates.

### Quantitative progression

- Git history spans 301 commits on the current branch and 317 across all refs.
- The post hoc normalized development crosswalk contains 35 records. It is not
  a prospective experiment registry, and it does not enumerate every informal
  threshold sweep, abandoned idea, or undocumented exploration.
- Of those records, 33 reached their intended state, 25 were historically live,
  one was staged only, seven had an adverse disposition, 17 were stopped or
  superseded, and 11 ended without a terminal efficacy verdict.
- None passed a precommitted efficacy-promotion rule.
- The focal profile accumulated 46,564 rated games and displayed 2590.02 at
  official close, with bargaining 2804.82, negotiation 2620.36, and persuasion
  2344.87.
- The official Agent 5 result was second in the agent track and third on the
  combined board.

The zero-promotion count does not mean that the final policy was arbitrary. It
means that retained components entered for several different reasons:
mathematical structure, action legality, safety, operational imitation,
field heuristics, or incomplete experiments. The paper must not collapse those
reasons into one efficacy claim.

## Strategy evolution by family

### Bargaining

The bargaining system moved from a generic finite-horizon solver plus empirical
floors to an ordered policy with a narrow highest-precedence Bob owner and a
generic fallback planner. The final banked narrow owner applied only to silent
Bob with disclosed horizon 12 and discount 0.95. It used a six-step share ladder
ending at \(M-0.01\) for Bob, which is 99.99 percent only when the pot is 100,
and a discounted acceptance floor tied to that terminal action.

Outside that cell, the final bank used finite or synthetic-horizon recursion,
an unknown-horizon quadratic concession clock, a discount-dependent acceptance
floor, and a fitted Bob expected-percentile offer optimizer. Integer-pot
rounding, an exact-cent exception for the narrow owner, legal coercion, and a
safe fallback were part of the returned action path.

The broad high-share delay guard was configured on but unreachable because its
parent no-regression flag was explicitly off. This is one of the clearest
examples of why configured state cannot be used as behavior evidence.

Key failures and corrections included:

- an unguarded stonewall release coincided with a roughly 200-point live drop and
  was reverted;
- per-opponent exploitation measured negative in the simulator and remained off;
- an observed-gain broadening was negative across three arena seeds;
- a high-share retrospective argument reversed under the later active stack;
- one unchanged stack produced sharply different fitted percentiles in adjacent
  windows, showing why time-series movement did not identify a component effect.

### Negotiation

Negotiation began as the largest weakness and received the largest number of
candidate mechanisms. Development separated complete-information states, where
the visible positive-trade interval could support exact structural actions,
from hidden-information states, where only support bounds and public history
were available.

The grid reconstruction established a crucial structural fact. All six
complete-information type cells were feasible, only six of 16 hidden type pairs
were feasible, and 12 of 22 total type pairs admitted trade under the stated
support model. The remaining 10 of 22 were infeasible. Hidden opponent value
was absent from the live hidden-information state. In some completed agreements
it can be algebraically recovered from payoff identities, but for unclosed or
otherwise unmatched hidden games individual feasibility remains unidentified.
The focal logs therefore do not reveal the complete hidden joint type
distribution.

Agent 5's final dispatcher combined complete-information structural owners, a
hidden one-round seller seed-rank table, hidden terminal bound inference,
observed leader buyer paths, and seller continuation, stall, endgame, and
Boulware-style fallbacks. That ordering matters because an earlier owner can
preempt every later fallback.

Important failures and reversals included:

- ultimatum shares 0.90 and 0.95 reduced the simulator objective and close rate;
- a response-model offer engine changed sign across continuation-value fits,
  revealing that unplayed asks were not identified from own logs;
- the surplus-share experiment leaked its treatment into accept decisions and
  was invalid as run;
- an apparently strong 0.10 ZOPA-share result was rejected after the simulator
  was found to auto-accept unsupported asks, use the wrong bins, and learn from
  selected agreements;
- the broad leader-derived buyer clone looked positive at an early read but
  failed its stopped 91-game checkpoint, increased no-deals, and was negative in
  the focal profile stratum;
- a live score-floor challenger collapsed close rate and was rolled back;
- a selected accept-all-profitable replay reversed after realized continuation
  and the larger all-exposure denominator were retained.

### Persuasion

Persuasion developed from fixed truth or push rules and optional LLM wording to
a deterministic seller policy and an ordered buyer policy. The banked buyer
order was: posterior money gate, 0.75 tight-cell threshold, 0.65 prior fence,
reversible credibility reset, then a final one-directional BUY-to-PASS decline
veto.

The one-shot obedience calculation was used as a benchmark, not as a proof of
optimal play in repeated cheap-talk interactions. When buyer value was hidden,
the bank used historical buy-rate heuristics instead of pretending the
obedience threshold was observable.

Important failures and limits included:

- LLM-worded messages converted less often than templates in an archived
  comparison, but the exact development-time provenance must remain bounded;
- the tight credibility reset was copied into the focal profile before its
  planned efficacy criterion was met;
- the final decline veto was one-directional and could only suppress a purchase;
- a stricter frozen selector found four warning turns among 80 text-buyer
  decisions in the pre-close window, all in one game, and all four purchases
  revealed LOW quality;
- this four-turn result establishes a clustered coverage failure, not a rating
  effect or 80 independent experimental units.

## Evidence populations that must never be merged

| Label | Population | What it supports | What it does not support |
|---|---|---|---|
| Agent 5 adaptive endpoint | 46,564 rated focal-profile games across Agent 5's cumulative trajectory | Official competitiveness and final displayed values | Efficacy of the final frozen policy or any component |
| Lifetime local assignment archive | 46,316 records: 46,079 completed, 222 failed terminals, 15 active | Local assignment statuses and historical behavior | Direct coverage of the 46,564 rated-game universe or random sampling |
| Pre-close final era | 63 games, 787 actions | Complete local description of one bounded banked era | Representative field performance or lifetime behavior |
| Two-window final census | 245 games, 2,288 actions | Complete local returned-action and outcome census for the selected windows | Owner conformance without reconstruction, server receipt, or causal effect |
| Bargaining auxiliary audit | 25 games, 153 eligible changed actions across three profiles | Live reach and action-change evidence | Focal-profile conformance or efficacy |
| Negotiation auxiliary simulation | 800 games, 6,188 eligible states | Simulated reach and precedence | Live frequency or reward value |
| Persuasion warning audit | Four games, 80 decisions, four misses in one game | Bounded parser and selector failure | Independent turn-level effect estimate |
| Clone checkpoint | 91 assigned games after two looks | Descriptive candidate-control contrast | Confirmatory effect, stable assignment audit, or isolated component value |

The 244 rated games in the selected windows are about 0.52 percent of the focal
46,564-game rated history; the 245th assignment timed out. They were chosen
around final operational windows and have a highly nonuniform
family mix. They are valuable because they are complete for their stated
windows, not because they are representative.

## Verification results at this snapshot

The following lightweight checks were run without changing strategy or live
state:

| Check | Result | Boundary |
|---|---|---|
| `paper/analysis/verify_theory_code.py` | PASS, five groups | Imports the mutable current working tree, not an isolated banked checkout |
| `paper/analysis/verify_derived_tables.py` | PASS | Verifies published aggregate arithmetic, not source joins |
| `paper/analysis/verify_artifact_manifest.py` | PASS | Verifies 23 banked Git blobs, an ordered checksum, 81 flags, and required defaults |
| `paper/review_artifact/verify_all.py` with system Python | PASS | Reproduces sanitized aggregate and synthetic outputs only |
| `paper/review_artifact/verify_all.py` with `.venv` Python | FAIL before analysis | The environment lacks installed `matplotlib` package metadata |
| Peer-review claim-matrix validator | FAIL | CSV row 32 uses the unsupported label `reproducibility` |

The review artifact verifier regenerated two quantitative figures. Its
`REPRODUCIBILITY_BOUNDARY.md` currently says four figures, which is a stale
internal inconsistency that should be corrected when artifact work begins.

## Source provenance around the final windows

The bank manifest names Git commit
`b54cb33ad9f4fe7da4c667262eee00ffaeac3ab6`, 23 source/model assets, 81 overlay
keys, and required defaults. The August 29 pre-close runner was explicitly
launched from that commit.

The August 30 close runners launched after repository commit `b8a5a87`. A Git
comparison shows no `glee_agent/` source change between `b54cb33` and `b8a5a87`.
The handoff ledger also records an unchanged `arms.json` hash throughout the
close activity. This is meaningful partial provenance for policy equivalence.
It is still not a per-process receipt that proves the checkout, imported blobs,
overlay, wrapper, and server-received action for every turn.

Current `HEAD` is later commit `ead1083`, which differs from the banked commit in
seven strategy-related files with 374 insertions and eight deletions. The current
theory verifier imports this later working tree. A green result therefore cannot
be cited as direct verification of the banked implementation until the verifier
is isolated.

## Review findings, handled one by one

The status labels used below are:

- `RESOLVABLE NOW`: existing evidence is sufficient, but no paper edit is made
  in this dossier pass.
- `NEW ANALYSIS`: the necessary raw material exists, but a reproducible analysis
  or verifier still has to be built.
- `SCOPE ONLY`: retrospective evidence cannot support the stronger claim, so the
  paper must narrow it.
- `USER INPUT`: factual metadata must come from the author.
- `EXTERNAL`: an organizer, institution, or review platform must decide it.

### B1. Author metadata placeholder

Status: `USER INPUT`

Current evidence: `paper/main.tex:45-47` still contains `Author Name`,
`Affiliation`, and `email@example.com`.

What can be done now: nothing safely. The real author name, affiliation, and
contact address should not be guessed from Git metadata or private account data.

Later action: obtain the exact author block from the user, update the single-blind
paper, rebuild, and inspect visible text plus PDF metadata.

### B2. Human-opponent ethics and data-use determination

Status: `EXTERNAL`

Current evidence: humans and agents shared the pool, while the released
aggregates do not reliably separate all opponent types. Deidentification and
withholding raw dialogue reduce privacy risk but do not create authorization.

What existing logs can establish: what fields were retained, how direct
identifiers can be removed, and which analyses use message content or opponent
behavior.

What existing logs cannot establish: whether the work is exempt, not human
subjects research, organizer-authorized secondary analysis, or subject to a
specific institutional review path.

Later action: obtain written organizer and institutional guidance covering
analysis, retention, access, public release, and any required exclusion of human
records.

### B3. Overleaf can compile the wrong document

Status: `RESOLVABLE NOW`

Current evidence: the Overleaf bundle's default `main.tex` enables the technical
appendix unless `corepaper` is defined. Its own README says compiling `main.tex`
produces the full paper, appendix, and checklist. The bundle does not include
`main_core.tex`. A normal Overleaf import can therefore build the 43-page
internal report rather than the submission-safe package.

Later action: make the Overleaf default root produce the exact four-page core,
references, and checklist. Move the long report behind a clearly named separate
root or separate project.

### B4. Review-time artifact is unavailable and non-production-equivalent

Status: `EXTERNAL` plus `RESOLVABLE NOW`

Current evidence: the local sanitized artifact passes with the system Python
environment and honestly states that it cannot prove private joins, server
receipt, assignment derivation, or production-source equivalence. It has not
been supplied through an approved reviewer channel.

Later action: first confirm an organizer-approved artifact route and release
permission. Then freeze a privacy-safe archive, environment receipt, checksum,
exact command, expected output, and claim-to-check map. If no route exists, keep
the paper at a bounded case-study claim level.

### M1. The full runner-up strategy is under-described

Status: `RESOLVABLE NOW`

Current evidence: the bank commit, 81-key overlay, six behavior-affecting
defaults/constants, and 23 policy/model assets are frozen. Code audits already
recover the bargaining and persuasion precedence in detail. Negotiation owner
order is present in source and the existing theory/code audit, but the core does
not expose its selected multipliers, full owner order, postguards, and fallbacks
compactly.

Later action: build a private, versioned final-policy specification before
editing the paper. Each row should state visible trigger, owner precedence,
objective, exact action rule or table hash, retained state, postguard, fallback,
and evidence class.

### M2. Final-era owner and action conformance is not measured

Status: `NEW ANALYSIS`

Current evidence: all 2,288 final-window actions retain state, plan, returned
action, and source. Gate instrumentation is partial: `plan.gates_fired` exists
on 1,207 actions and is nonempty on 905. There is no stable top-level owner ID.
The aggregate tables therefore cannot calculate the denominator directly.

What may be recoverable: an independent replay could evaluate the frozen owner
predicates, reproduce precedence, compute the intended action, apply postguards
and legal coercion, and compare with the logged returned action. The safest first
target is the complete 63-game pre-close window, followed by all 245 games if the
same provenance checks pass.

Required output fields:

1. eligible owner set;
2. selected owner;
3. independently specified action;
4. logged plan;
5. final post-coercion returned action;
6. exact match indicator;
7. override or fallback reason;
8. unresolved or malformed record status;
9. joined outcome status.

This analysis must import the banked source in isolation. Reusing the current
working tree would repeat M4.

### M3. Evidence populations are too easy to confuse

Status: `RESOLVABLE NOW`

Current evidence: the populations and denominators are fully enumerated in this
dossier. Their purposes are different and their membership is not nested in a
simple way.

Later action: assign each population one fixed label and use it consistently in
the abstract, methods, behavior section, captions, and limitations. Never use
the 245-game census as a representative sample of the 46,564-game trajectory.

### M4. The theory verifier imports mutable working-tree code

Status: `RESOLVABLE NOW`

Current evidence: `paper/analysis/verify_theory_code.py:19-30` places the current
repository root on `sys.path`. Current `HEAD` differs from the banked commit in
seven strategy files. The separate asset-manifest verifier correctly checks
Git blobs but does not force the theory verifier to import those blobs.

Later action: export the 23 named banked assets into a temporary isolated tree,
assert every hash, import only from that tree, and exercise representative rules
through dispatch and final legal coercion. The verification receipt should fail
if the current worktree leaks into `sys.path`.

### M5. The endpoint belongs to Agent 5's adaptive trajectory, not only the final policy

Status: `SCOPE ONLY`

Current evidence: official placement and ratings are strong external evidence
for Agent 5's full adaptive trajectory. The final selected windows were
operationally chosen and were not a randomized or representative frozen-policy
evaluation.

At a late update rate of 0.002, the 63-game pre-close blocks replace only about
3.73 percent, 3.73 percent, and 4.88 percent of inherited raw rating state in
bargaining, negotiation, and persuasion. The larger two-window census replaces
about 28.99 percent of bargaining state, 3.73 percent of negotiation state, and
10.25 percent of persuasion state under the same simplified recursion. Those
weights do not turn selected exposure in a moving field into a causal test.

Later action: keep second place prominent, but call it an Agent 5 adaptive-
trajectory endpoint. Use final-window data for behavior description and
conformance only.

### M6. Rank-aware is stronger than the empirical validation

Status: `SCOPE ONLY`, with an optional `NEW ANALYSIS`

Current evidence: the payoff-versus-rank reversal is mathematically sound. The
bargaining local proxy had reported calibration `R^2=0.667`; the persuasion
proxy had `R^2=0.329` and was nonmonotone above the 70th percentile. The
official opponent adjustment and tie handling remain undisclosed, and most final
owners optimize money, agreement, structure, or safety rather than a validated
official-rank objective.

Later action: use `rank-motivated` or `local raw-rank proxy` unless a held-out,
exact-cell validation against recoverable official targets is built. Do not call
the whole stack rank-optimal.

### M7. The 91-game clone is inferentially weak

Status: `SCOPE ONLY`

Current evidence: the released aggregate reproduces candidate 44, control 47,
mean difference 0.869 rating points per game, nominal normal interval
[-0.730, 2.469], and a 6.141 percentage-point no-deal increase. There were two
looks, assignment inputs are withheld, rating state carries across games, and
one focal stratum was negative.

Later action: retain the clone only as a failed operational checkpoint. Do not
give it a figure, a confirmatory interval, or causal weight in the paper's main
contribution.

### M8. Lifetime missingness needs a real flow

Status: `NEW ANALYSIS` plus `SCOPE ONLY`

Current evidence: the existing 248/263 missingness flow is invalid because it
subtracts local assignment counts from an official rated-game count. The local
archive instead contains 46,079 completed records, 222 failed terminal
assignments, and 15 active records. Under the unverified one-to-one assumption
that every completed local record produced an official rated increment, 485
rated games are absent at the count level.

Later action: characterize the 222 failed and 15 active local assignments by
family, era, status, and logging mechanism. Seek an official row-level rated-game
list before claiming a precise rated coverage or missingness mechanism. If that
list is unavailable, report the conditional 46,079-versus-46,564 comparison and
state that the membership of the 485-count gap is unidentified. Do not assume
missingness is random.

### M9. The audit is not validated as a general method

Status: `RESOLVABLE NOW` at a narrower claim level, `NEW ANALYSIS` for a stronger
claim

Current evidence: the workflow caught several concrete errors in this one
system, including an unreachable gate, treatment leakage, missing-final
misclassification, selected-denominator reversal, and parser coverage failure.
That is strong case-study evidence, but there is no standard observability
baseline, audit-element ablation, second system, or independent deployment.

Later action: either keep the contribution as an integrated one-system forensic
discipline, or build a compact error-catch ablation that shows which wrong claim
would have survived if eligibility, ownership, return, outcome, or causal-status
checks were removed. Do not claim general validation without comparative data.

### M10. Faster-concession evidence is internally contradictory

Status: `RESOLVABLE NOW`, but only after evidence adjudication

Current evidence:

- `.ai/FINDINGS.md:188-200`, the designated measured-fact ledger, says the
  corrected two-seed simulator result for exponent 1.2 versus 2.0 remained
  negative at -0.0166 and -0.0182 after the overlay bug was fixed.
- `paper/appendix.tex:784-785` also says the two seeds were negative.
- `paper/appendix.tex:1202` and `paper/appendix.tex:1374` instead say later
  audits invalidated the result and left its sign unresolved.
- The claim matrix copies the unresolved-sign interpretation.
- `.ai/REDTEAM_LOG.md:448` asserts that the sign is unproven, but its cited
  `TEST4_EXPERIMENT.md` location does not discuss Boulware and its cited findings
  location does not itself establish the claimed invalidation.

Adjudication: the available documentary record supports a corrected negative
result inside the stated simulator and control stack. It does not support a
live causal or general field-effect claim. The safe later wording is: two
corrected simulator seeds disfavored exponent 1.2 under that frozen harness;
this was a simulator diagnostic, not proof that slower concession is generally
optimal. The appendix and claim matrix should not say that later holdouts proved
the opposite unless the missing supporting artifact is located.

### M11. The narrative hierarchy is backwards

Status: `RESOLVABLE NOW`

Current evidence: the four-page core explains the audit vocabulary in more
detail than the complete runner-up strategy. It contains four tables and no
empirical figure, while the one-row result table and duplicated evidence-status
table consume space that could explain the policy or behavior.

Later action: use this order: what the agent did, why percentile scoring changed
the design, what the returned-action evidence establishes, what failed, and
what was learned. Add no decorative architecture figure. If conformance can be
reconstructed, use one evidence-bearing conformance matrix. Otherwise use an
honest audit-coverage matrix. The existing rating trajectory is the only other
figure with a strong core-paper case.

### M12. The claim-evidence matrix fails its validator

Status: `RESOLVABLE NOW`

Current evidence: the validator stops at CSV row 32 because
`CLAIM-HIDDEN-REPLAY-001` uses `alignment_issue=reproducibility`, which is not an
allowed label.

Later action: change the label to `scope` or `other`, review the row's support
classification after resolving M10, rerun the validator, and regenerate the
receipt for all current rows. This is a QA failure, not evidence that the replay
claim is true or false.

## Additional issues found during reconstruction

These were not all explicit in the harsh-review headline list.

### A1. Review artifacts describe different manuscript states

The final-audit directory assesses an older source/PDF state and refers to a
63-game, 787-action era. The current harsh review assesses the later 245-game,
2,288-action two-window version. Future review reports must record source and PDF
hashes and should not call an older verdict current.

### A2. The rating-trajectory timestamps have no explicit timezone

`paper/data/submitted_agent_rating_checkpoints.csv` uses naive timestamps. Its
provenance and plotted bank/close annotations appear to use IST, while a proposed
axis label says UTC. Any future figure must either convert every timestamp to
UTC or label the current values as IST. A date-only tick does not remove the
underlying provenance ambiguity.

### A3. The artifact figure count is stale

The review artifact boundary says four figures, while the current verifier and
README describe and regenerate two. The package map, allowlist, verifier, and
claim map must agree before release.

### A4. A verifier can pass in one Python and fail in another

The system Python passes the review artifact. The repository `.venv` fails the
dependency check because `matplotlib` package metadata is missing. Reproducible
instructions must name and test the intended environment rather than rely on an
unspecified `python3`.

### A5. Close-window source equivalence is stronger than the paper states, but
still incomplete

The August 30 launch occurred after commit `b8a5a87`, which made no
`glee_agent/` source change relative to bank commit `b54cb33`, and the overlay
hash remained unchanged. This supports source-level equivalence of the policy
files. It still does not prove the loaded process image or server receipt for
each action. The dossier should preserve both sides of that statement.

### A6. Two unrelated 63-game checkpoints can be confused

An August 23 first-principles checkpoint also contained 63 games and was
described conversationally as a favorable but underpowered early result. It is
not the August 29 pre-close final-profile census of 63 games and 787 actions.
The early checkpoint had a bootstrap interval crossing zero and later required
cell-level correction. Every later table, caption, or sentence must name the
date and cohort rather than saying only "the 63-game sample."

### A7. The published lifetime coverage ratio uses incompatible denominators

`paper/data/log_archive_coverage.csv` and downstream review text divide 46,301
local terminal assignments by 46,564 official rated games. The local numerator
includes 221 timeouts and one invalid-move ending that are not rated-game
increments, so the 99.44 percent ratio is not a coverage estimate for the public
denominator. This error was found only after classifying the terminal outcomes,
which makes it a useful example of the same denominator discipline the paper
advocates. The manuscript and review artifacts are intentionally not edited in
this dossier pass, but every downstream use of 248, 263, or 99.44 percent is now
marked stale.

### A8. Several CSV provenance locators have drifted

Mutable `.ai/HANDOFF.md` line numbers embedded in
`paper/data/submitted_agent_rating_checkpoints.csv` and
`paper/data/experiment_registry_crosswalk.csv` no longer resolve to the events
they claim. For example, the August 29 persuasion-copy checkpoint now resolves
at `.ai/HANDOFF.md:144-183`, while its stored locator points elsewhere. Sampled
high-share, leader-clone, and discounted-guard crosswalk rows also resolve to
unrelated sections. The numerical rows are not invalidated solely by locator
drift, but their present provenance strings are not durable receipts.

Later action: freeze a hash-addressed snapshot of `HANDOFF.md`, replace mutable
line references with dated event keys plus commit or content hashes, and audit
every affected CSV row before relying on it in the paper or artifact.

## Claims safe for later manuscript use

Subject to permissions and exact source citation, the following claims are
currently well supported:

- Agent 5 finished second in the agent track and third on the combined board at
  official close.
- The focal profile ended at 2590.02 after 46,564 rated games, with the reported
  family ratings and counts.
- Expected payoff and expected empirical raw rank can order actions differently
  under the stated fixed-reference assumptions.
- The final policy was an observable-state router with structural owners,
  empirical heuristics, postguards, and legal fallbacks.
- The closing configuration was deterministic and LLM-off, while a bounded
  wording-only LLM trial occurred earlier and was retired after measuring worse
  than templates.
- Under the reconstructed negotiation support, 12 of 22 type pairs were
  feasible: all six complete-information pairs and six of 16 hidden pairs.
- The 245-game two-window census contains 2,288 own actions, 244 rated games,
  one timeout, and no logged strategy error.
- The lifetime local archive contains 46,316 assignments: 46,079 completed,
  222 failed terminals, and 15 active records. These counts are not a nested
  coverage flow with the 46,564 official rated games.
- Several development conclusions were reversed or rejected after denominator,
  reachability, treatment-isolation, or outcome-join audits.
- The clone checkpoint was inconclusive and failed its promotion rule.
- The final endpoint is evidence of adaptive system competitiveness, not
  component causality.

## Claims not safe for later manuscript use

- The final frozen policy caused second place.
- Agent 5 won the competition.
- Every final-window action matched its designed owner.
- A green current-worktree verifier proves the banked policy.
- The full stack optimized the official adjusted rank.
- The 245-game census represents the lifetime trajectory or the 960-cell grid.
- The 91-game clone improved rating.
- Missing local records are random or harmless.
- The returned-action audit is generally validated across competitions.
- Faster concession has a proven live negative effect, or later holdouts proved
  its sign reversed, without the corresponding frozen evidence object.
- A configured flag was behavior merely because it was enabled.
- The project never used an LLM at any stage.
- Every component copied into the focal final profile passed a completed,
  precommitted efficacy criterion.

## Recommended work order

The paper should remain untouched while these evidence tasks are handled.

1. Freeze this dossier and its source-note receipts.
2. Build an isolated banked-source verifier and exact policy specification.
3. Attempt owner/action conformance reconstruction for the 63-game pre-close
   era, then extend to all 245 games if provenance is stable.
4. Characterize the 222 failed and 15 active local assignments, and either
   recover an official rated-game ID list or retain a conditional 485-count gap.
5. Reconcile the concession-speed record and repair the claim-matrix schema.
6. Decide the contribution posture based on conformance recovery: validated
   returned-action audit or bounded forensic case study.
7. Only then rewrite the four-page core, appendix, figures, and conclusion.
8. Separately obtain author metadata, ethics/data-use determination, licensing,
   and an approved artifact route.
9. Rebuild a submission-safe Overleaf project and run a final exact-package
   review.

## Decision gate

If the independent replay recovers exact owner and returned-action conformance
for the complete bounded era, it can serve as strong supporting evidence for
Agent 5. If it cannot, the paper should still lead with the runner-up Agent 5
and present the audit as partial evidence and a set of practical lessons.

Either version can be a strong competition paper. The award-level difference
will come from whether the paper can show, with one frozen evidence object, what
the final policy was designed to do and what it actually returned.

## Source notes

Detailed private reconstruction notes are stored in:

- `paper/evidence_dossier/EVIDENCE_RECEIPT.md`
- `paper/evidence_dossier/AGENT5_ONLY_PAPER_SCOPE.md`
- `paper/evidence_dossier/source_notes/timeline_and_decisions.md`
- `paper/evidence_dossier/source_notes/data_logs_and_conformance.md`
- `paper/evidence_dossier/source_notes/conversation_history.md`

Those files are supporting receipts. They contain internal source locators and
are not sanitized for public release. This dossier controls the evidence
synthesis. `AGENT5_ONLY_PAPER_SCOPE.md` controls manuscript inclusion.
