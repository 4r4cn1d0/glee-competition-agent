# Mathematics and frozen-policy review: working draft

Author-side technical review, 2026-09-05. This is an AI-assisted working draft for the accountable author, not an official venue review or an editorial decision. The intake validator returned `READY_FOR_LOCAL_REVIEW`. I read the peer-review skill and its ethical-review reference, the game-theory skill and equilibrium-concepts reference, the project state and findings, and the current experiment headings and relevant current designs. The state snapshot is dated August 30; I did not refresh live fleet state because this task concerns a frozen manuscript and policy.

## Scope and overall assessment

This pass covers the main mathematical claims, policy-to-source correspondence across bargaining, negotiation, and persuasion, and Appendices A, B, and F. Source evidence below is from `git show b54cb33:<path>`, not an assumption that the mutable working tree represents the submitted policy. I inspected selected implementation branches, the source fitter for the Bob model, and the frozen negotiation seed. The coordinator separately ran the artifact, arithmetic, and theory verifiers and handles the build and PDF review. I did not rerun live games, a full strategy replay, the arena, or red-team simulation.

The mathematical core is sound under its stated assumptions. In particular, Proposition 1 correctly separates adjusted-rank optimization from the raw-rank terminal identity, and its restrictions concerning clipping, adjustment, and reference-pool drift prevent a one-step identity from becoming an unsupported leaderboard claim. The finite bargaining recursion is correct with continuous feasible allocations, common knowledge, zero disagreement payoffs, and acceptance at indifference. The persuasion obedience bound is also correct for the stated one-shot benchmark with HIGH always recommended. I found no unresolved error in those central algebraic statements.

Most inspected final-policy routes agree with the frozen source. The strongest remaining substantive reporting concern is the core's ambiguous account of what imitation was excluded versus retained. The other findings are bounded specification or conceptual corrections. They do not establish that the observed actions or competition result are wrong.

# Comments to authors

### Major comment MC-1

Make the retained imitation component clear in the core.

- Location: [main.tex:190](</Users/spiderishi/Coding/GLEE Competition/paper/main.tex:190>), especially the negotiation exclusion entry at line 193 and the stopped-clone account at lines 278–290; [appendix.tex:420](</Users/spiderishi/Coding/GLEE Competition/paper/appendix.tex:420>).
- Observation: Table 1 lists “leader clone” among rules excluded after development, while the final route includes “leader buyer.” Appendix B explicitly says that the stopped randomized arm's broad buyer coverage was retained in the final assembly, including the adverse hidden unknown-horizon slice. The appendix resolves the distinction, but a reader of the four-page paper can reasonably infer that the tested imitation policy was removed.
- Evidence or criterion: Frozen `glee_agent/deterministic_negotiation.py:206–221` returns broad buyer coverage for `AGENT5_DEFAULT`, while `:256–294` gives the structural owners precedence. Frozen `glee_agent/top_buyer_clone.py:232–241` preserves the hidden unknown-horizon path and eight-price walk. Appendix B 420–434 correctly distinguishes stopping the randomized arm from retaining its buyer content. The issue is an ambiguous central design claim, not a newly discovered implementation contradiction.
- Why it matters: The paper treats failed strategies and final assembly as contributions. A stopped experiment and removal of the policy it tested are different facts, particularly when one negatively directed slice remains in the final agent.
- Requested action: Change the exclusion entry to “Randomized clone arm; buyer imitation retained,” or equivalent wording, and add one short sentence to the failed-clone discussion explaining the retained buyer coverage and its lack of a qualifying efficacy result. Keep the appendix's nuanced account; no new experiment is needed for this clarification.

### Minor comment MC-2

Restore the binary string `no` to the exact veto specification.

- Location: [appendix.tex:591](</Users/spiderishi/Coding/GLEE Competition/paper/appendix.tex:591>), through line 595.
- Observation: The binary V1 veto description names Boolean false and an absent-message false recommendation field, but omits the literal string `no`.
- Evidence or criterion: Frozen `glee_agent/strategies/persuasion.py:1006–1020` first handles Booleans, then strips and lowercases strings and returns false for `no`; it uses the recommendation field only when the message is `None`. The V1 veto invokes this helper at `:2844–2848`. A local extraction and execution of that exact frozen function returned false for `False`, `"no"`, and `" NO "`, and `None` for `"n"` and `"pass"`.
- Why it matters: The stated distinction between binary and text parsers is part of the paper's action-fidelity contribution. Literal `no` is an ordinary supported input, not a speculative malformed edge case, and it can change BUY to PASS.
- Requested action: State “Boolean false or the stripped, case-insensitive string `no`; when the message is absent, a false Boolean recommendation field.” The existing exclusion of aliases `n` and `pass` is correct.

### Minor comment MC-3

Distinguish the formal midrank from the Bob implementation's numerical and population details.

