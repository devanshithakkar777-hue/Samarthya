from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _psycopg_url(url: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"  # dev | test | prod
    database_url: str = "postgresql+psycopg://samarthya:samarthya@localhost:5432/samarthya_dev"
    # Direct (non-pooled) connection, used only for migrations. Falls back to database_url when empty.
    direct_database_url: str = ""
    db_pool_size: int = 5
    db_pool_recycle_seconds: int = 300  # serverless databases drop idle connections
    log_level: str = "INFO"
    journal_key: str = ""  # Fernet key (32 url-safe base64 bytes) that encrypts wellness journal text
    # Optional AI companion. Off unless a key is set. The model name is configuration, never hard-coded.
    llm_provider: str = ""  # "anthropic", "gemini", "groq", "openrouter" or empty
    llm_api_key: str = ""
    llm_model: str = ""
    llm_daily_limit: int = 30  # messages per signed-in student per day
    # How many trusted proxies sit in front of the API. 0 = ignore X-Forwarded-For (local dev, tests).
    # Render web -> Render API over the public URL is 2 (Render's edge in front of each service).
    trusted_proxy_hops: int = 0
    jwt_secret: str = ""
    jwt_ttl_hours: int = 24 * 7
    cors_origins: str = "http://localhost:3000"

    otp_ttl_minutes: int = 10
    otp_max_attempts: int = 5
    otp_requests_per_hour: int = 5

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = Field("Samarthya <no-reply@samarthya.example>", validation_alias=AliasChoices("mail_from", "smtp_from"))

    stale_days: int = 180
    allow_self_review: bool = False  # only ever true in dev or test
    admin_bootstrap_email: str = ""  # this address becomes admin on first sign-in

    @field_validator("database_url", "direct_database_url")
    @classmethod
    def _normalise_urls(cls, v: str) -> str:
        """Providers hand out postgres:// or postgresql:// strings; this app uses the psycopg 3 driver."""
        return _psycopg_url(v)

    @model_validator(mode="after")
    def _check(self) -> "Settings":
        if self.env == "prod":
            if len(self.journal_key) < 32:
                raise ValueError("JOURNAL_KEY must be set to at least 32 random characters in prod")
            if self.llm_provider and not (self.llm_api_key and self.llm_model):
                raise ValueError("LLM_PROVIDER needs LLM_API_KEY and LLM_MODEL")
            if len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be set to at least 32 characters in prod")
            if self.allow_self_review:
                raise ValueError("ALLOW_SELF_REVIEW must be false in prod")
            if not self.smtp_host:
                raise ValueError("SMTP_HOST is required in prod so sign-in codes can be sent")
        elif not self.jwt_secret:
            self.jwt_secret = "dev-only-secret-not-for-production-use-0000"
        return self

    @property
    def migration_url(self) -> str:
        return _psycopg_url(self.direct_database_url or self.database_url)

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
