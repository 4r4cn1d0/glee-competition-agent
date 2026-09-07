# Rank Aware Strategic Policy Design for Language Based Economic Environments

Research code, analysis, and paper materials from a second-place agent in
[Games in Language Based Economic Environments (GLEE)](https://glee-competition.com/),
the IAB Workshop competition at NeurIPS 2026.

[Paper](https://doi.org/10.5281/zenodo.22503374) ·
[OpenReview](https://openreview.net/forum?noteId=uW8cpaqXdr) ·
[GLEE documentation](https://glee-competition.com/docs) ·
[Original GLEE paper](https://arxiv.org/abs/2410.05254v3)

> **Release status.** This repository is a working research archive, not a
> sanitized, production-equivalent artifact. A future public release must exclude
> raw trajectories, player identities, messages, private values, service joins,
> and operational credentials. See [Reproducibility and scope](#reproducibility-and-scope)
> before relying on this code or mirroring the repository.

## Result at a glance

The focal competition profile finished **second in the 2026 GLEE agent track**
and third on the combined human-agent leaderboard. Its settled post-close result
was 2590.02 after 46,564 officially rated games.

| Family | Final displayed rating | Officially rated games |
| --- | ---: | ---: |
| Bargaining | 2804.82 | 15,639 |
| Negotiation | 2620.36 | 15,415 |
| Persuasion | 2344.87 | 15,510 |
| **Overall** | **2590.02** | **46,564** |

These are externally produced competition results, not an estimate from a
simulator. They belong to an evolving account with changing policies and
opponents. They do **not** show that any one final rule caused the placement.

## The problem we were actually solving

GLEE puts agents into multi-round economic games with language, private
information, incomplete information, varying horizons, and different roles:

| Family | Core decision | Central difficulty |
| --- | --- | --- |
| Bargaining | Divide a discounted pot through alternating offers | Capture value without turning a viable deal into a zero payoff |
| Negotiation | Trade a product at a price | Distinguish visible surplus from uncertain hidden values and infeasible trades |
| Persuasion | Recommend or buy a product of uncertain quality | Balance immediate value against credibility and selective feedback |

The competition does not score a simple win, loss, or expected-dollar objective.
For a payoff in a given configuration and role, GLEE first ranks it against a
reference pool of comparable payoffs and then applies an opponent-strength
adjustment. The exact adjustment and tie convention are not public. With a fixed
reference pool, expected money and expected empirical raw rank can order actions
differently, especially when an action creates more zeros or lands on a crowded
payoff atom.

That is the meaning of **rank aware** here. The system uses local raw-rank
proxies where the environment and data make them defensible. It is not claimed
to optimize GLEE's private adjusted-rating rule globally.

## What the submitted system was

The recorded configurations in the two audited final-policy windows were
deterministic and ran with language-model mode disabled. The source tree retains
optional LLM support and records earlier wording experiments, but those are not
part of the final policy described in the paper.

At each turn, an ordered dispatcher uses the observable game family, role,
horizon, information state, communication mode, own values, public parameters,
and dialogue history. The first eligible policy owner proposes an action;
postconditions and a typed legal-action normalizer attempt to repair malformed
proposals and fall back on exceptions before return.

| Layer | Responsibility | Main location |
| --- | --- | --- |
| Family dispatcher | Select a family decision path and contain exceptions | [glee_agent/dispatch.py](glee_agent/dispatch.py) |
| Theory-guided owners | Make offers, accept or reject decisions, and recommendations | [glee_agent/strategies/](glee_agent/strategies/) |
| Action guard | Coerce outputs to the server's legal schema and apply narrow numerical guards | [glee_agent/actions.py](glee_agent/actions.py) |
| Fixed empirical assets | Supply offline-fitted response estimates, priors, and policy tables | [models/](models/) |
| Per-game traces | Record proposed plans, returned actions, and rule markers for later audits | [glee_agent/gamelog.py](glee_agent/gamelog.py) |

The design deliberately separates a policy's economic claim from a safety
claim. A heuristic may be wrong about how an opponent will respond; it must not
be allowed to crash, submit an illegal object, or silently turn a measurement
into an unauditable action.

## Strategy by game family

### Bargaining: continuation value under delay

The bargaining owner starts from an alternating-offers benchmark with discounting
and finite-horizon parity. It then treats equilibrium as a reference point, not
a literal prediction of the field. Eligible states combine discounted
continuation values with empirical acceptance and payoff-rank proxies, while
hidden-horizon states use conservative clocks. A narrow, disclosed-horizon Bob
owner follows a predetermined commitment ladder derived from a terminal
discounted target.

The final audit illustrates the distinction. In a selected final-window subset,
a CDF-based offer rule changed 57 actions in 15 Bob games. Every game reached
agreement, but 14 received a negative displayed rating update, with mean change
-4.67. This is descriptive, not an estimate of the rule's causal effect.

### Negotiation: use structure without pretending hidden values are known

For complete-information trades, the policy uses explicit surplus and terminal
rules. For hidden values, it instead relies on support restrictions, observed
public prices, history-dependent bounds, and role-specific concession ladders.
Generic seller paths provide aspiration, concession, and acceptance fallbacks.
The policy never treats an unobserved hidden value or hidden zone of agreement
as known.

During development we also tested imitation of high-ranking public price paths.
The relevant checkpoint compared 44 hash-assigned candidate games with 47
controls across four development profiles. Its +0.869 rating-per-game point
estimate had a nominal 95% interval of [-0.730, 2.469], more no-deals, and a
negative focal-profile contrast. We rejected the candidate as inconclusive
rather than promote a noisy point estimate.

### Persuasion: recommendation value versus credibility

The persuasion owner uses a one-shot Bayesian-persuasion obedience calculation
as motivation, not as a claim that the repeated game is solved. Its deployed
policy combines prior value, observed purchased quality, recommendation history,
and posterior-style belief updates. A credibility reset and a final decline veto
are narrow history-based guards around buyer decisions. Seller recommendations
are conditional: the policy may recommend LOW-quality items when its prior-value
or history rule fires, and may decline otherwise.

Language was treated as part of the mechanism, not decoration. Earlier generated
wording was retired. The audited final-policy configuration used hand-controlled,
auditable action and message paths with the LLM disabled.

## How we developed it

The project was run as an adaptive live development program, not as a single
offline training run. Several policy profiles shared the same safety layer but
made deliberately different choices to generate diagnostic contrasts rather
than select among identical copies.

1. **Start from structure.** Use game-theoretic benchmarks to rule out clearly
   dominated actions and identify meaningful state distinctions.
2. **Measure field response.** Where the design allowed, retain complete
   assignment cohorts, no-deals, and timeouts, and resist statistics that
   condition only on accepted offers.
3. **Isolate uncertainty.** Behavioral changes were designed to be default-off;
   uncertain candidates were assigned per game where possible so they could be
   recovered in the logs.
4. **Verify reach and action change.** A candidate that never reaches an eligible
   state is not a null result. It is an untested candidate.
5. **Promote cautiously.** We distinguished a bug, a mechanism-safety repair,
   an observational pattern, and a causal efficacy claim. Across 35 named
   candidates in the development registry, none was promoted through a
   precommitted efficacy rule.

This process produced real negative results. Unconditional stonewalling,
broader acceptance-floor releases, generated persuasion wording, and several
negotiation concessions did not justify continued use. Those failures are part
of the research record, not omissions from it.

## Evidence and Agent Behavior Analysis

The paper's required Agent Behavior Analysis is based on two final-policy
operational windows, not an imagined static lifetime policy. It joins 245
assignments to authenticated replays: 244 rated outcomes, one timeout, and
2,288 returned actions. Every returned action in that bounded audit matched a
valid normalized replay move. This supports transmission and action fidelity;
it does not by itself establish unrecorded rule selection, parser correctness,
or causal policy effects.

| Family | Audited games | Observed outcomes | What the audit exposed |
| --- | ---: | --- | --- |
| Bargaining | 171 | 171 agreements; zero zero-payoff outcomes | Strong completion alone can still produce poor relative rank |
| Negotiation | 19 | 13 agreements, 3 walks, 3 no-deals | Some price and message checks were independently reproducible; small hidden-value slices remained uncertain |
| Persuasion | 55 | 54 rated outcomes and 1 buyer timeout | Conditional recommendation behavior and a parser miss were both visible |

The audit identified a real limitation: four warning messages in one audited
text-buyer game were not classified by the deployed decline parser, so purchases
remained possible and all revealed LOW quality. That is why the paper reports
alignment as a bounded, falsifiable claim rather than claiming that a high
placement proves perfect agent behavior.

## Repository guide

| Path | Contents |
| --- | --- |
| [glee_agent/](glee_agent/) | Runtime policy, dispatch, guards, message handling, and configuration |
| [glee_agent/strategies/](glee_agent/strategies/) | Family-specific bargaining, negotiation, and persuasion owners |
| [models/](models/) | Fixed response models, priors, acceptance artifacts, and policy tables |
| [tests/](tests/) | Unit, invariant, policy-isolation, and mechanism tests |
| [scripts/](scripts/) | Setup checks, offline diagnostics, collectors, and operational tooling |
| [analysis/](analysis/) | Offline analyses and estimators used during development |
| paper/ | Working manuscript, aggregate tables, and internal review materials; not an intended public release surface |
| paper/review_artifact/ | A limited local review bundle whose licensing and release boundary remain unresolved |

## Local verification

The following checks do not require a GLEE API key and do not queue a live
game. Use Python 3.10 or later. They are the safest way to inspect the policy
surface locally.

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/selftest.py

# Optional developer test suite. pytest is intentionally installed explicitly
# because it is not a runtime dependency.
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/ -q
~~~

Several scripts under scripts/, including run_agent.py, supervise.py, collect.py,
and fleet.py, can make authenticated requests to the GLEE service. They are not
needed to reproduce the paper's published aggregate checks; live use requires a
caller's own valid credentials.

The local review bundle in paper/review_artifact/ verifies an allowlisted,
aggregate-first subset of the paper: mathematical identities, synthetic policy
behavior, selected tables, and selected figures. It is not a released,
dependency-complete public package yet. A future sanitized archive will publish
the exact offline verification command alongside its dependencies and manifest.

## Reproducibility and scope

There are three distinct claims that should not be conflated:

| Claim | What this project supports | What it does not support |
| --- | --- | --- |
| Competition result | A captured post-close leaderboard result, reported in the paper | Attribution of second place to any single strategy revision |
| Bounded behavior audit | Replay-linked action and outcome checks for the declared 245-game window | Lifetime alignment or a causal effectiveness estimate for each rule |
| Limited artifact verification | Recomputing released aggregate arithmetic, figures, and synthetic-policy fixtures | Server replay, private scoring reconstruction, or production-source equivalence |

Raw player data, private values, interaction text, and service-side joins are
not an intended public dataset. The live environment also changed throughout
the competition, including its opponents and reference pools. Any public
release must therefore be sanitized, license-cleared, and reviewed for
participant data governance before it is treated as a reproducibility artifact.

## Responsible use

This project studies strategic behavior in settings that include negotiation
and persuasion, sometimes against human participants. High scores do not imply
fairness, welfare, or appropriateness in a real-world bargaining setting. Do
not use this code to target, profile, identify, or contact competition players.

## Citation

If this work is useful, please cite the paper rather than a mutable branch of
this working repository:

~~~bibtex
@misc{ghosh2026rankaware,
  author = {Aayush Ghosh},
  title = {Rank Aware Strategic Policy Design for Language Based Economic Environments},
  year = {2026},
  doi = {10.5281/zenodo.22503374},
  url = {https://doi.org/10.5281/zenodo.22503374}
}
~~~

## License and reuse

No repository-wide public license has been selected yet. Until one is added,
the code, paper materials, and data are not granted blanket reuse permission.
Third-party data and documentation have additional restrictions.
