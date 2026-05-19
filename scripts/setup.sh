#!/bin/bash
set -e

echo "?? Setting up antigravity-app monolith..."

# Backend setup
cd backend
pip install -r requirements.txt
cp ../.config/.env.example .env
echo "? Backend dependencies installed"
cd ..

# Frontend dashboard
cd frontend/dashboard
npm install
echo "? Frontend (dashboard) dependencies installed"
cd ../..

# Frontend wizard
cd frontend/wizard
npm install
echo "? Frontend (wizard) dependencies installed"
cd ../..

echo ""; echo "? Setup complete!"; echo ""
echo "Next steps:"
echo "  1. Copy .config/.env.example to backend/.env and fill in your credentials"
echo "  2. Run: ./scripts/dev.sh"
