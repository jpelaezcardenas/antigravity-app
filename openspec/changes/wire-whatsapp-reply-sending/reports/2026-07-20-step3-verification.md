# Step 3 verification — wire-whatsapp-reply-sending

Date: 2026-07-20

## Test results

Full targeted suite, 61/61 green, zero regression:

```
tests/test_whatsapp_endpoints.py ......... (9, incl. 3 new)
tests/test_whatsapp_channel.py
tests/test_taty_lead_router.py
```

## Scope of the change

`presentation/whatsapp_endpoints.py`: `whatsapp_webhook`'s text-message branch now sends
`route_lead_message`'s computed `reply` via `send_whatsapp_message(event["account_id"], reply)`,
mirroring the existing pattern `route_lead_document` already uses internally for the RUT/extractos
flow. The document/media branch is unaffected — confirmed by a dedicated regression test that
`send_whatsapp_message` is NOT called directly from the handler for media events (since
`route_lead_document` already sends internally).

## No migration, no new endpoint, no flag change

Reuses `WHATSAPP_CANONICAL`, already live.
