#!/usr/bin/env python3
"""Empirical soundness test of family Lambda (angle LP) and of the learned Lambda clauses.
For each test polygon (strictly convex):
  (1) compute the TRUE elementary angles x[p][k] (units of pi) and evaluate every base row (pos/int/tri) and every
      literal row for the polygon's TRUE local distance relations: each must hold (strict rows with margin > 0,
      equalities within tolerance);
  (2) the LP with all true local relations must be feasible with t > 0;
  (3) every learned clause in the given jsonl files must be satisfied by the polygon's true local relations.
Polygon generators: Valtr-random, near-circle (two radii spreads), and TIE-RICH ones: regular, bi-regular, mirror-
symmetric (axis through a vertex), 'fan' polygons with many vertices on one circle about a vertex, dihedral-k
symmetric, and regular polygons with a random subset of vertices pushed inward (keeps many equalities).
PLANT=1 inverts one family fact (sine-law orientation) / PLANT=2 adds a false clause, to show the test catches errors.
Usage: val_lambda.py n count seed [learned1.jsonl ...] [plant=0|1|2]"""
import sys, os, math, random, itertools, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
import validate as V
from angle_lp import AngleLP

args = [a for a in sys.argv[1:] if '=' not in a]; kw = dict(a.split('=') for a in sys.argv[1:] if '=' in a)
n, count, seed = int(args[0]), int(args[1]), int(args[2]); files = args[3:]
plant = int(kw.get('plant', 0))
rng = random.Random(seed); lp = AngleLP(n); base = lp.base_rows()
learned = []
for fn in files:
    for line in open(fn):
        J = json.loads(line)
        if 'core' in J: learned.append([tuple(x) for x in J['core']])
if plant == 2:   # a false clause: forbids the regular polygon's equality d(0,1) = d(0,n-1)
    learned.append([(0, 1, n - 1, '=')])

def rel(P, u, v, w, tol):
    a, b = math.dist(P[u], P[v]), math.dist(P[u], P[w])
    return '=' if abs(a - b) <= tol * max(a, b) else ('<' if a < b else '>')

def true_x(P):
    z = [0.0] * lp.nv
    for p in range(n):
        L = lp.L[p]
        for k in range(n - 2):
            a, b = P[L[k]], P[L[k + 1]]
            u = (a[0] - P[p][0], a[1] - P[p][1]); w = (b[0] - P[p][0], b[1] - P[p][1])
            c = (u[0] * w[0] + u[1] * w[1]) / (math.hypot(*u) * math.hypot(*w))
            z[lp.xi(p, k)] = math.acos(max(-1, min(1, c))) / math.pi
    return z

def lit_row(u, v, w, r):
    d, rr, k = lp.lit_row(u, v, w, r)
    if plant == 1 and r == '<':          # planted error: wrong orientation of the sine law
        d = {kk: (-x if kk != lp.T else x) for kk, x in d.items()}
    return d, rr, k

def evaluate(P, tol=1e-9):
    z = true_x(P); bad = []
    rows = list(base)
    R = {}
    for u in range(n):
        for v, w in itertools.combinations([x for x in range(n) if x != u], 2):
            r = rel(P, u, v, w, tol); R[(u, v, w)] = r
            d, rr, k = lit_row(u, v, w, r); rows.append((d, rr, k, (u, v, w, r)))
    # margin t = min over strict rows of (lhs - rhs) with t-coefficient removed
    margins = []
    for d, rr, kind, tag in rows:
        val = sum(x * z[k] for k, x in d.items() if k != lp.T)
        if kind == 'eq':
            if abs(val - rr) > 1e-7: bad.append(('eq', tag, val - rr))
        else:
            if lp.T in d: margins.append(val - rr)            # strict row: val - rr must be > 0
            elif val - rr < -1e-9: bad.append(('ge', tag, val - rr))
    if margins and min(margins) <= 0: bad.append(('strict', min(margins)))
    tm, _ = lp.solve(rows, want_dual=False)
    if tm <= 1e-9: bad.append(('lp', tm))
    for C in learned:
        def holds(x):
            u, v, w, r = x
            if v > w: v, w = w, v; r = {'<': '>', '>': '<', '=': '='}[r]
            return R[(u, v, w)] == r
        if all(holds(x) for x in C): bad.append(('clause', C))
    return bad, sum(1 for r in R.values() if r == '=')

