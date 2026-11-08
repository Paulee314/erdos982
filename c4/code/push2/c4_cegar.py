#!/usr/bin/env python3
"""Fishburn C4 (sum of distinct distances) CEGAR: is there a strictly convex n-gon with sum_x t(x) <= BOUND?
Default BOUND = C(n,2) - 1 (a C4 counterexample).  UNSAT  =>  C4 holds at this n (modulo the soundness of the
families below, all valid in EVERY strictly convex n-gon; no S'-violator assumption anywhere).

SAT side
  base  : e982lib.Enc(n, K=n-1, order=True, atmost=True)  [E transitivity, class representatives r(c,v), F1, F2,
          LT total preorder + congruence, F2-order, chord monotonicity, four-in-a-class gap]  -- the K=n-1 bound is vacuous
  sym   : dihedral lex-leader on local literals (verbatim from testA_sat.build, sym=lex); sound because every clause
          (incl. the cardinality constraint, which depends only on the multiset of t's) is D_n-invariant and every
          learned clause is added with all 2n dihedral images (Sigma records are added as-is: each is valid by itself)
  fams  : F (angle_fams), G X O (angle_fams2).  NOT used: A/D (not in the approved list), B/B0/B1 (violator only),
          K/N of angle_fams2 (not in the approved list).
  card  : t(c) = sum_v r(c,v)  (r(c,v) <=> v is the first vertex of its class at c, so t(c) = (n-1) - sum (size-1));
          AtMost(sum_c t(c) <= BOUND) via PySAT CardEnc (kmtotalizer).
LP side (lazy, per model; exact certificates are produced afterwards by c4_certify.py)
  tier 1  Lambda equalities only;  tier 2  + K (circle) + P (bisector) + H (hinge) items;  tier 3  + strict local
  comparisons;  then Delta (chord-length LP);  then Sigma (law of sines) if sigma=1.  No MEC rows, no S literals.
Usage: c4_cegar.py n OUT.jsonl [bound=B] [preload=f1,f2] [share=f] [circ=1] [bis=1] [hinge=1] [delta=1] [sigma=0]
                   [maxcores=8] [maxcores2=16] [seed=k] [timelimit=s] [sym=lex|none]"""
import sys, os, time, json, itertools, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sat')); sys.path.insert(0, HERE)
from e982lib import Enc
from angle_fams import add_families
from angle_fams2 import add_families2
from angle_lp import AngleLP
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153
import circle_rows, hinge_rows, delta_rows
from cegar2 import norm_lit, items_infeasible, core

FAMS1 = {'F', 'A', 'D'}; FAMS2 = {'G', 'X', 'O', 'K', 'N'}   # NB: 'K' here = angle_fams2 bisector cut (SAT), not the Lambda-circle K rows


def lex_clauses(enc):
    """dihedral lex-leader, verbatim from testA_sat.build (sym=lex)"""
    n = enc.n; pool = enc.pool; cl = []
    def vec(v, o):
        return [enc.e((v + o * t) % n, (v + o * (t + a)) % n, (v + o * (t + b)) % n)
                for t in range(n) for a in range(1, n) for b in range(a + 1, n)]
    X = vec(0, 1); m = len(X)
    for v in range(n):
        for o in (1, -1):
            if (v, o) == (0, 1): continue
            Y = vec(v, o); prev = None
            for i in range(m):
                cl.append(([-prev] if prev else []) + [-X[i], Y[i]])
                if i == m - 1: break
                nxt = pool.id(('lexeq', v, o, i)); pre = [prev] if prev else []
                if prev: cl.append([-nxt, prev])
                cl += [[-nxt, -X[i], Y[i]], [-nxt, X[i], -Y[i]],
                       [nxt] + [-x for x in pre] + [X[i], Y[i]], [nxt] + [-x for x in pre] + [-X[i], -Y[i]]]
                prev = nxt
    return cl


def build_c4(n, bound, sym='lex', fams='FGXO'):
    """returns enc, clause list (base + sym + families + cardinality), reps"""
    enc = Enc(n, n - 1, order=True, atmost=True)
    cl = list(enc.clauses)
    if sym == 'lex': cl += lex_clauses(enc)
    cl += add_families(enc, FAMS1 & set(fams), violator=False)[0]
    cl += add_families2(enc, FAMS2 & set(fams))[0]
    reps = [r for c in range(n) for r in enc.REPS[c]]
    if bound is not None:
        cl += CardEnc.atmost(lits=reps, bound=bound, vpool=enc.pool, encoding=EncType.kmtotalizer).clauses
    return enc, cl, reps


