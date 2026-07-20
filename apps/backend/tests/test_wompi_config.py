"""Tests for Wompi payment settings fail-closed validation (config.py)."""
import pytest

from config import Settings


def _settings(**overrides) -> Settings:
    base = dict(
        WOMPI_ENV="sandbox",
        WOMPI_PUBLIC_KEY="",
        WOMPI_PRIVATE_KEY="",
        WOMPI_INTEGRITY_SECRET="",
        WOMPI_EVENTS_SECRET="",
    )
    base.update(overrides)
    return Settings(**base)


class TestWompiProductionFailsClosed:
    def test_missing_public_key_in_production_raises(self):
        settings = _settings(
            WOMPI_ENV="production",
            WOMPI_PRIVATE_KEY="prv_prod_x",
            WOMPI_INTEGRITY_SECRET="prod_integrity_x",
            WOMPI_EVENTS_SECRET="prod_events_x",
        )
        with pytest.raises(ValueError, match="WOMPI_PUBLIC_KEY"):
            settings.validate_wompi_config()

    def test_missing_multiple_vars_in_production_lists_all(self):
        settings = _settings(WOMPI_ENV="production")
        with pytest.raises(ValueError) as exc_info:
            settings.validate_wompi_config()
        message = str(exc_info.value)
        for name in (
            "WOMPI_PUBLIC_KEY",
            "WOMPI_PRIVATE_KEY",
            "WOMPI_INTEGRITY_SECRET",
            "WOMPI_EVENTS_SECRET",
        ):
            assert name in message

    def test_all_vars_present_in_production_passes(self):
        settings = _settings(
            WOMPI_ENV="production",
            WOMPI_PUBLIC_KEY="pub_prod_x",
            WOMPI_PRIVATE_KEY="prv_prod_x",
            WOMPI_INTEGRITY_SECRET="prod_integrity_x",
            WOMPI_EVENTS_SECRET="prod_events_x",
        )
        settings.validate_wompi_config()  # should not raise


class TestWompiSandboxProductionKeyMismatch:
    def test_sandbox_env_with_production_public_key_raises(self):
        settings = _settings(WOMPI_ENV="sandbox", WOMPI_PUBLIC_KEY="pub_prod_x")
        with pytest.raises(ValueError, match="sandbox"):
            settings.validate_wompi_config()

    def test_sandbox_env_with_production_private_key_raises(self):
        settings = _settings(WOMPI_ENV="sandbox", WOMPI_PRIVATE_KEY="prv_prod_x")
        with pytest.raises(ValueError, match="sandbox"):
            settings.validate_wompi_config()

    def test_sandbox_env_with_sandbox_keys_passes(self):
        settings = _settings(
            WOMPI_ENV="sandbox",
            WOMPI_PUBLIC_KEY="pub_test_x",
            WOMPI_PRIVATE_KEY="prv_test_x",
        )
        settings.validate_wompi_config()  # should not raise

    def test_production_env_with_sandbox_public_key_raises(self):
        settings = _settings(
            WOMPI_ENV="production",
            WOMPI_PUBLIC_KEY="pub_test_x",
            WOMPI_PRIVATE_KEY="prv_prod_x",
            WOMPI_INTEGRITY_SECRET="prod_integrity_x",
            WOMPI_EVENTS_SECRET="prod_events_x",
        )
        with pytest.raises(ValueError, match="production"):
            settings.validate_wompi_config()

    def test_invalid_wompi_env_raises(self):
        settings = _settings(WOMPI_ENV="staging")
        with pytest.raises(ValueError, match="WOMPI_ENV"):
            settings.validate_wompi_config()

    def test_sandbox_env_with_empty_keys_passes(self):
        # Sandbox with no keys configured yet (e.g. local dev) should not
        # fail closed — only production requires all four to be present.
        settings = _settings(WOMPI_ENV="sandbox")
        settings.validate_wompi_config()  # should not raise
