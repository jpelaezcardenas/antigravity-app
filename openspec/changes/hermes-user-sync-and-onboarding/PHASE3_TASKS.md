# Phase 3 Task Specification: User Sync & Multi-Tenant Onboarding

**Duration:** 7 days (Jun 23-29)  
**Owner:** Claude (Engineering) + Juan David (Oversight)  
**Target Completion:** Jun 30, 2026

---

## PHASE 3A: USER MIGRATION & SYNC (Days 1-2: Jun 23-24)

### T1: Create user_tenants Junction Table
**Duration:** 2 hours  
**Owner:** Claude  
**Status:** 🟢 READY

**Specification:**
- Table name: `user_tenants`
- Columns:
  - `id` (UUID, PK)
  - `user_id` (FK → usuarios.id)
  - `tenant_id` (FK → tenants.id)
  - `is_owner` (BOOLEAN, default false) — marks user as tenant owner
  - `is_active` (BOOLEAN, default true)
  - `created_at` (TIMESTAMPTZ)
  - `updated_at` (TIMESTAMPTZ)
- Constraints:
  - `UNIQUE(user_id, tenant_id)` — each user can have 1 role per tenant
  - `ON DELETE CASCADE` for both FKs
- Indexes:
  - `idx_user_tenants_user_id`
  - `idx_user_tenants_tenant_id`
  - `idx_user_tenants_is_owner`

**Migration:** `0004_user_tenants_table.sql` ✅

**Acceptance Criteria:**
- [ ] Table exists in staging DB
- [ ] Indexes created
- [ ] Can insert test records
- [ ] UNIQUE constraint enforced

---

### T2: Create user_roles Table & role_type Enum
**Duration:** 2 hours  
**Owner:** Claude  
**Status:** 🟢 READY

**Specification:**
- Enum type: `role_type` with values:
  - `admin` — Full system access
  - `finance` — Financial/GL operations
  - `marketing` — Marketing operations
  - `growth` — Growth operations
  - `operator` — Operator execution
  - `viewer` — Read-only access

- Table name: `user_roles`
- Columns:
  - `id` (UUID, PK)
  - `user_id` (FK → usuarios.id)
  - `tenant_id` (FK → tenants.id)
  - `role` (role_type, NOT NULL, default 'viewer')
  - `created_at` (TIMESTAMPTZ)
  - `updated_at` (TIMESTAMPTZ)
- Constraints:
  - `UNIQUE(user_id, tenant_id)` — one role per user per tenant
- Indexes:
  - `idx_user_roles_user_id`
  - `idx_user_roles_tenant_id`
  - `idx_user_roles_role`

**Migration:** `0005_user_roles_table.sql` ✅

**Acceptance Criteria:**
- [ ] Enum type created with 6 values
- [ ] Table exists in staging DB
- [ ] Indexes created
- [ ] Can insert/update role records

---

### T3: Create role_permissions Table
**Duration:** 2 hours  
**Owner:** Claude  
**Status:** 🟢 READY

**Specification:**
- Enum types:
  - `action_type`: create, read, update, delete, export, admin
  - `resource_type`: alerts, approval_queue, radar_insights, auditoria_reports, shadow_gl, operators, users, admin_panel, all

- Table name: `role_permissions`
- Columns:
  - `id` (UUID, PK)
  - `role` (role_type, NOT NULL)
  - `resource` (resource_type, NOT NULL)
  - `action` (action_type, NOT NULL)
  - `description` (TEXT)
  - `created_at` (TIMESTAMPTZ)
- Constraints:
  - `UNIQUE(role, resource, action)` — each permission defined once
- Indexes:
  - `idx_role_permissions_role`
  - `idx_role_permissions_resource`
  - `idx_role_permissions_action`

**Migration:** `0006_role_permissions_table.sql` ✅

**Acceptance Criteria:**
- [ ] Enum types created
- [ ] Table exists in staging DB
- [ ] Indexes created
- [ ] Permission matrix can be queried

---

### T4: Assign Users to Contexia SAS Tenant
**Duration:** 1 hour  
**Owner:** Claude  
**Status:** 🟢 READY

**Specification:**
Users to assign:
1. Juan David (jpelaezcardenas@gmail.com) — `is_owner: true`
2. Marketing team (contexia.marketing@gmail.com) — `is_owner: false`
3. Demo user (cliente@demo.co) — `is_owner: false`

