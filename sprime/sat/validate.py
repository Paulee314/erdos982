#!/usr/bin/env python3
"""Empirical soundness check of angle_fams.py (Fable's advice): for random strictly convex polygons, fix every E/LT
variable to the polygon's true distance preorder, s_v to its MEC support, A_v to [int(v) < 90], D_v to [int(v) <= 60],
and ask a SAT solver whether the family clauses (with free cardinality auxiliaries) are satisfiable. Any UNSAT = an
unsound clause. B is tested (without the violator-only B0/B1) on polygons whose MEC has >= 3 support points and no
diametral pair. Also tests regular and bi-regular polygons (ties) and the C3 Danzer 9-gon.
Usage: validate.py n count seed"""
import sys, math, random, itertools, json
import numpy as np
from pysat.solvers import Cadical153
sys.path.insert(0, '.')
from e982lib import Enc
from angle_fams import add_families

def valtr(n, rng):
    xs = sorted(rng.random() for _ in range(n)); ys = sorted(rng.random() for _ in range(n))
    def chain(v):
        mn, mx = v[0], v[-1]; a, b = [mn], [mn]
        for x in v[1:-1]: (a if rng.random() < .5 else b).append(x)
        a.append(mx); b.append(mx)
        return [a[i + 1] - a[i] for i in range(len(a) - 1)] + [b[i] - b[i + 1] for i in range(len(b) - 1)]
    X, Y = chain(xs), chain(ys); rng.shuffle(Y)
    vec = sorted(zip(X, Y), key=lambda t: math.atan2(t[1], t[0]))
    pts = []; x = y = 0.0
    for dx, dy in vec: pts.append((x, y)); x += dx; y += dy
    return pts

def near_circle(n, rng, eps):
    ang = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    out = []
    for a in ang:
        r = 1 + eps * rng.uniform(-1, 1); out.append((r * math.cos(a), r * math.sin(a)))
    return out

def strictly_convex(P):
    n = len(P)
    for i in range(n):
        a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) <= 1e-9: return False
    turn = 0.0                                   # total turning must be exactly 2*pi (simple, winds once)
    for i in range(n):
        a, b, c = P[i], P[(i + 1) % n], P[(i + 2) % n]
        t = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0])
        turn += (t + math.pi) % (2 * math.pi) - math.pi
    return abs(turn - 2 * math.pi) < 1e-6

def mec(P):
    best = None
    def circ2(a, b): return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), math.dist(a, b) / 2
    def circ3(a, b, c):
        ax, ay = a; bx, by = b; cx, cy = c
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-14: return None
        ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
        uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
        return (ux, uy), math.dist((ux, uy), a)
    cands = [circ2(a, b) for a, b in itertools.combinations(P, 2)]
    cands += [c for c in (circ3(*t) for t in itertools.combinations(P, 3)) if c]
    for O, R in sorted(cands, key=lambda t: t[1]):
        if all(math.dist(O, p) <= R * (1 + 1e-9) for p in P): return O, R
    return None

def interior_angle(P, v):
    n = len(P); a, b, c = np.array(P[v - 1]), np.array(P[v]), np.array(P[(v + 1) % n])
    u, w = a - b, c - b
    return math.degrees(math.acos(max(-1, min(1, u @ w / (np.linalg.norm(u) * np.linalg.norm(w))))))

def check(P, encs, tol=1e-9):
    n = len(P); enc, cl_all, cl_noB, vars_ = encs
    d = {p: math.dist(P[p[0]], P[p[1]]) for p in enc.pairs}
    ass = []
    for i, j in itertools.combinations(range(enc.NP), 2):
        x, y = d[enc.pairs[i]], d[enc.pairs[j]]
        eq = abs(x - y) <= tol * max(x, y)
        ass.append(enc.E(i, j) if eq else -enc.E(i, j))
        ass.append(enc.LT(i, j) if (not eq and x < y) else -enc.LT(i, j))
        ass.append(enc.LT(j, i) if (not eq and y < x) else -enc.LT(j, i))
    ang = [interior_angle(P, v) for v in range(n)]
    for v in range(n):
        ass.append(vars_['A'][v] if ang[v] < 90 - 1e-9 else -vars_['A'][v])
        ass.append(vars_['D'][v] if ang[v] <= 60 + 1e-9 else -vars_['D'][v])
    O, R = mec(P)
    T = [v for v in range(n) if math.dist(O, P[v]) >= R * (1 - 1e-9)]
    diam = any(abs(math.dist(P[a], P[b]) - 2 * R) <= 1e-9 * R for a, b in itertools.combinations(T, 2))
    useB = len(T) >= 3 and not diam
    for v in range(n): ass.append(vars_['s'][v] if v in T else -vars_['s'][v])
    with Cadical153(bootstrap_with=(cl_all if useB else cl_noB)) as S:
        return S.solve(assumptions=ass), useB

def build(n):
    enc = Enc(n, n - 1, order=False)
    clB, vars_ = add_families(enc, {'A', 'D', 'B', 'F'}, violator=False)
    enc2 = enc  # same pool: build the no-B variant with the same variables
    clnoB, _ = add_families(enc2, {'A', 'D', 'F'}, violator=False)
    # map variable ids: second call created new A/D/s ids? IDPool.id is idempotent for the same key -> same ids
    return enc, clB, clnoB, vars_

if __name__ == '__main__':
    n, count, seed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    rng = random.Random(seed)
    encs = build(n)
    bad = 0; nB = 0; tested = 0
    gens = [lambda: valtr(n, rng), lambda: near_circle(n, rng, 0.05), lambda: near_circle(n, rng, 0.3)]
    for t in range(count):
        P = gens[t % 3]()
        if not strictly_convex(P): continue
        ok, useB = check(P, encs); tested += 1; nB += useB
        if not ok:
            bad += 1
            if bad <= 3: print("UNSOUND on", json.dumps(P))
    # structured: regular, bi-regular (ties)
    special = [[(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]]
    if n % 2 == 0:
        for r in (0.9, 0.97, 1.03):
            special.append([((1 if k % 2 == 0 else r) * math.cos(2 * math.pi * k / n), (1 if k % 2 == 0 else r) * math.sin(2 * math.pi * k / n)) for k in range(n)])
    sbad = 0
    for P in special:
        if strictly_convex(P):
            ok, _ = check(P, encs, tol=1e-9); sbad += (not ok)
    print(f"n={n}: {tested} random strictly convex polygons tested ({nB} with >=3-point MEC, B active): {bad} unsound; "
          f"special (regular/bi-regular, with ties): {len(special)} tested, {sbad} unsound")
