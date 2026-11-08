# Property S′ (the window variant of #982): n = 8, 10, 11 and 13

Let h = ⌊n/2⌋, P(p) = {p+1, …, p+h} and Q(p) = {p−h, …, p−1} (mod n). **S′(p)** holds if the distances from p to
P(p) are pairwise distinct, or the distances from p to Q(p) are. **S′ holds for n** if every strictly convex n-gon has
a vertex with S′(p). S′(p) gives p at least h distinct distances, so S′ for n implies #982 for n; S′ is strictly
stronger. For n ≤ 7 and n = 9 it follows from the Erdős–Fishburn run theorem (a run of ⌊(n+3)/3⌋ increasing
consecutive distances from some vertex; for these n that is ⌊n/2⌋).

## Status

| n | result | SAT proof | checked by | other certificates | files |
|---|---|---|---|---|---|
| ≤ 7, 9 | in print (Erdős–Fishburn) | also computed: base + F UNSAT (Glucose 4) | drat-trim | — | `n8_n9_proofs/sprimeF_9.drup` (n = 9) |
| 8 | **computed** | base + F UNSAT (Glucose 4) | drat-trim `s VERIFIED` | — | `n8_n9_proofs/sprimeF_8.drup` |
| 10 | **computed** | base + F + 113 Λ clauses UNSAT (Glucose 4) | drat-trim `s VERIFIED` | 113 exact Farkas certificates, accepted by the independent checker; the CNF is regenerated from the generators and compared | `cert_n10/` (bundle; its CNF and DRUP are in `MANIFEST.txt`) |
| 11 | **computed** | base + F UNSAT (Glucose 4) | drat-trim `s VERIFIED` (re-checked 5 Nov 2026) | — | proof not archived on the Studio (see MANIFEST) |
| 12 | **open; running** | CEGAR with Λ, Λ-MEC, Λ-circle, Λ-bisector, hinge, Δ and Σ families, three workers since 5 Nov 2026 | — | — | not in the repo (state files are being appended; sizes in `MANIFEST.txt`) |
| 13 | **computed, certified** | CEGAR (families B, F), then two-round certification: round 2 CNF = base + B + F + 105,990 certified learned clauses, UNSAT; DRUP proof | drat-trim `s VERIFIED`; LRAT from drat-trim checked by **cake_lpr** (`s VERIFIED UNSAT`) on the cleaned CNF | 105,990 exact Farkas certificates, each accepted by `check_lambda_certs.py` | `n13_logs/`, `n13_state/`, `diag13/` |

S′ at n = 12 is not claimed. S′ at n = 13 does not imply it (deleting a vertex changes the windows).

The cake_lpr check applies to n = 13 only. n = 8, 10 and 11 are drat-trim only.

## The n = 13 certification, including the round-2 bug (6 Nov 2026)

The CEGAR workers (`code/cegar2.py`, `n13_logs/w13_{A,B,C}.out`) finished UNSAT on 5 Nov with 524,901 learned clauses
(`n13_state/w13_*.jsonl`, `pre13.jsonl`). `code/final_certify2.py` then certifies in two rounds:

1. **Round 1.** CNF = base encoding + families B, F + every learned clause (all dihedral images). Glucose 4: UNSAT in
   21,476 s; drat-trim `s VERIFIED` with core extraction (DRUP 10.3 GB). The core used 105,782 learned clauses.
2. **Exact certificates.** Each learned clause in the core gets an exact rational Farkas certificate for its own
   literal set, accepted by the independent checker: 105,782 ok, 0 failed.
3. **Round 2.** CNF = base + B + F + exactly the accepted clauses. **This came out SAT** (`n13_logs/cert13.out`,
   "FINAL n=13: NOT VERIFIED").

Diagnosis (`diag13/check.py`, `check2.py`, `cnfscan.py`): drat-trim prints core clauses with duplicate literals
removed. One core lemma, `-1860 -1907 -2520 -2520 -6402 -7151`, has a repeated literal; the round-2 matching compared
sorted literal tuples, so that lemma did not match any learned-clause key and was silently left out of the round-2
CNF, which then had a model (`diag13/final.model`). The fix (`diag13/make_fix.py` → `code/final_certify2_fix.py`):
match core clauses by literal **set**, de-duplicate literals in round-2 clauses, and allow re-use of the round-1 core
after checking that every core clause is a base or learned clause. The bug drops lemmas, so it can only make round 2
fail, never pass wrongly; the round-1 proof and the certificates were unaffected.

