# Keeper → Bitwarden → Vaultwarden Migration

**Change ID:** `keeper-migration-2026-06-15`  
**Status:** 🟢 OpenSpec approved, ready for Phase 1  
**Owner:** Contexia Infra  
**Timeline:** Phase 1 (1 week) + Phase 2 (deferred, 2026-07-04 gate)

---

## Files in This Change

| File | Purpose | Phase |
|------|---------|-------|
| `spec.md` | Problem statement, solution, acceptance criteria | Phase 1 |
| `scenarios.md` | 10 detailed scenarios + prevention/detection | Phase 1 |
| `tasks.md` | 14 actionable tasks (T1–T14 Phase 1, T15–T18 Phase 2) | Phase 1 |
| `MIGRATION_DASHBOARD.md` | Status, metrics, risks, timeline, decision gate | Phase 1 |

---

## Code Files (Elsewhere in Repo)

| File | Location | Purpose |
|------|----------|---------|
| `secrets_provider.py` | `apps/backend/core/` | Abstract provider + Bitwarden + Vaultwarden impl |
| `secrets_endpoints.py` | `apps/backend/api/endpoints/` | FastAPI `/api/v1/secrets/health` endpoint |
| `docker-compose.vaultwarden.yml` | Repo root | Vaultwarden Phase 2 deployment |
| `railway.vaultwarden.toml` | Repo root | Railway config for Vaultwarden Phase 2 |
| `Dockerfile.vaultwarden` | Repo root | Vaultwarden container image |
| `.env.vaultwarden.example` | Repo root | Environment variable template |

---

## Quick Start (Right Now)

### Prerequisites
- Keeper account with 300+ secrets
- Bitwarden CLI (`bw`) local access
- Railway project write permission
- Python 3.9+ (for secrets_provider.py)

### Phase 1: Bitwarden Cloud (1 Week)

**Step 1–3 (Today, 2026-06-15):**
```bash
# T1: Export Keeper JSON
# T2: Create Bitwarden Cloud account (https://vault.bitwarden.com)
# T3: Install bw CLI
bw --version
```

**Step 4–6 (Tomorrow, 2026-06-16):**
```bash
# T4: Import 300+ secrets
bw import keepersecurity keeper-export-2026-06-15.json

# T5: Organize into folders (web UI: Infrastructure, LLM, Operations, Personal)

# T6: Validate each API key
curl -H "Authorization: Bearer $(bw get item groq_key | jq -r '.login.password')" \
  https://api.groq.com/openai/v1/models
```

**Step 7–12 (2026-06-17 to 2026-06-18):**
```bash
# T7: Code already in repo (secrets_provider.py)

# T8: Health endpoint already in repo (secrets_endpoints.py)

# T9: Run tests (pytest tests/backend/core/test_secrets_provider.py)

# T10: Add Railway env vars
#   SECRETS_BACKEND=bitwarden
#   BW_CLIENT_ID=...
#   BW_CLIENT_SECRET=... (masked)
#   BW_MASTER_PASSWORD=...
#   BW_VAULT_URL=https://vault.bitwarden.com

# T11: Deploy to staging, test health check

# T12: Deploy to production (Stage 11: commit → push → verify live)
curl https://contexia.online/api/v1/secrets/health
# → {"status": "healthy", "provider": "bitwarden-cloud", "latency_ms": 145}
```

**Step 13–14 (2026-06-19 to 2026-06-20):**
```bash
# T13: Audit health + validate all APIs work

# T14: Delete Keeper vault (irreversible)
# Log into Keeper: Settings → Delete Organization
```

---

## Phase 2: Vaultwarden Self-Hosted (Decision: 2026-07-04)

Only proceed if Phase 1 stable for 2 weeks (T15 gate).

```bash
# T16: Deploy Vaultwarden
docker-compose -f docker-compose.vaultwarden.yml --profile prod up

# T17: Migrate data from Bitwarden Cloud to Vaultwarden
bw export organization > bitwarden-export.json
# (Import via Vaultwarden CLI or API)

# T18: Update Railway env var
# BW_VAULT_URL=http://vaultwarden:80

# Verify health check still works
curl https://contexia.online/api/v1/secrets/health
```

---

## Rollback Strategy

### Before Keeper Deleted (T14)
- Keeper vault still readable
- If Bitwarden fails: restore from Keeper
- Cost: 1–2 hours re-import

### After Keeper Deleted (T14)
- **No rollback:** Bitwarden is only source
- Must fix forward
- Therefore: **never delete until T13 fully passes**

---

## Success Criteria

✅ All 300+ secrets imported  
✅ All API keys validated (Groq, OpenAI, Gemini, Mistral, Cerebras, OpenRouter)  
✅ `/api/v1/secrets/health` endpoint responds 200 in production  
✅ All LLM calls work (no credential failures)  
✅ Zero references to Keeper in code/logs  
✅ Keeper account deleted (irreversible)  

---

## Key Decisions

| Decision | Status | Date |
|----------|--------|------|
| Use Bitwarden Cloud (Phase 1) | ✅ Approved | 2026-06-15 |
| Later decide on Vaultwarden self-hosted (Phase 2) | ✅ Approved (deferred) | 2026-07-04 |
| Delete Keeper after Phase 1 complete | ✅ Approved | 2026-06-20 |
| Keep Keeper readonly for 7 days post-export | ✅ Approved | 2026-06-15 |

---

## Owners & Contacts

| Role | Name | Responsibilities |
|------|------|------------------|
| **Infra Lead** | Juan | T1, T2, T5, T14, T15 (decision) |
| **Dev Lead** | Dev Team | T3, T4, T7, T8, T9, T11, T12 |
| **QA** | QA | T9 (unit tests) |
| **DRI (Overall)** | Juan | Phase 1 completion gate |

---

## Approval Gate

**OpenSpec Status:** ✅ **APPROVED**

- [x] Problem statement clear
- [x] Solution well-architected (provider abstraction, factory pattern)
- [x] Scenarios comprehensive (10 scenarios, 3 blockers identified)
- [x] Tasks granular & sequenced
- [x] Success criteria testable
- [x] Rollback strategy documented
- [x] Timeline realistic (1 week Phase 1)

**Ready to Proceed?** ✅ YES  
**Start Phase 1:** 2026-06-15 (Today)  
**Phase 2 Decision Date:** 2026-07-04

---

## References

- [Keeper Security Audit (2026-06-15)](../../../MEMORY.md) — 15+ secrets exposed, Railway already rotated
- [Contexia Infrastructure Map (2026-05-30)](../../../DOCS.md) — Current stack, FastAPI on Railway, Supabase
- [OpenSpec Standard](../../../DEPLOYMENT_STAGE/) — Stage 11 mandatory for production changes

---

**Questions?** Ask in #infra-team Slack or create issue on GitHub repo.

**Last Updated:** 2026-06-15 16:15 UTC
