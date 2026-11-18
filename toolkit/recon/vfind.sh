#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1
F=8794-9e09a720aa8a0cf1.js

echo "=== V definitions ==="
grep -oE 'function V\([^)]*\)\{.{0,500}' $F | head -3
echo "---"
grep -oE '[^A-Za-z0-9_$]V=[^;]{0,400}' $F | head -3
echo
echo "=== around EXAMPLE strings ==="
grep -oE '.{350}"_ID_2025-EXAMPLE\.jpg".{350}' $F | head -2
echo
echo "=== _DL / Passport refs context ==="
grep -oE '.{250}"_Passport_2017-EXAMPLE\.jpg".{250}' $F | head -2
