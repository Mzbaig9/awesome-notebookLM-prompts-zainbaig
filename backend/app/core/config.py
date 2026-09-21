from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Print Ordering API"
    environment: str = "development"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24
    frontend_url: str = "http://localhost:3000"

    database_url: str = "sqlite:///./printshop.db"

    storage_backend: str = "local"
    local_storage_dir: str = "./storage"
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_endpoint_url: str | None = None
    max_upload_mb: int = 200

    payment_provider: str = "fake"
    currency: str = "cad"
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    email_backend: str = "console"
    email_from: str = "orders@example.com"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None

    shipping_standard_cents: int = 1500
    shipping_express_cents: int = 3500

    admin_email: str | None = None
    admin_password: str | None = None

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
