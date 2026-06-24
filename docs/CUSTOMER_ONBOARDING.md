# Customer Onboarding Guide

Complete guide to the Contexia customer onboarding process.

## Overview

The onboarding workflow is fully automated via Hermes Conductor pattern:
- **Invite Stage**: Admin creates customer invite
- **Acceptance Stage**: Customer clicks link, creates account
- **Setup Stage**: Automated provisioning (5 parallel operations)
- **Completion Stage**: Welcome emails, access granted

**Timeline**: 15 minutes from invite to production

---

## Customer Journey: Step-by-Step

### 1. Sales Creates Invite

**Who**: Sales team / Account manager  
**How**: Send invite to customer via admin dashboard

```
POST /api/v1/admin/customers/invite
{
  "email": "john@acme.com",
  "plan": "pro"
}
```

**Result**: Invite sent via email with magic link

### 2. Customer Receives Invite Email

Customer receives professional email with:
- Invite link
- Plan details
- Quick setup guide
- Support contact info

**Email template**: `welcome.html`  
**Valid for**: 7 days  
**Action**: Click link to activate account

### 3. Customer Accepts Invite

**How**: Click email link → Set password → Create account

**Behind the scenes**:
1. Auth user created in Supabase
2. Tenant created (customer's workspace)
3. User assigned to tenant
4. Admin role assigned automatically

**Status**: Mission = EXECUTING

### 4. Automated Setup (Parallel)

5 operations run in parallel (~400ms total):

1. **Auth Operator** (~100ms)
   - Creates Supabase auth user
   - Generates secure credentials
   - Sets up MFA (optional)

2. **DB Operator** (~150ms)
   - Creates customer tenant
   - Initializes database records
   - Sets up RLS policies

3. **Roles Operator** (~50ms)
   - Assigns admin role to customer
   - Configures permissions
   - Sets up role matrix

4. **Comms Operator** (~120ms)
   - Sends welcome email
   - Schedules onboarding emails
   - Logs communication

5. **Workflow Operator** (~20ms)
   - Logs setup to audit trail
   - Records timestamps
   - Enables compliance reporting

**Cost**: $0.0135 (one-time)

### 5. Mission Completes

**Status**: Mission = COMPLETED

**Result**: Customer can log in immediately

**What's ready**:
- ✅ Dashboard access
- ✅ Team management
- ✅ Settings + preferences
- ✅ Integration setup

---

## Admin Guide: Managing Customers

### Creating Invites

```bash
POST /api/v1/admin/customers/invite
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "email": "customer@company.com",
  "plan": "pro"  # starter, pro, enterprise
}
```

**Plans**:
- **starter**: 1 team member, 100 operations/month
- **pro**: 5 team members, 1000 operations/month  
- **enterprise**: unlimited, custom pricing

### Viewing All Customers

```bash
GET /api/v1/admin/customers
```

Returns list of all customers with:
- Email
- Plan
- Status (onboarding, active, suspended)
- Creation date
- Last activity

### Resending Invites

```bash
POST /api/v1/admin/customers/{email}/resend-invite
```

Sends fresh invite link (previous link becomes invalid)

### Monitoring Setup Status

```bash
GET /api/v1/missions/{mission_id}
```

Check mission status and individual task details:
- Task 1: Auth (✅/❌)
- Task 2: Database (✅/❌)
- Task 3: Roles (✅/❌)
- Task 4: Email (✅/❌)
- Task 5: Workflow log (✅/❌)

### Troubleshooting Failed Setups

**Problem**: Mission failed at Task 2 (DB operator)

**Options**:
1. Retry: `POST /api/v1/missions/{id}/retry`
2. Manual fix: Contact support
3. Escalate: Create urgent ticket

**Email sent**: Customer receives failure notification with:
- What failed
- Why it failed
- Retry button
- Support contact

---

## Inviting Team Members

### As Admin

After onboarding completes, admin can add team members:

```bash
POST /api/v1/admin/teams/{tenant_id}/invite
{
  "email": "jane@acme.com",
  "role": "finance"
}
```

**Roles**:
- **admin**: Full access, manage users + settings
- **editor**: Create/edit workflows, view costs
- **finance**: View cost breakdowns, export reports
- **viewer**: Read-only, see completed operations

### What They Receive

Each team member gets email:
- Role details (what they can do)
- Team member list
- Dashboard link
- Getting started guide

**Email template**: `role_assigned.html`

---

## Timeline & Expectations

| Step | Duration | Status |
|------|----------|--------|
| Invite sent | 0m | Email in inbox |
| Customer clicks link | 1-5m | Activation page loads |
| Account creation | 1m | Auth user created |
| Setup (parallel) | 0.4s | All 5 ops run concurrently |
| Welcome email | +1m | Inbox |
| **Total** | **~15 min** | Production ready |

---

## Typical Email Sequence

### Invite Email (T+0 minutes)

Subject: "You're invited to Contexia"

Content:
- Welcome message
- Plan details (pro, 5 users, 1000 ops/month)
- Click link to start
- Support contact

### Welcome Email (T+5 minutes)

Subject: "Welcome to Contexia! 🎉"

Content:
- Account confirmed
- What was set up ✅
- Next steps (add team, connect integrations)
- Quick start guide

### Team Member Invitation (T+30 minutes)

Subject: "You've been added to [Company Name]"

Content:
- Role details (Finance: view costs, export reports)
- Team member list
- Access link
- How to set password

---

## FAQ

**Q: How long does onboarding take?**  
A: 15 minutes from invite to production. Can use platform immediately after email.

**Q: Can we customize the onboarding flow?**  
A: Partially. Contact us for custom workflows (different roles, additional setup steps).

**Q: What if onboarding fails?**  
A: Automatic retry available. Contact support for manual assistance.

**Q: Is there a cost?**  
A: One-time setup cost of $0.0135 per customer. Included in plan.

**Q: Can we invite team members before setup completes?**  
A: No, wait for welcome email. Takes ~5 minutes.

**Q: What role should the initial admin have?**  
A: Admin. They can adjust roles for themselves and others later.

---

## Troubleshooting

### Email not received

1. Check spam folder
2. Verify email address is correct
3. Request resend: `POST /api/v1/admin/customers/{email}/resend-invite`

### Invite link expired

1. Invite valid for 7 days
2. Request new invite from admin dashboard
3. Contact support if invite lost

### Setup failed

1. Check mission status: `GET /api/v1/missions/{id}`
2. View error details and error ID
3. Click "Retry" button or contact support

### Cannot log in after setup

1. Verify email and password
2. Try password reset
3. Contact support with error message

---

## Best Practices

1. **Communicate early**: Tell customer onboarding is 15 min
2. **Check email**: Setup sends 2 confirmation emails
3. **Add team quickly**: While onboarding is fresh in mind
4. **Set up integrations**: Connect accounting software next
5. **Review settings**: Check preferences + security

---

## Next Steps After Onboarding

1. **Add team members**: Invite colleagues by role
2. **Connect integrations**: Link accounting systems
3. **Create first workflow**: Start with template
4. **Review reports**: Understand cost breakdown
5. **Schedule training**: Team gets familiar with UI

---

## Support

- **Email**: support@contexia.online
- **Phone**: +1-555-0100
- **Chat**: In-app (available 24/7)
- **Docs**: https://docs.contexia.online

---

Generated: Phase 3B Documentation  
Last updated: 2026-06-23
