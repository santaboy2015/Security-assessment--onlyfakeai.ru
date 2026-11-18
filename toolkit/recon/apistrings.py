import re

t = open("page-bf5f8970043f7336.js", encoding="utf-8").read()

print("=== /api/ strings ===")
for m in set(re.findall(r"[\"'`]((?:https?:)?//[^\"'`]*)?(/api/[A-Za-z0-9_\-/?.=&%${}]*)[\"'`]", t)):
    print(m)

print("\n=== FormData context ===")
i = t.find("FormData")
print(t[max(0, i - 800):i + 1200].replace("\n", " ")[:2000])