# ---------- generators
def regular(k=None, rad=None):
    rad = rad or [1.0] * n
    return [(rad[i] * math.cos(2 * math.pi * i / n), rad[i] * math.sin(2 * math.pi * i / n)) for i in range(n)]
def biregular():
    r = rng.uniform(0.85, 1.15); return regular(rad=[1 if i % 2 == 0 else r for i in range(n)])
def mirror():
    # axis = x-axis through vertex 0 at (1,0); upper chain = sorted random angles, lower = mirror
    m = (n - 1) // 2
    ang = sorted(rng.uniform(0.05, math.pi - 0.05) for _ in range(m))
    rad = [1 + rng.uniform(-0.03, 0.03) for _ in range(m)]
    up = [(rr * math.cos(a), rr * math.sin(a)) for a, rr in zip(ang, rad)]
    pts = [(1.0, 0.0)] + up + ([(-1.0 * rng.uniform(0.8, 1.2), 0.0)] if n % 2 == 0 else []) + [(x, -y) for x, y in reversed(up)]
    return pts
def fan():
    # vertex 0 at origin; k vertices on the circle of radius 1 about it in an arc of < pi; others random outward
    k = rng.randint(3, n - 1)
    th0 = rng.uniform(0, 2 * math.pi); span = rng.uniform(0.6, 0.95) * math.pi
    ang = sorted(rng.uniform(0, span) for _ in range(n - 1))
    pick = set(rng.sample(range(n - 1), k))
    pts = [(0.0, 0.0)]
    for i, a in enumerate(ang):
        r = 1.0 if i in pick else rng.uniform(0.98, 1.02)
        pts.append((r * math.cos(th0 + a), r * math.sin(th0 + a)))
    return pts
def dihedral():
    k = rng.choice([d for d in range(2, n + 1) if n % d == 0 and d >= 2])
    m = n // k
    base_ang = sorted(rng.uniform(0, 2 * math.pi / k) for _ in range(m))
    rad = [rng.uniform(0.85, 1.15) for _ in range(m)]
    pts = []
    for j in range(k):
        for a, r in zip(base_ang, rad):
            pts.append((r * math.cos(a + 2 * math.pi * j / k), r * math.sin(a + 2 * math.pi * j / k)))
    return pts
def pushed():
    rad = [1.0 if rng.random() < 0.6 else rng.uniform(0.9, 0.99) for _ in range(n)]
    return regular(rad=rad)

gens = [('valtr', lambda: V.valtr(n, rng)), ('circle.05', lambda: V.near_circle(n, rng, 0.05)),
        ('circle.3', lambda: V.near_circle(n, rng, 0.3)), ('mirror', mirror), ('fan', fan), ('dihedral', dihedral),
        ('pushed', pushed), ('biregular', biregular)]
stats = {g: [0, 0, 0] for g, _ in gens}   # tested, bad, total equalities
first_bad = None
for t in range(count):
    name, g = gens[t % len(gens)]
    for _ in range(500):
        P = g()
        if V.strictly_convex(P): break
    else: continue
    bad, neq = evaluate(P)
    stats[name][0] += 1; stats[name][2] += neq
    if bad:
        stats[name][1] += 1
        if first_bad is None: first_bad = (name, bad[:3])
for P in [regular()]:
    bad, neq = evaluate(P); stats.setdefault('regular', [0, 0, 0]); s = stats['regular']; s[0] += 1; s[1] += bool(bad); s[2] += neq
tot = sum(s[0] for s in stats.values()); totbad = sum(s[1] for s in stats.values())
print(f"n={n} plant={plant} learned_clauses={len(learned)}: {tot} polygons, {totbad} with a violated row/LP/clause")
for k, s in stats.items(): print(f"   {k:10s} tested {s[0]:6d}  bad {s[1]:5d}  mean local equalities {s[2]/max(1,s[0]):.1f}")
if first_bad: print("   first failure:", first_bad)
