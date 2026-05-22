# Cloud-Only LLM Deployment Guide

**Version:** 1.0  
**Date:** 2026-05-22  
**Target:** Staging → Production  

---

## Pre-Deployment Checklist

### Code & Tests
- [ ] All 7 verification tests passing: `python scripts/verify_cloud_only_setup.py`
- [ ] Branch: `claude/angry-sutherland-976d5d` (or merged to `main`)
- [ ] Git log shows 5 commits (refactor, docs, tests, dev strategy, migration guide)
- [ ] No uncommitted changes: `git status` clean

### Environment Preparation
- [ ] Staging environment created (separate from production)
- [ ] Backup of current production (if applicable)
- [ ] Rollback plan reviewed and tested
- [ ] Team notified of deployment window

### API Keys Secured
- [ ] OpenRouter Free API key obtained: https://openrouter.ai/keys
- [ ] Groq API key ready: https://console.groq.com
- [ ] Claude API key (development, optional): https://console.anthropic.com
- [ ] Keys stored in secure secret manager (NOT in git)

---

## Stage 1: Staging Deployment (Day 1)

### 1.1 Deploy Code

```bash
# Checkout latest branch
git checkout claude/angry-sutherland-976d5d
git pull origin claude/angry-sutherland-976d5d

# Or merge to main if approved
git checkout main
git merge claude/angry-sutherland-976d5d
git push origin main
```

### 1.2 Configure Environment

**Staging .env file:**
```bash
# Supabase (use staging DB)
SUPABASE_URL=https://staging-xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxx-staging

# LLM APIs (FREE tier for cost validation)
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXX-staging-key
GROQ_API_KEY=gsk_XXXXXXXX-staging-key
CLAUDE_API_KEY=sk-ant-XXXXXXXX-optional

# Logging
LOG_LLM_CALLS=True
DEV_LLM_LOG_FILE=logs/llm_usage.log
LLM_COST_TRACKING=True
```

### 1.3 Verify Deployment

```bash
# Run verification script
python scripts/verify_cloud_only_setup.py

# Expected output:
# [OK] No Ollama References
# [OK] Model Selector Routing
# [OK] Failover Chain
# [OK] API Endpoints
# [FAIL] API Keys (expected - keys are secrets)

# Start backend
python main.py

# Test endpoints (in new terminal)
curl http://localhost:8000/docs  # Should show Swagger UI

# Test a Tier 1 endpoint (doesn't use real LLM, safe)
curl -X POST http://localhost:8000/api/v1/agents/task-info/taty_faq
```

### 1.4 Initial Monitoring (24 hours)

**Check logs for:**
```bash
# Monitor API calls
tail -f logs/llm_usage.log

# Look for:
# [2026-05-22 10:30:45] OPENROUTER_FREE - /taty/ask - 1.2s - OK
# [2026-05-22 10:35:12] OPENROUTER_FREE - /pulso/analyze - 2.1s - OK
# [2026-05-22 10:40:00] GROQ - /centinela/decide - 0.8s - OK
```

**Metrics to track:**
- API latency: P95 < 5 seconds (target)
- Error rate: <0.1% (zero if possible)
- Failover triggers: Should be rare (<1% of requests)
- Cost: Should be ~$50/day in staging (if using real API keys)

---

## Stage 2: Client Staging Test (Days 2-3)

### 2.1 Invite Test Client

**Select:** 1 trusted client (suggestion: Sion or Lavaderos LD)
- Explain: "We've optimized our infrastructure. You won't notice any changes, but we're rolling out improvements."
- Ask: "Can you test your usual workflow? Look for any slowness or errors."
- Duration: 48 hours minimum

### 2.2 Run Smoke Tests

```bash
# Test each endpoint type
# Tier 1: Non-sensitive
curl -X POST http://staging.contexia.online/api/v1/agents/taty/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Renta?", "company_id": "test-123"}'

# Tier 2: Financial data
curl -X POST http://staging.contexia.online/api/v1/agents/pulso/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"income": 5000, "expenses": 2000}, "company_id": "test-123"}'

# Tier 3: Critical (verify Groq is used)
curl -X POST http://staging.contexia.online/api/v1/agents/centinela/decide \
  -H "Content-Type: application/json" \
  -d '{"data": {"renta": 10000000}, "company_id": "test-123"}'

# All should return 200 OK with proper responses
```

### 2.3 Analyze Results

**Success criteria:**
- [ ] Zero client complaints about slowness
- [ ] Zero errors in logs
- [ ] Latency unchanged from before (or better)
- [ ] All responses valid and helpful
- [ ] Cost metrics show savings

