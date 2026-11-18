#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36'
O=https://ops.onlyfakeai.ru
TOK=$(cat /tmp/token.txt 2>/dev/null || true)
cd /tmp/ops || exit 1

curl -sS -k -m 20 -A "$UA" -o scriptjs.txt "$O/script.js"
echo "script.js bytes: $(wc -c < scriptjs.txt)"

echo
echo "=== all /api refs ==="
grep -oE "/api/[a-zA-Z0-9/_:.\${}-]+" scriptjs.txt | sort -u

echo
echo "=== auth/verify context ==="
python3 - <<'EOF'
s=open('/tmp/ops/scriptjs.txt',encoding='utf-8',errors='ignore').read()
for kw in ["auth/verify","adminToken","isSuperAdmin","Authorization","login"]:
    i=s.find(kw)
    print("="*8, kw, i)
    if i>=0: print(s[max(0,i-400):i+500])
EOF

echo
echo "=== live endpoint probes with user JWT ==="
probe() {
  local m="$1" p="$2"
  echo "--- $m $p"
  if [ -n "${TOK:-}" ]; then
    curl -sS -k -m 20 -A "$UA" -X "$m" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
      -o /tmp/o.bin -w 'HTTP %{http_code} %{size_download}B\n' -d '{}' "$O$p"
  else
    curl -sS -k -m 20 -A "$UA" -X "$m" -H 'Content-Type: application/json' -o /tmp/o.bin -w 'HTTP %{http_code} %{size_download}B\n' -d '{}' "$O$p"
  fi
  head -c 300 /tmp/o.bin; echo
}
probe GET /api/admin
probe GET /api/profiles
probe GET /api/jobs
probe GET /api/jobs/stats
probe GET /api/analytics
probe GET /api/analytics/admin
probe POST /api/auth/verify
