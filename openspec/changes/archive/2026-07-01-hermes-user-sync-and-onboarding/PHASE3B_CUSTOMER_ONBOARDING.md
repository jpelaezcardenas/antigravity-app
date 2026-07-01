# Phase 3B: Customer Onboarding System & Hermes Integration

**Duration:** 5 days (Jun 24-28)  
**Owner:** Claude (Engineering) + Juan David (Product)  
**Scope:** Complete customer lifecycle from Contexia (Client 0) → Enterprise Customers  
**Integration:** Hermes operators automate customer registration + role assignment

---

## 🎯 OBJECTIVE

Establish a **complete customer onboarding system** where:
1. **Contexia (Client 0)** = System administrator + operator workspace
2. **Customers** = Invited by Contexia, onboarded via Hermes operators
3. **Hermes Operators** = Automated tools that register customers + assign roles + set up access
4. **Multi-Tenant Model** = Each customer gets own tenant, users, roles, audit trail

---

## 📊 CUSTOMER ONBOARDING FLOW

```
STEP 1: CONTEXIA (CLIENT 0) INVITES CUSTOMER
┌─────────────────────────────────────────────┐
│ Juan David (Admin) creates customer invite  │
│ - Customer name (e.g., "Lavaderos LD")      │
│ - Customer email (e.g., "admin@lavaderos.co") │
│ - Customer plan (starter, pro, enterprise) │
│ - Assigned roles (admin, finance, etc.)     │
└─────────────────────────────────────────────┘
            ↓
STEP 2: HERMES OPERATOR REGISTERS CUSTOMER
┌─────────────────────────────────────────────┐
│ Operator: "register_customer"               │
│ - Reads invite from queue                   │
│ - Creates auth.users entry (Supabase)      │
│ - Creates usuarios row (database)          │
│ - Creates tenant row (database)            │
│ - Sends welcome email with credentials     │
└─────────────────────────────────────────────┘
            ↓
STEP 3: CUSTOMER ADMIN LOGS IN
┌─────────────────────────────────────────────┐
│ Customer admin (lavaderos@admin.co)         │
│ - Receives email with login link + password │
│ - Logs in to Contexia system               │
│ - Sees dashboard (read-only initially)     │
└─────────────────────────────────────────────┘
            ↓
STEP 4: CUSTOMER INVITES TEAM MEMBERS
┌─────────────────────────────────────────────┐
│ Customer admin invites team:                │
│ - finance@lavaderos.co → finance role      │
│ - operations@lavaderos.co → operator role  │
│ - Each gets email invite                    │
└─────────────────────────────────────────────┘
            ↓
STEP 5: HERMES OPERATORS AUTO-ONBOARD TEAM
┌─────────────────────────────────────────────┐
│ Operator: "onboard_team_member"            │
│ - Reads team invite from queue              │
│ - Creates auth.users entry                 │
│ - Assigns role to user_roles               │
│ - Sets up initial workspace                │
│ - Sends welcome email                      │
└─────────────────────────────────────────────┘
            ↓
STEP 6: CUSTOMER TEAM ACCESSES SYSTEM
┌─────────────────────────────────────────────┐
│ Each team member logs in with their role   │
│ - Finance: GL, approvals, audit access    │
│ - Operations: operator configs, queue      │
│ - Each sees only their tenant + resources │
└─────────────────────────────────────────────┘
```

---

## 🔧 DATABASE ARCHITECTURE FOR ONBOARDING

### NEW TABLES

**1. customer_invites** — Track pending customer registrations
```sql
CREATE TABLE customer_invites (
  id UUID PRIMARY KEY,
  created_by UUID (Contexia admin),
  customer_name TEXT,
  customer_email TEXT UNIQUE,
  plan TEXT (starter, pro, enterprise),
  invite_token TEXT UNIQUE,
  invite_expires_at TIMESTAMPTZ,
  status TEXT (pending, accepted, expired),
  created_at TIMESTAMPTZ,
  accepted_at TIMESTAMPTZ,
  
  -- Hermes operator tracking
  operator_id TEXT (Hermes operator name),
  operator_executed_at TIMESTAMPTZ,
  
  FOREIGN KEY (created_by) REFERENCES usuarios(id)
);
```

