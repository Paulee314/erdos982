#!/usr/bin/env python3
"""Planted-error test for the LRAT path: CNF = C4 n=8 encoding (fams, cube 0:4,1:4); CaDiCaL --lrat proof; cake_lpr must
accept the genuine proof and REJECT three corrupted copies: (a) one hint id in a mid-proof addition replaced by another id,
(b) one literal removed from a mid-proof lemma's hints-target (i.e. a lemma made stronger), (c) the final empty-clause line's
hints truncated.  Usage: val_plant.py WORKDIR"""
import sys, os, subprocess, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sat'))
from c4_cegar import build_c4, cube_clauses
W = sys.argv[1]; os.makedirs(W, exist_ok=True)
CAD = os.environ['CADICAL']; CHK = os.environ['LRATCHK']
enc, cl, _ = build_c4(8, 27, 'lex', 'FGXOADKN'); cl += cube_clauses(enc, '0:4,1:4')
nv = max(abs(x) for c in cl for x in c); cnf = os.path.join(W, 'p.cnf')
open(cnf, 'w').write(f"p cnf {nv} {len(cl)}\n" + ''.join(' '.join(map(str, c)) + ' 0\n' for c in cl))
pf = os.path.join(W, 'p.lrat')
r = subprocess.run([CAD, '-q', '--lrat=true', '--binary=false', cnf, pf], capture_output=True, text=True); print('cadical:', [l for l in r.stdout.splitlines() if l.startswith('s ')])
def chk(p):
    o = subprocess.run([CHK, cnf, p], capture_output=True, text=True); out = (o.stdout + o.stderr).strip().splitlines()
    return any(l.strip() == 's VERIFIED UNSAT' for l in out), (out[-1] if out else '')
print('genuine:', chk(pf))
L = open(pf).read().splitlines(); adds = [i for i, l in enumerate(L) if l.split()[1:2] != ['d'] and len(l.split()) > 3]
R = random.Random(1); ok_all = True
# (a) wrong hint id
i = adds[len(adds) // 2]; p = L[i].split(); z = p.index('0', 1); hints = p[z + 1:-1]
j = z + 1 + R.randrange(len(hints)); p[j] = str(max(1, int(p[j]) - 1) if int(p[j]) > 1 else int(p[j]) + 1)
A = L[:]; A[i] = ' '.join(p); open(pf + '.a', 'w').write('\n'.join(A) + '\n')
# (b) lemma strengthened: drop one literal from a non-unit lemma
for i in adds[len(adds) // 3:]:
    p = L[i].split(); z = p.index('0', 1)
    if z >= 3: break
B = L[:]; p = L[i].split(); del p[1]; B[i] = ' '.join(p); open(pf + '.b', 'w').write('\n'.join(B) + '\n')
# (c) final empty clause: drop the last half of its hints
k = max(i for i, l in enumerate(L) if l.split()[1:2] == ['0']); p = L[k].split(); h = p[2:-1]
C = L[:]; C[k] = ' '.join(p[:2] + h[:max(1, len(h) // 2)] + ['0']); open(pf + '.c', 'w').write('\n'.join(C) + '\n')
for s in 'abc':
    v = chk(pf + '.' + s); print(f'corrupt ({s}):', v); ok_all &= not v[0]
print('PLANTED TEST', 'PASS (all corrupted proofs rejected)' if ok_all else 'FAIL')
