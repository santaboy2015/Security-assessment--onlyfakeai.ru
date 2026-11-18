#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1
F=page-bf5f8970043f7336.js

echo "=== export map containing tj ==="
grep -oE 'a\.d\(e,\{[^}]{0,400}tj:[^}]{0,100}\}\)' $F | head -5
grep -oE '\{tj:\(\)=>[A-Za-z0-9_$]+\}' $F | head -5
echo
echo "=== search 'tj' token occurrences ==="
grep -o 'tj' $F | wc -l
grep -oE '.{80}(\.tj|tj:).{120}' $F | head -6
echo
echo "=== EXAMPLE variants ==="
grep -c 'EXAMPLE' $F
grep -oE '.{100}EXAMPLE.{100}' $F | head -5
echo
echo "=== buckets referenced literals ==="
grep -oE 'storage\.from\("[a-z_]+"\)' $F | sort -u
echo
echo "=== .jpg literals in chunk ==="
grep -oE '"[A-Za-z0-9_./-]{2,60}\.(jpg|jpeg|png|webp)"' $F | sort -u | head -60
