# Data, log, and conformance evidence audit

Status: internal evidence dossier. This is not manuscript prose. Any claim
copied from it must retain its evidence class, denominator, and limitation.

Audit cutoff: 2026-08-30T14:41:43Z. The focal submitted-profile archive was
stable at the cutoff. Some development collectors were still moving, so their
counts are inventory facts at the stated cutoff, not frozen research
denominators.

Authenticated-replay addendum, 2026-08-31: the newer receipt at
`../OFFICIAL_FINAL_WINDOW_EXPORT.md` supersedes this note wherever it states
that independent server receipt was unavailable. All 245 official game IDs and
result objects join locally, and all 2,288 attributed submitted-agent replay
moves match the corresponding local returned action and are marked valid.
Selected-owner conformance, the uniform pre-coercion action, process-to-commit
provenance, and causal efficacy remain unavailable.

Manuscript scope boundary: the focal submitted profile is Agent 5 and is the
only paper subject. Other stores are retained here for inventory and direct
component-lineage checks, not for cross-agent comparison in the manuscript.
See `../AGENT5_ONLY_PAPER_SCOPE.md`.

## 1. Bottom line

1. The official focal-profile lifetime total of **46,564** counts rated games,
   while the **46,316** local per-game files count assignments. They do not form
   a nested flow. The local archive contains **46,079** completed records,
   **222** failed terminal assignments, and **15** active records. If every
   completed local record maps one-to-one to an official rated increment, the
   conditional count gap is 485 and the corresponding coverage is 98.96
   percent. The official aggregate has no row-level IDs with which to verify
   that mapping. The earlier 99.44 percent figure is invalid because its local
   numerator includes unrated timeouts and an invalid-move ending.
2. The two claimed final-policy windows reconcile exactly to **245 games and
   2,288 locally logged own actions**. The pre-close window contains **63 games
   and 787 actions**. The close window adds 182 games and 1,501 actions. Every
   one of the 245 games has a canonical local join. There are 244 rated
   terminals and one timeout.
3. All 2,288 focal action records have `state`, `plan`, `action`, `source`, and
   `ts`; all are tagged `source="heuristic"`; none has a logged `error`.
   Flat turn rows match the nested per-game `our_turns` rows exactly on
   timestamp, action, source, plan, and error, 2,288 of 2,288.
4. This is a strong **local returned-action and outcome census**, but it is not
   an all-owner conformance audit. The logs do not retain a stable exhaustive
   selected-owner field, the pre-coercion candidate action, or a complete
   process-to-commit receipt. `plan.component` is present for only 220 of 2,288
   actions. `plan.gates_fired` is present for 1,207 actions and nonempty for
   905; it is absent for 1,081 and empty for 302. It is also branch-specific
   and can contain multiple gates. An exact owner-specific denominator cannot
   be recovered by counting the original records.
5. The local action log is not a server acknowledgement. Canonical game
   histories support assignment and outcome joins, but they do not expose an
   independent receipt for every local message and decision. Any manuscript
   phrase such as "complete census" must therefore say **complete local census
   of recorded assignments, actions, and joined outcomes within the two
   windows**.
6. A stronger owner audit can be reconstructed only as a retrospective replay
   of the frozen policy on archived visible states. Unless a contemporaneous
   process receipt is recovered, that replay would be evidence about a
   reconstructed action function, not proof of which source a live process
   loaded or what the service received.

Primary frozen aggregate anchors:

- `paper/data/log_archive_coverage.csv:1-6`, retained as a stale artifact whose
  99.44 percent rated-coverage interpretation is invalid
- `paper/data/final_policy_era_census.csv:1-4`
- `paper/data/final_policy_two_window_census.csv:1-6`
- `paper/data/submitted_agent_leaderboard_snapshot.csv:1-3`
- `paper/data/submitted_agent_bank_manifest.csv:1-80`
- `paper/data/persuasion_parser_coverage.csv:1-4`

## 2. Evidence classes used in this note

| Class | Definition | What it can establish |
|---|---|---|
| `RAW` | Immutable or append-only local observation from a live process, collector, API capture, or canonical game file | What was locally recorded, with the logger and join limitations stated |
| `DERIVED` | Aggregate, model, figure input, or summary computed from raw records | Arithmetic and descriptive summaries if the transformation is reproducible |
| `SIM` | Arena, paired simulation, synthetic fixture, or reachability run | Mechanical behavior in the simulator, not live efficacy |
| `RETRO` | Counterfactual replay on previously observed trajectories | Pointwise changes under the replay assumptions, not opponent response to an unplayed action |
| `RCT` | Prospective per-game randomized assignment with all-assignment analysis | A causal estimate only under the assignment, join, stopping, and interference assumptions |
| `OPS` | Deployment, bank, rating, process, or configuration receipt | Operational chronology and provenance, not policy efficacy |

