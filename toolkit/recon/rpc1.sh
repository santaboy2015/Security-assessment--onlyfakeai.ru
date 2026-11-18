#!/bin/bash
set -u
UA='Mozilla/5.0'
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
TOK=$(cat /tmp/token.txt 2>/dev/null || true)

rpc() {
  local fn="$1"; local body="${2:-{\}}"
  echo "===== rpc/$fn body=$body"
  curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" ${TOK:+-H "Authorization: Bearer $TOK"} \
    -H 'Content-Type: application/json' -X POST -d "$body" -o /tmp/r.bin -w 'HTTP %{http_code} %{size_download}B\n' \
    "$SB/rest/v1/rpc/$fn"
  head -c 500 /tmp/r.bin; echo; echo
}

rpc get_jobs_time_series '{}'
rpc get_jobs_time_series '{"days":30}'
rpc get_jobs_time_series '{"period":"30d"}'
rpc get_jobs_time_series '{"interval":"day"}'