**Migration:** `0007_assign_users_to_tenants.sql` ✅

**Acceptance Criteria:**
- [ ] 3 user-tenant records created
- [ ] Juan David marked as owner
- [ ] All users active
- [ ] Query `SELECT COUNT(*) FROM user_tenants` returns 3

---

### T5: Assign Initial Roles to Users
**Duration:** 1 hour  
**Owner:** Claude  
**Status:** 🟢 READY

**Specification:**
- Juan David → `admin` role
- contexia.marketing@gmail.com → `marketing` role
- cliente@demo.co → `viewer` role

**Migration:** `0008_assign_initial_roles.sql` ✅

**Acceptance Criteria:**
- [ ] 3 user-role records created
- [ ] Roles correctly assigned
- [ ] Query verifies assignments

---

## PHASE 3B: ROLE & PERMISSION FRAMEWORK (Days 3-4: Jun 25-26)

### T6: Seed Default Role Permissions
**Duration:** 3 hours  
**Owner:** Claude  
**Status:** 🟢 READY

**Specification:**
Define permission matrix for each role:

**Admin:**
```
- all resources: admin action
- users: create, read, update, delete
- admin_panel: read, update
```

**Finance:**
```
- shadow_gl: read, create, update
- approval_queue: read, update (approve)
- auditoria_reports: read, export
```

**Marketing:**
```
- alerts: read
- radar_insights: read, create
- auditoria_reports: read
```

**Growth:**
```
- alerts: read, update
- radar_insights: read, create
- auditoria_reports: read
```

**Operator:**
```
- operators: read, update
- approval_queue: read
- alerts: read
```

**Viewer:**
```
- alerts: read
- radar_insights: read
- approval_queue: read
- auditoria_reports: read
```

**Migration:** `0009_seed_role_permissions.sql` ✅

**Acceptance Criteria:**
- [ ] Permission records created (24+ rows)
- [ ] No duplicate permissions
- [ ] Each role has minimum 3 permissions
- [ ] Query `SELECT role, COUNT(*) FROM role_permissions GROUP BY role` shows distribution

---

### T7: Create RBAC Middleware for Permission Checking
**Duration:** 4 hours  
**Owner:** Claude  
**Status:** PENDING

**Specification:**
Create `apps/backend/core/rbac.py`:

```python
async def check_permission(
    request: Request,
    resource: str,
    action: str
) -> bool:
    """
    Check if current user has permission for resource+action.
    
    Returns True if:
    - User has admin role, OR
    - User has specific role_permission matching resource+action
    
    Returns False otherwise (returns 403 Forbidden in endpoint).
    """
```

**Usage in endpoints:**
```python
@router.post("/approve-invoice")
async def approve_invoice(request: Request, payload: ApproveRequest):
    if not await check_permission(request, "approval_queue", "update"):
        raise HTTPException(status_code=403, detail="Not authorized")
    # ... continue
```

**Acceptance Criteria:**
- [ ] Middleware checks user_roles + role_permissions
- [ ] Admin users bypass all checks
- [ ] Non-admin users checked against matrix
- [ ] Returns 403 when unauthorized
- [ ] Unit tests pass (≥95% coverage)

---

### T8: Update RLS Policies for Role-Based Filtering
**Duration:** 3 hours  
**Owner:** Claude  
**Status:** PENDING

**Specification:**
Enhance existing RLS policies to respect user roles:

```sql
-- Example: approval_queue RLS with role check
CREATE POLICY "approval_queue_role_based" ON approval_queue
FOR ALL
USING (
  -- Must have access to own tenant
  tenant_id = COALESCE((auth.jwt()->>'tenant_id')::uuid, 'a0000000...')
  AND
  -- AND must have permission for this action
  EXISTS (
    SELECT 1 FROM user_roles ur
    WHERE ur.user_id = auth.uid()
    AND ur.tenant_id = approval_queue.tenant_id
    AND ur.role IN ('admin', 'finance', 'operator')
  )
);
```

**Acceptance Criteria:**
- [ ] RLS policies updated for core tables (5+)
- [ ] Policies check both tenant_id AND role
- [ ] Test queries blocked for unauthorized users
- [ ] Test queries allowed for authorized users

---

## PHASE 3C: ONBOARDING & SETUP (Days 5-7: Jun 27-29)

### T9: Create Admin Dashboard for User Management
**Duration:** 6 hours  
**Owner:** Claude  
**Status:** PENDING