These classes must not be pooled into one sample size or one conformance rate.
In particular, the 25-game live bargaining reach audit, the 800-game
negotiation simulation, and the 245-game focal local census answer different
questions.

## 3. Programmatic storage inventory

The repository-wide extension scan excluded `.git`, `.venv`, generated
Overleaf output, and temporary render directories. It found 19 CSV files under
`paper`, 27 JSONL files and 352,933 JSON files under `logs`, 12 JSON transcript
exports under `transcripts`, 39 JSON model artifacts under `models`, 23 JSON
operational records under `.ai`, 12 JSONL mirrors plus one SQLite database
under `opponent_intelligence`, and seven `.log` files under `logs`. The scan
also found operational `.out` files, which are discussed below but are not
action-level evidence.

The repository-local `.claude/worktrees/` tree is approximately 115 MiB and
contains 597 JSON files across historical worktree copies. These are duplicate
repository snapshots, not independent observations, so they were inventoried
but excluded from every empirical denominator. They are distinct from the two
external Claude conversation JSONL files audited in Section 10.4.

### 3.1 Per-game canonical stores

Counts and exact byte totals below are from the cutoff scan. The `randomized`
collector was still backfilling, so that row is explicitly moving.

| Store | Per-game JSON files | Exact bytes | Status and use |
|---|---:|---:|---|
| `logs/champion/games/` | 76,712 | 1,108,171,436 | Development archive, moving-history context |
| `logs/composite/games/` | 46,316 | 664,254,387 | Focal submitted-profile canonical archive, frozen lifetime denominator |
| `logs/hardliner/games/` | 81,509 | 1,155,778,809 | Development archive |
| `logs/conceder/games/` | 88,212 | 1,201,657,013 | Development archive |
| `logs/randomized/games/` | 53,246 | 758,629,519 | Moving collector at cutoff, not a frozen denominator |
| `logs/champion.pre-fix/games/` | 107 | 1,327,753 | Small historical pre-fix archive |
| `logs/hardliner.pre-fix/games/` | 118 | 1,432,036 | Small historical pre-fix archive |
| `logs/conceder.pre-fix/games/` | 120 | 1,552,488 | Small historical pre-fix archive |
| `logs/randomized.pre-fix/games/` | 112 | 902,698 | Small historical pre-fix archive |
| `logs/the_one_and_only/games/` | 527 | 6,180,339 | Late operational run, not focal evidence |
| `logs/the_one_and_only_continuous/run_0001_20260829T211903Z/games/` | 5,928 | 83,552,919 | Late continuous run, not focal evidence |

`du -sh` reported approximately 21 GiB under `logs/`. No whole-store hashing
was performed because it would add cost without resolving the missing owner or
process receipt.

### 3.2 Main flat JSONL streams

All rows in the streams below parsed as valid JSON in the bounded audit. Turn
timestamp spans are event-time spans from the `ts` field. Result `ts` is a
collector timestamp, so it should not be substituted for game start time.

| Store | Turn rows | Turn bytes | Turn `ts` span, UTC | Result rows | Result bytes |
|---|---:|---:|---|---:|---:|
| `logs/champion/` | 856,912 | 3,448,396,533 | 2026-08-19T10:47:06Z to 2026-08-29T11:44:09Z | 53,437 | 196,655,667 |
| `logs/composite/` | 517,261 | 2,090,953,409 | 2026-08-19T13:07:06Z to 2026-08-30T11:59:57Z | 24,803 | 91,547,217 |
| `logs/hardliner/` | 926,838 | 3,597,000,654 | 2026-08-19T10:47:09Z to 2026-08-30T12:00:49Z | 55,721 | 208,049,769 |
| `logs/conceder/` | 951,853 | 3,501,333,891 | 2026-08-19T10:47:09Z to 2026-08-30T12:00:18Z | 65,832 | 229,976,435 |
| `logs/randomized/` | 758,215 | 2,965,232,859 | 2026-08-19T10:47:08Z to 2026-08-30T12:23:45Z | 49,633 | 186,996,242 |
| `logs/the_one_and_only/` | 5,007 | 16,041,412 | 2026-08-29T12:57:24Z to 2026-08-29T14:07:12Z | 527 | 1,621,940 |
| continuous run 1 | 65,723 | 241,181,027 | 2026-08-29T21:19:09Z to 2026-08-30T12:00:00Z | 5,928 | 21,342,212 |

The four pre-fix pairs contain 5,316 turn rows and 457 result rows. Their turn
spans begin at epoch 1787134023.192735 or later and end by
1787136358.384394. They document early collection repair, not the final era.

Other top-level JSONL records are narrower operational sources:

