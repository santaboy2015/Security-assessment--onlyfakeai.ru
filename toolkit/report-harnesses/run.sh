#!/bin/bash
# Runner: execute evidence scripts, tee full output into raw/<name>.log, print summary.
# Usage: bash scripts/run.sh 00-baseline.sh 01-auth-jwt.sh ...
cd "$(dirname "$0")/.." || exit 1
mkdir -p raw
for s in "$@"; do
  name="${s%.sh}"
  echo "===== RUN $name ====="
  bash "scripts/$s" 2>&1 | tee "raw/$name.log" > /dev/null
  lines=$(wc -l < "raw/$name.log")
  bytes=$(wc -c < "raw/$name.log")
  echo "----- $name done: $lines lines, $bytes bytes -> raw/$name.log"
done
