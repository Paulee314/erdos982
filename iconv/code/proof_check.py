#!/usr/bin/env python3
"""DRUP/LRAT re-check of the I_conv upper bound  'no model with objective >= T'.
Rebuilds exactly the CNF of iconv_sat.py (same construction order => same variable numbering), adds the learned
clauses logged in <rundir>/blocks.w* whose kind is a certified lemma (lambda / core-* / big; SURVIVOR and allmax lines
are refused: a piece that needs them fails), then:
  mode 'single' : one CNF = encoding + lemmas + card(>= T), no symmetry breaking at all
  mode 'pieces' : one CNF per kept piece (vertex-0 partition units + sym_compact(pi)), same cover as the search
Each CNF is solved by Glucose 4 (pysat) with a DRUP proof, checked by drat-trim, which also emits LRAT, checked by the
verified checker cake_lpr.  Everything is written under <rundir>/proof/.
usage: proof_check.py n T rundir [single|pieces] [--sets] [--fams G,X,O] [--keep]"""
import sys, os, subprocess, time, glob, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
from e982lib import Enc, partitions
import fams_v2
from pysat.card import ITotalizer
from pysat.solvers import Glucose4

DT = os.environ.get('DRAT', os.path.join(HERE, 'bin/dt/drat-trim')); CAKE = os.environ.get('LRATCHK', os.path.join(HERE, 'bin/cl/cake_lpr'))
OK_KINDS = ('lambda', 'big', 'core-hit', 'core-new')


def build(n, T0, fams, sets):
    enc = Enc(n, n - 1, order=True, atmost=True)
    cl, _, _ = fams_v2.add_tstar_families(enc, list(fams)); enc.clauses += cl
    if sets:
        obj = []
        for a, b, c in itertools.combinations(range(n), 3):
            iv = enc.pool.id(('iso', a, b, c)); obj.append(iv)
            enc.clauses.append([-iv, enc.e(a, b, c), enc.e(b, a, c), enc.e(c, a, b)])
    else:
        obj = list(enc.lits)
    N = len(obj); top = enc.pool.top
    tot = ITotalizer(lits=[-l for l in obj], ubound=max(0, N - T0), top_id=top)
    enc.pool.occupy(top + 1, tot.top_id); enc.pool.top = tot.top_id
    return enc, enc.clauses + tot.cnf.clauses, tot, N


def write_cnf(fn, clauses, nv):
    with open(fn, 'w') as f:
        f.write(f'p cnf {nv} {len(clauses)}\n')
        for c in clauses: f.write(' '.join(map(str, c)) + ' 0\n')


def check(cnf_clauses, nv, base):
    t0 = time.time()
    s = Glucose4(bootstrap_with=cnf_clauses, with_proof=True)
    r = s.solve()
    if r: return 'SAT', 0
    proof = s.get_proof(); s.delete()
    write_cnf(base + '.cnf', cnf_clauses, nv)
    with open(base + '.drup', 'w') as f: f.write('\n'.join(proof) + '\n')
    p = subprocess.run([DT, base + '.cnf', base + '.drup', '-L', base + '.lrat', '-t', '20000'], capture_output=True, text=True)
    dt_ok = 's VERIFIED' in p.stdout
    q = subprocess.run([CAKE, base + '.cnf', base + '.lrat'], capture_output=True, text=True,
                       env=dict(os.environ, CML_HEAP_SIZE=os.environ.get('CML_HEAP_SIZE', '2000'), CML_STACK_SIZE=os.environ.get('CML_STACK_SIZE', '500')))
    cake_ok = 's VERIFIED UNSAT' in q.stdout
    return ('VERIFIED' if dt_ok and cake_ok else f'FAIL dt={dt_ok} cake={cake_ok} {p.stdout[-200:]} {q.stdout[-200:]}'), time.time() - t0


def main():
    n, T, rundir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    mode = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 'single'
    sets = '--sets' in sys.argv
    fams = sys.argv[sys.argv.index('--fams') + 1].split(',') if '--fams' in sys.argv else ['G', 'X', 'O']
    fams = [f for f in fams if f]
    enc, base_cl, tot, N = build(n, T, fams, sets)
    lemmas = []; refused = 0
    for fn in glob.glob(f'{rundir}/blocks.w*'):
        for line in open(fn):
            w = line.split()
            if not w: continue
            if w[0] in OK_KINDS: lemmas.append([int(x) for x in w[2:]])
            else: refused += 1
    k = N - T
    card = [[-tot.rhs[k]]] if k < len(tot.rhs) else []
    od = f'{rundir}/proof'; os.makedirs(od, exist_ok=True)
    print(f'n={n} T={T} mode={mode} fams={fams} sets={sets}: {len(base_cl)} base clauses, {len(lemmas)} lemma clauses '
          f'(refused {refused} non-lemma lines), N={N}', flush=True)
    nv = enc.pool.top
    if mode == 'single':
        res, t = check(base_cl + lemmas + card, nv, f'{od}/single')
        print(f'single: {res} ({t:.1f}s)'); ok = res == 'VERIFIED'
    else:
        allp = list(partitions(n - 1, n - 1, exact=False)); keep = enc.keep(allp)
        pieces = [(i, rg) for i, rg in enumerate(allp) if keep[i]]
        if '--W' in sys.argv:
            r_, W_ = int(sys.argv[sys.argv.index('--r') + 1]), int(sys.argv[sys.argv.index('--W') + 1])
            pieces = pieces[r_::W_]
        bad = 0; tt = 0
        for idx, rg in pieces:
            extra = enc.sym_compact(rg) + enc.unit_clauses(rg)
            res, t = check(base_cl + lemmas + card + extra, nv, f'{od}/p{idx}')
            tt += t
            if res != 'VERIFIED': bad += 1; print(f'piece {idx} {rg}: {res}', flush=True)
            if '--keep' not in sys.argv:
                for ext in ('.cnf', '.drup', '.lrat'):
                    if os.path.exists(f'{od}/p{idx}{ext}'): os.remove(f'{od}/p{idx}{ext}')
        print(f'pieces: {len(pieces)} checked, {bad} not verified, {tt:.0f}s'); ok = bad == 0
    print('PROOF', 'VERIFIED (drat-trim + cake_lpr)' if ok else 'FAILED')


if __name__ == '__main__':
    main()
