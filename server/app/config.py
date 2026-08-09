from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
