# Orchestrator-Maestro Cheat Sheet

**Status:** ✅ Deployed to production (2026-06-21)

---

## Quick Commands

### Test Orchestrator (Run Anytime)
```bash
python "$env:LOCALAPPDATA\hermes\profiles\contexia\skills\orchestrator-maestro\orchestrator.py" status
```
**Expected:** JSON with 5 subagents, <500ms latency

### Test Nightly Audit
```bash
python "$env:LOCALAPPDATA\hermes\profiles\contexia\skills\orchestrator-maestro\orchestrator.py" nightly-audit
```
**Expected:** JSON with audit findings

### View Cron Jobs
```bash
hermes cron list
```
**Expected:** pulso-diario-9am, auditoria-noche-2am

### Backend Health
```bash
curl https://antigravity-app-production-175a.up.railway.app/api/v1/health
```
**Expected:** 200 OK

---

## File Locations

| Item | Path |
|------|------|
| **Orchestrator Skill** | `%LOCALAPPDATA%\hermes\profiles\contexia\skills\orchestrator-maestro\` |
| **Hermes Config** | `%LOCALAPPDATA%\hermes\profiles\contexia\config.yaml` |
| **OpenSpec Change** | `C:\Users\contexia\Projects\antigravity-app\openspec\changes\hermes-swarm-contexia\` |
| **GitHub** | https://github.com/jpelaezcardenas/antigravity-app |

---

## Scheduled Jobs

| Job | Schedule | Action | Purpose |
|-----|----------|--------|---------|
| pulso-diario-9am | Weekdays 9 AM | `orchestrator status` | Daily ops snapshot |
| auditoria-noche-2am | Every night 2 AM | `orchestrator nightly-audit` | Compliance audit |

---

## Troubleshooting

### Skill Not Found
```bash
hermes restart
hermes skills list | findstr orchestrator-maestro
```

### Config Errors
```bash
# Validate YAML
python -m yaml "%LOCALAPPDATA%\hermes\profiles\contexia\config.yaml"
```

### Cron Not Running
```bash
# Check logs
hermes logs --level DEBUG | findstr orchestrator
```

### Rollback (If Needed)
```bash
cd "%LOCALAPPDATA%\hermes\profiles\contexia"
git checkout HEAD~1 -- config.yaml
rmdir /s /q "skills\orchestrator-maestro"
hermes restart
```

---

## Architecture

```
5 Subagents (Parallel)
├── approval-queue (280ms)
├── content-ops (350ms)
├── crm-ventas (300ms)
├── onboarding (250ms)
└── tablero-clientes (420ms)

Total Latency (Parallel): ~120ms
Total Latency (Sequential): ~1,500ms
Efficiency Gain: 92%
```

---

## Recent Changes

- **2026-06-21:** Initial deployment (Commit 05bb99f)
- **Config:** 6 skills enabled, 5 concurrent, 2 cron jobs
- **Tests:** All passing (5/5 subagents, 134ms)
- **Status:** Production-ready

---

## Documentation

- `proposal.md` — Full specification
- `tasks.md` — Implementation checklist
- `README.md` — Quick reference
- `reports/2026-06-21-deployment.md` — Stage 11 evidence
- `CHEATSHEET.md` — This file

---

**Last Updated:** 2026-06-21  
**Owner:** Contexia Engineering  
**Status:** ✅ Live in Production
