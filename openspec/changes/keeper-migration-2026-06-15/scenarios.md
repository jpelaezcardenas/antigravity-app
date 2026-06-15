# Scenarios: Keeper → Bitwarden Migration

## Scenario 1: Happy Path (Bitwarden Cloud Import Success)

**Given:**
- Keeper CSV export (300+ secrets) validated for integrity
- Bitwarden Cloud account created with 2FA
- bw CLI installed and authenticated locally

**When:**
- User runs checklist steps 4–11 (import, organize, validate)

**Then:**
- ✅ All 300+ secrets appear in Bitwarden Web Vault
- ✅ Folder structure matches expected (Infrastructure, LLM, Operations, Personal)
- ✅ API keys test successfully:
  ```bash
  bw get item [openai-key-id] → {"login": {"password": "sk-..."}}
  curl https://api.openai.com/v1/models -H "Authorization: Bearer sk-..." → 200
  ```
- ✅ `secrets_provider.py` in Railway staging retrieves secrets without error
- ✅ `/api/v1/secrets/health` returns `{"status": "healthy", "latency_ms": 145}`

---

## Scenario 2: Migration Failure - Broken API Key Format

**Given:**
- Keeper JSON export contains malformed API key (missing `sk-` prefix, bad encoding)
- Import script does NOT validate format before insertion

**When:**
- User attempts to use the key via `/api/v1/agents/llm_engine` (OpenAI fallback)

**Then:**
- ❌ LLM request fails: `OpenAI API error: Invalid authentication`
- ❌ Backend logs: `BitwardenProvider.get() returned invalid format for openai_key`
- ✅ **Recovery:** 
  1. Identify broken key via `bw list items --search openai`
  2. Delete corrupted entry: `bw delete item [bad-key-id]`
  3. Re-export Keeper, validate format, re-import
  4. Test LLM provider before considering migration complete

**Prevention:** Add format validation in import checklist (step 12).

---

## Scenario 3: Bitwarden CLI Auth Timeout

**Given:**
- Bitwarden vault rate-limit triggered (too many auth attempts)
- bw CLI session expires during bulk import

**When:**
- Checklist step 9 runs `bw import [file]` and hits rate limit

**Then:**
- ❌ Command exits: `Error: Request failed: 429 Too Many Requests`
- ❌ Partial import state unknown (may be incomplete)
- ✅ **Recovery:**
  1. Wait 15 minutes (rate limit window)
  2. Run `bw logout` then `bw login [email]` to refresh session
  3. Re-run import; Bitwarden detects duplicates and skips
  4. Verify final count matches 300+

**Prevention:** Add rate-limit backoff logic (documented in checklist).

---

## Scenario 4: Keeper Data Not Fully Exported

**Given:**
- User exports Keeper CSV but some secrets are inside shared vaults (org-level access restricted)
- Export only contains personal vault (50 secrets, missing 250 critical ones)

**When:**
- Checklist step 2 claims export is complete; user proceeds to import

**Then:**
- ❌ Migration appears successful but Railway gets `BW_VAULT_URL: [empty]`, `LLM_API_KEY: [missing]`
- ❌ LLM endpoints fail: `500 LLM provider credential not found`
- ❌ Social Ops ideas generation fails silently
- ✅ **Recovery:**
  1. Audit Keeper: Settings → Organization → Members → verify export scope
  2. Export again with org-level permissions (admin account)
  3. Merge both exports, re-import
  4. Run `/api/v1/secrets/health` to confirm all 300+ recovered

**Prevention:** Checklist step 1c explicitly warns about org vault scope.

---

## Scenario 5: Vercel/Railway Env Vars Not Updated

**Given:**
- Backend code successfully uses `BitwardenProvider`
- But Railway env vars still reference old Keeper URLs or legacy paths

**When:**
- Deploy to production; health check passes locally but fails on Railway

**Then:**
- ❌ Railway pod starts: `BW_VAULT_URL not set; falling back to Keeper (which is deleted)`
- ❌ All secret reads fail: `BitwardenProvider._auth(): client_id/secret not found`
- ✅ **Recovery:**
  1. Check Railway dashboard: Environment → Variables
  2. Add/update: `SECRETS_BACKEND=bitwarden`, `BW_CLIENT_ID`, `BW_CLIENT_SECRET`, `BW_VAULT_URL`
  3. Redeploy
  4. Verify: `curl https://api.contexia.online/api/v1/secrets/health` → 200

**Prevention:** Checklist step 17 (Railway config) is mandatory before step 19 (deploy).

---

## Scenario 6: Vaultwarden Phase 2 Decision (2-Week Gate)

**Given:**
- Bitwarden Cloud has been stable for 2 weeks (2026-07-04)
- All API keys working, no provider failures
- Team votes: migrate to self-hosted Vaultwarden

**When:**
- Checklist step 28 initiates: deploy `docker-compose.yml` to Railway

