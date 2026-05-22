# Staging Deployment - Setup Checklist

## API Key Configuration

### Step 1: Get OpenRouter Free Key
- [ ] Visit https://openrouter.ai/keys
- [ ] Create new API key
- [ ] Copy key (format: `sk-or-v1-...`)

### Step 2: Get Groq Key
- [ ] Visit https://console.groq.com
- [ ] Navigate to API Keys section
- [ ] Create new API key
- [ ] Copy key (format: `gsk_...`)

### Step 3: Update `.env`
- [ ] Open `apps/backend/.env`
- [ ] Replace `OPENROUTER_API_KEY=sk-or-v1-XXXXXXXX` with your actual key
- [ ] Replace `GROQ_API_KEY=gsk_XXXXXXXX` with your actual key
- [ ] Save file (never commit .env to git - already in .gitignore)

### Step 4: Verify Configuration
```bash
python scripts/verify_cloud_only_setup.py
```
- [ ] All 5 checks show `[PASS]`
- [ ] "ALL CHECKS PASSED" message appears

### Step 5: Start Backend
```bash
cd apps/backend
python main.py
```
- [ ] Backend starts on `http://localhost:8000`
- [ ] No errors in console

### Step 6: Quick Health Check
```bash
curl http://localhost:8000/docs
```
- [ ] Returns Swagger UI (200 OK)

### Step 7: Run Smoke Tests
Execute the 3 test commands in STAGING_SETUP.md:
- [ ] Tier 1 test passes (taty/ask)
- [ ] Tier 2 test passes (pulso/analyze)
- [ ] Tier 3 test passes (centinela/decide)

---

**When you've completed all steps above, let me know "ready for monitoring" and I'll set up the 24-hour monitoring for Stage 1.**
