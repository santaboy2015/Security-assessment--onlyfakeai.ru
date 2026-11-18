#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
cd /tmp/ofa/app || exit 1

curl -sS -k -m 25 -A "$UA" -o shop_page.js "$B/_next/static/chunks/app/%5Blocale%5D/shop/%5B%5B...params%5D%5D/page-eab1bba31e1ae7e0.js"
echo "shop chunk $(wc -c < shop_page.js)"

echo
echo "=== endpoints in shop chunk ==="
grep -oE '"/api/[a-zA-Z0-9/_.?=&-]+"' shop_page.js | sort -u
grep -oE 'fetch\("[^"]+"' shop_page.js | head -20

echo
echo "=== keywords ==="
grep -oE '(product|template|psd|download|price)[A-Za-z]*' shop_page.js | sort | uniq -c | sort -rn | head -20

echo
echo "=== product route chunk discovery ==="
curl -sS -k -m 20 -A "$UA" -o /tmp/prod.html -w 'prod page HTTP %{http_code}\n' "$B/en/product/1"
grep -oE '/_next/static/chunks/[^"]+\.js' /tmp/prod.html | sort -u | head -20
