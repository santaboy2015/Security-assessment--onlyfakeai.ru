# Admin-plane harnesses

- `ops_recon.sh` — fetch the panel shell, login page, `/health`, `/script.js`
- `ops_probe*.py` — endpoint probing and validation behaviour
- `ops_admin_test.py` — authz matrix runner
- `ops_brute.py` — low-rate credential probing (ops login limiter)
- `ops_identity.py` — identity/role surface checks
- `ops_deep.py` — route extraction + deep endpoint analysis
- `pace.py` — request pacing helper used across runs
