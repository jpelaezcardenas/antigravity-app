# Before & After: API Endpoint Fixes

## Summary of All Changes

### ❌ Problem: 422 Unprocessable Entity Errors

FastAPI didn't know where to find POST parameters, causing validation failures.

### ✅ Solution: Added Pydantic Models + Query Annotations

Now all parameters have explicit sources (request body or query string).

---

## Individual Endpoint Fixes

### 1. POST /pulso/today (Pulso Diario)

**BEFORE (Broken):**
```python
@router.post("/pulso/today", response_model=Dict)
async def get_pulso_today(company_id: str):  # ❌ Where is company_id?
    service = PulsoDiariaService()
    kpis = service.calculate_daily_kpis(company_id)
    return {"status": "success", "company_id": company_id, "kpis": kpis}
```

**AFTER (Fixed):**
```python
class PulsoDiariosRequest(BaseModel):
    company_id: str

@router.post("/pulso/today", response_model=Dict)
async def get_pulso_today(request: PulsoDiariosRequest):  # ✅ Pydantic model
    service = PulsoDiariaService()
    kpis = service.calculate_daily_kpis(request.company_id)
    return {"status": "success", "company_id": request.company_id, "kpis": kpis}
```

**Usage - BEFORE:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/pulso/today
# → 422 Unprocessable Entity
```

**Usage - AFTER:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/pulso/today \
  -H "Content-Type: application/json" \
  -d '{"company_id": "31676930-b476-472b-bced-fd25f973cf8a"}'
# → 200 OK with KPI data
```

---

### 2. GET /pulso/latest (Pulso Latest Snapshot)

**BEFORE (Ambiguous):**
```python
@router.get("/pulso/latest", response_model=Dict)
async def get_pulso_latest(company_id: str):  # ❌ Not clear this is a query param
    snapshot = service.get_latest_snapshot(company_id)
```

**AFTER (Explicit):**
```python
@router.get("/pulso/latest", response_model=Dict)
async def get_pulso_latest(company_id: str = Query(..., description="Company ID")):
    snapshot = service.get_latest_snapshot(company_id)
```

**Usage - BEFORE:**
```bash
curl http://localhost:8000/api/v1/agents/pulso/latest
# → Missing required parameter
```

**Usage - AFTER:**
```bash
curl http://localhost:8000/api/v1/agents/pulso/latest?company_id=31676930-b476-472b-bced-fd25f973cf8a
# → 200 OK with snapshot
```

---

### 3. POST /centinela/check-risks (Risk Assessment)

**BEFORE (Broken):**
```python
@router.post("/centinela/check-risks", response_model=Dict)
async def check_centinela_risks(company_id: str):  # ❌ 422 error
    result = service.check_all_risks(company_id)
    return {"status": "success", "data": result}
```

**AFTER (Fixed):**
```python
class CentinelaCheckRequest(BaseModel):
    company_id: str

@router.post("/centinela/check-risks", response_model=Dict)
async def check_centinela_risks(request: CentinelaCheckRequest):  # ✅ Fixed
    result = service.check_all_risks(request.company_id)
    return {"status": "success", "data": result}
```

**Usage:**
```bash
# BEFORE: 422 error
curl -X POST http://localhost:8000/api/v1/agents/centinela/check-risks

# AFTER: Works!
curl -X POST http://localhost:8000/api/v1/agents/centinela/check-risks \
  -H "Content-Type: application/json" \
  -d '{"company_id": "31676930-b476-472b-bced-fd25f973cf8a"}'
```

---

### 4. POST /taty/ask (Q&A Assistant)

**BEFORE (Broken):**
```python
@router.post("/taty/ask", response_model=Dict)
async def taty_ask_question(
    company_id: str,      # ❌ Where do these come from?
    question: str,        # ❌ Ambiguous
    language: str = "es"  # ❌ 422 error
):
    answer = service.answer_question(company_id, question, language)
    return answer
```

**AFTER (Fixed):**
```python
class TatyQuestionRequest(BaseModel):
    company_id: str
    question: str
    language: str = "es"

@router.post("/taty/ask", response_model=Dict)
async def taty_ask_question(request: TatyQuestionRequest):  # ✅ Clear structure
    answer = service.answer_question(request.company_id, request.question, request.language)
    return answer
```

**Usage:**
```bash
# BEFORE: 422 Unprocessable Entity
curl -X POST http://localhost:8000/api/v1/agents/taty/ask \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "...",
    "question": "...",
    "language": "es"
  }'

# AFTER: 200 OK
curl -X POST http://localhost:8000/api/v1/agents/taty/ask \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "31676930-b476-472b-bced-fd25f973cf8a",
    "question": "¿Cuál es la fecha de vencimiento para la declaración de renta 2025?",
    "language": "es"
  }'
```

---

### 5. GET /taty/history (Conversation History)

**BEFORE (Unclear):**
```python
@router.get("/taty/history", response_model=Dict)
async def get_taty_history(company_id: str, limit: int = 10):
    # ❌ Not clear these are query params
```

**AFTER (Explicit):**
```python
@router.get("/taty/history", response_model=Dict)
async def get_taty_history(
    company_id: str = Query(..., description="Company ID"),
    limit: int = Query(10, ge=1, le=100)
):
    # ✅ Clear these are query parameters
```

**Usage:**
```bash
curl "http://localhost:8000/api/v1/agents/taty/history?company_id=31676930-b476-472b-bced-fd25f973cf8a&limit=5"
```

---

### 6. POST /orchestrator/full-pipeline (7-Agent Pipeline)

