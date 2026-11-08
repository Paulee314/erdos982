#!/usr/bin/env python3
"""I_conv(n) upper bound by SAT + CEGAR (Erdos #982 machinery run in reverse).

Encoding: e982lib.Enc(n, n-1, order=True, atmost=True)  [E transitivity, F1, F2, strict total preorder LT, F2-order,
chord monotonicity, four-in-a-class gap; the class bound n-1 is vacuous]  + families G, X, O (fams_v2, valid in every
strictly convex polygon)  + GLOBAL cardinality  sum_{c, u<v} e(c,u,v) >= T   (= Z(P) >= T; each pair {u,v} in one
distance class at c is one isosceles triangle with apex c; an equilateral triangle gives 3 such triples).
Cardinality: incremental totalizer on the negated literals (at most N-T of them true).
Cover: pieces = restricted-growth strings pi of vertex 0's partition (all block counts), mirror-skipped, with the
dihedral lex-leader sym_compact(pi) (the reviewed T* cover; Z is dihedrally invariant so the cover stays complete).

CEGAR per model: (1) Lambda (exact Farkas cert) -> block core literals; (2) Singular core (library / new, Q-confirmed)
-> block positive core; (3) whole-pattern Singular with distinctness saturation (QCONFIRM=1: Q verdict) -> block
positive set; (4) numeric realisation (LM with strict-convexity penalty, then polish) -> if a strictly convex polygon
with all the model's equalities is found, its true Z (>= T) becomes the new lower bound and T := Z+1 for all later
solves (earlier UNSAT pieces stay UNSAT: monotone); (5) else SURVIVOR: recorded and full-blocked (the final upper
bound is then NOT claimed unless every survivor is resolved).
usage: iconv_sat.py n T0 outdir [--pieces a:b] [--r r --W W]"""
import sys, os, time, json, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
os.environ.setdefault('QCONFIRM', '1')
import apex_pieces_v1 as v1
from e982lib import Enc, partitions
import fams_v2
from lambda_v2 import LambdaFilter
from pysat.card import ITotalizer
from pysat.solvers import Cadical153
import realise
SETS_STRONG = os.environ.get('SETS_STRONG', '1') == '1'


