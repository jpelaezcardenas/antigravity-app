#!/usr/bin/env python3
"""
Organize a Bitwarden vault into a folder taxonomy by item-name keyword rules.

SAFE BY DEFAULT:
  - Dry-run unless you pass --apply (prints the planned moves, changes nothing).
  - Refuses to run unless BW_SESSION is set (an unlocked session).
  - Idempotent: items already in the right folder are skipped.
  - It NEVER deletes or edits secret values — it only changes each item's folderId.

PREREQUISITES (run these first, in the same shell):
  bw config server https://vault.bitwarden.com
  set BW_CLIENTID=user.<your-id>
  set BW_CLIENTSECRET=<your-current-client-secret>
  bw login --apikey                      (skip if already logged in)
  set BW_PASSWORD=<your-master-password>
  for /f %t in ('bw unlock --passwordenv BW_PASSWORD --raw') do set BW_SESSION=%t

  # ALWAYS take a backup before applying:
  bw export --format encrypted_json --output bitwarden-backup-before-reorg.json --session %BW_SESSION%

USAGE:
  python scripts/organize_bitwarden_folders.py            # dry-run (default)
  python scripts/organize_bitwarden_folders.py --apply    # actually move items

Edit RULES below to change the taxonomy. First matching rule wins, so list the
most specific keywords first. Items matching no rule go to DEFAULT_FOLDER.
"""

import json
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Taxonomy: (folder_name, [keywords]). First match wins. Case-insensitive.
# Folder names use "/" for nested display in the Bitwarden UI.
# ---------------------------------------------------------------------------
RULES = [
    ("Contexia/LLM", [
        "groq", "openai", "gemini", "google ai", "mistral", "cerebras",
        "openrouter", "anthropic", "claude", "deepseek", "huggingface",
        "together", "perplexity", "nemotron", "hermes", "llm",
    ]),
    ("Contexia/Infra/Supabase", ["supabase", "postgres", "database url", "db_url", "database_url"]),
    ("Contexia/Infra/Vercel", ["vercel"]),
    ("Contexia/Infra/Railway", ["railway"]),
    ("Contexia/Channels", [
        "telegram", "taty bot", "meta", "facebook", "instagram",
        "whatsapp", "tiktok", "linkedin",
    ]),
    ("Contexia/Integrations", ["siigo", "dian", "resend", "smtp", "sendgrid", "muisca"]),
    ("Contexia/Auth", ["jwt", "hmac", "webhook secret", "webhook_secret", "secret key", "session secret"]),
    ("Contexia/Accounts", [
        "contexia.online", "contexia.marketing", "growth@contexia",
        "@contexia", "stefamonsalve", "corporate", "cuenta",
    ]),
]

# Items that match no rule are moved here. Set to None to leave them untouched.
DEFAULT_FOLDER = "Personal"

# ---------------------------------------------------------------------------


def run(args, session=None, stdin=None):
    env = {**os.environ}
    if session:
        env["BW_SESSION"] = session
    result = subprocess.run(
        ["bw"] + args,
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"bw {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def target_folder(name: str) -> str | None:
    low = (name or "").lower()
    for folder, keywords in RULES:
        if any(k in low for k in keywords):
            return folder
    return DEFAULT_FOLDER


def ensure_folder(folder_name: str, folders: dict, session: str, apply: bool) -> str | None:
    """Return folderId for folder_name, creating it if needed (only when apply)."""
    if folder_name in folders:
        return folders[folder_name]
    if not apply:
        folders[folder_name] = f"<would-create:{folder_name}>"
        return folders[folder_name]
    template = json.loads(run(["get", "template", "folder"], session))
    template["name"] = folder_name
    encoded = run(["encode"], stdin=json.dumps(template)).strip()
    created = json.loads(run(["create", "folder", encoded], session))
    folders[folder_name] = created["id"]
    print(f"  + created folder: {folder_name}")
    return created["id"]


def main():
    apply = "--apply" in sys.argv
    session = os.environ.get("BW_SESSION")
    if not session:
        print("ERROR: BW_SESSION is not set. Unlock the vault first (see header).")
        sys.exit(1)

    print(f"Mode: {'APPLY (will move items)' if apply else 'DRY-RUN (no changes)'}\n")

    # Existing folders: name -> id
    folders = {f["name"]: f["id"] for f in json.loads(run(["list", "folders"], session)) if f.get("id")}

    items = json.loads(run(["list", "items"], session))
    print(f"Vault has {len(items)} items.\n")

    planned = []  # (name, current_folder_name, target_folder_name)
    id_to_folder = {v: k for k, v in folders.items()}

    for item in items:
        name = item.get("name", "")
        current_id = item.get("folderId")
        current_name = id_to_folder.get(current_id, "(none)")
        tgt = target_folder(name)
        if tgt is None:
            continue
        if current_name == tgt:
            continue
        planned.append((item, name, current_name, tgt))

    if not planned:
        print("Nothing to move — vault already organized. ✅")
        return

    # Group preview by target folder
    by_target = {}
    for _, name, cur, tgt in planned:
        by_target.setdefault(tgt, []).append((name, cur))

    print(f"Planned moves: {len(planned)}\n")
    for tgt in sorted(by_target):
        print(f"  → {tgt}  ({len(by_target[tgt])})")
        for name, cur in by_target[tgt][:12]:
            print(f"        {name}   [from {cur}]")
        if len(by_target[tgt]) > 12:
            print(f"        ... +{len(by_target[tgt]) - 12} more")
    print()

    if not apply:
        print("DRY-RUN complete. Re-run with --apply to perform these moves.")
        return

    # Apply: ensure folders exist, then edit each item's folderId.
    for tgt in by_target:
        ensure_folder(tgt, folders, session, apply=True)

    moved = 0
    for item, name, cur, tgt in planned:
        item["folderId"] = folders[tgt]
        encoded = run(["encode"], stdin=json.dumps(item)).strip()
        run(["edit", "item", item["id"], encoded], session)
        moved += 1
        if moved % 25 == 0:
            print(f"  moved {moved}/{len(planned)}...")

    run(["sync"], session)
    print(f"\nDone. Moved {moved} items. ✅")


if __name__ == "__main__":
    main()
