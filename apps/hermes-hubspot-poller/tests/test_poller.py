"""Tests for the Hermes->HubSpot sync poller.

All network access is mocked; no credentials are needed to run these. Covers the load-bearing
safety properties:
  - unconfigured node touches nothing (fail closed)
  - a new lead creates a Contact + Deal and persists the returned ids (idempotency key)
  - an already-synced lead is upserted (PATCH by stored id), never duplicated
  - stage mapping resolves correctly, including the Wompi-status override
  - b2b_clients sync NEVER creates a Deal
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import hubspot_client  # noqa: E402
import poller  # noqa: E402
import supabase_client  # noqa: E402
from config import settings  # noqa: E402
from stage_mapping import resolve_dealstage  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch):
    monkeypatch.setattr(settings, "DRY_RUN", False)
    monkeypatch.setattr(settings, "MAX_RECORDS_PER_TICK", 50)
    monkeypatch.setattr(settings, "HUBSPOT_DEAL_PIPELINE", "default")
    yield


def _lead(
    lead_id="lead-1",
    stage="NUEVOS",
    hubspot_contact_id=None,
    hubspot_deal_id=None,
    full_name="Jane Doe",
    last_message=None,
):
    return {
        "id": lead_id,
        "full_name": full_name,
        "email": "jane@example.com",
        "whatsapp_phone": "+573000000000",
        "stage": stage,
        "hubspot_contact_id": hubspot_contact_id,
        "hubspot_deal_id": hubspot_deal_id,
        "last_message": last_message,
    }


def _b2b_client(client_id="client-1", hubspot_company_id=None):
    return {
        "id": client_id,
        "contact_name": "Acme SAS",
        "phone": "+573000000001",
        "hubspot_company_id": hubspot_company_id,
    }


# --------------------------------------------------------------------------- stage mapping


class TestStageMapping:
    def test_stage_maps_to_expected_dealstage(self):
        assert resolve_dealstage("NUEVOS") == "appointmentscheduled"
        assert resolve_dealstage("PROSPECTOS") == "qualifiedtobuy"
        assert resolve_dealstage("POR_APROBAR") == "presentationscheduled"
        assert resolve_dealstage("LISTOS_CONTADORA") == "decisionmakerboughtin"

    def test_approved_wompi_transaction_overrides_to_closedwon(self):
        assert resolve_dealstage("NUEVOS", wompi_status="APPROVED") == "closedwon"

    def test_declined_wompi_transaction_overrides_to_closedlost(self):
        assert resolve_dealstage("LISTOS_CONTADORA", wompi_status="DECLINED") == "closedlost"

    def test_pending_wompi_transaction_does_not_override(self):
        assert resolve_dealstage("PROSPECTOS", wompi_status="PENDING") == "qualifiedtobuy"

    def test_unknown_stage_falls_back_to_nuevos_mapping(self):
        assert resolve_dealstage("SOMETHING_UNEXPECTED") == "appointmentscheduled"


# --------------------------------------------------------------------------- hubspot client


class TestHubspotClientNotesAndTasks:
    def test_create_note_without_token_makes_no_http_call(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "")
        with patch("hubspot_client.httpx.post") as mock_post:
            assert hubspot_client.create_note("contact-1", "hello") is None
        mock_post.assert_not_called()

    def test_create_note_posts_with_contact_association(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        response = MagicMock(status_code=201)
        response.json.return_value = {"id": "note-1"}
        with patch("hubspot_client.httpx.post", return_value=response) as mock_post:
            result = hubspot_client.create_note("contact-1", "hola desde WhatsApp")

        assert result == "note-1"
        url, kwargs = mock_post.call_args[0][0], mock_post.call_args.kwargs
        assert url.endswith("/crm/v3/objects/notes")
        body = kwargs["json"]
        assert body["properties"]["hs_note_body"] == "hola desde WhatsApp"
        assoc = body["associations"][0]
        assert assoc["to"]["id"] == "contact-1"

    def test_create_note_never_raises_on_network_error(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        with patch("hubspot_client.httpx.post", side_effect=Exception("boom")):
            assert hubspot_client.create_note("contact-1", "x") is None

    def test_has_open_task_without_token_makes_no_http_call(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "")
        with patch("hubspot_client.httpx.get") as mock_get:
            assert hubspot_client.has_open_task("deal-1") is False
        mock_get.assert_not_called()

    def test_has_open_task_true_when_incomplete_task_associated(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        assoc_response = MagicMock(status_code=200)
        assoc_response.json.return_value = {"results": [{"id": "task-1"}]}
        batch_response = MagicMock(status_code=200)
        batch_response.json.return_value = {
            "results": [{"id": "task-1", "properties": {"hs_task_status": "NOT_STARTED"}}]
        }
        with patch("hubspot_client.httpx.get", return_value=assoc_response), patch(
            "hubspot_client.httpx.post", return_value=batch_response
        ):
            assert hubspot_client.has_open_task("deal-1") is True

    def test_has_open_task_false_when_only_completed_tasks(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        assoc_response = MagicMock(status_code=200)
        assoc_response.json.return_value = {"results": [{"id": "task-1"}]}
        batch_response = MagicMock(status_code=200)
        batch_response.json.return_value = {
            "results": [{"id": "task-1", "properties": {"hs_task_status": "COMPLETED"}}]
        }
        with patch("hubspot_client.httpx.get", return_value=assoc_response), patch(
            "hubspot_client.httpx.post", return_value=batch_response
        ):
            assert hubspot_client.has_open_task("deal-1") is False

    def test_has_open_task_false_when_no_associated_tasks(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        assoc_response = MagicMock(status_code=200)
        assoc_response.json.return_value = {"results": []}
        with patch("hubspot_client.httpx.get", return_value=assoc_response), patch(
            "hubspot_client.httpx.post"
        ) as mock_post:
            assert hubspot_client.has_open_task("deal-1") is False
        mock_post.assert_not_called()

    def test_has_open_task_false_on_network_error(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        with patch("hubspot_client.httpx.get", side_effect=Exception("boom")):
            assert hubspot_client.has_open_task("deal-1") is False

    def test_create_task_posts_with_deal_association(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        response = MagicMock(status_code=201)
        response.json.return_value = {"id": "task-1"}
        with patch("hubspot_client.httpx.post", return_value=response) as mock_post:
            result = hubspot_client.create_task("deal-1", "Aprobar pago")

        assert result == "task-1"
        url, kwargs = mock_post.call_args[0][0], mock_post.call_args.kwargs
        assert url.endswith("/crm/v3/objects/tasks")
        assert kwargs["json"]["properties"]["hs_task_subject"] == "Aprobar pago"
        assert kwargs["json"]["associations"][0]["to"]["id"] == "deal-1"


class TestHubspotClient:
    def test_is_configured_reflects_the_access_token(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "")
        assert hubspot_client.is_configured() is False
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        assert hubspot_client.is_configured() is True

    def test_upsert_contact_without_token_makes_no_http_call(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "")
        with patch("hubspot_client.httpx.post") as mock_post:
            assert hubspot_client.upsert_contact(None, {}) is None
        mock_post.assert_not_called()

    def test_upsert_contact_posts_when_no_existing_id(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        response = MagicMock(status_code=201)
        response.json.return_value = {"id": "hs-contact-1"}
        with patch("hubspot_client.httpx.post", return_value=response) as mock_post:
            result = hubspot_client.upsert_contact(None, {"email": "a@b.com"})
        assert result == "hs-contact-1"
        assert mock_post.call_args[0][0].endswith("/crm/v3/objects/contacts")

    def test_upsert_contact_patches_when_existing_id(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        response = MagicMock(status_code=200)
        response.json.return_value = {"id": "hs-contact-1"}
        with patch("hubspot_client.httpx.patch", return_value=response) as mock_patch:
            result = hubspot_client.upsert_contact("hs-contact-1", {"email": "a@b.com"})
        assert result == "hs-contact-1"
        assert mock_patch.call_args[0][0].endswith("/crm/v3/objects/contacts/hs-contact-1")

    def test_upsert_never_raises_on_network_error(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        with patch("hubspot_client.httpx.post", side_effect=Exception("boom")):
            assert hubspot_client.upsert_contact(None, {}) is None

    def test_upsert_creates_fresh_object_when_stored_id_is_stale(self, monkeypatch):
        """Regression test for the live bug found 2026-08-15: HubSpot's own dedup/merge can
        retire a previously-synced Contact's id; a PATCH 404 must self-heal, not fail closed."""
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        from unittest.mock import MagicMock

        patch_response = MagicMock(status_code=404)
        patch_response.text = '{"message":"resource not found"}'
        post_response = MagicMock(status_code=201)
        post_response.json.return_value = {"id": "hs-contact-new"}
        with patch("hubspot_client.httpx.patch", return_value=patch_response), patch(
            "hubspot_client.httpx.post", return_value=post_response
        ) as mock_post:
            result = hubspot_client.upsert_contact("hs-contact-stale", {"email": "a@b.com"})

        assert result == "hs-contact-new"
        assert mock_post.call_args[0][0].endswith("/crm/v3/objects/contacts")


