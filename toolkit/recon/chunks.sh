#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
B=https://onlyfakeai.ru
cd /tmp/ofa/app || exit 1

# generator-priority chunks
for f in \
  /_next/static/chunks/app/%5Blocale%5D/generator/page-bf5f8970043f7336.js \
  /_next/static/chunks/2452-45f7f6199c98908a.js \
  /_next/static/chunks/8794-9e09a720aa8a0cf1.js \
  /_next/static/chunks/app/%5Blocale%5D/login/page-10ca31bf4df29208.js \
  /_next/static/chunks/7737-9f185d0901d4f3fb.js \
  /_next/static/chunks/8875-e8c048e6d4ba117e.js ; do
  n=$(echo "$f" | sed 's|.*/||')
  code=$(curl -sS -k -m 25 -A "$UA" -o "$n" -w '%{http_code}' "$B$f")
  echo "[$code] $n $(wc -c < "$n")"
done

echo
echo "=== API endpoints across app chunks ==="
grep -hoE '"/api/[a-zA-Z0-9/_.?=&-]+"' *.js 2>/dev/null | tr -d '"' | sort -u

echo
echo "=== absolute URLs in gen chunks ==="
grep -hoE 'https?://[a-zA-Z0-9._-]+\.[a-z]{2,}[a-zA-Z0-9/_.?=&%-]*' *.js 2>/dev/null | sort -u | grep -viE 'react|nextjs|w3\.org|github|typekit|google|telegram\.org/js|mozilla' | head -40

echo
echo "=== storage/s3/r2 refs ==="
grep -hoiE '(s3\.amazonaws|r2\.dev|workers\.dev|supabase|firebase|blob\.core|storage|bucket|uploads?/|cdn\.onlyfake)[a-zA-Z0-9./_?=&%-]{0,60}' *.js 2>/dev/null | sort -u | head -40

echo
echo "=== shop page data: product names/prices ==="
grep -oE '"[^"]{3,60}"\s*:\s*"[^"]{0,80}"' /tmp/ofa/app/_shop.html 2>/dev/null | head -20
sed -e 's/<[^>]*>/ /g' /tmp/ofa/app/_shop.html | tr -s ' \n' ' \n' | grep -oE '\$[0-9]+(\.[0-9]+)?' | sort -u | head -30
