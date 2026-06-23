"""
Pytest configuration: Configure Python path for backend imports.
Adds apps/backend to sys.path so tests can import main, core, etc.
"""

import sys
from pathlib import Path

# Add apps/backend to Python path
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))
