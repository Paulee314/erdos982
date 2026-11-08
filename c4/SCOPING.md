# C4 / C5 (Fishburn) certified verification for n = 9–12: scoping (5 Nov 2026)

Scoping only (Paul approved scoping, not a production run). Code: `~/c4/push2/` on the MacBook (copies of the
cloud push2 modules plus the new `c4_*.py`); source tarballs in this folder (`c4code_v*.tgz`); cloud copy in
`scratchpad/e982/sprime/push2/c4_*.py`.

* **C4.** For every convex n-gon, T(C) = Σ_x t(x) ≥ C(n,2), where t(x) = #distinct distances from vertex x.
* **C5.** T(C) = C(n,2) only for R_n (n odd) / bi-regular A_n (n even).

## 1. Literature (≈25 min)

Nothing beyond Fishburn's n ≤ 8 (C4) and n ≤ 7 (C5) was found: no computer verification, proof or counterexample.

* Fishburn, "Distances in Convex Polygons", *The Mathematics of Paul Erdős I* (1997; 2nd ed. 2013, pp. 483–492),
  https://rd.springer.com/chapter/10.1007/978-1-4614-7258-2_30. §2: C4 for n ≤ 8 (the n = 8 case is sketched,
  with "I omit details"). §3: C5 for n ≤ 7. The chapter says C4 was introduced in Erdős–Fishburn [4] below.
* Erdős–Fishburn, "Multiplicities of interpoint distances in finite planar sets", Discrete Appl. Math. 60 (1995)
  141–147 (Zbl 0831.52008), https://emis.muni.cz/classics/Erdos/cit/83152008.htm. The review mentions no C4 status.
* Erdős–Fishburn, "Intervertex distances in convex polygons", DAM 60 (1995) 149–158, doi 10.1016/0166-218X(94)00047-H,
  https://portal.mardi4nfdi.de/wiki/Item:Q1894358. It covers r1(n), r2(n) and monotone runs; nothing on Σ t.
* Nivasch–Pach–Pinchasi–Zerbib, arXiv 1207.1266 (JoCG 2013), https://arxiv.org/abs/1207.1266. It proves some vertex
  has ≥ (13/36+ε)n distances, improving Dumitrescu (DCG 36 (2006)) 13n/36. It does not discuss the Σ t conjecture
  and does no computer work. Dumitrescu's abstract is about the single-vertex bound only; I did not read its full text.
