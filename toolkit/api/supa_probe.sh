#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
H1="apikey: $KEY"
H2="Authorization: Bearer $KEY"

q() {
  local path="$1"
  echo "===== $path"
  curl -sS -k -m 20 -A "$UA" -H "$H1" -H "$H2" -H 'Accept: application/json' -o /tmp/sb.bin -w 'HTTP %{http_code} %{size_download}B\n' "$SB$path"
  head -c 600 /tmp/sb.bin; echo; echo
}

q /rest/v1/
q /auth/v1/health
q /storage/v1/bucket
q /storage/v1/object/list/portraits-public
q /storage/v1/object/list/backgrounds
q /storage/v1/object/list/photos
q /storage/v1/object/list/id
q /storage/v1/object/list/passport
q /rest/v1/profiles?select=*&limit=1
q /rest/v1/users?select=*&limit=1
q /rest/v1/generations?select=*&limit=1
q /rest/v1/orders?select=*&limit=1
