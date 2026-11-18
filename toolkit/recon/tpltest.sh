#!/bin/bash
set -u
UA='Mozilla/5.0'
SB='https://cdn.onlyfakeai.ru/storage/v1/object/public'

t() { curl -sS -k -m 15 -A "$UA" -o /dev/null -w '%{http_code} %{size_download}B  %{content_type}' "$1"; echo "  <- $1"; }

echo "=== try templates in public buckets ==="
t "$SB/id/USA_ID_2021-EXAMPLE.jpg"
t "$SB/id/USA_ID_2025-EXAMPLE.jpg"
t "$SB/id/USA_ID_2010-EXAMPLE.jpg"
t "$SB/passport/USA_Passport_2017-EXAMPLE.jpg"
t "$SB/dl/USA_DL_2025-EXAMPLE.jpg"
t "$SB/residence/USA_Residence_2020-EXAMPLE.jpg"
t "$SB/id/USA_SSN_2020-EXAMPLE.jpg"
t "$SB/product/passport/USA_Passport_2017-EXAMPLE.jpg"
t "$SB/product/id/USA_ID_2021-EXAMPLE.jpg"
echo
echo "=== product bucket guess paths ==="
t "$SB/product/passport/GERMANY_Passport_2017-EXAMPLE.jpg"
t "$SB/product/passport/USA_Passport_2017-EXAMPLE.jpg"
