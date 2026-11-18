#!/usr/bin/env python3
"""PROPOSAL B — SINGLE approved INSERT probe against `messages` ONLY (Lead-approved, one attempt).
Marker row; user_id = our test uid. No retries, no other tables, no further inserts."""
import ssl, json, time, uuid, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
URL = "https://onlyfakeai.ru/api/supabase/rest/v1/messages"
KEY = "<publishable-key>"
UID = "<redacted-user-uuid>"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]
MARK = "AUDIT-PROBE app-layer-specialist 2026-11-11 — non-destructive RLS insert test (safe to delete)"
row = {
    "user_id": UID,
    "conversation_id": str(uuid.uuid4()),
    "prompt": MARK,
    "model": "audit-probe",
}
hdr = {
    "User-Agent": UA,
    "apikey": KEY,
    "Authorization": "Bearer " + TOK,
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}
body = json.dumps(row).encode()
rq = urllib.request.Request(URL, data=body, headers=hdr, method="POST")
print("POST", URL)
print("body:", body.decode())
try:
    with op.open(rq, timeout=25) as x:
        st, hd, b = x.status, dict(x.headers), x.read()
except urllib.error.HTTPError as e:
    st, hd, b = e.code, dict(e.headers), e.read()
except Exception as e:
    st, hd, b = 0, {}, str(e).encode()
print("RESULT ->", st, "content-range:", hd.get("content-range"))
print("body:", b.decode("utf-8", "ignore")[:1200])
print("VERDICT:",
      "INSERT ALLOWED (row created)" if st in (200, 201) else
      "RLS INSERT DENIED/services blocked" if st in (401, 403) else
      "BLOCKED/validation error" if st in (400,) else
      "other/unexpected")
