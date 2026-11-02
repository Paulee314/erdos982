#!/bin/bash
# Upload the packaged n = 12 proofs to a NEW Zenodo DRAFT (it does not publish; you review and press Publish on zenodo.org).
# Run it yourself in Terminal:
#   cd ~/AI-workspace/Claude-Projects/Erdos/e982/zenodo_n12
#   read -s ZENODO_TOKEN && export ZENODO_TOKEN     # paste a personal access token (scopes: deposit:write, deposit:actions)
#   ./upload_to_zenodo.sh
# The token is only read from your environment; it is not written anywhere.
set -e; cd $(dirname $0)
[ -n "$ZENODO_TOKEN" ] || { echo "ZENODO_TOKEN is not set"; exit 1; }
API=https://zenodo.org/api
resp=$(curl -sS -X POST "$API/deposit/depositions" -H "Authorization: Bearer $ZENODO_TOKEN" -H "Content-Type: application/json" -d @metadata.json)
id=$(echo "$resp" | /usr/bin/python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
bucket=$(echo "$resp" | /usr/bin/python3 -c 'import sys,json; print(json.load(sys.stdin)["links"]["bucket"])')
echo "draft deposition $id created"
for f in README_dataset.md SHA256SUMS n12_proofs_*.tar.part*; do
  echo "uploading $f ($(du -h "$f" | cut -f1))"
  curl -sS --fail --retry 3 -o /dev/null -H "Authorization: Bearer $ZENODO_TOKEN" --upload-file "$f" "$bucket/$f"
done
echo "done: review and publish at https://zenodo.org/uploads/$id"
