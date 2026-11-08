import sys, random, time
sys.argv += []
import iconv_sat as I, apex_pieces_v1 as v1
from e982lib import partitions
n, T, cover, k = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
w = I.IWorker(n, T, f'runs/sample_{n}_{cover}_{int("--sets" in sys.argv)}', cover=cover, tag='.s', sets='--sets' in sys.argv)
allp = list(partitions(n-1, n-1, exact=False)); keep = w.enc.keep(allp)
pieces = [(i, rg) for i, rg in enumerate(allp) if keep[i] and (cover == 'lex' or v1.apex_of(rg)*n >= T)]
rng = random.Random(5); samp = rng.sample(pieces, k)
tot = 0
for idx, rg in samp:
    m, cpu = w.run_piece(idx, rg); tot += cpu
    print(idx, ''.join(map(str, rg)), m, f'{cpu:.1f}', flush=True)
print(f'{cover}: {len(pieces)} pieces, sample mean {tot/k:.1f}s -> est total {tot/k*len(pieces)/3600:.1f} CPU-h', flush=True)