| File | Rows at cutoff | Class | Appropriate use |
|---|---:|---|---|
| `logs/turns.jsonl` | 167 | `RAW` | Earliest small live-turn stream only |
| `logs/results.jsonl` | 8 | `RAW` | Earliest small result stream only |
| `logs/experiment.jsonl` | 40 | `SIM` | Synthetic framing fixture, never live final evidence |
| `logs/ratings_history.jsonl` | 1,363 | `OPS` | Descriptive rating trajectory; append-only and moving at cutoff |
| `logs/peak_events.jsonl` | 1 | `OPS` | Private peak-bank receipt; contains identifiers and process metadata |

The `.out` and `.log` files in `logs/` can support launch, collector, watcher,
and bank chronology. They do not contain a complete action-level owner trace.
`logs/sweeps/` contains 18 files totaling 68,442 bytes and is `SIM` or search
output, not raw live evidence.

### 3.3 Canonical schemas and join keys

Flat turn rows use these top-level fields:

```text
action, action_type, error, game_family, game_id, opponent, phase, plan,
round, source, stage, state, ts, your_player
```

`error` and `stage` are optional in older rows. Flat result rows contain
`ts`, `game_id`, and `final`. Canonical per-game JSON contains:

```text
game_id, game_family, your_player, opponent, status, config, result,
our_payoff, opponent_payoff, rounds_played, history, our_turns
```

The primary join is `game_id`. Within a canonical game, `our_turns[*].ts` is
the stable row key used to reconcile the nested turn to the flat stream. No
duplicate `ts` occurred within the 2,288 focal actions. The exact-match audit
used `ts`, `action`, `source`, `plan`, and `error`, not timestamp alone.

`state` is the serialized state visible to the agent at its turn. It is not a
public-data label and does not mean every field was visible to every role. It
can contain role-private values and interaction text, so it belongs inside the
private evidence boundary.

Family-specific visible state is stored in `config` and `history`:

- Bargaining config records information, horizon, maximum rounds when visible,
  communication, money, discount factors when visible, and proposer. History
  records round, proposer, offer, decision, and response time.
- Negotiation config records information, horizon, communication, roles, and
  values when visible. History records round, offer, counter or decision,
  deciding player, and response time.
- Persuasion config records the prior, payoffs or values when visible, price,
  seller knowledge, message type, and 20-round horizon. History records seller
  signal, buyer choice, revealed quality when available, payoff, and response
  time.

Absent private values in a partially informed configuration are information
structure, not logger missingness. Analyses must distinguish "not observed by
the agent" from "failed to log."

## 4. Focal lifetime reconciliation

The official closed snapshot in
`paper/data/submitted_agent_leaderboard_snapshot.csv:3` reports rank 2 in the
agent track, public combined rank 3, displayed rating 2590.02, and 46,564 total
games. Family totals are 15,639 bargaining, 15,415 negotiation, and 15,510
persuasion.

The official and local counts have different units:

```text
official stream: 46,564 rated-game increments
local stream:    46,316 assignment records
                 = 46,079 completed
                 +    222 failed terminal assignments
                 +     15 active records
```

Direct classification of every local canonical file gives:

| Canonical local status and result outcome | Count |
|---|---:|
| `completed`, agreement | 22,999 |
| `completed`, persuasion completion | 15,306 |
| `completed`, rated no-deal outcome | 5,597 |
| `completed`, walk | 2,177 |
| `no_deal` status, timeout | 221 |
| `no_deal` status, invalid moves exceeded | 1 |
| `active` | 15 |
| Total | 46,316 |

The 46,079 completed records sum exactly across the first four rows. The 222
failed terminal assignments are 221 timeouts and one invalid-move ending. The
two-window data independently show that a timeout assignment does not increment
the rated-game count. Therefore `46,079 + 222 = 46,301` is a valid count of
local records with terminal status, but it is not a valid numerator for the
46,564 rated-game denominator.

If every locally completed record corresponds to one official rated increment,
then `46,564 - 46,079 = 485` rated games are absent at the count level and local
rated coverage is 98.96 percent. That one-to-one mapping remains an assumption
because the official close source supplies an aggregate count rather than a
public row-level ID list. The identities, strata, and missingness mechanism of
the conditional 485-count gap cannot be recovered from the aggregate alone.
Lifetime complete-case analyses require either a row-level official join or
explicit adverse bounds.

The 24,803 unique flat result IDs are not a contradiction. The canonical
per-game collector recovered substantially more completed games than the flat
result stream. `unique_flat_result_ids`, `unique_per_game_records`, completed
local records, and terminal-status records are distinct pipeline stages. The
existing labels in `paper/data/log_archive_coverage.csv:1-2` must not be read as
one nested rated-game flow.

## 5. Exact two-window reconstruction

The windows are half-open intervals on local turn time:

```text
pre-close: [1787981256.596627, 1788007688.480755)
close:     [1788088111.586000, 1788091197.873000)
```

