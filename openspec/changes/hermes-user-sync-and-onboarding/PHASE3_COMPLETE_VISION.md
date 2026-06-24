# Phase 3: COMPLETE USER & CUSTOMER ONBOARDING SYSTEM

**Status:** 🟢 PHASE 3A COMPLETE | ⏳ PHASE 3B READY  
**Total Duration:** 10 days (Jun 23-Jul 2)  
**Vision:** From Contexia (Client 0 / nosotros mismos) to Enterprise Customers  
**Integration:** Hermes operators automate entire customer lifecycle

---

## 🎯 COMPLETE VISION

```
CONTEXIA (CLIENT 0 / NOSOTROS MISMOS)
─────────────────────────────────────
Juan David (jpelaezcardenas@gmail.com)
  ├─ Role: ADMIN
  ├─ Tenant: Contexia SAS  
  ├─ Permissions: All resources
  └─ Responsibility: Invite + manage all customers
  
          ↓ (Hermes Operators automate)
          
ENTERPRISE CUSTOMERS
───────────────────
✅ Customer 1: Lavaderos LD (PRO plan)
   ├─ Tenant: unique ID
   ├─ Admin: accounting@lavaderos.co
   ├─ Finance: contabilidad@lavaderos.co
   └─ Operations: ops@lavaderos.co

✅ Customer 2: SyncManager (ENTERPRISE plan)
   ├─ Tenant: unique ID
   ├─ Multiple team members
   └─ Custom roles + permissions

✅ Customer N: ...
```

---

## 🔄 CUSTOMER LIFECYCLE (COMPLETE FLOW)

```
1. CONTEXIA INVITES CUSTOMER
   Juan David → create customer invite
   
2. CUSTOMER ACCEPTS INVITE
   admin@lavaderos.co → clicks email link
   
3. HERMES REGISTERS CUSTOMER (OPERATOR: register_customer)
   ├─ Creates Supabase auth user
   ├─ Creates tenant + usuarios rows
   ├─ Assigns admin role
   └─ Sends welcome email
   
4. CUSTOMER LOGS IN
   Sets password → accesses dashboard
   
5. CUSTOMER INVITES TEAM
   admin@lavaderos.co → invites finance + ops team
   
6. HERMES ONBOARDS TEAM (OPERATOR: onboard_team_member)
   ├─ Creates auth users for each team member
   ├─ Assigns roles (finance, operator)
   ├─ Sends welcome emails
   
7. TEAM ACCESSES SYSTEM
   ├─ Finance: GL + approvals only
   ├─ Operations: operators + alerts only
   └─ RLS + RBAC enforce permissions
   
8. CUSTOMER MANAGES TEAM
   ├─ Update roles (OPERATOR: update_team_member_role)
   ├─ Remove members (OPERATOR: offboard_team_member)
   └─ Audit trail logged for all changes
```

---

## 📊 DATABASE ARCHITECTURE

### NEW TABLES (Phase 3B)
```
customer_invites (Phase 3B)
  ├─ customer_name, customer_email
  ├─ plan (starter, pro, enterprise)
  ├─ invite_token (7-day expiration)
  ├─ status (pending → accepted)
  └─ created_tenant_id (after acceptance)

team_invites (Phase 3B)
  ├─ tenant_id, invitee_email
  ├─ role (enum)
  ├─ invite_token (7-day expiration)
  ├─ status (pending → accepted)
  └─ created_user_id (after acceptance)

onboarding_workflows (Phase 3B - AUDIT TRAIL)
  ├─ tenant_id, user_id
  ├─ workflow_type (customer_registration, team_onboarding)
  ├─ operator_id (which Hermes operator executed)
  ├─ status (pending → in_progress → completed)
  └─ error_message (if failed)
```

### EXISTING TABLES (Phase 3A + Phase 1)
```
tenants (Phase 3A)
  ├─ All customers get own tenant
  └─ Contexia = cliente_cero tenant

usuarios (Phase 3A)
  └─ All users in single table

user_tenants (Phase 3A - junction)
  ├─ user_id → tenant_id mapping
  └─ is_owner, is_active flags

user_roles (Phase 3A - junction)
  ├─ Assigns role to user per tenant
  └─ One role per user per tenant

role_permissions (Phase 3A)
  ├─ Defines what each role can do
  └─ 31 permissions seeded
```

