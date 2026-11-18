#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
NOW=1794321000000   # approx 2026-11-10T14:30Z

echo "=== status sweep: one probe per hour, last 24h (status only, no URLs saved) ==="
for i in $(seq 0 23); do
  id=$((NOW - i*3600000))
  body=$(curl -sS -k -m 15 -A "$UA" "$B/api/status/$id")
  # record only top-level keys / status, strip URLs
  echo "$i $id :: $(echo "$body" | sed -E 's#https?://[^"]+#<URL-REDACTED>#g' | head -c 120)"
done

echo
echo "=== status edge probes ==="
for p in /api/status/0 /api/status/-1 /api/status/1 /api/status/9999999999999; do
  echo "[$(curl -sS -k -m 15 -A "$UA" -o /tmp/e.bin -w '%{http_code}' "$B$p")] $p :: $(head -c 150 /tmp/e.bin | tr -d '\n')"
done
