# Two-ring polygons, local symmetry, and a hand proof for n = 12

*2 November 2026. Status: proofs written out below. Each was checked by an independent AI reviewer, and the key steps
were checked numerically and symbolically. They have not been refereed. AI use: the proofs were found with Claude Fable
5.1 and checked with Gemini Argon and Claude; see "Provenance" at the end.*

**Notation.**
- **Polygons and distances.** P = P_0 … P_{N−1} is a strictly convex polygon, labelled counterclockwise, indices mod N.
  For a vertex p, Z_p is the number of unordered pairs {u, w} of other vertices with |pu| = |pw|, that is, the
  number of isosceles triangles with apex p.
- **Bi-regular 2m-gon** with ratio t > 0: the polygon
  A_k = e^{2πik/m}, B_k = t·e^{(2k+1)πi/m} (k = 0, …, m−1), up to similarity. It is strictly convex exactly when
  C < t < 1/C, where C = cos(π/m).
- **Locally symmetric:** |P_vP_{v+j}| = |P_vP_{v−j}| for all v and j.

## 1. Accidental coincidences in two-ring polygons

Let γ = π/m and E_{a,b}(t) = t² − 2t cos((2b+1)γ) + 1 − 4 sin²(aγ), for 1 ≤ a ≤ ⌊m/2⌋ and 0 ≤ b ≤ m − 1.
- At A_0, the squared distances to the other A's are 4 sin²(aγ), and those to the B's are t² − 2t cos((2b+1)γ) + 1.
- So an A–B distance coincidence at A_0 means E_{a,b}(t) = 0.
- After rescaling, a coincidence at B_0 means E_{a',b'}(1/t) = 0.
- Two A–A distances, or two A–B distances, never coincide except by the polygon's own symmetry.

**Theorem 1.** For t in the convex range (C, 1/C), an A–B coincidence at A_0 occurs for exactly one value of t:
- if m is even, t_1 = √(C² + 3) − C, which lies in (1, 1/C) (with a = m/2 and 2b + 1 = m ± 1);
- if m is odd, t_0 = 2cos(γ/2) − 1, which lies in (C, 1) (with a = b = (m − 1)/2).

A coincidence at B_0 occurs only at the reciprocal value. Since t_1 and t_0 differ from 1, **no strictly convex two-ring
polygon has accidental coincidences at both its outer and its inner vertices.** In particular, two-ring polygons never
violate Conjecture T: some vertex is the apex of at most ⌊(n−1)/2⌋ isosceles triangles.

*Proof.*

*Setup.* Put φ = 2aγ ∈ [2γ, π], an even multiple of γ. Put θ = min((2b+1)γ, 2π − (2b+1)γ) ∈ [γ, π], an odd multiple
of γ with cos θ = cos((2b+1)γ). Then E = g_θ(t) − (2 − 2cos φ), where g_θ(t) = t² − 2t cos θ + 1.

*Lemma 1.* g_θ is strictly increasing on [C, ∞), because g′ = 2(t − cos θ) ≥ 2(t − C).

*Lemma 2.* E(1) = 2cos φ − 2cos θ ≠ 0, because φ ≠ θ: one is an even and the other an odd multiple of γ.

*Proposition A (t ∈ (1, 1/C)).*
- By Lemma 1, g_θ(1) < g_θ(t) < g_θ(1/C).
- The left inequality gives φ > θ, so φ ≥ θ + γ by parity.
- The right inequality, multiplied by C², gives 2C(cos θ − C cos φ) < sin²γ.
- From cos φ ≤ cos(θ + γ) we get cos θ − C cos φ ≥ sin γ · sin(θ + γ). Hence 2 cos γ · sin(θ + γ) < sin γ.
- If θ + γ < π, then θ + γ ∈ [2γ, π − γ], so sin(θ + γ) ≥ sin γ. This would give 2 cos γ < 1, which is impossible for
  m ≥ 3.
- So θ + γ = π, which forces φ = π (m even, a = m/2) and 2b + 1 = m ± 1.
- Then E = t² + 2Ct − 3, whose positive root is t_1.

