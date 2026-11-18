#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36'

echo "=== host sweep: DNS + HTTP fingerprint ==="
for h in ops cdn www s3 mail ftp smtp webmail imap pop vpn proxy panel admin api app dev staging test ci git gitlab jenkins minio storage files upload img media static docs wiki db sql pg redis control server node bot worker jobs gen crm dashboard connect tunnels tunnel origin backend internal vault auth sso; do
  host="$h.onlyfakeai.ru"
  ips=$(dig +short +time=2 +tries=1 "$host" A | head -2 | tr '\n' ' ')
  [ -z "$ips" ] && continue
  out=$(curl -sS -k -m 8 -A "$UA" -o /tmp/h.bin -w '%{http_code}|%{size_download}|%{content_type}' "https://$host/" 2>/dev/null)
  body=$(head -c 90 /tmp/h.bin | tr -d '\n\r')
  echo "$h :: $ips| $out | $body"
done
