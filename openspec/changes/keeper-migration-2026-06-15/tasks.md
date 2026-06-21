# Tasks: Keeper â†’ Bitwarden Migration Implementation

## Grouping
- **T1â€“T3:** Migration setup (Keeper export, Bitwarden account, CLI install)
- **T4â€“T6:** Data migration (import, organize, validate)
- **T7â€“T9:** Backend integration (secrets_provider.py, health check, tests)
- **T10â€“T12:** Production deployment (Railway env, staging test, production push)
- **T13â€“T14:** Validation & cleanup (health check, Keeper delete)

---

## Phase 1: Bitwarden Cloud (T1â€“T14)

### T1: Export Keeper CSV (Phase 1 Blocker)

**Objective:** Export all 300+ secrets from Keeper to JSON format, validate structure.

**Steps:**
1. Access https://my.keepersecurity.com â†’ Settings â†’ Export
2. Select "JSON (unencrypted)" format
3. Export to file: `keeper-export-2026-06-15.json`
4. Validate JSON structure:
   ```bash
   jq '.[]' keeper-export-2026-06-15.json | head -5
   # Should show login entries with password, url, username, etc.
   ```
5. Count records: `jq '. | length' keeper-export-2026-06-15.json` â†’ Must be â‰¥ 300
6. Check for critical keys:
   ```bash
   jq -r '.[].title' keeper-export-2026-06-15.json | grep -E "(Groq|OpenAI|Gemini|Supabase|Railway|Vercel)"
   # All must be present
   ```

**Acceptance:** keeper-export-2026-06-15.json validated, 300+ records, all critical keys present.

**Owner:** Juan (Infra)  
**Effort:** 30 min  
**Deadline:** 2026-06-15  
**Status:** â³ Ready

---

### T2: Create Bitwarden Cloud Account

**Objective:** Set up Bitwarden Cloud account, enable 2FA, obtain API credentials.

**Steps:**
1. Go to https://vault.bitwarden.com â†’ Sign Up
2. Register account: email `growth@contexia.online`, master password (32+ chars, random)
3. Enable 2FA: authenticator app or backup codes
4. Log in to Web Vault
5. Create Organization:
   - Name: `Contexia`
   - Plan: Free (sufficient for Phase 1)
6. Navigate to Settings â†’ Organization â†’ API Key
7. Generate client ID + secret; store securely:
   ```
   BW_CLIENT_ID=[id]
   BW_CLIENT_SECRET=[secret]
   BW_MASTER_PASSWORD=[master-pwd]
   ```

**Acceptance:** Account verified, 2FA enabled, API keys generated and accessible.

**Owner:** Juan (Infra)  
**Effort:** 20 min  
**Deadline:** 2026-06-15  
**Status:** â³ Ready

---

### T3: Install & Test Bitwarden CLI

**Objective:** Install bw CLI, authenticate, verify connectivity.

**Steps:**
1. Install bw CLI:
   ```bash
   # macOS
   brew install bitwarden-cli
   # or download: https://bitwarden.com/download
   ```
2. Verify installation: `bw --version`
3. Test login:
   ```bash
   bw login growth@contexia.online [master-password]
   # Returns session token
   ```
4. Test sync:
   ```bash
   bw sync
   # Should complete without errors
   ```
5. Add to Railway Dockerfile:
   ```dockerfile
   RUN apt-get install -y bw
   ```

**Acceptance:** bw CLI works locally + Dockerfile includes bw, authenticated successfully.

**Owner:** Dev Team  
**Effort:** 30 min  
**Deadline:** 2026-06-15  
**Status:** â³ Ready

---

### T4: Transform & Import Keeper JSON to Bitwarden

**Objective:** Convert Keeper JSON format to Bitwarden JSON, import 300+ secrets.

