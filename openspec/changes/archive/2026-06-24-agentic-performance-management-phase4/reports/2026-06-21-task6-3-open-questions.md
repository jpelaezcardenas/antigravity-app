# Task 6.3 — Open Questions Resolution Checklist
**Date:** 2026-06-21  
**Scope:** design.md Open Questions requiring Dirección approval before Phase 4 archive  
**Status:** Awaiting Dirección confirmation

---

## Open Questions Status

### ✅ Question 1: Siigo Sandbox Credentials

**Original Question:**  
"Siigo sandbox credentials: confirmed available, or do we need to request them before Slice 2 starts?"

**Resolution:**  
✅ **RESOLVED (2026-06-21)**  
Status: Not yet available  
Action Taken: Slice 2 proceeds with manual XML ingestion only (`POST /api/v1/shadow-gl/dian-xml/ingest`); Siigo journal mirror sync and live DIAN webhook deferred to external-connection phase  
Impact: Zero; Slice 1-5 production deployment unaffected  
Document: design.md, line 81

---

### ❓ Question 2: Named Entidad A for Client Zero Approvals

**Original Question:**  
"Who is the named Entidad A for Cliente Cero approvals during testing (whose email goes in `approved_by`)?"

**Status:** ⏳ **PENDING DIRECCIÓN CONFIRMATION**

**Context:**  
- `approved_by` field in `approval_queue` table stores the email/ID of the approver (human who approved a draft)
- For testing purposes (Slices 1-5), one named Entidad A needs to be designated
- Entidad A is the entity legally/operationally authorized to approve Contexia SAS tax/financial corrections before they are written back to Siigo

**Options:**
1. Use a test email (e.g., `approver@contexia.test`)
2. Use an actual Dirección email (e.g., `direccion@contexia.local`)
3. Create a dedicated approval user in Supabase Auth

**Recommendation:**  
Option 2 (actual Dirección email) — maintains traceability for all Phase 4 testing; can be changed post-launch without schema/code changes

**Action Required:**  
**TO:** Dirección  
**REQUEST:** Designate a named Entidad A email address for Phase 4 testing approvals  
**DEADLINE:** Before Stage 11 verification (can be updated in environment variables/config if needed)

**Blocking:** No (tests use mock approver internally; real email only needed for production traceability)

---

### ❓ Question 3: Telegram Bot Token

**Original Question:**  
"Telegram bot token (`@contexia_bot`) — already provisioned, or part of Slice 4 setup?"

**Status:** ⏳ **PENDING VERIFICATION**

**Context:**  
- Slice 4 (Taty Intent Router) includes a Telegram webhook endpoint for intent routing
- The webhook URL is `/api/v1/agents/taty/telegram-webhook`
- Telegram's bot token is required to register this webhook with Telegram's API

**Current State:**  
- Endpoint implemented and tested in Slice 4
- Token assumed to be available in environment variables
- No explicit provisioning step documented in tasks.md

**Action Required:**  
**TO:** DevOps / Dirección  
**REQUEST:** Confirm Telegram bot token is available or provision `@contexia_bot` in Telegram BotFather  
**ENV VAR:** `TELEGRAM_BOT_TOKEN` (expected location in Railway environment)  
**DEADLINE:** Before Stage 11 production deployment verification  
**BLOCKING:** Stage 11 verification cannot confirm "Telegram bot responds in production" without this token

---

### ⚠️ Question 4: Supabase Advisor Findings (Security Remediation)

**Original Question:**  
"Should the Supabase advisor findings (RLS gaps, `set_hermes_tunnel` callable by anon) be opened as a separate, immediate security change before or in parallel with Slice 1?"

**Resolution:**  
✅ **DECIDED (design.md, line 84)**  
**Status:** Recommended parallel, not blocking  
**Action:** Flagged to Dirección separately as a distinct security remediation (out of Phase 4 scope)

**Details:**  
- Pre-existing RLS-disabled tables, SECURITY DEFINER views/functions callable by `anon`, permissive `USING (true)` policies are real vulnerabilities
- These are NOT regressions introduced by Phase 4
- Phase 4 does NOT introduce new vulnerabilities (all new tables use RLS + proper policies per Slice 1-2)
- Recommended: Open as a separate security ticket with Dirección; target a parallel security hardening sprint

**Action Required:**  
**TO:** Security / DevSecOps  
**STATUS:** Ensure separate security ticket exists (e.g., "Supabase RLS Policy Remediation")  
**BLOCKING:** No (not Phase 4 scope, pre-existing)

---

## Summary: Dirección Approval Required

| Item | Status | Owner | Deadline |
|------|--------|-------|----------|
| Siigo Sandbox Credentials | ✅ RESOLVED (defer) | — | — |
| Entidad A Email Address | ⏳ **PENDING** | Dirección | Before Stage 11 |
| Telegram Bot Token | ⏳ **PENDING** | DevOps / Dirección | Before Stage 11 |
| Supabase Advisor Findings | ✅ DECIDED (separate ticket) | Security / DevSecOps | Parallel, not blocking |

---

## Task 6.3 Completion Criteria

Task 6.3 is **ready for sign-off** once:

- [ ] Dirección confirms Entidad A email for approval testing
- [ ] DevOps/Dirección confirms Telegram bot token is available (or provisioned)
- [ ] Security confirms separate RLS remediation ticket is open

**Current Status:** Awaiting responses on items 1-2 above. Item 3 is already resolved (separate ticket track).

---

## Next Steps

1. **Action:** Send this checklist to Dirección with 24-hour confirm SLA
2. **Action:** Verify Telegram token availability in Railway production environment
3. **If confirmed:** Mark Task 6.3 COMPLETE and proceed to Task 6.4 (Archive)
4. **If unconfirmed:** Stage 11 verification will note "CONDITIONAL: pending Dirección confirmation"

---

Signed: Claude Code (Haiku 4.5) | 2026-06-21
