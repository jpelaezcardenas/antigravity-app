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

    def test_falls_back_to_update_when_the_path_already_exists(self):
        """Real bug found live 2026-09-11 (task 6b): a retry against a lead_id/document_type path
        that already has a file from a previous attempt raised
        storage3.utils.StorageException({'code': 'KeyAlreadyExists', ...}) despite
        file_options={"upsert": "true"} already being passed -- the installed storage3 version
        pinned for production (via supabase==2.0.3 in requirements.txt) doesn't honor that option
        the way this repo's local dev venv (2.31.0) might. Rather than guess the right
        upsert-string format for whichever version is actually running, fall back to the
        unconditional PUT (`update()`), which every storage3 version supports as a real distinct
        HTTP verb, not an option string."""
        import storage3.utils

        mock_client = MagicMock()
        mock_client.storage.from_.return_value.upload.side_effect = storage3.utils.StorageException(
            {"statusCode": 400, "error": "Duplicate", "message": "The resource already exists", "code": "KeyAlreadyExists"}
        )
        with patch(
            "services.document_storage_service.get_service_supabase", return_value=mock_client
        ):
            path = upload_tax_document(
                lead_id="lead-1", document_type="rut", file_bytes=b"fake-pdf", mime_type="application/pdf"
            )

        assert path == "lead-1/rut.pdf"
        mock_client.storage.from_.return_value.update.assert_called_once()

    def test_reraises_a_storage_error_that_is_not_a_duplicate(self):
        import storage3.utils

        mock_client = MagicMock()
        mock_client.storage.from_.return_value.upload.side_effect = storage3.utils.StorageException(
            {"statusCode": 500, "error": "Internal", "message": "boom", "code": "SomethingElse"}
        )
        with patch(
            "services.document_storage_service.get_service_supabase", return_value=mock_client
        ):
            try:
                upload_tax_document(
                    lead_id="lead-1", document_type="rut", file_bytes=b"x", mime_type="application/pdf"
                )
                assert False, "expected StorageException to propagate"
            except storage3.utils.StorageException:
                pass
        mock_client.storage.from_.return_value.update.assert_not_called()

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
