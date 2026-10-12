#!/bin/bash
# share.sh file... [-t 1h|12h|24h|72h] : upload renders to Litterbox (litterbox.catbox.moe) and print
# a temporary public download link per file. This is the main way to get renders out of a remote
# agent session (chat attachments cap at ~30 MB). Links expire after the chosen time (default 72h,
# the maximum); files must be under 1 GB. Anyone with a link can download, so share only renders.
set -e
TIME=72h FILES=()
while [ $# -gt 0 ]; do
  case $1 in -t) TIME=$2; shift 2;; *) FILES+=("$1"); shift;; esac
done
[ ${#FILES[@]} -gt 0 ] || { echo "usage: share.sh file... [-t 1h|12h|24h|72h]" >&2; exit 1; }
for f in "${FILES[@]}"; do
  size=$(stat -c %s "$f")
  [ "$size" -lt 1000000000 ] || { echo "$f: over Litterbox's 1 GB limit" >&2; exit 1; }
  for try in 1 2 3; do
    url=$(curl -sS --fail --retry 2 -F reqtype=fileupload -F time="$TIME" -F "fileToUpload=@$f" \
          https://litterbox.catbox.moe/resources/internals/api.php) && [[ $url == https://* ]] && break
    echo "$f: upload attempt $try failed (${url:-no response})" >&2; url=""; sleep $((try * 5))
  done
  [ -n "$url" ] || exit 1
  echo "$url  $(basename "$f") ($((size / 1000000)) MB, expires in $TIME)"
done
