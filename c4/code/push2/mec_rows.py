#!/usr/bin/env python3
"""Family Lambda-MEC: linear angle rows from the minimum enclosing circle (MEC) Gamma, conditioned on support selectors.
Valid for S'-violators (case (M) of L3: support T has >= 3 vertices, no diametral pair, consecutive support arcs < pi,
all non-support vertices strictly inside Gamma). Angles in units of pi; A(p;a,b) as in angle_lp.
Side convention: for a chord ab, the two open label arcs (a..b) and (b..a) lie strictly on opposite sides of line ab.
  C (concyclic):  a,b,t1,t2 support, t1,t2 on the same side of ab:      A(t1;a,b) - A(t2;a,b) = 0
  I (inside):     v non-support, a,b,t support:  same side:  A(v;a,b) - A(t;a,b) - t >= 0
                                                 opposite:   A(v;a,b) + A(t;a,b) - t >= 1
  R (minor arc):  a,b,t support, no support strictly inside the label arc from a to b that avoids t:
                                                 -A(t;a,b) - t >= -1/2
Each item: (tag, coef dict, rhs, kind, reqs) where reqs = list of (v, bool) support literals the row relies on."""
import itertools
from fractions import Fraction


def on_arc(x, a, b, n):
    """x strictly inside the ccw label arc from a to b"""
    return 0 < (x - a) % n < (b - a) % n


def same_side(x, y, a, b, n):
    return on_arc(x, a, b, n) == on_arc(y, a, b, n)


def items_for(lp, sup):
    """sup: list of bools (support indicator). returns list of items"""
    n = lp.n; T = [v for v in range(n) if sup[v]]; N = [v for v in range(n) if not sup[v]]
    out = []
    def A(p, a, b): return lp.ang(p, a, b)
    for a, b in itertools.combinations(T, 2):
        others = [t for t in T if t not in (a, b)]
        for t1, t2 in itertools.combinations(others, 2):
            if same_side(t1, t2, a, b, n):
                d = dict(A(t1, a, b))
                for k, x in A(t2, a, b).items(): d[k] = d.get(k, 0) - x
                out.append((('C', a, b, t1, t2), d, 0, 'eq', [(a, True), (b, True), (t1, True), (t2, True)]))
        for v in N:
            for t in others:
                d = dict(A(v, a, b))
                if same_side(v, t, a, b, n):
                    for k, x in A(t, a, b).items(): d[k] = d.get(k, 0) - x
                    rhs = 0; side = 's'
                else:
                    for k, x in A(t, a, b).items(): d[k] = d.get(k, 0) + x
                    rhs = 1; side = 'o'
                d[lp.T] = -1
                out.append((('I', v, a, b, t, side), d, rhs, 'ge', [(v, False), (a, True), (b, True), (t, True)]))
        for (x, y) in ((a, b), (b, a)):           # arc from x to y (ccw) with no support strictly inside
            inside = [z for z in range(n) if on_arc(z, x, y, n)]
            if any(sup[z] for z in inside): continue
            for t in others:                      # t is then on the other side
                d = {k: -c for k, c in A(t, x, y).items()}; d[lp.T] = -1
                out.append((('R', x, y, t), d, Fraction(-1, 2), 'ge',
                            [(x, True), (y, True), (t, True)] + [(z, False) for z in inside]))
    return out
