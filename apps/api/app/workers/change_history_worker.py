"""Change history worker that processes the Procrastinate queue.

This worker runs as a separate process, using PostgreSQL LISTEN/NOTIFY
to receive job notifications and recording change history entries asynchronously.

Usage:
    python -m app.workers.change_history_worker
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from ..queue.procrastinate_app import get_procrastinate_app

# Import tasks to register them with the app
from ..queue.tasks import change_history  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Worker configuration
WORKER_NAME = "change-history-worker"
WORKER_CONCURRENCY = 5  # Process up to 5 jobs in parallel
SHUTDOWN_TIMEOUT = 30.0  # Wait up to 30s for jobs to finish on shutdown


async def main() -> None:
    """Main entry point for the change history worker."""
    app = get_procrastinate_app()

    # Worker task reference for cancellation on shutdown
    worker_task: asyncio.Task[None] | None = None

    def signal_handler() -> None:
        logger.info("Shutdown signal received...")
        if worker_task is not None:
            worker_task.cancel()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    logger.info("Change history worker '%s' starting...", WORKER_NAME)
    logger.info("Registered tasks: %s", list(app.tasks.keys()))

    try:
        async with app.open_async():
            worker_task = asyncio.create_task(
                app.run_worker_async(
                    name=WORKER_NAME,
                    concurrency=WORKER_CONCURRENCY,
                    wait=True,
                    listen_notify=True,
                    delete_jobs="successful",
                    shutdown_graceful_timeout=SHUTDOWN_TIMEOUT,
                )
            )
            try:
                await worker_task
            except asyncio.CancelledError:
                logger.info("Worker task cancelled, shutting down...")

    except Exception as e:
        logger.exception("Worker error: %s", e)
        raise

    logger.info("Change history worker stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
