# CURRENT STATE — regenerate with `scripts/refresh_state.py`

_Snapshot 2026-08-22 08:05Z · repo commit `44f20cb`_

**This file is the single source of truth for what is LIVE.** Any agent (human
or model) reasoning about strategy must read it first. Reasoning from a stale
picture of the fleet has caused real errors: a flag believed live that was only
in `arms.json`, a revert believed effective that had not reached the running
process, and an analysis of "identical" agents that in fact differed.

## Fleet

### Test 1  (slot `champion`)

- **live rating**: 2134 overall | barg 2266 nego 1964 pers 2173
- **flags (31)**: `BARG_ACCEPT_FLOOR=0.50` `BARG_FLOOR_GAIN=0.05` `BARG_OFFER_FLOOR=0.57` `BARG_OPPONENT_FLOOR=0.39` `BARG_SPE_WEIGHT=1.0` `BARG_UNCAPPED_HORIZON=60` `NEGO_ACCEPT_SPAN=0.48` `NEGO_BOUND_AS_FLOOR=1` `NEGO_CLOSE_AB=1.2` `NEGO_CONTINUATION_ACCEPT=1` `NEGO_CURVE_PRICING=1` `NEGO_DEADGAME_V1=1` `NEGO_ENDGAME_V3=1` `NEGO_HORIZON_V2=1` `NEGO_MARGIN_WEIGHT=0.40` `NEGO_MIN_MARGIN=0.02` `NEGO_POSTERIOR=1` `NEGO_SPAN_INVARIANT=0.40` `NEGO_STALL_POLICY=1` `NEGO_TABLE=1` `NEGO_ULTIMATUM_SHARE=0.80` `NEGO_ZOPA_AB=0.10` `OPP_EXPLOIT=1` `OPP_PAD=0.16` `PERS_BACKLOAD_AB=2` `PERS_BUYER_TIGHT_PRIOR=0.65` `PERS_BUYER_V2=1` `PERS_KEEP_MSG=1` `PERS_MSG_STYLE=token` `PERS_PARSE_TRI=1` `PERS_TOKEN_MAX_P=0.5`
### Agent 5  (slot `composite`)

- **live rating**: 2065 overall | barg 2056 nego 1994 pers 2144
- **flags (32)**: `BARG_ACCEPT_FLOOR=0.50` `BARG_BOB_OFFER=1` `BARG_ECON_STALL=0` `BARG_FLOOR_GAIN=0.05` `BARG_OFFER_FLOOR=0.57` `BARG_OPPONENT_FLOOR=0.39` `BARG_STONEWALL=0` `BARG_STONEWALL_MIN=0` `NEGO_ACCEPT_SPAN=0.48` `NEGO_BOUND_AS_FLOOR=1` `NEGO_CLOSE_AB=1.2` `NEGO_CONTINUATION_ACCEPT=1` `NEGO_CURVE_PRICING=1` `NEGO_DEADGAME_V1=1` `NEGO_ENDGAME_V3=1` `NEGO_FINAL_OPTION=0.6` `NEGO_HORIZON_V2=1` `NEGO_MARGIN_WEIGHT=0.40` `NEGO_MIN_MARGIN=0.02` `NEGO_POSTERIOR=1` `NEGO_SPAN_INVARIANT=0.40` `NEGO_STALL_POLICY=1` `NEGO_SURPLUS_PROBE=0` `NEGO_TABLE=1` `NEGO_ULTIMATUM_SHARE=0.80` `NEGO_ZOPA_AB=0.10` `PERS_BACKLOAD_AB=2` `PERS_BUYER_TIGHT_PRIOR=0.65` `PERS_BUYER_V2=1` `PERS_KEEP_MSG=1` `PERS_MSG_STYLE=token` `TRACE_GATES=1`
### Test 2  (slot `hardliner`)

