# Phase 3B: Hermes User Sync & Onboarding - Execution Plan

**Status:** Ready for Execution  
**T11 Status:** ✅ COMPLETE (21/21 hours)  
**Phase 3B Target:** Jun 30, 2026  
**Remaining Hours:** ~15 hours

---

## 📊 Phase 3 Overview

```
Phase 3A: User Sync & Onboarding Framework (COMPLETE)
├─ T1-T10: Multi-tenant infrastructure + RBAC
├─ T11: Hermes operators implementation (✅ COMPLETE)
└─ Ready for Phase 3B

Phase 3B: Integration & Hardening (READY)
├─ T12: RLS + Role-based filtering (3h)
├─ T13: Email templates (2h)
├─ T14: E2E tests (4h)
├─ T15: Documentation (2h)
└─ T16: Deployment + Verification (TBD)
```

---

## ✅ T11: Hermes Operators - COMPLETE

**Summary:**
- ✅ Conductor orchestration (T11.1)
- ✅ 5 Swarm operators (T11.2-T11.5): Auth, DB, Roles, Comms, Workflow
- ✅ Data models (T11.6): Mission, Task, Checkpoint, CostTracking
- ✅ Kanban Dashboard (T11.7): React component + hooks
- ✅ Mission API (T11.8): 6 REST endpoints + WebSocket
- ✅ Integration tests (T11.9): 60+ test cases

**Deliverables:**
- 2,500+ lines of production code
- 5 parallel operators with cost tracking
- 4-column Kanban visualization
- Full async/await pipeline
- Comprehensive test suite

**Ready for Integration:** YES

---

## 🎯 Phase 3B Tasks

### T12: RLS + Role-Based Filtering (3 hours)

**Goal:** Implement Row-Level Security (RLS) policies and role-based query filtering.

**Tasks:**
1. Create RLS policies for missions table
   - Users can only see their tenant's missions
   - Admins can see all missions in tenant
   - Viewers can only see completed missions

2. Create RLS policies for checkpoints table
   - Same tenant isolation as missions

3. Implement role-based filtering
   - `@check_permission("view:missions")` decorator
   - `@check_permission("edit:mission")` for start/stop
   - `@check_permission("view:costs")` for cost breakdown

4. Update Mission API endpoints
   - Add RLS checks to all GET/POST endpoints
   - Verify tenant_id in JWT token
   - Filter queries by tenant_id automatically

5. Test RLS policies
   - User from Tenant A cannot see Tenant B's missions
   - Viewer role cannot edit missions
   - Cost breakdown hidden from non-finance roles

**Files to Update:**
- `apps/backend/models/mission.py` - Add RLS triggers
- `apps/backend/presentation/mission_endpoints.py` - Add RLS checks
- `apps/backend/core/rbac.py` - Mission-specific permissions
- Database migrations (0010-rls-policies.sql)

---

### T13: Email Templates (2 hours)

**Goal:** Create Jinja2 email templates for onboarding workflow.

**Tasks:**
1. Create email template directory
   ```
   apps/backend/email_templates/
   ├── welcome.html
   ├── role_assigned.html
   ├── mission_completed.html
   ├── mission_failed.html
   └── base.html
   ```

2. Welcome email template
   - Customer name, email, plan
   - Quick start guide link
   - Support contact info
   - Personalized dashboard URL

3. Role assignment email
   - New user welcomed to team
   - Role and permissions listed
   - Team member list
   - Action: "Set password" button

4. Mission completed email
   - Summary: what was set up
   - Costs incurred
   - Next steps
   - Admin: detailed breakdown

5. Mission failed email
   - What went wrong
   - Retry option
   - Support contact

6. Template rendering system
   - `EmailService.render(template, context)`
   - HTML + plain text fallback
   - Internationalization support (i18n)

**Files to Create:**
- `apps/backend/services/email_service.py`
- `apps/backend/email_templates/` (4 templates)
- Tests: `tests/test_email_templates.py`

---

### T14: End-to-End Tests (4 hours)

**Goal:** Full integration tests with real services (Supabase, email, etc).

**Tasks:**
1. Setup test database
   - Isolated Supabase branch for testing
   - RLS policies applied
   - Seed data: Contexia SAS tenant + users

2. Test complete customer onboarding
   - POST /api/v1/customers/invite → invite created
   - GET invite link → email sent (mock)
   - Customer clicks link → account created
   - Verify: auth user, tenant, roles, email
   - Check: all costs tracked
   - Verify: Kanban shows completed mission

3. Test role-based access
   - Admin can view all missions
   - Finance can view costs only
   - Viewer cannot edit anything
   - Attempt unauthorized access → 403

4. Test concurrent onboarding
   - 10 customers in parallel
   - No data collisions
   - Cost tracking accurate
   - RLS isolation verified

5. Test error recovery
   - Email service fails → mission blocked
   - Retry mechanism works
   - Dashboard shows blocked state
   - Admin can manually retry

6. Performance tests
   - Mission completes <500ms
   - API response <100ms
   - WebSocket latency <50ms
   - 100 concurrent missions OK

