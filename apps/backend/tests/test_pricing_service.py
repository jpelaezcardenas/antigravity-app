"""
Tests for the pre-quote engine (pricing-quote-engine, Stage 3).

Most of these assert *honesty* properties rather than arithmetic: that the payroll driver
is always declared missing, that confidence is never "alta", that a thin-history tenant
gets an explicit state instead of an invented band, and that `supera_umbral_declarante`
being false is never presented as "not obligated to file". Those are the properties the
Radar projection precedent (ARCHITECTURE.md, Radar section) requires an engine like this
to carry in its own payload.

The Supabase client is stubbed; the annualisation, unit conversion, banding and
confidence logic under test all run for real. The stub records the `.eq()` filters it
received so tenant isolation can be asserted against the actual query, not assumed.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from services.pricing_service import (
    COMPLEJO_MIN_MONTHLY_LINES,
    COMPLEJO_MIN_UVT,
    DECLARANT_THRESHOLD_UVT,
    MICRO_MAX_MONTHLY_LINES,
    MIN_HISTORY_MONTHS,
    MISSING_DRIVER_PAYROLL,
    compute_pre_quote,
)

UVT_2025_COP = 49_799
UVT_ROW = {
    "year": 2025,
    "value_cop": UVT_2025_COP,
    "resolution": "Resolución DIAN 000193 de 2024",
}


class _RecordingQuery:
    def __init__(self, rows, filters):
        self._rows = rows
        self._filters = filters

    def select(self, *_a, **_k):
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def gte(self, *_a, **_k):
        return self

    def lte(self, *_a, **_k):
        return self

    def in_(self, column, values):
        self._filters.append((column, tuple(values)))
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return type("Result", (), {"data": self._rows})()


class _StubClient:
    def __init__(self, entries, lines, uvt_row=UVT_ROW):
        self.entries = entries
        self.lines = lines
        self.uvt_row = uvt_row
        self.filters: dict[str, list] = {
            "erp_journal_entries": [],
            "erp_journal_lines": [],
            "uvt_values": [],
        }

    def table(self, name):
        rows = {
            "erp_journal_entries": self.entries,
            "erp_journal_lines": self.lines,
            "uvt_values": self.uvt_row,
        }[name]
        return _RecordingQuery(rows, self.filters[name])


def _months_of_entries(count: int, per_month: int = 1) -> list[dict]:
    """`count` distinct months of journal entries, most recent first."""
    today = date.today()
    entries = []
    for offset in range(count):
        month_day = (today.replace(day=1) - timedelta(days=offset * 30)).replace(day=15)
        for n in range(per_month):
            entries.append({"id": f"entry-{offset}-{n}", "entry_date": month_day.isoformat()})
    return entries


def _revenue_lines(total_credit_minor: int, extra_lines: int = 0) -> list[dict]:
    lines = [
        {"account_code": "4100", "debit_minor": 0, "credit_minor": total_credit_minor},
    ]
    for i in range(extra_lines):
        lines.append({"account_code": "5105", "debit_minor": 1000, "credit_minor": 0})
    return lines


class TestInsufficientHistory:
    def test_fewer_than_minimum_months_returns_explicit_state(self):
        client = _StubClient(
            entries=_months_of_entries(MIN_HISTORY_MONTHS - 1),
            lines=_revenue_lines(500_000_000_00),
        )

        result = compute_pre_quote("tenant-new", tax_year=2025, supabase_client=client)

        assert result["estado"] == "sin_historico_suficiente"
        assert result["banda_sugerida"] is None

    def test_no_history_at_all_returns_explicit_state(self):
        client = _StubClient(entries=[], lines=[])

        result = compute_pre_quote("tenant-empty", tax_year=2025, supabase_client=client)

        assert result["estado"] == "sin_historico_suficiente"
        assert result["banda_sugerida"] is None

    def test_thin_history_still_declares_its_missing_drivers(self):
        """An empty-state response must not drop the honesty fields — otherwise the
        caller sees 'no band' with no explanation of what was unobservable."""
        client = _StubClient(entries=[], lines=[])

        result = compute_pre_quote("tenant-empty", tax_year=2025, supabase_client=client)

        assert MISSING_DRIVER_PAYROLL in result["drivers_faltantes"]
        assert result["criterios_no_evaluables"]


class TestRevenueAndVolume:
    def test_annualises_partial_history_and_reports_the_month_count(self):
        # 6 months observed, $60.000.000 total revenue -> $120.000.000 annualised.
        client = _StubClient(
            entries=_months_of_entries(6),
            lines=_revenue_lines(60_000_000_00),
        )

        result = compute_pre_quote("tenant-partial", tax_year=2025, supabase_client=client)

        assert result["meses_observados"] == 6
        assert result["ingresos_anualizados_cop"] == 120_000_000

    def test_reports_revenue_in_whole_pesos_not_minor_units(self):
        """The Shadow GL stores cents. A missed //100 here would overstate revenue 100x
        and misclassify every tenant as complejo (design.md Decision #1)."""
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(100_000_000_00),  # $100.000.000 in minor units
        )

        result = compute_pre_quote("tenant-units", tax_year=2025, supabase_client=client)

        assert result["ingresos_anualizados_cop"] == 100_000_000

    def test_expresses_revenue_in_uvt_of_the_requested_tax_year(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(UVT_2025_COP * 1000 * 100),  # exactly 1.000 UVT
        )

        result = compute_pre_quote("tenant-uvt", tax_year=2025, supabase_client=client)

        assert result["ingresos_anualizados_uvt"] == pytest.approx(1000.0, rel=1e-6)

    def test_movimientos_mes_is_a_real_average_line_count(self):
        # 4 months of history, 1 revenue line + 39 expense lines = 40 lines -> 10/month.
        client = _StubClient(
            entries=_months_of_entries(4),
            lines=_revenue_lines(10_000_000_00, extra_lines=39),
        )

        result = compute_pre_quote("tenant-vol", tax_year=2025, supabase_client=client)

        assert result["movimientos_mes"] == 10


