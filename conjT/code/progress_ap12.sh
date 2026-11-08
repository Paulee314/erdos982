#!/bin/bash
# progress of the T* n = 12 (L = 7) run.  usage: ./progress_ap12.sh   (from agent_runs/theory2)
cd "$(dirname "$0")/ap12_L7" || exit 1
echo "$(date -u +%FT%TZ) pieces done $(cat w*.done 2>/dev/null | wc -l) of 265391; models $(cat w*.models 2>/dev/null | wc -l); big $(cat w*.big 2>/dev/null | wc -l); surv $(cat w*.surv 2>/dev/null | wc -l); workers running $(pgrep -f 'apex_pieces.py 12 ' | wc -l)"
cat w*.done 2>/dev/null | awk '{c+=$7} END {printf "CPU s in done pieces: %.0f\n", c}'
grep -h "DONE worker" ../ap12L7_w*.out 2>/dev/null | wc -l | awk '{print "workers finished: " $1}'
