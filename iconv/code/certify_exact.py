#!/usr/bin/env python3
"""Exact certification of a polygon with coordinates in a real number field (sympy, exact arithmetic).
Computes all squared distances exactly (expanded radical expressions; equality = expanded difference is 0, decided
with sympy minimal_polynomial when not syntactically 0), Z, #equilateral, T = Z - 2 #eq, and strict convexity (every
vertex strictly left of every directed edge: sign of an exact algebraic number)."""
import itertools, sympy as sp

def is_zero(x):
    x = sp.expand(x)
    if x == 0: return True
    return sp.minimal_polynomial(x, sp.Symbol('t')) == sp.Symbol('t')

def certify(P):
    n = len(P)
    D = {(a, b): sp.expand((P[a][0] - P[b][0])**2 + (P[a][1] - P[b][1])**2) for a in range(n) for b in range(n) if a != b}
    per = []
    for c in range(n):
        o = [v for v in range(n) if v != c]; z = 0
        for u, v in itertools.combinations(o, 2):
            if is_zero(D[c, u] - D[c, v]): z += 1
        per.append(z)
    eq = sum(1 for a, b, c in itertools.combinations(range(n), 3) if is_zero(D[a, b] - D[a, c]) and is_zero(D[a, b] - D[b, c]))
    conv = True
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        for k in range(n):
            if k in (i, (i + 1) % n): continue
            cr = sp.expand((b[0] - a[0]) * (P[k][1] - a[1]) - (b[1] - a[1]) * (P[k][0] - a[0]))
            if not (cr.is_positive is True): conv = False
    distinct = all(not is_zero(D[a, b]) for a in range(n) for b in range(a + 1, n))
    return sum(per), per, eq, conv, distinct

if __name__ == '__main__':
    s = sp.sqrt(7); R = sp.Rational
    P = [(0, 0), (1, 0), ((3 + s) / 4, (1 + s) / 4), ((3 + s) / 4, (5 + s) / 4), (R(1, 2), (2 + s) / 2),
         (-R(1, 2), (2 + s) / 2), (-(1 + s) / 4, (3 + s) / 4), (-(1 + s) / 4, (s - 1) / 4)]
    Z, per, eq, conv, distinct = certify(P)
    print(f'octagon Q(sqrt7): Z={Z} per={per} equilateral={eq} T={Z - 2 * eq} strictly_convex={conv} distinct={distinct}')