Their UTC boundaries and frozen summaries appear in
`paper/data/final_policy_two_window_census.csv:1-6`.

### 5.1 Games, roles, outcomes, and actions

| Window and family | Games | Role split | Rated and terminal result | Own action records |
|---|---:|---|---|---:|
| Pre-close bargaining | 19 | 9 player 1, 10 player 2 | 19 agreements | 97 |
| Pre-close negotiation | 19 | 10 seller, 9 buyer | 13 agreements, 3 walks, 3 no-deals | 190 |
| Pre-close persuasion | 25 | 11 seller, 14 buyer | 25 completed | 500 |
| Close bargaining | 152 | 80 player 1, 72 player 2 | 152 agreements | 904 |
| Close persuasion | 30 | 11 seller, 19 buyer | 29 rated completions, 1 timeout | 597 |
| Total | **245** | | **244 rated, 1 timeout** | **2,288** |

The combined family mix is highly selected: 171 bargaining games, 19
negotiation games, and 55 persuasion games. These are 69.8%, 7.8%, and 22.4%
of the 245 games. Negotiation has no close-window exposure. The closing family
allocation was operational, not a representative sample of the competition
grid.

The raw action split is:

| Window | Bargaining | Negotiation | Persuasion | Total |
|---|---:|---:|---:|---:|
| Pre-close | 97 | 190 | 500 | 787 |
| Close | 904 | 0 | 597 | 1,501 |
| Total | 1,001 | 190 | 1,097 | 2,288 |

Pre-close phases are 59 offers, 228 decisions, 280 buyer decisions, and 220
seller-message turns. Close phases are 454 offers, 450 decisions, 377 buyer
decisions, and 220 seller-message turns. These are traffic counts, not
owner-specific behavior measures.

### 5.2 Local completeness and missingness

| Check | Pre-close | Close | Combined |
|---|---:|---:|---:|
| Unique games in flat action stream | 63 | 182 | 245 |
| Canonical per-game files found | 63 | 182 | 245 |
| Flat own-action rows | 787 | 1,501 | 2,288 |
| Exact flat-to-nested matches | 787 | 1,501 | 2,288 |
| Rows with `state` | 787 | 1,501 | 2,288 |
| Rows with `plan` | 787 | 1,501 | 2,288 |
| Rows tagged `source="heuristic"` | 787 | 1,501 | 2,288 |
| Rows with `plan.gates_fired` field | 293 | 914 | 1,207 |
| Rows with nonempty `plan.gates_fired` | 270 | 635 | 905 |
| Rows with empty `plan.gates_fired` | 23 | 279 | 302 |
| Rows without `plan.gates_fired` | 494 | 587 | 1,081 |
| Logged errors | 0 | 0 | 0 |
| Duplicate nested turn timestamps | 0 | 0 | 0 |

Zero logged errors means the logger did not record an error in these rows. It
does not prove absence of unlogged process failures or service-side rejection.

### 5.3 Configuration support

After removing the embedded `result` field and canonicalizing each visible
config, the 245 games cover 206 distinct visible family-config combinations:
143 bargaining, 17 negotiation, and 46 persuasion. The pre-close window covers
58 distinct combinations; the close window covers 155.

Compact support facts:

- Bargaining, 171 games: 80 complete-information and 91 incomplete-information;
  90 known-horizon and 81 hidden-horizon; 86 with messages and 85 without.
- Negotiation, 19 games: 7 complete-information and 12 incomplete-information;
  11 known-horizon and 8 hidden-horizon; 13 with messages and 6 without. Both
  values are visible in 7 games and all 7 are feasible trades. The remaining
  12 expose only the role-appropriate value, so feasibility is not observable
  from the agent-visible state.
- Persuasion, 55 games: 30 cases where the seller knows quality and 25 where it
  does not; 24 binary-message and 31 text-message games.

This is useful support description, but it does not make the sample
representative of all configurations or of the lifetime adaptive profile.

## 6. Why full final-era owner conformance is not in the raw logs

The intended conformance estimand needs at least:

```text
eligible state -> selected owner -> specified action -> pre-coercion candidate
-> postguard or coercion -> returned local action -> server receipt -> outcome
```

What the two-window archive retains is:

| Stage | Retained for all 2,288? | Evidence boundary |
|---|---|---|
| Visible state | Yes | Local serialized `state` |
| Plan object | Yes | Heterogeneous branch diagnostics, not a fixed schema |
| Owner eligibility | No | Some branch-specific gates exist, no exhaustive eligibility vector |
| Selected owner | No | `plan.component` exists for 220 actions only |
| Pre-coercion candidate | No | Not logged uniformly |
| Returned local action | Yes | `action` and `action_type` |
| Local fallback or override reason | Partial | Branch-specific plan keys only |
| Canonical game join | Yes, 245 of 245 games | Assignment and local terminal join |
| Independent server receipt for every action | No | Canonical history is not a per-action acknowledgement stream |
| Joined rated outcome | 244 of 245 games | One timeout is retained in the denominator |