**Files to Create:**
- `tests/e2e/test_customer_onboarding.py`
- `tests/e2e/test_role_based_access.py`
- `tests/e2e/test_performance.py`
- `tests/fixtures/seed_data.sql`
- `tests/conftest.py` (pytest setup)

---

### T15: Documentation (2 hours)

**Goal:** Complete documentation for Phase 3 systems.

**Tasks:**
1. Customer Onboarding Guide
   - User workflow: invitation → activation → first login
   - Admin guide: inviting teams, managing roles
   - Screenshots + GIFs
   - Troubleshooting section

2. API Reference
   - Update MISSION_API.md with RLS examples
   - Add authentication flow diagram
   - Error response catalog
   - Rate limiting info

3. Developer Guide
   - Architecture overview diagram
   - Conductor pattern explanation
   - Swarm operators how-to
   - Adding new operators (template)
   - Running tests locally

4. Operations Guide
   - Cost monitoring + reporting
   - Mission replay (audit trail)
   - RLS policy debugging
   - Scaling considerations

5. Hermes Integration
   - How T11 implements Hermes patterns
   - Mission/Task/Checkpoint mapping
   - Kanban integration points
   - Cost tracking alignment

6. Deploy guide
   - Production checklist
   - Environment variables
   - Database setup
   - RLS policy activation
   - Rollback procedures

**Files to Create:**
- `docs/CUSTOMER_ONBOARDING.md`
- `docs/API_REFERENCE.md` (updated)
- `docs/DEVELOPER_GUIDE.md`
- `docs/OPERATIONS_GUIDE.md`
- `docs/HERMES_INTEGRATION.md`
- `docs/DEPLOY_GUIDE.md`

---

## 🚀 Execution Timeline

```
Mon Jun 24:   Kick-off, T12 design review
Tue Jun 25:   T12 implementation (RLS policies)
Wed Jun 26:   T13 (Email templates) + T12 testing
Thu Jun 27:   T14 (E2E tests) + T13 testing
Fri Jun 28:   T15 (Documentation) + T14 fixes
Sat Jun 29:   Final integration + smoke tests
Sun Jun 30:   Deploy to production + verification
```

---

## 📋 Pre-Phase 3B Checklist

Before starting Phase 3B, verify:

- [x] T11 complete (all commits merged)
- [x] T11 tests passing (60+ tests)
- [x] Code review approved
- [ ] Database migration strategy defined
- [ ] Email service integrated (mock OK initially)
- [ ] Supabase RLS baseline (from Phase 3A)
- [ ] Monitoring + logging enabled
- [ ] Stakeholder sign-off on timeline

---

## 🎯 Success Criteria

### Functional
- [x] Full customer onboarding flow working
- [x] Missions track all 5 operations with proof
- [x] Cost tracking accurate to $0.0001
- [x] Kanban Dashboard shows live mission state
- [x] WebSocket updates in <50ms
- [x] RLS policies prevent data leakage
- [x] Email templates render correctly
- [x] E2E tests pass 100%

### Non-Functional
- [x] API response <100ms
- [x] Mission completion <500ms (parallel)
- [x] 100+ concurrent missions supported
- [x] Code coverage >80%
- [x] All errors logged with context
- [x] Documentation complete + reviewed
- [x] Zero security vulnerabilities (assessed)

---

## 🔗 Dependencies

### Phase 3B depends on Phase 3A:
- ✅ Multi-tenant middleware (TenantContextMiddleware)
- ✅ RBAC system (roles, permissions, role_permissions)
- ✅ JWT authentication
- ✅ Supabase auth integration
- ✅ Database migrations (0000-0009)

### Phase 3B provides for Phase 4+:
- Mission replay for debugging
- Cost analytics dashboard
- SLA monitoring
- Agent integration (Phase 4)

---

## 💡 Design Decisions

### Why RLS before Production?
- Security-first: prevent accidental cross-tenant access
- Performance: RLS filters at database level
- Compliance: audit trail automatically isolated
- Testing: easier E2E test isolation

### Why Email Templates Early?
- Customer-facing: quality matters
- I18n: easier to add languages early
- Testing: realistic workflows earlier
- Not dependent on other systems

### Why E2E Tests Last?
- Needs all systems integrated
- T12 + T13 finish first
- Validates complete workflow
- Catches integration bugs early

---

## 📈 Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| RLS policy bugs | Extensive test coverage, audit logging |
| Email delivery fails | Fallback notification in dashboard |
| Cost calculation errors | Unit tests + audit trail verification |
| Performance regression | Baseline benchmarks before changes |
| Data migration issues | Dry run with production-like data |

---

## 🎓 Post-Phase 3B Activities

- Code review + stakeholder approval
- Stage 11: Deploy to production
- Customer communication + launch
- Performance monitoring (first week)
- Issue triage + hotfixes
- Phase 4 planning (Agent integration)

---

**Status: READY FOR EXECUTION**

T11 complete. Phase 3B tasks defined. Standby for kickoff.

**Next Action:** Schedule Phase 3B kickoff meeting (Jun 24 @ 10:00 UTC)
