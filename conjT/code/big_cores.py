#!/usr/bin/env python3
"""Replace whole-pattern ('big') certificates by small sub-cores: for each pattern in big_all.txt (lines r::W), find a
subset of k = 7 (then 8, then 9) vertices whose local equalities have std = {1} over Q (modular prefilter over all
subsets in one Singular call, Q confirmation on the modular hits), or, failing that, one whose saturation by one
squared distance is {1} (pairs from numsolve, modular prefilter, Q confirmation).  Writes big_cores_r<r>.txt lines
'<k-vertex pattern> | big <i> pat <pattern> k <k> S <subset> pair <pair> key <canonical key>'.  Patterns with no small
core are written to big_nocore_r<r>.txt (to be handled by alg_sat.py on the whole pattern, with a memory limit).
usage: big_cores.py n outdir r W"""
import sys, os, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apex_pieces as ap, numsolve
n, outdir, r, W = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
lines = [l.split('|')[0].strip() for l in open(f'{outdir}/big_all.txt') if l.strip()]
done = set()
outf = f'{outdir}/big_cores_r{r}.txt'; nof = f'{outdir}/big_nocore_r{r}.txt'
if os.path.exists(outf):
    for l in open(outf):
        if ' pat ' in l: done.add(l.split(' pat ', 1)[1].split(' k ', 1)[0].strip())
if os.path.exists(nof):
    for l in open(nof): done.add(l.split('|')[0].strip())
out = open(outf, 'a'); noc = open(nof, 'a')


def eqs_of(line):
    parts = line.split(); eqs = []
    for c in range(n):
        others = [v for v in range(n) if v != c]; lab = dict(zip(others, parts[c])); g = {}
        for v in others: g.setdefault(lab[v], []).append(v)
        for grp in g.values():
            for v in grp[1:]: eqs.append((c, grp[0], v))
    return eqs


def kpattern(k, eqs):
    parts = []
    for c in range(k):
        others = [v for v in range(k) if v != c]; parent = {v: v for v in others}
        def find(x):
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for cc, u, v in eqs:
            if cc == c: parent[find(u)] = find(v)
        lab = {}; s = ''
        for v in others: s += str(lab.setdefault(find(v), len(lab)))
        parts.append(s)
    return ' '.join(parts)


def subsets(eqs, k, thr, must=()):
    res = []
    for S in itertools.combinations(range(n), k):
        if any(x not in S for x in must): continue
        Sset = set(S); pos = {v: i for i, v in enumerate(S)}
        sub = [(c, u, v) for c, u, v in eqs if c in Sset and u in Sset and v in Sset]
        if len(sub) < thr: continue
        res.append((S, [(pos[c], pos[u], pos[v]) for c, u, v in sub]))
    res.sort(key=lambda t: -len(t[1]))
    return res


t_all = time.time(); nfound = 0; nno = 0
for i, line in enumerate(lines):
    if i % W != r or line in done: continue
    eqs = eqs_of(line); t0 = time.time(); found = None
    for k in (7, 8, 9):
        cands = subsets(eqs, k, 2 * k - 4)
        for b0 in range(0, len(cands), 60):
            batch = cands[b0:b0 + 60]
            resp = ap.sing_run(ap.sing_script_dead([(k, a) for S, a in batch], saturate=False, charp=32003), timeout=60, nsys=len(batch))
            for (S, a), d in zip(batch, resp):
                if d and ap.sing_run(ap.sing_script_dead([(k, a)], saturate=False), timeout=120)[0]:
                    found = (k, S, a, None); break
            if found: break
        if found: break
    if not found:
        pairs = numsolve.coincident_pairs(n, eqs, restarts=8)[:6]
        for k in (7, 8):
            for (pi, pj) in pairs:
                cands = subsets(eqs, k, 2 * k - 5, must=(pi, pj))
                sysl = []
                for S, a in cands:
                    pos = {v: t for t, v in enumerate(S)}; sysl.append((k, a, (pos[pi], pos[pj]), S))
                for b0 in range(0, len(sysl), 30):
                    bt = sysl[b0:b0 + 30]
                    resp = ap.sing_run(ap.sing_script_satpair([t[:3] for t in bt], charp=32003), timeout=60, nsys=len(bt))
                    for (kk, a, pr, S), d in zip(bt, resp):
                        if d and ap.sing_run(ap.sing_script_satpair([(kk, a, pr)]), timeout=180)[0]:
                            found = (kk, S, a, pr); break
                    if found: break
                if found: break
            if found: break
    if found:
        k, S, a, pr = found; key = ap.canon_key(k, set(a)) if k <= 7 else None
        out.write(f'{kpattern(k, a)} | big {i} pat {line} k {k} S {S} pair {pr} key {list(key) if key else None}\n'); out.flush(); nfound += 1
    else:
        noc.write(f'{line} | big {i}\n'); noc.flush(); nno += 1
    if (nfound + nno) % 25 == 0:
        print(f'{nfound} cores, {nno} without; {time.time()-t_all:.0f}s', flush=True)
print(f'DONE r={r}: {nfound} cores, {nno} without small core; {time.time()-t_all:.0f}s', flush=True)
