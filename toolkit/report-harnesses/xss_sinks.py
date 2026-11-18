#!/usr/bin/env python3
"""Find template-literal interpolations in ops dashboard script.js that render DB/user values
without an obvious escapeHtml() wrapper (stored-XSS candidate detection)."""
import re

PATH = "<WORKSPACE>/rehost/report/evidence/raw/ops-script.js"
src = open(PATH, encoding="utf-8", errors="replace").read()
lines = src.split("\n")
SUSPECT = re.compile(
    r"(email|remark|first_?name|last_?name|middle_?name|city|country|address|doc_?number|status|"
    r"activePlan|ban_?reason|banned_by|secret_?key|api_?key|admin_?email|document_?type|"
    r"user_?agent|error|details|message|name)\b",
    re.I,
)

hits = []
for i, line in enumerate(lines, 1):
    if i < 400 or i > 2266:
        continue
    for m in re.finditer(r"\$\{([^{}]{1,300})\}", line):
        expr = m.group(1)
        if "escapeHtml" in expr:
            continue
        # numeric / formatting helpers are safe
        if re.match(r"^[\s\d.+\-*/()]+$", expr):
            continue
        if re.search(r"(toLocaleString|toFixed|Number\(|\.length|getSortIcon|JSON\.|Math\.|Date\.)", expr):
            continue
        if SUSPECT.search(expr):
            hits.append((i, expr.strip()[:240], line.strip()[:300]))

print(f"unescaped-suspect interpolations: {len(hits)}")
for i, expr, line in hits:
    print(f"\nline {i}: ${{{expr}}}")
    print(f"  ctx: {line}")

print("\n\n===== getPlanBadge / getSortIcon / modal builders =====")
for name in ["function getPlanBadge", "function getSortIcon", "function editProfile", "function editJob", "function showEditModal", "function renderTopUsers", "function renderAdminBreakdown", "function loadAdmins", "function loadApiKeys"]:
    idx = src.find(name)
    if idx >= 0:
        print(f"\n----- {name} -----")
        print(src[idx:idx + 2500])
