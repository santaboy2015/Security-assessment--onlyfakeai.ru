# Storage & photos-bucket harnesses

- `photo_list.py` — anonymous bucket listing pagination
- `photos_all.py` — full object enumeration → `photos_all.txt`
- `mass_pull.py` / `pipeline.py` — bulk object collection (used read-only; PII never republished)
- `worker_check.py` — generation-worker availability probe (V-10 context)
- `pull.log` — collection log with counts/failures

The full SHA-256 manifest of the enumerated objects is in `../../data/`.
