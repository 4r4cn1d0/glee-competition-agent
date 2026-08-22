# Identical-fleet baseline

**Baseline epoch: 2026-08-22 16:24:50 IST (1787396090).**

At that moment all four live agents completed rotation onto `--probe champion`
with a byte-identical 39-flag `arms.json` entry and symmetric `control.json`
policy/families/llm tables. Verified by `scripts/verify_identical.py`, which
checks all four surfaces (arms, control, probe, running process) and passed all
three that apply while Test 4 is deactivated.

## What this window is for

Four agents running identical code answer exactly one question that nothing else
can: **what is the spread between them?** That spread is the cross-agent NOISE
FLOOR, and it is the floor under every future claim. A change smaller than it is
unmeasurable no matter how long it runs. Our prior estimate was +/-125 rating on
identical code; this window is the first proper measurement of it.

## Reading it

    python scripts/verify_identical.py --behaviour --hours <hours since 16:24>

Scope `--hours` to play AFTER the epoch above. Anything earlier mixes in the old
per-agent configurations and the spread it reports is not the noise floor -- at
15:54 that same command read spreads of 0.021 to 0.049 percentile purely because
the agents were still different.

## What the window will NOT tell you

Whether this configuration is good. That needs a change to test against it, which
is the entire point of having a clean control. Note also that the rating is an EMA
with a ~500-game time constant and these agents carry 16,000-20,000 games each, so
ratings will move only a fraction of the way toward their new level tonight.
Percentile from `live_percentile.py` responds immediately; the rating does not.

## Forecast on record, so it can be scored later

Selection-shrunk and calibrated against the server's own ratings:

| family | shrunk pct | implied | calibration | forecast |
|---|---|---|---|---|
| bargaining | 0.5070 | 2056 | +109 | ~2165 |
| negotiation | 0.5181 | 2145 | -8 | ~2137 |
| persuasion | 0.5455 | 2364 | -137 | ~2227 |
| **mean** | | | | **~2175** |

Realistic band 2150-2200. The per-family calibration offsets have +/-215 scatter
across agents, so treat per-family numbers as +/-150.

The top agent should move little (best config was already scoring ~2152); the
gain is the BOTTOM catching up -- Test 2 from 1964 and Agent 5 from 2082.

## Outstanding

Test 4 (`randomized` slot) is 403-deactivated and needs reactivating from the
dashboard. It is already configured identically and joins as a fifth sample.
