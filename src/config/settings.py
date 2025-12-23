import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: PostgresDsn = (
        "postgresql://autoria_user:autoria_pass@postgres:5432/autoria_db"
    )

    # Scraper
    start_url: str = "https://auto.ria.com/uk/car/used/"
    max_concurrent_requests: int = 5
    request_delay: float = 1.5
    max_pages_to_scrape: int = 10
    max_ads_to_scrape: int = 200

    # Scheduler
    scraper_start_time: str = "12:00"
    dump_time: str = "12:05"

    # Anti-ban
    user_agent_rotation: bool = True
    use_proxy: bool = False
    max_retries: int = 3
    retry_delay: int = 2

    # Dumps
    keep_dumps_days: int = 7
    dump_format: str = "sql"

    # Application
    log_level: str = "INFO"
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
