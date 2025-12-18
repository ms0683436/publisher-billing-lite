from fastapi import APIRouter

from . import auth, campaigns, comments, hello, history, invoices, notifications, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(hello.router)
router.include_router(campaigns.router)
router.include_router(invoices.router)
router.include_router(users.router)
router.include_router(comments.router)
router.include_router(history.router)
router.include_router(notifications.router)
