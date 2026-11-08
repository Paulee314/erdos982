# I_conv(n): first exact values (Erdős #982 side project). Computation A hand-back, 5–6 Nov 2026

## Conventions
- **Z(P)** = Σ_p Σ_{classes at p} C(m,2). It counts (apex, pair) triples, so an equilateral triangle counts **3×**.
  - **I_conv(n)** = max Z over strictly convex n-gons. This is what the transfer lemma uses.
- **T(P)** = isosceles triangles counted as vertex sets, T = Z − 2·#equilateral. This is **Aggarwal's convention**. His Prop. 2 formula ¼(3n² − 11n + 8 + 2⌊n/2⌋) counts T.

## Main table

| n | regular Z (T) | Aggarwal formula [T] | best Z realised (cert.) | Z upper bound | max T [Aggarwal conv.] | 3n²/4 | status (Z) |
|---|---|---|---|---|---|---|---|
| 5 | 10 (10) | 8 | 12 | Z≥13 UNSAT (LRAT) | not run | 18.75 | EXACT |
| 6 | 12 (8) | 14 | 20 | Z≥21 UNSAT (LRAT) | 14, T≥15 UNSAT (solver) | 27 | EXACT |
| 7 | 21 (21) | 21 | 29 | Z≥30 UNSAT (LRAT) | 21, T≥22 UNSAT (solver) | 36.75 | EXACT |
| 8 | 24 (16) | 30 | 38 | Z≥39 UNSAT (LRAT, pieces) | **32** (√7 octagon), T≥33 UNSAT (LRAT, pieces) | 48 | EXACT |
| 9 | 36 (30) | 40 | 50 | Z≥51 UNSAT (solver; LRAT re-check running) | 40*, T≥41 UNSAT (solver, apex cover*) | 60.75 | solver-exact |
| 10 | 40 (40) | 52 | 64 | Z≥65 running on Studio | not run | 75 | open |
| 11 | 55 (55) | 65 | 77 | not started (not approved) | not run | 90.75 | open |

\* The **apex cover** is a new symmetry-breaking scheme Paul has not reviewed yet. Keep the n=9 max-T result out of the headline numbers until he has.

**Certificate kinds**
- **"LRAT":** Glucose 4 produced a DRUP proof, drat-trim converted it to LRAT, and cake_lpr accepted it.
  - n = 5–7: single mode, with no symmetry breaking.
  - n = 8: pieces mode, 468 lex pieces.
- **"solver":** CaDiCaL 1.5.3 via pysat only.

## Lower bounds
1. **Regular n-gon:** Z = n·⌊(n−1)/2⌋.
2. **Aggarwal's Prop. 2 construction:** a centre v plus n−1 equal-chord points spanning less than 180°.
   - Counts: apex v gives C(n−1,2), and arc vertex i gives min(i−1, n−1−i).
   - Checked numerically for n = 5–12. It is a correct lower bound.
3. **The 60° fan:** centre O plus n−1 consecutive vertices of a regular 6k-gon, with k = ⌊(n−2)/3⌋+1.
   - There are n−1−k equilaterals, so Z = Aggarwal(n) + 2(n−1−k) and T = Aggarwal(n).
   - Z for n = 5–11: 12, 20, 29, 38, 50, 64, 77.
   - Certified by `certify_construct.py`: exact trig identities, 60-digit interval separation for all other distances, and interval strict convexity.
4. **The √7 octagon:** Z = T = 32, beating Aggarwal's 30 in his own convention.
   - Vertices: (0,0), (1,0), ((3+√7)/4, (1+√7)/4), ((3+√7)/4, (5+√7)/4), (1/2, (2+√7)/2), (−1/2, (2+√7)/2), (−(1+√7)/4, (3+√7)/4), (−(1+√7)/4, (√7−1)/4).
   - It is equilateral with 4-fold symmetry, and its vertices alternate between two concentric circles (radii ≈ 1.18804 and 1.38255).
   - Per-vertex counts are 5, 3, 5, 3, …. There are no equilaterals and only 5 distinct distances.
   - Certified exactly with sympy (`certify_exact.py`), and independently re-checked by main.
   - It is not a contradiction: Prop. 2 is only a lower bound. Asymptotically this kind of shape gives about n²/2.
5. **Searches:** none beat the 60° fan in Z.
   - Regular-N-gon subsets: with the centre for N ≤ 39, without it up to the enumeration limit.
   - Every model realised by the CEGAR loop.

## Upper bounds (`iconv_sat.py`)
- **Encoding:** the unchanged tstar_v2 v1 Enc(n, n−1, order=True, atmost=True), with families G, X and O. No new rule family was used.
- **Objective:** a totalizer over e(c;u,v), so the sum is exactly Z. For T: iso(abc) ↔ e(a;b,c) ∨ e(b;a,c) ∨ e(c;a,b), plus the redundant Z ≥ T.
- **Lex cover:** vertex-0 RG partitions, mirror-skipped. This is the reviewed T* cover.
- **CEGAR, per model:**
  1. Λ, with an exact Farkas certificate;
  2. Singular core, confirmed over Q;
  3. whole-pattern saturation;
  4. numeric realisation with a 60-digit polish;
  5. otherwise SURVIVOR, which is blocked.
