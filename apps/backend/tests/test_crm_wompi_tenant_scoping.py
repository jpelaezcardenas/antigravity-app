"""Tests confirming tenant scoping for the Wompi checkout/webhook flow cannot be
spoofed by caller input (change wompi-payment-integration, task 5.1).

crm_service uses the service-role Supabase client everywhere (no per-request
end-user session — see crm_service.py's module docstring), so DB-level RLS is
defense-in-depth, not the live access control. The property that actually
matters at this layer: tenant_id is always sourced from the lead's own DB row,
never accepted as caller input, and the webhook payload never contains a
tenant_id key that could let an attacker reassign a transaction to a
different tenant via upsert.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

from services.crm_service import CrmService
from services.wompi_signature import compute_event_checksum


def _patched_env():
    return patch(
        "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
    )


def _patched_wompi_settings():
    return patch.multiple(
        "config.settings",
        WOMPI_PUBLIC_KEY="pub_test_x",
        WOMPI_INTEGRITY_SECRET="test_integrity_x",
    )


class TestCheckoutTenantScoping:
    def test_checkout_signature_has_no_tenant_id_parameter(self):
        # A caller cannot pass a tenant_id to checkout_lead_payment at all —
        # the only way tenant_id reaches the inserted row is via the lead's
        # own DB record, fetched by lead_id.
        params = inspect.signature(CrmService.checkout_lead_payment).parameters
        assert "tenant_id" not in params

    def test_inserted_transaction_tenant_id_comes_from_the_leads_own_row(self):
        client = MagicMock()
        inserted = {}

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data={"id": "l1", "tenant_id": "tenant-owned-by-l1"}
                )
            elif name == "crm_wompi_transactions":
                def _insert(payload):
                    inserted.update(payload)
                    r = MagicMock()
                    r.execute.return_value = MagicMock(data=[payload])
                    return r
                m.insert.side_effect = _insert
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_wompi_settings():
            CrmService().checkout_lead_payment("l1")

        assert inserted["tenant_id"] == "tenant-owned-by-l1"


class TestWebhookTenantScoping:
    def test_webhook_upsert_payload_never_contains_tenant_id(self):
        # If the upsert payload included tenant_id, a forged (but validly
        # signed, e.g. replayed for a different reference) event could
        # reassign a transaction to a different tenant. It must not.
        secret = "test_events_x"
        event = {
            "data": {
                "transaction": {
                    "id": "wompi-txn-1",
                    "status": "APPROVED",
                    "amount_in_cents": 8_900_000,
                    "reference": "lead-l1-123",
                }
            },
            "signature": {
                "properties": ["transaction.id", "transaction.status", "transaction.amount_in_cents"],
                "checksum": "",
            },
            "timestamp": 1719000000,
        }
        event["signature"]["checksum"] = compute_event_checksum(event, secret)

        client = MagicMock()
        captured = {}

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_wompi_transactions":
                def _update(payload):
                    captured.update(payload)
                    inner = MagicMock()
                    r = MagicMock()
                    r.execute.return_value = MagicMock(data=[payload])
                    inner.eq.return_value = r
                    return inner
                m.update.side_effect = _update
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), patch.object(
            __import__("config").settings, "WOMPI_EVENTS_SECRET", secret
        ):
            CrmService().handle_wompi_webhook(event)

        assert "tenant_id" not in captured
