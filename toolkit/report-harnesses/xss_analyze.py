#!/usr/bin/env python3
"""Static analysis of ops dashboard script.js for XSS sinks and escaping of user-controlled fields."""
import re

PATH = "<WORKSPACE>/rehost/report/evidence/raw/ops-script.js"
src = open(PATH, encoding="utf-8", errors="replace").read()
lines = src.split("\n")
print(f"script.js lines={len(lines)} bytes={len(src)}")

print("\n===== lines containing innerHTML =====")
for i, line in enumerate(lines, 1):
    if "innerHTML" in line:
        print(f"{i}: {line.strip()[:700]}")

print("\n===== escapeHtml definition =====")
m = re.search(r"function escapeHtml\([^)]*\)\s*\{.*?\n\}", src, re.S)
print(m.group(0)[:800] if m else "not found")

print("\n===== renderProfiles / renderJobs functions (first 6000 chars) =====")
for name in ["renderProfiles", "renderJobs", "renderAdmins", "loadProfiles", "loadJobs", "renderAnalytics"]:
    idx = src.find("function " + name)
    if idx >= 0:
        print(f"\n----- {name} @char {idx} -----")
        print(src[idx:idx + 6000])

print("\n===== user-controlled columns appearing near innerHTML lines =====")
for i, line in enumerate(lines, 1):
    if "innerHTML" in line:
        for col in ["email", "remarks", "first_name", "firstName", "lastName", "country", "city", "status", "error", "ban_reason", "banned_by"]:
            if col in line:
                print(f"{i}: col={col} :: {line.strip()[:400]}")
