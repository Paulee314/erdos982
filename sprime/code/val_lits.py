#!/usr/bin/env python3
"""Empirical soundness of learned literal-set clauses (Lambda + Lambda-MEC, {'lits'} records, all dihedral images):
for strictly convex polygons in case (M) (support >= 3, no diametral pair), compute the TRUE local distance relations and
TRUE support; every clause must have a false literal. Also polygons not in case (M): clauses without support
literals must still hold. plant=1 adds a false clause.  Usage: val_lits.py n count seed file.jsonl [plant=1]"""
import sys, os, math, random, json, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
import validate as V
args = [a for a in sys.argv[1:] if '=' not in a]; kw = dict(a.split('=') for a in sys.argv[1:] if '=' in a)
n, count, seed, fn = int(args[0]), int(args[1]), int(args[2]), args[3]; rng = random.Random(seed)
FL = {'<': '>', '>': '<', '=': '='}
def norm(l):
    if l[0] == 'L':
        _, u, v, w, r = l; return ('L', u, v, w, r) if v < w else ('L', u, w, v, FL[r])
    return ('S', l[1], bool(l[2]))
clauses = set()
for line in open(fn):
    J = json.loads(line); base = [tuple(x) for x in J['lits']] if 'lits' in J else [('L',) + tuple(x) for x in J['core']]
    for r in range(n):
        for o in (1, -1):
            g = lambda x: (r + o * x) % n
            clauses.add(frozenset(norm(('L', g(l[1]), g(l[2]), g(l[3]), l[4]) if l[0] == 'L' else ('S', g(l[1]), l[2])) for l in base))
if kw.get('plant') == '1': clauses.add(frozenset([('L', 0, 1, n - 1, '=')]))   # false for regular / mirror polygons
clauses = list(clauses)
def circle_poly():
    m = rng.randint(3, n); ang = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    if rng.random() < 0.4: ang = sorted((2 * math.pi * i / n + rng.uniform(-0.15, 0.15) / n) % (2 * math.pi) for i in range(n))
    S = set(rng.sample(range(n), m)); out = []
    for i, a in enumerate(ang):
        r = 1.0 if i in S else rng.uniform(0.93, 0.999); out.append((r * math.cos(a), r * math.sin(a)))
    return out
def regular_pushed():
    S = set(rng.sample(range(n), rng.randint(3, n)))
    return [((1.0 if i in S else 0.97) * math.cos(2 * math.pi * i / n), (1.0 if i in S else 0.97) * math.sin(2 * math.pi * i / n)) for i in range(n)]
def evaluate(P, tol=1e-9):
    truth = set()
    for u in range(n):
        for v, w in itertools.combinations([x for x in range(n) if x != u], 2):
            a, b = math.dist(P[u], P[v]), math.dist(P[u], P[w])
            truth.add(('L', u, v, w, '=' if abs(a - b) <= tol * max(a, b) else ('<' if a < b else '>')))
    O, R = V.mec(P); sup = [abs(math.dist(O, p) - R) <= 1e-9 * R for p in P]; T = [v for v in range(n) if sup[v]]
    caseM = len(T) >= 3 and not any(abs(math.dist(P[a], P[b]) - 2 * R) <= 1e-9 * R for a in T for b in T if a < b)
    for v in range(n): truth.add(('S', v, sup[v]))
    bad = 0
    for C in clauses:
        if not caseM and any(l[0] == 'S' for l in C): continue
        if C <= truth: bad += 1
    return bad, caseM, sum(1 for l in truth if l[0] == 'L' and l[4] == '=')
gens = [lambda: V.valtr(n, rng), lambda: V.near_circle(n, rng, 0.05), circle_poly, circle_poly, regular_pushed]
tested = badp = cm = 0; eqs = 0
for t in range(count):
    for _ in range(200):
        P = gens[t % len(gens)]()
        if V.strictly_convex(P): break
    else: continue
    b, c, e = evaluate(P); tested += 1; cm += c; badp += (b > 0); eqs += e
print(f"n={n} {fn} plant={kw.get('plant','0')}: {len(clauses)} clauses (with images); {tested} polygons ({cm} case-(M)), "
      f"mean local equalities {eqs/max(1,tested):.1f}; {badp} polygons violating some clause")