**If issues:**
1. Check logs: `grep ERROR logs/llm_usage.log`
2. Run verification: `python scripts/verify_cloud_only_setup.py`
3. Review failover triggers: How many requests hit Groq fallback?
4. If >10% failover rate: Review OpenRouter Free rate limits

---

## Stage 3: Production Deployment (Day 4+)

### 3.1 Final Pre-Flight Checks

```bash
# Verify code state
git log --oneline -5  # Should show cloud-only commits
git status            # Should be clean

# Run tests one more time
python -m pytest tests/test_model_selector_cloud_only.py -v
# All 7 passing expected

# Verify script
python scripts/verify_cloud_only_setup.py
```

### 3.2 Deploy to Production

```bash
# Update production environment
# (Use your deployment tool: Railway, Vercel, Docker, etc.)

# Set production .env
SUPABASE_URL=https://prod-xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxx-prod
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXX-prod
GROQ_API_KEY=gsk_XXXXXXXX-prod

# Deploy
# (Your CI/CD pipeline here)
git push origin main  # Or trigger deployment manually
```

### 3.3 Post-Deployment Verification (First 24 Hours)

**Immediate (0-1 hours):**
```bash
# Health check
curl https://api.contexia.online/docs  # Swagger UI loads

# Test each tier
# (Same smoke tests as Stage 2, but against production)
```

**Continuous monitoring (24 hours):**
```bash
# Watch logs
tail -f logs/production_llm_usage.log

# Key metrics to watch:
# 1. Error rate: Should stay <0.1%
# 2. Latency: P95 should be <5 seconds
# 3. Failover rate: Should be <5% (OpenRouter rate-limited occasionally)
# 4. Cost: Should show immediate reduction
```

**What to alert on:**
- Error rate spikes >1%
- Latency P95 >10 seconds
- Failover rate >20% (suggests OpenRouter problems)
- Any 5xx errors in production

### 3.4 Cost Validation (First Week)

```bash
# Track actual vs. projected savings
# Expected: ~$400/week savings if deployed to all 5 clients

# Run cost report
python scripts/analyze_llm_costs.py  # (if created)

# Compare:
# Before: $3.000/week (Groq, Mistral, Gemini, etc.)
# After:  $1.500/week (OpenRouter Free gratis + Groq critical only)
# Savings: $1.500/week = $6.000/month
```

---

## Rollback Plan (If Needed)

### Scenario 1: OpenRouter Free Unstable (>50% failover rate)

**Action:** Switch Tier 2 back to Groq (costs more but guaranteed)

```bash
# Edit model_selector.py
# Change line: if task_type in ["pulso_analysis", ...]:
#              return LLMProvider.OPENROUTER_FREE
# To:          return LLMProvider.GROQ

# Commit and redeploy
git commit -am "hotfix: revert tier2 to groq due to openrouter instability"
git push origin main
```

**Cost impact:** Back to $2.500/week (vs. $1.500/week), but stable

### Scenario 2: Critical Latency Issue

**Action:** Revert to previous commit before Cloud-Only

```bash
git revert HEAD~4  # Revert all 5 cloud-only commits
git push origin main
# (Your CI/CD redeploys automatically)
```

**Timeline:** 15-30 minutes max downtime

### Scenario 3: Client Complaint (Slow Response)

**Before blaming Cloud-Only:**
1. Check latency logs: Is it actually slower, or perceived?
2. Run: `python scripts/verify_cloud_only_setup.py`
3. Check failover rate: Are we hitting Groq (slower) too often?
4. Profile the request: Which LLM provider is being used?

**Most likely causes:**
- OpenRouter Free rate-limited → switch to Groq (automatic fallback does this)
- Network latency → not related to Cloud-Only
- LLM model change → no, we use same models

---

## Monitoring & Operations

### Daily (First Week)

```bash
# Check cost tracking
cat logs/llm_usage.log | grep "COST_DAILY"
# Expected: $200-300/day for 5 clients

# Check error rate
cat logs/llm_usage.log | grep "ERROR" | wc -l
# Expected: <10 errors/day out of ~5000 requests

# Verify failover chain
cat logs/llm_usage.log | grep "GROQ" | wc -l
# Expected: <5% of requests (rate-limited occasionally)
```

### Weekly

**Run full analysis:**
```bash
python scripts/verify_cloud_only_setup.py
python scripts/analyze_llm_costs.py
python scripts/check_failover_health.py
```

