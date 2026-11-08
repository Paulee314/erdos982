#!/usr/bin/env python3
"""Per-sub-case certification for C4 (external CaDiCaL binary DRAT -> drat-trim core -> exact certificates -> checker).
CNF = build_c4(n, bound, lex, FAMS) + cube clauses + every learned clause currently in the given files (all dihedral images;
Sigma records as-is).  Steps:
  1. cadical CNF PROOF (binary DRAT)           -> must say UNSATISFIABLE
  2. drat-trim CNF PROOF -c CORE               -> must say s VERIFIED; then the raw proof is deleted (sha256 kept)
  3. learned clauses in CORE get exact certificates for their own literal sets (Lambda rows incl. K/P/H, else Delta)
  4. check_lambda_certs.py (independent exact checker) on those certificates
  5. if every core learned clause is accepted: VERIFIED (the round-1 core uses only base/family/cube clauses + accepted
     clauses).  Otherwise round 2: CNF2 = base + cube + accepted clauses only, steps 1-2 again.
Output: OUT.json summary {status, ...}; OUT_core.cnf.gz, OUT_lambda_ok.jsonl, OUT.log.
Usage: c4_certcube.py n OUT fams=F cube=c:a,c:b [bound=B] file1.jsonl ..."""
import sys, os, json, subprocess, time, hashlib, gzip
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
from c4_cegar import build_c4, lit_var, image, cube_clauses, code_md5
from angle_lp import AngleLP, exact_certificate, verify_certificate
from cegar2 import rows_for_lits, norm_lit
import delta_rows

n = int(sys.argv[1]); OUT = sys.argv[2]; kw = {}; files = []
for a in sys.argv[3:]:
    if '=' in a and not a.endswith('.jsonl'): k, v = a.split('=', 1); kw[k] = v
    else: files.append(a)
bound = int(kw.get('bound', n * (n - 1) // 2 - 1)); FAMS = kw.get('fams', 'FGXO'); CUBE = kw.get('cube', '')
CAD = os.environ.get('CADICAL', 'cadical'); DT = os.environ.get('DRAT', os.path.join(HERE, '..', 'drat-trim', 'drat-trim'))
t0 = time.time(); summ = {'n': n, 'bound': bound, 'fams': ''.join(sorted(set(FAMS))), 'cube': CUBE, 'ver': code_md5()}
def log(*a): print(*a, f"[{time.time()-t0:.0f}s]", flush=True)
def done(status, **extra):
    summ.update(extra); summ['status'] = status; summ['wall'] = round(time.time() - t0, 1)
    json.dump(summ, open(OUT + '.json', 'w')); log('FINAL', json.dumps(summ)); sys.exit(0 if status == 'VERIFIED' else 1)
enc, base_cl, reps = build_c4(n, bound, 'lex', FAMS)
base_cl = base_cl + cube_clauses(enc, CUBE)
var = lambda l: lit_var(enc, l)
keys = {}; SIGREC = {}
for fn in files:
    try: fh = open(fn)
    except FileNotFoundError: continue
    for line in fh:
        if not line.endswith('\n'): continue
        try: J = json.loads(line)
        except Exception: continue
        if 'lits' not in J or any(x[0] == 'S' for x in J['lits']): continue
        b = [norm_lit(tuple(l)) for l in J['lits']]
        if 'sigma' in J:
            I = tuple(sorted(set(b), key=str)); kk = tuple(sorted(var(l) for l in I)); keys.setdefault(kk, I); SIGREC[kk] = J; continue
        for r in range(n):
            for o in (1, -1):
                I = image(n, b, r, o); keys.setdefault(tuple(sorted(var(l) for l in I)), I)
log(f"C4 n={n} bound={bound} fams={summ['fams']} cube={CUBE}: {len(keys)} learned clauses (with images)")
def write_cnf(path, clauses):
    nv = max(abs(x) for c in clauses for x in c)
    with open(path, 'w') as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for c in clauses: f.write(' '.join(map(str, c)) + ' 0\n')
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 24), b''): h.update(blk)
    return h.hexdigest()
