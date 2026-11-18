#!/usr/bin/env python3
"""Build final prioritized queue: personal shortlist -> brand/classic block -> rockyou slice. Cap ~6000."""
import gzip, os

def dedup(seq):
    seen=set(); out=[]
    for x in seq:
        x=x.strip()
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

# 1) personal shortlist
names = ["nazarenko","nazar","yurii","yuriy","yuri","yura","uriel","septimberus","septimber",
         "torford","johnwick","johnwick","wick","babayaga","macdoc","onlyfake","onlyfakeai","onlyfakes"]
suffix = ["","1","12","123","1234","12345","123456","!","!!","@","#","123!","1!","007",
          "2021","2022","2023","2024","2025","2026","2026!","2025!","2024!","1990","1991","1992",
          "1993","1994","1995","1996","1997","1998","1999","2000","777","321","000","111"]
personal=[]
for n in names:
    for f in {n, n.capitalize(), n.upper()}:
        for s in suffix:
            personal.append(f+s)
# leet + name combos
leets = [("nazarenko","n4z4r3nk0"),("yurii","yur11"),("uriel","ur13l"),("johnwick","j0hnw1ck"),
         ("septimberus","53pt1mb3ru5")]
for a,b in leets:
    for s in ["","1","123","1234","!","123!","2024","2025","2026"]:
        personal += [b+s, b.capitalize()+s]
# aliyas joins
personal += ["urielseptimberus","uriel_septimberus","UrielSeptimberus123","torford","TorFord",
             "tor_ford","<remote-support>","onlyfakesup","onlyfake@tuta.io"]
personal = dedup(personal)

# 2) brand/classic block from the original generator file (first ~3000 entries)
src="/tmp/ops_pw.txt"
base=[l.rstrip("\n") for l in open(src,encoding="utf-8",errors="ignore") if l.strip()]
# find where rockyou starts (after classics) — approximate by taking first 3000 brand entries
brand_block = base[:3000]

# 3) rockyou top slice
rockyou=[]
ry="/usr/share/wordlists/rockyou.txt.gz"
if os.path.exists(ry):
    with gzip.open(ry,"rt",encoding="latin-1",errors="ignore") as f:
        for i,line in enumerate(f):
            if i>=4000: break
            p=line.rstrip("\n")
            if 6<=len(p)<=24: rockyou.append(p)

queue = dedup(personal + brand_block + rockyou)[:6000]
out="/tmp/ops_queue.txt"
open(out,"w",encoding="utf-8").write("\n".join(queue)+"\n")
print("queue:",len(queue),"personal:",len(personal),"brand:",len(brand_block),"rockyou:",len(rockyou))
print("first 10:",queue[:10])
