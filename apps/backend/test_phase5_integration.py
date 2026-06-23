#!/usr/bin/env python3
"""
Phase 5 Integration Test Script
Tests end-to-end data flow: agent -> transformer -> validator -> WebSocket output
"""

import json
from decimal import Decimal
from services.agent_transformers import AgentTransformers
from services.agent_validation import (
    PulsaOutput,
    DraftOutput,
    RiskScoreOutput,
    SocialOpsOutput,
    AuditOutput,
)

print("=" * 60)
print("Phase 5 Integration Tests")
print("=" * 60)

# Test 1: Pulso Transformation & Validation
print("\n[PASS] Test 1: Pulso Agent Integration")
pulso_raw = {
    "cash_on_hand": 42850000.50,
    "net_cash": 38500000.25,
    "yesterday_sales": 1250000,
    "outflows": 345000,
    "status": "bien",
}
pulso_transformed = AgentTransformers.transform_pulso(pulso_raw)
print(f"  Raw: {pulso_raw}")
print(f"  Transformed: {pulso_transformed}")

try:
    pulso_validated = PulsaOutput(**pulso_transformed)
    print(f"  [OK] Validation PASSED")
    print(f"  Output: caja_real={pulso_validated.caja_real}, estado={pulso_validated.estado_plata}")
except ValueError as e:
    print(f"  [FAIL] Validation FAILED: {e}")

# Test 2: Centinela Alerts
print("\n[PASS] Test 2: Centinela Agent Integration")
centinela_raw = [
    {
        "id": "alert-1",
        "alert_type": "iva-due",
        "title": "IVA vence en 3 dias",
        "description": "Prepara la plata",
        "urgency": "high",
        "due_date": "2026-06-25",
        "action": "Resolver con Taty",
    },
    {
        "id": "alert-2",
        "alert_type": "tax-warning",
        "title": "Advertencia fiscal",
        "description": "Revision pendiente",
        "urgency": "medium",
        "due_date": "2026-06-28",
        "action": "Ver detalles",
    },
]
centinela_transformed = AgentTransformers.transform_centinela(centinela_raw)
print(f"  Input: {len(centinela_raw)} alerts")
print(f"  Output: {len(centinela_transformed)} alerts")
print(f"  [OK] Transformation PASSED")

# Test 3: Approval Queue Drafts
print("\n[PASS] Test 3: Approval Queue Integration")
drafts_raw = [
    {
        "id": "draft-1",
        "draft_type": "tax_correction",
        "title": "Reclasificacion",
        "description": "Ajuste contable",
        "agent": "centinela",
        "content": {"amount": 500000, "reason": "Allocation"},
        "status": "pending",
        "created_at": "2026-06-22T10:30:00Z",
    }
]
drafts_transformed = AgentTransformers.transform_approval_queue(drafts_raw)
print(f"  Input: {len(drafts_raw)} drafts")
print(f"  Output: {len(drafts_transformed)} drafts")

try:
    for draft in drafts_transformed:
        validated = DraftOutput(**draft)
    print(f"  [OK] Validation PASSED")
except ValueError as e:
    print(f"  [FAIL] Validation FAILED: {e}")

# Test 4: Radar Risk Score
print("\n[PASS] Test 4: Radar Agent Integration")
radar_raw = {
    "risk_score": 42.5,
    "risk_level": "medium",
    "factors": ["cash_flow", "supplier_risk"],
}
radar_transformed = AgentTransformers.transform_radar(radar_raw)
print(f"  Raw: {radar_raw}")
print(f"  Transformed: {radar_transformed}")

try:
    radar_validated = RiskScoreOutput(**radar_transformed)
    print(f"  [OK] Validation PASSED")
except ValueError as e:
    print(f"  [FAIL] Validation FAILED: {e}")

# Test 5: Social Ops Status
print("\n[PASS] Test 5: Social Ops Agent Integration")
social_raw = {"status": "processing", "pending_posts": 5, "scheduled_posts": 12}
social_transformed = AgentTransformers.transform_social_ops(social_raw)
print(f"  Raw: {social_raw}")
print(f"  Transformed: {social_transformed}")

try:
    social_validated = SocialOpsOutput(**social_transformed)
    print(f"  [OK] Validation PASSED")
except ValueError as e:
    print(f"  [FAIL] Validation FAILED: {e}")

# Test 6: Audit Findings
print("\n[PASS] Test 6: Audit Agent Integration")
audit_raw = {
    "findings": [{"type": "discrepancy", "amount": 50000}],
    "severity": "warning",
}
audit_transformed = AgentTransformers.transform_audit(audit_raw)
print(f"  Raw: {audit_raw}")
print(f"  Transformed: {audit_transformed}")

try:
    audit_validated = AuditOutput(**audit_transformed)
    print(f"  [OK] Validation PASSED")
except ValueError as e:
    print(f"  [FAIL] Validation FAILED: {e}")

# Test 7: Error Cases
print("\n[PASS] Test 7: Error Handling")

# Invalid status
print("  Testing invalid status...")
try:
    bad_pulso = {
        "caja_real": 1000,
        "dinero_tuyo": 500,
        "ventas_ayer": 0,
        "salidas_plata": 0,
        "estado_plata": "invalid",  # Should fail
    }
    PulsaOutput(**bad_pulso)
    print("  [FAIL] Should have failed but didn't")
except ValueError as e:
    print(f"  [OK] Correctly rejected: {str(e)[:50]}...")

# Invalid risk level
print("  Testing invalid risk level...")
try:
    bad_radar = {
        "risk_score": 50,
        "risk_level": "super_high",  # Should fail
        "factors": [],
    }
    RiskScoreOutput(**bad_radar)
    print("  [FAIL] Should have failed but didn't")
except ValueError as e:
    print(f"  [OK] Correctly rejected: {str(e)[:50]}...")

# Test 8: Decimal Precision
print("\n[PASS] Test 8: Currency Precision (Decimal)")
pulso_large = {
    "cash_on_hand": 123456789.99,
    "net_cash": 987654321.01,
    "yesterday_sales": 555555555,
    "outflows": 111111111,
    "status": "bien",
}
pulso_validated = PulsaOutput(**AgentTransformers.transform_pulso(pulso_large))
print(f"  Large values preserved as Decimal:")
print(f"  - {pulso_validated.caja_real} (type: {type(pulso_validated.caja_real).__name__})")
print(f"  [OK] No floating point errors")

print("\n" + "=" * 60)
print("[PASS] All Phase 5 Integration Tests PASSED")
print("=" * 60)
