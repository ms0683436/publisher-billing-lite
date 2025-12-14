"""Shared test fixtures for the publisher-billing-api test suite."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.models import Base, Campaign, Invoice, InvoiceLineItem, LineItem

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
