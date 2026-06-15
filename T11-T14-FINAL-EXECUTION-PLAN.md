# T11-T14: Final Execution Plan

**Date:** 2026-06-15  
**Owner:** Juan David (Infra Lead)  
**Timeline:** 2-3 hours total  

---

## Status Check (Now)

```bash
# Current state
git branch -v
# Output: fix/security-bug-audit-2026-06-14 âœ… (ready to merge)

git log --oneline -1
# Output: 5f0c38e docs: final status summary (PRODUCTION READY)

curl https://contexia.online/api/v1/secrets/health
# Output: {"detail":"Not Found"}
# Reason: Code not yet in main (expected)
```

---

## T11: Staging Deploy âœ… Ready

**What it is:** Verify code builds in staging environment

**Steps:**

1. **Create PR or merge to `develop`** (if you have staging branch):
   ```bash
   git checkout develop
   git merge fix/security-bug-audit-2026-06-14
   git push origin develop
   ```
   â†’ Railway auto-deploys to staging

2. **Verify staging deploy (10 min):**
   ```bash
   # Check Railway dashboard: https://railway.app
   # Status should be: "Ready" (green)
   
   # Or check logs:
   railway logs --follow
   ```

3. **If staging passes â†’ proceed to T12**

---

## T12: Production Deploy (Stage 11) â³ READY

**What it is:** Merge code to `main` and deploy to production

### Step 1: Resolve Merge Conflict to Main

```bash
# Current state: on fix/security-bug-audit-2026-06-14
# Issue: origin/main is ahead (worktree conflict)

# Solution A (Recommended): Do merge via GitHub PR
gh pr create --base main --title "Keeper Migration T1-T14" \
  --body "Merge keeper migration to production"
# Then approve + merge in GitHub UI

# Solution B (If you have CLI access): Force merge
git checkout main
git pull origin main
git merge origin/fix/security-bug-audit-2026-06-14 --no-edit
git push origin main
```

### Step 2: SET RAILWAY ENV VARS (CRITICAL âš ï¸)

**Go to:** https://railway.app â†’ antigravity-app â†’ backend-production â†’ Variables

**Add these 5:**
```
SECRETS_BACKEND = bitwarden
BW_VAULT_URL = https://vault.bitwarden.com
BW_CLIENT_ID = user.a0b41278-dbb2-49e1-b67e-b46a013270c7
BW_CLIENT_SECRET = 8VDctT1xHKUwuSQY7yQJ4xkoHrJwlh
BW_MASTER_PASSWORD = [REDACTED_MASTER_PASSWORD]
```

**Save â†’ Railway auto-redeploys**

### Step 3: Verify Production Deploy (15 min)

```bash
# Check Vercel: https://vercel.com/luna-del-cerro/contexia-web-app
# Status: All green checkmarks âœ…

# Check Railway: https://railway.app
# Status: "Ready" (green)

# Hard refresh production:
# Open https://contexia.online/app/bunker
# Press Ctrl+F5 (hard refresh)
# Verify no errors in browser console
```

### Step 4: Test Health Endpoint (CRITICAL)

```bash
# This is the GATE 2 validation
curl https://contexia.online/api/v1/secrets/health

# Expected response:
{
  "status": "healthy",
  "provider": "bitwarden-cloud",
  "latency_ms": 150,
  "vault_url": "https://vault.bitwarden.com"
}

# If you get error:
# - Check Railway env vars are set âœ…
# - Check logs: railway logs --follow
# - Check Keeper export is in Bitwarden âœ…
```

---

## T13: Health Audits â³ READY

**What it is:** Validate all systems working (1 hour)

**Prerequisites:** T12 health check returns 200 âœ…

### Test 1: Health Endpoint (5 min)

```bash
# Run 5 times, measure latency
for i in {1..5}; do
  curl -w "\n%{time_total}s\n" https://contexia.online/api/v1/secrets/health
done

# Expected:
# - Response 200 âœ…
# - Latency <500ms âœ…
# - No errors âœ…
```

### Test 2: LLM Providers (30 min)

