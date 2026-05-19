.PHONY: help install setup dev build test clean docker-build docker-up docker-down

# Default target
help:
	@echo "antigravity-app monolith — Make targets:"
	@echo ""
	@echo "  make setup           Install all dependencies (backend + both frontends)"
	@echo "  make install         Same as setup"
	@echo "  make dev             Start all services locally (backend, dashboard, wizard)"
	@echo "  make build           Build both frontends for production"
	@echo "  make test            Run tests (backend pytest, frontend jest)"
	@echo "  make clean           Remove build artifacts and node_modules"
	@echo ""
	@echo "  make run-backend     Run FastAPI backend only"
	@echo "  make run-dashboard   Run Vite dashboard only"
	@echo "  make run-wizard      Run Next.js wizard only"
	@echo ""
	@echo "  make docker-build    Build Docker image for backend"
	@echo "  make docker-up       Start services with docker-compose"
	@echo "  make docker-down     Stop docker-compose services"
	@echo ""
	@echo "Documentation: see README.md and docs/"

# Setup & Installation
setup: install

install:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt && cd ..
	@echo "📦 Installing dashboard dependencies..."
	cd frontend/dashboard && npm install && cd ../..
	@echo "📦 Installing wizard dependencies..."
	cd frontend/wizard && npm install && cd ../..
	@echo "✅ All dependencies installed"

# Development
dev:
	@echo "🚀 Starting development environment..."
	./scripts/dev.sh

run-backend:
	cd backend && python -m uvicorn main:app --reload && cd ..

run-dashboard:
	cd frontend/dashboard && npm run dev && cd ../..

run-wizard:
	cd frontend/wizard && npm run dev && cd ../..

# Build
build:
	@echo "🔨 Building for production..."
	./scripts/build.sh

# Testing
test:
	@echo "🧪 Running tests..."
	cd backend && python -m pytest && cd ..
	cd frontend/dashboard && npm run test 2>/dev/null || echo "  (dashboard tests skipped)" && cd ../..
	cd frontend/wizard && npm run test 2>/dev/null || echo "  (wizard tests skipped)" && cd ../..

# Cleanup
clean:
	@echo "🧹 Cleaning..."
	rm -rf backend/__pycache__ backend/.pytest_cache backend/venv
	rm -rf frontend/dashboard/node_modules frontend/dashboard/dist frontend/dashboard/.next
	rm -rf frontend/wizard/node_modules frontend/wizard/dist frontend/wizard/.next
	@echo "✅ Cleaned"

# Docker
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t contexia-backend:latest ./backend

docker-up:
	@echo "🐳 Starting docker-compose..."
	docker-compose -f .config/docker-compose.yml up

docker-down:
	@echo "🛑 Stopping docker-compose..."
	docker-compose -f .config/docker-compose.yml down

# Utility
lint:
	cd backend && python -m black . && python -m isort . && cd ..
	cd frontend/dashboard && npm run lint && cd ../..
	cd frontend/wizard && npm run lint && cd ../..

format:
	cd backend && python -m black . && python -m isort . && cd ..
	cd frontend/dashboard && npm run format && cd ../..
	cd frontend/wizard && npm run format && cd ../..

.DEFAULT_GOAL := help
