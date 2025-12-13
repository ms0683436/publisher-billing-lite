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

```bash
docker compose up --build
```

- Web: <http://localhost:5173>
- API: <http://localhost:8000>
  - Example endpoint: <http://localhost:8000/api/v1/hello>

To stop:

```bash
docker compose down
```

## Local Development (optional)

### API

```bash
cd apps/api
uv sync --frozen
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web

```bash
cd apps/web
pnpm install --frozen-lockfile
VITE_API_URL=http://localhost:8000 pnpm dev --host 0.0.0.0 --port 5173
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
