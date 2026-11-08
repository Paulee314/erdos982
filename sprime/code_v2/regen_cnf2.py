#!/usr/bin/env python3
"""Regenerate the S'-violation CNF certified by final_certify2.py: testA_sat.build(n,'S','lex') (base clause families
+ both S' windows at every vertex + generic dihedral lex-leader) + families FAMS (angle_fams: B = MEC support selectors,
valid for S'-violators by L3; F = disjoint wide triangles) + one clause per record of the Lambda file, the disjunction of
the negated literals: ('L',u,v,w,rel) -> NOT[|uv| rel |uw|]  ('=' E, '<' LT(uv,uw), '>' LT(uw,uv));  ('S',v,b) -> NOT[s_v == b].
Usage: regen_cnf2.py n FAMS lambda.jsonl out.cnf"""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..', 'sat'))
from testA_sat import build
from angle_fams import add_families
n = int(sys.argv[1]); fams = set(sys.argv[2])
enc, _, _ = build(n, 'S', 'lex'); ex, V = add_families(enc, fams, violator=True)
pr, LT, E, S = enc.pr, enc.LT, enc.E, V['s']
def var(l):
    if l[0] == 'S': return S[l[1]] if l[2] else -S[l[1]]
    if l[0] == 'X':
        _, a1, b1, c1, d1, r = l; a, b = pr(a1, b1), pr(c1, d1)
        return E(a, b) if r == '=' else (LT(a, b) if r == '<' else LT(b, a))
    _, u, v, w, r = l; a, b = pr(u, v), pr(u, w); return E(a, b) if r == '=' else (LT(a, b) if r == '<' else LT(b, a))
cl = enc.clauses + ex; k = 0
for line in open(sys.argv[3]):
    J = json.loads(line); cl.append([-var(tuple(x)) for x in J['lits']]); k += 1
nv = max(abs(x) for c in cl for x in c)
with open(sys.argv[4], 'w') as f:
    f.write(f"p cnf {nv} {len(cl)}\n")
    for c in cl: f.write(' '.join(map(str, c)) + ' 0\n')
print(f"wrote {len(cl)} clauses ({len(enc.clauses)} base, {len(ex)} families {''.join(sorted(fams))}, {k} Lambda), {nv} vars")
