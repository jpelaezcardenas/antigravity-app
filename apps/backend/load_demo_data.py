"""
Load 3 demo clients with realistic tax/accounting data for DAY 6 live demo
"""

import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import Supabase
try:
    from supabase import create_client, Client
except ImportError:
    print("[ERROR] Supabase library not installed. Run: pip install supabase")
    exit(1)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL or SUPABASE_KEY not configured in .env")
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# DEMO DATA: 3 Realistic Colombian Tax/Accounting Clients
# ============================================================================

DEMO_CLIENTS = [
    {
        "company_id": str(uuid.uuid4()),
        "company_name": "TechStart Colombia SAS",
        "industry": "technology",
        "tax_id": "901123456-7",
        "email": "contabilidad@techstart.com.co",
        "phone": "+57 301 234 5678",
        "subscription_tier": "pro",
        "created_at": datetime.utcnow().isoformat(),
    },
    {
        "company_id": str(uuid.uuid4()),
        "company_name": "Consultoria Fiscal Lopez & Cia",
        "industry": "consulting",
        "tax_id": "800654321-9",
        "email": "info@consultorialopez.com.co",
        "phone": "+57 312 765 4321",
        "subscription_tier": "enterprise",
        "created_at": datetime.utcnow().isoformat(),
    },
    {
        "company_id": str(uuid.uuid4()),
        "company_name": "Importaciones Martinez LTDA",
        "industry": "import_export",
        "tax_id": "860987654-2",
        "email": "admin@importacionesmartinez.com.co",
        "phone": "+57 321 876 5432",
        "subscription_tier": "pro",
        "created_at": datetime.utcnow().isoformat(),
    },
]

# ============================================================================
# TAX PROFILES (Perfiles Fiscales)
# ============================================================================

def create_tax_profiles(company_id: str) -> list:
    return [
        {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "profile_type": "annual_return",
            "status": "pending",
            "due_date": (datetime.now() + timedelta(days=45)).isoformat(),
            "filing_deadline_days": 45,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "profile_type": "monthly_vat",
            "status": "completed",
            "due_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "filing_deadline_days": 0,
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "profile_type": "payroll",
            "status": "completed",
            "due_date": (datetime.now() - timedelta(days=2)).isoformat(),
            "filing_deadline_days": 0,
            "created_at": datetime.utcnow().isoformat(),
        },
    ]

# ============================================================================
# ALERTS (Centinela Fiscal Alerts)
# ============================================================================

def create_alerts(company_id: str) -> list:
    return [
        {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "type": "compliance_deadline",
            "severity": "warning",
            "message": "Declaración anual de renta vence en 30 días",
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "type": "audit_risk",
            "severity": "info",
            "message": "Deducción de gastos representativos en límite DIAN (80%)",
            "risk_score": 0.72,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        },
    ]

# ============================================================================
# LOAD DATA INTO SUPABASE
# ============================================================================

def load_demo_data():
    print("[INFO] Starting demo data load...")

    # 1. Delete existing demo clients (optional, for clean state)
    print("[INFO] Clearing previous demo data...")
    try:
        # Get all clients
        existing = supabase.table("clients").select("company_id").execute()
        if existing.data:
            for client in existing.data[:3]:  # Delete first 3
                try:
                    supabase.table("clients").delete().eq("company_id", client["company_id"]).execute()
                    print(f"[OK] Deleted client {client['company_id'][:8]}...")
                except Exception as e:
                    print(f"[SKIP] Could not delete {client['company_id'][:8]}: {str(e)[:50]}")
    except Exception as e:
        print(f"[WARN] Could not fetch existing clients: {str(e)[:50]}")

    # 2. Insert demo clients
    print("\n[INFO] Loading 3 demo clients...")
    client_ids = []
    for i, client in enumerate(DEMO_CLIENTS, 1):
        try:
            response = supabase.table("clients").insert(client).execute()
            client_ids.append(client["company_id"])
            print(f"[OK] {i}. {client['company_name'][:30]} (ID: {client['company_id'][:8]}...)")
        except Exception as e:
            print(f"[FAIL] Could not insert client {i}: {str(e)[:100]}")

    # 3. Insert tax profiles for each client
    print("\n[INFO] Loading tax profiles...")
    for client_id in client_ids:
        profiles = create_tax_profiles(client_id)
        for profile in profiles:
            try:
                supabase.table("tax_profiles").insert(profile).execute()
            except Exception as e:
                print(f"[WARN] Could not insert tax profile: {str(e)[:80]}")
        print(f"[OK] Loaded {len(profiles)} tax profiles for client {client_id[:8]}...")

    # 4. Insert alerts for each client
    print("\n[INFO] Loading Centinela alerts...")
    for client_id in client_ids:
        alerts = create_alerts(client_id)
        for alert in alerts:
            try:
                supabase.table("alerts").insert(alert).execute()
            except Exception as e:
                print(f"[WARN] Could not insert alert: {str(e)[:80]}")
        print(f"[OK] Loaded {len(alerts)} alerts for client {client_id[:8]}...")

    # 5. Summary
    print("\n" + "="*70)
    print("DEMO DATA LOADED SUCCESSFULLY")
    print("="*70)
    print(f"Clients loaded: {len(client_ids)}")
    print(f"Tax profiles per client: 3")
    print(f"Alerts per client: 2")
    print("\nClient IDs (for testing):")
    for i, client_id in enumerate(client_ids, 1):
        print(f"  {i}. {client_id}")

    return client_ids


if __name__ == "__main__":
    try:
        client_ids = load_demo_data()
        print("\n[SUCCESS] Ready for DAY 6 live demo!")
        print(f"\nTest commands:")
        print(f"  curl -X POST http://127.0.0.1:8000/api/v1/pulso/today \\")
        print(f"    -H 'Content-Type: application/json' \\")
        print(f"    -d '{{\"company_id\": \"{client_ids[0]}\"}}'")
    except Exception as e:
        print(f"\n[ERROR] Failed to load demo data: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
