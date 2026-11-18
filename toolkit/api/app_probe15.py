#!/usr/bin/env python3
"""Final read-only prep for the single approved INSERT:
 - extra column names for messages
 - data-type probe for conversation_id (uuid vs text) via invalid filter
 - verify exact own-row visibility semantics"""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru/api/supabase"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]
AUTH = {"apikey": KEY, "Authorization": "Bearer " + TOK}


def r(method, url, h=None, b=None):
    hh = {"User-Agent": UA}
    hh.update(h or {})
    rq = urllib.request.Request(url, data=b, headers=hh, method=method)
    try:
        with op.open(rq, timeout=20) as x:
            return x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


more = """response result output output_url result_url generated_url generated_image_url
generated_video_url image_urls video_urls model provider tokens tokens_used credits_used
credits duration elapsed role is_read read_at seen delivered error error_message completed_at
processed_at archived favorite pinned message_id tg_message_id chat_id user_prompt input
instruction size quality aspect_ratio seed batch_id request_id job_id photo_id""".split()
found = []
for c in more:
    st, hd, b = r("GET", f"{BASE}/rest/v1/messages?select={c}&limit=0", AUTH)
    if st == 200:
        found.append(c)
        print(f"  EXISTS: {c}")
    time.sleep(0.08)
print("== extra found:", found)

print("\n== type probes (read-only) ==")
for tag, q in [
    ("conversation_id as text", "conversation_id=eq.auditprobe"),
    ("conversation_id as uuid", "conversation_id=eq.11111111-1111-4111-8111-111111111111"),
    ("id is uuid", "id=eq.11111111-1111-4111-8111-111111111111"),
    ("prompt as text", "prompt=ilike.*auditprobe*"),
    ("user_id filter", "user_id=eq.<redacted-user-uuid>"),
]:
    st, hd, b = r("GET", f"{BASE}/rest/v1/messages?select=*&{q}&limit=1", AUTH)
    print(f"  {tag} -> {st}: {b[:180].decode('utf-8','ignore')}")
    time.sleep(0.2)

print("\n== does own-row SELECT work if rows existed? (policy probe via count) ==")
st, hd, b = r("GET", f"{BASE}/rest/v1/messages?select=id&limit=1", {**AUTH, "Prefer": "count=exact"})
print("  count headers:", hd.get("content-range"), "->", b[:100])
