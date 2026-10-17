"""Runtime configuration, read from environment variables (see .env.example)."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    secret_key: str
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    cookie_secure: bool = True
    session_ttl_days: int = 14
    # Used to group workouts into local calendar weeks.
    app_timezone: str = "Europe/Bucharest"
    # Login attempts (successful or not) per (email, IP) pair, and per IP across all emails.
    login_rate_limit: int = 5
    login_ip_rate_limit: int = 20
    login_rate_window_seconds: int = 15 * 60
    # Number of X-Forwarded-For entries added by proxies we trust, counted from the right.
    # 0 = ignore the header (direct connections, tests). See DECISIONS.md.
    trusted_proxy_hops: int = 0
    # External food database: "none" (default), "open_food_facts" or "mock" (tests).
    food_source: str = "none"
    # Open Food Facts asks for "AppName/Version (contact email)"; set your own contact.
    off_user_agent: str = "FitPlan/0.1 (set OFF_USER_AGENT)"
    feature_ai_meal_parsing: bool = False
    # Bearer token for internal maintenance endpoints (scheduled guest cleanup).
    # Empty = endpoints disabled. Use a long random value (>= 32 characters).
    maintenance_token: str = ""

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Hosting providers hand out plain "postgresql://" URLs; SQLAlchemy needs the driver name.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @field_validator("maintenance_token")
    @classmethod
    def long_enough_token(cls, value: str) -> str:
        if value and len(value) < 32:
            raise ValueError("MAINTENANCE_TOKEN must be at least 32 characters")
        return value

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
