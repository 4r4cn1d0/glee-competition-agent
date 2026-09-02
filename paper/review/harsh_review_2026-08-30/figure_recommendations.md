# Figure and Table Decisions

## Bottom line

Add **one new evidence-bearing visual at most**. Move and revise **one existing empirical figure**. Do not add an architecture diagram, decorative game tree, competitor chart, raw-action bar chart, or clone forest plot.

The paper is already dense. A visual earns space only if it resolves a relationship that prose or a compact table cannot show as clearly.

## Priority 1: owner-conformance figure, if the missing receipts can be recovered

This is the strongest possible new figure because it directly answers the required Agent Behavior Analysis question.

### Question answered

For the focal final-era actions, where did the declared owner become eligible, win precedence, produce an independently predicted action, survive postguards, and reach the returned wire action?

### Proposed design

Use a compact horizontal stage plot or annotated matrix.

Rows:

- bargaining P2 commitment owner;
- bargaining generic owner;
- negotiation structural owners;
- negotiation fallbacks;
- persuasion posterior and reset path;
- persuasion final decline veto.

Columns:

1. eligible;
2. selected;
3. independent specification available;
4. exact post-coercion match;
5. downstream override;
6. legal fallback;
7. unresolved;
8. joined outcome.

Each cell must contain the raw count. If a fraction is shown, print numerator and denominator. Missing evidence must remain visible and must not be removed from the denominator.

### Encoding

- Use text and border or hatch patterns, not color alone.
- Green may mean observed exact match, amber may mean partial stage evidence, gray with `NR` must mean not retained, and red may mean mismatch or fallback.
- The legend must define every encoding and must say that unmatched, unresolved, and not-retained are different states.
- Do not compute a single overall coverage percentage unless every row has a comparable universe and the weighting rule is predeclared.

### Caption requirements

Define `eligible`, `selected`, `specified`, `returned`, `override`, `fallback`, `unresolved`, and `joined`. State whether the cohort is the 63-game close window or all 245 final-window games. State that exact local conformance does not prove server receipt.

### Publication condition

Publish this figure only if a frozen table and generator can reproduce every cell. Suggested artifact file: `audit_conformance.csv`. The verifier should fail if a denominator changes or if a required stage is absent.

## Fallback Priority 1: returned-action audit coverage matrix

If exact final-era conformance cannot be reconstructed, do not fabricate a conformance plot. Use a matrix that exposes the evidence boundary.

### Proposed rows and frozen denominators

| Evidence cohort | Audit universe | Eligible state | Selected owner | Returned action | Joined outcome |
|---|---|---|---|---|---|
| Focal live two-window census | 245 games, 2,288 own actions | Not retained | Not retained | 2,288 logged | 245 local joins, 244 rated, 1 timeout |
| Pooled live bargaining owner audit | 25 finalized games | 153 eligible actions | Not separately reported in released aggregate | 153/153 changed versus control | 25 finalized, descriptive only |
| Negotiation paired simulation | 800 simulated games | 6,188 eligible states | 6,188/6,188 | 3,274/6,188 changed | Simulation only |
| Pre-close persuasion selector audit | 4 complete games, 80 decisions | 4 warnings in 1 game | 0/4 caught by deployed decline layer | 4/4 BUY | 4/4 LOW |

### Important distinction

`Changed versus control` is not `matched the independent policy specification`. The figure and caption must say this directly.

### Space trade

This matrix must replace the current audit-contract table and claim-to-evidence table. It should not be added on top of them. It turns repeated audit prose into one visible statement about what is and is not known.

### Provenance

Freeze an `audit_coverage.csv`, its generator, and its source receipts. If the 25-game bargaining aggregate and 6,188-state negotiation aggregate cannot be released in reproducible form, do not publish the visual.

## Move existing rating trajectory into the core

The current appendix rating trajectory is the strongest existing empirical visual. It directly supports the adaptive-endpoint framing and the discussion of rating reversals.

### Required revisions

- X-axis label: `Checkpoint time (UTC)`.
- Y-axis label: `Displayed family rating`.
- Series: bargaining, negotiation, persuasion.
- Preserve distinct colors, marker shapes, and line styles.
- Label the final point directly.
- Annotate only authenticated events, such as the pre-close bank and official close.
- State that the checkpoints are selected and irregular and that connecting lines are for legibility, not interpolation.
- If per-checkpoint exposure counts are authenticated, add them as labels or a small rug. If they are not, do not infer exposure from elapsed time.

### Space trade

Use this figure on page 4 in place of the one-row result table and repeated rating chronology. State final rank and ratings in the caption or one adjacent sentence.

### Interpretation

The trajectory is descriptive. It cannot identify field drift, policy effects, opponent mix, rating-state carryover, or decay. Its value is showing why the paper treats the endpoint as an adaptive system result rather than a clean final-policy ablation.

## Keep the payoff-versus-rank figure out of the four-page core

The repaired rank-reversal figure is mathematically correct, clearly labeled, and has a complete legend. Keep it in an authorized appendix or artifact. The finite example is short enough to state in prose in the core. The audit/conformance visual and rating trajectory answer more consequential empirical questions.

## Do not add these figures

### Architecture or router flowchart

The earlier diagram was visually busy and evidentially weak. Boxes and arrows encouraged the reader to infer a complete implemented policy even though the paper did not establish that complete chain. Use a compact strategy table instead. Every row can state trigger, owner, action, postguard, fallback, and evidence class without suggesting more proof than exists.

### Raw action-count bars

Bargaining offers, negotiation counters, and persuasion BUY/PASS decisions have different semantics and denominators. Comparing their heights would be visually easy and scientifically meaningless.

### Clone effect or forest plot

The 91-game clone was stopped after two looks, its released assignment cannot be re-derived, rating changes carry sequential state, and the profile stratum was negative. A polished effect plot would grant this failed operational checkpoint more inferential weight than it deserves.

### Competitor comparison chart

Do not add one unless every competitor value is organizer-authenticated at the same timestamp and measured on the same scale, with a defensible denominator. A final-rank bar chart adds little beyond `2nd of 152` and invites misleading comparisons.

### Theory map or game tree

The paper does not need more conceptual decoration. It needs policy receipts and conformance denominators. Formal material should remain only where it supports an implemented and evidenced rule.

### Configuration heatmap

A coverage heatmap across 960 configurations could be useful in a supplement, but only after the focal cohort's support is frozen and labeled by family, role, horizon, information, and communication. It should not displace the conformance visual in the core.

## Proposed four-page visual budget

| Page | Main visual object | Purpose |
|---|---|---|
| 1 | No figure | Preserve space for abstract, objective, result, and contribution. |
| 2 | Compact final-policy table | Make the actual agent reconstructible at the level possible in four pages. |
| 3 | Conformance plot or audit-coverage matrix, plus compact behavior table if space permits | Answer whether behavior matched design and show evidence gaps. |
| 4 | Revised rating trajectory | Show the adaptive endpoint and reversals without claiming causality. |

If page 3 becomes too dense, combine the behavior table and conformance stages into one evidence matrix. Do not shrink text below comfortable reading size to preserve both.

## Visual acceptance checklist

Before submission, every retained visual should satisfy all of the following:

- It answers a named research or review question.
- Its cohort and denominator are in the caption.
- Its causal status is in the caption.
- Every abbreviation is defined.
- Every nontrivial encoding has a legend.
- Color is redundant with shape, hatch, border, or direct label.
- Text remains readable at 100 percent zoom and in grayscale.
- The source data and generator are frozen and verified.
- The visual replaces equal or greater prose or table space.
- Removing the visual would materially reduce understanding.
