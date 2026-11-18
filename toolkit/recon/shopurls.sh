#!/bin/bash
set -u
cd /tmp/ofa
echo "=== all storage URLs in shop page ==="
grep -ohE 'https%3A%2F%2Fcdn\.onlyfakeai\.ru%2Fstorage%2Fv1%2Fobject%2Fpublic%2F[^&"\\]+' app/_shop.html | sed 's/%2F/\//g;s/%3A/:/g;s/%2E/./g;s/%20/ /g;s/%2D/-/g;s/%5F/_/g' | sort -u > /tmp/ofa/shop_urls.txt
wc -l < /tmp/ofa/shop_urls.txt
head -20 /tmp/ofa/shop_urls.txt
echo
echo "=== buckets in shop urls ==="
sed -E 's|.*/object/public/([^/]+)/.*|\1|' /tmp/ofa/shop_urls.txt | sort | uniq -c
echo
echo "=== doc dirs ==="
sed -E 's|.*/object/public/[^/]+/([^/]+)/.*|\1|' /tmp/ofa/shop_urls.txt | sort | uniq -c
