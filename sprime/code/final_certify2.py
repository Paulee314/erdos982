#!/usr/bin/env python3
"""Two-round certification for cegar2 runs (Lambda + Lambda-MEC + Lambda-circle, families B,F).
Round 1: CNF = testA_sat.build(n,'S','lex') + families (default BF) + every learned clause (all dihedral images of every
         record; records: {'lits'} or {'core'}) -> Glucose4 DRUP -> drat-trim -c core.
Round 2: every learned clause in the core gets an exact Farkas certificate for ITS OWN literal set (certify_lits logic:
         rows_for_lits = base rows + L rows + MEC rows + K rows derivable from the literals) -> independent checker
         check_lambda_certs.py must accept it -> CNF2 = base + families + exactly the accepted clauses -> Glucose4 DRUP
         -> drat-trim.
Usage: final_certify2.py n OUT FAMS file1.jsonl [file2.jsonl ...]"""
import sys, os, json, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
from testA_sat import build
from angle_fams import add_families
from angle_fams2 import add_families2
from angle_lp import AngleLP, exact_certificate, verify_certificate
from cegar2 import rows_for_lits, norm_lit
import delta_rows
from pysat.formula import CNF
from pysat.solvers import Glucose4

n = int(sys.argv[1]); OUT = sys.argv[2]; fams = set(sys.argv[3]); files = sys.argv[4:]
DT = os.environ.get('DRAT', os.path.join(HERE, '..', 'drat-trim', 'drat-trim')); t0 = time.time()
def log(*a): print(*a, f"[{time.time()-t0:.0f}s]", flush=True)
enc, _, _ = build(n, 'S', 'lex')
extra, V = add_families(enc, fams & set('ABDF'), violator=True); extra += add_families2(enc, fams & set('KNGXO'))[0]
pr, LT, E = enc.pr, enc.LT, enc.E; S = V['s']
def var(l):
    if l[0] == 'S': return S[l[1]] if l[2] else -S[l[1]]
    if l[0] == 'X':
        _, a1, b1, c1, d1, r = l; a, b = pr(a1, b1), pr(c1, d1)
        return E(a, b) if r == '=' else (LT(a, b) if r == '<' else LT(b, a))
    _, u, v, w, rel = l; a, b = pr(u, v), pr(u, w)
    return E(a, b) if rel == '=' else (LT(a, b) if rel == '<' else LT(b, a))
keys = {}; SIGREC = {}
for fn in files:
    for line in open(fn):
        try: J = json.loads(line)
        except Exception: continue
        if 'lits' in J: base = [tuple(x) for x in J['lits']]
        elif 'core' in J: base = [('L',) + tuple(x) for x in J['core']]
        else: continue
        base = [norm_lit(l) for l in base]
        if 'sigma' in J:            # certified Sigma record: base clause only, certificate kept verbatim
            I = tuple(sorted(set(base), key=str)); kk = tuple(sorted(var(l) for l in I))
            keys.setdefault(kk, I); SIGREC[kk] = J; continue
        for r in range(n):
            for o in (1, -1):
                g = lambda x: (r + o * x) % n
                I = tuple(sorted({norm_lit(('L', g(l[1]), g(l[2]), g(l[3]), l[4])) if l[0] == 'L' else
                                  (norm_lit(('X', g(l[1]), g(l[2]), g(l[3]), g(l[4]), l[5])) if l[0] == 'X' else ('S', g(l[1]), l[2]))
                                  for l in base}, key=str))
                keys.setdefault(tuple(sorted(var(l) for l in I)), I)
log(f"n={n}: {len(keys)} distinct learned clauses (with images)")
def solve_check(clauses, pre, core_out=None):
    cnf = CNF(from_clauses=clauses); cnf.to_file(pre + '.cnf')
    SOL = Glucose4
    if os.environ.get('SOLVER') == 'cadical':
        from pysat.solvers import Cadical195 as SOL
    with SOL(bootstrap_with=cnf.clauses, with_proof=True) as s:
        r = s.solve(); log(f"{pre}: {'SAT' if r else 'UNSAT'}")
        if r: return False
        with open(pre + '.drup', 'w') as f: f.write('\n'.join(s.get_proof()) + '\n')
    out = subprocess.run([DT, pre + '.cnf', pre + '.drup', '-t', '200000'] + (['-c', core_out] if core_out else []),
                         capture_output=True, text=True)
    st = [l for l in out.stdout.splitlines() if l.startswith('s ')]; log("drat-trim:", st)
    return bool(st) and 's VERIFIED' in st[-1]
base_cl = enc.clauses + extra
lam = [[-v for v in k] for k in keys]
if not solve_check(base_cl + lam, OUT + '_r1', OUT + '_r1.core'): sys.exit("round 1 failed")
neg = {tuple(sorted(c)): k for c, k in zip(lam, keys)}
used = []
for line in open(OUT + '_r1.core'):
    if line[0] in 'pc': continue
    c = tuple(sorted(int(x) for x in line.split()[:-1]))
    if c in neg: used.append(keys[neg[c]])
log(f"core uses {len(used)} learned clauses")
lp = AngleLP(n); base = lp.base_rows(); good = []; nf = 0; DLP = delta_rows.DeltaLP(n)
with open(OUT + '_lambda.jsonl', 'w') as f:
    for lits in used:
        kk = tuple(sorted(var(l) for l in lits))
        if kk in SIGREC:
            f.write(json.dumps(SIGREC[kk]) + '\n'); continue
        rows = rows_for_lits(lp, base, list(lits)); cert = exact_certificate(lp, rows)
        if cert is not None and verify_certificate(lp, rows, cert):
            cd = {str(rows[i][3]): str(y) for i, y in cert.items()}
        else:
            cd = DLP.certificate(DLP.base + delta_rows.rel_tags(list(lits)))
            if cd is None: nf += 1; continue
        f.write(json.dumps({'lits': [list(x) for x in lits], 'cert': cd}) + '\n')
log(f"exact certificates: {len(used)-nf} ok, {nf} failed")
chk = subprocess.run([sys.executable, os.path.join(HERE, 'check_lambda_certs.py'), str(n), OUT + '_lambda.jsonl'], capture_output=True, text=True)
log("checker:", chk.stdout.strip().splitlines()[-1])
bad = {int(l.split()[2]) for l in chk.stdout.splitlines() if l.startswith('FAILED')}
with open(OUT + '_lambda_ok.jsonl', 'w') as fo:
    for ln, line in enumerate(open(OUT + '_lambda.jsonl')):
        if ln in bad: continue
        fo.write(line); good.append([-var(tuple(x)) for x in json.loads(line)['lits']])
ok = solve_check(base_cl + good, OUT + '_final')
log(f"FINAL n={n}: {'VERIFIED UNSAT' if ok else 'NOT VERIFIED'} with {len(good)} certified learned clauses")
