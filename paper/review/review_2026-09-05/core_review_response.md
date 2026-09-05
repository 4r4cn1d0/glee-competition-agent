# Core review response and revision record

September 5, 2026. This records the author-requested corrections to
`core_peer_review.md`, not a new review or an acceptance prediction. The
original review remains unchanged as the record of the earlier manuscript.

## Scope

The revision preserves the title, abstract, three-family strategy coverage,
rating timeline, outcome table, and required Agent Behavior Analysis. It does
not add a figure, checklist, new experiment, or claim of component efficacy.
The writing pass removed repeated wording to retain four main-text pages
without changing the template, font size, margins, or figure dimensions.

## Responses, one by one

### M1. Make the core self-contained about its proxies and availability

Section 2 now identifies the bargaining acceptance model as L2-regularized
logistic regression. It gives the fitted sample of 15,812 labeled offers from
9,881 fleet bargaining histories, notes pooling across roles and opponents,
and names the feature groups. These are not described as 9,881 completed
games, an all-assignment sample, or exclusively Bob observations.

The hidden one-round seller description now identifies the fixed offline
lookup, asks one cent below supported buyer values above cost, and the
equally weighted seller-role midrank criterion over four values, two message
modes, and three scales in the public GLEE negotiation seed corpus. It states
the infeasible highest-cost fallback as 4s/3, with s already defined as seller
cost. This is not an online optimizer, and its lack of final-audit exposure
remains explicit.

The absent appendix directions were removed from the core. Section 5 states
what local checks do and that production source, fitted assets, and a
production-equivalent verifier are not publicly available. A sanitized
release remains planned, not accomplished. This resolves the presentation
defect, not the external access limitation.

Appendix B was also aligned with the inspected fitter: the empirical payoff
knots pool the fleet player's own discounted payoff shares across roles,
rather than consisting exclusively of Bob payoffs.

### M2. Explain why unproven policy content remained

Section 3 now explains that buyer paths filled cases outside the structural
rules in an operator-requested deterministic replacement. It does not invent
a successful efficacy result for the stopped whole-policy clone trial.

The credibility reset is tied to its recorded intended failures: continued
buying after LOW purchases and persistent passing despite
posterior-profitable recommendations. Its operator-requested transfer before
the source experiment's efficacy read remains explicit.

The all-push result is confined to the known-prior-value branch where value
covered price. The final seller remained conditional elsewhere; the text does
not imply that universal all-push was tested and subsequently narrowed by a
new successful experiment.

### m1. Correct the trial population, endpoint, interval, and chronology

The core states 44 candidate and 47 control games across four development
profiles, identifies the nominal normal interval, and explicitly excludes
walks from the reported no-deal category. It calls this a later checkpoint
of the stopped trial, not the original stopping read.

Appendix C now uses the same interval, [-0.730, 2.469]. It distinguishes
13/44 versus 11/47 explicit no-deal outcomes from 26/44 versus 16/47 total
nonagreements including walks. The latter is descriptive and does not replace
the historical gate. The arithmetic verifier reproduces the rating contrast
of +0.869101 and the no-deal contrast of +6.141 percentage points.

### m2. Separate observed actions from proven runtime state

Section 4 now describes complete replay-linked observations after the
recorded policy boundary, with incomplete runtime provenance. It no longer
implies that a complete action join proves every process loaded the exact
recorded configuration. The working-checkout limitation remains in Section 5.

### m3. Label the theoretical assumptions

Section 1 distinguishes the illustrative exact-equality midrank example from
the unpublished official tie and opponent-adjustment conventions. Section 2
calls the bargaining recurrence a complete-information monetary-payoff
benchmark, not a rank-utility equilibrium. The existing zero-disagreement
and acceptance-at-indifference assumptions remain.

### m4. Make the outcome table denominators explicit

The table header reads "Zeros / rated games" and the caption states that
zeros are pooled across roles. It explicitly separates 32 rated persuasion
buyer games from the additional assigned buyer timeout. The six role means
are unchanged.

### m5. Explain the behavioral failure sequence

Section 4 describes the warning category without publishing private text:
a warning against purchasing the current item was not classified as a decline,
so BUY survived the intended veto and each of four purchases revealed LOW.
The four decisions came from one game. The undefined internal name "V1" was
replaced with "the deployed decline parser." No closing-window language
reclassification or full posterior validation is claimed.

