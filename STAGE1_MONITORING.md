# Stage 1: 24-Hour Staging Monitoring

**Start Time:** [FILL IN: YYYY-MM-DD HH:MM UTC]  
**End Time:** [FILL IN: 24h later]  
**Status:** 🔴 IN PROGRESS

---

## Hourly Metrics Checklist

Monitor estas 24 veces (cada hora) durante Stage 1.

### Template por Hora:

```
=== HOUR [N] ===
Time: [HH:MM UTC]

LATENCY (P95 < 5s):
- Check logs for slowest requests
- grep "response_time" logs/llm_usage.log | tail -100 | sort -t: -k2 -nr | head -10
Expected: All <5 seconds

ERROR RATE (< 0.1%):
- Total errors in last hour: [N]
- Total requests in last hour: [N] 
- Error rate: [N]%
- Expected: <10 errors/1000 requests

FAILOVER RATE (< 5%):
- OpenRouter Free requests: [N]
- Groq fallback requests: [N]
- Failover %: [N]%
- Expected: <50 fallbacks per 1000 requests

COST (track spending):
- OpenRouter Free calls: [N] (cost: $0)
- Groq calls: [N] (cost: ~$0.20 per call)
- Hour cost estimate: $[X]

ERRORS/ISSUES:
- Any client complaints: [YES/NO]
- Any API errors: [YES/NO]
- Notes: [...]

✓ HOUR [N] PASS / ✗ HOUR [N] FAIL
```

---

## Monitoring Commands

### 1. Watch logs in real-time
```bash
cd apps/backend
tail -f logs/llm_usage.log
```

### 2. Check error rate (every hour)
```bash
# Count errors in last hour
grep "ERROR\|FAIL" logs/llm_usage.log | tail -100 | wc -l

# Count total requests in last hour
grep "OPENROUTER_FREE\|GROQ" logs/llm_usage.log | tail -1000 | wc -l

# Calculate: errors / requests × 100 = error %
```

### 3. Check failover rate
```bash
# Count OpenRouter Free requests
grep "OPENROUTER_FREE" logs/llm_usage.log | tail -1000 | wc -l

# Count Groq requests (fallback)
grep "GROQ" logs/llm_usage.log | tail -1000 | wc -l

# Calculate: groq_count / (openrouter_count + groq_count) = failover %
```

### 4. Check latency (P95)
```bash
# Extract response times and sort
grep "response_time\|latency" logs/llm_usage.log | tail -100 | sort -t: -k2 -nr | head -5
# Top 5 slowest = P95+ latency
# Expected: all <5 seconds
```

### 5. Cost tracking
```bash
# Count provider usage
echo "=== Cost Estimate ==="
echo "OpenRouter Free: $(grep OPENROUTER_FREE logs/llm_usage.log | wc -l) calls × $0 = $0"
echo "Groq: $(grep 'GROQ' logs/llm_usage.log | wc -l) calls × $0.20 = $(echo "$(grep GROQ logs/llm_usage.log | wc -l) * 0.20" | bc) USD"
```

---

## Success Criteria (All must pass)

| Metric | Target | Status | Hour Range |
|--------|--------|--------|------------|
| Latency P95 | <5s | ⏳ | H1-H24 |
| Error rate | <0.1% | ⏳ | H1-H24 |
| Failover rate | <5% | ⏳ | H1-H24 |
| Cost trend | $0 + Groq only | ⏳ | H1-H24 |
| Client complaints | 0 | ⏳ | H1-H24 |
| Uptime | 99.9%+ | ⏳ | H1-H24 |

---

## Hour-by-Hour Log

### Hour 1
- **Time:** [TIME]
- **Latency P95:** [VALUE]
- **Error rate:** [VALUE]%
- **Failover rate:** [VALUE]%
- **Cost estimate:** $[VALUE]
- **Issues:** [NONE / LIST]
- **Status:** ✓ PASS / ✗ FAIL

### Hour 2
- **Time:** [TIME]
- **Latency P95:** [VALUE]
- **Error rate:** [VALUE]%
- **Failover rate:** [VALUE]%
- **Cost estimate:** $[VALUE]
- **Issues:** [NONE / LIST]
- **Status:** ✓ PASS / ✗ FAIL

[... repeat for Hours 3-24 ...]

---

## Daily Summary (After 24 hours)

### Metrics Summary
- **Avg Latency P95:** [VALUE] seconds
- **Avg Error rate:** [VALUE]%
- **Avg Failover rate:** [VALUE]%
- **Total cost:** $[VALUE]
- **Client complaints:** [N]
- **Uptime:** [VALUE]%

### Issues Encountered
1. [Issue 1]: [Resolution]
2. [Issue 2]: [Resolution]
3. [Issue 3]: [Resolution]

### Recommendation
- ✓ **PROCEED to Stage 2** (Client test with Sion/Lavaderos LD)
- ✗ **HOLD** (Investigate issues before proceeding)
- ✗ **ROLLBACK** (Revert to previous architecture)

**Signed off by:** [NAME]  
**Date:** [DATE]

---

## Troubleshooting During Monitoring

### High Latency (P95 > 5s)?
1. Check if OpenRouter Free is rate-limited
2. Verify network connection
3. Check if Groq is slow (rare)
4. **Action:** Investigate root cause, document in logs

### High Error Rate (> 0.1%)?
1. Check API key validity
2. Verify Groq/OpenRouter status page
3. Check if rate limits hit
4. **Action:** Switch Tier 2 to Groq if OpenRouter issues persist

### High Failover Rate (> 5%)?
1. OpenRouter Free hitting rate limits
2. **Action:** Expected if >100 req/day; Groq handles overflow
3. Monitor daily - should stabilize

### Cost Higher Than Expected?
1. If Groq calls >> OpenRouter calls: failover is working correctly
2. Cost is still <$1.50/day (vs $3000+ before)
3. **Action:** No action needed, cost still far below baseline

---

## Next Steps After 24h

If ✓ **ALL METRICS PASS:**
1. Compile summary above ✓
2. Notify team: "Staging monitoring complete, ready for client test"
3. **Proceed to Stage 2:** Client staging test with Sion or Lavaderos LD (48h)

If ✗ **ANY METRIC FAILS:**
1. Investigate root cause
2. Document in "Issues Encountered" section
3. Fix issue (5-30 min typically)
4. **Restart monitoring** from Hour 1

If ✗ **CRITICAL FAILURE (>1% error rate or >50% failover):**
1. Check if Groq or OpenRouter are down
2. Review error logs for API key issues
3. If API keys expired: revoke & generate new ones
4. **Rollback procedure:** See DEPLOYMENT_GUIDE.md § Rollback Plan

---

**Questions?** See DEPLOYMENT_GUIDE.md or STAGING_SETUP.md
