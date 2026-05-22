#!/usr/bin/env python
"""
Test script to verify all API endpoints have proper parameter handling
Run this to verify the endpoint fixes work correctly
"""

import requests
import json
from datetime import datetime

# Backend URL
API_BASE = "http://localhost:8000/api/v1"

def test_health():
    """Test basic health endpoint"""
    print("\n[TEST] Health Check")
    try:
        resp = requests.get(f"{API_BASE}/agents/orchestrator/health", timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {resp.json()}")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_pulso_today():
    """Test Pulso Diario today endpoint"""
    print("\n[TEST] POST /pulso/today")
    try:
        payload = {
            "company_id": "31676930-b476-472b-bced-fd25f973cf8a"  # Demo client UUID
        }
        resp = requests.post(
            f"{API_BASE}/agents/pulso/today",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {json.dumps(resp.json(), indent=2)[:200]}...")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_pulso_latest():
    """Test Pulso Diario latest endpoint"""
    print("\n[TEST] GET /pulso/latest")
    try:
        company_id = "31676930-b476-472b-bced-fd25f973cf8a"
        resp = requests.get(
            f"{API_BASE}/agents/pulso/latest",
            params={"company_id": company_id},
            timeout=5
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {json.dumps(resp.json(), indent=2)[:200]}...")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_centinela_check():
    """Test Centinela risk check"""
    print("\n[TEST] POST /centinela/check-risks")
    try:
        payload = {
            "company_id": "31676930-b476-472b-bced-fd25f973cf8a"
        }
        resp = requests.post(
            f"{API_BASE}/agents/centinela/check-risks",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {json.dumps(resp.json(), indent=2)[:200]}...")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_centinela_alerts():
    """Test Centinela alerts endpoint"""
    print("\n[TEST] GET /centinela/alerts")
    try:
        company_id = "31676930-b476-472b-bced-fd25f973cf8a"
        resp = requests.get(
            f"{API_BASE}/agents/centinela/alerts",
            params={"company_id": company_id},
            timeout=5
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {json.dumps(resp.json(), indent=2)[:200]}...")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_taty_ask():
    """Test Taty question endpoint"""
    print("\n[TEST] POST /taty/ask")
    try:
        payload = {
            "company_id": "31676930-b476-472b-bced-fd25f973cf8a",
            "question": "¿Cuál es la fecha de vencimiento para la declaración de renta 2025?",
            "language": "es"
        }
        resp = requests.post(
            f"{API_BASE}/agents/taty/ask",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {json.dumps(resp.json(), indent=2)[:300]}...")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_taty_history():
    """Test Taty history endpoint"""
    print("\n[TEST] GET /taty/history")
    try:
        company_id = "31676930-b476-472b-bced-fd25f973cf8a"
        resp = requests.get(
            f"{API_BASE}/agents/taty/history",
            params={"company_id": company_id, "limit": 5},
            timeout=5
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {json.dumps(resp.json(), indent=2)[:200]}...")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_full_pipeline():
    """Test full pipeline endpoint"""
    print("\n[TEST] POST /orchestrator/full-pipeline")
    try:
        payload = {
            "company_url": "https://contexia.online",
            "campaign_objective": "Lead generation para auditoría sombra",
            "budget": 5000,
            "target_channels": ["instagram", "linkedin"]
        }
        resp = requests.post(
            f"{API_BASE}/agents/orchestrator/full-pipeline",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Workflow ID: {data.get('workflow_id')}")
            print(f"Total time: {data.get('total_execution_time_seconds')}s")
            print(f"Agent stages: {len(data.get('agent_stages', []))}/7")
            return True
        else:
            print(f"Error: {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Run all endpoint tests"""
    print("="*70)
    print("ENDPOINT PARAMETER FIX - TEST SUITE")
    print("="*70)

    results = {
        "Health Check": test_health(),
        "Pulso Today (POST)": test_pulso_today(),
        "Pulso Latest (GET)": test_pulso_latest(),
        "Centinela Check (POST)": test_centinela_check(),
        "Centinela Alerts (GET)": test_centinela_alerts(),
        "Taty Ask (POST)": test_taty_ask(),
        "Taty History (GET)": test_taty_history(),
        "Full Pipeline (POST)": test_full_pipeline(),
    }

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\nResult: {passed_count}/{total_count} tests passed")

    return all(results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
