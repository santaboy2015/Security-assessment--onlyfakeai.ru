#!/bin/bash
# Common environment for Vuln-Rat backend audit of onlyfakeai.ru (owner-authorized).
# Evidence helper: do not run destructive requests.
KEY="<publishable-key>"
SUPA="https://cdn.onlyfakeai.ru"
SITE="https://onlyfakeai.ru"
TOKEN="$(cat /tmp/token.txt 2>/dev/null)"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
EVID="<WORKSPACE>/rehost/report/evidence"

# req METHOD URL [extra curl args...] : prints status line, interesting headers and body head
req() {
  local method="$1"; local url="$2"; shift 2
  local hdr="/tmp/last_h.txt"; local body="/tmp/last_b.txt"
  local code
  code=$(curl -sS -k -m 25 -A "$UA" -X "$method" -D "$hdr" -o "$body" -w "%{http_code}" "$@" "$url")
  echo "### $method $url -> HTTP $code ($(wc -c < "$body") bytes)"
  grep -iE "^(HTTP/|content-type|content-length|server|x-powered-by|cf-ray|access-control|retry-after|www-authenticate|location|set-cookie|vary|sb-)" "$hdr" 2>/dev/null | sed 's/\r$//'
  echo "--- body ---"
  head -c 700 "$body"; echo
  echo "----------------------------------------"
}

# supa METHOD PATH [extra curl args...] : REST/Auth call with apikey + bearer
supa() {
  local method="$1"; local path="$2"; shift 2
  req "$method" "$SUPA$path" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" "$@"
}

# supa_anon METHOD PATH [extra curl args...] : REST/Auth call with apikey only
supa_anon() {
  local method="$1"; local path="$2"; shift 2
  req "$method" "$SUPA$path" -H "apikey: $KEY" -H "Accept: application/json" "$@"
}

# site METHOD PATH [extra curl args...] : Next.js front-end API call with bearer
site() {
  local method="$1"; local path="$2"; shift 2
  req "$method" "$SITE$path" -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" "$@"
}
