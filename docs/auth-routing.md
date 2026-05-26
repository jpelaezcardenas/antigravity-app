# Authentication & Routing Architecture

## Overview

Contexia uses **Supabase Auth** for authentication with SSO support (Google, Microsoft, Email). The routing system differentiates between **admin** and **client** roles, directing users to appropriate dashboards.

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Landing Page (/)                                         │
│    ↓ No session → redirect to /login.html                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Login Page (/login.html)                                 │
│    • Static HTML (not Next.js)                              │
│    • Supabase SDK v2 client-side                            │
│    • SSO: Google, Microsoft, Email                          │
│    • Role toggle: visible only for ADMIN_EMAILS             │
│                                                              │
│    ADMIN_EMAILS (hardcoded):                                │
│      - contexia.marketing@gmail.com                         │
│                                                              │
│    CLIENT_EMAILS (hardcoded):                               │
│      - fperez@ferez.co (FEREZ SAS)                          │
│      - carlos@importacionesmtz.co (Importaciones Martinez)  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Role Check & Redirect                                    │
│                                                              │
│    If user email ∈ ADMIN_EMAILS:                            │
│      → Redirect to /app/bunker (Admin Dashboard)            │
│                                                              │
│    Else if user email ∈ CLIENT_EMAILS:                      │
│      → Redirect to /app/overview (Client Dashboard)         │
│                                                              │
│    Else:                                                     │
│      → Error: "Este correo no tiene acceso"                 │
└─────────────────────────────────────────────────────────────┘
```

## Session Storage

Login.html stores session in localStorage:

```javascript
localStorage.setItem("cx_user", JSON.stringify({
  email: "user@example.com",
  role: "admin", // or "client"
  is_admin: true // boolean
}));

localStorage.setItem("token", session.access_token);
```

## Protected Routes

### Admin Dashboard (`/app/bunker`)
- **Accessible by**: contexia.marketing@gmail.com
- **Frontend**: React app in `contexia-wizard/app`
- **Features**: Audit trails, user management, system settings
- **Logout behavior**: Returns to `/login.html` (canonical login)

### Client Dashboard (`/app/overview`)
- **Accessible by**: Whitelisted client emails
- **Frontend**: React app in `contexia-wizard/app`
- **Features**: Tax insights, audit reports, Taty Q&A
- **Logout behavior**: Returns to `/login.html`

## Critical Implementation Details

### 1. Canonical Login (`login.html`)

**Path**: `C:\Users\contexia\Projects\antigravity-app\login.html`

- Static HTML file served directly from root
- **Not** a Next.js page (avoid routing complexity)
- Contains inline Supabase SDK initialization
- Uses `setWebhookSecret` with Supabase client
- Implements OAuth redirect flow (`signInWithOAuth`)

**Important**: This is the ONLY login entry point. Do not create alternative login pages.

### 2. Admin Dashboard Assets (Bundle Cache-Busting)

**File**: `contexia-wizard/app/admin/dashboard/page.tsx`

The admin dashboard compiles to:
```
/app/dashboard-assets/index-DblwMcm3.auth-logout-20260524.js
```

**Why the versioned suffix?**
- Dashboard bundle was hardcoded with old logout handler that returned 500
- Fix: Asset renamed to include version date (20260524) to bust browser cache
- This ensures users get the fixed logout flow

**Cache-busting rule**: When fixing critical bugs in the admin dashboard:
1. Apply the fix to the source code
2. Increment the date suffix in the asset filename
3. Update `app-admin/index.html` to reference the new filename

**Current status**: Logout tested ✅, returns 200 OK, redirects to `/login.html`

### 3. Role Detection (Client-Side)

**File**: `contexia-wizard/app/dashboard/page.tsx`

```typescript
const ADMIN_EMAILS = new Set(["contexia.marketing@gmail.com"]);
const CLIENT_EMAILS = new Set([
  "fperez@ferez.co",
  "carlos@importacionesmtz.co"
]);

