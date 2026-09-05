# Core revision against the competition-paper guidance

Author-side working revision, September 5, 2026. This records the approved
rebalancing of the four-page core, not a new official peer review or a claim
that every appendix-only issue in the earlier review has been repaired.
Three bounded specialist passes checked methods, behavior aggregates, and
the revised narrative. The author remains responsible for submission.

## What changed

- The 151-word abstract explains GLEE, the second-place result, the three
  strategic families, development, and a concrete agreement-versus-rating
  finding. It does not attribute placement to an individual component.
- Section 1 states the motivation and formalizes the supplied competition
  objective, without claiming to introduce the scoring rule.
- Section 2 gives a readable decision process and separate bold paragraphs
  for bargaining, negotiation, and persuasion. It defines previously obscure
  terms and explains the reached Bob rank mixture, retained buyer price paths,
  and persuasion prior/credibility restrictions.
- Section 3 joins the three-family rating timeline to development decisions.
  It distinguishes the stopped randomized clone arm from retained buyer
  content and does not claim a qualifying efficacy result for that content.
- Agent Behavior Analysis now leads with economic outcomes and conditional
  decisions. The small table reports role-specific rating means and explicitly
  separates assigned games from rated outcomes and the buyer timeout.
- Section 5 gives bounded limitations, reproducibility, human-data handling,
  and the conclusion. The private full-draft URL is no longer presented as
  a reader-accessible artifact.
- The full hidden-seller sum was moved to Appendix B with its label preserved,
  its finite candidate set stated, and related references repaired. The dense
  core routing table was removed; detailed precedence remains in Appendix B.
- The existing timeline was retained. No figure, bibliography entry, public
  release, or checklist was added. Main-text font size and margins were not
  reduced to fit the page limit.

## New bounded behavioral evidence

`analysis/verify_core_behavior_summary.py` validates the previously captured
export hash and reuses the existing 245-game/2,288-action replay join before
printing deidentified aggregates. It reads the authorized private inputs and
does not write them or contact the service.

Verified facts used in the core:

- Negotiation includes seven complete-information and 12 hidden-information
  games. Three hidden ten-round buyer games all agreed in round 10, averaging
  -1.8 displayed rating points. One of the seven complete-information games
  ended without agreement despite positive visible surplus.
- In 22 persuasion seller games, all 230 HIGH items and 86 of 210 LOW items
  were recommended. The LOW recommendations comprise 31 prior-value-route
  decisions and 55 unknown-value/history-route decisions; 124 LOW items were
  declined.
- Across four buyer games, the recorded credibility reset changed ten BUY
  decisions to PASS and five PASS decisions to BUY.

The script also verifies the horizon counts as three one-round, eight
ten-round, and eight unknown-horizon negotiation games. It corrected an
initial manual tally before the revision was finalized. These counts and
selected slices are descriptive, not treatment effects. Plan fields do not
independently validate parsing or posterior computation.

## Review response and verification

The narrative reviewer found all six supplied topics covered and the strategy
explanation materially clearer. Follow-up corrections clarified that negative
rating updates do not imply a low raw percentile, Bob's objective weights
agreement and continuation by acceptance probability, and nonterminal buyer
ladder acceptance differs from terminal reception.

Passed:

- Frozen artifact manifest: 23 asset hashes, ordered checksum, 81 flags/defaults.
- Derived-table accounting for separate local/official populations and final
  audit denominators.
- Five theory/code verification groups, with the existing limitation that
  selected formula checks import the current checkout.
- Corrected Appendix F one-cent rank calculations.
- New final-window behavior-aggregate verifier.
- All three LaTeX builds: four main pages plus one reference page for the core,
  22 pages for the full draft, and 18 for the separate supplement.
- Visual review of every core/reference page and the changed appendix pages.
  No overfull boxes or unresolved citations/references. Underfull-box notices
  remain, with no clipping in the inspected renders.

The project suite completed with **2,885 passed and five failed** in 514.01
seconds. Four are the previously reported bargaining threshold and three
live-grid checks. The additional fleet-control test refused its bank request
because a detected process could not establish a bounded safe boundary.
This was not treated as permission to alter any running process or control.
No strategy, model, test, simulation, live-control, or log file was edited.
The suite is not reported as passing.

The prior full review remains a historical report. Appendix-only issues such
as the promotion-gate account in C and several literature analogies remain for
a separate appendix revision. Public artifact availability, appendix submission
eligibility, and human-data governance are still unresolved. No commit or
GitHub push was made in this revision.
