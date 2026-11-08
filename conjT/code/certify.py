#!/usr/bin/env python3
"""Chunked certification driver.  usage: certify.py outdir k r W   (k = 5, 6, 7 for cores_k<k>.txt, or 'big' for big_all.txt)
Takes lines r::W of the pattern file, runs alg_sat.py on them (Singular std / saturation + sympy re-expansion) and writes
certify_k<k>_r<r>.log with the GLOBAL pattern indices, so that check_run.py can match them."""
import sys, os, subprocess
outdir, k, r, W = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
here = os.path.dirname(os.path.abspath(__file__))
src = f'{outdir}/big_all.txt' if k == 'big' else f'{outdir}/cores_k{k}.txt'
npts = int(open(f'{outdir}/n.txt').read()) if k == 'big' else int(k)
lines = [l for l in open(src) if l.strip()]
mine = [(i, l) for i, l in enumerate(lines) if i % W == r]
logf = f'{outdir}/certify_k{k}_r{r}.log'
def ident_of(src_line):
    return ('key ' + src_line.split('key', 1)[1].strip()) if 'key' in src_line else ('pat ' + src_line.split('|')[0].strip())
already = set()                   # resume by identity (key or pattern), from every log of this k, so that a regenerated
import glob                        # pattern file with new lines inserted does not invalidate earlier chunks
for lg in glob.glob(f'{outdir}/certify_k{k}_r*.log'):
    for line in open(lg):
        if line.startswith('pattern ') and 'VERIFIED' in line:
            already.add(line.split(' ', 2)[2].split(':', 1)[0].strip())
mine = [(i, l) for i, l in mine if ident_of(l) not in already]
chunk = f'{outdir}/chunk_k{k}_r{r}.txt'
open(chunk, 'w').write(''.join(l for i, l in mine))
if not mine:
    open(logf, 'a').write(''); sys.exit(0)
p = subprocess.run([sys.executable, f'{here}/alg_sat.py', str(npts), chunk, '--outdir', f'{outdir}/certs_k{k}_r{r}'],
                   capture_output=True, text=True)
out = []
for line in p.stdout.splitlines():
    if line.startswith('pattern '):
        j = int(line.split()[1].rstrip(':')); g = mine[j][0]
        line = f'pattern {g} {ident_of(mine[j][1])}:' + line.split(':', 1)[1]
    out.append(line)
open(logf, 'a').write('\n'.join(out) + '\n')
if p.returncode != 0:
    open(f'{outdir}/certify_k{k}_r{r}.err', 'w').write(p.stderr)
print(f'k={k} r={r}: {len(mine)} patterns, {sum("VERIFIED" in l for l in out)} VERIFIED, rc {p.returncode}')