- Location: [appendix.tex:323](</Users/spiderishi/Coding/GLEE Competition/paper/appendix.tex:323>), through line 345; compare the exact-equality definition at lines 25–36.
- Observation: The implemented Bob rank is a tolerance-based midrank over quantile knots, and those knots pool the focal seat across Alice and Bob. Describing them as “Bob payoff shares” is inaccurate. “Ties go upward” also omits the numerical near-tie tolerance.
- Evidence or criterion: Frozen `glee_agent/barg_offer.py:142–145` uses bisect cutoffs `x-1e-9` and `x+1e-9`. At `:193–195`, a later ask can replace the selected ask when its score is within `1e-9` below the best score, not only on exact equality. Frozen `scripts/fit_barg_bob_offer.py:115–135` uses each logged game's `your_player`, without filtering to Bob, and `:251–258` compresses each retained cell to 51 knots. The paper already correctly reports that role is absent from the CDF key. A frozen-function check on `D=[.5]`, `y=.5000000005` returns `.5`, whereas the formal exact-equality midrank returns `1`.
- Why it matters: Appendix B presents itself as a reimplementation specification. A reader should not silently identify a numerically tolerant, coarsened, mixed-role scoring function with the exact empirical midrank in Proposition 1. This is primarily a precision and reproducibility issue; no material live action or outcome difference was established by this pass.
- Requested action: Say that the implementation applies a `1e-9` tolerance to the 51-knot mixed-role CDF, and that score ties within `1e-9` favor the higher ask. Replace “Bob payoff shares” with “logged own-payoff shares pooled across roles.” Preserve the exact mathematical definition in Appendix A as the formal diagnostic, rather than changing the proposition to match numerical implementation details.

### Minor comment MC-4

State the feasible ask set for the hidden-seller maximization.

- Location: [main.tex:159](</Users/spiderishi/Coding/GLEE Competition/paper/main.tex:159>), Eq. 3 and its following definitions; [appendix.tex:368](</Users/spiderishi/Coding/GLEE Competition/paper/appendix.tex:368>), through line 377.
- Observation: The objective function and its 24-cell averaging are explicit, but the domain over which the ask multiplier is selected is not. “The first three values maximize” currently leaves open whether this means all prices, all cent prices, or the finite support-aligned candidates.
- Evidence or criterion: Frozen `glee_agent/first_principles.py:305–318` selects a support value strictly above the seller cost and subtracts one cent. The supplied theory verifier at `paper/analysis/verify_theory_code.py:382–396` compares only candidate multipliers in `{.8,1,1.2,1.5}` strictly greater than the cost multiplier. Its printed score checks support the reported selections within that set: for cost `.8`, `.377128` at ask multiplier `1.2` exceeds `.271781` at `1.0` and `.359457` at `1.5`; for cost `1.0`, `.282183` at `1.2` exceeds `.250627` at `1.5`.
- Why it matters: A finite comparison over declared candidates is reproducible and appropriately narrow. An unspecified maximization can be read as a stronger optimization result than was checked. The assumptions about latent buyer types, acceptance, and averaging over visible scales are already disclosed well.
- Requested action: Define `Pi_sigma = {pi in {.8,1,1.2,1.5}: pi > sigma}`, with prices `pi B-.01`, and separate the empty-set/dead-cell convention at `sigma=1.5`. Label the rule an argmax over this candidate set. One sentence is sufficient.

### Minor comment MC-5

Remove the incorrect out-of-grid explanation for the bargaining continuation term.

- Location: [appendix.tex:284](</Users/spiderishi/Coding/GLEE Competition/paper/appendix.tex:284>), through line 287.
- Observation: The supported-grid inequality is correct, but it does not imply that the continuation term can bind “only when delta_j > 1.” The implementation treats raw and clipped discounts differently outside the supported grid.
- Evidence or criterion: Frozen `glee_agent/strategies/bargaining.py:59–79` clips both discounts to `[0,1]` inside `proposer_share`, while `:363–364` multiplies the resulting continuation share by raw `delta_me`. Extracting the frozen recursion gives, for `delta_i=1.1`, `delta_j=.9`, `k=3`, `f_i(k)=1` and `C_i/M=1.1`. Thus the continuation term exceeds the recursion even though `delta_j` is below one; the final aspiration then clips back to `M`. For the actual four-point discount grid, `C_i <= f_i(k)M` remains correct.
- Why it matters: This is a small false explanatory claim in an otherwise careful specification. It is outside the supported experimental grid and is not evidence of a live policy failure.
- Requested action: Retain the supported-grid statement and remove the “only when delta_j > 1” claim, or explicitly describe the source's out-of-grid clipping convention. There is no need to expand testing or implementation to unsupported discounts.

### Minor comment MC-6

Do not make lack of commitment a consequence of repetition.

