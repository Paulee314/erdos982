#!/usr/bin/env python3
"""CEGAR with Lambda + Lambda-MEC. SAT side: testA_sat.build (base + S' windows + lex-leader) + families (default BF;
B gives the MEC support selectors s_v, valid for S'-violators). LP side: angle rows of angle_lp + L rows for the model's
local distance relations + MEC rows (mec_rows) implied by the model's support literals.
A learned clause is a set of literals: ('L',u,v,w,rel) and ('S',v,bool). Its LP = base + L rows + every MEC row whose
required support literals are all in the set (rows_for_lits). Records: {'lits': [...]} (+ 'cert' when certified).
Usage: cegar2.py n OUT.jsonl [fams=BF] [preload=f1,f2] [share=f] [maxcores=8] [maxcores2=16] [seed=k] [timelimit=s]"""
import sys, os, time, json, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
from testA_sat import build
from angle_fams import add_families
from angle_fams2 import add_families2
from angle_lp import AngleLP, farkas
import mec_rows, circle_rows, hinge_rows, delta_rows, sigma
from pysat.solvers import Cadical153

FL = {'<': '>', '>': '<', '=': '='}
HINGE_IN_ROWS = True


def norm_lit(l):
    if l[0] == 'X':
        return hinge_rows.xlit((l[1], l[2]), (l[3], l[4]), l[5])
    if l[0] == 'L':
        _, u, v, w, r = l
        return ('L', u, v, w, r) if v < w else ('L', u, w, v, FL[r])
    return ('S', l[1], bool(l[2]))


def rows_for_lits(lp, base, lits):
    """rows = base + L rows + all MEC rows derivable from the S literals (partial support knowledge)"""
    n = lp.n; rows = list(base)
    sl = {l[1]: l[2] for l in lits if l[0] == 'S'}
    for l in lits:
        if l[0] == 'L':
            d, r, k = lp.lit_row(l[1], l[2], l[3], l[4]); rows.append((d, r, k, l))
    T = sorted(v for v, b in sl.items() if b)
    if len(T) >= 2:
        # items_for needs a full indicator; emulate: generate with sup = known-true, then keep rows whose reqs hold
        sup = [sl.get(v) is True for v in range(n)]
        for tag, d, rhs, kind, reqs in mec_rows.items_for(lp, sup):
            if all(sl.get(v) is b for v, b in reqs):
                rows.append((d, rhs, kind, tag))
        # R rows need 'no support inside': items_for only emits them when no known-true support is inside; the reqs
        # check above then demands every inside vertex be known false.
    if any(l[0] == 'X' for l in lits) or HINGE_IN_ROWS:
        rows.extend(hinge_rows.rows_from_lits(lp, lits))
    Ls = {l for l in lits if l[0] == 'L'}
    for l in Ls:
        if l[4] != '=': continue
        _, p, a, b, _r = l
        for x in (a, b):
            for v in range(n):
                if v in (p, a, b): continue
                for rel in ('<', '=', '>'):
                    q = circle_rows.norm(('L', p, x, v, rel))
                    if q in Ls:
                        inside = {'>': 'in', '=': 'on', '<': 'out'}[rel]
                        d, rhs, kind = circle_rows.k_row(lp, p, a, b, v, inside)
                        rows.append((d, rhs, kind, ('K', p, a, b, v, x, rel)))
            for v in range(n):
                if v in (p, a, b): continue
                for rel in ('<', '=', '>'):
                    if circle_rows.norm(('L', v, a, b, rel)) in Ls:
                        d, rhs, kind = circle_rows.p_row(lp, p, a, b, v, rel)
                        rows.append((d, rhs, kind, ('P', p, a, b, v, rel)))
    return rows


def infeasible(lp, base, lits):
    tm, _ = lp.solve(rows_for_lits(lp, base, lits), want_dual=False)
    return tm <= 1e-9


