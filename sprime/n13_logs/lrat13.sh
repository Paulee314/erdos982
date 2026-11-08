#!/bin/bash
# Independent re-check of S' n=13 final round: drat-trim converts the DRUP proof to LRAT, then cake_lpr
# (CakeML-verified checker) checks it against fc13fix_final.cnf. Writes LRAT13.log; deletes the LRAT file only after a VERIFIED result.
cd /Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/sprime_cegar/state
T=/Users/paullee/AI-workspace/Claude-Projects/Erdos/tools
L=../LRAT13.log
echo "start $(date -u +%FT%TZ)" > $L
nice -n 10 $T/drat-trim/drat-trim fc13fix_final.cnf fc13fix_final.drup -L fc13fix_final.lrat -t 200000 > ../lrat13_drattrim.out 2>&1
echo "drat-trim: $(grep '^s ' ../lrat13_drattrim.out | tail -1) $(date -u +%FT%TZ)" >> $L
ls -la fc13fix_final.lrat >> $L
nice -n 10 $T/cake_lpr/cake_lpr fc13fix_final.cnf fc13fix_final.lrat > ../lrat13_cake.out 2>&1
echo "cake_lpr: $(tail -1 ../lrat13_cake.out) $(date -u +%FT%TZ)" >> $L
shasum -a 256 fc13fix_final.cnf fc13fix_final.lrat >> $L
if grep -q 's VERIFIED UNSAT' ../lrat13_cake.out; then rm -f fc13fix_final.lrat; echo "LRAT deleted after VERIFIED (sha256 kept above)" >> $L; fi
echo "DONE $(date -u +%FT%TZ)" >> $L
