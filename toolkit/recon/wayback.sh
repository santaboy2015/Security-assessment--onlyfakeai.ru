#!/bin/bash
set -u
UA='Mozilla/5.0'
mkdir -p /tmp/wb && cd /tmp/wb || exit 1

echo "=== CDX JS entries ==="
curl -sS -m 90 -A "$UA" "http://web.archive.org/cdx/search/cdx?url=onlyfakeai.ru%2F_next%2Fstatic%2F*&output=json&limit=300&filter=mimetype:application/javascript&collapse=urlkey" -o js.json -w 'HTTP %{http_code} %{size_download}B\n'
python3 - <<'EOF'
import json
try:
    d=json.load(open('/tmp/wb/js.json'))
    rows=d[1:]
    print("js rows:",len(rows))
    for r in rows[:40]:
        print(r[1], r[2], r[6])
except Exception as e:
    print("parse fail",e)
EOF

echo
echo "=== CDX ops-ish pages ==="
curl -sS -m 60 -A "$UA" "http://web.archive.org/cdx/search/cdx?url=onlyfakeai.ru%2Fscript*&output=json&limit=20" -o scr.json -w 'HTTP %{http_code}\n'
cat scr.json | head -c 600; echo

echo
echo "=== CDX admin pages ==="
for pat in "onlyfakeai.ru%2Fadmin*" "onlyfakeai.ru%2Fapi%2F*" "onlyfakeai.ru%2F.env*"; do
  echo "--- $pat"
  curl -sS -m 45 -A "$UA" "http://web.archive.org/cdx/search/cdx?url=$pat&output=json&limit=15" | head -c 700; echo
done
