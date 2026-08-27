"""
Application configuration.

Settings are loaded from environment variables (and a local .env file in
development). Nothing sensitive is hardcoded here -- see .env.example for
the full list of variables a deployment must supply.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Finora"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str

    POSTGRES_DB: str = "finora"
    POSTGRES_USER: str = "finora"
    POSTGRES_PASSWORD: str = ""

    DEFAULT_CURRENCY: str = "PKR"
    CORS_ORIGINS: str = "http://localhost"
    COOKIE_SECURE: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