### m6. Explain the timeline events

The caption identifies event 1 as code assembly from then-leading family
policies, not verified runtime activation. Event 3 is a common-policy baseline
for cross-agent variation, not a reset of competition ratings. The plotting
script's comments were corrected to match; plotted values, event times,
legend, and geometry were not altered.

## Source checks

The revision was checked against the frozen strategy commit b54cb33,
`scripts/fit_barg_bob_offer.py`, the bargaining model metadata,
`scripts/fit_official_negotiation_seed.py`, the development handoff and baseline
records, and the existing deidentified checkpoint and private replay-linked
audits. The relevant historical retention records include the August 25
deterministic negotiation replacement and August 29 persuasion transfer.
No private participant text or game identifier was added to the manuscript.

A separate source check corrected an ordering ambiguity: negotiation price
guards may run after initial API normalization. The core now says checks can
modify outputs before return, without claiming a universal normalization
order. A reader-facing closure check found M1, M2, and m1 through m6 addressed
at their requested presentation level after the small terminology and trial
chronology corrections above. This is not independent human peer review.

## Validation

Passed on this revision:

- `verify_artifact_manifest.py`: 23 policy assets, ordered checksum, 81 flags,
  and checked defaults.
- `verify_derived_tables.py`: separately verified lifecycle and official
  totals; 63-game subcohort; 245 assignments, 244 rated games, one timeout,
  and 2,288 actions; parser denominators.
- `verify_theory_code.py`: all five groups covering rank algebra, bargaining,
  negotiation, and persuasion.
- `analyze_clone_checkpoint.py`: reproduced the printed point estimate,
  nominal normal interval, profile contrasts, and explicit no-deal endpoint.
- `verify_core_behavior_summary.py`: checked the pinned private export,
  action joins, negotiation subgroups, seller recommendations, and buyer
  reset directions.
- `verify_environment_rank_ladder.py --check-manuscript`: all six printed
  currency-cent rows match the frozen seed.
- All three LaTeX targets build. The core has four main-text pages and one
  reference page; the full local draft has 22 pages and the standalone
  supplement has 18 pages.
- All core pages and the changed appendix pages were rendered and inspected.
  The core has no overfull or underfull box warnings. The other two builds
  retain two underfull paragraph warnings, without visible clipping or overlap.
- The first four pages of the core and full draft have identical extracted
  text. The manuscript sources contain no em dashes or checklist input.
- `git diff --check` passes.

The full repository suite completed in 542.47 seconds with **2,886 passed and
four failed**. The failures are the existing bargaining-floor expectation
(468 versus expected 450) and the three family-specific
`test_the_grid_still_matches_the_live_server` checks in `test_sim_grid.py`,
which compare sampled grid proportions with the stored live corpus. These
are not failed paper-arithmetic checks. This revision changes no strategy,
simulation, or test code and does not resolve those separate failures.
No live-control or fleet-process change is part of this revision. Unrelated
existing worktree changes were preserved.

Final SHA-256 receipts:

```text
main.tex
2aafb1345383b54a13485d9c56c5d5a535e9e0f78403f7c3b67e22e7e7128520
main_core.pdf
15bacf67cd6f2c33d3aab694448917ac96710219148fdefa6a2b695224522aab
main.pdf
2027eb9f85c4f10fc6cf3dbbcd3c7e7a3dccbc329d5ce084c8f8e513cf9be637
technical_supplement.pdf
2f81bc50b2b7e930828444647af7098841f2e63c7a76ee1546d189bc3b1eabb7
```

## Remaining external matters

- A reviewer-accessible artifact route or approved restricted-access route is
  not established by these edits.
- Organizer permission for technical appendices in the submission remains
  unconfirmed. The core-only PDF remains the submission candidate; the full
  draft and separate supplement are local working artifacts.
- Organizer or institutional confirmation of human-game data use remains
  unresolved. The manuscript does not claim approval.
- The revision cannot establish causal component effects, exact official
  same-cell percentiles, or full historical runtime provenance.

No files were pushed to GitHub and no commit was created by this revision.