def cube_clauses(enc, spec):
    """spec 'c1:a1,c2:a2' -> t(c1) = a1 and t(c2) = a2 exactly (all value combinations 1..n-1 partition the space)"""
    out = []
    for part in [x for x in spec.split(',') if x]:
        cv, ca = map(int, part.split(':'))
        out += CardEnc.equals(lits=enc.REPS[cv], bound=ca, vpool=enc.pool, encoding=EncType.seqcounter).clauses
    return out


def code_md5():
    import hashlib
    return hashlib.md5(b''.join(open(os.path.join(HERE, x), 'rb').read() for x in
                               ('c4_cegar.py', 'cegar2.py', 'angle_lp.py', 'circle_rows.py', 'hinge_rows.py', 'delta_rows.py',
                                'sigma.py', os.path.join('..', 'sat', 'e982lib.py'), os.path.join('..', 'sat', 'angle_fams.py'),
                                os.path.join('..', 'sat', 'angle_fams2.py')))).hexdigest()


def lit_var(enc, l):
    pr, LT, E = enc.pr, enc.LT, enc.E
    if l[0] == 'X':
        _, a1, b1, c1, d1, rel = l; a, b = pr(a1, b1), pr(c1, d1)
    else:
        _, u, v, w, rel = l; a, b = pr(u, v), pr(u, w)
    return E(a, b) if rel == '=' else (LT(a, b) if rel == '<' else LT(b, a))


def image(n, lits, r, o):
    g = lambda x: (r + o * x) % n
    def im(l):
        if l[0] == 'L': return norm_lit(('L', g(l[1]), g(l[2]), g(l[3]), l[4]))
        return norm_lit(('X', g(l[1]), g(l[2]), g(l[3]), g(l[4]), l[5]))
    return tuple(sorted((im(l) for l in lits), key=str))


class Refuter:
    """the LP side: given a full SAT model m, find an angle/length-infeasible literal subset (or None)"""
    def __init__(self, enc, circ=True, bis=True, hinge=True, delta=True, sigma_on=False):
        self.enc = enc; n = enc.n; self.n = n
        self.lp = AngleLP(n); self.base = self.lp.base_rows(); self.lp.build_cache(self.base)
        self.dlp = delta_rows.DeltaLP(n)
        self.circ, self.bis, self.hinge, self.delta, self.sigma_on = circ, bis, hinge, delta, sigma_on
        self.local = [(c, u, v) for c in range(n) for u, v in itertools.combinations([x for x in range(n) if x != c], 2)]

    def rel(self, m, a, b):
        E, LT = self.enc.E, self.enc.LT
        if a == b: return '='
        return '=' if E(a, b) in m else ('<' if LT(a, b) in m else '>')

    def tiers(self, m):
        """returns (cur, mitems, tier) with the LP infeasible, or None"""
        enc, lp, base = self.enc, self.lp, self.base; pr = enc.pr
        eqs = [('L', c, u, v, '=') for (c, u, v) in self.local if enc.e(c, u, v) in m]
        if items_infeasible(lp, base, eqs, []): return eqs, [], 1
        it_ = []
        relation = lambda p, x, v: self.rel(m, pr(p, x), pr(p, v))
        if self.circ:
            eq3 = [(c, u, v) for (_, c, u, v, _r) in eqs]
            extra = circle_rows.items_for(lp, eq3, relation) + (circle_rows.p_items_for(lp, eq3, relation) if self.bis else [])
            it_ += [(t, {k: float(x) for k, x in d.items()}, float(r), kd, q) for (t, d, r, kd, q) in extra]
        if self.hinge:
            it_ += hinge_rows.items_for(lp, lambda e1, e2: self.rel(m, pr(*e1), pr(*e2)))
        if it_ and items_infeasible(lp, base, eqs, it_): return eqs, it_, 2
        lts = [('L', c, u, v, self.rel(m, pr(c, u), pr(c, v))) for (c, u, v) in self.local if enc.e(c, u, v) not in m]
        if items_infeasible(lp, base, eqs + lts, it_): return eqs + lts, it_, 3
        return None

    def all_x(self, m):
        enc = self.enc; out = []
        for i, j in itertools.combinations(range(enc.NP), 2):
            out.append(norm_lit(('X',) + enc.pairs[i] + enc.pairs[j] + (self.rel(m, i, j),)))
        return out

    def delta_core(self, m):
        return delta_rows.core(self.dlp, self.all_x(m)) if self.delta else None

    def sigma_rec(self, m):
        if not self.sigma_on: return None
        import sigma
        enc = self.enc; sl = []
        for i, j in itertools.combinations(range(enc.NP), 2):
            rr = self.rel(m, i, j); p_, q_ = enc.pairs[i], enc.pairs[j]; sl.append(('X',) + p_ + q_ + (rr,))
            sh = set(p_) & set(q_)
            if sh:
                u_ = sh.pop(); v_ = p_[0] if p_[1] == u_ else p_[1]; w_ = q_[0] if q_[1] == u_ else q_[1]
                sl.append(circle_rows.norm(('L', u_, v_, w_, rr)))
        for _ in range(3):
            rec = sigma.build_and_certify(self.n, sl)
            if rec is not None: return rec
        return None


