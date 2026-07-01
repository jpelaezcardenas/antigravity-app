# Design: Hermes Profile-Based LLM Routing

**Change ID:** `hermes-profile-based-llm-routing`  
**Status:** Design Complete (2026-06-28)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hermes Workspace (9119)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Dashboard: MODELS, PROFILES, OPERATIONS, JOBS, API Gateway│  │
│  │                                                           │  │
│  │ PROFILES: Define LLM routing per agent                   │  │
│  │  ├─ taty-v1: Groq → [OpenRouter, Cerebras]             │  │
│  │  ├─ centinela-v1: Phi → [Groq, OpenRouter]             │  │
│  │  ├─ pulso-v1: Phi → [Groq, OpenRouter]                 │  │
│  │  ├─ radar-v1: Groq → [Cerebras, OpenRouter]            │  │
│  │  ├─ auditoria-v1: Groq → [Cerebras]                    │  │
│  │  ├─ social-ops-v1: Gemma → [Groq, OpenRouter]          │  │
│  │  ├─ kb-v1: Gemma → [Groq, OpenRouter]                  │  │
│  │  └─ maestro-v1: Groq → [Cerebras, OpenRouter]          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ API Gateway (8642)                                       │  │
│  │ ├─ Receives: POST /api/v1/agents/ask                    │  │
│  │ ├─ Injects: X-Hermes-Profile header (from profile tab)  │  │
│  │ └─ Routes to: http://localhost:8000 (antigravity-app)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│            antigravity-app Backend (Railway, Port 8000)         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ presentation/router.py (Middleware)                      │  │
│  │ ├─ Extract: X-Hermes-Profile header                     │  │
│  │ └─ Pass to: Service layer (context/dependency injection)│  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ services/taty_service.py (Example)                       │  │
│  │                                                           │  │
│  │ llm_engine = get_llm_engine()                            │  │
│  │ response = llm_engine.get_ai_response_with_profile(     │  │
│  │     prompt=masked_prompt,                               │  │
│  │     profile_name="taty-v1",  # ← From header            │  │
│  │     system_prompt=...,                                  │  │
│  │     ...                                                 │  │
│  │ )                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ agents/llm_engine.py (LLM Orchestrator)                  │  │
│  │                                                           │  │
│  │ PROFILE_CONFIGS = {                                      │  │
│  │     "taty-v1": {                                         │  │
│  │         "primary": LLMProvider.GROQ,                     │  │
│  │         "fallback_chain": [GROQ, OPENROUTER, CEREBRAS]  │  │
│  │     },                                                   │  │
│  │     ...                                                 │  │
│  │ }                                                        │  │
│  │                                                           │  │
│  │ def get_ai_response_with_profile(profile_name):          │  │
│  │     profile = PROFILE_CONFIGS.get(profile_name)          │  │
│  │     return _call_with_failover_custom_order(             │  │
│  │         provider_order=profile["fallback_chain"]         │  │
│  │     )                                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Provider Failover Chain (Groq/Cerebras/etc.)            │  │
│  │ 1. Try: Groq                                             │  │
│  │ 2. Fallback: OpenRouter                                  │  │
│  │ 3. Fallback: Cerebras                                    │  │
│  │ 4. Error: AllProvidersFailedError                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Log to agent_operations (Supabase)                       │  │
│  │ ├─ profile_name: "taty-v1"                              │  │
│  │ ├─ provider_used: "groq"                                │  │
│  │ ├─ latency_ms: 1240                                     │  │
│  │ └─ cost: 0.003                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. LLM Engine Enhancements

**File:** `apps/backend/agents/llm_engine.py`

#### PROFILE_CONFIGS (New)
```python
PROFILE_CONFIGS = {
    "taty-v1": {
        "primary": LLMProvider.GROQ,
        "fallback_chain": [
            LLMProvider.GROQ,
            LLMProvider.OPENROUTER,
            LLMProvider.CEREBRAS
        ],
        "description": "Fiscal advisor — interactive <2s"
    },
    # ... 7 more profiles
}
```

#### New Method: `get_ai_response_with_profile()`
```python
def get_ai_response_with_profile(
    self,
    prompt: str,
    profile_name: str = None,
    system_prompt: str = "",
    response_format: str = "text",
    # ... standard params
) -> Union[Dict, str]:
    """
    Route LLM call via Hermes profile.
    Falls back to default task-tier if profile unknown.
    """
    if profile_name and profile_name in PROFILE_CONFIGS:
        profile = PROFILE_CONFIGS[profile_name]
        fallback_chain = profile["fallback_chain"]
        logger.info(f"Using profile '{profile_name}'")
        
        # Use custom fallback chain
        return self._call_with_failover_custom_order(
            prompt, system_prompt, max_tokens, temperature, timeout,
            provider_order=fallback_chain
        )
    else:
        # Backward compat: use default routing
        return self.get_ai_response(prompt, system_prompt, ...)
```

