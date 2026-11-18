#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36'
O=https://ops.onlyfakeai.ru
cd /tmp/ops || exit 1

try() {
  local label="$1"; shift
  echo "--- $label"
  curl -sS -k -m 25 -A "$UA" -X POST -H 'Content-Type: application/json' "$@" \
    -d '{"email":"nobody@example.com","password":"wrongpass123"}' \
    -o /tmp/l.bin -D /tmp/l.hdr -w 'HTTP %{http_code} %{time_total}s\n' "$O/api/auth/login"
  grep -iE '^(retry-after|x-ratelimit|cf-)' /tmp/l.hdr | tr -d '\r' | head -5
  head -c 250 /tmp/l.bin; echo
}

try "plain"
try "XFF spoof 1" -H 'X-Forwarded-For: 203.0.113.77'
try "XFF spoof 2" -H 'X-Forwarded-For: 198.51.100.23' -H 'X-Real-IP: 198.51.100.23'
try "CF-Connecting-IP spoof" -H 'CF-Connecting-IP: 203.0.113.99'
try "True-Client-IP" -H 'True-Client-IP: 203.0.113.55'