def solve_check(clauses, pre, core):
    write_cnf(pre + '.cnf', clauses); ts = time.time()
    r = subprocess.run([CAD, '-q', pre + '.cnf', pre + '.drat'], capture_output=True, text=True)
    st = [l for l in r.stdout.splitlines() if l.startswith('s ')]
    tsolve = time.time() - ts; log(f"{pre}: cadical {st} in {tsolve:.0f}s, proof {os.path.getsize(pre + '.drat')/1e9:.2f} GB")
    if not st or st[-1] != 's UNSATISFIABLE': return False, {'solve': tsolve}
    psz = os.path.getsize(pre + '.drat'); ph = sha256(pre + '.drat'); ts = time.time()
    out = subprocess.run([DT, pre + '.cnf', pre + '.drat', '-t', '200000', '-c', core], capture_output=True, text=True)
    sd = [l for l in out.stdout.splitlines() if l.startswith('s ')]; tdt = time.time() - ts
    ok = bool(sd) and 's VERIFIED' in sd[-1]; log(f"drat-trim {sd} in {tdt:.0f}s")
    info = {'solve': round(tsolve, 1), 'drat': round(tdt, 1), 'proof_bytes': psz, 'proof_sha256': ph}
    if ok:
        info['cnf_sha256'] = sha256(pre + '.cnf')
        with open(pre + '.cnf', 'rb') as fi, gzip.open(pre + '.cnf.gz', 'wb') as fo: fo.write(fi.read())
        os.remove(pre + '.cnf')
        os.remove(pre + '.drat')                                   # raw proof deleted once verified (checksum kept)
        with open(core, 'rb') as fi, gzip.open(core + '.gz', 'wb') as fo: fo.write(fi.read())
        os.remove(core)
    return ok, info
lam = [[-v for v in k] for k in keys]
ok, info = solve_check(base_cl + lam, OUT + '_r1', OUT + '_r1.core')
summ['r1'] = info
if not ok: done('FAILED_R1')
neg = {tuple(sorted(c)): k for c, k in zip(lam, keys)}; used = []
with gzip.open(OUT + '_r1.core.gz', 'rt') as fc:
    for line in fc:
        if line[0] in 'pc': continue
        c = tuple(sorted(int(x) for x in line.split()[:-1]))
        if c in neg: used.append(keys[neg[c]])
log(f"core uses {len(used)} learned clauses")
lp = AngleLP(n); base = lp.base_rows(); nf = 0; DLP = delta_rows.DeltaLP(n)
with open(OUT + '_lambda.jsonl', 'w') as f:
    for lits in used:
        kk = tuple(sorted(var(l) for l in lits))
        if kk in SIGREC: f.write(json.dumps(SIGREC[kk]) + '\n'); continue
        rows = rows_for_lits(lp, base, list(lits)); cert = exact_certificate(lp, rows)
        if cert is not None and verify_certificate(lp, rows, cert): cd = {str(rows[i][3]): str(y) for i, y in cert.items()}
        else:
            cd = DLP.certificate(DLP.base + delta_rows.rel_tags(list(lits)))
            if cd is None: nf += 1; continue
        f.write(json.dumps({'lits': [list(x) for x in lits], 'cert': cd, 'ver': summ['ver']}) + '\n')
bad = set(); good = []
if used:
    chk = subprocess.run([sys.executable, os.path.join(HERE, 'check_lambda_certs.py'), str(n), OUT + '_lambda.jsonl'], capture_output=True, text=True)
    last = (chk.stdout.strip().splitlines() or ['(no output)'])[-1]; log("checker:", last, chk.stderr[-300:])
    bad = {int(l.split()[2]) for l in chk.stdout.splitlines() if l.startswith('FAILED')}
    summ['checker'] = last
with open(OUT + '_lambda_ok.jsonl', 'w') as fo:
    for ln, line in enumerate(open(OUT + '_lambda.jsonl')):
        if ln in bad: continue
        fo.write(line); good.append([-var(tuple(x)) for x in json.loads(line)['lits']])
summ.update(core_learned=len(used), cert_failed=nf, checker_rejected=len(bad))
if nf == 0 and not bad: done('VERIFIED')
ok, info = solve_check(base_cl + good, OUT + '_r2', OUT + '_r2.core')
summ['r2'] = info
done('VERIFIED' if ok else 'FAILED_R2')
