# OpenSpec Change: Keeper â†’ Bitwarden Cloud â†’ Vaultwarden Migration

## Change ID
`keeper-migration-2026-06-15`

## Problem Statement

**Current state:** 15+ critical secrets exposed in Keeper (Supabase PAT, Vercel token, LLM API keys). Railway already rotated (2026-06-14), but core providers remain unrotated.

**Risk:** Keeper breach would compromise production infrastructure (FastAPI/Railway, Supabase, Vercel, LLM providers). Migration required before EOQ 2026.

**Business impact:** Zero downtime to FastAPI/Vercel/Supabase runtime.

## Proposed Solution

**Phase 1 (Bitwarden Cloud):** Migrate Keeper CSV export â†’ Bitwarden Cloud CLI (fast, low-ops setup, instant validation).

**Phase 2 (Vaultwarden self-hosted):** Move to Railway-hosted Vaultwarden for cost, control, HA (decision point: after 2w stable Bitwarden).

## Architectural Decisions

- **SecretsProvider abstraction:** Backend never talks to Bitwarden directly; uses `SecretsProvider` interface (get/set/delete/list/health).
- **Factory pattern:** `get_provider()` reads `SECRETS_BACKEND=bitwarden|vaultwarden` env var â†’ returns concrete provider.
- **Health check:** `/api/v1/secrets/health` endpoint monitors provider latency, status, vault URL.
- **No breaking changes:** API contract unchanged; migration transparent to consumers.

## Success Criteria

1. âœ… All 300+ Keeper secrets imported to Bitwarden Cloud
2. âœ… All API keys validated (Groq, OpenAI, Gemini, Mistral, Cerebras, OpenRouter)
3. âœ… Backend `/api/v1/secrets/health` returns 200 in staging + production
4. âœ… No errors in Railway logs referencing Keeper
5. âœ… Keeper vault deleted (irreversible)
6. âœ… Bitwarden Cloud stable for 2 weeks before Phase 2 decision

## Out of Scope (Phase 2)

- Vaultwarden Docker deployment
- PostgreSQL HA setup
- S3 backup automation
- TLS/cert renewal

---

## Acceptance Criteria

| Criterion | How to Verify |
|-----------|---------------|
| `secrets_provider.py` deployed | `ls apps/backend/core/secrets_provider.py` |
| Bitwarden health check passes | `curl https://contexia.online/api/v1/secrets/health` â†’ 200 |
| All API keys work | Each provider (Groq, OpenAI, etc.) responds to test call |
| Zero Keeper references in code | `grep -r "keeper" apps/ â†’ 0 matches` |
| Keeper account deleted | Screenshot of Keeper deletion page |

---

## Timeline

| Date | Milestone |
|------|-----------|
| 2026-06-15 | OpenSpec approved, Bitwarden account created, import script ready |
| 2026-06-16 | Data migration completed, folder org done |
| 2026-06-17 | Backend code deployed, `secrets_provider.py` in staging |
| 2026-06-18 | `/api/v1/secrets/health` endpoint live, validation suite passes |
| 2026-06-20 | Keeper vault deleted |
| 2026-07-04 | 2-week stability gate cleared; Phase 2 readiness approved |
| 2026-07-08 | Bitwarden Cloud subscription cancelled (if proceeding to Phase 2) |

---

## Rollback Plan

If Bitwarden integration fails before Keeper deletion:
1. Restore Keeper from backup (keep 7-day retention)
2. Revert `SECRETS_BACKEND=keeper` env var in Railway
3. Restore `apps/backend/core/secrets_provider_legacy.py` (keeper-only)
4. Deploy to staging, verify endpoints
5. Post-mortem: why integration failed

If Keeper already deleted: Bitwarden is **only option**; no rollback possible. Therefore, **never delete Keeper until 2 weeks stable + Phase 2 decision made**.

---

## Dependencies

- **CLI:** Bitwarden CLI (installed locally + Railway container)
- **Infrastructure:** Railway (env vars), Vercel (for frontend tests)
- **External:** Bitwarden Cloud account (free tier sufficient for Phase 1)

---

## Document Version

- **Created:** 2026-06-15 15:45 UTC
- **Author:** Contexia Infra
- **Status:** Approved

