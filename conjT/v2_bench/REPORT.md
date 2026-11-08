# T* n=12 v2 encoding benchmark: report (5 Nov 2026)

Written by the benchmark agent; saved by the main session, because the agent couldn't write this file itself.
Cloud-only work: about 2.8 cloud core-hours at nice 10. No Studio CPU, no model calls, live runs untouched.

## Bottom line
- v2 adds the static families G, X and O, plus a lazy angle LP (Λ) that runs before Singular.
- It reached the same outcome as v1 on every piece tested: 192 pieces under v2, all UNSAT with no survivors.
- It is about 16× faster on the same machine.
- It fixes the heavy tail. Pieces that kept Studio workers stuck for 6–11+ hours took 147–385 cloud-s under v2.

Final tag: `v2[G+X+O+LAM]md5=70af391df465`.

## Live-run bug (independent of v2)
Each RESPLIT worker read the done files at its own start time, so the workers' slices overlap.

Verified by the main session at 18:15Z:

| | |
|---|---|
| lines in `w*.done` | 21,911 |
| distinct pieces | **16,066** (6.05% of 265,391) |
| pieces solved ≥2 times | 4,960 |
| CPU wasted | ≈ 662k CPU-s, about 25% of the run's CPU |

Some pieces are assigned to no worker at all, so they will need a final pass.

## Validity per family
- **Excluded:** B, B0/B1 and Λ-MEC. They assume an S′ violator, and the code rejects them by name.
- **Used:** G, X, O and plain Λ, which hold in every strictly convex polygon.
- **DAE:** not added. All 660 of its clauses are already in the base encoding.
- **NB:** its angle-forcing form is already in X (1,320 of 1,320 clauses). NB-direct is UNREFEREED and not used.
- **R3:** equivalent to the base gap clause. UNREFEREED, not used.

## Validation
- **New rule families:** 10,000 true 12-gons, 6,772 of them with exact distance ties. There were 0 violations in G, X, O, N, K, NB, R3 or DAE, and all 7 planted false variants were caught.
- **No over-pruning:** the integrated v2 clause set is satisfiable for 400 of 400 real 12-gons.
- **Λ certificates:** the independent checker accepted 33 of 33, and rejected 24 of 24 corrupted ones.

Polygons tested: Valtr random, near-circle, exact subsets of regular N-gons (N = 12–48), k-fold rotational and mirror-symmetric, fan, fan4, perturbed regular (10⁻⁶ to 10⁻³), and the regular 12-gon.

How many polygons caught each planted false variant:

| planted variant | polygons caught |
|---|---|
| NB with LT reversed | 6,500 |
| NB with disjoint intervals | 2,439 |
| NB with overlapping intervals | 1,228 |
| R3 with a chord literal dropped | 96 |
| DAE with a premise dropped | 6,343 |
| G with a budget of 2 | 10,000 |
| O plus one g | 7,160 |

## Regression
No disagreements.
- All 192 v2 pieces are UNSAT with no survivors, matching v1.
- Piece 20379's single v1 model is now pruned inside SAT.
- All 8 real T* patterns die under equality-only Λ, with cores of 4–8 equalities.
- Test at n=8, L=4 (12 pieces):
  - v1: 37 models, handled by Singular;
  - Λ only: 25 models, all killed by Λ;
  - full v2: 0 models;
  - none of the three leaves a survivor.

## Speed-up
R = cloud/Studio CPU ratio ≈ 2.8 (2.0–3.8).

| comparison | speed-up |
|---|---|
| same machine, uniform 52-piece sample | 15.6× (median 8× per piece); means 127.3 → 8.16 cloud-s |
| same machine, warm 23-piece stream | 17.4× |
| production streams w3 / w7, 60 pieces each, vs Studio records | 39,322 Studio-s → 420 cloud-s; 59,509 Studio-s → 684 cloud-s (≈244× and 262×) |
| G+X+O alone vs adding NB/R3 | 374 vs 420 s, so NB/R3 add nothing |

Trivial pieces, 55% of the total, gain nothing: about 0.3–0.5 cloud-s each.

Fresh-solver sample, Studio v1 vs cloud v2:

| piece | Studio v1 (Studio-s) | cloud v2 (cloud-s) |
|---|---|---|
| 7036 | 55 | 12.8 |
| 2943 | 57 | 14.1 |
| 12151 | 82 | 18.4 |
| 10396 | 99 | 7.2 |
| 7251 | 113 | 9.7 |
| 11388 | 129 | 7.4 |
| 18119 | 218 | 18.0 |
| 8074 | 222 | 8.5 |
| 7314 | 249 | 9.0 |
| 18227 | 468 | 154 (cubed) |
| 19704 | 2,068 | 192 |
| 20379 | 2,166 | 203 |
| 14460 | 2,259 | 210 |

## The tail
- **Stuck pieces:** 20033, 20069, 20838, 19812 and 20802 have had Studio workers stuck on them for 6–11+ hours. Under v2 they took 147–385 cloud-s.
- **Slowest completed pieces:** the five slowest took 20,000–35,800 Studio-s under v1, and 19–177 cloud-s under v2.
- **Cubing:** 3,892 cubed pieces used 2.46M CPU-s, which is 95% of the recorded 2.59M. None needed an unlimited solve, so a time cap with re-splitting would not cut v1's total CPU.
- **Conflict budget:** under v2 the remaining cost is the cubing floor. A budget of 2M took piece 19704 from 192 s to 71 s. That is a single data point.

## ETA for the ~249k remaining pieces
Assumes 16 workers at 94% utilisation, about 1.30M Studio-CPU-s per day, and that the later piece region behaves like the samples measured so far.

| basis | v1 cost per piece | v1 ETA | v2 ETA |
|---|---|---|---|
| uniform sample | 45.5 Studio-s | 8.7 d | 13.5 h (2.9 Studio-s per piece, measured) |
| mean of completed pieces | 118 Studio-s | 22.6 d | 1.4 d (at 16×) |
| most recent fifth of completed pieces | 394 Studio-s | 75 d | 4.7 d at 16×; ~15 h from the stream measurement |

Add 33% to the v1 figures while the duplication bug persists.

## Recommendation
Restart with v2 (G+X+O+Λ) on the not-done pieces, using a frozen piece list (`make_piecelist.py` + `PIECE_LIST`). First test a CONF_BUDGET of 1–2M.

Before relying on the result:
1. Update check_run_v6 to accept `lambda-*` kills and the version tags.
2. List G, X and O as trusted lemmas in the certificate audit.
3. Have G, X and O refereed for this use.

## Files
- **Code:**
  - `apex_v2.py`, `fams_v2.py`, `lambda_v2.py`, `make_piecelist.py`
  - `apex_pieces_v1.py`: byte-identical to Mac v13, md5 fe341427…
  - copied unchanged: `angle_lp.py`, `angle_fams2.py`, `check_lambda_certs.py`
- **Validation:** `val_v2.py`, `val_10k.log`, `integ_check.py`, `check_subsumed.py`, `lam_test*.{py,jsonl}`, `s8_lambda_all.jsonl`
- **Benchmarks:** `bench.py`, `bench_stream.py`, `bench_small.py`, `analyze.py`, `results/*.tsv`, `logs_*.txt`
- **On the Mac:** `theory2/v2_bench/` holds `snapshot_in.tgz`, `tstar_v2_bundle.tgz` and the unpacked `tstar_v2/`.

**Note for deployment:** v2's Λ needs numpy and scipy. The Studio T* venv (`e982/venv`) has neither, and neither does the MacBook `tstar` env. Use the S′ venv (`tests_abc/venv`) or install them first.
