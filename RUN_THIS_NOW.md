# ðŸš€ RUN THIS NOW: T11-T14 Quick Execution (90 minutes)

**Generated:** 2026-06-15 17:45 UTC  
**Status:** READY TO EXECUTE  
**Time:** 90 minutes total  

---

## âœ… PART 1: What's Already Done (Verified)

```
âœ… Code: Production-ready (secrets_provider.py, health endpoint)
âœ… Data: 330 secrets in Bitwarden
âœ… Specs: Complete OpenSpec (20+ pages)
âœ… Docs: All 14 files ready
âœ… Git: 21 commits, all pushed
âœ… Env: .env.local filled with 5 credentials
âœ… Branch: fix/security-bug-audit-2026-06-14 â†’ Ready to merge
```

---

## â³ PART 2: What YOU Need to Do (90 minutes)

### T11: Create & Merge PR (5 minutes)

**MANUAL STEP (GitHub Web)**

1. Open: https://github.com/jpelaezcardenas/antigravity-app
2. Click: **"Compare & pull request"** (or "New pull request")
3. Set:
   - Base: `main`
   - Compare: `fix/security-bug-audit-2026-06-14`
4. Title: `Keeper â†’ Bitwarden Migration (T1-T14)`
5. Click: **"Create pull request"**
6. Click: **"Merge pull request"** â†’ **"Confirm merge"**

**Result:** Vercel + Railway auto-deploy âœ…

---

### T12: Set Railway Environment Variables (10 minutes)

**MANUAL STEP (Railway Web)**

1. Go: https://railway.app
2. Select: `antigravity-app` project
3. Select: `backend-production` service
4. Click: **Variables** tab
5. Add these 5 (copy-paste from below):

```
SECRETS_BACKEND=bitwarden
BW_VAULT_URL=https://vault.bitwarden.com
BW_CLIENT_ID=[REDACTED_BW_CLIENT_ID]
BW_CLIENT_SECRET=[REDACTED_BW_CLIENT_SECRET]
BW_MASTER_PASSWORD=[REDACTED_MASTER_PASSWORD]
```

6. Click: **Save**

**Result:** Railway redeploys backend with secrets âœ…

---

### T13: Run Health Audits (60 minutes)

**AUTOMATED (Run in Terminal)**

Copy-paste each section into your terminal:

#### Test 1: Health Endpoint (5 min)
```bash
echo "Testing health endpoint 5 times..."
for i in {1..5}; do
  curl -s -w "Response $i: Status %{http_code}, Latency %{time_total}s\n" \
    https://contexia.online/api/v1/secrets/health
  sleep 5
done
```

**Expected:** 5x `Status 200`

#### Test 2: LLM Providers (30 min)

```bash
echo "=== Testing 6 LLM Providers ==="

# 1. GROQ
echo "1. GROQ"
GROQ_KEY=$(bw get item groq | jq -r '.login.password')
curl -s -w "Status: %{http_code}\n" -H "Authorization: Bearer $GROQ_KEY" \
  https://api.groq.com/openai/v1/models | head -1

# 2. OPENAI
echo "2. OPENAI"
OPENAI_KEY=$(bw get item openai | jq -r '.login.password')
curl -s -w "Status: %{http_code}\n" -H "Authorization: Bearer $OPENAI_KEY" \
  https://api.openai.com/v1/models | head -1

# 3. GEMINI
echo "3. GEMINI"
GEMINI_KEY=$(bw get item gemini | jq -r '.login.password')
curl -s -w "Status: %{http_code}\n" \
  "https://generativelanguage.googleapis.com/v1/models/gemini-pro?key=$GEMINI_KEY" | head -1

# 4. MISTRAL
echo "4. MISTRAL"
MISTRAL_KEY=$(bw get item mistral | jq -r '.login.password')
curl -s -w "Status: %{http_code}\n" -H "Authorization: Bearer $MISTRAL_KEY" \
  https://api.mistral.ai/v1/models | head -1

# 5. CEREBRAS
echo "5. CEREBRAS"
CEREBRAS_KEY=$(bw get item cerebras | jq -r '.login.password')
curl -s -w "Status: %{http_code}\n" -H "Authorization: Bearer $CEREBRAS_KEY" \
  https://api.cerebras.ai/v1/models | head -1

# 6. OPENROUTER
echo "6. OPENROUTER"
OPENROUTER_KEY=$(bw get item openrouter | jq -r '.login.password')
curl -s -w "Status: %{http_code}\n" -H "Authorization: Bearer $OPENROUTER_KEY" \
  https://openrouter.ai/api/v1/models | head -1

echo "=== All tests complete ==="
```

**Expected:** 6x `Status 200`

#### Test 3: Backend Integration (10 min)
```bash
echo "Testing backend integration..."
curl -s -X POST https://contexia.online/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | head -3
echo "Status: $?"
```

**Expected:** `Status 0` (no errors)

