#!/usr/bin/env python3
"""Geometry helpers for I_conv(n): Z(P) = sum_p sum_{classes at p} C(m,2) (apex-weighted isosceles count; an
equilateral triangle counts 3 times), T(P) = number of isosceles triangles as vertex sets (= Z - 2 * #equilateral),
strict convexity check, and exact Z for subsets of a regular N-gon plus optionally its centre."""
import itertools, math
from collections import Counter


def d2(p, q): return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def classes(P, tol=1e-9):
    """per centre: list of classes (lists of vertex indices) with relative tolerance tol"""
    n = len(P); out = []
    for c in range(n):
        ds = sorted(((d2(P[c], P[v]), v) for v in range(n) if v != c))
        cl = [[ds[0][1]]]; last = ds[0][0]
        for d, v in ds[1:]:
            if abs(d - last) <= tol * max(1.0, abs(d)): cl[-1].append(v)
            else: cl.append([v])
            last = d
        out.append(cl)
    return out


def Zof(P, tol=1e-9):
    cl = classes(P, tol)
    per = [sum(len(k) * (len(k) - 1) // 2 for k in c) for c in cl]
    return sum(per), per


def equilaterals(P, tol=1e-9):
    n = len(P); cnt = 0
    for a, b, c in itertools.combinations(range(n), 3):
        x, y, z = d2(P[a], P[b]), d2(P[a], P[c]), d2(P[b], P[c])
        m = max(x, y, z)
        if abs(x - y) <= tol * m and abs(x - z) <= tol * m: cnt += 1
    return cnt


def strictly_convex(P, margin=1e-9):
    """P in cyclic order; True iff every consecutive triple turns the same way strictly and total turning = 2pi"""
    n = len(P); s = []
    for i in range(n):
        a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
        s.append((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]))
    if not (all(x > margin for x in s) or all(x < -margin for x in s)): return False
    tot = 0.0
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]; c = P[(i + 2) % n]
        a1 = math.atan2(b[1] - a[1], b[0] - a[0]); a2 = math.atan2(c[1] - b[1], c[0] - b[0])
        d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi; tot += d
    return abs(abs(tot) - 2 * math.pi) < 1e-6


def regular(n, R=1.0, start=0.0):
    return [(R * math.cos(start + 2 * math.pi * k / n), R * math.sin(start + 2 * math.pi * k / n)) for k in range(n)]


def fan(n, theta):
    """Aggarwal: centre v plus n-1 points on a circle around v with equal angular step theta (radians)"""
    m = n - 1; span = (m - 1) * theta
    pts = [(math.cos(-span / 2 + k * theta), math.sin(-span / 2 + k * theta)) for k in range(m)]
    return [(0.0, 0.0)] + pts


def aggarwal_formula(n): return (3 * n * n - 11 * n + 8 + 2 * (n // 2)) // 4


def regular_Z(n): return n * ((n - 1) // 2)


# ---------- exact Z for subsets of a regular N-gon (+ centre) ----------
def subset_Z(N, S, centre=False):
    """S: sorted list of residues mod N; chord class of a pair = min(d, N-d); radius = chord iff d = N/6.
    Returns (Z, per-vertex list, #equilateral) exactly (integer arithmetic).  Centre is vertex index len(S) if used."""
    def cls(d):
        d %= N; d = min(d, N - d)
        return ('R',) if (6 * d == N) else ('c', d)
    per = []
    for a in S:
        cnt = Counter(cls(b - a) for b in S if b != a)
        if centre: cnt[('R',)] += 1
        per.append(sum(m * (m - 1) // 2 for m in cnt.values()))
    if centre: per.append(len(S) * (len(S) - 1) // 2)
    eq = 0
    pts = list(S)
    for a, b, c in itertools.combinations(pts, 3):
        if cls(b - a) == cls(c - a) == cls(c - b): eq += 1
    if centre:
        for a, b in itertools.combinations(pts, 2):
            if cls(b - a) == ('R',): eq += 1
    return sum(per), per, eq


def subset_points(N, S, centre=False):
    P = [(math.cos(2 * math.pi * s / N), math.sin(2 * math.pi * s / N)) for s in S]
    if centre: P = P + [(0.0, 0.0)]
    return P
