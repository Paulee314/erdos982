#!/usr/bin/env python3
"""Two modes.
  big_viacore.py prep outdir   : from big_cores_r*.txt build outdir/cores_k7.txt (distinct by key) and cores_k8.txt /
                                 cores_k9.txt (distinct by pattern string) for certify.py.
  big_viacore.py log outdir    : from certify_k7*/k8*/k9* logs write outdir/certify_big_viacore.log with one line
                                 'pattern i pat <big pattern>: via core <k-pattern> VERIFIED' per big pattern whose core
                                 is VERIFIED (check_run.py then accepts the big pattern)."""
import sys, glob, ast, os
mode, outdir = sys.argv[1], sys.argv[2]
rows = []
for fn in sorted(glob.glob(f'{outdir}/big_cores_r*.txt')):
    for l in open(fn):
        if ' | big ' not in l: continue
        core, rest = l.split(' | ', 1)
        i = int(rest.split()[1]); pat = rest.split(' pat ', 1)[1].split(' k ', 1)[0].strip()
        k = int(rest.split(' k ', 1)[1].split()[0]); key = rest.split(' key ', 1)[1].strip()
        rows.append((i, pat, core.strip(), k, key))
if mode == 'prep':
    seen = {}; byk = {}
    for i, pat, core, k, key in rows:
        ident = key if key != 'None' else core
        if (k, ident) in seen: continue
        seen[(k, ident)] = True; byk.setdefault(k, []).append((core, key))
    for k, items in byk.items():
        with open(f'{outdir}/cores_k{k}.txt', 'w') as f:
            for core, key in items:
                f.write(core + (f' | core key {key}\n' if key != 'None' else '\n'))
        print(f'k={k}: {len(items)} distinct cores -> cores_k{k}.txt')
else:
    vkeys = set(); vpats = set()
    for k in (7, 8, 9):
        for lg in glob.glob(f'{outdir}/certify_k{k}_r*.log'):
            for line in open(lg):
                if line.startswith('pattern ') and 'VERIFIED' in line:
                    ident = line.split(' ', 2)[2].split(':', 1)[0].strip()
                    if ident.startswith('key '): vkeys.add(ident[4:].strip())
                    else: vpats.add(ident[4:].strip())
    n_ok = 0
    with open(f'{outdir}/certify_big_viacore.log', 'w') as f:
        for i, pat, core, k, key in rows:
            ok = (key in vkeys) if key != 'None' else (core in vpats)
            if ok:
                f.write(f'pattern {i} pat {pat}: via core k={k} {core} VERIFIED\n'); n_ok += 1
    print(f'{n_ok} of {len(rows)} big patterns certified via a core')
