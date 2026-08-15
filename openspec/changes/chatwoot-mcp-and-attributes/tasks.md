## 1. Scaffold `contexia-mcp-servers/chatwoot/`

- [x] 1.1 Mirror `railway/`'s layout: `pyproject.toml`, `chatwoot_mcp/{__init__.py, __main__.py, client.py, server.py}`, `.env.example`, `.gitignore`, `README.md`
- [x] 1.2 `client.py`: thin async REST client reading `CHATWOOT_URL`, `CHATWOOT_ACCOUNT_ID`, `CHATWOOT_API_TOKEN` (required) and `CHATWOOT_ADMIN_TOKEN` (optional, for the one admin-only tool) from a local `.env`, same `_load_dotenv()` pattern as `railway/client.py`. Raises `ChatwootError` with an actionable message on missing config, 401/403, or HTTP errors — mirrors `RailwayError`.

## 2. Read tools

- [x] 2.1 `chatwoot_list_conversations(status?, inbox_id?, limit?)` — list conversations, optionally filtered
- [x] 2.2 `chatwoot_get_conversation_messages(conversation_id, limit?)` — message history for one conversation
- [x] 2.3 `chatwoot_search_contacts(query)` — find a contact by phone/name/email
- [x] 2.4 `chatwoot_get_conversation_labels(conversation_id)`

## 3. Write tools

- [x] 3.1 `chatwoot_set_contact_attributes(contact_id, attributes)` — PATCH custom_attributes on a contact
- [x] 3.2 `chatwoot_set_conversation_attributes(conversation_id, attributes)` — PATCH custom_attributes on a conversation
- [x] 3.3 `chatwoot_add_labels(conversation_id, labels)`
- [x] 3.4 `chatwoot_send_reply(conversation_id, text, private=False)` — reuses the same `outgoing`/`private` shape `apps/chatwoot-bridge/chatwoot_client.py::send_reply` already uses in production
- [x] 3.5 `chatwoot_create_custom_attribute_definition(...)` — requires `CHATWOOT_ADMIN_TOKEN`; raises a clear, named error (not a bare 403) when that env var is unset

## 4. Register + verify

- [x] 4.1 Build/install into a venv the same way `railway/` is installed, add `chatwoot` entry to `Projects/.mcp.json`
- [x] 4.2 Live smoke test against the real local Chatwoot (account `2`), all 9 tools exercised: `list_conversations` (3 results), `search_contacts` (found the real test contact), `get_conversation_messages`, `get_conversation_labels`, `set_conversation_attributes` (write did not raise), `set_contact_attributes` round-tripped (write → re-read confirmed `ok` → reverted), `add_labels` round-tripped (added `mcp_smoke_test` → read back → reverted to empty), and `create_custom_attribute_definition` without `CHATWOOT_ADMIN_TOKEN` raised the expected named error rather than a bare 403 — confirms the Decision #2 error-handling design works. `send_reply` was NOT live-tested (would have sent/attempted a real customer-visible or private message on a live conversation) — its request shape is a direct copy of `apps/chatwoot-bridge/chatwoot_client.py::send_reply`, already proven correct in production all night.
      Blocker found and fixed along the way: `pyproject.toml`'s unpinned `mcp>=1.2.0` resolved to `mcp==2.0.0`, which removed `mcp.server.fastmcp` (the import `server.py` and the sibling `railway_mcp` both depend on). Pinned to `mcp==1.27.2` (the exact version `railway/`'s working venv uses) and reinstalled with dependencies — fixed.
- [x] 4.3 Founder supplied `CHATWOOT_ADMIN_TOKEN` (his own account, `jpelaezcardenas@gmail.com`, confirmed via `GET /profile` -> `role: administrator` — already an Administrator, no privilege escalation of Taty Bot was needed). Stored in `contexia-mcp-servers/chatwoot/.env`.
- [x] 4.4 Provisioned the full attribute schema from design.md Decision #5 via `chatwoot_create_custom_attribute_definition` (the MCP's own tool, used for real): 9/9 contact-level + 7/7 conversation-level = 16/16 created. Verified live via `GET /custom_attribute_definitions`: all 16 keys present with the correct `attribute_model` split (9 contact_attribute, 7 conversation_attribute).

## 5. Deploy

- N/A — this MCP server runs local-only (same machine as Hermes/the Chatwoot bridge/Docker), same sovereignty principle as `ARCHITECTURE.md` decisions #1/#10. No Railway/Vercel deploy applies. "Deployed" here means: registered in `Projects/.mcp.json` and confirmed reachable by Claude Code (task 4.2).
