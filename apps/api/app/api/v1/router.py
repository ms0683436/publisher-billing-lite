from fastapi import APIRouter

from . import campaigns, hello, invoice_line_items, invoices

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router)
router.include_router(campaigns.router)
router.include_router(invoices.router)
router.include_router(invoice_line_items.router)
