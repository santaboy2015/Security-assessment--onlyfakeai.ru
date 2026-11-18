#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
mkdir -p /tmp/ofa/shop

for u in "/shop" "/shop?page=2" "/en/shop" "/en/shop?page=2" "/shop/2" "/shop/page/2"; do
  n=$(echo "$u" | tr '/?=&' '_____')
  code=$(curl -sS -k -m 25 -A "$UA" -o "/tmp/ofa/shop/$n.html" -w '%{http_code}' "$B$u")
  cnt=$(grep -oE 'Add to Cart' "/tmp/ofa/shop/$n.html" | wc -l)
  echo "[$code] $u size=$(wc -c < "/tmp/ofa/shop/$n.html") products=$cnt"
done

echo
echo "=== product links/ids in shop ==="
grep -ohE 'href="[^"]*"' /tmp/ofa/shop/_shop.html | grep -viE '\.(css|js|png|jpg|svg|ico|webmanifest)|^href="(https?://|#|/)?"' | sort -u | head -30
echo
echo "=== next data hints ==="
grep -ohE '"(id|slug|productId|templateId)":[^,]{0,30}' /tmp/ofa/shop/_shop.html | head -10
