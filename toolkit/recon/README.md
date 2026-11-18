# Recon harnesses

Surface discovery and mapping, in rough order of use:
- `recon.sh` — baseline: DNS, headers, well-known files
- `exposure.sh` / `enum.sh` — content and route discovery
- `bucketsweep.sh` / `bucketlist.sh` / `bucketfp.sh` — storage bucket fingerprinting
- `hostsweep.sh` / `subs` helpers — subdomain enumeration
- `wayback.sh` / `wayback2.py` — archive checks for historical leaks
- `deepgrep.py` / `deep2.py` — bundle/JS secret and contract greps
- `catalog.sh` / `shopthunk.sh` / `templates.sh` — product/template catalog extraction (rehost lane)
- `signup_oracle.sh` / `signup.py` — account-existence oracle probing
- `rpc1.sh` / `rpc_args.py` — RPC signature exploration
