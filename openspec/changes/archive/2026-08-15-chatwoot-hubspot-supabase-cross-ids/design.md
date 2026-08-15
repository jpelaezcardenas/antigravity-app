## Context

`apps/chatwoot-bridge/chatwoot_client.py` already has `set_contact_attributes(contact_id, attrs)` (a PATCH on the contact's own update endpoint — Chatwoot has no dedicated custom-attributes route) and `find_or_create_contact(phone, name)`. `hermes-hubspot-poller` is a separate local process/app (per the existing pattern of independent Hermes-local services — `hermes-manus-poller`, `chatwoot-bridge`, `hermes-hubspot-poller` each own their code, no cross-imports between app directories).

## Goals / Non-Goals

**Goals:**
- Close the identity triangle: given a Chatwoot contact, know its Supabase lead id and HubSpot Contact id.
- Reuse the already-verified Chatwoot instance/credentials, additive only.

**Non-Goals:**
- Not touching `apps/chatwoot-bridge/` — this poller writes to the same Chatwoot instance independently, on its own 5-min cadence, not through the bridge's process.
- Not building the custom-attribute schema from the founder's broader proposal (`tipo_contribuyente`, `lead_score`, etc.) — that's a separate, larger change once this identity link is verified.
- Not two-way — Chatwoot never writes back to Supabase/HubSpot from this attribute.

## Decisions

**1. New minimal Chatwoot client in `hermes-hubspot-poller`, not a shared import from `chatwoot-bridge`.**
The two apps are independent Hermes-local services (same pattern as `hermes-manus-poller`) with no shared package today. Duplicating ~20 lines (find-contact-by-phone, set-attributes) is simpler and safer than introducing a cross-app dependency between two independently-deployed local services for a single reused function.

**2. Find contact by phone (search), never create.**
If no Chatwoot contact exists for a lead's phone, this poller does nothing — a lead should only get cross-reference attributes if the WhatsApp bridge has already talked to them (contact already exists). This poller is not responsible for contact creation; that's the bridge's job (`find_or_create_contact`, triggered by real inbound messages).

**3. Runs after Contact/Deal upsert succeeds, every tick (not gated on first-sync).**
Unlike Notes (Decision #1, `hubspot-activity-value-sync`), setting attributes is idempotent — re-setting the same values every 5 minutes is harmless (no spam, no duplicate object). Simpler to always set than to track "did I already set this."

## Risks / Trade-offs

- **[Risk]** A lead whose phone format differs between `crm_leads.whatsapp_phone` and the Chatwoot contact's stored number won't match. → **Mitigation**: Chatwoot's contact search is already used this way by the bridge (`find_or_create_contact`); same phone-normalization behavior as the existing, working bridge. No new normalization logic introduced.
- **[Risk]** Extra API calls per tick (Chatwoot search + PATCH per lead). → **Mitigation**: trivial at ~15-lead scale, same reasoning as the HubSpot per-tick full sync (`hubspot-sync-renta-natural` Decision #7).
