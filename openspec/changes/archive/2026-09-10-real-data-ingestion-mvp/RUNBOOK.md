# Runbook — activating real-data ingestion

Everything in this file requires credentials or console access that no agent has. Until these
are done the feature is **inert by design**, not broken: the pollers exit without side effects
and the internal endpoints return 503.

Order matters: step 1 unblocks Tracks 2 and 3 at once.

---

## 1. `INTERNAL_API_KEY` — unblocks both pollers

Generate a random value (never reuse another secret):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set it in **three** places, identical value:

| Where | Why |
|---|---|
| Railway → `antigravity-app` → Variables | The backend compares against it |
| `apps/hermes-siigo-poller/.env` | Siigo poller authenticates with it |
| `apps/hermes-gmail-poller/.env` | Gmail poller authenticates with it |

Store it in Bitwarden. Never commit it.

**Verify:** `/internal/siigo-sync/run` should stop returning 503.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"tenant_id":"probe"}' https://antigravity-app-production-175a.up.railway.app/internal/siigo-sync/run
```

`503` = key still unset · `401` = key set, yours is wrong · `404` = **working** (authenticated, tenant just has no Siigo credentials).

---

## 2. Migration `0046_gmail_sender_map.sql` — required by Track 3

**Confirmed not applied** (checked live against the Supabase Management API: 47 migrations
present, none of them this one).

Apply via the Supabase SQL Editor (project `kpynymwghfwshvcvevxq`), pasting
`apps/backend/migrations/0046_gmail_sender_map.sql`.

Then map each client that will email attachments:

```sql
INSERT INTO gmail_sender_map (sender_email, tenant_id, notes)
VALUES ('facturacion@cliente.com', '<tenant-uuid>', 'Cliente X — facturas mensuales');
```

Until a sender is mapped, their mail is skipped and left **unlabeled**, so it ingests
automatically on a later tick once you add the row. No replay needed.

---

## 3. Siigo — `SIIGO_PARTNER_ID` is a blocker, not a nice-to-have

**This value is unknown.** The plan said `contexiaFinancialOS`; the first implementation used
`contexia-financial-os`. Nothing in the repo documents either, so both are guesses and the code
now refuses to send one.

Get the real Partner-Id from Siigo's partner console / your Siigo integration contact, then in
Railway set:

```
SIIGO_PARTNER_ID = <value Siigo issued>
```

Per client with Siigo, also set (UUID uppercased, dashes → underscores):

```
SIIGO_USERNAME_<TENANT_UUID>   = usuario@empresa.com
SIIGO_ACCESS_KEY_<TENANT_UUID> = <access_key from the client's Siigo>
```

> The `access_key` is **not** the client's password. It is generated in Siigo under
> *Configuración → API*. Ask the client for the access key only — never for their password.

Then in `apps/hermes-siigo-poller/.env`:

```
SIIGO_ELIGIBLE_TENANTS=<uuid1>,<uuid2>
```

**Verify before touching production data:**

```bash
python apps/hermes-siigo-poller/main.py --dry-run
```

---

## 4. Gmail OAuth — Track 3

1. Google Cloud Console → APIs & Services → **enable the Gmail API**
2. Credentials → Create → **OAuth client ID** → type **Desktop app**
3. Download the JSON as `apps/hermes-gmail-poller/credentials.json` (gitignored)
4. Fill `apps/hermes-gmail-poller/.env`:
   ```
   INTERNAL_API_KEY=<same as step 1>
   SUPABASE_URL=<project url>
   SUPABASE_SERVICE_ROLE_KEY=<service role key>
   GMAIL_INBOX_ADDRESS=<Taty's address>
   ```
5. Run once **interactively** to complete the consent flow (it opens a browser):
   ```bash
   python apps/hermes-gmail-poller/main.py --dry-run
   ```
   This writes `token.json` beside the poller. Later runs refresh it silently.

---

## 5. Register the scheduled tasks

```powershell
.\apps\hermes-siigo-poller\register_poller_task.ps1   # nightly 02:00
.\apps\hermes-gmail-poller\register_poller_task.ps1   # every 15 min
```

Both trigger `AtLogOn` — they run only while you are logged in. That is deliberate (no stored
Windows credential), matching the HubSpot poller and chatwoot-bridge.

---

## 6. Stage 11 close-out — still open

- [ ] Identify the pilot clients (query in the plan; still never run — we do not yet know *which*
      tenants this is for)
- [ ] Upload a real CSV from `/app/overview` with a client login, confirm rows land with
      `is_verified_real = true` **and the client's own `tenant_id`**
- [ ] Upload a DIAN XML and confirm the derived entry balances
- [ ] `openspec/changes/real-data-ingestion-mvp/reports/YYYY-MM-DD-deployment.md`
- [ ] Archive the change

The end-to-end upload test is the one thing no agent could verify: it needs a real client JWT.
Parser correctness is covered by tests running against production-pinned dependency versions.
