"""
Unit tests for document_storage_service.py (taty-document-collection, Change I).

Supabase Storage client mocked directly, no credentials needed. This is the first Storage-using
service in this repo — see design.md Decision 3 for the crm-tax-documents bucket rationale.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.document_storage_service import get_signed_document_url, upload_tax_document


class TestUploadTaxDocument:
    def test_uploads_to_the_expected_path_and_returns_it(self):
        mock_client = MagicMock()
        with patch(
            "services.document_storage_service.get_service_supabase", return_value=mock_client
        ):
            path = upload_tax_document(
                lead_id="lead-1", document_type="rut", file_bytes=b"fake-pdf", mime_type="application/pdf"
            )

        assert path == "lead-1/rut.pdf"
        mock_client.storage.from_.assert_called_once_with("crm-tax-documents")
        upload_call = mock_client.storage.from_.return_value.upload
        upload_call.assert_called_once()
        args, kwargs = upload_call.call_args
        assert "lead-1/rut.pdf" in args or kwargs.get("path") == "lead-1/rut.pdf"

    def test_extractos_document_uses_the_extractos_path(self):
        mock_client = MagicMock()
        with patch(
            "services.document_storage_service.get_service_supabase", return_value=mock_client
        ):
            path = upload_tax_document(
                lead_id="lead-1", document_type="extractos", file_bytes=b"fake-pdf",
                mime_type="application/pdf",
            )

        assert path == "lead-1/extractos.pdf"


class TestGetSignedDocumentUrl:
    def test_returns_a_signed_url(self):
        mock_client = MagicMock()
        mock_client.storage.from_.return_value.create_signed_url.return_value = {
            "signedURL": "https://signed.example/lead-1/rut.pdf?token=abc"
        }
        with patch(
            "services.document_storage_service.get_service_supabase", return_value=mock_client
        ):
            url = get_signed_document_url("lead-1/rut.pdf")

        assert url == "https://signed.example/lead-1/rut.pdf?token=abc"
        mock_client.storage.from_.assert_called_once_with("crm-tax-documents")
