"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str

    # Encryption
    encryption_key: str

    # Notifications
    ntfy_url: str = "http://ntfy:80"
    ntfy_topic: str = "missions"

    # CORS
    cors_origins: str = "http://missions.home,http://localhost:5173"

    # Development
    debug: bool = False
    log_level: str = "info"

    # Optional external APIs
    tavily_api_key: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