**BEFORE (Broken):**
```python
@router.post("/orchestrator/full-pipeline", response_model=Dict)
async def execute_full_pipeline(
    company_url: str,           # ❌ 422 error
    campaign_objective: str,    # ❌ Multiple params
    budget: float = 5000,       # ❌ Ambiguous source
    target_channels: Optional[list] = None,  # ❌ Not clear
    execute_distribution: bool = False
):
    # Body of function
```

**AFTER (Fixed):**
```python
class FullPipelineRequest(BaseModel):
    company_url: str
    campaign_objective: str
    budget: float = 5000
    target_channels: Optional[list] = None
    execute_distribution: bool = False

@router.post("/orchestrator/full-pipeline", response_model=Dict)
async def execute_full_pipeline(request: FullPipelineRequest):  # ✅ Single model
    # Use request.company_url, request.campaign_objective, etc.
```

**Usage:**
```bash
# BEFORE: 400 Bad Request
curl -X POST http://localhost:8000/api/v1/agents/orchestrator/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "...",
    "campaign_objective": "..."
  }'

# AFTER: 200 OK with all 7 agents executed
curl -X POST http://localhost:8000/api/v1/agents/orchestrator/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://contexia.online",
    "campaign_objective": "Lead generation para auditoría sombra",
    "budget": 5000,
    "target_channels": ["instagram", "linkedin"],
    "execute_distribution": false
  }'
```

---

### 7. POST /onboarding/analyze (Onboarding Agent)

**BEFORE:**
```python
@router.post("/onboarding/analyze", response_model=Dict)
async def analyze_company(company_url: str, company_data: Optional[Dict] = None):
    # ❌ 422 error - Dict parameter not clear
```

**AFTER:**
```python
class OnboardingAnalyzeRequest(BaseModel):
    company_url: str
    company_data: Optional[Dict] = None

@router.post("/onboarding/analyze", response_model=Dict)
async def analyze_company(request: OnboardingAnalyzeRequest):
    # ✅ Fixed
```

---

### 8. POST /planner/generate-options (Planner Agent)

**BEFORE:**
```python
@router.post("/planner/generate-options", response_model=Dict)
async def generate_campaign_options(
    campaign_objective: str,
    tax_dna: Dict,  # ❌ 422 error
    budget: float = 5000,
    timeline_weeks: int = 4
):
```

**AFTER:**
```python
class PlannerGenerateRequest(BaseModel):
    campaign_objective: str
    tax_dna: Dict
    budget: float = 5000
    timeline_weeks: int = 4

@router.post("/planner/generate-options", response_model=Dict)
async def generate_campaign_options(request: PlannerGenerateRequest):
```

---

### 9. POST /generator/create-content (Generator Agent)

**BEFORE:**
```python
@router.post("/generator/create-content", response_model=Dict)
async def generate_content_variations(
    campaign: Dict,       # ❌ 422 error
    tax_dna: Dict,       # ❌ Complex type
    channel: str = "instagram",
    variations_count: int = 3
):
```

**AFTER:**
```python
class GeneratorCreateRequest(BaseModel):
    campaign: Dict
    tax_dna: Dict
    channel: str = "instagram"
    variations_count: int = 3

@router.post("/generator/create-content", response_model=Dict)
async def generate_content_variations(request: GeneratorCreateRequest):
```

---

### 10. POST /repurposer/transform (Repurposer Agent)

**BEFORE:**
```python
@router.post("/repurposer/transform", response_model=Dict)
async def repurpose_content(
    source_content: str,
    source_type: str = "article",
    target_formats: Optional[list] = None  # ❌ 422 error
):
```

**AFTER:**
```python
class RepurposerTransformRequest(BaseModel):
    source_content: str
    source_type: str = "article"
    target_formats: Optional[List[str]] = None

@router.post("/repurposer/transform", response_model=Dict)
async def repurpose_content(request: RepurposerTransformRequest):
```

---

## Summary Table

| Endpoint | Type | Before Status | Fix Applied | After Status |
|----------|------|---------------|-------------|--------------|
| `/pulso/today` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/pulso/latest` | GET | Ambiguous | Query() annotation | ✅ 200 OK |
| `/centinela/check-risks` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/centinela/alerts` | GET | Ambiguous | Query() annotation | ✅ 200 OK |
| `/taty/ask` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/taty/history` | GET | Ambiguous | Query() annotation | ✅ 200 OK |
| `/taty/faq` | GET | Ambiguous | Query() annotation | ✅ 200 OK |
| `/onboarding/analyze` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/planner/generate-options` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/generator/create-content` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/repurposer/transform` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/analyst/analyze-metrics` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/distribution/schedule-publishing` | POST | 422 Error | Pydantic model | ✅ 200 OK |
| `/orchestrator/full-pipeline` | POST | 400 Error | Pydantic model | ✅ 200 OK |
| `/orchestrator/full-pipeline-with-persistence` | POST | 422 Error | Pydantic model | ✅ 200 OK |

---

## How FastAPI Parameter Resolution Works

FastAPI determines where a parameter comes from based on:

1. **Path parameters** (in route): `@router.get("/users/{user_id}")`
   - `user_id` automatically extracted from URL path

2. **Query parameters** (URL query string): `?company_id=xxx`
   - Must be marked: `company_id: str = Query(...)`
   - GET requests use this by default (unless in path)

3. **Request body** (JSON POST data):
   - Must be a Pydantic model class: `request: MyRequest`
   - POST/PUT requests use this by default

4. **Special parameters**: `Header()`, `Body()`, `Form()`, etc.

---

## Key Takeaway

**All POST endpoints now use Pydantic request models** → FastAPI knows parameters come from the JSON request body, not from paths or query strings.

**All GET endpoints with query parameters now use Query() annotations** → FastAPI knows these parameters come from the URL query string.

No more ambiguity = No more 422 errors! ✅
