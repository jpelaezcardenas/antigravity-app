#!/bin/bash

echo "?? Starting development environment..."
echo ""
echo "This will run all services in parallel."
echo "Press Ctrl+C to stop all services."
echo ""

# Cleanup on exit
cleanup() {
    echo ""; echo "?? Stopping all services..."; kill ${jobs -p} 2>/dev/null; exit 0
}
trap cleanup SIGINT

# Backend
echo "?? Starting FastAPI backend on port 8080..."
cd backend
python -m uvicorn main:app --reload &
BACKEND_PID=$!
cd ..

# Frontend Dashboard
echo "?? Starting dashboard on port 5173..."
cd frontend/dashboard
npm run dev &
DASHBOARD_PID=$!
cd ../..

# Frontend Wizard
echo "?? Starting wizard on port 3000..."
cd frontend/wizard
npm run dev &
WIZARD_PID=$!
cd ../..

echo ""
echo "? All services started!"
echo "  - Backend: http://localhost:8080"
echo "  - Dashboard: http://localhost:5173"
echo "  - Wizard: http://localhost:3000"
echo ""

wait