**2. team_invites** — Track pending team member invitations
```sql
CREATE TABLE team_invites (
  id UUID PRIMARY KEY,
  tenant_id UUID (which customer),
  invited_by UUID (customer admin),
  invitee_email TEXT,
  role role_type,
  invite_token TEXT UNIQUE,
  invite_expires_at TIMESTAMPTZ,
  status TEXT (pending, accepted, expired),
  created_at TIMESTAMPTZ,
  accepted_at TIMESTAMPTZ,
  
  -- Hermes operator tracking
  operator_id TEXT,
  operator_executed_at TIMESTAMPTZ,
  
  FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  FOREIGN KEY (invited_by) REFERENCES usuarios(id)
);
```

**3. onboarding_workflows** — Audit trail of all onboarding operations
```sql
CREATE TABLE onboarding_workflows (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  workflow_type TEXT (customer_registration, team_onboarding, role_update),
  operator_id TEXT (Hermes operator name),
  user_id UUID (user being onboarded),
  role_assigned role_type,
  status TEXT (pending, in_progress, completed, failed),
  error_message TEXT (if failed),
  created_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
  FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
);
```

---

## 🔐 RBAC WITH CUSTOMER TIERS

### ROLE MATRIX BY CUSTOMER PLAN

**STARTER PLAN** (small businesses)
```
Roles available:
- admin (full access to their tenant only)
- finance (GL, approvals)
- viewer (read-only)

Permissions:
- admin: all resources in their tenant
- finance: shadow_gl, approval_queue, auditoria_reports
- viewer: read-only on all
```

**PRO PLAN** (growing businesses)
```
Roles available:
- admin
- finance
- marketing
- growth
- operator
- viewer

Permissions: Full permission matrix (as seeded in Phase 3A)
```

**ENTERPRISE PLAN** (custom roles)
```
Roles available:
- All 6 standard roles
- Custom roles (configurable by admin)

Permissions: Custom permission matrix per role
```

---

## 🤖 HERMES OPERATORS FOR ONBOARDING

### OPERATOR 1: register_customer
**Trigger:** Customer invite accepted (email click)  
**Owner:** Contexia admin  
**Action:** Automatically register customer in system

```python
@operator
def register_customer(invite_id: str) -> dict:
    """
    Registered when customer clicks email invite link.
    
    Steps:
    1. Fetch customer_invite from DB
    2. Validate invite token + expiration
    3. Create Supabase auth user (email + temp password)
    4. Create usuarios row (database)
    5. Create tenants row (database)
    6. Create user_tenants mapping (is_owner: true)
    7. Assign admin role to user_roles
    8. Send email with login link
    9. Log workflow to onboarding_workflows
    10. Update customer_invites.status = 'accepted'
    
    Returns:
    {
      "status": "success",
      "customer_id": uuid,
      "tenant_id": uuid,
      "user_id": uuid,
      "admin_email": "...",
      "temporary_password": "...",
      "login_url": "https://contexia.online/app/bunker?token=..."
    }
    """
```

### OPERATOR 2: onboard_team_member
**Trigger:** Team member invite accepted  
**Owner:** Customer admin  
**Action:** Automatically register team member

```python
@operator
def onboard_team_member(invite_id: str) -> dict:
    """
    Registered when team member clicks email invite link.
    
    Steps:
    1. Fetch team_invite from DB
    2. Validate invite token + expiration
    3. Create Supabase auth user
    4. Create usuarios row
    5. Create user_tenants mapping (is_owner: false)
    6. Assign role (from team_invite.role)
    7. Create onboarding_workflows entry
    8. Send email with login link
    9. Update team_invites.status = 'accepted'
    
    Returns:
    {
      "status": "success",
      "user_id": uuid,
      "tenant_id": uuid,
      "role": "finance|marketing|growth|operator",
      "email": "...",
      "temporary_password": "...",
      "login_url": "..."
    }
    """
```

### OPERATOR 3: update_team_member_role
**Trigger:** Admin changes team member role  
**Owner:** Customer admin  
**Action:** Update role in system

