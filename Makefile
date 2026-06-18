.PHONY: help install dev test lint format migrate docker-up docker-down

help:
	@echo "PrepOS Development Commands"
	@echo "  make install     - Install backend & frontend dependencies"
	@echo "  make dev         - Start backend & frontend dev servers"
	@echo "  make test        - Run backend tests"
	@echo "  make lint        - Run linters (ruff, prettier)"
	@echo "  make format      - Format code (ruff, prettier)"
	@echo "  make migrate     - Run Alembic migrations"
	@echo "  make docker-up   - Start all services via Docker Compose"
	@echo "  make docker-down - Stop all services"

install:
	cd backend && pip install -r requirements/dev.txt
	cd frontend && npm install

dev:
	@echo "Start backend: cd backend && uvicorn app.main:app --reload"
	@echo "Start frontend: cd frontend && npm run dev"

test:
	cd backend && python -m pytest

lint:
	cd backend && ruff check .
	cd frontend && npx tsc --noEmit && npx prettier --check "src/**/*.{ts,tsx}"

format:
	cd backend && ruff format .
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

migrate:
	cd backend && alembic upgrade head

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