`plan.gates_fired` must not be summed as an owner census. Only 905 of 2,288
rows contain nonempty gate data. Multiple gates can appear on one action,
fields differ by family and branch, and absence can mean either ineligibility
or noninstrumentation. Similarly, the universal `source="heuristic"` label is
consistent with the logger's deterministic-path convention but does not
distinguish the policy owner inside that path or, by itself, prove that no
unlogged upstream model call occurred.

The strongest presently defensible statement is:

> In two bounded final-policy windows, the local archive contains all 245
> observed assignments, 2,288 own-action records, and 245 canonical game
> joins. Every own-action record has state, plan, and returned action, and none
> logs an error. The archive does not retain a uniform owner-selection trace or
> independent service receipt, so exact owner-specific conformance is not
> estimable from the original records.

## 7. Feasible reconstruction and its limits

A privacy-safe retrospective conformance reconstruction may be technically
possible if all required dependencies and state are recoverable and the
following work is done outside the live fleet:

1. Create an immutable worktree at the banked source commit recorded in
   `paper/data/submitted_agent_bank_manifest.csv:2`.
2. Load the exact effective defaults, 81-key overlay, and required fitted
   assets recorded by the bank and policy manifests.
3. Replay each archived pre-action visible state through an isolated dispatcher
   instrumented to emit eligibility, selected owner, specified action,
   pre-coercion action, returned action, override, and fallback.
4. Compare replay output with all 2,288 archived local returned actions.
5. Report raw numerator and denominator by family and owner for eligible,
   selected, specified, exact returned match, override, fallback, unresolved,
   and joined outcome. Keep the timeout and every unresolved row visible.
6. Validate a predeclared receipt sample against canonical histories where the
   service representation is comparable. Do not call this full wire receipt.

The output class would be `RETRO+MECH`, not `RAW` and not `RCT`. A replay match
can establish that frozen code reproduces an archived local action from an
archived visible state. It cannot prove that the original live process loaded
that commit. The bank manifest provides commit and hash evidence, but the
current archive does not contain a complete process-to-commit receipt for both
windows. The current verifier also imports the mutable working tree, so it is
not itself proof of banked production equivalence.

If the source receipt cannot be strengthened, the paper should use the
returned-action coverage matrix recommended in
`paper/review/harsh_review_2026-08-30/figure_recommendations.md:58-81`, not a
fabricated owner-conformance plot.

## 8. Other evidence populations, kept separate

### 8.1 Live bargaining reach audit

The pooled narrow bargaining audit covers 25 finalized games, with 23
agreements and two no-deals. It reports 153 of 153 eligible turns fired and
changed the returned action versus its control path, with no logged errors.
The operational source is `.ai/HANDOFF.md:4013-4033` and the released aggregate
is `paper/review_artifact/data/outcome_summary.csv:2-3`.

Class: `RAW+DERIVED+MECH`, descriptive. It is a three-profile selected cohort,
not the focal 245-game all-owner census and not a causal efficacy estimate.

### 8.2 Negotiation owner reachability

An exact paired policy simulation over 800 sampled negotiation games and 6,188
decision states reports 6,188 eligible states fired and 3,274 returned actions
changed. Sources: `.ai/HANDOFF.md:3568-3629` and
`paper/review_artifact/data/outcome_summary.csv:4-5`.

Class: `SIM+MECH`. It supports mechanical reach in the simulator. It does not
show that 6,188 live focal actions occurred, that the branch improved rating,
or that final-era live negotiation conformed.

### 8.3 Persuasion parser failure audit

The private pre-close raw archive supports an exact parser rerun over 25
persuasion games, 14 buyer-role games, and 280 buyer decisions. Four strict
parser misses occurred in one text-message game; all four were purchases of
LOW quality, with zero HIGH or missing quality outcomes. The reproducible
aggregate is `paper/data/persuasion_parser_coverage.csv:4`; the analysis entry
point is `paper/analysis/analyze_persuasion_parser_coverage.py`.

Class: `RAW+DERIVED`, clustered failure case. The private rerun reproduces four
selector-defined misses in that bounded cohort. It is not an estimate of
population prevalence, and it
does not establish conformance over all 1,097 persuasion actions. The public
aggregate removes messages and identifiers, so a reviewer cannot independently
reclassify the language. A stronger release would add privacy-safe classifier
labels and committed row hashes.

### 8.4 Clone checkpoint

The deidentified clone checkpoint contains 91 randomized assignments: 44
candidate and 47 control. Candidate mean rating change is +1.115909, control is
+0.246809, and the difference is +0.869101. The nominal unadjusted normal
interval is [-0.730366, 2.468567]. Candidate no-deal incidence is 6.141
percentage points higher. Sources:

