#!/bin/bash
# Analyse ops.onlyfakeai.ru dashboard JS (already saved as raw/ops-script.js + raw/ops-login.html).
source "$(dirname "$0")/env.sh"
OUT="$EVID/raw"

echo "=== script.js endpoint paths ==="
grep -oE '["'"'"'`]/api/[A-Za-z0-9_/:?=&.-]+' "$OUT/ops-script.js" | sort -u

echo
echo "=== fetch calls (context, first 40) ==="
grep -oE '.{120}fetch\(.{200}' "$OUT/ops-script.js" | head -40

echo
echo "=== auth / token handling ==="
grep -oE '.{100}(localStorage|sessionStorage|Authorization|Bearer |access_token|accessToken|token).{160}' "$OUT/ops-script.js" | head -25

echo
echo "=== file head (first 3000 bytes) ==="
head -c 3000 "$OUT/ops-script.js"

echo
echo "=== login.html inline <script> ==="
python3 - <<'PY'
import re
html=open('<WORKSPACE>/rehost/report/evidence/raw/ops-login.html').read()
for m in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.S):
    body=m.group(1).strip()
    if body:
        print(body[:4000])
        print('---')
PY
