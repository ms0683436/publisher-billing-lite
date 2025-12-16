"""Shared test fixtures for the publisher-billing-api test suite."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models import (
    Base,
    Campaign,
    Comment,
    CommentMention,
    Invoice,
    InvoiceLineItem,
    LineItem,
    User,
)

# Pre-computed bcrypt hash for "password123" (avoids import issues at module load)
# Generated with: get_password_hash("password123")
DEFAULT_TEST_PASSWORD_HASH = (
    "$2b$12$4/jYBe2FhZ1HQJZhqhQ11uHTwscvdsd2XeIqv7rCJmmtTE4FcrPF."
)

# Use TEST_DATABASE_URL or fall back to default test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://publisher:publisher@localhost:5432/publisher_billing_test",
)


@pytest.fixture
async def engine():
    """Create a test database engine with fresh tables for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    async with engine.connect() as conn:
        # Start a transaction
        await conn.begin()
        async_session = AsyncSession(bind=conn, expire_on_commit=False)

        yield async_session

        # Rollback the transaction (clean slate for next test)
        await async_session.close()
        await conn.rollback()


# =============================================================================
# Factory fixtures for creating test data
# =============================================================================


@pytest.fixture
def make_campaign(session: AsyncSession):
    """Factory fixture to create Campaign instances."""

    async def _make_campaign(name: str = "Test Campaign") -> Campaign:
        campaign = Campaign(name=name)
        session.add(campaign)
        await session.flush()
        await session.refresh(campaign)
        return campaign

    return _make_campaign


@pytest.fixture
def make_line_item(session: AsyncSession):
    """Factory fixture to create LineItem instances."""

    async def _make_line_item(
        campaign: Campaign,
        name: str = "Test Line Item",
        booked_amount: Decimal = Decimal("100.00"),
    ) -> LineItem:
        line_item = LineItem(
            campaign_id=campaign.id,
            name=name,
            booked_amount=booked_amount,
        )
        session.add(line_item)
        await session.flush()
        await session.refresh(line_item)
        return line_item

    return _make_line_item


@pytest.fixture
def make_invoice(session: AsyncSession):
    """Factory fixture to create Invoice instances."""

    async def _make_invoice(campaign: Campaign) -> Invoice:
        invoice = Invoice(campaign_id=campaign.id)
        session.add(invoice)
        await session.flush()
        await session.refresh(invoice)
        return invoice

    return _make_invoice


@pytest.fixture
def make_invoice_line_item(session: AsyncSession):
    """Factory fixture to create InvoiceLineItem instances."""

    async def _make_invoice_line_item(
        invoice: Invoice,
        line_item: LineItem,
        actual_amount: Decimal = Decimal("80.00"),
        adjustments: Decimal = Decimal("0.00"),
    ) -> InvoiceLineItem:
        invoice_line_item = InvoiceLineItem(
            invoice_id=invoice.id,
            line_item_id=line_item.id,
            actual_amount=actual_amount,
            adjustments=adjustments,
        )
        session.add(invoice_line_item)
        await session.flush()
        await session.refresh(invoice_line_item)
        return invoice_line_item

    return _make_invoice_line_item


@pytest.fixture
def make_user(session: AsyncSession):
    """Factory fixture to create User instances."""
    _counter = [0]

    async def _make_user(
        username: str | None = None,
        email: str | None = None,
        is_active: bool = True,
        password_hash: str | None = None,
    ) -> User:
        _counter[0] += 1
        if username is None:
            username = f"user{_counter[0]}"
        if email is None:
            email = f"{username}@example.com"
        if password_hash is None:
            password_hash = DEFAULT_TEST_PASSWORD_HASH

        user = User(
            username=username,
            email=email,
            is_active=is_active,
            password_hash=password_hash,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def make_comment(session: AsyncSession):
    """Factory fixture to create Comment instances."""

    async def _make_comment(
        campaign: Campaign,
        author: User,
        content: str = "Test comment",
        parent: Comment | None = None,
    ) -> Comment:
        comment = Comment(
            content=content,
            campaign_id=campaign.id,
            author_id=author.id,
            parent_id=parent.id if parent else None,
        )
        session.add(comment)
        await session.flush()
        await session.refresh(comment)
        return comment

    return _make_comment


@pytest.fixture
def make_comment_mention(session: AsyncSession):
    """Factory fixture to create CommentMention instances."""

    async def _make_comment_mention(
        comment: Comment,
        user: User,
    ) -> CommentMention:
        mention = CommentMention(comment_id=comment.id, user_id=user.id)
        session.add(mention)
        await session.flush()
        await session.refresh(mention)
        return mention

    return _make_comment_mention
