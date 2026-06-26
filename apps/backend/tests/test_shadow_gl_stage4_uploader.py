"""
Phase 8 Stage 4: Admin PWA File Uploader Tests

Tests for CSV file upload endpoint with ingestion_batches tracking.
"""

import pytest
from io import BytesIO
from fastapi.testclient import TestClient
import tempfile
import os


# Sample valid Siigo CSV
VALID_SIIGO_CSV = """Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,100.00,
2026-06-25,TX-001,4100,Sales Revenue,,100.00
2026-06-25,TX-002,1200,Accounts Payable,,50.00
2026-06-25,TX-002,5100,Purchases,50.00,
"""


@pytest.fixture
def csv_file():
    """Create a temporary CSV file for upload tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(VALID_SIIGO_CSV)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestUploadEndpoint:
    """Test CSV file upload endpoint."""

    def test_upload_endpoint_exists(self):
        """✅ Upload endpoint /siigo-csv/upload exists."""
        # Verify endpoint is reachable
        # This test just checks that the route is defined
        from presentation.shadow_gl_endpoints import router

        routes = [route.path for route in router.routes]
        assert any("/siigo-csv/upload" in path for path in routes)

    def test_upload_accepts_multipart_form_data(self):
        """✅ Upload endpoint accepts multipart/form-data with file param."""
        # Verify endpoint signature accepts UploadFile
        from presentation.shadow_gl_endpoints import upload_siigo_csv_endpoint
        import inspect

        sig = inspect.signature(upload_siigo_csv_endpoint)
        params = list(sig.parameters.keys())
        assert "file" in params  # Should have file parameter


class TestPhase8Stage4Acceptance:
    """Acceptance criteria for Stage 4."""

    def test_upload_endpoint_defined(self):
        """✅ POST /shadow-gl/siigo-csv/upload endpoint exists."""
        from presentation.shadow_gl_endpoints import router

        routes = [route for route in router.routes]
        upload_routes = [r for r in routes if "/siigo-csv/upload" in r.path]
        assert len(upload_routes) > 0

    def test_ingestion_batches_schema_exists(self):
        """✅ ingestion_batches table schema is defined in migration."""
        import os
        assert os.path.exists(
            "apps/backend/migrations/0019_shadow_gl_siigo_ingestion.sql"
        )

    def test_migration_has_ingestion_batches_creation(self):
        """✅ Migration includes CREATE TABLE ingestion_batches."""
        with open("apps/backend/migrations/0019_shadow_gl_siigo_ingestion.sql", "r") as f:
            content = f.read()

        assert "CREATE TABLE IF NOT EXISTS ingestion_batches" in content
        assert "data_source" in content
        assert "status" in content

    def test_endpoint_response_model_defined(self):
        """✅ Upload endpoint has proper response model."""
        from presentation.shadow_gl_endpoints import SiigoCSVIngestResponse

        # Verify response model has required fields
        response = SiigoCSVIngestResponse(
            success=True,
            row_count=4,
            date_range="2026-06-25..2026-06-25",
            error=""
        )
        assert response.success
        assert response.row_count == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
