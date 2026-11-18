#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
KEY='<publishable-key>'

qq() {
  local path="$1"; shift
  echo "===== $path"
  curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" "$@" -o /tmp/q.bin -w 'HTTP %{http_code} %{size_download}B\n' "$B$path"
  head -c 350 /tmp/q.bin; echo; echo
}

qq "/api/supabase/storage/v1/bucket"
qq "/api/supabase/rest/v1/"
qq "/api/supabase/rest/v1/profiles?select=*&limit=2"
qq "/api/supabase/auth/v1/health"
qq "/api/supabase/auth/v1/admin/users"
qq "/api/supabase/rest/v1/rpc/get_users" -X POST -H 'Content-Type: application/json' -d '{}'

echo "=== without apikey header ==="
curl -sS -k -m 20 -A "$UA" -o /tmp/q2.bin -w 'HTTP %{http_code}\n' "$B/api/supabase/rest/v1/profiles?select=*&limit=2"
head -c 300 /tmp/q2.bin; echo
