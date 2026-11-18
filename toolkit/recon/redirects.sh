#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'

echo "=== wildcard check ==="
dig +short randomnonexist1234.onlyfakeai.ru A

echo
echo "=== redirect chain login ==="
curl -sS -k -m 25 -A "$UA" -D - -o /dev/null "https://onlyfakeai.ru/en/login" | grep -iE '^(HTTP/|location|set-cookie|cf-)'

echo
echo "=== full chase ==="
curl -sS -k -m 30 -L -A "$UA" -D /tmp/hdr.txt -o /tmp/login.html "https://onlyfakeai.ru/en/login"
grep -iE '^(HTTP/|location)' /tmp/hdr.txt
echo "size: $(wc -c < /tmp/login.html)"
echo "--- scripts ---"
grep -oE '/_next/static/chunks/[^"]+\.js' /tmp/login.html | sort -u

echo
echo "=== s3 subdomain ==="
for u in https://s3.onlyfakeai.ru/ https://s3.onlyfakeai.ru/robots.txt https://s3.onlyfakeai.ru/index.html; do
  echo "--- $u"
  curl -sS -k -m 25 -A "$UA" -D - -o /tmp/s3.bin "$u" 2>&1 | grep -iE '^(HTTP/|content-type|server|x-amz|location|content-length)'
  head -c 500 /tmp/s3.bin; echo
done
