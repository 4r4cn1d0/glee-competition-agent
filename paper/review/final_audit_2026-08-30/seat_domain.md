# Domain and game-theory final audit

Date: 2026-08-30  
Seat: Domain reviewer, game theory, economic agents, and GLEE

## Scope and overall assessment

I reviewed `paper/main_core.pdf`, `paper/main.tex`, the relevant formal appendix, the theory verifier, the prior theory-code audit, the official competition documentation snapshot, and the policy path at frozen commit `b54cb33ad9f4fe7da4c667262eee00ffaeac3ab6`. I did not use sibling final-review reports. I also compared the framing with [Shapira et al., GLEE version 3](https://arxiv.org/html/2410.05254v3). The rendered core is legible and its equations match the source. Running `paper/analysis/verify_theory_code.py` produced five passing verification groups.

The central domain claims are sound. The rank objective is correctly restricted to a one-step result under fixed scoring inputs. The negotiation policy is presented as an ordered portfolio rather than a single equilibrium. The persuasion threshold is algebraically correct and is not misrepresented as a commitment solution for repeated cheap talk. Four localized corrections are required before acceptance.

## Required corrections

### D1. Do not state the undocumented official tie rule as midrank

Severity: Minor, high confidence, acceptance blocker.

The core defines the platform quantity as an empirical midrank at `paper/main.tex:97-99`. The competition documentation states only that payoff is converted to a percentile within the same configuration and role (`docs/reference/glee-docs.md:463-472`). It does not document tie handling. The supplement already says this explicitly at `paper/appendix.tex:16-37`, including that midrank is the local diagnostic convention and must not be called the official convention without organizer confirmation. The core currently removes that distinction.

This does not invalidate the monotonicity, dominance, reversal, or terminal-proposal arguments. Those results either assume a fixed nondecreasing map or explicitly use a local midrank construction. The required repair is to call `Q_{c,r,\tau}` the official raw empirical percentile with undocumented tie handling, then define midrank separately as the local diagnostic convention.

### D2. Attribute 960 configurations to the competition, not the original GLEE paper

Severity: Minor, high confidence, acceptance blocker.

At `paper/main.tex:90-95`, the sentence saying that GLEE varies parameters over 960 configurations cites Shapira et al. The cited version 3 paper reports 1,320 benchmark configurations, split as 384 bargaining, 576 negotiation, and 360 persuasion. The live competition documentation reports a 960-combination server grid at `docs/reference/glee-docs.md:506-509`. The supplement already makes the correct distinction at `paper/appendix.tex:169-181`.

The core should say that the live competition uses 960 configurations and cite the competition rules there. It may then cite Shapira et al. for the benchmark families, parameterization, and the self-gain, efficiency, and fairness analyses. This correction is also necessary for accurate literature positioning: the manuscript's contribution is a competition-policy and audit study built on GLEE, not a restatement of the benchmark experiment.

### D3. Distinguish the fitted bargaining CDF from official `Q`, and define the horizon field exactly

Severity: Minor, high confidence, acceptance blocker.

The core writes the generic Bob model as `Q_{\kappa(c)}` at `paper/main.tex:153-156`, immediately after using `Q_{c,r,\tau}` for the official role-, cell-, and time-specific percentile. These are not the same object. In the frozen source, `barg_offer.cell_key` is exactly `(money, max_rounds, bool(horizon_known), bool(complete_information))` at `b54cb33:glee_agent/barg_offer.py:113-115`, and the caller passes `state.get("max_rounds")` at `b54cb33:glee_agent/strategies/bargaining.py:614-628`. Thus the horizon entry is absent or `None` in the public no-limit state. It is not the synthetic 99-opportunity boundary used elsewhere by the bargaining planner. The CDF also pools acting role, both discounts, and message mode, and it lacks the official opponent adjustment and time-varying reference pool.

The supplement has the correct notation at `paper/appendix.tex:296-324`: `\widehat Q_{\kappa(c)}` with `T^{\mathrm{field}}`, which may be absent. The core should use that same notation. Without this change, a reader can reasonably infer that the fitted CDF uses the synthetic 99 horizon or is an official percentile model, neither of which is true.

### D4. State the candidate domain and the top-cost convention for the 24-cell seller proxy

Severity: Minor, high confidence, acceptance blocker.

Equation 2 at `paper/main.tex:163-177` correctly averages four latent buyer multipliers, two message modes, and three price scales, giving 24 cells for each fixed seller type. Its strict inequality also correctly leaves the buyer one cent when buyer and target multipliers coincide. The executable verifier reproduces the bank targets and the fixed-cell versus pooled-objective distinction.

The sentence that the hard-coded table maximized the proxy is nevertheless under-specified because the core never gives the candidate set for `\pi` and does not identify the top-cost exception. The actual calculation searches supported grid targets above cost for `\sigma\in\{.8,1.0,1.2\}`. At `\sigma=1.5` there is no supported buyer type above cost; the `2.0B` ask is a deterministic dead-cell convention and is not a unique optimizer. The supplement states this at `paper/appendix.tex:555-598`. The core should either add the supported candidate set and the exception or weaken the claim to say that the first three rows maximize the declared finite candidate objective while the top row is a dead-cell convention.

## Checks that found no domain blocker

- Rank objective: Under the assumptions listed at `paper/main.tex:105-114`, expected one-step rating is affine and increasing in expected adjusted percentile. The manuscript correctly does not infer a final-leaderboard ordering, and it correctly separates pointwise payoff dominance from ordering by expected payoff alone.

- Hidden negotiation: The 24-cell proxy is clearly a construction objective, not an identified live exposure distribution or a same-cell policy. The manuscript also avoids inferring exact hidden feasibility from completed deals. The conditional reservation-bound argument correctly requires proposer individual rationality.

- Persuasion: The threshold `q^*=p(v-P)/((1-p)(P-u))` at `paper/main.tex:183-192` follows directly from posterior obedience when all high items are recommended. All-push is weakly obedient exactly when prior expected value weakly exceeds price. The frozen seller code implements that branch, uses no LOW recommendations in the interior under the banked zero-shading and long-honesty settings, and uses the historical buy-rate cutoff when `v` is absent. The text properly labels this a one-shot commitment benchmark for a repeated, noncommitted cheap-talk environment.

- Information claims: The substantive distinctions are correct. Negotiation complete information exposes the opponent valuation, hidden information does not. Persuasion's `v/u` fields may be hidden from the seller, while the buyer acts on its own values and the public prior. Bargaining's public no-limit state omits `max_rounds`; the agent's 99-opportunity boundary is therefore an internal heuristic. For maximum clarity, “buyer values were hidden” at `paper/main.tex:187-188` could read “buyer values were hidden from the seller,” but the current paragraph context prevents a substantive error.

- Ordered implementation: The frozen negotiation path gives precedence to the promoted one-round seller, then the direct first-principles cells, hidden cap-10 terminal inference, observed-leader buyer tables, and the remaining seller fallback. Direct structural and buyer-table wires are exempted from generic numeric price guards before final schema coercion. Bargaining's narrow P2 owner likewise returns before the generic planner. Persuasion applies the buyer posterior, then the tight credibility reset, then the enabled one-directional BUY-to-PASS V1 decline veto. These relationships agree with `paper/appendix.tex:626-640` and the dated code path.

- Literature positioning: Apart from the configuration-count attribution in D2, the manuscript appropriately distinguishes the original GLEE benchmark's behavioral and market analysis from this competition agent's percentile-scoring and implementation-audit contribution. Its Rubinstein, automated-negotiation, Bayesian-persuasion, and cheap-talk benchmarks are used with explicit scope limits. Adding the bilateral-trade references discussed by the original GLEE paper would improve context but is not required for correctness in this short core.

## Verdict

**Minor Revision.** Exact blockers: (1) stop presenting midrank as the documented official tie rule; (2) attribute the 960-cell grid to the competition and retain 1,320 for GLEE version 3; (3) change the Bob model to `\widehat Q_{\kappa(c)}` and define `T^{\mathrm{field}}` as the possibly absent transmitted field; and (4) specify the hidden-seller candidate set and identify the `\sigma=1.5` ask as a nonunique dead-cell convention.