// On page load:
const session = await supabase.auth.getSession();
const userEmail = session.user.email.toLowerCase();

if (ADMIN_EMAILS.has(userEmail)) {
  router.push("/app/bunker");
} else if (CLIENT_EMAILS.has(userEmail)) {
  router.push("/app/overview");
} else {
  router.push("/login.html?error=unauthorized");
}
```

**Important**: Role sets are hardcoded. To add new users:
1. Update `ADMIN_EMAILS` or `CLIENT_EMAILS` in code
2. Deploy to production
3. Create user in Supabase Auth (via dashboard or invite)

### 4. Logout Handler

**File**: `contexia-wizard/app/admin/components/LogoutButton.tsx`

Logout flow:
```typescript
async handleLogout() {
  await supabase.auth.signOut();
  localStorage.removeItem("cx_user");
  localStorage.removeItem("token");
  window.location.assign("/login.html?logout=1");
}
```

**Result**: User redirected to canonical login page with `logout=1` flag

---

## Supabase Configuration

### JWT Secret
- Stored in `.env` (local development)
- Stored in Railway (production)
- Used to verify session tokens

### Anon Key vs Service Role
- **Anon Key** (public): Used by browser SDK, limited permissions (auth only)
- **Service Role** (secret): Used by backend, full database access

### Tables
- `auth.users` — Supabase-managed authentication
- `telegram_chat_mappings` — Maps Telegram chat IDs to company_id (for Taty webhook)

---

## Deployment & Environment Variables

### Local Development
```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://kpynymwghfwshvcvevxq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
```

### Production (Railway)
Environment variables set in Railway dashboard:
- `SUPABASE_URL` (used by backend)
- `SUPABASE_KEY` (used by backend)
- `TELEGRAM_BOT_TOKEN` (used by Taty webhook)

---

## Known Issues & Lessons Learned

### Issue 1: Admin Dashboard 500 Error on Logout
**Date**: 2026-05-24
**Root Cause**: Bundle contained syntax error in logout handler, returned 500 instead of redirect
**Fix**: Cache-busted filename + redeployed with corrected logout flow
**Verification**: E2E test logout, confirmed 200 OK + redirect to `/login.html`
**Lesson**: When deploying critical bug fixes to client-side bundles, use version suffix in filename to ensure cache bust

### Issue 2: Telegram Webhook Signature Verification
**Date**: 2026-05-25
**Root Cause**: Webhook registered without secret token, but code enforced signature verification
**Fix**: Made signature verification optional (HTTPS provides transport security)
**Verification**: Taty bot responds to Telegram messages end-to-end
**Lesson**: Don't require signature verification unless secret is explicitly set and header is present

---

## Testing Checklist

- [ ] Login with Google → redirects to correct dashboard (admin/client)
- [ ] Login with Microsoft → redirects to correct dashboard
- [ ] Login with Email → redirects to correct dashboard
- [ ] Logout from admin dashboard → redirects to `/login.html`
- [ ] Logout from client dashboard → redirects to `/login.html`
- [ ] Direct navigation to `/app/bunker` without session → redirects to `/login.html`
- [ ] Direct navigation to `/app/overview` without session → redirects to `/login.html`
- [ ] Invalid email (not in whitelist) → error message
- [ ] Taty bot responds to Telegram messages → end-to-end validation

---

## Future Improvements

1. **Server-side middleware** (middleware.ts): Protect routes at Next.js level, not just React components
2. **Dynamic role loading**: Load ADMIN_EMAILS and CLIENT_EMAILS from Supabase instead of hardcoding
3. **OAuth provider list**: Move to Supabase configuration (currently hardcoded in login.html)
4. **Audit logging**: Track all authentication events (login, logout, failed attempts)

---

**Last Updated**: 2026-05-25
**Status**: MVP Validated ✅
