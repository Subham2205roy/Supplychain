from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from backend.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _base_claims(sub: str, jti: str, pwd_hash: str, expires_delta: timedelta):
    now = datetime.now(timezone.utc)
    return {
        "sub": sub,
        "aud": settings.jwt_audience,
        "iss": settings.jwt_issuer,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": jti,
        "pwd": pwd_hash,
    }


def create_access_token(sub: str, pwd_hash: str, jti: str) -> str:
    claims = _base_claims(sub, jti, pwd_hash, timedelta(minutes=settings.access_token_minutes))
    claims["typ"] = "access"
    return jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(sub: str, pwd_hash: str, jti: str) -> str:
    claims = _base_claims(sub, jti, pwd_hash, timedelta(days=settings.refresh_token_days))
    claims["typ"] = "refresh"
    return jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)
