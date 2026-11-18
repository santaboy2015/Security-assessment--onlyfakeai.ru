# Credential operations harness

Built after every code path was exhausted. Two channels: ops login (global limiter) and direct GoTrue
(per-IP limiter, Tor circuit rotation).

- `build_pw*.py` — candidate-space generators (brand, OSINT, leet, date variants)
- `build_queue*.py` / `build_multi_queue.py` — queue builders (email:password rows)
- `brute_*.py` — channel runners (direct, GoTrue, hybrid, sequential, multi)
- `fast_*.py` / `spray*.py` — throughput and pacing variants
- `limiter_*.py` / `ratelimit.py` / `rate_analyze.py` — limiter measurement and analysis
- `socks_test*.py` / `tor_*.sh` — Tor circuit validation and rotation helpers

**Result:** 19,300 attempts, 0 valid credentials. The harness is published for the methodology, not the
outcome. Wordlists are not included; supply your own (rockyou + project-brand mutations as described in
the reports).
