#!/bin/bash
# ops.onlyfakeai.ru = publicly reachable Express "Admin Dashboard"/"Admin Login".
# Read-only recon: save HTML, extract endpoints/auth mechanism, probe GET surface.
source "$(dirname "$0")/env.sh"
OPS="https://ops.onlyfakeai.ru"
OUT="$EVID/raw"

echo "########## 1. Save ops pages ##########"
curl -sS -k -m 25 -A "$UA" -o "$OUT/ops-index.html" -w 'index HTTP %{http_code} bytes=%{size_download}\n' "$OPS/"
curl -sS -k -m 25 -A "$UA" -o "$OUT/ops-login.html" -w 'login HTTP %{http_code} bytes=%{size_download}\n' "$OPS/login"
curl -sS -k -m 25 -A "$UA" -o "$OUT/ops-health.json" -w 'health HTTP %{http_code}\n' "$OPS/health"
curl -sS -k -m 25 -A "$UA" -o "$OUT/ops-robots.txt" -w 'robots HTTP %{http_code} bytes=%{size_download}\n' "$OPS/robots.txt"

echo
echo "########## 2. Scripts / links / forms in login page ##########"
grep -oE '<script[^>]*src="[^"]+"' "$OUT/ops-login.html" | head -20
grep -oE '(action|href)="[^"]+"' "$OUT/ops-login.html" | sort -u | head -20
grep -oE 'fetch\([^)]{0,120}\)' "$OUT/ops-login.html" | head -20
grep -oE '(/api/[A-Za-z0-9_/?=&.-]+)' "$OUT/ops-login.html" | sort -u | head -30

echo
echo "########## 3. Scripts / API calls in dashboard page ##########"
grep -oE '<script[^>]*src="[^"]+"' "$OUT/ops-index.html" | head -20
grep -oE 'fetch\([^)]{0,160}\)' "$OUT/ops-index.html" | head -60
grep -oE '(/api/[A-Za-z0-9_/?=&.-]+)' "$OUT/ops-index.html" | sort -u | head -60
echo "--- auth/token hints in dashboard ---"
grep -oE '.{80}(localStorage|sessionStorage|Authorization|Bearer|token|password).{120}' "$OUT/ops-index.html" | head -20

echo
echo "########## 4. Dashboard content markers ##########"
grep -oE '<(h1|h2|h3)[^>]*>[^<]{1,120}</(h1|h2|h3)>' "$OUT/ops-index.html" | head -30
grep -oE 'id="[A-Za-z0-9_-]{2,40}"' "$OUT/ops-index.html" | sort -u | head -60

echo
echo "########## 5. GET probes of likely admin/worker endpoints ##########"
for p in "/status/test1" "/status/1" "/process" "/jobs" "/users" "/api/users" "/api/jobs" "/api/stats" "/api/login" "/api/auth/login" "/api/auth" "/api/broadcast" "/api/config" "/api/settings" "/api/servers" "/api/workers" "/api/telegram" "/api/logs" "/api/payments" "/api/promocodes" "/api/credentials" "/api/export" "/api/dashboard" "/api/me" "/dashboard-data" "/stats"; do
  code=$(curl -sS -k -m 20 -A "$UA" -o /tmp/b.bin -w "%{http_code}" "$OPS$p")
  echo "GET $p -> HTTP $code ($(wc -c < /tmp/b.bin)b) : $(head -c 160 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 6. OPTIONS / allowed methods on root & login ##########"
for p in "/" "/login" "/status/test1" "/process"; do
  echo "--- OPTIONS $p"
  curl -sS -k -m 20 -A "$UA" -X OPTIONS -D - -o /dev/null "$OPS$p" | sed 's/\r$//' | grep -iE "^(HTTP|allow|access-control)"
done

echo
echo "########## 7. Headers of login POST page (same as GET) ##########"
curl -sS -k -m 20 -A "$UA" -D - -o /dev/null "$OPS/login" | sed 's/\r$//' | grep -iE "^(HTTP|content-type|set-cookie|x-powered-by|server|cf-|vary)"
