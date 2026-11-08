#!/usr/bin/env python3
"""T* v2 static clause families (5 Nov 2026).  Every family here is claimed sound for EVERY strictly convex n-gon
(no S'-violator / MEC hypothesis).  Violator-only material (B0/B1, the B package, Lambda-MEC) is deliberately absent.

Imported unchanged from sprime/sat/angle_fams2.py (Fable/Wonder round 3, proofs refereed there):
  G   g(p;a,b) = 'angle apb >= 60':  wide source, isosceles-base source, superinterval closure, 3-disjoint budget
  X   t(p;a,b) = 'angle apb > 60':   strict sources, t -> g, triangle-sum rules, isosceles apex/base coupling
  O   o(y;x,z) = 'angle xyz > 90':   middle point of an equidistant triple; budgets (2 o's; 1 o + 2 g's)
  N, K  (optional; Fable's circular-segment / bisector-cut rules)
New (Wonder, wonder_jobs/wTstar_prune_out.json, section 2; UNREFEREED):
  NB  (R2 'direct budget'): at vertex a, three configurations (p_i, b_i) whose angular intervals at a are pairwise
      interior-disjoint cannot all have |p_i a| = |p_i b_i| and |a b_i| < |p_i a|   (each would give angle p_i a b_i > 60)
      clause: OR_i [ -E(p_i a, p_i b_i)  v  -LT(a b_i, p_i a) ]
      (R2's t-forcing form  -E(pa,pb) v -LT(ab,pa) v t(a;p,b)  is LITERALLY a clause of X -- see check_subsumed().)
  R3  four points q1..q4 (fan order at p) in one class at p: some consecutive chord is shorter than its radius
      clause: -e(p;q1,q2) v -e(p;q2,q3) v -e(p;q3,q4) v LT(q1q2,pq1) v LT(q2q3,pq2) v LT(q3q4,pq3)
      (the base encoding's 'gap' clause is the same statement with every radius written as pq1)
  DAE double-apex => equilateral:  -e(a;b,c) v -e(b;a,c) v e(c;a,b)   (is literally an E-transitivity clause of the base)
Angular order at p: L_p = p+1, ..., p-1 (positions 0..n-2)."""
import itertools, hashlib, os
from angle_fams2 import add_families2

ALL = ('G', 'X', 'O', 'N', 'K', 'NB', 'R3', 'DAE')


def disjoint_triples(m):
    """interval triples (i1,j1),(i2,j2),(i3,j3) on positions 0..m-1, i1<j1<=i2<j2<=i3<j3 (interior-disjoint)"""
    for i1, j1, i2, j2, i3, j3 in itertools.combinations_with_replacement(range(m), 6):
        if i1 < j1 <= i2 < j2 <= i3 < j3: yield (i1, j1), (i2, j2), (i3, j3)


def nb_clauses(enc, ntuple=3, disjoint=True):
    """NB direct budget.  ntuple/disjoint are parameters only so that validation can plant FALSE variants
    (ntuple=2, or disjoint=False); the solver uses ntuple=3, disjoint=True."""
    n, pr, E, LT = enc.n, enc.pr, enc.E, enc.LT
    out = []
    for a in range(n):
        La = [(a + i) % n for i in range(1, n)]
        if ntuple == 3 and disjoint:
            tri = disjoint_triples(n - 1)
        elif ntuple == 2:
            tri = (((i1, j1), (i2, j2)) for i1, j1, i2, j2 in itertools.combinations_with_replacement(range(n - 1), 4)
                   if i1 < j1 <= i2 < j2)
        else:   # planted: three intervals, nested/overlapping allowed
            iv = list(itertools.combinations(range(n - 1), 2))
            tri = itertools.combinations(iv, 3)
        for ivs in tri:
            for orient in itertools.product((0, 1), repeat=len(ivs)):
                cl = []
                for (i, j), o in zip(ivs, orient):
                    p, b = (La[i], La[j]) if o == 0 else (La[j], La[i])
                    cl += [-E(pr(p, a), pr(p, b)), -LT(pr(a, b), pr(p, a))]
                out.append(cl)
    return out


def r3_clauses(enc):
    n, pr, LT, e = enc.n, enc.pr, enc.LT, enc.e
    out = []
    for p in range(n):
        Lp = [(p + i) % n for i in range(1, n)]
        for q in itertools.combinations(Lp, 4):
            out.append([-e(p, q[0], q[1]), -e(p, q[1], q[2]), -e(p, q[2], q[3])] +
                       [LT(pr(q[t], q[t + 1]), pr(p, q[t])) for t in range(3)])
    return out


def dae_clauses(enc):
    n, e = enc.n, enc.e
    out = []
    for a, b, c in itertools.combinations(range(n), 3):
        for x, y, z in ((a, b, c), (a, c, b), (b, c, a)):        # apexes x, y; third vertex z
            out.append([-e(x, y, z), -e(y, x, z), e(z, x, y)])
    return out


def add_tstar_families(enc, fams):
    fams = set(fams)
    bad = fams - set(ALL)
    if bad: raise ValueError(f'unknown / not-allowed families for T*: {bad}')
    cl, V = add_families2(enc, fams & {'G', 'X', 'O', 'N', 'K'})
    counts = {'GXONK': len(cl)}
    if 'NB' in fams:
        c = nb_clauses(enc); counts['NB'] = len(c); cl += c
    if 'R3' in fams:
        c = r3_clauses(enc); counts['R3'] = len(c); cl += c
    if 'DAE' in fams:
        c = dae_clauses(enc); counts['DAE'] = len(c); cl += c
    return cl, V, counts


def code_md5():
    h = hashlib.md5()
    here = os.path.dirname(os.path.abspath(__file__))
    for f in ('apex_v2.py', 'fams_v2.py', 'angle_fams2.py', 'lambda_v2.py', 'angle_lp.py', 'apex_pieces_v1.py',
              'e982lib.py'):
        p = os.path.join(here, f)
        if os.path.exists(p): h.update(open(p, 'rb').read())
    return h.hexdigest()[:12]


def version_tag(fams, lam):
    order = [f for f in ALL if f in set(fams)]
    return 'v2[' + '+'.join(order + (['LAM'] if lam else [])) + ']md5=' + code_md5()
