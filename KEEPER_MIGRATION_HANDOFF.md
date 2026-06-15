# Keeper → Bitwarden Migration: Handoff Document

**Date Created:** 2026-06-15 16:45 UTC  
**Status:** Phase 1 T1 COMPLETED ✅ | Ready for T2–T14  
**Previous Session:** Claude Code (Web)  
**Continuing In:** Claude Code (Desktop/CLI)  
**DRI:** Juan (Infra Lead)

---

## SESSION CONTEXT

This is a **spec-first, OpenSpec-driven migration** of 330+ secrets from Keeper (exposed) → Bitwarden Cloud (Phase 1) → Vaultwarden self-hosted (Phase 2, deferred).

**Critical:** Do NOT skip OpenSpec validation. All code changes MUST be reflected in tasks.md first.

---

## CURRENT STATE (as of 2026-06-15 16:45 UTC)

### ✅ COMPLETED (2 commits)

**Commit 1: `ed8babd`**
- OpenSpec artifacts (5 files): spec.md, scenarios.md, tasks.md, README.md, MIGRATION_DASHBOARD.md
- Implementation code: secrets_provider.py, secrets_endpoints.py
- Phase 2 configs: docker-compose.vaultwarden.yml, railway.vaultwarden.toml, Dockerfile.vaultwarden, .env.vaultwarden.example

**Commit 2: `177d2fc`**
- T1 validation report: reports/T1-KEEPER-EXPORT-VALIDATION-2026-06-15.md
- Result: 330 secrets exported, all 6 LLM keys present, Supabase/Railway/Vercel credentials intact

### ⏳ PENDING (T2–T14)

| Task | Owner | Est. Effort | Timeline | Blocker |
|------|-------|-------------|----------|---------|
| T2: Bitwarden Cloud account | Juan | 20m | 2026-06-15 | T1 ✅ |
| T3: bw CLI install | Dev | 30m | 2026-06-15 | T2 |
| T4: Data import to BW | Dev | 1h | 2026-06-16 | T3 |
| T5: Folder organization | Juan | 1h | 2026-06-16 | T4 |
| T6: API key validation | Dev+Infra | 2h | 2026-06-16 | T5 **GATE** |
| T7: SecretsProvider impl | Dev | 3h | 2026-06-17 | None (code ✅ exists) |
| T8: Health endpoint | Dev | 1h | 2026-06-18 | T7 (code ✅ exists) |
| T9: Unit tests | QA | 2h | 2026-06-17 | T7 |
| T10: Railway env vars | Infra | 20m | 2026-06-18 | T6, T7 |
| T11: Staging deploy | Dev | 1h | 2026-06-18 | T10 |
| T12: Production (Stage 11) | Dev+Infra | 1.5h | 2026-06-18 | T11 **GATE** |
| T13: Health audits | Infra+Dev | 1h | 2026-06-19 | T12 |
| T14: Delete Keeper | Juan | 30m | 2026-06-20 | T13 **GATE** |

---

## NEXT IMMEDIATE ACTIONS (Priority Order)

### 1️⃣ T2: Create Bitwarden Cloud Account (Juan, NOW)

```bash
# 1. Open https://vault.bitwarden.com → Sign Up
# 2. Register:
#    - Email: growth@contexia.online
#    - Master Password: Generate random 32+ chars
#    - Save to secure location (Keeper temporarily, then delete)
#
# 3. Enable 2FA: Settings → Two-Step Login → Authenticator app
#
# 4. Create Organization:
#    - Name: "Contexia"
#    - Plan: Free (sufficient for Phase 1)
#
# 5. Generate API Key:
#    - Settings → Organization → API Key
#    - Save: BW_CLIENT_ID, BW_CLIENT_SECRET, BW_MASTER_PASSWORD
#    - These MUST go to Railway env vars in T10
#
# 6. Commit progress:
#    git commit -m "docs: T2 bitwarden cloud account created (growth@contexia.online)"
```

**Timeline:** 20 minutes  
**Next Step:** T3 (bw CLI install) by same person or Dev team

---

### 2️⃣ T3: Install & Verify bw CLI (Dev Team, after T2)

```bash
# 1. Install bw CLI (choose your OS):
#    macOS: brew install bitwarden-cli
#    Windows: Download https://bitwarden.com/download
#    Linux: npm install -g @bitwarden/cli
#
# 2. Verify installation:
bw --version
#
# 3. Login to Bitwarden (from T2):
bw login growth@contexia.online
# → Will prompt for master password, enter from T2
# → Returns session token
#
# 4. Verify sync:
bw sync
# → Should complete without errors
#
# 5. Add to Railway Dockerfile (if not already done):
#    RUN apt-get install -y bw
#
# 6. Commit:
git commit -m "docs: T3 bw CLI installed and verified locally"
```