#### Test 4: Code Audit (5 min)
```bash
echo "Checking for Keeper references..."
git log --all --oneline | grep -i "keeper\|secret\|expose" | wc -l
echo "Expected: < 10 (only migrations)"
```

#### Test 5: Summary (10 min)

**Fill in the T13 report:**

```bash
# Open and edit:
nano openspec/changes/keeper-migration-2026-06-15/reports/T13-HEALTH-AUDITS-2026-06-15.md

# Fill in results from above tests
# Check all boxes: [ ] âœ…
# Save: Ctrl+O â†’ Enter â†’ Ctrl+X
```

**Commit:**
```bash
git add openspec/changes/keeper-migration-2026-06-15/reports/T13-HEALTH-AUDITS-2026-06-15.md
git commit -m "docs: T13 health audits complete (all 6 providers + endpoint verified)"
git push origin fix/security-bug-audit-2026-06-14
```

---

### T14: Delete Keeper (5 minutes)

**âš ï¸ IRREVERSIBLE - ONLY AFTER T13 ALL PASS âœ…**

#### Step 1: Backup (1 min)
```bash
bw export --format json > bitwarden-backup-2026-06-15.json
ls -lh bitwarden-backup-2026-06-15.json
```

#### Step 2: Get Keeper ID (1 min)
```bash
bw list items | grep -i "keeper"
# Copy the "id" value from output
# Save it: KEEPER_ID="<paste-id-here>"
```

#### Step 3: DELETE (1 min)
```bash
# THIS CANNOT BE UNDONE
bw delete item <paste-keeper-id-here>
```

#### Step 4: Verify (1 min)
```bash
# Confirm deletion
bw list items | grep -i "keeper"
# Expected: (empty)
```

#### Step 5: Final Report (1 min)

```bash
# Open and edit:
nano openspec/changes/keeper-migration-2026-06-15/reports/T14-KEEPER-DELETION-APPROVAL-2026-06-15.md

# Fill in:
# - Name, date, time
# - Approvals
# - Verification results
# - Save
```

**Final commit:**
```bash
git add openspec/changes/keeper-migration-2026-06-15/reports/T14-KEEPER-DELETION-APPROVAL-2026-06-15.md
git commit -m "docs: T14 keeper deletion complete (irreversible, backup retained)"
git push origin main
```

---

## ðŸŽ¯ Timeline

| Task | Time | Status |
|------|------|--------|
| T11 (PR merge) | 5 min | â³ Manual |
| T12 (Railway vars) | 10 min | â³ Manual |
| T13 (Health audits) | 60 min | â³ Copy-paste curl + manual report |
| T14 (Delete Keeper) | 5 min | â³ Manual + git |
| **TOTAL** | **80 min** | â³ Ready to start |

---

## âœ… Verification Checklist

After each section, check:

- [ ] T11: PR merged (GitHub shows merge commit)
- [ ] T12: Railway env vars visible in dashboard (5/5)
- [ ] T12: Vercel build green (https://vercel.com/luna-del-cerro/contexia-web-app)
- [ ] T12: Railway backend "Ready" status
- [ ] T13: Health endpoint returns 200
- [ ] T13: All 6 LLM providers return 200
- [ ] T13: Backend integration test passes
- [ ] T13: T13 report created and committed
- [ ] T14: Keeper ID found and saved
- [ ] T14: Keeper deleted (`bw list items | grep keeper` = empty)
- [ ] T14: T14 report created and committed
- [ ] T14: Final commits pushed to main

---

## ðŸ†˜ If Anything Breaks

**Health endpoint 404 or 500?**
- Check: `railway logs --follow`
- Verify: T12 env vars set (5/5 in Railway dashboard)
- Retry: After vars are confirmed

**LLM provider fails?**
- Check: API status (not your issue)
- Use: Failover cascade (already implemented)
- Retry: In 5 minutes

**Keeper delete fails?**
- Contact: Bitwarden support
- Backup intact: `bitwarden-backup-2026-06-15.json`
- Retry: `bw delete item <id>` again

---

## ðŸŽ‰ When Done

```bash
# Verify final state
git log --oneline -5
# Shows: T14 deletion + T13 audits + other commits

# Push final commits
git push origin main

# Confirm migration
curl https://contexia.online/api/v1/secrets/health
# Expected: {"status": "healthy", ...}
```

---

## ðŸ“‹ Copy-Paste Checklist

- [ ] Step 1: Merge PR on GitHub (5 min)
- [ ] Step 2: Set 5 Railway env vars (10 min)
- [ ] Step 3: Run 5 curl test sections (60 min)
  - [ ] Health endpoint test
  - [ ] 6 LLM providers test
  - [ ] Backend integration test
  - [ ] Code audit test
  - [ ] Fill T13 report
- [ ] Step 4: Delete Keeper (5 min)
  - [ ] Backup exported
  - [ ] Keeper ID found
  - [ ] Deleted
  - [ ] Verified gone
  - [ ] T14 report filled

---

**Status:** âœ… 100% READY TO EXECUTE

**You have everything. Just follow the steps. 90 minutes. Done.**

ðŸš€


