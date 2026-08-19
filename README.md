# GLEE Competition agent

An agent for the [GLEE Competition](https://glee-competition.com) (NeurIPS 2026, IAB
workshop): bargaining, negotiation and persuasion played against other agents and
humans in a shared matchmaking pool.

**No neural network, no LLM, no fitted policy in the decision path.** Three
closed-form game-theoretic solvers behind a dispatcher, wrapped in a layer whose
only job is to guarantee that whatever comes out is a move the server accepts.
Zero strategy errors and zero invalid moves across 24,000+ live scored turns.

## Why it is built this way

The scoring rules, more than the game theory, dictate the shape:

- **Percentile, not win/loss.** A payoff is ranked against every payoff earned on
  the same configuration in the same role, adjusted for opponent rating.
- **A no-deal pays $0**, at the bottom of that scale — and a deal at your own
  valuation pays zero too, which is the same thing wearing a disguise.
- **Abandoning scores at the 5th percentile.** A turn timeout or five invalid
  moves is worth strictly less than any legal move, however poor.
- **Volume is half the score.** The rating is shrunk toward 1000 by `g/(g+30)`
  and the board averages three families, with an unplayed family counting 1000.

So: a fast deterministic core, total error containment, and continuous play.

## Layout

| path | role |
|---|---|
| `glee_agent/dispatch.py` | routes each game to its family; the total safety net |
| `glee_agent/strategies/` | one solver per family — the numbers |
| `glee_agent/actions.py` | repairs any action into a legal move before the wire |
| `glee_agent/text.py` | reads opponent messages (100% on a 1,532-message live corpus) |
| `glee_agent/probes.py` | five policies: champion, hardliner, conceder, randomized, composite |
| `sim/` | local simulator of all three families, for offline tuning |
| `scripts/supervise.py` | keeps the fleet playing continuously, with per-agent experiment arms |
| `scripts/collect.py` | fetches game outcomes while play continues |
| `models/`, `analysis/`, `experiments/` | fitted artefacts and experiment infrastructure |

Two SDK behaviours make the safety net load-bearing: a strategy that raises makes
the SDK submit **nothing** — the game then dies on the 120s clock as a no-deal —
and a rejected action is **not retried**, it just burns one of five attempts. So
`dispatch.make_strategy` never raises and every action passes through
`actions.coerce`.

## The solvers

**Bargaining** solves the alternating-offers game by backward induction,
`f(k) = 1 - d_responder * f(k-1)` with `f(1) = 1`, converging to Rubinstein's
`(1 - d_opp)/(1 - d_me * d_opp)`. Parity is decisive and fully determined: Alice
proposes on odd rounds, Bob on even, verified across 949 offers with zero
exceptions. Payoffs are `u_i = g_i * d_i^(t-1)`, confirmed to the cent against
live server arithmetic.

Equilibrium is not played neat. The field enforces a **fairness threshold at 0.39
of the pot** (95% set [0.38, 0.40], p = 5e-6, replicated on exogenous randomised
offers) below which acceptance collapses to ~5–13% and is flat. So the solver
supplies the continuation value and an empirically derived floor supplies the
offer.

**Negotiation** concedes from an anchor toward a reservation on a Boulware curve,
with a hard floor at your own valuation and a margin above it, because a deal at
your valuation is payoff-identical to no deal.

**Persuasion** computes the Bayesian-persuasion lie budget
`q* = p(v - price) / ((1 - p)(price - u))`, with a Beta-smoothed buyer belief
estimated from rounds actually purchased — the only rounds where quality is
revealed.

## Running it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export GLEE_API_KEY=glee_...          # from glee-competition.com/dashboard
.venv/bin/python scripts/check_setup.py
.venv/bin/python scripts/selftest.py  # 2,077 synthetic states, no network
.venv/bin/python run_agent.py --max-games 5 --llm-mode off
```

Continuous supervised play across several agents:

```bash
.venv/bin/python scripts/supervise.py   # keeps the fleet up, restarts on crash
.venv/bin/python scripts/collect.py     # fetches outcomes while play continues
```

`scripts/supervise.py` carries an `ARMS` map assigning experiment flags per
agent, so a change can be A/B'd live against unchanged controls.

## Tests

```
.venv/bin/python -m pytest tests/ -q      # 547 tests
.venv/bin/python scripts/selftest.py      # 2,077 states, every action legal
```

The selftest matters more than the unit tests: it drives every probe through
every family, phase, seat and information condition and asserts the submitted
action is one the server will accept — including deliberately malformed states,
because a strategy that raises submits nothing and loses the game to the clock.

## Licence

MIT
