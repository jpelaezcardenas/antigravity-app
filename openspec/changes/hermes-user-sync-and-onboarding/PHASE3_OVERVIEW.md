# Phase 3: User Sync & Multi-Tenant Onboarding

**Status:** 🟢 INITIATED (2026-06-23)  
**Target Completion:** 2026-07-01  
**Owner:** Juan David Pelaez Cardenas  
**Duration:** 7 days (3 sub-phases)

---

## 🎯 OBJECTIVE

Connect all active Contexia users to the multi-tenant system with proper role hierarchy, establishing **Juan David as User 0 (Admin)** of Contexia SAS tenant before Phase 2 execution (Jul 3).

---

## 📋 CURRENT STATE

### Users in Auth System
```
✅ jpelaezcardenas@gmail.com        (Not yet in auth.users)
✅ contexia.marketing@gmail.com     (In auth.users, active today)
✅ growth@contexia.online           (In auth.users, active today)
✅ cliente@demo.co                  (In auth.users, demo)
✅ fperez@ferez.co                  (In auth.users, test)
```

### Users in Database
```
✅ jpelaezcardenas@gmail.com        (Enterprise, no tenant assigned)
✅ contexia.marketing@gmail.com     (Enterprise, no tenant assigned)
✅ admin@contexia.co                (Enterprise admin account)
✅ cliente@demo.co                  (Starter, demo)
✅ lavaderos_ld@contexia.com        (Starter, demo)
✅ sion@contexia.com                (Starter, demo)
✅ repuestos_don_alvaro@contexia.com (Starter, demo)
```

### Tenants
```
✅ Contexia SAS (cliente_cero: true)
   └─ No users assigned yet
```

---

## 🔄 PHASE 3 STRUCTURE

### PHASE 3A: USER MIGRATION & SYNC (Days 1-2)
**Goal:** Unify user data across auth.users and usuarios table

- [ ] 3A.1 Create `user_tenants` junction table
- [ ] 3A.2 Create `user_roles` table
- [ ] 3A.3 Add growth@contexia.online to usuarios table
- [ ] 3A.4 Assign all users to Contexia SAS tenant
- [ ] 3A.5 Verify auth.users ↔ usuarios sync

### PHASE 3B: ROLE & PERMISSION FRAMEWORK (Days 3-4)
**Goal:** Define roles and establish access control

- [ ] 3B.1 Define 5 core roles (Admin, Finance, Marketing, Growth, Operator)
- [ ] 3B.2 Create role_permissions table
- [ ] 3B.3 Assign roles to users
- [ ] 3B.4 Update RLS policies for role-based access
- [ ] 3B.5 Test role enforcement

### PHASE 3C: ONBOARDING & SETUP (Days 5-7)
**Goal:** Activate all users and verify system readiness

- [ ] 3C.1 Promote Juan David to Admin of Contexia SAS
- [ ] 3C.2 Onboard marketing team (contexia.marketing@gmail.com)
- [ ] 3C.3 Onboard growth team (growth@contexia.online)
- [ ] 3C.4 Verify demo accounts (cliente@demo.co)
- [ ] 3C.5 Create admin dashboard for user management
- [ ] 3C.6 Final verification before Phase 2 launch

---

## 🎯 SUCCESS CRITERIA

Phase 3 is complete when:

```
✅ All 4 active users assigned to Contexia SAS tenant
✅ Juan David = User 0 (Admin role)
✅ contexia.marketing@gmail.com = Marketing role
✅ growth@contexia.online = Growth role
✅ cliente@demo.co = Demo/Test role
✅ RLS policies enforce role-based access
✅ Admin dashboard functional
✅ All 4+ users can log in and access their assigned resources
✅ Phase 2 can launch safely on Jul 3
```

---

## 📊 USER ASSIGNMENTS (TARGET STATE)

| Email | Role | Tenant | Status | Priority |
|-------|------|--------|--------|----------|
| jpelaezcardenas@gmail.com | Admin | Contexia SAS | User 0 | CRITICAL |
| contexia.marketing@gmail.com | Marketing | Contexia SAS | Active | HIGH |
| growth@contexia.online | Growth | Contexia SAS | Active | HIGH |
| cliente@demo.co | Demo | Contexia SAS | Active | MEDIUM |
| fperez@ferez.co | Test | Contexia SAS | Test | LOW |

---

## 🔧 TECHNICAL ARCHITECTURE

```
auth.users (Supabase Auth)
    ↓ (JWT contains email + tenant)
middleware (TenantContextMiddleware) ← Phase 1 ✅
    ↓ (adds tenant_id to request.state)
RLS Policies (enforce tenant isolation) ← Phase 1 ✅
    ↓ (role-based filtering)
users ← Phase 3 NEW
    ↓ (user_id → user_roles)
user_roles ← Phase 3 NEW
    ↓ (role_id → role_permissions)
role_permissions ← Phase 3 NEW
    ↓ (what each role can do)
Authorized Access
```

---

## 📅 TIMELINE

```
Jun 23 (TODAY):     Phase 3 launch
Jun 24-25:          Phase 3A (user migration)
Jun 26-27:          Phase 3B (role framework)
Jun 28-29:          Phase 3C (onboarding)
Jun 30:             Final verification
Jul 1:              Phase 3 COMPLETE
Jul 3:              Phase 2 KICKOFF (safe to proceed)
```

---

## 📁 DELIVERABLES

```
openspec/changes/hermes-user-sync-and-onboarding/

DOCUMENTATION:
✅ PHASE3_OVERVIEW.md (this file)
✅ PHASE3_TASKS.md (detailed task specs)
✅ PHASE3_TIMELINE.md (visual timeline)

DATABASE:
✅ migrations/0004_user_tenants_table.sql
✅ migrations/0005_user_roles_table.sql
✅ migrations/0006_role_permissions_table.sql
✅ migrations/0007_assign_users_to_tenants.sql
✅ migrations/0008_assign_roles_to_users.sql

CODE:
✅ apps/backend/core/user_management.py (user/role service)
✅ apps/backend/core/auth_permissions.py (RBAC)

VERIFICATION:
✅ tests/backend/core/test_user_roles.py
✅ tests/backend/core/test_rbac.py
```

---

## ✅ NEXT IMMEDIATE STEPS

**STEP 1 (TODAY - Jun 23):**
```
→ Create user_tenants migration
→ Create user_roles migration  
→ Create user_roles assignment migration
→ Deploy migrations to staging
```

**STEP 2 (Jun 24):**
```
→ Add growth@contexia.online to usuarios table
→ Assign all users to Contexia SAS tenant
→ Verify sync complete
```

**STEP 3 (Jun 25):**
```
→ Define 5 core roles
→ Assign roles to users
→ Test RLS with role-based filtering
```

---

**PHASE 3 READY TO EXECUTE**

All planning complete. Starting with Step 1 now.

🚀 **You (Juan David) will be User 0 Admin of Contexia SAS when this is done.**