**Steps:**
1. Create transformation script (or use https://github.com/bitwarden/vault-import-tools):
   ```python
   import json
   keeper_export = json.load(open('keeper-export-2026-06-15.json'))
   bitwarden_items = []
   for secret in keeper_export:
       item = {
           "organizationId": None,
           "type": 1,  # login type
           "name": secret.get('title'),
           "notes": secret.get('notes'),
           "login": {
               "username": secret.get('login'),
               "password": secret.get('password')
           },
           "fields": []
       }
       bitwarden_items.append(item)
   json.dump({"encrypted": False, "items": bitwarden_items}, 
             open('keeper-export-bitwarden.json', 'w'))
   ```
2. Run import:
   ```bash
   bw import keepersecurity keeper-export-bitwarden.json
   # or use bw create item [item-json] per entry
   ```
3. Verify count: `bw list items | jq '. | length'` â†’ Must be 300+

**Acceptance:** 300+ items imported, accessible via Web Vault.

**Owner:** Dev Team  
**Effort:** 1 hour  
**Deadline:** 2026-06-16  
**Status:** â³ Ready

---

### T5: Organize Bitwarden Folders & Validate Structure

**Objective:** Create folder hierarchy, move secrets to proper folders, validate structure.

**Steps:**
1. Create folders in Bitwarden Web Vault:
   - `Contexia/Infrastructure` (Railway, Vercel, Supabase, DNS, GitHub)
   - `Contexia/LLM-Providers` (OpenAI, Groq, Gemini, Mistral, Cerebras, OpenRouter)
   - `Contexia/Operations` (n8n, Slack, Telegram, Discord)
   - `Personal/` (user personal credentials)
2. Move items to folders (manual or script):
   ```bash
   bw get item [item-id] | jq '.folderId = "[folder-id]"' | bw encode | bw edit item [item-id]
   ```
3. Validate structure:
   ```bash
   bw list items | jq '.[] | {name, folderId}' | sort
   ```
4. Spot-check critical items:
   - `Contexia/Infrastructure/Supabase-PAT`
   - `Contexia/LLM-Providers/Groq-API-Key`
   - `Contexia/LLM-Providers/OpenAI-Key`

**Acceptance:** All folders created, items organized, spot-checks pass.

**Owner:** Juan (Infra)  
**Effort:** 1 hour  
**Deadline:** 2026-06-16  
**Status:** â³ Ready

---

### T6: Validate All API Keys (Critical Gate)

**Objective:** Test each API key against its provider; confirm no expired/invalid keys.

**Steps:**
1. For each LLM provider key, test:
   ```bash
   # Groq
   curl -H "Authorization: Bearer $(bw get item [groq-key-id] | jq -r '.login.password')" \
     https://api.groq.com/openai/v1/models
   
   # OpenAI
   curl -H "Authorization: Bearer $(bw get item [openai-key-id] | jq -r '.login.password')" \
     https://api.openai.com/v1/models
   
   # Gemini
   curl "https://generativelanguage.googleapis.com/v1/models/gemini-pro?key=$(bw get item [gemini-key-id] | jq -r '.login.password')"
   ```
2. Log results to validation report:
   ```
   Groq: âœ… 200 OK
   OpenAI: âœ… 200 OK
   Gemini: âœ… 200 OK
   Mistral: âœ… 200 OK
   Cerebras: âœ… 200 OK
   OpenRouter: âœ… 200 OK
   ```
3. For infrastructure keys, verify basic access:
   ```bash
   # Railway
   export RAILWAY_TOKEN=$(bw get item [railway-token-id] | jq -r '.login.password')
   curl -H "Authorization: Bearer $RAILWAY_TOKEN" https://api.railway.app/graphql
   
   # Vercel
   export VERCEL_TOKEN=$(bw get item [vercel-token-id] | jq -r '.login.password')
   curl -H "Authorization: Bearer $VERCEL_TOKEN" https://api.vercel.com/v2/user
   ```
4. Document any failures; escalate as T6-BLOCKER

**Acceptance:** All critical keys validated, report signed off, zero failures.

**Owner:** Dev Team + Infra  
**Effort:** 2 hours  
**Deadline:** 2026-06-16  
**Status:** â³ Ready

---

### T7: Implement SecretsProvider Module (Type-Safe)

**Objective:** Create abstract `SecretsProvider` class + Bitwarden/Vaultwarden concrete implementations.

**Deliverable:** `apps/backend/core/secrets_provider.py` (500+ LOC)

**Requirements:**
- Abstract base class: `get()`, `set()`, `delete()`, `list()`, `health()`
- `BitwardenCloudProvider`: subprocess bw CLI calls, session management
- `VaultwardenProvider`: wrapper using same logic, different BW_URL
- Full typing: Pydantic BaseSettings, Dict[str, Any] returns, Optional handling
- Error handling: try/except with structured logging
- No print statements; logging only

**Steps:**
1. Create file: `apps/backend/core/secrets_provider.py`
2. Implement classes per spec (Section 2)
3. Add type hints: `async def get(self, key: str) -> Optional[str]`
4. Add docstrings: "Obtiene valor de una clave (formato 'folder/name' o ID)"
5. Add logging: `logger.info()`, `logger.error()`
6. Test locally:
   ```python
   provider = BitwardenCloudProvider(...)
   value = await provider.get("Contexia/Infrastructure/Groq-API-Key")
   assert value.startswith("gsk_")
   ```

**Acceptance:** Module compiles, type-checks pass, all methods callable.

**Owner:** Dev Team (Backend)  
**Effort:** 3 hours  
**Deadline:** 2026-06-17  
**Status:** â³ Ready

---

### T8: Implement /api/v1/secrets/health Endpoint

**Objective:** Create FastAPI endpoint to health-check active SecretsProvider.

**Deliverable:** `apps/backend/api/endpoints/secrets_endpoints.py` + integration in `main.py`

**Steps:**
1. Create file: `apps/backend/api/endpoints/secrets_endpoints.py`
2. Implement router:
   ```python
   @router.get("/health")
   async def secrets_health(provider = Depends(get_provider)) -> Dict[str, Any]:
       return await provider.health()
   ```
3. Return schema:
   ```json
   {
     "status": "healthy",
     "provider": "bitwarden-cloud",
     "latency_ms": 145,
     "vault_url": "https://vault.bitwarden.com"
   }
   ```
4. Integrate in `apps/backend/main.py`:
   ```python
   from apps.backend.api.endpoints.secrets_endpoints import router as secrets_router
   app.include_router(secrets_router, prefix="/api/v1")
   ```
5. Test locally:
   ```bash
   curl http://localhost:8000/api/v1/secrets/health
   # â†’ {"status": "healthy", "latency_ms": ...}
   ```

**Acceptance:** Endpoint deployed, returns 200 with correct schema, latency < 500ms.

**Owner:** Dev Team (Backend)  
**Effort:** 1 hour  
**Deadline:** 2026-06-18  
**Status:** â³ Ready

---

### T9: Unit Tests for SecretsProvider (Async)

**Objective:** Write pytest tests for all SecretsProvider methods (mock bw CLI).

**Steps:**
1. Create file: `tests/backend/core/test_secrets_provider.py`
2. Mock bw CLI subprocess:
   ```python
   @pytest.fixture
   def mock_bw_run(monkeypatch):
       async def fake_run(*args):
           if "groq" in str(args):
               return {"login": {"password": "gsk_fake_..."}}
           return {}
       monkeypatch.setattr("subprocess.run", fake_run)
       yield fake_run
   ```
3. Test all methods:
   - `test_get_bitwarden_success()`
   - `test_get_invalid_key_returns_none()`
   - `test_set_creates_item()`
   - `test_delete_removes_item()`
   - `test_list_filters_by_folder()`
   - `test_health_check_returns_schema()`
4. Run tests:
   ```bash
   pytest tests/backend/core/test_secrets_provider.py -v
   # target: 12 passed
   ```

**Acceptance:** All 12 tests passing, >90% code coverage.

**Owner:** Dev Team (QA)  
**Effort:** 2 hours  
**Deadline:** 2026-06-17  
**Status:** â³ Ready

---

### T10: Configure Railway Environment Variables (Production)

**Objective:** Add SECRETS_BACKEND, BW_*, env vars to Railway project.

**Steps:**
1. Log into Railway: https://railway.app â†’ Contexia project â†’ antigravity-app
2. Go to: Variables tab
3. Add new variables:
   ```
   SECRETS_BACKEND=bitwarden
   BW_CLIENT_ID=[from T2]
   BW_CLIENT_SECRET=[from T2, masked]
   BW_MASTER_PASSWORD=[from T2, masked]
   BW_VAULT_URL=https://vault.bitwarden.com
   ```
4. Verify no typos:
   - BW_CLIENT_ID starts with lowercase
   - BW_CLIENT_SECRET matches exactly
   - BW_VAULT_URL has https://
5. Save variables

**Acceptance:** All 5 variables set in Railway, no validation errors.

**Owner:** Infra  
**Effort:** 20 min  
**Deadline:** 2026-06-18  
**Status:** â³ Ready

---

### T11: Deploy to Staging + Test Health Endpoint

**Objective:** Deploy secrets_provider.py to Railway staging, verify /api/v1/secrets/health.

**Steps:**
1. Commit code:
   ```bash
   git add apps/backend/core/secrets_provider.py apps/backend/api/endpoints/secrets_endpoints.py
   git commit -m "feat: add bitwarden secrets provider with health check endpoint"
   ```
2. Push to staging branch:
   ```bash
   git push origin feature/secrets-provider-bitwarden
   ```
3. Wait for Railway deploy: 2â€“3 minutes
4. Test staging endpoint:
   ```bash
   curl https://staging-api.contexia.online/api/v1/secrets/health
   # â†’ {"status": "healthy", "provider": "bitwarden-cloud", "latency_ms": 234}
   ```
5. Monitor logs for errors:
   ```bash
   railway logs --follow
   # Should show zero BitwardenProvider errors
   ```

**Acceptance:** Endpoint responds 200, latency <500ms, zero errors in logs.

**Owner:** Dev Team  
**Effort:** 1 hour  
**Deadline:** 2026-06-18  
**Status:** â³ Ready

---

### T12: Production Deploy + Stage 11

**Objective:** Deploy to production, run Stage 11 checklist.

**Steps:**
1. **Stage 11: Commit & Push**
   ```bash
   git push origin main
   ```
2. **Stage 11: Verify CI/CD**
   - Vercel: wait for deployment to Ready
   - Railway: wait for backend deploy to Active
3. **Stage 11: Verify Production URL**
   ```bash
   curl https://contexia.online/api/v1/secrets/health
   # â†’ {"status": "healthy", ...}
   ```
4. **Stage 11: Test Endpoints**
   ```bash
   # LLM endpoint should work (uses secrets)
   curl -X POST https://contexia.online/api/v1/agents/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
   # Should succeed (not fail with credential error)
   ```
5. **Stage 11: Report**
   - Create: `openspec/changes/keeper-migration-2026-06-15/reports/2026-06-18-production-deploy.md`
   - Document: deploy time, endpoints tested, zero errors
6. **Stage 11: Archive** (done in T14)

**Acceptance:** Production endpoint 200, all LLM calls work, health check passes.

**Owner:** Dev Team + Infra  
**Effort:** 1.5 hours  
**Deadline:** 2026-06-18  
**Status:** â³ Ready

---

### T13: Comprehensive Health & Audit Checks

**Objective:** Verify all API keys work, zero Keeper references remain, audit trail ready.

**Steps:**
1. Run validation suite:
   ```bash
   pytest tests/backend/core/test_secrets_provider.py -v  # Must pass
   bash scripts/validate-api-keys.sh  # All providers respond
   grep -r "keeper" apps/ --include="*.py"  # Must be 0 matches
   ```
2. Check logs for Keeper references:
   ```bash
   railway logs --follow 2>&1 | grep -i keeper  # Must be empty
   ```
3. Verify audit table exists (if logging implemented):
   ```sql
   SELECT COUNT(*) FROM secret_audit WHERE created_at > NOW() - INTERVAL '1 day';
   # Should show secret accesses logged
   ```
4. Document in report

**Acceptance:** All validations pass, zero Keeper references, audit logs active.

**Owner:** Infra + Dev Team  
**Effort:** 1 hour  
**Deadline:** 2026-06-19  
**Status:** â³ Ready

---

### T14: Delete Keeper Vault (Irreversible)

**Objective:** Remove Keeper organization, confirm deletion, document in report.

**Prerequisites:** T13 (all validations passing), 2 weeks stable Bitwarden NOT required for Phase 1; can proceed immediately after T13.

**Steps:**
1. Log into Keeper: https://my.keepersecurity.com
2. Go to: Settings â†’ Organization â†’ Delete Organization
3. Confirm deletion (irreversible warning)
4. Wait 24 hours for deletion to complete
5. Verify deletion: try to log in with old org account â†’ should fail
6. Document:
   ```markdown
   ## Keeper Deletion Report
   - Deleted: 2026-06-20 14:30 UTC
   - Organization: [Keeper org name]
   - Total secrets deleted: 300+
   - Backup: Bitwarden export saved to S3
   ```
7. Notify team: "Keeper vault deleted; Bitwarden is single source of truth"

**Acceptance:** Keeper account completely deleted, confirmed inaccessible, report filed.

**Owner:** Juan (Infra)  
**Effort:** 30 min (plus 24-hour wait)  
**Deadline:** 2026-06-20  
**Status:** â³ Ready

---

## Phase 2: Vaultwarden Self-Hosted (T15â€“T18, Deferred)

### T15: 2-Week Stability Gate (Decision Point)

**Objective:** Monitor Bitwarden Cloud for 14 days; decide Phase 2 go/no-go.

**Timeline:** 2026-07-04 (2 weeks after Keeper deletion 2026-06-20)

**Success Criteria:**
- âœ… Zero secret retrieval failures
- âœ… Health check latency <300ms consistently
- âœ… All LLM provider calls working
- âœ… No rate-limit errors from Bitwarden
- âœ… Team consensus: proceed to self-hosted

**Decision Options:**
1. **Proceed to T16:** Deploy Vaultwarden, migrate from Cloud
2. **Defer:** Keep Bitwarden Cloud, revisit in Q3 2026
3. **Abandon:** Bitwarden Cloud proven sufficient; no Phase 2

**Owner:** Juan (Infra) + Tech Lead  
**Effort:** Monitoring (auto), decision (30 min)  
**Deadline:** 2026-07-04  
**Status:** â³ Deferred

---

### T16â€“T18: Vaultwarden Deploy, Migrate, Cleanup (T16â€“T18)
*(Same as docker-compose + railway.toml in Section 4; not implemented yet)*

---

## Summary Table

| Task | Owner | Effort | Deadline | Status | Blocker |
|------|-------|--------|----------|--------|---------|
| T1: Export Keeper | Juan | 30m | 2026-06-15 | â³ | None |
| T2: BW Cloud account | Juan | 20m | 2026-06-15 | â³ | T1 |
| T3: bw CLI install | Dev | 30m | 2026-06-15 | â³ | T2 |
| T4: Import to BW | Dev | 1h | 2026-06-16 | â³ | T3 |
| T5: Organize folders | Juan | 1h | 2026-06-16 | â³ | T4 |
| T6: Validate API keys | Dev+Infra | 2h | 2026-06-16 | â³ | T5 |
| T7: SecretsProvider | Dev | 3h | 2026-06-17 | â³ | None |
| T8: Health endpoint | Dev | 1h | 2026-06-18 | â³ | T7 |
| T9: Unit tests | QA | 2h | 2026-06-17 | â³ | T7 |
| T10: Railway env vars | Infra | 20m | 2026-06-18 | â³ | T6, T7 |
| T11: Deploy staging | Dev | 1h | 2026-06-18 | â³ | T10 |
| T12: Production deploy | Dev+Infra | 1.5h | 2026-06-18 | â³ | T11 |
| T13: Health audits | Infra+Dev | 1h | 2026-06-19 | â³ | T12 |
| T14: Delete Keeper | Juan | 30m | 2026-06-20 | â³ | T13 |
| T15: 2w gate (decision) | Juan+TL | 30m | 2026-07-04 | â³ | T14 |

---

## Total Phase 1 Effort

**Dev Team:** 11 hours (T3, T4, T7, T8, T9, T11, T12, T13)  
**Infra Team:** 4 hours (T2, T5, T10, T13, T14)  
**Juan:** 2.5 hours (T1, T2, T5, T14)  
**QA:** 2 hours (T9)

**Total:** ~20 hours, concurrent execution â†’ **1 week calendar time**

---

## Dependencies & Critical Path

```
T1 â†’ T3 â†’ T4 â†’ T5 â†’ T6 â†˜
                        â†“
T7 â†’ T8 â†’ T9 â†’ T10 â†’ T11 â†’ T12 â†’ T13 â†’ T14
```

**Critical path:** T1 â†’ T3 â†’ T4 â†’ T5 â†’ T6 â†’ T10 â†’ T11 â†’ T12 â†’ T13 â†’ T14 (â‰ˆ 1 week)

---

## Mandatory OpenSpec Updates

If any of these occur, STOP and update OpenSpec:
- API key format changes â†’ update T6 validation
- Bitwarden import fails due to new record type â†’ update T4, scenarios
- Health check latency unexpectedly high â†’ update T8 schema, scenarios
- Keeper deletion cannot happen as scheduled â†’ update timeline

