.PHONY: help up down migrate migration-generate migration-downgrade migration-current migration-history db-reset seed db-setup test test-unit test-integration test-api test-cov

help:
	@echo "Available commands:"
	@echo "  make up                   - Start all services (creates .env if needed)"
	@echo "  make down                 - Stop all services"
	@echo "  make migrate              - Run all migrations (upgrade to head)"
	@echo "  make migration-generate   - Generate a new migration (autogenerate)"
	@echo "  make migration-downgrade  - Downgrade database by 1 revision"
	@echo "  make migration-current    - Show current migration revision"
	@echo "  make migration-history    - Show migration history"
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

# Start all services (create .env if needed)
up:
	@if [ ! -f .env ]; then \
		echo "📄 .env not found, creating from .env.example..."; \
		cp .env.example .env; \
		echo "✅ .env created. You can edit it to change ports if needed."; \
	else \
		echo "✅ .env already exists."; \
	fi
	@echo "🚀 Starting services..."
	docker compose up --build -d
	@echo "✅ Services started!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make db-setup' to initialize the database"
	@echo "  2. Access the app at http://localhost:5173"

# Stop all services
down:
	@echo "🛑 Stopping services..."
	docker compose down
	@echo "✅ Services stopped!"

# Run migrations (upgrade to head)
migrate:
	docker compose exec api uv run alembic upgrade head

# Generate a new migration
migration-generate:
	@read -p "Enter migration message: " message; \
	docker compose exec api uv run alembic revision --autogenerate -m "$$message"

# Downgrade database by 1 revision
migration-downgrade:
	docker compose exec api uv run alembic downgrade -1

# Show current migration revision
migration-current:
	docker compose exec api uv run alembic current

# Show migration history
migration-history:
	docker compose exec api uv run alembic history --verbose

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
	@echo "✅ Database setup complete!"

# Ensure test database exists
test-db-create:
	@docker compose exec db psql -U publisher -d publisher_billing -tc "SELECT 1 FROM pg_database WHERE datname = 'publisher_billing_test'" | grep -q 1 || \
		docker compose exec db psql -U publisher -d publisher_billing -c "CREATE DATABASE publisher_billing_test;"

# Run all tests
test: test-db-create
	@echo "🧪 Running all tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest -v
	@echo "✅ All tests passed!"

# Run unit tests only
test-unit:
	@echo "🧪 Running unit tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest tests/unit -v
	@echo "✅ Unit tests passed!"

# Run integration tests only
test-integration: test-db-create
	@echo "🧪 Running integration tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest tests/integration -v
	@echo "✅ Integration tests passed!"

# Run API tests only
test-api: test-db-create
	@echo "🧪 Running API tests..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest tests/api -v
	@echo "✅ API tests passed!"

# Run tests with coverage report
test-cov: test-db-create
	@echo "🧪 Running tests with coverage..."
	docker compose exec -e PYTHONPATH=/app api uv run --group test pytest --cov=app --cov-report=term-missing -v
	@echo "✅ Tests with coverage complete!"
