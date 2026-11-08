#!/usr/bin/env python3
"""Pure-Python Levenberg-Marquardt for the equidistance equations of a pattern (no numpy: the Mac venv has none).
solve(n, eqs, restarts, seed) -> list of (residual, points) for the converged restarts, points with v0=(0,0), v1=(1,0).
coincident_pairs(n, eqs) -> pairs (i,j) that coincide (distance < tol) in some near-exact solution (residual < 1e-16)."""
import random, math


def _residual_jac(n, eqs, z):
    P = [(0j, 0j), (1 + 0j, 0j)] + [(z[2 * i], z[2 * i + 1]) for i in range(n - 2)]
    f = []; J = []
    for c, u, v in eqs:
        (cx, cy), (ux, uy), (vx, vy) = P[c], P[u], P[v]
        f.append((cx - ux) ** 2 + (cy - uy) ** 2 - (cx - vx) ** 2 - (cy - vy) ** 2)
        row = [0j] * (2 * n - 4)
        def add(i, dx, dy):
            if i >= 2: row[2 * (i - 2)] += dx; row[2 * (i - 2) + 1] += dy
        add(c, 2 * (cx - ux) - 2 * (cx - vx), 2 * (cy - uy) - 2 * (cy - vy))
        add(u, -2 * (cx - ux), -2 * (cy - uy))
        add(v, 2 * (cx - vx), 2 * (cy - vy))
        J.append(row)
    return f, J


def _solve_spd(A, b):
    m = len(A); A = [row[:] for row in A]; b = b[:]
    for i in range(m):
        p = i
        for r in range(i + 1, m):
            if abs(A[r][i]) > abs(A[p][i]): p = r
        A[i], A[p] = A[p], A[i]; b[i], b[p] = b[p], b[i]
        if abs(A[i][i]) < 1e-300: return None
        for r in range(i + 1, m):
            t = A[r][i] / A[i][i]
            if t:
                for cidx in range(i, m): A[r][cidx] -= t * A[i][cidx]
                b[r] -= t * b[i]
    x = [0j] * m
    for i in range(m - 1, -1, -1):
        s = b[i] - sum(A[i][j] * x[j] for j in range(i + 1, m)); x[i] = s / A[i][i]
    return x


def lm(n, eqs, z, iters=200):
    lam = 1e-3
    f, J = _residual_jac(n, eqs, z); cost = sum(abs(t) ** 2 for t in f)
    m = len(z)
    for _ in range(iters):
        JtJ = [[sum(J[r][i].conjugate() * J[r][j] for r in range(len(J))) for j in range(m)] for i in range(m)]
        Jtf = [sum(J[r][i].conjugate() * f[r] for r in range(len(J))) for i in range(m)]
        for i in range(m): JtJ[i][i] += lam * (1 + abs(JtJ[i][i]))
        d = _solve_spd(JtJ, [-t for t in Jtf])
        if d is None: lam *= 10; continue
        z2 = [a + b for a, b in zip(z, d)]
        f2, J2 = _residual_jac(n, eqs, z2); cost2 = sum(abs(t) ** 2 for t in f2)
        if cost2 < cost:
            z, f, J, cost = z2, f2, J2, cost2; lam = max(lam / 3, 1e-12)
            if cost < 1e-28: break
        else:
            lam *= 4
            if lam > 1e12: break
    return cost, z


def solve(n, eqs, restarts=20, seed=0):
    rng = random.Random(seed); out = []
    for _ in range(restarts):
        z = [complex(rng.uniform(-2, 2), rng.uniform(-1, 1) if _ % 2 else 0.0) for _ in range(2 * n - 4)]
        cost, z = lm(n, eqs, z)
        out.append((cost, z))
    out.sort(key=lambda t: t[0])
    return out


def coincident_pairs(n, eqs, restarts=20, tol=1e-5, seed=0):
    pairs = {}
    for cost, z in solve(n, eqs, restarts, seed):
        if cost > 1e-16: continue
        P = [(0j, 0j), (1 + 0j, 0j)] + [(z[2 * i], z[2 * i + 1]) for i in range(n - 2)]
        for i in range(n):
            for j in range(i + 1, n):
                if abs((P[i][0] - P[j][0]) ** 2 + (P[i][1] - P[j][1]) ** 2) < tol:   # coincident or on the null cone
                    pairs[(i, j)] = pairs.get((i, j), 0) + 1
    return sorted(pairs, key=lambda p: -pairs[p])


if __name__ == '__main__':
    import sys, time
    n = int(sys.argv[1])
    for line in sys.stdin:
        line = line.split('|')[0].strip()
        if len(line.split()) != n: continue
        parts = line.split(); eqs = []
        for c in range(n):
            others = [v for v in range(n) if v != c]; lab = dict(zip(others, parts[c])); groups = {}
            for v in others: groups.setdefault(lab[v], []).append(v)
            for g in groups.values():
                for v in g[1:]: eqs.append((c, g[0], v))
        t = time.time(); sols = solve(n, eqs)
        print(f'{line} | best cost {sols[0][0]:.2e}; coincident {coincident_pairs(n, eqs)}; {time.time()-t:.1f}s')