- `paper/data/clone_checkpoint_deidentified.csv:1-92`
- `paper/review_artifact/data/reported_claims.csv:19-24`
- private assignment records in `.ai/NEGOTIATION_CLONE_CHECKPOINT_RECORDS_THROUGH_2306.json`

Class: `RCT` in design, descriptive and inconclusive in reporting. The run had
two looks, rating is sequential state, one host stratum was negative, and raw
game IDs plus assignment salt are excluded from the public artifact. Fourteen
later rows required deterministic multi-key recovery rather than strict direct
joins. Assignment and linkage therefore cannot be independently rederived
from the released table. The result must not be presented as a successful
causal experiment.

### 8.5 Retrospective hidden-horizon replay

The corrected accept-all-profitable replay covers 32,403 public negotiation
trajectories, a 4,050-game target cohort, 375 exposed decisions, and 156 changed
decisions. It reports exposed exact-percentile delta -0.06628 with bootstrap
interval [-0.08183, -0.05096], and cohort ITT -0.00614. Sources:
`.ai/EXPERIMENTS.md:1392-1397` and `.ai/FINDINGS.md:174-177`.

Class: `RETRO`. The derived row-level input and resampling receipt are not in
the public review artifact, so the numerical claim is currently unreproduced
for review. It also cannot identify opponent response to the unplayed action.

### 8.6 Faster-concession arena result

The corrected arena comparison reports diagnostic percentile differences
-0.0166 and -0.0182 on two seeds, with lower close rate. Sources:
`.ai/FINDINGS.md:188-191`, `.ai/HANDOFF.md:2899-2918`, and
`paper/review_artifact/data/outcome_summary.csv:11-12`.

Class: `SIM`, negative diagnostic. The appendix label saying the sign is
unresolved is inconsistent with the corrected ledger and should be repaired.

## 9. SQLite opponent-intelligence store

The database is
`opponent_intelligence/opponent_intelligence.sqlite3`, 203,939,840 bytes, with
a zero-byte WAL and 32,768-byte shared-memory file at audit. It was queried
read-only.

| Table | Rows | Join and content summary |
|---|---:|---|
| `games` | 57,793 | Primary key `encounter_id`; also contains `game_id`, slot, family, status, role, times, cells, outcomes, payoffs, and JSON features/config/results |
| `target_moves` | 9,143 | Composite key `encounter_id, ordinal`; contains action/context/normalized JSON, message class and response time |
| `tactic_matches` | 6,435 | Composite key `encounter_id, target_key`; fitted label, score, percentile, specificity, support, and reasons |
| `live_target_turns` | 6,414 | Primary key `turn_id`; contains slot, game, target, timestamp, phase, and raw record JSON |
| `streams` | 5 | Source path, inode, offset, update time |
| `meta` | 3 | Key-value metadata |

Coverage spans 2026-08-27T16:37:32Z to 2026-08-29T08:35:59Z. The `games` table
contains 19,849 bargaining, 18,103 negotiation, and 19,841 persuasion rows;
57,664 are `completed` and 129 are `no_deal`. Outcomes are 28,191 agreements,
19,787 persuasion completions, 6,780 no-deals, 2,906 walks, 118 timeouts, and 11
invalid-move endings.

The audited `games` rows have zero missing `game_id`, `start_ts`, `end_ts`,
`our_payoff`, `opponent_payoff`, `config_json`, or `result_json`. This is schema
completeness, not proof of correct extraction. The database covers only a
portion of the pre-close period and focuses on opponent behavior. It cannot
fill the final owner-conformance gap.

The 12 JSONL mirrors under `opponent_intelligence/` contain 560 named
encounters, 9,143 moves, 357 live unfinalized turns, and 6,435 tactic matches.
They mirror database subsets and add no independent denominator.

## 10. Derived models, transcript exports, operational JSON, and conversations

### 10.1 Model artifacts

`models/` contains 39 JSON files totaling 4,926,980 bytes. They are `DERIVED`,
not raw observations and not the official scorer. Important examples are:

- `models/percentile_cdf_v3.json`: schema `glee.percentile_cdf/v3`, 131,413
  games and 198 cells.
- `models/negotiation_seed_cdf_full.json`: 32,403 public games, 64,806 role
  samples, and 1,152 cells.
- `models/barg_bob_offer_v1.json`: 9,881 corpus games and 15,812 offers.
- `models/pers_buyer_prior_v1.json`: 4,191 games and six cells.
- `models/theory_decision_rules_v1.json`: built from an older 1,658-game live
  archive.

Model counts must not be cited as final-window exposure. A model's source game
count is a training or reconstruction denominator.

### 10.2 Transcript exports

