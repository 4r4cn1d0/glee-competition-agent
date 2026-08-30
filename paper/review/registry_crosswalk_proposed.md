# Proposed bounded experiment-registry crosswalk

Status: author-side reconstruction for audit, not yet a manuscript claim or a
public-data release.

Cutoff: the August 29 bank. The source registry is `.ai/EXPERIMENTS.md`, with
`.ai/HANDOFF.md` used only where a later activation, stop, or retrospective
disposition is absent from the experiment entry.

## Normalization rule needed to obtain 35 records

1. Collapse duplicate design, activation, and status headings for the same flag,
   salt, host cohort, and estimand.
2. Retain a replication as a separate row when it has a separately declared
   host, boundary, cohort, and decision rule. This is why the Test 3 and Test 4
   direct-decline cohorts are separate.
3. Treat the Test 4 strict-edge challenger as one named composite cohort. Its
   three component changes are not separately titled registry records.
4. Treat buyer selectivity and its independently hashed strike factor as one
   named factorial record because they share one heading, one reader, and one
   joint terminal decision. A flag-level registry would split this row and
   produce 36 rather than 35 records.
5. Collapse the two hidden-minimum-share headings because they use the same flag,
   salt, host, estimand, and cohort; the later heading is the activation update.
6. Collapse same-salt re-arms after an operational reset as deployment epochs,
   not new records. This applies to the scoped clone and post-decline pulse.
7. Keep the randomized bargaining no-regress arm and the later deterministic
   guard separate. They have different assignments, flags, and estimands; the
   randomized arm was staged and superseded before exposure.
8. Exclude the fleet-wide full-stack cutover at `.ai/EXPERIMENTS.md:2305-2329`.
   It is an administrative stop and topology epoch, not a new candidate.
9. Exclude embedded thresholds, unimplemented Stage 2/3 variants, parameter
   levels inside multi-arm probes, the `NEXT` idea list, and candidates appearing
   only in handoff notes.

The normalization in item 4 is the only material judgment required to reproduce
the manuscript's exact denominator. The source itself calls the strike factor a
separate independently assigned arm, so the manuscript should publish this
crosswalk or state the record-level convention explicitly.

## Field definitions

- `Reach`: 1 only when implementation plus a documented submitted-action change
  exists in simulation, replay, or live traces. A design-only shadow is not
  enough if the implementation was never built.
- `Live`: 1 when code containing the candidate was loaded and the relevant
  configuration was armed at least once before the cutoff. This does not imply a
  natural fire, adequate exposure, or efficacy.
- `Stage`: 1 only for a configuration staged but superseded before a
  behaviorally live cohort. The code-loaded dynamic-stop rollout is therefore
  `Live=1`, not the sole staged-only row, even though its natural mechanism fire
  was still pending.
- `Disposition`: `A` is an explicit adverse or invalid disposition; `S` is
  stopped or superseded without an efficacy verdict; `N` is no terminal efficacy
  disposition.
- No row passed a precommitted efficacy-promotion rule.

## Crosswalk

