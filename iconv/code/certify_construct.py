#!/usr/bin/env python3
"""Certified Z for 'regular-subset + centre' constructions: points e^{2 pi i s/N} (s in S, S inside an open half-circle)
plus the centre O = 0.  Equalities are exact identities: |e^{ia}-e^{ib}|^2 = 2-2cos(a-b) depends only on
d = min(|s-t| mod N, N-|s-t| mod N), and equals |O e^{ia}|^2 = 1 iff 2 pi d/N = pi/3 (d = N/6).  For 0 <= d <= N/2 the
chord 2 sin(pi d/N) is strictly increasing, so different d give different distances.  Hence Z is the integer count
subset_Z (geom.py).  This script re-derives Z INDEPENDENTLY with mpmath interval arithmetic: all squared distances as
intervals (60 digits); two distances are declared equal only if they are equal by the identity above (same d, or
radius/N/6-chord), and every other pair of distances at a common centre must have DISJOINT intervals (certified
inequality).  Strict convexity: every vertex strictly left of every directed edge, certified by interval sign.
usage: certify_construct.py N s1 s2 ... [--nocentre]"""
import sys, itertools
from mpmath import iv, mp
iv.dps = 60


def certify(N, S, centre=True):
    S = sorted(S)
    pts = [(iv.cos(2 * iv.pi * s / N), iv.sin(2 * iv.pi * s / N)) for s in S]
    key = [('s', s) for s in S]
    if centre:
        pts.append((iv.mpf(0), iv.mpf(0))); key.append(('O',))
    n = len(pts)

    def cls(a, b):     # exact class label of the distance between vertices a and b
        ka, kb = key[a], key[b]
        if ka[0] == 'O' or kb[0] == 'O': return ('R',)
        d = (ka[1] - kb[1]) % N; d = min(d, N - d)
        return ('R',) if 6 * d == N else ('c', d)

    D = [[(pts[a][0] - pts[b][0]) ** 2 + (pts[a][1] - pts[b][1]) ** 2 for b in range(n)] for a in range(n)]
    Z = 0; per = []
    for c in range(n):
        others = [v for v in range(n) if v != c]
        z = 0
        for u, v in itertools.combinations(others, 2):
            if cls(c, u) == cls(c, v):
                z += 1
                # identity check (sanity): intervals must overlap
                assert D[c][u].a <= D[c][v].b and D[c][v].a <= D[c][u].b
            else:
                # certified inequality: disjoint intervals
                if not (D[c][u].b < D[c][v].a or D[c][v].b < D[c][u].a):
                    raise AssertionError(f'cannot separate |{c}{u}| and |{c}{v}|')
        per.append(z); Z += z
    # strict convexity: cyclic order = S increasing, then centre (S within an open half circle)
    assert S[-1] - S[0] < N / 2 if centre else True
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for k in range(n):
            if k in (i, (i + 1) % n): continue
            cr = (b[0] - a[0]) * (pts[k][1] - a[1]) - (b[1] - a[1]) * (pts[k][0] - a[0])
            if not cr.a > 0: raise AssertionError(f'convexity not certified at edge {i}, vertex {k}')
    eq = 0
    for a, b, c in itertools.combinations(range(n), 3):
        if cls(a, b) == cls(a, c) == cls(b, c): eq += 1
    return Z, per, eq


if __name__ == '__main__':
    N = int(sys.argv[1]); S = [int(x) for x in sys.argv[2:] if not x.startswith('--')]
    Z, per, eq = certify(N, S, '--nocentre' not in sys.argv)
    print(f'N={N} S={S} centre={"--nocentre" not in sys.argv}: n={len(per)} Z={Z} per={per} equilateral={eq} '
          f'T_sets={Z - 2 * eq}  CERTIFIED (exact identities + interval separation + interval convexity)')
