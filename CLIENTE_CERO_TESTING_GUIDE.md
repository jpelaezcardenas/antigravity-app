# 🧪 MVP Testing Guide — Cliente Cero (Contexia)

**Start Date:** 2026-06-26  
**Status:** Ready for real-world testing  
**Duration:** 1-2 weeks  
**Objective:** Validate Shadow GL with real Siigo data

---

## Getting Started

### 1. Access the MVP

**Production URL:** https://antigravity-app-production-dc78.up.railway.app

**What you'll see:**
- Login with your Supabase credentials
- PWA dashboard for Contexia's financial data
- Option to upload Siigo CSVs

### 2. Prepare Test Data

**What you need:**
- Siigo journal export (CSV format)
- Recent transactions (ideally last 30 days)
- Mix of transaction types (invoices, transfers, etc.)

**Where to export from Siigo:**
1. Login to Siigo
2. Reports → Journal/Accounting Journal
3. Date range: Last 30 days
4. Format: CSV/Excel
5. Download

---

## Testing Scenarios

### ✅ **Scenario 1: CSV Upload (Happy Path)**

**Goal:** Verify CSV import works end-to-end

**Steps:**
1. Go to https://antigravity-app-production-dc78.up.railway.app/app
2. Navigate to "Upload CSV" (or shadow-gl/siigo-csv/upload)
3. Select your Siigo CSV file
4. System validates + imports
5. See confirmation message

**Expected:**
- ✅ File uploads without errors
- ✅ Shows row count + date range
- ✅ "Success rate: 100%" if all rows import
- ✅ Transactions appear in erp_journal_entries

**Document:**
- Screenshot of upload success
- Row count imported
- Any warnings/errors (even if minor)

---

### ✅ **Scenario 2: Auto-Approval (Recurring Transactions)**

**Goal:** Verify auto-approval rules reduce manual work

**Steps:**
1. After CSV import, check Hermes Workspace (localhost:3000)
2. Look at Conductor kanban board
3. Scroll to "completed" column
4. Count entries in "completed" (these were auto-approved)

**Expected:**
- ✅ 40-60% of entries auto-approved (depending on your data)
- ✅ Mostly recurring transactions (same vendor, same amount)
- ✅ Confidence score 0.95 (95% confidence)

**Document:**
- Count of auto-approved entries
- Example of a recurring transaction that was auto-approved
- Did it match your expectation?

---

### ✅ **Scenario 3: Manual Review (Uncertain Entries)**

**Goal:** Verify manual approval workflow works