*Proposition B (t ∈ (C, 1)).*
- By Lemma 1, g_θ(C) < g_θ(t) < g_θ(1).
- The right inequality gives φ < θ, so φ ≤ θ − γ and θ ≥ 3γ.
- The left inequality gives 2(cos φ − C cos θ) < sin²γ.
- **Case θ = π.** Then m is odd and b = (m−1)/2, and E = 0 means t = 2 sin(aγ) − 1. The condition t > C holds only for
  a = (m−1)/2, giving t_0. For smaller a, sin(aγ) ≤ cos(3γ/2) < cos²(γ/2).
- **Case θ < π.** Then cos φ ≥ cos(θ − γ), so cos φ − C cos θ ≥ sin γ · sin θ, which gives sin θ < ½ sin γ. This
  contradicts sin θ ≥ sin γ on [γ, π − γ].

*Assembly.* Within (C, 1/C), the set of t with a coincidence at A_0 is a single point t* ≠ 1. The map t ↦ 1/t maps
(C, 1/C) to itself. So coincidences at both A_0 and B_0 at the same t would force t = t* = 1/t*, that is, t* = 1,
which is impossible. ∎

*Remark.* Convexity is essential. Outside the convex range common roots do exist: for m = 4, t = (√6 + √2)/2, and
for m = 5, t = (3 + √5)/2.

## 2. Locally symmetric convex polygons

**Theorem 2 (rigidity).** A strictly convex, locally symmetric polygon is regular if N is odd, and two-ring
(bi-regular) if N is even.

*Lemma A.* Let P be a strictly convex 2m-gon, m ≥ 3, with all sides equal and with its even vertices forming a
regular m-gon Q_k = β^{2k}, where β = e^{iπ/m}. Then P is bi-regular.

*Proof.*
- O_k = P_{2k+1} is equidistant from Q_k and Q_{k+1}, so O_k = τ_k β^{2k+1} for some real τ_k.
- The common side length s satisfies s² = τ_k² − 2Cτ_k + 1.
- The diagonal Q_kQ_{k+1} separates O_k from the other even vertices, so τ_k > C.
- The two roots of τ² − 2Cτ + (1 − s²) = 0 sum to 2C, so at most one of them exceeds C.
- Hence all τ_k are equal. ∎

*Lemma B.* Let m = 2p ≥ 4 and Q_k = r_k β^{2k}, with r_k = R for k even and r_k = ρ for k odd. If a point O satisfies
|OQ_{−i}| = |OQ_{1+i}| for i = 0, 1, 2 (only i = 0, 1 when m = 4), then R = ρ.

*Proof.*
- Write O = β(x + iy), θ_i = (2i+1)π/m and ε_i = (−1)^i.
- The three equalities become 2x ε_i (R − ρ) cos θ_i − 2y (R + ρ) sin θ_i = ε_i (R − ρ)(R + ρ).
- Suppose R ≠ ρ. Put X = 2x/(R + ρ) and Y = 2y/(R − ρ). Then the equalities say that the point (X, Y) lies on the
  tangent lines to the unit circle at the three distinct angles −ε_i θ_i.
- A point lies on at most two tangent lines of a circle. For m = 4 the two tangent lines are parallel and distinct.
- Either way this is a contradiction, so R = ρ. ∎

*Proof of Theorem 2.*

(a) N odd.
- Local symmetry with gaps 1 and 2, chained around the polygon (this works because gcd(2, N) = 1), makes all sides
  equal and all gap-2 chords equal.
- So the triangles P_{k−1}P_kP_{k+1} are congruent, and all interior angles are equal.
- Hence P is regular.

(b) N = 2m, by induction on N.
- For N = 4, P is a rhombus, which is bi-regular.
- For m ≥ 3, the even sub-polygon Q = (P_0, P_2, …) is strictly convex and locally symmetric.
  - If m is odd, Q is regular by (a).
  - If m is even, Q is bi-regular by induction. The local symmetry of P at P_1, for gaps 1, 3 and 5, is exactly the
    hypothesis of Lemma B, so Q is regular.
- Lemma A then makes P bi-regular. ∎

The proof uses only the following hypotheses:
- local symmetry at the even vertices for even gaps;
- all sides equal;
- |P_1P_{1+j}| = |P_1P_{1−j}| for j = 3 and 5 (only j = 3 when m = 4).

**Corollary 3.** No strictly convex polygon realizes a *merged two-ring pattern*: a locally symmetric equal-distance
pattern with at most ⌊n/2⌋ − 1 classes at every vertex.

