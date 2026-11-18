#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36'
O=https://ops.onlyfakeai.ru
TOK=$(cat /tmp/token.txt 2>/dev/null || true)
cd /tmp/ops || exit 1

echo "=== GET /api/auth/verify with user JWT ==="
curl -sS -k -m 20 -A "$UA" -H "Authorization: Bearer ${TOK:-none}" -o /tmp/av.bin -w 'HTTP %{http_code}\n' "$O/api/auth/verify"
head -c 500 /tmp/av.bin; echo

echo
echo "=== exposure probes ==="
for p in /.git/HEAD /.git/config /.env /package.json /server.js /index.js /app.js /.env.local /config.js /api/auth/verify /api/auth/login /api/login /login.html /script.js.bak /backup.zip /admin-users /api/admin-users; do
  code=$(curl -sS -k -m 15 -A "$UA" -o /tmp/e.bin -w '%{http_code}' "$O$p")
  size=$(wc -c < /tmp/e.bin)
  echo "[$code $size] $p"
done

echo
echo "=== login page script refs / form ==="
grep -oE '<script[^>]*src="[^"]+"' _login.out
grep -oE '(fetch|action=)[^ >]{0,80}' _login.out | head -20
grep -oE '"/api/[^"]+"' _login.out | sort -u

echo
echo "=== crt.sh subdomains ==="
curl -sS -k -m 60 "https://crt.sh/?q=%25.onlyfakeai.ru&output=json" -o /tmp/crt.json
python3 - <<'EOF'
import json,re
try:
    d=json.load(open('/tmp/crt.json'))
    names=set()
    for e in d:
        for n in (e.get('name_value') or '').split('\n'):
            n=n.strip().lower()
            if n: names.add(n)
    print("\n".join(sorted(names)))
except Exception as ex:
    print("crt parse fail:",ex)
EOF