# --------------------------------------------------------------------------- tick


class TestRunTick:
    def test_unconfigured_node_touches_nothing(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "")
        monkeypatch.setattr(settings, "SUPABASE_URL", "")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
        with patch("supabase_client.list_leads") as mock_leads, patch(
            "supabase_client.list_b2b_clients"
        ) as mock_clients:
            summary = poller.run_tick()
        assert summary["skipped"] == 1
        mock_leads.assert_not_called()
        mock_clients.assert_not_called()

    def test_new_lead_creates_contact_and_deal_and_persists_ids(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead()]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("supabase_client.get_latest_wompi_transaction", return_value=None), patch(
            "hubspot_client.upsert_contact", return_value="hs-contact-1"
        ) as mock_contact, patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ) as mock_deal, patch(
            "supabase_client.mark_lead_synced", return_value=True
        ) as mock_mark:
            summary = poller.run_tick()

        assert summary["leads_synced"] == 1
        mock_contact.assert_called_once_with(None, {
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane@example.com",
            "phone": "+573000000000",
        })
        mock_deal.assert_called_once()
        assert mock_deal.call_args[0][0] is None
        mock_mark.assert_called_once()
        assert mock_mark.call_args[0][0] == "lead-1"
        assert mock_mark.call_args[0][1] == "hs-contact-1"
        assert mock_mark.call_args[0][2] == "hs-deal-1"

    def test_already_synced_lead_is_upserted_by_stored_id_not_duplicated(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        existing_lead = _lead(hubspot_contact_id="hs-contact-1", hubspot_deal_id="hs-deal-1")
        with patch("supabase_client.list_leads", return_value=[existing_lead]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("supabase_client.get_latest_wompi_transaction", return_value=None), patch(
            "hubspot_client.upsert_contact", return_value="hs-contact-1"
        ) as mock_contact, patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ) as mock_deal, patch("supabase_client.mark_lead_synced", return_value=True):
            poller.run_tick()

        assert mock_contact.call_args[0][0] == "hs-contact-1"
        assert mock_deal.call_args[0][0] == "hs-deal-1"

    def test_lead_dealstage_uses_wompi_override_when_present(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead(stage="PROSPECTOS")]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch(
            "supabase_client.get_latest_wompi_transaction", return_value={"status": "APPROVED"}
        ), patch("hubspot_client.upsert_contact", return_value="hs-contact-1"), patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ) as mock_deal, patch("supabase_client.mark_lead_synced", return_value=True):
            poller.run_tick()

        assert mock_deal.call_args[0][1]["dealstage"] == "closedwon"

    def test_b2b_client_sync_never_creates_a_deal(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[]), patch(
            "supabase_client.list_b2b_clients", return_value=[_b2b_client()]
        ), patch("hubspot_client.upsert_company", return_value="hs-company-1") as mock_company, patch(
            "hubspot_client.upsert_deal"
        ) as mock_deal, patch("supabase_client.mark_b2b_client_synced", return_value=True) as mock_mark:
            summary = poller.run_tick()

        assert summary["b2b_clients_synced"] == 1
        mock_company.assert_called_once()
        mock_deal.assert_not_called()
        mock_mark.assert_called_once_with("client-1", "hs-company-1", mock_mark.call_args[0][2])

    def test_new_b2b_client_creates_company_and_persists_id(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[]), patch(
            "supabase_client.list_b2b_clients", return_value=[_b2b_client()]
        ), patch("hubspot_client.upsert_company", return_value="hs-company-1") as mock_company, patch(
            "supabase_client.mark_b2b_client_synced", return_value=True
        ):
            poller.run_tick()

        assert mock_company.call_args[0][0] is None

    def test_dry_run_changes_nothing(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        monkeypatch.setattr(settings, "DRY_RUN", True)
        with patch("supabase_client.list_leads", return_value=[_lead()]), patch(
            "supabase_client.list_b2b_clients", return_value=[_b2b_client()]
        ), patch("hubspot_client.upsert_contact") as mock_contact, patch(
            "hubspot_client.upsert_company"
        ) as mock_company:
            summary = poller.run_tick()

        assert summary["leads_synced"] == 0
        assert summary["b2b_clients_synced"] == 0
        mock_contact.assert_not_called()
        mock_company.assert_not_called()

    def test_first_sync_with_message_creates_a_note(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch(
            "supabase_client.list_leads", return_value=[_lead(last_message="Hola, quiero info")]
        ), patch("supabase_client.list_b2b_clients", return_value=[]), patch(
            "supabase_client.get_latest_wompi_transaction", return_value=None
        ), patch("hubspot_client.upsert_contact", return_value="hs-contact-1"), patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ), patch("supabase_client.mark_lead_synced", return_value=True), patch(
            "hubspot_client.create_note", return_value="note-1"
        ) as mock_note:
            poller.run_tick()

        mock_note.assert_called_once_with("hs-contact-1", "Hola, quiero info")

    def test_first_sync_without_message_creates_no_note(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead(last_message=None)]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("supabase_client.get_latest_wompi_transaction", return_value=None), patch(
            "hubspot_client.upsert_contact", return_value="hs-contact-1"
        ), patch("hubspot_client.upsert_deal", return_value="hs-deal-1"), patch(
            "supabase_client.mark_lead_synced", return_value=True
        ), patch("hubspot_client.create_note") as mock_note:
            poller.run_tick()

        mock_note.assert_not_called()

    def test_already_synced_lead_creates_no_note(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        existing = _lead(
            hubspot_contact_id="hs-contact-1", hubspot_deal_id="hs-deal-1", last_message="hola"
        )
        with patch("supabase_client.list_leads", return_value=[existing]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("supabase_client.get_latest_wompi_transaction", return_value=None), patch(
            "hubspot_client.upsert_contact", return_value="hs-contact-1"
        ), patch("hubspot_client.upsert_deal", return_value="hs-deal-1"), patch(
            "supabase_client.mark_lead_synced", return_value=True
        ), patch("hubspot_client.create_note") as mock_note:
            poller.run_tick()

        mock_note.assert_not_called()

    def test_deal_amount_set_from_latest_wompi_transaction(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead()]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch(
            "supabase_client.get_latest_wompi_transaction",
            return_value={"status": "PENDING", "amount_cents": 15000000},
        ), patch("hubspot_client.upsert_contact", return_value="hs-contact-1"), patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ) as mock_deal, patch("supabase_client.mark_lead_synced", return_value=True):
            poller.run_tick()

        assert mock_deal.call_args[0][1]["amount"] == "150000.0"

    def test_deal_amount_unset_when_no_transaction(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead()]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("supabase_client.get_latest_wompi_transaction", return_value=None), patch(
            "hubspot_client.upsert_contact", return_value="hs-contact-1"
        ), patch("hubspot_client.upsert_deal", return_value="hs-deal-1") as mock_deal, patch(
            "supabase_client.mark_lead_synced", return_value=True
        ):
            poller.run_tick()

        assert "amount" not in mock_deal.call_args[0][1]

    def test_por_aprobar_lead_with_no_open_task_creates_one(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch(
            "supabase_client.list_leads", return_value=[_lead(stage="POR_APROBAR")]
        ), patch("supabase_client.list_b2b_clients", return_value=[]), patch(
            "supabase_client.get_latest_wompi_transaction", return_value=None
        ), patch("hubspot_client.upsert_contact", return_value="hs-contact-1"), patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ), patch("supabase_client.mark_lead_synced", return_value=True), patch(
            "hubspot_client.has_open_task", return_value=False
        ), patch("hubspot_client.create_task", return_value="task-1") as mock_task:
            poller.run_tick()

        mock_task.assert_called_once()
        assert mock_task.call_args[0][0] == "hs-deal-1"

    def test_por_aprobar_lead_with_open_task_creates_no_duplicate(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch(
            "supabase_client.list_leads", return_value=[_lead(stage="POR_APROBAR")]
        ), patch("supabase_client.list_b2b_clients", return_value=[]), patch(
            "supabase_client.get_latest_wompi_transaction", return_value=None
        ), patch("hubspot_client.upsert_contact", return_value="hs-contact-1"), patch(
            "hubspot_client.upsert_deal", return_value="hs-deal-1"
        ), patch("supabase_client.mark_lead_synced", return_value=True), patch(
            "hubspot_client.has_open_task", return_value=True
        ), patch("hubspot_client.create_task") as mock_task:
            poller.run_tick()

        mock_task.assert_not_called()

    def test_non_por_aprobar_lead_never_checks_tasks(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead(stage="NUEVOS")]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("supabase_client.get_latest_wompi_transaction", return_value=None), patch(
            "hubspot_client.upsert_contact", return_value="hs-contact-1"
        ), patch("hubspot_client.upsert_deal", return_value="hs-deal-1"), patch(
            "supabase_client.mark_lead_synced", return_value=True
        ), patch("hubspot_client.has_open_task") as mock_has_open:
            poller.run_tick()

        mock_has_open.assert_not_called()

    def test_hubspot_failure_does_not_mark_lead_synced(self, monkeypatch):
        monkeypatch.setattr(settings, "HUBSPOT_ACCESS_TOKEN", "token-123")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key-123")
        with patch("supabase_client.list_leads", return_value=[_lead()]), patch(
            "supabase_client.list_b2b_clients", return_value=[]
        ), patch("hubspot_client.upsert_contact", return_value=None), patch(
            "supabase_client.mark_lead_synced"
        ) as mock_mark:
            summary = poller.run_tick()

        assert summary["leads_synced"] == 0
        mock_mark.assert_not_called()