```python
@operator
def update_team_member_role(
    user_id: str,
    tenant_id: str,
    new_role: str  # admin, finance, marketing, growth, operator, viewer
) -> dict:
    """
    Triggered when customer admin updates team member role.
    
    Steps:
    1. Validate user exists in tenant
    2. Validate new_role is allowed for customer plan
    3. Update user_roles.role
    4. Send email notifying of role change
    5. Log to onboarding_workflows
    
    Returns:
    {
      "status": "success",
      "user_id": uuid,
      "previous_role": "...",
      "new_role": "...",
      "timestamp": "..."
    }
    """
```

### OPERATOR 4: offboard_team_member
**Trigger:** Admin removes team member  
**Owner:** Customer admin  
**Action:** Disable user access

```python
@operator
def offboard_team_member(user_id: str, tenant_id: str) -> dict:
    """
    Triggered when customer admin removes team member.
    
    Steps:
    1. Validate user in tenant
    2. Set user_tenants.is_active = false
    3. Invalidate active sessions
    4. Send email confirming offboarding
    5. Log to onboarding_workflows
    6. Archive user data
    
    Returns:
    {
      "status": "success",
      "user_id": uuid,
      "offboarded_at": timestamp
    }
    """
```

---

## 📋 PHASE 3B DETAILED TASKS

### T7: Create customer_invites + team_invites Tables
**Duration:** 2 hours  
**Status:** 🟢 READY

**Migration:** `0010_customer_invites_table.sql`  
**Migration:** `0011_team_invites_table.sql`

**Acceptance Criteria:**
- [ ] Both tables exist with correct columns
- [ ] Foreign keys established
- [ ] Indexes created (email, status, token)
- [ ] Can insert test records

---

### T8: Create onboarding_workflows Audit Table
**Duration:** 1 hour  
**Status:** 🟢 READY

**Migration:** `0012_onboarding_workflows_table.sql`

**Acceptance Criteria:**
- [ ] Table exists with all columns
- [ ] Indexes on tenant_id, operator_id, status
- [ ] Can log workflow records

---

### T9: Create RBAC Middleware with Plan-Based Roles
**Duration:** 4 hours  
**Status:** 🟡 PENDING

**File:** `apps/backend/core/rbac.py`

```python
async def check_permission(
    request: Request,
    resource: str,
    action: str
) -> bool:
    """
    Check if user has permission based on:
    1. User role in user_roles
    2. Customer plan (starter, pro, enterprise)
    3. Allowed roles for that plan
    4. Permission matrix in role_permissions
    """
    user_id = auth.uid()
    tenant_id = request.state.tenant_id
    
    # Get user role + customer plan
    role = await get_user_role(user_id, tenant_id)
    plan = await get_tenant_plan(tenant_id)
    
    # Check if role allowed for plan
    if not is_role_allowed_for_plan(role, plan):
        return False
    
    # Check permission in matrix
    return await has_permission(role, resource, action)
```

**Acceptance Criteria:**
- [ ] Checks user_roles + role_permissions
- [ ] Enforces plan-based role restrictions
- [ ] Admin users bypass restrictions
- [ ] Returns 403 when unauthorized
- [ ] ≥90% test coverage

---

### T10: Create Admin Dashboard Endpoints
**Duration:** 6 hours  
**Status:** 🟡 PENDING

**File:** `apps/backend/presentation/admin_endpoints.py`

```python
# CUSTOMER MANAGEMENT (Contexia admin only)
POST /api/v1/admin/customers/invite
  → Create customer invite
  → Parameters: customer_name, customer_email, plan
  → Returns: invite_token, invite_link

GET /api/v1/admin/customers
  → List all customers with status
  → Filters: plan, status (active, pending, suspended)

PUT /api/v1/admin/customers/{tenant_id}/plan
  → Update customer plan (for billing)

# TEAM MANAGEMENT (Customer admin or Contexia)
POST /api/v1/admin/teams/{tenant_id}/invite
  → Invite team member to customer
  → Parameters: invitee_email, role
  → Returns: invite_link

GET /api/v1/admin/teams/{tenant_id}/members
  → List team members with roles

PUT /api/v1/admin/teams/{tenant_id}/members/{user_id}/role
  → Update team member role

DELETE /api/v1/admin/teams/{tenant_id}/members/{user_id}
  → Offboard team member

# ONBOARDING WORKFLOWS (Audit trail)
GET /api/v1/admin/workflows
  → List all onboarding operations
  → Filters: tenant_id, operator_id, status

GET /api/v1/admin/workflows/{workflow_id}
  → View workflow details + logs
```

