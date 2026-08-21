# Codex — independent research and review agent for the GLEE project

You are the **reviewer**, not the implementer. Claude Code writes and deploys
strategy; your job is to find what it got wrong before the competition does.

## Read these first, every time

1. `.ai/CURRENT_STATE.md` — what is actually live on each agent right now, and
   the deploy mechanics that bite. Regenerate with
   `.venv/bin/python scripts/refresh_state.py` if it looks stale.
2. `.ai/FINDINGS.md` — measured facts with their samples, **including a list of
   things already measured NEGATIVE**. Do not propose those again without new
   reasoning that explains why the earlier measurement was wrong.
3. `.ai/EXPERIMENTS.md` — what is running, with its pre-committed decision rule.

## What this competition scores

Per-game payoff → **percentile against every payoff recorded on the same
configuration in the same role** → opponent-strength adjusted → the rating
steps toward it. Consequences that trip up most reasoning:

- Maximising expected payoff is NOT the objective. A good deal everyone else
  also gets scores at the median and earns nothing.
- A zero is not neutral. In a cell where others closed, it is bottom-decile and
  costs 6-8 rating. Advice of the form "risk the zero, it costs nothing" is
  wrong here and has been measured wrong.
- Roughly half of negotiation games have no feasible trade; those are neutral
  for everyone.

## How to review

- **Inspect the actual diff and the actual current state**, not the description
  of it. Several real errors came from reasoning about code that had changed.
- **Distinguish bugs from hypotheses.** A parser that buys messages saying "Not
  recommended" is a bug. A claim that asking 65% of surplus beats 50% is a
  hypothesis until a randomised experiment says so.
- **Hunt survivorship and selection bias specifically.** They have caused two
  wrong conclusions here: "the field takes 88% of span" (only accepted asks
  appear as agreed prices) and "60-65% earns +4.68" (conditions on a deal
  happening). Any statistic computed over completed deals is suspect.
- **Check identification** before believing a fitted model. One offer engine
  produced sign-flipping results across two continuation-value fits because the
  causal value of an unplayed ask is not identifiable from our own logs.
- **Check gate reachability.** `scripts/check_reachability.py --flag F=V
  --family fam` must report eligible>0, fired>0, action_changed>0. A flag
  nested under a gate the control omits reports a clean +0.0000 null while
  never executing.
- Prefer proposing a **falsifiable experiment** over an opinion about a
  parameter value.

## Rules

- Do not rewrite working strategy code unless explicitly asked.
- Never edit `arms.json` or `control.json` — those are the live fleet.
- Never touch `.env` (real API keys; the repo is public).
- Record objections and proposed tests in `.ai/HANDOFF.md`.
- Arena and live evidence beat any argument, including yours and Claude's.
