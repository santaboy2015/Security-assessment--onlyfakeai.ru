#!/usr/bin/env python3
"""Add OSINT-derived candidates (site operator identity) to the password list."""
import os

path = "/tmp/ops_pw.txt"
existing = [l.rstrip("\n") for l in open(path, encoding="utf-8", errors="ignore") if l.strip()]

# Operator identity from public DOJ/security reporting (site is his infrastructure):
# Yurii Nazarenko, aliases "Uriel Septimberus", "Tor Ford", "John Wick".
stems = ["nazarenko", "nazar", "yurii", "yuriy", "yuri", "yura", "uriel", "septimberus",
         "septimber", "torford", "tor_ford", "tor-ford", "johnwick", "john_wick", "john-wick",
         "wick", "babayaga", "baba_yaga", "onlyfakeai", "onlyfake", "macdoc", "mac_doc"]
years = ["", "0", "00", "1", "2", "3", "7", "12", "13", "123", "321", "1234", "12345", "777",
         "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999",
         "2000", "2001", "2002", "2003", "2004", "2005", "2021", "2022", "2023", "2024", "2025", "2026"]
suffixes = ["", "!", "!!", "@", "#", "$", "?", "!?", "@1", "!1", "@123", "!@#", "1!", "123!", "_1", ".1"]

out = []
for s in stems:
    forms = {s, s.capitalize(), s.upper()}
    for f in list(forms):
        for y in years:
            for sfx in suffixes:
                cand = f + y + sfx
                if 5 <= len(cand) <= 30:
                    out.append(cand)

# leetspeak basics for the names
leets = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
for s in stems:
    leet = s
    for k, v in leets.items():
        leet = leet.replace(k, v)
    for y in ["", "1", "12", "123", "1234", "!", "!1", "2024", "2025", "2026"]:
        cand = leet + y
        if 5 <= len(cand) <= 30:
            out.append(cand)

seen = set(existing)
added = 0
for c in out:
    if c not in seen:
        seen.add(c)
        existing.append(c)
        added += 1

# keep curated personal candidates at the FRONT of the queue (after the 1.5k brand block)
# brand block is at start already; insert personal block right after it by re-sorting risky:
# simplest: write personal candidates first in a separate priority file, harness will concat.
with open("/tmp/ops_pw_personal.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(existing) + "\n")

print("added personal:", added, "total now:", len(existing), "->", path)
print("personal file:", len(out), "-> /tmp/ops_pw_personal.txt")
