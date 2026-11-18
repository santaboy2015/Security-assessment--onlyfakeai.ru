#!/bin/bash
# Baseline surface checks: response headers, API routes auth requirements, notable endpoints.
source "$(dirname "$0")/env.sh"

echo "########## 1. Response headers / fingerprint ($SITE) ##########"
req GET "$SITE/"
req GET "$SITE/nonexistent-page-xyz"
req GET "$SITE/api/maintenance-status"
req GET "$SITE/api/auth/telegram-webapp"
req GET "$SITE/api/broadcast"
req GET "$SITE/api/maintenance-status" -H "Authorization: Bearer $TOKEN"
req GET "$SITE/api/broadcast" -H "Authorization: Bearer $TOKEN"

echo "########## 2. Remaining API routes as-is ##########"
for p in "/api/telegram-admin-url" "/api/telegram-auth-bot-url" "/api/telegram-channel-url" "/api/telegram-oidc/start" "/api/portraits/list?gender=male&ageGroup=20s" "/api/portraits/list?gender=male&ageGroup=male"; do
  req GET "$SITE$p"
done

echo "########## 3. Unauthenticated / bogus-id API behavior ##########"
req GET "$SITE/api/no-watermark/test1"
req GET "$SITE/api/status/test1"
req GET "$SITE/api/no-watermark/1"
req GET "$SITE/api/status/1"

echo "########## 4. Bearer-authenticated probes (control; our own account) ##########"
site GET "/api/no-watermark/test1"
site GET "/api/no-watermark/1"
site GET "/api/status/test1"
site GET "/api/broadcast"
site GET "/api/auth/telegram-webapp"

echo "########## 5. POST probes with our bearer ##########"
site POST "/api/submit-photoshop-job" -H "Content-Type: application/json" -d '{}'
site POST "/api/remove-background" -H "Content-Type: application/json" -d '{}'
site POST "/api/verify-recaptcha" -H "Content-Type: application/json" -d '{}'

echo "########## 6. Well-known files ##########"
for p in "/.well-known/security.txt" "/robots.txt" "/sitemap.xml" "/_next/static/chunks/webpack-3219caacd565a7bb.js"; do
  req GET "$SITE$p"
done
