#!/usr/bin/env python3
"""Conjecture T search (theory2): is there a strictly convex n-gon in which EVERY vertex is the apex of at least
L = floor((n-1)/2) + 1 isosceles triangles?  Encoding: e982lib.Enc(n, n-1, order=True, atmost=True) (E equivalence,
F1, F2, total preorder LT with F2-order, chord monotonicity, four-in-a-class; the class bound is vacuous) plus, for every
centre c, CardEnc.atleast(sum_{u<v} e(c,u,v) >= L).  Cover: pieces = restricted-growth strings pi for vertex 0's
partition (all block counts) with apex(pi) >= L, mirror-skipped, lex-leader over all 2n frames (sym_compact), as in the
reviewed unified cover of fable_tasks/n12.  Every clause is invariant under relabelling by the dihedral group, so the
lex-min relabelling of any real polygon satisfying the hypothesis lies in a kept piece.

Within a piece, models are enumerated with one incremental CaDiCaL per worker.  Each model is killed by a CORE: a subset
S of k (5, 6, then 7) vertices such that the local equalities of the model inside S have no complex solution with the two
lowest vertices of S normalised to (0,0), (1,0) (Singular std = {1}); the core's positive literals are blocked by one
clause (sound: more equalities, fewer solutions; the normalisation is w.l.o.g. for pairwise distinct points).  Cores are
cached as abstract types (canonical under relabelling) in w<r>.cores and looked up before calling Singular.  If no core
of size <= 7 exists, the whole pattern is tested with distinctness saturation (sat by the product of all d_ij^2); if dead,
its full positive set is blocked and recorded in w<r>.big (certificate by alg_sat.py later); if not dead it is a
SURVIVOR: recorded, full-blocked (not pos-blocked), and the run continues.

usage: apex_pieces.py n r W outdir [--pieces a:b] [--nocore]   (worker r of W; SINGULAR env var; restart-safe)
outputs in outdir: w<r>.done (piece index, rg, models, new cores, big, survivors, cpu), w<r>.cores (jsonl), w<r>.big,
w<r>.surv, w<r>.models (every model with the core that killed it)."""
import sys, os, time, json, itertools, subprocess, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e982lib import Enc, partitions
import numsolve
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

SINGULAR = os.environ.get('SINGULAR', 'Singular')


