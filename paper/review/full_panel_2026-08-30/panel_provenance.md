# Review Panel Provenance

## Execution record

- **Mode**: Full five-seat review, academic-paper-reviewer v1.11.1.
- **Panel date**: 2026-08-30.
- **Actor type**: Model for all five seats.
- **Dispatch**: Five sequential `fork_turns="none"` subagent invocations.
- **Peer-output visibility before commitment**: False. Each seat committed its report in its first turn. No report file was written until all five seats had committed, and no peer output was included in any seat's forked context.
- **Context separation scope**: Within this panel attempt only. It does not establish freshness relative to earlier reviews or future retries.
- **Criteria binding**: `criteria_binding_unavailable`.
- **Calibration**: `NOT_CALIBRATED`.

| Seat | Role ID | Invocation context | Report file | Model family | Provider | Accountable human |
|---|---|---|---|---|---|---|
| EIC | `eic` | `/root/award_narrative_review/panel_eic` | `seat_eic.md` | unknown | unknown | none |
| R1 | `methodology` | `/root/award_narrative_review/panel_r1_methodology` | `seat_r1_methodology.md` | unknown | unknown | none |
| R2 | `domain` | `/root/award_narrative_review/panel_r2_domain` | `seat_r2_domain.md` | unknown | unknown | none |
| R3 | `perspective` | `/root/award_narrative_review/panel_r3_behavior_ethics` | `seat_r3_behavior_ethics.md` | unknown | unknown | none |
| DA | `da` | `/root/award_narrative_review/panel_da` | `seat_da.md` | unknown | unknown | none |

Committed report SHA-256 values:

- EIC: f8e50ecffa0df754ee2b1d06d59021e15953c2d4b590957e4365bee901d4afd2
- R1: 6170e9791ce96a473e6aabf13fd91cb769e55e901ea61e5bbca193e661fe1bff
- R2: d430d2866cb9030ce11c8070c6149139692646fa6b2e271303f745c9dac988f5
- R3: 0b1a55c9bd97b1034a0a56c6fb45e8cffc745c54e091c70d5aae8d7dce35e077
- DA: fb47b06e0321dfbbd4181ca6bb11d8b5b4cf9a1c0fc9b8d4e25605ce4557d88c

## Provenance axes

| Axis | Status | Basis |
|---|---|---|
| Role-separated | true | Five unique, explicitly assigned roles. |
| Within-panel invocation-context separation | true | Five unique `fork_turns="none"` contexts. |
| Blind to peer outputs before commitment | true | Reports remained only in the orchestrator context until every seat committed. |
| Model-family distinct | unknown | No model override or model-family receipt was exposed by the dispatcher. |
| Provider distinct | unknown | No provider receipt was exposed by the dispatcher. |
| Human-reviewer distinct | false | No accountable human reviewer participated. |

**Binary independence claim**: Not computed. Persona and context separation establish only the named axes and do not establish independent error processes.

**Correlated-error disclosure**: Model-family distinctness is unknown, and all seats were dispatched through the same orchestration environment. Correlated model errors therefore cannot be ruled out. The panel is a structured model critique, not five independent human reviews.

## Artifact limitations

The canonical provenance builder, schemas, and pinned `reviewer_full` contract referenced by the installed skill were not present in the installed skill directory. No schema-valid typed provenance artifact or replay validation was produced. This Markdown record is an honest operational receipt, not a substitute for that unavailable artifact.

The manuscript was not hash-frozen for the duration of Phase 1. `paper/main.tex` and `paper/appendix.tex` were edited by the root authoring process while seats were running. In particular, later revisions added clearer strategy origin, owner-objective scope, adaptive-trajectory endpoint wording, and submission-package controls. The seat reports remain their committed first-turn assessments of the versions they observed. The editorial synthesis explicitly distinguishes panel findings from issues already repaired in the later current source.
