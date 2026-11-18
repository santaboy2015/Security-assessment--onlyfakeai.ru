#!/bin/bash
set -u
UA='Mozilla/5.0'
B=https://onlyfakeai.ru
OUT=/tmp/ofa/catalog
mkdir -p "$OUT"

python3 - <<'PYEOF'
import re, json, subprocess, random, time, html

B="https://onlyfakeai.ru"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
cats = ["", "passport", "id", "id-usa", "dl", "dl-usa", "residence"]
products = {}

def fetch(path):
    cb = random.randint(100000, 999999)
    url = f"{B}{path}{'&' if '?' in path else '?'}cb={cb}"
    r = subprocess.run(["curl","-sS","-k","-m","30","-A",UA,url],capture_output=True,text=True)
    return r.stdout

def parse(html_text):
    m = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html_text, flags=re.S)
    blob = "\n".join(m).encode('utf-8').decode('unicode_escape', errors='ignore')
    out = []
    # find serverData products array occurrences
    for mm in re.finditer(r'"serverData":\{"products":\[', blob):
        start = blob.find('[', mm.end()-1)
        depth=0; i=start
        while i < len(blob):
            if blob[i]=='[': depth+=1
            elif blob[i]==']':
                depth-=1
                if depth==0: break
            i+=1
        arr = blob[start:i+1]
        try:
            arr = arr.replace('\\"','"')
            data = json.loads(arr)
            out.extend(data)
        except Exception as e:
            pass
    return out

for cat in cats:
    page=1
    while page<=12:
        path = "/shop" if not cat else f"/shop/{cat}"
        path += f"?page={page}"
        h = fetch(path)
        items = parse(h)
        if not items:
            break
        new=0
        for it in items:
            pid = it.get("id")
            if pid and pid not in products:
                products[pid]=it; new+=1
        print(f"{cat or 'all'} page {page}: {len(items)} items, {new} new, total {len(products)}", flush=True)
        if new==0:
            break
        page+=1
        time.sleep(0.4)

json.dump(list(products.values()), open("/tmp/ofa/catalog/products.json","w"), indent=1)
print("TOTAL PRODUCTS:", len(products))
PYEOF
