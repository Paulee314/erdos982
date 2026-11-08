#!/usr/bin/env python3
"""Numeric realisation of an equality pattern as a strictly convex polygon with vertices 0..n-1 in CCW order.
realise(n, eqs) -> (P [mpf pairs], Z, per-vertex Z, #equilateral) or None.
Stage 1: scipy least_squares from random convex starts (equalities + hinge penalties forcing every vertex strictly left
of every edge).  Stage 2: Gauss-Newton (SVD pseudo-inverse) on the equalities only, in mpmath at 60 digits, until the
residual is < 1e-45; then strict convexity is re-checked (margin) and the TRUE Z is recomputed with tolerance 1e-30.
This is numeric evidence only; certification is separate (certify_real.py)."""
import math, random, itertools
import numpy as np
from scipy.optimize import least_squares
import mpmath as mp


def _unpack(z, n):
    P = np.zeros((n, 2)); P[1, 0] = 1.0; P[2:, :] = z.reshape(n - 2, 2); return P


def _resid(z, n, eqs, delta, w):
    P = _unpack(z, n)
    D = ((P[:, None, :] - P[None, :, :]) ** 2).sum(-1)
    f = [D[c, u] - D[c, v] for c, u, v in eqs]
    pen = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        for k in range(n):
            if k in (i, (i + 1) % n): continue
            cr = (b[0] - a[0]) * (P[k, 1] - a[1]) - (b[1] - a[1]) * (P[k, 0] - a[0])
            pen.append(w * max(0.0, delta - cr))
    return np.array(f + pen)


def _start(n, rng):
    """random strictly convex polygon, CCW, normalised p0=(0,0), p1=(1,0)"""
    while True:
        k = rng.choice([0, 1, 2])
        if k == 0:
            ang = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
        elif k == 1:     # arc + centre-ish (fan-like)
            span = rng.uniform(0.5, 2.9)
            ang = sorted(rng.uniform(0, span) for _ in range(n))
        else:
            ang = [2 * math.pi * i / n + rng.uniform(-0.3, 0.3) * 2 * math.pi / n for i in range(n)]
        rad = [1 + rng.uniform(-0.3, 0.3) for _ in range(n)]
        P = [(r * math.cos(a), r * math.sin(a)) for r, a in zip(rad, ang)]
        if k == 1:
            P[0] = (0.0, 0.0)
        s = rng.randrange(n); P = P[s:] + P[:s]
        # convex hull check: must be strictly convex in this order
        ok = True
        for i in range(n):
            a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) <= 1e-3: ok = False; break
        if not ok: continue
        # normalise
        (x0, y0), (x1, y1) = P[0], P[1]
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
        Q = []
        for x, y in P:
            X, Y = x - x0, y - y0
            Q.append(((X * dx + Y * dy) / L2, (-X * dy + Y * dx) / L2))
        return np.array(Q[2:]).reshape(-1)


