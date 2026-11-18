#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
B=https://onlyfakeai.ru
mkdir -p /tmp/ofa/pages /tmp/ofa/sub

for p in /en/login /en/live360 /en/rate /en/documentation /en/terms /en/faq /en/blog; do
  n=$(echo "$p" | tr '/' '_')
  code=$(curl -sS -k -m 25 -A "$UA" -o "/tmp/ofa/pages/$n.html" -w '%{http_code}' "$B$p")
  echo "[$code] $p -> $(wc -c < /tmp/ofa/pages/$n.html) bytes"
done

echo "=== login page scripts ==="
grep -oE '/_next/static/chunks/[^"]+\.js' /tmp/ofa/pages/_en_login.html | sort -u

echo
echo "=== live360 / rate body snippets ==="
for f in /tmp/ofa/pages/_en_live360.html /tmp/ofa/pages/_en_rate.html; do
  echo "--- $f"
  grep -oE 'https?://[a-zA-Z0-9._-]+\.[a-z]{2,}[^"'"'"' <)]*' "$f" | sort -u | head -20
done

echo
echo "=== subdomain brute ==="
for s in api admin app bot panel dashboard auth generator pay payment storage files cdn r2 s3 upload cdn2 static img media db sql pg redis minio backend internal dev staging test vpn mail ftp webmail ns1; do
  r=$(dig +short +time=2 +tries=1 "$s.onlyfakeai.ru" A | head -2 | tr '\n' ' ')
  if [ -n "$r" ]; then echo "$s.onlyfakeai.ru -> $r"; fi
done
