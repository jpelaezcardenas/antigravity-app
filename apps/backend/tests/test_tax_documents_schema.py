"""
Integration tests for the tax-document storage schema (taty-document-collection, Change I).

Gated by RUN_TAX_DOCUMENTS=1 since they hit the real Supabase project — mirrors the pattern used
by test_operator_tasks_schema.py for RUN_OPERATOR_TASKS.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_service_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_TAX_DOCUMENTS") != "1",
    reason="Set RUN_TAX_DOCUMENTS=1 to run tax-document integration tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    return get_service_supabase()


class TestCrmTaxProfilesNewColumns:
    def test_rut_storage_path_column_is_queryable(self, supabase) -> None:
        result = (
            supabase.table("crm_tax_profiles").select("rut_storage_path").limit(1).execute()
        )
        assert isinstance(result.data, list)

    def test_extractos_storage_path_column_is_queryable(self, supabase) -> None:
        result = (
            supabase.table("crm_tax_profiles")
            .select("extractos_storage_path")
            .limit(1)
            .execute()
        )
        assert isinstance(result.data, list)


class TestCrmTaxDocumentsBucket:
    def test_bucket_exists(self, supabase) -> None:
        buckets = supabase.storage.list_buckets()
        bucket_ids = [b.id if hasattr(b, "id") else b.get("id") for b in buckets]
        assert "crm-tax-documents" in bucket_ids

    def test_bucket_is_private(self, supabase) -> None:
        buckets = supabase.storage.list_buckets()
        target = next(
            (b for b in buckets if (b.id if hasattr(b, "id") else b.get("id")) == "crm-tax-documents"),
            None,
        )
        assert target is not None
        is_public = target.public if hasattr(target, "public") else target.get("public")
        assert is_public is False
