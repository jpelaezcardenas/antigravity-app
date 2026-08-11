# Taty WhatsApp Campaign — Runbook for Manus

This is the operational reference for running the declaración-de-renta-persona-natural WhatsApp
campaign through Taty. No Chatwoot/WhatsApp runbook existed before this document
(taty-whatsapp-renta-sales-capability) — the operational knowledge previously lived only in commit
messages and `openspec/changes/` prose.

## The link and attribution

- Customer entry point: `https://wa.me/573106229289` (or `wa.me/573106229289?text=...` to
  pre-fill an opening message).
- This is **inbound-first by design**: the customer messages first, which opens WhatsApp's 24h
  service window and lets Taty reply in free-form text with no approved template and no effect on
  the business-initiated-conversation cap (see Limits below).
- **Attribution convention**: append a distinct pre-filled `?text=` per content piece (e.g. a
  specific Instagram post vs. a specific landing page) so replies can be traced back to what
  drove them. Do not reuse the same pre-filled text across two different pieces of content — it
  makes attribution ambiguous. There is no dashboard for this yet; attribution today means reading
  the first message's exact text in Chatwoot.

## Real limits

- **Inbound has no practical cap.** A customer messaging first is never a "business-initiated
  conversation" and does not count against Meta's messaging limit tier.
- **250 business-initiated conversations / 24h** applies only if Contexia messages someone first
  (cold outreach, re-engagement after the 24h window closes). This campaign does not do that today
  — it is 100% inbound. This cap only becomes relevant once Meta Business Verification (tasks.md
  6.2, founder-owned, not yet done) raises it and outbound/re-engagement becomes part of the
  campaign.
- **No approved marketing template exists yet** beyond Meta's default `hello_world` (English).
  Re-engaging a lead whose 24h window has closed is not possible today — that requires an
  approved `es_CO` template (tasks.md 6.4, founder-owned).

## What Taty can and cannot say

- Taty is Contexia — **Entidad B**, the technology layer. She never claims to be a firma contable,
  never states she is signing or certifying a declaración. See `.antigravity/GROUND_TRUTH.md`.
- **Taty never states a price.** Pricing tiers (asalariado vs. independiente/freelancer) are
  undefined as of this change — deferred to a follow-up conversation with the founder. If a lead
  asks the price, Taty says a Contexia advisor will confirm it for their specific case. Do not
  treat any number Taty states in a screenshot as real without checking `crm_service.py`'s
  `RENTA_NATURAL_PRICE_CENTS` (currently a flat $89.000 COP, unrelated to any tier discussion).
- **Taty never states a specific contact email, phone, or website** — none is configured, and
  earlier testing (2026-08-11) confirmed the model fabricates plausible-looking ones if not
  explicitly told not to. If this ever appears in a real conversation, it is a regression — flag
  it, don't correct the customer's expectation by hand.
- Taty grounds fiscal figures (UVT, Art. 592 thresholds, plazos) in the knowledge base
  (`knowledge_chunks`, `client_id='__global__'`) rather than the model's own training data — the
  KB is the source of truth for anything cited as fact. See KB health below.

## Where leads land

- **Chatwoot**: account 2, inbox `1` ("Taty Contadora Amiga 24/7", `Channel::Whatsapp`, the real
  Meta-linked inbox as of taty-whatsapp-renta-sales-capability Stage 5). Inbox `3`
  (`Channel::Api`) is a test/injection-only channel with no Meta credentials — it cannot deliver
  to a real phone. Never point the bridge at inbox `3` for real traffic.
- **`crm_leads`** (Supabase): one row per WhatsApp phone number, keyed by `whatsapp_phone`, staged
  `NUEVOS → PROSPECTOS → POR_APROBAR → LISTOS_CONTADORA`. `crm_tax_profiles` holds detected persona
  fields (`es_asalariado`, `topes`, `obligado_declarar` — a preliminary signal, not a legal
  determination).

## Human handover

- Tag a Chatwoot conversation with the `bot_off` label to pause Taty's automated replies —
  verified working (`test_webhook_filter.py::test_bot_off_label_pauses_processing`).
- A human's reply typed directly in a Chatwoot conversation under inbox `1` reaches the customer's
  real WhatsApp (this specifically did NOT work under inbox `3` before Stage 5 — inbox `3` had no
  way to deliver a human's reply at all).

## The Wompi payment gate (do not bypass)

- When a lead expresses sales interest, Taty **never** sends a real payment link automatically. A
  draft (`draft_type="wompi_payment_link"`) lands in `approval_queue` and a human must approve it
  (`ApprovalQueueService.approve_draft`) before a real Wompi checkout link is generated and sent.
- This exists because of a real incident: an earlier version of this flow sent a live,
  production Wompi link with zero human review, and the account behind it belongs to Contexia
  (Entidad B), not the regulated accounting firm — see `taty-wompi-link-hitl-gate`. Do not
  re-automate this without the founder's explicit sign-off on which entity's Wompi account is
  correct to use.

## KB health (check this if Taty's answers seem generic or wrong)

Taty's retrieval has two backends: **pgvector** (Supabase `knowledge_chunks`, 84 chunks as of this
change — the real, current content) and an **in-memory fallback** (only the original 48-chunk
`dian_chunks.json`, loaded once at process start, **not synced with pgvector**). Any transient
pgvector/embedding failure silently degrades every answer to the smaller, staler in-memory pool
with no visible error to the customer or the operator. Known trigger: Gemini's free embedding
tier has a real daily quota (confirmed exhausted 2026-08-11 by this session's own testing volume)
— if `OPENAI_API_KEY` (the primary provider) has no credits, Gemini is the only fallback and it
can run out too. Check via:

```sql
select count(*), count(embedding) from knowledge_chunks;
```

Both numbers should match and be > 0 (84 as of this writing). If Taty's answers start reading as
generic/less grounded, this silent-degradation path is the first thing to check, not a KB
content problem.

## Bringing the local stack up

The bridge and Chatwoot run **locally, on the founder's machine** — never on Railway/Vercel (data
sovereignty, same principle as Hermes — see `ARCHITECTURE.md` decision #1).

```bash
docker compose -f docker-compose.chatwoot.yml up -d
```

The bridge runs as the Windows Scheduled Task `ContexiaChatwootBridge` (auto-starts at logon,
1-minute watchdog trigger — see `apps/chatwoot-bridge/register_bridge_task.ps1`).

**Important operational gotcha (found live 2026-08-11):** `Stop-ScheduledTask` /
`Start-ScheduledTask` does **not** reliably restart the bridge after a deliberate config change
(e.g. editing `.env`). The watchdog's own self-check (`run_bridge.ps1`) exits immediately as a
no-op whenever *something* already answers on port 8090 — it cannot tell a healthy fresh process
from a healthy stale one still running the old config in memory. To force a real restart after
changing `.env`:

```powershell
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
  Where-Object { $_.CommandLine -like "*uvicorn*main:app*" } |
  Select-Object ProcessId, CreationDate

Stop-Process -Id <the PID above> -Force
Start-ScheduledTask -TaskName "ContexiaChatwootBridge"
```

Confirm it actually restarted by checking the new process's `CreationDate` and
`http://localhost:8090/` returns `{"status":"ok",...}`.
