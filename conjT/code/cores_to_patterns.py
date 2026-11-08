#!/usr/bin/env python3
"""Convert the core library of apex_pieces.py (w*.cores, jsonl with k and abstract equalities (c,u,v)) into k-vertex
pattern lines for alg_sat.py (one restricted-growth string per centre, local closure of the equalities), grouped by k:
writes <outdir>/cores_k<k>.txt with lines "<pattern> | core <index> key <key>".  Then run
    alg_sat.py k cores_k<k>.txt --outdir certs_k<k>
which prints, per core, std(I) = {1} / saturation pairs and VERIFIED after exact re-expansion in sympy.
usage: cores_to_patterns.py outdir"""
import sys, os, glob, json, collections

outdir = sys.argv[1]
cores = {}
for fn in sorted(glob.glob(f'{outdir}/w*.cores')):
    for line in open(fn):
        try: d = json.loads(line)
        except Exception: continue
        key = tuple(map(tuple, d['key']))
        if key not in cores: cores[key] = (d['k'], [tuple(e) for e in d['eqs']])
byk = collections.defaultdict(list)
for idx, (key, (k, eqs)) in enumerate(sorted(cores.items(), key=lambda t: (t[1][0], t[0]))):
    byk[k].append((idx, key, eqs))
for k, items in sorted(byk.items()):
    with open(f'{outdir}/cores_k{k}.txt', 'w') as f:
        for idx, key, eqs in items:
            # local closure at each centre
            parts = []
            for c in range(k):
                others = [v for v in range(k) if v != c]
                parent = {v: v for v in others}
                def find(x):
                    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
                    return x
                for cc, u, v in eqs:
                    if cc == c: parent[find(u)] = find(v)
                lab = {}; s = ''
                for v in others:
                    r = find(v); s += str(lab.setdefault(r, len(lab)))
                parts.append(s)
            f.write(' '.join(parts) + f' | core {idx} key {list(key)}\n')
    print(f'k={k}: {len(items)} cores -> {outdir}/cores_k{k}.txt')
print(f'{len(cores)} distinct cores')