def lp_of_items(lp, base, eqlts, mitems):
    rows = list(base)
    for l in eqlts:
        d, r, k = lp.lit_row(l[1], l[2], l[3], l[4]); rows.append((d, r, k, ('LIT', l)))
    for tag, d, rhs, kind, reqs in mitems: rows.append((d, rhs, kind, ('MEC', tag, tuple(reqs))))
    return rows


def items_infeasible(lp, base, eqlts, mitems):
    tm, _ = lp.solve(lp_of_items(lp, base, eqlts, mitems), want_dual=False)
    return tm <= 1e-9


def core(lp, base, eqlts, mitems, full=True):
    """infeasible subset of (L literals, MEC/K items) -> literal set; full=True: deletion-minimal"""
    rows = lp_of_items(lp, base, eqlts, mitems); nb = len(base)
    du = farkas(lp, rows)
    if du is None:
        _, du = lp.solve(rows); du = du or {}
    sel = [i - nb for i, y in du.items() if i >= nb and abs(y) > 1e-11]
    L = [eqlts[i] for i in sel if i < len(eqlts)]; M = [mitems[i - len(eqlts)] for i in sel if i >= len(eqlts)]
    if not items_infeasible(lp, base, L, M): L, M = list(eqlts), list(mitems)
    if not full:
        lits = set(L)
        for tag, d, rhs, kind, reqs in M:
            for r in reqs: lits.add(('S', r[0], r[1]) if len(r) == 2 else r)
        return sorted(lits, key=str), L, M
    i = 0
    while i < len(L):
        if items_infeasible(lp, base, L[:i] + L[i + 1:], M): L = L[:i] + L[i + 1:]
        else: i += 1
    i = 0
    while i < len(M):
        if items_infeasible(lp, base, L, M[:i] + M[i + 1:]): M = M[:i] + M[i + 1:]
        else: i += 1
    lits = set(L)
    for tag, d, rhs, kind, reqs in M:
        for r in reqs: lits.add(('S', r[0], r[1]) if len(r) == 2 else r)
    return sorted(lits, key=str), L, M


