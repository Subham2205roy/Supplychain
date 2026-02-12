import secrets
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "supplychain-users"
    jwt_issuer: str = "supplychain-api"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    database_url: AnyUrl | str = "sqlite:///./supplychain.db"

    class Config:
        env_file = ".env"


settings = Settings()

