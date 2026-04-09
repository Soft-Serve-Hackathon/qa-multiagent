"""FastAPI application entry point — registers routes, initializes DB, starts ResolutionWatcher."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.infrastructure.database import init_db
from src.agents.resolution_watcher import get_watcher
from src.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    watcher = get_watcher()
    watcher.start()
    yield
    # Shutdown
    watcher.stop()


app = FastAPI(
    title="SRE Incident Intake & Triage Agent",
    description=(
        "Multi-agent system for automated SRE incident triage. "
        "Powered by Claude claude-sonnet-4-6 with multimodal support. "
        "Built for the AgentX Hackathon by SoftServe."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "SRE Incident Intake & Triage Agent",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
