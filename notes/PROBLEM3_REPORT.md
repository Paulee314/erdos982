# Erdős #982: NPPZ Problem 3 (the 1-D midpoint / cap problem). Agent B final report, 5 Nov 2026

The work files are in `prob3_bundle.tgz` next to this file: the scripts in `src/`, the logs, `Bpq.json`, and `patterns_*.json` with the 132 certified infeasible cores.

## Bottom line
- **NPPZ's n²/2 conjecture is false, and this was already known in print.** The truth is (3/5)n² + O(n), proved by Lev and Pinchasi: Acta Arith. 163(2) (2014) 127–140, arXiv:1211.6567. Their Theorem 1 gives B(n) ≤ 0.6n² + n, and their example shows the bound is sharp.
- **Exact values for small n.** B(n) = ⌊3n²/5⌋ is proved by computer for n ≤ 5: B(2..5) = 2, 5, 9, 15. For n = 6, 21 ≤ B(6) ≤ 24, uncertified.
- **Constructions.** Explicit configurations attain ⌊3n²/5⌋ for every n ≤ 30. Simulated annealing for n ≤ 16 never beat it.
- **Payoff for #982.** A 3/5 cap lemma would give ε ≈ 1/6911 as NPPZ write it, or ≈ 1/8123 with the Case 1 fix. Even a perfect cap lemma (c = 0) gives only ε ≈ 1/2900 to 1/4300. The bottleneck is NPPZ's overall argument, not the cap constant.

## Literature
- The April 2012 preprint (renyi.hu distdist042512.pdf), just after Lemma 13: "We conjecture that the number of edges in G in Lemma 13 is in fact at most n²/2 + O(n)."
- In arXiv v2 (2013, the JoCG version) this is Problem 2, the bichromatic 3-term-AP formulation. That version cites Lev and Pinchasi for (3/5)t² ± O(t). Their example fits on a circular arc, so the cap lemma cannot go below 3/5.
- **Lev–Pinchasi.** For any finite real sets A and B, #{(a,b,c) ∈ A×B×(A∪B) : a+b = 2c} ≤ 0.15(|A|+|B|)² + 0.5(|A|+|B|).
  - Example: A = [1,m] ∪ {m+2, m+4, …, 4m}, mirrored.
  - Proof outline: reduce to integers, split by parity and mod 4, then induct using Lev's 1998 bound for a+b = c.

## Small-n table
Upper bounds for n ≥ 7 are ⌊0.6n² + n⌋, from Lev–Pinchasi.

| n | B(n) | Status | n²/2 | 3n²/5 | (7/8)n² |
|---|---|---|---|---|---|
| 2 | 2 | CEGAR proof | 2 | 2.4 | 3.5 |
| 3 | 5 | CEGAR proof + CBC | 4.5 | 5.4 | 7.9 |
| 4 | 9 | CEGAR proof + CBC | 8 | 9.6 | 14 |
| 5 | 15 | CEGAR proof + CBC | 12.5 | 15 | 21.9 |
| 6 | 21–24 | not certified | 18 | 21.6 | 31.5 |
| 7 | ≥ 29 | lower bound only | 24.5 | 29.4 | 42.9 |
| 8 | ≥ 38 | lower bound only | 32 | 38.4 | 56 |
| 10 | ≥ 60 | lower bound only | 50 | 60 | 87.5 |

Further lower bounds: n = 9: ≥ 48; n = 11 to 16: ≥ 72, 86, 101, 117, 135, 153.

B(p,q) is exact for every p+q ≤ 12 except (6,6); the full table is in `Bpq.json`.

## Rigour
- **Formulation.** A midpoint pattern is realisable iff {Ag = 0, g > 0} is feasible in gap coordinates.
- **Infeasible patterns** are certified exactly by rational Stiemke vectors.
- **Search.** A 0/1 MIP over the possible patterns, using:
  - at most one midpoint per pair;
  - row/column monotonicity;
  - no shared midpoints for comparable pairs;
  - window bounds from smaller B(p,q).
- **Cores.** 132 minimal infeasible cores were needed, each with 4–6 equalities on 5–8 points. Each was forbidden in every order-isomorphic position.
- **MIP infeasibility** comes from HiGHS. For n = 3, 4, 5 it was re-checked with CBC; the off-diagonal B(p,q) values were not.
- **Standard:** this meets the usual "MIP solver plus exact certificates" standard. It is not formally verified.

## Extremal structure
- **Conjecture:** B(n) = ⌊3n²/5⌋.
- **Shape of every optimum found:** all even integers in [0, 2E] plus a window of consecutive odd integers near the middle. That is about 80% evens and 20% odds; for n = 16, the evens 0..50 and the odds 19..29. It is Lev–Pinchasi's example.
- **Degrees:** odd points have degree about 0.2n, even points up to about 0.8n.

## Slack in NPPZ Lemma 13
On the optimal configurations, the actual Σ(d(u)+d(v)) is about 0.69–0.70 of the NPPZ bound for n = 10, 20 and 40. The slack is uniform, about n/2 per segment. Most of the loss is in the step |N(u) ∪ N(v)| ≤ n.

## ε as a function of the cap constant c (Theorem 14, re-optimised over a and d)

| c | as written | with (n−3dn)² fix | fully conservative |
|---|---|---|---|
| 7/8 | 1/21576 | 1/25465 | 1/26444 |
| 0.75 | 1/10911 | 1/12854 | 1/13815 |
| 0.6 | 1/6911 | 1/8123 | 1/9067 |
| 0.5 | 1/5578 | 1/6546 | 1/7478 |
| 0 | 1/2908 | 1/3390 | 1/4277 |

**Possible slip in NPPZ.** Case 1 states (n−3dn)²/12 but then uses (n−dn)²/12, in both the preprint and v2. With the fix, ε at c = 7/8 is about 1/25465. That is still an improvement on 13/36, but not by the stated 1/22701.

## 2-D cap version
- **Caps contain the 1-D problem.** An arc of at most a semicircle embeds the 1-D problem, so cap(n) ≥ B(n), and cap(n) ≥ (3/5)n² − O(n).
- **cap(3) = 6 > B(3) = 5.** A 6-point cap with 6 witnessed cross edges exists. It was refined to residual 1e-62, and the convexity margin is ≥ 1.5e-3. The coordinates are in `src/cap3verify.py`.
- **Rigidity.** For n = 4..8 the 1-D optimum, placed on a circle, is locally rigid in 2-D: it can only move along the circle, and no extra witnessed edge was found.
- **Assessment:** cap(n) = (3/5 + o(1))n² is plausible but unproven. The Lev–Pinchasi method is purely additive and does not lift to the quadratic witness condition. A plausible route is a stability step (near-extremal caps are nearly concyclic) followed by an angular reduction; this was not attempted.
