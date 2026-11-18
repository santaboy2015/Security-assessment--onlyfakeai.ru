#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1
F=page-bf5f8970043f7336.js

echo "=== supabase.co ==="
grep -oE 'https://[a-z0-9]{15,30}\.supabase\.co' *.js | sort -u

echo
echo "=== createClient context ==="
grep -oE '.{120}createClient.{200}' $F | head -5
echo "---"
grep -oE 'submit-photoshop-job.{0,300}' *.js | head -3
echo
echo "=== anon key candidates (JWT) ==="
grep -oE 'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}' *.js | sort -u | head -10

echo
echo "=== apikey assignment ==="
grep -oE '.{80}apikey.{120}' *.js | grep -v 'access-control' | head -10

echo
echo "=== env-ish names in gen chunk ==="
grep -oE '(NEXT_PUBLIC_[A-Z0-9_]+|VITE_[A-Z0-9_]+)' *.js | sort -u

echo
echo "=== supabase url var ==="
grep -oE '.{60}(supabaseUrl|SUPABASE_URL|supabaseKey|SUPABASE_ANON_KEY|anonKey).{140}' *.js | head -10
echo
echo "=== sample fetch calls ==="
grep -oE 'fetch\([^)]{0,180}\)' $F | head -30
