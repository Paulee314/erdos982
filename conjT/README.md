# Conjecture T and T*: the isosceles-apex count, n = 11 and n = 12

For a vertex p of a strictly convex n-gon, group the other vertices by their distance from p, with class sizes
m_1, …, m_k, and let Z_p = Σ_i C(m_i, 2): the number of isosceles triangles with apex p. Since
C(m, 2) ≥ 2m − 3, Z_p ≥ 2(n − 1) − 3k, so a small Z_p forces many distinct distances at p.

- **Conjecture T.** Every strictly convex n-gon has a vertex with Z_p ≤ ⌊(n − 1)/2⌋. T implies #982 and is tight for
  the regular n-gon.
- **Conjecture T\*** (weaker). Every strictly convex n-gon has a vertex with Z_p ≤ n/2 (n even) or ≤ (n + 3)/2
  (n odd, n ≥ 7). T\* still implies #982: a counterexample to #982 has k ≤ ⌊n/2⌋ − 1 classes at every vertex, and the
  least Z_p with that many classes is n/2 + 1 (n even) or (n + 5)/2 (n odd).

"Refute T at n" means: show that no strictly convex n-gon has Z_p ≥ ⌊(n − 1)/2⌋ + 1 at every vertex; for T\* the
threshold is L = n/2 + 1 (n even). At n = 12, L = 7.

## Results

| n | statement | pieces | models | status |
|---|---|---|---|---|
| 11 | T: no 11-gon has Z_p ≥ 6 at every vertex | 45,963 | 178, all refuted by exact algebraic certificates (131 certificates) | **computed**: SAT side solver-only (CaDiCaL 1.5.3, no proof logs); algebra certified exactly and re-checked by an independent checker; audit PASS (`AUDIT_ap11_L6.md`, `n11_T/`) |
| 12 | **T\*** (L = 7): no 12-gon has Z_p ≥ 7 at every vertex, i.e. some vertex has Z_p ≤ 6 | 265,391 (16,074 in run v1 + 249,317 in run v2) | 4, all in v1, all blocked by 6-vertex cores; v2 found none | **computed**: SAT side solver-only (no proof logs); the 9 cores have exact certificates (Gröbner basis {1}, cofactor identity 1 = Σ c_i f_i re-expanded exactly), independent check PASS; audit PASS (`AUDIT_ap12_L7.md`, `n12_Tstar/`) |

Note the distinction: at n = 12 the run establishes **T\***, not T. T at n = 12 would need Z_p ≤ 5 at some vertex and
is open. (The headline sentence of `AUDIT_ap12_L7.md`, written at the end of the run, says "Conjecture T"; the
statement it then gives, Z_p ≥ 7 at every vertex is impossible, is T\*.) Both results give #982 at n = 11 and 12
again, by a different route from the main search; neither is proof-logged on the SAT side, so they are a level
below the certified #982 results in the top-level table.

## How the n = 12 run was done

Driver `code/apex_pieces.py` (v1, 2–5 Nov 2026, 16 workers on the Mac Studio) and `code/apex_v2.py` (v2, 5 Nov).
Both use the #982 encoding `code/e982lib.py` with the class bound removed, the apex clauses (Σ e(c; u, v) ≥ L at every
centre c, as a PySAT cardinality constraint), and the reviewed dihedral lex-leader cover; the pieces are the RG strings
of vertex 0. v2 adds the static angle families G, X, O (`code/angle_fams2.py` via `code/fams_v2.py`; written referee
report `v2_bench/wonder_GXO_referee.txt`; benchmark and regression notes in `v2_bench/REPORT.md`, 10,000-polygon validation in `v2_bench/val_10k.log`) and a lazy angle-LP
step with exact Farkas certificates (`code/lambda_v2.py`; 0 such clauses were needed). v1 was stopped because a race in
its re-splitting logic duplicated work (4,960 duplicated done records, no missing pieces); v2 ran the frozen list of the
249,317 pieces v1 had not finished (`n12_Tstar/ap12_L7_v2/pieces_todo.md5`), tagged every record with the code
version, and finished in 150,811 CPU-s against 2,676,014 CPU-s for v1.

Each model found by the SAT solver is a local equality pattern. A sub-pattern on 5–6 vertices (a "core") is extracted,
normalised to x0 = (0, 0), x1 = (1, 0), and its polynomial ideal is shown to be {1} in Singular; the cofactors of
1 = Σ c_i f_i are re-expanded exactly in sympy (`code/alg_sat_v2.py`, `code/certify.py`) and then again by
`code/verify_indep.py`, which shares no code with the generator (own parser, own exact polynomial arithmetic), and also
checks that each blocked model really contains its certified core. `code/check_run_v7.py` checks coverage (every
piece done exactly once across v1 and v2, missing 0, extra 0) and that every blocked model has a verified certificate.

## Layout

- `AUDIT_ap12_L7.md`, `AUDIT_ap11_L6.md`: the audit notes.
- `n12_Tstar/ap12_L7_v2/`: `NOTES.txt` (the switch from v1 to v2), `final_check.log` (first audit: FAIL, 4 cores not yet
  certified), `final_check2.log` (after certification: PASS), `VERIFY_INDEP_v1.txt` (independent check PASS),
  `VERSION`, `restarts.log`, `pieces_todo.md5`, `v1_algpass/` (the 4 whole v1 models re-certified by alg_sat_v2:
  `alg.log`, `v1_models.txt`).
- `n12_Tstar/ap12_L7/`: the v1 core library `cores_k5.txt` (1 core), `cores_k6.txt` (8 cores), the certification logs
  `certify_k{5,6}_r0.log` and the 9 certificates `certs_k{5,6}_r0/cert_*.txt` (cofactors c_i), `rate_estimate.txt`,
  `restarts.log`.
- `n11_T/`: `AUDIT.txt` and `VERIFY_INDEP.txt` of the n = 11 run.
- `code/`: as above, plus `cores_to_patterns.py`, `big_cores.py`, `big_viacore.py`, `numsolve.py`, `patterns.py`,
  `make_piecelist.py`, the start and progress scripts.
- `MANIFEST.txt`: the per-piece done records (16 × 1 MB for v2, plus v1), the frozen piece list, the 748 MB of
  whole-model certificates in `v1_algpass/certs`, and the n = 10 and n = 11 record folders, with sha256 and sizes.

AI use: the conjectures were proposed, the drivers, certifiers and checkers written, and the runs run and audited by
AI tools under my direction; the angle families were refereed by a second model; this note was drafted by an AI tool
and edited by me.
