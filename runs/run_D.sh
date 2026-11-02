#!/bin/bash
# Job D (Paul approved 2 Nov 2026 01:42 CT): certify the unified at-most-K cover. 16 workers, nice 10, then per-piece re-certification
# of any batch not accepted by both checkers or containing a structure, then the cover check.
R=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/n12_run; PY=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/venv/bin/python; W=16; cd $R
echo "$(date -u +%FT%TZ) job D start" >> $R/progress.log
for r in $(seq 0 $((W-1))); do nice -n 10 $R/worker.sh D $r $W & done; wait
echo "$(date -u +%FT%TZ) job D all workers ended" >> $R/progress.log
$PY recert_jobs.py atmost > logs/recert_jobs_atmost.log 2>&1
for w in $(seq 0 11); do nice -n 10 $PY $R/recert.py atmost $R/recert_atmost_jobs.txt $w 12 > $R/logs/recert_atmost_$w.log 2>&1 & done; wait
echo "$(date -u +%FT%TZ) job D recert done" >> $R/progress.log
$PY c_cover_check.py atmost > logs/cover_check_atmost.log 2>&1
touch $R/D_finished; echo "$(date -u +%FT%TZ) job D finished" >> $R/progress.log
