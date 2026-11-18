#!/bin/bash
set -u
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
B=https://onlyfakeai.ru
J=/tmp/tgauth

post() {
  echo "===== $1"
  curl -sS -k -m 25 -A "$UA" -H 'Content-Type: application/json' \
    -D /tmp/h.txt -o /tmp/b.txt -X POST -d "$2" "$B/api/auth/telegram-webapp"
  grep -iE '^(HTTP/|set-cookie|location|content-type)' /tmp/h.txt | tr -d '\r'
  head -c 700 /tmp/b.txt; echo; echo
}

USER_OBJ='{"id":100000001,"first_name":"Rat","username":"rat4080","language_code":"en","is_bot":false}'

# 1: raw initData
post "raw initData with user only" "{\"initData\":\"user=$(python3 -c 'import urllib.parse,json;print(urllib.parse.quote(json.dumps({"id":100000001,"first_name":"Rat","username":"rat4080"})))')\",\"user\":$USER_OBJ}"

# 2: empty initData
post "empty initData" "{\"initData\":\"\",\"user\":$USER_OBJ}"

# 3: fake hash
post "fake hash" "{\"initData\":\"user=%7B%22id%22%3A100000001%7D&auth_date=1794320000&hash=deadbeef\",\"user\":$USER_OBJ}"

# 4: no user object
post "no user object" "{\"initData\":\"user=%7B%22id%22%3A100000001%7D&auth_date=1794320000&hash=deadbeef\"}"

# 5: garbage
post "garbage" "{\"initData\":\"garbage\",\"user\":$USER_OBJ}"
