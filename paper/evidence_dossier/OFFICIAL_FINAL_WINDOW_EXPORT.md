# Authenticated final-window export receipt

Status: private evidence note. The raw export is not a release artifact.

Captured from the authenticated GLEE dashboard on 2026-08-31 at
`2026-08-31T11:13:36.704Z`.

## What was retrieved

The dashboard was treated as a same-origin client for the competition JSON API.
No history cards or `Show more` controls were scraped. The extraction used:

1. `GET /api/agents` to resolve the submitted agent;
2. paginated `GET /api/games/history` requests for bargaining, negotiation, and
   persuasion;
3. `GET /api/games/<game_id>/replay` for every selected assignment, using a
   bounded concurrency pool and retry with backoff.

The union is exactly the two declared final-era windows already used by the
paper. It contains 245 unique assignments: 171 bargaining, 19 negotiation, and
55 persuasion. All 245 replay requests succeeded. There are 244 rated games
and one persuasion timeout.

The private JSON export is retained outside the repository at:

`/Users/spiderishi/Downloads/agent5_official_final_windows_2026-08-29_30.json`

Its SHA-256 is:

`b777bfc314adb7ec4a522641118a39bebe0fb9153ce98030f8eaa49c8f06ca98`

The file is 1,653,574 bytes. It must not be copied into a public Git repository,
Overleaf project, reviewer bundle, or artifact without an approved data-use
plan and sanitization.

## Local join and service receipt

The verifier is
`paper/analysis/analyze_final_window_outcomes.py`. It fails closed if an
official game is missing locally, an outcome differs, an attributed replay
action is invalid, or the ordered local and replay actions do not match after
family-specific wire normalization.

All 245 official game IDs joined to the canonical local game store. All 245
official result objects matched the local result objects. Protocol phase,
round parity, role, and the replay's `your_player` field attributed exactly
2,288 replay moves to the submitted agent. Every one matched the corresponding
local returned action and every matched replay move was marked valid.

| Family and role | Local returned actions | Exact valid replay matches |
|---|---:|---:|
| Bargaining, Alice | 427 | 427 |
| Bargaining, Bob | 574 | 574 |
| Negotiation, seller | 87 | 87 |
| Negotiation, buyer | 103 | 103 |
| Persuasion, seller | 440 | 440 |
| Persuasion, buyer | 657 | 657 |
| **All** | **2,288** | **2,288** |

Two invalid replay records were present, both opponent-owned bargaining offer
attempts. They were excluded by agent attribution. No submitted-agent move was
excluded.

This establishes bounded local-to-service receipt for these 2,288 returned
actions. It does not establish which internal owner was selected, the uniform
pre-coercion candidate, a contemporaneous process-to-commit receipt, or the
causal value of a policy component. `plan.component` exists for only 220 of
2,288 local actions, and the heterogeneous gate trace is not an owner census.

## Official displayed rating changes

The history endpoint supplies the dashboard's one-decimal displayed
`rating_delta`. Means and 95 percent game-level bootstrap intervals use 20,000
resamples with seed 20260831. These are selected, sequential final-window
descriptions, not randomized estimates.

| Family | Rated | Zero payoff | Mean displayed delta | 95% interval |
|---|---:|---:|---:|---:|
| Bargaining | 171 | 0 | +1.2608 | [0.5930, 1.9216] |
| Negotiation | 19 | 6 | -0.0526 | [-2.1684, 2.0474] |
| Persuasion | 54 of 55 | 12 | +0.7574 | [-0.3148, 1.8074] |

The role-level aggregate is preserved in
`paper/data/final_window_outcome_summary.csv`. The main asymmetries are
bargaining Alice versus Bob, +1.8640 versus +0.6061, and negotiation seller
versus buyer, +1.0900 versus -1.3222. Persuasion seller versus buyer is +1.2909
versus +0.3906. All intervals remain visible in the CSV and manuscript table.

## Frozen raw-percentile proxy

The local comparison uses the frozen 2026-08-25 pooled-CDF model with SHA-256
`dd85dcde6ec5ce671786409c6458e469fe3a218558c09ff4ef00fcdef4ada55d`.
Its family means are .5459 for bargaining, .6051 for negotiation, and .5745
for persuasion. Persuasion has proxy support for 43 rated games, not all 54.

The proxy is not the official same-configuration percentile and it omits the
undocumented opponent adjustment. The negotiation proxy mean above .60 while
the official mean displayed delta is near zero is direct evidence that the
proxy must not be presented as the competition score or as validation of the
rank-aware components.

## Privacy and release boundary

The raw replay payload contains game identifiers, messages, private values,
timestamps, opponent-linked records, and one human opponent. It stays private.
The repository contains only:

- the aggregate outcome CSV;
- a non-transcript export manifest and source hash;
- the verifier code;
- manuscript statistics derived from those aggregates.

Before public release, the verifier should accept an organizer-approved
sanitized schema or synthetic fixture so that reviewers can run it without
receiving raw participant trajectories.