- **Apex cover (new, unreviewed):** max_c Z_c ≥ Z/n ≥ T/n.
  - Rotate a vertex with maximum Z_c to position 0, reflecting if needed.
  - The pieces are then {π : mirror(π) ≥ π, n·apex(π) ≥ T}, with the assumptions Z_c ≤ apex(π).
  - It matches lex on all three n = 8 checks: Z at 39 UNSAT, T at 33 UNSAT, and T at 32 re-finds the octagon.
- **Lemma usage:**
  - At T = best+1, the Z runs for n = 5–9 had zero models, so no Λ or Singular lemmas were used.
  - n = 8 max-T used 28 Λ lemmas (re-verified) and 1 Singular core.
  - n = 9 max-T had 11 Λ kills, all re-verified, and no survivors.
- **No-over-pruning test** (`validate_enc.py`):
  - real tied polygons must come out SAT, and all did: n = 6 300/300, n = 7 300/300, n = 8 283/283, n = 7 with the T objective 200/200;
  - with G/X/O and Λ off, n = 6 and 7 give the same bounds.

## Extremal Z structures (up to dihedral symmetry)
All are a centre plus points of a regular 6k-gon on an arc of less than 180°.
- **n = 5:** 2 structures, {0,30,60,90}° and {0,30,60,120}°.
- **n = 6:** unique, the 30° fan. Per-vertex counts [10,1,2,4,2,1].
- **n = 7:** unique, the 30° fan. Per-vertex counts [15,1,2,4,4,2,1].
- **n = 8:** 3 structures, each certified Z = 38, T = 30: the 18-gon at {0..6}, the 24-gon at {0,2,4,5,6,8,10}, the 18-gon at {0,2,3,4,5,6,8}.
- **n = 9:** not enumerated.
- **Max-T extremals:** fans at n = 6, 7 and 9; the √7 octagon at n = 8.

## Comparison with 3n²/4
- I_conv(n) − 3n²/4 for n = 5–9: −6.75, −7, −7.75, −10, −10.75.
- The fan gives about 3n²/4 − 1.42n.
- Every exact value so far equals the fan formula.

## Trust summary
- **Lower bounds:** certified.
- **Z upper bounds for n ≤ 8:** LRAT-verified, relative to the trusted encoding lemmas and to the CNF meaning what the code says.
- **n = 9 Z:** solver-only, lex cover; the LRAT re-check is running.
- **n = 9 max-T:** solver-only, apex cover (unreviewed).

## Files
`Erdos/agent_runs/iconv/` contains:
- `code/`: iconv_sat.py (md5 fd25115a…), realise.py, geom.py, canon.py, certify_construct.py, certify_exact.py, proof_check.py, validate_enc.py, lib/;
- `iconv_cloud_runs.tgz`;
- `STATUS_FOR_MAIN.txt`;
- `runs/`.

## Open items
1. **n = 10 Z (Studio):**
   - Setup: `code/iconv_sat.py 10 65 runs/n10 --r R --W 12`, 12 workers, started 02:27Z.
   - Progress at 04:33Z: 3,142/10,743 pieces, 0 models.
   - ETA: about 12–15Z on 6 Nov (±50%). It is restart-safe.
2. **n = 9 Z LRAT re-check (Studio):**
   - Setup: `code/proof_check.py 9 51 runs/n9proof pieces --r R --W 6`, started 04:33Z.
   - Each worker ends with PROOF VERIFIED or PROOF FAILED.
3. **One-line progress check:**
   ```
   cd /Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/iconv && echo "n10 done $(cat runs/n10/done.w* | wc -l)/10743 models $(cat runs/n10/models.w* | wc -l) surv $(cat runs/n10/surv.w* | wc -l) realised $(cat runs/n10/realised.w* | wc -l) DONE $(grep -l DONE n10_w*.out | wc -l)/12; n9proof finished $(grep -l PROOF n9proof_w*.out | wc -l)/6 verified $(grep -l 'PROOF VERIFIED' n9proof_w*.out | wc -l) fails $(grep -h FAIL n9proof_w*.out | wc -l)"
   ```
4. **Not done:**
   - n = 11 (3–6 days; not approved);
   - n = 9 and 10 extremal enumeration;
   - alg_sat re-certification of the n = 8 max-T Singular core;
   - Paul's review of the apex cover;
   - an LRAT run for n = 9 max-T.
5. **Housekeeping:** kill the iconv guard.sh (pid in `iconv/guard.pid`) after the jobs finish.

No paid model calls were made, and no war-room, .env or other runs were touched.
