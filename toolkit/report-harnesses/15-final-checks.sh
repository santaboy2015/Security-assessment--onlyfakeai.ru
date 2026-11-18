#!/bin/bash
# Final evidence collection: scale of public photos-bucket exposure, last cross-checks.
source "$(dirname "$0")/env.sh"

echo "########## 1. Anon listing scale of public bucket 'photos' (metadata only) ##########"
curl -sS -k -m 25 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" -X POST \
  -d '{"prefix":"","limit":100,"offset":0,"sortBy":{"column":"name","order":"asc"}}' \
  -o /tmp/photos.json -w 'anon list photos limit=100 -> HTTP %{http_code} bytes=%{size_download}\n' \
  "$SUPA/storage/v1/object/list/photos"
python3 - <<'PY'
import json
d=json.load(open('/tmp/photos.json'))
files=[x for x in d if x.get('name') and not x['name'].startswith('.')]
print('total entries returned:', len(d))
print('user files (non-placeholder):', len(files))
png=[x for x in files if (x.get('metadata') or {}).get('mimetype')=='image/png']
print('image/png files:', len(png))
print('total bytes of listed images:', sum((x.get('metadata') or {}).get('size') or 0 for x in png))
ts=[]
for x in files:
    p=x['name'].split('_')[0]
    if p.isdigit(): ts.append(int(p))
if ts:
    import datetime
    print('timestamp-prefix range:', datetime.datetime.utcfromtimestamp(min(ts)/1000).isoformat(), '->', datetime.datetime.utcfromtimestamp(max(ts)/1000).isoformat())
print('sample filename patterns (redacted middle):')
for x in files[:5]:
    n=x['name']; print('  ', n[:6]+'...'+n[-12:])
PY

echo
echo "########## 2. Anon object read (HEAD only, no content download) for 3 listed user files ##########"
python3 - <<'PY'
import json, subprocess
d=json.load(open('/tmp/photos.json'))
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
BASE="https://cdn.onlyfakeai.ru/storage/v1/object/public/photos/"
for x in [y for y in d if y.get('name') and not y['name'].startswith('.')][:3]:
    url=BASE+x['name']
    out=subprocess.run(["curl","-sS","-k","-m","20","-A",UA,"-I",url],capture_output=True,text=True).stdout
    lines=[l.strip() for l in out.splitlines() if l.lower().startswith(('http/','content-type','content-length','cache-control'))]
    print('HEAD', x['name'][:10]+'...', '->', ' | '.join(lines))
PY

echo
echo "########## 3. secret_key uniqueness oracle check (own profile only) ##########"
U1="23c8fb62-49c5-42d9-b031-906b97cd1cb4"
for val in "audit-secret-unique-$RANDOM" "x"; do
  code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -X PATCH -d "{\"secret_key\":\"$val\"}" -o /tmp/b.bin -w "%{http_code}" "$SUPA/rest/v1/profiles?user_id=eq.$U1")
  echo "PATCH secret_key='$val' -> HTTP $code : $(head -c 200 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 4. Control: regular user token role string seen by ops admin API ##########"
curl -sS -k -m 20 -A "$UA" -H "Authorization: Bearer $TOKEN" -o /tmp/b.bin -w 'GET ops /api/auth/verify -> HTTP %{http_code}\n' "https://ops.onlyfakeai.ru/api/auth/verify"
head -c 300 /tmp/b.bin; echo

echo
echo "########## 5. GoTrue settings (auth exposure to anonymous) ##########"
curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -o /tmp/b.bin -w 'GET /auth/v1/settings -> HTTP %{http_code}\n' "$SUPA/auth/v1/settings"
head -c 700 /tmp/b.bin; echo

echo
echo "########## 6. Regular user cannot reach ops admin data (summary) ##########"
for p in "/api/profiles" "/api/jobs" "/api/admin-users" "/api/admin-api-keys"; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "Authorization: Bearer $TOKEN" -o /tmp/b.bin -w "%{http_code}" "https://ops.onlyfakeai.ru$p")
  echo "  $p -> HTTP $code : $(head -c 120 /tmp/b.bin | tr -d '\n')"
done
