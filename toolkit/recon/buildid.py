import re, ssl, urllib.request, json

src = open("index_raw.html", encoding="utf-8").read()
m = re.findall(r"buildId[^a-zA-Z0-9\-]+([a-zA-Z0-9\-]+)", src)
print("buildIds:", set(m))
for x in re.findall(r"/_next/static/[^\"' ]+", src):
    if "chunks/app" in x or "Manifest" in x:
        print(x)
