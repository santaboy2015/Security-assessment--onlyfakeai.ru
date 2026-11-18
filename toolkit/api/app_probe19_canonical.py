#!/usr/bin/env python3
"""Canonical Supabase endpoint (correct project ref <supabase-project-ref>) — bypasses the cdn
custom-domain Cloudflare Worker. Read-only; goal = PostgREST OpenAPI schema."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
KEY = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
B = "https://<supabase-project-ref>.supabase.co"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))


def g(p, hdr=None):
    h = {"User-Agent": UA, "apikey": KEY}
    h.update(hdr or {})
    rq = urllib.request.Request(B + p, headers=h)
    try:
        with op.open(rq, timeout=25) as x:
            return x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


CASES = [
    ("auth health", "/auth/v1/health", {}),
    ("rest root openapi", "/rest/v1/", {"Accept": "application/openapi+json"}),
    ("rest root openapi+user", "/rest/v1/", {"Accept": "application/openapi+json",
                                             "Authorization": "Bearer " + TOK}),
    ("rest root json", "/rest/v1/", {"Accept": "application/json"}),
    ("rest root plain", "/rest/v1/", {}),
    ("rest no-slash", "/rest/v1", {"Accept": "application/openapi+json"}),
    ("profiles", "/rest/v1/profiles?select=user_id&limit=1",
     {"Authorization": "Bearer " + TOK}),
    ("admin_api_keys", "/rest/v1/admin_api_keys?select=id&limit=1",
     {"Authorization": "Bearer " + TOK}),
    ("messages", "/rest/v1/messages?select=id&limit=1",
     {"Authorization": "Bearer " + TOK}),
]
for tag, p, h in CASES:
    st, hd, b = g(p, h)
    t = b.decode("utf-8", "ignore")
    print(f"{tag} -> {st} ct={hd.get('content-type','')[:30]} len={len(b)} "
          f"gw={hd.get('sb-gateway-version','')} :: {t[:220].replace(chr(10),' ')}")
    if '"openapi"' in t or '"swagger"' in t or '"definitions"' in t:
        open("supabase_openapi_dump.json", "w", encoding="utf-8").write(t)
        print("  >>> JACKPOT saved supabase_openapi_dump.json", len(t), "bytes")
        try:
            d = json.loads(t)
            defs = d.get("definitions") or d.get("components", {}).get("schemas", {})
            print("  tables:", sorted(defs.keys()))
        except Exception as e:
            print("  parse err", e)
    time.sleep(0.6)