| Stable ID | Record and source location | Inclusion category | Reach | Live | Stage | Disposition | Evidence and qualification |
|---|---|---|---:|---:|---:|:---:|---|
| `REG-001` | `complete-unknown-buyer-dynamic-stop-v1`, Test 4; `.ai/EXPERIMENTS.md:3-69` | Named candidate; duplicate design/live headings collapsed | 1 | 1 | 0 | N | Exact-stack reach is 1,225/1,225/1,225 at lines 40-43. PID 57711 was code-loaded and armed at lines 3-16, but no natural fire had occurred. |
| `REG-002` | `seller-positive-pass-streak-truth-v1`, Test 4 Stage 1; `.ai/EXPERIMENTS.md:71-240` | Named candidate; shared activation update at lines 71-89 | 1 | 1 | 0 | N | Two preflights reached 371/371/371 and 326/326/326 at lines 138-146; the operator-accepted live boundary is at lines 71-89. No efficacy promotion is recorded. |
| `REG-003` | `direct-decline-safety-v1`, Test 3 replication; `.ai/EXPERIMENTS.md:71-89,242-340` | Separately enrolled replication | 1 | 1 | 0 | N | V2/V3 reach is documented at lines 272-278; the Test 3 flags were armed at lines 71-89. This remains separate from `REG-006`. |
| `REG-004` | `seller-terminal-push-v1`, Test 2; `.ai/EXPERIMENTS.md:341-434` | Named candidate | 1 | 1 | 0 | S | Reach is 117/117/117 at lines 387-394. The live cohort had 19 clean fires and was operator-terminated below its efficacy boundary at lines 341-355. |
| `REG-005` | `tight-credibility-reset-v1`, Test 2; `.ai/EXPERIMENTS.md:395-402,435-525` | Named candidate; initial cohort and retained mechanism treated as one record | 1 | 1 | 0 | N | Reach is 460/460/460 at lines 474-479 and activation is at lines 435-450. Its initial reset-only cohort was superseded, but the buyer mechanism was retained as background and later on Agent 5; no terminal efficacy verdict exists. |
| `REG-006` | `direct-decline-safety-v1`, Test 4; `.ai/EXPERIMENTS.md:527-618` | Named original-host cohort | 1 | 1 | 0 | N | Reach is 630/630/630 at lines 580-585; clean activation is at lines 527-545. The mechanism remained retained as Test 4 buyer background without a promotion verdict. |
| `REG-007` | `adaptive-credibility-v1`, Test 2; `.ai/EXPERIMENTS.md:619-730` | Named composite candidate profile | 1 | 0 | 0 | S | Component reach includes 128 V2/V3 changes plus 272/272/272 buyer-unlock and 346/346/346 seller-repair checks at lines 653-683 and 721-724. It was canceled before exposure at lines 619-629. |
| `REG-008` | Test 4 strict-edge challenger; `.ai/EXPERIMENTS.md:732-744` | Named composite cohort: direct-decline V2, zero-margin truth, and positive prose | 1 | 1 | 0 | S | The source records an armed, completed cohort and operator stop without causal verdict. Component reach is 644/644/644, 2,109/2,109/2,109, and 1,492/1,492/1,492 in `.ai/HANDOFF.md:4021-4056`. |
| `REG-009` | Complete-information unknown-horizon late stasis; `.ai/EXPERIMENTS.md:746-771` | Named candidate | 1 | 0 | 0 | N | Built default off; exact simulated reach is 4,914/4,914/4,914 on two stacks at lines 762-765. It was never run because unresolved outcomes could reverse the diagnostic sign. |
| `REG-010` | Bargaining high-share delay guard, Agent 5; `.ai/EXPERIMENTS.md:773-843` | Named deterministic candidate | 1 | 1 | 0 | A | Historical reach is 130/130/130, with live preflight 38/38/38 at lines 795-801, and it was armed at lines 802-810. Later current-stack replay found acceptance worse in 45/45 joined cases and the child unreachable; `.ai/HANDOFF.md:306-318`. This later evidence supplies the adverse disposition. |
| `REG-011` | Deterministic negotiation leader replica, Test 4; `.ai/EXPERIMENTS.md:844-888` | Named deterministic candidate lineage | 1 | 1 | 0 | N | Complete live shifts and action-source fires are documented at lines 844-888. The local decision remained KEEP/watch; narrower inherited leader logic survived in later fallbacks, but no precommitted efficacy promotion or terminal component verdict exists. This row-level disposition is inferential rather than explicit in the heading. |
| `REG-012` | First-principles terminal cells, Test 4; `.ai/EXPERIMENTS.md:890-915` | Named randomized candidate | 1 | 1 | 0 | S | A live pre-action hash cohort existed, but 64 of 82 outcomes were unresolved. Promotion was withdrawn and both cells remained pending at lines 899-915; the later fleetwide arm stop closed exposure without efficacy. |
| `REG-013` | Surplus-share response probe; `.ai/EXPERIMENTS.md:917-930` | Named randomized candidate | 1 | 1 | 0 | A | The probe was historically live on Agent 5 and Test 3; `.ai/HANDOFF.md:2820-2826`. Assignment contaminated the accept/reject target and the result join was wrong, so the experiment is explicitly invalid and must not be restored. |
| `REG-014` | Seller-message parser v2; `.ai/EXPERIMENTS.md:917,931-937` | Historical candidate | 0 | 0 | 0 | N | The registry calls it historical only and provides neither a stable implementation record nor action-changing reach. A newer tri-state parser is explicitly a separate mechanism. |
| `REG-015` | Hidden unknown-horizon first-offer greed probe; `.ai/EXPERIMENTS.md:939-980` | Named three-arm candidate | 1 | 1 | 0 | S | Shadow reach is 47 eligible, 35 fired, 35 changed at lines 970-974; three hosts were live at lines 964-969. It was later stopped by the fleetwide arm cutover without an efficacy verdict. |
| `REG-016` | Hidden cap-10 buyer-1.2 terminal counter; `.ai/EXPERIMENTS.md:982-1021` | Named randomized candidate | 1 | 1 | 0 | S | Reach is 57/20/20 at lines 1009-1018 and three hosts were live at lines 1010-1014. The fleetwide arm cutover stopped it before the frozen final. |
| `REG-017` | Broad direct-leader hidden cap-10 buyer trajectory; `.ai/EXPERIMENTS.md:1023-1070` | Named randomized candidate | 1 | 1 | 0 | S | Reach is 549/227/227 at lines 1059-1065. It was briefly live on four hosts and operator-stopped before a meaningful sample at lines 1066-1070. |
| `REG-018` | Top-four/five observable negotiation behavior, buyer only; `.ai/EXPERIMENTS.md:1072-1184` | Named randomized broad clone | 1 | 1 | 0 | S | Reach is 3,827/1,575/1,575 at lines 1132-1136. The stopped 91-game checkpoint failed the interval, no-deal, and every-host promotion gates at lines 1169-1184. Its positive point contrast and interval spanning zero do not support an adverse efficacy conclusion, so this is a stop rather than an adverse disposition. |
| `REG-019` | Hidden-information cap-10 buyer leader clone; `.ai/EXPERIMENTS.md:1186-1261` | Named randomized scoped clone; same-salt rearm epochs collapsed | 1 | 1 | 0 | S | Live host boundaries and 335/164/164 reach are at lines 1226-1243. It remained below the frozen final, and later arm/topology stops ended the cohort without efficacy promotion. |
| `REG-020` | Opus hidden unknown-horizon buyer trajectory clone; `.ai/EXPERIMENTS.md:1262-1328` | Named randomized candidate | 1 | 1 | 0 | S | Preflight reach is 241 changed actions at lines 1286-1292. Although this entry still says default off, `.ai/HANDOFF.md:3397-3422` records later arming and two official candidate outcomes; the later full-stack decision stopped it without a verdict. |
| `REG-021` | Direct-leader hidden unknown-horizon opening copy; `.ai/EXPERIMENTS.md:1329-1378` | Named randomized candidate | 1 | 1 | 0 | S | Reach is 100/49/49 and live boundaries are at lines 1361-1376. It was stopped by the later fleetwide arm cutover before its final rule. |
| `REG-022` | Hidden unknown-horizon 95%-share support ladder; `.ai/EXPERIMENTS.md:1379-1390` | Named randomized candidate | 1 | 0 | 0 | A | Implementation and live-state shadow reach of 316/159/159 are in `.ai/HANDOFF.md:1752-1787`. Independent review rejected the bundled mechanism and it was removed before deployment at lines 1381-1389. |
| `REG-023` | Hidden unknown-horizon accept-all-profitable; `.ai/EXPERIMENTS.md:1391-1402` | Named retrospective candidate | 1 | 0 | 0 | A | Corrected replay exposed 375 decisions and changed 156; the exact-percentile contrast was -0.06628. Implementation and reader were removed before deployment. |
| `REG-024` | Buyer selectivity safety factorial, including independently hashed strike; `.ai/EXPERIMENTS.md:1403-1474` | One named factorial record under the 35-row convention | 1 | 0 | 0 | A | The main and strike factors are independently assigned at lines 1408-1418, and historical reconstruction shows both action-changing surfaces at lines 1448-1463. The held-out performance claim failed and neither flag was armed; lines 1457-1474. Splitting the factor creates a 36-row registry. |
| `REG-025` | Current-offer stale-stall break; `.ai/EXPERIMENTS.md:1476-1506` | Named randomized candidate | 1 | 0 | 0 | N | Built default off. `.ai/HANDOFF.md:2927-2956` records 35-107 changed counters per major-slot shadow. It waited for an uncontaminated window and received no terminal efficacy disposition. |
| `REG-026` | Hidden support minimum-share acceptance veto, Test 3; `.ai/EXPERIMENTS.md:1507-1561,2006-2037` | One named candidate; build and activation headings collapsed | 1 | 1 | 0 | S | Exact-stack reach is 55/26/26 at lines 1556-1559; the later heading records its clean live boundary and mechanism parity at lines 2017-2024. It was stopped by the fleetwide arm cutover without the frozen final. |
| `REG-027` | Exact weak-cell token versus non-leaking prose; `.ai/EXPERIMENTS.md:1570-1659` | Named randomized candidate | 1 | 1 | 0 | S | Three exact-stack checks report 320/160/160, 220/100/100, and 160/60/60 at lines 1609-1620. The arm was live but did not reach its fixed official decision before the later stop. |
| `REG-028` | Exact zero-margin binary seller truthfulness; `.ai/EXPERIMENTS.md:1660-1769` | Named randomized candidate | 1 | 1 | 0 | S | Reach is 31/21/21 at lines 1703-1707; Test 2 and later research hosts were code-loaded and armed at lines 1726-1752. It was stopped without reaching the efficacy boundary. |
| `REG-029` | Exact buyer/text explicit-decline veto; `.ai/EXPERIMENTS.md:1770-1893` | Named randomized candidate | 1 | 1 | 0 | S | Two seeds reached 340/25/25 and 380/30/30 at lines 1868-1877; three hosts were armed at lines 1878-1887. It was later stopped without an efficacy verdict. |
| `REG-030` | Exact p=.5/r=1.2 buyer selectivity unlock; `.ai/EXPERIMENTS.md:1894-1986` | Named design record | 0 | 0 | 0 | N | The source explicitly says not built at lines 1894 and 1917-1919. A frozen predicate shadow would change 246 actions at lines 1980-1983, but that is not implemented reach. |
| `REG-031` | Continuation-aware persuasion rank gate, Test 2; `.ai/EXPERIMENTS.md:1987-2005` | Named randomized candidate | 1 | 1 | 0 | A | The live census found 828 action flips, including 539 unintended flips. It was explicitly disarmed and rejected for mechanism failure at lines 1989-2004. |
| `REG-032` | Trend-confirmed TABLE versus continuation precedence; `.ai/EXPERIMENTS.md:2038-2072` | Named randomized candidate | 1 | 0 | 0 | N | Built default off; reach is 47/19/19 at lines 2055-2065. It remained waiting for an uncontaminated window and has no terminal efficacy disposition. |
| `REG-033` | Persuasion buyer binary post-decline pulse; `.ai/EXPERIMENTS.md:2073-2191` | Named randomized candidate; same-salt rearm epochs collapsed | 1 | 1 | 0 | S | Preflight is 12/7/7 on each research host at lines 2163-2173. The arm was live, externally reset, rearmed under the same rule, and later stopped without reaching its efficacy boundary. |
| `REG-034` | Bargaining discounted reject/counter consistency A/B; `.ai/EXPERIMENTS.md:2192-2260` | Named randomized candidate | 1 | 0 | 1 | S | Exact-stack reach is 50/16/16 at lines 2248-2255. Code and overlay were prepared, but activation still awaited a code-loaded clean cycle at lines 2256-2260; the operator then zeroed randomized arms before exposure. This is the sole staged-only row. |
| `REG-035` | Deterministic discounted-counter guard; `.ai/EXPERIMENTS.md:2262-2303` | Separate deterministic candidate, not the preceding A/B | 1 | 1 | 0 | A | Reach is documented on three profiles at lines 2288-2294; `.ai/HANDOFF.md:1210-1217` confirms later code-loaded live PIDs. The human source then established that the comparator belonged only to Bob/P2 with a disclosed 12-round horizon, and the broad guard was explicitly retired as a scope error; `.ai/HANDOFF.md:4148-4158`. This is an adverse mechanism/scope disposition, not an adverse causal efficacy estimate. |

