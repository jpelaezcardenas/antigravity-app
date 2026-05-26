// Create or upgrade a Supabase Auth user with a role in app_metadata.
//
// Usage:
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
//   npx tsx scripts/create-user.ts <email> <password> <role>
//
// Example:
//   npx tsx scripts/create-user.ts growth@contexia.online "MyPass123" cliente
//
// Role must be "admin" or "cliente". If the user already exists, this updates
// the password and app_metadata.role instead of failing.

import { createClient } from "@supabase/supabase-js";

async function main() {
  const [, , email, password, role] = process.argv;

  if (!email || !password || !role) {
    console.error("Usage: tsx create-user.ts <email> <password> <admin|cliente>");
    process.exit(2);
  }
  if (role !== "admin" && role !== "cliente") {
    console.error(`Invalid role "${role}". Must be "admin" or "cliente".`);
    process.exit(2);
  }

  const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !serviceKey) {
    console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars.");
    process.exit(1);
  }

  const admin = createClient(url, serviceKey, { auth: { autoRefreshToken: false, persistSession: false } });

  // Look up existing user.
  const { data: list, error: listErr } = await admin.auth.admin.listUsers({ page: 1, perPage: 200 });
  if (listErr) {
    console.error("listUsers failed:", listErr.message);
    process.exit(1);
  }
  const existing = list.users.find((u) => (u.email || "").toLowerCase() === email.toLowerCase());

  if (existing) {
    const { error } = await admin.auth.admin.updateUserById(existing.id, {
      password,
      app_metadata: { ...existing.app_metadata, role, roles: [role] },
      email_confirm: true,
    });
    if (error) {
      console.error("update failed:", error.message);
      process.exit(1);
    }
    console.log(`✓ Updated existing user ${email} → role=${role}`);
  } else {
    const { error } = await admin.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      app_metadata: { role, roles: [role] },
    });
    if (error) {
      console.error("create failed:", error.message);
      process.exit(1);
    }
    console.log(`✓ Created user ${email} → role=${role}`);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
