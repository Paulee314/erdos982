#!/usr/bin/env python3
"""Fast single-solve sub-case pipeline for C4 (pipeline B+C, approved 5 Nov 2026).
CNF = build_c4(n, bound, lex, FAMS) + cube clauses + every learned clause in the given files (all dihedral images; Sigma
records as-is), learned clauses LAST so their clause ids are known.  Steps:
  1. CaDiCaL (--lrat, text) on the CNF.  'SATISFIABLE' -> status SAT (the driver falls back to the CEGAR/LP loop and the
     two-round c4_certcube certification).  'UNSATISFIABLE' -> 2.
  2. LRAT checker (cake_lpr, the CakeML-verified LRAT/LPR checker) on CNF + proof: must print 's VERIFIED UNSAT'.
  3. Learned clauses referenced in any hint of the proof (a superset of the ones the refutation needs; if the proof had
     any RAT step, i.e. a negative hint, ALL learned clauses count as referenced) get exact certificates for their own
     literal sets (Lambda rows incl. K/P/H; else Delta) and go through the independent checker check_lambda_certs.py.
     All accepted -> VERIFIED.  Any failure -> status CERT_FAIL (driver falls back to c4_certcube, two rounds).
  4. The raw LRAT is deleted after verification (sha256 + size kept); CNF and the referenced-id list are kept gzipped.
Output: OUT.json summary; OUT_r1.cnf.gz; OUT_refs.txt.gz; OUT_lambda_ok.jsonl.
Usage: c4_fastcube.py n OUT fams=F cube=c:a,c:b [bound=B] file1.jsonl ..."""
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
CAD = os.environ.get('CADICAL', 'cadical'); CHK = os.environ.get('LRATCHK', 'cake_lpr')
t0 = time.time()
summ = {'n': n, 'bound': bound, 'fams': ''.join(sorted(set(FAMS))), 'cube': CUBE, 'ver': code_md5(), 'pipeline': 'fast-lrat',
        'checker': os.path.basename(CHK)}
def log(*a): print(*a, f"[{time.time()-t0:.0f}s]", flush=True)
def done(status, **extra):
    summ.update(extra); summ['status'] = status; summ['wall'] = round(time.time() - t0, 1)
    json.dump(summ, open(OUT + '.json', 'w')); log('FINAL', json.dumps(summ)); sys.exit(0)
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 24), b''): h.update(blk)
    return h.hexdigest()
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
klist = list(keys); lam = [[-v for v in k] for k in klist]
clauses = base_cl + lam; nb = len(base_cl)
log(f"C4 n={n} bound={bound} fams={summ['fams']} cube={CUBE}: {nb} base clauses + {len(lam)} learned (ids {nb+1}..{len(clauses)})")
pre = OUT + '_r1'
nv = max(abs(x) for c in clauses for x in c)
with open(pre + '.cnf', 'w') as f:
    f.write(f"p cnf {nv} {len(clauses)}\n")
    for c in clauses: f.write(' '.join(map(str, c)) + ' 0\n')
summ['cnf_sha256'] = sha256(pre + '.cnf'); summ['learned_in_cnf'] = len(lam)
ts = time.time()
r = subprocess.run([CAD, '-q', '--lrat=true', '--binary=false', pre + '.cnf', pre + '.lrat'], capture_output=True, text=True)
st = [l for l in r.stdout.splitlines() if l.startswith('s ')]; summ['solve'] = round(time.time() - ts, 1)
log(f"cadical {st} in {summ['solve']}s")
if st and st[-1] == 's SATISFIABLE':
    for p in (pre + '.lrat',):
        if os.path.exists(p): os.remove(p)
    done('SAT')
if not st or st[-1] != 's UNSATISFIABLE': done('SOLVER_ERROR', solver_out=(r.stdout + r.stderr)[-500:])
summ['proof_bytes'] = os.path.getsize(pre + '.lrat'); summ['proof_sha256'] = sha256(pre + '.lrat')
ts = time.time()
c = subprocess.run([CHK, pre + '.cnf', pre + '.lrat'], capture_output=True, text=True)
summ['check'] = round(time.time() - ts, 1); outl = (c.stdout + c.stderr).strip().splitlines()
summ['checker_out'] = outl[-1] if outl else ''
log(f"checker: {summ['checker_out']} in {summ['check']}s")
if not any(l.strip() == 's VERIFIED UNSAT' for l in outl): done('CHECK_FAILED')
# learned clauses referenced by the proof
refs = set(); rat = False; lo, hi = nb + 1, len(clauses)
with open(pre + '.lrat') as f:
    for line in f:
        p = line.split()
        if len(p) < 2 or p[1] == 'd': continue
        z = p.index('0', 1)
        for h in p[z + 1:-1]:
            v = int(h)
            if v < 0: rat = True
            elif lo <= v <= hi: refs.add(v)
if rat: refs = set(range(lo, hi + 1))
os.remove(pre + '.lrat')
with open(pre + '.cnf', 'rb') as fi, gzip.open(pre + '.cnf.gz', 'wb') as fo: fo.write(fi.read())
os.remove(pre + '.cnf')
with gzip.open(OUT + '_refs.txt.gz', 'wt') as f: f.write('\n'.join(map(str, sorted(refs))) + '\n')
used = [keys[klist[i - lo]] for i in sorted(refs)]
summ.update(core_learned=len(used), rat_steps=rat)
log(f"proof references {len(used)} learned clauses (rat={rat})")
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
bad = set()
if used:
    chk = subprocess.run([sys.executable, os.path.join(HERE, 'check_lambda_certs.py'), str(n), OUT + '_lambda.jsonl'], capture_output=True, text=True)
    last = (chk.stdout.strip().splitlines() or ['(no output)'])[-1]; log("cert checker:", last)
    bad = {int(l.split()[2]) for l in chk.stdout.splitlines() if l.startswith('FAILED')}; summ['cert_checker'] = last
with open(OUT + '_lambda_ok.jsonl', 'w') as fo:
    for ln, line in enumerate(open(OUT + '_lambda.jsonl')):
        if ln not in bad: fo.write(line)
summ.update(cert_failed=nf, checker_rejected=len(bad))
done('VERIFIED' if nf == 0 and not bad else 'CERT_FAIL')
