# Computation C: bounding the isosceles count Z through "kites"

An analysis note, not a computer-verified result. 5–6 Nov 2026.

Write w(ab) ∈ {0, 1, 2} for the number of vertices on the perpendicular bisector of the pair ab (at most 2 in a strictly
convex polygon), so Z = Σ_pairs w(ab) ≤ C(n, 2) + K, where K is the number of pairs with w = 2 ("kites": a, b are
mirror images across a line through two vertices). The published bounds for #982 (Dumitrescu, NPPZ) are exactly bounds
on how many pairs have w ≤ 1; K ≤ n²/4 + O(n) would give Z ≤ 3n²/4 + O(n) and the vertex bound 5n/12, the ceiling of
this method.

`RESULTS_compC.txt` records, with status labels:

- **Proved (checked by the agent):** four lemmas (mirror pairs across a vertex-line are bounded by the smaller side;
  the kites with a given apex number at most ⌊(n−2)²/4⌋; kites cross and polygon edges are never kites; a
  non-collinear triple lies in at most one distance class) and **Theorem A′**: if all but k vertices lie on one circle,
  K ≤ n²/4 + O(kn), hence Z ≤ 3n²/4 + O(kn). This covers fans, near-fans, subsets of regular N-gons with or without the
  centre, and the H2 counterexample below.
- **Proved modulo a cited theorem** (Raz–Sharir–de Zeeuw 2016 / Elekes–Szabó; the non-speciality step is a sketch):
  **Theorem B**, the same bound up to o(n²) when all but k = o(n) vertices lie on O(1) concentric circles.
- **Refuted** (explicit counterexamples, checked exactly): the per-vertex kite-degree conjecture H2
  (`H2_refutation.txt`, `harness.py`: a centre plus regular-N-gon points at c ± 2^k gives kite degree n − 4), and
  several further proposed lemmas.
- **Numerics** (`scan1.py`, `tworing.py`, `tworing.out`): over subsets of regular N-gons (N ≤ 30, n ≤ 11) the maximum
  K for n = 5..11 is 3, 6, 8, 12, 14, 20, 22, all below n²/4, and the maximum Z reproduces the I_conv values 12, 20,
  29, 38, 50, 64, 77 (see `../iconv`); two interleaved concentric regular m-gons give K = n(n−2)/4 exactly.
- **Open:** a general bound K ≤ βn² with β < 0.4165 (the NPPZ constant) was not reached. The note ends with the
  decomposition the authors think most promising.

refutations and the write-up were assembled.

AI use: the lemmas and their proofs were proposed by two AI models and checked by a third acting as the agent; the
counterexample search code and the numerics were written and run by AI tools under my direction; none of this has had
a human referee. This note was drafted by an AI tool and edited by me.

The raw model transcripts behind RESULTS_compC.txt are kept privately; every claim in that file is labelled proved / model claim (unchecked) / refuted on its own evidence.
