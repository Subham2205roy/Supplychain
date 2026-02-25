import os
import secrets
from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CRITICAL: secret_key should ideally have no default in production
    # to force the developer to set it in .env
    secret_key: str 
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "supplychain-users"
    jwt_issuer: str = "supplychain-api"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_api_key: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/api/auth/google/callback"

    # Default to local sqlite, but can be overridden by DATABASE_URL env var
    database_url: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'supplychain.db'))}"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

