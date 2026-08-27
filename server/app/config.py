import re
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GamePickup API"
    env: str = "development"
    # 개발·테스트·운영 모두 PostgreSQL을 사용한다. 환경별로 주소만 바꾼다.
    database_url: str = (
        "postgresql+psycopg://gamepickup:gamepickup_dev@127.0.0.1:5432/gamepickup"
    )
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    admin_username: str = "admin"
    admin_password_hash: str = ""

    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 720
    jwt_algorithm: str = "HS256"

    ingest_api_key: str = ""

    # LLM 요약 (비우면 규칙 기반 요약으로 폴백)
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    summarize_daily_limit: int = 300

    # 푸시: false면 스텁 발송(로그만), true면 Expo Push API 실발송
    expo_push_enabled: bool = False
    # 조용시간(현지 기준): 이 시간대에 발행된 푸시는 다음 quiet_hours_end 정각으로 미룬다
    quiet_hours_start: int = 23
    quiet_hours_end: int = 8
    quiet_hours_utc_offset: int = 9  # KST

    # 주기 작업 러너 (마감 리마인더·예약 발행·데드링크 감지)
    scheduler_enabled: bool = False
    # 게시 후 푸시 outbox와 이벤트 마감 알림을 빠르게 처리하되,
    # 1인 운영 MVP에서 별도 큐 인프라는 추가하지 않는다.
    scheduler_interval_seconds: int = Field(default=60, ge=30, le=86400)

    # collector가 비정상 종료된 뒤 작업을 다시 시도하기까지의 최대 실행 시간
    ingest_stale_after_minutes: int = Field(default=45, ge=5, le=1440)

    # 앱 최소 지원 버전 (semver, 빈 값이면 게이트 없음)
    min_app_version: str = ""

    # 업로드 이미지 저장 경로 (프로덕션은 볼륨 마운트 경로로 지정)
    media_dir: str = "./media"
    # 관리자 웹 정적 빌드 경로 — 존재하면 /admin 으로 same-origin 서빙
    admin_dist_dir: str = "../admin/dist"
    # 스토어 개인정보처리방침에 표시할 운영 문의처
    privacy_contact_email: str = ""

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

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_postgres_driver(cls, value: str) -> str:
        """Railway URL에도 psycopg3 드라이버를 명시하고 PostgreSQL만 허용한다."""
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://") :]
        if not value.lower().startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL must use PostgreSQL (postgresql+psycopg://) in every environment"
            )
        return value

    @model_validator(mode="after")
    def production_secrets(self) -> "Settings":
        if self.is_production:
            if self.jwt_secret.strip() in {
                "dev-only-change-me",
                "change-me-to-a-long-random-string",
            }:
                raise ValueError("JWT_SECRET must be rotated in production")
            if len(self.jwt_secret.encode("utf-8")) < 32:
                raise ValueError("JWT_SECRET must be at least 32 bytes in production")
            if not self.admin_password_hash:
                raise ValueError("ADMIN_PASSWORD_HASH is required in production")
            if not self.ingest_api_key:
                raise ValueError("INGEST_API_KEY is required in production")
            if self.ingest_api_key.strip() in {"change-me-ingest-key", "test-ingest-key"}:
                raise ValueError("INGEST_API_KEY must be rotated in production")
            if len(self.ingest_api_key.encode("utf-8")) < 32:
                raise ValueError("INGEST_API_KEY must be at least 32 bytes in production")
            if not self.cors_origin_list:
                raise ValueError("CORS_ORIGINS allowlist is required in production")
            if "*" in self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must not contain '*' in production")
            for origin in self.cors_origin_list:
                parsed = urlparse(origin)
                hostname = (parsed.hostname or "").lower().rstrip(".")
                if parsed.scheme != "https" or not hostname:
                    raise ValueError("CORS_ORIGINS must contain HTTPS origins in production")
                if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(
                    (".local", ".localhost", ".test", ".invalid", ".example")
                ):
                    raise ValueError("CORS_ORIGINS must not contain development placeholders")
                if (
                    parsed.username
                    or parsed.password
                    or parsed.path not in {"", "/"}
                    or parsed.query
                    or parsed.fragment
                ):
                    raise ValueError("CORS_ORIGINS must contain origins without paths")
            if not self.expo_push_enabled:
                raise ValueError("EXPO_PUSH_ENABLED=true is required in production")
            if not self.scheduler_enabled:
                raise ValueError("SCHEDULER_ENABLED=true is required in production")
            contact = self.privacy_contact_email.strip()
            contact_domain = contact.rsplit("@", 1)[-1].lower().rstrip(".")
            if (
                not contact
                or "@" not in contact
                or not contact.split("@", 1)[0].strip()
                or contact_domain in {"example.com", "example.org", "example.net"}
                or contact_domain.endswith((".example", ".test", ".invalid", ".local"))
            ):
                raise ValueError("PRIVACY_CONTACT_EMAIL is required in production")
            if not re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", self.admin_password_hash.strip()):
                raise ValueError("ADMIN_PASSWORD_HASH must be a valid bcrypt hash in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
