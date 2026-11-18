#!/bin/bash
set -u
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
UA='Mozilla/5.0'

EMAIL="rat4080$(date +%s)@dropmail.me"
PASS="NestWarm!4080x"

echo "[*] signup $EMAIL"
curl -sS -k -m 25 -A "$UA" \
  -H "apikey: $KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  -o /tmp/signup.json -w 'HTTP %{http_code}\n' "$SB/auth/v1/signup"
head -c 900 /tmp/signup.json; echo

python3 - <<'EOF'
import json
try:
    d=json.load(open('/tmp/signup.json'))
except Exception as e:
    print('no json', e); raise SystemExit
tok=d.get('access_token')
if tok:
    open('/tmp/token.txt','w').write(tok)
    print('TOKEN OK len', len(tok))
    print('user id', d.get('user',{}).get('id'))
    open('/tmp/email.txt','w').write(d.get('user',{}).get('email',''))
else:
    print('keys:', list(d.keys()))
EOF
