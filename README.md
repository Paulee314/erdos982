# Erdős Problem #982 for small n: a computer verification up to n = 13

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23880465.svg)](https://doi.org/10.5281/zenodo.23880465) (n = 12 proofs)

**Status, 2 Nov 2026:** the computations are complete and checked. This write-up is a first version; corrections are welcome.

**Correction, 5 Nov 2026:** the n = 8 case was already settled in print by Fishburn (see below); an earlier version of this page said otherwise.

**Update, 7 Nov 2026:** results from the week of 3–7 Nov have been added in new folders: Fishburn's sum conjecture C4 at
n = 9–11 (`c4/`), the window property S′ at n = 13 together with the earlier n = 8, 10, 11 records (`sprime/`),
Conjecture T\* at n = 12 and T at n = 11 (`conjT/`), the exact values of I_conv(n) for n = 5–10 (`iconv/`), and two
analysis notes (`compC/`, `notes/`). See [Results summary](#results-summary) and [What's new](#whats-new-7-nov-2026).
The large new proof files are **not** in the repository; each new folder has a `MANIFEST.txt` with their sha256 and size.

## The problem

[Erdős Problem #982](https://www.erdosproblems.com/982) asks for f(n): the largest k such that every strictly convex
n-gon has a vertex with at least k distinct distances to the other vertices. Erdős conjectured f(n) = ⌊n/2⌋. The
regular n-gon shows f(n) ≤ ⌊n/2⌋.

Known lower bounds:

| Bound | Source |
|---|---|
| f(n) ≥ ⌈n/3⌉ | Moser |
| f(n) ≥ ⌊n/3⌋ + 1 | Erdős–Fishburn 1994 |
| f(n) ≥ ⌈(13n − 6)/36⌉ | Dumitrescu |
| f(n) ≥ (13/36 + 1/22701)n − O(1) | Nivasch–Pach–Pinchasi–Zerbib |
| f(n) ≥ (13/36 + 3/5270)n − O(1) | Kominers 2026, posted on the erdosproblems.com forum; not yet refereed, and not checked here |

These bounds settle the conjecture for n ≤ 7 and n = 9. The case n = 8 is also settled in print: Fishburn's survey
chapter (P. Fishburn, "Distances in convex polygons", in *The Mathematics of Paul Erdős I*, Springer; Theorem 3) proves
that the number of distinct distances, summed over all vertices, is at least n(n−1)/2 for n ≤ 8. At n = 8 the average
vertex therefore sees at least 3.5 distinct distances, so some vertex sees at least 4 = ⌊8/2⌋. (Plasma AI's public
record of the Erdős problems, github.com/plasma-ai/erdos, October 2026, lists n = 8 as the smallest open case; given
Fishburn's theorem it is not.) As far as I could find, nothing in print covers any n ≥ 10.

## Results summary

Certification levels, from strongest to weakest: **cake_lpr** = DRUP proof checked by drat-trim, its LRAT output
checked by the formally verified checker cake_lpr; **drat-trim** = DRUP proof checked by drat-trim only;
**solver-only** = the UNSAT answer of the SAT solver, no proof log; **exact algebra** = Gröbner-basis or Farkas
certificates re-expanded in exact arithmetic (used for the patterns or learned clauses a search relies on). Every
level rests on the hand-proved clause families: the checkers certify that a CNF is unsatisfiable, not that it encodes
the problem.

| Claim | n | Certification | Folder |
|---|---|---|---|
| **#982:** f(n) = ⌊n/2⌋ | n ≤ 13 (new: 10–13) | n = 8, 10, 12: cake_lpr; at n = 12 one surviving pattern by exact algebra, also a hand proof; n = 9, 11, 13 follow by monotonicity | `n8/`, `n10/`, `n12/` (proofs on Zenodo), `theory/` |
| **Fishburn's C4:** Σ_x t(x) ≥ C(n, 2) | n = 9, 10, 11 (n ≤ 8 in print) | n = 11: cake_lpr for 95 of 100 sub-cases, drat-trim for 5; n = 9: drat-trim; n = 10: drat-trim + 25 exact Farkas certificates. C4 at n implies #982 at n by averaging, so this is a second, independent route to n = 9–11 | `c4/` |
| **S′** (some vertex has distinct distances to one of its two half-windows) | new: n = 8, 10, 11, 13; n ≤ 7, 9 in print; **n = 12 open** | n = 13: cake_lpr (on a cleaned, equivalent CNF) + 105,990 exact Farkas certificates; n = 10: drat-trim + 113 exact certificates; n = 8, 11: drat-trim | `sprime/` |
| **Conjecture T** (some vertex is the apex of ≤ ⌊(n−1)/2⌋ isosceles triangles) | n = 11 | solver-only + exact algebra for the 178 blocked patterns; independent re-check | `conjT/` |
| **Conjecture T\*** (the weaker form: ≤ n/2 at some vertex, n even) | n = 12 | solver-only + exact algebra for the 4 blocked patterns; independent re-check | `conjT/` |
| **I_conv(n)** = max Σ_p (isosceles apex count) = 12, 20, 29, 38, 50, 64 | n = 5–10 | lower bounds exact (60° fan); upper bounds: n ≤ 9 cake_lpr, **n = 10 solver-only** | `iconv/` |
| max number of isosceles triangles (Aggarwal's convention) = 14, 21, 32, 40 | n = 6–9 | n = 8: cake_lpr (the √7 octagon attains 32); n = 6, 7: solver-only; **n = 9: solver-only with an unreviewed symmetry cover** | `iconv/` |
| Kite bound for Z (Computation C) | — | analysis note: lemmas checked by the agent, one theorem modulo a cited result, several refutations; no human referee | `compC/` |
| NPPZ Problem 3: B(n) = ⌊3n²/5⌋ | n ≤ 5 | computed: CEGAR with 132 certified infeasible cores; the asymptotics were already in print (Lev–Pinchasi 2014) | `notes/` |

Trust base, in one sentence: everything above is relative to the soundness of the geometric clause families (proved by
hand, reviewed by independent readings, tested on real polygons), and the SAT side is proof-logged only where the table
says so.

## What's new (7 Nov 2026)

- **`c4/` — Fishburn's C4 for n = 9, 10, 11.** Σ_x t(x) ≥ C(n, 2) for every strictly convex n-gon, where t(x) is the
  number of distinct distances from x. Fishburn proved n ≤ 8. The n = 11 case was split into 100 sub-cases
  (t(0), t(1)) = (a, b); every sub-case is pure SAT (no LP-learned clause, no model) and 95 were checked by cake_lpr
  from CaDiCaL 2.1.3 LRAT proofs, 5 by drat-trim (27.6 CPU-h of solving, 0.227 TB of proofs, deleted after checking).
  The clause families were refereed in writing; the referee report is in the folder.
- **`sprime/` — S′ at n = 13.** S′ says some vertex has pairwise distinct distances to the vertices on one side of it
  (its clockwise or its counterclockwise half); it implies #982 and is strictly stronger. For n ≤ 7 and n = 9 it is a
  corollary of the Erdős–Fishburn run theorem; the new cases are n = 8, 10, 11 (drat-trim) and now **n = 13**: a CEGAR
  search over the angle LP, 105,990 learned clauses with exact Farkas certificates, and a final DRUP proof checked by
  drat-trim and by cake_lpr. The folder documents a bug found on 6 Nov in the second certification round (lemmas with a
  repeated literal were dropped when matching drat-trim's core; fixed in `final_certify2_fix.py`; the bug could only
  cause false failures, never false passes) and why the cake_lpr check was done on a cleaned CNF (tautologies removed,
  duplicate literals merged; sha256 in `LRAT13b.log`). **S′ at n = 12 is open**: the CEGAR run is still going.
- **`conjT/` — Conjecture T\* at n = 12 (and T at n = 11).** No strictly convex 12-gon has 7 or more isosceles
  triangles with apex at every vertex (265,391 pieces; 4 patterns, all refuted by exact algebra with an independent
  re-check). This is T\*, which implies #982 at n = 12 by a second route; T itself at n = 12 is open. The SAT side has
  no proof logs.
- **`iconv/` — exact maxima of the isosceles-triangle count.** I_conv(n) = 12, 20, 29, 38, 50, 64 for n = 5–10
  (n ≤ 9 LRAT-checked, n = 10 solver-only), all attained by the 60° fan; max T = 14, 21, 32, 40 for n = 6–9 in
  Aggarwal's convention, where 32 at n = 8 comes from a new equilateral √7 octagon with vertices on two concentric
  circles (coordinates in `iconv/REPORT.md`) and 40 at n = 9 uses an unreviewed "apex cover" and should be read as
  provisional.
- **`compC/` — Computation C**, an analysis note on bounding Z through "kites" (pairs whose perpendicular bisector
  carries two vertices): what is proved, what is proved modulo Raz–Sharir–de Zeeuw, what was refuted by explicit
  polygons, and what is open.
- **`notes/`** — a literature map of the linear bounds and of the ceiling 5n/12 of the Szemerédi-type method, and a
  report on NPPZ's Problem 3 (their n²/2 conjecture is false; the truth is (3/5)n², already proved by Lev–Pinchasi).

Caveats, collected: the n = 10 value of I_conv and the T/T\* results are solver-only on the SAT side; the n = 9 max-T
value uses an unreviewed symmetry cover; S′ is new only at n = 8, 10, 11, 13 and open at n = 12; S′ at n ≤ 12 is
drat-trim only (the cake_lpr check covers n = 13 and the #982 searches); Kominers' bound is cited as a claim and has not
been checked here; the big proof files of this week (CNFs, DRUP/LRAT, Λ certificate files) are not in the repository
and are listed in the `MANIFEST.txt` files with sha256 and size; the n = 11 S′ proof file was not archived on the
machine the repository was built from; the n = 12 #982 proofs remain on Zenodo as before.

## Results

**Theorem (computer-assisted).** For every n ≤ 13, every strictly convex n-gon has a vertex with at least ⌊n/2⌋
distinct distances to the other vertices. In other words, f(n) = ⌊n/2⌋ for n ≤ 13.

Since f(n+1) ≥ f(n) (delete a vertex), the cases that need computing are n = 8, 10 and 12. They give n = 9, 11 and 13 as well. The new cases are n = 10–13; n = 8 is an independent machine check of a case already in print.

| n | Claim | How it was shown | Status |
|---|---|---|---|
| ≤ 7, 9 | f(n) = ⌊n/2⌋ | Erdős–Fishburn 1994 | in print |
| 8 | f(8) = 4 | Fishburn's chapter, Theorem 3 (sum of distinct-distance counts) | in print |
| 8 | no 8-gon has ≤ 3 distances at every vertex (independent check of the case above) | SAT search with the order rules: 196 pieces, all UNSAT, no algebra needed | certified |
| 10 | no 10-gon has ≤ 4 distances at every vertex | (a) SAT search with the order rules: 5,611 pieces, all UNSAT, no algebra needed; (b) an earlier, independent search without the order rules: 63,587 candidate patterns, each ruled out by an exact algebraic certificate | (a) certified; (b) independently audited |
| 11 | follows from n = 10 | — | — |
| 12 | no 12-gon has ≤ 5 distances at every vertex | SAT search with the order rules, DRUP proofs checked by drat-trim and cake_lpr; one candidate pattern, ruled out by an exact certificate | certified |
| 13 | follows from n = 12 | — | — |

**Update (2 Nov 2026).** The single n = 12 pattern that survives the search now also has a short hand proof. Two general results come with it: (i) in a strictly convex two-ring (bi-regular) polygon, accidental distance coincidences never happen at both the outer and the inner vertices; (ii) a strictly convex polygon in which every vertex sees equal distances clockwise and counterclockwise is regular or two-ring. Together they rule out the whole family of "merged two-ring" patterns, the main obstruction to the search method, for every n. See [`theory/two_ring_and_local_symmetry.md`](theory/two_ring_and_local_symmetry.md); these proofs have been reviewed but not refereed.

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

The new searches of 7 Nov (`c4/`, `sprime/`, `conjT/`, `iconv/`) reuse this encoding with the class bound removed and
a different objective (a cardinality constraint on Σ_x t(x), the window clauses, an apex-count bound, or a totalizer
over the isosceles indicators), plus further clause families on angles. Two of them (`c4/`, `sprime/`) also learn
clauses from an exact angle LP; every learned clause that a proof uses carries an exact rational Farkas certificate
checked by an independent script. Each folder's README states its own trust base.

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
- `theory/`: hand proofs (the two-ring coincidence theorem, rigidity of locally symmetric polygons, and the n = 12 survivor).
- `n12/`: the n = 12 records. Run B is in `B_quick_unified/`, run C in `C_exact/` and `C_below/`, and run D in `C_atmost/`. Each holds `w*.done` and `manifest_w*.txt`. `recert_*/` holds the per-piece re-certifications (manifests, plus the structure and blocking clause), and `logs/cover_check_*.log` the cover checks. There is also `algebra/` (the surviving pattern, `alg_sat.py`, and the certificate
  `cert_0.txt`: cofactors c_i with 1 = Σ c_i f_i). The proofs themselves are on Zenodo: [10.5281/zenodo.23880465](https://doi.org/10.5281/zenodo.23880465). The scripts that packed and uploaded them are in `zenodo/`.
- Added 7 Nov 2026, each with its own README and `MANIFEST.txt`:
  - [`c4/`](c4/): Fishburn's C4 for n = 9–11 (records, code, validation, referee report).
  - [`sprime/`](sprime/): S′ for n = 8, 10, 11, 13 (the n = 13 certification logs and learned-clause records, the
    round-2 bug diagnosis, the n = 10 bundle, the n = 8, 9 proofs, code).
  - [`conjT/`](conjT/): Conjecture T at n = 11 and T\* at n = 12 (audits, core certificates, code).
  - [`iconv/`](iconv/): I_conv(n) for n = 5–10 (report, logs, cloud run records, code).
  - [`compC/`](compC/): the kite-bound analysis note with its transcripts.
  - [`notes/`](notes/): the literature map and the Problem 3 report with its bundle.

## Reproduce

Requirements: Python 3 with `python-sat` (CaDiCaL 1.5.3) and `sympy`; Singular for the algebra; drat-trim (commit
`2e3b2dc`) and cake_lpr (commit `a4323b2`, built with `make cake_lpr_arm8` on Apple silicon). Set `CHECKER_TOOLS` to the
folder that holds both.

```sh
CHECKER_TOOLS=/path/to/tools ./runs/small_n_certified.sh 10 4 6    # n = 10: about a minute on 6 cores; output in code/C_*
```

The n = 12 drivers are `runs/run_all.sh` (runs B and C) and `runs/run_D.sh` (run D), with 16 workers. CaDiCaL is
deterministic, so a re-run writes byte-identical proofs, which can be compared against the SHA-256 values in the manifests.

The 7 Nov folders have their own drivers (see each README); the C4 and S′ pipelines additionally use CaDiCaL 2.1.3
(`--lrat`), Glucose 4 through PySAT, and HiGHS for the angle LP.

## Credits and AI use

AI tools were used for the computations and code, for the independent reviews and audits, and for drafting this
note. For the 7 Nov additions in particular, AI agents wrote the encodings, drivers, certifiers and checkers, ran and
audited the searches, found and fixed the round-2 bug, did the literature search, and drafted the folder READMEs; a
second and a third model refereed the clause families and the LP row families in writing. I directed the work and take
full responsibility for its content. Corrections are welcome as GitHub issues.