class TestDeclarantThreshold:
    def test_crossing_the_revenue_threshold_is_reported(self):
        above = (DECLARANT_THRESHOLD_UVT + 100) * UVT_2025_COP
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(above * 100),
        )

        result = compute_pre_quote("tenant-big", tax_year=2025, supabase_client=client)

        assert result["supera_umbral_declarante"] is True
        assert result["umbral_declarante_uvt"] == DECLARANT_THRESHOLD_UVT
        assert result["umbral_declarante_cop"] == DECLARANT_THRESHOLD_UVT * UVT_2025_COP

    def test_not_crossing_is_never_presented_as_not_obligated(self):
        """The other four quantitative criteria and the IVA criterion are unobservable,
        so `false` means 'the one criterion we can see was not crossed' — the response
        must say which criterion it evaluated and which it did not."""
        below = (DECLARANT_THRESHOLD_UVT - 500) * UVT_2025_COP
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(below * 100),
        )

        result = compute_pre_quote("tenant-small", tax_year=2025, supabase_client=client)

        assert result["supera_umbral_declarante"] is False
        assert result["criterio_evaluado"] == "ingresos_brutos"
        for unevaluated in (
            "compras_y_consumos",
            "consignaciones_y_depositos",
            "consumos_tarjeta_credito",
            "patrimonio_bruto",
            "responsabilidad_iva",
        ):
            assert unevaluated in result["criterios_no_evaluables"]

    def test_patrimony_is_never_computed(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(50_000_000_00),
        )

        result = compute_pre_quote("tenant-any", tax_year=2025, supabase_client=client)

        assert "patrimonio_bruto" in result["criterios_no_evaluables"]
        assert "patrimonio_bruto_cop" not in result
        assert "patrimonio_bruto_uvt" not in result


class TestBandHeuristics:
    def test_low_revenue_and_low_volume_suggests_micro(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(20_000_000_00, extra_lines=11),  # 12 lines / 12 months = 1
        )

        result = compute_pre_quote("tenant-micro", tax_year=2025, supabase_client=client)

        assert result["banda_sugerida"] == "micro"

    def test_high_revenue_suggests_complejo(self):
        big = (COMPLEJO_MIN_UVT + 10) * UVT_2025_COP
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(big * 100),
        )

        result = compute_pre_quote("tenant-complejo", tax_year=2025, supabase_client=client)

        assert result["banda_sugerida"] == "complejo"

    def test_high_volume_alone_suggests_complejo(self):
        """Volume is an independent driver: a low-revenue, very high-movement client is
        still heavy accounting work."""
        lines = COMPLEJO_MIN_MONTHLY_LINES * 12
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(10_000_000_00, extra_lines=lines - 1),
        )

        result = compute_pre_quote("tenant-busy", tax_year=2025, supabase_client=client)

        assert result["banda_sugerida"] == "complejo"

    def test_mid_revenue_suggests_estandar(self):
        mid = (DECLARANT_THRESHOLD_UVT + 500) * UVT_2025_COP
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(mid * 100, extra_lines=50),
        )

        result = compute_pre_quote("tenant-mid", tax_year=2025, supabase_client=client)

        assert result["banda_sugerida"] == "estandar"

    def test_low_revenue_but_busy_is_not_micro(self):
        """Micro is 'minimal movement'. Low revenue alone must not qualify."""
        busy = MICRO_MAX_MONTHLY_LINES * 12 * 2
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(20_000_000_00, extra_lines=busy),
        )

        result = compute_pre_quote("tenant-lowrev-busy", tax_year=2025, supabase_client=client)

        assert result["banda_sugerida"] != "micro"


