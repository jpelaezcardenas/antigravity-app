# Keeper → Bitwarden → Vaultwarden Migration Dashboard

**Last Updated:** 2026-06-15 16:00 UTC  
**Status:** 🟡 Phase 1 ready to initiate  
**Owner:** Contexia Infra Team  

---

## Phase 1: Bitwarden Cloud (Target: 2026-06-20)

| Task | Component | Status | Start | ETA | Owner | Notes |
|------|-----------|--------|-------|-----|-------|-------|
| T1 | Keeper CSV Export | ✅ Complete | 2026-06-15 | 2026-06-15 | Juan | 330 secrets validated |
| T2 | Bitwarden Cloud Account | ✅ Complete | 2026-06-15 | 2026-06-15 | Juan | jpelaezcardenas@gmail.com, 2FA, API keys ✅ |
| T3 | bw CLI Install | ⏳ Ready | 2026-06-15 | 2026-06-15 | Dev | Verified locally + Railway |
| T4 | Data Import (BW) | ✅ Complete | 2026-06-16 | 2026-06-15 | Dev | 330 items imported manually ✅ |
| T5 | Folder Organization | ✅ Complete | 2026-06-16 | 2026-06-15 | Juan | 9 folders organized by zone ✅ |
| T6 | API Key Validation | ⏳ Ready | 2026-06-16 | 2026-06-17 | Dev+Infra | All 6 providers ready for validation |
| T7 | SecretsProvider Module | ✅ Complete | 2026-06-17 | 2026-06-17 | Dev | Code in apps/backend/core/ ✅ |
| T8 | /api/v1/secrets/health | ⏳ Pending | 2026-06-18 | 2026-06-18 | Dev | FastAPI endpoint, <500ms latency |
| T9 | Unit Tests | ⏳ Pending | 2026-06-17 | 2026-06-17 | QA | 12 tests, >90% coverage |
| T10 | Railway Env Vars | ⏳ Pending | 2026-06-18 | 2026-06-18 | Infra | 5 variables set + masked |
| T11 | Staging Deploy | ⏳ Pending | 2026-06-18 | 2026-06-18 | Dev | Health check passes, <300ms |
| T12 | Production Deploy (Stage 11) | ⏳ Pending | 2026-06-18 | 2026-06-18 | Dev+Infra | Vercel + Railway ready, endpoints work |
| T13 | Health Audits | ⏳ Pending | 2026-06-19 | 2026-06-19 | Infra+Dev | Zero Keeper refs, all validations |
| T14 | Delete Keeper | ⏳ Pending | 2026-06-20 | 2026-06-20 | Juan | Irreversible; backup in place |

**Phase 1 Success Criteria:**
- ✅ All 14 tasks completed
- ✅ Production health check returns 200
- ✅ All LLM providers working (no credential failures)
- ✅ Keeper account deleted
- ✅ Zero references to Keeper in code/logs
- ✅ Team consensus: stable for Phase 2 decision

---

## Phase 2: Vaultwarden Self-Hosted (Decision: 2026-07-04)

| Task | Component | Status | Start | ETA | Owner | Notes |
|------|-----------|--------|-------|-----|-------|-------|
| T15 | 2-Week Stability Gate | ⏳ Pending | 2026-06-20 | 2026-07-04 | Juan+TL | Monitor Bitwarden; decide go/no-go |
| T16 | Vaultwarden Deploy | ⏳ Deferred | TBD | TBD | Infra | Docker-compose + Railway config |
| T17 | Data Migration (BW→VW) | ⏳ Deferred | TBD | TBD | Infra | bw export → vaultwarden import |
| T18 | Backend URL Switch | ⏳ Deferred | TBD | TBD | Dev | BW_VAULT_URL=http://vaultwarden:80 |

**Phase 2 Decision Gate (2026-07-04):**
- [ ] 14 days stable Bitwarden (zero failures)
- [ ] Health check latency <300ms consistently
- [ ] All LLM providers respond within SLA
- [ ] No rate-limit errors from Bitwarden
- [ ] Team vote: proceed to self-hosted?

**Phase 2 Outcomes:**
1. **Proceed:** Deploy Vaultwarden, migrate from Cloud (1 week, T16–T18)
2. **Defer:** Keep Bitwarden Cloud, revisit Q3 2026
3. **Abandon:** Bitwarden Cloud sufficient; no self-hosted

---

## Key Metrics & SLAs

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Secrets Migrated** | 300+ | 0 | ⏳ |
| **API Keys Validated** | 100% | 0% | ⏳ |
| **Health Check Latency** | <500ms | N/A | ⏳ |
| **Endpoint Availability** | 99.9% | N/A | ⏳ |
| **Secret Retrieval Time** | <200ms | N/A | ⏳ |
| **Keeper Delete Confirmed** | Yes | No | ⏳ |
| **Zero Keeper References** | Yes (grep -r) | No | ⏳ |

---

## Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|-----------|-------|
| **Keeper export incomplete** | HIGH | CRITICAL | Audit Keeper scope; export with org permissions | Juan |
| **API key format incompatible** | MEDIUM | HIGH | Validate format in T6 before deployment | Dev+Infra |
| **Bitwarden auth timeout** | LOW | MEDIUM | Rate-limit backoff; manual retry; document | Dev |
| **Railway env vars missing** | MEDIUM | HIGH | Mandatory checklist step T10 | Infra |
| **Health check latency spikes** | LOW | MEDIUM | Add circuit-breaker cache fallback | Dev |
| **Keeper account undeletable** | LOW | CRITICAL | Export/backup Bitwarden before T14 | Juan |
| **Vaultwarden deploy fails (Phase 2)** | LOW | MEDIUM | PostgreSQL failover; backup strategy | Infra |
| **LLM provider key rotated** | LOW | MEDIUM | Monthly validation; alert on first failure | Dev |

---

## Critical Dependencies

```
T1 Export Keeper
  ↓
T2 Bitwarden Account
  ↓
T3 bw CLI
  ↓
T4 Data Import → T5 Organize
  ↓
T6 Validation (Gate: all APIs work)
  ↓
T7 SecretsProvider + T9 Tests
  ↓
T8 Health Endpoint
  ↓
T10 Railway Env (Gate: vars set)
  ↓
T11 Staging Deploy
  ↓
T12 Production Deploy (Stage 11)
  ↓
T13 Audit Checks
  ↓
T14 Delete Keeper (Gate: backup exists)
  ↓
T15 2-Week Stability Gate → Phase 2 Decision
```

**Critical Path:** T1→T3→T4→T5→T6→T10→T11→T12→T13→T14  
**Duration:** ~1 week (parallel execution where possible)  
**Blockers:** T6 (APIs must validate), T10 (env vars mandatory), T14 (backup required)

---

## Rollback Procedures

### If Bitwarden import fails (before T14):
1. Keep Keeper vault for 7 days (readonly)
2. Fix import issue (format, scope, etc.)
3. Re-import to new Bitwarden org
4. Validate again (T6)
5. Re-run T12 (production deploy)

### If health check fails in production (T12):
1. Revert to legacy secrets provider (if exists)
2. Or: Restore Keeper from 7-day backup
3. Post-mortem: why integration failed
4. Fix root cause
5. Retry T7–T12

### If Keeper already deleted (T14 complete):
- **No rollback:** Bitwarden is only source of truth
- Must fix forward (migrate, debug, etc.)
- Therefore: **never delete until T13 fully passes**

---

## Communication Plan

### Phase 1 Kickoff (2026-06-15)
- [ ] OpenSpec approved in standup
- [ ] Tasks assigned (Dev, Infra, Juan, QA)
- [ ] Slack notification: "Keeper migration Phase 1 initiated"

### Phase 1 Milestones (Daily updates)
- [ ] T1–T6 complete (2026-06-16)
- [ ] T7–T12 complete (2026-06-18)
- [ ] T13–T14 complete (2026-06-20)

### Phase 2 Decision Gate (2026-07-04)
- [ ] Stability report published
- [ ] Team vote on go/no-go
- [ ] Decision documented + communicated

### Keeper Deletion Confirmation (2026-06-20)
- [ ] Slack: "Keeper vault deleted; Bitwarden is live"
- [ ] Email to team: "All secrets now in Bitwarden Cloud"

---

## Success Checklist (Phase 1 Done)

- [ ] Keeper export validated (300+ secrets)
- [ ] Bitwarden Cloud account created + 2FA
- [ ] bw CLI installed locally + Railway Docker
- [ ] All 300+ secrets imported + organized
- [ ] All API keys tested (Groq, OpenAI, Gemini, etc.)
- [ ] `secrets_provider.py` deployed + type-checked
- [ ] `/api/v1/secrets/health` returns 200
- [ ] Unit tests passing (12/12)
- [ ] Railway env vars set + masked
- [ ] Production endpoint responding
- [ ] Zero Keeper references in code
- [ ] Keeper vault deleted + confirmed
- [ ] Audit logs active (if implemented)
- [ ] Stage 11 report filed

---

## Effort & Timeline Summary

| Role | Effort | Dates |
|------|--------|-------|
| **Dev Team** | 11 hours | 2026-06-15 to 2026-06-18 |
| **Infra Team** | 4 hours | 2026-06-15 to 2026-06-20 |
| **Juan (Lead)** | 2.5 hours | 2026-06-15, 2026-06-20 |
| **QA** | 2 hours | 2026-06-17 |
| **Total** | ~20 hours | 1 week calendar time |

---

## Next Steps (Right Now)

1. ✅ OpenSpec created (spec.md, scenarios.md, tasks.md)
2. ✅ Code templates written (secrets_provider.py, endpoints, docker-compose)
3. ⏳ **T1 Start:** Juan exports Keeper CSV (30 min)
4. ⏳ **T2 Start:** Juan creates Bitwarden account (20 min)
5. ⏳ **T3 Start:** Dev installs bw CLI (30 min)
6. ⏳ **T4 Start:** Dev imports data to Bitwarden (1 hour)

**Go/No-Go Decision:** Once T1–T3 complete, team confirms readiness → proceed to T4–T6.

---

## Dashboard Update Schedule

- **Daily** (during Phase 1): Update task status, blockers, risks
- **Weekly** (Phase 2 gate): Stability metrics report
- **On-change:** Add new risks, update critical path if tasks slip

**DRI (Directly Responsible Individual):** Juan (Infra Lead)  
**Last Update:** 2026-06-15 16:00 UTC