def main():
    n = int(sys.argv[1]); out = sys.argv[2]; kw = dict(a.split('=') for a in sys.argv[3:])
    fams = set(kw.get('fams', 'BF')); tl = float(kw.get('timelimit', 1e18))
    maxcores = int(kw.get('maxcores', 8)); use_circ = kw.get('circ', '0') == '1'; full2 = kw.get('full2', '1') == '1'; use_bis = kw.get('bis', '0') == '1'; tiered = kw.get('tiered', '1') == '1'; do_shrink = kw.get('shrink', '0') == '1'; use_hinge = kw.get('hinge', '0') == '1'; use_delta = kw.get('delta', '0') == '1'; use_sigma = kw.get('sigma', '0') == '1'; nsigma = 0; ndelta = 0; dlp = delta_rows.DeltaLP(n); maxcores2 = int(kw.get('maxcores2', 16))
    t0 = time.time()
    enc, _, _ = build(n, 'S', 'lex')
    extra, V = add_families(enc, fams & set('ABDF'), violator=True)
    extra += add_families2(enc, fams & set('KNGXO'))[0]
    s = Cadical153(bootstrap_with=enc.clauses + extra)
    pr, LT, E = enc.pr, enc.LT, enc.E; S = V['s']
    lp = AngleLP(n); base = lp.base_rows(); lp.build_cache(base)
    def var(l):
        if l[0] == 'S': return S[l[1]] if l[2] else -S[l[1]]
        if l[0] == 'X':
            _, a1, b1, c1, d1, rel = l; a, b = pr(a1, b1), pr(c1, d1)
            return E(a, b) if rel == '=' else (LT(a, b) if rel == '<' else LT(b, a))
        _, u, v, w, rel = l; a, b = pr(u, v), pr(u, w)
        return E(a, b) if rel == '=' else (LT(a, b) if rel == '<' else LT(b, a))
    seen = set(); nlearn = 0; CURFAM = ['lambda']; SIGLIT = {}; SIGCNT = [0]
    cegar2_norm = norm_lit
    def image(lits, r, o):
        g = lambda x: (r + o * x) % n
        def im(l):
            if l[0] == 'L': return norm_lit(('L', g(l[1]), g(l[2]), g(l[3]), l[4]))
            if l[0] == 'X': return norm_lit(('X', g(l[1]), g(l[2]), g(l[3]), g(l[4]), l[5]))
            return ('S', g(l[1]), l[2])
        return tuple(sorted((im(l) for l in lits), key=str))
    import hashlib
    VER = hashlib.md5(b''.join(open(os.path.join(HERE, x), 'rb').read() for x in
                               ('cegar2.py', 'angle_lp.py', 'mec_rows.py', 'circle_rows.py', 'hinge_rows.py', 'delta_rows.py', 'sigma.py'))).hexdigest()[:12]
    f = open(out, 'a')
    def add(lits, write=True, images=True, rec=None):
        nonlocal nlearn
        key = tuple(sorted(map(norm_lit, lits), key=str)); new = 0
        if rec is not None:            # certified record (e.g. Sigma): base clause only, record written verbatim
            rec = dict(rec); rec['fam'] = 'sigma'; rec['ver'] = VER
            h = hash(key)
            if h not in seen:
                seen.add(h); s.add_clause([-var(l) for l in key]); nlearn += 1; new += 1
                f.write(json.dumps(rec) + '\n')
            return new
        for r in (range(n) if images else [0]):
            for o in ((1, -1) if images else (1,)):
                I = image(key, r, o); hI = hash(I)
                if hI in seen: continue
                seen.add(hI); s.add_clause([-var(l) for l in I]); nlearn += 1; new += 1
                if write and (r, o) == (0, 1): f.write(json.dumps({'lits': [list(x) for x in I], 'fam': CURFAM[0], 'ver': VER}) + '\n')
        return new
    for fn in [x for x in kw.get('preload', '').split(',') if x]:
        for line in open(fn):
            try: J = json.loads(line)
            except Exception: continue
            if 'lits' in J: add([tuple(x) for x in J['lits']], False, images=('sigma' not in J))
            elif 'core' in J: add([('L',) + tuple(x) for x in J['core']], False)
            if 'sigma' in J:
                SIGCNT[0] += 1
                for l in {norm_lit(tuple(x)) for x in J['lits']}: SIGLIT[l] = SIGLIT.get(l, 0) + 1
    if kw.get('assume'):
        sys.path.insert(0, os.path.join(HERE, '..', 'sat')); from patutil import eqset
        for (c, u, v) in eqset(open(kw['assume']).read(), n): s.add_clause([enc.e(c, u, v)])
    print(f"n={n} fams={''.join(sorted(fams))}: {len(enc.clauses)+len(extra)} clauses, preloaded {nlearn}; "
          f"{time.time()-t0:.0f}s", flush=True)
    if kw.get('seed'):
        import random
        R = random.Random(int(kw['seed'])); s.set_phases([x if R.random() < 0.3 else -x for x in enc.lits])
    share = [[fn, 0] for fn in kw.get('share', '').split(',') if fn]
    def pull():
        k = 0
        for ent in share:
            try:
                with open(ent[0]) as g:
                    g.seek(ent[1])
                    while True:
                        line = g.readline()
                        if not line or not line.endswith('\n'): break
                        ent[1] = g.tell()
                        J = json.loads(line)
                        if 'lits' in J: k += add([tuple(x) for x in J['lits']], False, images=('sigma' not in J))
                        elif 'core' in J: k += add([('L',) + tuple(x) for x in J['core']], False)
            except FileNotFoundError: pass
        return k
    local = [(c, u, v) for c in range(n) for u, v in itertools.combinations([x for x in range(n) if x != c], 2)]
    it = 0; status = 'TIMEOUT'; tsat = tlp = 0.0; nfeas = 0; nsh = 0
    while time.time() - t0 < tl:
        it += 1
        if share: nsh += pull()
        _t = time.time(); r_ = s.solve(); tsat += time.time() - _t
        if not r_: status = 'UNSAT'; break
        _t = time.time()
        m = set(x for x in s.get_model() if x > 0)
        if do_shrink:
            lits_all = enc.lits; cur0 = [x for x in lits_all if x in m]
            while True:
                cs = set(cur0); off = [-x for x in lits_all if x not in cs]
                sel = enc.pool.id(('shrink2', it, len(cur0))); s.add_clause([-sel] + [-x for x in cur0])
                if s.solve(assumptions=off + [sel]):
                    mm = set(x for x in s.get_model() if x > 0); cur0 = [x for x in lits_all if x in mm]; m = mm
                else:
                    s.add_clause([-sel]); break
        sup = [S[v] in m for v in range(n)]
        eqs = [('L', c, u, v, '=') for (c, u, v) in local if enc.e(c, u, v) in m]
        mec_items = mec_rows.items_for(lp, sup)
        def relation(p, x, v):
            a, b = pr(p, x), pr(p, v)
            return '=' if E(a, b) in m else ('<' if LT(a, b) in m else '>')
        def full_items():
            it_ = list(mec_items)
            if use_circ:
                eq3 = [(c, u, v) for (_, c, u, v, _r) in eqs]
                extra = circle_rows.items_for(lp, eq3, relation) + (circle_rows.p_items_for(lp, eq3, lambda v, a, b: relation(v, a, b)) if use_bis else [])
                it_ += [(t, {k: float(x) for k, x in d.items()}, float(r), kd, q) for (t, d, r, kd, q) in extra]
            if use_hinge:
                def rel_of(e1, e2):
                    a, b = pr(*e1), pr(*e2)
                    if a == b: return '='
                    return '=' if E(a, b) in m else ('<' if LT(a, b) in m else '>')
                it_ += hinge_rows.items_for(lp, rel_of)
            return it_
        # tiers: (1) equalities only, (2) + MEC rows, (3) + strict comparisons + circle/bisector rows
        cur = None; mitems = []
        if tiered and items_infeasible(lp, base, eqs, []): cur, mitems = eqs, []
        elif tiered and items_infeasible(lp, base, eqs, mec_items): cur, mitems = eqs, mec_items
        else:
            mitems = full_items()
            if items_infeasible(lp, base, eqs, mitems): cur = eqs
            else:
                lts = [('L', c, u, v, '<' if LT(pr(c, u), pr(c, v)) in m else '>') for (c, u, v) in local if enc.e(c, u, v) not in m]
                if items_infeasible(lp, base, eqs + lts, mitems): cur = eqs + lts
        if cur is None and use_delta:
            allx = []
            for i, j in itertools.combinations(range(enc.NP), 2):
                rr = '=' if E(i, j) in m else ('<' if LT(i, j) in m else '>')
                allx.append(norm_lit(('X',) + enc.pairs[i] + enc.pairs[j] + (rr,)))
            C = delta_rows.core(dlp, allx)
            if C:
                CURFAM[0] = 'delta'; add(C); CURFAM[0] = 'lambda'; f.flush(); ndelta += 1
                tlp += time.time() - _t
                print(f"  it {it}: DELTA core {len(C)} lits (delta clauses {ndelta})", flush=True)
                continue
        if cur is None and use_sigma:
            sl = []
            for i, j in itertools.combinations(range(enc.NP), 2):
                rr = '=' if E(i, j) in m else ('<' if LT(i, j) in m else '>')
                p_, q_ = enc.pairs[i], enc.pairs[j]; sl.append(('X',) + p_ + q_ + (rr,))
                sh = set(p_) & set(q_)
                if sh:
                    u_ = sh.pop(); v_ = p_[0] if p_[1] == u_ else p_[1]; w_ = q_[0] if q_[1] == u_ else q_[1]
                    sl.append(circle_rows.norm(('L', u_, v_, w_, rr)))
            rec = None
            # generalization: first try the model's literals restricted to those frequent in earlier Sigma clauses
            if SIGCNT[0] >= 5:
                slset = set(sl)
                for frac in (0.75, 0.5):
                    common = {l for l, c in SIGLIT.items() if c >= frac * SIGCNT[0]}
                    sub = [l for l in sl if l in common]
                    if len(sub) >= 20 and len(sub) < len(sl):
                        rec = sigma.build_and_certify(n, sub)
                        if rec is not None: break
            for attempt in range(3 if rec is None else 0):   # HiGHS is not fully deterministic: retry before giving up
                rec = sigma.build_and_certify(n, sl)
                if rec is not None: break
            if rec is not None:
                SIGCNT[0] += 1
                for l in {cegar2_norm(tuple(x)) for x in rec['lits']}: SIGLIT[l] = SIGLIT.get(l, 0) + 1
            if rec is not None:
                add([tuple(x) for x in rec['lits']], rec=rec); f.flush(); nsigma += 1
                tlp += time.time() - _t
                print(f"  it {it}: SIGMA clause {len(rec['lits'])} lits (sigma clauses {nsigma})", flush=True)
                continue
        if cur is None:
            nfeas += 1; print(f"  ANGLE+MEC-FEASIBLE model #{nfeas}: {enc.structure(m)} supp={[v for v in range(n) if sup[v]]}", flush=True)
            try:
                rels = {}
                for i, j in itertools.combinations(range(enc.NP), 2):
                    rels[f"{enc.pairs[i]}|{enc.pairs[j]}"] = '=' if E(i, j) in m else ('<' if LT(i, j) in m else '>')
                with open(out + '.feasible', 'a') as g:
                    g.write(json.dumps({'pattern': enc.structure(m), 'supp': [v for v in range(n) if sup[v]], 'rels': rels}) + '\n')
            except Exception as ex_:
                print('  (could not dump model)', ex_)
            if kw.get('stop_on_feasible') == '1': status = 'FEASIBLE'; break
            s.add_clause(enc.block_clause(m) + [(-S[v] if sup[v] else S[v]) for v in range(n)])
            tlp += time.time() - _t; continue
        found = []; restL, restM = list(cur), list(mitems); k = 0; last = None
        while k < maxcores and items_infeasible(lp, base, restL, restM):
            lits, L, M = core(lp, base, restL, restM); add(lits); found.append((L, M)); k += 1; last = lits
            Ls = set(L); Ms = {x[0] for x in M}
            restL = [x for x in restL if x not in Ls]; restM = [x for x in restM if x[0] not in Ms]
        q = [(i, j) for i, (L, M) in enumerate(found) for j in range(len(L) + len(M))]; k2 = 0
        while q and k2 < maxcores2:
            i, j = q.pop(0); L, M = found[i]
            if j < len(L):
                drop = L[j]; L2 = [x for x in cur if x != drop]; M2 = mitems
            else:
                drop = M[j - len(L)][0]; L2 = cur; M2 = [x for x in mitems if x[0] != drop]
            if not items_infeasible(lp, base, L2, M2): continue
            lits, L3, M3 = core(lp, base, L2, M2, full=full2)
            if add(lits): k2 += 1; found.append((L3, M3))
        f.flush(); tlp += time.time() - _t
        if it % 5 == 0:
            ns = sum(1 for l in last if l[0] == 'S') if last else 0
            print(f"  it {it}: learned {nlearn} (last {len(last) if last else 0} lits, {ns} support), feasible {nfeas}, "
                  f"shared {nsh}, {time.time()-t0:.0f}s (sat {tsat:.0f}s, lp {tlp:.0f}s)", flush=True)
    print(f"RESULT n={n} fams={''.join(sorted(fams))}: {status}; learned {nlearn}, feasible {nfeas}, it {it}, "
          f"{time.time()-t0:.1f}s", flush=True)


if __name__ == '__main__': main()
