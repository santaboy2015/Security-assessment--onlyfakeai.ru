#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
B='https://onlyfakeai.ru'

echo "=== auth settings ==="
curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" "$SB/auth/v1/settings" ; echo

echo
echo "=== site public API probes ==="
for p in \
  "/api/portraits/list?gender=male" \
  "/api/portraits/list?gender=female" \
  "/api/portraits/list" \
  "/api/maintenance-status" \
  "/api/generate-qr" \
  "/api/status/1" \
  "/api/no-watermark/1" \
  "/api/telegram-oidc/start" \
  ; do
  echo "--- $p"
  curl -sS -k -m 15 -A "$UA" -o /tmp/p.bin -w 'HTTP %{http_code} %{size_download}B CT=%{content_type}\n' "$B$p"
  head -c 400 /tmp/p.bin; echo
done

echo
echo "=== portraits fn decompile ==="
grep -oE 'async function b\(l,e\).{0,400}' /tmp/ofa/app/8794-9e09a720aa8a0cf1.js | head -3
echo "---"
grep -oE '.{80}portraits.{0,300}' /tmp/ofa/app/8794-9e09a720aa8a0cf1.js | head -6
