#!/bin/bash
set -u
BASE="https://cdn.onlyfakeai.ru/storage/v1/object/public"

echo "=== bucket existence oracle sweep ==="
for b in id dl residence passport product portraits-public photos backgrounds files uploads upload public private png jpeg jpg documents generated output outputs jobs watermarks no-watermark previews temp thumbnails signatures logos icons mockups psd templates raw assets data storage backup backups user users thumbnails-small texture textures originals masters examples samples cards docs card passport-id idcard id-card driving residence-permit permit selfies selfie faces portraits faces-public avatars avatars-public backgrounds-public inputs results renders gfx media img images; do
  r=$(curl -sS -k -m 10 -A "Mozilla/5.0" "$BASE/$b/.probe-nope" 2>/dev/null)
  case "$r" in
    *NoSuchBucket*) : ;;
    *NoSuchKey*) echo "EXISTS: $b" ;;
    *) echo "OTHER : $b :: $(echo "$r" | head -c 80)" ;;
  esac
done