class TestConfidenceAndMissingDrivers:
    def test_confidence_is_never_alta(self):
        """Half the fee criterion (labour load) is structurally absent from the data
        model, so no output of this engine is ever fully grounded."""
        for revenue_uvt, extra_lines in [(100, 0), (2000, 50), (10_000, 500)]:
            client = _StubClient(
                entries=_months_of_entries(12),
                lines=_revenue_lines(revenue_uvt * UVT_2025_COP * 100, extra_lines=extra_lines),
            )

            result = compute_pre_quote("tenant-x", tax_year=2025, supabase_client=client)

            assert result["confianza"] in ("media", "baja")
            assert result["confianza"] != "alta"

    def test_micro_is_always_low_confidence(self):
        """Micro is defined as 'minimal movement WITHOUT labour load' — the absence of
        payroll is precisely what cannot be observed, so a micro suggestion is the least
        grounded output the engine can produce."""
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(20_000_000_00, extra_lines=5),
        )

        result = compute_pre_quote("tenant-micro", tax_year=2025, supabase_client=client)

        assert result["banda_sugerida"] == "micro"
        assert result["confianza"] == "baja"

    def test_thin_history_lowers_confidence(self):
        thin = _StubClient(
            entries=_months_of_entries(MIN_HISTORY_MONTHS),
            lines=_revenue_lines(2000 * UVT_2025_COP * 100, extra_lines=100),
        )
        full = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(2000 * UVT_2025_COP * 100, extra_lines=100),
        )

        assert compute_pre_quote("t", 2025, supabase_client=thin)["confianza"] == "baja"
        assert compute_pre_quote("t", 2025, supabase_client=full)["confianza"] == "media"

    def test_payroll_is_always_a_declared_missing_driver(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(2000 * UVT_2025_COP * 100),
        )

        result = compute_pre_quote("tenant-any", tax_year=2025, supabase_client=client)

        assert MISSING_DRIVER_PAYROLL in result["drivers_faltantes"]

    def test_no_payroll_figure_is_ever_emitted(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(2000 * UVT_2025_COP * 100),
        )

        result = compute_pre_quote("tenant-any", tax_year=2025, supabase_client=client)

        for key in result:
            assert "nomina" not in key
            assert "payroll" not in key


class TestTenantIsolation:
    def test_every_shadow_gl_query_is_filtered_by_the_callers_tenant(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(50_000_000_00),
        )

        compute_pre_quote("tenant-A", tax_year=2025, supabase_client=client)

        assert ("tenant_id", "tenant-A") in client.filters["erp_journal_entries"]
        assert ("tenant_id", "tenant-A") in client.filters["erp_journal_lines"]

    def test_lines_are_restricted_to_the_tenants_own_entry_ids(self):
        entries = _months_of_entries(12)
        client = _StubClient(entries=entries, lines=_revenue_lines(50_000_000_00))

        compute_pre_quote("tenant-A", tax_year=2025, supabase_client=client)

        entry_id_filters = [f for f in client.filters["erp_journal_lines"] if f[0] == "entry_id"]
        assert entry_id_filters, "journal lines must be restricted to the fetched entry ids"
        assert set(entry_id_filters[0][1]) == {e["id"] for e in entries}


class TestUvtWiring:
    def test_uses_the_uvt_of_the_requested_tax_year(self):
        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(52_374 * 1000 * 100),
            uvt_row={"year": 2026, "value_cop": 52_374, "resolution": "Res. 000238 de 2025"},
        )

        result = compute_pre_quote("t", tax_year=2026, supabase_client=client)

        assert result["anio_gravable"] == 2026
        assert result["uvt_cop"] == 52_374
        assert result["ingresos_anualizados_uvt"] == pytest.approx(1000.0, rel=1e-6)

    def test_missing_uvt_year_propagates_rather_than_defaulting(self):
        from services.uvt_service import UvtNotFoundError

        client = _StubClient(
            entries=_months_of_entries(12),
            lines=_revenue_lines(50_000_000_00),
            uvt_row=None,
        )

        with pytest.raises(UvtNotFoundError):
            compute_pre_quote("t", tax_year=2099, supabase_client=client)


class TestReadOnly:
    def test_computing_a_pre_quote_writes_nothing(self):
        """A read endpoint that writes is exactly the exception radar-adoption-tracking
        had to justify explicitly; this engine takes no such exception."""

        class _WriteTrap(_StubClient):
            def table(self, name):
                query = super().table(name)
                for forbidden in ("insert", "update", "upsert", "delete"):
                    setattr(
                        query,
                        forbidden,
                        lambda *a, **k: pytest.fail("pre-quote must not write"),
                    )
                return query

        client = _WriteTrap(
            entries=_months_of_entries(12),
            lines=_revenue_lines(50_000_000_00),
        )

        compute_pre_quote("tenant-A", tax_year=2025, supabase_client=client)
