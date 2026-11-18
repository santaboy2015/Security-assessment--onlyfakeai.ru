#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1
F=page-bf5f8970043f7336.js

echo "=== EXAMPLE strings context ==="
grep -oE '.{150}_ID_2025-EXAMPLE\.jpg.{150}' $F | head -3
echo
echo "=== '.tj' definition (template path builder) ==="
grep -oE 'tj:\(\)=>[^,]{0,80}' $F | head -5
grep -oE 'tj=[^;]{0,600}' $F | head -3
echo
echo "=== find function that builds template paths ==="
grep -oE '.{200}getPublicUrl.{300}' $F | head -4
echo
echo "=== doc type keys ==="
for k in passport_card id_card driving_license residence ssn passport; do
  echo "--- $k"
  grep -oE ".{100}\"$k\".{180}" $F | head -2
done
