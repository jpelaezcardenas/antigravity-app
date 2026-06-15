# Quick Reference — OpenSpec Stage 11

**Print this. Keep it visible.**

---

## The Gap

```
❌ OpenSpec archive ≠ production
✅ OpenSpec archive + Stage 11 = production ✓
```

---

## Stage 11 in 5 Steps

1. **git commit + push** → `main`
2. **Vercel/Railway builds** → Wait for green ✅
3. **Hard refresh production** → Ctrl+F5 or Cmd+Shift+R
4. **Verify changes live** → Check URL
5. **Create report** → `openspec/changes/[ID]/reports/YYYY-MM-DD-deployment.md`

---

## Before Each Stage 11

| Check | Frontend | Backend |
|-------|----------|---------|
| Code ready? | ✅ Tests pass | ✅ Tests pass |
| No secrets? | ✅ .env not committed | ✅ .env not committed |
| Branch correct? | ✅ main | ✅ main |

---

## During Deployment

| Platform | Dashboard | Status |
|----------|-----------|--------|
| Frontend (Vercel) | https://vercel.com/contexia | ✅ Ready |
| Backend (Railway) | https://railway.app | ✅ Active |
| DB (Supabase) | https://supabase.com | ✅ Migrations OK |

---

## After Deployment

```bash
# Verify
curl https://[production-url]/[endpoint]
# OR open in browser with hard refresh

# Create report (in openspec/changes/[ID]/reports/)
# Include: commit hash, Vercel/Railway URL, screenshots before/after
```

---

## If Something Breaks

```bash
# 1. Identify last good commit
git log --oneline -5

# 2. Revert
git revert [hash-of-breaking-commit]

# 3. Push
git push origin main

# 4. Wait for Vercel/Railway to redeploy
# 5. Verify production is back to normal
```

---

## Key Files

| File | When |
|------|------|
| `DEPLOYMENT_STAGE.md` | Full workflow (read once) |
| `checklist-vercel.md` | If UI change |
| `checklist-railway.md` | If API/DB change |
| `CHECKPOINTS.md` | Objective criteria to pass |

---

## Checklist (Paste in tasks.md)

```markdown
## Stage 11. Deploy to Production

- [ ] 11.1 Commit + push to main
- [ ] 11.2 Vercel/Railway build: ✅ READY
- [ ] 11.3 Production URL: changes visible
- [ ] 11.4 No console errors (F12)
- [ ] 11.5 Report created + pushed
```

---

## Production URLs

| Project | URL |
|---------|-----|
| Antigravity | https://contexia.online/app/bunker |
| Backend | https://antigravity-app-production-175a.up.railway.app |
| Dashboards | https://vercel.com/contexia + https://railway.app |

---

## Red Flags ⚠️

- ❌ "Archive without Stage 11"
- ❌ "Change is 'done' but not live"
- ❌ "Forgot to hard refresh"
- ❌ "Env vars in git commits"
- ❌ "Vercel/Railway shows error, pushing anyway"

---

## Green Lights ✅

- ✅ Commit message includes change ID
- ✅ Vercel/Railway shows build success
- ✅ Hard refresh shows changes
- ✅ No errors in console (F12)
- ✅ Report created with screenshots
- ✅ Ready to archive

---

**Print & Tape to Monitor**  
**Updated:** 2026-05-30