**Then:**
- ✅ Vaultwarden container starts: `listening on http://vaultwarden:80`
- ✅ PostgreSQL reachable: health check 200
- ✅ Data migrates: `bw export → vaultwarden import`
- ✅ Backend: update `BW_VAULT_URL=http://vaultwarden:80`
- ✅ All endpoints still work
- ✅ Bitwarden Cloud subscription cancelled (no longer needed)

**Alternative:** Bitwarden Cloud proves stable; Phase 2 deferred indefinitely.

---

## Scenario 7: Keeper Backup Retention Failure

**Given:**
- Keeper account deleted (step 20, irreversible)
- 2 days later, team discovers a secret was never imported (e.g., a shared vault key)

**When:**
- User tries to recover from Keeper: account gone, 7-day backup expired

**Then:**
- ❌ No recovery path; secret is lost
- ❌ Infrastructure affected: e.g., Supabase replication key missing, backups fail
- ✅ **Prevention (mandatory):**
  - Before step 20 (Keeper delete), run FULL audit:
    ```bash
    bw list items | wc -l  # Must equal 300+ or Keeper count
    bw list items --search [critical-key-name]  # Find each critical provider
    ```
  - Keep Keeper read-only for 30 days after deletion (don't hard-delete)
  - Export Bitwarden to JSON as backup: `bw export organization [org-id] > bitwarden-backup-2026-06-20.json`

---

## Scenario 8: LLM Provider Cascade Failure (Groq → Cerebras → Gemini)

**Given:**
- `llm_engine.py` uses failover: Groq (primary) → Cerebras → Mistral → Gemini → OpenRouter
- Groq key in Bitwarden is invalidated (leaked/rotated)

**When:**
- Backend calls `get_provider().get("llm/groq_api_key")` → returns old, invalid key
- Groq request fails: `401 Unauthorized`

**Then:**
- ✅ Failover triggers: tries Cerebras
- ✅ But Cerebras key is ALSO in Bitwarden with same issue
- ❌ Eventually hits OpenRouter free tier (slow, rate-limited)
- ✅ **Prevention:**
  1. Keep Groq key valid; test monthly via `/api/v1/agents/health`
  2. Use `SecretsProvider.list("LLM")` to audit all LLM keys monthly
  3. Log provider-switch events: `llm_engine: cascading to Cerebras (Groq failed)`

---

## Scenario 9: Audit Trail Missing (Compliance Gap)

**Given:**
- Bitwarden logs each secret access in Web Vault dashboard
- But FastAPI backend doesn't log which app/process accessed which secret

**When:**
- Compliance audit asks: "Who accessed the Supabase PAT on 2026-06-18?"

**Then:**
- ❌ No FastAPI audit trail; only Bitwarden shows vault access
- ✅ **Solution:** Add logging to `SecretsProvider`:
  ```python
  async def get(self, key: str) -> Optional[str]:
      logger.info(f"SECRET_ACCESS: key={key}, user={current_user}, timestamp={now}")
      return ...
  ```
- Persist logs to Supabase `secret_audit` table (RLS enabled)

---

## Scenario 10: Bitwarden Cloud Outage (Phase 1 Dependency)

**Given:**
- Bitwarden Cloud API is down (DDoS, maintenance, etc.)
- Backend in production tries to fetch secret

**When:**
- `BitwardenProvider.get()` times out: `urllib3.exceptions.ConnectTimeout`

**Then:**
- ❌ LLM call fails if retry_policy not set
- ✅ **Recovery:** Add circuit-breaker pattern:
  ```python
  if bw_health_check() fails:
      logger_alert("CRITICAL: Bitwarden provider down; falling back to local cache")
      return SECRET_CACHE.get(key)  # Last-known-good value
  ```
- Notify ops: "Bitwarden outage detected; mitigated by cache"
- Post-outage: refetch from Bitwarden to sync

**Prevention:** Health check runs every 30s; alert on first failure.

---

## Summary Table

| Scenario | Severity | Prevention | Detection |
|----------|----------|-----------|-----------|
| 1: Happy path | Low | None (success) | Checklist ✅ |
| 2: Broken API key | High | Format validation (checklist #12) | Test LLM call |
| 3: Auth timeout | Medium | Rate limit backoff | bw import error |
| 4: Incomplete export | Critical | Audit Keeper scope first | Secret missing from Bw |
| 5: Missing env vars | High | Checklist #17 mandatory | Railway pod logs |
| 6: Phase 2 smooth | Low | 2-week stable gate | Migration success |
| 7: Keeper lost | Critical | Audit + export backup | Unrecoverable |
| 8: LLM failover cascade | Medium | Monthly key validation | Fallback to OpenRouter |
| 9: Audit gap | Medium | Add logging to `SecretsProvider` | Compliance audit |
| 10: Bitwarden outage | High | Circuit-breaker + cache | Health check failure |
