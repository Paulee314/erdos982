# Erdős Problem #982 for small n: a computer verification up to n = 13

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23880465.svg)](https://doi.org/10.5281/zenodo.23880465) (n = 12 proofs)

**Status, 2 Nov 2026:** the computations are complete and checked. This write-up is a first version; corrections are welcome.

## The problem

[Erdős Problem #982](https://www.erdosproblems.com/982) asks for f(n): the largest k such that every strictly convex
n-gon has a vertex with at least k distinct distances to the other vertices. Erdős conjectured f(n) = ⌊n/2⌋. The
regular n-gon shows f(n) ≤ ⌊n/2⌋.

Published lower bounds:

| Bound | Source |
|---|---|
| f(n) ≥ ⌈n/3⌉ | Moser |
| f(n) ≥ ⌊n/3⌋ + 1 | Erdős–Fishburn 1994 |
| f(n) ≥ ⌈(13n − 6)/36⌉ | Dumitrescu |
| f(n) ≥ (13/36 + 1/22701)n − O(1) | Nivasch–Pach–Pinchasi–Zerbib |

These bounds settle the conjecture for n ≤ 7 and n = 9. As far as I could find, nothing in print covers n = 8 or any
n ≥ 10. Fishburn's 1997 survey chapter may cover n = 8, but I have not yet been able to source a copy.

## Results

**Theorem (computer-assisted).** For every n ≤ 13, every strictly convex n-gon has a vertex with at least ⌊n/2⌋
distinct distances to the other vertices. In other words, f(n) = ⌊n/2⌋ for n ≤ 13.

Since f(n+1) ≥ f(n) (delete a vertex), the cases that need computing are n = 8, 10 and 12. They give n = 9, 11 and 13 as well.

| n | Claim | How it was shown | Status |
|---|---|---|---|
| ≤ 7, 9 | f(n) = ⌊n/2⌋ | Erdős–Fishburn 1994 | in print |
| 8 | no 8-gon has ≤ 3 distances at every vertex | SAT search with the order rules: 196 pieces, all UNSAT, no algebra needed | certified |
| 10 | no 10-gon has ≤ 4 distances at every vertex | (a) SAT search with the order rules: 5,611 pieces, all UNSAT, no algebra needed; (b) an earlier, independent search without the order rules: 63,587 candidate patterns, each ruled out by an exact algebraic certificate | (a) certified; (b) independently audited |
| 11 | follows from n = 10 | — | — |
| 12 | no 12-gon has ≤ 5 distances at every vertex | SAT search with the order rules, DRUP proofs checked by drat-trim and cake_lpr; one candidate pattern, ruled out by an exact certificate | certified |
| 13 | follows from n = 12 | — | — |

## How it works

A counterexample with n vertices has, at every vertex c, the other n − 1 vertices split into at most K = ⌊n/2⌋ − 1
classes of equal distance. The search runs over these equal-distance patterns.

1. **Encoding.**
   - Boolean variables record which pairs of distances are equal.
   - Further variables give a total order on the distances.
   - Clauses encode facts that hold in every strictly convex polygon:
     - equal distance is an equivalence relation;
     - at most K classes at each vertex;
     - two perpendicular-bisector facts (F1, F2);
     - the convex-quadrilateral inequality: the two diagonals are together longer than either pair of opposite sides;
     - two facts about points at equal distance from a vertex (chord monotonicity, and "four in a class").
2. **Splitting and symmetry.**
   - The search is split into pieces by the partition at vertex 0.
   - Rotations and reflections are removed by lex-leader clauses and mirror skipping.
3. **Solving.**
   - Each piece goes to the CaDiCaL SAT solver.
   - "UNSAT" means no counterexample pattern fits that piece.
4. **Algebra for anything that survives.**
   - With v0 = (0, 0) and v1 = (1, 0), the pattern's equalities generate a polynomial ideal.
   - A Gröbner basis equal to {1} means there is no solution even over ℂ.
   - The certificate 1 = Σ cᵢ fᵢ is computed in Singular and re-expanded exactly in sympy.

## n = 12 in detail

| Run | Pieces | What it checks | Result |
|---|---|---|---|
| B: quick (uncertified) | 211,659 | unified "at most 5 classes" cover | 1 candidate pattern |
| C: certified | 123,680 + 87,979 | exactly-5 cover plus below-5 cover | every piece UNSAT except the same candidate |
| D: certified | 211,659 | unified cover, independent of C | every piece UNSAT except the same candidate |

- **Certification.**
  - The pieces run in batches of 50.
  - Each batch has a CNF file and a DRUP proof.
  - drat-trim checks each proof and emits LRAT; cake_lpr, a formally verified checker, checks the LRAT.
  - A batch whose proof did not pass both checkers was re-run one piece at a time, each with a fresh solver and its own proof. This affected 23 below-5 batches, plus the batch containing the candidate in each of runs C and D.
  - A script confirms that every piece of each cover is certified exactly once.
- **The candidate pattern.**
  - The vertices' equal-distance partitions are
    `01123432110 00123424321 01100234320 01221034043 01122110343 01234432102 01233443321 01021344312 01210334433 01202103443 00123210044 01234243210`.
  - Every vertex has exactly 5 classes.
  - Its equations have Gröbner basis {1}, so it has no solution even over ℂ. The certificate has 2,355 cofactor terms and was verified exactly.
- **Compute.** About two hours of wall-clock time on 16 cores of a Mac Studio (M3 Ultra) for run C, including proof checking.

## What has and has not been checked

**Checked:**
- **Soundness review.** An independent review read every clause family from the code and re-derived it. It found no unsound clause.
- **Polygon tests.** The review tested 782 real polygons (n = 6 to 12) against the generated clauses. There were 0 violations, and the test does detect deliberately planted wrong clauses.
- **n = 10 audit.** A separate audit:
  - re-derived all 63,587 n = 10 certificates from scratch;
  - re-verified the 59,085 stored ones;
  - re-ran 3,605 search pieces, all with identical results.

**Not checked:**
- **The geometric clause families.** They are proved by hand, not in a proof assistant.
- **The CNF itself.** The DRUP checkers certify that the CNF is unsatisfiable. They do not certify that the CNF correctly encodes the problem. That rests on the hand proofs, the review and the polygon tests.
- **The earlier n = 10 search** (b) has no checked proof logs; it predates the certified pipeline. The certified run (a) covers n = 10 on its own.

## Repository layout

- `code/`: the encoding (`e982lib.py`), the incremental search (`cube982o.py`), the batched proof-producing search
  (`cube982p.py`), the proof check (`checkproofs.py`, `chk.sh`), per-piece re-certification (`recert.py`,
  `recert_jobs.py`) and the cover checks (`c_cover_check.py`, `cover_check.py`).
- `runs/`: the shell drivers used on the Mac Studio.
- `n8/`, `n10/`: certified runs. For each cover, `w*.done` records each batch, `manifest_w*.txt` gives the proof SHA-256
  and checker verdict, and `*.drup.gz` holds the proofs.
- `n12/`: the n = 12 records. Run B is in `B_quick_unified/`, run C in `C_exact/` and `C_below/`, and run D in `C_atmost/`. Each holds `w*.done` and `manifest_w*.txt`. `recert_*/` holds the per-piece re-certifications (manifests, plus the structure and blocking clause), and `logs/cover_check_*.log` the cover checks. There is also `algebra/` (the surviving pattern, `alg_sat.py`, and the certificate
  `cert_0.txt`: cofactors c_i with 1 = Σ c_i f_i). The proofs themselves are on Zenodo: [10.5281/zenodo.23880465](https://doi.org/10.5281/zenodo.23880465). The scripts that packed and uploaded them are in `zenodo/`.

## Reproduce

Requirements: Python 3 with `python-sat` (CaDiCaL 1.5.3) and `sympy`; Singular for the algebra; drat-trim (commit
`2e3b2dc`) and cake_lpr (commit `a4323b2`, built with `make cake_lpr_arm8` on Apple silicon). Set `CHECKER_TOOLS` to the
folder that holds both.

```sh
CHECKER_TOOLS=/path/to/tools ./runs/small_n_certified.sh 10 4 6    # n = 10: about a minute on 6 cores; output in code/C_*
```

The n = 12 drivers are `runs/run_all.sh` (runs B and C) and `runs/run_D.sh` (run D), with 16 workers. CaDiCaL is
deterministic, so a re-run writes byte-identical proofs, which can be compared against the SHA-256 values in the manifests.

## Credits and AI use

This work was carried out with substantial assistance from AI tools, which were used for the computations and code,
for the independent reviews and audits, and for drafting this note. I directed the work and take full responsibility
for its content. Corrections are welcome as GitHub issues.