* erdosproblems.com/93 (https://www.erdosproblems.com/93) gives the Σ R(x) ≥ C(n,2) remark with no status, and its
  forum thread has nothing on it. Aggarwal (arXiv 1009.2218) is unrelated.
* The only search hits on "computer verification" were this project's own e982 pages (github Paulee314/erdos982,
  plasma-ai/erdos issue #66).

## 2. Encoding (`c4_cegar.py`)

* **Base** = `e982lib.Enc(n, K=n-1, order=True, atmost=True)`, byte-identical to the Mac's `agent_runs/theory2/e982lib.py`
  (md5 4782d8d5…). Its K = n−1 class bound is vacuous. No S′ windows and no Q mode.
* **t(x).** Enc's representative variables satisfy r(c,v) ⇔ "v is the first vertex of its class at c", so
  t(c) = Σ_v r(c,v) = (n−1) − Σ_classes (size−1). The constraint Σ_c t(c) ≤ C(n,2)−1 is encoded with PySAT
  `CardEnc.atmost` (kmtotalizer) over all n(n−1) r-variables.
* **Symmetry.** The dihedral lex-leader is copied verbatim from `testA_sat.build(sym=lex)`. It is sound because every
  clause, including the cardinality constraint (which depends only on the multiset of t-values), is D_n-invariant, and
  every learned clause is added with all 2n images.
* **CEGAR.** This is cegar2's loop **minus every MEC/S′ piece**: no B, B0, B1 or Λ-MEC, no S literals, and preloaded
  records with S literals are refused. Tiers: Λ equalities, then + K/P/H items, then + strict comparisons, then Δ,
  then Σ (Σ is optional and off by default; sigma.py is marked "cloud prototype, not deployed").
* **Certification** (`c4_certify.py`, adapted from final_certify2):
  1. CNF + all learned images → Glucose4 DRUP → drat-trim core.
  2. An exact rational certificate for each core clause, checked by the independent `check_lambda_certs.py`.
  3. CNF + the accepted clauses → DRUP → drat-trim.
* **Options.** `cube=c:a` (t(c) = a; the cubes a = 1..n−1 partition the space), `block=F.feasible` (C5 mode) and
  `fams=` (ablation).

Validity of every family used (each holds in **every** strictly convex n-gon; none assumes a violator):

| family | statement | why valid |
|---|---|---|
| base E/r/F1/F2 | transitivity; class representatives; F1: at most one centre equidistant from u,v on each arc; F2: not (ac=ab ∧ bd=cd) etc. | real-number equality; definitional; the perpendicular bisector of uv meets the convex boundary twice, once per side; ac+bd > ab+cd for a convex quadrilateral |
| order axioms, F2-order, chord, gap | total preorder; ac+bd > both sums of opposite sides; outer chord on a circle is longest; four points in a class give a gap < 60° | order of reals; the diagonals cross; points on a circle within the half-plane at c; interior angle < π |
| F | at p, three interior-disjoint "wide" triangles (chord ≥ both radii, so angle ≥ 60°) are impossible | 3×60° ≥ π > interior angle |
| G, X, O | angle ≥ 60° / > 60° / > 90° indicators; triangle sum; isosceles apex/base coupling; budgets | angle_fams2 docstring ("sound for every strictly convex n-gon"); designed by Fable and Wonder in round 3 |
| Λ | fan-angle LP: positivity, interior < π, triangle sum, side ⇔ opposite angle | PROVED and refereed (push2 REPORT); exact Farkas certificates |
| K, P | circle (inscribed angle) and bisector rows | PROVED; refereed SOUND |
| H | SSS / hinge (Euclid I.8, I.24/25) rows | hinge_rows docstring; validated in push2 |
| Δ | chord-length LP (strict triangle inequality, crossing diagonals) | delta_rows docstring; validated in push2 |

Not used: A, D (not on the approved list), B/B0/B1 and Λ-MEC (violator-only), angle_fams2's K/N (not on the list),
and Σ (off).

## 3. Sanity checks (`c4_sanity.py`; all OK)

* **C4, n = 5..8.** UNSAT (pure SAT, no LP clause learned: 0.0 / 0.0 / 0.2 / 2.0 s), each **drat-trim VERIFIED**.
  Ablation: with base only (no F/G/X/O), n ≤ 7 is pure SAT, and n = 8 needs 2 Λ refinements.
* **Equality cases.** For the real R_5, A_6, R_7, A_8, R_9, A_10, R_11, A_12 (convexity checked; t-sequences as
  Fishburn states): the encoding is SAT at bound T = C(n,2) and UNSAT at C(n,2)−1 under the polygon's exact E/LT
  pattern, and Λ (tiers 1–3 with K/P/H) and Δ do not refute it. The same check passes for R_n (n even), R_{n+1}−1,
  100 random generic polygons (n = 5..12) and 75 random n-subsets of R_N (n = 8..12, many equal distances):
  **0 failures**.

## 4. Prototype runs (MacBook M1 Max, nice, ≤ 6 processes)

**C4, bound C(n,2)−1.** Times are CaDiCaL 1.5.3 times inside the CEGAR loop, wall clock with up to 6 jobs running.

| n | result | LP work | search time | certification |
|---|---|---|---|---|
| 5–8 | UNSAT | none | ≤ 2 s | drat-trim VERIFIED (n=8: 7 s) |
| **9** | **UNSAT** | **none** (pure SAT: base+F+G+X+O+card) | 33–39 s (2 seeds) | **VERIFIED**: Glucose 68 s, DRUP 119 MB, drat-trim 62 s per round, 257 s total |
| **10** | **UNSAT** | 2 SAT calls; 1 model, refuted by Λ tier 1 (equalities only); 21 core records (4 from worker a, 17 from worker b) = 290 clauses with images, shared between the workers | 1,244 s for 1 worker | **VERIFIED.** Round 1: Glucose 2,393 s, DRUP **2.6 GB**, drat-trim **s VERIFIED** in 1,840 s. The drat core uses **25** learned clauses, and all 25 have exact Λ certificates accepted by the independent checker, so the certificate is complete. Round 2 (a redundant re-solve) was stopped to free the MacBook. Total 71 min |
| 10, cubes t(0)=a, with the 290 clauses preloaded | all 9 cubes UNSAT, pure SAT | — | a=1..9: 0.6, 0.6, 10, 174, 532, 510, 157, 94, 35 s; Σ 1,514 CPU-s, 532 s wall | — |
| 11 (partial) | cubes t(0)=10 and 9 UNSAT, pure SAT | — | 1,038 s and 2,618 s (no preload, 6 jobs); the other 8 cubes and the whole-instance run were **stopped** (out of scope) | — |

No angle-LP-feasible ("residual") model appeared at any n ≤ 10. At n ≤ 9 the SAT families alone suffice. Two
ablations: with base only, n = 8 already needs 2 Λ refinements; adding the other all-convex families A, D, N and
angle_fams2-K speeds n = 9 by 27% (cloud: 67 s → 49 s).

Growth: corresponding cubes go up about ×28–30 from n = 10 to n = 11 (35 → 1,038 s; 94 → 2,618 s). The whole
instance goes ×18 from n = 8 to n = 9 and ×32 from n = 9 to n = 10. DRUP size goes ×22 from n = 9 to n = 10.

## 5. C5 (uniqueness)

Method: run the same CEGAR at bound **= C(n,2)** (C4 already rules out anything lower). Every model the LP cannot
refute is recorded and its local pattern is blocked. `c5_match.py` then compares each recorded pattern, up to D_n,
with the real R_n/A_n. `c4_certify.py block=…` certifies "UNSAT once those patterns are excluded".

| n | LP-feasible patterns at T = C(n,2) | match | search | certification |
|---|---|---|---|---|
| 5 | 1 | R_5 | 0.0 s | VERIFIED (0 Λ clauses) |
| 6 | 1 | A_6 | 0.1 s | VERIFIED (0) |
| 7 | 1 | R_7 | 0.4 s | VERIFIED (4 exact Λ certificates) |
| **8** | 1 | **A_8** | 6.4 s | **VERIFIED** (18) |
| **9** | 1 | **R_9** | 112 s | **VERIFIED** (19; 462 s) |

So: **every convex n-gon with T = C(n,2), n ≤ 9, has exactly the local distance-equality pattern of R_n or A_n.**
Fishburn only reached n ≤ 7, so n = 8 and 9 are new, subject to one remaining step:
* **The pattern pins down the polygon.** For R_n this is immediate. Equal sides plus equal span-2 diagonals (both
  chain around the polygon through the local equalities) make the triangles (x−1, x, x+1) congruent by SSS, so all
  interior angles are equal and the polygon is regular.
* For A_n a short rigidity lemma is still **needed**. For n = 6 Fishburn proves it by hand.

C5 at n = 10..12 costs about 3× the C4 run at the same n, judging by n = 9 (C4 39 s, C5 112 s).

## 6. Cost estimates and recommendation

Estimates, extrapolated at ×30 per step (MacBook M1 Max, 6 niced jobs):

| n | C4 search | C4 certificate | C5 |
|---|---|---|---|
| 10 | **done**: 21 min on 1 core, or 9 min wall over 9 cubes | **done**: 71 min (Glucose 40 min + drat-trim 31 min) | ~1 h search; certification about 2× that |
| 11 | ~12 CPU-h; ~3–5 h wall with 6 cubes in parallel (the largest t(0) cube is ~4 h, so split finer on (t(0), t(1))) | DRUP ~60–80 GB if done as one piece. Do it per cube (Glucose ~2× CaDiCaL), check, delete; ~1 day wall | ~1.5 days |
| 12 | ~15 CPU-days; ~3–4 days wall on 6 cores even with fine cubes | ~1–2 TB of DRUP: needs per-cube streaming with deletion, binary DRAT/LRAT, and more disk than the MacBook's 123 GB free | ×3 again (~2 weeks) |

**Recommendation.**
1. **Bank n ≤ 10 now.** C4 at n = 9 and 10 and C5 at n = 8 and 9 are certified and new (C5 at n = 8 still needs the A_8
   rigidity step; for n = 9 the R_9 step is immediate), at almost no cost. In future runs, skip round 2 when every core clause certifies, because the
   round-1 drat core plus the exact certificates is already a complete certificate.
2. **n = 11 is worth one overnight MacBook run** after these speedups:
   * finer cubes;
   * the extra all-convex families A, D, N and angle_fams2-K, after Paul approves them (+27% at n = 9);
   * CaDiCaL 1.9.5 with a proof instead of a separate Glucose re-solve.
3. **n = 12 is not worth brute force** on current hardware. It needs a stronger encoding: Fishburn's Lemmas 2–3
   (t(x)=1 ⇒ T large; adjacent t=2,2 ⇒ n ≤ 5) as proved clauses, and t-sequence cubes. It would also need the Studio.
4. **Before quoting results:**
   * prove the A_n rigidity lemma (pattern ⇒ polygon); C5 at n = 8 depends on it;
   * have a referee review F/G/X/O. The C4 n ≤ 9 certificates rest on base + F/G/X/O + the cardinality constraint
     alone, with no LP clauses. n = 10 adds 25 refereed-family Λ clauses. I found no referee record for G/X/O in
     push2/REPORT.md, only the angle_fams2 docstring.

Files (MacBook `~/c4/push2/runs/`): `cegar_*.log`, `cert_*.log`, `c5_*.log` (+ `.feasible`), `c5cert_*.log`, `cube10_*.log`,
`cube11_{9,10}.log`, `sanity_*.log`; certificates `cert_{5..9}_final.{cnf,drup}`, `cert_10_r1.{cnf,drup,core}` + `cert_10_lambda_ok.jsonl`, `c5cert_{5..9}_*`. All jobs are stopped; the MacBook is free.
