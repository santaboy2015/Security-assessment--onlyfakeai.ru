#!/bin/bash
set -u
cd /tmp/ops || exit 1
ls -la | head -20
echo
echo "=== health ==="
cat _health.out; echo
echo
echo "=== login body text ==="
sed -e 's/<[^>]*>/ /g' _login.out | tr -s ' \n' ' \n' | grep -vE '^\s*$' | head -30
echo
echo "=== endpoints in script.js ==="
grep -oE "['\"\`]/api/[a-zA-Z0-9/_:.$-]+" _script.js.out | tr -d "'\"\`" | sort -u | head -100
echo
echo "=== other fetches ==="
grep -oE 'fetch\([^)]{0,120}\)' _script.js.out | head -40
echo
echo "=== localStorage / token keys ==="
grep -oE '(localStorage|sessionStorage)\.[a-zA-Z]+\([^)]{0,60}\)' _script.js.out | sort -u | head -20
