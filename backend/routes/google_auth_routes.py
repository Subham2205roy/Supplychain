"""Google OAuth 2.0 login routes."""

import secrets
import urllib.parse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.user_model import User
from backend.models.company_model import Company
from backend.settings import settings
from backend.routes.auth_utils import create_access_token, create_refresh_token
from backend.routes.auth_routes import _set_access_cookie, _set_refresh_cookie

import uuid

router = APIRouter(tags=["Google OAuth"])

# Google endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/api/auth/google/login")
def google_login():
    """Redirect user to Google's OAuth consent screen."""
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@router.get("/api/auth/google/callback")
def google_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Handle the callback from Google after user grants permission."""

    # 1. Exchange authorization code for tokens
    token_data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    with httpx.Client() as client:
        token_resp = client.post(GOOGLE_TOKEN_URL, data=token_data)

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token from Google")

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token from Google")

    # 2. Get user info from Google
    with httpx.Client() as client:
        userinfo_resp = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    google_user = userinfo_resp.json()
    email = google_user.get("email")
    name = google_user.get("name", email.split("@")[0] if email else "User")

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    # 3. Find or create user
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user with Google auth
        # Generate a unique username from the Google name
        base_username = name.replace(" ", "_").lower()
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            hashed_password=None,
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a company for the new user
        company = Company(name=f"{name}'s Company", owner_user_id=user.id)
        db.add(company)
        db.commit()
        db.refresh(company)

        user.company_id = company.id
        db.commit()
        db.refresh(user)

    # 4. Issue JWT tokens (reusing existing token helpers)
    jti = str(uuid.uuid4())
    pwd_hash = user.hashed_password or "google-oauth"
    access = create_access_token(user.email, pwd_hash, jti)
    refresh = create_refresh_token(user.email, pwd_hash, jti)

    # 5. Set cookies and redirect to dashboard
    response = RedirectResponse(url="/dashboard", status_code=302)
    _set_access_cookie(response, access)
    _set_refresh_cookie(response, refresh)

    return response
