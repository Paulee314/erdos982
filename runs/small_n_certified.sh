#!/bin/bash
# Certified re-run of a small case with the n = 12 code (Paul approved 2 Nov 2026 01:52 CT): exactly-K and below-K covers,
# DRUP proof per 50-piece batch checked by drat-trim + cake_lpr, per-piece re-certification of any batch not accepted or with structures,
# then the cover check. Usage: run.sh n K W
R=$(cd $(dirname $0)/../code && pwd); PY=${PY:-python3}; N=$1; K=$2; W=$3; cd $R
export N K W
echo "$(date -u +%FT%TZ) start n=$N K=$K W=$W" >> progress.log
for c in exact below; do
  ev=""; [ $c = below ] && ev="BELOW=1"
  for r in $(seq 0 $((W-1))); do ( env NOCNF=1 $ev nice -n 10 $PY cube982p.py $N $K $r $W 50 C_$c > logs/solve_${c}_$r.log 2>&1; env $ev nice -n 10 $PY checkproofs.py $N $K $r $W 50 C_$c --checker $R/chk.sh > logs/check_${c}_$r.log 2>&1 ) & done; wait
  echo "$(date -u +%FT%TZ) $c solved and checked" >> progress.log
done
$PY recert_jobs.py exact below > logs/recert_jobs.log 2>&1
for c in exact below; do
  [ -s recert_${c}_jobs.txt ] || continue
  for w in $(seq 0 $((W-1))); do nice -n 10 $PY recert.py $c recert_${c}_jobs.txt $w $W > logs/recert_${c}_$w.log 2>&1 & done; wait
done
$PY c_cover_check.py exact below > logs/cover_check.log 2>&1
gzip -1 -f C_*/*.drup 2>/dev/null
echo "$(date -u +%FT%TZ) finished" >> progress.log; touch finished