## Aggregate reconciliation

| Flow item | Reconstructed count | Rows |
|---|---:|---|
| Named candidate or cohort records | 35 | `REG-001` through `REG-035` |
| Implemented with documented action-changing reach | 33 | All except `REG-014`, `REG-030` |
| Code-loaded and armed live at least once | 25 | `REG-001`-`006`, `008`, `010`-`013`, `015`-`021`, `026`-`029`, `031`, `033`, `035` |
| Staged only | 1 | `REG-034` |
| Passed a precommitted efficacy-promotion rule | 0 | None |
| Explicit adverse disposition | 7 | `REG-010`, `013`, `022`, `023`, `024`, `031`, `035` |
| Stopped or superseded without efficacy verdict | 17 | `REG-004`, `007`, `008`, `012`, `015`, `016`, `017`, `018`, `019`, `020`, `021`, `026`, `027`, `028`, `029`, `033`, `034` |
| No terminal efficacy disposition | 11 | `REG-001`, `002`, `003`, `005`, `006`, `009`, `011`, `014`, `025`, `030`, `032` |

The 11 no-terminal rows reproduce the manuscript's explanatory partition:

- live or retained without promotion: `REG-001`, `002`, `003`, `005`, `006`,
  `011`;
- built but unrun: `REG-009`, `025`, `032`;
- not built: `REG-030`;
- historical or unclear: `REG-014`.

## Residual support limits

- The exact denominator is not unique without the normalization rules above.
  Most importantly, the source explicitly calls the strike factor independently
  assigned even though it sits inside one named factorial record.
- `REG-011` has no explicit terminal-status sentence. Its `N` disposition is
  reconstructed from the KEEP/watch record and later retention of narrower
  leader logic, while the original whole Test 4 profile was superseded.
- Several final stop labels rely on the generic fleetwide randomized-arm stop at
  `.ai/EXPERIMENTS.md:2305-2314` rather than a candidate-specific final heading.
- `REG-020` requires `.ai/HANDOFF.md` to prove that the initially default-off
  Opus arm was later armed. The experiment entry alone would undercount live
  records by one.
- The source files are structured prose rather than an immutable registry. A
  submission supplement should freeze this table as CSV and generate the flow
  counts from it instead of maintaining the aggregate numbers manually.
