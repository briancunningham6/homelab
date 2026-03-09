"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api import missions, files, health, providers, messages, chat, suggested_actions, capture, notifications
from app.services.scheduler import mission_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    print("[APP] Starting application...")
    mission_scheduler.start()
    yield
    # Shutdown
    print("[APP] Shutting down application...")
    mission_scheduler.shutdown()


app = FastAPI(
    title="Missions",
    description="Persistent AI agent management system",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
app.include_router(files.router, prefix="/api/missions", tags=["files"])
app.include_router(suggested_actions.router, prefix="/api/missions", tags=["suggested-actions"])
app.include_router(providers.router)
app.include_router(messages.router)
app.include_router(chat.router)
app.include_router(capture.router, tags=["capture"])
app.include_router(notifications.router, tags=["notifications"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Missions API",
        "version": "0.1.0",
        "status": "running",
    }
