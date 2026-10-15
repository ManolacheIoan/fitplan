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
    login_rate_limit: int = 5
    login_rate_window_seconds: int = 15 * 60
    # External food database adapter: "none" (default) or "mock". See nutrition/food_sources.
    food_source: str = "none"
    feature_ai_meal_parsing: bool = False

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Hosting providers hand out plain "postgresql://" URLs; SQLAlchemy needs the driver name.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
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
