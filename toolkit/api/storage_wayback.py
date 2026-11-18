import ssl, json, urllib.request, urllib.error, re

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, extra=None, timeout=15):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
    }
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

print("=== storage object listing attempts ===")
for p in [
    "/storage/v1/object/photos/",
    "/storage/v1/object/photos",
    "/storage/v1/object/public/photos/",
    "/storage/v1/object/public/",
]:
    st, txt = req("GET", p)
    print(p, "->", st, txt[:200].replace("\n", " "))

print("\n=== more bucket names ===")
names = [
    "photo", "photos2", "user-photos", "public-photos", "profile-photos",
    "profile_pics", "profile-pictures", "profile-pics", "pictures",
    "pics", "media", "assets", "static", "content", "data", "archive",
    "temp", "tmp", "cache", "thumbs", "thumbnails", "watermarked",
    "no-watermark", "preview", "preview-photos", "doc-photos",
    "document-photos", "id-photos", "id-docs", "selfies", "verification",
    "proof", "source", "original", "original-photos", "uploads-photos",
    "generated-photos", "results-photos", "jobs", "job-files",
    "job-outputs", "outputs", "storage", "backups", "exports",
    "photos-bucket", "photo-bucket", "images", "img", "files",
    "documents", "docs", "inputs", "user-uploads", "uploaded",
]
for n in names:
    st, txt = req("GET", f"/storage/v1/bucket/{n}")
    if st != 400 or "NoSuchBucket" not in txt:
        print(f"bucket/{n} -> {st} {txt[:150]}")

print("\n=== edge functions ===")
for n in ["hello", "health", "generate", "process", "process-document",
          "webhook", "admin", "api", "stripe", "payment", "create-checkout",
          "telegram", "tg-webhook", "bot", "proxy", "upload", "job"]:
    st, txt = req("POST", f"/functions/v1/{n}", body={}, timeout=12)
    print(f"functions/v1/{n} -> {st} {txt[:120]}")

print("\n=== wayback CDX for ops and main ===")
for dom in ["ops.onlyfakeai.ru", "onlyfakeai.ru", "cdn.onlyfakeai.ru"]:
    try:
        url = f"https://web.archive.org/cdx/search/cdx?url={dom}*&output=json&limit=40&fl=timestamp,original,statuscode&collapse=urlkey"
        req2 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=25, context=ctx) as r:
            t = r.read().decode("utf-8", "ignore")
        print(f"\n=== CDX {dom} ===")
        print(t[:2000])
    except Exception as e:
        print(dom, "CDX err", e)
