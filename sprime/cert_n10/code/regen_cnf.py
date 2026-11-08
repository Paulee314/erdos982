#!/usr/bin/env python3
"""Regenerate the n = 10 S'-violation CNF: testA_sat.build(10,'S','lex') (base clause families of the n<=13
verification + both S' window clauses at every vertex + generic dihedral lex-leader) + family F (angle_fams) +
one clause per record of the Lambda file: OR over the core literals (u,v,w,rel) of NOT[ |uv| rel |uw| ],
where '=' -> E(uv,uw), '<' -> LT(uv,uw), '>' -> LT(uw,uv) in e982lib's variable numbering.
Usage: regen_cnf.py lambda.jsonl out.cnf"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testA_sat import build
from angle_fams import add_families
enc, _, _ = build(10, 'S', 'lex'); ex, _ = add_families(enc, {'F'}, violator=True)
pr, LT, E = enc.pr, enc.LT, enc.E
def lv(u, v, w, r):
    a, b = pr(u, v), pr(u, w); return E(a, b) if r == '=' else (LT(a, b) if r == '<' else LT(b, a))
cl = enc.clauses + ex
for line in open(sys.argv[1]):
    J = json.loads(line); cl.append([-lv(*x) for x in J['core']])
nv = max(abs(x) for c in cl for x in c)
with open(sys.argv[2], 'w') as f:
    f.write(f"p cnf {nv} {len(cl)}\n")
    for c in cl: f.write(' '.join(map(str, c)) + ' 0\n')
print(f"wrote {len(cl)} clauses ({len(enc.clauses)} base, {len(ex)} F, {len(cl)-len(enc.clauses)-len(ex)} Lambda), {nv} vars")
