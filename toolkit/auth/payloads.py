import re

t = open("page-bf5f8970043f7336.js", encoding="utf-8").read()

for needle in ["submit-photoshop-job", "generate-qr", "generate-code128",
               "remove-background", "generate-itf", "generate-datamatrix",
               "generate-pdf417", "generate-code39"]:
    idxs = [m.start() for m in re.finditer(re.escape(needle), t)]
    print("=" * 20, needle, "x", len(idxs))
    for i in idxs[:2]:
        a = max(0, i - 500)
        z = min(len(t), i + 800)
        print(t[a:z].replace("\n", " ")[:1300])
        print("---")
