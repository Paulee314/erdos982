#!/usr/bin/env python3
"""T* piece solver v2 = apex_pieces.py (v13, imported unchanged as apex_pieces_v1) + static families (fams_v2.py) +
lazy Lambda filter before the Singular core search (lambda_v2.py).  Same cover, same pieces, same budget/cubing,
same core / whole-pattern / survivor logic; v1's variable numbering is unchanged (family auxiliaries are allocated after
all v1 variables).  Every record carries ver=<tag> (family set + md5 of the code); outdir/VERSION holds the tag.
Extra output: w<r>.lambda (jsonl: one exact Farkas certificate per Lambda-killed model; check_lambda_certs.py format).
env: TSTAR_FAMS (default 'G,X,O'; NB,R3 optional, unrefereed), TSTAR_LAMBDA (default 1); everything else as apex_pieces.py.
usage: apex_v2.py n r W outdir [--pieces a:b] [--nocore]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apex_pieces_v1 as v1
import fams_v2
from lambda_v2 import LambdaFilter

DEFAULT_FAMS = 'G,X,O'   # NB, R3 available (UNREFEREED) but gave no measurable gain


class TagFile:
    """line-oriented writer that appends ' ver=TAG' to text lines, or a 'ver' key to JSON lines"""
    def __init__(self, f, tag, js=False): self.f, self.tag, self.js = f, tag, js
    def write(self, s):
        out = []
        for line in s.splitlines(keepends=True):
            if line.endswith('\n') and line.strip():
                body = line[:-1]
                if self.js:
                    d = json.loads(body); d['ver'] = self.tag; body = json.dumps(d)
                else:
                    body = body + ' ver=' + self.tag
                line = body + '\n'
            out.append(line)
        return self.f.write(''.join(out))
    def flush(self): return self.f.flush()
    def close(self): return self.f.close()


class SideTag:
    """writes lines unchanged; one 'ver=TAG' line per written line to a sidecar (same line order)"""
    def __init__(self, f, side, tag): self.f, self.side, self.tag = f, side, tag
    def write(self, s):
        k = s.count('\n'); self.side.write(f'ver={self.tag}\n' * k); return self.f.write(s)
    def flush(self): self.side.flush(); return self.f.flush()
    def close(self): self.side.close(); return self.f.close()


class WorkerV2(v1.Worker):
    def __init__(self, n, r, W, outdir, nocore=False, fams=None, lam=None):
        fams = fams if fams is not None else [f for f in os.environ.get('TSTAR_FAMS', DEFAULT_FAMS).split(',') if f]
        lam = lam if lam is not None else os.environ.get('TSTAR_LAMBDA', '1') == '1'
        super().__init__(n, r, W, outdir, nocore)
        self.fams, self.lam = list(fams), lam
        t0 = time.time()
        cl, self.famvars, self.famcounts = fams_v2.add_tstar_families(self.enc, self.fams)
        for c in cl: self.solver.add_clause(c)
        self.fam_build = time.time() - t0
        self.tag = fams_v2.version_tag(self.fams, lam)
        with open(f'{outdir}/VERSION', 'a') as f:
            f.write(f'{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} worker {r} {self.tag} counts={self.famcounts}\n')
        for name, js in (('fdone', False), ('fcores', True), ('fmodels', False)):
            setattr(self, name, TagFile(getattr(self, name), self.tag, js))
        # .big / .surv lines must stay exactly n tokens (alg_sat.py drops other lines): tag goes to a sidecar
        self.fbig = SideTag(self.fbig, open(f'{outdir}/w{r}.big.ver', 'a'), self.tag)
        self.fsurv = SideTag(self.fsurv, open(f'{outdir}/w{r}.surv.ver', 'a'), self.tag)
        self.flam = TagFile(open(f'{outdir}/w{r}.lambda', 'a'), self.tag, js=True)
        self.lf = LambdaFilter(self.enc) if lam else None
        self.stats.update(lam_kills=0)

    def handle_model(self, idx, m):
        if self.lf is not None:
            tm = time.time()
            r = self.lf.check(m)
            if r is not None:
                clause, rec, tier = r
                rec['piece'] = idx
                self.flam.write(json.dumps(rec) + '\n'); self.flam.flush()
                self.solver.add_clause(clause); self.stats['lam_kills'] += 1
                self.fmodels.write(f'{self.enc.structure(m)} | piece {idx} lambda-{tier} ({len(clause)} lits) '
                                   f't={time.time() - tm:.1f}\n')
                return
        return super().handle_model(idx, m)


def global_done(outdir):
    import glob
    s = set()
    for fn in glob.glob(f'{outdir}/w*.done'):
        for line in open(fn):
            try: s.add(int(line.split()[0]))
            except Exception: pass
    return s


def main():
    """as v1.main, except: PIECE_LIST=<file> (one piece index per line, written ONCE before any worker starts, e.g.
    by make_piecelist.py) replaces RESPLIT.  v1's RESPLIT lets each worker read w*.done at its own start time, so
    workers that start a few seconds apart split differently-shifted lists r::W -> duplicated pieces and holes (seen in
    ap12_L7: 4,958 duplicated indices; w1=w11, w4=w10=w13, w8=w15 run identical sequences).  With a frozen list the
    r::W slices are disjoint and cover the list; a piece already in ANY w*.done is skipped (checked before each piece)."""
    plist = os.environ.get('PIECE_LIST')
    if not plist:
        v1.Worker = WorkerV2          # v1.main() instantiates Worker(n, r, W, outdir, nocore)
        return v1.main()
    n, r, W, outdir = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    nocore = '--nocore' in sys.argv
    t0 = time.time()
    w = WorkerV2(n, r, W, outdir, nocore)
    allp = list(v1.partitions(n - 1, n - 1, exact=False))
    keep = w.enc.keep(allp)
    lst = [int(x) for x in open(plist).read().split()]
    assert all(keep[i] and v1.apex_of(allp[i]) >= w.L for i in lst), 'piece list contains a non-kept piece'
    mine = lst[r::W]
    print(f'n={n} L={w.L} PIECE_LIST {plist}: {len(lst)} pieces, worker {r}/{W}: {len(mine)}; tag {w.tag}; '
          f'families {w.famcounts}; lib {len(w.lib)}; build {time.time() - t0:.1f}s', flush=True)
    gd = global_done(outdir)
    for j, idx in enumerate(mine):
        if j % 20 == 0: w.load_lib(); gd = global_done(outdir)
        if idx in w.done or idx in gd: continue
        models, cpu = w.run_piece(idx, allp[idx])
        if models or j % 50 == 0:
            print(f'piece {idx}: {models} models, cpu {cpu:.1f}s; totals {w.stats}; lib {len(w.lib)}; '
                  f'wall {time.time() - t0:.0f}s', flush=True)
    print(f'DONE worker {r}: {w.stats}; wall {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
