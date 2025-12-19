"""Procrastinate application configuration for async task processing."""

from __future__ import annotations

import procrastinate

from ..settings import get_settings


def _create_app() -> procrastinate.App:
    """Create the Procrastinate application instance."""
    settings = get_settings()

    # Convert asyncpg URL to psycopg format for Procrastinate
    # asyncpg: postgresql+asyncpg://user:pass@host/db
    # psycopg: postgresql://user:pass@host/db
    db_url = settings.database_url.replace("+asyncpg", "")

    return procrastinate.App(
        connector=procrastinate.PsycopgConnector(conninfo=db_url, kwargs={}),
        import_paths=["app.queue.tasks"],
    )


# Module-level app instance for CLI usage (procrastinate --app=...)
app = _create_app()


def get_procrastinate_app() -> procrastinate.App:
    """Get the Procrastinate application instance."""
    return app
