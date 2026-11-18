# Infrastructure harnesses

Scripts used to map the estate beyond the web app: origin hunting, worker tier, DNS/brand space, DB
surface, tunnels and threat-intel.

| File | Purpose |
|---|---|
| `origin_probe.py` | PTR / origin-candidate probing, TLS and HTTP behaviour from non-Cloudflare paths |
| `probe_origin.py` / `probe_services.py` | Origin service enumeration (ports, banners, TLS) |
| `worker_probe.py` | `s1.*` worker tier endpoint matrix (`/health`, `/status`, `/process`, debug paths) |
| `worker_auth.py` | Worker auth-model probes (JWT classes, worker-secret header variants) |
| `main_worker_probe.py` | Next.js → worker proxy behaviour through the main app |
| `fresh_token_worker.py` | Fresh account/session flow used to test authenticated worker access |
| `dns_core.py` | Core DNS resolution (A/NS/TXT/MX) for domain and sibling mapping |
| `passive_dns.py` | Passive-DNS and reverse-IP intel collection |
| `brand_check.py` | Brand/typo domain liveness and fingerprinting |
| `live360_probe.py` | `live360.*` app probe |
| `mail_ports.py` | Mail/edge port checks through third-party check-host |
| `watch_tunnels.py` | Tunnel-state watcher (`s2`/`s3` Cloudflare Tunnel 1033 state, `s1` health) |

All outputs referenced by [`../../docs/domains-and-infrastructure.md`](../../docs/domains-and-infrastructure.md)
are preserved under [`../../evidence/artifacts/`](../../evidence/artifacts/).

**Notes**
- Hosts/IPs are the engagement's public DNS facts; the Supabase project ref and publishable key are
  placeholder-sanitised before publication.
- `worker_auth.py` reads a session token from a local file; no token material is included in this repo.
