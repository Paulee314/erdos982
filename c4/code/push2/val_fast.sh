#!/bin/bash
# Validation of pipeline B+C (fast single solve + LRAT/cake_lpr) on the Studio, in agent_runs/c4_studio
S=/Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/c4_studio; E=/Users/paullee/AI-workspace/Claude-Projects/Erdos
export CADICAL=$S/bin/cadical LRATCHK=$E/tools/cake_lpr/cake_lpr DRAT=$S/code/drat-trim/drat-trim
PY=$S/venv/bin/python; C=$S/code/push2; V=$S/state/val; mkdir -p $V
for a in 1 2 3 4 5 6 7; do for b in 1 2 3 4 5 6 7; do echo "0:$a,1:$b"; done; done > $V/list8
echo "== V3 planted LRAT corruption"; $PY $C/val_plant.py $V/plant
echo "== V1a n=8 base only (forces SAT -> CEGAR/LP fallback + two-round cert)"
$PY $C/c4_driver2.py 8 $V/v8none fams=none list=$V/list8 slots=3 maxheavy=3 tag=$V/v8none; tail -1 $V/v8none/driver.log; cat $V/v8none/ALERTS.txt 2>/dev/null
echo "== V1b n=8 full families"
$PY $C/c4_driver2.py 8 $V/v8full fams=FGXOADKN list=$V/list8 slots=3 maxheavy=3 tag=$V/v8full; tail -1 $V/v8full/driver.log; cat $V/v8full/ALERTS.txt 2>/dev/null
echo "== V2 n=11 reruns of verified sub-cases (3,5) (4,4) (4,5)"
for c in 3_5 4_4 4_5; do a=${c%_*}; b=${c#*_}; $PY $C/c4_fastcube.py 11 $V/r11_$c fams=FGXOADKN cube=0:$a,1:$b > $V/r11_$c.log 2>&1 & done; wait
for c in 3_5 4_4 4_5; do tail -1 $V/r11_$c.log | cut -c1-600; done
echo VALDONE
