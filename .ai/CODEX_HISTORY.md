# Codex session history — distilled

Imported 2026-09-02 from `~/.codex/sessions` (5 GLEE-cwd top-level sessions,
4,178 messages, Aug 23 - Aug 30). Raw redacted markdown: `~/Desktop/codex-glee/`.
336 subagent threads under the same cwd were excluded as execution noise.

Division of labour during the competition: Claude Code owned deployment;
Codex was the reviewer and, from 2026-08-28, an authorised deployer for
NEGOTIATION ONLY. Bargaining and persuasion deployment stayed with Claude.

## THE COMPETITION IS OVER

Closed **2026-08-30 11:59:59 UTC**. Final, verified against the official
agent and combined leaderboard APIs:

- **Agent 5: 2nd in the agent track, 3rd on the combined board**
- **Final rating 2590.02 after 46,564 games**

At 02:04 UTC on Aug 30 the board still showed 1st in agent track / 2nd overall;
the close moved it to 2nd/3rd. The paper was rewritten around the real outcome.

Anything in this repo written before Aug 30 that treats the competition as live,
or the placement as provisional, is stale. That includes most of the Claude-side
session notes, which were still tuning flags on a fleet that has since stopped.

## The paper

**"Percentiles, Not Payoffs"** — NeurIPS 2026 IAB workshop, Competition Paper
Track, single-blind (`sglblindworkshop`, `\workshoptitle{Interpreting Agent
Behavior}`), official NeurIPS 2026 kit.

- **Submission deadline: September 5, AoE.**
- Submission package: 4 main pages + references from page 5 + 7 checklist pages
  = 12 pages, one PDF. The OpenReview form exposes ONE PDF field and no
  supplement or artifact upload, so the four pages must stand alone.
- Full working version: 43 pages with technical appendix.
- Overleaf: https://www.overleaf.com/project/6a94347a04325a8d6060d641
- Private paper repo: https://github.com/4r4cn1d0/glee-neurips-2026-paper
  (8 source files only; the operational repo stays private and separate)
- The four-page submission deliberately contains **zero figures** — only
  equations and tables. The appendix keeps exactly two, both quantitative:
  the payoff-versus-rank reversal, and the authenticated rating trajectory.
- Repository suite at last run: **2,886 passing, 4 failing**, all four the
  documented pre-existing baseline (one bargaining accept-floor threshold,
  three live simulation-grid drift alarms).

### Blockers, all requiring the operator or an external party

1. Author name, affiliation and email are still placeholders (`main.tex:45`).
2. Human-opponent ethics / data-use determination. The GLEE Terms establish
   Technion approval for the ORIGINAL collection; that does not automatically
   cover an entrant's secondary analysis. Until resolved, either obtain written
   organizer confirmation plus the applicable institutional determination, or
   restrict the affected analyses to verifiably agent-only games.
3. OpenReview profiles for every author, plus the submitted agent's public ID.
4. Artifact redistribution, licensing and reviewer-access permissions.

## What the paper actually claims, and what it refuses to claim

The central discipline is separating four different scientific objects that
are easy to blur together:

- the **leaderboard endpoint** — an adaptive, account-level result over 46,564
  games, best active profile;
- the **frozen final policy** — a specification, exposed to only a small
  closing cohort;
- **individual heuristics** — reachable and audited, but not isolated;
- **behaviour audits** — execution conformance, not efficacy.

Explicitly NOT claimed: that the final policy caused the placement, that the
two rank-aware components caused it, that retained components were promoted on
measured efficacy, or that policy ownership was causally validated.

Final-era behaviour census: **245 assignments across the two final-profile
windows, 244 rated games, one timeout, 2,288 returned actions.** An earlier
draft used a 63-game cohort; the close added 181 further games on the same
LLM-off profile and unchanged overlay, so the 63 games became the deeply
audited pre-close subcohort and the rest a separately bounded extension.

At update rate eta=.002, the final games replace only ~3.7-4.9% of inherited
raw-rating state. In a 35-record experiment registry, **no named experiment
passed a precommitted efficacy-promotion rule**; components were retained for
structural, safety or operational reasons.

## Corrections the reviews forced, worth not re-deriving

- **The hidden one-round seller is not a fixed-cell optimizer.** It is a
  support-averaged seed-rank proxy: the seed CDF keys on both values, message
  mode and scale, so varying the latent buyer value changes the scoring cell.
  The banked ask is optimal under the POOLED objective only. Pooled across the
  six visible message and scale conditions, 1.2B-.01 scores .377 against .359
  for 1.5B-.01 — the ranking flips by condition.
- **The bargaining CDF is coarsened.** `barg_offer.py` keys only on money, max
  rounds, known-horizon and complete-information; it omits discount factors and
  pools roles. Write it as a coarsening map, not the exact configuration
  percentile.
- **The rating ordering result is local** — fixed current rating, positive
  update rate, fixed opponent adjustment, common scoring time and reference
  pool. It is not a theorem about the dynamic leaderboard or final placement.
- **The banked persuasion policy is not optimal Bayesian persuasion.** Where
  0 < q* < 1 the theory permits partial low-quality recommendation and the bank
  conservatively uses q=0; with hidden buyer values q* is unavailable and the
  policy falls back to a historical buy-rate heuristic.
- **Two components, not one, optimize a local rank surrogate**: Bob's
  bargaining offer floor and the hidden one-round seller.
- The live competition has **960 configurations**; the GLEE v3 benchmark paper
  reports 1,320. Do not conflate them.
- The account rule is **best active profile at the account level**, not "best of
  exactly five identities."

## Negative results the paper keeps as contributions

- **The competitor-clone study.** 154 games observed against three then-leading
  profiles produced a clone hypothesis; a game-level hash-assigned checkpoint
  reached 91 games after an earlier look; the estimate was +0.8691 with a
  [-0.7304, 2.4686] interval, no-deals increased, the focal-profile stratum was
  negative, and the clone **failed its frozen promotion rule and was rejected**.
  Because of the earlier look and profile dependence, the interval is
  descriptive, not inferential.
- **The persuasion parser failure.** Four final-era text-buyer games supplied 80
  decisions; a frozen stricter selector found four missed explicit warnings, all
  in one game, all followed by purchases, all revealing LOW quality. This is a
  production counterexample, not a 4/80 recall estimate.
- Unreachable gates, treatment leakage into a variable used by another decision,
  replay-overlay artifacts, and selection bias in "the field takes 88% of span"
  and "60-65% earns +4.68" (both conditioned on a deal happening).

## Operator preferences visible across these sessions

- No em dashes anywhere in the writing.
- Figures must earn their place. A dispatcher diagram and an audit flowchart
  were both removed for being dense, unlabelled and merely restating prose;
  every surviving visual must encode a numerical relationship and carry a real
  legend.
- Wants the result stated prominently once verified, failures kept as
  contributions, and enough implementation detail for genuine reproduction.
