#!/bin/bash
set -u
SB='https://cdn.onlyfakeai.ru'
KEY='<publishable-key>'
TOK=$(cat /tmp/token.txt 2>/dev/null || true)
UA='Mozilla/5.0'

echo "=== pg_graphql introspection ==="
curl -sS -k -m 25 -A "$UA" -H "apikey: $KEY" ${TOK:+-H "Authorization: Bearer $TOK"} \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __schema { queryType { name } mutationType { name } types { name kind } } }"}' \
  -o /tmp/gql.bin -w 'HTTP %{http_code} %{size_download}B\n' "$SB/graphql/v1"
head -c 1000 /tmp/gql.bin; echo

echo
echo "=== functions via gql type names if available ==="
grep -oE '"name":"[A-Za-z0-9_]+"' /tmp/gql.bin | sort -u | head -40

echo
echo "=== subfinder ==="
subfinder -d onlyfakeai.ru -silent 2>/dev/null | sort -u
