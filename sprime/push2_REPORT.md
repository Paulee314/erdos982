# S′ push 2 (Erdős #982): report (4 Nov 2026, ~20:40 CT)

Tags: COMPUTED (machine result, with its certificate status stated) / PROVED (written proof, refereed by Wonder) / BELIEVED.
All files are under sprime/push2/ (cloud). The container restarted twice; every run was relaunched from saved clause files.

## 1. Status of S′ by n
| n | status |
|---|---|
| ≤ 9, 11 | COMPUTED earlier with family F (DRUP) |
| **10** | **COMPUTED, fully certified.** Bundle `cert_n10/` (`verify.sh` takes about 1 min) contains: base + F + **113 Λ clauses**. Each Λ clause carries an exact rational Farkas certificate, accepted by the independent checker. The script regenerates the CNF from the generators and matches it to the shipped CNF; drat-trim gives **s VERIFIED**. A second, independent certificate (base + B + F + 65 Λ/Λ-MEC/Λ-circle clauses, `fc2_10_*`) is also drat-trim VERIFIED. All 846 old survivors are dead under equality-only Λ, so the mod-p/Gröbner route is no longer needed. Details: `cert_n10/README.md`. |
| 12 | **Not yet UNSAT.** The CEGAR run with Λ + Λ-MEC + Λ-circle + Λ-bisector has learned about 64k base clauses (2.5M with dihedral images). Across more than 5,000 refinement iterations it has **never found an angle-feasible model**. The rate at which a probe finds new minimal violating patterns fell from ~6/s to ~0.5/s. Every sampled survivor dies under the LP: 2,101/2,101 + 2,000/2,000 F-minimal samples, and 248/248 of the latest probe, by equalities alone; in an earlier probe 282/300 died by equalities alone and the rest needed strict comparisons. Two workers are still running: `cegar2_12P.log`, `cegar2_12Q.log`. BELIEVED: n = 12 closes with the same families given more CPU. |
| 13 | Not run to completion since the restart. 1,500/1,500 sampled F-minimal patterns are killed by equality-only Λ. BELIEVED to close the same way. |

## 2. New clause families (all D_n-invariant)
| family | content | proof / referee | empirical validation (true polygons) |
|---|---|---|---|
| **Λ** (angle LP, lazy, certified) | Variables are the elementary fan angles. Rows: positivity, interior angle < π, triangle sums, and side ⇔ opposite-angle order for chords sharing a vertex. A clause is the negation of a literal set whose rows have an exact Farkas certificate. | PROVED; Wonder: "sound with fixes". The fix was the checker's domain validation: malformed tags had let an empty core be "certified". Fixed, and a planted malformed certificate is rejected. | 10,115 (n=10), 9,148 (n=12), 9,110 (n=13) polygons incl. regular/bi-regular/mirror/dihedral/fan: 0 failures. Planted errors caught 353/353 and 162/351. Control: the false conjecture Q stays SAT, and the Danzer 9-gon satisfies all rows. |
| **Λ-MEC** (violators only) | MEC support selectors from B. Rows: concyclic support points see a chord at equal angles (C). A non-support vertex sees a support chord under a larger angle than the inscribed one, or > π − inscribed on the opposite side (I). Consecutive supports subtend < π/2 at any other support (R, uses L3). | PROVED; Wonder: "sound with fixes". R is valid only for violators (stated). Literal polarity and distinctness are now checked in the checker; a planted dropped-support literal is rejected. | 10,684 / 10,850 / 11,064 case-(M) polygons, 0 failures; planted side flip caught 272/272 |
| **Λ-circle** (K) | \|pa\| = \|pb\| and v inside / on / outside circle(p, \|pa\|) ⇒ A(v;a,b) >, =, < the inscribed angle on v's side. | PROVED (inscribed-angle comparison); not separately refereed | 11,384 / 10,534 / 10,504 polygons, 0 failures; planted caught 184/264 |
| **Λ-bisector** (P) | \|pa\| = \|pb\| and \|va\| vs \|vb\| ⇒ the ray p→v lies on a's or b's side of the bisector ray of ∠apb (linear in fan positions). | PROVED (bisector of an isosceles apex); not refereed | only 377 polygons (n=10), 0 failures; planted caught 71/192. **Below the 10k target; validate further before relying on it.** |
| T1, T4 (static k-point lemmas) | T1: an equidistant triple's middle point is not the base of another isosceles triangle whose base sector contains the triple. T4: three nested base sectors at one vertex. | PROVED; Wonder: "sound with fixes" (distinctness hypotheses) | n=10 2,000 polygons, 0 failures. On their own, F + T1 + T4 are still SAT at n = 10. |

