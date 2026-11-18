#!/usr/bin/env python3
"""Queue v3: brand-password-first for the 3 confirmed admin e-mails, then personal block."""
brand = [l.rstrip("\n") for l in open("/tmp/ops_pw.txt", encoding="utf-8", errors="ignore") if l.strip()][:600]
personal = [l.rstrip("\n") for l in open("/tmp/ops_queue.txt", encoding="utf-8", errors="ignore") if l.strip()][:300]
admin_emails = ["admin@onlyfakeai.ru", "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"]

rows = []
for e in admin_emails:
    for pw in brand:          # onlyfake*, Onlyfake123!, etc.
        rows.append(f"{e}:{pw}")
for e in admin_emails:
    for pw in personal:       # nazarenko..., uriel..., johnwick...
        rows.append(f"{e}:{pw}")
# lastly: give tuta another brand pass (in case earlier personal-first missed brand)
for pw in brand[:400]:
    rows.append(f"onlyfake@tuta.io:{pw}")

seen = set(); out = []
for r in rows:
    if r not in seen:
        seen.add(r); out.append(r)
open("/tmp/ops_queue3.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("queue3 rows:", len(out))
print("first 3:", out[:3])