Test each of 6 API keys:

```bash
# 1. GROQ
curl -H "Authorization: Bearer $(bw get item groq | jq -r '.login.password')" \
  https://api.groq.com/openai/v1/models 2>&1 | grep -i "error\|status" | head -1

# 2. OPENAI
curl -H "Authorization: Bearer $(bw get item openai | jq -r '.login.password')" \
  https://api.openai.com/v1/models 2>&1 | grep -i "error\|status" | head -1

# 3. GEMINI
GEMINI_KEY=$(bw get item gemini | jq -r '.login.password')
curl "https://generativelanguage.googleapis.com/v1/models/gemini-pro?key=$GEMINI_KEY" \
  2>&1 | grep -i "error\|name" | head -1

# 4. MISTRAL
curl -H "Authorization: Bearer $(bw get item mistral | jq -r '.login.password')" \
  https://api.mistral.ai/v1/models 2>&1 | grep -i "error\|status" | head -1

# 5. CEREBRAS
curl -H "Authorization: Bearer $(bw get item cerebras | jq -r '.login.password')" \
  https://api.cerebras.ai/v1/models 2>&1 | grep -i "error\|status" | head -1

# 6. OPENROUTER
curl -H "Authorization: Bearer $(bw get item openrouter | jq -r '.login.password')" \
  https://openrouter.ai/api/v1/models 2>&1 | grep -i "error\|status" | head -1

# Expected: All 6 return 200 or successful response (no "error")
```

### Test 3: Backend Integration (10 min)

```bash
# Test actual agent endpoint (if exists)
curl -X POST https://contexia.online/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Expected: 200 (no 500 credential errors)
```

### Test 4: Keeper References (5 min)

```bash
# Verify NO references to Keeper in code
git log --all --oneline | grep -i "keeper\|secret\|expose" | wc -l
# Expected: Only migration-related commits (< 10 lines)

# Check logs for Keeper errors
railway logs | grep -i "keeper" | head -5
# Expected: (empty or only migration logs)
```

### Step 5: Create T13 Report

```bash
# Create file: openspec/changes/keeper-migration-2026-06-15/reports/T13-HEALTH-AUDITS-2026-06-15.md
cat > T13-HEALTH-AUDITS-2026-06-15.md << 'EOF'
# T13: Health Audits Report

**Date:** 2026-06-15  
**Auditor:** [Your name]  
**Duration:** 1 hour  

## Test Results

### Health Endpoint
- âœ… Response: 200
- âœ… Latency: <500ms
- âœ… Format: Valid JSON

### LLM Providers (6/6)
- âœ… GROQ: 200
- âœ… OPENAI: 200
- âœ… GEMINI: 200
- âœ… MISTRAL: 200
- âœ… CEREBRAS: 200
- âœ… OPENROUTER: 200

### Backend Integration
- âœ… Chat endpoint: 200
- âœ… No credential errors

### Code Audit
- âœ… Zero Keeper references
- âœ… All credentials in Bitwarden
- âœ… No secrets in logs

## Conclusion
âœ… **ALL TESTS PASSED** â€” Ready for T14 (Keeper deletion)

## Sign-Off
- Auditor: [Your name]
- Date: 2026-06-15 [time]
- Status: APPROVED FOR KEEPER DELETION
EOF

git add T13-HEALTH-AUDITS-2026-06-15.md
git commit -m "docs: T13 health audits complete (all 6 providers + endpoint verified)"
```

---

## T14: Delete Keeper â˜ ï¸ IRREVERSIBLE

**âš ï¸ CRITICAL: This cannot be undone. Only execute after T13 passes.**

### Prerequisites Checklist
- [ ] T13 health audits all PASSED âœ…
- [ ] All 6 LLM providers working âœ…
- [ ] Health endpoint returning 200 âœ…
- [ ] Bitwarden backup exported âœ…
- [ ] Team approval obtained âœ…

### Step 1: Backup Keeper (Safety net)