def apex_of(rg):
    from collections import Counter
    return sum(m * (m - 1) // 2 for m in Counter(rg).values())


def canon_key(k, eqs):
    """eqs: set of (c,u,v) on points 0..k-1 (u<v).  Canonical form under all relabellings."""
    best = None
    for perm in itertools.permutations(range(k)):
        t = tuple(sorted((perm[c], min(perm[u], perm[v]), max(perm[u], perm[v])) for c, u, v in eqs))
        if best is None or t < best: best = t
    return best


def inv_key(k, eqs):
    cc = [0] * k; ee = [0] * k
    for c, u, v in eqs: cc[c] += 1; ee[u] += 1; ee[v] += 1
    return (k, len(eqs), tuple(sorted(zip(cc, ee))))


def sing_script_dead(systems, saturate=True, charp=0):
    """systems: list of (k, eqs) abstract; Singular script printing per system 1 if std(I) == {1}, 2 if not but
    I saturated by the product of all squared distances of the k points (except the normalised pair) is {1}, else 0."""
    out = ['LIB "elim.lib"; option(redSB);']
    for k, eqs in systems:
        vars_ = [f'x{i}' for i in range(2, k)] + [f'y{i}' for i in range(2, k)]
        def pt(i): return ('0', '0') if i == 0 else ('1', '0') if i == 1 else (f'x{i}', f'y{i}')
        def d2(a, b):
            (ax, ay), (bx, by) = pt(a), pt(b); return f'(({ax})-({bx}))^2+(({ay})-({by}))^2'
        polys = [f'({d2(c,u)})-({d2(c,v)})' for c, u, v in eqs]
        g = '*'.join(f'({d2(i,j)})' for i in range(k) for j in range(i + 1, k) if (i, j) != (0, 1))
        sat_part = (f' else {{ ideal S = sat(G, ideal({g})); S = std(S); if (size(S) == 1 && S[1] == 1) {{ print(2); }} '
                    f'else {{ print(0); }} }}') if saturate else ' else { print(0); }'
        out.append(f'ring R = {charp}, ({",".join(vars_)}), dp; ideal I = {", ".join(polys)}; ideal G = std(I); '
                   f'if (size(G) == 1 && G[1] == 1) {{ print(1); }}{sat_part} kill R;')
    return '\n'.join(out)


def sing_script_satpair(systems, charp=0):
    """systems: list of (k, eqs, (i,j)); prints 1 if sat(std(I), d_ij^2) == {1} (dead for v_i != v_j off the null cone)."""
    out = ['LIB "elim.lib"; option(redSB);']
    for k, eqs, (pi, pj) in systems:
        vars_ = [f'x{i}' for i in range(2, k)] + [f'y{i}' for i in range(2, k)]
        def pt(i): return ('0', '0') if i == 0 else ('1', '0') if i == 1 else (f'x{i}', f'y{i}')
        def d2(a, b):
            (ax, ay), (bx, by) = pt(a), pt(b); return f'(({ax})-({bx}))^2+(({ay})-({by}))^2'
        polys = [f'({d2(c,u)})-({d2(c,v)})' for c, u, v in eqs]
        out.append(f'ring R = {charp}, ({",".join(vars_)}), dp; ideal I = {", ".join(polys)}; ideal G = std(I); '
                   f'ideal S = sat(G, ideal({d2(pi, pj)})); S = std(S); print(size(S) == 1 && S[1] == 1); kill R;')
    return '\n'.join(out)


DEBUG = os.environ.get('SINGDEBUG')


def sing_run(script, timeout=300, nsys=1):
    """returns the printed integers; on timeout returns [0]*nsys (treated as 'not shown dead')"""
    t0 = time.time()
    if DEBUG: print(f'  sing_run nsys={nsys} timeout={timeout} chars={len(script)} head={script[40:90]!r}', file=sys.stderr, flush=True)
    try:
        r = subprocess.run([SINGULAR, '-q'], input=script + '\nquit;', capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        if DEBUG: print(f'  -> TIMEOUT after {time.time()-t0:.1f}s', file=sys.stderr, flush=True)
        return [0] * nsys
    if r.returncode != 0: raise RuntimeError(r.stderr[-2000:])
    if DEBUG: print(f'  -> {time.time()-t0:.1f}s {r.stdout.split()[:12]}', file=sys.stderr, flush=True)
    return [int(x) for x in r.stdout.split()]


def whole_dead(n, eqs, timeout=240):
    """Whole-pattern test.  (1) modular (char 32003) std; if unit, confirm over Q.  (2) else modular greedy single-pair
    distinctness saturation (as alg_sat.py) to find the coincidence pairs quickly; (3) confirm over Q with exactly those
    pairs.  True only on a Q verdict (sound); False (-> survivor, offline alg_sat.py) on timeout or if the modular search
    does not reach {1}."""
    vars_ = [f'x{i}' for i in range(2, n)] + [f'y{i}' for i in range(2, n)]
    def pt(i): return ('0', '0') if i == 0 else ('1', '0') if i == 1 else (f'x{i}', f'y{i}')
    def d2(a, b):
        (ax, ay), (bx, by) = pt(a), pt(b); return f'(({ax})-({bx}))^2+(({ay})-({by}))^2'
    polys = [f'({d2(c,u)})-({d2(c,v)})' for c, u, v in eqs]
    def head(ch): return (f'LIB "elim.lib"; option(redSB); ring R = {ch}, ({",".join(vars_)}), dp; ideal I = {", ".join(polys)}; '
                          f'ideal G = std(I);')
    unit_q = ' print(size(G) == 1 && G[1] == 1);'
    PAIRS = [(i, j) for i in range(n) for j in range(i + 1, n) if (i, j) != (0, 1)]
    t0 = time.time()
    out = sing_run(head(32003) + unit_q, timeout=60, nsys=1)
    QCONFIRM = os.environ.get('QCONFIRM')     # default: the modular verdict blocks the pattern; the Q certificate is
    if out and out[0] == 1:                   # produced offline by alg_sat.py and required by check_run.py's audit
        if not QCONFIRM: return True
        out = sing_run(head(0) + unit_q, timeout=timeout, nsys=1)
        return bool(out and out[0] == 1)
    # modular greedy saturation
    chosen = []; state = None
    while time.time() - t0 < 90:
        sat_chain = ''.join(f' S = sat(S, ideal({d2(i,j)}));' for i, j in chosen)
        tests = ''.join(f' T = sat(S, ideal({d2(i,j)})); T = std(T); print({i}); print({j}); print(dim(T)); '
                        f'if (dim(T) == 0) {{ print(vdim(T)); }} else {{ print(-1); }}' for i, j in PAIRS if (i, j) not in chosen)
        w = sing_run(head(32003) + ' ideal S = G; ideal T;' + sat_chain + tests, timeout=60, nsys=1)
        if len(w) < 4: return False
        best = None
        for q in range(0, len(w) - 3, 4):
            i, j, d, vd = w[q:q + 4]
            key = (-1, 0) if d == -1 else (d, vd if d == 0 else 10 ** 9)
            if best is None or key < best[0]: best = (key, (i, j))
        if best is None: return False
        chosen.append(best[1])
        if best[0] == (-1, 0): break
        if state is not None and best[0] >= state: return False
        state = best[0]
    else:
        return False
    if not QCONFIRM: return True
    # confirm over Q with exactly these pairs
    sat_chain = ''.join(f' S = sat(S, ideal({d2(i,j)}));' for i, j in chosen)
    out = sing_run(head(0) + ' ideal S = G;' + sat_chain + ' S = std(S); print(size(S) == 1 && S[1] == 1);',
                   timeout=max(30, int(timeout - (time.time() - t0))), nsys=1)
    return bool(out and out[0] == 1)


class Worker:
    def __init__(self, n, r, W, outdir, nocore=False):
        self.n, self.r, self.W, self.outdir, self.nocore = n, r, W, outdir, nocore
        self.L = int(os.environ.get('APEX_L', (n - 1) // 2 + 1))   # APEX_L overrides (e.g. T*: n/2+1 even, (n+5)/2 odd)
        os.makedirs(outdir, exist_ok=True)
        enc = Enc(n, n - 1, order=True, atmost=True); self.enc = enc
        for c in range(n):
            lits = [enc.e(c, u, v) for u in range(n) for v in range(u + 1, n) if c not in (u, v)]
            enc.clauses += CardEnc.atleast(lits=lits, bound=self.L, vpool=enc.pool, encoding=EncType.seqcounter).clauses
        self.solver = Cadical153(bootstrap_with=enc.clauses)
        self.local_index = {t: i for i, t in enumerate(enc.local)}
        self.lib = {}          # canonical key -> (k, eqs)
        self.libinv = set()    # invariants of library cores (pre-filter for the expensive canonical form)
        self.load_lib()
        self.done = set()
        dn = f'{outdir}/w{r}.done'
        if os.path.exists(dn):
            for line in open(dn):
                self.done.add(int(line.split()[0]))
        self.fdone = open(dn, 'a'); self.fcores = open(f'{outdir}/w{r}.cores', 'a')
        self.fmodels = open(f'{outdir}/w{r}.models', 'a'); self.fbig = open(f'{outdir}/w{r}.big', 'a')
        self.fsurv = open(f'{outdir}/w{r}.surv', 'a')
        self.stats = dict(models=0, newcores=0, big=0, surv=0, hits=0)

    def load_lib(self):
        for fn in glob.glob(f'{self.outdir}/w*.cores'):
            for line in open(fn):
                try: d = json.loads(line)
                except Exception: continue
                key = tuple(map(tuple, d['key']))
                if key not in self.lib:
                    self.lib[key] = (d['k'], [tuple(e) for e in d['eqs']]); self.libinv.add(inv_key(d['k'], key))

    def model_eqs(self, m):
        return [t for t, lit in zip(self.enc.local, self.enc.lits) if lit in m]

    def subsets(self, eqs, k, thr, must=()):
        n = self.n; out = []
        for S in itertools.combinations(range(n), k):
            if any(x not in S for x in must): continue
            Sset = set(S); pos = {v: i for i, v in enumerate(S)}
            sub = [(c, u, v) for c, u, v in eqs if c in Sset and u in Sset and v in Sset]
            if len(sub) < thr: continue
            out.append((S, sub, set((pos[c], pos[u], pos[v]) for c, u, v in sub)))
        out.sort(key=lambda t: -len(t[1]))
        return out

    def minimise(self, k, cur, script_of, thr):
        """greedy removal of equalities keeping the system dead; each round tests all single removals in one Singular call"""
        t_min = time.time()
        while len(cur) > thr and time.time() - t_min < 90:
            trials = [cur[:i] + cur[i + 1:] for i in range(len(cur))]
            res = sing_run(script_of(trials), timeout=60, nsys=len(trials))
            hit = [i for i, d in enumerate(res) if d]
            if not hit: break
            cur = trials[hit[0]]
        return cur

    def record_core(self, k, S, cur, kind):
        key = canon_key(k, set(cur))
        if key not in self.lib:
            self.lib[key] = (k, cur); self.stats['newcores'] += 1; self.libinv.add(inv_key(k, key))
            self.fcores.write(json.dumps({'k': k, 'key': key, 'eqs': cur, 'kind': kind}) + '\n'); self.fcores.flush()
        inv = {i: v for i, v in enumerate(S)}
        lits = [self.enc.lits[self.local_index[(inv[c], min(inv[u], inv[v]), max(inv[u], inv[v]))]] for c, u, v in cur]
        return 'new', lits, (k, kind, key)

    def find_core(self, eqs):
        """returns (kind, lits_to_block, info); kind in hit / new / None"""
        n = self.n
        # stage 0: library lookup on 5- and 6-subsets
        for k in (5, 6):
            for S, sub, abst in self.subsets(eqs, k, 2 * k - 5):
                if inv_key(k, abst) not in self.libinv: continue
                key = canon_key(k, abst)
                if key in self.lib:
                    self.stats['hits'] += 1
                    return 'hit', [self.enc.lits[self.local_index[t]] for t in sub], (k, key)
        if self.nocore: return None, None, None
        # stage 1: std(I) = {1} on 5- then 6-subsets, most equalities first, in small batches (stop at the first dead one)
        for k in (5, 6):
            cands = self.subsets(eqs, k, 2 * k - 4)[:400]
            B = 50 if k == 5 else 40
            for b0 in range(0, len(cands), B):
                batch = cands[b0:b0 + B]
                # modular prefilter (char 32003, fast, heuristic), then confirmation over Q (the sound verdict)
                resp = sing_run(sing_script_dead([(k, abst) for S, sub, abst in batch], saturate=False, charp=32003), timeout=30, nsys=len(batch))
                for (S, sub, abst), deadp in zip(batch, resp):
                    if not deadp: continue
                    if not sing_run(sing_script_dead([(k, abst)], saturate=False), timeout=25)[0]: continue
                    cur = self.minimise(k, list(abst), lambda sysl: sing_script_dead([(k, e) for e in sysl], saturate=False), 2 * k - 4)
                    return self.record_core(k, S, cur, 'unit')
        # stage 2: degenerate patterns -- find coincident / null-cone pairs numerically (complex LM), then test
        # 5-, 6-subsets containing such a pair with saturation by that pair's squared distance
        pairs = numsolve.coincident_pairs(n, eqs, restarts=8)[:6]
        t_stage2 = time.time()
        for (i, j) in pairs:
            for k in (5, 6):
                if time.time() - t_stage2 > 8: break            # global time budget for stage 2 (then whole_dead / surv)
                cands = self.subsets(eqs, k, 2 * k - 5, must=(i, j))[:60]
                if not cands: continue
                sysl = []
                for S, sub, abst in cands:
                    pos = {v: t for t, v in enumerate(S)}; sysl.append((k, abst, (pos[i], pos[j])))
                res = []
                for b0 in range(0, len(sysl), 12):
                    bt = sysl[b0:b0 + 12]
                    resp = sing_run(sing_script_satpair(bt, charp=32003), timeout=15, nsys=len(bt))
                    for q, dp_ in enumerate(resp):
                        if dp_ and sing_run(sing_script_satpair([bt[q]]), timeout=40)[0]: res.append(1)
                        else: res.append(0)
                    if any(res): break
                res += [0] * (len(sysl) - len(res))
                for (S, sub, abst), pr, dead in zip(cands, [t[2] for t in sysl], res):
                    if not dead: continue
                    cur = self.minimise(k, list(abst), lambda sysl: sing_script_satpair([(k, e, pr) for e in sysl]), 2 * k - 5)
                    return self.record_core(k, S, cur, f'sat{pr}')
        return None, None, None

    def unit_lits_at(self, c, rg):
        o = [v for v in range(self.n) if v != c]; out = []
        for x in range(len(o)):
            for y in range(x + 1, len(o)):
                lit = self.enc.e(c, o[x], o[y]); out.append(lit if rg[x] == rg[y] else -lit)
        return out

    def handle_model(self, idx, m):
        enc, n = self.enc, self.n
        tm = time.time()
        st = enc.structure(m); eqs = self.model_eqs(m)
        kind, lits, info = self.find_core(eqs)
        if kind is None:
            if whole_dead(n, eqs):
                self.stats['big'] += 1; self.fbig.write(st + '\n'); self.fbig.flush()
                self.solver.add_clause([-x for x in self.enc.lits if x in m]); kind = 'big'
            else:
                self.stats['surv'] += 1; self.fsurv.write(st + '\n'); self.fsurv.flush()
                self.solver.add_clause(enc.block_clause(m)); kind = 'SURVIVOR'
        else:
            self.solver.add_clause([-x for x in lits])
        self.fmodels.write(f'{st} | piece {idx} {kind} {info} t={time.time() - tm:.1f}\n')

    def run_piece(self, idx, rg):
        """enumerate and kill all models of the piece.  Each solve gets a conflict budget; when it is exhausted the
        piece is CUBED on vertex 1's partition (all RG strings with apex >= L, no symmetry): each cube is solved under
        assumptions with a 10x budget, and unlimited if that is exhausted too (logged)."""
        enc, n = self.enc, self.n
        t0 = time.process_time(); act = enc.pool.id(('act', idx))
        for cl in enc.sym_compact(rg): self.solver.add_clause(cl + [-act])
        units = [c[0] for c in enc.unit_clauses(rg)]
        models = 0; newc0 = self.stats['newcores']; big0 = self.stats['big']; surv0 = self.stats['surv']
        BUDGET = int(os.environ.get('CONF_BUDGET', 20000))
        cubes = None; ci = 0; ncubes_solved = 0; unlimited = 0
        while True:
            if cubes is None:
                self.solver.conf_budget(BUDGET)
                r = self.solver.solve_limited(assumptions=units + [act])
                if r is None:
                    cubes = [c for c in partitions(n - 1, n - 1, exact=False) if apex_of(c) >= self.L]
                    print(f'piece {idx}: budget exhausted after {models} models -> cubing on vertex 1 ({len(cubes)} cubes)', flush=True)
                    continue
                if not r: break
            else:
                if ci >= len(cubes): break
                u1 = self.unit_lits_at(1, cubes[ci])
                self.solver.conf_budget(10 * BUDGET)
                r = self.solver.solve_limited(assumptions=units + u1 + [act])
                if r is None:
                    unlimited += 1; r = self.solver.solve(assumptions=units + u1 + [act])
                if not r: ci += 1; ncubes_solved += 1; continue
            m = set(l for l in self.solver.get_model() if l > 0); models += 1; self.stats['models'] += 1
            self.handle_model(idx, m)
        self.solver.add_clause([-act])
        self.fmodels.flush()
        cpu = time.process_time() - t0
        if cubes is not None:
            print(f'piece {idx}: cubed, {ncubes_solved} cubes, {unlimited} unlimited solves, {models} models, cpu {cpu:.1f}s', flush=True)
        self.fdone.write(f'{idx} {"".join(map(str, rg))} {models} {self.stats["newcores"] - newc0} '
                         f'{self.stats["big"] - big0} {self.stats["surv"] - surv0} {cpu:.2f}\n'); self.fdone.flush()
        return models, cpu


def main():
    n, r, W, outdir = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    nocore = '--nocore' in sys.argv
    lo, hi = 0, None
    if '--pieces' in sys.argv:
        a, b = sys.argv[sys.argv.index('--pieces') + 1].split(':'); lo, hi = int(a), int(b)
    t0 = time.time()
    w = Worker(n, r, W, outdir, nocore)
    allp = list(partitions(n - 1, n - 1, exact=False))
    keep = w.enc.keep(allp)
    pieces = [(i, rg) for i, rg in enumerate(allp) if keep[i] and apex_of(rg) >= w.L]
    if hi is not None: pieces = pieces[lo:hi]
    if os.environ.get('RESPLIT'):      # take the pieces not yet done by ANY worker and split those r::W
        alldone = set()
        for fn in glob.glob(f'{outdir}/w*.done'):
            for line in open(fn): alldone.add(int(line.split()[0]))
        pieces = [p for p in pieces if p[0] not in alldone]
    mine = pieces[r::W]
    print(f'n={n} L={w.L} pieces total {len(pieces)} (of {len(allp)} RG strings), worker {r}/{W}: {len(mine)}; '
          f'{len(w.enc.clauses)} clauses; lib {len(w.lib)}; build {time.time()-t0:.1f}s', flush=True)
    for j, (idx, rg) in enumerate(mine):
        if idx in w.done: continue
        if j % 20 == 0: w.load_lib()
        models, cpu = w.run_piece(idx, rg)
        if models or j % 50 == 0:
            print(f'piece {idx} {"".join(map(str, rg))}: {models} models, cpu {cpu:.1f}s; totals {w.stats}; '
                  f'lib {len(w.lib)}; wall {time.time()-t0:.0f}s', flush=True)
    print(f'DONE worker {r}: {w.stats}; wall {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
