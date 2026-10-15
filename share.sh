#!/bin/bash
# share.sh file... : upload renders to Filebin (filebin.net) and print a public download link per file.
# This is the main way to get renders out of a remote agent session (chat attachments cap at ~30 MB).
# Each run uploads into a new bin with an unguessable random name; no account is used. Filebin deletes
# bins after about a week (the server sets the expiry). Anyone with a link can download, so share only renders.
set -e
[ $# -gt 0 ] || { echo "usage: share.sh file..." >&2; exit 1; }
BIN=$(head -c 10 /dev/urandom | od -An -tx1 | tr -d ' \n')
for f in "$@"; do
  size=$(stat -c %s "$f")
  name=$(python3 -c 'import sys, urllib.parse, os; print(urllib.parse.quote(os.path.basename(sys.argv[1])))' "$f")
  url=https://filebin.net/$BIN/$name ok=
  for try in 1 2 3; do
    code=$(curl -sS -o /dev/null -w '%{http_code}' --data-binary "@$f" -H 'Content-Type: application/octet-stream' "$url") || code=000
    [ "$code" = 201 ] && { ok=1; break; }
    echo "$f: upload attempt $try failed (HTTP $code)" >&2; sleep $((try * ${SHARE_RETRY_WAIT:-5}))
  done
  [ -n "$ok" ] || exit 1
  echo "$url  $(basename "$f") ($((size / 1000000)) MB, expires in about a week)"
done
