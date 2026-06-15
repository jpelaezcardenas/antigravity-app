# CURSOR PROMPT: Keeper → Bitwarden Migration (Phase 1)

**Copy-paste this prompt into Cursor and follow it step by step.**

---

## THE MISSION

Migrate 330+ secrets from Keeper (exposed) → Bitwarden Cloud (Phase 1: 1 week).

**Status:** T1 COMPLETE ✅ (Keeper export validated)  
**Next:** T2–T14 (follow checklist below)  
**Timeline:** 2026-06-15 to 2026-06-20  
**Constraint:** Spec-first (update OpenSpec tasks.md BEFORE coding)

---

## IMMEDIATE: T2 (Juan, 20 min)

Create Bitwarden Cloud account:

```
1. Go https://vault.bitwarden.com → Sign Up
2. Email: growth@contexia.online
3. Master password: random 32+ chars (save securely)
4. Enable 2FA: Settings → Two-Step Login → Authenticator app
5. Create organization: "Contexia", Plan "Free"
6. API Key: Settings → Organization → API Key
7. Save: BW_CLIENT_ID, BW_CLIENT_SECRET, BW_MASTER_PASSWORD
8. Git commit: "docs: T2 bitwarden cloud account created"
```

---

## THEN: T3 (Dev, 30 min)

Install & verify bw CLI:

```bash
# Install
brew install bitwarden-cli
# Or download: https://bitwarden.com/download

# Verify
bw --version

# Login (from T2 credentials)
bw login growth@contexia.online

# Sync
bw sync

# Commit
git commit -m "docs: T3 bw CLI installed and verified"
```

---

## NEXT PHASES (Follow tasks.md)

**Read these files IN THIS ORDER:**

1. `KEEPER_MIGRATION_HANDOFF.md` ← Full instructions for T2-T14
2. `openspec/changes/keeper-migration-2026-06-15/tasks.md` ← Task details
3. `openspec/changes/keeper-migration-2026-06-15/MIGRATION_DASHBOARD.md` ← Progress tracking

---

## QUICK COMMANDS

```bash
# View current task
cat openspec/changes/keeper-migration-2026-06-15/tasks.md | grep "^### T[0-9]"

# See git status
git status -sb

# Commit after task
git commit -m "feat/docs: [T#] [description]"

# Update progress (edit this file)
openspec/changes/keeper-migration-2026-06-15/MIGRATION_DASHBOARD.md
```

---

## DECISION GATES (MUST PASS)

🛑 **GATE 1 (T6):** All API keys validated (Groq, OpenAI, Gemini, Mistral, Cerebras, OpenRouter)  
🛑 **GATE 2 (T12):** Production deploy verified (health check 200, no Keeper refs)  
🛑 **GATE 3 (T14):** T13 audits passed BEFORE deleting Keeper (irreversible)

---

## IMPORTANT RULES

✅ Update `tasks.md` BEFORE coding (spec-first)  
✅ Commit after each task completion  
✅ Run T4-T6 in parallel (independent)  
✅ Follow Stage 11 checklist for T12 production deploy  

❌ Don't skip decision gates  
❌ Don't delete Keeper before T13✅  
❌ Don't leave Keeper CSV export on disk after T4 (shred it)

---

## IF YOU GET STUCK

1. Check `KEEPER_MIGRATION_HANDOFF.md` → "DEBUGGING CHECKLIST" section
2. Check `scenarios.md` → Find your issue, see mitigation
3. Message Juan (Infra Lead) or Dev Team

---

## WHEN YOU'RE DONE (Before returning to Claude)

✅ All tasks completed  
✅ All commits pushed  
✅ Update MIGRATION_DASHBOARD.md with final status  
✅ Document any issues in `reports/` folder  

Then go back to Claude (when you have credits) — everything will be ready to verify & close.

---

**Start:** T2 (Juan, right now)  
**Reference:** KEEPER_MIGRATION_HANDOFF.md  
**Questions:** See DEBUGGING CHECKLIST or contact Juan
