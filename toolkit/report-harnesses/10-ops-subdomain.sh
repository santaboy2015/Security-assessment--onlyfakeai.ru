#!/bin/bash
# New lead: ops.onlyfakeai.ru discovered via crt.sh (not in original scope list).
# Read-only reachability check + certificate + auth-wall identification. No credential guessing.
source "$(dirname "$0")/env.sh"

echo "########## 1. DNS for discovered hosts ##########"
for h in ops.onlyfakeai.ru www.onlyfakeai.ru cdn.onlyfakeai.ru api.onlyfakeai.ru admin.onlyfakeai.ru; do
  echo "--- $h"
  getent hosts "$h" || echo "  (no A/AAAA)"
done

echo
echo "########## 2. ops.onlyfakeai.ru TLS certificate ##########"
timeout 20 openssl s_client -connect ops.onlyfakeai.ru:443 -servername ops.onlyfakeai.ru </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null || echo "TLS handshake failed"

echo
echo "########## 3. ops.onlyfakeai.ru HTTP surface (read-only GET/HEAD) ##########"
for u in "https://ops.onlyfakeai.ru/" "https://ops.onlyfakeai.ru/login" "https://ops.onlyfakeai.ru/admin" "https://ops.onlyfakeai.ru/dashboard" "https://ops.onlyfakeai.ru/health" "https://ops.onlyfakeai.ru/api/health" "https://ops.onlyfakeai.ru/api/status" "https://ops.onlyfakeai.ru/api/broadcast" "https://ops.onlyfakeai.ru/metrics" "https://ops.onlyfakeai.ru/robots.txt" "https://ops.onlyfakeai.ru/favicon.ico"; do
  echo "--- GET $u"
  code=$(curl -sS -k -m 20 -A "$UA" -D /tmp/h.txt -o /tmp/b.bin -w "%{http_code}" "$u" 2>/dev/null || echo CONNFAIL)
  grep -iE "^(HTTP|server|location|content-type|www-authenticate|cf-|x-powered-by|set-cookie|cf-mitigated|vary)" /tmp/h.txt 2>/dev/null | sed 's/\r$//' | head -8
  echo "  bytes=$(wc -c < /tmp/b.bin 2>/dev/null) body-head=$(head -c 300 /tmp/b.bin 2>/dev/null | tr -d '\n')"
done

echo
echo "########## 4. follows redirects for ops root ##########"
curl -sS -k -m 25 -A "$UA" -L -D /tmp/h2.txt -o /tmp/ops.html -w 'final HTTP %{http_code} url=%{url_effective} bytes=%{size_download}\n' "https://ops.onlyfakeai.ru/" 2>/dev/null || echo CONNFAIL
grep -iE "^(HTTP|location)" /tmp/h2.txt | sed 's/\r$//' | head -10
echo "title: $(grep -oE '<title>[^<]*</title>' /tmp/ops.html 2>/dev/null | head -1)"

echo
echo "########## 5. Repeat crt.sh for other subdomain wildcard patterns ##########"
for q in "%25.ops.onlyfakeai.ru" "%25.api.onlyfakeai.ru" "onlyfakeai.ru"; do
  curl -sS -m 60 -A "$UA" "https://crt.sh/?q=$q&output=json" -o /tmp/crt2.json -w "crt.sh $q HTTP %{http_code} bytes=%{size_download}\n" || true
  python3 - <<'PY'
import json
try:
    d=json.load(open('/tmp/crt2.json'))
except Exception:
    raise SystemExit
names=set()
for row in d:
    for n in str(row.get('name_value','')).split('\n'):
        n=n.strip().lower()
        if n: names.add(n)
print('  names:', ', '.join(sorted(names))[:600])
PY
done

echo
echo "########## 6. /en/login redirect chain check ##########"
curl -sS -k -m 25 -A "$UA" -D - -o /dev/null "https://onlyfakeai.ru/en/login" | sed 's/\r$//' | grep -iE "^(HTTP|location|set-cookie)"
curl -sS -k -m 25 -A "$UA" -D - -o /dev/null "https://onlyfakeai.ru/en/generator" | sed 's/\r$//' | grep -iE "^(HTTP|location|set-cookie)"
echo "--- without /en prefix"
curl -sS -k -m 25 -A "$UA" -D - -o /dev/null "https://onlyfakeai.ru/login" | sed 's/\r$//' | grep -iE "^(HTTP|location|set-cookie)"
