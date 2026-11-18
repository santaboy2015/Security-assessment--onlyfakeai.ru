# GitHub profile README (`<username>/<username>/README.md`)

Copy this into your special profile repo (create a repo named exactly your GitHub username). It makes the
audit repo the first thing a recruiter sees when they click your profile.

---

```markdown
### security research · pentesting · reverse engineering

I map systems from zero, prove what's broken, and write the report like it's part of the deliverable.

**Latest engagement** — [onlyfakeai-security-audit](https://github.com/<username>/onlyfakeai-security-audit)

> A two-day full-stack assessment of a live SaaS estate: Cloudflare → Next.js → Supabase → a public
> Express admin plane.
>
> - 10 findings (2 High / 3 Medium / 4 Low / 1 Info), CVSS-rated with reproduction steps
> - Anonymous exposure of **24,170 user images (20.2 GiB)** in a public storage bucket — proven by
>   raw listing + SHA-256 manifest + blurred proof sheet, no personal data republished
> - **19,300-attempt** credential operation across 4 admin identities (Tor-isolated harness) — **0 hits**,
>   with the remaining takeover ladder documented instead of faked
> - Full negative-results register: JWT forgery, role injection, RLS/trigger escalation, admin-plane bypass
>   matrices — every wall proven and recorded

**What I work with**

`web/API pentesting` · `Supabase / Firebase / cloud identity` · `JWT & OAuth flows` · `storage & IDOR`
`Cloudflare edge recon` · `reverse engineering (JS & native)` · `Python / Bash tooling` · `report writing`

**Currently** — open to application security, pentest, or red-team roles. Remote or relocation.

**Reach me** — <your-email> · <your-linkedin>
```

---

## Profile checklist (10 minutes, high leverage)

- [ ] Create repo named exactly your username, add the block above as `README.md`
- [ ] Pin the audit repo + 1–2 other best repos on your profile
- [ ] Repository description: `Full-stack security assessment: Cloudflare → Next.js → Supabase → Express admin plane. 10 findings, 24,170-image exposure, raw evidence.`
- [ ] Add topics: `security`, `pentesting`, `red-team`, `supabase`, `nextjs`, `cloudflare`, `writeup`, `infosec`
- [ ] Add the blurred proof sheet as the repo's social preview image (Settings → Social preview)
- [ ] Link the repo from your LinkedIn headline/featured section and your CV header
- [ ] Enable "Security advisories" visibility so viewers see how you handle disclosure