#### Helper Methods
- `_call_with_failover_custom_order()` — Failover with custom provider chain
- `_get_json_with_retry_custom_order()` — JSON retry with custom order

### 2. Service Integration

**Pattern (Taty example):**

```python
# BEFORE
from agents.llm_engine import get_ai_response

response = get_ai_response(
    prompt=masked_prompt,
    system_prompt=system_prompt,
    ...
)

# AFTER
from agents.llm_engine import get_llm_engine

llm_engine = get_llm_engine()
response = llm_engine.get_ai_response_with_profile(
    prompt=masked_prompt,
    profile_name="taty-v1",
    system_prompt=system_prompt,
    ...
)
```

**Services to Update:**
1. ✅ `taty_service.py` — "taty-v1"
2. ✅ `social_ops_service.py` — "social-ops-v1"
3. (Others: Centinela/Pulso/Radar are rules-based, no direct LLM calls)

### 3. Hermes Configuration

**Phase 1 (Dashboard Manual):**
1. Open Hermes Dashboard (http://localhost:9119)
2. Go to PROFILES tab
3. For each profile, set Model:
   - taty-v1 → glm-5.2
   - centinela-v1 → phi:latest
   - etc.
4. Configure API Gateway (8642):
   - Backend: http://localhost:8000
   - Header: X-Hermes-Profile (auto-injected from profile selection)

### 4. Backward Compatibility

**Guaranteed:**
- Old `get_ai_response()` still works (unchanged)
- Old services (using default routing) unaffected
- Gradual migration: service-by-service

**Test:** All unit tests pass without modification

### 5. Cost Model

| Agent | Profile | Primary | Est. Cost/Month |
|-------|---------|---------|-----------------|
| Taty | taty-v1 | Groq ($0.20/call) | $180 (30 calls/day) |
| Centinela | centinela-v1 | Phi local (free) | $0 |
| Pulso | pulso-v1 | Phi local (free) | $0 |
| Radar | radar-v1 | Groq | ~$5 |
| Auditoría | auditoria-v1 | Groq | ~$5 |
| Social Ops | social-ops-v1 | Gemma local (free) | $0 |
| KB | kb-v1 | Gemma local (free) | $0 |

**Total:** ~$190/month (vs. $337 before = **44% savings**)

---

## Data Flow

### Request Flow
```
1. Client: POST http://localhost:8642/api/v1/agents/ask
2. Hermes Gateway: Injects X-Hermes-Profile: "taty-v1"
3. antigravity-app: Receives request with header
4. Middleware: Extracts profile name
5. Service: Calls llm_engine.get_ai_response_with_profile("taty-v1")
6. LLM Engine: Selects Groq (from profile config)
7. Provider: Returns response
8. Log: agent_operations table records (profile_name, provider_used, latency, cost)
```

### Fallback Chain Activation
```
Request with profile="centinela-v1"
→ Primary: Phi local (timeout or error)
→ Fallback 1: Groq (success) ✓
→ Log: centinela-v1 via Groq fallback
```

---

## Testing Strategy

### Unit Tests (`test_profile_support.py`)
- ✅ All 8 profiles exist
- ✅ Each profile has fallback_chain
- ✅ Profile routing uses custom order
- ✅ Unknown profile falls back to default
- ✅ JSON + text formats work
- ✅ Groq in all fallback chains

### Integration Tests (Future)
- Hermes Gateway → antigravity-app routing with header
- Profile selection via Dashboard → header injection
- Cost tracking per profile

### Performance Benchmarks
- Taty P95 latency <2s (verify via monitoring)
- Centinela P95 <30s
- No regression on existing latencies

---

## Deployment Checklist (Stage 11)

- [ ] Code pushed to main
- [ ] Vercel frontend deploys (if any changes)
- [ ] Railway backend redeploys (code changes)
- [ ] Production health check: /api/v1/health
- [ ] Hermes Dashboard models configured
- [ ] API Gateway routing tested with curl
- [ ] Deployment report created
- [ ] Archive in OpenSpec

---

## Appendix: Profile Configs (Full)

All profiles hardcoded in `llm_engine.py`:

```python
PROFILE_CONFIGS = {
    "taty-v1": {...},          # Interactive (<2s)
    "centinela-v1": {...},     # Monitoring (~25s)
    "pulso-v1": {...},         # Nightly (~85s)
    "radar-v1": {...},         # Predictive (<10s)
    "auditoria-v1": {...},     # Regulatory (<30s)
    "social-ops-v1": {...},    # Content (~60s)
    "kb-v1": {...},            # RAG (~15s)
    "maestro-v1": {...},       # Orchestration (<30s)
}
```

See `llm_engine.py` for full definition.
