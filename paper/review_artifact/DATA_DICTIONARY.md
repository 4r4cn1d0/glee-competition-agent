# Data dictionary

All tables use UTF-8 CSV with a header row. Empty cells mean unavailable, not
zero. Counts are nonnegative integers unless a column description says
otherwise.

## `data/clone_checkpoint.csv`

A 91-row deidentified randomized checkpoint. This is the only row-level input
in the bundle.

- `row_id`: sequential row number created for the released table.
- `stratum`: anonymous analysis stratum, `S1` through `S4`.
- `arm`: `candidate` or `control`.
- `rating_change`: observed per-game rating change.
- `outcome`: `agreement`, `no_deal`, or `walk`.
- `information`: `complete` or `hidden`.
- `horizon`: `one`, `cap10`, or `unknown`.
- `messages`: whether language communication was enabled.

The table omits assignment inputs, game identifiers, values, prices, messages,
opponents, and wall-clock records.

## `data/rating_trajectory_relative.csv`

- `sequence_index`: order of authenticated aggregate checkpoints.
- `bargaining`, `negotiation`, `persuasion`: displayed family rating, or empty.
- `overall_rating`: displayed overall rating when released, or empty.
- `agent_track_place`, `overall_place`: official snapshot placement when
  released, or empty. The bundle checks the released values but cannot
  independently establish their service provenance.
- `public_games`: aggregate service count when released, or empty.
- `event`: generic event label. It is not an internal profile or deployment
  name.

The relative index replaces wall-clock information and private provenance.

## `data/outcome_summary.csv`

- `measure`: anonymous aggregate measurement.
- `estimate`: central estimate.
- `unit`: scale of the estimate.
- `sample_size`: games, turns, or seeds represented by the row.
- `lower`, `upper`: descriptive interval when available.
- `status`: evidential classification.

Rows marked `invalidated_diagnostic_sign_unresolved` preserve an early recorded
number while explicitly denying that its direction is established evidence.

## `data/archive_coverage_anonymous.csv`

- `profile_label`: anonymous focal or auxiliary label.
- `per_game_records`: unique local per-game records.
- `terminal_finals`: joined terminal records.
- `unresolved`: local records without a terminal join.
- `public_total`: aggregate service count when reconciled.
- `coverage_percent`: terminal finals divided by public total when valid.
- `comparison_status`: whether the denominator supports that comparison.

## `data/final_era_census_anonymous.csv`

- `family`: game family.
- `joined_games`: games joined across the two final-policy audit windows.
- `rated_games`: joined games with a public rated outcome.
- `timeout_games`: joined games that ended locally as timeouts and did not
  produce a public rated outcome.
- `role_a`, `role_a_games`, `role_b`, `role_b_games`: public role and count.
- `terminal_summary`: aggregate terminal outcomes.
- `recorded_action_summary`: aggregate returned actions.
- `own_action_records`: total own actions.
- `logged_errors`: local logged errors.

## `data/parser_coverage_aggregate.csv`

Each row is a declared analysis slice. It contains counts of roles, modes,
decisions, strict misses, actions after misses, and revealed outcomes. The row
named `preclose_final_policy_subcohort` is the audited 25-game pre-close
persuasion subcohort. It is not the complete two-window final-policy census.
The table omits source text, row hashes, source boundaries, and direct
identifiers.

## `data/experiment_registry_public.csv`

- `record_number`: sequential release record number.
- `record_type`: generic normalization category.
- `action_changing_reach`: whether action-changing reach was documented.
- `historically_live`: whether the candidate was historically active.
- `staged_only`: whether it was staged but not active.
- `terminal_disposition`: `adverse`, `stopped_or_superseded`, or
  `no_terminal_efficacy`.

Rows are anonymous derived records. They do not contain candidate names,
private source locations, or activation details.

## `data/reported_claims.csv`

- `claim`: stable human-readable aggregate claim key.
- `value`: released numerical value.
- `unit`: unit or scale.
- `released_source`: relative aggregate input that reproduces the value.
- `verification`: check that recomputes it.
- `boundary`: interpretation limit.
