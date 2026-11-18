#!/bin/bash
set -u
BASE="https://cdn.onlyfakeai.ru/storage/v1/object/public"
for u in "id/NOPE.jpg" "psd/NOPE.jpg" "templates/NOPE.jpg" "mockups/NOPE.jpg" "ssn/NOPE.jpg" "passport_card/NOPE.jpg" "photo/NOPE.jpg" "docs/NOPE.jpg" "textures/NOPE.jpg" "assets/NOPE.jpg"; do
  echo "--- $u"
  curl -sS -k -m 15 -A "Mozilla/5.0" "$BASE/$u" | head -c 200; echo
done
