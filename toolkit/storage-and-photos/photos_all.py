import ssl, json, urllib.request, urllib.error, time

ctx = ssl.create_default_context()
KEY = "<publishable-key>"

def list_page(offset):
    body = {"prefix": "", "limit": 100, "offset": offset,
            "sortBy": {"column": "name", "order": "asc"}}
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY, "Content-Type": "application/json"}
    r = urllib.request.Request(
        "https://cdn.onlyfakeai.ru/storage/v1/object/list/photos",
        data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return e.code, []
    except Exception as e:
        return 0, []

all_names = []
offset = 0
while True:
    st, data = list_page(offset)
    if st != 200 or not data:
        print("stop at offset", offset, "st", st)
        break
    names = [e["name"] for e in data if e["name"] != ".emptyFolderPlaceholder"]
    if not names:
        break
    all_names.extend(names)
    print(f"offset {offset}: +{len(names)} (total {len(all_names)})")
    if len(data) < 100:
        break
    offset += 100
    time.sleep(0.5)

open("photos_all.txt", "w").write("\n".join(all_names))
print("total files:", len(all_names))
if all_names:
    ts = [int(n.split("_")[0]) for n in all_names if n.split("_")[0].isdigit()]
    print("ts range:", min(ts), "->", max(ts))
