#!/bin/bash
# One worker of the n = 12 run. Usage: worker.sh <job> <r> <W>
#   job B : unified at-most-K cover, incremental search (uncertified, fast)
#   job D : unified at-most-K cover, certified the same way as job C
#   job C : exactly-K then below-K cover, certified: DRUP proof per 50-piece batch, each checked by chk.sh, proofs gzipped
R=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/n12_run; PY=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/venv/bin/python
J=$1; r=$2; W=$3; cd $R
st() { echo "$(date -u +%FT%TZ) $*" >> $R/progress.log; }
if [ "$J" = B ]; then
  st "B r$r start"; ATMOST=1 $PY $R/cube982o.py 12 5 $r $W $R/B_unified > $R/logs/B_r$r.log 2>&1; st "B r$r end rc=$?"
else
  covs="exact below"; [ "$J" = D ] && covs="atmost"
  for c in $covs; do
    ev=""; [ $c = below ] && ev="BELOW=1"; [ $c = atmost ] && ev="ATMOST=1"
    st "C $c r$r solve start"; env NOCNF=1 $ev $PY $R/cube982p.py 12 5 $r $W 50 $R/C_$c > $R/logs/C_${c}_solve_r$r.log 2>&1; st "C $c r$r solve end rc=$?"
    st "C $c r$r check start"; env $ev $PY $R/checkproofs.py 12 5 $r $W 50 $R/C_$c --checker $R/chk.sh > $R/logs/C_${c}_check_r$r.log 2>&1; rc=$?; st "C $c r$r check end rc=$rc"
    gzip -1 -f $R/C_$c/${c}_w${r}_b*.drup; st "C $c r$r gzipped"
  done
fi