class IWorker(v1.Worker):
    def __init__(self, n, T0, outdir, fams=('G', 'X', 'O'), lam=True, tag='', sets=False, allmax=False, cover='lex'):
        self.n, self.outdir, self.nocore = n, outdir, False
        self.cover = cover
        self.sets, self.allmax = sets, allmax
        self.r = tag
        os.makedirs(outdir, exist_ok=True)
        enc = Enc(n, n - 1, order=True, atmost=True); self.enc = enc
        cl, self.famvars, self.famcounts = fams_v2.add_tstar_families(enc, list(fams))
        enc.clauses += cl
        if sets:     # objective = number of isosceles triangles as vertex sets: iso(abc) -> e(a;b,c) v e(b;a,c) v e(c;a,b)
            self.obj = []
            for a, b, c in itertools.combinations(range(n), 3):
                iv = enc.pool.id(('iso', a, b, c)); self.obj.append(iv)
                enc.clauses.append([-iv, enc.e(a, b, c), enc.e(b, a, c), enc.e(c, a, b)])
                if SETS_STRONG:      # definitional reverse direction (iso <-> OR); sound, only adds propagation
                    for x in (enc.e(a, b, c), enc.e(b, a, c), enc.e(c, a, b)): enc.clauses.append([-x, iv])
        else:        # objective = Z = number of true local literals e(c;u,v)
            self.obj = list(enc.lits)
        self.N = len(self.obj)
        top = enc.pool.top
        self.tot = ITotalizer(lits=[-l for l in self.obj], ubound=max(0, self.N - T0), top_id=top)
        enc.pool.occupy(top + 1, self.tot.top_id)
        enc.pool.top = self.tot.top_id
        extra = []
        self.ztot = None
        if sets and SETS_STRONG:   # redundant: Z >= T_sets always (Z = T_sets + 2 #equilateral)
            tp = enc.pool.top
            self.ztot = ITotalizer(lits=[-l for l in enc.lits], ubound=max(0, len(enc.lits) - T0), top_id=tp)
            enc.pool.occupy(tp + 1, self.ztot.top_id); enc.pool.top = self.ztot.top_id; extra += self.ztot.cnf.clauses
        if cover == 'apex':      # per-vertex counters: Z_c <= A is assumed per piece (vertex 0 = a vertex of max Z_c)
            self.vtot = []
            for c in range(n):
                lc = [enc.e(c, u, v) for u in range(n) for v in range(u + 1, n) if c not in (u, v)]
                tp = enc.pool.top
                tt = ITotalizer(lits=lc, ubound=len(lc), top_id=tp)
                enc.pool.occupy(tp + 1, tt.top_id); enc.pool.top = tt.top_id
                self.vtot.append(tt); extra += tt.cnf.clauses
        self.solver = Cadical153(bootstrap_with=enc.clauses + self.tot.cnf.clauses + extra)
        self.local_index = {t: i for i, t in enumerate(enc.local)}
        self.lib = {}; self.libinv = set(); self.load_lib()
        self.T = T0
        self.lf = LambdaFilter(enc) if lam else None
        self.vtag = fams_v2.version_tag(list(fams), lam)
        o = lambda name, m='a': open(f'{outdir}/{name}{tag}', m)
        self.fdone, self.fcores, self.fmodels = o('done'), o('cores'), o('models')
        self.fbig, self.fsurv, self.flam, self.freal = o('big'), o('surv'), o('lambda'), o('realised')
        self.fblocks = o('blocks')      # every learned clause: kind piece lits... (for the DRUP re-check)
        self.stats = dict(models=0, newcores=0, big=0, surv=0, hits=0, lam=0, real=0)
        self.sync_T()
        self.done = set()
        for fn in os.listdir(outdir):        # resume: a piece done at T_d is UNSAT for every T >= T_d
            if fn.startswith('done'):
                for line in open(f'{outdir}/{fn}'):
                    w = line.split()
                    if w and int(w[2]) <= self.T: self.done.add(int(w[0]))

    def sync_T(self):
        if self.allmax: return
        for fn in os.listdir(self.outdir):        # best realised so far (any worker)
            if fn.startswith('realised'):
                for line in open(f'{self.outdir}/{fn}'):
                    if line.strip():
                        d = json.loads(line); self.T = max(self.T, d.get('obj', d['Z']) + 1)

    def load_lib(self):
        import glob
        for fn in glob.glob(f'{self.outdir}/cores*'):
            for line in open(fn):
                try: d = json.loads(line)
                except Exception: continue
                key = tuple(map(tuple, d['key']))
                if key not in self.lib:
                    self.lib[key] = (d['k'], [tuple(e) for e in d['eqs']]); self.libinv.add(v1.inv_key(d['k'], key))

    def logblock(self, kind, idx, clause):
        self.fblocks.write(f'{kind} {idx} ' + ' '.join(map(str, clause)) + '\n'); self.fblocks.flush()

    def card_assump(self):
        k = self.N - self.T
        if k < 0: return None
        out = [-self.tot.rhs[k]] if k < len(self.tot.rhs) else []
        if self.ztot is not None:
            kz = len(self.enc.lits) - self.T
            if kz < len(self.ztot.rhs): out.append(-self.ztot.rhs[kz])
        return out

    def handle_model(self, idx, m):
        enc, n = self.enc, self.n
        tm = time.time(); st = enc.structure(m); eqs = self.model_eqs(m); cnt = sum(1 for l in self.obj if l in m)
        if self.lf is not None:
            r = self.lf.check(m)
            if r is not None:
                clause, rec, tier = r; rec['piece'] = idx
                self.flam.write(json.dumps(rec) + '\n'); self.flam.flush()
                self.solver.add_clause(clause); self.stats['lam'] += 1; self.logblock('lambda', idx, clause)
                self.fmodels.write(f'{st} | piece {idx} lambda-{tier} ({len(clause)} lits) cnt={cnt} T={self.T} '
                                   f't={time.time() - tm:.1f}\n'); self.fmodels.flush()
                return
        kind, lits, info = self.find_core(eqs)
        if kind is None:
            if v1.whole_dead(n, eqs):
                self.stats['big'] += 1; self.fbig.write(st + '\n'); self.fbig.flush()
                cl_ = [-x for x in enc.lits if x in m]; self.solver.add_clause(cl_); kind = 'big'
                self.logblock('big', idx, cl_)
            else:
                res = realise.realise(n, eqs, tries=60)
                if res is not None:
                    P, Z, per, neq = res
                    self.stats['real'] += 1
                    obj = Z - 2 * neq if self.sets else Z
                    self.freal.write(json.dumps({'obj': obj, 'Z': Z, 'per': per, 'equilateral': neq, 'T_sets': Z - 2 * neq,
                                                 'model_cnt': cnt, 'piece': idx, 'pattern': st,
                                                 'P': [[float(a), float(b)] for a, b in P]}) + '\n'); self.freal.flush()
                    print(f'  REALISED obj={obj} Z={Z} T_sets={Z - 2 * neq} (model cnt {cnt}) piece {idx}: {st}', flush=True)
                    kind = f'REALISED obj={obj}'
                    if self.allmax:
                        self.solver.add_clause(enc.block_clause(m)); self.logblock('allmax-realised', idx, enc.block_clause(m))
                    else: self.T = max(self.T, obj + 1)
                else:
                    self.stats['surv'] += 1; self.fsurv.write(st + f' | piece {idx} cnt={cnt}\n'); self.fsurv.flush()
                    self.solver.add_clause(enc.block_clause(m)); kind = 'SURVIVOR'
                    self.logblock('SURVIVOR', idx, enc.block_clause(m))
        else:
            self.solver.add_clause([-x for x in lits]); self.logblock('core-' + kind, idx, [-x for x in lits])
        self.fmodels.write(f'{st} | piece {idx} {kind} {info} cnt={cnt} T={self.T} t={time.time() - tm:.1f}\n')
        self.fmodels.flush()

    def run_piece(self, idx, rg):
        enc = self.enc
        t0 = time.process_time(); act = enc.pool.id(('act', idx))
        units = [c[0] for c in enc.unit_clauses(rg)]
        if self.cover == 'lex':
            for cl in enc.sym_compact(rg): self.solver.add_clause(cl + [-act])
        else:
            A = v1.apex_of(rg)
            units = units + [-self.vtot[c].rhs[A] for c in range(1, self.n) if A < len(self.vtot[c].rhs)]
        models = 0
        while True:
            ca = self.card_assump()
            if ca is None: break
            if not self.solver.solve(assumptions=units + [act] + ca): break
            m = set(l for l in self.solver.get_model() if l > 0); models += 1; self.stats['models'] += 1
            self.handle_model(idx, m)
        self.solver.add_clause([-act])
        cpu = time.process_time() - t0
        self.fdone.write(f'{idx} {"".join(map(str, rg))} {self.T} {models} {cpu:.2f} ver={self.vtag} cover={self.cover}\n'); self.fdone.flush()
        return models, cpu


