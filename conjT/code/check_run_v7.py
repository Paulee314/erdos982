#!/usr/bin/env python3
"""Audit of a T* run split over a v1 directory (apex_pieces.py v13) and a v2 directory (apex_v2.py), check_run_v6 + v2.
usage: check_run_v7.py n v2dir [APEX_L] [--v1dir DIR] [--piecelist FILE] [--allow-unrefereed]
Checks:
 (1) coverage: the union of w*.done over both directories covers every kept piece (duplicates are harmless: every
     line is a completed UNSAT piece); with --piecelist, every listed piece is done in v2dir or v1dir;
 (2) per directory, as v6: every model was blocked by a library core ('hit'/'new') with a VERIFIED certificate, or
     recorded 'big' with a VERIFIED pattern certificate -- no SURVIVOR;
 (3) v2 only: every model killed by Lambda ('lambda-eq'/'lambda-full') has a record in w<r>.lambda for that piece, and
     EVERY record in every w*.lambda is re-verified by the independent exact checker check_lambda_certs.py;
 (4) v2 only: every .done/.models line carries ver=<tag>; the tags (family sets + code md5) are listed; a family not
     in the refereed set {G, X, O} (e.g. NB, R3) makes the audit FAIL unless --allow-unrefereed.
TRUSTED LEMMAS (the UNSAT verdicts are relative to these; the audit cannot check them):
  v1 encoding: E transitivity, class-count bound, F1, F2, strict total preorder axioms, F2-order, chord monotonicity,
               four-in-a-class gap clause, dihedral lex-leader cover (sym_compact), T* cardinality (Z_p >= L);
  v2 adds:     G ('angle >= 60' sources/closure/3-disjoint budget), X ('> 60' sources, triangle sums, isosceles
               coupling), O (middle of an equidistant triple is > 90; budgets) -- angle_fams2.py via fams_v2.py;
               valid in every strictly convex polygon (no S'-violator hypothesis); Wonder referee in
               v2_bench/wonder_GXO_referee*.txt; empirical check v2_bench/tstar_v2/val_10k.log.
  Lambda clauses are NOT trusted: each is re-verified here from its exact Farkas certificate."""
import sys, os, glob, ast, json, collections, subprocess, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from e982lib import Enc, partitions
from apex_pieces_v1 import apex_of

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
n, v2dir = int(args[0]), args[1]
L = int(args[2]) if len(args) > 2 and args[2] != opt('--v1dir') and args[2] != opt('--piecelist') else (n - 1) // 2 + 1
v1dir = opt('--v1dir'); plist = opt('--piecelist'); allow_unref = '--allow-unrefereed' in sys.argv
REFEREED = {'G', 'X', 'O', 'LAM'}
print('TRUSTED LEMMAS' + __doc__.split('TRUSTED LEMMAS')[1])
enc = Enc(n, n - 1, order=False, atmost=True)
allp = list(partitions(n - 1, n - 1, exact=False)); keep = enc.keep(allp)
kept = {i for i, rg in enumerate(allp) if keep[i] and apex_of(rg) >= L}