**Timeline:** 30 minutes  
**Blocker:** Requires T2 complete (Bitwarden account created)  
**Next Step:** T4 (import Keeper JSON)

---

## CRITICAL FILES TO REFERENCE

| File | Purpose | Read When |
|------|---------|-----------|
| `openspec/changes/keeper-migration-2026-06-15/spec.md` | Problem/solution/criteria | Before coding |
| `openspec/changes/keeper-migration-2026-06-15/tasks.md` | Task details, dependencies, rollback | Before each T |
| `openspec/changes/keeper-migration-2026-06-15/MIGRATION_DASHBOARD.md` | Timeline, metrics, gates, risks | For progress tracking |
| `openspec/changes/keeper-migration-2026-06-15/README.md` | Quick start guide | First thing |
| `apps/backend/core/secrets_provider.py` | Abstract provider (✅ DONE) | Reference only |
| `apps/backend/api/endpoints/secrets_endpoints.py` | Health endpoint (✅ DONE) | Reference only |
| `docker-compose.vaultwarden.yml` | Phase 2 config (✅ DONE) | For T16 (Phase 2) |

---

## KEY CONSTRAINTS & RULES

### ❌ DO NOT

- ❌ Commit code without updating OpenSpec tasks.md first (spec-first)
- ❌ Delete Keeper before T13 validation complete (irreversible)
- ❌ Skip T6 API validation gate (all providers MUST work)
- ❌ Deploy production without T11 staging pass + T12 Stage 11 checklist
- ❌ Leave Keeper CSV export on disk after T4 complete (use `shred` or `cipher /w`)

### ✅ DO

- ✅ Run T4–T6 in parallel (import, organize, validate can overlap)
- ✅ Update MIGRATION_DASHBOARD.md status as you complete each task
- ✅ Add validation evidence to `reports/` folder (screenshots, curl responses)
- ✅ Create new commits for each logical task completion
- ✅ Use Stage 11 checklist for T12 (commit → push → verify live → report)

---

## GIT WORKFLOW

### Commit Template

```bash
git add [files]
git commit -m "feat/docs: [T#] [description]

Detailed explanation if needed.

OpenSpec change: keeper-migration-2026-06-15
Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

### Example Commits

```bash
# T2 completion
git commit -m "docs: T2 bitwarden cloud account created"

# T4 completion
git commit -m "docs: T4 keeper json imported to bitwarden cloud (330 items)"

# T7 completion
git commit -m "feat: T7 integrate secrets_provider into fastapi (no changes needed, already in place)"

# T12 completion (Stage 11)
git commit -m "feat: T12 production deploy secrets migration complete (Stage 11)

Verified:
- Railway health check: 200 ✅
- All LLM endpoints working ✅
- Zero Keeper references in logs ✅

OpenSpec change: keeper-migration-2026-06-15"
```

---

## TESTING VERIFICATION COMMANDS

### Before/After Each API Key Validation (T6)

```bash
# Groq
GROQ_KEY=$(bw get item groq_key | jq -r '.login.password')
curl -H "Authorization: Bearer $GROQ_KEY" \
  https://api.groq.com/openai/v1/models \
  | jq '.data[0].id'
# Expected: "mixtral-8x7b-32768" or similar

# OpenAI
OPENAI_KEY=$(bw get item openai_key | jq -r '.login.password')
curl -H "Authorization: Bearer $OPENAI_KEY" \
  https://api.openai.com/v1/models \
  | jq '.data[0].id'
# Expected: "gpt-4" or similar

# Gemini
GEMINI_KEY=$(bw get item gemini_key | jq -r '.login.password')
curl "https://generativelanguage.googleapis.com/v1/models/gemini-pro?key=$GEMINI_KEY" \
  | jq '.name'
# Expected: "models/gemini-pro" or similar
```

### After Production Deploy (T12)

```bash
# Health check
curl https://contexia.online/api/v1/secrets/health
# Expected: {"status": "healthy", "provider": "bitwarden-cloud", "latency_ms": <int>}

