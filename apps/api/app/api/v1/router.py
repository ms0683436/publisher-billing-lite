from fastapi import APIRouter

from . import hello

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router)
