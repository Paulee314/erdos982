#!/usr/bin/env python3
"""Summarise cube982o.py .done files: pieces solved, structures, CPU/wall per piece, tail of the distribution, by index segment.
Usage: sumdone.py dir [dir ...]"""
import sys, os, statistics as st
for d in sys.argv[1:]:
    rows = [l.split() for f in sorted(os.listdir(d)) if f.endswith('.done') for l in open(os.path.join(d, f)) if l.strip()]
    real = [r for r in rows if r[1] != 'mirror']; mir = len(rows) - len(real)
    cnt = sum(int(r[1]) for r in real); wall = [float(r[2]) for r in real]; cpu = [float(r[4][4:]) for r in real]
    s = sorted(cpu); N = len(s)
    print(f"{d}: {len(rows)} pieces listed, {mir} mirror-skipped, {len(real)} solved, {cnt} structures; first {real[0][3]} last {real[-1][3]}")
    print(f"  CPU s/piece: sum {sum(cpu):.1f} mean {st.mean(cpu):.3f} median {st.median(cpu):.3f} p90 {s[int(.9*N)]:.3f} p99 {s[int(.99*N)]:.3f} max {max(cpu):.2f};  wall mean {st.mean(wall):.3f} max {max(wall):.2f}")
    B = 6
    print('  by index segment (mean / max CPU s): ' + '; '.join(f"{real[b*len(real)//B][0]}-{real[min((b+1)*len(real)//B, len(real))-1][0]}: {st.mean(float(r[4][4:]) for r in real[b*len(real)//B:(b+1)*len(real)//B]):.3f}/{max(float(r[4][4:]) for r in real[b*len(real)//B:(b+1)*len(real)//B]):.2f}" for b in range(B)))
    print(f"  pieces over 1 s: {sum(1 for c in cpu if c > 1)}, over 5 s: {sum(1 for c in cpu if c > 5)}")