**Acceptance Criteria:**
- [ ] All 10+ endpoints implemented
- [ ] Admin-only authorization enforced
- [ ] Customer admins can invite teams
- [ ] Contexia admins can manage all customers
- [ ] ≥90% test coverage

---

### T11: Create Hermes Operators for Customer Onboarding
**Duration:** 6 hours  
**Status:** 🟡 PENDING

**Files:**
- `apps/backend/operators/register_customer.py`
- `apps/backend/operators/onboard_team_member.py`
- `apps/backend/operators/update_team_member_role.py`
- `apps/backend/operators/offboard_team_member.py`

**Implementation:**
1. Fetch invite from queue
2. Create user in Supabase auth
3. Create user in database
4. Assign roles + tenants
5. Send welcome email
6. Log to onboarding_workflows
7. Update invite status

**Acceptance Criteria:**
- [ ] All 4 operators implemented
- [ ] Operators register with Hermes correctly
- [ ] Can be called from admin dashboard
- [ ] Error handling + retry logic
- [ ] Audit trail logged
- [ ] ≥90% test coverage

---

### T12: Update RLS Policies for Role-Based Access
**Duration:** 3 hours  
**Status:** 🟡 PENDING

**Migration:** `0013_update_rls_for_roles.sql`

Update RLS policies on core tables:
```sql
-- Example: approval_queue with role check
CREATE POLICY "approval_queue_role_based" ON approval_queue
FOR ALL
USING (
  -- User must be in same tenant
  tenant_id = (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid())
  
  -- AND user must have permission for this action
  AND (
    -- Admin can do anything
    (SELECT role FROM user_roles WHERE user_id = auth.uid())::text = 'admin'
    
    -- OR specific role + permission match
    OR EXISTS (
      SELECT 1 FROM role_permissions rp
      WHERE rp.role = (SELECT role FROM user_roles WHERE user_id = auth.uid())
      AND rp.resource = 'approval_queue'
      AND rp.action = 'read'  -- or update, create, delete
    )
  )
);
```

**Acceptance Criteria:**
- [ ] RLS policies updated for 5+ core tables
- [ ] Policies check both tenant_id AND role
- [ ] Test queries blocked for unauthorized users
- [ ] Test queries allowed for authorized users
- [ ] No performance degradation

---

### T13: Email Templates for Customer Onboarding
**Duration:** 2 hours  
**Status:** 🟡 PENDING

**Files:**
- `apps/backend/templates/customer_invite_email.html`
- `apps/backend/templates/team_invite_email.html`
- `apps/backend/templates/welcome_email.html`
- `apps/backend/templates/role_update_email.html`

**Content:**
1. **Customer Invite Email**
   - "You've been invited to Contexia"
   - Customer name + plan
   - Invite link (expires in 7 days)
   - CTA: "Accept Invite"

2. **Team Invite Email**
   - "You've been invited to [Customer Name]"
   - Your role
   - Invite link
   - CTA: "Join Team"

3. **Welcome Email**
   - Temporary password
   - Login link
   - Initial setup checklist
   - Support contact

4. **Role Update Email**
   - "Your role has been updated"
   - Previous role → New role
   - New permissions

**Acceptance Criteria:**
- [ ] 4 email templates created
- [ ] Branded with Contexia styling
- [ ] Personalization (customer name, role, etc.)
- [ ] Mobile-responsive HTML
- [ ] Links tested

---

### T14: End-to-End Customer Onboarding Test
**Duration:** 4 hours  
**Status:** 🟡 PENDING

**Test Scenario 1: New Customer Registration**
```
1. Contexia admin (Juan) invites "Lavaderos LD"
2. Invite email sent to lavaderos@admin.co
3. Lavaderos admin clicks link
4. System creates user + tenant + role
5. Lavaderos admin can log in
6. Lavaderos admin sees only their data (tenant isolation)
7. Lavaderos admin invites team members
8. Team members get onboarded via operators
9. Finance team member can see GL
10. Marketing team member cannot see GL (permission denied)
```

