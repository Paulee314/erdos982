# C4 (Fishburn), n = 11: certified UNSAT, 5 Nov 2026

**Result.** Every one of the 100 sub-cases t(0) = a, t(1) = b (a, b = 1..10) is VERIFIED UNSAT. Together they cover
every value of t(0), the full split Wonder requires. So **no strictly convex 11-gon has Σ_x t(x) ≤ C(11,2) − 1 = 54**.
Fishburn's C4 holds at n = 11.

## Setup

**Families.** All Wonder-cleared:
* SAT side: base + F + G/X/O + A/D/N + angle_fams2-K (`fams` tag `ADFGKNOX`).
* LP side: Λ/K/P/H/Δ (Σ off).
* No LP-learned clause was needed in any sub-case (core_learned = 0 everywhere), and no SAT or LP-feasible model ever
  appeared.

**Pipelines.**
* **95 sub-cases, fast pipeline (B+C):**
  * one CaDiCaL 2.1.3 solve with `--lrat`;
  * check with cake_lpr, the CakeML-verified checker (git a4323b203cc9ecd584ba7da9e3fff08135a09d5f, binary sha256
    fb21a64a…bbcf83), which gives `s VERIFIED UNSAT`;
  * code md5 8e5eb4ea…
* **5 sub-cases, original two-round pipeline:** (3,5), (4,4), (4,5), (4,6), (5,3).
  * Steps: CEGAR search, CaDiCaL 2.1.3 binary-DRAT proof, then drat-trim `s VERIFIED` with core.
  * Code md5 a03209f5…; the only code difference is the hand-off guard in c4_cegar.main.
  * (3,5), (4,4) and (4,5) were re-run on the fast pipeline during validation. All three verified again, with identical
    CNF sha256.

**Raw proofs.** Deleted after verification, with sha256 and size kept. The CNFs and the reference/core lists are kept
gzipped. In total there were 0.227 TB of LRAT/DRAT, 27.6 CPU-h of solving and 4.0 CPU-h of checking.

**Hardest sub-cases** (solve time, seconds): (6,5) 11,808, (6,6) 9,769, (5,5) 6,392, (6,4) 5,828, (5,6) 5,094,
(7,4) 4,893.

## Machines and cross-checks

**Machines.**

| Driver | Machine | Sub-cases | Location |
|---|---|---|---|
| A | Studio | 56 | `agent_runs/c4_studio/state/prod11` |
| B | Studio | 27 (the 6 centre double-runs + 21 moved from the MacBook) | `state/p11c` |
| fast | MacBook | 12 | `~/c4/prod11f` |
| old | MacBook | 5 | `~/c4/prod11` |

**Old-pipeline copies of the 6 centre sub-cases.** These stayed on the MacBook as a cross-check. Each was stopped as soon
as its Studio fast-path copy VERIFIED (log: `mac_old/CROSSCHECK.log`).
* (5,6): the old search had independently reached UNSAT (14,794 s) before it was stopped during its certification.
* None of the old copies completed certification.
* The old driver's log lists these stopped copies as "FAILED_R1", "NO_SUMMARY" or "search FAILED". It also logs the 89
  re-assigned sub-cases as "HANDED_OFF". These are approved stops and reassignments, not errors.

## Records
* `COMBINED_n11.json`: one entry per sub-case per run, with source, pipeline, times, proof and CNF sha256, fams and
  code version.
* `studio_A/`, `studio_B/`, `mac_fast/`, `mac_old/`: STATUS, logs, summaries, gzipped CNFs and core/reference lists.
* `MOVE_LOG.txt` and the `list11_*` files: the static split and the rebalance.
