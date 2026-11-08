#!/bin/bash
# T* at n = 12 (some vertex has Z_p <= 6, i.e. refute "Z_p >= L = 7 at every vertex"), driver apex_pieces.py (== v13),
# piece set: RG strings of vertex 0 with apex >= 7, mirror-skipped, lex-leader kept (265,391 pieces).
# Restart-safe and re-sizable: stops ALL running ap12_L7 workers, then starts W new ones together with RESPLIT=1
# (each worker takes the pieces not yet in ANY ap12_L7/w*.done, split r::W).  Always restart all workers at once.
# usage: ./start_ap12.sh W        (from agent_runs/theory2)
W=${1:-12}
cd "$(dirname "$0")" || exit 1
T=$(pwd); PY=/Users/paullee/AI-workspace/Claude-Projects/Erdos/e982/venv/bin/python
pkill -f "$T/apex_pieces.py 12 " && sleep 3
mkdir -p ap12_L7
echo "$(date -u +%FT%TZ) start_ap12.sh W=$W (done so far: $(cat ap12_L7/w*.done 2>/dev/null | wc -l))" >> ap12_L7/restarts.log
for ((r=0; r<W; r++)); do
  ../run.sh theory2 ap12L7_w$r env APEX_L=7 RESPLIT=1 CONF_BUDGET=50000 SINGULAR=/opt/homebrew/bin/Singular PYTHONDONTWRITEBYTECODE=1 $PY $T/apex_pieces.py 12 $r $W ap12_L7 > /dev/null
done
echo "started $W workers"