*Proof.*
- For odd n, Theorem 2 makes P regular, and a regular polygon has exactly ⌊n/2⌋ distinct distances at every vertex.
- For even n, P is a two-ring polygon in the convex range, and every vertex has exactly m distances unless an
  accidental coincidence occurs.
- Getting m − 1 classes at every vertex needs coincidences at both parities, which Theorem 1 forbids. ∎

Of the 35 "fakes" that our convexity clauses cannot exclude (n = 12, 14, 16, 18), 31 are locally symmetric. All of
those are therefore excluded by Corollary 3, uniformly in n. The remaining 4 (n = 18, with rotational symmetry only) are
excluded individually by Gröbner certificates.

## 3. A hand proof for the n = 12 survivor

The certified search for n = 12 leaves exactly one equal-distance pattern ("pattern B"; see `n12/algebra/structure.txt`).
It is excluded by Corollary 3. It also has the following direct three-step proof, which does not use Theorem 1.

The proof uses four facts, all read off the pattern:
- (F1) the triangle P_0P_4P_8 is equilateral;
- (F2) the even gap-2 chords are all equal, to g say;
- (F3) |P_1P_0| = |P_1P_2|, |P_1P_4| = |P_1P_10| and |P_1P_6| = |P_1P_8|;
- (F4) |P_1P_4| = g.

Write Q_k = P_{2k} and ω = e^{iπ/3}.

1. **The even hexagon has alternating radii.**
   - Place Q_0 = R, Q_2 = Rω² and Q_4 = Rω⁴.
   - Q_1 is equidistant from Q_0 and Q_2, so Q_1 = ρ_1ω.
   - Convexity puts Q_1 beyond the chord Q_0Q_2, so ρ_1 > R/2.
   - Then g² = ρ_1² − Rρ_1 + R², and this expression is strictly increasing in ρ_1 there. The same holds for Q_3 and Q_5,
     so ρ_1 = ρ_3 = ρ_5 =: ρ.
2. **R = ρ.**
   - Write O = P_1. The three equalities of (F3) are linear in the coordinates (x, y) of O.
   - Eliminating x and y leaves 3(R − ρ)(R + ρ) = 0.
3. **Contradiction.**
   - Now Q is a regular hexagon of side R, and Q_2, Q_5 are antipodal at distance 2R.
   - By (F3) and (F4), |OQ_2| = |OQ_5| = R, so O is the midpoint of Q_2Q_5, which is the hexagon's centre.
   - The centre is an interior point of the polygon, contradicting strict convexity. ∎

So the n ≤ 13 result has a fully human-readable final step: every pattern other than B is excluded by the certified SAT
search, and B by this argument. The Gröbner certificate for B remains in the repository as an independent check.

## 4. Related work

- **Aggarwal**, *On isosceles triangles and related problems in a convex polygon* (arXiv:1009.2218, 2010).
  - Shows that if no vertex is equidistant from three others, every vertex is the apex of at most ⌊(n−1)/2⌋ isosceles
    triangles.
  - Conjectures that a convex n-gon has at most 3n²/4 + O(n) isosceles triangles.
  - Shows that this conjecture would give 5n/12 + o(n) distinct distances at some vertex.

  Our Conjecture T asks for the apex bound at *some* vertex without the no-three-equidistant hypothesis. Section 1
  verifies it for all two-ring polygons.
- **Theorem 2.** I did not find it stated in the literature, but it may well be classical. Pointers are welcome.

## Provenance

- **Theorem 1.**
  - Proof: Claude Fable 5.1, via the Anthropic API.
  - Review: Gemini Argon, verdict sound.
  - Numerical check: the coincidence set equals {t_1} or {t_0} for every m ≤ 200.
- **Theorem 2, Corollary 3 and Section 3.**
  - Proofs: Claude Fable 5.1, at maximum reasoning effort.
  - Review: Gemini Argon, verdict sound with no errors.
  - Independent checks by Claude:
    - a symbolic check of the elimination in Step 2;
    - a numerical check of Lemma B for m = 4, …, 12;
    - a check of the 35 fakes for local symmetry.
- The arguments were directed and assembled by Paul Lee, who takes responsibility for this note.
