#!/usr/bin/env python3
"""Last classification edge cases for the gateway (read-only) + raw /rest/v1 table typo response."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
KEY = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))


def g(url, hdr):
    h = {"User-Agent": UA, "Accept": "application/openapi+json"}
    h.update(hdr)
    rq = urllib.request.Request(url, headers=h)
    try:
        with op.open(rq, timeout=20) as x:
            return x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


CASES = [
    ("user-JWT as apikey (proxy)", "https://onlyfakeai.ru/api/supabase/rest/v1/",
     {"apikey": TOK}),
    ("user-JWT as apikey (canonical)", "https://<supabase-project-ref>.supabase.co/rest/v1/",
     {"apikey": TOK}),
    ("publishable+JWT-auth (canonical HEAD)", "https://<supabase-project-ref>.supabase.co/rest/v1/",
     {"apikey": KEY, "Authorization": "Bearer " + TOK}),
    ("unknown-table typo /rest/v1/profil", "https://onlyfakeai.ru/api/supabase/rest/v1/profil?select=*&limit=0",
     {"apikey": KEY, "Authorization": "Bearer " + TOK}),
    ("unknown-table typo /rest/v1/jobz", "https://onlyfakeai.ru/api/supabase/rest/v1/jobz?select=*&limit=0",
     {"apikey": KEY, "Authorization": "Bearer " + TOK}),
]
for tag, url, hdr in CASES:
    st, hd, b = g(url, hdr)
    print(f"[{tag}] -> {st} len={len(b)} :: {b.decode('utf-8','ignore')[:260]}")
    time.sleep(0.5)
