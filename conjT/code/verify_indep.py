#!/usr/bin/env python3
"""INDEPENDENT re-check of an apex_pieces.py run after certify.py / big_cores.py / big_viacore.py (written 3 Nov 2026 for
the n = 11, L = 6 audit).  Shares no code with alg_sat.py, certify.py, check_run.py or sympy:
  (1) every certificate file certs_k<k>_r<r>/cert_<j>.txt is parsed with an own parser (exact Fractions) and the identity
      sum_i c_i * f_i == g^m is re-expanded with own dict-polynomial arithmetic, where f_i are rebuilt from the pattern line
      (x0 = (0,0), x1 = (1,0); f = d(c,u)^2 - d(c,v)^2 for consecutive members of each class), and (pairs, m) are read
      from the certify log line (g = prod of d_ij^2 over the pairs);
  (2) every model in w*.models blocked by a library core ('new'/'hit') CONTAINS that core: an injective vertex map from the
      certified representative (cores_k<k>.txt line with that key) into the model is found by backtracking such that every
      equality of the representative maps to an equality of the model;
  (3) every 'big' model's pattern is in big_all.txt and CONTAINS the certified sub-core recorded for it in big_cores_r*.txt
      (same embedding test, representative = cores_k<k>.txt line with that key / pattern), and that certificate is VERIFIED by (1);
  (4) done files: piece indices distinct, count printed.
usage: verify_indep.py outdir n"""
import sys, os, glob, re, ast, json, collections
from fractions import Fraction
outdir, N = sys.argv[1], int(sys.argv[2])

def classes(line):
    """pattern line -> list over centres of list of classes (lists of vertices), class order = first appearance"""
    parts = line.split(); n = len(parts); out = []
    for c in range(n):
        others = [v for v in range(n) if v != c]; assert len(parts[c]) == n - 1
        g = {}
        for v, ch in zip(others, parts[c]): g.setdefault(ch, []).append(v)
        out.append(list(g.values()))
    return out

# ---- polynomials: dict {exponent tuple: Fraction}, variables x2..x_{k-1}, y2..y_{k-1}
def var_index(k):
    names = [f'x{i}' for i in range(2, k)] + [f'y{i}' for i in range(2, k)]
    return {nm: t for t, nm in enumerate(names)}, len(names)
def padd(a, b, s=1):
    r = dict(a)
    for m, c in b.items():
        v = r.get(m, 0) + s * c
        if v: r[m] = v
        else: r.pop(m, None)
    return r
def pmul(a, b):
    r = {}
    for m1, c1 in a.items():
        for m2, c2 in b.items():
            m = tuple(x + y for x, y in zip(m1, m2)); v = r.get(m, 0) + c1 * c2
            if v: r[m] = v
            else: r.pop(m, None)
    return r
def lin(k, i, comp):
    """coordinate comp (0 = x, 1 = y) of point i as a polynomial"""
    vi, nv = var_index(k); z = tuple([0] * nv)
    if i == 0: return {}
    if i == 1: return {z: Fraction(1)} if comp == 0 else {}
    e = [0] * nv; e[vi[('x' if comp == 0 else 'y') + str(i)]] = 1; return {tuple(e): Fraction(1)}
def dist2(k, a, b):
    r = {}
    for comp in (0, 1):
        d = padd(lin(k, a, comp), lin(k, b, comp), -1); r = padd(r, pmul(d, d))
    return r
def gens(line):
    k = len(line.split()); out = []
    for c, cls in enumerate(classes(line)):
        for g in cls:
            for v in g[1:]: out.append(padd(dist2(k, c, g[0]), dist2(k, c, v), -1))
    return out
TERM = re.compile(r'[+-]?[^+-]+')
def parse(txt, k):
    vi, nv = var_index(k); r = {}
    txt = txt.strip().replace(' ', '')
    if txt in ('', '0'): return {}
    assert '(' not in txt and 'e' not in txt.replace('y', '').replace('x', ''), txt[:80]
    for t in TERM.findall(txt):
        sign = -1 if t[0] == '-' else 1; t = t.lstrip('+-'); coef = Fraction(sign); e = [0] * nv
        for f in t.split('*'):
            if f[0] in 'xy':
                nm, _, p = f.partition('^'); e[vi[nm]] += int(p) if p else 1
            else:
                coef *= Fraction(f)
        m = tuple(e); v = r.get(m, 0) + coef
        if v: r[m] = v
        else: r.pop(m, None)
    return r

