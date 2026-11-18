#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'

echo "=== ageGroup values ==="
grep -oE '.{60}ageGroup.{120}' /tmp/ofa/app/*.js | head -10
echo
echo "=== v[l] fallback structure ==="
grep -oE 'var v=[^;]{0,900}' /tmp/ofa/app/8794-9e09a720aa8a0cf1.js | head -2

echo
echo "=== try ageGroups ==="
for g in male female; do
 for a in young adult middle-aged middle aged old senior child teen 18-25 25-35 35-45 45-55 55-65 65+; do
  r=$(curl -sS -k -m 10 -A "$UA" -o /tmp/pp.bin -w '%{http_code}' "https://onlyfakeai.ru/api/portraits/list?gender=$g&ageGroup=$a")
  s=$(head -c 120 /tmp/pp.bin)
  echo "$r $g/$a :: $s"
 done
done