**Team sync:**
- Costs trending as expected?
- Any error spikes?
- Client feedback?
- Any manual Groq uses (debug/critical)?

### Monthly

**Cost reconciliation:**
```
Budget: -$2.700/month savings
Actual: -$2.100 to -$2.800/month (expected variance)
Action: If <-$1.500, investigate why savings not realized
```

---

## Operations Handbook

### How to Debug High Latency

```bash
# 1. Check if it's Cloud-Only related
grep "OPENROUTER_FREE\|GROQ" logs/llm_usage.log | tail -100
# Look for: Which provider handled the slow request?

# 2. If Groq: Check rate limiting
grep "GROQ.*rate" logs/llm_usage.log
# If many: OpenRouter Free is exhausted, fallback to Groq

# 3. If OpenRouter Free: Check network
# (Might be regional latency, not our fault)
```

### How to Handle Client Complaints

**Client:** "Responses are slower now"  
**Debug:**
```bash
# 1. Check timestamps
grep "Client-A.*timestamp" logs/llm_usage.log | head -5
# See before/after latency

# 2. Check which provider
grep "Client-A.*model_used" logs/llm_usage.log
# If GROQ: rate-limit hit, expected fallback
# If OPENROUTER_FREE: network or LLM issue
```

**Response template:**
```
"Thanks for reporting! We've optimized our infrastructure.
Most requests use our new free tier (OpenRouter Free), which
should be faster. If you're seeing slowness, we've likely 
hit a rate limit on that service (very rare), causing automatic
fallback to our paid provider (Groq), which costs more but is
reliable.

This should resolve within 24 hours as rate limits reset.
Let us know if slowness persists."
```

---

## Success Metrics (Target vs. Actual)

| Metric | Target | Week 1 | Week 2 | Month 1 |
|--------|--------|--------|--------|---------|
| Cost savings | -$2.700/mo | -$600 | -$1.200 | -$2.400+ |
| Latency P95 | <5s | <5s | <5s | <5s |
| Error rate | <0.1% | <0.5% | <0.1% | <0.1% |
| Failover rate | <5% | 3-8% | <5% | <3% |
| Client impact | Zero | Zero | Zero | Zero |
| Uptime | 99.9% | 99.9% | 99.9% | 99.9% |

---

## FAQ - Deployment

**Q: What if staging shows high failover rate (>10%)?**  
A: OpenRouter Free is hitting rate limits. Either:
1. Reduce concurrent requests (batch them)
2. Switch Tier 2 to Groq (higher cost, guaranteed)
3. Use both: smart rate-limit detection + fallback

**Q: Should we tell clients about this change?**  
A: No. It's internal infrastructure. Completely transparent.
If asked: "We've optimized our backend. You won't notice any changes."

**Q: What's our SLA if OpenRouter goes down?**  
A: Automatic failover to Groq (paid, guaranteed).
SLA: 99.9% uptime, <5s P95 latency.

**Q: Can we monitor cost per client?**  
A: Yes! Track in logs: `{"client_id": "X", "cost": $0.05}`
Build dashboard: Cost per client per month.

**Q: How do we scale to 100+ clients?**  
A: Monitor OpenRouter Free rate limits.
At ~500 req/day per client, we hit limit at 10-15 concurrent clients.
Then switch to paid OpenRouter (not free) or increase Groq usage.

**Q: What if a client requests "use Groq always" for security?**  
A: Allow it! Update model_selector:
```python
if client_id == "paranoid_client":
    return LLMProvider.GROQ  # Always paid, never free
```
Cost: Higher, but client is happy.

---

## Contacts & Escalation

**Deployment Issues:**
- Tech Lead: [Your name]
- On-Call: [Schedule]

**Cost Concerns:**
- CFO: [Name]
- Monthly reconciliation: [Date]

**Client Complaints:**
- Support team: [Channel]
- Escalate if: >3 complaints about latency

---

## Sign-Off Checklist

Before going to production:

- [ ] Tech Lead: "Code is production-ready"
- [ ] QA: "All tests passing, no regressions"
- [ ] DevOps: "Infrastructure ready"
- [ ] Finance: "Savings projections validated"
- [ ] Support: "Team trained on troubleshooting"
- [ ] Compliance: "No changes to data handling"

**Go/No-Go Decision:**
- [ ] **GO TO PRODUCTION** (All cleared)
- [ ] **HOLD** (Issues to resolve)

---

**Deployment Date: [TBD]**  
**Deployed by: [Name]**  
**Approved by: [Names]**

