"""
Seed script to load 3 demo clients into Supabase usuarios table.
This script is meant to run AFTER RLS has been disabled on the usuarios table.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from infrastructure.supabase_client import supabase_client
from datetime import datetime
import uuid

# Demo users that match what the auth_service.login() expects
DEMO_USERS = [
    {
        "id": str(uuid.uuid4()),
        "email": "jpelaezcardenas@gmail.com",
        "nombre_empresa": "Contexia",
        "nit": "9.867.082-4",
        "plan": "enterprise",
        "password_hash": "$2b$12$placeholder.contexia.context",  # Placeholder that auth_service recognizes
        "porcentaje_renta": 0.35,
        "porcentaje_iva": 0.19,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "email": "fperez@ferez.co",
        "nombre_empresa": "FEREZ SAS",
        "nit": "900.123.456-7",
        "plan": "enterprise",
        "password_hash": "$2b$12$placeholder.ferez.context",  # Placeholder that auth_service recognizes
        "porcentaje_renta": 0.35,
        "porcentaje_iva": 0.19,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "email": "carlos@importacionesmtz.co",
        "nombre_empresa": "Importaciones Martinez",
        "nit": "800.456.789-0",
        "plan": "growth",
        "password_hash": "$2b$12$placeholder.martinez.context",  # Placeholder that auth_service recognizes
        "porcentaje_renta": 0.35,
        "porcentaje_iva": 0.19,
        "created_at": datetime.utcnow().isoformat()
    }
]

def seed_usuarios():
    """Insert demo usuarios into Supabase."""
    try:
        print("[INFO] Starting seed of demo usuarios...")

        # Insert each user
        for user in DEMO_USERS:
            print("[INFO] Inserting {} ({})...".format(user['nombre_empresa'], user['email']))

            response = supabase_client.table("usuarios").insert(user).execute()

            if response.data:
                print("[OK] {} inserted successfully (ID: {})".format(user['nombre_empresa'], user['id']))
            else:
                print("[FAIL] Failed to insert {}".format(user['nombre_empresa']))
                print("  Response: {}".format(response))

        print("\n[SUCCESS] All demo usuarios seeded!")

        # Verify insertion
        print("\n[INFO] Verifying seeded data...")
        response = supabase_client.table("usuarios").select("id, email, nombre_empresa").execute()
        print("[INFO] Total usuarios in database: {}".format(len(response.data)))
        for user in response.data:
            print("  - {} ({})".format(user['nombre_empresa'], user['email']))

    except Exception as e:
        print("[ERROR] Failed to seed usuarios: {}".format(e))
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = seed_usuarios()
    sys.exit(0 if success else 1)
