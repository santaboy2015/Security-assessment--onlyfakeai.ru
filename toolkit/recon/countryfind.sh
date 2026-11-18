#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1

echo "=== country keys from generator chunk ==="
grep -oE '"(usa|canada|uk|germany|france|italy|spain|poland|romania|estonia|lithuania|kazakhstan|indonesia|turkey|austria|bulgaria|mexico|brazil|argentina|chile|china|japan|korea|india|australia|newzealand|ireland|netherlands|belgium|switzerland|sweden|norway|finland|denmark|iceland|portugal|greece|cyprus|hungary|czech|slovakia|slovenia|croatia|serbia|ukraine|russia|georgia|armenia|israel|egypt|morocco|southafrica|nigeria|kenya|saudi|uae|qatar|kuwait|pakistan|bangladesh|srilanka|nepal|thailand|vietnam|malaysia|singapore|philippines|taiwan|hongkong)":' page-bf5f8970043f7336.js | sort -u | wc -l
grep -oE '"(usa|canada|uk)"' page-bf5f8970043f7336.js | sort -u | head

echo
echo "=== p(l,e) revision fn ==="
grep -oE 'function p\(l,e\)\{.{0,700}' 8794-9e09a720aa8a0cf1.js | head -2
echo
echo "=== revisions map ==="
grep -oE '(revisions|revision)[^;]{0,500}' 8794-9e09a720aa8a0cf1.js | head -5
