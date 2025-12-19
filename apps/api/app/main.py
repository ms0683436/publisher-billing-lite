from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router as v1_router
from .queue.procrastinate_app import get_procrastinate_app
from .services.notification_broadcaster import shutdown_broadcaster
from .services.notification_queue import shutdown_notification_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup: open Procrastinate connection
    procrastinate_app = get_procrastinate_app()
    await procrastinate_app.open_async()
    try:
        yield
    finally:
        # Shutdown: clean up connections (ensure all run even if one fails)
        try:
            await shutdown_broadcaster()
        finally:
            try:
                await shutdown_notification_queue()
            finally:
                await procrastinate_app.close_async()


app = FastAPI(title="Publisher Billing API", lifespan=lifespan)

# CORS configuration (only needed for direct access, nginx proxy is same-origin)
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(v1_router)
