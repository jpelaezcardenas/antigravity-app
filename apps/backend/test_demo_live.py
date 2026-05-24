"""
DAY 6 LIVE DEMO TEST SCRIPT
Executes 4 segments with demo data to validate everything works end-to-end
"""

import requests
import json
from datetime import datetime

# Demo client ID (loaded in previous step)
COMPANY_ID = "ff1a8b7c-b0a1-422e-bc48-fac6242be027"
BASE_URL = "http://127.0.0.1:8000/api/v1"

print("=" * 70)
print("DAY 6 LIVE DEMO - 4 SEGMENTS TEST")
print("=" * 70)
print(f"Company ID: {COMPANY_ID}\n")

# ============================================================================
# SEGMENT 1: Pulso Diario (KPI Dashboard)
# ============================================================================

print("[SEGMENT 1] PULSO DIARIO - 8AM KPI Dashboard")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/pulso/today",
        json={"company_id": COMPANY_ID},
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Status: {response.status_code}")
        if "kpis" in data:
            kpis = data["kpis"]
            print(f"  Tax Filings Pending: {kpis.get('tax_filings_pending', 'N/A')}")
            print(f"  Compliance Status: {kpis.get('compliance_status', 'N/A')}")
            print(f"  Alerts Count: {kpis.get('alerts_count', 'N/A')}")
            print(f"  Audit Risk Score: {kpis.get('audit_risk_score', 'N/A')}")
    else:
        print(f"[FAIL] Status: {response.status_code} - {response.text[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)}")

# ============================================================================
# SEGMENT 2: Centinela Fiscal (Risk Alerts)
# ============================================================================

print("\n[SEGMENT 2] CENTINELA FISCAL - Risk Alerts")
print("-" * 70)

try:
    response = requests.get(
        f"{BASE_URL}/centinela/alerts",
        params={"company_id": COMPANY_ID},
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Status: {response.status_code}")
        print(f"  Total Alerts: {data.get('total_alerts', 0)}")
        by_severity = data.get('alerts_by_severity', {})
        print(f"  - Critical: {len(by_severity.get('critical', []))}")
        print(f"  - Warning: {len(by_severity.get('warning', []))}")
        print(f"  - Info: {len(by_severity.get('info', []))}")
    else:
        print(f"[FAIL] Status: {response.status_code} - {response.text[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)}")

# ============================================================================
# SEGMENT 3: Taty Q&A (RAG Assistant)
# ============================================================================

print("\n[SEGMENT 3] TATY - Q&A Assistant")
print("-" * 70)

try:
    question = "¿Cuál es la fecha de vencimiento para la declaración de renta 2025?"
    response = requests.post(
        f"{BASE_URL}/taty/ask",
        json={
            "company_id": COMPANY_ID,
            "question": question,
            "language": "es"
        },
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Status: {response.status_code}")
        print(f"  Question: {question}")
        print(f"  Answer: {data.get('answer', 'N/A')[:100]}...")
        print(f"  Confidence: {data.get('confidence', 'N/A')}")
    else:
        print(f"[FAIL] Status: {response.status_code} - {response.text[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)}")

# ============================================================================
# SEGMENT 4: Full Pipeline (7-Agent Orchestration)
# ============================================================================

print("\n[SEGMENT 4] FULL PIPELINE - 7-Agent Orchestration")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/agents/orchestrator/full-pipeline",
        json={
            "company_url": "https://contexia.com",
            "campaign_objective": "Lead generation para auditoría",
            "budget": 5000,
            "target_channels": ["instagram", "linkedin"],
            "company_id": COMPANY_ID
        },
        timeout=15
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Status: {response.status_code}")
        print(f"  Workflow ID: {data.get('workflow_id', 'N/A')}")
        print(f"  Total Time: {data.get('total_time', 'N/A')}")
        stages = data.get('stages', [])
        print(f"  Agents Executed: {len(stages)}/7")
        for i, stage in enumerate(stages[:3], 1):  # Show first 3
            print(f"    {i}. {stage.get('agent', 'unknown')}: {stage.get('status', 'unknown')} ({stage.get('duration', 'N/A')})")
        if len(stages) > 3:
            print(f"    ... + {len(stages)-3} more agents")
    else:
        print(f"[FAIL] Status: {response.status_code} - {response.text[:200]}")

except Exception as e:
    print(f"[ERROR] {str(e)}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("DEMO TEST COMPLETE")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print("All 4 segments tested. Check [OK] above for success, [FAIL]/[ERROR] for issues.")
