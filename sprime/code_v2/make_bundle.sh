#!/bin/bash
# Build cert_n<n>/ from final_certify2 output prefix OUT (OUT_final.cnf/.drup, OUT_lambda_ok.jsonl) and verify it.
# Usage: make_bundle.sh n FAMS OUT [DRAT]
set -e
H=$(cd "$(dirname "$0")" && pwd); n=$1; F=$2; O=$3; DRAT=${4:-${DRAT:-$H/../drat-trim/drat-trim}}
B=$(dirname $O)/bundle_n$n; mkdir -p $B/code $B/sat
cp $H/check_lambda_certs.py $H/regen_cnf2.py $B/code/; cp $H/../sat/{testA_sat.py,e982lib.py,angle_fams.py,angle_fams2.py} $B/sat/
mkdir -p $B/generators; for f in cegar2.py angle_lp.py mec_rows.py circle_rows.py hinge_rows.py delta_rows.py sigma.py final_certify2.py certify_lits.py manifest.py; do [ -f $H/$f ] && cp $H/$f $B/generators/; done
cp ${O}_final.cnf $B/sprime${n}.cnf; cp ${O}_final.drup $B/sprime${n}.drup; cp ${O}_lambda_ok.jsonl $B/lambda_clauses_n${n}.jsonl
cat > $B/verify.sh <<EOS
#!/bin/bash
# Checks: (1) exact Farkas certificates of every learned clause, (2) the CNF equals the one regenerated from the
# generators + the clause file, (3) drat-trim on the DRUP proof.  DRAT=<path to drat-trim>
set -e; cd "\$(dirname "\$0")"; DRAT=\${DRAT:-$DRAT}; PY=\${PY:-python3}
echo "[1] certificates"; \$PY code/check_lambda_certs.py $n lambda_clauses_n$n.jsonl | tail -1
echo "[2] CNF identity"; \$PY code/regen_cnf2.py '$n' $F lambda_clauses_n$n.jsonl regen.cnf
\$PY - <<'PY'
def cls(fn):
    return sorted(tuple(sorted(int(x) for x in l.split()[:-1])) for l in open(fn) if l[0] not in 'pc')
a, b = cls('regen.cnf'), cls('sprime$n.cnf'); print("    regenerated == shipped:", a == b, len(a)); assert a == b
PY
rm -f regen.cnf
echo "[3] DRUP"; \$DRAT sprime$n.cnf sprime$n.drup -t 500000 | tr "\r" "\n" | grep -E "s VERIFIED|s NOT VERIFIED|lemmas in core"
shasum -a 256 sprime$n.cnf sprime$n.drup lambda_clauses_n$n.jsonl 2>/dev/null || sha256sum sprime$n.cnf sprime$n.drup lambda_clauses_n$n.jsonl
EOS
chmod +x $B/verify.sh; DRAT=$DRAT PY=${PY:-python3} $B/verify.sh
${PY:-python3} $H/manifest.py $B $n $F
