import ssl, os, json, threading, time, urllib.request, urllib.error

ctx = ssl.create_default_context()
names = [l.rstrip("\n") for l in open("photos_all.txt", encoding="utf-8")
         if l.strip() and l.strip() != ".emptyFolderPlaceholder"]
OUT = "photos_archive"
os.makedirs(OUT, exist_ok=True)

state_file = "pull_state.json"
if os.path.exists(state_file):
    state = json.load(open(state_file))
else:
    state = {"i": 0, "done": 0, "failed": [], "bytes": 0}

lock = threading.Lock()
log = open("pull.log", "a", encoding="utf-8")
t0 = time.time()

def pull(name):
    url = f"https://cdn.onlyfakeai.ru/storage/v1/object/public/photos/{name}"
    dest = os.path.join(OUT, name)
    if os.path.exists(dest):
        return "skip", os.path.getsize(dest)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                b = r.read()
            tmp = dest + ".part"
            open(tmp, "wb").write(b)
            os.replace(tmp, dest)
            return "ok", len(b)
        except Exception as e:
            if attempt == 2:
                return "fail", 0
            time.sleep(2)
    return "fail", 0

def worker():
    while True:
        with lock:
            if state["i"] >= len(names):
                break
            i = state["i"]
            state["i"] += 1
        name = names[i]
        res, size = pull(name)
        with lock:
            if res == "ok":
                state["done"] += 1
                state["bytes"] += size
            elif res == "fail":
                state["failed"].append(name)
            # skip counts as done for progress purposes
            if state["i"] % 100 == 0 or res == "fail":
                elapsed = max(1, time.time() - t0)
                mb = state["bytes"] / 1048576
                log.write(f"{time.strftime('%H:%M:%S')} {state['i']}/{len(names)} "
                          f"ok={state['done']} fail={len(state['failed'])} "
                          f"{mb:.0f}MB {mb/elapsed:.1f}MB/s\n")
                log.flush()
                json.dump(state, open(state_file, "w"))
            if res == "fail":
                time.sleep(1)

ts = [threading.Thread(target=worker, daemon=True) for _ in range(6)]
print(f"[pull] {len(names)} files -> {OUT}/  (resume at {state['i']})", flush=True)
for t in ts:
    t.start()
for t in ts:
    t.join()
json.dump(state, open(state_file, "w"))
elapsed = time.time() - t0
print(f"[done] ok={state['done']} failed={len(state['failed'])} "
      f"{state['bytes']/1048576:.0f}MB in {elapsed:.0f}s", flush=True)
