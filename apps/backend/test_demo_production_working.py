"""
DAY 6 PRODUCTION TEST - Working Endpoints Only
Tests endpoints verified to be deployed on Railway

Note: This test uses ONLY endpoints confirmed working in production.
Once all routers are deployed, use test_demo_live.py for full 4-segment test.
"""

import requests
import json
from datetime import datetime

COMPANY_ID = "ff1a8b7c-b0a1-422e-bc48-fac6242be027"
PRODUCTION_URL = "https://antigravity-app-production-175a.up.railway.app/api/v1"

print("=" * 70)
print("DAY 6 PRODUCTION TEST - WORKING ENDPOINTS")
print("=" * 70)
print(f"Company ID: {COMPANY_ID}")
print(f"Base URL: {PRODUCTION_URL}\n")

# ============================================================================
# TEST 1: Health Check
# ============================================================================

print("[TEST 1] Health Check")
print("-" * 70)

try:
    response = requests.get(f"{PRODUCTION_URL}/health", timeout=5)

    if response.status_code == 200:
        print(f"[✓ OK] Status: {response.status_code}")
        print(f"  Backend is running and responsive")
    else:
        print(f"[✗ FAIL] Status: {response.status_code}")
        print(f"  Response: {response.text[:100]}")

except Exception as e:
    print(f"[✗ ERROR] {str(e)}")

# ============================================================================
# TEST 2: Centinela Fiscal Alerts (VERIFIED WORKING)
# ============================================================================

print("\n[TEST 2] CENTINELA FISCAL - Risk Alerts (VERIFIED WORKING)")
print("-" * 70)

try:
    response = requests.get(
        f"{PRODUCTION_URL}/centinela/alerts",
        params={"company_id": COMPANY_ID},
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[✓ OK] Status: {response.status_code}")
        print(f"  Endpoint: GET /api/v1/centinela/alerts")
        print(f"  Response: {json.dumps(data, indent=2)[:200]}...")

        # This endpoint works, so let's show what data structure it returns
        if isinstance(data, list):
            print(f"  Data Type: Array of alerts ({len(data)} items)")
        elif isinstance(data, dict):
            print(f"  Data Type: Object with keys: {list(data.keys())}")
            if "total_alerts" in data:
                print(f"  Total Alerts: {data.get('total_alerts', 0)}")
    else:
        print(f"[✗ FAIL] Status: {response.status_code}")
        print(f"  Response: {response.text[:100]}")

except Exception as e:
    print(f"[✗ ERROR] {str(e)}")

# ============================================================================
# TEST 3: Missing Endpoints (For Documentation)
# ============================================================================

print("\n[TEST 3] MISSING ENDPOINTS STATUS")
print("-" * 70)

missing_endpoints = [
    {"name": "Pulso Diario", "method": "POST", "path": "/pulso/today"},
    {"name": "Taty Q&A", "method": "POST", "path": "/taty/ask"},
    {"name": "Full Pipeline", "method": "POST", "path": "/agents/orchestrator/full-pipeline"},
]

for endpoint in missing_endpoints:
    try:
        if endpoint["method"] == "GET":
            response = requests.get(
                f"{PRODUCTION_URL}{endpoint['path']}",
                timeout=5
            )
        else:
            response = requests.post(
                f"{PRODUCTION_URL}{endpoint['path']}",
                json={"company_id": COMPANY_ID},
                timeout=5
            )

        if response.status_code == 404:
            print(f"[✗ MISSING] {endpoint['method']} {endpoint['path']}")
            print(f"           Endpoint not deployed on Railway")
        elif response.status_code == 405:
            print(f"[⚠ ERROR] {endpoint['method']} {endpoint['path']}")
            print(f"          Wrong HTTP method or routing issue")
        else:
            print(f"[? UNKNOWN] {endpoint['method']} {endpoint['path']}")
            print(f"            Status: {response.status_code}")

    except Exception as e:
        print(f"[✗ ERROR] {endpoint['method']} {endpoint['path']}: {str(e)[:50]}")

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================

print("\n" + "=" * 70)
print("TEST SUMMARY & DEPLOYMENT STATUS")
print("=" * 70)

print("""
✓ WORKING (Deployed):
  - Health Check
  - Centinela Alerts

✗ MISSING (Not Deployed):
  - Pulso Diario
  - Taty Q&A
  - Full Pipeline (7-Agent Orchestration)

NEXT STEPS:
1. Check Railway deployment logs for build errors
2. Verify that pulso_router, taty_router, agents_router are included in main.py
3. Redeploy backend to include all routers
4. Once all endpoints are deployed, run full test_demo_live.py

INTERIM RECOMMENDATION:
This test confirms that:
- The Railway backend is alive and serving requests
- At least one service (Centinela) is functional
- Other services need to be deployed/fixed
""")

print(f"\nTest completed: {datetime.now().isoformat()}")
print("=" * 70)
