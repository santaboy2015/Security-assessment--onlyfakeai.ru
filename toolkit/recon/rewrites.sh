#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
TOK=$(cat /tmp/token.txt 2>/dev/null || true)

echo "=== product links in shop page ==="
grep -ohE 'href="/[^"]*product[^"]*"' /tmp/ofa/app/_shop.html | sort -u | head -20
grep -ohE '"/en/product/[^"]+"' /tmp/ofa/app/_shop.html | sort -u | head -10

echo
echo "=== /api/process/1 probes ==="
for m in GET POST PUT; do
  code=$(curl -sS -k -m 20 -A "$UA" -X "$m" -H 'Content-Type: application/json' ${TOK:+-H "Authorization: Bearer $TOK"} -d '{}' -o /tmp/p1.bin -w '%{http_code}' "$B/api/process/1")
  echo "[$m $code] $(head -c 200 /tmp/p1.bin)"
done

echo
echo "=== /api/status/1 probes ==="
for p in /api/status/1/ /api/status/1/test /api/status/1/abc /api/status/1/00000000-0000-0000-0000-000000000000; do
  code=$(curl -sS -k -m 20 -A "$UA" ${TOK:+-H "Authorization: Bearer $TOK"} -o /tmp/p2.bin -w '%{http_code}' "$B$p")
  echo "[$code] $p :: $(head -c 200 /tmp/p2.bin)"
done

echo
echo "=== /api/supabase/rest/v1/profiles ==="
code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: <publishable-key>" -o /tmp/p3.bin -w '%{http_code}' "$B/api/supabase/rest/v1/profiles?select=*&limit=1")
echo "[$code] $(head -c 300 /tmp/p3.bin)"

echo
echo "=== product pages ==="
for i in 1 2 3; do
  code=$(curl -sS -k -m 20 -A "$UA" -o /tmp/prod$i.html -w '%{http_code}' "$B/en/product/$i")
  echo "[$code] /en/product/$i $(wc -c < /tmp/prod$i.html)"
done
