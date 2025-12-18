from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router as v1_router
from .services.notification_broadcaster import shutdown_broadcaster
from .services.notification_queue import shutdown_notification_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    yield
    # Shutdown: clean up Redis connections
    await shutdown_broadcaster()
    await shutdown_notification_queue()


app = FastAPI(title="Publisher Billing API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(v1_router)
