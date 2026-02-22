"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import missions, files, health, providers, messages, chat, suggested_actions

app = FastAPI(
    title="Missions",
    description="Persistent AI agent management system",
    version="0.1.0",
    debug=settings.debug,
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Missions API",
        "version": "0.1.0",
        "status": "running",
    }