def main():
    n, T0, outdir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    opt = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    r, W = int(opt('--r', 0)), int(opt('--W', 1))
    t0 = time.time()
    w = IWorker(n, T0, outdir, tag=f'.w{r}', sets='--sets' in sys.argv, allmax='--allmax' in sys.argv, cover=opt('--cover', 'lex'),
                fams=tuple(f for f in opt('--fams', 'G,X,O').split(',') if f), lam=opt('--lam', '1') == '1')
    allp = list(partitions(n - 1, n - 1, exact=False)); keep = w.enc.keep(allp)
    pieces = [(i, rg) for i, rg in enumerate(allp) if keep[i]]
    if w.cover == 'apex':
        pieces = [(i, rg) for i, rg in pieces if v1.apex_of(rg) * n >= w.T]
    if opt('--pieces'):
        a, b = opt('--pieces').split(':'); pieces = pieces[int(a):int(b)]
    mine = pieces[r::W]
    print(f'n={n} T0={T0} T={w.T} N={w.N} pieces {len(pieces)} (worker {r}/{W}: {len(mine)}); clauses {len(w.enc.clauses)}; '
          f'fams {w.famcounts}; tag {w.vtag}; build {time.time() - t0:.1f}s', flush=True)
    for j, (idx, rg) in enumerate(mine):
        if idx in w.done: continue
        if w.cover == 'apex' and v1.apex_of(rg) * n < w.T: continue
        if j % 20 == 0: w.load_lib(); w.sync_T()
        models, cpu = w.run_piece(idx, rg)
        if models or j % 100 == 0:
            print(f'piece {idx} {"".join(map(str, rg))}: {models} models, cpu {cpu:.1f}s; T={w.T}; {w.stats}; '
                  f'lib {len(w.lib)}; wall {time.time() - t0:.0f}s', flush=True)
    print(f'DONE worker {r}: final T={w.T} (UNSAT at T for all my pieces if no survivors); {w.stats}; '
          f'wall {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
