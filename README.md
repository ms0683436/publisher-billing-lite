# Publisher Billing Lite

A small full-stack app for managing publisher campaigns/orders and invoices (billing adjustments).

## Features

- **Authentication** - JWT-based login with access token (15min) and refresh token (7 days, HttpOnly cookie). Auto-refresh on 401.
- **Campaigns & Invoices** - Manage publisher campaigns with line items and billing adjustments.
- **Comments** - Campaign comments with @mention support (↑/↓ navigate, Tab/Enter select, Esc close).
- **Change History** - Audit trail for editable fields (adjustments, comments). View timeline with old→new values, editor, and timestamp.

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
  - API Documentation (Swagger UI): <http://localhost:8000/docs>
  - API Documentation (ReDoc): <http://localhost:8000/redoc>

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
