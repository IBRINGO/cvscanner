.PHONY: up down build logs backend frontend worker test test-backend test-frontend lint lint-backend lint-frontend migrate

COMPOSE = docker compose -f docker-compose.yml -f docker-compose.dev.yml

## Start the full stack (postgres, redis, backend, worker, frontend) via Docker Compose.
up:
	$(COMPOSE) up --build

## Stop and remove the stack's containers.
down:
	$(COMPOSE) down

## Build (or rebuild) all images without starting them.
build:
	$(COMPOSE) build

## Follow logs from every running service.
logs:
	$(COMPOSE) logs -f

## Run the Django dev server locally (outside Docker), using backend/.venv.
backend:
	cd backend && source .venv/Scripts/activate && python manage.py runserver 0.0.0.0:8000

## Run the Angular dev server locally (outside Docker).
frontend:
	cd frontend && npm start

## Run a Celery worker locally (outside Docker), using backend/.venv.
worker:
	cd backend && source .venv/Scripts/activate && celery -A workers.celery_app worker --loglevel=info

## Apply Django migrations locally (outside Docker).
migrate:
	cd backend && source .venv/Scripts/activate && python manage.py migrate

## Run both test suites.
test: test-backend test-frontend

## Run backend tests (pytest, SQLite in-memory — no services required).
test-backend:
	cd backend && source .venv/Scripts/activate && python -m pytest

## Run frontend tests headlessly (requires Chrome).
test-frontend:
	cd frontend && npx ng test --watch=false --browsers=ChromeHeadless

## Run both projects' static checks.
lint: lint-backend lint-frontend

## Ruff + Black (check-only) for the backend.
lint-backend:
	cd backend && source .venv/Scripts/activate && ruff check . && black --check .

## TypeScript type-checking for the frontend (no ESLint config yet — see README).
lint-frontend:
	cd frontend && npx tsc -p tsconfig.app.json --noEmit
