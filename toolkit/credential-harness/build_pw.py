#!/usr/bin/env python3
"""Build candidate password list for onlyfake@tuta.io (curated brand list + rockyou top slice)."""
import gzip, itertools, os, string

out = []

# --- 1. owner/brand-curated ---
brands = [
    "onlyfake", "onlyfakeai", "onlyfakes", "onlyfak", "onlyfakea", "onlyfake.ai",
    "ofake", "onlyf", "only", "fake", "fakeai", "onlyfakeid", "onlyfake_doc",
]
suffixes = ["", "1", "12", "123", "1234", "12345", "123456", "123!", "1234!", "12345!",
            "!", "@", "#", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
            "2024!", "2025!", "2026!", "@123", "@1234", "007", "321", "000", "111",
            "123!", "321!", "6969", "777", "7777", "555", "5555", "4080", "!@#", ".ru", "ru"]
caps = []
for b in brands:
    caps += [b, b.capitalize(), b.upper(), b[0].upper() + b[1:]]
for c in caps:
    for s in suffixes:
        out.append(c + s)
        if s and s[0].isdigit():
            out.append(c + "_" + s)
            out.append(c + "." + s)

# --- 2. tuta/telegram/domain related ---
for stem in ["tuta", "tutanota", "<remote-support>", "onlyfakeai.ru", "onlyfake.ru",
             "onlyfakesup", "<remote-support>port", "rat", "ratman", "admin"]:
    for s in ["", "1", "123", "1234", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
              "123!", "!", "@123", "_123", "007"]:
        out.append(stem + s)
        out.append(stem.capitalize() + s)

# --- 3. classic weak passwords (first ~300) ---
classics = """123456 password 12345678 qwerty 123456789 12345 1234 111111 1234567 dragon 123123 baseball
abc123 football monkey letmein 696969 shadow master 666666 qwertyuiop 123321 mustang 1234567890 michael
654321 pussy superman 1qaz2wsx 7777777 fuckyou 121212 000000 qazwsx 123qwe killer trustno1 jordan jennifer
zxcvbnm asdfgh hunter buster soccer harley batman andrew tigger sunshine iloveyou fuckme 2000 charlie
robert thomas hockey ranger daniel starwars klaster 112233 george asshole computer michelle jessica pepper
1111 zxcvbn 555555 11111111 131313 freedom 777777 pass fuck maggie 159753 aaaaaa ginger princess joshua
cheese amanda summer love ashley 6969 nicole chelsea biteme matthew access yankees 987654321 dallas austin
thunder taylor matrix mobilemail mom monitor monitoring montana moon moscow""".split()
out += classics

# mutations on classics
for p in classics[:120]:
    out += [p + "1", p + "12", p + "123", p + "1234", p + "!", p + "2024", p + "2025"]
    out.append(p.capitalize())
    out.append(p.capitalize() + "123")

# --- 4. rockyou top slice ---
ry = "/usr/share/wordlists/rockyou.txt.gz"
if os.path.exists(ry):
    try:
        with gzip.open(ry, "rt", encoding="latin-1", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= 20000:
                    break
                p = line.rstrip("\n")
                if 6 <= len(p) <= 24:
                    out.append(p)
    except Exception as e:
        print("rockyou read error:", e)

# dedupe preserving order
seen = set()
uniq = []
for p in out:
    if p and p not in seen:
        seen.add(p)
        uniq.append(p)

path = "/tmp/ops_pw.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(uniq) + "\n")
print("candidates:", len(uniq), "->", path)