Infrastructure: `cegar.py` / `cegar2.py` (tiered CEGAR: equalities first, then MEC, then strict comparisons and circle rows; dihedral images; clause sharing between workers), `angle_lp.py`, `check_lambda_certs.py` (independent exact checker for all row kinds), `certify_lits.py`, `final_certify2.py` (two-round pipeline: DRUP core → exact certificates for the core clauses only → checker → DRUP again), and validators `val_lambda.py`, `val_mec.py`, `val_circle.py`, `val_lits.py`.

## 3. Case (M) (human proof): what is PROVED
* **Lemma 1:** Σ_v int(v) = (n−2)π follows from the triangle equations alone, so the linear system already gives "≤ 3 vertices with angle ≤ π/2" (refereed; the m = n boundary case was added).
* **Lemmas 2 and 3:** a neighbour-base vertex is acute; the middle point b of an equidistant triple has ∠(x b z) = π − ∠(x p z)/2 > π/2. Refereed.
* **M1:** a non-support vertex in gap (s1, s2) sees s1 s2 under > π − θ12/2.
  **M2:** a window equality with apex and both partners inside one gap forces θ > 2π/3, so at most two gaps contain one. Refereed. Wonder's "straddle" objection does not apply in case (M): gaps have ≤ h−1 steps, so a window cannot wrap around within a gap.
* **S1 (support straddle):** with a ∈ (s, s′], b ∈ (s′, s′₂) and \|sa\| = \|sb\|, the angles at s′ and b exceed Λ/2, so θ + θ₂ > π. Refereed; needs b ≠ s′₂.
* Fable (not refereed): L-A (crossing lemma); L-B/L-C (the far partners b_i ≤ c_i lie in the opposite gap, and P(b_i) ⊆ (b_i, s_i] does not wrap); L-D (three cases for the near partner).
* COMPUTED (floating-point MILP, not certified): the pure 2n-window linear system is infeasible for n = 8, 9. With only the n P-windows it is FEASIBLE, e.g. pairs (p+3, p+4). So any proof must couple P- and Q-windows at different vertices.
* **MISSING:** a proof of case (M). Fable's assessment (`push2_f_M2.txt`) is that m = 3 does not close with one-apex tools. The partner vertices' own windows are needed, which matches the computer's cores: 5–15 equalities on 7–12 vertices. Fable gives a finite LP test list (≈122 sign patterns for m = 3), not yet run.


## 5. Recommended next steps
1. **n = 12:** let workers P/Q finish. To resume: `cegar2.py 12 OUT preload=pre12_j.jsonl,m12_all7.jsonl,<new m12_*.jsonl> circ=1 bis=1`. Then run `final_certify2.py 12 fc12 BF <all m12 files>`, which produces the DRUP core, exact certificates, the checker run and a second DRUP. With bis=1 the clauses can contain Λ-bisector rows, so first validate those on ≥ 10k polygons, or rerun with bis=0.
2. **n = 13:** the same pipeline, which is better parallelised on the Studio once it is free: N workers sharing clause files.
3. **Human proof:** the learned cores cluster into a few k-point lemma types (16 certified types for k = 5–7, which embed into ~10^5 clauses at n = 12–13). Classifying the cores by type (`classify_cores.py`, `emb_lib.py`) is the route to a finite forbidden-configuration list. Also run Fable's m = 3 LP test list.