# Test LLM (sample)
curl -X POST https://contexia.online/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
# Expected: 200, not 500 (no credential errors)
```

---

## DECISION GATES (MANDATORY STOPS)

### 🛑 GATE 1: T6 Complete (All APIs Validated)

**Before proceeding to T7:**
- [ ] All 6 LLM keys tested successfully (curl responses 200)
- [ ] Supabase connection verified
- [ ] Telegram bot token working
- [ ] Document results in `reports/T6-API-VALIDATION-RESULTS.md`

**If gate fails:** Root-cause in scenarios.md (Scenario 2: API key format incompatible)

### 🛑 GATE 2: T12 Production Deploy (Stage 11 Complete)

**Before deleting Keeper (T14):**
- [ ] Commit pushed to origin
- [ ] Vercel + Railway showing "Ready" / "Active"
- [ ] Health check endpoint returns 200 in production
- [ ] LLM endpoints respond (no credential errors)
- [ ] Zero Keeper references in `git log` or code
- [ ] Stage 11 report filed: `reports/2026-06-18-production-deploy.md`

**If gate fails:** Rollback per scenarios.md (Scenario 5: Missing env vars)

### 🛑 GATE 3: T14 Keeper Deletion (Irreversible)

**Before running Keeper delete:**
- [ ] T13 health audits PASSED
- [ ] Bitwarden export backed up to S3 (if available) or encrypted USB
- [ ] 7-day Keeper read-only retention enabled (if possible)
- [ ] Team sign-off documented in `reports/T14-KEEPER-DELETION-APPROVAL.md`

**After deletion:** No rollback available. Keep backup safe for 30 days.

---

## PHASE 2 DECISION GATE (2026-07-04)

After T14 complete, **wait 2 weeks** (2 weeks stable on Bitwarden Cloud).

On 2026-07-04:
1. Review MIGRATION_DASHBOARD.md metrics (health check latency, uptime, failures)
2. Team vote: **Proceed to Vaultwarden self-hosted (T16–T18)?** or **Stay on Cloud?**
3. Document decision in `reports/2026-07-04-phase2-decision.md`

If **YES**: Proceed with T16–T18 (docker-compose.vaultwarden.yml already written)  
If **NO**: Keep Bitwarden Cloud; close change as stable

---

## DEBUGGING CHECKLIST

### If bw CLI times out (T3/T4)

```bash
# Increase timeout
export BW_BASEURL=https://vault.bitwarden.com
bw logout
bw login growth@contexia.online --raw
# Wait for output, then try again
```

### If Bitwarden import fails (T4)

```bash
# Check format
jq . keeper-export-2026-06-15.json | head -20
# Should show login entries with password, url, username

# Try single item
bw create item '{"type": 1, "name": "test", "login": {"username": "x", "password": "y"}}'
# If this works, format is correct; retry full import
```

### If health check fails in production (T12)

```bash
# Check Railway logs
railway logs --follow
# Look for BitwardenProvider errors

# Check Railway env vars
railway env list
# Verify: SECRETS_BACKEND=bitwarden, BW_CLIENT_ID, BW_CLIENT_SECRET set

# Rollback to staging
git revert HEAD~1
git push origin main
```

---

## HANDOFF SUMMARY

| Item | Status | Location |
|------|--------|----------|
| **OpenSpec** | ✅ Complete (5 docs) | openspec/changes/keeper-migration-2026-06-15/ |
| **Code** | ✅ Written (6 files) | apps/backend/core/, apps/backend/api/endpoints/ |
| **T1 Validation** | ✅ Complete (330 secrets) | reports/T1-KEEPER-EXPORT-VALIDATION-2026-06-15.md |
| **T2–T3** | ⏳ Ready to start | Instructions above ↑ |
| **T4–T14** | ⏳ Follow tasks.md | openspec/changes/keeper-migration-2026-06-15/tasks.md |
| **Phase 2 (T15–T18)** | ⏳ Decision gate 2026-07-04 | Configs already written |

---

## CONTACT & ESCALATION

| Issue | Contact | Slack Channel |
|-------|---------|---------------|
| Bitwarden account (T2) | Juan (Infra Lead) | #infra-team |
| Code/testing (T3–T9, T11–T13) | Dev Team | #engineering |
| Railway deploy (T10, T12) | Infra | #infra-team |
| Keeper deletion approval (T14) | Juan + Tech Lead | #security |
| Phase 2 decision (T15) | Juan + Tech Lead | #engineering |

---

## FINAL NOTES

1. **This is production-critical security work.** All gates MUST pass before proceeding.
2. **Spec-first discipline:** Update tasks.md BEFORE coding. No exceptions.
3. **Time estimate:** 20 hours total effort, 1 week calendar time with parallel execution.
4. **Stage 11 required:** Production deploy must include commit → push → verify live → report.
5. **Irreversible actions:** T14 (Keeper delete) has no rollback. Gate 3 MUST PASS.

---

**Last Updated:** 2026-06-15 16:45 UTC  
**Ready to Continue:** YES ✅  
**Next Owner:** Juan (T2)  
**Baseline:** All OpenSpec artifacts approved and code in place
