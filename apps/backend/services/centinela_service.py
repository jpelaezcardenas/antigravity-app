"""
Centinela Rules Engine - Detección fiscal ex-ante

Implementa 10 reglas de detección automática de riesgos fiscales:
1. UVT Excedido
2. Retención No Pagada
3. Facturación Irregular
4. Cambio Régimen No Reportado
5. Provisiones Insuficientes
6. Margen Bruto Sospechoso
7. Operación Relacionada No Reportada
8. Activo Sobrevaluado
9. Deuda con DIAN
10. Inconsistencia Contable
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging
import json

from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Constantes fiscales 2026 para Colombia
UVT_2026 = 52.374
REGIMEN_SIMPLE_LIMIT_UVT = 160
REGIMEN_COMUN_MIN_RETENTION = 0.03  # 3%
IVA_STANDARD_RATE = 0.19


class CentinelaRule:
    """Base class para reglas de Centinela"""

    def __init__(self, rule_id: str, name: str, severity: str = "warning"):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity

    def evaluate(self, data: Dict) -> Optional[Dict]:
        """
        Evalúa la regla contra los datos.
        Retorna dict con alerta si la regla se activa, None si no aplica.
        """
        raise NotImplementedError


class Rule1UVTExcedido(CentinelaRule):
    """Regla 1: Ingresos superan límites por régimen"""

    def __init__(self):
        super().__init__("R001", "UVT Excedido", "warning")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        """Verifica si ingresos anuales superan límites del régimen"""
        regime = data.get("regimen", "")
        annual_revenue = data.get("annual_revenue", 0)

        if regime == "Régimen Simple":
            limit_pesos = REGIMEN_SIMPLE_LIMIT_UVT * UVT_2026
            if annual_revenue > limit_pesos:
                return {
                    "rule_id": self.rule_id,
                    "rule_name": self.name,
                    "severity": self.severity,
                    "title": "Ingresos superan límite de Régimen Simple",
                    "description": f"Ingresos anuales (${annual_revenue:,.0f}) superan {REGIMEN_SIMPLE_LIMIT_UVT} UVT (${limit_pesos:,.0f})",
                    "recommendation": "Cambiar a Régimen Común o solicitud formal a DIAN",
                    "evidence": {
                        "regime": regime,
                        "annual_revenue": annual_revenue,
                        "limit_pesos": limit_pesos,
                        "excess": annual_revenue - limit_pesos,
                    },
                }
        return None


class Rule2RetencionNoPagada(CentinelaRule):
    """Regla 2: Obligación de retención sin pago"""

    def __init__(self):
        super().__init__("R002", "Retención No Pagada", "critical")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        if data.get("regime") == "Régimen Común":
            service_revenue = data.get("service_revenue", 0)
            retention_paid = data.get("retention_paid", 0)
            expected_retention = service_revenue * REGIMEN_COMUN_MIN_RETENTION

            if retention_paid < expected_retention * 0.9:  # 90% tolerance
                return {
                    "rule_id": self.rule_id,
                    "rule_name": self.name,
                    "severity": self.severity,
                    "title": "Retención en la fuente no pagada",
                    "description": f"Retención esperada (${expected_retention:,.0f}), pagada (${retention_paid:,.0f})",
                    "recommendation": "Pagar retención pendiente + intereses a DIAN",
                    "evidence": {
                        "service_revenue": service_revenue,
                        "retention_paid": retention_paid,
                        "expected_retention": expected_retention,
                        "shortfall": expected_retention - retention_paid,
                    },
                }
        return None


class Rule3FacturacionIrregular(CentinelaRule):
    """Regla 3: Gaps o inconsistencias en facturación"""

    def __init__(self):
        super().__init__("R003", "Facturación Irregular", "warning")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        invoices = data.get("invoices", [])
        if not invoices:
            return None

        invoice_numbers = sorted([inv.get("number", 0) for inv in invoices])
        gaps = []

        for i in range(len(invoice_numbers) - 1):
            if invoice_numbers[i + 1] - invoice_numbers[i] > 1:
                gaps.append({
                    "from": invoice_numbers[i],
                    "to": invoice_numbers[i + 1],
                })

        if gaps:
            return {
                "rule_id": self.rule_id,
                "rule_name": self.name,
                "severity": self.severity,
                "title": "Numeración de facturas con gaps",
                "description": f"Se detectaron {len(gaps)} brechas en numeración consecutiva",
                "recommendation": "Revisar registros de anulaciones o documentación faltante",
                "evidence": {"gaps": gaps, "total_gaps": len(gaps)},
            }
        return None


class Rule4CambioRegimenNoReportado(CentinelaRule):
    """Regla 4: Cambio de régimen sin comunicación a DIAN"""

    def __init__(self):
        super().__init__("R004", "Cambio Régimen No Reportado", "critical")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        current_regime = data.get("current_regime", "")
        last_regime_change = data.get("last_regime_change_date", None)
        dian_notified = data.get("dian_notified", False)

        if last_regime_change and not dian_notified:
            return {
                "rule_id": self.rule_id,
                "rule_name": self.name,
                "severity": self.severity,
                "title": "Cambio de régimen no reportado a DIAN",
                "description": f"Cambio detectado desde {data.get('previous_regime')} a {current_regime}",
                "recommendation": "Comunicar cambio a DIAN inmediatamente con formulario RUT",
                "evidence": {
                    "current_regime": current_regime,
                    "previous_regime": data.get("previous_regime"),
                    "change_date": last_regime_change,
                    "dian_notified": dian_notified,
                },
            }
        return None


class Rule5ProvisionesInsuficientes(CentinelaRule):
    """Regla 5: Provisiones contables por debajo de requerimientos"""

    def __init__(self):
        super().__init__("R005", "Provisiones Insuficientes", "warning")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        # Provisión mínima para cuentas por cobrar: 5% del saldo
        accounts_receivable = data.get("accounts_receivable", 0)
        provision_recorded = data.get("allowance_for_doubtful_accounts", 0)
        required_provision = accounts_receivable * 0.05

        if provision_recorded < required_provision:
            return {
                "rule_id": self.rule_id,
                "rule_name": self.name,
                "severity": self.severity,
                "title": "Provisión insuficiente por incobrabilidad",
                "description": f"Provisión requerida (${required_provision:,.0f}), registrada (${provision_recorded:,.0f})",
                "recommendation": "Aumentar provisión a mínimo 5% de CxC",
                "evidence": {
                    "accounts_receivable": accounts_receivable,
                    "provision_recorded": provision_recorded,
                    "required_provision": required_provision,
                    "shortfall": required_provision - provision_recorded,
                },
            }
        return None


class Rule6MargenBrutaSospechoso(CentinelaRule):
    """Regla 6: Margen bruto desviado vs sector"""

    def __init__(self):
        super().__init__("R006", "Margen Bruto Sospechoso", "warning")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        sector = data.get("sector", "")
        gross_margin = data.get("gross_margin_percent", 0)

        # Márgenes típicos por sector (simplificado)
        sector_ranges = {
            "Servicios Digitales": (40, 70),
            "Comercio": (20, 40),
            "Importaciones": (15, 35),
        }

        if sector in sector_ranges:
            min_margin, max_margin = sector_ranges[sector]
            if gross_margin < min_margin or gross_margin > max_margin:
                return {
                    "rule_id": self.rule_id,
                    "rule_name": self.name,
                    "severity": self.severity,
                    "title": f"Margen bruto sospechoso para sector {sector}",
                    "description": f"Margen {gross_margin}% fuera de rango esperado ({min_margin}-{max_margin}%)",
                    "recommendation": "Validar cálculo de costo de venta y estructura de precios",
                    "evidence": {
                        "sector": sector,
                        "gross_margin": gross_margin,
                        "expected_range": sector_ranges[sector],
                    },
                }
        return None


class Rule7OperacionRelacionadaNoReportada(CentinelaRule):
    """Regla 7: Transacción con vinculada sin declaración"""

    def __init__(self):
        super().__init__("R007", "Operación Relacionada No Reportada", "critical")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        related_party_transactions = data.get("related_party_transactions", [])
        declared_related_parties = data.get("declared_related_parties", [])

        for transaction in related_party_transactions:
            party_id = transaction.get("party_id")
            if party_id and party_id not in declared_related_parties:
                return {
                    "rule_id": self.rule_id,
                    "rule_name": self.name,
                    "severity": self.severity,
                    "title": "Operación con vinculada no reportada",
                    "description": f"Transacción detectada con {transaction.get('party_name')}",
                    "recommendation": "Declarar operación en formulario de partes vinculadas",
                    "evidence": {
                        "undeclared_party": transaction.get("party_name"),
                        "transaction_amount": transaction.get("amount"),
                        "transaction_date": transaction.get("date"),
                    },
                }
        return None


class Rule8ActivoSobrevaluado(CentinelaRule):
    """Regla 8: Depreciación anómala o inflación de valores"""

    def __init__(self):
        super().__init__("R008", "Activo Sobrevaluado", "warning")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        fixed_assets = data.get("fixed_assets", {})
        accumulated_depreciation = data.get("accumulated_depreciation", 0)
        total_cost = data.get("total_fixed_asset_cost", 0)

        if total_cost > 0:
            depreciation_rate = accumulated_depreciation / total_cost
            # Tasa típica: 10-20% anual para máquinas, 5% para edificios
            if depreciation_rate < 0.05 and total_cost > 0:
                return {
                    "rule_id": self.rule_id,
                    "rule_name": self.name,
                    "severity": self.severity,
                    "title": "Activo fijo con depreciación baja",
                    "description": "Tasa de depreciación inferior a lo esperado",
                    "recommendation": "Revisar vidas útiles y métodos de depreciación con auditor",
                    "evidence": {
                        "total_cost": total_cost,
                        "accumulated_depreciation": accumulated_depreciation,
                        "depreciation_rate": depreciation_rate,
                    },
                }
        return None


class Rule9DeudaDIAN(CentinelaRule):
    """Regla 9: Obligaciones pendientes con DIAN"""

    def __init__(self):
        super().__init__("R009", "Deuda con DIAN", "critical")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        dian_debt = data.get("dian_debt", 0)
        dian_debt_overdue_days = data.get("dian_debt_overdue_days", 0)

        if dian_debt > 0:
            return {
                "rule_id": self.rule_id,
                "rule_name": self.name,
                "severity": self.severity,
                "title": "Obligación pendiente con DIAN",
                "description": f"Deuda por ${dian_debt:,.0f} con {dian_debt_overdue_days} días de mora",
                "recommendation": "Establecer plan de pago con DIAN o pagar inmediatamente",
                "evidence": {
                    "dian_debt": dian_debt,
                    "overdue_days": dian_debt_overdue_days,
                },
            }
        return None


class Rule10InconsistenciaContable(CentinelaRule):
    """Regla 10: Balance y P&L no cuadran"""

    def __init__(self):
        super().__init__("R010", "Inconsistencia Contable", "critical")

    def evaluate(self, data: Dict) -> Optional[Dict]:
        assets = data.get("total_assets", 0)
        liabilities = data.get("total_liabilities", 0)
        equity = data.get("total_equity", 0)

        # Balance debe: Assets = Liabilities + Equity
        expected_assets = liabilities + equity
        variance = abs(assets - expected_assets)
        variance_percent = (variance / assets * 100) if assets > 0 else 0

        # Tolerar 0.1% de variación por redondeo
        if variance_percent > 0.1:
            return {
                "rule_id": self.rule_id,
                "rule_name": self.name,
                "severity": self.severity,
                "title": "Balance general no cuadra",
                "description": f"Diferencia de ${variance:,.0f} ({variance_percent:.2f}%)",
                "recommendation": "Auditar asientos contables y ciclos de cierre",
                "evidence": {
                    "total_assets": assets,
                    "total_liabilities": liabilities,
                    "total_equity": equity,
                    "expected_assets": expected_assets,
                    "variance": variance,
                    "variance_percent": variance_percent,
                },
            }
        return None


class CentinelaService:
    """Motor de reglas Centinela"""

    def __init__(self):
        self.rules = [
            Rule1UVTExcedido(),
            Rule2RetencionNoPagada(),
            Rule3FacturacionIrregular(),
            Rule4CambioRegimenNoReportado(),
            Rule5ProvisionesInsuficientes(),
            Rule6MargenBrutaSospechoso(),
            Rule7OperacionRelacionadaNoReportada(),
            Rule8ActivoSobrevaluado(),
            Rule9DeudaDIAN(),
            Rule10InconsistenciaContable(),
        ]
        logger.info(f"CentinelaService initialized with {len(self.rules)} rules")

    def evaluate(self, company_id: str, data: Dict) -> List[Dict]:
        """
        Evalúa todas las reglas contra los datos.
        Retorna lista de alertas activadas.
        """
        alerts = []

        for rule in self.rules:
            try:
                alert = rule.evaluate(data)
                if alert:
                    alert["company_id"] = company_id
                    alerts.append(alert)
                    logger.info(f"Rule {rule.rule_id} triggered for {company_id}")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")

        return alerts

    def save_alerts(self, alerts: List[Dict]) -> List[str]:
        """Guarda alertas en Supabase y retorna IDs creados"""
        if not alerts:
            return []

        try:
            supabase = get_supabase()
            saved_ids = []

            for alert in alerts:
                result = supabase.table("centinela_alerts").insert(alert).execute()
                if result.data:
                    saved_ids.append(result.data[0]["id"])
                logger.info(f"Alert saved: {alert['rule_id']} for {alert['company_id']}")

            return saved_ids
        except Exception as e:
            logger.error(f"Error saving alerts: {str(e)}")
            return []


# Singleton
_centinela_service = None


def get_centinela_service() -> CentinelaService:
    """Get or create Centinela service singleton"""
    global _centinela_service
    if _centinela_service is None:
        _centinela_service = CentinelaService()
    return _centinela_service
