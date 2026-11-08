#!/usr/bin/env python3
"""Count distinct patterns and dihedral orbits among the models logged by apex_pieces.py.  usage: orbits_of_models.py n outdir"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patterns import parse, apply_map, to_string
n, outdir = int(sys.argv[1]), sys.argv[2]
pats = set()
for fn in glob.glob(f'{outdir}/w*.models'):
    for line in open(fn):
        pats.add(line.split('|')[0].strip())
orbits = set()
for s in pats:
    nn, lab = parse(s)
    orbits.add(min(to_string(n, apply_map(n, lab, [(refl * v + r) % n for v in range(n)])) for r in range(n) for refl in (1, -1)))
print(f'{len(pats)} distinct models, {len(orbits)} dihedral orbits')
