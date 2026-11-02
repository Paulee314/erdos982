#!/bin/bash
# n = 12 run (Paul approved 1 Nov 2026 22:22 CT): job B (unified cover, quick, uncertified), then job C (certified, exactly-K + below-K).
# 16 workers (the #982 n = 10 audit agent uses ~8 cores at the same time). nice 10. Restart-safe: rerun this script.
R=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/n12_run; W=16; cd $R
echo "$(date -u +%FT%TZ) run_all start pid $$" >> $R/progress.log
for J in B C; do
  for r in $(seq 0 $((W-1))); do nice -n 10 $R/worker.sh $J $r $W & done; wait
  echo "$(date -u +%FT%TZ) job $J all workers ended" >> $R/progress.log
done
touch $R/finished; echo "$(date -u +%FT%TZ) run_all finished" >> $R/progress.log
