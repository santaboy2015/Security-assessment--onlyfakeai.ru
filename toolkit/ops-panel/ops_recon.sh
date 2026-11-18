#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
O=https://ops.onlyfakeai.ru
mkdir -p /tmp/ops && cd /tmp/ops || exit 1

for p in / /login /health /script.js /favicon.ico /robots.txt /admin /api /metrics /dashboard; do
  n=$(echo "$p" | tr '/' '_')
  code=$(curl -sS -k -m 20 -A "$UA" -o "$n.out" -D "$n.hdr" -w '%{http_code}' "$O$p" 2>/dev/null)
  echo "[$code] $p size=$(wc -c < "$n.out") ct=$(grep -i '^content-type' "$n.hdr" | tr -d '\r' | head -1)"
done

echo
echo "=== headers /login ==="
grep -iE '^(server|content-type|x-powered|set-cookie|cf-|location)' /login.hdr | tr -d '\r'

echo
echo "=== root body head ==="
head -c 800 _.out; echo

echo
echo "=== script.js endpoints ==="
grep -oE '"/api/[a-zA-Z0-9/_:${}.-]+"' script.js.out | sort -u | head -80
grep -oE "/api/[a-zA-Z0-9/_:.-]+" script.js.out | sort -u | head -80
