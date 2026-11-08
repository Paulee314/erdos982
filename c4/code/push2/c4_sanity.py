#!/usr/bin/env python3
"""Sanity checks for c4_cegar: for the regular R_n (n odd), bi-regular A_n (n even; Fishburn's construction) and R_n
(n even), compute the exact distance-order pattern (floating point, tolerance 1e-9), then
  (1) sum t = expected;  (2) the SAT encoding with bound = sum t (sym=none) is SAT under the pattern's E/LT literals,
  and with bound = sum t - 1 is UNSAT;  (3) the LP side (Lambda tiers 1-3 with K/P/H, Delta) does NOT refute it.
Also: random strictly convex polygons (all families must accept them).
Usage: c4_sanity.py n [nrandom]"""
import sys, os, math, itertools, random
FAMS = os.environ.get('C4FAMS', 'FGXO')
from c4_cegar import build_c4, Refuter
from pysat.solvers import Cadical153


def regular(n):
    return [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]


def biregular(n):
    """Fishburn's A_{2k}: R_k with diameter 1, plus on each ray from the centre bisecting a side the point whose
    maximum distance to the R_k vertices is 1.  Vertices listed in angular order."""
    k = n // 2
    if k == 2:      # A_4: two equilateral triangles sharing a side
        return [(0, 0), (0.5, -math.sqrt(3) / 2), (1, 0), (0.5, math.sqrt(3) / 2)]
    diam = 2 * math.sin(math.pi * (k // 2) / k)          # diameter of R_k with circumradius 1
    R = 1 / diam
    V = [(R * math.cos(2 * math.pi * j / k), R * math.sin(2 * math.pi * j / k)) for j in range(k)]
    def maxd(rho, phi):
        x, y = rho * math.cos(phi), rho * math.sin(phi)
        return max(math.hypot(x - a, y - b) for a, b in V)
    pts = []
    for j in range(k):
        phi = 2 * math.pi * (j + 0.5) / k
        lo, hi = 0.0, 2.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if maxd(mid, phi) < 1: lo = mid
            else: hi = mid
        pts.append((lo * math.cos(phi), lo * math.sin(phi)))
    out = []
    for j in range(k): out += [V[j], pts[j]]
    return out


def convex_strict(P):
    n = len(P); sg = set()
    for i in range(n):
        a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) < 1e-9: return False
        sg.add(cr > 0)
    # also total turning = 2pi (simple)
    tot = 0
    for i in range(n):
        a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
        a1 = math.atan2(b[1] - a[1], b[0] - a[0]); a2 = math.atan2(c[1] - b[1], c[0] - b[0])
        tot += (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
    return len(sg) == 1 and abs(abs(tot) - 2 * math.pi) < 1e-6


def model_of(enc, P, tol=1e-9):
    D = [math.dist(P[a], P[b]) for (a, b) in enc.pairs]
    m = set(); ass = []
    for i, j in itertools.combinations(range(enc.NP), 2):
        if abs(D[i] - D[j]) < tol: v = enc.E(i, j)
        elif D[i] < D[j]: v = enc.LT(i, j)
        else: v = enc.LT(j, i)
        m.add(v); ass.append(v)
    t = [len({round(math.dist(P[c], P[v]) / tol) for v in range(len(P)) if v != c}) for c in range(len(P))]
    # robust count of classes with tolerance
    t = []
    for c in range(len(P)):
        ds = sorted(math.dist(P[c], P[v]) for v in range(len(P)) if v != c)
        t.append(1 + sum(1 for a, b in zip(ds, ds[1:]) if b - a > tol))
    return m, ass, t


def check(n, P, name, R=None, encs=None):
    assert convex_strict(P), name + ' not strictly convex'
    enc0, cl0, _ = build_c4(n, None, 'none', FAMS)
    m, ass, t = model_of(enc0, P)
    T = sum(t)
    res = {}
    for b in (T, T - 1):
        enc, cl, _ = build_c4(n, b, 'none', FAMS)
        with Cadical153(bootstrap_with=cl) as s: res[b] = s.solve(assumptions=ass)
    if R is None: R = Refuter(enc0)
    tr = R.tiers(m); dc = R.delta_core(m)
    ok = res[T] and not res[T - 1] and tr is None and not dc
    print(f"{name}: t-seq {t} sum {T} (C(n,2)={n*(n-1)//2}); SAT@bound={T}: {res[T]}; SAT@bound={T-1}: {res[T-1]}; "
          f"Lambda refutes: {tr is not None}{' tier '+str(tr[2]) if tr else ''}; Delta refutes: {bool(dc)} -> {'OK' if ok else 'FAIL'}", flush=True)
    return ok


if __name__ == '__main__':
    n = int(sys.argv[1]); nr = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    enc0, _, _ = build_c4(n, None, 'none', FAMS); R = Refuter(enc0)
    allok = True
    if n % 2: allok &= check(n, regular(n), f"R_{n}", R)
    else:
        allok &= check(n, biregular(n), f"A_{n}", R)
        allok &= check(n, regular(n), f"R_{n}", R)
    rnd = random.Random(n)
    for i in range(nr):
        while True:
            ang = sorted(rnd.uniform(0, 2 * math.pi) for _ in range(n))
            rx, ry = rnd.uniform(0.5, 2), rnd.uniform(0.5, 2)
            P = [(rx * math.cos(a), ry * math.sin(a)) for a in ang]
            if convex_strict(P) and min(math.dist(P[i], P[(i + 1) % n]) for i in range(n)) > 1e-3: break
        allok &= check(n, P, f"random#{i}", R)
    # highly non-generic polygons: R_{n+1} - 1 and random n-subsets of R_N (N = n+1 .. 2n), many equal distances
    allok &= check(n, regular(n + 1)[:n], f"R_{n+1}-1", R)
    nsub = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    for i in range(nsub):
        N = rnd.randint(n + 1, 2 * n); idx = sorted(rnd.sample(range(N), n)); Q = regular(N)
        P = [Q[j] for j in idx]
        allok &= check(n, P, f"sub R_{N} {idx}", R)
    print("ALL OK" if allok else "SOME FAILED")