**Steps:**
1. In Hermes Workspace, look for entries in "ready" column
2. These are entries that DIDN'T auto-approve (uncertain)
3. Click one entry to see details
4. Read the rejection reason (why it wasn't auto-approved)
5. Click "Approve" or "Reject"
6. Entry moves to "completed" or "rejected"

**Expected:**
- ✅ At least 1-2 uncertain entries in queue
- ✅ Can see reason for uncertainty
- ✅ Can manually approve/reject
- ✅ Entry persists to database

**Document:**
- Screenshot of uncertain entry
- Reason it was rejected (auto-approval)
- Your decision (approve/reject + why)

---

### ✅ **Scenario 4: Data Validation (Error Handling)**

**Goal:** Verify system rejects bad data safely

**Steps:**
1. Create a malformed CSV (intentional error):
   - Missing required column
   - Invalid date format (e.g., "2026/06/25" instead of "2026-06-25")
   - Imbalanced transaction (debit ≠ credit)
2. Try to upload
3. System should reject with error message

**Expected:**
- ✅ System rejects file
- ✅ Shows clear error message (not technical jargon)
- ✅ Suggests how to fix it
- ✅ No data persists from failed upload

**Document:**
- Screenshot of error message
- Was it clear what went wrong?
- Could you understand how to fix it?

---

### ✅ **Scenario 5: Re-Upload Idempotency**

**Goal:** Verify system doesn't duplicate entries

**Steps:**
1. Upload the same CSV twice
2. Check row counts both times
3. Query database: `SELECT COUNT(*) FROM erp_journal_entries WHERE external_reference_id = 'XXX'`

**Expected:**
- ✅ Second upload succeeds
- ✅ Same row count both times
- ✅ NO duplicate entries in database
- ✅ System skips already-imported transactions

**Document:**
- Row count from first upload
- Row count from second upload
- Confirm they match

---

## Performance Tests (Optional)

### Load Time
```
Start timer → navigate to /app → page fully loaded
Expected: < 2 seconds
Document: Actual load time
```

### CSV Processing Speed
```
Start timer → upload CSV → completion message
Expected: < 5 seconds for typical Siigo export (100-500 rows)
Document: File size + processing time
```

### API Response Time (Developer Tools)
```
Network tab → POST /api/v1/shadow-gl/siigo-csv/upload
Expected: < 500ms response
Document: Screenshot of response time
```

---

## Reporting Issues

### If Something Breaks

**Option 1: Quick Fix (< 5 min)**
- Message Claude directly
- "CSV upload fails with error XYZ"
- I'll investigate + deploy fix

**Option 2: Detailed Report**
- File issue: Create `TESTING_ISSUES.md` in repo
- Include:
  - What you did
  - What happened
  - What you expected
  - Screenshot (if applicable)
  - Error message (full text)

**Example:**
```markdown
## Issue: CSV upload returns 500 error

### Steps to reproduce:
1. Navigate to upload page
2. Select Siigo CSV (20 rows)
3. Click "Upload"

### Expected:
System accepts file and shows success message

### Actual:
500 Internal Server Error: "Connection timeout"

### Screenshot:
[attach screenshot]

### Error message:
```
Error: ECONNREFUSED - cannot connect to database
```
```

---

## Success Criteria (When to Stop Testing)

### ✅ Phase passes testing when:
- ✅ Can upload real Siigo CSV without errors
- ✅ Auto-approval works (40-60% of entries)
- ✅ Can manually approve/reject uncertain entries
- ✅ Data persists correctly in database
- ✅ No data lost or duplicated on re-upload
- ✅ Error handling is clear + actionable
- ✅ Performance is acceptable (< 5 sec per upload)

### ⚠️ Known Limitations (expected):
- Vendor whitelist is empty (no "known vendor" approvals yet)
- Micro transaction threshold is fixed (not customizable)
- No metrics dashboard (Phase 9)
- Limited error logging (basic prod logs only)

---

## Timeline

| Week | Activity |
|------|----------|
| **This week (Jun 26-30)** | Contexia tests all 5 scenarios |
| **Next week (Jul 1-5)** | Feedback review + iterations |
| **Week after (Jul 8+)** | Phase 9 kickoff (dashboards) |

---

## Support

**During testing:**
- I'm available for bugs/blockers
- Quick-fix deployment within 1 hour
- Async updates via GitHub issues

**What I need from you:**
- Clear issue reports (steps to reproduce)
- Screenshots when unclear
- Feedback on UX (approval workflow, error messages)

---

## Checklist for Contexia

- [ ] Account created in production app
- [ ] Can login successfully
- [ ] Have Siigo CSV ready for testing
- [ ] Hermes Workspace running locally (port 3000)
- [ ] Read this guide completely
- [ ] Start with Scenario 1 (happy path)
- [ ] Progress through Scenarios 2-5
- [ ] Document findings
- [ ] Report issues (or confirm all working)

---

## Questions Before You Start?

- How to export Siigo CSV? → See "Prepare Test Data" above
- Can't see Hermes Workspace? → Run `pnpm dev` in hermes-workspace folder
- Getting login error? → Check your Supabase credentials
- CSV upload hangs? → Check browser console for errors (F12)

---

## Let's Go! 🚀

You're ready to test. Start with Scenario 1, document what you find, and let me know what happens.

Good luck! 🎯
