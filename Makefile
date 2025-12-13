.PHONY: help migrate migration-generate migration-downgrade migration-current migration-history db-reset

help:
	@echo "Available commands:"
	@echo "  make migrate              - Run all migrations (upgrade to head)"
	@echo "  make migration-generate   - Generate a new migration (autogenerate)"
	@echo "  make migration-downgrade  - Downgrade database by 1 revision"
	@echo "  make migration-current    - Show current migration revision"
	@echo "  make migration-history    - Show migration history"
	@echo "  make db-reset             - Reset database (downgrade to base, then upgrade to head)"

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
