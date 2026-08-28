# Deployment report — freemium-tenant-minimum-seed

- Date: 2026-08-28
- Commit: `de2065b` (pushed to `main`)

## Stage 11 checklist

- [x] 11.1 git commit + push to main (`de2065b`, isolated from other parallel sessions' uncommitted
      `AGENTES.md`/`progress/current.md`/`ai-specs/references/`)
- [x] 11.2 Vercel build complete — `dpl_HS9bUHau8MWq3wGQJictAGqJn8iF`, `state: READY`,
      `githubCommitSha: de2065b3281519b0bc2cc0db71e36dc39fa6e67a`
- [x] 11.3 Railway deploy active — deployment `8605c6d7-2a6e-45c2-91b0-6538da358935`,
      `status: SUCCESS`
- [x] 11.4 Production URL verified: `POST /api/v1/crm/b2b/clients` on
      `antigravity-app-production-175a.up.railway.app` returns `401` unauthenticated (no
      regression — same behavior as before this change, confirmed via `curl`)
- [x] 11.5 This report

## Notes

No visual/UI verification of the new "Saldo de apertura" field was performed against a live
freemium alta (same pre-existing limitation as Subdomains 3/4 — local `SUPABASE_URL` gap, no
founder session token available in this session). Correctness is covered by 44 passing backend
tests (gating logic, idempotency, account codes) plus a clean `tsc --noEmit`.
