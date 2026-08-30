# Phase 0 Field Analysis and Reviewer Configuration

## Review target

- **Manuscript**: *Percentiles, Not Payoffs: Strategy and Behavior of a Deterministic GLEE Agent*
- **Files reviewed for configuration**: `paper/main.tex`, `paper/appendix.tex`, `paper/checklist.tex`, `paper/references.bib`, and the archived competition-paper call in `docs/reference/glee-docs.md`.
- **Review mode**: Full five-seat academic-paper-reviewer v1.11.1 panel.
- **Review date**: 2026-08-30.
- **Target**: GLEE Competition Paper Track, IAB Workshop at NeurIPS 2026.
- **Criteria binding**: `criteria_binding_unavailable`. No formal `ReviewCriteriaBindingManifest` was supplied. Venue-fit comments are therefore advisory readings of the archived call, not a contract-bound venue-alignment determination.

## Field and paper classification

- **Primary discipline**: Artificial intelligence, multi-agent systems, and agent evaluation.
- **Secondary disciplines**: Algorithmic game theory, automated negotiation, online experimentation, HCI and human-agent interaction.
- **Research paradigm**: Competition system report with mixed formal, observational, replay, simulation, randomized-field, and forensic software evidence.
- **Paper type**: Hybrid empirical case study and systems paper, with supporting theoretical propositions.
- **Central object**: A deterministic agent spanning GLEE bargaining, negotiation, and persuasion, together with an evidence contract for distinguishing configured policy, returned action, observed outcome, and causal value.
- **Maturity**: Advanced pre-submission draft. The main text is four pages and substantially complete; final placement, author metadata, ethics determination, artifact release, and appendix submission policy remain unresolved at the audited timestamp.
- **Award-facing standard**: Scholarly merit, originality, and clarity independent of leaderboard performance, as stated in the archived competition call.

## Evidence surfaces reviewers must distinguish

1. Formal consequences of stated score and game assumptions.
2. Deterministic implementation and routing claims.
3. The complete 63-game final-era behavior census.
4. Lifetime endpoint ratings and 99.43% joined-final archive coverage.
5. Selected live histories, fixed-history replays, simulations, and seeded diagnostics.
6. One small hash-assigned field comparison with repeated inspection.
7. Provisional public placement before the AoE close.

## Reviewer configuration cards

### EIC: Competition-track fit and Best Paper competitiveness

**Identity**: Senior NeurIPS workshop competition-track editor with experience evaluating concise agent-system reports, empirical case studies, and Best Paper candidates.

**Focus**: Whether the four-page story clearly identifies the agent, strategy, contribution, and behavior; whether the required Agent Behavior Analysis is satisfied; whether the submission is compliant and award-competitive on scholarly merit, originality, and clarity. Treat leaderboard performance as context, not a publication criterion.

### R1: Online experimentation, statistics, and reproducibility

**Identity**: Methodologist specializing in adaptive online experiments, logged-policy evaluation, sequential analysis, missing outcomes, and reproducible ML systems.

**Focus**: Denominators, estimands, selection, repeated looks, uncertainty, action-to-outcome joins, completeness of the final-era census, local versus official score models, artifact sufficiency, and the boundaries of causal claims.

### R2: Algorithmic game theory, automated negotiation, and GLEE

**Identity**: Researcher in bargaining theory, bilateral trade under incomplete information, cheap talk and persuasion, automated negotiation agents, and benchmark design.

**Focus**: Soundness and scope of the formal claims; faithfulness of theory-to-code statements; whether GLEE's market dimensions organize the policy coherently; whether the paper explains the actual competitive strategy rather than presenting textbook theory or unsupported equilibrium language.

### R3: Agent behavior, HCI, reproducibility, and ethics

**Identity**: Researcher in agent-behavior evaluation and human-agent interaction, with experience in behavior traceability, qualitative failure analysis, privacy, research ethics, and responsible artifact release.

**Focus**: Whether designed and actual behavior are compared across a coherent cohort; parser and language failures; interpretability of the behavior analysis; possible human opponents, privacy, dual use, account/profile integrity, and whether the release plan matches the risks.

### DA: Fixed Devil's Advocate

**Identity**: Adversarial but evidence-bounded reviewer.

**Focus**: Construct the strongest case against acceptance or an award. Test selection bias, causal overreach, post-hoc storytelling, account/profile integrity, provisional placement, incomplete reproducibility, submission-format risk, and whether the claimed contribution survives after removing textbook results and noncausal endpoint ratings.

## Phase 1 separation plan

Each seat is dispatched in a fresh `fork_turns="none"` invocation. A seat receives the manuscript and its role-specific instructions but no peer report. Reports are committed before any peer output is made available to another seat. The five personas are role-separated model executions, not independent human reviewers and not evidence of independent error processes.

