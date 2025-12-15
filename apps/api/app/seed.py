"""Idempotent seed data importer from seed.json

This module provides functionality to import seed data from seed.json
in an idempotent manner, preserving user edits to adjustments.
"""

import asyncio
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from .db import get_session_maker
from .models import Campaign, Invoice, InvoiceLineItem, LineItem, User

# Default seed users
SEED_USERS = [
    {"username": "alice", "email": "alice@example.com"},
    {"username": "bob", "email": "bob@example.com"},
    {"username": "charlie", "email": "charlie@example.com"},
]


async def get_or_create_user(session: AsyncSession, username: str, email: str) -> User:
    """Get or create a User by username.

    Args:
        session: Database session
        username: Username
        email: Email address

    Returns:
        User instance
    """
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        user = User(username=username, email=email, is_active=True)
        session.add(user)
        await session.flush()

    return user


def parse_decimal(value: float | str) -> Decimal:
    """Parse a numeric value into Decimal, avoiding float artifacts.

    Args:
        value: A numeric value (float or string)

    Returns:
        Decimal representation of the value
    """
    return Decimal(str(value))


async def upsert_campaign(
    session: AsyncSession, campaign_id: int, campaign_name: str
) -> Campaign:
    """Upsert a campaign by campaign_id.

    Args:
        session: Database session
        campaign_id: Campaign ID from seed data
        campaign_name: Campaign name

    Returns:
        Campaign instance
    """
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if campaign:
        # Update name if changed
        if campaign.name != campaign_name:
            campaign.name = campaign_name
    else:
        # Create new campaign
        campaign = Campaign(id=campaign_id, name=campaign_name)
        session.add(campaign)

    return campaign


async def get_or_create_line_item(
    session: AsyncSession,
    campaign_id: int,
    line_item_name: str,
    booked_amount: Decimal,
) -> LineItem:
    """Get or create a LineItem by (campaign_id, name).

    Args:
        session: Database session
        campaign_id: Campaign ID
        line_item_name: Line item name
        booked_amount: Booked amount

    Returns:
        LineItem instance
    """
    result = await session.execute(
        select(LineItem).where(
            LineItem.campaign_id == campaign_id, LineItem.name == line_item_name
        )
    )
    line_item = result.scalar_one_or_none()

    if not line_item:
        # Create new line item
        line_item = LineItem(
            campaign_id=campaign_id, name=line_item_name, booked_amount=booked_amount
        )
        session.add(line_item)
        await session.flush()  # Get the ID

    return line_item


async def get_or_create_invoice(session: AsyncSession, campaign_id: int) -> Invoice:
    """Get or create an Invoice by campaign_id (1:1 relationship).

    Args:
        session: Database session
        campaign_id: Campaign ID

    Returns:
        Invoice instance
    """
    result = await session.execute(
        select(Invoice).where(Invoice.campaign_id == campaign_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        # Create new invoice
        invoice = Invoice(campaign_id=campaign_id)
        session.add(invoice)
        await session.flush()  # Get the ID

    return invoice


async def get_or_create_invoice_line_item(
    session: AsyncSession,
    invoice_id: int,
    line_item_id: int,
    actual_amount: Decimal,
    adjustments: Decimal,
) -> InvoiceLineItem:
    """Get or create an InvoiceLineItem, preserving existing adjustments.

    Args:
        session: Database session
        invoice_id: Invoice ID
        line_item_id: Line item ID
        actual_amount: Actual amount from seed
        adjustments: Adjustments from seed (only used if creating new)

    Returns:
        InvoiceLineItem instance
    """
    result = await session.execute(
        select(InvoiceLineItem).where(
            InvoiceLineItem.invoice_id == invoice_id,
            InvoiceLineItem.line_item_id == line_item_id,
        )
    )
    invoice_line_item = result.scalar_one_or_none()

    if invoice_line_item:
        # Update actual_amount, but DO NOT overwrite adjustments
        # (preserve user edits)
        invoice_line_item.actual_amount = actual_amount
    else:
        # Create new invoice line item with seed adjustments
        invoice_line_item = InvoiceLineItem(
            invoice_id=invoice_id,
            line_item_id=line_item_id,
            actual_amount=actual_amount,
            adjustments=adjustments,
        )
        session.add(invoice_line_item)

    return invoice_line_item


async def import_seed_data(
    seed_path: Path | None = None, show_progress: bool = True
) -> dict[str, int]:
    """Import seed data from seed.json in an idempotent manner.

    Args:
        seed_path: Optional path to seed.json (defaults to app/seeds/placements_teaser_data.json)
        show_progress: Whether to show progress bar (default: True)

    Returns:
        Dictionary with counts of processed entities
    """
    # Determine seed file path
    if seed_path is None:
        app_dir = Path(__file__).parent
        seed_path = app_dir / "seeds" / "placements_teaser_data.json"

    # Read seed data
    with open(seed_path, encoding="utf-8") as f:
        seed_data = json.load(f)

    # Get async session
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Create seed users first
        users_processed = 0
        for user_data in SEED_USERS:
            await get_or_create_user(session, user_data["username"], user_data["email"])
            users_processed += 1

        campaigns_processed = set()
        line_items_processed = 0
        invoices_processed = set()
        invoice_line_items_processed = 0

        # Create progress bar
        iterator = (
            tqdm(seed_data, desc="Importing seed data", unit="row")
            if show_progress
            else seed_data
        )

        for entry in iterator:
            campaign_id = entry["campaign_id"]
            campaign_name = entry["campaign_name"]
            line_item_name = entry["line_item_name"]
            booked_amount = parse_decimal(entry["booked_amount"])
            actual_amount = parse_decimal(entry["actual_amount"])
            adjustments = parse_decimal(entry["adjustments"])

            # Upsert campaign
            await upsert_campaign(session, campaign_id, campaign_name)
            campaigns_processed.add(campaign_id)

            # Get or create line item
            line_item = await get_or_create_line_item(
                session, campaign_id, line_item_name, booked_amount
            )
            line_items_processed += 1

            # Get or create invoice (1:1 with campaign)
            invoice = await get_or_create_invoice(session, campaign_id)
            invoices_processed.add(campaign_id)

            # Get or create invoice line item (preserving adjustments)
            await get_or_create_invoice_line_item(
                session, invoice.id, line_item.id, actual_amount, adjustments
            )
            invoice_line_items_processed += 1

        # Commit all changes
        await session.commit()

        return {
            "users": users_processed,
            "campaigns": len(campaigns_processed),
            "line_items": line_items_processed,
            "invoices": len(invoices_processed),
            "invoice_line_items": invoice_line_items_processed,
        }


async def main():
    """CLI entry point for running seed import."""
    print("Starting seed data import...")
    counts = await import_seed_data()
    print("✅ Seed import completed:")
    print(f"   Users: {counts['users']}")
    print(f"   Campaigns: {counts['campaigns']}")
    print(f"   Line items: {counts['line_items']}")
    print(f"   Invoices: {counts['invoices']}")
    print(f"   Invoice line items: {counts['invoice_line_items']}")


if __name__ == "__main__":
    asyncio.run(main())