# ---- (1) certificates
cert_ok = {}          # (k, ident) -> True/False
nterms_tot = 0; ncert = 0; bad = []
for lg in sorted(glob.glob(f'{outdir}/certify_k*_r*.log')):
    m_ = re.search(r'certify_k(\w+)_r(\d+)\.log$', lg); kk, r = m_.group(1), m_.group(2)
    chunk = [l for l in open(f'{outdir}/chunk_k{kk}_r{r}.txt') if l.strip()]
    loglines = [l for l in open(lg) if l.startswith('pattern ')]
    if len(loglines) != len(chunk): bad.append(f'{lg}: {len(loglines)} log lines vs {len(chunk)} chunk lines'); continue
    for j, (ll, cl) in enumerate(zip(loglines, chunk)):
        ident = ll.split(' ', 2)[2].split(':', 1)[0].strip()
        cid = ('key ' + cl.split('key', 1)[1].strip()) if 'key' in cl else ('pat ' + cl.split('|')[0].strip())
        if ident != cid: bad.append(f'{lg} line {j}: ident mismatch'); continue
        pat = cl.split('|')[0].strip(); k = len(pat.split())
        pairs = ast.literal_eval(re.search(r'saturation pairs (\[[^\]]*\])', ll).group(1)); m = int(re.search(r'certificate g\^(\d+)', ll).group(1))
        cf = f'{outdir}/certs_k{kk}_r{r}/cert_{j}.txt'
        F = gens(pat); C = [parse(s, k) for s in open(cf).read().strip().split('\n')]
        ok = len(C) == len(F) and 'VERIFIED' in ll
        if ok:
            tot = {}
            for c, f in zip(C, F): tot = padd(tot, pmul(c, f))
            vi, nv = var_index(k); g = {tuple([0] * nv): Fraction(1)}
            for (a, b) in pairs: g = pmul(g, dist2(k, a, b))
            gm = {tuple([0] * nv): Fraction(1)}
            for _ in range(m): gm = pmul(gm, g)
            ok = padd(tot, gm, -1) == {}
        nterms_tot += sum(len(c) for c in C); ncert += 1
        cert_ok[(int(kk) if kk.isdigit() else kk, ident)] = ok
        if not ok: bad.append(f'{cf}: identity FAILS')
print(f'(1) certificates re-expanded: {ncert}, identity holds: {sum(cert_ok.values())}, failures: {ncert - sum(cert_ok.values())}; '
      f'total cofactor terms {nterms_tot}; by k {dict(collections.Counter(k for k, _ in cert_ok))}')

# ---- embedding test
def eq_set(line):
    S = set()
    for c, cls in enumerate(classes(line)):
        for g in cls:
            for a in g:
                for b in g:
                    if a < b: S.add((c, a, b))
    return S
def embeds(small, big):
    """injective map phi: vertices of small -> vertices of big with every equality of small mapped into big's"""
    k = len(small.split()); n = len(big.split()); Es = eq_set(small); Eb = eq_set(big)
    order = sorted(range(k), key=lambda v: -sum(v in t for t in Es))
    cons = {v: [t for t in Es if v in t] for v in range(k)}
    phi = {}
    def ok_with(v):
        for (c, a, b) in cons[v]:
            if c in phi and a in phi and b in phi:
                x, y = sorted((phi[a], phi[b]))
                if (phi[c], x, y) not in Eb: return False
        return True
    def rec(i):
        if i == k: return True
        v = order[i]
        for w in range(n):
            if w in phi.values(): continue
            phi[v] = w
            if ok_with(v) and rec(i + 1): return True
            del phi[v]
        return False
    return dict(phi) if rec(0) else None

rep = {}                                   # (k, ident) -> representative pattern (certified)
for fn in glob.glob(f'{outdir}/cores_k*.txt'):
    for l in open(fn):
        pat = l.split('|')[0].strip(); k = len(pat.split())
        ident = ('key ' + l.split('key', 1)[1].strip()) if 'key' in l else ('pat ' + pat)
        rep[(k, ident)] = pat
# ---- (2) models blocked by library cores; (3) big models
bigall = set(l.split('|')[0].strip() for l in open(f'{outdir}/big_all.txt') if l.strip())
bigcore = {}
for fn in glob.glob(f'{outdir}/big_cores_r*.txt'):
    for l in open(fn):
        core, rest = l.split(' | ', 1); pat = rest.split(' pat ', 1)[1].split(' k ', 1)[0].strip()
        k = int(rest.split(' k ', 1)[1].split()[0]); key = rest.split(' key ', 1)[1].strip()
        bigcore[pat] = (k, ('key ' + key) if key != 'None' else ('pat ' + core.strip()))
n_core = n_big = 0; fails = []
for fn in sorted(glob.glob(f'{outdir}/w*.models')):
    for l in open(fn):
        pat, rest = l.split('|'); pat = pat.strip(); w = rest.split(); kind = w[2]
        if kind in ('new', 'hit'):
            info = ast.literal_eval(rest[rest.index('('):].split(' t=')[0].strip())
            k, key = info[0], list(map(tuple, info[-1])); ident = 'key ' + str(key)
            r_ = rep.get((k, ident))
            if r_ is None or not cert_ok.get((k, ident)) or embeds(r_, pat) is None: fails.append(('core', pat))
            n_core += 1
        elif kind == 'big':
            if pat not in bigall or pat not in bigcore: fails.append(('big-missing', pat)); continue
            k, ident = bigcore[pat]; r_ = rep.get((k, ident))
            if r_ is None or not cert_ok.get((k, ident)) or embeds(r_, pat) is None: fails.append(('big', pat))
            n_big += 1
        else:
            fails.append((kind, pat))
print(f'(2)+(3) models: {n_core} blocked by library cores, {n_big} big; each contains a certified core (embedding found, '
      f'certificate re-expanded): {n_core + n_big - len(fails)}; failures {len(fails)}')
for f in fails[:20]: print('   FAIL', f)
# ---- (4) done files
idx = collections.Counter()
for fn in glob.glob(f'{outdir}/w*.done'):
    for l in open(fn): idx[int(l.split()[0])] += 1
print(f'(4) done records: {sum(idx.values())}, distinct pieces {len(idx)}, duplicated {sum(1 for c in idx.values() if c > 1)}')
for b in bad[:20]: print('   PROBLEM', b)
print('INDEPENDENT CHECK', 'PASS' if not fails and not bad and all(cert_ok.values()) else 'FAIL')