- **live rating**: 1943 overall | barg 2057 nego 1759 pers 2013
- **flags (8)**: `BARG_OPPONENT_FLOOR=0.39` `NEGO_BOUND_AS_FLOOR=1` `NEGO_CLOSE_AB=1.2` `NEGO_ZOPA_AB=0.10` `PERS_BACKLOAD_AB=2` `PERS_KEEP_MSG=1` `PERS_MSG_STYLE=token` `PERS_PARSE_V2=1`
### Test 3  (slot `conceder`)

- **live rating**: 2127 overall | barg 2245 nego 1946 pers 2189
- **flags (32)**: `BARG_ACCEPT_FLOOR=0.50` `BARG_BOB_OFFER=1` `BARG_ECON_STALL=0` `BARG_FLOOR_GAIN=0.05` `BARG_OFFER_FLOOR=0.57` `BARG_OPPONENT_FLOOR=0.39` `BARG_SPE_WEIGHT=1.0` `BARG_UNCAPPED_HORIZON=60` `NEGO_ACCEPT_SPAN=0.48` `NEGO_BOUND_AS_FLOOR=1` `NEGO_CLOSE_AB=1.2` `NEGO_CONTINUATION_ACCEPT=1` `NEGO_CURVE_PRICING=1` `NEGO_DEADGAME_V1=1` `NEGO_ENDGAME_V3=1` `NEGO_FINAL_OPTION=0.6` `NEGO_HORIZON_V2=1` `NEGO_MARGIN_WEIGHT=0.40` `NEGO_MIN_MARGIN=0.02` `NEGO_POSTERIOR=1` `NEGO_SPAN_INVARIANT=0.40` `NEGO_STALL_POLICY=1` `NEGO_SURPLUS_PROBE=0` `NEGO_TABLE=1` `NEGO_ULTIMATUM_SHARE=0.80` `NEGO_ZOPA_AB=0.10` `PERS_BACKLOAD_AB=2` `PERS_BUYER_TIGHT_PRIOR=0.65` `PERS_BUYER_V2=1` `PERS_KEEP_MSG=1` `PERS_MSG_STYLE=token` `TRACE_GATES=1`
### Test 4  (slot `randomized`)

- **live rating**: unavailable (HTTP Error 403: Forbidde)
- **flags (22)**: `BARG_ACCEPT_FLOOR=0.50` `BARG_FLOOR_GAIN=0.05` `BARG_OFFER_FLOOR=0.57` `BARG_OPPONENT_FLOOR=0.39` `BARG_SPE_WEIGHT=1.0` `BARG_UNCAPPED_HORIZON=60` `NEGO_ACCEPT_SPAN=0.48` `NEGO_BOUND_AS_FLOOR=1` `NEGO_CONTINUATION_ACCEPT=1` `NEGO_CURVE_PRICING=1` `NEGO_DEADGAME_V1=1` `NEGO_ENDGAME_V3=1` `NEGO_HORIZON_V2=1` `NEGO_MARGIN_WEIGHT=0.40` `NEGO_MIN_MARGIN=0.02` `NEGO_POSTERIOR=1` `NEGO_STALL_POLICY=1` `NEGO_TABLE=1` `NEGO_ULTIMATUM_SHARE=0.80` `PERS_BUYER_TIGHT_PRIOR=0.65` `PERS_BUYER_V2=1` `PERS_MSG_STYLE=token`

## Deploy mechanics that bite

- `arms.json` is an OVERLAY read live (~3s). Setting a flag reaches a running
  agent immediately; **clearing a key does NOT** — `runtime_flags` falls back to
  the launch environment, so a revert needs an explicit disabling value
  (`FLAG=0`) or a rotation.
- Code changes reach an agent only at its next shift boundary (3600s).
- `check_reachability.py` must PASS (eligible>0, fired>0, action_changed>0)
  before any arena run on a new flag.

## Current experiments

- `GLEE_NEGO_SURPLUS_PROBE=1` on Agent 5 + Test 3 — randomised surplus-share
  arms {0.50..0.75} in complete-info offers; read with
  `scripts/analyze_surplus_probe.py`. NOT a policy; ~2% of games carry an
  off-policy ask.
- `GLEE_PERS_PARSE_V2=1` on Test 2 only — seller-message parser fix.
