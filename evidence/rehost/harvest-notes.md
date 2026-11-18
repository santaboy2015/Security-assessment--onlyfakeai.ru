# HARVEST-NOTES.md — public Supabase template assets (`product`, `id`, `dl`, `residence`, `passport`)

Generated: 2026-11-10 16:00 (local). Target: `https://cdn.onlyfakeai.ru/storage/v1/object/public/<bucket>/<file>`

## Totals

- Files: **518**
- Total size: **730.1 MiB** (765,598,120 bytes)
- Distinct sha256: **289** — 228 duplicate groups, 228 of them mix `product/` with a
  template bucket (product previews are byte-identical copies); redundant payload 302.8 MiB
- Files failing JPEG/PNG magic check: **0**
- Filenames not matching the expected `COUNTRY_DOCTYPE_YEAR-EXAMPLE.ext` shape: 1 (INDONESIA_passport_2015-EXAMPLE.jpg)

## Counts per bucket (local path preserved after `/object/public/`)

| bucket path | files | size |
|---|---:|---:|
| dl | 74 | 95.0 MiB |
| id | 110 | 145.2 MiB |
| passport | 68 | 111.6 MiB |
| product/dl | 9 | 10.5 MiB |
| product/dl-usa | 50 | 48.8 MiB |
| product/id | 36 | 36.5 MiB |
| product/id-usa | 49 | 64.0 MiB |
| product/passport | 59 | 93.4 MiB |
| product/residence | 30 | 56.1 MiB |
| residence | 33 | 69.1 MiB |

## Method

1. Decompiled `rehost/src/app/8794-9e09a720aa8a0cf1.js`: recovered the exact public-URL builder
   `V(country, doctype, state, extra, override)`, its `M`/`P` revision tables (per country+doc revision
   dates), the country->doctype option map, the USA-state DL revision map, and the location map
   (50 USA states, 10 Canadian provinces).
2. Cross-checked `rehost/src/template-map.json` and the Lead's shop-catalog enumeration
   (`catalog-products.json`: 232 products / 231 unique preview URLs).
3. Generated **5,694** candidate paths — every app-constructible filename for all countries x doctypes x
   every revision year, a blanket 2005-2026 year sweep, all 50 US states, all 10 CA provinces, textures —
   and HEAD-checked them with `curl --parallel 8` (HTTP/2; 200=exists, 400 `NoSuchKey`=absent).
4. Adaptive second pass (**911** candidates): catalog-derived template copies (exact years from product
   tags into `id`/`dl`/`residence`/`passport`), underscore province/state naming variants, and `product/`
   mirrors of every discovered template file. 455 hits, mostly product mirrors of pass-1 hits.
5. Downloaded every 200 in parallel into `rehost/assets/<bucket>/<original-name>` (5 workers, polite
   pacing); verified size + JPEG magic; recorded `sha256`.

## Candidate / hit statistics

| pass | candidates HEADed | 200 hits | unique new files |
|---|---:|---:|---:|
| 1. app-exact + year sweep + states/provinces | 5,694 | 399 | 285 |
| 2. catalog-derived + product mirrors + variants | 911 | 455 | 231 (mostly product mirrors) |
| 3. gap-fill (AU states, USA extra ID years, product mirrors) | 438 | 0 | 0 |
| **combined (deduped)** | **7,043** | — | **518** |

### Verification

- Random 24-file sample re-HEADed: **24/24 remote `content-length` == local size**.
- Shop-catalog cross-check: **231/231 catalog URLs present on disk** (0 missing).
- 518/518 files pass JPEG magic-byte check; **0** files came from an excluded bucket.
- 2 bonus product files found on the CDN that are absent from the shop catalog:
  `product/dl-usa/NEWYORK_DL_2025-EXAMPLE.jpg` and `product/passport/RUSSIA_Passport_2014-EXAMPLE.jpg`.

