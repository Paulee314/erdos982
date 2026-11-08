#!/bin/bash
# Second attempt at the cake_lpr re-check of S' n=13 (fixed final round).
# First attempt failed at LRAT line 478: fc13fix_final.cnf contains 234 tautological clauses and 156 clauses with a
# repeated literal; drat-trim drops/normalises these, so its LRAT clause numbering no longer matches the CNF that
# cake_lpr reads. Here we write a cleaned CNF (tautologies removed -- they are satisfied by every assignment, so the
# cleaned CNF is equisatisfiable; repeated literals removed) and redo drat-trim -L + cake_lpr on it.
cd /Users/paullee/AI-workspace/Claude-Projects/Erdos/agent_runs/sprime_cegar/state
T=/Users/paullee/AI-workspace/Claude-Projects/Erdos/tools
L=../LRAT13b.log
echo "start $(date -u +%FT%TZ)" > $L
/usr/bin/python3 - <<'PY' >> $L
out = open('fc13fix_final_clean.cnf', 'w'); body = []; nv = 0; dropped = dedup = 0
for line in open('fc13fix_final.cnf'):
    if line[0] in 'pc':
        if line[0] == 'p': nv = int(line.split()[2])
        continue
    lits = [int(x) for x in line.split()[:-1]]
    s = set(lits)
    if any(-l in s for l in s): dropped += 1; continue
    u = list(dict.fromkeys(lits))
    if len(u) != len(lits): dedup += 1
    body.append(' '.join(map(str, u)) + ' 0\n')
out.write('p cnf %d %d\n' % (nv, len(body))); out.writelines(body); out.close()
print('clean CNF: kept', len(body), 'dropped tautologies', dropped, 'deduplicated', dedup)
PY
nice -n 10 $T/drat-trim/drat-trim fc13fix_final_clean.cnf fc13fix_final.drup -L fc13fix_final_clean.lrat -t 200000 > ../lrat13b_drattrim.out 2>&1
echo "drat-trim: $(grep '^s ' ../lrat13b_drattrim.out | tail -1) $(date -u +%FT%TZ)" >> $L
nice -n 10 $T/cake_lpr/cake_lpr fc13fix_final_clean.cnf fc13fix_final_clean.lrat > ../lrat13b_cake.out 2>&1
echo "cake_lpr: $(tail -1 ../lrat13b_cake.out) $(date -u +%FT%TZ)" >> $L
shasum -a 256 fc13fix_final_clean.cnf fc13fix_final_clean.lrat >> $L
if grep -q 's VERIFIED UNSAT' ../lrat13b_cake.out; then rm -f fc13fix_final_clean.lrat fc13fix_final.lrat; echo "LRAT files deleted after VERIFIED (sha256 kept)" >> $L; fi
echo "DONE $(date -u +%FT%TZ)" >> $L
