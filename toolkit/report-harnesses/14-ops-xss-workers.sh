#!/bin/bash
# ops dashboard: XSS sink analysis (static) + worker endpoint method matrix.
source "$(dirname "$0")/env.sh"
OPS="https://ops.onlyfakeai.ru"
OUT="$EVID/raw"

echo "########## 1. innerHTML / DOM-sink usage in dashboard JS ##########"
grep -c "innerHTML" "$OUT/ops-script.js" || true
echo "--- lines mentioning innerHTML (context trimmed) ---"
grep -oE '.{200}innerHTML.{200}' "$OUT/ops-script.js" | head -40

echo
echo "########## 2. Profile/job rendering functions (email, remarks, fields) ##########"
grep -oE '.{100}(profile\.email|p\.email|user\.email|\.remarks|remarks).{200}' "$OUT/ops-script.js" | head -30

echo
echo "########## 3. escape helpers present? ##########"
grep -oE 'function (escapeHtml|escape|sanitize)[A-Za-z]*\([^)]*\)' "$OUT/ops-script.js" | head
grep -oE '(escapeHtml|textContent =)' "$OUT/ops-script.js" | sort | uniq -c | head

echo
echo "########## 4. Worker/process endpoints method matrix ##########"
for p in "/process" "/status/1778112266686" "/status" "/api/process" "/api/status/1778112266686" "/job" "/jobs/1778112266686" "/api/jobs/1778112266686"; do
  for m in OPTIONS POST PUT; do
    case "$m" in
      OPTIONS) code=$(curl -sS -k -m 15 -A "$UA" -X OPTIONS -D /tmp/h.txt -o /tmp/b.bin -w "%{http_code}" "$OPS$p") ;;
      POST)    code=$(curl -sS -k -m 15 -A "$UA" -H "Content-Type: application/json" -X POST -d '{}' -o /tmp/b.bin -w "%{http_code}" "$OPS$p") ;;
      PUT)     code=$(curl -sS -k -m 15 -A "$UA" -H "Content-Type: application/json" -X PUT -d '{}' -o /tmp/b.bin -w "%{http_code}" "$OPS$p") ;;
    esac
    echo "  $m $p -> HTTP $code : $(head -c 140 /tmp/b.bin | tr -d '\n')"
  done
done

echo
echo "########## 5. More unauth endpoint candidates ##########"
for p in "/api/auth/refresh" "/api/auth/logout" "/api/auth/me" "/api/auth/status" "/api/version" "/api/info" "/api/telegram/webhook" "/api/telegram" "/api/webhook" "/webhook" "/api/payments/webhook" "/api/stripe/webhook" "/api/cron" "/api/tasks" "/api/queue" "/api/worker/health" "/api/server" "/api/servers/health" "/api/apis" "/api/apikeys" "/api/api-keys" "/api/plan" "/api/plans" "/api/generations" "/api/credits"; do
  code=$(curl -sS -k -m 15 -A "$UA" -o /tmp/b.bin -w "%{http_code}" "$OPS$p")
  echo "  GET $p -> HTTP $code ($(wc -c < /tmp/b.bin)b) : $(head -c 120 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 6. HTML head of dashboard: CSP / inline script context ##########"
head -c 1600 "$OUT/ops-index.html"

echo
echo "########## 7. content-security-policy header on ops pages ##########"
for p in "/" "/login"; do
  echo "--- $p"
  curl -sS -k -m 20 -A "$UA" -D - -o /dev/null "$OPS$p" | sed 's/\r$//' | grep -iE "^(HTTP|content-security-policy|x-frame-options|x-content-type-options|access-control)"
done

echo
echo "########## 8. Login response body shape for a validation error with JSON error styles ##########"
curl -sS -k -m 20 -A "$UA" -H "Content-Type: application/json" -X POST -d '{"email":"not-an-email","password":"x"}' -D /tmp/h.txt -o /tmp/b.bin -w 'HTTP %{http_code}\n' "$OPS/api/auth/login"
sed 's/\r$//' /tmp/h.txt | grep -iE "^(HTTP|content-type|set-cookie|retry-after|x-ratelimit)"
head -c 400 /tmp/b.bin; echo
