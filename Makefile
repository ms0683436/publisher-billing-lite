.PHONY: help up down up-prod-ngrok down-prod ngrok ngrok-down web-install migrate migration-generate migration-downgrade db-reset seed db-setup test test-unit test-integration test-api test-cov lint lint-api lint-api-fix lint-web format format-api format-check

help:
	@echo "Available commands:"
	@echo "  make up                   - Start core services with nginx (creates .env if needed)"
	@echo "  make down                 - Stop core services (keeps ngrok running)"
	@echo "  make ngrok                - Start ngrok for external access"
	@echo "  make migrate              - Run all migrations (upgrade to head)"
	@echo "  make migration-generate   - Generate a new migration (autogenerate)"
	@echo "  make migration-downgrade  - Downgrade database by 1 revision"
	@echo "  make db-reset             - Reset database (downgrade to base, then upgrade to head)"
	@echo "  make seed                 - Import seed data from seed.json (idempotent)"
	@echo "  make db-setup             - Full database setup (migrate + seed)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests only"
	@echo "  make test-api             - Run API tests only"
	@echo "  make test-cov             - Run tests with coverage report"
	@echo ""
	@echo "Linting / Formatting:"
	@echo "  make lint                 - Run all linters (API + Web)"
	@echo "  make lint-api             - Run Ruff + Mypy (Python)"
	@echo "  make lint-api-fix         - Auto-fix + format Python via Ruff"
	@echo "  make lint-web             - Run ESLint (TypeScript)"
	@echo "  make format               - Format all code"
	@echo "  make format-api           - Run Ruff format (Python)"
	@echo "  make format-check         - Check formatting without changes"

# Start core services (create .env if needed)
up:
	@if [ ! -f .env ]; then \
		echo ".env not found, creating from .env.example..."; \
		cp .env.example .env; \
		echo "Done. .env created. You can edit it to change ports if needed."; \
	else \
		echo ".env already exists."; \
	fi
	@echo "Starting core services..."
	docker compose up --build -d db redis api notification-worker change-history-worker web nginx
	@echo "Done. Services started!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make db-setup' to initialize the database"
	@echo "  2. Access the app at http://localhost"
	@echo "  3. Run 'make ngrok' for external access via ngrok"

# Update web dependencies in named volume (run when package.json changes)
web-install:
	docker compose exec web pnpm install --frozen-lockfile

# Stop core services (keeps ngrok running if started separately)
down:
	@echo "Stopping core services..."
	docker compose down db redis api notification-worker change-history-worker web nginx
	@echo "Done. Core services stopped!"

# Start all production services with ngrok
up-prod-ngrok:
	@echo "Starting production services with ngrok..."
	docker compose -f docker-compose.prod.yml up --build -d
	@echo "Done. Production services started!"
	@echo "Access the app at http://localhost (or via ngrok)"

# Stop all production services
down-prod:
	@echo "Stopping production services..."
	docker compose -f docker-compose.prod.yml down
	@echo "Done. Production services stopped!"

# Start ngrok for external access
ngrok:
	@echo "Starting ngrok..."
	docker compose up -d ngrok
	@echo "Done. ngrok started! Dashboard at http://localhost:4040"

# Stop ngrok
ngrok-down:
	@echo "Stopping ngrok..."
	docker compose stop ngrok
	docker compose rm -f ngrok
	@echo "Done. ngrok stopped!"

# Run migrations (upgrade to head)
migrate:
	docker compose run --rm api-migrate

# Generate a new migration
migration-generate:
	@read -p "Enter migration message: " message; \
	docker compose exec api uv run alembic revision --autogenerate -m "$$message"

# Downgrade database by 1 revision
migration-downgrade:
	docker compose exec api uv run alembic downgrade -1

# Reset database (downgrade to base, then upgrade to head)
db-reset:
	docker compose exec api uv run alembic downgrade base
	docker compose exec api uv run alembic upgrade head

# Import seed data (idempotent - can be run multiple times)
seed:
	docker compose exec api uv run python -m app.seed

# Full database setup (migrate + seed)
db-setup:
	@echo "Running migrations..."
	@$(MAKE) migrate
	@echo "Importing seed data..."
	@$(MAKE) seed
	@echo "Done. Database setup complete!"

# Ensure test database exists
test-db-create:
	@docker compose exec db psql -U publisher -d publisher_billing -tc "SELECT 1 FROM pg_database WHERE datname = 'publisher_billing_test'" | grep -q 1 || \
		docker compose exec db psql -U publisher -d publisher_billing -c "CREATE DATABASE publisher_billing_test;"

# Run all tests
test: test-db-create
	@echo "Running all tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest -v
	@echo "Done. All tests passed!"

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest tests/unit -v
	@echo "Done. Unit tests passed!"

# Run integration tests only
test-integration: test-db-create
	@echo "Running integration tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest tests/integration -v
	@echo "Done. Integration tests passed!"

# Run API tests only
test-api: test-db-create
	@echo "Running API tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest tests/api -v
	@echo "Done. API tests passed!"

# Run tests with coverage report
test-cov: test-db-create
	@echo "Running tests with coverage..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest --cov=app --cov-report=term-missing -v
	@echo "Done. Tests with coverage complete!"

# Linting
lint: lint-api lint-web

lint-api:
	@echo "Running Python linters..."
	docker compose exec api uv run ruff check app tests
	docker compose exec api uv run mypy app
	@echo "Done. Python linting passed!"

lint-api-fix:
	@echo "Auto-fixing + formatting Python (Ruff)..."
	docker compose exec api uv run ruff check --fix app tests
	docker compose exec api uv run ruff format app tests
	@echo "Done. Ruff fix + format complete!"

lint-web:
	@echo "Running TypeScript linter..."
	docker compose exec web pnpm lint
	@echo "Done. TypeScript linting passed!"

# Formatting
format: format-api

format-api:
	@echo "Formatting Python code..."
	docker compose exec api uv run ruff format .
	@echo "Done. Python formatting complete!"

format-check:
	@echo "Checking Python formatting..."
	docker compose exec api uv run ruff format --check .
	@echo "Done. Python formatting check passed!"
