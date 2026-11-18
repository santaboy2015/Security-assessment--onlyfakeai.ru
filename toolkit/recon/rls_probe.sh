#!/bin/bash
set -u
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
TOK=$(cat /tmp/token.txt)
UA='Mozilla/5.0'

t() {
  local path="$1"
  echo "===== $path"
  curl -sS -k -m 15 -A "$UA" \
    -H "apikey: $KEY" -H "Authorization: Bearer $TOK" \
    -H 'Accept: application/json' -H 'Prefer: count=exact' \
    -o /tmp/t.bin -D /tmp/t.hdr "$SB$path"
  grep -iE '^(HTTP/|content-range)' /tmp/t.hdr | tr -d '\r'
  head -c 500 /tmp/t.bin; echo; echo
}

for tbl in profiles users user_profiles orders generations documents templates photos portraits uploads jobs payments plans products subscriptions balance tokens credits admin admins roles settings configs logs history id_cards photoshop_jobs; do
  t "/rest/v1/$tbl?select=*&limit=1"
done
