from fastapi import APIRouter

from . import campaigns, comments, hello, invoices, users

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router)
router.include_router(campaigns.router)
router.include_router(invoices.router)
router.include_router(users.router)
router.include_router(comments.router)
