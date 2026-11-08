"""Exact rational Phase-1 simplex (Bland's rule): find y >= 0 with A y = b (A, b rational). Returns list or None.
Dense tableau over Fractions; meant for small systems (a few hundred rows/cols)."""
from fractions import Fraction


def feasible(A, b, max_pivots=20000):
    m = len(A); n = len(A[0]) if m else 0
    # make b >= 0
    T = []
    for i in range(m):
        row = [Fraction(x) for x in A[i]]; bi = Fraction(b[i])
        if bi < 0: row = [-x for x in row]; bi = -bi
        T.append(row + [Fraction(1) if j == i else Fraction(0) for j in range(m)] + [bi])
    N = n + m
    basis = [n + i for i in range(m)]
    # objective: minimize sum of artificials -> reduced costs
    obj = [Fraction(0)] * (N + 1)
    for i in range(m):
        for j in range(N + 1): obj[j] -= T[i][j]
    for j in range(n, N): obj[j] += 1          # artificial cost 1 cancels
    for it in range(max_pivots):
        # entering: Bland -> smallest index with negative reduced cost
        e = next((j for j in range(N) if obj[j] < 0), None)
        if e is None: break
        # ratio test
        best = None
        for i in range(m):
            if T[i][e] > 0:
                r = T[i][N] / T[i][e]
                if best is None or r < best[0] or (r == best[0] and basis[i] < basis[best[1]]): best = (r, i)
        if best is None: return None            # unbounded (cannot happen in phase 1)
        p = best[1]; pv = T[p][e]
        T[p] = [x / pv for x in T[p]]
        for i in range(m):
            if i != p and T[i][e] != 0:
                f = T[i][e]; Ti = T[i]; Tp = T[p]
                T[i] = [Ti[j] - f * Tp[j] for j in range(N + 1)]
        if obj[e] != 0:
            f = obj[e]; obj = [obj[j] - f * T[p][j] for j in range(N + 1)]
        basis[p] = e
    else:
        return None
    if -obj[N] != 0: return None               # artificials not driven to zero -> infeasible
    y = [Fraction(0)] * n
    for i in range(m):
        if basis[i] < n: y[basis[i]] = T[i][N]
    return y
