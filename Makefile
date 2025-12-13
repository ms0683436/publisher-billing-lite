.PHONY: help up down migrate migration-generate migration-downgrade migration-current migration-history db-reset seed db-setup

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
