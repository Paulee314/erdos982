# Fishburn's sum conjecture C4, verified for n = 9, 10, 11

**C4** (Fishburn, "Distances in convex polygons", *The Mathematics of Paul Erdős I*, §2): for every strictly convex
n-gon, T(C) = Σ_x t(x) ≥ C(n, 2), where t(x) is the number of distinct distances from vertex x to the other vertices.
Fishburn proves it for n ≤ 8 (the n = 8 details are omitted in print). C4 at n implies #982 at n by averaging (some
vertex has t(x) ≥ (n − 1)/2, so t(x) ≥ ⌊n/2⌋), so the results below also give #982 at n = 9, 10, 11 by a route that
is independent of the main search.

**Result (computer-assisted).** C4 holds for n = 9, 10 and 11: no strictly convex n-gon has Σ_x t(x) ≤ C(n, 2) − 1.

| n | sub-cases | search | certificate | where |
|---|---|---|---|---|
| 5–8 | whole instance | pure SAT, UNSAT | two-round DRUP, drat-trim `s VERIFIED` | `macbook_runs/cert_{5..8}.log` |
| 9 | whole instance (two seeds) | pure SAT, UNSAT in 33–39 s | two-round DRUP (119 MB), drat-trim `s VERIFIED` both rounds, 0 learned clauses | `macbook_runs/cegar_9{a,b}.log`, `cert_9.log` |
| 10 | whole instance | CEGAR: 1 model, refuted by the angle LP (equalities only); 290 learned clauses with images | round 1: DRUP 2.6 GB, drat-trim `s VERIFIED`; the drat core uses 25 learned clauses, all 25 with exact rational Farkas certificates accepted by the independent checker. Round 2 (a redundant re-solve) was stopped. | `macbook_runs/cegar_10a.log`, `cert_10.log`, `cert_10_lambda_ok.jsonl` |
| 10, cubes t(0) = a | 9 cubes, a = 1..9, with the 290 clauses preloaded | all UNSAT, pure SAT | — (cross-check of the whole-instance run) | `macbook_runs/cube10_*.log` |
| 11 | 100 sub-cases (t(0), t(1)) = (a, b), a, b = 1..10 | pure SAT in every sub-case: 0 LP-learned clauses, 0 models | 95 sub-cases: CaDiCaL 2.1.3 `--lrat`, checked by **cake_lpr** (`s VERIFIED UNSAT`). 5 sub-cases: two-round pipeline, binary DRAT, **drat-trim** `s VERIFIED`. 3 of those 5 were re-run on the cake_lpr pipeline with identical CNF sha256. | `n11_record/` |

The sub-cases of n = 11 (t(0) = a, t(1) = b for all a, b) partition the search space, so together they cover every
11-gon. See `n11_record/RESULT_n11.md` for the full record: 27.6 CPU-h of solving, 4.0 CPU-h of checking, 0.227 TB of
proofs (deleted after checking; sha256 and size of every proof are in `n11_record/COMBINED_n11.json` and in each
sub-case's `.json`).

## Encoding and trust base

`code/push2/c4_cegar.py`. The base is the #982 encoding (`code/sat/e982lib.py`, `Enc(n, K = n−1, order=True,
atmost=True)`: the class bound is vacuous) with the sum Σ_x t(x) ≤ C(n, 2) − 1 as a cardinality constraint over the
class-representative variables (PySAT totalizer), the dihedral lex-leader of the #982 search, and the clause families

- F, G, X, O (angle facts at a vertex: wide triangles, 60° and 90° indicators, triangle sums) and, at n = 11, the
  extra families A, D, N and angle_fams2-K. All hold in every strictly convex polygon. The written soundness referee
  report is `WONDER_C4_families_referee.txt` (verdict: A, D, N, K, F, G, X, O sound for C4; the cube split sound as the
  complete union; the two raw referee outputs are the `wonder_C4fams_*.json` files);
- the angle LP families Λ / K / P / H / Δ, used only through learned clauses that carry exact rational Farkas
  certificates (`code/push2/check_lambda_certs.py`). At n = 11 no such clause was needed.

What the SAT checkers certify is that each CNF is unsatisfiable. That the CNF encodes C4 correctly rests on the hand
proofs of the clause families, the referee reports, and the tests below. `SCOPING.md` (5 Nov 2026) has the derivation,
the sanity checks and the cost estimates that preceded the production run.

## Tests

- `macbook_runs/sanity_*.log`: the real equality cases R_5, A_6, R_7, A_8, R_9, A_10, R_11, A_12, plus 100 random
  generic polygons and 75 random subsets of regular N-gons, come out SAT at T = C(n, 2) and UNSAT at C(n, 2) − 1 under
  their exact distance pattern, and the LP families do not refute them: 0 failures.
- `validation/val_fast.out`: (V1) n = 8 with the base encoding only and with the full families, 49/49 sub-cases
  verified in each mode (`validation/v8none`, `validation/v8full`); (V2) three n = 11 sub-cases re-run on the cake_lpr
  pipeline, verified, identical CNF sha256 to the first run (`validation/r11_reruns`); (V3) planted LRAT corruptions,
  all three rejected by cake_lpr.
- `macbook_runs/c5*`: a scoping run for Fishburn's C5 (uniqueness of the equality case) at n ≤ 9. It is **not** a
  claimed result: the step "the local distance pattern pins down the polygon" is proved only for R_n, not yet for A_n.

## Layout

- `n11_record/`: `RESULT_n11.md`, `COMBINED_n11.json` (one entry per sub-case per run), the per-driver folders
  `studio_A/`, `studio_B/`, `mac_fast/`, `mac_old/` (STATUS.json, driver logs, per-sub-case `.json` summaries, solver
  and checker logs, Λ files), `MOVE_LOG.txt` and the `list11_*` split files, `studio_jobs.log`. The gzipped CNFs (282 MB)
  are not in the repo: `MANIFEST.txt` lists their sha256 and size.
- `macbook_runs/`: the n ≤ 10 logs from the MacBook (`cegar_*.log`, `cert_*.log`, `cube10_*.log`, `c5*`, sanity logs),
  the small CNFs and drat cores; files over 2 MB (the DRUP proofs, the n = 9/10 CNFs and the n = 10 core) are in
  `MANIFEST.txt`.
- `validation/`: see Tests.
- `code/`: `push2/` (the CEGAR driver `c4_cegar.py`, the fast LRAT driver `c4_fastcube.py`, the two-round certifier
  `c4_certcube.py`, the drivers, `c4_sanity.py`, the LP row generators and the exact checker), `sat/` (the base
  encoding and the angle families), `c4_combine.py`, `c4status.py`. Solvers: CaDiCaL 2.1.3 (`--lrat`), CaDiCaL 1.5.3
  through PySAT inside the CEGAR loop, Glucose 4 for the n ≤ 10 two-round certificates and CaDiCaL 2.1.3 (binary DRAT) for the five n = 11 two-round sub-cases; checkers: drat-trim (commit `2e3b2dc`)
  and cake_lpr (commit `a4323b2`).
- `SCOPING.md`, `HANDOFF_v1`, `WONDER_C4_families_referee.txt`, `wonder_C4fams_*.json`.

AI use: the encoding, drivers and checkers were written by AI tools under my direction; the clause-family soundness
review was done by a second model (the referee file above); the production runs were run and audited by AI agents;
this note was drafted by an AI tool and edited by me.
