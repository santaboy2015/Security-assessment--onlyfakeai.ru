#!/bin/bash
set -u
cd /tmp/ofa/app || exit 1

echo "=== portraits-public context ==="
grep -oE '.{180}portraits-public.{180}' *.js | head -6
echo
echo "=== storage.from context ==="
grep -oE '.{140}storage\.from.{200}' *.js | head -5
echo
echo "=== supabase client init ==="
grep -oE '.{120}(createClient|sb_publishable|service_role|projectRef|project_ref).{180}' *.js | head -8
echo
echo "=== telegram oidc ==="
grep -oE '.{100}telegram-oidc.{200}' *.js | head -5
echo
echo "=== access token source ==="
grep -oE '.{100}(access_token|session)\s*=.{160}' *.js | head -10
