# Outreach templates

Small, sharp, evidence-first. Never send a wall of text. Always lead with the repo link.

---

## 1. Cold email / DM to a pentest shop

Subject: `Application/API pentester — live-engagement portfolio`

> Hey <name>,
>
> I'm applying to <company>. I just published my latest engagement: a full audit of a live Next.js +
> Supabase estate — public storage bucket serving 24,170 user images, unlinked admin plane, a 19,300-attempt
> credential operation that stayed honest about failing.
>
> Everything is reproducible in the repo — raw logs, harnesses, reports, and the negative results:
> <repo-link>
>
> If that signals the kind of work you'd hire for, I'd like 15 minutes. Résumé attached.
>
> — <name>

## 2. DM to a security hiring manager / recruiter

> Hi <name> — saw the <role> opening at <company>. Short version: I run full-stack security assessments
> (web/API/cloud), write the report like it's part of the deliverable, and publish the evidence.
>
> Latest engagement (2 days, 10 findings, 1 storage breach, verified by SHA-256 manifest):
> <repo-link>
>
> Happy to do a walkthrough of the methodology in an intro call.

## 3. LinkedIn connection note (300 char max)

> I do web/API/cloud pentesting and publish full engagement records — latest: <repo-link>.
> Open to red-team/appsec roles. Would be glad to connect.

## 4. Follow-up after they open the repo but go quiet (day 6)

> Hey <name> — bumping this once. If the exact-fit isn't there, any team in your network doing
> application-security or red-team work? The repo doubles as my methodology demo:
> <repo-link>
> Either way, thanks for looking.

## 5. Freelance / contract pitch (Upwork, direct)

Subject: `Security assessment — fixed scope, evidence-backed report`

> I deliver web/API security assessments with a report you can hand to an engineer without translation.
> Recent engagement for context: <repo-link> — 10 findings, P0–P3 remediation, every claim backed by a raw
> request log.
>
> Fixed-price offers:
> - External web/API surface review — <price>
> - Full-stack review incl. cloud identity (Supabase/Firebase/AWS auth) — <price>
> - Quick exposure audit (public buckets, admin panels, auth misconfig, 24h turnaround) — <price>
>
> Tell me the stack and the scope and I'll send a one-page proposal.

---

## Application checklist (do this weekly, 30 min)

- [ ] 5 direct-company applications (pentest shops, security consultancies, MSSPs) — always link the repo
- [ ] 2 outreach messages to people whose team does what you want to do
- [ ] 1 long-form technical post (teardown, methodology note) — keeps the repo fresh
- [ ] 1 engagement record update (new repo, blog, or finding) so the profile doesn't go cold

## Where these actually convert

| Channel | Reality |
|---|---|
| Pentest consultancies | Portfolio + interview; they hire on demonstrated methodology |
| In-house appsec teams | Cross-check the repo yourself in the interview, so leave it clean |
| Bug bounty platforms | Repo is evidence of skill; pay comes from programs, not the repo |
| Freelance marketplaces | Repo is social proof; keep it free of anything you can't defend |

## What NOT to attach

- Raw user data (never; it destroys the candidate instantly)
- Anything copied from the target's private source
- Credential lists or session captures
- Claims of authorization you can't document if asked