**Test Scenario 2: Multi-Tenant Isolation**
```
1. Lavaderos admin invites accounting@lavaderos.co (finance role)
2. SyncManager admin invites admin@syncmanager.co (admin role)
3. Both login simultaneously
4. Lavaderos user sees ONLY Lavaderos data
5. SyncManager user sees ONLY SyncManager data
6. No data leakage
7. RLS enforces tenant isolation at DB level
8. RBAC enforces role at app level
```

**Test Scenario 3: Plan-Based Role Restrictions**
```
1. Contexia creates customer with STARTER plan
2. Starter plan only allows: admin, finance, viewer
3. Admin tries to invite user with 'growth' role (not allowed)
4. System rejects with clear error
5. Create with 'finance' role instead
6. User gets assigned correctly
```

**Acceptance Criteria:**
- [ ] All 3 scenarios pass
- [ ] No data leakage between tenants
- [ ] Roles enforced correctly
- [ ] Plan restrictions respected
- [ ] Email notifications sent
- [ ] Audit trail complete

---

### T15: Documentation + Handoff for Phase 2
**Duration:** 2 hours  
**Status:** 🟡 PENDING

**Documentation:**
- `CUSTOMER_ONBOARDING_GUIDE.md` — How customers get onboarded
- `OPERATOR_GUIDE.md` — How Hermes operators work
- `ADMIN_DASHBOARD_GUIDE.md` — How to use admin panel
- `RBAC_PERMISSION_MATRIX.md` — Full permission reference

**Handoff Checklist for Phase 2:**
- [ ] Operators fully integrated with Hermes
- [ ] Admin dashboard operational
- [ ] All 3+ test scenarios pass
- [ ] Documentation complete
- [ ] Team trained on new system
- [ ] Staging DB ready for Phase 2 execution

---

## 📊 SUMMARY

| Task | Duration | Status | Owner |
|------|----------|--------|-------|
| T7: customer_invites table | 2h | ⏳ PENDING | Claude |
| T8: onboarding_workflows table | 1h | ⏳ PENDING | Claude |
| T9: RBAC middleware | 4h | ⏳ PENDING | Claude |
| T10: Admin dashboard | 6h | ⏳ PENDING | Claude |
| T11: Hermes operators | 6h | ⏳ PENDING | Claude |
| T12: RLS + roles | 3h | ⏳ PENDING | Claude |
| T13: Email templates | 2h | ⏳ PENDING | Claude |
| T14: E2E onboarding tests | 4h | ⏳ PENDING | Claude |
| T15: Documentation | 2h | ⏳ PENDING | Claude |
| **TOTAL** | **30h** | **All PENDING** | |

---

## 🎯 SUCCESS CRITERIA (PHASE 3B COMPLETE)

```
✅ Customer can self-register (via Hermes operator)
✅ Customer admin can invite team members
✅ Team members auto-onboarded (via Hermes operator)
✅ RBAC enforces role-based permissions
✅ RLS enforces tenant isolation at DB level
✅ Multi-tenant data never leaks
✅ Plan-based role restrictions work
✅ Admin dashboard fully operational
✅ Audit trail complete for all operations
✅ E2E onboarding tests all pass
✅ Documentation complete
✅ Ready for Phase 2 launch (Jul 3)
```

---

## 🚀 TIMELINE

```
Jun 24 (TODAY):     T7-T8 migrations
Jun 25:             T9 RBAC middleware
Jun 26:             T10 Admin dashboard
Jun 27:             T11 Hermes operators
Jun 28:             T12-T15 (RLS, emails, tests, docs)
Jun 29:             Final verification
Jun 30:             Phase 3B COMPLETE ✅
Jul 1:              Phase 3 COMPLETE ✅
Jul 3:              Phase 2 KICKOFF ✅
```

---

**PHASE 3B READY TO EXECUTE**

Complete customer onboarding system from Contexia (Client 0) to enterprise customers, integrated with Hermes operators.

This is the foundation for:
- ✅ Automatic customer registration
- ✅ Automatic team member onboarding
- ✅ Role-based access control
- ✅ Multi-tenant data isolation
- ✅ Compliance + audit trails

Ready to build. 🚀
