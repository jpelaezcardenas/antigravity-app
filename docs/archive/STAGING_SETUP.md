# Staging Deployment Setup (Cloud-Only)

**Date:** 2026-05-22  
**Status:** Ready for API key configuration  
**Branch:** `claude/angry-sutherland-976d5d` → merge to `main` after staging validation

---

## Prerequisites

✓ Code: Cloud-Only LLM architecture implemented  
✓ Tests: 7/7 passing  
✓ Docs: Complete (CLOUD_ONLY_MIGRATION.md, DEVELOPMENT_STRATEGY.md, DEPLOYMENT_GUIDE.md)  
⏳ **PENDING:** API keys configuration

---

## Step 1: Configure API Keys (5 minutes)

### 1.1 Get Your API Keys

**OpenRouter Free** (REQUIRED - for Tier 1 & 2):
- Go to https://openrouter.ai/keys
- Generate a new API key
- Key format: `sk-or-v1-XXXXXXXX`
- Rate limit: ~100 requests/day (free, no auth required but faster with key)

**Groq** (REQUIRED - for Tier 3 critical tasks):
- Go to https://console.groq.com
- Create API key in "API Keys" section
- Key format: `gsk_XXXXXXXX`
- No rate limit for development tier

**Claude** (OPTIONAL - for fallback & development):
- Go to https://console.anthropic.com
- Create API key
- Key format: `sk-ant-XXXXXXXX`

### 1.2 Update `.env` File

Edit `apps/backend/.env` and fill in your keys:

```bash
# OpenRouter Free (REQUIRED)
OPENROUTER_API_KEY=sk-or-v1-[YOUR_KEY_HERE]

# Groq (REQUIRED)
GROQ_API_KEY=gsk_[YOUR_KEY_HERE]

# Claude (Optional)
CLAUDE_API_KEY=sk-ant-[YOUR_KEY_HERE]
```

**IMPORTANT:** Never commit `.env` to git (already in `.gitignore`)

---

## Step 2: Verify Configuration (2 minutes)

```bash
# Run verification script
python scripts/verify_cloud_only_setup.py

# Expected output:
# [PASS] No Ollama References
# [PASS] API Keys Configured
# [PASS] Model Selector Routing
# [PASS] Failover Chain Order
# [PASS] API Endpoints
# 
# [OK] ALL CHECKS PASSED - Cloud-Only setup is complete!
```

If any checks fail, see Troubleshooting section below.

---

## Step 3: Start Backend (Staging)

```bash
# Option A: Direct Python (for testing)
cd apps/backend
python main.py

# Option B: Via Railway deployment (recommended for staging)
# (Use your deployment tool commands here)

# Backend should start on http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

---

## Step 4: Run Smoke Tests (Staging)

### 4.1 Health Check

```bash
curl http://localhost:8000/docs
# Should return Swagger UI (200 OK)
```

### 4.2 Test Tier 1 (Non-sensitive)

```bash
curl -X POST http://localhost:8000/api/v1/agents/taty/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Renta?", "company_id": "test-123"}'

# Should return: 200 OK with FAQ response
```

### 4.3 Test Tier 2 (Financial)

```bash
curl -X POST http://localhost:8000/api/v1/agents/pulso/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"income": 5000, "expenses": 2000}, "company_id": "test-123"}'

# Should return: 200 OK with analysis
```

### 4.4 Test Tier 3 (Critical)

```bash
curl -X POST http://localhost:8000/api/v1/agents/centinela/decide \
  -H "Content-Type: application/json" \
  -d '{"data": {"renta": 10000000}, "company_id": "test-123"}'

# Should return: 200 OK with decision (uses Groq)
```

---

## Step 5: 24-Hour Monitoring (Staging)

Monitor these metrics for 24 hours:

```bash
# Watch logs in real-time
tail -f logs/llm_usage.log

# Check for errors
grep ERROR logs/llm_usage.log | wc -l
# Expected: <10 errors/day out of ~5000 requests

# Check failover rate
grep GROQ logs/llm_usage.log | wc -l
# Expected: <5% (OpenRouter Free handles 95%+)

# Monitor latency (P95 should be <5 seconds)
# Check logs for response times
```

---

## Troubleshooting

### Issue: `verify_cloud_only_setup.py` fails on API keys

**Cause:** API keys not configured in `.env`  
**Solution:**
1. Copy `.env.example` as template: `cp apps/backend/.env.example apps/backend/.env`
2. Fill in your actual API keys
3. Re-run verification script

### Issue: OpenRouter Free rate-limited (>50% failover)

**Cause:** Too many concurrent requests hitting rate limit  
**Mitigation:**
- Automatic fallback to Groq (paid) handles overflow
- Log the event for monitoring
- Expected behavior: recovers within hours

**Action if persistent:**
- Batch similar requests
- Reduce concurrent API calls
- Monitor daily usage in logs/llm_usage.log

### Issue: Groq API key returns 401 Unauthorized

**Cause:** Invalid API key  
**Solution:**
1. Verify key format: `gsk_XXXXXXXX`
2. Regenerate key at https://console.groq.com
3. Restart backend after updating `.env`

### Issue: Backend won't start

**Cause:** Missing dependencies  
**Solution:**
```bash
cd apps/backend
pip install -r requirements.txt
python main.py
```

---

## Next Steps

After 24-hour staging monitoring ✓:

1. **Approve staging results** (check success criteria in DEPLOYMENT_GUIDE.md)
2. **Test with real client** (Stage 2: Sion or Lavaderos LD)
3. **Production deployment** (Stage 3: after client validation)

See `DEPLOYMENT_GUIDE.md` for complete 3-stage plan.

---

## Quick Reference

| Component | Status | Location |
|-----------|--------|----------|
| Code | ✅ Complete | `apps/backend/` |
| Tests | ✅ 7/7 Passing | `apps/backend/tests/test_model_selector_cloud_only.py` |
| Config Template | ✅ Ready | `apps/backend/.env.example` |
| Verify Script | ✅ Ready | `scripts/verify_cloud_only_setup.py` |
| API Keys | ⏳ Needs Setup | `apps/backend/.env` |
| Staging Deployment | ⏳ Awaiting Keys | See Step 3+ above |

---

**Questions?** See DEPLOYMENT_GUIDE.md FAQ section.
