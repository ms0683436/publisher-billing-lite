# Publisher Billing Lite

A small full-stack app for managing publisher campaigns/orders and invoices (billing adjustments).

## Repo Conventions

- Commit message guidelines: see [docs/commit-message-guidelines.md](docs/commit-message-guidelines.md)

## Tech Stack

### Backend (API)

- **Language:** Python 3.12
- **Framework:** FastAPI + Uvicorn
- **Why:** Fast to iterate, simple request/response APIs, great typing/docs support.
- **Dependency tooling:** `uv`
  - **Why:** Reproducible, fast installs via `uv.lock`.

### Frontend (Web)

- **Language:** TypeScript
- **Framework:** React (Vite)
- **UI:** MUI
- **Why:** React + TS gives strong developer ergonomics; Vite keeps dev server/builds fast; MUI provides solid, accessible UI primitives quickly.
- **Package manager:** pnpm
  - **Why:** Fast, disk-efficient installs; pinned via `packageManager` for reproducibility.

### Dev/Runtime

- Docker + Docker Compose
  - **Why:** One-command startup with consistent environments.

## Run with Docker (recommended)

Prerequisites: Docker Desktop.

**Start the application:**

```bash
make up
```

This will automatically:

- Create `.env` from `.env.example` if it doesn't exist
- Build and start all services in detached mode

If you have port conflicts, edit `.env` and change `DB_PORT`, `API_PORT`, and/or `WEB_PORT`, then run `make up` again.

**Initialize database (first time only):**

After containers are running, set up the database schema and import seed data:

```bash
make db-setup
```

This will:

1. Run database migrations (create tables)
2. Import seed data from `apps/api/app/seeds/placements_teaser_data.json`

You can also run these steps separately:

- `make migrate` - Run migrations only
- `make seed` - Import seed data only (idempotent, safe to run multiple times)

**Access the application:**

- Web: <http://localhost:5173>
- API: <http://localhost:8000>
  - Example endpoint: <http://localhost:8000/api/v1/hello>

**Stop the application:**

```bash
make down
```

## Linting / formatting

### Web (frontend)

```bash
cd apps/web
pnpm lint
pnpm build
```

### API (backend, Python 3.12)

```bash
cd apps/api
uv sync --frozen --group dev
uv run black app
uv run ruff check app
uv run mypy app
```

To enforce these checks locally on commit:

```bash
# from repo root
uv run --project apps/api pre-commit install
```

CI also runs the same checks via `.github/workflows/python-quality.yml`.
