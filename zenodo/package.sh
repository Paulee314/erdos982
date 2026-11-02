#!/bin/bash
# Package the n = 12 DRUP proofs for Zenodo (run after job D has finished). Proof files are already gzipped; tar without
# further compression, split into 4 GB parts (Zenodo: 50 GB and 100 files per record). Writes SHA256SUMS.
Z=$(cd $(dirname $0) && pwd); R=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/n12_run; cd $R
for d in C_exact C_below C_atmost recert_exact recert_below recert_atmost; do
  [ -d $d ] || continue
  tar cf - $d | split -b 4000m -d -a 2 - $Z/n12_proofs_$d.tar.part
done
cd $Z && shasum -a 256 n12_proofs_*.tar.part* > SHA256SUMS && ls -la && echo packaged
