"""
FastAPI application entry point.

Main application instance and startup/shutdown events.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agents.resolution_watcher import ResolutionWatcher
from .api.routes import router
from .config import get_settings
from .infrastructure.database import create_tables
from .infrastructure.observability.logger import configure_logging

settings = get_settings()

configure_logging(level=settings.log_level, log_file=settings.log_file)
logger = logging.getLogger(__name__)

_start_time = time.time()

# Initialize ResolutionWatcher for background polling
resolution_watcher = ResolutionWatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    logger.info("Database tables ready")

    await resolution_watcher.start()
    logger.info("ResolutionWatcher started")

    yield

    # Shutdown
    await resolution_watcher.stop()
    logger.info("ResolutionWatcher stopped")


app = FastAPI(
    title="SRE Incident Intake & Triage Agent",
    version="1.0.0",
    description="Automated incident triage pipeline powered by Claude",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - _start_time),
        "database": "connected",
        "mock_mode": settings.mock_integrations,
    }
