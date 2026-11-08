#!/usr/bin/env python3
"""Write the frozen list of NOT-yet-done kept pieces (T*, n=12, L=7) ONCE, before starting workers with PIECE_LIST.
usage: make_piecelist.py outdir > pieces_todo.txt     (reads outdir/w*.done; prints one index per line, piece order)"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e982lib import Enc, partitions
import apex_pieces_v1 as v1
outdir = sys.argv[1]; n = 12; L = int(os.environ.get('APEX_L', 7))
done = set()
for fn in glob.glob(f'{outdir}/w*.done'):
    for line in open(fn): done.add(int(line.split()[0]))
enc = Enc(n, n - 1)      # keep() needs only the mirror map
allp = list(partitions(n - 1, n - 1, exact=False)); keep = enc.keep(allp)
todo = [i for i, rg in enumerate(allp) if keep[i] and v1.apex_of(rg) >= L and i not in done]
print(f'# {len(todo)} pieces not done ({len(done)} distinct done) in {outdir}', file=sys.stderr)
print('\n'.join(map(str, todo)))