Fixed run (`n13_logs/cert13fix.out`, 6 Nov): round-1 core re-used (472,828 core clauses, all found among base or
learned clauses); 105,990 core lemmas, 105,990 certificates ok, 0 failed; round 2 UNSAT in 14,673 s; drat-trim
`s VERIFIED` (DRUP 10.6 GB).

LRAT and cake_lpr (`n13_logs/lrat13.sh`, `LRAT13.log`): drat-trim re-verified the round-2 proof in LRAT mode and wrote
a 21 GB LRAT file; cake_lpr **rejected it at line 478** ("clause not empty or singleton after reduction"). The round-2
CNF contained 234 tautological clauses and 156 clauses with a repeated literal. drat-trim deletes duplicate literals as
it reads (see the warnings in `lrat13_drattrim.out`), so the LRAT it writes refers to the clauses as drat-trim stored
them; the likely cause of the rejection is that cake_lpr parses the CNF as written. `lrat13b.sh` removed the tautologies, merged the duplicate literals (1,918,483 clauses
kept), re-ran drat-trim in LRAT mode (`lrat13b_drattrim.out`: `s VERIFIED`, 23,249 s) and cake_lpr on the result:
**`s VERIFIED UNSAT`** (`lrat13b_cake.out`, `LRAT13b.log`, 7 Nov 2026 23:12 UTC). Removing a tautology and merging a
repeated literal do not change the clause set's meaning, so the cleaned CNF is equivalent to the round-2 CNF.
sha256 of the cleaned CNF and of the LRAT file are in `LRAT13b.log`; the proof files were deleted after checking.

## Trust base

Every S′ result depends on the soundness of the base encoding (`sat/testA_sat.py`, `sat/e982lib.py`: the #982 clause
families with the class bound removed, plus both window clauses at every vertex, and the dihedral lex-leader), family F
(at most two angularly disjoint wide triangles at a vertex), family B (minimum-enclosing-circle selectors; it uses a
lemma that holds for S′-violators, which is what is being searched for), and, where used, the angle-LP clauses, each of
which carries an exact certificate checked independently. The SAT checkers certify unsatisfiability of the CNF, not
that the CNF encodes S′. `push2_REPORT.md` is the report on the LP row families and their written reviews;
`cert_n10/README.md` describes the Λ rows and the n = 10 certificate in detail.

## Layout

- `n13_logs/`: `cert13.out` (buggy round 2), `cert13c.out` (a CaDiCaL copy of round 1, stopped), `cert13fix.out`,
  `LRAT13.log`, `LRAT13b.log`, `lrat13*_cake.out`, `lrat13*_drattrim.out`, `lrat13.sh`, `lrat13b.sh`, `w13_{A,B,C}.out`
  (the CEGAR workers), `smoke10.out`, `notes.log`, `jobs.log`, `launch.sh`.
- `n13_state/`: `w13_{A,B,C}.jsonl`, `pre13.jsonl` (the learned-clause records), `smoke10.jsonl`.
- `diag13/`: the diagnosis scripts and outputs, `final.model`, `make_fix.py`.
- `code/` (n = 13 run: `cegar2.py`, `final_certify2.py`, `final_certify2_fix.py`, `check_lambda_certs.py`, the LP row
  generators `angle_lp.py`, `mec_rows.py`, `circle_rows.py`, `hinge_rows.py`, `delta_rows.py`, `sigma.py`, validation
  scripts), `code_v2/` (the n = 12 run: `cegar2.py` with the Δ and Σ tiers), `sat/` (base encoding and angle families).
- `n8_n9_proofs/`: `sprimeF_8.drup`, `sprimeF_9.drup` (Glucose 4 DRUP proofs; the CNFs are regenerated by
  `sat/testA_sat.py` with family F).
- `cert_n10/`: the n = 10 bundle (`README.md`, `verify.sh`, the 113 Λ clauses with certificates, the generators); the
  6.4 MB CNF and 12.7 MB DRUP are listed in `MANIFEST.txt` and the CNF is regenerated by `cert_n10/code/regen_cnf.py`.
- `MANIFEST.txt`: the n = 13 CNFs, DRUP proofs, cores and certificate files (sha256, size); the n = 12 state (sizes
  only, in progress); the n = 10 CNF and DRUP.

AI use: the encoding, the CEGAR loop, the LP row families, the certifiers and the checkers were written by AI tools under
my direction; the row families were reviewed by two other models; the runs, the round-2 bug diagnosis and the fix were
done by AI agents; this note was drafted by an AI tool and edited by me.
