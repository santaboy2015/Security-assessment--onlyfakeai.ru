#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
TOK=$(cat /tmp/token.txt 2>/dev/null || true)

echo "=== remove-background: no auth, multipart, error verbosity ==="
printf 'notanimage' > /tmp/n.jpg
code=$(curl -sS -k -m 60 -A "$UA" -F "file=@/tmp/n.jpg;filename=photo.jpg" -o /tmp/rb.bin -w '%{http_code}' "$B/api/remove-background")
echo "HTTP $code size $(wc -c < /tmp/rb.bin)"
head -c 400 /tmp/rb.bin | strings | head -5; echo

echo
echo "=== status endpoint no auth, timestamp ids (limited) ==="
for id in 1794320000000 1794319000000 1794269602000; do
  code=$(curl -sS -k -m 20 -A "$UA" -o /tmp/st.bin -w '%{http_code}' "$B/api/status/$id")
  echo "[$code] $id :: $(head -c 200 /tmp/st.bin | tr -d '\n')"
done

echo
echo "=== no-watermark with token on one guessed ts (status only) ==="
if [ -n "${TOK:-}" ]; then
  code=$(curl -sS -k -m 20 -A "$UA" -H "Authorization: Bearer $TOK" -o /tmp/nw.bin -w '%{http_code}' "$B/api/no-watermark/1794320000000")
  echo "[$code] $(head -c 300 /tmp/nw.bin)"
fi

echo
echo "=== generate-signature (free) behavior ==="
code=$(curl -sS -k -m 20 -A "$UA" -H 'Content-Type: application/json' -d '{"text":"John Doe"}' -o /tmp/sig.bin -w '%{http_code}' "$B/api/generate-signature")
echo "[$code] type-size $(wc -c < /tmp/sig.bin)"; head -c 200 /tmp/sig.bin | strings | head -3
