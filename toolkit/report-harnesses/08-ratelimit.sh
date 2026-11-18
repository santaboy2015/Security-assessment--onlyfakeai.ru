#!/bin/bash
# Hunt 11: rate limiting / abuse controls on auth + verification endpoints (gentle, <=20 per endpoint).
source "$(dirname "$0")/env.sh"

TS=$(date +%s)

echo "########## 1. 20 rapid POST /api/verify-recaptcha (junk tokens) ##########"
START=$(date +%s%N)
for i in $(seq 1 20); do
  code=$(curl -sS -k -m 15 -A "$UA" -H "Content-Type: application/json" -X POST \
    -d "{\"token\":\"junk-$TS-$i\",\"action\":\"login\"}" -D /tmp/h.txt -o /tmp/b.bin -w "%{http_code}" "$SITE/api/verify-recaptcha")
  ra=$(grep -i "^retry-after" /tmp/h.txt | tr -d '\r' | head -1)
  echo "  #$i HTTP $code $ra $(head -c 80 /tmp/b.bin | tr -d '\n')"
done
END=$(date +%s%N)
echo "elapsed_ms=$(( (END-START)/1000000 ))"

echo
echo "########## 2. 20 rapid POST /api/auth/telegram-webapp (junk) ##########"
START=$(date +%s%N)
for i in $(seq 1 20); do
  code=$(curl -sS -k -m 15 -A "$UA" -H "Content-Type: application/json" -X POST \
    -d "{\"initData\":\"junk-$TS-$i\",\"user\":{\"id\":$i}}" -D /tmp/h.txt -o /tmp/b.bin -w "%{http_code}" "$SITE/api/auth/telegram-webapp")
  ra=$(grep -i "^retry-after" /tmp/h.txt | tr -d '\r' | head -1)
  echo "  #$i HTTP $code $ra $(head -c 80 /tmp/b.bin | tr -d '\n')"
done
END=$(date +%s%N)
echo "elapsed_ms=$(( (END-START)/1000000 ))"

echo
echo "########## 3. 8 rapid signups (unique fake emails, no captcha) ##########"
for i in $(seq 1 8); do
  email="vulnrat-rl-$TS-$<probe>@dropmail.me"
  code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"VulnRat!Audit2026\"}" -o /tmp/b.bin -w "%{http_code}" "$SUPA/auth/v1/signup")
  has=$(grep -o "access_token" /tmp/b.bin | head -1)
  echo "  signup #$i HTTP $code token=$([ -n "$has" ] && echo yes || echo no) $(head -c 120 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 4. 10 rapid wrong-password logins on our test account ##########"
EMAIL1=$(grep -oE 'rat[0-9]+[0-9]*@dropmail.me' /tmp/email.txt 2>/dev/null || true)
EMAIL1=$(python3 - <<'PY'
import base64,json
tok=open('/tmp/token.txt').read().strip()
p=tok.split('.')[1]
p+='='*(-len(p)%4)
d=json.loads(base64.urlsafe_b64decode(p))
print(d.get('email',''))
PY
)
echo "target account: $EMAIL1"
for i in $(seq 1 10); do
  code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL1\",\"password\":\"wrong-$TS-$i\"}" -o /tmp/b.bin -w "%{http_code}" "$SUPA/auth/v1/token?grant_type=password")
  echo "  login#$i HTTP $code $(head -c 120 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 5. Password policy checks ##########"
for pw in "123" "123456" "abcdef"; do
  email="vulnrat-pw-$TS-$<probe>@dropmail.me"
  code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$pw\"}" -o /tmp/b.bin -w "%{http_code}" "$SUPA/auth/v1/signup")
  echo "  password '$pw' -> HTTP $code $(head -c 160 /tmp/b.bin | tr -d '\n')"
done

echo
echo "########## 6. Password-recovery endpoint enumeration test ##########"
for email in "test2@x.com" "definitely-not-a-user-$<probe>@dropmail.me"; do
  code=$(curl -sS -k -m 20 -A "$UA" -H "apikey: $KEY" -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\"}" -o /tmp/b.bin -w "%{http_code}" "$SUPA/auth/v1/recover")
  echo "  recover '$email' -> HTTP $code $(head -c 120 /tmp/b.bin | tr -d '\n')"
done