---

## 🤖 HERMES OPERATORS

```
register_customer (Phase 3B)
  Triggered: Customer clicks email invite
  Actions:
  ├─ Create Supabase auth user
  ├─ Create tenant + usuarios rows
  ├─ Assign admin role
  ├─ Send welcome email
  └─ Log to onboarding_workflows

onboard_team_member (Phase 3B)
  Triggered: Team member clicks email invite
  Actions:
  ├─ Create auth user
  ├─ Create usuarios row
  ├─ Assign role (finance, marketing, operator)
  ├─ Send welcome email
  └─ Log to onboarding_workflows

update_team_member_role (Phase 3B)
  Triggered: Customer admin changes role
  Actions:
  ├─ Update user_roles.role
  ├─ Validate plan allows new role
  ├─ Send notification email
  └─ Log to onboarding_workflows

offboard_team_member (Phase 3B)
  Triggered: Customer admin removes member
  Actions:
  ├─ Set user_tenants.is_active = false
  ├─ Invalidate sessions
  ├─ Archive user data
  ├─ Send offboarding email
  └─ Log to onboarding_workflows
```

---

## ✅ PHASE 3A: COMPLETE ✅

```
Status: 🟢 DEPLOYED & VERIFIED

✅ Migrations 0004-0009 deployed
✅ 3 users assigned to Contexia SAS
✅ 3 roles assigned (admin, marketing, viewer)
✅ 31 permissions seeded
✅ USER 0 ESTABLISHED: Juan David = Admin
```

---

## ⏳ PHASE 3B: READY TO BUILD

```
Status: 🟡 ARCHITECTURE COMPLETE | 9 TASKS | 30 HOURS

Tasks:
  T6: Deploy customer_invites table (0010)
  T7: Deploy team_invites table (0011)
  T8: Deploy onboarding_workflows table (0012)
  T9: Build RBAC middleware (plan-based roles)
  T10: Build admin dashboard (10+ endpoints)
  T11: Build Hermes operators (4 operators)
  T12: Update RLS + role-based filtering
  T13: Email templates (4 templates)
  T14: E2E onboarding tests (3 scenarios)
  T15: Documentation + Phase 2 handoff

Timeline:
  Jun 24: T6-T7 (migrations)
  Jun 25: T8-T9 (workflows + RBAC)
  Jun 26: T10 (admin dashboard)
  Jun 27: T11 (Hermes operators)
  Jun 28: T12-T15 (RLS, emails, tests, docs)
  Jun 30: PHASE 3B COMPLETE ✅
```

---

## 🎯 COMPLETE SUCCESS CRITERIA

### Phase 3A ✅
- ✅ All users assigned to tenants
- ✅ All roles assigned
- ✅ All permissions seeded
- ✅ User 0 admin ready
- ✅ Multi-tenant architecture ready

### Phase 3B (READY)
- ⏳ Customer self-registration (via Hermes)
- ⏳ Team member invitations working
- ⏳ Auto-onboarding complete
- ⏳ RBAC enforces roles
- ⏳ RLS enforces tenant isolation
- ⏳ No data leakage
- ⏳ Plan-based roles working
- ⏳ Admin dashboard operational
- ⏳ Hermes operators integrated
- ⏳ Audit trail complete
- ⏳ Documentation complete
- ⏳ Ready for Phase 2 (Jul 3)

---

## 📅 COMPLETE TIMELINE

```
Jun 23: Phase 3A COMPLETE ✅
Jun 24-28: Phase 3B execution
Jun 30: Phase 3 COMPLETE ✅
Jul 1: Ready for Phase 2
Jul 3: Phase 2 KICKOFF 🚀
Jul 25: Customer call 🎤
```

---

**PHASE 3: COMPLETE VISION**

✅ Phase 3A: USER MIGRATION (COMPLETE)  
⏳ Phase 3B: CUSTOMER ONBOARDING (READY)

🚀 **Ready to execute Phase 3B!**