Known gaps: **Australian driving licences** — only `NEWSOUTHWALES_DL_2025-EXAMPLE.jpg` exists in the
public bucket; `AUSTRALIA_DL_*` and the other 7 state/territory names return `NoSuchKey` for 2015-2026,
and the shop catalog lists no Australia DL product. Everything else the app offers resolves to a file.

## Coverage

- Country x doctype pairs (excluding state/province entries): **155**
- Plus state-level: 99 USA state pairs, 18 Canadian province pairs
- Years present: 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025

| doctype | template files | country/state/province pairs |
|---|---:|---:|
| id_card | 109 | 103 |
| passport | 68 | 64 |
| residence | 33 | 33 |
| driving_license | 74 | 71 |
| ssn | 1 | 1 |

### Gaps

App offers the pair but no public file was found:
- Australia / DL

### Notable findings

- **USA**: `id` bucket has **49 state ID cards** (all 2025; NEW YORK absent) and `dl` bucket has **all 50**
  state DLs (2025, plus revision years `CALIFORNIA_DL_2017/2024`, `TEXAS_DL_2021/2025`, `MICHIGAN_DL_2024`,
  `WESTVIRGINIA_DL_2019/2023`). Mirrors: `product/id-usa` (49) and `product/dl-usa` (50, incl. NEW YORK,
  which the catalog itself does not list). Country-level: `USA_ID_2008` + `USA_ID_2010`, `USA_SSN_2020`,
  `USA_Passport_2020`, `USA_Residence_2025`.
- **Canada**: provincial DL templates for all 10 provinces/territories (2025) and provincial ID templates
  for 8 of 10 (ALBERTA, MANITOBA, NEW BRUNSWICK, NEWFOUNDLAND AND LABRADOR, NOVA SCOTIA, ONTARIO,
  PRINCE EDWARD ISLAND, SASKATCHEWAN; British Columbia / Quebec ID absent), plus `CANADA_Passport_2012/2023`.
- **Australia**: only `NEWSOUTHWALES_DL_2025` exists; no other AU state/territory DL (see Gaps).
- **Revision-year variants coexist** per country/doctype (e.g. `BULGARIA_ID_2024`+`_2025`, `AZERBAIJAN_Passport_2013`+`_2024`,
  `JAPAN_Passport_2020`+`_2025`, `ROMANIA_Passport_2019`+`_2022`, and both `RUSSIA_Passport_2014` and `RUSSIA1_Passport_2014`).
- **Anomaly**: two catalog entries carry year **2099** (`MEXICO_Passport_2099`, `SWITZERLAND_Passport_2099`,
  2.3/2.5 MB) — placeholder years in the target's product data; both objects are real and were saved.
- **Lower-case token anomaly**: catalog preview `product/passport/INDONESIA_passport_2015-EXAMPLE.jpg` (lower-case
  `passport`) differs from the canonical `INDONESIA_Passport_2015` in the `passport` bucket; both kept.
- No `product/ssn` preview exists; the SSN template lives only at `id/USA_SSN_2020-EXAMPLE.jpg`.
- `product/` copies are byte-identical to their template-bucket originals (see duplicate groups), so the
  four template buckets alone are sufficient for a re-host; product copies are kept for the shop UI.

## Exclusions honoured

- No file was requested from `generated`, `photos`, `backgrounds` or `portraits-public` — verified 0 rows
  from those buckets across all sweep candidate lists, hit lists and the download list.

## Files

- `HARVEST-LIST.txt` — one line per file: `bucket<TAB>filename<TAB>bytes<TAB>sha256(first 16 hex)`
- `HARVEST-NOTES.md` — this file
- `.work/` — reproducible harness: `gen_candidates.py`, `sweep.py`, `gen_phaseC.py`, `gen_phaseD.py`,
  `download.sh`, extracted app tables (`M.json`, `P.json`, `country_options.json`, `states.json`),
  `sweep_results.tsv`, `phaseCD_results.tsv`, `hits_download.tsv`, `hits_dl.log`.
