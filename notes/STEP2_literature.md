# #982 step 2: improving the linear bound. Literature map (5 Nov 2026)

## How every published bound works (Szemerédi, Dumitrescu, NPPZ)

- Z(P) = number of isosceles triangles, counted as pairs {(p,a),(p,b)} with |pa| = |pb|; equilateral triangles count 3 times.
- Transfer lemma (NPPZ Lemma 4): Z(P) <= alpha n^2 + O(n) implies some vertex has >= ((2 - alpha)/3) n - O(1) distinct distances.
- Upper bound on Z: Z <= 2 C(n,2) - #good edges. A pair {a,b} is good if its perpendicular bisector contains at most one vertex.
  So #good >= beta n^2 gives f >= ((1 + beta)/3) n.
  - Dumitrescu 2006: beta = 1/12, from the smallest enclosing circle (3 caps) and Cor. 9 (a t-point cap has <= t^2/4 edges with a witness inside). This gives 13/36.
  - NPPZ 2013 (JoCG 4:1-12): beta = 1/11.981, from two cap decompositions that differ (Case 1, uses Lemma 13 at 7/8 n^2) or not (Case 2, Lemma 11). This gives 13/36 + 1/22701.

## Ceiling of the method

- Aggarwal (arXiv 1009.2218, 2010, unrefereed) and NPPZ give convex n-gons with Z >= 3n^2/4 + O(n). So this method can never beat 5n/12 (about 0.4167 n).
- Aggarwal's Conjecture 1 and NPPZ Problem 2: I_conv(n) = max Z over convex n-gons = 3n^2/4 + Theta(n). If this is proved, f >= 5n/12 follows, a big jump from 0.3612.
- Reaching n/2 needs a per-vertex argument. The lossless version of the count is Fishburn's C4:
  sum_p (n - 1 - t(p)) <= C(n,2), where (n - 1 - t(p)) <= Z_p.

## Open sub-problems stated in NPPZ (all improve the constant if solved)

1. Lemma 13 conjecture: edges between the two halves of a 2n-cap with a witness in the cap number <= n^2/2 + O(n). Known: 7/8 n^2. NPPZ say this gives a slight improvement.
2. Problem 3 (1-D limit case): x1 < ... < xn < y1 < ... < yn; count pairs (xi, yj) whose midpoint is some xk or yk. Known <= 7/8 n^2; an arithmetic progression gives about n^2/2.
3. Problem 2: determine I_conv(n).
4. NPPZ say their own constants can be tweaked upward slightly.

No improvement after 2013 was found: searches on 5 Nov 2026, plus the erdosproblems.com 982 page and forum.
