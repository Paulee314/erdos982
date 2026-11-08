# Audit of the Conjecture T run at n = 11 (L = 6) — `ap11_L6/`

Mac Studio, `agent_runs/theory2`, audit run 3 Nov 2026 15:16–15:31 UTC (Paul approved 09:15 CT).

## Verdict

**Conjecture T verified at n = 11 (COMPUTED, mod soundness of the encoding).** No strictly convex 11-gon has
Z_p ≥ 6 at every vertex, i.e. every strictly convex 11-gon has a vertex with Z_p ≤ 5 = ⌊(n−1)/2⌋.

"Mod soundness of the encoding" means, as for n = 10: the result rests on (a) soundness of the clause families of
`e982lib.Enc(11, 10, order=True, atmost=True)` plus the apex clauses (CardEnc.atleast Σ e(c,u,v) ≥ 6 at every centre),
(b) the reviewed lex-leader cover (`sym_compact`, mirror skipping, RG strings of vertex 0 with apex ≥ 6), and (c) the
UNSAT answers of CaDiCaL 1.5.3 (pysat) on every piece once the models below were blocked (no DRUP proofs). The algebra
part — every blocked model really is impossible — is certified exactly and re-checked independently (below).

## The run (search)

| item | value |
|---|---|
| driver | `apex_pieces.py` (byte-identical to `apex_pieces_v13.py`, md5 fe341427…), `e982lib.py` md5 4782d8d5… |
| command | `env APEX_L=6 CONF_BUDGET=50000 SINGULAR=/opt/homebrew/bin/Singular python apex_pieces.py 11 r 16 ap11_L6`, r = 0..15 (`jobs.log`, 2 Nov 20:46:35Z) |
| wall | 42,735–59,649 s per worker (finished 3 Nov ≈ 13:20Z; ≈ 16.6 h) |
| python CPU | 781,896 s (≈ 217 CPU-h) recorded in the done files |
| pieces | 45,963 kept (of 115,975 RG strings), all 16 workers printed DONE |
| cubing | 4,376 pieces exceeded the conflict budget and were cubed on vertex 1 (91,239 cubes each); **0 unlimited solves** |
| models | 178 (131 blocked by a 5/6-vertex core found in the run, 47 'big', 0 library hits, 0 survivors) |
| core library | 113 records, 111 distinct canonical cores (k = 5: 2, k = 6: 109) |

## Audit procedure (same as ap10, latest versions actually used there)

Scripts (all in `agent_runs/theory2`): `cores_to_patterns.py`, `certify.py` (= `certify_v4.py`), `alg_sat.py`
(= `alg_sat_v2.py`: Singular std / greedy distinctness saturation, `lift` cofactors, exact re-expansion in sympy),
`big_cores.py`, `big_viacore.py`, `check_run.py` (= `check_run_v6.py`); plus the new independent checker
`verify_indep.py`. Python = `Erdos/e982/venv/bin/python`, Singular = `/opt/homebrew/bin/Singular`.

```
echo 11 > ap11_L6/n.txt
python cores_to_patterns.py ap11_L6                       # -> cores_k5.txt (2), cores_k6.txt (109)
(dedupe of w*.big)                                         # -> big_all.txt (47 distinct = 47 recorded)
python certify.py ap11_L6 5 0 1 ; python certify.py ap11_L6 6 r 2   (r = 0,1)
python big_cores.py 11 ap11_L6 r 4                         (r = 0..3)  -> big_cores_r*.txt, big_nocore_r*.txt
python big_viacore.py prep ap11_L6                         # -> cores_k7.txt (18 distinct), cores_k8.txt (2)
python certify.py ap11_L6 7 r 4 (r = 0..3) ; python certify.py ap11_L6 8 0 1
python big_viacore.py log ap11_L6                          # -> certify_big_viacore.log
python check_run.py 11 ap11_L6 6        > ap11_L6/AUDIT.txt
python verify_indep.py ap11_L6 11       > ap11_L6/VERIFY_INDEP.txt
```

## Results

**Big patterns (47).** Exactly as at n = 10, the 16-unknown whole-pattern `lift` is not used; each big pattern is
certified through a sub-core. `big_cores.py` found a sub-core for **all 47** (0 without a small core):
45 via a 7-vertex sub-core, 2 via an 8-vertex sub-core, all with std = {1} (no saturation needed); 20 distinct sub-cores
(18 on 7 vertices, 2 on 8). Each was certified by `alg_sat.py` (Singular `lift` cofactors, exact sympy re-expansion):
**20/20 VERIFIED**; `big_viacore.py log`: **47 of 47 big patterns certified via a core**.

**Cores used to block models (111).** `certify.py` on `cores_k5.txt` / `cores_k6.txt`: **111/111 VERIFIED**, all with
std = {1} (no saturation pair needed).

In total **131 certificates**, all of the form 1 = Σ c_i f_i (g = 1, m = 0), 251,055 cofactor terms in all.

**check_run.py** (`ap11_L6/AUDIT.txt`):
```
pieces kept 45963; done 45963; missing 0; extra 0; duplicates 0; python cpu 781896s
library: 111 distinct cores; by k: Counter({6: 109, 5: 2})
k=5: 2 cores, 2 VERIFIED
k=6: 109 cores, 109 VERIFIED
k=7: 18 cores, 18 VERIFIED
big patterns: 47 recorded, 47 in big_all.txt, 47 VERIFIED
models logged: 178; sum over done files 178; pieces with fewer logged models than recorded: 0; kinds {'new': 131, 'big': 47};
blocked by unknown core or survivor: 0; blocked by a core/pattern without VERIFIED certificate: 0
AUDIT PASS
```
Coverage: the union of the 16 done files is exactly the kept piece set — every one of the 45,963 pieces recorded
exactly once (missing 0, extra 0, duplicated 0).

**Independent re-check** (`verify_indep.py`, `ap11_L6/VERIFY_INDEP.txt`; shares no code with alg_sat/certify/check_run
and does not use sympy: own parser of Singular's cofactor strings into exact Fractions, own dict-polynomial arithmetic,
generators rebuilt from the pattern lines):
```
(1) certificates re-expanded: 131, identity holds: 131, failures: 0; total cofactor terms 251055; by k {5: 2, 6: 109, 7: 18, 8: 2}
(2)+(3) models: 131 blocked by library cores, 47 big; each contains a certified core (embedding found, certificate re-expanded): 178; failures 0
(4) done records: 45963, distinct pieces 45963, duplicated 0
INDEPENDENT CHECK PASS
```
(2)/(3) are the "cores are valid" check: for every one of the 178 models, the certified representative of the core that
blocked it (library core for 'new', recorded 7/8-vertex sub-core for 'big') embeds into the model's equality pattern by an
injective vertex map found by backtracking (every equality of the core maps to an equality of the model), and its
certificate re-expands exactly. Negative controls (run on a scratch copy): altering one cofactor coefficient, and
giving a model another model's pattern, were both caught (1 identity failure, 2 embedding failures, verdict FAIL).

## What this does not cover
- The SAT side is not proof-logged (as for n = 10 and the T\* runs): the UNSAT answers of CaDiCaL per piece and the
  correctness of `e982lib` clause families / lex-leader cover are assumed (both reviewed earlier for #982).
- The normalisation x0 = (0,0), x1 = (1,0) of each core is w.l.o.g. for distinct real points (real similarity).

Studio time for the audit: ≈ 10 CPU-minutes of Singular/sympy for the 131 certificates and the sub-core search
(≤ 7 processes, ≈ 10 min wall), < 1 min for check_run.py and verify_indep.py.