def audit_dir(outdir, is_v2):
    done = collections.Counter(); models_by_piece = {}; cpu = 0.0; untagged = 0; tags = collections.Counter()
    for fn in glob.glob(f'{outdir}/w*.done'):
        for line in open(fn):
            w = line.split()
            if not w: continue
            done[int(w[0])] += 1; models_by_piece[int(w[0])] = int(w[2]); cpu += float(w[6])
            t = [x for x in w if x.startswith('ver=')]
            if t: tags[t[0][4:]] += 1
            elif is_v2: untagged += 1
    lib = {}
    for fn in glob.glob(f'{outdir}/w*.cores'):
        for line in open(fn):
            d = json.loads(line); lib[tuple(map(tuple, d['key']))] = d
    cert_ok = {}
    for k in (5, 6, 7):
        fn = f'{outdir}/cores_k{k}.txt'
        if not os.path.exists(fn): continue
        keys = [tuple(map(tuple, ast.literal_eval(line.split('key')[1].strip()))) for line in open(fn)]
        verified = set(); vkeys = set()
        for lg2 in glob.glob(f'{outdir}/certify_k{k}*.log'):
            for line in open(lg2):
                if line.startswith('pattern ') and 'VERIFIED' in line:
                    if ' key ' in line: vkeys.add(tuple(map(tuple, ast.literal_eval(line.split(' key ', 1)[1].split(':', 1)[0]))))
                    else: verified.add(int(line.split()[1].rstrip(':')))
        for i, key in enumerate(keys): cert_ok[key] = (key in vkeys) or (i in verified)
    big_lines = [l.split('|')[0].strip() for l in open(f'{outdir}/big_all.txt')] if os.path.exists(f'{outdir}/big_all.txt') else []
    big_verified = set(); vpats = set()
    for lg2 in glob.glob(f'{outdir}/certify_big*.log') + glob.glob(f'{outdir}/certify_kbig*.log'):
        for line in open(lg2):
            if line.startswith('pattern ') and 'VERIFIED' in line:
                if ' pat ' in line: vpats.add(line.split(' pat ', 1)[1].split(':', 1)[0].strip())
                else: big_verified.add(int(line.split()[1].rstrip(':')))
    big_ok = {p: (i in big_verified or p in vpats) for i, p in enumerate(big_lines)}
    kinds = collections.Counter(); bad = 0; total = 0; uncert = 0; per_piece = collections.Counter()
    lam_lines = collections.Counter()
    for fn in glob.glob(f'{outdir}/w*.models'):
        for line in open(fn):
            if not line.strip(): continue
            total += 1
            pat, rest = line.split('|', 1); w = rest.split()
            if is_v2 and not any(x.startswith('ver=') for x in w): untagged += 1
            kind = w[2]; kinds[kind] += 1; per_piece[int(w[1])] += 1
            if kind in ('hit', 'new'):
                info = ast.literal_eval(rest[rest.index('('):].split(' t=')[0].strip())
                key = tuple(map(tuple, info[-1]))
                if key not in lib: bad += 1
                elif not cert_ok.get(key, False):
                    uncert += 1
                    if uncert <= 20: print('  UNCERTIFIED core', kind, key)
            elif kind in ('big', 'SURVIVOR'):
                if not (big_ok.get(pat.strip(), False) or pat.strip() in vpats):
                    uncert += 1
                    if uncert <= 20: print('  UNCERTIFIED', kind, pat.strip())
            elif is_v2 and kind in ('lambda-eq', 'lambda-full'):
                lam_lines[int(w[1])] += 1
            else:
                bad += 1
    lam_ok = True; lam_recs = collections.Counter(); nver = nfail = 0
    if is_v2:
        for fn in sorted(glob.glob(f'{outdir}/w*.lambda')):
            for line in open(fn):
                if line.strip(): lam_recs[json.loads(line).get('piece')] += 1
            if os.path.getsize(fn) == 0: continue
            r = subprocess.run([sys.executable, os.path.join(HERE, 'check_lambda_certs.py'), str(n), fn],
                               capture_output=True, text=True)
            m = re.search(r'(\d+) certificates verified exactly, (\d+) failed', r.stdout)
            if not m: lam_ok = False; print('  check_lambda_certs.py gave no verdict on', fn, r.stderr[-300:]); continue
            nver += int(m.group(1)); nfail += int(m.group(2))
        missing_rec = [p for p, c in lam_lines.items() if lam_recs[p] < c]
        if nfail or missing_rec: lam_ok = False
        print(f'  Lambda: {sum(lam_lines.values())} model lines, {sum(lam_recs.values())} records; re-verified {nver}, '
              f'failed {nfail}; pieces with fewer records than lambda kills: {len(missing_rec)}')
    short = [i for i, c in models_by_piece.items() if per_piece[i] < c]
    print(f'[{outdir}] done {len(done)} distinct ({sum(done.values())} lines, duplicates {sum(1 for c in done.values() if c > 1)}); '
          f'python cpu {cpu:.0f}s; library {len(lib)}; big patterns {len(big_lines)} listed / {sum(big_ok.values())} VERIFIED; '
          f'models {total} kinds {dict(kinds)}; bad {bad}; uncertified {uncert}; short {len(short)}'
          + (f'; untagged v2 lines {untagged}; tags {dict(tags)}' if is_v2 else ''))
    ok = bad == 0 and uncert == 0 and not short and lam_ok and (untagged == 0 or not is_v2)
    return done, ok, tags


dv2, ok2, tags = audit_dir(v2dir, True)
dv1, ok1 = collections.Counter(), True
if v1dir: dv1, ok1, _ = audit_dir(v1dir, False)
fams_used = set()
for t in tags:
    m = re.match(r'v2\[([^\]]*)\]', t)
    if m: fams_used |= set(m.group(1).split('+'))
unref = fams_used - REFEREED
if unref: print(f'families in use outside the refereed set: {sorted(unref)}' + (' (allowed by flag)' if allow_unref else ' -> FAIL'))
union = set(dv1) | set(dv2)
missing = kept - union; extra = union - kept
print(f'coverage: kept {len(kept)}; v1 {len(dv1)}; v2 {len(dv2)}; overlap {len(set(dv1) & set(dv2))}; union {len(union)}; '
      f'missing {len(missing)}; extra {len(extra)}')
plist_missing = []
if plist:
    lst = [int(x) for x in open(plist).read().split()]
    plist_missing = [i for i in lst if i not in union]
    print(f'piece list {plist}: {len(lst)} pieces, not done {len(plist_missing)}')
ok = ok1 and ok2 and not missing and not extra and not plist_missing and (not unref or allow_unref)
print('AUDIT', 'PASS' if ok else 'FAIL')