- Location: [appendix.tex:925](</Users/spiderishi/Coding/GLEE Competition/paper/appendix.tex:925>), especially lines 927–930; compare [main.tex:173](</Users/spiderishi/Coding/GLEE Competition/paper/main.tex:173>).
- Observation: “Repeated play removes commitment” conflates two separate properties of the game. Repeated interaction can exist with a committed signal policy; GLEE's seller chooses messages sequentially without an enforceable ex ante signal-policy commitment.
- Evidence or criterion: The one-shot obedience calculation is valid for a committed policy. The frozen persuasion seller selects its current recommendation on each call (`glee_agent/strategies/persuasion.py:430–444`, `:514–550`, `:648–665`), and the manuscript's credibility rule is a fixed policy reacting to history, not an equilibrium commitment mechanism. Repetition alone does not establish the distinction from Bayesian persuasion.
- Why it matters: The theoretical connection should identify the game's actual missing mechanism. The existing qualification that the credibility reset was not analyzed as an equilibrium is useful and should remain.
- Requested action: Use “GLEE's repeated persuasion game provides no ex ante commitment to a signal policy” or similarly precise language. This is a conceptual clarification and does not require an equilibrium analysis of the deployed system.

## Finding corrected during this pass

The original Appendix F one-cent table evaluated `.01` directly in an asset containing payoff divided by `B`. Those entries therefore measured a payoff of `.01B`, not one currency cent. I independently reproduced all six original rows using normalized `.01` and all six corrected rows using `.01/B` from the frozen `b54cb33` seed. The coordinator corrected the table, ranges, units, and labels during this pass. The corrected values were inspected in the current appendix and match the calculations below (rounding aside):

| Information | B | n | Q(0) | Q(one cent) | Near-zero jump | Remaining span |
|---|---:|---:|---:|---:|---:|---:|
| Complete | 100 | 898 | .381960 | .688196 | .306236 | .307906 |
| Complete | 10,000 | 904 | .375000 | .652655 | .277655 | .346792 |
| Complete | 1,000,000 | 906 | .356512 | .596026 | .239514 | .401214 |
| Hidden | 100 | 904 | .120022 | .240044 | .120022 | .759403 |
| Hidden | 10,000 | 900 | .113333 | .226667 | .113333 | .772778 |
| Hidden | 1,000,000 | 901 | .110988 | .221976 | .110988 | .777469 |

The pooling and lack of an acceptance model remain explicitly disclosed. These numbers therefore establish reference-distribution properties, not the desirability of conceding, a payoff-rank equivalence, or policy optimality. A residual editorial phrase, “For a one-round seller cell” at the revised appendix line 1010, could simply say “For each pooled row”; the caption and surrounding limitations otherwise identify the object correctly.

## What was verified and what remains unverified

Verified by direct algebra and selected frozen-source inspection:

- The affine one-step ordering, terminal-offer identity, exact midrank definition, and sure-payoff/lottery reversal.
- The finite alternating-proposer recurrence and the distinction between the infinite-horizon benchmark and the deployed finite recursion.
- The silent Bob offer ladder, discounted terminal floor, parity restrictions, and separate owned-offer coercion path.
- The generic bargaining clock, continuation estimator, offer/acceptance floors, Bob raise-only model integration, and static unreachability of the high-share delay child when the deterministic parent is off.
- Negotiation's outer seller precedence, complete-information cap-10 buyer rule, hidden terminal cost ceiling, observed-leader buyer paths, eight-price walk, generic-seller routing, and the role of the final price guards.
- The persuasion LOW-rate posterior likelihoods, current-message reweighting, baseline money gate, tight-prior restriction, credibility-reset precedence, and V1 veto predicate; and the one-shot persuasion bound by algebra.
- The corrected Appendix F rank table by independent read-only recomputation from the frozen seed, with exact sample counts and monetary rescaling.

Not established by this pass:

- A full state-by-state execution of the frozen dispatcher, source defaults, inherited environment, cached assets, overlays, and coercer over all 2,288 audited actions.
- That a source receipt proves which exact imports and configuration every live process loaded. The manuscript explicitly acknowledges this limitation.
- Calibration or causal validity of the fitted acceptance/continuation models, optimality of the retained policies, or a component contribution to placement.
- Independent reconstruction of all private raw participant data, all experiment outcomes, or the organizer's undocumented adjusted-score implementation.
- A new public-source citation or venue-policy audit; those are assigned to other review passes. No unpublished manuscript or private log content was sent to external services.

No requested strategy change, live deployment, fleet configuration mutation, process manipulation, or heavy simulation was performed. Only this review file was written by this pass. Retain it within the author's private revision workspace under the intake handling record.

# Confidential comments to editor

Not applicable: this is an author-side working review, and the intake records no separate editor channel. All substantive observations and competence limitations are author-facing above. No material has been submitted to an editor.
