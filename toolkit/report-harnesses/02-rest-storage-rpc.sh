#!/bin/bash
# Hunt 5/6/7 + API detail: REST table exposure, storage buckets, RPC enum, recaptcha fail-closed.
source "$(dirname "$0")/env.sh"
TS=$(date +%s)

echo "########## A. REST table exposure (anon) ##########"
for t in jobs orders payments users profiles generations portraits templates subscriptions promo_codes settings config admins telegram_users sessions webhook_logs broadcasts ban_list; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Accept: application/json" -o /tmp/t.bin -w "%{http_code}" "$SUPA/rest/v1/$t?select=*&limit=1")
  echo "anon  $t -> $code : $(head -c 180 /tmp/t.bin | tr -d '\n')"
done

echo
echo "########## B. REST table exposure (authed, our own account) ##########"
for t in jobs orders payments users profiles generations portraits templates subscriptions promo_codes settings config admins telegram_users sessions webhook_logs broadcasts; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" -o /tmp/t.bin -w "%{http_code}" "$SUPA/rest/v1/$t?select=*&limit=1")
  echo "authed $t -> $code : $(head -c 180 /tmp/t.bin | tr -d '\n')"
done

echo
echo "########## C. Storage buckets ##########"
req GET "$SUPA/storage/v1/bucket" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"
for b in portraits-public photos backgrounds id dl passport residence product templates site-assets; do
  req POST "$SUPA/storage/v1/object/list/$b" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"prefix":"","limit":3,"offset":0,"sortBy":{"column":"name","order":"asc"}}'
done

echo
echo "########## D. Storage anon list (no bearer) ##########"
for b in photos backgrounds portraits-public; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" -X POST -d '{"prefix":"","limit":2,"offset":0}' -o /tmp/t.bin -w "%{http_code}" "$SUPA/storage/v1/object/list/$b")
  echo "anon list $b -> $code : $(head -c 220 /tmp/t.bin | tr -d '\n')"
done

echo
echo "########## E. Storage upload test (own files, cleaned up) ##########"
echo "vulnrat-audit-test-$TS" > /tmp/rat-probe.txt
for b in backgrounds photos portraits-public; do
  req POST "$SUPA/storage/v1/object/$b/vulnrat-audit-$TS.txt" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: text/plain" -H "x-upsert: false" --data-binary @/tmp/rat-probe.txt
done
echo "--- public fetch of uploaded probe (if any) ---"
for b in backgrounds photos portraits-public; do
  code=$(curl -sS -k -m 15 -A "$UA" -o /tmp/t.bin -w "%{http_code}" "$SUPA/storage/v1/object/public/$b/vulnrat-audit-$TS.txt")
  echo "public GET $b -> $code : $(head -c 80 /tmp/t.bin | tr -d '\n')"
done
echo "--- cleanup of our own probe files ---"
for b in backgrounds photos portraits-public; do
  req DELETE "$SUPA/storage/v1/object/$b/vulnrat-audit-$TS.txt" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"
done

echo
echo "########## F. Signed URL creation test ##########"
req POST "$SUPA/storage/v1/object/sign/photos/vulnrat-audit-$TS.txt" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"expiresIn":600}'
req POST "$SUPA/storage/v1/object/sign/photos/1620000000000_probe.png" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"expiresIn":600}'

echo
echo "########## G. RPC enumeration ##########"
for fn in exec_sql run_sql sql admin_users get_users get_all_profiles is_admin promote set_role get_profiles list_users get_user admin_get_users grant_admin update_role add_generations credit get_subscription check_payment admin_stats get_stats delete_user ban_user unban_user reset_password get_secret secrets get_job get_jobs update_job complete_job claim_generation consume_generation; do
  code=$(curl -sS -k -m 15 -A "$UA" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST -d '{}' -o /tmp/t.bin -w "%{http_code}" "$SUPA/rest/v1/rpc/$fn")
  echo "rpc $fn -> $code : $(head -c 200 /tmp/t.bin | tr -d '\n')"
done

echo
echo "########## H. verify-recaptcha fail-closed ##########"
req POST "$SITE/api/verify-recaptcha" -H "Content-Type: application/json" -d '{}'
req POST "$SITE/api/verify-recaptcha" -H "Content-Type: application/json" -d '{"token":"","action":"login"}'
req POST "$SITE/api/verify-recaptcha" -H "Content-Type: application/json" -d '{"token":"garbage-token-123","action":"login"}'
req POST "$SITE/api/verify-recaptcha" -H "Content-Type: application/json" -d '{"token":"03AGdBq24-garbage","action":"signup"}'
req POST "$SITE/api/verify-recaptcha" -H "Content-Type: application/json" -d '{"token":"test","action":"unknown_action"}'

echo
echo "########## I. Correct telegram OIDC path + locale handling ##########"
for u in "/api/auth/telegram-oidc/start" "/api/auth/telegram-oidc/start?locale=en" "/api/auth/telegram-oidc/start?locale=../../evil.com" "/api/auth/telegram-oidc/start?locale=https://evil.example" "/api/auth/telegram-oidc/start?locale=%2F%2Fevil.example"; do
  code=$(curl -sS -k -m 20 -A "$UA" -D /tmp/h.txt -o /tmp/b.bin -w "%{http_code}" "$SITE$u")
  echo "GET $u -> $code"; grep -iE "^(location|set-cookie|content-type)" /tmp/h.txt | sed 's/\r$//'; head -c 260 /tmp/b.bin; echo
done

echo
echo "########## J. CORS reflection test ##########"
req OPTIONS "$SITE/api/no-watermark/x" -H "Origin: https://evil.example" -H "Access-Control-Request-Method: GET"
req GET "$SITE/api/maintenance-status" -H "Origin: https://evil.example"
req GET "$SUPA/rest/v1/profiles?select=user_id&limit=1" -H "Origin: https://evil.example" -H "apikey: $KEY" -H "Authorization: Bearer $TOKEN"
