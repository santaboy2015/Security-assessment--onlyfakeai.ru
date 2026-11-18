# Interview kit — how to walk this engagement

Interviewers don't want the vuln list. They want to hear you *think*. Have three stories ready and keep
each to 90 seconds. The repo supplies the receipts; you supply the reasoning.

---

## Story 1 — "How did you find it?" (the mapping story)

**Lead with process:** "The public site had no docs and no repo. Certificate transparency gave me four
hostnames — one of them was an admin dashboard nothing linked to. From there it was bundle reverse
engineering: beautify the Next.js chunks, pull the request contracts, confirm each one with a live request.
Then I knew the whole estate before I tested anything."

**The details that make it real:**

- `crt.sh` → `*.onlyfakeai.ru`, `cdn`, `ops`, `www`. `ops` was 403'd by a WAF to normal discovery and
  admin.onlyfakeai.ru didn't resolve — CT was the only path.
- Client bundles gave up auth settings, bucket names, job flow, and the `_buildManifest` rewrites that
  exposed the internal worker/proxy structure.
- "I always reconstruct the API contract before running tests — otherwise you're blind fuzzing."

## Story 2 — "What was the best finding?" (the storage bug)

**Lead with the *user impact*, not the payload:** "A bucket named `photos` accepted anonymous LIST calls
signed only with the publishable key — which is public by design. From the listing you get object names,
sizes and timestamps; object reads need no credentials at all. The names were `<unix-ms>_preview.png`.
Same strings were job IDs in `/api/no-watermark/<jobId>`. So the bug wasn't just a leak — it handed you an
IDOR oracle too. I quantified it read-only: 24,170 objects, 20.2 GiB, verified by SHA-256 manifest. I did
not download them. The proof is the listing + manifest + a blurred contact sheet."

**If they ask "why not download?"** — "Because the finding isn't mine to publish. Those are private
citizens' faces. My report proves exposure; it doesn't re-expose them. That distinction is the job."

## Story 3 — "Tell me about a failure." (credential ops — the star answer)

**Never hide the zero in interviews — frame it.** "The takeover didn't succeed. I mapped 10 findings, but
the admin plane was correctly gated. So the only path was credentials. I found four registered admin
identities through the signup existence oracle, built a candidate space from OSINT — operator aliases from
public reporting, brand mutations, dates, rockyou — and ran 19,300 attempts across two channels, including
Tor circuit rotation because the ops login limiter was global at 5 attempts/900 seconds. Zero hits. That's
a defensible negative: the password isn't in the guessable space. I closed the operation and documented
the remaining finish paths instead of pretending."

**The follow-up they always ask:** "What would you do next?" →
admin credential from the operator, or host-level access to the Express app's environment (service-role
key), or the Cloudflare Tunnel host. "The door was a credential door, not a code door — that's the whole
finding of the second half of the engagement."

## Story 4 — "What went wrong technically?" (builds credibility)

- Worker fleet was down during the test, so `/api/status` IDOR and the `photoUrl` SSRF couldn't be validated
  live. **What I did:** documented them as "unconfirmed — needs conditions", wrote the exact retest
  procedure, and didn't inflate them into confirmed bugs.
- The admin panel XSS chain looked promising (28 `innerHTML` sinks) but static review found consistent
  `escapeHtml()`. **What I did:** recorded it as a negative result instead of forcing a finding.
- Rewriting the environment hashes twice burned hours — **lesson:** snapshot target state (headers,
  build-id) at the start and diff later instead of re-probing.

---

## Likely technical questions + crisp answers

**"How do you decide a target is out of scope vs. in scope?"**
Rules of engagement first: authorized domains, methods allowed, data handling, and a stop condition.
In this engagement: read-only, no destructive writes, no user content downloaded, disposable accounts only.
Findings that required breaching RoE were not performed — they were reported as "not confirmed, needs
credentials / conditions".

**"Walk me through testing Supabase."**
Four planes: GoTrue (auth: JWT alg/JWKS, signup flows, metadata trust), PostgREST (RLS per table, semantics
of `service_role`), Storage (bucket policies, anon list/read/write, signed URL scope), and RPCs
(`SECURITY DEFINER` grant hygiene, `EXECUTE` via anon/authenticated). Check every plane for anon reachability
first — that's where this engagement's big finding lived.

**"How do you write a report a client will actually act on?"**
Executive summary with business impact first, findings sorted by severity, each with reproduction +
evidence pointer, then remediation prioritized P0–P3. Include the negative results — the client shouldn't
pay twice for the same wall.

**"What's your testing philosophy?"**
Read-only until proven safe. Prove impact with minimum noise. Negative results are data. The report is
part of the exploit — a finding nobody acts on didn't land.

---

## Self-introduction script (30 seconds, live)

"I'm a security researcher focused on web, API and cloud surfaces. My latest engagement was a full audit of
a live Next.js + Supabase estate — I found and proved the anonymous exposure of 24,170 user images, mapped
an unlinked admin plane, and documented ten findings with raw evidence. It's all public in my repo, including
the negative results and the parts where the takeover failed. I'm looking for a team that treats
documentation as part of the craft."
