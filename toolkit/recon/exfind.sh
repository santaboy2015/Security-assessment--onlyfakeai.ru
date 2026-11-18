#!/bin/bash
set -u
cd /tmp/ofa || exit 1
echo "=== which files contain EXAMPLE ==="
grep -rl 'EXAMPLE' js loginjs app 2>/dev/null

echo
echo "=== context ==="
grep -rhoE '.{200}EXAMPLE\.jpg.{200}' js loginjs app 2>/dev/null | head -6

echo
echo "=== function around ==="
grep -rhoE 'function [A-Za-z0-9_$]{1,4}\([A-Za-z0-9_$,]{0,40}\)\{[^}]{0,400}EXAMPLE[^}]{0,300}\}' js loginjs app 2>/dev/null | head -3
