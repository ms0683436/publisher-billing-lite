# Publisher Billing Lite

A small full-stack app for managing publisher campaigns/orders and invoices (billing adjustments).

[![codecov](https://codecov.io/gh/ms0683436/publisher-billing-lite/graph/badge.svg?token=O13ADIRX0A)](https://codecov.io/gh/ms0683436/publisher-billing-lite)

## Features

- **Authentication** - JWT-based login with access token (15min) and refresh token (7 days, HttpOnly cookie). Auto-refresh on 401.
- **Campaigns & Invoices** - Manage publisher campaigns with line items and billing adjustments.
- **Comments** - Campaign comments with @mention support (↑/↓ navigate, Tab/Enter select, Esc close).
- **Notifications** - Real-time notification system for @mentions and replies via SSE (Server-Sent Events). Includes notification bell with badge, popover list, toast alerts, and full notifications page with pagination.
- **Change History** - Audit trail for editable fields (adjustments, comments). View timeline with old→new values, editor, and timestamp. Processed asynchronously via Procrastinate job queue.

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

### Background Processing

- **Job Queue:** Procrastinate (PostgreSQL-based)
  - **Why:** No additional infrastructure (uses existing PostgreSQL), supports LISTEN/NOTIFY for real-time job notifications, async-native Python.
- **Worker:** Change history worker with concurrency=5, entity-level locking for sequential processing per entity.

### Dev/Runtime

- Docker + Docker Compose
  - **Why:** One-command startup with consistent environments.

## Database Schema

```text
┌──────────────┐       ┌──────────────┐
│  campaigns   │       │   invoices   │
├──────────────┤       ├──────────────┤
│ id           │───1:1─│ id           │
│ name         │       │ campaign_id  │
└──────┬───────┘       └──────┬───────┘
       │                      │
       │ 1:N                  │ 1:N
       ▼                      ▼
┌──────────────┐       ┌────────────────────┐
│  line_items  │       │ invoice_line_items │
├──────────────┤       ├────────────────────┤
│ id           │───1:N─│ id                 │
│ campaign_id  │       │ invoice_id         │
│ name         │       │ line_item_id       │
│ booked_amount│       │ actual_amount      │
└──────────────┘       │ adjustments        │
                       └────────────────────┘
```

**Key relationships:**

- Campaign ↔ Invoice: 1:1 (one invoice per campaign)
- Campaign → LineItems: 1:N (campaign has many line items)
- Invoice → InvoiceLineItems: 1:N (invoice has many billing entries)
- LineItem → InvoiceLineItems: 1:N (line item can appear in multiple invoices)

## Run with Docker (recommended)

Prerequisites: Docker Desktop.

**Start the application:**

```bash
make up
```

This will automatically:

- Create `.env` from `.env.example` if it doesn't exist
- Build and start all services in detached mode (API, Web, Worker, Database)
- Run API database migrations via the `api-migrate` init service

**Services started:**

- `db` - PostgreSQL database
- `api` - FastAPI backend
- `web` - React frontend
- `change-history-worker` - Background worker for async change history processing

If you have port conflicts, edit `.env` and change `DB_PORT`, `API_PORT`, and/or `WEB_PORT`, then run `make up` again.

**Initialize database (seed data):**

Migrations are applied automatically on startup (via `api-migrate`). To import seed data:

```bash
make seed
```

This imports seed data from `apps/api/app/seeds/placements_teaser_data.json` and `apps/api/app/seeds/users.json`

If you prefer a one-command setup, `make db-setup` is still available (it will re-run migrations safely, then seed).

You can also run these steps separately:

- `make migrate` - Run migrations only
- `make seed` - Import seed data only (idempotent, safe to run multiple times)

**Access the application:**

- App: <http://localhost> (via nginx proxy)
- API Documentation (Swagger UI): <http://localhost/api/docs>
- API Documentation (ReDoc): <http://localhost/api/redoc>

Direct access (bypassing nginx):

- Web: <http://localhost:5173>
- API: <http://localhost:8000>

**Stop the application:**

```bash
make down
```

## Linting / formatting

```bash
make lint            # Run all linters (API + Web)
make lint-api        # Ruff + Mypy for Python
make lint-web        # ESLint for TypeScript

make format          # Format all code
make format-api      # Ruff format for Python
make format-check    # Check formatting without changes
```

> Note: Requires services to be running (`make up`)

## Testing

Run tests via Docker (recommended):

```bash
make test
```

Other useful targets:

```bash
make test-api         # API tests only
make test-unit        # unit tests only
make test-integration # integration tests only
make test-cov         # coverage
```

> Note: `make test` expects `.env` to define `DATABASE_URL` and `TEST_DATABASE_URL` (see `.env.example`).

To enforce these checks locally on commit:

```bash
# from repo root
uv run --project apps/api pre-commit install
```

CI also runs the same checks via `.github/workflows/python-quality.yml`.

### code coverage

[![codecov](https://codecov.io/gh/ms0683436/publisher-billing-lite/graph/badge.svg?token=O13ADIRX0A)](https://codecov.io/gh/ms0683436/publisher-billing-lite)
