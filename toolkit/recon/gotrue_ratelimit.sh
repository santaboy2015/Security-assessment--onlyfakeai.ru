#!/bin/bash
set -u
SUP="https://cdn.onlyfakeai.ru/auth/v1/token?grant_type=password"
KEY="<publishable-key>"
UA="Mozilla/5.0"

echo "=== 10 rapid bad creds from host IP (rate-limit probe) ==="
start=$(date +%s)
for i in $(seq 1 10); do
  code=$(curl -sS -k -m 30 -A "$UA" -H "apikey: $KEY" -H 'Content-Type: application/json' \
    -d "{\"email\":\"onlyfake@tuta.io\",\"password\":\"WrongProbe$i!\"}" \
    -o /tmp/gt$i.bin -D /tmp/gth$i.hdr -w '%{http_code}' "$SUP")
  ra=$(grep -i '^retry-after' /tmp/gth$i.hdr | tr -d '\r' | head -1)
  echo "[$code] $i $ra :: $(head -c 120 /tmp/gt$i.bin)"
done
end=$(date +%s)
echo "elapsed: $((end-start))s"
