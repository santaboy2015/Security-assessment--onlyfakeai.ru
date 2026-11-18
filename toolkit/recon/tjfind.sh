#!/bin/bash
set -u
cd /tmp/ofa
echo "=== tj export ==="
grep -oE 'tj:\(\)=>[A-Za-z0-9_$]+' js/*.js app/*.js loginjs/*.js 2>/dev/null | sort -u
echo
echo "=== modules with .d maps containing tj ==="
grep -lE 'tj:\(\)=>' js/*.js app/*.js loginjs/*.js 2>/dev/null
echo
echo "=== B8 / R3 exports ==="
grep -oE '.{200}B8:\(\)=>[A-Za-z0-9_$]{1,3}.{100}' js/*.js app/*.js loginjs/*.js 2>/dev/null | head -3
echo
echo "=== filename year patterns in 8794 ==="
grep -oE '"[A-Za-z0-9_ -]{3,50}\.(jpg|jpeg|png)"' app/8794-9e09a720aa8a0cf1.js | sort -u | head -40