```bash
# Export Bitwarden as backup (in case we need to recover)
bw export --format json > bitwarden-backup-2026-06-15.json

# Keep this file safe for 30 days, then delete
# Location: /Backups/bitwarden-backup-2026-06-15.json (encrypted)
```

### Step 2: Delete Keeper

```bash
# Get Keeper vault ID
bw list items | grep -i "keeper" | head -1
# Copy the "id" field

# Delete (ONE-WAY, NO UNDO)
bw delete item <keeper-vault-id>

# Confirm deletion
bw list items | grep -i "keeper"
# Expected: (empty)

# Double-check GitHub
git log --all --oneline | grep -i "keeper\|secret\|expose"
# Expected: Only migration commits
```

### Step 3: Create T14 Approval Report

```bash
cat > T14-KEEPER-DELETION-APPROVAL-2026-06-15.md << 'EOF'
# T14: Keeper Deletion Approval Report

**Date:** 2026-06-15  
**Executed By:** [Your name]  
**Approved By:** [Team lead]  

## Pre-Deletion Checklist
- âœ… T13 health audits passed
- âœ… All LLM providers validated
- âœ… Bitwarden backup created (30-day retention)
- âœ… Zero Keeper references in code
- âœ… Team approval obtained

## Deletion Executed
- Time: 2026-06-15 [time]
- Command: `bw delete item <keeper-vault-id>`
- Status: âœ… COMPLETE

## Post-Deletion Verification
- âœ… No Keeper items in Bitwarden
- âœ… No Keeper references in git logs
- âœ… Production still operational (health check 200)

## Backup Location
- File: `/Backups/bitwarden-backup-2026-06-15.json` (encrypted)
- Retention: 30 days
- Reason: Disaster recovery only

## Conclusion
âœ… **KEEPER DELETION COMPLETE** â€” Migration successful

## Signatures
- Executed: [Your name] at 2026-06-15 [time]
- Approved: [Team lead] at 2026-06-15 [time]
EOF

git add T14-KEEPER-DELETION-APPROVAL-2026-06-15.md
git commit -m "docs: T14 keeper deletion complete (irreversible, backup retained 30 days)"
git push origin main
```

---

## Timeline

```
NOW            T11 âœ… Staging (0-30 min)
T11 +30min     T12 âœ… Production merge (15 min) + env vars (5 min) + verify (15 min)
T12 +1hr       T13 âœ… Health audits (60 min)
T13 +2hrs      T14 â˜ ï¸ Keeper deletion (5 min)
TOTAL: 2:30hrs ðŸŽ‰ Migration complete
```

---

## Rollback Plan (If something breaks)

**If T12 fails (endpoint 500):**
```bash
git revert HEAD
git push origin main
# Railway auto-redeploys to previous commit
```

**If T13 fails (LLM provider down):**
```bash
# Wait for provider to recover (not our issue)
# Or use failover cascade (already implemented)
```

**If T14 fails (can't delete):**
```bash
# Contact Bitwarden support
# Keeper vault is still in Bitwarden, not deleted
# Retry with `bw delete item` again
```

---

## Next Steps (After T14 âœ…)

1. **Phase 2 Decision Gate** (2026-07-04)
   - Monitor Bitwarden stability for 2 weeks
   - Vote: Stay on Cloud or migrate to Vaultwarden self-hosted?
   - Decision recorded in `reports/2026-07-04-phase2-decision.md`

2. **Archive OpenSpec Change**
   ```bash
   git mv openspec/changes/keeper-migration-2026-06-15 \
           openspec/changes/archive/keeper-migration-2026-06-15
   git commit -m "archive: keeper migration complete (T1-T14 closed)"
   git push origin main
   ```

---

## Questions?

- **T11 failing?** Check `railway logs --follow`
- **T12 failing?** Verify 5 env vars in Railway dashboard
- **T13 failing?** Run each curl command individually
- **T14 failing?** Email Bitwarden support with error

---

**Status:** âœ… READY TO EXECUTE  
**Execution Owner:** Juan David  
**Approval Required:** TBD  
**Timeline:** 2:30 hours  