def main():
    n = int(sys.argv[1]); out = sys.argv[2]; kw = dict(a.split('=') for a in sys.argv[3:])
    bound = int(kw.get('bound', n * (n - 1) // 2 - 1)); tl = float(kw.get('timelimit', 1e18))
    hf = os.path.join(os.path.dirname(os.path.abspath(out)), 'HANDOFF')      # sub-cases reassigned to the fast pipeline
    if kw.get('cube') and os.path.exists(hf) and kw['cube'] in open(hf).read().split():
        print(f"RESULT C4 n={n} bound={bound} cube={kw['cube']}: HANDED_OFF (reassigned, see {hf})", flush=True); return
    maxcores = int(kw.get('maxcores', 8)); maxcores2 = int(kw.get('maxcores2', 16)); full2 = kw.get('full2', '1') == '1'
    t0 = time.time()
    enc, cl, reps = build_c4(n, bound, kw.get('sym', 'lex'), kw.get('fams', 'FGXO'))
    cl += cube_clauses(enc, kw.get('cube', ''))
    s = Cadical153(bootstrap_with=cl)
    R = Refuter(enc, kw.get('circ', '1') == '1', kw.get('bis', '1') == '1', kw.get('hinge', '1') == '1',
                kw.get('delta', '1') == '1', kw.get('sigma', '0') == '1')
    lp, base = R.lp, R.base
    VER = code_md5(); FAMTAG = ''.join(sorted(set(kw.get('fams', 'FGXO')))); CUBE = kw.get('cube', '')
    seen = set(); nlearn = 0; CURFAM = ['lambda']; f = open(out, 'a')
    def add(lits, write=True, images=True, rec=None):
        nonlocal nlearn
        key = tuple(sorted(map(norm_lit, lits), key=str)); new = 0
        if rec is not None:
            rec = dict(rec); rec['fam'] = 'sigma'; rec['ver'] = VER; rec['fams'] = FAMTAG; rec['n'] = n; rec['cube'] = CUBE
            if hash(key) not in seen:
                seen.add(hash(key)); s.add_clause([-lit_var(enc, l) for l in key]); nlearn += 1; new += 1
                f.write(json.dumps(rec) + '\n')
            return new
        for r in (range(n) if images else [0]):
            for o in ((1, -1) if images else (1,)):
                I = image(n, key, r, o); hI = hash(I)
                if hI in seen: continue
                seen.add(hI); s.add_clause([-lit_var(enc, l) for l in I]); nlearn += 1; new += 1
                if write and (r, o) == (0, 1): f.write(json.dumps({'lits': [list(x) for x in I], 'fam': CURFAM[0], 'ver': VER, 'fams': FAMTAG, 'n': n, 'cube': CUBE}) + '\n')
        return new
    def load_line(line):
        try: J = json.loads(line)
        except Exception: return 0
        if 'lits' not in J or any(x[0] == 'S' for x in J['lits']): return 0      # never import MEC/S'-only clauses
        return add([tuple(x) for x in J['lits']], False, images=('sigma' not in J))
    for fn in [x for x in kw.get('preload', '').split(',') if x]:
        for line in open(fn): load_line(line)
    print(f"C4 n={n} bound={bound} fams={kw.get('fams', 'FGXO')}: {len(cl)} clauses, {enc.pool.top} vars, preloaded {nlearn}; {time.time()-t0:.1f}s", flush=True)
    if kw.get('seed'):
        import random
        Rr = random.Random(int(kw['seed'])); s.set_phases([x if Rr.random() < 0.3 else -x for x in enc.lits])
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
                        ent[1] = g.tell(); k += load_line(line)
            except FileNotFoundError: pass
        return k
    it = 0; status = 'TIMEOUT'; tsat = tlp = 0.0; nfeas = 0; nsh = 0; tier_ct = {1: 0, 2: 0, 3: 0, 'delta': 0, 'sigma': 0}
    while time.time() - t0 < tl:
        it += 1
        if share: nsh += pull()
        _t = time.time(); r_ = s.solve(); tsat += time.time() - _t
        if not r_: status = 'UNSAT'; break
        _t = time.time()
        m = set(x for x in s.get_model() if x > 0)
        tsum = sum(1 for r in reps if r in m)
        res = R.tiers(m)
        if res is None:
            C = R.delta_core(m)
            if C:
                CURFAM[0] = 'delta'; add(C); CURFAM[0] = 'lambda'; f.flush(); tier_ct['delta'] += 1; tlp += time.time() - _t
                continue
            rec = R.sigma_rec(m)
            if rec is not None:
                add([tuple(x) for x in rec['lits']], rec=rec); f.flush(); tier_ct['sigma'] += 1; tlp += time.time() - _t
                continue
            nfeas += 1
            print(f"  LP-FEASIBLE model #{nfeas} (sum t = {tsum}): {enc.structure(m)}", flush=True)
            with open(out + '.feasible', 'a') as g:
                g.write(json.dumps({'pattern': enc.structure(m), 'sumt': tsum, 'ver': VER, 'fams': FAMTAG, 'cube': CUBE,
                                    'rels': {f"{enc.pairs[i]}|{enc.pairs[j]}": R.rel(m, i, j)
                                             for i, j in itertools.combinations(range(enc.NP), 2)}}) + '\n')
            if kw.get('stop_on_feasible') == '1': status = 'FEASIBLE'; break
            s.add_clause(enc.block_clause(m)); tlp += time.time() - _t; continue
        cur, mitems, tier = res; tier_ct[tier] += 1
        found = []; restL, restM = list(cur), list(mitems); k = 0; last = None
        while k < maxcores and items_infeasible(lp, base, restL, restM):
            lits, L, M = core(lp, base, restL, restM); add(lits); found.append((L, M)); k += 1; last = lits
            Ls = set(L); Ms = {x[0] for x in M}
            restL = [x for x in restL if x not in Ls]; restM = [x for x in restM if x[0] not in Ms]
        q = [(i, j) for i, (L, M) in enumerate(found) for j in range(len(L) + len(M))]; k2 = 0
        while q and k2 < maxcores2:
            i, j = q.pop(0); L, M = found[i]
            if j < len(L): drop = L[j]; L2 = [x for x in cur if x != drop]; M2 = mitems
            else: drop = M[j - len(L)][0]; L2 = cur; M2 = [x for x in mitems if x[0] != drop]
            if not items_infeasible(lp, base, L2, M2): continue
            lits, L3, M3 = core(lp, base, L2, M2, full=full2)
            if add(lits): k2 += 1; found.append((L3, M3))
        f.flush(); tlp += time.time() - _t
        if it % 10 == 0:
            print(f"  it {it}: learned {nlearn} (last {len(last) if last else 0} lits), sum t {tsum}, tiers {tier_ct}, "
                  f"feasible {nfeas}, shared {nsh}, {time.time()-t0:.0f}s (sat {tsat:.0f}s, lp {tlp:.0f}s)", flush=True)
    print(f"RESULT C4 n={n} bound={bound} cube={kw.get('cube','-')}: {status}; learned {nlearn}, feasible {nfeas}, it {it}, tiers {tier_ct}, "
          f"{time.time()-t0:.1f}s (sat {tsat:.0f}s, lp {tlp:.0f}s)", flush=True)


if __name__ == '__main__': main()
