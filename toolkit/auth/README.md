# Auth-boundary harnesses

- `authprobe*.py` — incremental auth model probing (JWKS, alg, transports)
- `jwt_forge.py` — alg:none / HS256 / claim-tampering matrix
- `rls_test.py` — RLS row-visibility tests per table
- `role_attempts.py` — privilege-write attempts (trigger test)
- `rpc_fuzz.py` / `rpc_fuzz2.py` — RPC surface fuzzing
- `login_variants.py` / `login_diff.py` — auth-flow differential testing
- `openredir_hunt.py` / `inject_test.py` — redirect and injection probes
- `idtoken_opsroute_probe.py` — token-class confusion against admin routes
