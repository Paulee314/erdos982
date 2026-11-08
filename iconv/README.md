# I_conv(n): exact maxima of the isosceles-triangle count, n = 5–10

For a strictly convex n-gon P let Z(P) = Σ_p Z_p, where Z_p = Σ over the distance classes at p of C(m, 2). Z counts
(apex, pair) triples, so an equilateral triangle counts three times. I_conv(n) = max Z over strictly convex n-gons.
This quantity controls the linear bounds for #982: Z ≤ αn² + O(n) for every convex n-gon gives a vertex with at least
((2 − α)/3)n − O(1) distinct distances (the transfer lemma of Nivasch–Pach–Pinchasi–Zerbib), and Aggarwal (arXiv
1009.2218) and NPPZ conjecture I_conv(n) = 3n²/4 + Θ(n). T(P) = Z − 2·#equilateral is the number of isosceles
triangles as vertex sets (Aggarwal's convention).

## Results

| n | I_conv(n) = max Z | lower bound (construction) | upper bound: Z ≥ max+1 is UNSAT | max T (Aggarwal's convention) |
|---|---|---|---|---|
| 5 | **12** | 60° fan, certified exactly | LRAT (drat-trim + cake_lpr) | not run |
| 6 | **20** | 60° fan | LRAT | 14 (T ≥ 15 UNSAT, solver-only) |
| 7 | **29** | 60° fan | LRAT | 21 (T ≥ 22 UNSAT, solver-only) |
| 8 | **38** | 60° fan | LRAT, 468 lex pieces | **32**, the √7 octagon (T ≥ 33 UNSAT, LRAT, pieces) |
| 9 | **50** | 60° fan | LRAT: 359 pieces, drat-trim + cake_lpr, `PROOF VERIFIED` on all 6 workers (`logs/n9proof_w*.out`) | 40\* (T ≥ 41 UNSAT, solver-only, **apex cover**) |
| 10 | **64** | 60° fan | **solver-only**: 10,743 lex pieces, 12 workers, 0 models, 0 survivors, all `DONE` (`logs/n10_w*.out`, `RUNS_SUMMARY.txt`) | not run |

\* The n = 9 max-T value uses the "apex cover", a symmetry-breaking scheme (rotate a vertex of maximum Z_c to position 0)
that has **not been reviewed**; it agrees with the lex cover on the three n = 8 checks. Treat 40 as unreviewed.

Every exact value so far equals the 60° fan: a centre plus n − 1 consecutive vertices of a regular 6k-gon,
k = ⌊(n − 2)/3⌋ + 1 (Z = 12, 20, 29, 38, 50, 64, 77 for n = 5–11; `code/certify_construct.py`). I_conv(n) − 3n²/4 is
−6.75, −7, −7.75, −10, −10.75, −11 for n = 5–10.

**The √7 octagon** (T = Z = 32, beating Aggarwal's Prop. 2 value 30 in his own convention): vertices
(0, 0), (1, 0), ((3+√7)/4, (1+√7)/4), ((3+√7)/4, (5+√7)/4), (1/2, (2+√7)/2), (−1/2, (2+√7)/2), (−(1+√7)/4, (3+√7)/4),
(−(1+√7)/4, (√7−1)/4). Equilateral, 4-fold symmetric, vertices alternating between two concentric circles, 5 distinct
distances, no equilateral triangles. Certified exactly with sympy (`code/certify_exact.py`).

## Method

`code/iconv_sat.py`: the T\* encoding of `../conjT/code` (base encoding with the class bound removed, families G, X, O,
the reviewed vertex-0 lex cover) with a totalizer over the e(c; u, v) variables so that the objective is exactly Z (or,
for T, iso(abc) ↔ e(a; b, c) ∨ e(b; a, c) ∨ e(c; a, b)). The bound Z ≥ best + 1 is searched; each model, if any, goes
through the angle LP (exact Farkas certificate), a Singular core over Q, whole-pattern saturation and a numerical
realisation attempt (`code/realise.py`, 60-digit polish). At Z = best + 1 the runs for n = 5–10 had **zero models**, so
the upper bounds rest on the SAT side alone: proof-logged and checked for n ≤ 9, solver-only (CaDiCaL 1.5.3) for
n = 10. `code/validate_enc.py`: real tied polygons come out SAT (n = 6: 300/300, n = 7: 300/300, n = 8: 283/283,
n = 7 with the T objective: 200/200). `REPORT.md` is the full hand-back note (5–6 Nov 2026), written while the n = 9
proof check and the n = 10 run were still going; `RUNS_SUMMARY.txt` records how they ended.

## Layout

- `REPORT.md`, `STATUS_FOR_MAIN.txt`, `RUNS_SUMMARY.txt`, `jobs.log`.
- `logs/`: `n10_w0..11.out` (each ends with `DONE worker r: final T=65`), `n9proof_w0..5.out` (each ends with
  `PROOF VERIFIED (drat-trim + cake_lpr)`).
- `runs_cloud/`: the n ≤ 9 run records from the cloud machine (`ub_n5..ub_n8` and `all_n*`: the Z upper bounds; `n*_sets*`: the max-T runs; `*apex*`: the apex-cover runs; `proof_*.log`: the drat-trim + cake_lpr checks for n = 8 and the first n = 9 attempt). Code snapshots that differ from `code/` are in `code/cloud_extra/`.
- `code/`: `iconv_sat.py`, `realise.py`, `geom.py`, `canon.py`, `certify_construct.py`, `certify_exact.py`,
  `proof_check.py`, `validate_enc.py`, `explore1.py`, `sample_cost.py`. The `lib/` folder of the original is not copied:
  its files are byte-identical to the same-named files in `../conjT/code/` (md5 list in `MANIFEST.txt`).
- `MANIFEST.txt`: the n = 10 per-piece done records (sha256, size).

AI use: the encoding, the search and certification code and the constructions were produced by AI tools under my
direction, which also ran the computations; the √7 octagon was found by an AI agent and re-checked independently;
this note was drafted by an AI tool and edited by me.
