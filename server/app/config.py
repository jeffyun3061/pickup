from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GamePickup API"
    env: str = "development"
    database_url: str = "sqlite:///./gamepickup.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    admin_username: str = "admin"
    admin_password_hash: str = ""

    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 720
    jwt_algorithm: str = "HS256"

    ingest_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT_SECRET must not be empty")
        return value

    @model_validator(mode="after")
    def production_secrets(self) -> "Settings":
        if self.is_production:
            if self.jwt_secret == "dev-only-change-me":
                raise ValueError("JWT_SECRET must be rotated in production")
            if not self.admin_password_hash:
                raise ValueError("ADMIN_PASSWORD_HASH is required in production")
            if not self.ingest_api_key:
                raise ValueError("INGEST_API_KEY is required in production")
            if not self.cors_origin_list:
                raise ValueError("CORS_ORIGINS allowlist is required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
