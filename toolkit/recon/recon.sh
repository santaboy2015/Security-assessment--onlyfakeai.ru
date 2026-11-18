#!/bin/bash
# onlyfakeai.ru bundle recon
set -u
OUT=/tmp/ofa
mkdir -p "$OUT/js"
cd "$OUT/js" || exit 1

curl -sS -k -m 30 -o index.html "https://onlyfakeai.ru/"

grep -oE '/_next/static/chunks/[^"]+\.js' index.html | sort -u > files.txt
echo "[*] chunk count: $(wc -l < files.txt)"

while IFS= read -r f; do
  n=$(basename "$f")
  [ -s "$n" ] || curl -sS -k -m 20 -o "$n" "https://onlyfakeai.ru$f"
done < files.txt

echo "[*] downloaded: $(ls *.js 2>/dev/null | wc -l)"

echo "=== SUPABASE URLS ==="
grep -rhoE 'https://[a-zA-Z0-9.-]+\.supabase\.co' . 2>/dev/null | sort -u

echo "=== JWT-LIKE TOKENS ==="
grep -rhoE 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}' . 2>/dev/null | sort -u | head -10

echo "=== API PATHS ==="
grep -rhoE '"/api/[a-zA-Z0-9/_.-]+"' . 2>/dev/null | tr -d '"' | sort -u | head -60

echo "=== EXTERNAL HOSTS ==="
grep -rhoE 'https://[a-zA-Z0-9.-]+\.[a-z]{2,}' . 2>/dev/null | sed 's|https://||' | sort | uniq -c | sort -rn | head -40

echo "=== KEYWORDS ==="
grep -rhoE '(NEXT_PUBLIC_[A-Z0-9_]+|VITE_[A-Z0-9_]+|SUPABASE_[A-Z0-9_]+|API_URL|BACKEND_[A-Z_]+)' . 2>/dev/null | sort -u | head -40
