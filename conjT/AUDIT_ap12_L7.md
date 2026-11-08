# Audit of the Conjecture T run at n = 12 (L = 7): ap12_L7/ (v1) + ap12_L7_v2/ (v2)

Mac Studio, agent_runs/theory2. Audit 5 Nov 2026, 22:05-23:00 UTC, by the main Claude session.

## Verdict

Conjecture T is verified at n = 12. It is COMPUTED, and relative to the soundness of the encoding:
no strictly convex 12-gon has Z_p >= 7 at every vertex.

The result rests on:
- the v1 encoding lemmas, as for n = 11 (see AUDIT_ap11_L6.md);
- the v2 static families G, X and O (Wonder referee in v2_bench/, plus 10k-polygon empirical validation);
- the UNSAT answers of the SAT solver. No DRUP proofs were produced, as at n = 11.

Every algebraic kill is certified exactly and re-checked independently. No Lambda clause was ever needed: v2 found 0 models.

## Runs

| run | dates | pieces | done records | duplicates | models | CPU |
|---|---|---|---|---|---|---|
| v1 (apex_pieces.py v13) | 2-5 Nov 2026, stopped 19:20Z | 16,074 distinct | 21,919 | 4,960 (RESPLIT race) | 4, all blocked by k=6 cores | 2,676,014 s |
| v2 (apex_v2.py) | 19:20:34Z to about 22:00Z on 5 Nov | 249,317 (frozen list, md5 c65a8ac4...) | 249,317 | 0 | 0 | 150,811 s |

v2 tag: v2[G+X+O+LAM]md5=70af391df465.

Coverage: kept 265,391 = v1 16,074 + v2 249,317. Overlap 0, missing 0, extra 0.

## Certification of the v1 core library

- `cores_to_patterns.py ap12_L7` gives 9 distinct cores: 1 with k=5 and 8 with k=6.
- `certify.py ap12_L7 5 0 1` and `certify.py ap12_L7 6 0 1`: 9/9 VERIFIED, all with std = {1}, no saturation.
- As a cross-check, alg_sat_v2 was also run on the 4 full v1 models (ap12_L7_v2/v1_algpass/): 4/4 VERIFIED, std = {1}.
- `ap12_L7/w12.big` holds 7 lines with no matching .models records. They come from w12's unfinished piece at the moment of the stop: .models writes are buffered.
  - That piece is not in v1 done, so it was re-solved in v2, with 0 models.
  - The checker's "short 0" confirms that every completed v1 piece has all of its model lines.
  - An empty ap12_L7/big_all.txt was created so that verify_indep.py could run. The v1 run recorded no 'big' models.

## Checks

- `check_run_v7.py 12 ap12_L7_v2 7 --v1dir ap12_L7 --piecelist ap12_L7_v2/pieces_todo.txt` gives AUDIT PASS (ap12_L7_v2/final_check2.log).
  - The first run, before the core certificates, gave AUDIT FAIL with only "uncertified 4" (ap12_L7_v2/final_check.log).
- `verify_indep.py ap12_L7 12` gives INDEPENDENT CHECK PASS (ap12_L7_v2/VERIFY_INDEP_v1.txt):
  - 9/9 certificate identities re-expanded;
  - 4/4 models contain a certified core;
  - 0 failures.
- Lambda: 0 records, 0 needed.
