#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1
F=page-bf5f8970043f7336.js

echo "=== submit-photoshop-job full body construction ==="
grep -oE '.{900}submit-photoshop-job.{250}' $F | head -2
echo
echo "=== status poll ==="
grep -oE '.{200}\/api\/status.{300}' $F | head -3
echo
echo "=== no-watermark call ==="
grep -oE '.{300}no-watermark.{300}' $F | head -3
echo
echo "=== remove-background body ==="
grep -oE '.{200}remove-background.{400}' $F | head -3
