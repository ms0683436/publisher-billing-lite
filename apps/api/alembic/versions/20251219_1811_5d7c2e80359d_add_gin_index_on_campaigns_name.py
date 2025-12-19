"""add_gin_index_on_campaigns_name

Revision ID: 5d7c2e80359d
Revises: a5020676b7cb
Create Date: 2025-12-19 18:11:50.027389+08:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5d7c2e80359d"
down_revision: str | Sequence[str] | None = "a5020676b7cb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add GIN index on campaigns.name for efficient ILIKE searches."""
    # Enable pg_trgm extension for trigram-based text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create GIN index using trigram ops for ILIKE optimization
    op.execute(
        "CREATE INDEX ix_campaigns_name_trgm ON campaigns USING gin (name gin_trgm_ops)"
    )


def downgrade() -> None:
    """Remove GIN index on campaigns.name."""
    op.execute("DROP INDEX IF EXISTS ix_campaigns_name_trgm")
    # Note: We don't drop the pg_trgm extension as it may be used elsewhere
