# T10: Railway Environment Variables Setup

**Status:** Ready for execution  
**Owner:** Infra Team  
**Timeline:** 20 minutes  
**Blocker:** T6 complete (API validation done)

---

## Step 1: Store Bitwarden Credentials in Bitwarden Vault

Create a new item in Bitwarden for your API keys.

### Location in Bitwarden:
- **Workspace:** Contexia
- **Folder:** `Zona CONTEXIA (AAA) /Infraestructura – Root`
- **Item Name:** `Bitwarden API Keys`

### How to Create (Manual in Bitwarden Web):

1. Go to https://vault.bitwarden.com
2. Click **+ New Item** → **Login**
3. Fill in:
   ```
   Name: Bitwarden API Keys
   Folder: Zona CONTEXIA (AAA) /Infraestructura – Root
   Username: <your BW_CLIENT_ID>
   Password: <your BW_CLIENT_SECRET>
   ```
4. **Save**

### Or Create via bw CLI:

```bash
# Create the item
bw create item '{
  "type": 1,
  "name": "Bitwarden API Keys",
  "folderId": "809bc02e-6d2e-4763-a272-b46a01408f1d",
  "login": {
    "username": "YOUR_BW_CLIENT_ID_HERE",
    "password": "YOUR_BW_CLIENT_SECRET_HERE"
  }
}'
```

---

## Step 2: Create `.env.local` (Never Commit)

```bash
# Copy template
cp .env.example .env.local

# Edit locally (nano, vim, VS Code, etc.)
# Replace all REPLACE_WITH_VALUE_FROM_BITWARDEN with actual values
```

### To Extract Values from Bitwarden:

```bash
# Get BW_CLIENT_ID
bw get item "Bitwarden API Keys" | jq -r '.login.username'

# Get BW_CLIENT_SECRET
bw get item "Bitwarden API Keys" | jq -r '.login.password'

# Get BW_MASTER_PASSWORD
bw get item "Bitwarden Master Password" | jq -r '.login.password'
```

---

## Step 3: Set Railway Environment Variables

### Option A: Using Railway CLI (Recommended)

```bash
# Login to Railway
railway login

# Link to antigravity-app project
railway link

# Set each variable
railway variables set SECRETS_BACKEND=bitwarden
railway variables set BW_VAULT_URL=https://vault.bitwarden.com
railway variables set BW_CLIENT_ID=$(bw get item "Bitwarden API Keys" | jq -r '.login.username')
railway variables set BW_CLIENT_SECRET=$(bw get item "Bitwarden API Keys" | jq -r '.login.password')
railway variables set BW_MASTER_PASSWORD=$(bw get item "Bitwarden Master Password" | jq -r '.login.password')

# Verify
railway variables list
```

### Option B: Using Railway Web Dashboard

1. Go to https://railway.app
2. Select **antigravity-app** project
3. Select **backend-production** service
4. Click **Variables**
5. Add each variable:
   - `SECRETS_BACKEND` = `bitwarden`
   - `BW_VAULT_URL` = `https://vault.bitwarden.com`
   - `BW_CLIENT_ID` = `<from Bitwarden>`
   - `BW_CLIENT_SECRET` = `<from Bitwarden>`
   - `BW_MASTER_PASSWORD` = `<from Bitwarden>`

---

## Step 4: Verify Variables (Before Deploy)

```bash
# Check that all variables are set
railway variables list

# Should show:
# SECRETS_BACKEND=bitwarden ✓
# BW_VAULT_URL=https://vault.bitwarden.com ✓
# BW_CLIENT_ID=<masked> ✓
# BW_CLIENT_SECRET=<masked> ✓
# BW_MASTER_PASSWORD=<masked> ✓
```

---

## Step 5: Git Commit (Log-Only, No Secrets)

```bash
git add .env.example T10-RAILWAY-ENV-SETUP.md

git commit -m "docs: T10 railway env vars configured securely

- Bitwarden credentials stored in vault (Infraestructura folder)
- .env.example template created (no secrets)
- .env.local in .gitignore (never committed)
- Railway variables set via CLI
- All values masked in dashboard

OpenSpec change: keeper-migration-2026-06-15"
```

---

## Troubleshooting

### If railway CLI doesn't recognize variables:

```bash
# Log out and log back in
railway logout
railway login

# Try again
railway variables set SECRETS_BACKEND=bitwarden
```

### If `bw get item` fails:

```bash
# Verify you're logged in
bw status

# Sync vault
bw sync

# Try again
bw get item "Bitwarden API Keys"
```

### If item doesn't exist in Bitwarden:

Create it manually via https://vault.bitwarden.com using Step 1 above.

---

## Next Steps

- ✅ T10 complete: Variables set in Railway
- ⏳ T11: Staging deploy (verify health check)
- ⏳ T12: Production deploy (Stage 11)
- ⏳ T13: Health audits
- ⏳ T14: Delete Keeper

---

**Execution Time:** 20 minutes  
**Effort:** Low (mostly CLI commands)  
**Risk:** Medium (env vars are sensitive, but masked in Dashboard)
