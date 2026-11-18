# LinkedIn — final post (paste-ready)

**Before posting:** replace `<REPO-LINK>` with the repo URL, decide on the blurred proof image (it works
better than text alone), and post from a profile where the repo is pinned. Target length ~1,900 characters.

---

## The post

I took apart a criminal fake-ID service — all the way to its backend. Here's what two days of offensive work produced, and what I learned about how real platforms actually fall.

`onlyfakeai.ru` sells forged passports, driver's licences and IDs for ~$25 in crypto. 13,804 registered profiles. 25,925 generation jobs. Customers upload their own faces to print identity documents.

My job was to map and compromise it. What I walked away with:

→ The entire backend **without a single password**. Three access-control bypasses — anonymous storage reads, unauthenticated job endpoints with no ownership check, and a user-writable ban flag — opened every layer that mattered.

→ The data plane: 24,169 user files (20.18 GiB), the full product factory (580 templates, 731 MB), the complete application source, the API/DB contract, and a runnable replica of the service.

→ The origin host: reverse DNS pointed straight at the operator's own server. SSH exposed. Cloudflare Tunnel ingress mapped. "Hosted locally" bought them nothing.

→ The estate: 2 operator domains on the same Cloudflare account, 9 subdomains (admin panel, worker tier, live apps), Postgres ports open, and an evidence-tiered inventory of 47 domains, endpoints and contacts.

→ The dirty detail: 19,300 credential attempts across four admin identities proved the password was irrelevant. Authorization was the weak layer, not authentication. That distinction is the whole job.

Third-party threat intel rates the domain Critical. I documented everything with raw HTTP logs, reproduction steps and severity ratings — and published none of the victims' images. Proof of exposure lives in the hashes, not in their faces.

What this tested: reverse engineering obfuscated Next.js bundles, Supabase/RLS/trigger analysis, Cloudflare-edge and origin hunting, OSINT, credential operations under rate limits, and report writing that an engineer can act on.

I'm looking for a security team where this is the day job — application security, red team, or pentest. Full engagement record, evidence and toolkit are here: <REPO-LINK>

#cybersecurity #penetrationtesting #redteam #appsec #infosec #cloudsecurity

---

## Shorter variant (if the long one feels heavy)

I spent two days taking apart a criminal fake-ID marketplace — and owned its backend without a single password.

Three access-control bypasses gave me 24,169 customer images, the full product factory, the application source, and a runnable replica of the service. Reverse DNS then handed me the operator's own server: SSH exposed, Cloudflare Tunnel mapped, "local hosting" and all.

19,300 credential attempts proved the admin password was irrelevant — authorization was the weak layer, not authentication.

Every claim is backed by raw HTTP logs. No victim data published: proof by SHA-256 manifest.

Full record: <REPO-LINK>

Looking for application security / red-team / pentest roles where this is the work.
#cybersecurity #pentesting #redteam #appsec

---

## Posting notes

- **Image:** attach `data/proof/photos-bucket-sample-blurred.jpg` (blurred faces = proof without victims) or
  the architecture diagram. Proof image wins on scroll-stop.
- **First 2 lines are everything** — LinkedIn truncates. Keep the hook ("I took apart a criminal fake-ID
  service — all the way to its backend.").
- **Tag nobody** unless you know them; don't tag the target.
- **Reply to comments with specific numbers** — the manifest, the 3 bypasses, the PTR story. Specifics
  convert; adjectives don't.
- **Repost cadence:** once. Then write technical follow-ups (e.g. "How a global rate limiter became a DoS")
  and link back to the repo. One good engagement beats five vague posts.
- Don't add "thoughts?" at the end. Don't use "thrilled/excited/humbled". Let the work talk.
