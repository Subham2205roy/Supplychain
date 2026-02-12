from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.user_model import User
from backend.models.company_model import Company
from backend.models.team_invite_model import TeamInvite
from backend.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.routes.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from backend.settings import settings

# OAuth2PasswordBearer still supports Authorization header; auto_error=False lets us fall back to cookies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

router = APIRouter(tags=["Authentication"])


def _decode_token(token: str, expected_typ: str):
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("typ") != expected_typ:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    return payload


def _issue_tokens(user: User):
    jti = str(uuid.uuid4())
    access = create_access_token(user.email, user.hashed_password, jti)
    refresh = create_refresh_token(user.email, user.hashed_password, jti)
    return access, refresh


def _set_access_cookie(resp: Response, token: str):
    resp.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        max_age=settings.access_token_minutes * 60,
        path="/",
    )


def _set_refresh_cookie(resp: Response, token: str):
    resp.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        max_age=settings.refresh_token_days * 24 * 3600,
        path="/api/refresh",
    )


def _clear_cookies(resp: Response):
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/api/refresh")


@router.post("/api/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check for a pending invite for this email
    invite = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.invited_email == user.email,
            TeamInvite.status == "pending"
        )
        .order_by(TeamInvite.created_at.desc())
        .first()
    )

    if invite and invite.expires_at and invite.expires_at < datetime.utcnow():
        invite = None

    hashed_pwd = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_pwd)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if invite:
        # Join the inviter's company
        new_user.company_id = invite.company_id
        invite.status = "accepted"
        invite.accepted_by_user_id = new_user.id
        db.commit()
        db.refresh(new_user)
        return new_user

    # Create a new company for this user
    company_name = f"{user.username}'s Company"
    new_company = Company(name=company_name, owner_user_id=new_user.id)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    new_user.company_id = new_company.id
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/api/login", response_model=Token)
def login(user_credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_credentials.email).first()

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    access, refresh = _issue_tokens(user)
    _set_access_cookie(response, access)
    _set_refresh_cookie(response, refresh)

    return {"access_token": access, "token_type": "bearer", "username": user.username}


@router.post("/api/refresh", response_model=Token)
def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = _decode_token(refresh_token, "refresh")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user or user.hashed_password != payload.get("pwd"):
        raise HTTPException(status_code=401, detail="Token revoked")

    access, new_refresh = _issue_tokens(user)
    _set_access_cookie(response, access)
    _set_refresh_cookie(response, new_refresh)

    return {"access_token": access, "token_type": "bearer", "username": user.username}


@router.post("/api/logout")
def logout(response: Response):
    _clear_cookies(response)
    return {"message": "Logged out"}


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    bearer = token or request.cookies.get("access_token")
    if not bearer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = _decode_token(bearer, "access")
    email: str | None = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user or user.hashed_password != payload.get("pwd"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    return user
