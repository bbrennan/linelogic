"""
Settings and configuration management using Pydantic.

All settings are loaded from environment variables (via .env file).
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """LineLogic application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Data Provider: BALLDONTLIE
    balldontlie_api_key: str = Field(
        default="", description="BALLDONTLIE API key (optional for free tier)"
    )
    balldontlie_tier: str = Field(
        default="free", description="BALLDONTLIE tier: free, all-star, mvp"
    )
    balldontlie_rpm: int = Field(
        default=5, description="BALLDONTLIE rate limit (requests per minute)"
    )

    # Cache Settings
    cache_ttl_seconds: int = Field(
        default=86400, description="Default cache TTL (24 hours)"
    )
    cache_db_path: str = Field(
        default=".linelogic/cache.db", description="Cache SQLite database path"
    )

    # Rate Limiting
    global_rpm: int = Field(
        default=5, description="Global rate limit (requests per minute)"
    )

    # Storage
    database_path: str = Field(
        default=".linelogic/linelogic.db", description="Main SQLite database path"
    )

    # Application
    log_level: str = Field(
        default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR"
    )
    user_agent: str = Field(
        default="LineLogic/0.1.0 (github.com/linelogic/linelogic)",
        description="User-Agent for HTTP requests",
    )

    # Optional: Other providers (future)
    odds_api_key: str = Field(default="", description="The Odds API key")
    weatherapi_key: str = Field(default="", description="WeatherAPI key")


# Global settings instance
settings = Settings()