def polish(n, eqs, z, digits=60, iters=60):
    mp.mp.dps = digits
    x = [mp.mpf(float(t)) for t in z]
    m = len(x)
    def F(x):
        P = [(mp.mpf(0), mp.mpf(0)), (mp.mpf(1), mp.mpf(0))] + [(x[2 * i], x[2 * i + 1]) for i in range(n - 2)]
        d = lambda a, b: (P[a][0] - P[b][0]) ** 2 + (P[a][1] - P[b][1]) ** 2
        f = mp.matrix([d(c, u) - d(c, v) for c, u, v in eqs])
        J = mp.matrix(len(eqs), m)
        for r, (c, u, v) in enumerate(eqs):
            def add(i, gx, gy):
                if i >= 2: J[r, 2 * (i - 2)] += gx; J[r, 2 * (i - 2) + 1] += gy
            add(c, 2 * (P[c][0] - P[u][0]) - 2 * (P[c][0] - P[v][0]), 2 * (P[c][1] - P[u][1]) - 2 * (P[c][1] - P[v][1]))
            add(u, -2 * (P[c][0] - P[u][0]), -2 * (P[c][1] - P[u][1]))
            add(v, 2 * (P[c][0] - P[v][0]), 2 * (P[c][1] - P[v][1]))
        return f, J
    res = None
    for _ in range(iters):
        f, J = F(x)
        res = max(abs(t) for t in f) if len(f) else mp.mpf(0)
        if res < mp.mpf(10) ** (-(digits - 12)): break
        # min-norm least-squares step via SVD
        U, S, V = mp.svd_r(J)
        smax = max(S) if len(S) else 1
        dx = [mp.mpf(0)] * m
        for k in range(len(S)):
            if S[k] > smax * mp.mpf(10) ** (-(digits // 3)):
                coef = sum(U[r, k] * f[r] for r in range(len(f))) / S[k]
                for j in range(m): dx[j] -= coef * V[k, j]
        x = [a + b for a, b in zip(x, dx)]
    return x, res


def analyse(P, tol=mp.mpf(10) ** -30):
    n = len(P)
    d = lambda a, b: (P[a][0] - P[b][0]) ** 2 + (P[a][1] - P[b][1]) ** 2
    per = []
    for c in range(n):
        ds = sorted(d(c, v) for v in range(n) if v != c)
        groups = [1]
        for a, b in zip(ds, ds[1:]):
            if abs(b - a) <= tol * max(1, abs(b)): groups[-1] += 1
            else: groups.append(1)
        per.append(sum(g * (g - 1) // 2 for g in groups))
    neq = 0
    for a, b, c in itertools.combinations(range(n), 3):
        x, y, z = d(a, b), d(a, c), d(b, c)
        if abs(x - y) <= tol * x and abs(x - z) <= tol * x: neq += 1
    return sum(per), per, neq


def convex_margin(P):
    n = len(P); mn = None
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        for k in range(n):
            if k in (i, (i + 1) % n): continue
            cr = (b[0] - a[0]) * (P[k][1] - a[1]) - (b[1] - a[1]) * (P[k][0] - a[0])
            mn = cr if mn is None or cr < mn else mn
    return mn


def min_dist(P):
    n = len(P)
    return min((P[a][0] - P[b][0]) ** 2 + (P[a][1] - P[b][1]) ** 2 for a in range(n) for b in range(a + 1, n))


def realise(n, eqs, tries=40, seed=1, delta=0.02, verbose=False):
    rng = random.Random(seed)
    best = None
    for t in range(tries):
        z0 = _start(n, rng)
        dl = [delta, delta / 10, delta / 100, delta / 1000][t % 4]
        try:
            r = least_squares(_resid, z0, args=(n, eqs, dl, 3.0), method='lm', max_nfev=4000, xtol=1e-15, ftol=1e-15)
        except Exception:
            continue
        f = _resid(r.x, n, eqs, dl, 3.0)
        cost = float((f ** 2).sum())
        if cost > 1e-16: continue
        P0 = _unpack(r.x, n)
        if min(((P0[a] - P0[b]) ** 2).sum() for a in range(n) for b in range(a + 1, n)) < 1e-6: continue
        x, res = polish(n, eqs, r.x)
        P = [(mp.mpf(0), mp.mpf(0)), (mp.mpf(1), mp.mpf(0))] + [(x[2 * i], x[2 * i + 1]) for i in range(n - 2)]
        if res is None or res > mp.mpf(10) ** -40: continue
        cm = convex_margin(P)
        if cm < mp.mpf(10) ** -6 or min_dist(P) < mp.mpf(10) ** -8: continue
        Z, per, neq = analyse(P)
        if verbose: print(f'try {t}: Z={Z} margin {float(cm):.3g}')
        if best is None or Z > best[1]: best = (P, Z, per, neq)
        break
    return best
