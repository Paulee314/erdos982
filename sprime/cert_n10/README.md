# Certificate: no strictly convex 10-gon violates S′ (Erdős #982 strengthening)

Status: COMPUTED and machine-checked (`./verify.sh`, about 1 minute). The result depends on the soundness of the clause
families listed under "Trusted base"; each has a written proof that a referee model has reviewed.

## Statement
For every strictly convex 10-gon (vertices 0..9 ccw, h = 5) some vertex p has pairwise distinct distances to
P(p) = {p+1..p+5} or to Q(p) = {p−5..p−1}. With the earlier results (n ≤ 9, n = 11 via family F, DRUP-checked), S′ is
now COMPUTED for every n ≤ 11, which implies #982 for those n.

## Files
| file | content |
|---|---|
| `sprime10_F_lambda.cnf` | 356,059 clauses / 9,926 vars = 351,326 base + 4,620 family F + 113 Λ |
| `sprime10_F_lambda.drup` | Glucose 4 DRUP refutation (drat-trim: `s VERIFIED`; 46,747 core lemmas) |
| `lambda_clauses_n10.jsonl` | the 113 Λ clauses, each with an exact rational Farkas certificate |
| `code/regen_cnf.py` | regenerates the CNF from the generators plus the Λ file; `verify.sh` checks it equals the shipped CNF |
| `code/check_lambda_certs.py` | independent exact checker for Λ certificates (rebuilds each row from its tag, checks domains, uses `Fraction` arithmetic) |
| `code/testA_sat.py, e982lib.py, angle_fams.py` | generators (copied unchanged from sprime/sat/) |

SHA-256: CNF `6497bf68…bef`, DRUP `e777f577…5f`, Λ file `ee3b91cb…181`.

## Trusted base (soundness of the clauses)
1. Base encoding (`testA_sat.build`, reviewed earlier): E/LT total preorder on the C(10,2) distances, F1/F2 bisector facts, F2-order (convex quadrilateral), chord monotonicity, four-in-a-class. Both S′ window clauses at every vertex. Generic dihedral lex-leader on the local E literals; every clause family here is D_n-invariant, Λ included.
2. Family F (reviewed by Wonder, `r3_wonder_review_F.txt`): at most two angularly disjoint "wide" triangles at a vertex.
3. **Family Λ (new; Wonder review `push2_w_lambda.txt`: "sound with fixes"; the fixes are in the checker).** Angles are in units of π. Let x[p,k] > 0 be the angle at p between the rays to p+1+k and p+2+k, and A(p;a,b) the sum of the x[p,·] between a and b. The rays from p meet the other vertices in label order inside the interior angle, which is < π. The rows are:
   * x[p,k] > 0, and Σ_k x[p,k] < 1;
   * A(p;a,b) + A(a;p,b) + A(b;p,a) = 1 for every triangle;
   * for chords sharing a vertex u: |uv| = |uw| ⇔ A(v;u,w) = A(w;u,v), and |uv| < |uw| ⇔ A(w;u,v) < A(v;u,w) (Euclid I.5/6, I.18/19).

   A real polygon satisfies every row, with strictness slack t > 0. A Λ clause is the negation of a set C of distance literals whose rows admit a Farkas certificate: either (a) Σy·row = −t with Σy·rhs ≥ 0, or (b) Σy·row = 0 with Σy·rhs > 0. Its multipliers are ≥ 0 on the inequality rows. Hence no strictly convex 10-gon satisfies C.
   Wonder found that the first checker accepted malformed tags (out-of-range vertices aliased by `mod n`), which let an empty core be "certified". The checker now validates every tag explicitly and rejects empty cores. A planted malformed certificate is rejected (`planted_bad.jsonl`).
4. Empirical validation of Λ (rows on the true angles, LP with all true relations, and every learned clause, on random and tie-rich polygons: regular, bi-regular, mirror, dihedral, fan, pushed-regular): n = 10: 10,115 polygons, 0 failures; n = 12: 9,148, 0 failures; n = 13: 9,110, 0 failures. Planted errors were caught: reversed side–angle orientation on 353/353 polygons, and a false clause on 162/351.
   End-to-end control: the false analogue Q ("some vertex has no 3 equidistant others") stays SAT under the same CEGAR at n = 9. The near-exact Danzer C3 9-gon satisfies all Λ rows and all 448 learned Q-clauses.

## How the Λ clauses were found
A CEGAR loop (`push2/cegar.py`) alternates two steps. The SAT step finds a violating pattern. Its isosceles equalities, and the strict comparisons if needed, go into the angle LP (HiGHS). If the LP is infeasible, a deletion-minimal core becomes a clause. Exact certificates are rationalized from the LP duals and verified in `Fraction` arithmetic. The LP is a relaxation of geometry: it is never used to claim realizability, only infeasibility, and every infeasibility is backed by an exact certificate. Typical cores have 3–6 equalities.
Example (n = 8): |31| = |32| makes int(2) a base angle, so int(2) < π/2. But |60| = |62| = |64| puts 0, 2, 4 on a circle about 6, with 1 and 3 between them, so ∠024 = π − ∠064/2 > π/2 while ∠024 ≤ int(2).

## Second, independent n = 10 certificate (`../fc2_10_*`)
This one uses base + MEC selectors B + F, plus 65 certified clauses from Λ, Λ-MEC and Λ-circle. B and Λ-MEC rely on L3, so they hold for S′-violators only. drat-trim: `s VERIFIED`; the checker accepts all 65. It relies on more lemmas than the primary certificate, so treat it as corroboration.

## Consequence for the old n = 10 programme
All 846 minimal violating patterns that survived ABDF+KNGXO are refuted by the equality-only Λ LP. Exact certificates for the 783 mod-p patterns are therefore unnecessary.