`transcripts/` contains 12 JSON exports totaling approximately 38 MiB. They
span historical batches from 2026-08-20 through 2026-08-22 and include family
histories, setup, payoffs, official rating deltas, timestamps, profile labels,
game IDs, and opponent identities. They are useful for earlier strategy and
join diagnostics, but they do not cover the final two windows and cannot prove
final conformance.

### 10.3 `.ai` operational captures

The `.ai` directory includes bank and deployment ledgers, raw dashboard
captures, parsed official joins, experiment stack snapshots, and the private
91-row clone assignment record. These sources support chronology, selected
official-result joins, and operational receipts. Several raw captures contain
displayed interaction text and identities. Only deidentified aggregates should
leave the private workspace.

### 10.4 Claude conversation history

The user-provided Claude project directory contains two top-level JSONL
transcripts totaling 42,128,139 bytes and 20,668 records. The primary history
contains 19,159 records over 2026-08-19T09:14:56.038Z to
2026-08-29T18:45:30.251Z; the second contains 1,509 records over
2026-08-23T19:55:37.590Z to 2026-08-24T15:23:56.588Z. Record types include
user and assistant messages, attachments, queue operations, bridge events,
file-history records, modes, and system metadata.

These conversation logs are useful for discovering decisions and locating
receipts, but they are not independent empirical evidence. They contain user
prompts, assistant prose, tool outputs, attachments, account or organization
metadata, and possibly sensitive operational material. No raw conversation
record, session identifier, message, or attachment should enter the release.
Claims discovered there must be re-anchored to code, raw game records,
experiment ledgers, or official snapshots.

## 11. Review-criticism to source map

| Review criticism | Best available evidence object | Resolution now |
|---|---|---|
| Final-policy owner conformance is missing | `logs/composite/turns.jsonl`, canonical `games/`, bank manifest | Confirmed. Returned actions and states are complete locally; exhaustive owner and pre-coercion fields are absent. Requires retrospective instrumented replay or narrower claim. |
| Late windows are selected and unbalanced | `paper/data/final_policy_two_window_census.csv:2-6` plus raw window scan | Confirmed. 63 plus 182 games; family mix 171/19/55; no close-window negotiation. Descriptive only. |
| Lifetime coverage hides missingness | `paper/data/log_archive_coverage.csv:1-2`, official close snapshot, full canonical status and outcome classification | The existing 99.44 percent ratio is invalid because it mixes terminal assignments with rated games. Report 46,079 completed, 222 failed terminal, and 15 active local records. A 485 rated-game gap is conditional on one-to-one completed-to-rated mapping; its membership and mechanism remain unknown. |
| Clone checkpoint is weakly auditable | deidentified 91-row CSV, private assignment record, reported claims | Arithmetic reproducible. Assignment salt and IDs are withheld; recovered joins and two looks prevent a clean independent inferential audit. Keep descriptive and inconclusive. |
| Rank proxy is not validated against official scoring | local CDF models, transcript rating deltas, official aggregates | Unresolved. Models are local approximations; no frozen held-out proxy-versus-official calibration object was found. Narrow to rank-motivated proxies unless such a study is built. |
| Artifact does not reproduce the production agent | bank and asset manifests, review verifier, raw logs | Confirmed. Artifact verifies arithmetic and fixtures, not full action function, process load, private joins, assignment, or service receipt. |
| Raw action categories are too coarse | 2,288 raw `plan` and `state` objects | Partly addressable. State stratification can be derived; exact owner stratification cannot be counted without replay because plan schema is heterogeneous. |
| "Complete census" overstates execution receipt | flat-to-nested equality and 245 canonical joins | Confirmed. Use "complete local census" and keep server receipt separate. |
| Configuration support is not described | 245 canonical visible configs | Resolved descriptively: 206 distinct visible combinations and compact information/horizon/message support above. No representativeness claim. |
| Two windows lack complete process-to-commit receipts | bank manifest and `.ai/HANDOFF.md` process history | Unresolved. Repository byte equivalence is not a contemporaneous receipt that each process loaded that source. |
| Human and opponent data need a release boundary | raw logs, SQLite, transcripts, dashboard captures, conversations | Confirmed privacy risk. Release only approved aggregates or sanitized labeled records after organizer and institutional determination. |
| Faster-concession sign is called unresolved | corrected findings ledger and two-seed aggregate | Review criticism is valid. Corrected simulation is negative on both seeds and should be labeled as such. |

## 12. Privacy and release boundary

Do not release these raw sources without an explicit approved data-use plan:

- `logs/*/turns.jsonl`, `logs/*/games/*.json`, and raw results;
- the SQLite database and its JSONL mirrors;
- raw `transcripts/` exports;
- raw dashboard or official-join captures in `.ai`;
- operational `.out`, `.log`, controls, process commands, or peak receipts;
- Claude conversation JSONL, attachments, or tool outputs;
- raw game IDs, opponent identifiers, player IDs, message text, private values,
  assignment salts, credentials, or source paths that identify a person.

