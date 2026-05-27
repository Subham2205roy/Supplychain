import os
import secrets
from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CRITICAL: secret_key should ideally have no default in production
    # to force the developer to set it in .env
    secret_key: str = "default-temp-secret-key-for-dev"
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "supplychain-users"
    jwt_issuer: str = "supplychain-api"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    # Production-safe defaults (override in .env for local dev)
    cookie_domain: str | None = None
    cookie_secure: bool = True
    cookie_samesite: str = "none"

    # Frontend URL (set in production to your Vercel URL)
    frontend_url: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_api_key: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/api/auth/google/callback"

    # SQL Alchemy Database Configuration
    # You can provide a full URL or individual components
    database_url: str | None = None
    db_host: str | None = None
    db_port: int = 5432
    db_user: str | None = None
    db_password: str | None = None
    db_name: str = "postgres"

    @property
    def sqlalchemy_database_url(self) -> str:
        from sqlalchemy.engine import URL
        
        if self.database_url:
            return self.database_url
        
        # Fallback to local sqlite if nothing else provided
        if not self.db_host:
            return f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'supplychain.db'))}"
        
        return URL.create(
            drivername="postgresql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)

    # SMTP Settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Internal Service Authentication
    internal_service_key: str = ""

    # Base URL for internal API calls
    base_url: str = "http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Dynamically adjust settings for Hugging Face Spaces environment
space_host = os.environ.get("SPACE_HOST")
space_id = os.environ.get("SPACE_ID")

if not space_host and space_id:
    # E.g. "subham2205/supplychain-app" -> "subham2205-supplychain-app.hf.space"
    parts = space_id.split("/")
    if len(parts) == 2:
        space_host = f"{parts[0]}-{parts[1]}.hf.space".replace("_", "-").lower()

if space_host:
    # If using the default localhost redirect URI, auto-update it to the secure space callback URL
    if settings.google_redirect_uri == "http://127.0.0.1:8000/api/auth/google/callback":
        settings.google_redirect_uri = f"https://{space_host}/api/auth/google/callback"


