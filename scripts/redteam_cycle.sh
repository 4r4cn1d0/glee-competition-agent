#!/bin/bash
# Recurring adversarial review of the live strategy stack, run by Codex.
#
# Why on a schedule: the field adapts and we deploy, so a hole that did not
# exist this morning can exist tonight. Two of the three real defects found on
# 2026-08-22 -- the econ-stall crawl attack and the surplus probe leaking into
# our ACCEPT threshold -- were found by adversarial review, not by sweeps.
#
# Each run takes ONE surface, so consecutive runs do not re-report the same
# thing, and appends only what is NEW to .ai/REDTEAM_LOG.md.
set -u
cd "$(dirname "$0")/.." || exit 1
LOG=".ai/REDTEAM_LOG.md"
SURFACES=(
  "the bargaining accept/offer floors and their exact boundary values -- can an opponent sit just above a threshold?"
  "the negotiation acceptance path: span veto, span invariant, final-round any-positive, and how they interact"
  "the concession schedule and stall detection -- can an opponent be paced or waited out?"
  "the persuasion buyer DP and its belief update -- can a seller manipulate the posterior?"
  "cross-family: anything that reads opponent identity, or any state an opponent can manufacture"
  "VARIANCE: which live rules have the highest payoff dispersion, and which cliffs cause large swings rather than small ones"
)
IDX=$(( ($(date +%s) / 3600) % ${#SURFACES[@]} ))
SURFACE="${SURFACES[$IDX]}"
STAMP="$(date -u '+%Y-%m-%d %H:%MZ')"

PROMPT="RECURRING RED TEAM. You are the OPPONENT trying to beat our GLEE agent.

Read AGENTS.md, .ai/CURRENT_STATE.md, .ai/FINDINGS.md, and .ai/REDTEAM_LOG.md FIRST. The log lists what you have already reported -- do NOT repeat a finding that is already in it unless you have genuinely new evidence, and say what is new.

THIS RUN'S SURFACE: ${SURFACE}

Scoring is PERCENTILE against the same configuration and role, so an opponent wins by out-RANKING us, not by taking money off us. Our live flags are the composite entry in arms.json.

Report, in under 400 words:
1. NEW holes on this surface only. file:line, the exact state, what the opponent does, what it costs us in PERCENTILE.
2. For each, the fix as a DECISION RULE, not a patched constant. If the hole exists because a threshold is a cliff, say what the smooth or randomised replacement is.
3. Anything in .ai/FINDINGS.md you now believe is WRONG, with evidence.
If you find nothing new on this surface, say exactly that -- a clean report is a useful result. Do not pad.

Read-only. Do NOT edit any file. Do NOT run replay_eval, arena, redteam.py or any multi-thousand-game simulation -- this machine runs the live fleet."

OUT="$(codex exec -s read-only --skip-git-repo-check "$PROMPT" </dev/null 2>&1 | grep -v 'ERROR codex_core' | tail -60)"

{
  echo ""
  echo "## ${STAMP} — surface: ${SURFACE%% --*}"
  echo ""
  echo "$OUT"
} >> "$LOG"
echo "[redteam_cycle] appended $(date -u '+%H:%MZ') surface=$IDX"