Potentially releasable after verification and the applicable authorization:

- aggregate CSVs already under `paper/data/` and
  `paper/review_artifact/data/`;
- a new `audit_coverage.csv` containing only cohort labels and raw aggregate
  denominators;
- sanitized owner-conformance vectors with deidentified row IDs, committed
  hashes, no messages, and no private state values;
- exact frozen source or complete pseudocode only if it excludes credentials,
  fleet controls, and exploitable deployment material.

Privacy-preserving aggregation does not itself answer whether competition
interactions involving humans may be used for research. That is an external
authorization and ethics determination, not a technical deidentification
claim.

## 13. Reproduction commands

These commands are read-only. They intentionally print counts and schemas, not
raw identities or messages.

### File and JSONL inventory

```sh
du -sh logs transcripts models opponent_intelligence paper/data \
  paper/review_artifact/data .ai

find logs/composite/games -type f -name '*.json' | wc -l
find logs/composite/games -type f -name '*.json' -exec stat -f '%z' {} + \
  | awk '{s += $1} END {printf "%.0f\n", s}'

wc -l logs/composite/turns.jsonl logs/composite/results.jsonl
jq -c . logs/composite/turns.jsonl >/dev/null
jq -c . logs/composite/results.jsonl >/dev/null
```

### Focal canonical statuses

```sh
rg -o '"status": "[^"]+"' logs/composite/games/*.json \
  | cut -d'"' -f4 | sort | uniq -c

find logs/composite/games -type f -name '*.json' \
  -exec jq -r '[.status, (.result.outcome // "null")] | @tsv' {} + \
  | sort | uniq -c
```

Expected status and outcome output at the audit cutoff:

```text
  15 active null
22999 completed agreement
15306 completed completed
 5597 completed no_deal
 2177 completed walked_away
    1 no_deal invalid_moves_exceeded
  221 no_deal timeout
```

### Parser audit

```sh
.venv/bin/python paper/analysis/analyze_persuasion_parser_coverage.py \
  --turns logs/composite/turns.jsonl \
  --since 1787981256.596627 \
  --until 1788007688.480755 \
  --expect final
```

### SQLite schema, rows, coverage, and missingness

```sh
sqlite3 -readonly opponent_intelligence/opponent_intelligence.sqlite3 \
  '.tables' 'PRAGMA table_info(games);' \
  'PRAGMA table_info(target_moves);' \
  'PRAGMA table_info(tactic_matches);' \
  'PRAGMA table_info(live_target_turns);'

sqlite3 -readonly opponent_intelligence/opponent_intelligence.sqlite3 \
  "SELECT 'games',COUNT(*) FROM games
   UNION ALL SELECT 'target_moves',COUNT(*) FROM target_moves
   UNION ALL SELECT 'tactic_matches',COUNT(*) FROM tactic_matches
   UNION ALL SELECT 'live_target_turns',COUNT(*) FROM live_target_turns
   UNION ALL SELECT 'streams',COUNT(*) FROM streams
   UNION ALL SELECT 'meta',COUNT(*) FROM meta;"

sqlite3 -readonly opponent_intelligence/opponent_intelligence.sqlite3 \
  "SELECT MIN(start_ts),MAX(end_ts),
          SUM(game_id IS NULL OR game_id=''),
          SUM(start_ts IS NULL),SUM(end_ts IS NULL),
          SUM(our_payoff IS NULL),SUM(opponent_payoff IS NULL),
          SUM(config_json IS NULL OR config_json=''),
          SUM(result_json IS NULL OR result_json='')
   FROM games;"
```

### Aggregate verifier boundary

```sh
python3 paper/review_artifact/verify_all.py
```

The command above passes in the current system Python environment. The same
command under `.venv/bin/python` currently fails its dependency preflight
because that environment lacks installed `matplotlib` package metadata.
Passing in a working environment verifies the released aggregate artifact
according to its allowlist. It does not verify production equivalence, live
assignment, private joins, selected owner, or server receipt.

## 14. Required next decision

Choose one of two scientifically honest paths before changing the manuscript:

1. **Build the retrospective conformance artifact.** Freeze the banked source,
   instrument the dispatcher, replay all 2,288 archived visible states, retain
   unresolved rows, and publish privacy-safe aggregate owner denominators plus
   source receipts. Label it retrospective local conformance.
2. **Narrow the claim.** Present the 245-game record as a complete local
   returned-action and outcome census, pair it with the separate 153-action
   live bargaining reach audit and 6,188-state simulation, and state plainly
   that exhaustive owner conformance and service receipt were not retained.

Until path 1 is complete, path 2 is the only claim supported by the existing
evidence.
