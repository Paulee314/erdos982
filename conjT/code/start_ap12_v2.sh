#!/bin/bash
# T* at n = 12 (refute "Z_p >= 7 at every vertex"), v2 driver apex_v2.py: v13 encoding + static families G, X, O (Wonder
# referee v2_bench/wonder_GXO_referee.txt: SOUND) + lazy Lambda before Singular; tag v2[G+X+O+LAM]md5=70af391df465.
# FROZEN piece list, never RESPLIT: ap12_L7_v2/pieces_todo.txt = kept pieces minus the DISTINCT pieces done by v1 in
# ap12_L7/ (made ONCE by make_piecelist.py; md5 in ap12_L7_v2/pieces_todo.md5; this script never regenerates it).
# Restart-safe and re-sizable: stops ALL running apex_v2.py n=12 workers, then starts W workers; worker r takes
# list[r::W] (disjoint, covering the list for any W) and skips any piece already in ap12_L7_v2/w*.done.
# ap12_L7/ is the untouched v1 record.  Audit: check_run_v7.py 12 ap12_L7_v2 7 --v1dir ap12_L7 --piecelist <list>
# usage: ./start_ap12_v2.sh W        (from agent_runs/theory2)
W=${1:-16}
cd "$(dirname "$0")" || exit 1
T=$(pwd); PY=/Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/tests_abc/venv/bin/python
OUT=ap12_L7_v2; LIST=$OUT/pieces_todo.txt
[ -s "$LIST" ] || { echo "missing frozen list $LIST (create it once with make_piecelist.py)"; exit 1; }
[ "$(md5 -q $LIST)" = "$(cat $OUT/pieces_todo.md5)" ] || { echo "frozen list md5 mismatch -- refusing to start"; exit 1; }
pkill -f "$T/apex_v2.py 12 " && sleep 3
echo "$(date -u +%FT%TZ) start_ap12_v2.sh W=$W list md5 $(cat $OUT/pieces_todo.md5) ($(wc -l < $LIST) pieces; v2 done so far: $(cat $OUT/w*.done 2>/dev/null | wc -l))" >> $OUT/restarts.log
for ((r=0; r<W; r++)); do
  ../run.sh theory2 ap12L7v2_w$r env APEX_L=7 CONF_BUDGET=2000000 TSTAR_FAMS=G,X,O TSTAR_LAMBDA=1 PIECE_LIST=$LIST SINGULAR=/opt/homebrew/bin/Singular PYTHONDONTWRITEBYTECODE=1 $PY $T/apex_v2.py 12 $r $W $OUT > /dev/null
done
echo "started $W workers"