**Specification:**
Create `apps/backend/presentation/admin_endpoints.py`:

Endpoints:
```
POST /api/v1/admin/users
  → Create new user + assign to tenant + assign role
  
GET /api/v1/admin/users
  → List all users in tenant with roles
  
PUT /api/v1/admin/users/{user_id}/role
  → Update user role (admin only)
  
DELETE /api/v1/admin/users/{user_id}
  → Remove user from tenant (admin only)
  
GET /api/v1/admin/roles
  → List all roles + permissions (for reference)
```

**Acceptance Criteria:**
- [ ] All 5 endpoints implemented
- [ ] Admin-only authorization enforced
- [ ] Unit tests pass (≥90% coverage)
- [ ] Integration tests pass with real DB
- [ ] E2E tests verify user lifecycle

---

### T10: Verify All 4+ Users Can Log In and Access Resources
**Duration:** 2 hours  
**Owner:** Claude  
**Status:** PENDING

**Specification:**
Test each user with their assigned role:

1. **Juan David (Admin)**
   - [ ] Can log in
   - [ ] Can access admin panel
   - [ ] Can create/update/delete users
   - [ ] Can access all resources

2. **contexia.marketing@gmail.com (Marketing)**
   - [ ] Can log in
   - [ ] Can read alerts
   - [ ] Can create/read insights
   - [ ] Cannot approve invoices (not finance)

3. **growth@contexia.online (Growth)**
   - [ ] Can log in
   - [ ] Can read/update alerts
   - [ ] Can create insights
   - [ ] Cannot access finance panel

4. **cliente@demo.co (Viewer)**
   - [ ] Can log in
   - [ ] Can read (all read-only operations)
   - [ ] Cannot create/update/delete

**Acceptance Criteria:**
- [ ] All 4 users can authenticate
- [ ] Each user accesses only permitted resources
- [ ] Unauthorized requests return 403
- [ ] No cross-tenant data leakage

---

### T11: Final Verification Before Phase 2 Launch
**Duration:** 2 hours  
**Owner:** Claude  
**Status:** PENDING

**Specification:**
Verify Phase 2 can launch safely on Jul 3:

- [ ] All users assigned to tenants ✅
- [ ] All roles assigned ✅
- [ ] All permissions seeded ✅
- [ ] RBAC middleware working ✅
- [ ] RLS policies enforcing roles ✅
- [ ] Admin dashboard operational ✅
- [ ] E2E tests passing ✅
- [ ] Staging DB clean (no stale data)
- [ ] Production migration ready (dry-run successful)
- [ ] Team notified of new user management endpoints

**Acceptance Criteria:**
- [ ] All 11 tasks complete
- [ ] All tests passing (100% coverage on critical paths)
- [ ] No blockers for Phase 2
- [ ] Deployment checklist ready

---

## 📊 SUMMARY

| Task | Duration | Status | Owner |
|------|----------|--------|-------|
| T1: user_tenants table | 2h | ✅ DONE | Claude |
| T2: user_roles table | 2h | ✅ DONE | Claude |
| T3: role_permissions table | 2h | ✅ DONE | Claude |
| T4: Assign users to tenants | 1h | ✅ DONE | Claude |
| T5: Assign initial roles | 1h | ✅ DONE | Claude |
| T6: Seed permissions | 3h | ✅ DONE | Claude |
| T7: RBAC middleware | 4h | ⏳ PENDING | Claude |
| T8: RLS + roles | 3h | ⏳ PENDING | Claude |
| T9: Admin dashboard | 6h | ⏳ PENDING | Claude |
| T10: User login verification | 2h | ⏳ PENDING | Claude |
| T11: Pre-Phase-2 verification | 2h | ⏳ PENDING | Claude |
| **TOTAL** | **28h** | **6h done, 22h pending** | |

---

## ✅ MILESTONE DATES

```
Jun 23: Migrations created + ready to deploy ✅
Jun 24: Migrations deployed to staging
Jun 25: RBAC middleware implemented
Jun 26: RLS policies updated
Jun 27: Admin dashboard complete
Jun 28: User verification complete
Jun 29: Final verification + sign-off
Jun 30: Phase 3 COMPLETE
Jul 1: All clear for Phase 2 (Jul 3 kickoff)
```

---

**PHASE 3 READY TO EXECUTE**

All task specifications defined. Migrations prepared. Starting deployment now.
