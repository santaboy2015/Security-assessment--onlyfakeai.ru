# API probing suite

Numbered live probes against the Next.js API, Supabase proxy, PostgREST, Storage and Realtime.
`app_probe1.py` → `app_probe22.py` were run in order; each answers one question and logs its
own output. Also here:
- `probe_supa*.py` — Supabase gateway baseline (settings, JWKS, tables)
- `probe_realtime*.py` — Realtime channel/auth probes
- `probe_rpc*.py` — PostgREST RPC contract checks
- `probe_storage*.py` — Storage policy checks
- `r2s_origin_replay.py` — React2Shell payload replay against alternate ingress
- `mailflow*.py` / `mailpoison_test.py` — system-mail flow and spoof-policy checks
- `p2_capture_server.py` / `browser_p2_prep.py` — redirect-capture experiment (failed, documented)
