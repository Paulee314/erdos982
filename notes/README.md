# Literature and analysis notes (5 Nov 2026)

- `STEP2_literature.md`: how every published linear bound for #982 works (Szemerédi's transfer argument as stated by
  NPPZ, Dumitrescu 2006, NPPZ 2013), why the method cannot beat 5n/12 (Aggarwal's and NPPZ's constructions with
  Z ≥ 3n²/4 + O(n)), and the open sub-problems NPPZ state. Kominers' July 2026 forum post (bound
  (13/36 + 3/5270)n − O(1)) is not analysed there; it is cited in the main README as a claim that has not been checked
  here.
- `PROBLEM3_REPORT.md`: NPPZ's Problem 3, the one-dimensional midpoint ("cap") problem. Finding: NPPZ's n²/2 conjecture
  is false and this was already in print: Lev–Pinchasi (Acta Arith. 163 (2014); arXiv 1211.6567) prove the truth is
  (3/5)n² + O(n) and show it is sharp. Exact small values B(n) = ⌊3n²/5⌋ for n ≤ 5 by computer (CEGAR with certified
  infeasible cores), 21 ≤ B(6) ≤ 24, constructions attaining ⌊3n²/5⌋ for n ≤ 30, and what a 3/5 cap lemma would be
  worth for #982 (an improvement of the NPPZ constant of order 1/7000, so the bottleneck is elsewhere).
- `prob3_bundle.tgz` (185 KB): the scripts (`src/`), logs, `Bpq.json` and the 132 certified infeasible cores behind
  `PROBLEM3_REPORT.md`.

AI use: the literature search, the reading of the sources and both notes were done by AI tools under my direction; the
Problem 3 computations were written and run by an AI agent. This note was drafted
by an AI tool and edited by me.
