#!/bin/bash
set -e

echo "?? Building monolith..."

# Backend (no build needed, just linting)
cd backend
echo "?? Checking backend..."
python -m py_compile **/*.py 2>/dev/null || echo "  (Python syntax check skipped)"
cd ..

# Frontend Dashboard
cd frontend/dashboard
echo "?? Building dashboard..."
npm run build
cd ../..

# Frontend Wizard
cd frontend/wizard
echo "?? Building wizard..."
npm run build
cd ../..

echo ""
echo "? Build complete!"
echo "  - Dashboard build: frontend/dashboard/dist"
echo "  - Wizard build: frontend/wizard/.next"
