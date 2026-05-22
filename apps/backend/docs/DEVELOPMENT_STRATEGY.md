# Contexia Development Strategy: Cloud-Only LLM APIs

**Last Updated:** 2026-05-22  
**Status:** MVP - Cloud-Only (No local models)

---

## Overview

Contexia uses **OpenRouter Free API + Claude Opus** for internal development to optimize costs while maintaining quality. This is a **development-only policy**, completely invisible to clients.

**Key Principle:** Use free APIs 80% of the time, Claude Opus 20% for critical tasks. Target: **-60% development costs vs 100% Claude Code**.

---

## Decision Matrix: When to Use What

### ✅ Use OpenRouter Free API (Gratis, ~100 req/day)

**Good for:**
- Backend development (standard endpoints, algorithms)
- Frontend UI/UX work (components, styles, layout)
- Prototyping and architecture exploration
- Code generation (boilerplate, templates)
- Documentation writing (READMEs, guides, comments)
- Refactoring and cleanup
- Test writing (unit tests, integration tests)

**How to use:**
```bash
# Option 1: Via CLI (if you have OpenRouter CLI installed)
openrouter-cli --api-key $OPENROUTER_API_KEY "Your prompt here"

# Option 2: Direct API call
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/llama-2-7b-chat",
    "messages": [{"role": "user", "content": "Your prompt"}]
  }'

# Option 3: Python requests
import requests
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
    json={"model": "meta-llama/llama-2-7b-chat", "messages": [...]}
)
```

**Rate Limit Strategy:**
- ~100 requests/day without authentication
- If hitting limits: batch requests, use Claude Opus for that batch
- Monitor daily usage: `docs/llm_usage.log`

---

### ⚠️ Use Claude Opus (Pago, Fallback/Critical)

**Good for:**
- Architecture decisions (system design, critical paths)
- Fiscal/compliance critical code (DIAN, retenciones)
- Complex debugging (when OpenRouter can't solve)
- Code review of sensitive components
- Security-critical implementations
- When OpenRouter is **rate-limited for >5 minutes**
- When you need **guaranteed quality** (not "best effort")

**Policy:**
- Always start with OpenRouter Free
- If blocked/confused for >5 min → use Claude Opus (no waiting)
- Never compromise timeline on free API limits
- Log decision: "Why Claude Opus was needed" in commit message

---

## Setup

### Prerequisites

```bash
# 1. OpenRouter Free API key
export OPENROUTER_API_KEY="sk-or-v1-XXXXXXXX"  # Get from https://openrouter.ai/keys

# 2. Claude Opus API key (already in project)
export ANTHROPIC_API_KEY="sk-ant-XXXXXXXX"

# 3. Optional: OpenRouter CLI for easier integration
npm install -g @openrouter/openrouter-cli
```

### .env Configuration

```bash
# OpenRouter Free (Development)
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXX

# Claude Opus (Critical/Fallback)
CLAUDE_API_KEY=sk-ant-XXXXXXXX

# Usage tracking
LOG_LLM_CALLS=True
DEV_LLM_LOG_FILE=docs/llm_usage.log
```

---

## Cost Model

### Monthly Development Budget (Example)

```
Total dev time: ~160 hours/month

OpenRouter Free (80% of time): 128 hours
  → Cost: $0 (free tier)
  → Model: Llama 2, Mistral, or other open-source

Claude Opus (20% of time): 32 hours
  → Cost: ~$40-60/month (at $0.015/min input)
  → Model: Claude 3 Opus (best quality)

Monthly Savings: $2.000 → $800 = -60%
```

---

## Monitoring & Logging

### Track Your Usage

**File:** `docs/llm_usage.log`

Format:
```
[2026-05-22 14:30:45] OpenRouter Free - Backend endpoint - 2min
[2026-05-22 14:35:12] Claude Opus - Fiscal logic review - 8min (CRITICAL: DIAN compliance)
[2026-05-22 14:45:00] OpenRouter Free - UI component - 1min
...
```

### Weekly Review

- Check if OpenRouter rate limit is hitting (should be rare)
- Document any critical work that required Claude (why OpenRouter wasn't enough)
- Suggest optimizations if consistently needing Claude for non-critical tasks

---

## Common Workflows

### Workflow 1: New Backend Endpoint

```
1. Start with OpenRouter Free
   → "Design REST endpoint for /api/v1/transactions"
   
2. If confused/slow:
   → Switch to Claude Opus
   → "Why is this endpoint failing? Design robust version"
```

**Expected:** 80% OpenRouter Free, 20% Claude Opus max

---

### Workflow 2: Fiscal/Compliance Feature

```
1. Start with OpenRouter Free for research/design
   → "What are DIAN requirements for invoice validation?"
   
2. ALWAYS use Claude Opus for implementation
   → "Implement DIAN-compliant invoice validator"
   
3. Claude Opus for code review
   → "Code review: Does this handle all DIAN edge cases?"
```

**Expected:** 30% OpenRouter Free (research), 70% Claude Opus (implementation)

---

### Workflow 3: Bug Hunt

```
1. Start with OpenRouter Free
   → "Why is pulso_analysis returning null?"
   
2. If OpenRouter can't debug after 5min:
   → Switch to Claude Opus
   → "Deep debug: trace through transaction flow"
```

**Expected:** 50% OpenRouter Free (initial analysis), 50% Claude Opus (if complex)

---

## Fallback Policy (When to Escalate)

| Situation | Action | Timeout |
|-----------|--------|---------|
| OpenRouter rate-limited | Use Claude Opus | Immediate |
| OpenRouter response too generic/unhelpful | Use Claude Opus | 5 minutes |
| Fiscal/compliance task | Use Claude Opus | N/A (always) |
| Complex debugging | Use Claude Opus | 5 minutes |
| Architecture decision | Use Claude Opus | N/A (always) |
| Prototype/POC | Use OpenRouter Free | No limit |

**Golden Rule:** Never wait >5 minutes on free API. Escalate to Claude.

---

## Integration with Backend

### LLM Models Already Configured

**Backend LLMEngine uses:**
- Tier 1 (FAQ, social): OpenRouter Free ✅
- Tier 2 (Pulso, Centinela): OpenRouter Free ✅
- Tier 3 (Fiscal, Compliance): Groq ✅

**Development uses same APIs:**
- OpenRouter Free: Backend dev, prototyping
- Claude Opus: Critical/fiscal tasks
- Groq: Only for critical backend tasks (already configured)

---

## FAQs

**Q: Can I use OpenRouter Free for everything?**  
A: No. Fiscal/compliance requires Claude Opus. Use OpenRouter for non-critical only.

**Q: What if OpenRouter hits rate limit?**  
A: Use Claude Opus immediately. No waiting. Log the decision.

**Q: How do I measure success?**  
A: Track `docs/llm_usage.log`. Target: 80% OpenRouter, 20% Claude Opus. If >40% Claude, something's wrong—optimize requests.

**Q: Can I share OpenRouter API key?**  
A: Yes, it's a team dev API. Never commit to git. Use `.env`.

**Q: What if code needs private processing?**  
A: Use Claude Opus (encrypted, no retention). Never send private code to OpenRouter Free.

---

## Next Steps

1. **Week 1:** Set up OpenRouter API key, test with simple request
2. **Week 2:** Use OpenRouter for 80% of development, log usage
3. **Week 3:** Review logs, optimize if Claude >40%
4. **Week 4+:** Maintain 80/20 split, measure monthly savings

**Target outcome:** -60% development costs by end of month.

