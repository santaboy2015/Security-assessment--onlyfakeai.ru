#!/bin/bash
set -u
cd /tmp/ofa || exit 1
echo "=== telegram-webapp auth body/fields in login chunks ==="
grep -rhoE '.{200}telegram-webapp.{400}' loginjs app js 2>/dev/null | head -6
echo
echo "=== initData usage ==="
grep -rhoE '.{150}initData.{250}' loginjs app js 2>/dev/null | head -8
echo
echo "=== telegram-oidc/start ==="
grep -rhoE '.{100}telegram-oidc.{200}' loginjs app js 2>/dev/null | head -4
echo
echo "=== telegram auth in gen chunk ==="
grep -hoE '.{120}(webApp|Telegram|initDataUnsafe).{200}' app/page-bf5f8970043f7336.js 2>/dev/null | head -6
